from __future__ import annotations

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from battle_api.app import (
    app,
    battle_attempt_registry,
    get_progression_store,
    registry,
)
from battle_api.attempts import BattleAttemptRegistry
from battle_api.progression import ProgressionStore


@pytest.fixture()
def progression_client(tmp_path: Path):
    store = ProgressionStore(tmp_path / "rng001.sqlite3")
    store.create_save_slot(1)
    app.dependency_overrides[get_progression_store] = lambda: store
    battle_attempt_registry.clear()
    try:
        with TestClient(app) as client:
            yield client, store
    finally:
        battle_attempt_registry.clear()
        app.dependency_overrides.clear()


def _stage_payload(attempt_id: str | None = None, **overrides: object) -> dict:
    payload: dict[str, object] = {
        "playerTeam": [
            "hero.warrior.weapon_master",
            "hero.mage.comprehensiveness",
        ],
        "playerFormation": "front-rear",
    }
    if attempt_id is not None:
        payload["attemptId"] = attempt_id
    payload.update(overrides)
    return payload


def _unlock_six(store: ProgressionStore) -> list[str]:
    for stage_id in ("paladins-altar", "warriors-barrack"):
        for battle_index in range(1, 4):
            store.commit_victory(
                battle_id=f"rng001.unlock.{stage_id}.{battle_index}",
                stage_id=stage_id,
                battle_index=battle_index,
            )
    return store.read_progression()["unlockedHeroDefinitionIds"]


def test_stage_attempt_id_replays_transport_retry_without_second_entropy_draw(
    progression_client, monkeypatch: pytest.MonkeyPatch
):
    client, _store = progression_client
    seeds = iter((101, 202, 303))
    monkeypatch.setattr("battle_api.app._fresh_battle_seed", lambda: next(seeds))

    first = client.post(
        "/api/v1/stages/warriors-barrack/battles/1",
        json=_stage_payload("stage-attempt-1"),
    )
    retry = client.post(
        "/api/v1/stages/warriors-barrack/battles/1",
        json=_stage_payload("stage-attempt-1"),
    )
    new_attempt = client.post(
        "/api/v1/stages/warriors-barrack/battles/1",
        json=_stage_payload("stage-attempt-2"),
    )

    assert first.status_code == retry.status_code == new_attempt.status_code == 200
    assert first.json()["battleId"] == retry.json()["battleId"]
    assert registry.get(first.json()["battleId"]).seed == 101
    assert registry.get(new_attempt.json()["battleId"]).seed == 202


def test_stage_attempt_id_conflict_does_not_create_or_consume_a_new_attempt(
    progression_client, monkeypatch: pytest.MonkeyPatch
):
    client, _store = progression_client
    seeds = iter((404, 505))
    monkeypatch.setattr("battle_api.app._fresh_battle_seed", lambda: next(seeds))

    created = client.post(
        "/api/v1/stages/warriors-barrack/battles/1",
        json=_stage_payload("stage-conflict"),
    )
    conflict = client.post(
        "/api/v1/stages/warriors-barrack/battles/1",
        json=_stage_payload("stage-conflict", playerFormation="side-by-side"),
    )
    next_attempt = client.post(
        "/api/v1/stages/warriors-barrack/battles/1",
        json=_stage_payload("stage-conflict-new"),
    )

    assert created.status_code == 200
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["code"] == "battleAttemptConflict"
    assert next_attempt.status_code == 200
    assert registry.get(next_attempt.json()["battleId"]).seed == 505


def test_attempt_id_cannot_cross_active_save_profiles(
    progression_client, monkeypatch: pytest.MonkeyPatch
):
    client, _store = progression_client
    seeds = iter((515, 616))
    monkeypatch.setattr("battle_api.app._fresh_battle_seed", lambda: next(seeds))

    first = client.post(
        "/api/v1/stages/warriors-barrack/battles/1",
        json=_stage_payload("profile-bound-attempt"),
    )
    switched = client.post("/api/v1/save-slots/2/create")
    same_id_in_other_profile = client.post(
        "/api/v1/stages/warriors-barrack/battles/1",
        json=_stage_payload("profile-bound-attempt"),
    )
    new_id_in_other_profile = client.post(
        "/api/v1/stages/warriors-barrack/battles/1",
        json=_stage_payload("profile-bound-attempt-new"),
    )

    assert first.status_code == 200
    assert switched.status_code == 200
    assert same_id_in_other_profile.status_code == 409
    assert same_id_in_other_profile.json()["detail"]["code"] == "battleAttemptConflict"
    assert new_id_in_other_profile.status_code == 200
    assert registry.get(first.json()["battleId"]).seed == 515
    assert registry.get(new_id_in_other_profile.json()["battleId"]).seed == 616


