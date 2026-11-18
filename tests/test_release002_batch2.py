"""RELEASE-002 Batch 2 isolated persistence and lifecycle-boundary tests.

These tests deliberately exercise only the Public SQLite foundation that is
stable before the battle registry wiring is installed.  They use a disposable
database per test and never import or mutate the repository Development save.
The route/lifecycle tests are added in the same file once the Batch 2 service
boundary is present.
"""

from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
import importlib
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from battle_api.progression import (
    PUBLIC_BATTLE_SCHEMA_REVISION,
    ProgressionStore,
    ProgressionStoreError,
    SaveSlotAccessError,
)
from battle_api.progression import INITIAL_UNLOCKED_HERO_IDS
from battle_api.public_identity import PublicIdentityService


def _public_store(tmp_path) -> ProgressionStore:
    store = ProgressionStore(
        tmp_path / "public-batch2.sqlite3",
        public_mode=True,
        allow_public_initialize=True,
    )
    store._connection().close()
    return store


def _owned_public_player(store: ProgressionStore, name: str = "Player_A"):
    service = PublicIdentityService(store, key=b"k" * 32)
    issued = service.enroll(name)
    session = service.acknowledge(
        service.validate_session(issued.session_token, require_confirmed=False)
    )
    store.create_save_slot(1, session.player_id, session.session_id, session.generation)
    return session


def _prepare_public_stage_progress(
    store: ProgressionStore,
    session,
    stage_id: str,
    highest: int,
    *,
    learner_indices: range | list[int] | None = None,
):
    profile_id = store.active_profile_id(session.player_id)
    connection = store._connection()
    try:
        connection.execute(
            "UPDATE stage_progress SET highest_completed_battle = ?, completed = ? "
            "WHERE profile_id = ? AND stage_id = ?",
            (highest, int(highest == 9), profile_id, stage_id),
        )
        for index in learner_indices or []:
            connection.execute(
                """INSERT OR IGNORE INTO stage_mode_completions(
                    profile_id, stage_id, battle_index, mode, completion_battle_id,
                    completed_at
                ) VALUES (?, ?, ?, 'learner', ?, '2026-11-16T00:00:00Z')""",
                (profile_id, stage_id, index, f"seeded-{stage_id}-{index}"),
            )
        connection.commit()
    finally:
        connection.close()
    return profile_id


def _unlock_public_heroes(store: ProgressionStore, session, definition_ids: list[str]):
    profile_id = store.active_profile_id(session.player_id)
    connection = store._connection()
    try:
        connection.executemany(
            "INSERT OR IGNORE INTO unlocked_heroes(profile_id, definition_id) VALUES (?, ?)",
            [(profile_id, definition_id) for definition_id in definition_ids],
        )
        connection.commit()
    finally:
        connection.close()
    return profile_id


class _Unset:
    pass


_UNSET = _Unset()


def _public_http_fixture(tmp_path, monkeypatch):
    database = tmp_path / "public-http.sqlite3"
    fixture = ProgressionStore(
        database, public_mode=True, allow_public_initialize=True
    )
    fixture._connection().close()
    monkeypatch.setenv("LOCT_RELEASE_MODE", "public")
    monkeypatch.setenv("BATTLE_API_PUBLIC_DB", str(database))
    monkeypatch.setenv("BATTLE_API_PUBLIC_DB_INITIALIZE", "0")
    monkeypatch.setenv("BATTLE_API_PUBLIC_HMAC_KEY", "k" * 64)
    monkeypatch.setenv("BATTLE_API_RATE_LIMIT_HMAC_KEY", "r" * 64)
    monkeypatch.setenv("BATTLE_API_PUBLIC_ORIGIN", "https://public.test")
    monkeypatch.setenv("BATTLE_API_TRUSTED_PROXY_IPS", "127.0.0.1")
    monkeypatch.setenv("BATTLE_API_ENABLE_PUBLIC_BATTLES", "1")
    import battle_api.app as app_module

    app_module = importlib.reload(app_module)
    client = TestClient(app_module.app, base_url="https://public.test")
    created = client.post(
        "/api/v1/players",
        json={"playerName": "Http_Player"},
        headers={"Origin": "https://public.test"},
    )
    assert created.status_code == 200
    csrf = created.json()["csrfToken"]
    headers = {"Origin": "https://public.test", "X-CSRF-Token": csrf}
    acknowledged = client.post(
        "/api/v1/recovery-code/acknowledge", json={}, headers=headers
    )
    assert acknowledged.status_code == 200
    created_slot = client.post("/api/v1/save-slots/1/create", json={}, headers=headers)
    assert created_slot.status_code == 200
    return app_module, client, headers


def _launch_public_stage(client, headers, *, attempt_id="http-attempt", seed=_UNSET):
    payload = {
        "playerTeam": [
            "hero.priest.comprehensiveness",
            "hero.mage.comprehensiveness",
        ],
        "playerFormation": "front-rear",
        "mode": "learner",
        "attemptId": attempt_id,
    }
    if seed is not _UNSET:
        payload["seed"] = seed
    return client.post(
        "/api/v1/stages/paladins-altar/battles/1",
        json=payload,
        headers=headers,
    )


def _insert_player(connection: sqlite3.Connection, player_id: str) -> None:
    connection.execute(
        """INSERT INTO players(
               player_id, display_name, recovery_mac, recovery_key_version,
               recovery_issued_at, created_at
           ) VALUES (?, ?, ?, 1, '2026-11-16T00:00:00+00:00',
                     '2026-11-16T00:00:00+00:00')""",
            (player_id, player_id.replace("-", "_"), f"mac-{player_id}".encode()),
    )
    connection.execute(
        "INSERT INTO profiles(profile_id) VALUES (?)", (f"profile-{player_id}",)
    )


def _sqlite_row_snapshot(path) -> tuple[tuple[str, str, str], ...]:
    """Return a stable, read-only snapshot of every user-table row/schema."""
    connection = sqlite3.connect(path)
    try:
        tables = [
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        snapshot: list[tuple[str, str, str]] = []
        for table in tables:
            schema = connection.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?",
                (table,),
            ).fetchone()[0]
            snapshot.append((table, "__schema__", schema))
            for row in connection.execute(f'SELECT * FROM "{table}"'):
                snapshot.append((table, repr(tuple(row)), ""))
        return tuple(snapshot)
    finally:
        connection.close()


def test_public_batch2_schema_contains_lease_diagnostic_and_receipt_tables(tmp_path):
    store = _public_store(tmp_path)
    connection = store._connection()
    try:
        tables = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        assert {
            "active_battle_leases",
            "battle_diagnostics",
            "battle_settlements",
        } <= tables

        lease_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(active_battle_leases)")
        }
        assert {
            "player_id",
            "battle_id",
            "profile_id",
            "slot_id",
            "status",
            "reserved_at",
            "expires_at",
        } <= lease_columns
    finally:
        connection.close()


def test_public_batch2_lease_constraints_prevent_duplicate_player_or_battle(tmp_path):
    store = _public_store(tmp_path)
    connection = store._connection()
    try:
        _insert_player(connection, "player-a")
        _insert_player(connection, "player-b")
        connection.commit()
        row = (
            "player-a",
            "battle-a",
            "profile-player-a",
            1,
            "session-player-a",
            1,
            "active",
            "2026-11-16T00:00:00+00:00",
            "2026-11-16T00:30:00+00:00",
        )
        connection.execute(
            """INSERT INTO active_battle_leases(
                player_id, battle_id, profile_id, slot_id, launch_session_id,
                session_generation, status, reserved_at, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            row,
        )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """INSERT INTO active_battle_leases(
                    player_id, battle_id, profile_id, slot_id, launch_session_id,
                    session_generation, status, reserved_at, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    "player-a",
                    "battle-b",
                    "profile-player-a",
                    1,
                    "session-player-a",
                    1,
                    "active",
                    "2026-11-16T00:00:00+00:00",
                    "2026-11-16T00:30:00+00:00",
                ),
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """INSERT INTO active_battle_leases(
                    player_id, battle_id, profile_id, slot_id, launch_session_id,
                    session_generation, status, reserved_at, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    "player-b",
                    "battle-a",
                    "profile-player-a",
                    1,
                    "session-player-b",
                    1,
                    "active",
                    "2026-11-16T00:00:00+00:00",
                    "2026-11-16T00:30:00+00:00",
                ),
            )
    finally:
        connection.rollback()
        connection.close()


def test_public_batch2_diagnostic_seed_is_text_not_sqlite_integer(tmp_path):
    store = _public_store(tmp_path)
    connection = store._connection()
    try:
        _insert_player(connection, "player-a")
        connection.execute(
            """INSERT INTO battle_diagnostics(
                battle_id, player_id, slot_id, profile_id, launch_session_id,
                session_generation, seed_hex, build_version, started_at,
                battle_type, context_json, lifecycle_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "battle-a",
                "player-a",
                1,
                "profile-player-a",
                "session-player-a",
                1,
                "00" * 32,
                "test-build",
                "2026-11-16T00:00:00+00:00",
                "stage",
                "{}",
                "active",
            ),
        )
        connection.commit()
        value = connection.execute(
            "SELECT seed_hex FROM battle_diagnostics WHERE battle_id = ?",
            ("battle-a",),
        ).fetchone()["seed_hex"]
        assert value == "00" * 32
        assert isinstance(value, str)
    finally:
        connection.close()


