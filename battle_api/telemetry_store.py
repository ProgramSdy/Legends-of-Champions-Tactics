"""Small additive, best-effort Public telemetry sidecar.

Canonical identity, battle outcome, rewards, and saves remain owned by the
existing progression store.  This module records only facts absent from those
tables, after canonical commits.  Every public method is bounded and swallows
SQLite failures so telemetry can never change a gameplay response.
"""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta
import json
import sqlite3
import threading
import time
from typing import Any, Callable, Mapping, Sequence

from .models import TelemetryEventRequest
from .progression import ProgressionStore


TELEMETRY_SCHEMA_REVISION = 1
ANALYTICS_SESSION_TIMEOUT = timedelta(minutes=30)
ACTIVITY_THROTTLE = timedelta(minutes=5)
CLIENT_ERROR_SESSION_CAP = 5
EVENT_SESSION_CAP = 16
API_METRIC_FLUSH_COUNT = 100
API_METRIC_FLUSH_SECONDS = 30.0
API_METRIC_MAX_KEYS = 256

TELEMETRY_TABLES = frozenset(
    {
        "telemetry_visitors",
        "telemetry_sessions",
        "telemetry_battles",
        "telemetry_events",
        "telemetry_internal_accounts",
        "telemetry_api_metrics",
    }
)


class TelemetrySchemaError(RuntimeError):
    """The optional telemetry schema is absent or incompatible."""


