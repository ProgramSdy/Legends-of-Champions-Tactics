"""SQLite-backed default-profile progression and static training curricula."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
import threading
from typing import Any, Literal
from urllib.parse import quote


DEFAULT_PROFILE_ID = "profile.local.default"
SCHEMA_VERSION = 1
ITEM_CARD_REWARD_ID = "reward.item-card.basic"
StageId = Literal["paladins-altar", "warriors-barrack"]

INITIAL_UNLOCKED_HERO_IDS: tuple[str, ...] = (
    "hero.priest.comprehensiveness",
    "hero.priest.discipline",
    "hero.mage.comprehensiveness",
    "hero.warrior.weapon_master",
    "hero.rogue.comprehensiveness",
)
ALL_HERO_IDS = frozenset(INITIAL_UNLOCKED_HERO_IDS) | {
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


class ProgressionStore:
    """Small transaction-scoped SQLite store for one stable local profile."""

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
                self._validate_store()
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
                CREATE TABLE profiles (
                    profile_id TEXT PRIMARY KEY
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
            connection.execute(
                "INSERT INTO profiles(profile_id) VALUES (?)", (DEFAULT_PROFILE_ID,)
            )
            connection.executemany(
                "INSERT INTO unlocked_heroes(profile_id, definition_id) VALUES (?, ?)",
                ((DEFAULT_PROFILE_ID, hero_id) for hero_id in INITIAL_UNLOCKED_HERO_IDS),
            )
            connection.executemany(
                """INSERT INTO stage_progress(
                       profile_id, stage_id, highest_completed_battle, completed
                   ) VALUES (?, ?, 0, 0)""",
                ((DEFAULT_PROFILE_ID, stage_id) for stage_id in STAGE_BATTLES),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise

    def _validate_store(self) -> None:
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
            if row is None or row["value"] != str(SCHEMA_VERSION):
                raise ProgressionStoreError(
                    "Persistent progression has an unsupported schema. Retry later."
                )
            profile = connection.execute(
                "SELECT 1 FROM profiles WHERE profile_id = ?", (DEFAULT_PROFILE_ID,)
            ).fetchone()
            if profile is None:
                raise ProgressionStoreError(
                    "The default local profile is missing. Retry later."
                )
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

    def read_progression(self) -> dict[str, Any]:
        connection: sqlite3.Connection | None = None
        try:
            connection = self._connection()
            return self._read_progression(connection)
        except ProgressionStoreError:
            raise
        except sqlite3.Error as exc:
            raise ProgressionStoreError(
                "Persistent progression could not be read. Retry later."
            ) from exc
        finally:
            if connection is not None:
                connection.close()

    def _read_progression(self, connection: sqlite3.Connection) -> dict[str, Any]:
        unlocked = [
            row["definition_id"]
            for row in connection.execute(
                """SELECT definition_id FROM unlocked_heroes
                   WHERE profile_id = ? ORDER BY definition_id""",
                (DEFAULT_PROFILE_ID,),
            )
        ]
        progress_rows = connection.execute(
            """SELECT stage_id, highest_completed_battle, completed
               FROM stage_progress WHERE profile_id = ? ORDER BY stage_id""",
            (DEFAULT_PROFILE_ID,),
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
                (DEFAULT_PROFILE_ID,),
            )
        ]
        if any(reward["count"] != 1 for reward in rewards):
            raise ProgressionStoreError(
                "The stored reward progression is corrupt. Retry later."
            )
        return {
            "profileId": DEFAULT_PROFILE_ID,
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

    def assert_player_team_unlocked(self, definition_ids: list[str]) -> None:
        progression = self.read_progression()
        unlocked = set(progression["unlockedHeroDefinitionIds"])
        locked = sorted(set(definition_ids) - unlocked)
        if locked:
            raise StageAccessError(
                "heroLocked",
                f"The player profile has not unlocked: {', '.join(locked)}.",
            )

    def assert_stage_battle_access(self, stage_id: str, battle_index: int) -> StageBattle:
        battle = stage_battle(stage_id, battle_index)
        connection: sqlite3.Connection | None = None
        try:
            connection = self._connection()
            row = connection.execute(
                """SELECT highest_completed_battle FROM stage_progress
                   WHERE profile_id = ? AND stage_id = ?""",
                (DEFAULT_PROFILE_ID, stage_id),
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
        except (ProgressionStoreError, StageAccessError):
            raise
        except sqlite3.Error as exc:
            raise ProgressionStoreError(
                "Persistent progression could not be read. Retry later."
            ) from exc
        finally:
            if connection is not None:
                connection.close()

    def commit_victory(
        self, *, battle_id: str, stage_id: str, battle_index: int
    ) -> dict[str, Any]:
        battle = stage_battle(stage_id, battle_index)
        connection = self._connection()
        try:
            connection.execute("BEGIN IMMEDIATE")
            duplicate = connection.execute(
                """SELECT 1 FROM battle_completions
                   WHERE profile_id = ? AND battle_id = ?""",
                (DEFAULT_PROFILE_ID, battle_id),
            ).fetchone()
            if duplicate is not None:
                progression = self._read_progression(connection)
                connection.commit()
                return {
                    "alreadyCommitted": True,
                    "newlyGrantedRewards": [],
                    "progression": progression,
                }

            row = connection.execute(
                """SELECT highest_completed_battle FROM stage_progress
                   WHERE profile_id = ? AND stage_id = ?""",
                (DEFAULT_PROFILE_ID, stage_id),
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
                (DEFAULT_PROFILE_ID, battle_id, stage_id, battle_index),
            )
            if battle_index == highest + 1:
                connection.execute(
                    """UPDATE stage_progress SET highest_completed_battle = ?,
                           completed = ? WHERE profile_id = ? AND stage_id = ?""",
                    (battle_index, int(battle_index == 9), DEFAULT_PROFILE_ID, stage_id),
                )

            newly_granted: list[dict[str, Any]] = []
            reward = battle.reward
            if reward is not None:
                cursor = connection.execute(
                    """INSERT OR IGNORE INTO granted_rewards(profile_id, reward_id, count)
                       VALUES (?, ?, 1)""",
                    (DEFAULT_PROFILE_ID, reward.reward_id),
                )
                if cursor.rowcount == 1:
                    if reward.hero_definition_id is not None:
                        connection.execute(
                            """INSERT OR IGNORE INTO unlocked_heroes(
                                   profile_id, definition_id
                               ) VALUES (?, ?)""",
                            (DEFAULT_PROFILE_ID, reward.hero_definition_id),
                        )
                    newly_granted.append(reward_dict(reward))

            progression = self._read_progression(connection)
            connection.commit()
            return {
                "alreadyCommitted": False,
                "newlyGrantedRewards": newly_granted,
                "progression": progression,
            }
        except (ProgressionStoreError, StageAccessError):
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
