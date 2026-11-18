"""SQLite-backed default-profile progression and static training curricula."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
import random
import secrets
import sqlite3
import threading
from typing import Any, Callable, Literal
from urllib.parse import quote
import uuid


DEFAULT_PROFILE_ID = "profile.local.default"
SCHEMA_VERSION = 4
PUBLIC_SCHEMA_VERSION = 5
PUBLIC_BATTLE_SCHEMA_REVISION = 2
PUBLIC_BATTLE_PROVISIONAL_TTL_SECONDS = 120
PUBLIC_BATTLE_INACTIVITY_SECONDS = 30 * 60
PUBLIC_BATTLE_CAPACITY = 20
ARENA_RUN_SCHEMA_VERSION = 1
ARENA_NODE_COUNT = 12
ARENA_REQUIRED_HERO_COUNT = 6
SAVE_SLOT_IDS = (1, 2, 3, 4, 5)
ITEM_CARD_REWARD_ID = "reward.item-card.basic"
StageId = Literal["paladins-altar", "warriors-barrack"]
StageMode = Literal["learner", "tactics"]
STAGE_DISPLAY_NAMES: dict[StageId, str] = {
    "paladins-altar": "Paladin's Altar",
    "warriors-barrack": "Warrior's Barrack",
}

INITIAL_UNLOCKED_HERO_IDS: tuple[str, ...] = (
    "hero.priest.comprehensiveness",
    "hero.mage.comprehensiveness",
    "hero.warrior.weapon_master",
    "hero.rogue.comprehensiveness",
)
ALL_HERO_IDS = frozenset(INITIAL_UNLOCKED_HERO_IDS) | {
    "hero.priest.discipline",
    "hero.paladin.protection",
    "hero.paladin.retribution",
    "hero.paladin.holy",
    "hero.warrior.berserker",
    "hero.warrior.defence",
}
ARENA_FRONT_HERO_IDS = tuple(sorted(
    hero_id for hero_id in ALL_HERO_IDS
    if hero_id.startswith(("hero.warrior.", "hero.paladin."))
))
ARENA_REAR_HERO_IDS = tuple(sorted(
    hero_id for hero_id in ALL_HERO_IDS
    if hero_id.startswith(("hero.mage.", "hero.rogue.", "hero.priest."))
))


@dataclass(frozen=True)
class StageReward:
    reward_id: str
    kind: Literal["heroUnlock", "itemCard"]
    hero_definition_id: str | None
    notification: str


@dataclass(frozen=True)
class StageBattle:
    stage_id: StageId
    battle_index: int
    battle_size: Literal[1, 2, 3]
    formation: str | None
    enemy_definition_ids: tuple[str, ...]
    reward: StageReward | None = None

    @property
    def battle_id(self) -> str:
        return f"{self.stage_id}.battle-{self.battle_index}"


def _hero_reward(definition_id: str, notification: str) -> StageReward:
    return StageReward(
        reward_id=f"unlock.{definition_id}",
        kind="heroUnlock",
        hero_definition_id=definition_id,
        notification=notification,
    )


STAGE_BATTLES: dict[StageId, tuple[StageBattle, ...]] = {
    "paladins-altar": (
        StageBattle("paladins-altar", 1, 2, "front-rear", (
            "hero.paladin.protection", "hero.mage.comprehensiveness",
        )),
        StageBattle("paladins-altar", 2, 1, None, (
            "hero.paladin.protection",
        )),
        StageBattle("paladins-altar", 3, 3, "two-front-one-rear", (
            "hero.paladin.protection", "hero.warrior.defence",
            "hero.mage.comprehensiveness",
        ), _hero_reward(
            "hero.paladin.protection", "Paladin_Protection is unlocked",
        )),
        StageBattle("paladins-altar", 4, 2, "side-by-side", (
            "hero.paladin.retribution", "hero.warrior.weapon_master",
        )),
        StageBattle("paladins-altar", 5, 1, None, (
            "hero.paladin.retribution",
        )),
        StageBattle("paladins-altar", 6, 3, "two-front-one-rear", (
            "hero.paladin.protection", "hero.paladin.retribution",
            "hero.priest.discipline",
        ), _hero_reward(
            "hero.paladin.retribution", "Paladin_Retribution is unlocked",
        )),
        StageBattle("paladins-altar", 7, 2, "side-by-side", (
            "hero.paladin.holy", "hero.rogue.comprehensiveness",
        )),
        StageBattle("paladins-altar", 8, 1, None, (
            "hero.paladin.holy",
        )),
        StageBattle("paladins-altar", 9, 3, "all-front", (
            "hero.paladin.retribution", "hero.paladin.protection",
            "hero.paladin.holy",
        ), _hero_reward(
            "hero.paladin.holy", "Paladin_Holy is unlocked",
        )),
    ),
    "warriors-barrack": (
        StageBattle("warriors-barrack", 1, 2, "front-rear", (
            "hero.warrior.berserker", "hero.priest.comprehensiveness",
        )),
        StageBattle("warriors-barrack", 2, 1, None, (
            "hero.warrior.berserker",
        )),
        StageBattle("warriors-barrack", 3, 3, "two-front-one-rear", (
            "hero.warrior.berserker", "hero.rogue.comprehensiveness",
            "hero.mage.comprehensiveness",
        ), _hero_reward(
            "hero.warrior.berserker", "Warrior_Baserker is unlocked",
        )),
        StageBattle("warriors-barrack", 4, 2, "side-by-side", (
            "hero.warrior.berserker", "hero.warrior.weapon_master",
        )),
        StageBattle("warriors-barrack", 5, 1, None, (
            "hero.warrior.weapon_master",
        )),
        StageBattle("warriors-barrack", 6, 3, "two-front-one-rear", (
            "hero.warrior.weapon_master", "hero.paladin.retribution",
            "hero.priest.discipline",
        ), StageReward(
            ITEM_CARD_REWARD_ID,
            "itemCard",
            None,
            "You have granted an item card",
        )),
        StageBattle("warriors-barrack", 7, 2, "front-rear", (
            "hero.warrior.defence", "hero.priest.discipline",
        )),
        StageBattle("warriors-barrack", 8, 1, None, (
            "hero.warrior.defence",
        )),
        StageBattle("warriors-barrack", 9, 3, "all-front", (
            "hero.warrior.weapon_master", "hero.warrior.defence",
            "hero.warrior.berserker",
        ), _hero_reward(
            "hero.warrior.defence", "Warrior_Defence is unlocked",
        )),
    ),
}


def hero_unlock_sources() -> dict[str, dict[str, Any]]:
    """Describe starter access and only currently implemented unlock rewards."""
    sources: dict[str, dict[str, Any]] = {
        definition_id: {"kind": "starter"}
        for definition_id in INITIAL_UNLOCKED_HERO_IDS
    }
    for stage_id, battles in STAGE_BATTLES.items():
        for battle in battles:
            reward = battle.reward
            if reward is None or reward.kind != "heroUnlock":
                continue
            if reward.hero_definition_id is None:
                raise RuntimeError("A hero-unlock reward is missing its definition ID.")
            if reward.hero_definition_id in sources:
                raise RuntimeError(
                    f"Duplicate hero unlock source for {reward.hero_definition_id}."
                )
            sources[reward.hero_definition_id] = {
                "kind": "stageReward",
                "stageId": stage_id,
                "stageDisplayName": STAGE_DISPLAY_NAMES[stage_id],
                "battleIndex": battle.battle_index,
            }
    return sources


class ProgressionStoreError(RuntimeError):
    """A retryable failure at the persistent progression boundary."""


class StageAccessError(ValueError):
    """A stage or player-team request conflicts with authoritative progress."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class SaveSlotAccessError(ValueError):
    """A requested save-slot operation conflicts with authoritative state."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class ArenaAccessError(ValueError):
    """An Arena Run request conflicts with backend-owned run state."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class PublicBattleAccessError(ValueError):
    """A Public battle lifecycle request is unauthorized or conflicts."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class ProgressionStore:
    """Transaction-scoped SQLite store for five local save slots."""

    def __init__(
        self,
        database_path: Path,
        *,
        public_mode: bool = False,
        allow_public_initialize: bool = False,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self.database_path = database_path
        self.public_mode = public_mode
        self.allow_public_initialize = allow_public_initialize
        self._now = now or (lambda: datetime.now(UTC))
        self._initialize_lock = threading.Lock()
        self._initialized = False

    def _connect_existing(self) -> sqlite3.Connection:
        uri = f"file:{quote(str(self.database_path))}?mode=rw"
        connection = sqlite3.connect(uri, uri=True, timeout=5.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def ensure_initialized(self) -> None:
        with self._initialize_lock:
            if self._initialized:
                return
            created = False
            try:
                created = not self.database_path.exists()
                if created:
                    if self.public_mode and not self.allow_public_initialize:
                        raise ProgressionStoreError(
                            "The Public progression database is missing. Run the explicit "
                            "Public database initialization step before starting the API."
                        )
                    if not self.database_path.parent.is_dir():
                        raise ProgressionStoreError(
                            "The progression database directory is unavailable."
                        )
                    connection = sqlite3.connect(self.database_path, timeout=5.0)
                    connection.row_factory = sqlite3.Row
                    connection.execute("PRAGMA foreign_keys = ON")
                    try:
                        self._create_schema(connection)
                        if self.public_mode:
                            self._upgrade_empty_v4_to_public_v5(connection)
                    finally:
                        connection.close()
                self._upgrade_and_validate_store()
                self._initialized = True
            except ProgressionStoreError:
                if created and self.public_mode:
                    self.database_path.unlink(missing_ok=True)
                raise
            except (OSError, sqlite3.Error) as exc:
                if created and self.public_mode:
                    self.database_path.unlink(missing_ok=True)
                raise ProgressionStoreError(
                    "Persistent progression is unavailable or corrupt. Retry later."
                ) from exc

    def _create_schema(self, connection: sqlite3.Connection) -> None:
        try:
            connection.executescript(
                """
                BEGIN IMMEDIATE;
                CREATE TABLE metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE profiles (profile_id TEXT PRIMARY KEY);
                CREATE TABLE save_slots (
                    slot_id INTEGER PRIMARY KEY CHECK (slot_id BETWEEN 1 AND 5),
                    profile_id TEXT UNIQUE REFERENCES profiles(profile_id),
                    created_at TEXT,
                    last_played_at TEXT,
                    CHECK ((profile_id IS NULL) = (created_at IS NULL)),
                    CHECK ((profile_id IS NULL) = (last_played_at IS NULL))
                );
                CREATE TABLE active_slot (
                    singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1),
                    slot_id INTEGER REFERENCES save_slots(slot_id)
                );
                CREATE TABLE unlocked_heroes (
                    profile_id TEXT NOT NULL REFERENCES profiles(profile_id),
                    definition_id TEXT NOT NULL,
                    PRIMARY KEY (profile_id, definition_id)
                );
                CREATE TABLE stage_progress (
                    profile_id TEXT NOT NULL REFERENCES profiles(profile_id),
                    stage_id TEXT NOT NULL,
                    highest_completed_battle INTEGER NOT NULL DEFAULT 0
                        CHECK (highest_completed_battle BETWEEN 0 AND 9),
                    completed INTEGER NOT NULL DEFAULT 0 CHECK (completed IN (0, 1)),
                    PRIMARY KEY (profile_id, stage_id)
                );
                CREATE TABLE granted_rewards (
                    profile_id TEXT NOT NULL REFERENCES profiles(profile_id),
                    reward_id TEXT NOT NULL,
                    count INTEGER NOT NULL CHECK (count > 0),
                    PRIMARY KEY (profile_id, reward_id)
                );
                CREATE TABLE battle_completions (
                    profile_id TEXT NOT NULL REFERENCES profiles(profile_id),
                    battle_id TEXT NOT NULL,
                    stage_id TEXT NOT NULL,
                    battle_index INTEGER NOT NULL CHECK (battle_index >= 1),
                    PRIMARY KEY (profile_id, battle_id)
                );
                CREATE TABLE stage_mode_completions (
                    profile_id TEXT NOT NULL REFERENCES profiles(profile_id),
                    stage_id TEXT NOT NULL,
                    battle_index INTEGER NOT NULL CHECK (battle_index >= 1),
                    mode TEXT NOT NULL CHECK (mode IN ('learner', 'tactics')),
                    completion_battle_id TEXT,
                    completed_at TEXT NOT NULL,
                    PRIMARY KEY (profile_id, stage_id, battle_index, mode),
                    UNIQUE (profile_id, completion_battle_id)
                );
                CREATE TABLE arena_runs (
                    run_id TEXT PRIMARY KEY,
                    profile_id TEXT NOT NULL UNIQUE
                        REFERENCES profiles(profile_id) ON DELETE CASCADE,
                    run_schema_version INTEGER NOT NULL CHECK (run_schema_version = 1),
                    status TEXT NOT NULL CHECK (status IN ('active', 'completed')),
                    squad_json TEXT NOT NULL,
                    schedule_seed INTEGER NOT NULL CHECK (schedule_seed >= 0),
                    current_node_index INTEGER CHECK (current_node_index BETWEEN 1 AND 12),
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    CHECK (
                        (status = 'active' AND current_node_index IS NOT NULL
                         AND completed_at IS NULL)
                        OR
                        (status = 'completed' AND current_node_index IS NULL
                         AND completed_at IS NOT NULL)
                    )
                );
                CREATE TABLE arena_nodes (
                    run_id TEXT NOT NULL REFERENCES arena_runs(run_id) ON DELETE CASCADE,
                    node_index INTEGER NOT NULL CHECK (node_index BETWEEN 1 AND 12),
                    battle_size INTEGER NOT NULL CHECK (battle_size BETWEEN 1 AND 3),
                    enemy_formation TEXT,
                    enemy_team_json TEXT NOT NULL,
                    battle_seed INTEGER NOT NULL CHECK (battle_seed >= 0),
                    completed INTEGER NOT NULL DEFAULT 0 CHECK (completed IN (0, 1)),
                    completion_battle_id TEXT UNIQUE,
                    PRIMARY KEY (run_id, node_index),
                    CHECK ((completed = 0) = (completion_battle_id IS NULL))
                );
                """
            )
            connection.execute(
                "INSERT INTO metadata(key, value) VALUES ('schema_version', ?)",
                (str(SCHEMA_VERSION),),
            )
            connection.executemany(
                "INSERT INTO save_slots(slot_id) VALUES (?)",
                ((slot_id,) for slot_id in SAVE_SLOT_IDS),
            )
            connection.execute(
                "INSERT INTO active_slot(singleton_id, slot_id) VALUES (1, NULL)"
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise

    def _upgrade_and_validate_store(self) -> None:
        connection = self._connect_existing()
        try:
            integrity = connection.execute("PRAGMA quick_check").fetchone()[0]
            if integrity != "ok":
                raise ProgressionStoreError(
                    "Persistent progression failed its integrity check. Retry later."
                )
            row = connection.execute(
                "SELECT value FROM metadata WHERE key = 'schema_version'"
            ).fetchone()
            if row is None:
                raise ProgressionStoreError(
                    "Persistent progression has an unsupported schema. Retry later."
                )
            if self.public_mode:
                if row["value"] != str(PUBLIC_SCHEMA_VERSION):
                    raise ProgressionStoreError(
                        "The Public progression database has an unsupported schema. "
                        "Refusing to migrate or replace it automatically."
                    )
                self._validate_public_v5(connection)
                return
            if row["value"] == "1":
                self._migrate_v1(connection)
                row = {"value": "2"}
            if row["value"] == "2":
                self._migrate_v2(connection)
                row = {"value": "3"}
            if row["value"] == "3":
                self._migrate_v3(connection)
            elif row["value"] != str(SCHEMA_VERSION):
                raise ProgressionStoreError(
                    "Persistent progression has an unsupported schema. Retry later."
                )
            self._validate_v4(connection)
        finally:
            connection.close()

    def _upgrade_empty_v4_to_public_v5(
        self, connection: sqlite3.Connection
    ) -> None:
        """Create the clean Public-only ownership/authentication foundation.

        This path is used only while explicitly initializing a brand-new empty
        database. Existing Development v4 files are never passed through it.
        """

        try:
            connection.execute("BEGIN IMMEDIATE")
            if connection.execute("SELECT 1 FROM profiles LIMIT 1").fetchone():
                raise ProgressionStoreError(
                    "A non-empty database cannot be converted into a Public store."
                )
            statements = (
                """CREATE TABLE players (
                    player_id TEXT PRIMARY KEY,
                    display_name TEXT NOT NULL
                        CHECK (length(display_name) BETWEEN 3 AND 20)
                        CHECK (display_name NOT GLOB '*[^A-Za-z0-9_]*'),
                    recovery_mac BLOB NOT NULL UNIQUE,
                    recovery_key_version INTEGER NOT NULL CHECK (recovery_key_version > 0),
                    recovery_issued_at TEXT NOT NULL,
                    recovery_confirmed_at TEXT,
                    session_generation INTEGER NOT NULL DEFAULT 1
                        CHECK (session_generation >= 1),
                    created_at TEXT NOT NULL
                )""",
                """CREATE TABLE player_sessions (
                    session_id TEXT PRIMARY KEY,
                    player_id TEXT NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
                    token_mac BLOB NOT NULL UNIQUE,
                    previous_token_mac BLOB UNIQUE,
                    previous_token_valid_until TEXT,
                    generation INTEGER NOT NULL CHECK (generation >= 1),
                    csrf_mac BLOB NOT NULL,
                    issued_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    revoked_at TEXT
                )""",
                """CREATE UNIQUE INDEX one_active_session_per_player
                    ON player_sessions(player_id) WHERE revoked_at IS NULL""",
                "CREATE INDEX player_sessions_expiry ON player_sessions(expires_at)",
                """CREATE TABLE recovery_ip_attempts (
                    attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_mac BLOB NOT NULL,
                    attempted_at TEXT NOT NULL
                )""",
                """CREATE INDEX recovery_ip_attempts_window
                    ON recovery_ip_attempts(ip_mac, attempted_at)""",
                """CREATE TABLE recovery_ip_blocks (
                    ip_mac BLOB PRIMARY KEY,
                    blocked_until TEXT NOT NULL
                )""",
                """CREATE TABLE player_save_slots (
                    player_id TEXT NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
                    slot_id INTEGER NOT NULL CHECK (slot_id BETWEEN 1 AND 5),
                    profile_id TEXT UNIQUE REFERENCES profiles(profile_id) ON DELETE SET NULL,
                    created_at TEXT,
                    last_played_at TEXT,
                    PRIMARY KEY (player_id, slot_id),
                    CHECK ((profile_id IS NULL) = (created_at IS NULL)),
                    CHECK ((profile_id IS NULL) = (last_played_at IS NULL))
                )""",
                """CREATE TABLE player_active_slots (
                    player_id TEXT PRIMARY KEY REFERENCES players(player_id) ON DELETE CASCADE,
                    slot_id INTEGER,
                    FOREIGN KEY (player_id, slot_id)
                        REFERENCES player_save_slots(player_id, slot_id)
                )""",
                """CREATE TABLE active_battle_leases (
                    player_id TEXT PRIMARY KEY REFERENCES players(player_id) ON DELETE CASCADE,
                    battle_id TEXT NOT NULL UNIQUE,
                    profile_id TEXT NOT NULL REFERENCES profiles(profile_id),
                    slot_id INTEGER CHECK (slot_id BETWEEN 1 AND 5),
                    launch_session_id TEXT NOT NULL,
                    session_generation INTEGER NOT NULL CHECK (session_generation >= 1),
                    status TEXT NOT NULL CHECK (status IN ('provisional', 'active')),
                    reserved_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )""",
                """CREATE TABLE battle_diagnostics (
                    battle_id TEXT PRIMARY KEY,
                    player_id TEXT NOT NULL REFERENCES players(player_id),
                    slot_id INTEGER CHECK (slot_id BETWEEN 1 AND 5),
                    profile_id TEXT,
                    launch_session_id TEXT NOT NULL,
                    session_generation INTEGER NOT NULL CHECK (session_generation >= 1),
                    seed_hex TEXT NOT NULL,
                    build_version TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    battle_type TEXT NOT NULL,
                    context_json TEXT NOT NULL,
                    last_accepted_action_at TEXT,
                    expires_at TEXT,
                    outcome TEXT,
                    outcome_at TEXT,
                    lifecycle_status TEXT NOT NULL,
                    terminal_reason TEXT,
                    settlement_at TEXT,
                    receipt_key TEXT
                )""",
                """CREATE INDEX battle_diagnostics_player_started
                    ON battle_diagnostics(player_id, started_at)""",
                """CREATE TABLE battle_settlements (
                    battle_id TEXT PRIMARY KEY,
                    outcome TEXT NOT NULL,
                    settled_at TEXT NOT NULL,
                    original_result_json TEXT NOT NULL,
                    receipt_key TEXT UNIQUE
                )""",
            )
            for statement in statements:
                connection.execute(statement)
            connection.execute("DELETE FROM save_slots")
            connection.execute("DELETE FROM active_slot")
            connection.execute(
                "INSERT INTO metadata(key, value) VALUES ('database_role', 'public')"
            )
            connection.execute(
                "INSERT INTO metadata(key, value) "
                "VALUES ('public_battle_schema_revision', ?)",
                (str(PUBLIC_BATTLE_SCHEMA_REVISION),),
            )
            connection.execute(
                "UPDATE metadata SET value = ? WHERE key = 'schema_version'",
                (str(PUBLIC_SCHEMA_VERSION),),
            )
            connection.commit()
        except (ProgressionStoreError, sqlite3.Error):
            connection.rollback()
            raise

    def _validate_public_v5(self, connection: sqlite3.Connection) -> None:
        role = connection.execute(
            "SELECT value FROM metadata WHERE key = 'database_role'"
        ).fetchone()
        if role is None or role["value"] != "public":
            raise ProgressionStoreError(
                "The configured Public database is not marked for Public use."
            )
        battle_revision = connection.execute(
            "SELECT value FROM metadata "
            "WHERE key = 'public_battle_schema_revision'"
        ).fetchone()
        if (
            battle_revision is None
            or battle_revision["value"] != str(PUBLIC_BATTLE_SCHEMA_REVISION)
        ):
            raise ProgressionStoreError(
                "This Public v5 database predates the Batch 2 battle schema. "
                "An explicit offline upgrade or approved disposable-database "
                "reinitialization is required; runtime migration is refused."
            )
        required = {
            "players", "player_sessions", "recovery_ip_attempts",
            "recovery_ip_blocks", "player_save_slots", "player_active_slots",
            "active_battle_leases", "battle_diagnostics", "battle_settlements",
        }
        actual = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        if not required.issubset(actual):
            raise ProgressionStoreError(
                "The Public progression schema is incomplete or corrupt."
            )
        player_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(players)")
        }
        if not {
            "player_id", "display_name", "recovery_mac", "recovery_key_version",
            "recovery_confirmed_at", "session_generation",
        }.issubset(player_columns):
            raise ProgressionStoreError(
                "The Public player schema is incomplete or corrupt."
            )
        session_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(player_sessions)")
        }
        if not {
            "session_id", "player_id", "token_mac", "previous_token_mac",
            "generation", "csrf_mac", "issued_at", "last_seen_at",
            "expires_at", "revoked_at",
        }.issubset(session_columns):
            raise ProgressionStoreError(
                "The Public session schema is incomplete or corrupt."
            )
        lease_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(active_battle_leases)")
        }
        if not {
            "player_id", "battle_id", "profile_id", "slot_id",
            "launch_session_id", "session_generation", "status",
            "reserved_at", "expires_at",
        }.issubset(lease_columns):
            raise ProgressionStoreError(
                "The Public battle lease schema is incomplete or corrupt."
            )
        diagnostic_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(battle_diagnostics)")
        }
        if not {
            "battle_id", "player_id", "slot_id", "profile_id",
            "launch_session_id", "session_generation", "seed_hex",
            "build_version", "started_at", "battle_type", "context_json",
            "last_accepted_action_at", "expires_at", "outcome", "outcome_at",
            "lifecycle_status", "terminal_reason", "settlement_at", "receipt_key",
        }.issubset(diagnostic_columns):
            raise ProgressionStoreError(
                "The Public battle diagnostic schema is incomplete or corrupt."
            )
        slot_info = connection.execute(
            "PRAGMA table_info(player_save_slots)"
        ).fetchall()
        slot_primary_key = [
            row["name"]
            for row in sorted(slot_info, key=lambda item: item["pk"])
            if row["pk"]
        ]
        if slot_primary_key != ["player_id", "slot_id"]:
            raise ProgressionStoreError(
                "The Public save-slot ownership key is missing or corrupt."
            )
        slot_foreign_keys = connection.execute(
            "PRAGMA foreign_key_list(player_save_slots)"
        ).fetchall()
        if not any(
            row["table"] == "players"
            and row["from"] == "player_id"
            and row["to"] == "player_id"
            and row["on_delete"].upper() == "CASCADE"
            for row in slot_foreign_keys
        ):
            raise ProgressionStoreError(
                "The Public save-slot player ownership constraint is missing or corrupt."
            )
        active_info = connection.execute(
            "PRAGMA table_info(player_active_slots)"
        ).fetchall()
        active_primary_key = [
            row["name"]
            for row in sorted(active_info, key=lambda item: item["pk"])
            if row["pk"]
        ]
        if active_primary_key != ["player_id"]:
            raise ProgressionStoreError(
                "The Public active-slot player key is missing or corrupt."
            )
        active_foreign_keys = connection.execute(
            "PRAGMA foreign_key_list(player_active_slots)"
        ).fetchall()
        grouped: dict[int, list[tuple[int, str, str]]] = {}
        targets: dict[int, tuple[str, str]] = {}
        for row in active_foreign_keys:
            grouped.setdefault(row["id"], []).append(
                (row["seq"], row["from"], row["to"])
            )
            targets[row["id"]] = (row["table"], row["on_delete"].upper())
        if not any(
            targets[key] == ("player_save_slots", "NO ACTION")
            and sorted(columns) == [
                (0, "player_id", "player_id"), (1, "slot_id", "slot_id")
            ]
            for key, columns in grouped.items()
        ):
            raise ProgressionStoreError(
                "The Public active-slot ownership constraint is missing or corrupt."
            )
        if not any(
            row["table"] == "players"
            and row["from"] == "player_id"
            and row["to"] == "player_id"
            and row["on_delete"].upper() == "CASCADE"
            for row in active_foreign_keys
        ):
            raise ProgressionStoreError(
                "The Public active-slot player constraint is missing or corrupt."
            )
        active_session_index = connection.execute(
            """SELECT sql FROM sqlite_master
               WHERE type = 'index' AND name = 'one_active_session_per_player'"""
        ).fetchone()
        normalized_index = (
            " ".join(active_session_index["sql"].lower().split())
            if active_session_index is not None and active_session_index["sql"]
            else ""
        )
        if (
            "unique index" not in normalized_index
            or "player_sessions" not in normalized_index
            or "player_id" not in normalized_index
            or "where revoked_at is null" not in normalized_index
        ):
            raise ProgressionStoreError(
                "The Public single-session constraint is missing or corrupt."
            )
        index_columns = [
            row["name"]
            for row in connection.execute(
                "PRAGMA index_info(one_active_session_per_player)"
            )
        ]
        if index_columns != ["player_id"]:
            raise ProgressionStoreError(
                "The Public single-session constraint is missing or corrupt."
            )
        foreign_key_failures = connection.execute("PRAGMA foreign_key_check").fetchall()
        if foreign_key_failures:
            raise ProgressionStoreError(
                "The Public progression database failed its foreign-key check."
            )

    def _migrate_v1(self, connection: sqlite3.Connection) -> None:
        """Atomically place the UI-020 default profile into slot 1 exactly once."""
        try:
            connection.execute("BEGIN IMMEDIATE")
            profile = connection.execute(
                "SELECT 1 FROM profiles WHERE profile_id = ?", (DEFAULT_PROFILE_ID,)
            ).fetchone()
            if profile is None:
                raise ProgressionStoreError(
                    "The legacy default profile cannot be preserved. Retry later."
                )
            connection.execute(
                """CREATE TABLE save_slots (
                    slot_id INTEGER PRIMARY KEY CHECK (slot_id BETWEEN 1 AND 5),
                    profile_id TEXT UNIQUE REFERENCES profiles(profile_id),
                    created_at TEXT,
                    last_played_at TEXT,
                    CHECK ((profile_id IS NULL) = (created_at IS NULL)),
                    CHECK ((profile_id IS NULL) = (last_played_at IS NULL))
                )"""
            )
            connection.execute(
                """CREATE TABLE active_slot (
                    singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1),
                    slot_id INTEGER REFERENCES save_slots(slot_id)
                )"""
            )
            connection.executemany(
                "INSERT INTO save_slots(slot_id) VALUES (?)",
                ((slot_id,) for slot_id in SAVE_SLOT_IDS),
            )
            migrated_at = self._timestamp()
            connection.execute(
                """UPDATE save_slots SET profile_id = ?, created_at = ?,
                       last_played_at = ? WHERE slot_id = 1""",
                (DEFAULT_PROFILE_ID, migrated_at, migrated_at),
            )
            connection.execute(
                "INSERT INTO active_slot(singleton_id, slot_id) VALUES (1, 1)"
            )
            # Validate the legacy payload before the schema marker commits so
            # an incomplete/corrupt UI-020 profile leaves schema v1 untouched.
            self._read_progression(connection, DEFAULT_PROFILE_ID)
            connection.execute(
                "UPDATE metadata SET value = ? WHERE key = 'schema_version'",
                ("2",),
            )
            connection.commit()
        except ProgressionStoreError:
            connection.rollback()
            raise
        except sqlite3.Error as exc:
            connection.rollback()
            raise ProgressionStoreError(
                "Legacy progression migration could not preserve the profile. Retry later."
            ) from exc

    def _migrate_v2(self, connection: sqlite3.Connection) -> None:
        """Add empty per-profile Arena storage without fabricating run history."""
        try:
            connection.executescript(
                """
                BEGIN IMMEDIATE;
                CREATE TABLE arena_runs (
                    run_id TEXT PRIMARY KEY,
                    profile_id TEXT NOT NULL UNIQUE
                        REFERENCES profiles(profile_id) ON DELETE CASCADE,
                    run_schema_version INTEGER NOT NULL CHECK (run_schema_version = 1),
                    status TEXT NOT NULL CHECK (status IN ('active', 'completed')),
                    squad_json TEXT NOT NULL,
                    schedule_seed INTEGER NOT NULL CHECK (schedule_seed >= 0),
                    current_node_index INTEGER CHECK (current_node_index BETWEEN 1 AND 12),
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    CHECK (
                        (status = 'active' AND current_node_index IS NOT NULL
                         AND completed_at IS NULL)
                        OR
                        (status = 'completed' AND current_node_index IS NULL
                         AND completed_at IS NOT NULL)
                    )
                );
                CREATE TABLE arena_nodes (
                    run_id TEXT NOT NULL REFERENCES arena_runs(run_id) ON DELETE CASCADE,
                    node_index INTEGER NOT NULL CHECK (node_index BETWEEN 1 AND 12),
                    battle_size INTEGER NOT NULL CHECK (battle_size BETWEEN 1 AND 3),
                    enemy_formation TEXT,
                    enemy_team_json TEXT NOT NULL,
                    battle_seed INTEGER NOT NULL CHECK (battle_seed >= 0),
                    completed INTEGER NOT NULL DEFAULT 0 CHECK (completed IN (0, 1)),
                    completion_battle_id TEXT UNIQUE,
                    PRIMARY KEY (run_id, node_index),
                    CHECK ((completed = 0) = (completion_battle_id IS NULL))
                );
                UPDATE metadata SET value = '3' WHERE key = 'schema_version';
                COMMIT;
                """
            )
        except sqlite3.Error as exc:
            connection.rollback()
            raise ProgressionStoreError(
                "Arena progression migration could not preserve the profiles. Retry later."
            ) from exc

    def _migrate_v3(self, connection: sqlite3.Connection) -> None:
        """Add mode-specific completion history and preserve Learner progress."""
        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """CREATE TABLE IF NOT EXISTS stage_mode_completions (
                    profile_id TEXT NOT NULL REFERENCES profiles(profile_id),
                    stage_id TEXT NOT NULL,
                    battle_index INTEGER NOT NULL CHECK (battle_index >= 1),
                    mode TEXT NOT NULL CHECK (mode IN ('learner', 'tactics')),
                    completion_battle_id TEXT,
                    completed_at TEXT NOT NULL,
                    PRIMARY KEY (profile_id, stage_id, battle_index, mode),
                    UNIQUE (profile_id, completion_battle_id)
                )"""
            )
            migrated_at = self._timestamp()
            rows = connection.execute(
                """SELECT profile_id, stage_id, highest_completed_battle
                   FROM stage_progress"""
            ).fetchall()
            connection.executemany(
                """INSERT OR IGNORE INTO stage_mode_completions(
                       profile_id, stage_id, battle_index, mode,
                       completion_battle_id, completed_at
                   ) VALUES (?, ?, ?, 'learner', NULL, ?)""",
                (
                    (row["profile_id"], row["stage_id"], battle_index, migrated_at)
                    for row in rows
                    for battle_index in range(1, row["highest_completed_battle"] + 1)
                ),
            )
            connection.execute(
                "UPDATE metadata SET value = '4' WHERE key = 'schema_version'"
            )
            connection.commit()
        except sqlite3.Error as exc:
            connection.rollback()
            raise ProgressionStoreError(
                "Campaign-mode migration could not preserve the profiles. Retry later."
            ) from exc

    def _validate_v4(self, connection: sqlite3.Connection) -> None:
        if connection.execute(
            """SELECT 1 FROM sqlite_master
               WHERE type = 'table' AND name = 'stage_mode_completions'"""
        ).fetchone() is None:
            raise ProgressionStoreError(
                "The campaign-mode progression schema is incomplete. Retry later."
            )
        slots = connection.execute(
            "SELECT slot_id, profile_id FROM save_slots ORDER BY slot_id"
        ).fetchall()
        if [row["slot_id"] for row in slots] != list(SAVE_SLOT_IDS):
            raise ProgressionStoreError(
                "The save-slot catalogue is incomplete or corrupt. Retry later."
            )
        active_rows = connection.execute(
            "SELECT slot_id FROM active_slot WHERE singleton_id = 1"
        ).fetchall()
        if len(active_rows) != 1:
            raise ProgressionStoreError(
                "The active save-slot state is corrupt. Retry later."
            )
        active_slot_id = active_rows[0]["slot_id"]
        occupied = {row["slot_id"]: row["profile_id"] for row in slots}
        if active_slot_id is not None and occupied.get(active_slot_id) is None:
            raise ProgressionStoreError(
                "The active save slot is empty or corrupt. Retry later."
            )
        assigned_profiles = {value for value in occupied.values() if value is not None}
        stored_profiles = {
            row["profile_id"]
            for row in connection.execute("SELECT profile_id FROM profiles")
        }
        if assigned_profiles != stored_profiles:
            raise ProgressionStoreError(
                "Stored profiles are not assigned to exactly one save slot. Retry later."
            )
        for profile_id in assigned_profiles:
            self._read_progression(connection, profile_id)
            self._read_arena_run(connection, profile_id)

    def _timestamp(self) -> str:
        value = self._now()
        if value.tzinfo is None:
            raise ValueError("The progression clock must return a timezone-aware value.")
        return value.astimezone(UTC).isoformat(timespec="milliseconds").replace(
            "+00:00", "Z"
        )

    def _timestamp_after(self, seconds: int) -> str:
        value = self._now()
        if value.tzinfo is None:
            raise ValueError("The progression clock must return a timezone-aware value.")
        return (value.astimezone(UTC) + timedelta(seconds=seconds)).isoformat(
            timespec="milliseconds"
        ).replace("+00:00", "Z")

    @staticmethod
    def _public_battle_payload(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "battleId": row["battle_id"],
            "playerId": row["player_id"],
            "slotId": row["slot_id"],
            "profileId": row["profile_id"],
            "launchSessionId": row["launch_session_id"],
            "sessionGeneration": row["session_generation"],
            "seedHex": row["seed_hex"],
            "battleType": row["battle_type"],
            "context": json.loads(row["context_json"]),
            "startedAt": row["started_at"],
            "lastAcceptedActionAt": row["last_accepted_action_at"],
            "expiresAt": row["expires_at"],
            "outcome": json.loads(row["outcome"]) if row["outcome"] else None,
            "outcomeAt": row["outcome_at"],
            "lifecycleStatus": row["lifecycle_status"],
            "terminalReason": row["terminal_reason"],
            "settlementAt": row["settlement_at"],
            "receiptKey": row["receipt_key"],
        }

    def _expire_public_battles_tx(
        self, connection: sqlite3.Connection, *, now: str
    ) -> list[str]:
        rows = connection.execute(
            """SELECT l.battle_id
               FROM active_battle_leases l
               JOIN battle_diagnostics d ON d.battle_id = l.battle_id
               WHERE l.expires_at <= ?
                 AND d.lifecycle_status NOT IN ('resolving', 'terminalPending', 'settled')""",
            (now,),
        ).fetchall()
        battle_ids = [row["battle_id"] for row in rows]
        if battle_ids:
            connection.executemany(
                """UPDATE battle_diagnostics
                   SET lifecycle_status = 'expired', terminal_reason = 'inactivity',
                       outcome = ?, outcome_at = ?, expires_at = ?
                   WHERE battle_id = ?""",
                (
                    (
                        json.dumps({"kind": "abandoned", "reason": "expired"},
                                   sort_keys=True, separators=(",", ":")),
                        now, now, battle_id,
                    )
                    for battle_id in battle_ids
                ),
            )
            connection.executemany(
                "DELETE FROM active_battle_leases WHERE battle_id = ?",
                ((battle_id,) for battle_id in battle_ids),
            )
        return battle_ids

    def reserve_public_battle(
        self,
        *,
        battle_id: str,
        player_id: str,
        session_id: str,
        session_generation: int,
        seed_hex: str,
        battle_type: Literal["stage", "arena"],
        context: dict[str, Any],
        build_version: str,
        capacity: int = PUBLIC_BATTLE_CAPACITY,
        provisional_ttl_seconds: int = PUBLIC_BATTLE_PROVISIONAL_TTL_SECONDS,
    ) -> dict[str, Any]:
        """Atomically reserve one Public battle slot before RAM construction."""
        if not self.public_mode:
            raise ProgressionStoreError("Public battle reservations require Public mode.")
        if capacity < 1 or provisional_ttl_seconds < 1:
            raise ValueError("Battle capacity and provisional TTL must be positive.")
        if len(seed_hex) != 64 or any(value not in "0123456789abcdef" for value in seed_hex):
            raise ValueError("seed_hex must be canonical 256-bit lowercase hexadecimal.")
        connection = self._connection()
        try:
            connection.execute("BEGIN IMMEDIATE")
            self._assert_public_session(
                connection, player_id=player_id, session_id=session_id,
                generation=session_generation,
            )
            now = self._timestamp()
            expired = self._expire_public_battles_tx(connection, now=now)
            binding = connection.execute(
                """SELECT a.slot_id, s.profile_id
                   FROM player_active_slots a
                   JOIN player_save_slots s
                     ON s.player_id = a.player_id AND s.slot_id = a.slot_id
                   WHERE a.player_id = ? AND s.profile_id IS NOT NULL""",
                (player_id,),
            ).fetchone()
            if binding is None:
                connection.commit()
                raise SaveSlotAccessError(
                    "noActiveSaveSlot",
                    "Create or load a save slot before starting a battle.",
                )
            if connection.execute(
                "SELECT 1 FROM active_battle_leases WHERE player_id = ?",
                (player_id,),
            ).fetchone() is not None:
                connection.commit()
                raise PublicBattleAccessError(
                    "activeBattleExists", "This player already has an active battle."
                )
            count = connection.execute(
                "SELECT COUNT(*) FROM active_battle_leases"
            ).fetchone()[0]
            if count >= capacity:
                connection.commit()
                raise PublicBattleAccessError(
                    "battleCapacityReached",
                    "Battle capacity is currently full. Retry later.",
                )
            expires_at = self._timestamp_after(provisional_ttl_seconds)
            connection.execute(
                """INSERT INTO active_battle_leases(
                       player_id, battle_id, profile_id, slot_id,
                       launch_session_id, session_generation, status,
                       reserved_at, expires_at
                   ) VALUES (?, ?, ?, ?, ?, ?, 'provisional', ?, ?)""",
                (
                    player_id, battle_id, binding["profile_id"], binding["slot_id"],
                    session_id, session_generation, now, expires_at,
                ),
            )
            connection.execute(
                """INSERT INTO battle_diagnostics(
                       battle_id, player_id, slot_id, profile_id,
                       launch_session_id, session_generation, seed_hex,
                       build_version, started_at, battle_type, context_json,
                       last_accepted_action_at, expires_at, lifecycle_status
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, 'provisional')""",
                (
                    battle_id, player_id, binding["slot_id"], binding["profile_id"],
                    session_id, session_generation, seed_hex, build_version, now,
                    battle_type,
                    json.dumps(context, sort_keys=True, separators=(",", ":")),
                    expires_at,
                ),
            )
            connection.commit()
            return {
                "battleId": battle_id,
                "slotId": binding["slot_id"],
                "profileId": binding["profile_id"],
                "expiresAt": expires_at,
                "expiredBattleIds": expired,
            }
        except (ProgressionStoreError, SaveSlotAccessError, PublicBattleAccessError):
            if connection.in_transaction:
                connection.rollback()
            raise
        except sqlite3.Error as exc:
            connection.rollback()
            raise ProgressionStoreError(
                "The Public battle reservation could not be created. Retry later."
            ) from exc
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def activate_public_battle(
        self,
        *,
        battle_id: str,
        player_id: str,
        session_id: str,
        session_generation: int,
        inactivity_seconds: int = PUBLIC_BATTLE_INACTIVITY_SECONDS,
    ) -> dict[str, Any]:
        """Durably activate a still-owned provisional lease after RAM construction."""
        connection = self._connection()
        try:
            connection.execute("BEGIN IMMEDIATE")
            self._assert_public_session(
                connection, player_id=player_id, session_id=session_id,
                generation=session_generation,
            )
            now = self._timestamp()
            self._expire_public_battles_tx(connection, now=now)
            row = connection.execute(
                """SELECT l.*, s.profile_id AS current_profile_id,
                          a.slot_id AS current_slot_id
                   FROM active_battle_leases l
                   LEFT JOIN player_active_slots a ON a.player_id = l.player_id
                   LEFT JOIN player_save_slots s
                     ON s.player_id = a.player_id AND s.slot_id = a.slot_id
                   WHERE l.battle_id = ? AND l.player_id = ?""",
                (battle_id, player_id),
            ).fetchone()
            if row is None or row["status"] != "provisional":
                raise PublicBattleAccessError(
                    "battleReservationExpired",
                    "The battle reservation expired before activation.",
                )
            if (
                row["launch_session_id"] != session_id
                or row["session_generation"] != session_generation
                or row["profile_id"] != row["current_profile_id"]
                or row["slot_id"] != row["current_slot_id"]
            ):
                raise PublicBattleAccessError(
                    "battleLaunchContextChanged",
                    "The battle launch context changed before activation.",
                )
            expires_at = self._timestamp_after(inactivity_seconds)
            connection.execute(
                """UPDATE active_battle_leases
                   SET status = 'active', expires_at = ? WHERE battle_id = ?""",
                (expires_at, battle_id),
            )
            connection.execute(
                """UPDATE battle_diagnostics
                   SET lifecycle_status = 'active', expires_at = ?
                   WHERE battle_id = ?""",
                (expires_at, battle_id),
            )
            diagnostic = connection.execute(
                "SELECT * FROM battle_diagnostics WHERE battle_id = ?", (battle_id,)
            ).fetchone()
            connection.commit()
            return self._public_battle_payload(diagnostic)
        except (ProgressionStoreError, SaveSlotAccessError, PublicBattleAccessError):
            connection.rollback()
            raise
        except sqlite3.Error as exc:
            connection.rollback()
            raise ProgressionStoreError(
                "The Public battle reservation could not be activated. Retry later."
            ) from exc
        finally:
            connection.close()

    def abandon_public_reservation(
        self, *, battle_id: str, reason: str = "constructionFailed"
    ) -> None:
        """Compensate a failed RAM construction or durable activation."""
        if not self.public_mode:
            return
        connection = self._connection()
        try:
            connection.execute("BEGIN IMMEDIATE")
            now = self._timestamp()
            connection.execute(
                """UPDATE battle_diagnostics
                   SET lifecycle_status = 'abandoned', terminal_reason = ?,
                       outcome = ?, outcome_at = ?, expires_at = ?
                   WHERE battle_id = ?
                     AND lifecycle_status IN ('provisional', 'active')""",
                (
                    reason,
                    json.dumps({"kind": "abandoned", "reason": reason},
                               sort_keys=True, separators=(",", ":")),
                    now, now, battle_id,
                ),
            )
            connection.execute(
                "DELETE FROM active_battle_leases WHERE battle_id = ?", (battle_id,)
            )
            connection.commit()
        except sqlite3.Error as exc:
            connection.rollback()
            raise ProgressionStoreError(
                "The failed Public battle reservation could not be released."
            ) from exc
        finally:
            connection.close()

    def public_launch_binding(
        self,
        *,
        player_id: str,
        session_id: str,
        session_generation: int,
    ) -> dict[str, Any]:
        connection = self._connection()
        try:
            # This operation may synchronously expire stale leases before it
            # reads the launch context.  Use a write transaction and commit so
            # cleanup is not silently rolled back when the connection closes.
            connection.execute("BEGIN IMMEDIATE")
            self._assert_public_session(
                connection, player_id=player_id, session_id=session_id,
                generation=session_generation,
            )
            now = self._timestamp()
            self._expire_public_battles_tx(connection, now=now)
            row = connection.execute(
                """SELECT a.slot_id, s.profile_id
                   FROM player_active_slots a
                   JOIN player_save_slots s
                     ON s.player_id = a.player_id AND s.slot_id = a.slot_id
                   WHERE a.player_id = ? AND s.profile_id IS NOT NULL""",
                (player_id,),
            ).fetchone()
            if row is None:
                connection.commit()
                raise SaveSlotAccessError(
                    "noActiveSaveSlot",
                    "Create or load a save slot before starting a battle.",
                )
            result = {"slotId": row["slot_id"], "profileId": row["profile_id"]}
            connection.commit()
            return result
        except (ProgressionStoreError, SaveSlotAccessError):
            raise
        except sqlite3.Error as exc:
            raise ProgressionStoreError(
                "The Public launch context could not be read. Retry later."
            ) from exc
        finally:
            connection.close()

    def authorize_public_battle(
        self,
        *,
        battle_id: str,
        player_id: str,
        session_id: str,
        session_generation: int,
    ) -> dict[str, Any]:
        """Authenticate ownership and current immutable launch context."""
        connection = self._connection()
        try:
            connection.execute("BEGIN IMMEDIATE")
            self._assert_public_session(
                connection, player_id=player_id, session_id=session_id,
                generation=session_generation,
            )
            now = self._timestamp()
            expired = self._expire_public_battles_tx(connection, now=now)
            row = connection.execute(
                "SELECT * FROM battle_diagnostics WHERE battle_id = ?", (battle_id,)
            ).fetchone()
            if row is None or row["player_id"] != player_id:
                raise PublicBattleAccessError("battleNotFound", "Battle was not found.")
            lifecycle = row["lifecycle_status"]
            if lifecycle in {"settled", "abandoned", "expired"}:
                connection.commit()
                payload = self._public_battle_payload(row)
                payload["expiredBattleIds"] = expired
                return payload
            if (
                row["launch_session_id"] != session_id
                or row["session_generation"] != session_generation
            ):
                if lifecycle == "terminalPending":
                    connection.execute(
                        """UPDATE battle_diagnostics
                           SET terminal_reason = 'sessionRevokedBeforeSettlement'
                           WHERE battle_id = ?""",
                        (battle_id,),
                    )
                else:
                    connection.execute(
                        """UPDATE battle_diagnostics
                           SET lifecycle_status = 'abandoned',
                               terminal_reason = 'sessionRevoked', expires_at = ?
                           WHERE battle_id = ?""",
                        (now, battle_id),
                    )
                if lifecycle != "terminalPending":
                    connection.execute(
                        "DELETE FROM active_battle_leases WHERE battle_id = ?", (battle_id,)
                    )
                connection.commit()
                raise PublicBattleAccessError("battleNotFound", "Battle was not found.")
            binding = connection.execute(
                """SELECT a.slot_id, s.profile_id
                   FROM player_active_slots a
                   LEFT JOIN player_save_slots s
                     ON s.player_id = a.player_id AND s.slot_id = a.slot_id
                   WHERE a.player_id = ?""",
                (player_id,),
            ).fetchone()
            if (
                binding is None
                or binding["slot_id"] != row["slot_id"]
                or binding["profile_id"] != row["profile_id"]
            ):
                if lifecycle == "terminalPending":
                    connection.execute(
                        """UPDATE battle_diagnostics
                           SET terminal_reason = 'launchContextChangedBeforeSettlement'
                           WHERE battle_id = ?""",
                        (battle_id,),
                    )
                else:
                    connection.execute(
                        """UPDATE battle_diagnostics
                           SET lifecycle_status = 'abandoned',
                               terminal_reason = 'launchContextChanged', expires_at = ?
                           WHERE battle_id = ?""",
                        (now, battle_id),
                    )
                if lifecycle != "terminalPending":
                    connection.execute(
                        "DELETE FROM active_battle_leases WHERE battle_id = ?", (battle_id,)
                    )
                connection.commit()
                raise PublicBattleAccessError(
                    "battleLaunchContextChanged",
                    "The battle launch save context is no longer active.",
                )
            connection.commit()
            payload = self._public_battle_payload(row)
            payload["expiredBattleIds"] = expired
            return payload
        except (ProgressionStoreError, SaveSlotAccessError, PublicBattleAccessError):
            if connection.in_transaction:
                connection.rollback()
            raise
        except sqlite3.Error as exc:
            connection.rollback()
            raise ProgressionStoreError(
                "The Public battle could not be authorized. Retry later."
            ) from exc
        finally:
            connection.close()

    def touch_public_battle_after_action(
        self,
        *,
        battle_id: str,
        player_id: str,
        session_id: str,
        session_generation: int,
        inactivity_seconds: int = PUBLIC_BATTLE_INACTIVITY_SECONDS,
    ) -> dict[str, Any]:
        """Reset inactivity only after one newly accepted action fully resolves."""
        connection = self._connection()
        try:
            connection.execute("BEGIN IMMEDIATE")
            self._assert_public_session(
                connection, player_id=player_id, session_id=session_id,
                generation=session_generation,
            )
            row = connection.execute(
                """SELECT l.*, d.lifecycle_status
                   FROM active_battle_leases l
                   JOIN battle_diagnostics d ON d.battle_id = l.battle_id
                   WHERE l.battle_id = ? AND l.player_id = ?""",
                (battle_id, player_id),
            ).fetchone()
            if (
                row is None or row["status"] != "active"
                or row["lifecycle_status"] != "resolving"
                or row["launch_session_id"] != session_id
                or row["session_generation"] != session_generation
            ):
                raise PublicBattleAccessError(
                    "battleNoLongerActive", "The battle is no longer active."
                )
            now = self._timestamp()
            expires_at = self._timestamp_after(inactivity_seconds)
            connection.execute(
                "UPDATE active_battle_leases SET expires_at = ? WHERE battle_id = ?",
                (expires_at, battle_id),
            )
            connection.execute(
                """UPDATE battle_diagnostics
                   SET lifecycle_status = 'active', last_accepted_action_at = ?,
                       expires_at = ?
                   WHERE battle_id = ?""",
                (now, expires_at, battle_id),
            )
            diagnostic = connection.execute(
                "SELECT * FROM battle_diagnostics WHERE battle_id = ?", (battle_id,)
            ).fetchone()
            connection.commit()
            return self._public_battle_payload(diagnostic)
        except (ProgressionStoreError, SaveSlotAccessError, PublicBattleAccessError):
            connection.rollback()
            raise
        except sqlite3.Error as exc:
            connection.rollback()
            raise ProgressionStoreError(
                "The Public battle inactivity deadline could not be updated."
            ) from exc
        finally:
            connection.close()

    def begin_public_battle_action(
        self,
        *,
        battle_id: str,
        player_id: str,
        session_id: str,
        session_generation: int,
    ) -> dict[str, Any]:
        """Protect a newly accepted action from concurrent expiry cleanup."""
        connection = self._connection()
        try:
            connection.execute("BEGIN IMMEDIATE")
            self._assert_public_session(
                connection, player_id=player_id, session_id=session_id,
                generation=session_generation,
            )
            now = self._timestamp()
            row = connection.execute(
                """SELECT l.*, d.lifecycle_status
                   FROM active_battle_leases l
                   JOIN battle_diagnostics d ON d.battle_id = l.battle_id
                   WHERE l.battle_id = ? AND l.player_id = ?""",
                (battle_id, player_id),
            ).fetchone()
            if row is None:
                raise PublicBattleAccessError(
                    "battleNoLongerActive", "The battle is no longer active."
                )
            if row["expires_at"] <= now:
                self._expire_public_battles_tx(connection, now=now)
                connection.commit()
                raise PublicBattleAccessError(
                    "battleExpired", "The battle expired due to inactivity."
                )
            if (
                row["status"] != "active"
                or row["lifecycle_status"] != "active"
                or row["launch_session_id"] != session_id
                or row["session_generation"] != session_generation
            ):
                raise PublicBattleAccessError(
                    "battleNoLongerActive", "The battle is no longer active."
                )
            connection.execute(
                """UPDATE battle_diagnostics SET lifecycle_status = 'resolving'
                   WHERE battle_id = ?""",
                (battle_id,),
            )
            connection.commit()
            return {"acceptedAt": now, "previousExpiresAt": row["expires_at"]}
        except (ProgressionStoreError, SaveSlotAccessError, PublicBattleAccessError):
            if connection.in_transaction:
                connection.rollback()
            raise
        except sqlite3.Error as exc:
            connection.rollback()
            raise ProgressionStoreError(
                "The Public battle action could not begin safely."
            ) from exc
        finally:
            connection.close()

    def cancel_public_battle_action(
        self,
        *,
        battle_id: str,
        player_id: str,
        session_id: str,
        session_generation: int,
    ) -> bool:
        """Restore the pre-action lifecycle after an unexpected engine failure."""
        connection = self._connection()
        try:
            connection.execute("BEGIN IMMEDIATE")
            current = connection.execute(
                """SELECT p.session_generation, s_current.expires_at,
                          EXISTS(
                              SELECT 1 FROM player_sessions s
                              WHERE s.session_id = ? AND s.player_id = ?
                                AND s.generation = ? AND s.revoked_at IS NULL
                          ) AS session_active
                   FROM players p
                   LEFT JOIN player_sessions s_current ON s_current.session_id = ?
                   WHERE p.player_id = ?""",
                (
                    session_id, player_id, session_generation,
                    session_id, player_id,
                ),
            ).fetchone()
            session_still_active = bool(
                current is not None
                and current["session_generation"] == session_generation
                and current["session_active"]
                and current["expires_at"] is not None
                and current["expires_at"] > self._timestamp()
            )
            if session_still_active:
                connection.execute(
                    """UPDATE battle_diagnostics SET lifecycle_status = 'active'
                       WHERE battle_id = ? AND player_id = ?
                         AND launch_session_id = ? AND session_generation = ?
                         AND lifecycle_status = 'resolving'""",
                    (battle_id, player_id, session_id, session_generation),
                )
            else:
                connection.execute(
                    """UPDATE battle_diagnostics
                       SET lifecycle_status = 'abandoned',
                           terminal_reason = 'sessionRevokedDuringResolution'
                       WHERE battle_id = ? AND player_id = ?
                         AND lifecycle_status = 'resolving'""",
                    (battle_id, player_id),
                )
                connection.execute(
                    "DELETE FROM active_battle_leases WHERE battle_id = ?",
                    (battle_id,),
                )
            connection.commit()
            return not session_still_active
        except sqlite3.Error as exc:
            connection.rollback()
            raise ProgressionStoreError(
                "The failed Public battle action could not be released."
            ) from exc
        finally:
            connection.close()

    def mark_public_battle_terminal_pending(
        self,
        *,
        battle_id: str,
        player_id: str,
        session_id: str,
        session_generation: int,
        outcome: dict[str, Any],
    ) -> dict[str, Any]:
        """Retain capacity while terminal settlement is retryable."""
        connection = self._connection()
        try:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute(
                """UPDATE battle_diagnostics
                   SET lifecycle_status = 'terminalPending', outcome = ?, outcome_at = ?
                   WHERE battle_id = ? AND player_id = ?
                     AND launch_session_id = ? AND session_generation = ?
                     AND lifecycle_status IN ('active', 'resolving', 'terminalPending')""",
                (
                    json.dumps(outcome, sort_keys=True, separators=(",", ":")),
                    self._timestamp(), battle_id, player_id, session_id,
                    session_generation,
                ),
            )
            if cursor.rowcount != 1:
                raise PublicBattleAccessError(
                    "battleNoLongerActive", "The battle is no longer active."
                )
            row = connection.execute(
                "SELECT * FROM battle_diagnostics WHERE battle_id = ?", (battle_id,)
            ).fetchone()
            connection.commit()
            return self._public_battle_payload(row)
        except (ProgressionStoreError, SaveSlotAccessError, PublicBattleAccessError):
            connection.rollback()
            raise
        except sqlite3.Error as exc:
            connection.rollback()
            raise ProgressionStoreError(
                "The Public terminal outcome could not be retained."
            ) from exc
        finally:
            connection.close()

    def resign_public_battle(
        self,
        *,
        battle_id: str,
        player_id: str,
        session_id: str,
        session_generation: int,
    ) -> dict[str, Any]:
        """Idempotently abandon an unfinished owned battle without rewards."""
        connection = self._connection()
        try:
            connection.execute("BEGIN IMMEDIATE")
            self._assert_public_session(
                connection, player_id=player_id, session_id=session_id,
                generation=session_generation,
            )
            now = self._timestamp()
            self._expire_public_battles_tx(connection, now=now)
            row = connection.execute(
                "SELECT * FROM battle_diagnostics WHERE battle_id = ?", (battle_id,)
            ).fetchone()
            if row is None or row["player_id"] != player_id:
                raise PublicBattleAccessError("battleNotFound", "Battle was not found.")
            if row["lifecycle_status"] == "terminalPending":
                raise PublicBattleAccessError(
                    "battleSettlementPending",
                    "The authoritative battle result is pending durable settlement.",
                )
            if row["lifecycle_status"] == "settled":
                stored = connection.execute(
                    "SELECT original_result_json FROM battle_settlements WHERE battle_id = ?",
                    (battle_id,),
                ).fetchone()
                if stored is None:
                    raise ProgressionStoreError(
                        "The settled battle receipt is missing. Retry later."
                    )
                connection.commit()
                return json.loads(stored["original_result_json"])
            if row["lifecycle_status"] in {"abandoned", "expired"}:
                stored = connection.execute(
                    "SELECT original_result_json FROM battle_settlements WHERE battle_id = ?",
                    (battle_id,),
                ).fetchone()
                connection.commit()
                return (
                    json.loads(stored["original_result_json"])
                    if stored is not None else self._public_battle_payload(row)
                )
            if (
                row["launch_session_id"] != session_id
                or row["session_generation"] != session_generation
            ):
                raise PublicBattleAccessError("battleNotFound", "Battle was not found.")
            outcome = {"kind": "abandoned", "reason": "resigned"}
            outcome_json = json.dumps(outcome, sort_keys=True, separators=(",", ":"))
            result = {
                "battleId": battle_id,
                "lifecycleStatus": "abandoned",
                "terminalReason": "resigned",
                "outcome": outcome,
                "serverNow": now,
                "expiresAt": now,
                "settlementStatus": "settled",
            }
            receipt_key = f"resign:{battle_id}"
            connection.execute(
                """INSERT OR IGNORE INTO battle_settlements(
                       battle_id, outcome, settled_at, original_result_json, receipt_key
                   ) VALUES (?, ?, ?, ?, ?)""",
                (
                    battle_id, outcome_json, now,
                    json.dumps(result, sort_keys=True, separators=(",", ":")),
                    receipt_key,
                ),
            )
            connection.execute(
                """UPDATE battle_diagnostics
                   SET lifecycle_status = 'abandoned', terminal_reason = 'resigned',
                       outcome = ?, outcome_at = ?, expires_at = ?,
                       settlement_at = ?, receipt_key = ?
                   WHERE battle_id = ?""",
                (outcome_json, now, now, now, receipt_key, battle_id),
            )
            connection.execute(
                "DELETE FROM active_battle_leases WHERE battle_id = ?", (battle_id,)
            )
            connection.commit()
            return result
        except (ProgressionStoreError, SaveSlotAccessError, PublicBattleAccessError):
            if connection.in_transaction:
                connection.rollback()
            raise
        except sqlite3.Error as exc:
            connection.rollback()
            raise ProgressionStoreError("The battle could not be resigned. Retry later.") from exc
        finally:
            connection.close()

    def _before_public_settlement_commit(
        self, connection: sqlite3.Connection, battle_id: str
    ) -> None:
        """Test seam for fault injection immediately before durable confirmation."""
        del connection, battle_id

    def settle_public_battle(
        self,
        *,
        battle_id: str,
        player_id: str,
        session_id: str,
        session_generation: int,
        outcome: dict[str, Any],
    ) -> dict[str, Any]:
        """Atomically persist outcome, progression effects, receipt, and release."""
        connection = self._connection()
        try:
            connection.execute("BEGIN IMMEDIATE")
            self._assert_public_session(
                connection, player_id=player_id, session_id=session_id,
                generation=session_generation,
            )
            row = connection.execute(
                "SELECT * FROM battle_diagnostics WHERE battle_id = ?", (battle_id,)
            ).fetchone()
            if row is None or row["player_id"] != player_id:
                raise PublicBattleAccessError("battleNotFound", "Battle was not found.")
            existing = connection.execute(
                "SELECT original_result_json FROM battle_settlements WHERE battle_id = ?",
                (battle_id,),
            ).fetchone()
            if existing is not None:
                connection.commit()
                return json.loads(existing["original_result_json"])
            lease = connection.execute(
                """SELECT * FROM active_battle_leases
                   WHERE battle_id = ? AND player_id = ?""",
                (battle_id, player_id),
            ).fetchone()
            if (
                lease is None or lease["status"] != "active"
                or lease["profile_id"] != row["profile_id"]
                or lease["slot_id"] != row["slot_id"]
                or lease["launch_session_id"] != row["launch_session_id"]
                or lease["session_generation"] != row["session_generation"]
            ):
                raise PublicBattleAccessError(
                    "battleNoLongerActive",
                    "The battle no longer has a valid settlement lease.",
                )
            if row["lifecycle_status"] == "resolving" and (
                row["launch_session_id"] != session_id
                or row["session_generation"] != session_generation
            ):
                raise PublicBattleAccessError(
                    "battleSessionRevoked",
                    "The battle session was revoked before durable confirmation.",
                )
            if row["lifecycle_status"] not in {"resolving", "terminalPending"}:
                raise PublicBattleAccessError(
                    "battleNoLongerActive", "The battle is not awaiting settlement."
                )
            if row["lifecycle_status"] == "terminalPending":
                recorded_outcome = (
                    json.loads(row["outcome"]) if row["outcome"] else None
                )
                if recorded_outcome is None or outcome != recorded_outcome:
                    raise PublicBattleAccessError(
                        "battleOutcomeMismatch",
                        "The pending battle outcome does not match the durable record.",
                    )
            binding = connection.execute(
                """SELECT a.slot_id, s.profile_id
                   FROM player_active_slots a
                   LEFT JOIN player_save_slots s
                     ON s.player_id = a.player_id AND s.slot_id = a.slot_id
                   WHERE a.player_id = ?""",
                (player_id,),
            ).fetchone()
            if (
                binding is None or binding["slot_id"] != row["slot_id"]
                or binding["profile_id"] != row["profile_id"]
            ):
                raise PublicBattleAccessError(
                    "battleLaunchContextChanged",
                    "The battle launch save context changed before settlement.",
                )

            result: dict[str, Any] = {"battleId": battle_id, "outcome": outcome}
            friendly_victory = outcome == {
                "kind": "victory", "winningSideId": "friendly"
            }
            context = json.loads(row["context_json"])
            if friendly_victory and row["battle_type"] == "stage":
                result.update(self._commit_stage_victory_tx(
                    connection,
                    battle_id=battle_id,
                    stage_id=context["stageId"],
                    battle_index=context["battleIndex"],
                    mode=context.get("mode", "learner"),
                    profile_id=row["profile_id"],
                ))
            elif friendly_victory and row["battle_type"] == "arena":
                result.update(self._commit_arena_victory_tx(
                    connection,
                    run_id=context["runId"],
                    node_index=context["nodeIndex"],
                    battle_id=battle_id,
                    profile_id=row["profile_id"],
                ))
            else:
                result["alreadyCommitted"] = False

            settled_at = self._timestamp()
            receipt_key = f"battle:{battle_id}"
            outcome_json = json.dumps(outcome, sort_keys=True, separators=(",", ":"))
            result.update({
                "lifecycleStatus": "settled",
                "settlementStatus": "settled",
                "settledAt": settled_at,
            })
            result_json = json.dumps(result, sort_keys=True, separators=(",", ":"))
            connection.execute(
                """INSERT INTO battle_settlements(
                       battle_id, outcome, settled_at, original_result_json, receipt_key
                   ) VALUES (?, ?, ?, ?, ?)""",
                (battle_id, outcome_json, settled_at, result_json, receipt_key),
            )
            connection.execute(
                """UPDATE battle_diagnostics
                   SET lifecycle_status = 'settled', outcome = ?, outcome_at = ?,
                       settlement_at = ?, receipt_key = ?, terminal_reason = NULL,
                       expires_at = ? WHERE battle_id = ?""",
                (
                    outcome_json, settled_at, settled_at, receipt_key, settled_at,
                    battle_id,
                ),
            )
            connection.execute(
                "DELETE FROM active_battle_leases WHERE battle_id = ?", (battle_id,)
            )
            self._before_public_settlement_commit(connection, battle_id)
            connection.commit()
            return result
        except (
            ProgressionStoreError, SaveSlotAccessError, StageAccessError,
            ArenaAccessError, PublicBattleAccessError,
        ):
            connection.rollback()
            raise
        except sqlite3.Error as exc:
            connection.rollback()
            raise ProgressionStoreError(
                "The authoritative battle result could not be settled. Retry later."
            ) from exc
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def public_terminal_pending_battle(
        self,
        *,
        player_id: str,
        session_id: str,
        session_generation: int,
    ) -> dict[str, Any] | None:
        """Return one immutable pending result to the current owner session.

        The current session may be a recovery replacement.  The old launch
        session is retained in diagnostics/lease binding, while this read only
        authorizes the current owner to ask the server to finish the already
        recorded outcome; it never grants gameplay authority.
        """

        connection = self._connection()
        try:
            connection.execute("BEGIN")
            self._assert_public_session(
                connection,
                player_id=player_id,
                session_id=session_id,
                generation=session_generation,
            )
            row = connection.execute(
                """SELECT d.battle_id, d.outcome
                   FROM battle_diagnostics d
                   JOIN active_battle_leases l ON l.battle_id = d.battle_id
                   WHERE d.player_id = ?
                     AND d.lifecycle_status = 'terminalPending'
                     AND l.status = 'active'
                   LIMIT 1""",
                (player_id,),
            ).fetchone()
            if row is None:
                return None
            if row["outcome"] is None:
                raise ProgressionStoreError(
                    "The pending battle outcome is missing. Retry later."
                )
            return {
                "battleId": row["battle_id"],
                "outcome": json.loads(row["outcome"]),
            }
        except (ProgressionStoreError, SaveSlotAccessError):
            raise
        except sqlite3.Error as exc:
            raise ProgressionStoreError(
                "The pending battle result could not be read. Retry later."
            ) from exc
        finally:
            connection.close()

    def public_battle_receipt(
        self,
        *,
        battle_id: str,
        player_id: str,
        session_id: str,
        session_generation: int,
    ) -> dict[str, Any] | None:
        """Return the original durable result to the current owning player."""
        connection = self._connection()
        try:
            connection.execute("BEGIN")
            self._assert_public_session(
                connection, player_id=player_id, session_id=session_id,
                generation=session_generation,
            )
            owner = connection.execute(
                "SELECT player_id FROM battle_diagnostics WHERE battle_id = ?",
                (battle_id,),
            ).fetchone()
            if owner is None or owner["player_id"] != player_id:
                raise PublicBattleAccessError("battleNotFound", "Battle was not found.")
            row = connection.execute(
                "SELECT original_result_json FROM battle_settlements WHERE battle_id = ?",
                (battle_id,),
            ).fetchone()
            return json.loads(row["original_result_json"]) if row else None
        except sqlite3.Error as exc:
            raise ProgressionStoreError(
                "The battle receipt could not be read. Retry later."
            ) from exc
        finally:
            connection.close()

    def invalidate_player_battles_after_revocation(
        self, *, player_id: str, reason: str
    ) -> list[str]:
        """End non-settled battle authority after logout/recovery/context change."""
        if not self.public_mode:
            return []
        connection = self._connection()
        try:
            connection.execute("BEGIN IMMEDIATE")
            rows = connection.execute(
                """SELECT l.battle_id, d.lifecycle_status
                   FROM active_battle_leases l
                   JOIN battle_diagnostics d ON d.battle_id = l.battle_id
                   WHERE l.player_id = ?""",
                (player_id,),
            ).fetchall()
            removable = [
                row["battle_id"] for row in rows
                if row["lifecycle_status"] != "terminalPending"
            ]
            pending = [
                row["battle_id"] for row in rows
                if row["lifecycle_status"] == "terminalPending"
            ]
            now = self._timestamp()
            connection.executemany(
                """UPDATE battle_diagnostics
                   SET lifecycle_status = 'abandoned', terminal_reason = ?,
                       expires_at = ? WHERE battle_id = ?""",
                ((reason, now, battle_id) for battle_id in removable),
            )
            connection.executemany(
                """UPDATE battle_diagnostics SET terminal_reason = ?
                   WHERE battle_id = ?""",
                ((f"{reason}BeforeSettlement", battle_id) for battle_id in pending),
            )
            connection.executemany(
                "DELETE FROM active_battle_leases WHERE battle_id = ?",
                ((battle_id,) for battle_id in removable),
            )
            connection.commit()
            # terminalPending retains its RAM session for bounded trusted
            # settlement retry.  Callers should evict only battles whose
            # authority was actually ended here.
            return removable
        except sqlite3.Error as exc:
            connection.rollback()
            raise ProgressionStoreError(
                "Revoked Public battle authority could not be invalidated."
            ) from exc
        finally:
            connection.close()

    def assert_public_battle_context_change_allowed(self, *, player_id: str) -> None:
        """Block destructive context changes while settlement needs RAM retry."""

        if not self.public_mode:
            return
        connection = self._connection()
        try:
            row = connection.execute(
                """SELECT 1 FROM active_battle_leases l
                   JOIN battle_diagnostics d ON d.battle_id = l.battle_id
                   WHERE l.player_id = ? AND d.lifecycle_status = 'terminalPending'
                   LIMIT 1""",
                (player_id,),
            ).fetchone()
            if row is not None:
                raise SaveSlotAccessError(
                    "battleSettlementPending",
                    "The current battle result is still being settled. Retry later.",
                )
        except sqlite3.Error as exc:
            raise ProgressionStoreError(
                "The Public battle context could not be checked. Retry later."
            ) from exc
        finally:
            connection.close()

    def reconcile_public_battles_after_restart(self) -> list[str]:
        """Expire RAM-dependent active/provisional battles after process restart."""
        if not self.public_mode:
            return []
        connection = self._connection()
        try:
            connection.execute("BEGIN IMMEDIATE")
            rows = connection.execute(
                """SELECT l.battle_id FROM active_battle_leases l
                   JOIN battle_diagnostics d ON d.battle_id = l.battle_id
                   WHERE d.lifecycle_status IN (
                       'provisional', 'active', 'resolving', 'terminalPending'
                   )"""
            ).fetchall()
            battle_ids = [row["battle_id"] for row in rows]
            now = self._timestamp()
            connection.executemany(
                """UPDATE battle_diagnostics
                   SET lifecycle_status = 'expired', terminal_reason = 'serverRestart',
                       outcome = ?, outcome_at = ?, expires_at = ?
                   WHERE battle_id = ?""",
                (
                    (
                        json.dumps({"kind": "abandoned", "reason": "serverRestart"},
                                   sort_keys=True, separators=(",", ":")),
                        now, now, battle_id,
                    )
                    for battle_id in battle_ids
                ),
            )
            connection.execute("DELETE FROM active_battle_leases")
            connection.commit()
            return battle_ids
        except sqlite3.Error as exc:
            connection.rollback()
            raise ProgressionStoreError(
                "Public battle restart reconciliation failed."
            ) from exc
        finally:
            connection.close()

    def _connection(self) -> sqlite3.Connection:
        self.ensure_initialized()
        try:
            return self._connect_existing()
        except (OSError, sqlite3.Error) as exc:
            raise ProgressionStoreError(
                "Persistent progression is unavailable or missing. Retry later."
            ) from exc

    @staticmethod
    def _validate_slot_id(slot_id: int) -> None:
        if slot_id not in SAVE_SLOT_IDS:
            raise SaveSlotAccessError(
                "invalidSaveSlot", "slotId must be an integer from 1 through 5."
            )

    def _assert_public_session(
        self,
        connection: sqlite3.Connection,
        *,
        player_id: str | None,
        session_id: str | None,
        generation: int | None,
    ) -> None:
        if not self.public_mode:
            return
        if not player_id or not session_id or generation is None:
            raise SaveSlotAccessError("authenticationRequired", "Authentication required.")
        row = connection.execute(
            """SELECT s.player_id, s.generation, s.revoked_at, s.expires_at,
                      p.session_generation, p.recovery_confirmed_at
               FROM player_sessions s
               JOIN players p ON p.player_id = s.player_id
               WHERE s.session_id = ?""",
            (session_id,),
        ).fetchone()
        if (
            row is None
            or row["player_id"] != player_id
            or row["generation"] != generation
            or row["session_generation"] != generation
            or row["revoked_at"] is not None
        ):
            raise SaveSlotAccessError(
                "sessionRevoked", "The player session is no longer active."
            )
        if row["expires_at"] <= self._timestamp():
            raise SaveSlotAccessError(
                "sessionExpired", "The player session has expired."
            )
        if row["recovery_confirmed_at"] is None:
            raise SaveSlotAccessError(
                "recoveryConfirmationRequired",
                "Confirm that you saved your Recovery Code first.",
            )

    def _active_profile_id(
        self, connection: sqlite3.Connection, player_id: str | None = None
    ) -> str:
        if self.public_mode:
            if not player_id:
                raise SaveSlotAccessError("authenticationRequired", "Authentication required.")
            row = connection.execute(
                """SELECT s.profile_id FROM player_active_slots a
                   LEFT JOIN player_save_slots s
                     ON s.player_id = a.player_id AND s.slot_id = a.slot_id
                   WHERE a.player_id = ?""",
                (player_id,),
            ).fetchone()
        else:
            row = connection.execute(
                """SELECT s.profile_id FROM active_slot a
                   LEFT JOIN save_slots s ON s.slot_id = a.slot_id
                   WHERE a.singleton_id = 1"""
            ).fetchone()
        if row is None or row["profile_id"] is None:
            raise SaveSlotAccessError(
                "noActiveSaveSlot",
                "Create or load a save slot before accessing progression.",
            )
        return row["profile_id"]

    def active_profile_id(self, player_id: str | None = None) -> str:
        connection = self._connection()
        try:
            return self._active_profile_id(connection, player_id)
        except sqlite3.Error as exc:
            raise ProgressionStoreError(
                "Persistent progression could not be read. Retry later."
            ) from exc
        finally:
            connection.close()

    def list_save_slots(
        self,
        player_id: str | None = None,
        session_id: str | None = None,
        session_generation: int | None = None,
    ) -> dict[str, Any]:
        connection = self._connection()
        try:
            if self.public_mode:
                connection.execute("BEGIN")
                self._assert_public_session(
                    connection, player_id=player_id, session_id=session_id,
                    generation=session_generation,
                )
            if self.public_mode:
                if not player_id:
                    raise SaveSlotAccessError("authenticationRequired", "Authentication required.")
                active = connection.execute(
                    "SELECT slot_id FROM player_active_slots WHERE player_id = ?",
                    (player_id,),
                ).fetchone()
                rows = connection.execute(
                    """SELECT slot_id, profile_id, created_at, last_played_at
                       FROM player_save_slots WHERE player_id = ? ORDER BY slot_id""",
                    (player_id,),
                ).fetchall()
            else:
                active = connection.execute(
                    "SELECT slot_id FROM active_slot WHERE singleton_id = 1"
                ).fetchone()
                rows = connection.execute(
                    """SELECT slot_id, profile_id, created_at, last_played_at
                       FROM save_slots ORDER BY slot_id"""
                ).fetchall()
            active_slot_id = active["slot_id"] if active else None
            return {
                "activeSlotId": active_slot_id,
                "slots": [self._slot_summary(row, active_slot_id) for row in rows],
            }
        except sqlite3.Error as exc:
            raise ProgressionStoreError(
                "Save slots could not be read. Retry later."
            ) from exc
        finally:
            connection.close()

    @staticmethod
    def _slot_summary(row: sqlite3.Row, active_slot_id: int | None) -> dict[str, Any]:
        return {
            "slotId": row["slot_id"],
            "occupied": row["profile_id"] is not None,
            "profileId": row["profile_id"],
            "createdAt": row["created_at"],
            "lastPlayedAt": row["last_played_at"],
            "active": row["slot_id"] == active_slot_id,
        }

    def create_save_slot(
        self,
        slot_id: int,
        player_id: str | None = None,
        session_id: str | None = None,
        session_generation: int | None = None,
    ) -> dict[str, Any]:
        return self._initialize_slot(
            slot_id, overwrite=False, player_id=player_id,
            session_id=session_id, session_generation=session_generation,
        )

    def overwrite_save_slot(
        self,
        slot_id: int,
        player_id: str | None = None,
        session_id: str | None = None,
        session_generation: int | None = None,
    ) -> dict[str, Any]:
        return self._initialize_slot(
            slot_id, overwrite=True, player_id=player_id,
            session_id=session_id, session_generation=session_generation,
        )

    def _initialize_slot(
        self,
        slot_id: int,
        *,
        overwrite: bool,
        player_id: str | None = None,
        session_id: str | None = None,
        session_generation: int | None = None,
    ) -> dict[str, Any]:
        self._validate_slot_id(slot_id)
        connection = self._connection()
        try:
            connection.execute("BEGIN IMMEDIATE")
            self._assert_public_session(
                connection, player_id=player_id, session_id=session_id,
                generation=session_generation,
            )
            if self.public_mode:
                if not player_id:
                    raise SaveSlotAccessError("authenticationRequired", "Authentication required.")
                row = connection.execute(
                    """SELECT profile_id FROM player_save_slots
                       WHERE player_id = ? AND slot_id = ?""",
                    (player_id, slot_id),
                ).fetchone()
            else:
                row = connection.execute(
                    "SELECT profile_id FROM save_slots WHERE slot_id = ?", (slot_id,)
                ).fetchone()
            if row is None:
                raise ProgressionStoreError(
                    "The save-slot catalogue is incomplete. Retry later."
                )
            old_profile_id = row["profile_id"]
            if old_profile_id is not None and not overwrite:
                raise SaveSlotAccessError(
                    "slotOccupied",
                    f"Save slot {slot_id} is occupied; confirmed overwrite is required.",
                )
            if old_profile_id is None and overwrite:
                raise SaveSlotAccessError(
                    "loadEmptySlot", f"Save slot {slot_id} is empty."
                )
            if old_profile_id is not None:
                for table in (
                    "stage_mode_completions",
                    "battle_completions",
                    "granted_rewards",
                    "stage_progress",
                    "unlocked_heroes",
                ):
                    connection.execute(
                        f"DELETE FROM {table} WHERE profile_id = ?", (old_profile_id,)
                    )
                if self.public_mode:
                    connection.execute(
                        """UPDATE player_save_slots
                           SET profile_id = NULL, created_at = NULL, last_played_at = NULL
                           WHERE player_id = ? AND slot_id = ?""",
                        (player_id, slot_id),
                    )
                else:
                    connection.execute(
                        "UPDATE save_slots SET profile_id = NULL, created_at = NULL, "
                        "last_played_at = NULL WHERE slot_id = ?",
                        (slot_id,),
                    )
                connection.execute(
                    "DELETE FROM profiles WHERE profile_id = ?", (old_profile_id,)
                )
            profile_id = (
                f"profile.public.{player_id}.slot.{slot_id}.{uuid.uuid4().hex}"
                if self.public_mode else
                f"profile.local.slot.{slot_id}.{uuid.uuid4().hex}"
            )
            now = self._timestamp()
            connection.execute(
                "INSERT INTO profiles(profile_id) VALUES (?)", (profile_id,)
            )
            connection.executemany(
                "INSERT INTO unlocked_heroes(profile_id, definition_id) VALUES (?, ?)",
                ((profile_id, hero_id) for hero_id in INITIAL_UNLOCKED_HERO_IDS),
            )
            connection.executemany(
                """INSERT INTO stage_progress(
                       profile_id, stage_id, highest_completed_battle, completed
                   ) VALUES (?, ?, 0, 0)""",
                ((profile_id, stage_id) for stage_id in STAGE_BATTLES),
            )
            if self.public_mode:
                connection.execute(
                    """UPDATE player_save_slots SET profile_id = ?, created_at = ?,
                           last_played_at = ? WHERE player_id = ? AND slot_id = ?""",
                    (profile_id, now, now, player_id, slot_id),
                )
                connection.execute(
                    "UPDATE player_active_slots SET slot_id = ? WHERE player_id = ?",
                    (slot_id, player_id),
                )
            else:
                connection.execute(
                    """UPDATE save_slots SET profile_id = ?, created_at = ?,
                           last_played_at = ? WHERE slot_id = ?""",
                    (profile_id, now, now, slot_id),
                )
                connection.execute(
                    "UPDATE active_slot SET slot_id = ? WHERE singleton_id = 1", (slot_id,)
                )
            progression = self._read_progression(connection, profile_id)
            slot = connection.execute(
                ("""SELECT slot_id, profile_id, created_at, last_played_at
                    FROM player_save_slots WHERE player_id = ? AND slot_id = ?"""
                 if self.public_mode else
                 """SELECT slot_id, profile_id, created_at, last_played_at
                    FROM save_slots WHERE slot_id = ?"""),
                ((player_id, slot_id) if self.public_mode else (slot_id,)),
            ).fetchone()
            connection.commit()
            return {
                "activeSlotId": slot_id,
                "slot": self._slot_summary(slot, slot_id),
                "progression": progression,
            }
        except (ProgressionStoreError, SaveSlotAccessError):
            connection.rollback()
            raise
        except sqlite3.Error as exc:
            connection.rollback()
            raise ProgressionStoreError(
                "The save slot could not be initialized. Retry later."
            ) from exc
        finally:
            connection.close()

    def load_save_slot(
        self,
        slot_id: int,
        player_id: str | None = None,
        session_id: str | None = None,
        session_generation: int | None = None,
    ) -> dict[str, Any]:
        self._validate_slot_id(slot_id)
        connection = self._connection()
        try:
            connection.execute("BEGIN IMMEDIATE")
            self._assert_public_session(
                connection, player_id=player_id, session_id=session_id,
                generation=session_generation,
            )
            if self.public_mode:
                if not player_id:
                    raise SaveSlotAccessError("authenticationRequired", "Authentication required.")
                row = connection.execute(
                    """SELECT slot_id, profile_id, created_at, last_played_at
                       FROM player_save_slots WHERE player_id = ? AND slot_id = ?""",
                    (player_id, slot_id),
                ).fetchone()
            else:
                row = connection.execute(
                    """SELECT slot_id, profile_id, created_at, last_played_at
                       FROM save_slots WHERE slot_id = ?""",
                    (slot_id,),
                ).fetchone()
            if row is None or row["profile_id"] is None:
                raise SaveSlotAccessError(
                    "loadEmptySlot", f"Save slot {slot_id} is empty."
                )
            now = self._timestamp()
            if self.public_mode:
                connection.execute(
                    """UPDATE player_save_slots SET last_played_at = ?
                       WHERE player_id = ? AND slot_id = ?""",
                    (now, player_id, slot_id),
                )
                connection.execute(
                    "UPDATE player_active_slots SET slot_id = ? WHERE player_id = ?",
                    (slot_id, player_id),
                )
            else:
                connection.execute(
                    "UPDATE save_slots SET last_played_at = ? WHERE slot_id = ?",
                    (now, slot_id),
                )
                connection.execute(
                    "UPDATE active_slot SET slot_id = ? WHERE singleton_id = 1", (slot_id,)
                )
            progression = self._read_progression(connection, row["profile_id"])
            updated = connection.execute(
                ("""SELECT slot_id, profile_id, created_at, last_played_at
                    FROM player_save_slots WHERE player_id = ? AND slot_id = ?"""
                 if self.public_mode else
                 """SELECT slot_id, profile_id, created_at, last_played_at
                    FROM save_slots WHERE slot_id = ?"""),
                ((player_id, slot_id) if self.public_mode else (slot_id,)),
            ).fetchone()
            connection.commit()
            return {
                "activeSlotId": slot_id,
                "slot": self._slot_summary(updated, slot_id),
                "progression": progression,
            }
        except (ProgressionStoreError, SaveSlotAccessError):
            connection.rollback()
            raise
        except sqlite3.Error as exc:
            connection.rollback()
            raise ProgressionStoreError(
                "The save slot could not be loaded. Retry later."
            ) from exc
        finally:
            connection.close()

    def read_progression(
        self,
        player_id: str | None = None,
        session_id: str | None = None,
        session_generation: int | None = None,
    ) -> dict[str, Any]:
        connection: sqlite3.Connection | None = None
        try:
            connection = self._connection()
            if self.public_mode:
                connection.execute("BEGIN")
                self._assert_public_session(
                    connection, player_id=player_id, session_id=session_id,
                    generation=session_generation,
                )
            return self._read_progression(
                connection, self._active_profile_id(connection, player_id)
            )
        except (ProgressionStoreError, SaveSlotAccessError):
            raise
        except sqlite3.Error as exc:
            raise ProgressionStoreError(
                "Persistent progression could not be read. Retry later."
            ) from exc
        finally:
            if connection is not None:
                connection.close()

    def _read_progression(
        self, connection: sqlite3.Connection, profile_id: str
    ) -> dict[str, Any]:
        unlocked = [
            row["definition_id"]
            for row in connection.execute(
                """SELECT definition_id FROM unlocked_heroes
                   WHERE profile_id = ? ORDER BY definition_id""",
                (profile_id,),
            )
        ]
        progress_rows = connection.execute(
            """SELECT stage_id, highest_completed_battle, completed
               FROM stage_progress WHERE profile_id = ? ORDER BY stage_id""",
            (profile_id,),
        ).fetchall()
        if {row["stage_id"] for row in progress_rows} != set(STAGE_BATTLES):
            raise ProgressionStoreError(
                "The stored stage progression is incomplete or corrupt. Retry later."
            )
        if any(
            bool(row["completed"])
            != (row["highest_completed_battle"] == len(STAGE_BATTLES[row["stage_id"]]))
            for row in progress_rows
        ):
            raise ProgressionStoreError(
                "The stored stage completion state is corrupt. Retry later."
            )
        has_mode_table = connection.execute(
            """SELECT 1 FROM sqlite_master
               WHERE type = 'table' AND name = 'stage_mode_completions'"""
        ).fetchone()
        mode_rows = (
            connection.execute(
                """SELECT stage_id, battle_index, mode
                   FROM stage_mode_completions
                   WHERE profile_id = ?
                   ORDER BY stage_id, mode, battle_index""",
                (profile_id,),
            ).fetchall()
            if has_mode_table is not None
            else [
                {
                    "stage_id": row["stage_id"],
                    "battle_index": battle_index,
                    "mode": "learner",
                }
                for row in progress_rows
                for battle_index in range(1, row["highest_completed_battle"] + 1)
            ]
        )
        completed_by_stage_mode: dict[tuple[str, str], list[int]] = {}
        for row in mode_rows:
            battles = STAGE_BATTLES.get(row["stage_id"])
            if (
                battles is None
                or row["mode"] not in {"learner", "tactics"}
                or row["battle_index"] < 1
                or row["battle_index"] > len(battles)
            ):
                raise ProgressionStoreError(
                    "The stored campaign-mode completion is corrupt. Retry later."
                )
            completed_by_stage_mode.setdefault(
                (row["stage_id"], row["mode"]), []
            ).append(row["battle_index"])
        for row in progress_rows:
            expected_learner = list(range(1, row["highest_completed_battle"] + 1))
            if completed_by_stage_mode.get((row["stage_id"], "learner"), []) != expected_learner:
                raise ProgressionStoreError(
                    "The stored Learner completion history is corrupt. Retry later."
                )
            if (
                completed_by_stage_mode.get((row["stage_id"], "tactics"), [])
                and row["highest_completed_battle"]
                != len(STAGE_BATTLES[row["stage_id"]])
            ):
                raise ProgressionStoreError(
                    "The stored Tactics completion history is locked or corrupt. Retry later."
                )
        if not set(unlocked).issubset(ALL_HERO_IDS):
            raise ProgressionStoreError(
                "The stored hero progression is corrupt. Retry later."
            )
        rewards = [
            {"rewardId": row["reward_id"], "count": row["count"]}
            for row in connection.execute(
                """SELECT reward_id, count FROM granted_rewards
                   WHERE profile_id = ? ORDER BY reward_id""",
                (profile_id,),
            )
        ]
        if any(reward["count"] != 1 for reward in rewards):
            raise ProgressionStoreError(
                "The stored reward progression is corrupt. Retry later."
            )
        return {
            "profileId": profile_id,
            "unlockedHeroDefinitionIds": unlocked,
            "stageProgress": [
                self._progress_row(
                    row["stage_id"],
                    row["highest_completed_battle"],
                    completed_by_stage_mode,
                )
                for row in progress_rows
            ],
            "grantedRewards": rewards,
        }

    @staticmethod
    def _progress_row(
        stage_id: str,
        highest_completed: int,
        completed_by_stage_mode: dict[tuple[str, str], list[int]],
    ) -> dict[str, Any]:
        required_count = len(STAGE_BATTLES[stage_id])  # type: ignore[index]
        learner_completed = completed_by_stage_mode.get((stage_id, "learner"), [])
        tactics_completed = completed_by_stage_mode.get((stage_id, "tactics"), [])
        modes = {
            "learner": {
                "available": True,
                "completed": len(learner_completed) == required_count,
                "completedBattleIndices": learner_completed,
            },
            "tactics": {
                "available": len(learner_completed) == required_count,
                "completed": len(tactics_completed) == required_count,
                "completedBattleIndices": tactics_completed,
            },
        }
        return {
            "stageId": stage_id,
            "highestCompletedBattle": highest_completed,
            "unlockedBattle": min(highest_completed + 1, required_count),
            "completed": highest_completed == required_count,
            "modes": modes,
        }

    def assert_player_team_unlocked(
        self,
        definition_ids: list[str],
        expected_profile_id: str | None = None,
        *,
        player_id: str | None = None,
        session_id: str | None = None,
        session_generation: int | None = None,
    ) -> None:
        connection = self._connection()
        try:
            if self.public_mode:
                connection.execute("BEGIN")
                self._assert_public_session(
                    connection, player_id=player_id, session_id=session_id,
                    generation=session_generation,
                )
            profile_id = self._active_profile_id(connection, player_id)
            if expected_profile_id is not None and profile_id != expected_profile_id:
                raise SaveSlotAccessError(
                    "activeSaveSlotChanged",
                    "The active save slot changed; start the battle again.",
                )
            unlocked = {
                row["definition_id"]
                for row in connection.execute(
                    "SELECT definition_id FROM unlocked_heroes WHERE profile_id = ?",
                    (profile_id,),
                )
            }
            locked = sorted(set(definition_ids) - unlocked)
            if locked:
                raise StageAccessError(
                    "heroLocked",
                    f"The player profile has not unlocked: {', '.join(locked)}.",
                )
        except (ProgressionStoreError, SaveSlotAccessError, StageAccessError):
            raise
        except sqlite3.Error as exc:
            raise ProgressionStoreError(
                "Player roster access could not be checked. Retry later."
            ) from exc
        finally:
            connection.close()

    @staticmethod
    def _decode_hero_ids(value: str, *, expected_count: int) -> list[str]:
        try:
            decoded = json.loads(value)
        except (TypeError, json.JSONDecodeError) as exc:
            raise ProgressionStoreError(
                "The stored Arena Run is corrupt. Retry later."
            ) from exc
        if (
            not isinstance(decoded, list)
            or len(decoded) != expected_count
            or any(not isinstance(hero_id, str) for hero_id in decoded)
            or any(hero_id not in ALL_HERO_IDS for hero_id in decoded)
        ):
            raise ProgressionStoreError(
                "The stored Arena Run is corrupt. Retry later."
            )
        return decoded

    def _read_arena_run(
        self, connection: sqlite3.Connection, profile_id: str
    ) -> dict[str, Any] | None:
        run = connection.execute(
            """SELECT run_id, run_schema_version, status, squad_json,
                      current_node_index, created_at, completed_at
               FROM arena_runs WHERE profile_id = ?""",
            (profile_id,),
        ).fetchone()
        if run is None:
            return None
        if run["run_schema_version"] != ARENA_RUN_SCHEMA_VERSION:
            raise ProgressionStoreError(
                "The stored Arena Run has an unsupported version. Retry later."
            )
        squad = self._decode_hero_ids(
            run["squad_json"], expected_count=ARENA_REQUIRED_HERO_COUNT
        )
        if len(set(squad)) != ARENA_REQUIRED_HERO_COUNT:
            raise ProgressionStoreError(
                "The stored Arena squad is corrupt. Retry later."
            )
        rows = connection.execute(
            """SELECT node_index, battle_size, enemy_formation, enemy_team_json,
                      battle_seed, completed, completion_battle_id
               FROM arena_nodes WHERE run_id = ? ORDER BY node_index""",
            (run["run_id"],),
        ).fetchall()
        if [row["node_index"] for row in rows] != list(
            range(1, ARENA_NODE_COUNT + 1)
        ):
            raise ProgressionStoreError(
                "The stored Arena schedule is incomplete or corrupt. Retry later."
            )
        nodes: list[dict[str, Any]] = []
        for row in rows:
            size = row["battle_size"]
            enemies = self._decode_hero_ids(
                row["enemy_team_json"], expected_count=size
            )
            formation = row["enemy_formation"]
            valid_formations = {
                1: {None},
                2: {"front-rear", "side-by-side"},
                3: {"one-front-two-rear", "two-front-one-rear", "all-front"},
            }[size]
            if formation not in valid_formations:
                raise ProgressionStoreError(
                    "The stored Arena formation is corrupt. Retry later."
                )
            positions = {
                None: ("front",),
                "side-by-side": ("front", "front"),
                "front-rear": ("front", "rear"),
                "all-front": ("front", "front", "front"),
                "two-front-one-rear": ("front", "front", "rear"),
                "one-front-two-rear": ("front", "rear", "rear"),
            }[formation]
            if formation not in {None, "side-by-side", "all-front"}:
                if any(
                    hero_id not in (
                        ARENA_FRONT_HERO_IDS if position == "front"
                        else ARENA_REAR_HERO_IDS
                    )
                    for hero_id, position in zip(enemies, positions, strict=True)
                ):
                    raise ProgressionStoreError(
                        "The stored Arena enemy positions are corrupt. Retry later."
                    )
            completed = bool(row["completed"])
            if completed != (row["completion_battle_id"] is not None):
                raise ProgressionStoreError(
                    "The stored Arena completion is corrupt. Retry later."
                )
            nodes.append({
                "nodeIndex": row["node_index"],
                "battleSize": size,
                "enemyFormation": formation,
                "enemyDefinitionIds": enemies,
                "battleSeed": row["battle_seed"],
                "completed": completed,
                "completionBattleId": row["completion_battle_id"],
            })
        first_unresolved = next(
            (node["nodeIndex"] for node in nodes if not node["completed"]), None
        )
        if run["status"] == "active" and run["current_node_index"] != first_unresolved:
            raise ProgressionStoreError(
                "The stored Arena progress is corrupt. Retry later."
            )
        if run["status"] == "completed" and first_unresolved is not None:
            raise ProgressionStoreError(
                "The stored Arena completion is corrupt. Retry later."
            )
        return {
            "runId": run["run_id"],
            "status": run["status"],
            "squadDefinitionIds": squad,
            "currentNodeIndex": run["current_node_index"],
            "createdAt": run["created_at"],
            "completedAt": run["completed_at"],
            "nodes": nodes,
        }

    def _arena_state(
        self, connection: sqlite3.Connection, profile_id: str
    ) -> dict[str, Any]:
        unlocked_count = connection.execute(
            "SELECT COUNT(*) FROM unlocked_heroes WHERE profile_id = ?",
            (profile_id,),
        ).fetchone()[0]
        return {
            "profileId": profile_id,
            "eligibility": {
                "eligible": unlocked_count >= ARENA_REQUIRED_HERO_COUNT,
                "unlockedHeroCount": unlocked_count,
                "requiredHeroCount": ARENA_REQUIRED_HERO_COUNT,
            },
            "run": self._read_arena_run(connection, profile_id),
        }

    def read_arena_state(
        self,
        player_id: str | None = None,
        session_id: str | None = None,
        session_generation: int | None = None,
    ) -> dict[str, Any]:
        connection = self._connection()
        try:
            if self.public_mode:
                connection.execute("BEGIN")
                self._assert_public_session(
                    connection, player_id=player_id, session_id=session_id,
                    generation=session_generation,
                )
            return self._arena_state(
                connection, self._active_profile_id(connection, player_id)
            )
        except (ProgressionStoreError, SaveSlotAccessError):
            raise
        except sqlite3.Error as exc:
            raise ProgressionStoreError(
                "Arena progression could not be read. Retry later."
            ) from exc
        finally:
            connection.close()

    @staticmethod
    def _generate_arena_nodes(schedule_seed: int) -> list[dict[str, Any]]:
        generator = random.Random(schedule_seed)
        battle_sizes = [1, 1, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3]
        generator.shuffle(battle_sizes)
        nodes: list[dict[str, Any]] = []
        for node_index, size in enumerate(battle_sizes, start=1):
            if size == 1:
                formation = None
                pools = (tuple(sorted(ALL_HERO_IDS)),)
            elif size == 2:
                formation = generator.choice(("front-rear", "side-by-side"))
                pools = (
                    (ARENA_FRONT_HERO_IDS, ARENA_REAR_HERO_IDS)
                    if formation == "front-rear"
                    else (tuple(sorted(ALL_HERO_IDS)),) * 2
                )
            else:
                formation = generator.choice((
                    "one-front-two-rear", "two-front-one-rear", "all-front"
                ))
                pools = {
                    "one-front-two-rear": (
                        ARENA_FRONT_HERO_IDS, ARENA_REAR_HERO_IDS, ARENA_REAR_HERO_IDS
                    ),
                    "two-front-one-rear": (
                        ARENA_FRONT_HERO_IDS, ARENA_FRONT_HERO_IDS, ARENA_REAR_HERO_IDS
                    ),
                    "all-front": (tuple(sorted(ALL_HERO_IDS)),) * 3,
                }[formation]
            nodes.append({
                "nodeIndex": node_index,
                "battleSize": size,
                "enemyFormation": formation,
                "enemyDefinitionIds": [generator.choice(pool) for pool in pools],
                "battleSeed": generator.randrange(0, 2**63),
            })
        return nodes

    def create_arena_run(
        self,
        squad_definition_ids: list[str],
        *,
        schedule_seed: int | None = None,
        player_id: str | None = None,
        session_id: str | None = None,
        session_generation: int | None = None,
    ) -> dict[str, Any]:
        connection = self._connection()
        try:
            connection.execute("BEGIN IMMEDIATE")
            self._assert_public_session(
                connection, player_id=player_id, session_id=session_id,
                generation=session_generation,
            )
            profile_id = self._active_profile_id(connection, player_id)
            unlocked = {
                row["definition_id"]
                for row in connection.execute(
                    "SELECT definition_id FROM unlocked_heroes WHERE profile_id = ?",
                    (profile_id,),
                )
            }
            if len(unlocked) < ARENA_REQUIRED_HERO_COUNT:
                raise ArenaAccessError(
                    "arenaRosterInsufficient",
                    f"Arena requires 6 unlocked heroes; this profile has {len(unlocked)}.",
                )
            if len(squad_definition_ids) != ARENA_REQUIRED_HERO_COUNT:
                raise ArenaAccessError(
                    "invalidArenaSquad", "Arena squad must contain exactly 6 heroes."
                )
            if len(set(squad_definition_ids)) != ARENA_REQUIRED_HERO_COUNT:
                raise ArenaAccessError(
                    "invalidArenaSquad", "Arena squad heroes must be distinct."
                )
            unknown = sorted(set(squad_definition_ids) - ALL_HERO_IDS)
            locked = sorted(set(squad_definition_ids) - unlocked)
            if unknown or locked:
                raise ArenaAccessError(
                    "arenaSquadHeroLocked",
                    "Arena squad contains an unsupported or locked hero.",
                )
            existing = self._read_arena_run(connection, profile_id)
            if existing is not None and existing["status"] == "active":
                if existing["squadDefinitionIds"] == squad_definition_ids:
                    state = self._arena_state(connection, profile_id)
                    connection.commit()
                    return state
                raise ArenaAccessError(
                    "arenaRunAlreadyActive",
                    "Complete the active Arena Run before building another squad.",
                )
            if existing is not None:
                connection.execute(
                    "DELETE FROM arena_runs WHERE profile_id = ?", (profile_id,)
                )
            seed = schedule_seed if schedule_seed is not None else secrets.randbits(63)
            if seed < 0 or seed >= 2**63:
                raise ArenaAccessError(
                    "invalidArenaSeed", "The server-authored Arena seed is invalid."
                )
            run_id = f"arena.{uuid.uuid4().hex}"
            now = self._timestamp()
            connection.execute(
                """INSERT INTO arena_runs(
                       run_id, profile_id, run_schema_version, status, squad_json,
                       schedule_seed, current_node_index, created_at, completed_at
                   ) VALUES (?, ?, ?, 'active', ?, ?, 1, ?, NULL)""",
                (
                    run_id, profile_id, ARENA_RUN_SCHEMA_VERSION,
                    json.dumps(squad_definition_ids, separators=(",", ":")), seed, now,
                ),
            )
            connection.executemany(
                """INSERT INTO arena_nodes(
                       run_id, node_index, battle_size, enemy_formation,
                       enemy_team_json, battle_seed, completed, completion_battle_id
                   ) VALUES (?, ?, ?, ?, ?, ?, 0, NULL)""",
                (
                    (
                        run_id, node["nodeIndex"], node["battleSize"],
                        node["enemyFormation"],
                        json.dumps(node["enemyDefinitionIds"], separators=(",", ":")),
                        node["battleSeed"],
                    )
                    for node in self._generate_arena_nodes(seed)
                ),
            )
            state = self._arena_state(connection, profile_id)
            connection.commit()
            return state
        except (ProgressionStoreError, SaveSlotAccessError, ArenaAccessError):
            connection.rollback()
            raise
        except sqlite3.Error as exc:
            connection.rollback()
            raise ProgressionStoreError(
                "Arena Run could not be created. Retry later."
            ) from exc
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def abandon_arena_run(
        self,
        *,
        run_id: str,
        player_id: str | None = None,
        session_id: str | None = None,
        session_generation: int | None = None,
    ) -> dict[str, Any]:
        """Delete only the active profile's current Arena Run after confirmation."""
        connection = self._connection()
        try:
            connection.execute("BEGIN IMMEDIATE")
            self._assert_public_session(
                connection, player_id=player_id, session_id=session_id,
                generation=session_generation,
            )
            profile_id = self._active_profile_id(connection, player_id)
            run = self._read_arena_run(connection, profile_id)
            if run is None or run["runId"] != run_id:
                raise ArenaAccessError("arenaRunNotFound", "The Arena Run was not found.")
            connection.execute("DELETE FROM arena_runs WHERE run_id = ?", (run_id,))
            state = self._arena_state(connection, profile_id)
            connection.commit()
            return state
        except (ProgressionStoreError, SaveSlotAccessError, ArenaAccessError):
            connection.rollback()
            raise
        except sqlite3.Error as exc:
            connection.rollback()
            raise ProgressionStoreError("Arena Run could not be abandoned. Retry later.") from exc
        finally:
            connection.close()

    def arena_node_for_launch(
        self,
        *,
        run_id: str,
        node_index: int,
        player_team: list[str],
        player_formation: str | None,
        player_id: str | None = None,
        session_id: str | None = None,
        session_generation: int | None = None,
    ) -> dict[str, Any]:
        connection = self._connection()
        try:
            if self.public_mode:
                connection.execute("BEGIN")
                self._assert_public_session(
                    connection, player_id=player_id, session_id=session_id,
                    generation=session_generation,
                )
            profile_id = self._active_profile_id(connection, player_id)
            run = self._read_arena_run(connection, profile_id)
            if run is None or run["runId"] != run_id:
                raise ArenaAccessError("arenaRunNotFound", "The Arena Run was not found.")
            if run["status"] != "active":
                raise ArenaAccessError("arenaRunCompleted", "This Arena Run is complete.")
            if node_index != run["currentNodeIndex"]:
                raise ArenaAccessError(
                    "arenaNodeOutOfOrder", "Only the current Arena node can be launched."
                )
            node = run["nodes"][node_index - 1]
            size = node["battleSize"]
            if len(player_team) != size or len(set(player_team)) != size:
                raise ArenaAccessError(
                    "invalidArenaPlayerTeam",
                    "Player team must contain the node's exact number of distinct heroes.",
                )
            if not set(player_team).issubset(set(run["squadDefinitionIds"])):
                raise ArenaAccessError(
                    "arenaHeroOutsideSquad",
                    "Player team must be selected from the locked Arena squad.",
                )
            valid_formations = {
                1: {None},
                2: {"front-rear", "side-by-side"},
                3: {"one-front-two-rear", "two-front-one-rear", "all-front"},
            }[size]
            if player_formation not in valid_formations:
                raise ArenaAccessError(
                    "invalidArenaPlayerFormation",
                    "Player formation must be valid for the current Arena node.",
                )
            return {"profileId": profile_id, "runId": run_id, **node}
        except (ProgressionStoreError, SaveSlotAccessError, ArenaAccessError):
            raise
        except sqlite3.Error as exc:
            raise ProgressionStoreError(
                "Arena node could not be read. Retry later."
            ) from exc
        finally:
            connection.close()

    def _commit_arena_victory_tx(
        self,
        connection: sqlite3.Connection,
        *,
        run_id: str,
        node_index: int,
        battle_id: str,
        profile_id: str,
    ) -> dict[str, Any]:
        run = self._read_arena_run(connection, profile_id)
        if run is None or run["runId"] != run_id:
            raise ArenaAccessError("arenaRunNotFound", "The Arena Run was not found.")
        node = run["nodes"][node_index - 1] if 1 <= node_index <= 12 else None
        if node is None:
            raise ArenaAccessError("arenaNodeNotFound", "The Arena node was not found.")
        if node["completionBattleId"] == battle_id:
            return {"alreadyCommitted": True, "arena": self._arena_state(connection, profile_id)}
        if run["status"] != "active" or run["currentNodeIndex"] != node_index:
            raise ArenaAccessError(
                "arenaNodeOutOfOrder", "Only the current Arena node can advance."
            )
        if node["completed"]:
            raise ArenaAccessError(
                "arenaNodeAlreadyCompleted", "This Arena node is already complete."
            )
        connection.execute(
            """UPDATE arena_nodes SET completed = 1, completion_battle_id = ?
               WHERE run_id = ? AND node_index = ?""",
            (battle_id, run_id, node_index),
        )
        if node_index == ARENA_NODE_COUNT:
            connection.execute(
                """UPDATE arena_runs SET status = 'completed',
                       current_node_index = NULL, completed_at = ?
                   WHERE run_id = ?""",
                (self._timestamp(), run_id),
            )
        else:
            connection.execute(
                "UPDATE arena_runs SET current_node_index = ? WHERE run_id = ?",
                (node_index + 1, run_id),
            )
        return {"alreadyCommitted": False, "arena": self._arena_state(connection, profile_id)}

    def commit_arena_victory(
        self,
        *,
        run_id: str,
        node_index: int,
        battle_id: str,
        expected_profile_id: str,
    ) -> dict[str, Any]:
        connection = self._connection()
        try:
            connection.execute("BEGIN IMMEDIATE")
            profile_id = self._active_profile_id(connection)
            if profile_id != expected_profile_id:
                raise SaveSlotAccessError(
                    "activeSaveSlotChanged",
                    "The active save slot changed; start the Arena battle again.",
                )
            result = self._commit_arena_victory_tx(
                connection,
                run_id=run_id,
                node_index=node_index,
                battle_id=battle_id,
                profile_id=profile_id,
            )
            connection.commit()
            return result
        except (ProgressionStoreError, SaveSlotAccessError, ArenaAccessError):
            connection.rollback()
            raise
        except sqlite3.Error as exc:
            connection.rollback()
            raise ProgressionStoreError(
                "Arena victory could not be committed. Retry later."
            ) from exc
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def assert_stage_battle_access(
        self,
        stage_id: str,
        battle_index: int,
        expected_profile_id: str | None = None,
        mode: StageMode = "learner",
        *,
        player_id: str | None = None,
        session_id: str | None = None,
        session_generation: int | None = None,
    ) -> StageBattle:
        if mode not in {"learner", "tactics"}:
            raise StageAccessError("invalidStageMode", "Unknown structured-stage mode.")
        battle = stage_battle(stage_id, battle_index)
        connection: sqlite3.Connection | None = None
        try:
            connection = self._connection()
            if self.public_mode:
                connection.execute("BEGIN")
                self._assert_public_session(
                    connection, player_id=player_id, session_id=session_id,
                    generation=session_generation,
                )
            profile_id = self._active_profile_id(connection, player_id)
            if expected_profile_id is not None and profile_id != expected_profile_id:
                raise SaveSlotAccessError(
                    "activeSaveSlotChanged",
                    "The active save slot changed; start the battle again.",
                )
            row = connection.execute(
                """SELECT highest_completed_battle FROM stage_progress
                   WHERE profile_id = ? AND stage_id = ?""",
                (profile_id, stage_id),
            ).fetchone()
            if row is None:
                raise ProgressionStoreError(
                    "The stored stage progression is incomplete. Retry later."
                )
            required_count = len(STAGE_BATTLES[battle.stage_id])
            if mode == "tactics" and row["highest_completed_battle"] != required_count:
                raise StageAccessError(
                    "stageModeLocked",
                    "Complete this campaign in Learner mode before starting Tactics.",
                )
            if mode == "learner" and battle_index > min(
                row["highest_completed_battle"] + 1, required_count
            ):
                raise StageAccessError(
                    "stageBattleLocked",
                    "Complete the preceding battle before starting this battle.",
                )
            return battle
        except (ProgressionStoreError, SaveSlotAccessError, StageAccessError):
            raise
        except sqlite3.Error as exc:
            raise ProgressionStoreError(
                "Persistent progression could not be read. Retry later."
            ) from exc
        finally:
            if connection is not None:
                connection.close()

    def _commit_stage_victory_tx(
        self,
        connection: sqlite3.Connection,
        *,
        battle_id: str,
        stage_id: str,
        battle_index: int,
        mode: StageMode,
        profile_id: str,
    ) -> dict[str, Any]:
        battle = stage_battle(stage_id, battle_index)
        duplicate = connection.execute(
            (
                """SELECT 1 FROM battle_completions
                   WHERE profile_id = ? AND battle_id = ?"""
                if mode == "learner"
                else """SELECT 1 FROM stage_mode_completions
                   WHERE profile_id = ? AND completion_battle_id = ?"""
            ),
            (profile_id, battle_id),
        ).fetchone()
        if duplicate is not None:
            return {
                "alreadyCommitted": True,
                "newlyGrantedRewards": [],
                "progression": self._read_progression(connection, profile_id),
            }
        row = connection.execute(
            """SELECT highest_completed_battle FROM stage_progress
               WHERE profile_id = ? AND stage_id = ?""",
            (profile_id, stage_id),
        ).fetchone()
        if row is None:
            raise ProgressionStoreError(
                "The stored stage progression is incomplete. Retry later."
            )
        highest = row["highest_completed_battle"]
        required_count = len(STAGE_BATTLES[battle.stage_id])
        if mode == "tactics" and highest != required_count:
            raise StageAccessError(
                "stageModeLocked",
                "Complete this campaign in Learner mode before committing Tactics.",
            )
        if mode == "learner" and battle_index > min(highest + 1, required_count):
            raise StageAccessError(
                "stageBattleLocked",
                "Complete the preceding battle before committing this victory.",
            )
        if mode == "tactics":
            existing = connection.execute(
                """SELECT 1 FROM stage_mode_completions
                   WHERE profile_id = ? AND stage_id = ?
                     AND battle_index = ? AND mode = 'tactics'""",
                (profile_id, stage_id, battle_index),
            ).fetchone()
            if existing is not None:
                return {
                    "alreadyCommitted": True,
                    "newlyGrantedRewards": [],
                    "progression": self._read_progression(connection, profile_id),
                }
            connection.execute(
                """INSERT INTO stage_mode_completions(
                       profile_id, stage_id, battle_index, mode,
                       completion_battle_id, completed_at
                   ) VALUES (?, ?, ?, 'tactics', ?, ?)""",
                (profile_id, stage_id, battle_index, battle_id, self._timestamp()),
            )
        else:
            connection.execute(
                """INSERT INTO battle_completions(
                       profile_id, battle_id, stage_id, battle_index
                   ) VALUES (?, ?, ?, ?)""",
                (profile_id, battle_id, stage_id, battle_index),
            )
            connection.execute(
                """INSERT OR IGNORE INTO stage_mode_completions(
                       profile_id, stage_id, battle_index, mode,
                       completion_battle_id, completed_at
                   ) VALUES (?, ?, ?, 'learner', ?, ?)""",
                (profile_id, stage_id, battle_index, battle_id, self._timestamp()),
            )
            if battle_index == highest + 1:
                connection.execute(
                    """UPDATE stage_progress SET highest_completed_battle = ?,
                           completed = ? WHERE profile_id = ? AND stage_id = ?""",
                    (
                        battle_index, int(battle_index == required_count),
                        profile_id, stage_id,
                    ),
                )
        newly_granted: list[dict[str, Any]] = []
        reward = battle.reward if mode == "learner" else None
        if reward is not None:
            cursor = connection.execute(
                """INSERT OR IGNORE INTO granted_rewards(profile_id, reward_id, count)
                   VALUES (?, ?, 1)""",
                (profile_id, reward.reward_id),
            )
            if cursor.rowcount == 1:
                if reward.hero_definition_id is not None:
                    connection.execute(
                        """INSERT OR IGNORE INTO unlocked_heroes(
                               profile_id, definition_id
                           ) VALUES (?, ?)""",
                        (profile_id, reward.hero_definition_id),
                    )
                newly_granted.append(reward_dict(reward))
        return {
            "alreadyCommitted": False,
            "newlyGrantedRewards": newly_granted,
            "progression": self._read_progression(connection, profile_id),
        }

    def commit_victory(
        self,
        *,
        battle_id: str,
        stage_id: str,
        battle_index: int,
        mode: StageMode = "learner",
        expected_profile_id: str | None = None,
    ) -> dict[str, Any]:
        if mode not in {"learner", "tactics"}:
            raise StageAccessError("invalidStageMode", "Unknown structured-stage mode.")
        battle = stage_battle(stage_id, battle_index)
        connection = self._connection()
        try:
            connection.execute("BEGIN IMMEDIATE")
            profile_id = self._active_profile_id(connection)
            if expected_profile_id is not None and profile_id != expected_profile_id:
                raise SaveSlotAccessError(
                    "activeSaveSlotChanged",
                    "The active save slot changed; start the battle again.",
                )
            duplicate = connection.execute(
                (
                    """SELECT 1 FROM battle_completions
                       WHERE profile_id = ? AND battle_id = ?"""
                    if mode == "learner"
                    else """SELECT 1 FROM stage_mode_completions
                       WHERE profile_id = ? AND completion_battle_id = ?"""
                ),
                (profile_id, battle_id),
            ).fetchone()
            if duplicate is not None:
                progression = self._read_progression(connection, profile_id)
                connection.commit()
                return {
                    "alreadyCommitted": True,
                    "newlyGrantedRewards": [],
                    "progression": progression,
                }

            row = connection.execute(
                """SELECT highest_completed_battle FROM stage_progress
                   WHERE profile_id = ? AND stage_id = ?""",
                (profile_id, stage_id),
            ).fetchone()
            if row is None:
                raise ProgressionStoreError(
                    "The stored stage progression is incomplete. Retry later."
                )
            highest = row["highest_completed_battle"]
            required_count = len(STAGE_BATTLES[battle.stage_id])
            if mode == "tactics" and highest != required_count:
                raise StageAccessError(
                    "stageModeLocked",
                    "Complete this campaign in Learner mode before committing Tactics.",
                )
            if mode == "learner" and battle_index > min(highest + 1, required_count):
                raise StageAccessError(
                    "stageBattleLocked",
                    "Complete the preceding battle before committing this victory.",
                )

            if mode == "tactics":
                existing_completion = connection.execute(
                    """SELECT 1 FROM stage_mode_completions
                       WHERE profile_id = ? AND stage_id = ?
                         AND battle_index = ? AND mode = 'tactics'""",
                    (profile_id, stage_id, battle_index),
                ).fetchone()
                if existing_completion is not None:
                    progression = self._read_progression(connection, profile_id)
                    connection.commit()
                    return {
                        "alreadyCommitted": True,
                        "newlyGrantedRewards": [],
                        "progression": progression,
                    }
                connection.execute(
                    """INSERT INTO stage_mode_completions(
                           profile_id, stage_id, battle_index, mode,
                           completion_battle_id, completed_at
                       ) VALUES (?, ?, ?, 'tactics', ?, ?)""",
                    (profile_id, stage_id, battle_index, battle_id, self._timestamp()),
                )
            else:
                connection.execute(
                    """INSERT INTO battle_completions(
                           profile_id, battle_id, stage_id, battle_index
                       ) VALUES (?, ?, ?, ?)""",
                    (profile_id, battle_id, stage_id, battle_index),
                )
                connection.execute(
                    """INSERT OR IGNORE INTO stage_mode_completions(
                           profile_id, stage_id, battle_index, mode,
                           completion_battle_id, completed_at
                       ) VALUES (?, ?, ?, 'learner', ?, ?)""",
                    (profile_id, stage_id, battle_index, battle_id, self._timestamp()),
                )
                if battle_index == highest + 1:
                    connection.execute(
                        """UPDATE stage_progress SET highest_completed_battle = ?,
                               completed = ? WHERE profile_id = ? AND stage_id = ?""",
                        (
                            battle_index,
                            int(battle_index == required_count),
                            profile_id,
                            stage_id,
                        ),
                    )

            newly_granted: list[dict[str, Any]] = []
            reward = battle.reward if mode == "learner" else None
            if reward is not None:
                cursor = connection.execute(
                    """INSERT OR IGNORE INTO granted_rewards(profile_id, reward_id, count)
                       VALUES (?, ?, 1)""",
                    (profile_id, reward.reward_id),
                )
                if cursor.rowcount == 1:
                    if reward.hero_definition_id is not None:
                        connection.execute(
                            """INSERT OR IGNORE INTO unlocked_heroes(
                                   profile_id, definition_id
                               ) VALUES (?, ?)""",
                            (profile_id, reward.hero_definition_id),
                        )
                    newly_granted.append(reward_dict(reward))

            progression = self._read_progression(connection, profile_id)
            connection.commit()
            return {
                "alreadyCommitted": False,
                "newlyGrantedRewards": newly_granted,
                "progression": progression,
            }
        except (ProgressionStoreError, SaveSlotAccessError, StageAccessError):
            connection.rollback()
            raise
        except sqlite3.Error as exc:
            connection.rollback()
            raise ProgressionStoreError(
                "Persistent progression could not be committed. Retry later."
            ) from exc
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()