def test_public_batch2_lease_insert_is_serializable_for_distinct_players(tmp_path):
    store = _public_store(tmp_path)
    setup = store._connection()
    try:
        for player_id in ("player-a", "player-b"):
            _insert_player(setup, player_id)
        setup.commit()
    finally:
        setup.close()

    def insert(player_id: str) -> str:
        connection = store._connection()
        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """INSERT INTO active_battle_leases(
                    player_id, battle_id, profile_id, slot_id, launch_session_id,
                    session_generation, status, reserved_at, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    player_id,
                    f"battle-{player_id}",
                    "profile-" + player_id,
                    1,
                    "session-" + player_id,
                    1,
                    "provisional",
                    "2026-11-16T00:00:00+00:00",
                    "2026-11-16T00:02:00+00:00",
                ),
            )
            connection.commit()
            return "ok"
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(insert, ("player-a", "player-b")))
    assert results == ["ok", "ok"]


def test_public_batch2_reservation_binds_owner_context_and_is_idempotency_free(tmp_path):
    store = _public_store(tmp_path)
    session = _owned_public_player(store)
    reserved = store.reserve_public_battle(
        battle_id="battle-owner",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
        seed_hex="ab" * 32,
        battle_type="stage",
        context={"stageId": "stage.warrior", "battleIndex": 1},
        build_version="test-build",
    )
    assert reserved["battleId"] == "battle-owner"
    assert reserved["profileId"]
    with pytest.raises(Exception) as error:
        store.reserve_public_battle(
            battle_id="battle-owner-2",
            player_id=session.player_id,
            session_id=session.session_id,
            session_generation=session.generation,
            seed_hex="cd" * 32,
            battle_type="stage",
            context={},
            build_version="test-build",
        )
    assert getattr(error.value, "code", None) == "activeBattleExists"


def test_public_batch2_activation_changes_provisional_to_active_and_refreshes_deadline(tmp_path):
    now = datetime(2026, 11, 16, tzinfo=UTC)
    store = ProgressionStore(
        tmp_path / "public-batch2-clock.sqlite3",
        public_mode=True,
        allow_public_initialize=True,
        now=lambda: now,
    )
    store._connection().close()
    session = _owned_public_player(store)
    store.reserve_public_battle(
        battle_id="battle-activate",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
        seed_hex="01" * 32,
        battle_type="arena",
        context={"runId": "run-a", "nodeIndex": 1},
        build_version="test-build",
    )
    active = store.activate_public_battle(
        battle_id="battle-activate",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
    )
    assert active["lifecycleStatus"] == "active"
    assert active["expiresAt"] > active["startedAt"]


def test_public_batch2_failed_construction_releases_reservation_and_keeps_diagnostic(tmp_path):
    store = _public_store(tmp_path)
    session = _owned_public_player(store)
    store.reserve_public_battle(
        battle_id="battle-abandon",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
        seed_hex="02" * 32,
        battle_type="stage",
        context={},
        build_version="test-build",
    )
    store.abandon_public_reservation(
        battle_id="battle-abandon", reason="constructionFailed"
    )
    connection = store._connection()
    try:
        assert connection.execute(
            "SELECT 1 FROM active_battle_leases WHERE battle_id = ?",
            ("battle-abandon",),
        ).fetchone() is None
        row = connection.execute(
            "SELECT lifecycle_status, terminal_reason FROM battle_diagnostics "
            "WHERE battle_id = ?", ("battle-abandon",)
        ).fetchone()
        assert (row["lifecycle_status"], row["terminal_reason"]) == (
            "abandoned", "constructionFailed"
        )
    finally:
        connection.close()


def test_public_batch2_expiry_is_exact_and_next_reservation_reclaims_capacity(tmp_path):
    clock = {"now": datetime(2026, 11, 16, tzinfo=UTC)}
    store = ProgressionStore(
        tmp_path / "public-batch2-expiry.sqlite3",
        public_mode=True,
        allow_public_initialize=True,
        now=lambda: clock["now"],
    )
    store._connection().close()
    first = _owned_public_player(store, "First_Player")
    store.reserve_public_battle(
        battle_id="battle-expiring",
        player_id=first.player_id,
        session_id=first.session_id,
        session_generation=first.generation,
        seed_hex="03" * 32,
        battle_type="stage",
        context={},
        build_version="test-build",
    )
    store.activate_public_battle(
        battle_id="battle-expiring",
        player_id=first.player_id,
        session_id=first.session_id,
        session_generation=first.generation,
    )
    clock["now"] += __import__("datetime").timedelta(minutes=30)
    second = _owned_public_player(store, "Second_Player")
    reclaimed = store.reserve_public_battle(
        battle_id="battle-after-expiry",
        player_id=second.player_id,
        session_id=second.session_id,
        session_generation=second.generation,
        seed_hex="04" * 32,
        battle_type="arena",
        context={},
        build_version="test-build",
    )
    assert reclaimed["expiredBattleIds"] == ["battle-expiring"]
    connection = store._connection()
    try:
        row = connection.execute(
            "SELECT lifecycle_status, terminal_reason FROM battle_diagnostics "
            "WHERE battle_id = ?", ("battle-expiring",)
        ).fetchone()
        assert (row["lifecycle_status"], row["terminal_reason"]) == (
            "expired", "inactivity"
        )
        assert connection.execute(
            "SELECT 1 FROM active_battle_leases WHERE battle_id = ?",
            ("battle-expiring",),
        ).fetchone() is None
    finally:
        connection.close()


def test_public_batch2_activation_rejects_revoked_session_and_preserves_reservation(tmp_path):
    store = _public_store(tmp_path)
    service = PublicIdentityService(store, key=b"k" * 32)
    issued = service.enroll("Revoked_Player")
    session = service.acknowledge(
        service.validate_session(issued.session_token, require_confirmed=False)
    )
    store.create_save_slot(1, session.player_id, session.session_id, session.generation)
    store.reserve_public_battle(
        battle_id="battle-revoked",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
        seed_hex="05" * 32,
        battle_type="stage",
        context={},
        build_version="test-build",
    )
    replacement = service.recover(issued.recovery_code or "", "203.0.113.99")
    with pytest.raises(Exception) as error:
        store.activate_public_battle(
            battle_id="battle-revoked",
            player_id=session.player_id,
            session_id=session.session_id,
            session_generation=session.generation,
        )
    assert getattr(error.value, "code", None) in {"sessionRevoked", "sessionExpired"}
    del replacement
    connection = store._connection()
    try:
        assert connection.execute(
            "SELECT status FROM active_battle_leases WHERE battle_id = ?",
            ("battle-revoked",),
        ).fetchone()["status"] == "provisional"
    finally:
        connection.close()


def test_public_batch2_authorization_rejects_foreign_battle_and_profile_switch(tmp_path):
    store = _public_store(tmp_path)
    first = _owned_public_player(store, "First_Player")
    second = _owned_public_player(store, "Second_Player")
    store.reserve_public_battle(
        battle_id="battle-private",
        player_id=first.player_id,
        session_id=first.session_id,
        session_generation=first.generation,
        seed_hex="06" * 32,
        battle_type="stage",
        context={},
        build_version="test-build",
    )
    with pytest.raises(Exception) as error:
        store.authorize_public_battle(
            battle_id="battle-private",
            player_id=second.player_id,
            session_id=second.session_id,
            session_generation=second.generation,
        )
    assert getattr(error.value, "code", None) == "battleNotFound"

    # Switching the player's active slot invalidates the immutable launch
    # profile context rather than redirecting the battle to a new profile.
    store.create_save_slot(2, first.player_id, first.session_id, first.generation)
    with pytest.raises(Exception) as error:
        store.authorize_public_battle(
            battle_id="battle-private",
            player_id=first.player_id,
            session_id=first.session_id,
            session_generation=first.generation,
        )
    assert getattr(error.value, "code", None) == "battleLaunchContextChanged"


def test_public_batch2_restart_reconciliation_abandons_ram_dependent_leases(tmp_path):
    store = _public_store(tmp_path)
    session = _owned_public_player(store)
    store.reserve_public_battle(
        battle_id="battle-restart",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
        seed_hex="07" * 32,
        battle_type="arena",
        context={},
        build_version="test-build",
    )
    store.activate_public_battle(
        battle_id="battle-restart",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
    )
    assert store.reconcile_public_battles_after_restart() == ["battle-restart"]
    connection = store._connection()
    try:
        row = connection.execute(
            "SELECT lifecycle_status, terminal_reason FROM battle_diagnostics "
            "WHERE battle_id = ?", ("battle-restart",)
        ).fetchone()
        assert (row["lifecycle_status"], row["terminal_reason"]) == (
            "expired", "serverRestart"
        )
        assert connection.execute(
            "SELECT 1 FROM active_battle_leases WHERE battle_id = ?",
            ("battle-restart",),
        ).fetchone() is None
    finally:
        connection.close()


def test_public_batch2_global_capacity_rejects_the_21st_active_reservation(tmp_path):
    store = _public_store(tmp_path)
    sessions = [
        _owned_public_player(store, f"Player_{index:02d}")
        for index in range(1, 22)
    ]
    for index, session in enumerate(sessions[:20], start=1):
        store.reserve_public_battle(
            battle_id=f"battle-cap-{index}",
            player_id=session.player_id,
            session_id=session.session_id,
            session_generation=session.generation,
            seed_hex=f"{index:064x}",
            battle_type="stage",
            context={},
            build_version="test-build",
            capacity=20,
        )
    with pytest.raises(Exception) as error:
        store.reserve_public_battle(
            battle_id="battle-cap-21",
            player_id=sessions[20].player_id,
            session_id=sessions[20].session_id,
            session_generation=sessions[20].generation,
            seed_hex="15" * 32,
            battle_type="stage",
            context={},
            build_version="test-build",
            capacity=20,
        )
    assert getattr(error.value, "code", None) == "battleCapacityReached"


@pytest.mark.parametrize("seed_hex", ["", "00", "GG" * 32, "01" * 31])
def test_public_batch2_reservation_rejects_noncanonical_effective_seed(tmp_path, seed_hex):
    store = _public_store(tmp_path)
    session = _owned_public_player(store)
    with pytest.raises(ValueError, match="seed_hex"):
        store.reserve_public_battle(
            battle_id="battle-invalid-seed",
            player_id=session.player_id,
            session_id=session.session_id,
            session_generation=session.generation,
            seed_hex=seed_hex,
            battle_type="stage",
            context={},
            build_version="test-build",
        )


def test_public_batch2_launch_helper_serializes_same_player_and_cleans_factory_failure(
    tmp_path, monkeypatch
):
    import battle_api.app as app_module

    store = _public_store(tmp_path)
    session = _owned_public_player(store)
    calls = {"count": 0}

    def factory(seed: int, battle_id: str, profile_id: str):
        del seed, profile_id
        calls["count"] += 1
        return SimpleNamespace(battle_id=battle_id), {"battleId": battle_id}

    first_session, first_envelope = app_module._public_launch(
        session=session,
        store=store,
        attempt_id="attempt-one",
        fingerprint=("stage", "stage.warrior", 1),
        battle_type="stage",
        context={"stageId": "stage.warrior", "battleIndex": 1},
        factory=factory,
    )
    assert first_session is not None
    assert first_envelope["lifecycleStatus"] == "active"
    replay_session, replay_envelope = app_module._public_launch(
        session=session,
        store=store,
        attempt_id="attempt-one",
        fingerprint=("stage", "stage.warrior", 1),
        battle_type="stage",
        context={"stageId": "stage.warrior", "battleIndex": 1},
        factory=factory,
    )
    assert replay_session.battle_id == first_session.battle_id
    assert replay_envelope["battleId"] == first_envelope["battleId"]
    assert calls["count"] == 1
    failing_session = _owned_public_player(store, "Failure_Player")

    def failing_factory(seed: int, battle_id: str, profile_id: str):
        del seed, battle_id, profile_id
        raise RuntimeError("injected RAM construction failure")

    with pytest.raises(RuntimeError, match="construction failure"):
        app_module._public_launch(
            session=failing_session,
            store=store,
            attempt_id=None,
            fingerprint=("stage", "stage.warrior", 2),
            battle_type="stage",
            context={"stageId": "stage.warrior", "battleIndex": 2},
            factory=failing_factory,
        )
    connection = store._connection()
    try:
        row = connection.execute(
            "SELECT lifecycle_status, terminal_reason FROM battle_diagnostics "
            "WHERE lifecycle_status = 'abandoned' ORDER BY started_at DESC LIMIT 1"
        ).fetchone()
        assert row is not None
        assert row["terminal_reason"] == "constructionOrActivationFailed"
    finally:
        connection.close()


def test_public_batch2_launch_helper_does_not_expose_seed_to_client_envelope(tmp_path):
    import battle_api.app as app_module

    store = _public_store(tmp_path)
    session = _owned_public_player(store)

    def factory(seed: int, battle_id: str, profile_id: str):
        del profile_id
        return SimpleNamespace(battle_id=battle_id), {"battleId": battle_id, "seed": seed}

    _, envelope = app_module._public_launch(
        session=session,
        store=store,
        attempt_id=None,
        fingerprint=("arena", "run-a", 1),
        battle_type="arena",
        context={"runId": "run-a", "nodeIndex": 1},
        factory=factory,
    )
    # The helper must not add or echo the server-owned seed.  A deliberately
    # malformed factory envelope is sanitized at this boundary.
    assert "seedHex" not in envelope


def test_public_batch2_concurrent_same_player_launches_allow_only_one(tmp_path):
    import battle_api.app as app_module

    store = _public_store(tmp_path)
    session = _owned_public_player(store)

    def factory(seed: int, battle_id: str, profile_id: str):
        del seed, profile_id
        return SimpleNamespace(battle_id=battle_id), {"battleId": battle_id}

    def launch(index: int):
        try:
            result = app_module._public_launch(
                session=session,
                store=store,
                attempt_id=None,
                fingerprint=("stage", "stage.warrior", index),
                battle_type="stage",
                context={"stageId": "stage.warrior", "battleIndex": index},
                factory=factory,
            )
            return "ok", result[1]["battleId"]
        except Exception as error:  # boundary assertion below inspects typed code
            return "error", getattr(error, "code", None)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(launch, (1, 2)))
    assert [result[0] for result in results].count("ok") == 1
    assert [result[1] for result in results].count("activeBattleExists") == 1


def test_public_batch2_activation_failure_releases_lease_and_ram_binding(tmp_path, monkeypatch):
    import battle_api.app as app_module

    store = _public_store(tmp_path)
    session = _owned_public_player(store)
    original_activate = store.activate_public_battle

    def fail_activation(**kwargs):
        del kwargs
        raise RuntimeError("injected activation failure")

    monkeypatch.setattr(store, "activate_public_battle", fail_activation)

    def factory(seed: int, battle_id: str, profile_id: str):
        del seed, profile_id
        return SimpleNamespace(battle_id=battle_id), {"battleId": battle_id}

    with pytest.raises(RuntimeError, match="activation failure"):
        app_module._public_launch(
            session=session,
            store=store,
            attempt_id=None,
            fingerprint=("arena", "run-a", 1),
            battle_type="arena",
            context={"runId": "run-a", "nodeIndex": 1},
            factory=factory,
        )
    monkeypatch.setattr(store, "activate_public_battle", original_activate)
    connection = store._connection()
    try:
        assert connection.execute(
            "SELECT COUNT(*) FROM active_battle_leases"
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT terminal_reason FROM battle_diagnostics "
            "WHERE lifecycle_status = 'abandoned'"
        ).fetchone()["terminal_reason"] == "constructionOrActivationFailed"
    finally:
        connection.close()


def test_public_batch2_attempt_replay_after_abandonment_is_rejected_and_not_recreated(
    tmp_path,
):
    import battle_api.app as app_module

    store = _public_store(tmp_path)
    session = _owned_public_player(store)

    def factory(seed: int, battle_id: str, profile_id: str):
        del seed, profile_id
        return SimpleNamespace(battle_id=battle_id), {"battleId": battle_id}

    first_session, first_envelope = app_module._public_launch(
        session=session,
        store=store,
        attempt_id="attempt-abandoned",
        fingerprint=("stage", "stage.warrior", 1),
        battle_type="stage",
        context={"stageId": "stage.warrior", "battleIndex": 1},
        factory=factory,
    )
    store.abandon_public_reservation(
        battle_id=first_session.battle_id, reason="resign"
    )
    with pytest.raises(Exception) as error:
        app_module._public_launch(
            session=session,
            store=store,
            attempt_id="attempt-abandoned",
            fingerprint=("stage", "stage.warrior", 1),
            battle_type="stage",
            context={"stageId": "stage.warrior", "battleIndex": 1},
            factory=factory,
        )
    assert getattr(error.value, "code", None) == "battleNoLongerActive"
    assert first_envelope["battleId"] == first_session.battle_id


def test_public_batch2_completed_action_resets_deadline_before_global_cleanup(
    tmp_path,
):
    clock = {"now": datetime(2026, 11, 16, tzinfo=UTC)}
    store = ProgressionStore(
        tmp_path / "public-batch2-action-clock.sqlite3",
        public_mode=True,
        allow_public_initialize=True,
        now=lambda: clock["now"],
    )
    store._connection().close()
    first = _owned_public_player(store, "Action_Player")
    store.reserve_public_battle(
        battle_id="battle-action",
        player_id=first.player_id,
        session_id=first.session_id,
        session_generation=first.generation,
        seed_hex="08" * 32,
        battle_type="stage",
        context={},
        build_version="test-build",
    )
    store.activate_public_battle(
        battle_id="battle-action",
        player_id=first.player_id,
        session_id=first.session_id,
        session_generation=first.generation,
    )
    clock["now"] += __import__("datetime").timedelta(minutes=29, seconds=59)
    before = store.authorize_public_battle(
        battle_id="battle-action",
        player_id=first.player_id,
        session_id=first.session_id,
        session_generation=first.generation,
    )
    accepted = store.begin_public_battle_action(
        battle_id="battle-action",
        player_id=first.player_id,
        session_id=first.session_id,
        session_generation=first.generation,
    )
    clock["now"] += __import__("datetime").timedelta(seconds=1)
    after = store.touch_public_battle_after_action(
        battle_id="battle-action",
        player_id=first.player_id,
        session_id=first.session_id,
        session_generation=first.generation,
    )
    assert before["lifecycleStatus"] == "active"
    assert accepted["previousExpiresAt"] == before["expiresAt"]
    assert after["lifecycleStatus"] == "active"
    assert after["lastAcceptedActionAt"] is not None
    assert after["expiresAt"] > before["expiresAt"]


def test_public_batch2_resolving_action_survives_other_player_cleanup_race(tmp_path):
    clock = {"now": datetime(2026, 11, 16, tzinfo=UTC)}
    store = ProgressionStore(
        tmp_path / "public-batch2-race-clock.sqlite3",
        public_mode=True,
        allow_public_initialize=True,
        now=lambda: clock["now"],
    )
    store._connection().close()
    first = _owned_public_player(store, "Race_First")
    second = _owned_public_player(store, "Race_Second")
    store.reserve_public_battle(
        battle_id="battle-race-first",
        player_id=first.player_id,
        session_id=first.session_id,
        session_generation=first.generation,
        seed_hex="09" * 32,
        battle_type="stage",
        context={},
        build_version="test-build",
    )
    store.activate_public_battle(
        battle_id="battle-race-first",
        player_id=first.player_id,
        session_id=first.session_id,
        session_generation=first.generation,
    )
    clock["now"] += __import__("datetime").timedelta(minutes=29, seconds=59)
    store.begin_public_battle_action(
        battle_id="battle-race-first",
        player_id=first.player_id,
        session_id=first.session_id,
        session_generation=first.generation,
    )
    clock["now"] += __import__("datetime").timedelta(seconds=1)
    reclaimed = store.reserve_public_battle(
        battle_id="battle-race-second",
        player_id=second.player_id,
        session_id=second.session_id,
        session_generation=second.generation,
        seed_hex="0a" * 32,
        battle_type="arena",
        context={},
        build_version="test-build",
    )
    assert reclaimed["expiredBattleIds"] == []
    completed = store.touch_public_battle_after_action(
        battle_id="battle-race-first",
        player_id=first.player_id,
        session_id=first.session_id,
        session_generation=first.generation,
    )
    assert completed["lifecycleStatus"] == "active"
    assert completed["lastAcceptedActionAt"] is not None


def test_public_batch2_resign_is_idempotent_and_releases_capacity(tmp_path):
    store = _public_store(tmp_path)
    session = _owned_public_player(store)
    store.reserve_public_battle(
        battle_id="battle-resign",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
        seed_hex="0b" * 32,
        battle_type="stage",
        context={},
        build_version="test-build",
    )
    store.activate_public_battle(
        battle_id="battle-resign",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
    )
    first = store.resign_public_battle(
        battle_id="battle-resign",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
    )
    second = store.resign_public_battle(
        battle_id="battle-resign",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
    )
    assert first == second
    assert first["terminalReason"] == "resigned"
    connection = store._connection()
    try:
        assert connection.execute(
            "SELECT 1 FROM active_battle_leases WHERE battle_id = ?",
            ("battle-resign",),
        ).fetchone() is None
        assert connection.execute(
            "SELECT COUNT(*) FROM battle_settlements WHERE battle_id = ?",
            ("battle-resign",),
        ).fetchone()[0] == 1
    finally:
        connection.close()


def test_public_batch2_resign_cannot_erase_terminal_pending_result(tmp_path):
    store = _public_store(tmp_path)
    session = _owned_public_player(store)
    store.reserve_public_battle(
        battle_id="battle-pending",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
        seed_hex="0c" * 32,
        battle_type="stage",
        context={},
        build_version="test-build",
    )
    store.activate_public_battle(
        battle_id="battle-pending",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
    )
    store.mark_public_battle_terminal_pending(
        battle_id="battle-pending",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
        outcome={"kind": "victory", "winningSideId": "friendly"},
    )
    with pytest.raises(Exception) as error:
        store.resign_public_battle(
            battle_id="battle-pending",
            player_id=session.player_id,
            session_id=session.session_id,
            session_generation=session.generation,
        )
    assert getattr(error.value, "code", None) == "battleSettlementPending"


@pytest.mark.parametrize("seconds_after_deadline", [0, 1])
def test_public_batch2_resign_at_or_after_deadline_returns_expiry_receipt(
    tmp_path, seconds_after_deadline
):
    clock = {"now": datetime(2026, 11, 16, tzinfo=UTC)}
    store = ProgressionStore(
        tmp_path / f"public-batch2-resign-expiry-{seconds_after_deadline}.sqlite3",
        public_mode=True,
        allow_public_initialize=True,
        now=lambda: clock["now"],
    )
    store._connection().close()
    session = _owned_public_player(store)
    store.reserve_public_battle(
        battle_id="battle-resign-expiry",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
        seed_hex="0d" * 32,
        battle_type="stage",
        context={},
        build_version="test-build",
    )
    store.activate_public_battle(
        battle_id="battle-resign-expiry",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
    )
    clock["now"] += __import__("datetime").timedelta(
        minutes=30, seconds=seconds_after_deadline
    )
    result = store.resign_public_battle(
        battle_id="battle-resign-expiry",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
    )
    assert result["terminalReason"] == "inactivity"
    assert result["lifecycleStatus"] == "expired"


def test_public_batch2_terminal_pending_transition_accepts_resolving_action(tmp_path):
    store = _public_store(tmp_path)
    session = _owned_public_player(store)
    store.reserve_public_battle(
        battle_id="battle-resolving-pending",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
        seed_hex="0e" * 32,
        battle_type="stage",
        context={"stageId": "stage.warrior", "battleIndex": 1},
        build_version="test-build",
    )
    store.activate_public_battle(
        battle_id="battle-resolving-pending",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
    )
    store.begin_public_battle_action(
        battle_id="battle-resolving-pending",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
    )
    pending = store.mark_public_battle_terminal_pending(
        battle_id="battle-resolving-pending",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
        outcome={"kind": "victory", "winningSideId": "friendly"},
    )
    assert pending["lifecycleStatus"] == "terminalPending"


def test_public_batch2_resign_after_settled_result_returns_original_receipt(tmp_path):
    store = _public_store(tmp_path)
    session = _owned_public_player(store)
    store.reserve_public_battle(
        battle_id="battle-settled-receipt",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
        seed_hex="0f" * 32,
        battle_type="stage",
        context={"stageId": "stage.warrior", "battleIndex": 1},
        build_version="test-build",
    )
    store.activate_public_battle(
        battle_id="battle-settled-receipt",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
    )
    store.begin_public_battle_action(
        battle_id="battle-settled-receipt",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
    )
    original = store.settle_public_battle(
        battle_id="battle-settled-receipt",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
        outcome={"kind": "defeat", "winningSideId": "enemy"},
    )
    repeated = store.resign_public_battle(
        battle_id="battle-settled-receipt",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
    )
    assert repeated == original


def test_public_batch2_settlement_defeat_draw_has_no_reward_and_duplicate_is_original(
    tmp_path,
):
    store = _public_store(tmp_path)
    session = _owned_public_player(store)
    store.reserve_public_battle(
        battle_id="battle-defeat-receipt",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
        seed_hex="10" * 32,
        battle_type="stage",
        context={"stageId": "stage.warrior", "battleIndex": 1},
        build_version="test-build",
    )
    store.activate_public_battle(
        battle_id="battle-defeat-receipt",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
    )
    store.begin_public_battle_action(
        battle_id="battle-defeat-receipt",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
    )
    original = store.settle_public_battle(
        battle_id="battle-defeat-receipt",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
        outcome={"kind": "draw"},
    )
    duplicate = store.settle_public_battle(
        battle_id="battle-defeat-receipt",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
        outcome={"kind": "victory", "winningSideId": "friendly"},
    )
    assert duplicate == original
    assert original["alreadyCommitted"] is False
    assert original["outcome"] == {"kind": "draw"}


def test_public_batch2_settlement_fault_rolls_back_receipt_and_lease(tmp_path, monkeypatch):
    store = _public_store(tmp_path)
    session = _owned_public_player(store)
    store.reserve_public_battle(
        battle_id="battle-settle-fault",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
        seed_hex="11" * 32,
        battle_type="stage",
        context={"stageId": "stage.warrior", "battleIndex": 1},
        build_version="test-build",
    )
    store.activate_public_battle(
        battle_id="battle-settle-fault",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
    )
    store.begin_public_battle_action(
        battle_id="battle-settle-fault",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
    )

    def fail_commit(connection, battle_id):
        del connection, battle_id
        raise RuntimeError("injected settlement fault")

    monkeypatch.setattr(store, "_before_public_settlement_commit", fail_commit)
    with pytest.raises(RuntimeError, match="settlement fault"):
        store.settle_public_battle(
            battle_id="battle-settle-fault",
            player_id=session.player_id,
            session_id=session.session_id,
            session_generation=session.generation,
            outcome={"kind": "draw"},
        )
    connection = store._connection()
    try:
        assert connection.execute(
            "SELECT lifecycle_status FROM battle_diagnostics WHERE battle_id = ?",
            ("battle-settle-fault",),
        ).fetchone()["lifecycle_status"] == "resolving"
        assert connection.execute(
            "SELECT 1 FROM active_battle_leases WHERE battle_id = ?",
            ("battle-settle-fault",),
        ).fetchone() is not None
        assert connection.execute(
            "SELECT 1 FROM battle_settlements WHERE battle_id = ?",
            ("battle-settle-fault",),
        ).fetchone() is None
    finally:
        connection.close()


def test_public_batch2_settlement_requires_live_lease(tmp_path):
    store = _public_store(tmp_path)
    session = _owned_public_player(store)
    store.reserve_public_battle(
        battle_id="battle-no-lease",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
        seed_hex="12" * 32,
        battle_type="stage",
        context={"stageId": "stage.warrior", "battleIndex": 1},
        build_version="test-build",
    )
    store.activate_public_battle(
        battle_id="battle-no-lease",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
    )
    store.begin_public_battle_action(
        battle_id="battle-no-lease",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
    )
    connection = store._connection()
    try:
        connection.execute(
            "DELETE FROM active_battle_leases WHERE battle_id = ?",
            ("battle-no-lease",),
        )
        connection.commit()
    finally:
        connection.close()
    with pytest.raises(Exception) as error:
        store.settle_public_battle(
            battle_id="battle-no-lease",
            player_id=session.player_id,
            session_id=session.session_id,
            session_generation=session.generation,
            outcome={"kind": "draw"},
        )
    assert getattr(error.value, "code", None) == "battleNoLongerActive"


def test_public_batch2_committed_receipt_survives_recovery_for_idempotent_retry(tmp_path):
    store = _public_store(tmp_path)
    service = PublicIdentityService(store, key=b"k" * 32)
    issued = service.enroll("Recovery_Battle")
    session = service.acknowledge(
        service.validate_session(issued.session_token, require_confirmed=False)
    )
    store.create_save_slot(1, session.player_id, session.session_id, session.generation)
    store.reserve_public_battle(
        battle_id="battle-recovery-receipt",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
        seed_hex="13" * 32,
        battle_type="stage",
        context={"stageId": "stage.warrior", "battleIndex": 1},
        build_version="test-build",
    )
    store.activate_public_battle(
        battle_id="battle-recovery-receipt",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
    )
    store.begin_public_battle_action(
        battle_id="battle-recovery-receipt",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
    )
    original = store.settle_public_battle(
        battle_id="battle-recovery-receipt",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
        outcome={"kind": "draw"},
    )
    recovered = service.recover(issued.recovery_code or "", "203.0.113.77")
    retry = store.settle_public_battle(
        battle_id="battle-recovery-receipt",
        player_id=recovered.player_id,
        session_id=recovered.session_id,
        session_generation=recovered.generation,
        outcome={"kind": "victory", "winningSideId": "friendly"},
    )
    assert retry == original


def test_public_batch2_http_exposes_owned_stage_launch_lifecycle_and_hides_generic(
    tmp_path, monkeypatch
):
    app_module, client, headers = _public_http_fixture(tmp_path, monkeypatch)
    paths = app_module.app.openapi()["paths"]
    assert "/api/v1/battles" not in paths
    assert "/api/v1/stages/{stage_id}/battles/{battle_index}" in paths
    generic = client.post(
        "/api/v1/battles",
        json={"battleSize": 1, "playerTeam": ["hero.warrior.weapon_master"]},
        headers=headers,
    )
    assert generic.status_code == 404
    launched = _launch_public_stage(client, headers)
    assert launched.status_code == 200, launched.text
    body = launched.json()
    assert body["lifecycleStatus"] == "active"
    assert body["serverNow"]
    assert body["expiresAt"]
    assert "seedHex" not in body
    del app_module


@pytest.mark.parametrize("seed", [7, None])
def test_public_batch2_http_rejects_numeric_or_null_seed(tmp_path, monkeypatch, seed):
    _app, client, headers = _public_http_fixture(tmp_path, monkeypatch)
    response = _launch_public_stage(
        client, headers, attempt_id=f"seed-{seed}", seed=seed
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "publicSeedForbidden"


def test_public_batch2_http_foreign_battle_is_hidden_and_unsafe_calls_need_csrf(
    tmp_path, monkeypatch
):
    app_module, client, headers = _public_http_fixture(tmp_path, monkeypatch)
    launched = _launch_public_stage(client, headers, attempt_id="owned-battle")
    assert launched.status_code == 200
    battle_id = launched.json()["battleId"]

    second = TestClient(app_module.app, base_url="https://public.test")
    created = second.post(
        "/api/v1/players",
        json={"playerName": "Foreign_Player"},
        headers={"Origin": "https://public.test"},
    )
    second_csrf = created.json()["csrfToken"]
    second_headers = {"Origin": "https://public.test", "X-CSRF-Token": second_csrf}
    assert second.post("/api/v1/recovery-code/acknowledge", json={}, headers=second_headers).status_code == 200
    assert second.post("/api/v1/save-slots/1/create", json={}, headers=second_headers).status_code == 200

    foreign_get = second.get(f"/api/v1/battles/{battle_id}")
    assert foreign_get.status_code == 404
    foreign_resign = second.post(
        f"/api/v1/battles/{battle_id}/resign", json={}, headers=second_headers
    )
    assert foreign_resign.status_code == 404
    snapshot = launched.json()["data"]["snapshot"]
    action = snapshot["legalActions"][0]
    foreign_command = second.post(
        f"/api/v1/battles/{battle_id}/commands",
        json={
            "type": "useSkill",
            "commandId": "foreign-command",
            "expectedRevision": launched.json()["revision"],
            "actorId": snapshot["activeCombatantId"],
            "skillId": action["skillId"],
            "targetIds": action["validTargetIds"][: action["minimumTargets"]],
        },
        headers=second_headers,
    )
    assert foreign_command.status_code == 404
    foreign_preview = second.post(
        f"/api/v1/battles/{battle_id}/preview",
        json={
            "expectedRevision": launched.json()["revision"],
            "actorId": snapshot["activeCombatantId"],
            "skillId": action["skillId"],
            "targetIds": action["validTargetIds"][: action["minimumTargets"]],
        },
        headers=second_headers,
    )
    assert foreign_preview.status_code == 404
    foreign_completion = second.post(
        f"/api/v1/battles/{battle_id}/completion", json={}, headers=second_headers
    )
    assert foreign_completion.status_code == 404
    missing_csrf = client.post(f"/api/v1/battles/{battle_id}/resign", json={})
    assert missing_csrf.status_code == 403
    bad_origin = client.post(
        f"/api/v1/battles/{battle_id}/resign",
        json={},
        headers={"Origin": "https://evil.test", "X-CSRF-Token": headers["X-CSRF-Token"]},
    )
    assert bad_origin.status_code == 403


def test_public_batch2_http_lost_terminal_response_replays_durable_receipt_after_ram_eviction(
    tmp_path, monkeypatch
):
    app_module, client, headers = _public_http_fixture(tmp_path, monkeypatch)
    launched = _launch_public_stage(client, headers, attempt_id="lost-terminal")
    assert launched.status_code == 200
    battle_id = launched.json()["battleId"]
    session = app_module.registry.get(battle_id)
    assert session is not None
    store = app_module.progression_store
    assert store is not None
    auth = app_module.identity_service.validate_session(
        client.cookies.get(app_module.SESSION_COOKIE), require_confirmed=True
    )
    store.begin_public_battle_action(
        battle_id=battle_id,
        player_id=auth.player_id,
        session_id=auth.session_id,
        session_generation=auth.generation,
    )
    receipt = store.settle_public_battle(
        battle_id=battle_id,
        player_id=auth.player_id,
        session_id=auth.session_id,
        session_generation=auth.generation,
        outcome={"kind": "victory", "winningSideId": "friendly"},
    )
    app_module._remove_process_battle(battle_id)
    replay = client.post(
        f"/api/v1/battles/{battle_id}/commands",
        json={
            "type": "useSkill",
            "commandId": "lost-response-retry",
            "expectedRevision": 0,
            "actorId": "missing-after-eviction",
            "skillId": "skill.warrior.slash",
            "targetIds": [],
        },
        headers=headers,
    )
    assert replay.status_code == 200, replay.text
    assert replay.json()["settlement"] == receipt
    completion = client.post(
        f"/api/v1/battles/{battle_id}/completion", json={}, headers=headers
    )
    assert completion.status_code == 200
    assert completion.json()["battleId"] == battle_id


def test_public_batch2_http_preview_includes_authoritative_lifecycle_timing(
    tmp_path, monkeypatch
):
    _app, client, headers = _public_http_fixture(tmp_path, monkeypatch)
    launched = _launch_public_stage(client, headers, attempt_id="preview-timing")
    assert launched.status_code == 200
    body = launched.json()
    snapshot = body["data"]["snapshot"]
    action = snapshot["legalActions"][0]
    preview = client.post(
        f"/api/v1/battles/{body['battleId']}/preview",
        json={
            "expectedRevision": body["revision"],
            "actorId": snapshot["activeCombatantId"],
            "skillId": action["skillId"],
            "targetIds": action["validTargetIds"][: action["minimumTargets"]],
        },
        headers=headers,
    )
    assert preview.status_code == 200, preview.text
    preview_body = preview.json()
    assert preview_body["serverNow"]
    assert preview_body["expiresAt"]
    assert preview_body["lifecycleStatus"] == "active"


def test_public_batch2_http_resign_is_idempotent_and_releases_battle(tmp_path, monkeypatch):
    _app, client, headers = _public_http_fixture(tmp_path, monkeypatch)
    launched = _launch_public_stage(client, headers, attempt_id="http-resign")
    battle_id = launched.json()["battleId"]
    first = client.post(
        f"/api/v1/battles/{battle_id}/resign", json={}, headers=headers
    )
    second = client.post(
        f"/api/v1/battles/{battle_id}/resign", json={}, headers=headers
    )
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json() == first.json()
    assert first.json()["terminalReason"] == "resigned"


def test_public_batch2_http_terminal_command_settles_before_response(
    tmp_path, monkeypatch
):
    app_module, client, headers = _public_http_fixture(tmp_path, monkeypatch)
    launched = _launch_public_stage(client, headers, attempt_id="terminal-command")
    assert launched.status_code == 200
    body = launched.json()
    battle_id = body["battleId"]
    snapshot = body["data"]["snapshot"]
    action = snapshot["legalActions"][0]
    original_submit = app_module.registry.adapter.submit

    def terminal_submit(battle, command, *, on_accepted=None):
        if on_accepted is not None:
            on_accepted()
        battle.revision += 1
        return {
            "accepted": True,
            "commandId": command["commandId"],
            "revision": battle.revision,
            "snapshot": {
                "phase": "ended",
                "outcome": {"kind": "victory", "winningSideId": "friendly"},
            },
        }

    monkeypatch.setattr(app_module.registry.adapter, "submit", terminal_submit)
    response = client.post(
        f"/api/v1/battles/{battle_id}/commands",
        json={
            "type": "useSkill",
            "commandId": "terminal-command",
            "expectedRevision": body["revision"],
            "actorId": snapshot["activeCombatantId"],
            "skillId": action["skillId"],
            "targetIds": action["validTargetIds"][: action["minimumTargets"]],
        },
        headers=headers,
    )
    monkeypatch.setattr(app_module.registry.adapter, "submit", original_submit)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["lifecycleStatus"] == "settled"
    assert result["settlement"]["outcome"] == {
        "kind": "victory", "winningSideId": "friendly"
    }
    assert result["settlementStatus"] == "settled"


def test_release002_development_keeps_seeded_generic_stage_and_debug_routes(
    tmp_path, monkeypatch
):
    database = tmp_path / "development-http.sqlite3"
    monkeypatch.setenv("LOCT_RELEASE_MODE", "development")
    monkeypatch.setenv("BATTLE_API_PROGRESSION_DB", str(database))
    monkeypatch.delenv("BATTLE_API_ENABLE_PUBLIC_BATTLES", raising=False)
    import battle_api.app as app_module

    app_module = importlib.reload(app_module)
    assert app_module.progression_store is not None
    app_module.progression_store.create_save_slot(1)
    with TestClient(app_module.app) as client:
        paths = app_module.app.openapi()["paths"]
        assert "/api/v1/battles" in paths
        assert "/api/v1/debug/battles" in paths
        generic = client.post(
            "/api/v1/battles",
            json={
                "battleSize": 1,
                "playerTeam": ["hero.warrior.weapon_master"],
                "enemyTeam": ["hero.rogue.comprehensiveness"],
                "seed": 17,
            },
        )
        assert generic.status_code == 200
        debug = client.post(
            "/api/v1/debug/battles",
            json={
                "battleSize": 1,
                "playerTeam": ["hero.warrior.weapon_master"],
                "enemyCompositionMode": "random",
                "enemyControlMode": "computer",
                "seed": 17,
            },
        )
        assert debug.status_code == 200


@pytest.mark.parametrize("seed", [_UNSET, 17, None])
def test_public_batch2_arena_seed_is_server_owned_and_client_seed_is_rejected(
    tmp_path, monkeypatch, seed
):
    app_module, client, headers = _public_http_fixture(tmp_path, monkeypatch)
    store = app_module.progression_store
    assert store is not None
    auth = app_module.identity_service.validate_session(
        client.cookies.get(app_module.SESSION_COOKIE), require_confirmed=True
    )
    squad = list(INITIAL_UNLOCKED_HERO_IDS) + [
        "hero.paladin.protection", "hero.warrior.defence"
    ]
    _unlock_public_heroes(store, auth, squad)
    run_response = client.post(
        "/api/v1/arena/runs",
        json={"squadDefinitionIds": squad},
        headers=headers,
    )
    assert run_response.status_code == 200, run_response.text
    run = run_response.json()["run"]
    node = run["nodes"][0]
    size = node["battleSize"]
    formation = {
        1: None,
        2: "front-rear",
        3: "one-front-two-rear",
    }[size]
    payload = {
        "playerTeam": squad[:size],
        "playerFormation": formation,
        "attemptId": "arena-seed-missing" if seed is _UNSET else f"arena-seed-{seed}",
    }
    if seed is not _UNSET:
        payload["seed"] = seed
    response = client.post(
        f"/api/v1/arena/runs/{run['runId']}/nodes/1/battles",
        json=payload,
        headers=headers,
    )
    if seed is _UNSET:
        assert response.status_code == 200, response.text
        assert "seedHex" not in response.json()
    else:
        assert response.status_code == 422
        detail = response.json()["detail"]
        if isinstance(detail, dict):
            assert detail["code"] == "publicSeedForbidden"
        else:
            assert any(item.get("loc", [])[-1:] == ["seed"] for item in detail)


def test_public_batch2_stage_learner_victory_commits_reward_before_duplicate_response(
    tmp_path,
):
    store = _public_store(tmp_path)
    session = _owned_public_player(store)
    profile_id = _prepare_public_stage_progress(
        store, session, "paladins-altar", 2, learner_indices=[1, 2]
    )
    store.reserve_public_battle(
        battle_id="battle-stage-learner-victory",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
        seed_hex="14" * 32,
        battle_type="stage",
        context={"stageId": "paladins-altar", "battleIndex": 3, "mode": "learner"},
        build_version="test-build",
    )
    store.activate_public_battle(
        battle_id="battle-stage-learner-victory",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
    )
    store.begin_public_battle_action(
        battle_id="battle-stage-learner-victory",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
    )
    result = store.settle_public_battle(
        battle_id="battle-stage-learner-victory",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
        outcome={"kind": "victory", "winningSideId": "friendly"},
    )
    assert result["newlyGrantedRewards"]
    assert result["newlyGrantedRewards"][0]["rewardId"] == "unlock.hero.paladin.protection"
    progression = store.read_progression(
        session.player_id, session.session_id, session.generation
    )
    assert "hero.paladin.protection" in progression["unlockedHeroDefinitionIds"]
    duplicate = store.settle_public_battle(
        battle_id="battle-stage-learner-victory",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
        outcome={"kind": "defeat", "winningSideId": "enemy"},
    )
    assert duplicate == result
    del profile_id


def test_public_batch2_stage_tactics_victory_records_mode_completion(tmp_path):
    store = _public_store(tmp_path)
    session = _owned_public_player(store)
    _prepare_public_stage_progress(
        store,
        session,
        "warriors-barrack",
        9,
        learner_indices=range(1, 10),
    )
    store.reserve_public_battle(
        battle_id="battle-stage-tactics-victory",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
        seed_hex="15" * 32,
        battle_type="stage",
        context={"stageId": "warriors-barrack", "battleIndex": 1, "mode": "tactics"},
        build_version="test-build",
    )
    store.activate_public_battle(
        battle_id="battle-stage-tactics-victory",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
    )
    store.begin_public_battle_action(
        battle_id="battle-stage-tactics-victory",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
    )
    result = store.settle_public_battle(
        battle_id="battle-stage-tactics-victory",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
        outcome={"kind": "victory", "winningSideId": "friendly"},
    )
    assert result["lifecycleStatus"] == "settled"
    progression = store.read_progression(
        session.player_id, session.session_id, session.generation
    )
    stage = next(
        row for row in progression["stageProgress"] if row["stageId"] == "warriors-barrack"
    )
    assert stage["modes"]["tactics"]["completedBattleIndices"] == [1]


def test_public_batch2_arena_victory_advances_node_and_duplicate_is_original(tmp_path):
    store = _public_store(tmp_path)
    session = _owned_public_player(store)
    squad = list(INITIAL_UNLOCKED_HERO_IDS) + ["hero.paladin.protection", "hero.warrior.defence"]
    _unlock_public_heroes(store, session, squad)
    run = store.create_arena_run(
        squad,
        schedule_seed=123,
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
    )["run"]
    store.reserve_public_battle(
        battle_id="battle-arena-victory",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
        seed_hex="16" * 32,
        battle_type="arena",
        context={"runId": run["runId"], "nodeIndex": 1},
        build_version="test-build",
    )
    store.activate_public_battle(
        battle_id="battle-arena-victory",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
    )
    store.begin_public_battle_action(
        battle_id="battle-arena-victory",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
    )
    result = store.settle_public_battle(
        battle_id="battle-arena-victory",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
        outcome={"kind": "victory", "winningSideId": "friendly"},
    )
    assert result["lifecycleStatus"] == "settled"
    arena = store.read_arena_state(
        session.player_id, session.session_id, session.generation
    )
    assert arena["run"]["currentNodeIndex"] == 2
    duplicate = store.settle_public_battle(
        battle_id="battle-arena-victory",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
        outcome={"kind": "draw"},
    )
    assert duplicate == result


def test_public_batch2_friendly_victory_fault_rolls_back_then_retries_exactly_once(
    tmp_path, monkeypatch
):
    store = _public_store(tmp_path)
    session = _owned_public_player(store)
    _prepare_public_stage_progress(store, session, "paladins-altar", 2, learner_indices=[1, 2])
    store.reserve_public_battle(
        battle_id="battle-victory-retry",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
        seed_hex="17" * 32,
        battle_type="stage",
        context={"stageId": "paladins-altar", "battleIndex": 3, "mode": "learner"},
        build_version="test-build",
    )
    store.activate_public_battle(
        battle_id="battle-victory-retry",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
    )
    store.begin_public_battle_action(
        battle_id="battle-victory-retry",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
    )
    original_hook = store._before_public_settlement_commit
    monkeypatch.setattr(
        store,
        "_before_public_settlement_commit",
        lambda connection, battle_id: (_ for _ in ()).throw(RuntimeError("fault")),
    )
    with pytest.raises(RuntimeError, match="fault"):
        store.settle_public_battle(
            battle_id="battle-victory-retry",
            player_id=session.player_id,
            session_id=session.session_id,
            session_generation=session.generation,
            outcome={"kind": "victory", "winningSideId": "friendly"},
        )
    monkeypatch.setattr(store, "_before_public_settlement_commit", original_hook)
    retry = store.settle_public_battle(
        battle_id="battle-victory-retry",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
        outcome={"kind": "victory", "winningSideId": "friendly"},
    )
    assert retry["newlyGrantedRewards"]
    duplicate = store.settle_public_battle(
        battle_id="battle-victory-retry",
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
        outcome={"kind": "draw"},
    )
    assert duplicate == retry


def test_public_batch2_terminal_pending_survives_fault_logout_and_recovery(
    tmp_path, monkeypatch
):
    """A revoked launcher cannot strand a pending result or its capacity lease."""
    store = _public_store(tmp_path)
    identity = PublicIdentityService(store, key=b"k" * 32)
    issued = identity.enroll("Pending_Recovery")
    old_session = identity.acknowledge(
        identity.validate_session(issued.session_token, require_confirmed=False)
    )
    store.create_save_slot(
        1, old_session.player_id, old_session.session_id, old_session.generation
    )
    battle_id = "battle-terminal-recovery"
    outcome = {"kind": "victory", "winningSideId": "friendly"}
    store.reserve_public_battle(
        battle_id=battle_id,
        player_id=old_session.player_id,
        session_id=old_session.session_id,
        session_generation=old_session.generation,
        seed_hex="18" * 32,
        battle_type="stage",
        context={
            "stageId": "paladins-altar",
            "battleIndex": 1,
            "mode": "learner",
        },
        build_version="test-build",
    )
    store.activate_public_battle(
        battle_id=battle_id,
        player_id=old_session.player_id,
        session_id=old_session.session_id,
        session_generation=old_session.generation,
    )
    store.begin_public_battle_action(
        battle_id=battle_id,
        player_id=old_session.player_id,
        session_id=old_session.session_id,
        session_generation=old_session.generation,
    )
    store.mark_public_battle_terminal_pending(
        battle_id=battle_id,
        player_id=old_session.player_id,
        session_id=old_session.session_id,
        session_generation=old_session.generation,
        outcome=outcome,
    )

    original_hook = store._before_public_settlement_commit
    monkeypatch.setattr(
        store,
        "_before_public_settlement_commit",
        lambda connection, battle: (_ for _ in ()).throw(RuntimeError("commit fault")),
    )
    with pytest.raises(RuntimeError, match="commit fault"):
        store.settle_public_battle(
            battle_id=battle_id,
            player_id=old_session.player_id,
            session_id=old_session.session_id,
            session_generation=old_session.generation,
            outcome=outcome,
        )

    pending = store.public_terminal_pending_battle(
        player_id=old_session.player_id,
        session_id=old_session.session_id,
        session_generation=old_session.generation,
    )
    assert pending == {"battleId": battle_id, "outcome": outcome}

    identity.logout(old_session)
    with pytest.raises(SaveSlotAccessError, match="session is no longer active"):
        store.settle_public_battle(
            battle_id=battle_id,
            player_id=old_session.player_id,
            session_id=old_session.session_id,
            session_generation=old_session.generation,
            outcome=outcome,
        )

    monkeypatch.setattr(store, "_before_public_settlement_commit", original_hook)
    recovered = identity.recover(issued.recovery_code, "127.0.0.1")
    new_session = identity.validate_session(recovered.session_token)
    retried = store.settle_public_battle(
        battle_id=battle_id,
        player_id=new_session.player_id,
        session_id=new_session.session_id,
        session_generation=new_session.generation,
        outcome=outcome,
    )
    assert retried["lifecycleStatus"] == "settled"
    assert retried["newlyGrantedRewards"] == []
    assert store.public_terminal_pending_battle(
        player_id=new_session.player_id,
        session_id=new_session.session_id,
        session_generation=new_session.generation,
    ) is None
    assert store.public_battle_receipt(
        battle_id=battle_id,
        player_id=new_session.player_id,
        session_id=new_session.session_id,
        session_generation=new_session.generation,
    ) == retried


def test_public_batch2_revision_marker_validates_on_new_v5_database(tmp_path):
    """A newly initialized Public v5 store carries and accepts Batch 2 marker."""
    database = tmp_path / "new-public-v5.sqlite3"
    store = ProgressionStore(
        database, public_mode=True, allow_public_initialize=True
    )
    connection = store._connection()
    try:
        marker = connection.execute(
            "SELECT value FROM metadata "
            "WHERE key = 'public_battle_schema_revision'"
        ).fetchone()
        assert marker is not None
        assert marker["value"] == str(PUBLIC_BATTLE_SCHEMA_REVISION)
        assert connection.execute(
            "SELECT value FROM metadata WHERE key = 'schema_version'"
        ).fetchone()["value"] == "5"
    finally:
        connection.close()

    # Re-opening the same store is the validation path used by the API.
    reopened = ProgressionStore(database, public_mode=True)
    reopened._connection().close()


def test_public_batch2_rejects_old_v5_without_mutating_database(tmp_path):
    """A legitimate Batch 1 v5 foundation fails closed without migration/writeback."""
    database = tmp_path / "old-public-v5.sqlite3"
    current = ProgressionStore(
        database, public_mode=True, allow_public_initialize=True
    )
    current._connection().close()

    # Batch 1 had schema v5 and the Public ownership tables, but no Batch 2
    # battle marker. Remove only that marker to model a real old-v5 database.
    connection = sqlite3.connect(database)
    try:
        connection.execute(
            "DELETE FROM metadata WHERE key = 'public_battle_schema_revision'"
        )
        connection.commit()
    finally:
        connection.close()

    before_bytes = database.read_bytes()
    before_rows = _sqlite_row_snapshot(database)
    legacy = ProgressionStore(database, public_mode=True)
    with pytest.raises(ProgressionStoreError) as error:
        legacy._connection()
    assert str(error.value) == (
        "This Public v5 database predates the Batch 2 battle schema. "
        "An explicit offline upgrade or approved disposable-database "
        "reinitialization is required; runtime migration is refused."
    )

    assert database.read_bytes() == before_bytes
    assert _sqlite_row_snapshot(database) == before_rows


def test_public_batch2_http_recovery_retries_terminal_pending_after_fault(
    tmp_path, monkeypatch
):
    """Recovery endpoint settles pending authority before revoking old battles."""
    database = tmp_path / "public-http-recovery.sqlite3"
    fixture = ProgressionStore(
        database, public_mode=True, allow_public_initialize=True
    )
    fixture._connection().close()
    monkeypatch.setenv("LOCT_RELEASE_MODE", "public")
    monkeypatch.setenv("BATTLE_API_PUBLIC_DB", str(database))
    monkeypatch.setenv("BATTLE_API_PUBLIC_DB_INITIALIZE", "0")
    monkeypatch.setenv("BATTLE_API_PUBLIC_HMAC_KEY", "k" * 64)
    monkeypatch.setenv("BATTLE_API_RATE_LIMIT_HMAC_KEY", "r" * 64)
    monkeypatch.setenv("BATTLE_API_PUBLIC_ORIGIN", "https://public.test")
    monkeypatch.setenv("BATTLE_API_TRUSTED_PROXY_IPS", "127.0.0.1")
    monkeypatch.setenv("BATTLE_API_ENABLE_PUBLIC_BATTLES", "1")
    import battle_api.app as app_module

    app_module = importlib.reload(app_module)
    client = TestClient(app_module.app, base_url="https://public.test")
    created = client.post(
        "/api/v1/players",
        json={"playerName": "Http_Recovery"},
        headers={"Origin": "https://public.test"},
    )
    assert created.status_code == 200
    body = created.json()
    recovery_code = body["recoveryCode"]
    csrf = body["csrfToken"]
    headers = {"Origin": "https://public.test", "X-CSRF-Token": csrf}
    assert client.post(
        "/api/v1/recovery-code/acknowledge", json={}, headers=headers
    ).status_code == 200
    assert client.post(
        "/api/v1/save-slots/1/create", json={}, headers=headers
    ).status_code == 200

    launched = _launch_public_stage(client, headers, attempt_id="recovery-route")
    assert launched.status_code == 200, launched.text
    battle_id = launched.json()["battleId"]
    token = client.cookies.get(app_module.SESSION_COOKIE)
    session = app_module.identity_service.validate_session(token)
    store = app_module.progression_store
    assert store is not None
    outcome = {"kind": "victory", "winningSideId": "friendly"}
    store.mark_public_battle_terminal_pending(
        battle_id=battle_id,
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
        outcome=outcome,
    )
    original_hook = store._before_public_settlement_commit
    monkeypatch.setattr(
        store,
        "_before_public_settlement_commit",
        lambda connection, battle: (_ for _ in ()).throw(RuntimeError("route fault")),
    )
    with pytest.raises(RuntimeError, match="route fault"):
        store.settle_public_battle(
            battle_id=battle_id,
            player_id=session.player_id,
            session_id=session.session_id,
            session_generation=session.generation,
            outcome=outcome,
        )
    monkeypatch.setattr(store, "_before_public_settlement_commit", original_hook)
    app_module.identity_service.logout(session)
    monkeypatch.setattr(
        app_module, "canonical_client_ip", lambda peer, forwarded, trusted: "127.0.0.1"
    )

    recovered = client.post(
        "/api/v1/sessions/recover",
        json={"recoveryCode": recovery_code},
        headers={
            "Origin": "https://public.test",
            "X-Forwarded-For": "127.0.0.1",
        },
    )
    assert recovered.status_code == 200, recovered.text
    assert recovered.json()["playerId"] == session.player_id
    new_session = app_module.identity_service.validate_session(
        client.cookies.get(app_module.SESSION_COOKIE)
    )
    receipt = store.public_battle_receipt(
        battle_id=battle_id,
        player_id=new_session.player_id,
        session_id=new_session.session_id,
        session_generation=new_session.generation,
    )
    assert receipt is not None
    assert receipt["battleId"] == battle_id
    assert receipt["outcome"] == outcome
    assert store.public_terminal_pending_battle(
        player_id=new_session.player_id,
        session_id=new_session.session_id,
        session_generation=new_session.generation,
    ) is None
    connection = store._connection()
    try:
        assert connection.execute(
            "SELECT 1 FROM active_battle_leases WHERE battle_id = ?", (battle_id,)
        ).fetchone() is None
    finally:
        connection.close()
