"""RELEASE-002 Batch 1 security boundary regressions.

These tests use disposable progression databases and exercise only the public
route boundary.  They intentionally do not touch the repository Development
save database or create a player battle in Public mode.
"""

from __future__ import annotations

import importlib
import hashlib
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from battle_api.progression import (
    ProgressionStore,
    ProgressionStoreError,
    SaveSlotAccessError,
)
from battle_api.public_identity import (
    PREVIOUS_TOKEN_GRACE,
    PublicIdentityError,
    PublicIdentityService,
    canonical_client_ip,
)


def _load_app(monkeypatch, tmp_path, mode: str):
    database_path = tmp_path / f"{mode}.sqlite3"
    if mode == "public":
        # Public startup is fail-closed, so create only a disposable fixture
        # through the explicit initializer before importing the app.
        fixture = ProgressionStore(
            database_path,
            public_mode=True,
            allow_public_initialize=True,
        )
        fixture._connection().close()
        monkeypatch.setenv("BATTLE_API_PUBLIC_DB", str(database_path))
        monkeypatch.setenv("BATTLE_API_PUBLIC_DB_INITIALIZE", "0")
        monkeypatch.setenv("BATTLE_API_PUBLIC_HMAC_KEY", "k" * 64)
        monkeypatch.setenv("BATTLE_API_RATE_LIMIT_HMAC_KEY", "r" * 64)
        monkeypatch.setenv("BATTLE_API_PUBLIC_ORIGIN", "https://public.test")
        monkeypatch.setenv("BATTLE_API_TRUSTED_PROXY_IPS", "127.0.0.1")
    monkeypatch.setenv("BATTLE_API_PROGRESSION_DB", str(database_path))
    monkeypatch.setenv("LOCT_RELEASE_MODE", mode)
    import battle_api.app as app_module

    return importlib.reload(app_module)


def test_public_generic_battle_route_is_not_registered(monkeypatch, tmp_path):
    app_module = _load_app(monkeypatch, tmp_path, "public")

    paths = app_module.app.openapi()["paths"]
    assert "/api/v1/battles" not in paths
    assert not any("/battles" in path for path in paths)
    with TestClient(app_module.app) as client:
        response = client.post("/api/v1/battles", json={"battleSize": 1})
    assert response.status_code == 404


def test_public_save_slots_require_player_session(monkeypatch, tmp_path):
    app_module = _load_app(monkeypatch, tmp_path, "public")

    with TestClient(app_module.app) as client:
        response = client.get("/api/v1/save-slots")
    assert response.status_code == 401


def test_public_identity_origin_and_csrf_boundaries(monkeypatch, tmp_path):
    app_module = _load_app(monkeypatch, tmp_path, "public")
    with TestClient(app_module.app, base_url="https://public.test") as client:
        created = client.post(
            "/api/v1/players",
            json={"playerName": "Api_Player"},
            headers={"Origin": "https://public.test"},
        )
        assert created.status_code == 200
        csrf = created.json()["csrfToken"]
        bad_origin = client.post(
            "/api/v1/recovery-code/acknowledge",
            json={},
            headers={"Origin": "https://evil.test", "X-CSRF-Token": csrf},
        )
        assert bad_origin.status_code == 403
        missing_csrf = client.post(
            "/api/v1/recovery-code/acknowledge",
            json={},
            headers={"Origin": "https://public.test"},
        )
        assert missing_csrf.status_code == 403
        acknowledged = client.post(
            "/api/v1/recovery-code/acknowledge",
            json={},
            headers={"Origin": "https://public.test", "X-CSRF-Token": csrf},
        )
        assert acknowledged.status_code == 200
        assert acknowledged.json()["recoveryConfirmed"] is True


def test_public_profile_reads_and_arena_state_require_session(monkeypatch, tmp_path):
    app_module = _load_app(monkeypatch, tmp_path, "public")
    with TestClient(app_module.app, base_url="https://public.test") as client:
        for path in ("/api/v1/save-slots", "/api/v1/progression", "/api/v1/arena"):
            response = client.get(path)
            assert response.status_code == 401, (path, response.status_code)


def test_development_generic_battle_route_remains_available(monkeypatch, tmp_path):
    app_module = _load_app(monkeypatch, tmp_path, "development")

    assert "/api/v1/battles" in app_module.app.openapi()["paths"]


