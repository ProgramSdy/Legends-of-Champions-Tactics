"""RELEASE-002 Batch 3 local-only Public database operations.

These tests use disposable Public v5 databases under pytest's temporary
directory. They exercise the SQLite online-backup/restore boundary without
touching a repository or live player database.
"""

from datetime import UTC, datetime, timedelta
from pathlib import Path
import sqlite3
from threading import Event, Thread

import pytest

import battle_api.public_db_ops as public_db_ops
from battle_api.progression import ProgressionStore
from battle_api.public_config import (
    PublicConfigurationError,
    validate_public_configuration,
)
from battle_api.public_db_ops import (
    PublicDatabaseOperationError,
    backup_public_database,
    inspect_public_database,
    restore_public_database_for_validation,
)


def _public_database(tmp_path: Path) -> Path:
    database = tmp_path / "public.sqlite3"
    store = ProgressionStore(database, public_mode=True, allow_public_initialize=True)
    store._connection().close()
    return database


def test_inspection_is_read_only_and_confirms_public_batch2_schema(tmp_path):
    database = _public_database(tmp_path)
    before = database.read_bytes()

    evidence = inspect_public_database(database)

    assert evidence.path == str(database.resolve())
    assert evidence.schema_version == 5
    assert evidence.battle_schema_revision == 2
    assert evidence.integrity == "ok"
    assert database.read_bytes() == before


def test_online_backup_and_isolated_restore_preserve_evidence(tmp_path):
    database = _public_database(tmp_path)
    backup_root = tmp_path / "backups"
    now = datetime(2026, 11, 17, 12, 0, tzinfo=UTC)

    backup = backup_public_database(
        database, backup_root, kind="release", label="pre-release", now=now
    )
    restored = restore_public_database_for_validation(
        Path(backup.backup.path), tmp_path / "restore.sqlite3"
    )

    assert backup.kind == "release"
    assert Path(backup.backup.path).is_file()
    assert Path(backup.manifest_path).is_file()
    assert restored.sha256 == backup.backup.sha256
    assert restored.battle_schema_revision == 2
    assert (tmp_path / "restore.sqlite3").stat().st_mode & 0o077 == 0


def test_daily_retention_keeps_seven_and_release_backup_is_separate(tmp_path):
    database = _public_database(tmp_path)
    backup_root = tmp_path / "backups"
    start = datetime(2026, 11, 17, 12, 0, tzinfo=UTC)

    for index in range(9):
        backup_public_database(
            database,
            backup_root,
            kind="daily",
            now=start + timedelta(seconds=index),
        )
    release = backup_public_database(
        database,
        backup_root,
        kind="release",
        label="release-002",
        now=start + timedelta(minutes=1),
    )

    assert len(list((backup_root / "daily").glob("public-daily-*.sqlite3"))) == 7
    assert len(list((backup_root / "release").glob("public-release-*.sqlite3"))) == 1
    assert release.removed_daily_backups == ()


def test_backup_and_restore_never_overwrite_existing_files(tmp_path):
    database = _public_database(tmp_path)
    backup_root = tmp_path / "backups"
    backup = backup_public_database(database, backup_root, now=datetime.now(UTC))

    with pytest.raises(PublicDatabaseOperationError, match="must differ"):
        restore_public_database_for_validation(
            Path(backup.backup.path), Path(backup.backup.path)
        )

    destination = tmp_path / "existing.sqlite3"
    destination.write_bytes(b"owner data")
    with pytest.raises(PublicDatabaseOperationError, match="overwrite"):
        restore_public_database_for_validation(Path(backup.backup.path), destination)
    assert destination.read_bytes() == b"owner data"


def test_operations_reject_repository_paths(tmp_path):
    database = _public_database(tmp_path)
    with pytest.raises(PublicDatabaseOperationError, match="outside the repository"):
        backup_public_database(database, Path.cwd() / "tmp-public-backups")


def test_public_configuration_is_secret_redacting_and_defaults_battles_off(tmp_path):
    database = _public_database(tmp_path)
    evidence = validate_public_configuration(
        {
            "LOCT_RELEASE_MODE": "public",
            "BATTLE_API_PUBLIC_DB": str(database),
            "BATTLE_API_PUBLIC_ORIGIN": "https://public.test",
            "BATTLE_API_PUBLIC_HMAC_KEY": "i" * 64,
            "BATTLE_API_RATE_LIMIT_HMAC_KEY": "r" * 64,
            "BATTLE_API_PUBLIC_HMAC_KEY_VERSION": "2",
            "BATTLE_API_TRUSTED_PROXY_IPS": "127.0.0.1",
        }
    )
    assert evidence.public_battles_enabled is False
    assert evidence.hmac_key_version == 2
    assert not hasattr(evidence, "hmac_key")