def create_telemetry_schema(connection: sqlite3.Connection) -> None:
    """Add the revision-1 telemetry sidecar inside the caller's transaction."""

    marker = connection.execute(
        "SELECT value FROM metadata WHERE key = 'telemetry_schema_revision'"
    ).fetchone()
    if marker is not None:
        if marker[0] != str(TELEMETRY_SCHEMA_REVISION):
            raise TelemetrySchemaError("Telemetry schema revision is unsupported.")
        validate_telemetry_schema(connection)
        return

    statements = (
        """
        CREATE TABLE telemetry_visitors (
            visitor_id TEXT PRIMARY KEY,
            first_seen_at TEXT NOT NULL,
            first_source TEXT NOT NULL CHECK (
                first_source IN (
                    'itch.io', 'reddit', 'x', 'threads', 'taptap',
                    'direct', 'other', 'unknown'
                )
            ),
            first_campaign TEXT CHECK (
                first_campaign IS NULL OR length(first_campaign) BETWEEN 1 AND 64
            ),
            linked_player_id TEXT REFERENCES players(player_id) ON DELETE SET NULL
        )
        """,
        """CREATE INDEX telemetry_visitors_player
            ON telemetry_visitors(linked_player_id, first_seen_at)""",
        """
        CREATE TABLE telemetry_sessions (
            session_id TEXT PRIMARY KEY,
            visitor_id TEXT NOT NULL
                REFERENCES telemetry_visitors(visitor_id) ON DELETE CASCADE,
            player_id TEXT REFERENCES players(player_id) ON DELETE SET NULL,
            started_at TEXT NOT NULL,
            last_activity_at TEXT NOT NULL,
            session_source TEXT NOT NULL CHECK (
                session_source IN (
                    'itch.io', 'reddit', 'x', 'threads', 'taptap',
                    'direct', 'other', 'unknown'
                )
            ),
            game_version TEXT NOT NULL CHECK (length(game_version) BETWEEN 1 AND 128),
            environment TEXT NOT NULL CHECK (environment IN ('development', 'public'))
        )
        """,
        """CREATE INDEX telemetry_sessions_player_activity
            ON telemetry_sessions(player_id, last_activity_at)""",
        """CREATE INDEX telemetry_sessions_visitor_activity
            ON telemetry_sessions(visitor_id, last_activity_at)""",
        """
        CREATE TABLE telemetry_battles (
            battle_id TEXT PRIMARY KEY
                REFERENCES battle_diagnostics(battle_id) ON DELETE CASCADE,
            player_id TEXT NOT NULL REFERENCES players(player_id),
            activated_at TEXT NOT NULL,
            mode TEXT NOT NULL CHECK (length(mode) BETWEEN 1 AND 32),
            encounter_id TEXT NOT NULL CHECK (length(encounter_id) BETWEEN 1 AND 128),
            stage_id TEXT CHECK (stage_id IS NULL OR length(stage_id) <= 64),
            attempt_id TEXT CHECK (attempt_id IS NULL OR length(attempt_id) <= 128),
            player_team_json TEXT NOT NULL CHECK (length(player_team_json) <= 1024),
            enemy_team_json TEXT NOT NULL CHECK (length(enemy_team_json) <= 1024),
            player_formation TEXT CHECK (
                player_formation IS NULL OR length(player_formation) <= 64
            ),
            enemy_formation TEXT CHECK (
                enemy_formation IS NULL OR length(enemy_formation) <= 64
            ),
            available_roster_json TEXT NOT NULL
                CHECK (length(available_roster_json) <= 4096),
            control_mode TEXT NOT NULL CHECK (length(control_mode) BETWEEN 1 AND 32),
            ruleset_version TEXT NOT NULL CHECK (length(ruleset_version) BETWEEN 1 AND 128),
            completed_rounds INTEGER CHECK (completed_rounds IS NULL OR completed_rounds >= 0)
        )
        """,
        """CREATE INDEX telemetry_battles_player_activated
            ON telemetry_battles(player_id, activated_at)""",
        """CREATE INDEX telemetry_battles_encounter_activated
            ON telemetry_battles(encounter_id, activated_at)""",
        """
        CREATE TABLE telemetry_events (
            event_id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL CHECK (
                event_type IN (
                    'landing_view', 'home_view', 'session_activity', 'client_error'
                )
            ),
            schema_version INTEGER NOT NULL CHECK (schema_version = 1),
            timestamp_utc TEXT NOT NULL,
            occurred_at_utc TEXT,
            player_id TEXT REFERENCES players(player_id) ON DELETE SET NULL,
            visitor_id TEXT NOT NULL
                REFERENCES telemetry_visitors(visitor_id) ON DELETE CASCADE,
            session_id TEXT NOT NULL
                REFERENCES telemetry_sessions(session_id) ON DELETE CASCADE,
            battle_id TEXT REFERENCES battle_diagnostics(battle_id) ON DELETE SET NULL,
            producer TEXT NOT NULL CHECK (producer = 'ui'),
            environment TEXT NOT NULL CHECK (environment IN ('development', 'public')),
            game_version TEXT NOT NULL CHECK (length(game_version) BETWEEN 1 AND 128),
            event_data_json TEXT NOT NULL CHECK (length(event_data_json) <= 512)
        )
        """,
        """CREATE INDEX telemetry_events_type_time
            ON telemetry_events(event_type, timestamp_utc)""",
        """CREATE INDEX telemetry_events_player_time
            ON telemetry_events(player_id, timestamp_utc)""",
        """CREATE INDEX telemetry_events_session_time
            ON telemetry_events(session_id, timestamp_utc)""",
        """CREATE UNIQUE INDEX telemetry_one_landing_per_session
            ON telemetry_events(session_id, event_type)
            WHERE event_type = 'landing_view'""",
        """CREATE UNIQUE INDEX telemetry_one_home_per_session
            ON telemetry_events(session_id, event_type)
            WHERE event_type = 'home_view'""",
        """
        CREATE TABLE telemetry_internal_accounts (
            player_id TEXT PRIMARY KEY REFERENCES players(player_id) ON DELETE CASCADE,
            classification TEXT NOT NULL CHECK (
                classification IN ('load_test', 'owner_test', 'automation')
            ),
            created_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE telemetry_api_metrics (
            bucket_utc TEXT NOT NULL,
            route_id TEXT NOT NULL CHECK (length(route_id) BETWEEN 1 AND 128),
            status_class TEXT NOT NULL CHECK (
                status_class IN ('2xx', '3xx', '4xx', '5xx', 'exception')
            ),
            request_count INTEGER NOT NULL CHECK (request_count >= 0),
            failed_count INTEGER NOT NULL CHECK (
                failed_count >= 0 AND failed_count <= request_count
            ),
            latency_le_100_ms INTEGER NOT NULL CHECK (latency_le_100_ms >= 0),
            latency_le_250_ms INTEGER NOT NULL CHECK (latency_le_250_ms >= 0),
            latency_le_500_ms INTEGER NOT NULL CHECK (latency_le_500_ms >= 0),
            latency_le_1000_ms INTEGER NOT NULL CHECK (latency_le_1000_ms >= 0),
            latency_le_2000_ms INTEGER NOT NULL CHECK (latency_le_2000_ms >= 0),
            latency_gt_2000_ms INTEGER NOT NULL CHECK (latency_gt_2000_ms >= 0),
            latency_sum_ms REAL NOT NULL CHECK (latency_sum_ms >= 0),
            PRIMARY KEY (bucket_utc, route_id, status_class),
            CHECK (
                latency_le_100_ms + latency_le_250_ms + latency_le_500_ms +
                latency_le_1000_ms + latency_le_2000_ms + latency_gt_2000_ms =
                request_count
            )
        )
        """,
        """CREATE INDEX telemetry_api_metrics_route_time
            ON telemetry_api_metrics(route_id, bucket_utc)""",
        """INSERT INTO metadata(key, value)
            VALUES ('telemetry_schema_revision', '1')""",
    )
    for statement in statements:
        connection.execute(statement)
    validate_telemetry_schema(connection)


