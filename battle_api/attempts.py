"""Process-local idempotency for player-facing battle launch attempts.

Battle sessions are process-local, so launch idempotency intentionally has the
same lifetime.  A stable client attempt ID can safely retry a lost creation
response without constructing a second session, while a new ID represents a
new player-intended attempt.
"""

from __future__ import annotations

from collections.abc import Callable, Hashable
from copy import deepcopy
from dataclasses import dataclass
import threading
from typing import Any, TypeVar


SessionT = TypeVar("SessionT")
LaunchResult = tuple[SessionT, dict[str, Any]]


class BattleAttemptConflict(ValueError):
    """An attempt ID was reused for a different launch configuration."""


@dataclass(frozen=True)
class _BattleAttempt:
    profile_id: str
    fingerprint: Hashable
    session: Any
    envelope: dict[str, Any]
    player_id: str | None = None
    session_generation: int | None = None


class BattleAttemptRegistry:
    """Atomically bind an attempt ID, its owning profile, and one session."""

    def __init__(self) -> None:
        self._attempts: dict[str, _BattleAttempt] = {}
        self._lock = threading.RLock()

    def get_or_create(
        self,
        *,
        profile_id: str,
        attempt_id: str | None,
        fingerprint: Hashable,
        factory: Callable[[], LaunchResult[SessionT]],
    ) -> LaunchResult[SessionT]:
        if attempt_id is None:
            return factory()

        with self._lock:
            existing = self._attempts.get(attempt_id)
            if existing is not None:
                if existing.profile_id != profile_id:
                    raise BattleAttemptConflict(
                        "attemptId is already bound to a different active save profile."
                    )
                if existing.fingerprint != fingerprint:
                    raise BattleAttemptConflict(
                        "attemptId is already bound to a different battle "
                        "launch configuration."
                    )
                return existing.session, deepcopy(existing.envelope)

            session, envelope = factory()
            cached_envelope = deepcopy(envelope)
            self._attempts[attempt_id] = _BattleAttempt(
                profile_id=profile_id,
                fingerprint=fingerprint,
                session=session,
                envelope=cached_envelope,
            )
            return session, deepcopy(cached_envelope)

    def clear(self) -> None:
        """Clear process-local bindings; intended for isolated tests."""

        with self._lock:
            self._attempts.clear()

    def get(
        self,
        *,
        attempt_id: str,
        profile_id: str,
        fingerprint: Hashable,
        player_id: str | None = None,
        session_generation: int | None = None,
    ) -> LaunchResult[Any] | None:
        """Read a binding without running battle construction under this lock."""
        with self._lock:
            existing = self._attempts.get(attempt_id)
            if existing is None:
                return None
            if existing.profile_id != profile_id or existing.player_id != player_id:
                raise BattleAttemptConflict(
                    "attemptId is already bound to a different battle owner."
                )
            if existing.fingerprint != fingerprint:
                raise BattleAttemptConflict(
                    "attemptId is already bound to a different battle launch configuration."
                )
            if (
                existing.session_generation is not None
                and existing.session_generation != session_generation
            ):
                raise BattleAttemptConflict(
                    "attemptId belongs to a revoked player session."
                )
            return existing.session, deepcopy(existing.envelope)

    def bind(
        self,
        *,
        attempt_id: str | None,
        profile_id: str,
        fingerprint: Hashable,
        session: Any,
        envelope: dict[str, Any],
        player_id: str | None = None,
        session_generation: int | None = None,
    ) -> LaunchResult[Any]:
        """Bind only after successful durable activation."""
        if attempt_id is None:
            return session, deepcopy(envelope)
        with self._lock:
            if attempt_id in self._attempts:
                raise BattleAttemptConflict("attemptId is already bound.")
            self._attempts[attempt_id] = _BattleAttempt(
                profile_id=profile_id,
                fingerprint=fingerprint,
                session=session,
                envelope=deepcopy(envelope),
                player_id=player_id,
                session_generation=session_generation,
            )
            return session, deepcopy(envelope)

    def remove_battle(self, battle_id: str) -> None:
        with self._lock:
            self._attempts = {
                attempt_id: attempt
                for attempt_id, attempt in self._attempts.items()
                if getattr(attempt.session, "battle_id", None) != battle_id
            }
