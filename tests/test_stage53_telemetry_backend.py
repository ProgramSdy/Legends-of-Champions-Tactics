"""Stage 5.3 Batch B additive Public telemetry boundary tests.

All databases are disposable local fixtures.  No Production path or network
operation is used.
"""

from __future__ import annotations

from datetime import UTC, datetime
import importlib
from pathlib import Path
import sqlite3

from fastapi.testclient import TestClient
import pytest
from pydantic import TypeAdapter

import battle_api.public_db_ops as public_db_ops
from battle_api.models import TelemetryEventRequest
from battle_api.progression import INITIAL_UNLOCKED_HERO_IDS, ProgressionStore
from battle_api.public_config import (
    PublicConfigurationError,
    validate_public_configuration,
)
from battle_api.telemetry_store import TelemetryStore, create_telemetry_schema


def _public_database(tmp_path: Path) -> Path:
    database = tmp_path / "public-telemetry.sqlite3"
    store = ProgressionStore(database, public_mode=True, allow_public_initialize=True)
    store._connection().close()
    return database


def _add_telemetry_schema(database: Path) -> None:
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        connection.execute("BEGIN IMMEDIATE")
        create_telemetry_schema(connection)
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()


def _event(event_id: str, session_id: str, *, event_type: str = "landing_view"):
    data = (
        {"source": "direct", "campaign": "pre-alpha"}
        if event_type == "landing_view"
        else {"activity": "navigation"}
    )
    return TypeAdapter(TelemetryEventRequest).validate_python(
        {
            "eventId": event_id,
            "eventType": event_type,
            "schemaVersion": 1,
            "visitorId": "00000000-0000-4000-8000-000000000001",
            "sessionId": session_id,
            "occurredAtUtc": "2026-11-28T00:00:00Z",
            "eventData": data,
        }
    )


def test_offline_migration_is_atomic_idempotent_and_release004_compatible(
    tmp_path, monkeypatch
):
    database = _public_database(tmp_path)
    before = database.read_bytes()
    monkeypatch.setattr(
        public_db_ops,
        "_before_telemetry_upgrade_commit",
        lambda connection: (_ for _ in ()).throw(RuntimeError("migration fault")),
    )
    with pytest.raises(RuntimeError, match="migration fault"):
        public_db_ops.upgrade_public_telemetry_v1(
            database, tmp_path / "failed-backup", confirm=True
        )
    assert database.read_bytes() == before

    monkeypatch.setattr(
        public_db_ops, "_before_telemetry_upgrade_commit", lambda connection: None
    )
    upgraded = public_db_ops.upgrade_public_telemetry_v1(
        database,
        tmp_path / "successful-backup",
        confirm=True,
        now=datetime(2026, 11, 28, tzinfo=UTC),
    )
    assert upgraded.database.telemetry_schema_revision == 1
    assert upgraded.pre_upgrade_backup is not None
    assert upgraded.already_upgraded is False
    # The pre-telemetry RELEASE-004 store accepts additive tables/metadata.
    ProgressionStore(database, public_mode=True).ensure_initialized()

    repeated = public_db_ops.upgrade_public_telemetry_v1(
        database, tmp_path / "unused-backup", confirm=True
    )
    assert repeated.already_upgraded is True
    assert repeated.pre_upgrade_backup is None


def test_store_deduplicates_events_and_flushes_bounded_api_aggregates(tmp_path):
    database = _public_database(tmp_path)
    _add_telemetry_schema(database)
    store = TelemetryStore(
        ProgressionStore(database, public_mode=True),
        enabled=True,
        environment="public",
        game_version="RELEASE-005-test",
        ruleset_version="1.0",
        now=lambda: datetime(2026, 11, 28, 1, 2, 3, tzinfo=UTC),
    )
    event = _event(
        "10000000-0000-4000-8000-000000000001",
        "20000000-0000-4000-8000-000000000001",
    )
    assert store.record_client_event(event, player_id=None) == {
        "accepted": True,
        "duplicate": False,
        "reason": None,
    }
    assert store.record_client_event(event, player_id=None)["duplicate"] is True

    store.record_api_request(route_id="/api/v1/health", status_code=200, latency_ms=80)
    store.record_api_request(route_id="/api/v1/health", status_code=503, latency_ms=150)
    assert store.flush_api_metrics() is True
    connection = sqlite3.connect(database)
    try:
        event_count = connection.execute("SELECT COUNT(*) FROM telemetry_events").fetchone()[0]
        metric = connection.execute(
            """SELECT SUM(request_count), SUM(failed_count),
                      SUM(latency_le_100_ms), SUM(latency_le_250_ms)
               FROM telemetry_api_metrics"""
        ).fetchone()
    finally:
        connection.close()
    assert event_count == 1
    assert metric == (2, 1, 1, 1)


