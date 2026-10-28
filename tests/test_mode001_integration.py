from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from battle_api.app import app, get_progression_store, registry
from battle_api.adapter import BattleAdapter
from battle_api.progression import ProgressionStore, STAGE_BATTLES


@pytest.fixture()
def mode_client(tmp_path: Path):
    store = ProgressionStore(tmp_path / "mode001.sqlite3")
    store.create_save_slot(1)
    app.dependency_overrides[get_progression_store] = lambda: store
    with TestClient(app) as client:
        yield client, store
    app.dependency_overrides.clear()


def _stage_progress(client, stage_id: str) -> dict:
    body = client.get("/api/v1/stages").json()
    return next(stage for stage in body["stages"] if stage["stageId"] == stage_id)


def _complete_learner_campaign(store: ProgressionStore, stage_id: str) -> None:
    for battle in STAGE_BATTLES[stage_id]:
        store.commit_victory(
            battle_id=f"mode001.learner.{stage_id}.{battle.battle_index}",
            stage_id=stage_id,
            battle_index=battle.battle_index,
            mode="learner",
        )


def test_new_profile_publishes_learner_default_and_locked_tactics(mode_client):
    client, _store = mode_client
    stage = _stage_progress(client, "warriors-barrack")

    assert stage["modes"] == {
        "learner": {
            "available": True,
            "completed": False,
            "completedBattleIndices": [],
        },
        "tactics": {
            "available": False,
            "completed": False,
            "completedBattleIndices": [],
        },
    }

    locked = client.post(
        "/api/v1/stages/warriors-barrack/battles/1",
        json={
            "mode": "tactics",
            "playerTeam": ["hero.warrior.weapon_master", "hero.mage.comprehensiveness"],
            "playerFormation": "front-rear",
            "seed": 701,
        },
    )
    assert locked.status_code == 409
    assert locked.json()["detail"]["code"] == "stageModeLocked"


def test_invalid_mode_is_rejected_without_launching(mode_client):
    client, _store = mode_client
    response = client.post(
        "/api/v1/stages/warriors-barrack/battles/1",
        json={
            "mode": "expert",
            "playerTeam": ["hero.warrior.weapon_master", "hero.mage.comprehensiveness"],
            "playerFormation": "front-rear",
        },
    )
    assert response.status_code == 422


def test_campaign_unlock_is_scoped_and_tactics_is_any_order_without_rewards(mode_client):
    client, store = mode_client
    _complete_learner_campaign(store, "warriors-barrack")

    warrior = _stage_progress(client, "warriors-barrack")
    paladin = _stage_progress(client, "paladins-altar")
    assert warrior["modes"]["tactics"]["available"] is True
    assert paladin["modes"]["tactics"]["available"] is False

    response = client.post(
        "/api/v1/stages/warriors-barrack/battles/8",
        json={
            "mode": "tactics",
            "playerTeam": ["hero.warrior.weapon_master"],
            "seed": 702,
            "attemptId": "mode001-tactics-any-order",
        },
    )
    assert response.status_code == 200
    battle_id = response.json()["battleId"]
    session = registry.get(battle_id)
    assert session is not None
    assert session.stage_mode == "tactics"

    result = store.commit_victory(
        battle_id="mode001.tactics.warriors-barrack.8",
        stage_id="warriors-barrack",
        battle_index=8,
        mode="tactics",
    )
    assert result["newlyGrantedRewards"] == []
    warrior_progress = next(
        item for item in result["progression"]["stageProgress"]
        if item["stageId"] == "warriors-barrack"
    )
    assert warrior_progress["highestCompletedBattle"] == 9


def test_attempt_id_cannot_switch_structured_mode(mode_client):
    client, store = mode_client
    _complete_learner_campaign(store, "warriors-barrack")
    payload = {
        "playerTeam": ["hero.warrior.weapon_master"],
        "seed": 703,
        "attemptId": "mode001-cross-mode",
    }
    learner = client.post(
        "/api/v1/stages/warriors-barrack/battles/8",
        json={**payload, "mode": "learner"},
    )
    assert learner.status_code == 200
    tactics = client.post(
        "/api/v1/stages/warriors-barrack/battles/8",
        json={**payload, "mode": "tactics"},
    )
    assert tactics.status_code == 409
    assert tactics.json()["detail"]["code"] == "battleAttemptConflict"


def test_learner_enemy_does_not_invoke_specialization_ai(monkeypatch):
    """Learner policy must bypass hero strategy and use the session RNG path."""
    adapter = BattleAdapter()
    session, _envelope = adapter.create_battle(
        seed=704,
        battle_size=1,
        player_team=["hero.warrior.weapon_master"],
        enemy_team=["hero.warrior.berserker"],
        enemy_control_mode="computer",
        stage_id="warriors-barrack",
        stage_battle_index=1,
        stage_mode="learner",
    )
    enemy = session.game.opponent_heroes[0]
    session.game.unactioned_sorted_heroes = [enemy]
    enemy.actioned = False

    def strategy_must_not_run(*_args, **_kwargs):
        raise AssertionError("Learner invoked specialization strategy")

    def resolve_once(_session, command):
        assert command["actorId"] == adapter._combatant_id(session, enemy)
        enemy.actioned = True
        session.game.unactioned_sorted_heroes = []
        return {"events": []}

    monkeypatch.setattr(enemy, "ai_choose_skill", strategy_must_not_run)
    monkeypatch.setattr(adapter, "_resolve", resolve_once)
    adapter._drain_automatic_turns(session, maximum_turns=2)
