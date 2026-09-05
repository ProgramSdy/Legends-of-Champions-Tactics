from __future__ import annotations

from pathlib import Path
import sqlite3

from fastapi.testclient import TestClient
import pytest

from battle_api.adapter import HERO_ROSTER
from battle_api.app import app, get_progression_store, registry
from battle_api.progression import (
    ALL_HERO_IDS,
    ARENA_FRONT_HERO_IDS,
    ARENA_NODE_COUNT,
    ARENA_REAR_HERO_IDS,
    ArenaAccessError,
    ProgressionStore,
    ProgressionStoreError,
)


@pytest.fixture()
def arena_client(tmp_path: Path):
    store = ProgressionStore(tmp_path / "arena.sqlite3")
    store.create_save_slot(1)
    app.dependency_overrides[get_progression_store] = lambda: store
    with TestClient(app) as client:
        yield client, store
    app.dependency_overrides.clear()


def _unlock_six(store: ProgressionStore) -> list[str]:
    for stage_id in ("paladins-altar", "warriors-barrack"):
        for battle_index in range(1, 4):
            store.commit_victory(
                battle_id=f"unlock.{stage_id}.{battle_index}",
                stage_id=stage_id,
                battle_index=battle_index,
            )
    return store.read_progression()["unlockedHeroDefinitionIds"]


def _force_friendly_victory(battle_id: str) -> None:
    session = registry.get(battle_id)
    assert session is not None
    for enemy in session.game.opponent_heroes:
        enemy.hp = 0
    session.game.game_state = "game_over"


def test_arena_is_gated_at_exact_unlocked_count_and_rejects_forged_squad(
    arena_client,
):
    client, store = arena_client

    state = client.get("/api/v1/arena")
    blocked = client.post(
        "/api/v1/arena/runs",
        json={"squadDefinitionIds": list(store.read_progression()[
            "unlockedHeroDefinitionIds"
        ]) + ["hero.paladin.protection", "hero.warrior.berserker"]},
    )

    assert state.status_code == 200
    assert state.json()["eligibility"] == {
        "eligible": False,
        "unlockedHeroCount": 4,
        "requiredHeroCount": 6,
    }
    assert blocked.status_code == 409
    assert blocked.json()["detail"]["code"] == "arenaRosterInsufficient"

    unlocked = _unlock_six(store)
    locked = client.post(
        "/api/v1/arena/runs",
        json={"squadDefinitionIds": unlocked[:5] + ["hero.paladin.holy"]},
    )
    duplicate = client.post(
        "/api/v1/arena/runs",
        json={"squadDefinitionIds": [unlocked[0]] * 6},
    )
    assert locked.status_code == 409
    assert locked.json()["detail"]["code"] == "arenaSquadHeroLocked"
    assert duplicate.status_code == 422


def test_seeded_schedule_is_stable_valid_and_survives_restart(tmp_path: Path):
    database = tmp_path / "arena.sqlite3"
    store = ProgressionStore(database)
    store.create_save_slot(1)
    squad = _unlock_six(store)[:6]

    created = store.create_arena_run(squad, schedule_seed=2301)
    restarted = ProgressionStore(database).read_arena_state()
    run = created["run"]

    assert restarted == created
    assert run["squadDefinitionIds"] == squad
    assert run["currentNodeIndex"] == 1
    assert len(run["nodes"]) == ARENA_NODE_COUNT
    assert [node["nodeIndex"] for node in run["nodes"]] == list(range(1, 13))
    for node in run["nodes"]:
        assert len(node["enemyDefinitionIds"]) == node["battleSize"]
        assert set(node["enemyDefinitionIds"]).issubset(ALL_HERO_IDS)
        positions = {
            None: ("front",),
            "side-by-side": ("front", "front"),
            "front-rear": ("front", "rear"),
            "all-front": ("front", "front", "front"),
            "two-front-one-rear": ("front", "front", "rear"),
            "one-front-two-rear": ("front", "rear", "rear"),
        }[node["enemyFormation"]]
        if node["enemyFormation"] not in {None, "side-by-side", "all-front"}:
            for hero_id, position in zip(
                node["enemyDefinitionIds"], positions, strict=True
            ):
                assert hero_id in (
                    ARENA_FRONT_HERO_IDS if position == "front"
                    else ARENA_REAR_HERO_IDS
                )
    # A replayed create request is idempotent only for the already-locked squad.
    replay = store.create_arena_run(squad, schedule_seed=999)
    assert replay == created
    with pytest.raises(ArenaAccessError, match="active Arena Run"):
        store.create_arena_run(list(reversed(squad)), schedule_seed=2301)