def test_public_store_requires_explicit_initialization_and_has_public_foundation(tmp_path):
    database_path = tmp_path / "public.sqlite3"
    blocked = ProgressionStore(database_path, public_mode=True)
    try:
        blocked.list_save_slots()
    except ProgressionStoreError:
        pass
    else:
        raise AssertionError("Public startup must not silently create its database")

    store = ProgressionStore(
        database_path,
        public_mode=True,
        allow_public_initialize=True,
    )
    connection = store._connection()
    try:
        role = connection.execute(
            "SELECT value FROM metadata WHERE key = 'database_role'"
        ).fetchone()["value"]
        version = connection.execute(
            "SELECT value FROM metadata WHERE key = 'schema_version'"
        ).fetchone()["value"]
        tables = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        assert role == "public"
        assert version == "5"
        assert {"players", "player_save_slots", "player_active_slots"} <= tables
    finally:
        connection.close()


def test_public_store_rejects_nonempty_development_database(tmp_path):
    database_path = tmp_path / "nonempty.sqlite3"
    development = ProgressionStore(database_path)
    development.list_save_slots()

    public = ProgressionStore(
        database_path,
        public_mode=True,
        allow_public_initialize=True,
    )
    try:
        public.list_save_slots()
    except ProgressionStoreError:
        pass
    else:
        raise AssertionError("Public initialization must reject a non-empty Dev DB")


def test_public_store_rejects_incompatible_schema_without_replacing_it(tmp_path):
    database_path = tmp_path / "incompatible.sqlite3"
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        connection.execute(
            "INSERT INTO metadata(key, value) VALUES ('schema_version', '5')"
        )
        connection.execute(
            "INSERT INTO metadata(key, value) VALUES ('database_role', 'public')"
        )
    before = database_path.read_bytes()
    store = ProgressionStore(database_path, public_mode=True)
    try:
        store._connection()
    except ProgressionStoreError:
        pass
    else:
        raise AssertionError("Public startup must reject incomplete schema")
    assert database_path.read_bytes() == before


def test_public_store_rejects_v5_with_dropped_single_session_index(tmp_path):
    database_path = tmp_path / "dropped-index.sqlite3"
    initialized = ProgressionStore(
        database_path, public_mode=True, allow_public_initialize=True
    )
    initialized._connection().close()
    with sqlite3.connect(database_path) as connection:
        connection.execute("DROP INDEX one_active_session_per_player")
        connection.commit()
    before = database_path.read_bytes()
    with __import__("pytest").raises(ProgressionStoreError):
        ProgressionStore(database_path, public_mode=True)._connection()
    assert database_path.read_bytes() == before


def test_development_and_public_databases_are_separate_and_dev_bytes_unchanged(tmp_path):
    development_path = tmp_path / "development.sqlite3"
    public_path = tmp_path / "public.sqlite3"
    development = ProgressionStore(development_path)
    development.list_save_slots()
    before_hash = hashlib.sha256(development_path.read_bytes()).hexdigest()

    public = ProgressionStore(
        public_path,
        public_mode=True,
        allow_public_initialize=True,
    )
    public._connection().close()

    assert development_path != public_path
    assert hashlib.sha256(development_path.read_bytes()).hexdigest() == before_hash
    assert public_path.exists()


def test_public_schema_enforces_foreign_keys_and_slot_constraints(tmp_path):
    database_path = tmp_path / "public.sqlite3"
    store = ProgressionStore(
        database_path,
        public_mode=True,
        allow_public_initialize=True,
    )
    connection = store._connection()
    try:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        connection.execute(
            "INSERT INTO players(player_id, display_name, recovery_mac, recovery_key_version, "
            "recovery_issued_at, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            ("p1", "Player_1", b"mac-1", 1, "now", "now"),
        )
        connection.execute(
            "INSERT INTO player_save_slots(player_id, slot_id) VALUES (?, ?)",
            ("p1", 1),
        )
        try:
            connection.execute(
                "INSERT INTO player_save_slots(player_id, slot_id) VALUES (?, ?)",
                ("p1", 1),
            )
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("player slot positions must be unique per player")
        try:
            connection.execute(
                "INSERT INTO player_save_slots(player_id, slot_id) VALUES (?, ?)",
                ("missing", 1),
            )
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("slot rows must reference an existing player")
    finally:
        connection.rollback()
        connection.close()


def test_public_initialization_failure_does_not_mark_database_public(monkeypatch, tmp_path):
    database_path = tmp_path / "failed-public.sqlite3"

    def fail_upgrade(self, connection):
        del self, connection
        raise ProgressionStoreError("injected schema failure")

    monkeypatch.setattr(
        ProgressionStore,
        "_upgrade_empty_v4_to_public_v5",
        fail_upgrade,
    )
    store = ProgressionStore(
        database_path,
        public_mode=True,
        allow_public_initialize=True,
    )
    try:
        store._connection()
    except ProgressionStoreError:
        pass
    else:
        raise AssertionError("injected Public schema failure must abort startup")

    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        assert "players" not in tables
        if "metadata" in tables:
            metadata = connection.execute(
                "SELECT value FROM metadata WHERE key = 'database_role'"
            ).fetchone()
            assert metadata is None


