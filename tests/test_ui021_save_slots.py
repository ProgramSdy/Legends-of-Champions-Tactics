from __future__ import annotations

from pathlib import Path
import sqlite3

from fastapi.testclient import TestClient
import pytest

from battle_api.app import app, get_progression_store, registry
from battle_api.progression import (
    DEFAULT_PROFILE_ID,
    INITIAL_UNLOCKED_HERO_IDS,
    ITEM_CARD_REWARD_ID,
    ProgressionStore,
    ProgressionStoreError,
)


@pytest.fixture()
def slot_client(tmp_path: Path):
    store = ProgressionStore(tmp_path / "progression.sqlite3")
    app.dependency_overrides[get_progression_store] = lambda: store
    with TestClient(app) as client:
        yield client, store
    app.dependency_overrides.clear()


def _stage(progress: dict, stage_id: str) -> dict:
    return next(item for item in progress["stageProgress"] if item["stageId"] == stage_id)


def _create_legacy_v1(database: Path) -> None:
    with sqlite3.connect(database) as connection:
        connection.executescript(
            """
            CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE profiles (profile_id TEXT PRIMARY KEY);
            CREATE TABLE unlocked_heroes (
                profile_id TEXT NOT NULL REFERENCES profiles(profile_id),
                definition_id TEXT NOT NULL,
                PRIMARY KEY (profile_id, definition_id)
            );
            CREATE TABLE stage_progress (
                profile_id TEXT NOT NULL REFERENCES profiles(profile_id),
                stage_id TEXT NOT NULL,
                highest_completed_battle INTEGER NOT NULL DEFAULT 0,
                completed INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (profile_id, stage_id)
            );
            CREATE TABLE granted_rewards (
                profile_id TEXT NOT NULL REFERENCES profiles(profile_id),
                reward_id TEXT NOT NULL,
                count INTEGER NOT NULL,
                PRIMARY KEY (profile_id, reward_id)
            );
            CREATE TABLE battle_completions (
                profile_id TEXT NOT NULL REFERENCES profiles(profile_id),
                battle_id TEXT NOT NULL,
                stage_id TEXT NOT NULL,
                battle_index INTEGER NOT NULL,
                PRIMARY KEY (profile_id, battle_id)
            );
            INSERT INTO metadata VALUES ('schema_version', '1');
            INSERT INTO profiles VALUES ('profile.local.default');
            """
        )
        connection.executemany(
            "INSERT INTO unlocked_heroes VALUES (?, ?)",
            (
                (DEFAULT_PROFILE_ID, hero_id)
                for hero_id in (
                    *INITIAL_UNLOCKED_HERO_IDS,
                    "hero.priest.discipline",
                    "hero.warrior.berserker",
                )
            ),
        )
        connection.executemany(
            "INSERT INTO stage_progress VALUES (?, ?, ?, ?)",
            (
                (DEFAULT_PROFILE_ID, "paladins-altar", 3, 0),
                (DEFAULT_PROFILE_ID, "warriors-barrack", 6, 0),
            ),
        )
        connection.execute(
            "INSERT INTO granted_rewards VALUES (?, ?, 1)",
            (DEFAULT_PROFILE_ID, ITEM_CARD_REWARD_ID),
        )
        connection.execute(
            "INSERT INTO battle_completions VALUES (?, ?, ?, ?)",
            (DEFAULT_PROFILE_ID, "battle.legacy.6", "warriors-barrack", 6),
        )


def test_lists_exactly_five_empty_slots_and_requires_active_slot(slot_client):
    client, _store = slot_client

    listed = client.get("/api/v1/save-slots")
    progression = client.get("/api/v1/progression")
    invalid = client.post("/api/v1/save-slots/6/create")
    empty_load = client.post("/api/v1/save-slots/3/load")

    assert listed.status_code == 200
    assert listed.json()["activeSlotId"] is None
    assert [slot["slotId"] for slot in listed.json()["slots"]] == [1, 2, 3, 4, 5]
    assert all(not slot["occupied"] for slot in listed.json()["slots"])
    assert progression.status_code == 409
    assert progression.json()["detail"]["code"] == "noActiveSaveSlot"
    assert invalid.status_code == 422
    assert invalid.json()["detail"]["code"] == "invalidSaveSlot"
    assert empty_load.status_code == 409
    assert empty_load.json()["detail"]["code"] == "loadEmptySlot"


