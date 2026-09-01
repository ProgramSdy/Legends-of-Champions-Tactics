"""SQLite-backed default-profile progression and static training curricula."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
import random
import secrets
import sqlite3
import threading
from typing import Any, Literal
from urllib.parse import quote
import uuid


DEFAULT_PROFILE_ID = "profile.local.default"
SCHEMA_VERSION = 3
ARENA_RUN_SCHEMA_VERSION = 1
ARENA_NODE_COUNT = 12
ARENA_REQUIRED_HERO_COUNT = 6
SAVE_SLOT_IDS = (1, 2, 3, 4, 5)
ITEM_CARD_REWARD_ID = "reward.item-card.basic"
StageId = Literal["paladins-altar", "warriors-barrack"]

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


class ProgressionStore:
    """Transaction-scoped SQLite store for five local save slots."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
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
            try:
                created = not self.database_path.exists()
                if created:
                    if not self.database_path.parent.is_dir():
                        raise ProgressionStoreError(
                            "The progression database directory is unavailable."
                        )
                    connection = sqlite3.connect(self.database_path, timeout=5.0)
                    connection.row_factory = sqlite3.Row
                    connection.execute("PRAGMA foreign_keys = ON")
                    try:
                        self._create_schema(connection)
                    finally:
                        connection.close()
                self._upgrade_and_validate_store()
                self._initialized = True
            except ProgressionStoreError:
                raise
            except (OSError, sqlite3.Error) as exc:
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
                    battle_index INTEGER NOT NULL CHECK (battle_index BETWEEN 1 AND 9),
                    PRIMARY KEY (profile_id, battle_id)
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
            if row["value"] == "1":
                self._migrate_v1(connection)
                row = {"value": "2"}
            if row["value"] == "2":
                self._migrate_v2(connection)
            elif row["value"] != str(SCHEMA_VERSION):
                raise ProgressionStoreError(
                    "Persistent progression has an unsupported schema. Retry later."
                )
            self._validate_v3(connection)
        finally:
            connection.close()

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

    def _validate_v3(self, connection: sqlite3.Connection) -> None:
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

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")

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

    def _active_profile_id(self, connection: sqlite3.Connection) -> str:
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

    def active_profile_id(self) -> str:
        connection = self._connection()
        try:
            return self._active_profile_id(connection)
        except sqlite3.Error as exc:
            raise ProgressionStoreError(
                "Persistent progression could not be read. Retry later."
            ) from exc
        finally:
            connection.close()

    def list_save_slots(self) -> dict[str, Any]:
        connection = self._connection()
        try:
            active = connection.execute(
                "SELECT slot_id FROM active_slot WHERE singleton_id = 1"
            ).fetchone()
            active_slot_id = active["slot_id"] if active else None
            rows = connection.execute(
                """SELECT slot_id, profile_id, created_at, last_played_at
                   FROM save_slots ORDER BY slot_id"""
            ).fetchall()
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

    def create_save_slot(self, slot_id: int) -> dict[str, Any]:
        return self._initialize_slot(slot_id, overwrite=False)

    def overwrite_save_slot(self, slot_id: int) -> dict[str, Any]:
        return self._initialize_slot(slot_id, overwrite=True)

    def _initialize_slot(self, slot_id: int, *, overwrite: bool) -> dict[str, Any]:
        self._validate_slot_id(slot_id)
        connection = self._connection()
        try:
            connection.execute("BEGIN IMMEDIATE")
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
                    "battle_completions",
                    "granted_rewards",
                    "stage_progress",
                    "unlocked_heroes",
                ):
                    connection.execute(
                        f"DELETE FROM {table} WHERE profile_id = ?", (old_profile_id,)
                    )
                connection.execute(
                    "UPDATE save_slots SET profile_id = NULL, created_at = NULL, "
                    "last_played_at = NULL WHERE slot_id = ?",
                    (slot_id,),
                )
                connection.execute(
                    "DELETE FROM profiles WHERE profile_id = ?", (old_profile_id,)
                )
            profile_id = f"profile.local.slot.{slot_id}.{uuid.uuid4().hex}"
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
                """SELECT slot_id, profile_id, created_at, last_played_at
                   FROM save_slots WHERE slot_id = ?""",
                (slot_id,),
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

    def load_save_slot(self, slot_id: int) -> dict[str, Any]:
        self._validate_slot_id(slot_id)
        connection = self._connection()
        try:
            connection.execute("BEGIN IMMEDIATE")
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
            connection.execute(
                "UPDATE save_slots SET last_played_at = ? WHERE slot_id = ?",
                (now, slot_id),
            )
            connection.execute(
                "UPDATE active_slot SET slot_id = ? WHERE singleton_id = 1", (slot_id,)
            )
            progression = self._read_progression(connection, row["profile_id"])
            updated = connection.execute(
                """SELECT slot_id, profile_id, created_at, last_played_at
                   FROM save_slots WHERE slot_id = ?""",
                (slot_id,),
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

    def read_progression(self) -> dict[str, Any]:
        connection: sqlite3.Connection | None = None
        try:
            connection = self._connection()
            return self._read_progression(connection, self._active_profile_id(connection))
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
            bool(row["completed"]) != (row["highest_completed_battle"] == 9)
            for row in progress_rows
        ):
            raise ProgressionStoreError(
                "The stored stage completion state is corrupt. Retry later."
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
                self._progress_row(row["stage_id"], row["highest_completed_battle"])
                for row in progress_rows
            ],
            "grantedRewards": rewards,
        }

    @staticmethod
    def _progress_row(stage_id: str, highest_completed: int) -> dict[str, Any]:
        return {
            "stageId": stage_id,
            "highestCompletedBattle": highest_completed,
            "unlockedBattle": min(highest_completed + 1, 9),
            "completed": highest_completed == 9,
        }

    def assert_player_team_unlocked(
        self, definition_ids: list[str], expected_profile_id: str | None = None
    ) -> None:
        progression = self.read_progression()
        if (
            expected_profile_id is not None
            and progression["profileId"] != expected_profile_id
        ):
            raise SaveSlotAccessError(
                "activeSaveSlotChanged",
                "The active save slot changed; start the battle again.",
            )
        unlocked = set(progression["unlockedHeroDefinitionIds"])
        locked = sorted(set(definition_ids) - unlocked)
        if locked:
            raise StageAccessError(
                "heroLocked",
                f"The player profile has not unlocked: {', '.join(locked)}.",
            )

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

    def read_arena_state(self) -> dict[str, Any]:
        connection = self._connection()
        try:
            return self._arena_state(connection, self._active_profile_id(connection))
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
        nodes: list[dict[str, Any]] = []
        for node_index in range(1, ARENA_NODE_COUNT + 1):
            size = generator.choices((1, 2, 3), weights=(20, 50, 30), k=1)[0]
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
        self, squad_definition_ids: list[str], *, schedule_seed: int | None = None
    ) -> dict[str, Any]:
        connection = self._connection()
        try:
            connection.execute("BEGIN IMMEDIATE")
            profile_id = self._active_profile_id(connection)
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

    def abandon_arena_run(self, *, run_id: str) -> dict[str, Any]:
        """Delete only the active profile's current Arena Run after confirmation."""
        connection = self._connection()
        try:
            connection.execute("BEGIN IMMEDIATE")
            profile_id = self._active_profile_id(connection)
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
    ) -> dict[str, Any]:
        connection = self._connection()
        try:
            profile_id = self._active_profile_id(connection)
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
            run = self._read_arena_run(connection, profile_id)
            if run is None or run["runId"] != run_id:
                raise ArenaAccessError("arenaRunNotFound", "The Arena Run was not found.")
            node = run["nodes"][node_index - 1] if 1 <= node_index <= 12 else None
            if node is None:
                raise ArenaAccessError("arenaNodeNotFound", "The Arena node was not found.")
            if node["completionBattleId"] == battle_id:
                state = self._arena_state(connection, profile_id)
                connection.commit()
                return {"alreadyCommitted": True, "arena": state}
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
            state = self._arena_state(connection, profile_id)
            connection.commit()
            return {"alreadyCommitted": False, "arena": state}
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
    ) -> StageBattle:
        battle = stage_battle(stage_id, battle_index)
        connection: sqlite3.Connection | None = None
        try:
            connection = self._connection()
            profile_id = self._active_profile_id(connection)
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
            if battle_index > min(row["highest_completed_battle"] + 1, 9):
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

    def commit_victory(
        self,
        *,
        battle_id: str,
        stage_id: str,
        battle_index: int,
        expected_profile_id: str | None = None,
    ) -> dict[str, Any]:
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
                """SELECT 1 FROM battle_completions
                   WHERE profile_id = ? AND battle_id = ?""",
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
            if battle_index > min(highest + 1, 9):
                raise StageAccessError(
                    "stageBattleLocked",
                    "Complete the preceding battle before committing this victory.",
                )

            connection.execute(
                """INSERT INTO battle_completions(
                       profile_id, battle_id, stage_id, battle_index
                   ) VALUES (?, ?, ?, ?)""",
                (profile_id, battle_id, stage_id, battle_index),
            )
            if battle_index == highest + 1:
                connection.execute(
                    """UPDATE stage_progress SET highest_completed_battle = ?,
                           completed = ? WHERE profile_id = ? AND stage_id = ?""",
                    (battle_index, int(battle_index == 9), profile_id, stage_id),
                )

            newly_granted: list[dict[str, Any]] = []
            reward = battle.reward
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
            "displayName": (
                "Paladin's Altar" if stage_id == "paladins-altar"
                else "Warrior's Barrack"
            ),
            "progress": stage_progress,
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