def _identity_fixture(tmp_path, now):
    store = ProgressionStore(
        tmp_path / "identity.sqlite3",
        public_mode=True,
        allow_public_initialize=True,
    )
    store._connection().close()
    return PublicIdentityService(store, key=b"k" * 32, now=lambda: now)


def test_identity_enrollment_code_and_acknowledgement_are_safe(tmp_path):
    now = datetime(2026, 11, 15, tzinfo=UTC)
    service = _identity_fixture(tmp_path, now)
    issued = service.enroll("Case_Name")

    assert issued.player_id
    assert issued.recovery_code is not None
    assert len(issued.recovery_code.replace("-", "")) == 16
    assert issued.recovery_confirmed is False
    assert service.validate_session(
        issued.session_token, require_confirmed=False
    ).player_id == issued.player_id
    with sqlite3.connect(service.store.database_path) as connection:
        row = connection.execute(
            "SELECT display_name, recovery_mac FROM players WHERE player_id = ?",
            (issued.player_id,),
        ).fetchone()
        assert row[0] == "Case_Name"
        assert issued.recovery_code.replace("-", "").encode() not in row[1]
        assert connection.execute(
            "SELECT COUNT(*) FROM player_save_slots WHERE player_id = ?",
            (issued.player_id,),
        ).fetchone()[0] == 5
    confirmed = service.acknowledge(
        service.validate_session(issued.session_token, require_confirmed=False)
    )
    assert confirmed.recovery_confirmed is True
    with __import__("pytest").raises(PublicIdentityError) as error:
        service.enroll("ab")
    assert error.value.code == "invalidPlayerName"
    with __import__("pytest").raises(PublicIdentityError):
        service.enroll("bad-name")


def test_recovery_is_code_only_and_revokes_old_device(tmp_path):
    now = datetime(2026, 11, 15, tzinfo=UTC)
    service = _identity_fixture(tmp_path, now)
    issued = service.enroll("Player_One")
    recovered = service.recover(issued.recovery_code or "", "203.0.113.5")
    assert recovered.player_id == issued.player_id
    with __import__("pytest").raises(PublicIdentityError) as error:
        service.validate_session(issued.session_token, require_confirmed=False)
    assert error.value.code in {"sessionRequired", "sessionRevoked"}
    # Recovery codes remain valid until the authenticated replacement flow;
    # a second recovery rotates/revokes the current device again.
    second = service.recover(issued.recovery_code or "", "203.0.113.5")
    assert second.player_id == issued.player_id


def test_recovery_rate_limit_is_tenth_failure_then_fifteen_minute_block(tmp_path):
    now = datetime(2026, 11, 15, tzinfo=UTC)
    service = _identity_fixture(tmp_path, now)
    for attempt in range(9):
        try:
            service.recover("INVALID-CODE", "203.0.113.9")
        except PublicIdentityError as error:
            assert error.code == "recoveryInvalid"
    with __import__("pytest").raises(PublicIdentityError) as error:
        service.recover("INVALID-CODE", "203.0.113.9")
    assert error.value.code == "recoveryInvalid"
    with __import__("pytest").raises(PublicIdentityError) as error:
        service.recover("INVALID-CODE", "203.0.113.9")
    assert error.value.code == "recoveryRateLimited"
    later = now + timedelta(minutes=15, seconds=1)
    service.now = lambda: later
    with __import__("pytest").raises(PublicIdentityError) as error:
        service.recover("INVALID-CODE", "203.0.113.9")
    assert error.value.code == "recoveryInvalid"


def test_session_slides_and_rotates_with_previous_token_grace(tmp_path):
    now = datetime(2026, 11, 15, tzinfo=UTC)
    service = _identity_fixture(tmp_path, now)
    issued = service.enroll("Rotate_Me")
    service.acknowledge(
        service.validate_session(issued.session_token, require_confirmed=False)
    )
    service.now = lambda: now + timedelta(days=1, seconds=1)
    rotated = service.validate_session(issued.session_token, touch=True, rotate=True)
    assert rotated.rotated_token is not None
    assert service.validate_session(rotated.rotated_token).player_id == issued.player_id
    service.now = lambda: now + timedelta(days=31, seconds=PREVIOUS_TOKEN_GRACE.total_seconds() + 1)
    with __import__("pytest").raises(PublicIdentityError):
        service.validate_session(issued.session_token)