def test_late_landing_sets_unknown_first_touch_without_overwriting_it(tmp_path):
    database = _public_database(tmp_path)
    _add_telemetry_schema(database)
    store = TelemetryStore(
        ProgressionStore(database, public_mode=True),
        enabled=True,
        environment="public",
        game_version="RELEASE-005-test",
        ruleset_version="1.0",
    )
    session_id = "20000000-0000-4000-8000-000000000002"
    activity = _event(
        "10000000-0000-4000-8000-000000000002",
        session_id,
        event_type="session_activity",
    )
    landing = TypeAdapter(TelemetryEventRequest).validate_python(
        {
            "eventId": "10000000-0000-4000-8000-000000000003",
            "eventType": "landing_view",
            "schemaVersion": 1,
            "visitorId": "00000000-0000-4000-8000-000000000001",
            "sessionId": session_id,
            "eventData": {"source": "reddit", "campaign": "launch"},
        }
    )
    later_landing = TypeAdapter(TelemetryEventRequest).validate_python(
        {
            "eventId": "10000000-0000-4000-8000-000000000004",
            "eventType": "landing_view",
            "schemaVersion": 1,
            "visitorId": "00000000-0000-4000-8000-000000000001",
            "sessionId": session_id,
            "eventData": {"source": "x", "campaign": "overwrite"},
        }
    )
    assert store.record_client_event(activity, player_id=None)["accepted"] is True
    assert store.record_client_event(landing, player_id=None)["accepted"] is True
    assert store.record_client_event(later_landing, player_id=None)["duplicate"] is True
    connection = sqlite3.connect(database)
    try:
        visitor = connection.execute(
            "SELECT first_source, first_campaign FROM telemetry_visitors"
        ).fetchone()
        session = connection.execute(
            "SELECT session_source FROM telemetry_sessions"
        ).fetchone()
    finally:
        connection.close()
    assert visitor == ("reddit", "launch")
    assert session == ("reddit",)


def _telemetry_http_fixture(tmp_path, monkeypatch):
    database = _public_database(tmp_path)
    _add_telemetry_schema(database)
    monkeypatch.setenv("LOCT_RELEASE_MODE", "public")
    monkeypatch.setenv("LOCT_BUILD_VERSION", "RELEASE-005-test")
    monkeypatch.setenv("BATTLE_API_PUBLIC_DB", str(database))
    monkeypatch.setenv("BATTLE_API_PUBLIC_HMAC_KEY", "k" * 64)
    monkeypatch.setenv("BATTLE_API_RATE_LIMIT_HMAC_KEY", "r" * 64)
    monkeypatch.setenv("BATTLE_API_PUBLIC_ORIGIN", "https://public.test")
    monkeypatch.setenv("BATTLE_API_TRUSTED_PROXY_IPS", "127.0.0.1")
    monkeypatch.setenv("BATTLE_API_ENABLE_PUBLIC_BATTLES", "1")
    monkeypatch.setenv("BATTLE_API_ENABLE_PUBLIC_TELEMETRY", "1")
    import battle_api.app as app_module

    app_module = importlib.reload(app_module)
    return database, app_module, TestClient(
        app_module.app, base_url="https://public.test"
    )


def test_event_endpoint_is_strict_anonymous_origin_bounded_and_server_linked(
    tmp_path, monkeypatch
):
    database, app_module, client = _telemetry_http_fixture(tmp_path, monkeypatch)
    del app_module
    payload = {
        "eventId": "10000000-0000-4000-8000-000000000001",
        "eventType": "landing_view",
        "schemaVersion": 1,
        "visitorId": "00000000-0000-4000-8000-000000000001",
        "sessionId": "20000000-0000-4000-8000-000000000001",
        "eventData": {"source": "direct"},
    }
    accepted = client.post(
        "/api/v1/telemetry/events",
        json=payload,
        headers={"Origin": "https://public.test"},
    )
    assert accepted.status_code == 202, accepted.text
    assert accepted.json() == {
        "contractVersion": "1.0",
        "accepted": True,
        "duplicate": False,
        "reason": None,
    }
    assert client.post("/api/v1/telemetry/events", json=payload).status_code == 403
    invalid = {**payload, "serverOwnedPlayerId": "forged"}
    assert client.post(
        "/api/v1/telemetry/events",
        json=invalid,
        headers={"Origin": "https://public.test"},
    ).status_code == 422
    created = client.post(
        "/api/v1/players",
        json={"playerName": "Telemetry_Linked"},
        headers={"Origin": "https://public.test"},
    )
    csrf = created.json()["csrfToken"]
    auth_headers = {"Origin": "https://public.test", "X-CSRF-Token": csrf}
    assert client.post(
        "/api/v1/recovery-code/acknowledge", json={}, headers=auth_headers
    ).status_code == 200
    home = {
        "eventId": "10000000-0000-4000-8000-000000000010",
        "eventType": "home_view",
        "schemaVersion": 1,
        "visitorId": "00000000-0000-4000-8000-000000000010",
        "sessionId": "20000000-0000-4000-8000-000000000010",
        "eventData": {},
    }
    linked = client.post(
        "/api/v1/telemetry/events", json=home, headers=auth_headers
    )
    assert linked.status_code == 202, linked.text
    connection = sqlite3.connect(database)
    try:
        player_id = connection.execute(
            "SELECT player_id FROM telemetry_events WHERE event_id = ?",
            (home["eventId"],),
        ).fetchone()[0]
        canonical = connection.execute("SELECT player_id FROM players").fetchone()[0]
    finally:
        connection.close()
    assert player_id == canonical


