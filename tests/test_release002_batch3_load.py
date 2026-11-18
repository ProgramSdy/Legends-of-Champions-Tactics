"""Local representative 3v3 engine load evidence for RELEASE-002 Batch 3.

This is deliberately a local-process harness. It exercises real adapter
sessions and commands, but it is not evidence of e2-micro capacity or network
proxy performance.
"""

from __future__ import annotations

import resource
from concurrent.futures import ThreadPoolExecutor
from time import perf_counter, process_time
from pathlib import Path

from battle_api.adapter import BattleRegistry
from battle_api.progression import ProgressionStore, PublicBattleAccessError
from battle_api.public_identity import PublicIdentityService


TEAM = [
    "hero.warrior.weapon_master",
    "hero.paladin.retribution",
    "hero.priest.comprehensiveness",
]


def _metric_rss() -> int:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss


def test_local_twenty_three_vs_three_sessions_execute_one_command_each():
    registry = BattleRegistry()
    sessions = []
    launch_start = perf_counter()
    for index in range(20):
        session, envelope = registry.create(
            battle_id=f"batch3-load-{index}",
            seed=9000 + index,
            battle_size=3,
            player_team=TEAM,
            enemy_team=TEAM,
            enemy_control_mode="computer",
            player_formation="two-front-one-rear",
            enemy_formation="two-front-one-rear",
            fixed_computer_formation=True,
        )
        sessions.append((session, envelope))
    launch_elapsed = perf_counter() - launch_start

    command_start = perf_counter()
    results = []
    for session, envelope in sessions:
        snapshot = envelope["data"]["snapshot"]
        action = snapshot["legalActions"][0]
        results.append(
            registry.adapter.submit(
                session,
                {
                    "type": "useSkill",
                    "commandId": f"batch3-command-{session.battle_id}",
                    "expectedRevision": session.revision,
                    "actorId": action["actorId"],
                    "skillId": action["skillId"],
                    "targetIds": action["validTargetIds"][: action["minimumTargets"]],
                },
            )
        )
    command_elapsed = perf_counter() - command_start
    rss = _metric_rss()

    assert len(sessions) == 20
    assert len(registry._sessions) == 20
    assert all(result["accepted"] is True for result in results)
    assert all(session.battle_size == 3 for session, _ in sessions)
    print(
        "batch3 local load: sessions=20 launches_ms="
        f"{launch_elapsed * 1000:.2f} commands_ms={command_elapsed * 1000:.2f} "
        f"peak_rss_raw={rss} failures=0 lock_busy=0"
    )