def test_abandon_current_run_deletes_only_the_active_profiles_run(arena_client):
    client, store = arena_client
    squad = _unlock_six(store)[:6]
    run = store.create_arena_run(squad, schedule_seed=41)["run"]

    abandoned = client.post(f"/api/v1/arena/runs/{run['runId']}/abandon")

    assert abandoned.status_code == 200
    assert abandoned.json()["run"] is None
    assert store.read_arena_state()["run"] is None
    missing = client.post(f"/api/v1/arena/runs/{run['runId']}/abandon")
    assert missing.status_code == 404
    assert missing.json()["detail"]["code"] == "arenaRunNotFound"


def test_arena_size_pool_is_fixed_shuffled_and_seeded():
    first = ProgressionStore._generate_arena_nodes(91)
    repeated = ProgressionStore._generate_arena_nodes(91)
    sequences = {
        tuple(node["battleSize"] for node in ProgressionStore._generate_arena_nodes(seed))
        for seed in range(20)
    }

    assert len(first) == ARENA_NODE_COUNT
    assert [node["battleSize"] for node in first].count(1) == 2
    assert [node["battleSize"] for node in first].count(2) == 6
    assert [node["battleSize"] for node in first].count(3) == 4
    assert first == repeated
    assert len(sequences) > 1
    assert any(
        len(node["enemyDefinitionIds"]) != len(set(node["enemyDefinitionIds"]))
        for seed in range(100)
        for node in ProgressionStore._generate_arena_nodes(seed)
    )


def test_debug_creation_uses_full_roster_without_save_or_persistence(tmp_path: Path):
    store = ProgressionStore(tmp_path / "debug.sqlite3")
    app.dependency_overrides[get_progression_store] = lambda: store
    with TestClient(app) as client:
        before = client.get("/api/v1/save-slots").json()
        created = client.post(
            "/api/v1/debug/battles",
            json={
                "battleSize": 2,
                "playerTeam": [
                    "hero.paladin.holy", "hero.priest.discipline",
                ],
                "enemyCompositionMode": "specified",
                "enemyTeam": [
                    "hero.warrior.berserker", "hero.warrior.defence",
                ],
                "enemyControlMode": "player",
                "playerFormation": "side-by-side",
                "enemyFormation": "side-by-side",
                "seed": 23,
            },
        )
        after = client.get("/api/v1/save-slots").json()
    app.dependency_overrides.clear()

    assert created.status_code == 200
    assert before == after
    assert before["activeSlotId"] is None
    with sqlite3.connect(store.database_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM arena_runs").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM profiles").fetchone()[0] == 0