def test_create_has_exact_starter_state_and_rejects_client_progression(slot_client):
    client, _store = slot_client

    created = client.post("/api/v1/save-slots/2/create")
    occupied = client.post("/api/v1/save-slots/2/create")
    injected = client.post(
        "/api/v1/save-slots/3/create",
        json={"progression": {"grantedRewards": [{"rewardId": "forged"}]}},
    )

    assert created.status_code == 200
    body = created.json()
    assert body["activeSlotId"] == 2
    assert body["slot"]["occupied"] is True
    assert body["slot"]["active"] is True
    assert body["progression"]["unlockedHeroDefinitionIds"] == sorted(
        INITIAL_UNLOCKED_HERO_IDS
    )
    assert body["progression"]["grantedRewards"] == []
    assert all(
        stage["highestCompletedBattle"] == 0
        for stage in body["progression"]["stageProgress"]
    )
    assert occupied.status_code == 409
    assert occupied.json()["detail"]["code"] == "slotOccupied"
    assert injected.status_code == 422
    assert client.get("/api/v1/save-slots").json()["slots"][2]["occupied"] is False


def test_slots_are_isolated_and_survive_restart(slot_client):
    client, store = slot_client
    slot_one = client.post("/api/v1/save-slots/1/create").json()
    store.commit_victory(
        battle_id="battle.slot-one.1",
        stage_id="warriors-barrack",
        battle_index=1,
    )
    slot_two = client.post("/api/v1/save-slots/2/create").json()

    assert slot_one["progression"]["profileId"] != slot_two["progression"]["profileId"]
    assert _stage(slot_two["progression"], "warriors-barrack")[
        "highestCompletedBattle"
    ] == 0

    restarted = ProgressionStore(store.database_path)
    assert _stage(restarted.read_progression(), "warriors-barrack")[
        "highestCompletedBattle"
    ] == 0
    restored = restarted.load_save_slot(1)
    assert _stage(restored["progression"], "warriors-barrack")[
        "highestCompletedBattle"
    ] == 1


def test_cancelled_overwrite_makes_no_write_and_confirmed_overwrite_resets(slot_client):
    client, store = slot_client
    original = client.post("/api/v1/save-slots/4/create").json()
    store.commit_victory(
        battle_id="battle.before-overwrite.1",
        stage_id="paladins-altar",
        battle_index=1,
    )
    before = client.get("/api/v1/save-slots").json()["slots"][3]

    cancelled = client.post(
        "/api/v1/save-slots/4/overwrite", json={"confirmOverwrite": False}
    )
    after_cancel = client.get("/api/v1/save-slots").json()["slots"][3]
    confirmed = client.post(
        "/api/v1/save-slots/4/overwrite", json={"confirmOverwrite": True}
    )

    assert cancelled.status_code == 409
    assert cancelled.json()["detail"]["code"] == "overwriteConfirmationRequired"
    assert after_cancel == before
    assert confirmed.status_code == 200
    assert confirmed.json()["progression"]["profileId"] != original["progression"][
        "profileId"
    ]
    assert _stage(confirmed.json()["progression"], "paladins-altar")[
        "highestCompletedBattle"
    ] == 0


def test_overwrite_failure_rolls_back_old_profile(tmp_path: Path):
    database = tmp_path / "rollback.sqlite3"
    store = ProgressionStore(database)
    original = store.create_save_slot(1)["progression"]
    store.commit_victory(
        battle_id="battle.rollback.slot.1",
        stage_id="paladins-altar",
        battle_index=1,
    )
    with sqlite3.connect(database) as connection:
        connection.execute(
            """CREATE TRIGGER fail_new_profile BEFORE INSERT ON profiles
               BEGIN SELECT RAISE(ABORT, 'forced overwrite failure'); END"""
        )

    with pytest.raises(ProgressionStoreError):
        store.overwrite_save_slot(1)

    unchanged = store.read_progression()
    assert unchanged["profileId"] == original["profileId"]
    assert _stage(unchanged, "paladins-altar")["highestCompletedBattle"] == 1


def test_legacy_default_migrates_once_without_data_loss(tmp_path: Path):
    database = tmp_path / "legacy.sqlite3"
    _create_legacy_v1(database)

    migrated = ProgressionStore(database)
    slots = migrated.list_save_slots()
    progress = migrated.read_progression()
    restarted = ProgressionStore(database)

    assert slots["activeSlotId"] == 1
    assert [slot["occupied"] for slot in slots["slots"]] == [True, False, False, False, False]
    assert progress["profileId"] == DEFAULT_PROFILE_ID
    assert _stage(progress, "paladins-altar")["highestCompletedBattle"] == 3
    assert _stage(progress, "warriors-barrack")["highestCompletedBattle"] == 6
    assert progress["grantedRewards"] == [{"rewardId": ITEM_CARD_REWARD_ID, "count": 1}]
    assert "hero.priest.discipline" in progress["unlockedHeroDefinitionIds"]
    assert restarted.read_progression() == progress
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM profiles").fetchone()[0] == 1
        assert connection.execute(
            "SELECT value FROM metadata WHERE key = 'schema_version'"
        ).fetchone()[0] == "2"