def stage_battle(stage_id: str, battle_index: int) -> StageBattle:
    battles = STAGE_BATTLES.get(stage_id)  # type: ignore[arg-type]
    if battles is None:
        raise StageAccessError("stageNotFound", "The structured stage was not found.")
    if battle_index < 1 or battle_index > len(battles):
        raise StageAccessError("stageBattleNotFound", "The stage battle was not found.")
    return battles[battle_index - 1]


def reward_dict(reward: StageReward) -> dict[str, Any]:
    return {
        "rewardId": reward.reward_id,
        "kind": reward.kind,
        "heroDefinitionId": reward.hero_definition_id,
        "notification": reward.notification,
    }


def stages_response(progression: dict[str, Any]) -> dict[str, Any]:
    progress_by_stage = {
        item["stageId"]: item for item in progression["stageProgress"]
    }
    stages = []
    for stage_id, battles in STAGE_BATTLES.items():
        stage_progress = progress_by_stage[stage_id]
        stages.append({
            "stageId": stage_id,
            "displayName": STAGE_DISPLAY_NAMES[stage_id],
            "progress": stage_progress,
            "modes": stage_progress["modes"],
            "battles": [
                {
                    "id": battle.battle_id,
                    "displayOrder": battle.battle_index,
                    "battleSize": battle.battle_size,
                    "formation": battle.formation,
                    "enemyDefinitionIds": list(battle.enemy_definition_ids),
                    "reward": reward_dict(battle.reward) if battle.reward else None,
                    "unlocked": battle.battle_index <= stage_progress["unlockedBattle"],
                    "completed": battle.battle_index <= stage_progress["highestCompletedBattle"],
                }
                for battle in battles
            ],
        })
    return {"contractVersion": "1.0", "stages": stages}