def test_only_current_node_and_locked_squad_can_launch_and_retry_is_stable(
    arena_client,
):
    client, store = arena_client
    squad = _unlock_six(store)[:6]
    run = store.create_arena_run(squad, schedule_seed=9)["run"]
    run_id = run["runId"]
    node = run["nodes"][0]
    formation = {1: None, 2: "side-by-side", 3: "all-front"}[node["battleSize"]]
    payload = {
        "playerTeam": squad[:node["battleSize"]],
        "playerFormation": formation,
    }

    early = client.post(
        f"/api/v1/arena/runs/{run_id}/nodes/2/battles", json=payload
    )
    outside_team = squad[:node["battleSize"]]
    outside_team[0] = "hero.paladin.holy"
    outside = client.post(
        f"/api/v1/arena/runs/{run_id}/nodes/1/battles",
        json={**payload, "playerTeam": outside_team},
    )
    first = client.post(
        f"/api/v1/arena/runs/{run_id}/nodes/1/battles", json=payload
    )
    retry = client.post(
        f"/api/v1/arena/runs/{run_id}/nodes/1/battles", json=payload
    )

    assert early.status_code == 409
    assert early.json()["detail"]["code"] == "arenaNodeOutOfOrder"
    assert outside.status_code == 409
    assert outside.json()["detail"]["code"] == "arenaHeroOutsideSquad"
    assert first.status_code == retry.status_code == 200
    first_snapshot = first.json()["data"]["snapshot"]
    retry_snapshot = retry.json()["data"]["snapshot"]
    assert first_snapshot["formations"] == retry_snapshot["formations"]
    assert [
        first_snapshot["combatants"][hero_id]["definitionId"]
        for hero_id in first_snapshot["sides"][1]["combatantIds"]
    ] == [
        retry_snapshot["combatants"][hero_id]["definitionId"]
        for hero_id in retry_snapshot["sides"][1]["combatantIds"]
    ] == node["enemyDefinitionIds"]


def test_authoritative_victory_advances_once_and_stale_slot_cannot_commit(
    arena_client,
):
    client, store = arena_client
    squad = _unlock_six(store)[:6]
    run = store.create_arena_run(squad, schedule_seed=17)["run"]
    node = run["nodes"][0]
    formation = {1: None, 2: "front-rear", 3: "all-front"}[node["battleSize"]]
    created = client.post(
        f"/api/v1/arena/runs/{run['runId']}/nodes/1/battles",
        json={
            "playerTeam": squad[:node["battleSize"]],
            "playerFormation": formation,
        },
    ).json()
    battle_id = created["battleId"]

    unfinished = client.post(f"/api/v1/arena/battles/{battle_id}/completion")
    _force_friendly_victory(battle_id)
    committed = client.post(f"/api/v1/arena/battles/{battle_id}/completion")
    replay = client.post(f"/api/v1/arena/battles/{battle_id}/completion")

    assert unfinished.status_code == 409
    assert unfinished.json()["detail"]["code"] == "friendlyVictoryRequired"
    assert committed.status_code == replay.status_code == 200
    assert committed.json()["alreadyCommitted"] is False
    assert replay.json()["alreadyCommitted"] is True
    assert replay.json()["arena"]["run"]["currentNodeIndex"] == 2

    # A session created for slot 1 cannot advance after active-slot authority moves.
    node_two = replay.json()["arena"]["run"]["nodes"][1]
    formation_two = {1: None, 2: "front-rear", 3: "all-front"}[
        node_two["battleSize"]
    ]
    second = client.post(
        f"/api/v1/arena/runs/{run['runId']}/nodes/2/battles",
        json={
            "playerTeam": squad[:node_two["battleSize"]],
            "playerFormation": formation_two,
        },
    ).json()
    _force_friendly_victory(second["battleId"])
    client.post("/api/v1/save-slots/2/create")
    stale = client.post(
        f"/api/v1/arena/battles/{second['battleId']}/completion"
    )
    assert stale.status_code == 409
    assert stale.json()["detail"]["code"] == "activeSaveSlotChanged"
    assert client.get("/api/v1/arena").json()["run"] is None


