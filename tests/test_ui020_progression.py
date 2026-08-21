from __future__ import annotations

from pathlib import Path
import sqlite3

from fastapi.testclient import TestClient
import pytest

from battle_api.app import app, get_progression_store, registry
from battle_api.progression import (
    INITIAL_UNLOCKED_HERO_IDS,
    ITEM_CARD_REWARD_ID,
    ProgressionStore,
    ProgressionStoreError,
    STAGE_BATTLES,
)


@pytest.fixture()
def progression_client(tmp_path: Path):
    store = ProgressionStore(tmp_path / "progression.sqlite3")
    store.create_save_slot(1)
    app.dependency_overrides[get_progression_store] = lambda: store
    with TestClient(app) as client:
        yield client, store
    app.dependency_overrides.clear()


def _progress(progress, stage_id):
    return next(item for item in progress["stageProgress"] if item["stageId"] == stage_id)


def _launch_stage_battle(client, stage_id, index, player_team, formation=None):
    payload = {"playerTeam": player_team, "seed": index}
    if formation is not None:
        payload["playerFormation"] = formation
    return client.post(f"/api/v1/stages/{stage_id}/battles/{index}", json=payload)


def _force_friendly_victory(battle_id):
    session = registry.get(battle_id)
    for enemy in session.game.opponent_heroes:
        enemy.hp = 0
    session.game.game_state = "game_over"


def test_active_slot_initialization_is_typed_persistent_and_uses_exact_fresh_roster(
    progression_client,
):
    client, store = progression_client

    response = client.get("/api/v1/progression")

    assert response.status_code == 200
    body = response.json()
    assert body["contractVersion"] == "1.0"
    assert body["profileId"].startswith("profile.local.slot.1.")
    assert body["unlockedHeroDefinitionIds"] == sorted(INITIAL_UNLOCKED_HERO_IDS)
    assert body["grantedRewards"] == []
    assert body["stageProgress"] == [
        {
            "stageId": "paladins-altar",
            "highestCompletedBattle": 0,
            "unlockedBattle": 1,
            "completed": False,
        },
        {
            "stageId": "warriors-barrack",
            "highestCompletedBattle": 0,
            "unlockedBattle": 1,
            "completed": False,
        },
    ]
    restarted = ProgressionStore(store.database_path).read_progression()
    assert restarted == {key: body[key] for key in body if key != "contractVersion"}


def test_stage_catalogue_exposes_exact_two_nine_battle_curricula(progression_client):
    client, _store = progression_client

    response = client.get("/api/v1/stages")

    assert response.status_code == 200
    stages = {stage["stageId"]: stage for stage in response.json()["stages"]}
    assert set(stages) == {"paladins-altar", "warriors-barrack"}
    for stage_id, static_battles in STAGE_BATTLES.items():
        battles = stages[stage_id]["battles"]
        assert len(battles) == 9
        assert [
            (
                battle["displayOrder"],
                battle["battleSize"],
                battle["formation"],
                tuple(battle["enemyDefinitionIds"]),
                battle["reward"]["rewardId"] if battle["reward"] else None,
            )
            for battle in battles
        ] == [
            (
                battle.battle_index,
                battle.battle_size,
                battle.formation,
                battle.enemy_definition_ids,
                battle.reward.reward_id if battle.reward else None,
            )
            for battle in static_battles
        ]
        assert [battle["unlocked"] for battle in battles] == [True] + [False] * 8


def test_arena_and_stage_player_teams_are_owned_but_fixed_enemies_use_static_roster(
    progression_client,
):
    client, _store = progression_client
    locked = client.post(
        "/api/v1/battles",
        json={
            "battleSize": 1,
            "playerTeam": ["hero.warrior.berserker"],
            "enemyTeam": ["hero.rogue.comprehensiveness"],
        },
    )
    assert locked.status_code == 409
    assert locked.json()["detail"]["code"] == "heroLocked"

    stage_locked_team = _launch_stage_battle(
        client,
        "warriors-barrack",
        1,
        ["hero.warrior.weapon_master", "hero.warrior.berserker"],
        "front-rear",
    )
    assert stage_locked_team.status_code == 409
    assert stage_locked_team.json()["detail"]["code"] == "heroLocked"

    created = _launch_stage_battle(
        client,
        "warriors-barrack",
        1,
        ["hero.warrior.weapon_master", "hero.mage.comprehensiveness"],
        "front-rear",
    )
    assert created.status_code == 200
    snapshot = created.json()["data"]["snapshot"]
    enemy_ids = [
        snapshot["combatants"][combatant_id]["definitionId"]
        for combatant_id in snapshot["sides"][1]["combatantIds"]
    ]
    assert enemy_ids == [
        "hero.warrior.berserker",
        "hero.priest.comprehensiveness",
    ]
    assert snapshot["formations"] == {
        "friendly": "front-rear",
        "enemy": "front-rear",
    }