def validate_telemetry_schema(connection: sqlite3.Connection) -> None:
    marker = connection.execute(
        "SELECT value FROM metadata WHERE key = 'telemetry_schema_revision'"
    ).fetchone()
    if marker is None or marker[0] != str(TELEMETRY_SCHEMA_REVISION):
        raise TelemetrySchemaError("Telemetry schema revision 1 is required.")
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    if not TELEMETRY_TABLES.issubset(tables):
        raise TelemetrySchemaError("Telemetry schema is incomplete.")


class TelemetryStore:
    """Best-effort bounded writer sharing the Public SQLite database."""

    def __init__(
        self,
        progression_store: ProgressionStore,
        *,
        enabled: bool,
        environment: str,
        game_version: str,
        ruleset_version: str,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        if not progression_store.public_mode:
            raise ValueError("Telemetry requires the Public progression store.")
        if environment not in {"development", "public"}:
            raise ValueError("Telemetry environment must be development or public.")
        self.progression_store = progression_store
        self.enabled = enabled
        self.environment = environment
        self.game_version = game_version[:128]
        self.ruleset_version = ruleset_version[:128]
        self._now = now or (lambda: datetime.now(UTC))
        self._failures: Counter[str] = Counter()
        self._failure_lock = threading.Lock()
        self._api_metrics: dict[tuple[str, str, str], list[float]] = {}
        self._api_metric_lock = threading.Lock()
        self._api_metric_count = 0
        self._last_api_flush = time.monotonic()

    def _instant(self) -> datetime:
        instant = self._now()
        if instant.tzinfo is None:
            raise ValueError("Telemetry clock must be timezone-aware.")
        return instant.astimezone(UTC)

    @staticmethod
    def _stamp(instant: datetime) -> str:
        return instant.astimezone(UTC).isoformat(timespec="microseconds").replace(
            "+00:00", "Z"
        )

    @staticmethod
    def _parse(stamp: str) -> datetime:
        return datetime.fromisoformat(stamp.replace("Z", "+00:00")).astimezone(UTC)

    @staticmethod
    def _json(value: object, *, maximum: int) -> str:
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"))
        if len(encoded.encode("utf-8")) > maximum:
            raise ValueError("Telemetry payload exceeds its bounded size.")
        return encoded

    def _count_failure(self, operation: str) -> None:
        with self._failure_lock:
            self._failures[operation] += 1

    def failure_counts(self) -> Mapping[str, int]:
        with self._failure_lock:
            return dict(self._failures)

    def note_failure(self, operation: str) -> None:
        """Expose a bounded counter for failures caught outside this store."""

        self._count_failure(operation[:64])

    def record_api_request(
        self,
        *,
        route_id: str,
        status_code: int | None,
        latency_ms: float,
    ) -> None:
        """Aggregate one request in memory and occasionally flush one batch."""

        if not self.enabled:
            return
        try:
            now = self._instant()
            bucket = now.replace(second=0, microsecond=0)
            bucket_text = self._stamp(bucket)
            normalized_route = route_id[:128] or "unmatched"
            status_class = (
                "exception"
                if status_code is None
                else f"{min(max(status_code // 100, 2), 5)}xx"
            )
            latency = max(float(latency_ms), 0.0)
            with self._api_metric_lock:
                key = (bucket_text, normalized_route, status_class)
                if key not in self._api_metrics and len(self._api_metrics) >= API_METRIC_MAX_KEYS:
                    key = (bucket_text, "__other__", status_class)
                values = self._api_metrics.setdefault(key, [0.0] * 9)
                values[0] += 1
                # KPI numerator is every unsuccessful HTTP result.  Status
                # class remains available so reports can separate expected
                # client rejection (4xx) from service failure (5xx/exception).
                values[1] += int(status_code is None or status_code >= 400)
                if latency <= 100:
                    values[2] += 1
                elif latency <= 250:
                    values[3] += 1
                elif latency <= 500:
                    values[4] += 1
                elif latency <= 1000:
                    values[5] += 1
                elif latency <= 2000:
                    values[6] += 1
                else:
                    values[7] += 1
                values[8] += latency
                self._api_metric_count += 1
                due = (
                    self._api_metric_count >= API_METRIC_FLUSH_COUNT
                    or time.monotonic() - self._last_api_flush >= API_METRIC_FLUSH_SECONDS
                )
            if due:
                self.flush_api_metrics()
        except (OSError, sqlite3.Error, TelemetrySchemaError, ValueError):
            self._count_failure("api_metric")

    def flush_api_metrics(self) -> bool:
        """Atomically flush the current aggregate batch, restoring it on failure."""

        if not self.enabled:
            return False
        with self._api_metric_lock:
            if not self._api_metrics:
                return True
            pending = self._api_metrics
            self._api_metrics = {}
            self._api_metric_count = 0
            self._last_api_flush = time.monotonic()
        try:
            connection = self.progression_store._connection()
            try:
                connection.execute("PRAGMA busy_timeout = 250")
                connection.execute("BEGIN IMMEDIATE")
                validate_telemetry_schema(connection)
                for (bucket, route, status_class), values in pending.items():
                    connection.execute(
                        """INSERT INTO telemetry_api_metrics(
                               bucket_utc, route_id, status_class,
                               request_count, failed_count,
                               latency_le_100_ms, latency_le_250_ms,
                               latency_le_500_ms, latency_le_1000_ms,
                               latency_le_2000_ms, latency_gt_2000_ms,
                               latency_sum_ms
                           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                           ON CONFLICT(bucket_utc, route_id, status_class) DO UPDATE SET
                               request_count = request_count + excluded.request_count,
                               failed_count = failed_count + excluded.failed_count,
                               latency_le_100_ms = latency_le_100_ms + excluded.latency_le_100_ms,
                               latency_le_250_ms = latency_le_250_ms + excluded.latency_le_250_ms,
                               latency_le_500_ms = latency_le_500_ms + excluded.latency_le_500_ms,
                               latency_le_1000_ms = latency_le_1000_ms + excluded.latency_le_1000_ms,
                               latency_le_2000_ms = latency_le_2000_ms + excluded.latency_le_2000_ms,
                               latency_gt_2000_ms = latency_gt_2000_ms + excluded.latency_gt_2000_ms,
                               latency_sum_ms = latency_sum_ms + excluded.latency_sum_ms""",
                        (bucket, route, status_class, *values),
                    )
                connection.commit()
            except BaseException:
                connection.rollback()
                raise
            finally:
                connection.close()
            return True
        except (OSError, sqlite3.Error, TelemetrySchemaError, ValueError):
            self._count_failure("api_metric_flush")
            with self._api_metric_lock:
                for key, values in pending.items():
                    current = self._api_metrics.setdefault(key, [0.0] * 9)
                    for index, value in enumerate(values):
                        current[index] += value
                    self._api_metric_count += int(values[0])
            return False

    def ensure_initialized(self) -> None:
        if not self.enabled:
            return
        connection = self.progression_store._connection()
        try:
            validate_telemetry_schema(connection)
        finally:
            connection.close()

    def record_client_event(
        self,
        event: TelemetryEventRequest,
        *,
        player_id: str | None,
    ) -> dict[str, Any]:
        if not self.enabled:
            return {"accepted": False, "duplicate": False, "reason": "unavailable"}
        try:
            return self._record_client_event(event, player_id=player_id)
        except (OSError, sqlite3.Error, TelemetrySchemaError, ValueError):
            self._count_failure("client_event")
            return {"accepted": False, "duplicate": False, "reason": "unavailable"}

    def _record_client_event(
        self,
        event: TelemetryEventRequest,
        *,
        player_id: str | None,
    ) -> dict[str, Any]:
        now = self._instant()
        now_text = self._stamp(now)
        visitor_id = str(event.visitor_id)
        session_id = str(event.session_id)
        event_id = str(event.event_id)
        data = event.event_data.model_dump(by_alias=True, mode="json")
        data_json = self._json(data, maximum=512)
        source = data.get("source", "unknown")
        campaign = data.get("campaign")
        occurred = (
            self._stamp(event.occurred_at_utc)
            if event.occurred_at_utc is not None
            else None
        )

        connection = self.progression_store._connection()
        try:
            connection.execute("PRAGMA busy_timeout = 250")
            connection.execute("BEGIN IMMEDIATE")
            validate_telemetry_schema(connection)
            if connection.execute(
                "SELECT 1 FROM telemetry_events WHERE event_id = ?", (event_id,)
            ).fetchone() is not None:
                connection.commit()
                return {"accepted": True, "duplicate": True, "reason": None}

            connection.execute(
                """INSERT OR IGNORE INTO telemetry_visitors(
                       visitor_id, first_seen_at, first_source, first_campaign,
                       linked_player_id
                   ) VALUES (?, ?, ?, ?, ?)""",
                (visitor_id, now_text, source, campaign, player_id),
            )
            visitor = connection.execute(
                "SELECT linked_player_id FROM telemetry_visitors WHERE visitor_id = ?",
                (visitor_id,),
            ).fetchone()
            if visitor is None:
                raise TelemetrySchemaError("Telemetry visitor could not be stored.")
            if visitor["linked_player_id"] is None and player_id is not None:
                connection.execute(
                    "UPDATE telemetry_visitors SET linked_player_id = ? WHERE visitor_id = ?",
                    (player_id, visitor_id),
                )
            elif (
                player_id is not None
                and visitor["linked_player_id"] not in {None, player_id}
            ):
                # A browser identifier already linked to another player must not
                # silently merge account cohorts.
                player_id = None
            if event.event_type == "landing_view" and source != "unknown":
                connection.execute(
                    """UPDATE telemetry_visitors
                       SET first_source = ?, first_campaign = COALESCE(first_campaign, ?)
                       WHERE visitor_id = ? AND first_source = 'unknown'""",
                    (source, campaign, visitor_id),
                )

            session = connection.execute(
                "SELECT * FROM telemetry_sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
            if session is None:
                connection.execute(
                    """INSERT INTO telemetry_sessions(
                           session_id, visitor_id, player_id, started_at,
                           last_activity_at, session_source, game_version, environment
                       ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        session_id, visitor_id, player_id, now_text, now_text,
                        source, self.game_version, self.environment,
                    ),
                )
            else:
                if session["visitor_id"] != visitor_id:
                    raise ValueError("Analytics session is bound to another visitor.")
                if now - self._parse(session["last_activity_at"]) >= ANALYTICS_SESSION_TIMEOUT:
                    connection.commit()
                    return {
                        "accepted": False,
                        "duplicate": False,
                        "reason": "sessionExpired",
                    }
                if session["player_id"] is None and player_id is not None:
                    connection.execute(
                        "UPDATE telemetry_sessions SET player_id = ? WHERE session_id = ?",
                        (player_id, session_id),
                    )
                elif player_id is not None and session["player_id"] not in {None, player_id}:
                    player_id = None
                if event.event_type == "landing_view" and source != "unknown":
                    connection.execute(
                        """UPDATE telemetry_sessions SET session_source = ?
                           WHERE session_id = ? AND session_source = 'unknown'""",
                        (source, session_id),
                    )

            count = connection.execute(
                "SELECT COUNT(*) FROM telemetry_events WHERE session_id = ?",
                (session_id,),
            ).fetchone()[0]
            if count >= EVENT_SESSION_CAP:
                connection.commit()
                return {
                    "accepted": False,
                    "duplicate": False,
                    "reason": "sessionCapReached",
                }
            if event.event_type in {"landing_view", "home_view"} and connection.execute(
                "SELECT 1 FROM telemetry_events WHERE session_id = ? AND event_type = ?",
                (session_id, event.event_type),
            ).fetchone() is not None:
                connection.commit()
                return {"accepted": True, "duplicate": True, "reason": None}
            if event.event_type == "session_activity":
                prior = connection.execute(
                    """SELECT timestamp_utc FROM telemetry_events
                       WHERE session_id = ? AND event_type = 'session_activity'
                       ORDER BY timestamp_utc DESC LIMIT 1""",
                    (session_id,),
                ).fetchone()
                if prior is not None and now - self._parse(prior[0]) < ACTIVITY_THROTTLE:
                    connection.commit()
                    return {
                        "accepted": False,
                        "duplicate": False,
                        "reason": "throttled",
                    }
            if event.event_type == "client_error":
                errors = connection.execute(
                    """SELECT COUNT(*) FROM telemetry_events
                       WHERE session_id = ? AND event_type = 'client_error'""",
                    (session_id,),
                ).fetchone()[0]
                if errors >= CLIENT_ERROR_SESSION_CAP:
                    connection.commit()
                    return {
                        "accepted": False,
                        "duplicate": False,
                        "reason": "sessionCapReached",
                    }

            connection.execute(
                """INSERT INTO telemetry_events(
                       event_id, event_type, schema_version, timestamp_utc,
                       occurred_at_utc, player_id, visitor_id, session_id,
                       battle_id, producer, environment, game_version,
                       event_data_json
                   ) VALUES (?, ?, 1, ?, ?, ?, ?, ?, NULL, 'ui', ?, ?, ?)""",
                (
                    event_id, event.event_type, now_text, occurred, player_id,
                    visitor_id, session_id, self.environment, self.game_version,
                    data_json,
                ),
            )
            connection.execute(
                "UPDATE telemetry_sessions SET last_activity_at = ? WHERE session_id = ?",
                (now_text, session_id),
            )
            connection.commit()
            return {"accepted": True, "duplicate": False, "reason": None}
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def record_battle_started(self, **facts: Any) -> bool:
        if not self.enabled:
            return False
        try:
            self._record_battle_started(**facts)
            return True
        except (OSError, sqlite3.Error, TelemetrySchemaError, ValueError, TypeError):
            self._count_failure("battle_started")
            return False

    def _record_battle_started(
        self,
        *,
        battle_id: str,
        player_id: str,
        mode: str,
        encounter_id: str,
        stage_id: str | None,
        attempt_id: str | None,
        player_team: Sequence[str],
        enemy_team: Sequence[str],
        player_formation: str | None,
        enemy_formation: str | None,
        available_roster: Sequence[str],
        control_mode: str,
    ) -> None:
        activated_at = self._stamp(self._instant())
        values = (
            battle_id,
            player_id,
            activated_at,
            mode,
            encounter_id,
            stage_id,
            attempt_id,
            self._json(list(player_team), maximum=1024),
            self._json(list(enemy_team), maximum=1024),
            player_formation,
            enemy_formation,
            self._json(sorted(set(available_roster)), maximum=4096),
            control_mode,
            self.ruleset_version,
        )
        connection = self.progression_store._connection()
        try:
            connection.execute("PRAGMA busy_timeout = 250")
            connection.execute("BEGIN IMMEDIATE")
            validate_telemetry_schema(connection)
            cursor = connection.execute(
                """INSERT OR IGNORE INTO telemetry_battles(
                       battle_id, player_id, activated_at, mode, encounter_id,
                       stage_id, attempt_id, player_team_json, enemy_team_json,
                       player_formation, enemy_formation, available_roster_json,
                       control_mode, ruleset_version, completed_rounds
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)""",
                values,
            )
            if cursor.rowcount == 0:
                existing = connection.execute(
                    """SELECT player_id, mode, encounter_id, stage_id, attempt_id,
                              player_team_json, enemy_team_json, player_formation,
                              enemy_formation, available_roster_json, control_mode,
                              ruleset_version
                       FROM telemetry_battles WHERE battle_id = ?""",
                    (battle_id,),
                ).fetchone()
                if existing is None or tuple(existing) != (
                    player_id,
                    mode,
                    encounter_id,
                    stage_id,
                    attempt_id,
                    values[7],
                    values[8],
                    player_formation,
                    enemy_formation,
                    values[11],
                    control_mode,
                    self.ruleset_version,
                ):
                    raise ValueError(
                        "A telemetry battle ID is bound to different launch facts."
                    )
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def record_battle_rounds(self, battle_id: str, completed_rounds: int) -> bool:
        if not self.enabled:
            return False
        try:
            if completed_rounds < 0:
                raise ValueError("completed_rounds must be non-negative")
            connection = self.progression_store._connection()
            try:
                connection.execute("PRAGMA busy_timeout = 250")
                connection.execute("BEGIN IMMEDIATE")
                validate_telemetry_schema(connection)
                cursor = connection.execute(
                    """UPDATE telemetry_battles
                       SET completed_rounds = MAX(COALESCE(completed_rounds, 0), ?)
                       WHERE battle_id = ?""",
                    (completed_rounds, battle_id),
                )
                if cursor.rowcount != 1:
                    raise ValueError("Telemetry battle launch facts are missing.")
                connection.commit()
                return True
            except BaseException:
                connection.rollback()
                raise
            finally:
                connection.close()
        except (OSError, sqlite3.Error, TelemetrySchemaError, ValueError):
            self._count_failure("battle_rounds")
            return False