@pytest.mark.parametrize(
    ("missing", "message"),
    [
        ("BATTLE_API_PUBLIC_ORIGIN", "exact HTTPS origin"),
        ("BATTLE_API_RATE_LIMIT_HMAC_KEY", "at least 32 bytes"),
        ("BATTLE_API_TRUSTED_PROXY_IPS", "explicit Nginx peer"),
    ],
)
def test_public_configuration_fails_closed_for_missing_security_values(
    tmp_path, missing, message
):
    database = _public_database(tmp_path)
    environment = {
        "LOCT_RELEASE_MODE": "public",
        "BATTLE_API_PUBLIC_DB": str(database),
        "BATTLE_API_PUBLIC_ORIGIN": "https://public.test",
        "BATTLE_API_PUBLIC_HMAC_KEY": "i" * 64,
        "BATTLE_API_RATE_LIMIT_HMAC_KEY": "r" * 64,
        "BATTLE_API_TRUSTED_PROXY_IPS": "127.0.0.1",
    }
    del environment[missing]
    with pytest.raises(PublicConfigurationError, match=message):
        validate_public_configuration(environment)


def test_public_configuration_honors_explicit_empty_mapping():
    with pytest.raises(PublicConfigurationError, match="LOCT_RELEASE_MODE"):
        validate_public_configuration({})


def test_online_backup_tolerates_concurrent_wal_writer_and_restores(tmp_path):
    database = _public_database(tmp_path)
    writer = sqlite3.connect(database, timeout=5.0)
    writer.execute("PRAGMA journal_mode=WAL")
    writer.execute("CREATE TABLE backup_probe(value TEXT NOT NULL)")
    writer.commit()
    writer.close()

    writer_started = Event()
    stop_writer = Event()

    def write_rows():
        writer = sqlite3.connect(database, timeout=5.0)
        index = 0
        while not stop_writer.is_set():
            writer.execute("INSERT INTO backup_probe(value) VALUES (?)", (str(index),))
            writer.commit()
            writer_started.set()
            index += 1
        writer.close()

    thread = Thread(target=write_rows)
    thread.start()
    assert writer_started.wait(timeout=2)
    try:
        evidence = backup_public_database(
            database,
            tmp_path / "backups",
            kind="release",
            label="wal-concurrent",
        )
    finally:
        stop_writer.set()
    thread.join()
    restored = restore_public_database_for_validation(
        Path(evidence.backup.path), tmp_path / "wal-restore.sqlite3",
        require_batch2=False,
    )
    assert restored.integrity == "ok"


def test_offline_batch1_upgrade_requires_confirmation_backs_up_and_adds_revision(tmp_path):
    database = _public_database(tmp_path)
    connection = sqlite3.connect(database)
    connection.execute("DELETE FROM metadata WHERE key = 'public_battle_schema_revision'")
    connection.commit()
    connection.close()

    with pytest.raises(PublicDatabaseOperationError, match="confirm"):
        public_db_ops.upgrade_batch1_public_v5(database, tmp_path / "backups")

    upgraded = public_db_ops.upgrade_batch1_public_v5(
        database, tmp_path / "backups", confirm=True
    )
    assert upgraded.database.battle_schema_revision == 2
    assert Path(upgraded.pre_upgrade_backup.backup.path).is_file()
    assert upgraded.pre_upgrade_backup.kind == "release"
    assert len(list((tmp_path / "backups" / "release").glob("*.sqlite3"))) == 1


def test_offline_upgrade_ddl_failure_keeps_original_and_preflight_backup(tmp_path, monkeypatch):
    database = _public_database(tmp_path)
    connection = sqlite3.connect(database)
    connection.execute("DELETE FROM metadata WHERE key = 'public_battle_schema_revision'")
    connection.commit()
    connection.close()
    before = database.read_bytes()
    monkeypatch.setattr(
        public_db_ops,
        "_before_public_upgrade_commit",
        lambda connection: (_ for _ in ()).throw(RuntimeError("upgrade fault")),
    )

    with pytest.raises(RuntimeError, match="upgrade fault"):
        public_db_ops.upgrade_batch1_public_v5(
            database, tmp_path / "backups", confirm=True
        )
    assert database.read_bytes() == before
    assert len(list((tmp_path / "backups" / "release").glob("*.sqlite3"))) == 1
