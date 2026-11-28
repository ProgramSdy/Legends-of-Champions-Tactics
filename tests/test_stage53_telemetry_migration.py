import hashlib
import sqlite3

from battle_api.progression import ProgressionStore
from battle_api.public_db_ops import upgrade_public_telemetry_v1


def canonical_fingerprint(database):
    connection = sqlite3.connect(database)
    rows = []
    for table in ("players", "profiles", "battle_diagnostics", "battle_settlements"):
        rows.extend((table, tuple(row)) for row in connection.execute(f"SELECT * FROM {table} ORDER BY 1"))
    connection.close()
    return hashlib.sha256(repr(rows).encode()).hexdigest()


def test_release004_public_copy_accepts_additive_telemetry_migration_without_canonical_change(tmp_path):
    database = tmp_path / "release004-copy.sqlite3"
    backup_root = tmp_path / "backups"
    backup_root.mkdir()
    store = ProgressionStore(database, public_mode=True, allow_public_initialize=True)
    store.ensure_initialized()
    connection = sqlite3.connect(database)
    connection.execute(
        "INSERT INTO players VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("p1", "Release_Test", b"mac", 1, "2026-01-01T00:00:00Z", None, 1, "2026-01-01T00:00:00Z"),
    )
    connection.commit()
    connection.close()
    before = canonical_fingerprint(database)

    evidence = upgrade_public_telemetry_v1(
        database, backup_root, confirm=True,
    )
    assert evidence.database.telemetry_schema_revision == 1
    assert evidence.database.integrity == "ok"
    connection = sqlite3.connect(database)
    assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    assert canonical_fingerprint(database) == before
    assert connection.execute("SELECT value FROM metadata WHERE key='telemetry_schema_revision'").fetchone()[0] == "1"
    connection.close()