def test_enabled_configuration_requires_offline_schema_but_default_off_does_not(
    tmp_path,
):
    database = _public_database(tmp_path)
    environment = {
        "LOCT_RELEASE_MODE": "public",
        "BATTLE_API_PUBLIC_DB": str(database),
        "BATTLE_API_PUBLIC_ORIGIN": "https://public.test",
        "BATTLE_API_PUBLIC_HMAC_KEY": "k" * 64,
        "BATTLE_API_RATE_LIMIT_HMAC_KEY": "r" * 64,
        "BATTLE_API_TRUSTED_PROXY_IPS": "127.0.0.1",
    }
    assert validate_public_configuration(environment).public_telemetry_enabled is False
    with pytest.raises(PublicConfigurationError, match="offline telemetry schema"):
        validate_public_configuration(
            {**environment, "BATTLE_API_ENABLE_PUBLIC_TELEMETRY": "1"}
        )


def test_normal_app_shutdown_flushes_pending_api_metric_batch(tmp_path, monkeypatch):
    database, app_module, client = _telemetry_http_fixture(tmp_path, monkeypatch)
    with client:
        assert client.get("/api/v1/health").status_code == 200
    connection = sqlite3.connect(database)
    try:
        count = connection.execute(
            "SELECT SUM(request_count) FROM telemetry_api_metrics"
        ).fetchone()[0]
    finally:
        connection.close()
    assert count == 1
    assert app_module.telemetry_store.failure_counts() == {}


def test_stage_launch_captures_ordered_post_activation_battle_facts(
    tmp_path, monkeypatch
):
    database, app_module, client = _telemetry_http_fixture(tmp_path, monkeypatch)
    created = client.post(
        "/api/v1/players",
        json={"playerName": "Telemetry_Player"},
        headers={"Origin": "https://public.test"},
    )
    assert created.status_code == 200
    csrf = created.json()["csrfToken"]
    headers = {"Origin": "https://public.test", "X-CSRF-Token": csrf}
    assert client.post(
        "/api/v1/recovery-code/acknowledge", json={}, headers=headers
    ).status_code == 200
    assert client.post(
        "/api/v1/save-slots/1/create", json={}, headers=headers
    ).status_code == 200
    launched = client.post(
        "/api/v1/stages/paladins-altar/battles/1",
        json={
            "playerTeam": [
                "hero.priest.comprehensiveness",
                "hero.mage.comprehensiveness",
            ],
            "playerFormation": "front-rear",
            "mode": "learner",
            "attemptId": "telemetry-stage-launch",
        },
        headers=headers,
    )
    assert launched.status_code == 200, launched.text
    battle_id = launched.json()["battleId"]
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    try:
        row = connection.execute(
            "SELECT * FROM telemetry_battles WHERE battle_id = ?", (battle_id,)
        ).fetchone()
    finally:
        connection.close()
    assert row is not None
    assert row["mode"] == "learner"
    assert row["encounter_id"] == "stage:paladins-altar:1"
    assert row["player_formation"] == "front-rear"
    assert row["attempt_id"] == "telemetry-stage-launch"
    assert app_module.telemetry_store.failure_counts() == {}