def test_stage_access_and_player_formation_choice_are_server_protected(progression_client):
    client, store = progression_client
    locked = _launch_stage_battle(
        client,
        "paladins-altar",
        2,
        ["hero.warrior.weapon_master"],
    )
    assert locked.status_code == 409
    assert locked.json()["detail"]["code"] == "stageBattleLocked"

    wrong_size = _launch_stage_battle(
        client,
        "paladins-altar",
        1,
        ["hero.warrior.weapon_master"],
        "front-rear",
    )
    assert wrong_size.status_code == 422
    assert wrong_size.json()["detail"]["code"] == "invalidStageBattleConfiguration"

    player_selected_formation = _launch_stage_battle(
        client,
        "paladins-altar",
        1,
        ["hero.warrior.weapon_master", "hero.mage.comprehensiveness"],
        "side-by-side",
    )
    assert player_selected_formation.status_code == 200
    assert player_selected_formation.json()["data"]["snapshot"]["formations"] == {
        "friendly": "side-by-side",
        "enemy": "front-rear",
    }

    wrong_size_formation = _launch_stage_battle(
        client,
        "paladins-altar",
        1,
        ["hero.warrior.weapon_master", "hero.mage.comprehensiveness"],
        "all-front",
    )
    assert wrong_size_formation.status_code == 422

    store.commit_victory(
        battle_id="unlock.paladins-altar.1",
        stage_id="paladins-altar",
        battle_index=1,
    )
    store.commit_victory(
        battle_id="unlock.paladins-altar.2",
        stage_id="paladins-altar",
        battle_index=2,
    )
    trio_choice = _launch_stage_battle(
        client,
        "paladins-altar",
        3,
        [
            "hero.warrior.weapon_master",
            "hero.mage.comprehensiveness",
            "hero.priest.comprehensiveness",
        ],
        "all-front",
    )
    assert trio_choice.status_code == 200
    assert trio_choice.json()["data"]["snapshot"]["formations"] == {
        "friendly": "all-front",
        "enemy": "two-front-one-rear",
    }


def test_only_authoritative_friendly_victory_commits_and_replay_is_idempotent(
    progression_client,
):
    client, _store = progression_client
    created = _launch_stage_battle(
        client,
        "warriors-barrack",
        1,
        ["hero.warrior.weapon_master", "hero.mage.comprehensiveness"],
        "front-rear",
    ).json()
    battle_id = created["battleId"]

    unfinished = client.post(f"/api/v1/battles/{battle_id}/completion")
    assert unfinished.status_code == 409
    assert unfinished.json()["detail"]["code"] == "friendlyVictoryRequired"

    _force_friendly_victory(battle_id)
    first = client.post(f"/api/v1/battles/{battle_id}/completion")
    replay = client.post(f"/api/v1/battles/{battle_id}/completion")

    assert first.status_code == replay.status_code == 200
    assert first.json()["alreadyCommitted"] is False
    assert replay.json()["alreadyCommitted"] is True
    assert replay.json()["newlyGrantedRewards"] == []
    assert _progress(first.json()["progression"], "warriors-barrack") == {
        "stageId": "warriors-barrack",
        "highestCompletedBattle": 1,
        "unlockedBattle": 2,
        "completed": False,
    }


