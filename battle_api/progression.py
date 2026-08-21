"""SQLite-backed default-profile progression and static training curricula."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import sqlite3
import threading
from typing import Any, Literal
from urllib.parse import quote
import uuid


DEFAULT_PROFILE_ID = "profile.local.default"
SCHEMA_VERSION = 2
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
            elif row["value"] != str(SCHEMA_VERSION):
                raise ProgressionStoreError(
                    "Persistent progression has an unsupported schema. Retry later."
                )
            self._validate_v2(connection)
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
                (str(SCHEMA_VERSION),),
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

    def _validate_v2(self, connection: sqlite3.Connection) -> None:
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