def test_arena_launch_captures_canonical_run_and_node_context(tmp_path, monkeypatch):
    database, app_module, client = _telemetry_http_fixture(tmp_path, monkeypatch)
    created = client.post(
        "/api/v1/players",
        json={"playerName": "Telemetry_Arena"},
        headers={"Origin": "https://public.test"},
    )
    csrf = created.json()["csrfToken"]
    headers = {"Origin": "https://public.test", "X-CSRF-Token": csrf}
    assert client.post(
        "/api/v1/recovery-code/acknowledge", json={}, headers=headers
    ).status_code == 200
    assert client.post(
        "/api/v1/save-slots/1/create", json={}, headers=headers
    ).status_code == 200
    auth = app_module.identity_service.validate_session(
        client.cookies.get(app_module.SESSION_COOKIE), require_confirmed=True
    )
    squad = list(INITIAL_UNLOCKED_HERO_IDS) + [
        "hero.paladin.protection",
        "hero.warrior.defence",
    ]
    profile_id = app_module.progression_store.active_profile_id(auth.player_id)
    connection = app_module.progression_store._connection()
    try:
        connection.executemany(
            "INSERT OR IGNORE INTO unlocked_heroes(profile_id, definition_id) VALUES (?, ?)",
            [(profile_id, definition_id) for definition_id in squad],
        )
        connection.commit()
    finally:
        connection.close()
    run_response = client.post(
        "/api/v1/arena/runs",
        json={"squadDefinitionIds": squad},
        headers=headers,
    )
    assert run_response.status_code == 200, run_response.text
    run = run_response.json()["run"]
    size = run["nodes"][0]["battleSize"]
    formation = {1: None, 2: "front-rear", 3: "one-front-two-rear"}[size]
    launched = client.post(
        f"/api/v1/arena/runs/{run['runId']}/nodes/1/battles",
        json={
            "playerTeam": squad[:size],
            "playerFormation": formation,
            "attemptId": "telemetry-arena-launch",
        },
        headers=headers,
    )
    assert launched.status_code == 200, launched.text
    connection = sqlite3.connect(database)
    try:
        context = connection.execute(
            "SELECT mode, encounter_id FROM telemetry_battles WHERE battle_id = ?",
            (launched.json()["battleId"],),
        ).fetchone()
    finally:
        connection.close()
    assert context == ("arena", f"arena:{run['runId']}:1")


def test_post_commit_telemetry_failure_does_not_change_battle_launch(
    tmp_path, monkeypatch
):
    database, app_module, client = _telemetry_http_fixture(tmp_path, monkeypatch)
    created = client.post(
        "/api/v1/players",
        json={"playerName": "Telemetry_Failure"},
        headers={"Origin": "https://public.test"},
    )
    csrf = created.json()["csrfToken"]
    headers = {"Origin": "https://public.test", "X-CSRF-Token": csrf}
    assert client.post(
        "/api/v1/recovery-code/acknowledge", json={}, headers=headers
    ).status_code == 200
    assert client.post(
        "/api/v1/save-slots/1/create", json={}, headers=headers
    ).status_code == 200
    monkeypatch.setattr(
        app_module.telemetry_store,
        "record_battle_started",
        lambda **facts: (_ for _ in ()).throw(RuntimeError("sidecar fault")),
    )
    launched = client.post(
        "/api/v1/stages/paladins-altar/battles/1",
        json={
            "playerTeam": [
                "hero.priest.comprehensiveness",
                "hero.mage.comprehensiveness",
            ],
            "playerFormation": "front-rear",
            "mode": "learner",
            "attemptId": "telemetry-failure-launch",
        },
        headers=headers,
    )
    assert launched.status_code == 200, launched.text
    connection = sqlite3.connect(database)
    try:
        lifecycle = connection.execute(
            "SELECT lifecycle_status FROM battle_diagnostics WHERE battle_id = ?",
            (launched.json()["battleId"],),
        ).fetchone()
    finally:
        connection.close()
    assert lifecycle == ("active",)
    assert app_module.telemetry_store.failure_counts()["battle_started_dispatch"] == 1


def test_default_off_does_not_require_telemetry_schema(tmp_path, monkeypatch):
    database = _public_database(tmp_path)
    monkeypatch.setenv("LOCT_RELEASE_MODE", "public")
    monkeypatch.setenv("BATTLE_API_PUBLIC_DB", str(database))
    monkeypatch.setenv("BATTLE_API_PUBLIC_HMAC_KEY", "k" * 64)
    monkeypatch.setenv("BATTLE_API_RATE_LIMIT_HMAC_KEY", "r" * 64)
    monkeypatch.setenv("BATTLE_API_PUBLIC_ORIGIN", "https://public.test")
    monkeypatch.setenv("BATTLE_API_TRUSTED_PROXY_IPS", "127.0.0.1")
    monkeypatch.delenv("BATTLE_API_ENABLE_PUBLIC_TELEMETRY", raising=False)
    import battle_api.app as app_module

    app_module = importlib.reload(app_module)
    client = TestClient(app_module.app, base_url="https://public.test")
    assert client.get("/api/v1/health").status_code == 200
    response = client.post(
        "/api/v1/telemetry/events",
        json={},
        headers={"Origin": "https://public.test"},
    )
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "telemetryDisabled"
