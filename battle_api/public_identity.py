"""Public player credentials and sessions; no battle or Development-save access.

The caller owns HTTP Origin/CSRF headers and cookie serialization. This service
owns cryptographic verification and SQLite transactions, and returns a raw
recovery code only from enrollment or authenticated replacement.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import ipaddress
import re
import secrets
import sqlite3
from collections.abc import Callable, Iterator, Mapping
from typing import TYPE_CHECKING
import uuid

from .progression import ProgressionStoreError

if TYPE_CHECKING:
    from .progression import ProgressionStore


RECOVERY_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
assert len(RECOVERY_ALPHABET) == 32 and len(set(RECOVERY_ALPHABET)) == 32
PLAYER_NAME_PATTERN = re.compile(r"[A-Za-z0-9_]{3,20}\Z", re.ASCII)
SESSION_DAYS = 30
ROTATE_AFTER = timedelta(hours=24)
PREVIOUS_TOKEN_GRACE = timedelta(seconds=60)
RECOVERY_WINDOW = timedelta(minutes=15)
RECOVERY_BLOCK = timedelta(minutes=15)
MAX_RECOVERY_FAILURES = 10


class PublicIdentityError(ValueError):
    """Stable, non-secret error surfaced through typed HTTP responses."""

    def __init__(self, code: str, message: str, status_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


@dataclass(frozen=True)
class AuthenticatedSession:
    player_id: str
    display_name: str
    session_id: str
    generation: int
    csrf_token: str = field(repr=False)
    expires_at: str
    recovery_confirmed: bool
    rotated_token: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class IssuedIdentity:
    player_id: str
    display_name: str
    session_id: str
    generation: int
    session_token: str = field(repr=False)
    csrf_token: str = field(repr=False)
    expires_at: str
    recovery_confirmed: bool
    recovery_code: str | None = field(default=None, repr=False)


def _canonical_ip(value: str) -> str:
    address = ipaddress.ip_address(value)
    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
        address = address.ipv4_mapped
    return address.compressed


def canonical_client_ip(
    peer_ip: str,
    forwarded_for: str | None,
    trusted_proxy_ips: frozenset[str] = frozenset(),
) -> str:
    """Accept one proxy-overwritten address only from an explicitly trusted peer.

    A comma-separated forwarded chain is deliberately rejected: allowing the
    first value would let an attacker supply an arbitrary rate-limit identity.
    The deployment proxy must overwrite, not append, this header.
    """

    try:
        peer = _canonical_ip(peer_ip)
        trusted = {_canonical_ip(ip) for ip in trusted_proxy_ips}
        if peer not in trusted:
            return peer
        if forwarded_for is None:
            raise ValueError("trusted proxy omitted the client address")
        if "," in forwarded_for:
            raise ValueError("forwarded chain is not canonical")
        return _canonical_ip(forwarded_for.strip())
    except ValueError as exc:
        raise PublicIdentityError(
            "invalidClientAddress", "The client address could not be verified.", 400
        ) from exc


class PublicIdentityService:
    """The Public-only Player ID, Recovery Code, and session authority.

    ``assert_current_session`` is intentionally public to the progression
    store: call it *inside the same BEGIN IMMEDIATE transaction* as each
    protected write, so recovery/logout cannot race between route auth and the
    durable mutation.
    """

    def __init__(
        self,
        store: ProgressionStore,
        *,
        key: bytes,
        key_version: int = 1,
        previous_keys: Mapping[int, bytes] | None = None,
        rate_limit_key: bytes | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        if not store.public_mode:
            raise ValueError("Public identity requires a Public progression store")
        if not isinstance(key, bytes) or key_version < 1 or len(key) < 32:
            raise ValueError("Public identity needs a versioned 256-bit server key")
        old_keys = dict(previous_keys or {})
        if key_version in old_keys or any(
            version < 1 or not isinstance(old_key, bytes) or len(old_key) < 32
            for version, old_key in old_keys.items()
        ):
            raise ValueError("Previous key versions must be distinct and secure")
        if rate_limit_key is not None and (
            not isinstance(rate_limit_key, bytes) or len(rate_limit_key) < 32
        ):
            raise ValueError("Rate-limit key must contain at least 256 bits")
        self.store = store
        self.key_version = key_version
        self.keys = {key_version: key, **old_keys}
        # A separately configured stable key is preferred. During an auth-key
        # rotation, also consult previous key versions so a 15-minute block
        # cannot be evaded merely by crossing the rotation boundary.
        self.rate_limit_keys = (
            [rate_limit_key] if rate_limit_key else list(self.keys.values())
        )
        self.now = now or (lambda: datetime.now(UTC))

    @staticmethod
    def _stamp(instant: datetime) -> str:
        if instant.tzinfo is None:
            raise ValueError("The identity clock must return timezone-aware UTC")
        return instant.astimezone(UTC).isoformat(timespec="microseconds").replace(
            "+00:00", "Z"
        )

    def _instant(self) -> datetime:
        value = self.now()
        if value.tzinfo is None:
            raise ValueError("The identity clock must return timezone-aware UTC")
        return value.astimezone(UTC)

    @staticmethod
    def _parse(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    @staticmethod
    def _mac(key: bytes, domain: str, value: str) -> bytes:
        payload = b"loct/public/v1/" + domain.encode("ascii") + b"\0" + value.encode(
            "utf-8"
        )
        return hmac.new(key, payload, hashlib.sha256).digest()

    def _current_mac(self, domain: str, value: str) -> bytes:
        return self._mac(self.keys[self.key_version], domain, value)

    def _csrf(self, session_id: str, key: bytes) -> str:
        # Stable across routine token rotation so a late same-device tab
        # response cannot replace a valid CSRF value with an obsolete one.
        return self._mac(key, "csrf-token", session_id).hex()

    @staticmethod
    def _new_code() -> str:
        raw = "".join(secrets.choice(RECOVERY_ALPHABET) for _ in range(16))
        return "-".join(raw[index : index + 4] for index in range(0, 16, 4))

    @staticmethod
    def _normalize_code(code: str) -> str | None:
        if not isinstance(code, str):
            return None
        canonical = code.replace("-", "").upper()
        if len(canonical) != 16 or any(
            character not in RECOVERY_ALPHABET for character in canonical
        ):
            return None
        return canonical

    @staticmethod
    def _new_token() -> str:
        return secrets.token_urlsafe(32)

    @contextmanager
    def _write(self) -> Iterator[sqlite3.Connection]:
        try:
            connection = self.store._connection()
        except (sqlite3.Error, ProgressionStoreError) as exc:
            raise PublicIdentityError(
                "identityStoreUnavailable", "Player data is temporarily unavailable.", 503
            ) from exc
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except (sqlite3.Error, ProgressionStoreError) as exc:
            connection.rollback()
            raise PublicIdentityError(
                "identityStoreUnavailable", "Player data is temporarily unavailable.", 503
            ) from exc
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    @contextmanager
    def _read(self) -> Iterator[sqlite3.Connection]:
        """Validate a session without opening a write transaction or changing it."""

        try:
            connection = self.store._connection()
        except (sqlite3.Error, ProgressionStoreError) as exc:
            raise PublicIdentityError(
                "identityStoreUnavailable", "Player data is temporarily unavailable.", 503
            ) from exc
        try:
            yield connection
        except (sqlite3.Error, ProgressionStoreError) as exc:
            raise PublicIdentityError(
                "identityStoreUnavailable", "Player data is temporarily unavailable.", 503
            ) from exc
        finally:
            connection.close()

    def _unused_code(self, connection: sqlite3.Connection) -> tuple[str, bytes]:
        for _ in range(10):
            code = self._new_code()
            mac = self._current_mac("recovery-code", code.replace("-", ""))
            if connection.execute(
                "SELECT 1 FROM players WHERE recovery_mac = ?", (mac,)
            ).fetchone() is None:
                return code, mac
        raise PublicIdentityError(
            "identityStoreUnavailable", "Player data is temporarily unavailable.", 503
        )

    def _insert_session(
        self,
        connection: sqlite3.Connection,
        *,
        player_id: str,
        display_name: str,
        generation: int,
        recovery_confirmed: bool,
        instant: datetime,
        recovery_code: str | None,
    ) -> IssuedIdentity:
        token = self._new_token()
        session_id = uuid.uuid4().hex
        csrf = self._csrf(session_id, self.keys[self.key_version])
        expires_at = self._stamp(instant + timedelta(days=SESSION_DAYS))
        connection.execute(
            """INSERT INTO player_sessions
               (session_id, player_id, token_mac, previous_token_mac,
                previous_token_valid_until, generation, csrf_mac,
                issued_at, last_seen_at, expires_at, revoked_at)
               VALUES (?, ?, ?, NULL, NULL, ?, ?, ?, ?, ?, NULL)""",
            (
                session_id,
                player_id,
                self._current_mac("session-token", token),
                generation,
                self._current_mac("csrf-verifier", csrf),
                self._stamp(instant),
                self._stamp(instant),
                expires_at,
            ),
        )
        return IssuedIdentity(
            player_id=player_id,
            display_name=display_name,
            session_id=session_id,
            generation=generation,
            session_token=token,
            csrf_token=csrf,
            expires_at=expires_at,
            recovery_confirmed=recovery_confirmed,
            recovery_code=recovery_code,
        )

    def enroll(self, display_name: str) -> IssuedIdentity:
        """Create a permanent Player ID and five empty slots atomically."""

        if not isinstance(display_name, str) or not PLAYER_NAME_PATTERN.fullmatch(
            display_name
        ):
            raise PublicIdentityError(
                "invalidPlayerName", "Player Name must be 3–20 ASCII letters, numbers, or underscores.", 422
            )
        instant = self._instant()
        with self._write() as connection:
            code, mac = self._unused_code(connection)
            player_id = uuid.uuid4().hex
            connection.execute(
                """INSERT INTO players
                   (player_id, display_name, recovery_mac, recovery_key_version,
                    recovery_issued_at, recovery_confirmed_at,
                    session_generation, created_at)
                   VALUES (?, ?, ?, ?, ?, NULL, 1, ?)""",
                (
                    player_id,
                    display_name,
                    mac,
                    self.key_version,
                    self._stamp(instant),
                    self._stamp(instant),
                ),
            )
            connection.executemany(
                "INSERT INTO player_save_slots(player_id, slot_id) VALUES (?, ?)",
                [(player_id, slot_id) for slot_id in range(1, 6)],
            )
            connection.execute(
                "INSERT INTO player_active_slots(player_id, slot_id) VALUES (?, NULL)",
                (player_id,),
            )
            return self._insert_session(
                connection,
                player_id=player_id,
                display_name=display_name,
                generation=1,
                recovery_confirmed=False,
                instant=instant,
                recovery_code=code,
            )

    def _failed_recovery(
        self,
        connection: sqlite3.Connection,
        *,
        ip_macs: list[bytes],
        instant: datetime,
    ) -> None:
        connection.execute(
            "INSERT INTO recovery_ip_attempts(ip_mac, attempted_at) VALUES (?, ?)",
            (ip_macs[0], self._stamp(instant)),
        )
        placeholders = ",".join("?" for _ in ip_macs)
        failures = connection.execute(
            f"SELECT COUNT(*) AS n FROM recovery_ip_attempts WHERE ip_mac IN ({placeholders})",
            tuple(ip_macs),
        ).fetchone()["n"]
        if failures >= MAX_RECOVERY_FAILURES:
            connection.execute(
                """INSERT INTO recovery_ip_blocks(ip_mac, blocked_until)
                   VALUES (?, ?)
                   ON CONFLICT(ip_mac) DO UPDATE SET blocked_until = excluded.blocked_until""",
                (ip_macs[0], self._stamp(instant + RECOVERY_BLOCK)),
            )

    def recover(self, recovery_code: str, client_ip: str) -> IssuedIdentity:
        """Recover by code alone and revoke the former device in one transaction."""

        try:
            normalized_ip = _canonical_ip(client_ip)
        except ValueError as exc:
            raise PublicIdentityError(
                "invalidClientAddress", "The client address could not be verified.", 400
            ) from exc
        instant = self._instant()
        ip_macs = [
            self._mac(key, "recovery-ip", normalized_ip)
            for key in self.rate_limit_keys
        ]
        normalized = self._normalize_code(recovery_code)
        candidates = [
            (version, self._mac(key, "recovery-code", normalized or "invalid"))
            for version, key in self.keys.items()
        ]
        failure: PublicIdentityError | None = None
        issued: IssuedIdentity | None = None
        with self._write() as connection:
            cutoff = self._stamp(instant - RECOVERY_WINDOW)
            connection.execute(
                "DELETE FROM recovery_ip_attempts WHERE attempted_at <= ?", (cutoff,)
            )
            placeholders = ",".join("?" for _ in ip_macs)
            block = connection.execute(
                f"""SELECT MAX(blocked_until) AS blocked_until
                    FROM recovery_ip_blocks WHERE ip_mac IN ({placeholders})""",
                tuple(ip_macs),
            ).fetchone()
            if block["blocked_until"] is not None and self._parse(block["blocked_until"]) > instant:
                failure = PublicIdentityError(
                    "recoveryRateLimited", "Recovery is temporarily unavailable. Try again later.", 429
                )
            else:
                if block["blocked_until"] is not None:
                    connection.execute(
                        f"DELETE FROM recovery_ip_blocks WHERE ip_mac IN ({placeholders})",
                        tuple(ip_macs),
                    )
                placeholders = ",".join("?" for _ in candidates)
                row = connection.execute(
                    f"""SELECT player_id, display_name, recovery_mac,
                               recovery_key_version, recovery_confirmed_at,
                               session_generation
                        FROM players WHERE recovery_mac IN ({placeholders})""",
                    tuple(mac for _, mac in candidates),
                ).fetchone()
                matched = (
                    normalized is not None
                    and row is not None
                    and any(
                        version == row["recovery_key_version"]
                        and hmac.compare_digest(mac, row["recovery_mac"])
                        for version, mac in candidates
                    )
                )
                if not matched:
                    # Keep the failure shape independent of whether the code
                    # was malformed or simply unknown.
                    hmac.compare_digest(candidates[0][1], bytes(32))
                    self._failed_recovery(connection, ip_macs=ip_macs, instant=instant)
                    failure = PublicIdentityError(
                        "recoveryInvalid", "Recovery Code could not be verified.", 401
                    )
                else:
                    assert row is not None
                    player_id = row["player_id"]
                    generation = row["session_generation"] + 1
                    connection.execute(
                        "UPDATE player_sessions SET revoked_at = ? WHERE player_id = ? AND revoked_at IS NULL",
                        (self._stamp(instant), player_id),
                    )
                    connection.execute(
                        "UPDATE players SET session_generation = ? WHERE player_id = ?",
                        (generation, player_id),
                    )
                    issued = self._insert_session(
                        connection,
                        player_id=player_id,
                        display_name=row["display_name"],
                        generation=generation,
                        recovery_confirmed=row["recovery_confirmed_at"] is not None,
                        instant=instant,
                        recovery_code=None,
                    )
        if failure is not None:
            raise failure
        assert issued is not None
        return issued

    def validate_session(
        self,
        token: str | None,
        *,
        touch: bool = False,
        rotate: bool = False,
        require_confirmed: bool = True,
        csrf_token: str | None = None,
        require_csrf: bool = False,
    ) -> AuthenticatedSession:
        """Validate a cookie; unsafe callers may opt into sliding/rotation.

        A previous token is accepted for 60 seconds only to let in-flight
        same-device requests finish. It is never rotated or issued again.
        Recovery/logout revocation invalidates both verifiers immediately.
        Read-only callers leave expiry, last-seen, and tokens unchanged even
        if ``rotate`` is requested; ``touch=True`` is required for renewal.
        """

        if not token or not isinstance(token, str) or len(token) > 256:
            raise PublicIdentityError(
                "sessionRequired", "A valid player session is required.", 401
            )
        instant = self._instant()
        candidates = [
            (version, key, self._mac(key, "session-token", token))
            for version, key in self.keys.items()
        ]
        placeholders = ",".join("?" for _ in candidates)
        with (self._write() if touch else self._read()) as connection:
            row = connection.execute(
                f"""SELECT s.*, p.display_name, p.recovery_confirmed_at,
                           p.session_generation
                    FROM player_sessions s JOIN players p ON p.player_id = s.player_id
                    WHERE s.token_mac IN ({placeholders})
                       OR s.previous_token_mac IN ({placeholders})""",
                tuple(mac for _, _, mac in candidates) * 2,
            ).fetchone()
            if row is None or row["revoked_at"] is not None:
                raise PublicIdentityError(
                    "sessionRequired", "A valid player session is required.", 401
                )
            if row["generation"] != row["session_generation"]:
                raise PublicIdentityError(
                    "sessionRevoked", "This player session is no longer active.", 401
                )
            if self._parse(row["expires_at"]) <= instant:
                raise PublicIdentityError(
                    "sessionExpired", "This player session has expired.", 401
                )
            matched_key: bytes | None = None
            is_current = False
            for _, key, mac in candidates:
                if hmac.compare_digest(mac, row["token_mac"]):
                    matched_key = key
                    is_current = True
                    break
                if (
                    row["previous_token_mac"] is not None
                    and hmac.compare_digest(mac, row["previous_token_mac"])
                    and row["previous_token_valid_until"] is not None
                    and self._parse(row["previous_token_valid_until"]) > instant
                ):
                    matched_key = key
                    break
            if matched_key is None:
                raise PublicIdentityError(
                    "sessionRequired", "A valid player session is required.", 401
                )
            confirmed = row["recovery_confirmed_at"] is not None
            if require_confirmed and not confirmed:
                raise PublicIdentityError(
                    "recoveryConfirmationRequired",
                    "Confirm that you saved your Recovery Code first.",
                    403,
                )
            csrf = self._csrf(row["session_id"], matched_key)
            if is_current and not hmac.compare_digest(
                self._mac(matched_key, "csrf-verifier", csrf), row["csrf_mac"]
            ):
                raise PublicIdentityError(
                    "sessionRequired", "A valid player session is required.", 401
                )
            if require_csrf and (
                csrf_token is None
                or len(csrf_token) != 64
                or not hmac.compare_digest(csrf, csrf_token)
            ):
                # Reject before sliding the session: a forged unsafe request
                # must not keep an otherwise idle device signed in.
                raise PublicIdentityError(
                    "csrfInvalid", "The request verification token is invalid.", 403
                )
            rotated_token: str | None = None
            if touch and is_current and rotate and instant - self._parse(row["issued_at"]) >= ROTATE_AFTER:
                rotated_token = self._new_token()
                previous_mac = row["token_mac"]
                csrf = self._csrf(row["session_id"], self.keys[self.key_version])
                connection.execute(
                    """UPDATE player_sessions SET token_mac = ?, previous_token_mac = ?,
                           previous_token_valid_until = ?, csrf_mac = ?, issued_at = ?
                       WHERE session_id = ?""",
                    (
                        self._current_mac("session-token", rotated_token),
                        previous_mac,
                        self._stamp(instant + PREVIOUS_TOKEN_GRACE),
                        self._current_mac("csrf-verifier", csrf),
                        self._stamp(instant),
                        row["session_id"],
                    ),
                )
            expires_at = row["expires_at"]
            if touch:
                expires_at = self._stamp(instant + timedelta(days=SESSION_DAYS))
                connection.execute(
                    "UPDATE player_sessions SET last_seen_at = ?, expires_at = ? WHERE session_id = ?",
                    (self._stamp(instant), expires_at, row["session_id"]),
                )
            return AuthenticatedSession(
                player_id=row["player_id"],
                display_name=row["display_name"],
                session_id=row["session_id"],
                generation=row["generation"],
                csrf_token=csrf,
                expires_at=expires_at,
                recovery_confirmed=confirmed,
                rotated_token=rotated_token,
            )

    @staticmethod
    def verify_csrf(session: AuthenticatedSession, supplied_token: str | None) -> None:
        if not supplied_token or len(supplied_token) != 64 or not hmac.compare_digest(
            session.csrf_token, supplied_token
        ):
            raise PublicIdentityError(
                "csrfInvalid", "The request verification token is invalid.", 403
            )

    def assert_current_session(
        self,
        connection: sqlite3.Connection,
        session: AuthenticatedSession,
        *,
        require_confirmed: bool = True,
    ) -> None:
        """Recheck Player/session ownership inside a caller's write transaction."""

        row = connection.execute(
            """SELECT s.player_id, s.generation, s.expires_at, s.revoked_at,
                      p.session_generation, p.recovery_confirmed_at
               FROM player_sessions s JOIN players p ON p.player_id = s.player_id
               WHERE s.session_id = ?""",
            (session.session_id,),
        ).fetchone()
        if (
            row is None
            or row["player_id"] != session.player_id
            or row["generation"] != session.generation
            or row["session_generation"] != session.generation
            or row["revoked_at"] is not None
        ):
            raise PublicIdentityError(
                "sessionRevoked", "This player session is no longer active.", 401
            )
        if self._parse(row["expires_at"]) <= self._instant():
            raise PublicIdentityError(
                "sessionExpired", "This player session has expired.", 401
            )
        if require_confirmed and row["recovery_confirmed_at"] is None:
            raise PublicIdentityError(
                "recoveryConfirmationRequired",
                "Confirm that you saved your Recovery Code first.",
                403,
            )

    def acknowledge(self, session: AuthenticatedSession) -> AuthenticatedSession:
        instant = self._instant()
        with self._write() as connection:
            self.assert_current_session(connection, session, require_confirmed=False)
            connection.execute(
                """UPDATE players SET recovery_confirmed_at = ?
                   WHERE player_id = ? AND recovery_confirmed_at IS NULL""",
                (self._stamp(instant), session.player_id),
            )
        return replace(session, recovery_confirmed=True)

    def replace_code(self, session: AuthenticatedSession) -> str:
        """Immediately invalidate the old code; disclose its replacement once."""

        instant = self._instant()
        with self._write() as connection:
            self.assert_current_session(connection, session, require_confirmed=False)
            code, mac = self._unused_code(connection)
            connection.execute(
                """UPDATE players SET recovery_mac = ?, recovery_key_version = ?,
                      recovery_issued_at = ?, recovery_confirmed_at = NULL
                   WHERE player_id = ?""",
                (mac, self.key_version, self._stamp(instant), session.player_id),
            )
        return code

    def logout(self, session: AuthenticatedSession) -> None:
        instant = self._instant()
        with self._write() as connection:
            self.assert_current_session(connection, session, require_confirmed=False)
            connection.execute(
                "UPDATE player_sessions SET revoked_at = ? WHERE session_id = ?",
                (self._stamp(instant), session.session_id),
            )
            connection.execute(
                "UPDATE players SET session_generation = session_generation + 1 WHERE player_id = ?",
                (session.player_id,),
            )