def test_exact_rewards_are_granted_once_and_survive_restart(tmp_path: Path):
    database = tmp_path / "progression.sqlite3"
    store = ProgressionStore(database)
    store.create_save_slot(1)

    newly_granted = []
    for stage_id in ("paladins-altar", "warriors-barrack"):
        for index in range(1, 10):
            result = store.commit_victory(
                battle_id=f"battle.{stage_id}.{index}",
                stage_id=stage_id,
                battle_index=index,
            )
            newly_granted.extend(result["newlyGrantedRewards"])

    restarted = ProgressionStore(database).read_progression()
    assert {reward["rewardId"] for reward in newly_granted} == {
        "unlock.hero.paladin.protection",
        "unlock.hero.paladin.retribution",
        "unlock.hero.paladin.holy",
        "unlock.hero.warrior.berserker",
        ITEM_CARD_REWARD_ID,
        "unlock.hero.warrior.defence",
    }
    assert set(restarted["unlockedHeroDefinitionIds"]) == {
        *INITIAL_UNLOCKED_HERO_IDS,
        "hero.paladin.protection",
        "hero.paladin.retribution",
        "hero.paladin.holy",
        "hero.warrior.berserker",
        "hero.warrior.defence",
    }
    assert restarted["grantedRewards"] == [
        {"rewardId": reward_id, "count": 1}
        for reward_id in sorted({reward["rewardId"] for reward in newly_granted})
    ]
    assert all(progress["completed"] for progress in restarted["stageProgress"])


def test_reward_failure_rolls_back_progress_completion_and_unlock(tmp_path: Path):
    database = tmp_path / "progression.sqlite3"
    store = ProgressionStore(database)
    store.create_save_slot(1)
    store.commit_victory(
        battle_id="battle.rollback.1", stage_id="paladins-altar", battle_index=1
    )
    store.commit_victory(
        battle_id="battle.rollback.2", stage_id="paladins-altar", battle_index=2
    )
    with sqlite3.connect(database) as connection:
        connection.execute(
            """CREATE TRIGGER fail_reward BEFORE INSERT ON granted_rewards
               BEGIN SELECT RAISE(ABORT, 'forced reward failure'); END"""
        )

    with pytest.raises(ProgressionStoreError):
        store.commit_victory(
            battle_id="battle.rollback.3", stage_id="paladins-altar", battle_index=3
        )

    unchanged = store.read_progression()
    assert _progress(unchanged, "paladins-altar")["highestCompletedBattle"] == 2
    assert "hero.paladin.protection" not in unchanged["unlockedHeroDefinitionIds"]
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT 1 FROM battle_completions WHERE battle_id = 'battle.rollback.3'"
        ).fetchone() is None


def test_corrupt_and_disappeared_store_return_retryable_503(tmp_path: Path):
    corrupt_path = tmp_path / "corrupt.sqlite3"
    corrupt_path.write_bytes(b"not a sqlite database")
    corrupt_store = ProgressionStore(corrupt_path)
    app.dependency_overrides[get_progression_store] = lambda: corrupt_store
    with TestClient(app) as client:
        corrupt = client.get("/api/v1/progression")
    assert corrupt.status_code == 503
    assert corrupt.json()["detail"]["retryable"] is True

    missing_path = tmp_path / "missing.sqlite3"
    missing_store = ProgressionStore(missing_path)
    missing_store.list_save_slots()
    missing_path.unlink()
    app.dependency_overrides[get_progression_store] = lambda: missing_store
    with TestClient(app) as client:
        missing = client.get("/api/v1/stages")
    app.dependency_overrides.clear()
    assert missing.status_code == 503
    assert missing.json()["detail"]["code"] == "progressionStoreUnavailable"
    assert missing.json()["detail"]["retryable"] is True


def test_openapi_keeps_battle_create_shape_and_adds_typed_progression_contracts():
    schema = app.openapi()
    create_properties = schema["components"]["schemas"]["CreateBattleRequest"]["properties"]
    assert not ({"stageId", "stageBattleIndex", "progression"} & set(create_properties))
    assert schema["paths"]["/api/v1/progression"]["get"]["responses"]["200"][
        "content"
    ]["application/json"]["schema"]["$ref"].endswith("PlayerProgressionResponse")
    assert schema["paths"]["/api/v1/battles/{battle_id}/completion"]["post"][
        "responses"
    ]["200"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "VictoryCommitResponse"
    )