def test_arena_new_attempts_are_fresh_but_preserve_node_configuration(
    progression_client, monkeypatch: pytest.MonkeyPatch
):
    client, store = progression_client
    squad = _unlock_six(store)[:6]
    run = store.create_arena_run(squad, schedule_seed=81)["run"]
    node = run["nodes"][0]
    formation = {1: None, 2: "front-rear", 3: "one-front-two-rear"}[node["battleSize"]]
    payload = {
        "playerTeam": squad[: node["battleSize"]],
        "playerFormation": formation,
    }
    seeds = iter((606, 707))
    monkeypatch.setattr("battle_api.app._fresh_battle_seed", lambda: next(seeds))

    first = client.post(
        f"/api/v1/arena/runs/{run['runId']}/nodes/1/battles",
        json={**payload, "attemptId": "arena-attempt-1"},
    )
    retry = client.post(
        f"/api/v1/arena/runs/{run['runId']}/nodes/1/battles",
        json={**payload, "attemptId": "arena-attempt-1"},
    )
    second_attempt = client.post(
        f"/api/v1/arena/runs/{run['runId']}/nodes/1/battles",
        json={**payload, "attemptId": "arena-attempt-2"},
    )

    assert first.status_code == retry.status_code == second_attempt.status_code == 200
    assert first.json()["battleId"] == retry.json()["battleId"]
    first_session = registry.get(first.json()["battleId"])
    second_session = registry.get(second_attempt.json()["battleId"])
    assert first_session.seed == 606
    assert second_session.seed == 707
    first_snapshot = first.json()["data"]["snapshot"]
    second_snapshot = second_attempt.json()["data"]["snapshot"]
    assert first_snapshot["formations"] == second_snapshot["formations"]
    assert [
        first_snapshot["combatants"][hero_id]["definitionId"]
        for hero_id in first_snapshot["sides"][1]["combatantIds"]
    ] == [
        second_snapshot["combatants"][hero_id]["definitionId"]
        for hero_id in second_snapshot["sides"][1]["combatantIds"]
    ] == node["enemyDefinitionIds"]


def test_legacy_arena_run_survives_store_reload_without_seed_migration(
    progression_client, monkeypatch: pytest.MonkeyPatch
):
    client, store = progression_client
    squad = _unlock_six(store)[:6]
    run = store.create_arena_run(squad, schedule_seed=901)["run"]
    node = run["nodes"][0]
    formation = {1: None, 2: "side-by-side", 3: "all-front"}[node["battleSize"]]
    reloaded_store = ProgressionStore(store.database_path)
    app.dependency_overrides[get_progression_store] = lambda: reloaded_store
    monkeypatch.setattr("battle_api.app._fresh_battle_seed", lambda: 919)

    response = client.post(
        f"/api/v1/arena/runs/{run['runId']}/nodes/1/battles",
        json={
            "playerTeam": squad[: node["battleSize"]],
            "playerFormation": formation,
            "attemptId": "legacy-reloaded-arena",
        },
    )

    assert response.status_code == 200
    assert reloaded_store.read_arena_state()["run"]["runId"] == run["runId"]
    assert reloaded_store.read_arena_state()["run"]["nodes"][0] == node
    assert registry.get(response.json()["battleId"]).seed == 919


def test_explicit_stage_seed_remains_reproducible_and_legacy_requests_remain_compatible(
    progression_client,
):
    client, _store = progression_client
    seeded_one = client.post(
        "/api/v1/stages/warriors-barrack/battles/1",
        json=_stage_payload("seeded-1", seed=8181),
    )
    seeded_two = client.post(
        "/api/v1/stages/warriors-barrack/battles/1",
        json=_stage_payload("seeded-2", seed=8181),
    )
    legacy_one = client.post(
        "/api/v1/stages/warriors-barrack/battles/1",
        json=_stage_payload(),
    )
    legacy_two = client.post(
        "/api/v1/stages/warriors-barrack/battles/1",
        json=_stage_payload(),
    )

    assert seeded_one.status_code == seeded_two.status_code == 200
    assert registry.get(seeded_one.json()["battleId"]).seed == 8181
    assert registry.get(seeded_two.json()["battleId"]).seed == 8181
    assert seeded_one.json()["data"]["snapshot"] == seeded_two.json()["data"]["snapshot"]
    assert legacy_one.status_code == legacy_two.status_code == 200
    assert legacy_one.json()["battleId"] != legacy_two.json()["battleId"]


def test_attempt_registry_concurrent_same_id_calls_factory_once():
    attempts = BattleAttemptRegistry()
    factory_calls = 0

    def factory():
        nonlocal factory_calls
        factory_calls += 1
        return object(), {"battleId": "battle.concurrent"}

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(
            lambda _index: attempts.get_or_create(
                profile_id="profile.concurrent",
                attempt_id="attempt.concurrent",
                fingerprint=("stage", 1),
                factory=factory,
            ),
            range(8),
        ))

    assert factory_calls == 1
    assert {envelope["battleId"] for _session, envelope in results} == {
        "battle.concurrent"
    }