def test_impossible_legacy_migration_fails_without_reset(tmp_path: Path):
    database = tmp_path / "impossible.sqlite3"
    _create_legacy_v1(database)
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE save_slots (slot_id INTEGER PRIMARY KEY)")

    with pytest.raises(ProgressionStoreError, match="migration"):
        ProgressionStore(database).list_save_slots()

    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT value FROM metadata WHERE key = 'schema_version'"
        ).fetchone()[0] == "1"
        assert connection.execute(
            "SELECT COUNT(*) FROM profiles WHERE profile_id = ?", (DEFAULT_PROFILE_ID,)
        ).fetchone()[0] == 1
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'active_slot'"
        ).fetchone() is None


def test_incomplete_legacy_payload_rolls_back_schema_upgrade(tmp_path: Path):
    database = tmp_path / "incomplete-legacy.sqlite3"
    _create_legacy_v1(database)
    with sqlite3.connect(database) as connection:
        connection.execute(
            "DELETE FROM stage_progress WHERE stage_id = 'paladins-altar'"
        )

    with pytest.raises(ProgressionStoreError, match="incomplete or corrupt"):
        ProgressionStore(database).list_save_slots()

    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT value FROM metadata WHERE key = 'schema_version'"
        ).fetchone()[0] == "1"
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'save_slots'"
        ).fetchone() is None
        assert connection.execute(
            "SELECT COUNT(*) FROM profiles WHERE profile_id = ?", (DEFAULT_PROFILE_ID,)
        ).fetchone()[0] == 1


def test_database_write_contention_is_retryable_and_preserves_active_slot(
    tmp_path: Path,
):
    database = tmp_path / "locked.sqlite3"
    store = ProgressionStore(database)
    original = store.create_save_slot(1)
    with sqlite3.connect(database) as blocker:
        blocker.execute("BEGIN IMMEDIATE")
        with pytest.raises(ProgressionStoreError, match="Retry later"):
            store.load_save_slot(1)

    assert store.read_progression()["profileId"] == original["progression"][
        "profileId"
    ]


def test_stage_completion_rejects_session_after_active_slot_switch(slot_client):
    client, _store = slot_client
    client.post("/api/v1/save-slots/1/create")
    created = client.post(
        "/api/v1/stages/warriors-barrack/battles/1",
        json={
            "playerTeam": [
                "hero.warrior.weapon_master",
                "hero.mage.comprehensiveness",
            ],
            "playerFormation": "front-rear",
        },
    )
    battle_id = created.json()["battleId"]
    session = registry.get(battle_id)
    for enemy in session.game.opponent_heroes:
        enemy.hp = 0
    session.game.game_state = "game_over"
    client.post("/api/v1/save-slots/2/create")

    stale = client.post(f"/api/v1/battles/{battle_id}/completion")
    active = client.get("/api/v1/progression").json()

    assert stale.status_code == 409
    assert stale.json()["detail"]["code"] == "activeSaveSlotChanged"
    assert _stage(active, "warriors-barrack")["highestCompletedBattle"] == 0


def test_openapi_exposes_typed_slot_contracts_without_changing_battle_create():
    schema = app.openapi()
    paths = schema["paths"]

    assert "/api/v1/save-slots" in paths
    assert "/api/v1/save-slots/{slot_id}/create" in paths
    assert "/api/v1/save-slots/{slot_id}/load" in paths
    assert "/api/v1/save-slots/{slot_id}/overwrite" in paths
    assert paths["/api/v1/save-slots"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]["$ref"].endswith("SaveSlotListResponse")
    overwrite_schema = paths["/api/v1/save-slots/{slot_id}/overwrite"]["post"][
        "requestBody"
    ]["content"]["application/json"]["schema"]
    assert overwrite_schema["$ref"].endswith("ConfirmSaveSlotOverwriteRequest")
    create_properties = schema["components"]["schemas"]["CreateBattleRequest"][
        "properties"
    ]
    assert not ({"slotId", "profileId", "progression"} & set(create_properties))