def test_local_public_capacity_twenty_active_leases_rejects_21st_and_cleans_up(
    tmp_path: Path
):
    """Exercise SQLite's real Public lease cap with disposable player data."""
    database = tmp_path / "public-load.sqlite3"
    store = ProgressionStore(database, public_mode=True, allow_public_initialize=True)
    store._connection().close()
    identity = PublicIdentityService(store, key=b"l" * 32)
    sessions = []
    battle_sessions = []
    launch_latencies: list[float] = []
    command_cpu_start = process_time()
    wall_start = perf_counter()
    busy_failures = 0
    registry = BattleRegistry()

    for index in range(21):
        issued = identity.enroll(f"Load_Player_{index:02d}")
        session = identity.acknowledge(
            identity.validate_session(issued.session_token, require_confirmed=False)
        )
        store.create_save_slot(1, session.player_id, session.session_id, session.generation)
        if index == 20:
            try:
                store.reserve_public_battle(
                    battle_id="public-load-21",
                    player_id=session.player_id,
                    session_id=session.session_id,
                    session_generation=session.generation,
                    seed_hex="ab" * 32,
                    battle_type="stage",
                    context={"stageId": "paladins-altar", "battleIndex": 3, "battleSize": 3},
                    build_version="batch3-load-test",
                )
            except PublicBattleAccessError as error:
                assert error.code == "battleCapacityReached"
            else:
                raise AssertionError("the 21st Public lease unexpectedly succeeded")
            continue
        started = perf_counter()
        store.reserve_public_battle(
            battle_id=f"public-load-{index}",
            player_id=session.player_id,
            session_id=session.session_id,
            session_generation=session.generation,
            seed_hex=f"{index + 1:064x}",
            battle_type="stage",
            context={"stageId": "paladins-altar", "battleIndex": 3, "battleSize": 3},
            build_version="batch3-load-test",
        )
        launch_latencies.append(perf_counter() - started)
        sessions.append(session)
        battle_session, envelope = registry.create(
            battle_id=f"public-load-{index}",
            seed=10000 + index,
            battle_size=3,
            player_team=TEAM,
            enemy_team=TEAM,
            enemy_control_mode="computer",
            player_formation="two-front-one-rear",
            enemy_formation="two-front-one-rear",
            fixed_computer_formation=True,
        )
        store.activate_public_battle(
            battle_id=f"public-load-{index}",
            player_id=session.player_id,
            session_id=session.session_id,
            session_generation=session.generation,
        )
        battle_sessions.append((battle_session, envelope))

    assert len(sessions) == 20
    connection = store._connection()
    try:
        assert connection.execute("SELECT COUNT(*) FROM active_battle_leases").fetchone()[0] == 20
    finally:
        connection.close()

    def submit_one(item):
        battle_session, envelope = item
        action = envelope["data"]["snapshot"]["legalActions"][0]
        started = perf_counter()
        result = registry.adapter.submit(
            battle_session,
            {
                "type": "useSkill",
                "commandId": f"public-load-command-{battle_session.battle_id}",
                "expectedRevision": battle_session.revision,
                "actorId": action["actorId"],
                "skillId": action["skillId"],
                "targetIds": action["validTargetIds"][: action["minimumTargets"]],
            },
        )
        return result, perf_counter() - started

    with ThreadPoolExecutor(max_workers=20) as executor:
        command_results = list(executor.map(submit_one, battle_sessions))
    command_latencies = [duration for _, duration in command_results]
    assert all(result["accepted"] for result, _ in command_results)
    assert all(item[0].battle_size == 3 for item in battle_sessions)

    cleanup_start = perf_counter()
    for index, session in enumerate(sessions):
        result = store.resign_public_battle(
            battle_id=f"public-load-{index}",
            player_id=session.player_id,
            session_id=session.session_id,
            session_generation=session.generation,
        )
        assert result["lifecycleStatus"] in {"abandoned", "expired"}
    cleanup_elapsed = perf_counter() - cleanup_start
    connection = store._connection()
    try:
        assert connection.execute("SELECT COUNT(*) FROM active_battle_leases").fetchone()[0] == 0
    finally:
        connection.close()

    total_elapsed = perf_counter() - wall_start
    cpu_elapsed = process_time() - command_cpu_start
    p95 = sorted(launch_latencies)[max(0, int(len(launch_latencies) * 0.95) - 1)]
    command_p95 = sorted(command_latencies)[max(0, int(len(command_latencies) * 0.95) - 1)]
    print(
        "batch3 public lease load: leases=20 rejected_21=1 "
        f"launch_p95_ms={p95 * 1000:.2f} cleanup_ms={cleanup_elapsed * 1000:.2f} "
        f"command_p95_ms={command_p95 * 1000:.2f} "
        f"wall_ms={total_elapsed * 1000:.2f} cpu_ms={cpu_elapsed * 1000:.2f} "
        f"peak_rss_raw={_metric_rss()} sqlite_busy_failures={busy_failures} "
        "sqlite_contention=separate concurrent test"
    )


def test_local_sqlite_concurrent_reservations_serialize_without_busy_failure(
    tmp_path: Path,
):
    """Exercise distinct-player BEGIN IMMEDIATE contention on disposable data."""

    database = tmp_path / "public-contention.sqlite3"
    store = ProgressionStore(database, public_mode=True, allow_public_initialize=True)
    store._connection().close()
    identity = PublicIdentityService(store, key=b"c" * 32)
    sessions = []
    for index in range(20):
        issued = identity.enroll(f"Contention_{index:02d}")
        session = identity.acknowledge(
            identity.validate_session(issued.session_token, require_confirmed=False)
        )
        store.create_save_slot(
            1, session.player_id, session.session_id, session.generation
        )
        sessions.append(session)

    def reserve(item):
        index, session = item
        started = perf_counter()
        store.reserve_public_battle(
            battle_id=f"contention-{index}",
            player_id=session.player_id,
            session_id=session.session_id,
            session_generation=session.generation,
            seed_hex=f"{index + 1:064x}",
            battle_type="stage",
            context={
                "stageId": "paladins-altar",
                "battleIndex": 3,
                "battleSize": 3,
            },
            build_version="batch3-contention-test",
        )
        return perf_counter() - started

    with ThreadPoolExecutor(max_workers=20) as executor:
        durations = list(executor.map(reserve, enumerate(sessions)))

    connection = store._connection()
    try:
        assert connection.execute(
            "SELECT COUNT(*) FROM active_battle_leases"
        ).fetchone()[0] == 20
    finally:
        connection.close()
    assert len(durations) == 20
    print(
        "batch3 sqlite contention: reservations=20 busy_failures=0 "
        f"max_latency_ms={max(durations) * 1000:.2f}"
    )
