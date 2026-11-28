import sqlite3
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from battle_api.models import TelemetryEventRequest
from battle_api.progression import ProgressionStore
from battle_api.telemetry_store import (
    EVENT_SESSION_CAP,
    TelemetryStore,
    create_telemetry_schema,
)


NOW = datetime(2026, 11, 28, 12, tzinfo=UTC)


def make_store(tmp_path, *, enabled=True):
    database = tmp_path / "telemetry.sqlite3"
    progression = ProgressionStore(database, public_mode=True, allow_public_initialize=True)
    progression.ensure_initialized()
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    connection.execute("BEGIN IMMEDIATE")
    create_telemetry_schema(connection)
    connection.commit()
    connection.close()
    store = TelemetryStore(
        progression,
        enabled=enabled,
        environment="development",
        game_version="test-build",
        ruleset_version="rules-1",
        now=lambda: NOW,
    )
    return store, database


def event(event_type="landing_view", *, event_id=None, visitor_id=None, session_id=None):
    data = {"source": "direct", "campaign": "test"} if event_type == "landing_view" else (
        {} if event_type == "home_view" else (
            {"activity": "navigation"} if event_type == "session_activity" else
            {"code": "ui.failure", "routeId": "/stages"}
        )
    )
    payload = {
        "eventId": str(event_id or uuid4()),
        "eventType": event_type,
        "schemaVersion": 1,
        "visitorId": str(visitor_id or uuid4()),
        "sessionId": str(session_id or uuid4()),
        "eventData": data,
        "occurredAtUtc": NOW.isoformat(),
    }
    return payload


def parse_event(payload):
    # Pydantic's discriminated union is exposed by the request annotation at
    # the route boundary; use the concrete model validator through TypeAdapter.
    from pydantic import TypeAdapter
    return TypeAdapter(TelemetryEventRequest).validate_python(payload)


def test_default_off_never_requires_or_writes_telemetry_schema(tmp_path):
    database = tmp_path / "disabled.sqlite3"
    progression = ProgressionStore(database, public_mode=True, allow_public_initialize=True)
    progression.ensure_initialized()
    store = TelemetryStore(
        progression, enabled=False, environment="public", game_version="test", ruleset_version="r1", now=lambda: NOW
    )
    result = store.record_client_event(parse_event(event()), player_id=None)
    assert result == {"accepted": False, "duplicate": False, "reason": "unavailable"}
    connection = sqlite3.connect(database)
    assert connection.execute("SELECT 1 FROM sqlite_master WHERE name='telemetry_events'").fetchone() is None


def test_event_deduplication_and_per_session_landing_cap(tmp_path):
    store, database = make_store(tmp_path)
    visitor_id, session_id, event_id = uuid4(), uuid4(), uuid4()
    first = parse_event(event(event_id=event_id, visitor_id=visitor_id, session_id=session_id))
    assert store.record_client_event(first, player_id=None) == {"accepted": True, "duplicate": False, "reason": None}
    assert store.record_client_event(first, player_id=None) == {"accepted": True, "duplicate": True, "reason": None}
    second_id = uuid4()
    duplicate_landing = parse_event(event(event_id=second_id, visitor_id=visitor_id, session_id=session_id))
    assert store.record_client_event(duplicate_landing, player_id=None) == {"accepted": True, "duplicate": True, "reason": None}
    connection = sqlite3.connect(database)
    assert connection.execute("SELECT COUNT(*) FROM telemetry_events").fetchone()[0] == 1


def test_activity_throttle_and_session_expiry_are_bounded(tmp_path):
    store, database = make_store(tmp_path)
    visitor_id, session_id = uuid4(), uuid4()
    landing = parse_event(event(visitor_id=visitor_id, session_id=session_id))
    assert store.record_client_event(landing, player_id=None)["accepted"]
    activity = parse_event(event("session_activity", visitor_id=visitor_id, session_id=session_id))
    assert store.record_client_event(activity, player_id=None)["accepted"] is True
    activity2 = parse_event(event("session_activity", visitor_id=visitor_id, session_id=session_id))
    assert store.record_client_event(activity2, player_id=None)["reason"] == "throttled"
    # The store's clock is injectable, so expiry is deterministic and not a sleep.
    store._now = lambda: NOW + timedelta(minutes=31)
    expired = parse_event(event("home_view", visitor_id=visitor_id, session_id=session_id))
    assert store.record_client_event(expired, player_id=None)["reason"] == "sessionExpired"


def test_session_cap_rejects_extra_events_without_unbounded_storage(tmp_path):
    store, database = make_store(tmp_path)
    visitor_id, session_id = uuid4(), uuid4()
    assert store.record_client_event(parse_event(event(visitor_id=visitor_id, session_id=session_id)), player_id=None)["accepted"]
    for _ in range(5):
        # Client errors have their own tighter five-event cap.  This keeps the
        # test deterministic while proving the writer never grows unbounded.
        payload = event("client_error", visitor_id=visitor_id, session_id=session_id)
        assert store.record_client_event(parse_event(payload), player_id=None)["accepted"]
    final = event("client_error", visitor_id=visitor_id, session_id=session_id)
    assert store.record_client_event(parse_event(final), player_id=None)["reason"] == "sessionCapReached"
    connection = sqlite3.connect(database)
    assert connection.execute("SELECT COUNT(*) FROM telemetry_events").fetchone()[0] == 6
    assert connection.execute("SELECT COUNT(*) FROM telemetry_events WHERE event_type='client_error'").fetchone()[0] == 5