def test_store_completes_twelve_nodes_and_new_run_is_intentional(tmp_path: Path):
    store = ProgressionStore(tmp_path / "complete.sqlite3")
    store.create_save_slot(1)
    squad = _unlock_six(store)[:6]
    first = store.create_arena_run(squad, schedule_seed=31)["run"]

    state = None
    for node_index in range(1, 13):
        result = store.commit_arena_victory(
            run_id=first["runId"],
            node_index=node_index,
            battle_id=f"arena.win.{node_index}",
            expected_profile_id=store.active_profile_id(),
        )
        state = result["arena"]
    assert state["run"]["status"] == "completed"
    assert state["run"]["currentNodeIndex"] is None
    assert all(node["completed"] for node in state["run"]["nodes"])
    assert ProgressionStore(store.database_path).read_arena_state() == state

    replacement = store.create_arena_run(squad, schedule_seed=32)["run"]
    assert replacement["runId"] != first["runId"]
    assert replacement["currentNodeIndex"] == 1


def test_schema_v2_migrates_without_fabricating_arena_history(tmp_path: Path):
    database = tmp_path / "migrate-v2.sqlite3"
    original = ProgressionStore(database)
    profile = original.create_save_slot(1)["progression"]
    with sqlite3.connect(database) as connection:
        connection.execute("DROP TABLE arena_nodes")
        connection.execute("DROP TABLE arena_runs")
        connection.execute(
            "UPDATE metadata SET value = '2' WHERE key = 'schema_version'"
        )

    migrated = ProgressionStore(database)
    assert migrated.read_progression() == profile
    assert migrated.read_arena_state()["run"] is None
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT value FROM metadata WHERE key = 'schema_version'"
        ).fetchone()[0] == "3"


def test_arena_create_failure_rolls_back_run_and_nodes(tmp_path: Path):
    database = tmp_path / "rollback.sqlite3"
    store = ProgressionStore(database)
    store.create_save_slot(1)
    squad = _unlock_six(store)[:6]
    with sqlite3.connect(database) as connection:
        connection.execute(
            """CREATE TRIGGER fail_arena_node BEFORE INSERT ON arena_nodes
               BEGIN SELECT RAISE(ABORT, 'forced Arena node failure'); END"""
        )

    with pytest.raises(ProgressionStoreError):
        store.create_arena_run(squad, schedule_seed=99)
    assert store.read_arena_state()["run"] is None


def test_arena_commit_failure_rolls_back_node_and_progress(tmp_path: Path):
    database = tmp_path / "commit-rollback.sqlite3"
    store = ProgressionStore(database)
    store.create_save_slot(1)
    squad = _unlock_six(store)[:6]
    run = store.create_arena_run(squad, schedule_seed=100)["run"]
    with sqlite3.connect(database) as connection:
        connection.execute(
            """CREATE TRIGGER fail_arena_advance BEFORE UPDATE ON arena_runs
               BEGIN SELECT RAISE(ABORT, 'forced Arena advance failure'); END"""
        )

    with pytest.raises(ProgressionStoreError):
        store.commit_arena_victory(
            run_id=run["runId"],
            node_index=1,
            battle_id="arena.rollback.win",
            expected_profile_id=store.active_profile_id(),
        )
    unchanged = store.read_arena_state()["run"]
    assert unchanged["currentNodeIndex"] == 1
    assert unchanged["nodes"][0]["completed"] is False


def test_openapi_exposes_strict_arena_and_debug_boundaries():
    schema = app.openapi()
    paths = schema["paths"]

    assert "/api/v1/debug/battles" in paths
    assert "/api/v1/arena" in paths
    assert "/api/v1/arena/runs" in paths
    assert "/api/v1/arena/runs/{run_id}/nodes/{node_index}/battles" in paths
    create_run = schema["components"]["schemas"]["CreateArenaRunRequest"]
    assert set(create_run["properties"]) == {"squadDefinitionIds"}
    assert create_run["additionalProperties"] is False
    launch = schema["components"]["schemas"]["CreateArenaBattleRequest"]
    assert set(launch["properties"]) == {"playerTeam", "playerFormation"}
    assert not ({"enemyTeam", "seed", "completed", "profileId"} & set(
        launch["properties"]
    ))
    assert set(HERO_ROSTER) == ALL_HERO_IDS