def test_read_only_session_validation_does_not_slide_or_rotate(tmp_path):
    now = datetime(2026, 11, 15, tzinfo=UTC)
    service = _identity_fixture(tmp_path, now)
    issued = service.enroll("Read_Only")
    service.acknowledge(
        service.validate_session(issued.session_token, require_confirmed=False)
    )
    with sqlite3.connect(service.store.database_path) as connection:
        before = connection.execute(
            "SELECT token_mac, previous_token_mac, issued_at, last_seen_at, expires_at "
            "FROM player_sessions WHERE session_id = ?", (issued.session_id,)
        ).fetchone()
    service.now = lambda: now + timedelta(days=1, seconds=1)
    checked = service.validate_session(issued.session_token, rotate=True)
    assert checked.rotated_token is None
    with sqlite3.connect(service.store.database_path) as connection:
        after = connection.execute(
            "SELECT token_mac, previous_token_mac, issued_at, last_seen_at, expires_at "
            "FROM player_sessions WHERE session_id = ?", (issued.session_id,)
        ).fetchone()
    assert after == before

    touched = service.validate_session(issued.session_token, touch=True, rotate=True)
    assert touched.rotated_token is not None
    with sqlite3.connect(service.store.database_path) as connection:
        renewed = connection.execute(
            "SELECT token_mac, previous_token_mac, issued_at, last_seen_at, expires_at "
            "FROM player_sessions WHERE session_id = ?", (issued.session_id,)
        ).fetchone()
    assert renewed != before


def test_client_ip_header_requires_trusted_proxy_and_single_address():
    assert canonical_client_ip("198.51.100.1", "203.0.113.4") == "198.51.100.1"
    assert canonical_client_ip(
        "10.0.0.1", "203.0.113.4", frozenset({"10.0.0.1"})
    ) == "203.0.113.4"
    with __import__("pytest").raises(PublicIdentityError):
        canonical_client_ip("10.0.0.1", "203.0.113.4, 198.51.100.2", frozenset({"10.0.0.1"}))


def test_two_public_players_have_independent_slots_and_active_profiles(tmp_path):
    now = datetime.now(UTC)
    service = _identity_fixture(tmp_path, now)
    first = service.enroll("First_Player")
    second = service.enroll("Second_Player")
    service.acknowledge(
        service.validate_session(first.session_token, require_confirmed=False)
    )
    service.acknowledge(
        service.validate_session(second.session_token, require_confirmed=False)
    )
    store = service.store

    first_slot = store.create_save_slot(
        1, first.player_id, first.session_id, first.generation
    )
    second_slot = store.create_save_slot(
        1, second.player_id, second.session_id, second.generation
    )
    first_profile = first_slot["slot"]["profileId"]
    second_profile = second_slot["slot"]["profileId"]
    assert first_profile != second_profile
    assert store.list_save_slots(
        first.player_id, first.session_id, first.generation
    )["activeSlotId"] == 1
    assert store.list_save_slots(
        second.player_id, second.session_id, second.generation
    )["activeSlotId"] == 1
    assert store.active_profile_id(first.player_id) == first_profile
    assert store.active_profile_id(second.player_id) == second_profile
    assert store.read_progression(
        first.player_id, first.session_id, first.generation
    )["profileId"] == first_profile
    assert store.read_arena_state(
        second.player_id, second.session_id, second.generation
    )["profileId"] == second_profile
    with __import__("pytest").raises(SaveSlotAccessError):
        store.read_progression(
            first.player_id, second.session_id, second.generation
        )


def test_public_same_slot_race_has_one_atomic_winner(tmp_path):
    now = datetime.now(UTC)
    service = _identity_fixture(tmp_path, now)
    issued = service.enroll("Race_Player")
    service.acknowledge(
        service.validate_session(issued.session_token, require_confirmed=False)
    )
    store = service.store

    def create():
        try:
            result = store.create_save_slot(
                1, issued.player_id, issued.session_id, issued.generation
            )
            return ("ok", result["slot"]["profileId"])
        except SaveSlotAccessError as error:
            return (error.code, None)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: create(), range(2)))
    assert sorted(result[0] for result in results) == ["ok", "slotOccupied"]
    state = store.list_save_slots(
        issued.player_id, issued.session_id, issued.generation
    )
    assert sum(slot["occupied"] for slot in state["slots"]) == 1


def test_public_arena_mutation_rejects_other_players_session(tmp_path):
    now = datetime.now(UTC)
    service = _identity_fixture(tmp_path, now)
    first = service.enroll("Arena_First")
    second = service.enroll("Arena_Second")
    for identity in (first, second):
        service.acknowledge(
            service.validate_session(identity.session_token, require_confirmed=False)
        )
        service.store.create_save_slot(
            1, identity.player_id, identity.session_id, identity.generation
        )
    with __import__("pytest").raises(SaveSlotAccessError):
        service.store.create_arena_run(
            [],
            player_id=first.player_id,
            session_id=second.session_id,
            session_generation=second.generation,
        )
