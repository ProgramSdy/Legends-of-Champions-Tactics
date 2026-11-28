"""Offline Public SQLite backup, restore-validation, and schema-upgrade tools.

This module is deliberately not imported by the running API.  Operators invoke
it while following the deployment runbook, against an absolute database path
outside the source tree.  It never enables Public battle routes and never
overwrites a restore destination.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
from typing import Literal
from urllib.parse import quote

from .progression import (
    PUBLIC_BATTLE_SCHEMA_REVISION,
    PUBLIC_SCHEMA_VERSION,
    ProgressionStore,
    ProgressionStoreError,
)
from .telemetry_store import (
    TELEMETRY_SCHEMA_REVISION,
    TelemetrySchemaError,
    create_telemetry_schema,
    validate_telemetry_schema,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BACKUP_KINDS = ("daily", "release")
_SAFE_LABEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")


class PublicDatabaseOperationError(RuntimeError):
    """A safe offline database operation could not be completed."""


@dataclass(frozen=True)
class PublicDatabaseEvidence:
    path: str
    sha256: str
    size_bytes: int
    schema_version: int
    battle_schema_revision: int | None
    telemetry_schema_revision: int | None
    integrity: str


@dataclass(frozen=True)
class BackupEvidence:
    kind: str
    backup: PublicDatabaseEvidence
    manifest_path: str
    removed_daily_backups: tuple[str, ...]


@dataclass(frozen=True)
class UpgradeEvidence:
    database: PublicDatabaseEvidence
    pre_upgrade_backup: BackupEvidence


@dataclass(frozen=True)
class TelemetryUpgradeEvidence:
    database: PublicDatabaseEvidence
    pre_upgrade_backup: BackupEvidence | None
    already_upgraded: bool


def _absolute_external_path(path: Path, *, description: str) -> Path:
    if not path.is_absolute():
        raise PublicDatabaseOperationError(f"{description} path must be absolute.")
    resolved = path.resolve(strict=False)
    if resolved == REPOSITORY_ROOT or REPOSITORY_ROOT in resolved.parents:
        raise PublicDatabaseOperationError(
            f"{description} must be outside the repository and release artifacts."
        )
    return resolved


def _existing_database(path: Path, *, description: str) -> Path:
    resolved = _absolute_external_path(path, description=description)
    if not resolved.is_file():
        raise PublicDatabaseOperationError(f"{description} does not exist.")
    return resolved


def _connect_read_only(path: Path) -> sqlite3.Connection:
    uri = f"file:{quote(str(path))}?mode=ro"
    connection = sqlite3.connect(uri, uri=True, timeout=5.0)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_public_database(
    database_path: Path, *, require_batch2: bool = True
) -> PublicDatabaseEvidence:
    """Validate role, integrity, and schema without changing the database."""

    resolved = _existing_database(database_path, description="Public database")
    try:
        connection = _connect_read_only(resolved)
        try:
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                raise PublicDatabaseOperationError(
                    "Public database failed SQLite integrity_check."
                )
            metadata = {
                row["key"]: row["value"]
                for row in connection.execute("SELECT key, value FROM metadata")
            }
            if metadata.get("database_role") != "public":
                raise PublicDatabaseOperationError(
                    "Database is not marked for Public use."
                )
            if metadata.get("schema_version") != str(PUBLIC_SCHEMA_VERSION):
                raise PublicDatabaseOperationError(
                    "Public database schema version is unsupported."
                )
            revision_text = metadata.get("public_battle_schema_revision")
            try:
                revision = int(revision_text) if revision_text is not None else None
            except ValueError as exc:
                raise PublicDatabaseOperationError(
                    "Public battle schema revision is malformed."
                ) from exc
            telemetry_text = metadata.get("telemetry_schema_revision")
            try:
                telemetry_revision = (
                    int(telemetry_text) if telemetry_text is not None else None
                )
            except ValueError as exc:
                raise PublicDatabaseOperationError(
                    "Telemetry schema revision is malformed."
                ) from exc
        finally:
            connection.close()
        if require_batch2:
            try:
                ProgressionStore(resolved, public_mode=True).ensure_initialized()
            except ProgressionStoreError as exc:
                raise PublicDatabaseOperationError(str(exc)) from exc
        return PublicDatabaseEvidence(
            path=str(resolved),
            sha256=_digest(resolved),
            size_bytes=resolved.stat().st_size,
            schema_version=PUBLIC_SCHEMA_VERSION,
            battle_schema_revision=revision,
            telemetry_schema_revision=telemetry_revision,
            integrity=integrity,
        )
    except sqlite3.Error as exc:
        raise PublicDatabaseOperationError(
            "Public database could not be inspected safely."
        ) from exc


def _copy_with_sqlite_backup(source_path: Path, destination_path: Path) -> None:
    if destination_path.exists():
        raise PublicDatabaseOperationError(
            "Refusing to overwrite an existing backup or restore destination."
        )
    if not destination_path.parent.is_dir():
        raise PublicDatabaseOperationError("Destination directory does not exist.")
    try:
        descriptor = os.open(
            destination_path,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            0o600,
        )
        os.close(descriptor)
    except FileExistsError as exc:
        raise PublicDatabaseOperationError(
            "Refusing to overwrite an existing backup or restore destination."
        ) from exc
    source: sqlite3.Connection | None = None
    destination: sqlite3.Connection | None = None
    try:
        source = _connect_read_only(source_path)
        destination = sqlite3.connect(destination_path, timeout=5.0)
        source.backup(destination)
        destination.execute("PRAGMA foreign_keys = ON")
        destination.commit()
    except BaseException:
        if destination is not None:
            destination.close()
            destination = None
        destination_path.unlink(missing_ok=True)
        raise
    finally:
        if source is not None:
            source.close()
        if destination is not None:
            destination.close()
    os.chmod(destination_path, 0o600)


def _timestamp(value: datetime | None) -> str:
    instant = value or datetime.now(UTC)
    if instant.tzinfo is None:
        raise PublicDatabaseOperationError("Backup clock must be timezone-aware.")
    return instant.astimezone(UTC).strftime("%Y%m%dT%H%M%S.%fZ")


def _validate_label(label: str | None) -> str | None:
    if label is None:
        return None
    if not _SAFE_LABEL.fullmatch(label):
        raise PublicDatabaseOperationError(
            "Backup label must contain only letters, numbers, dot, underscore or dash."
        )
    return label


def _write_manifest(path: Path, evidence: PublicDatabaseEvidence, kind: str) -> Path:
    manifest = path.with_suffix(path.suffix + ".manifest.json")
    if manifest.exists():
        raise PublicDatabaseOperationError("Refusing to overwrite a backup manifest.")
    temporary = manifest.with_name(
        f".{manifest.name}.tmp-{os.getpid()}-{secrets.token_hex(4)}"
    )
    payload = (
        json.dumps(
            {"kind": kind, "database": asdict(evidence)},
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    descriptor = os.open(
        temporary,
        os.O_CREAT | os.O_EXCL | os.O_WRONLY,
        0o600,
    )
    try:
        with os.fdopen(descriptor, "wb") as destination:
            destination.write(payload)
            destination.flush()
            os.fsync(destination.fileno())
        # Hard-linking is an atomic no-overwrite publish on the same filesystem.
        os.link(temporary, manifest)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    temporary.unlink()
    return manifest


def _prune_daily(directory: Path, retain_daily: int) -> tuple[str, ...]:
    if retain_daily < 1:
        raise PublicDatabaseOperationError("Daily backup retention must be at least 1.")
    backups = sorted(directory.glob("public-daily-*.sqlite3"), reverse=True)
    removed: list[str] = []
    for old in backups[retain_daily:]:
        old.with_suffix(old.suffix + ".manifest.json").unlink(missing_ok=True)
        old.unlink()
        removed.append(str(old))
    return tuple(removed)


def backup_public_database(
    database_path: Path,
    backup_root: Path,
    *,
    kind: Literal["daily", "release"] = "daily",
    label: str | None = None,
    retain_daily: int = 7,
    now: datetime | None = None,
    require_batch2: bool = True,
) -> BackupEvidence:
    """Create and verify a consistent online backup using SQLite's backup API."""

    source = _existing_database(database_path, description="Public database")
    root = _absolute_external_path(backup_root, description="Backup root")
    if kind not in BACKUP_KINDS:
        raise PublicDatabaseOperationError("Backup kind must be daily or release.")
    validated_label = _validate_label(label)
    inspect_public_database(source, require_batch2=require_batch2)
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(root, 0o700)
    directory = root / kind
    directory.mkdir(mode=0o700, exist_ok=True)
    os.chmod(directory, 0o700)
    suffix = f"-{validated_label}" if validated_label else ""
    destination = directory / f"public-{kind}-{_timestamp(now)}{suffix}.sqlite3"
    try:
        _copy_with_sqlite_backup(source, destination)
        evidence = inspect_public_database(
            destination, require_batch2=require_batch2
        )
        manifest = _write_manifest(destination, evidence, kind)
        removed = _prune_daily(directory, retain_daily) if kind == "daily" else ()
        return BackupEvidence(
            kind=kind,
            backup=evidence,
            manifest_path=str(manifest),
            removed_daily_backups=removed,
        )
    except BaseException:
        destination.with_suffix(destination.suffix + ".manifest.json").unlink(
            missing_ok=True
        )
        destination.unlink(missing_ok=True)
        raise


def restore_public_database_for_validation(
    backup_path: Path,
    destination_path: Path,
    *,
    require_batch2: bool = True,
) -> PublicDatabaseEvidence:
    """Restore to a new isolated path and validate; never replace a live file."""

    source = _existing_database(backup_path, description="Public backup")
    destination = _absolute_external_path(
        destination_path, description="Restore destination"
    )
    if source == destination:
        raise PublicDatabaseOperationError(
            "Restore destination must differ from the backup."
        )
    _copy_with_sqlite_backup(source, destination)
    try:
        return inspect_public_database(
            destination, require_batch2=require_batch2
        )
    except BaseException:
        destination.unlink(missing_ok=True)
        raise


def _validate_batch1_public_shape(connection: sqlite3.Connection) -> None:
    metadata = {
        row["key"]: row["value"]
        for row in connection.execute("SELECT key, value FROM metadata")
    }
    if (
        metadata.get("schema_version") != str(PUBLIC_SCHEMA_VERSION)
        or metadata.get("database_role") != "public"
    ):
        raise PublicDatabaseOperationError(
            "Offline upgrade requires a Public schema-v5 database."
        )
    if "public_battle_schema_revision" in metadata:
        raise PublicDatabaseOperationError(
            "Database already has a Public battle schema marker; no upgrade applied."
        )
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        raise PublicDatabaseOperationError(
            "Public database failed SQLite integrity_check."
        )
    if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
        raise PublicDatabaseOperationError(
            "Public database failed its foreign-key check."
        )
    actual_signature = _schema_signature(connection)
    expected_signature = _batch1_reference_signature()
    if actual_signature != expected_signature:
        raise PublicDatabaseOperationError(
            "Database does not exactly match the supported Batch 1 Public-v5 schema."
        )


def _schema_signature(connection: sqlite3.Connection) -> tuple[tuple[str, str, str], ...]:
    """Return exact user-authored tables/indexes; include columns and constraints."""

    return tuple(
        (row["type"], row["name"], " ".join(row["sql"].split()))
        for row in connection.execute(
            """SELECT type, name, sql FROM sqlite_master
               WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%'
               ORDER BY type, name"""
        )
    )


def _batch1_reference_signature() -> tuple[tuple[str, str, str], ...]:
    """Build the supported Batch 1 shape from the authoritative schema builder."""

    reference = sqlite3.connect(":memory:")
    reference.row_factory = sqlite3.Row
    reference.execute("PRAGMA foreign_keys = ON")
    try:
        builder = ProgressionStore(
            Path("/nonexistent/reference.sqlite3"),
            public_mode=True,
            allow_public_initialize=True,
        )
        builder._create_schema(reference)
        builder._upgrade_empty_v4_to_public_v5(reference)
        reference.execute(
            "DELETE FROM metadata WHERE key = 'public_battle_schema_revision'"
        )
        reference.commit()
        return _schema_signature(reference)
    finally:
        reference.close()


def upgrade_batch1_public_v5(
    database_path: Path,
    backup_root: Path,
    *,
    confirm: bool = False,
    now: datetime | None = None,
) -> UpgradeEvidence:
    """Backup then transactionally add the Batch 2 battle schema offline."""

    if not confirm:
        raise PublicDatabaseOperationError(
            "Offline upgrade requires explicit confirm=True after stopping the API."
        )
    database = _existing_database(database_path, description="Public database")
    connection = _connect_read_only(database)
    try:
        _validate_batch1_public_shape(connection)
    finally:
        connection.close()
    backup = backup_public_database(
        database,
        backup_root,
        kind="release",
        label="pre-batch2-upgrade",
        now=now,
        require_batch2=False,
    )
    writable = sqlite3.connect(database, timeout=5.0)
    writable.row_factory = sqlite3.Row
    writable.execute("PRAGMA foreign_keys = ON")
    try:
        writable.execute("BEGIN IMMEDIATE")
        _validate_batch1_public_shape(writable)
        writable.execute(
            "INSERT INTO metadata(key, value) VALUES (?, ?)",
            ("public_battle_schema_revision", str(PUBLIC_BATTLE_SCHEMA_REVISION)),
        )
        _before_public_upgrade_commit(writable)
        writable.commit()
    except BaseException:
        writable.rollback()
        raise
    finally:
        writable.close()
    return UpgradeEvidence(
        database=inspect_public_database(database),
        pre_upgrade_backup=backup,
    )


def _before_public_upgrade_commit(connection: sqlite3.Connection) -> None:
    """Fault-injection seam; production intentionally performs no work here."""

    del connection


def upgrade_public_telemetry_v1(
    database_path: Path,
    backup_root: Path,
    *,
    confirm: bool = False,
    now: datetime | None = None,
) -> TelemetryUpgradeEvidence:
    """Backup then atomically add the optional telemetry sidecar offline.

    Re-running against a valid revision-1 sidecar is a read-only success.  A
    different or incomplete marker fails closed instead of attempting repair.
    """

    if not confirm:
        raise PublicDatabaseOperationError(
            "Offline telemetry upgrade requires explicit confirm=True after stopping the API."
        )
    database = _existing_database(database_path, description="Public database")
    before = inspect_public_database(database)
    if before.telemetry_schema_revision is not None:
        connection = _connect_read_only(database)
        try:
            validate_telemetry_schema(connection)
        except TelemetrySchemaError as exc:
            raise PublicDatabaseOperationError(str(exc)) from exc
        finally:
            connection.close()
        return TelemetryUpgradeEvidence(
            database=before,
            pre_upgrade_backup=None,
            already_upgraded=True,
        )

    backup = backup_public_database(
        database,
        backup_root,
        kind="release",
        label="pre-telemetry-v1-upgrade",
        now=now,
    )
    writable = sqlite3.connect(database, timeout=5.0)
    writable.row_factory = sqlite3.Row
    writable.execute("PRAGMA foreign_keys = ON")
    try:
        writable.execute("BEGIN IMMEDIATE")
        metadata = {
            row["key"]: row["value"]
            for row in writable.execute("SELECT key, value FROM metadata")
        }
        if metadata.get("schema_version") != str(PUBLIC_SCHEMA_VERSION):
            raise PublicDatabaseOperationError(
                "Telemetry upgrade requires a Public schema-v5 database."
            )
        if metadata.get("public_battle_schema_revision") != str(
            PUBLIC_BATTLE_SCHEMA_REVISION
        ):
            raise PublicDatabaseOperationError(
                "Telemetry upgrade requires Public battle schema revision 2."
            )
        create_telemetry_schema(writable)
        _before_telemetry_upgrade_commit(writable)
        writable.commit()
    except BaseException:
        writable.rollback()
        raise
    finally:
        writable.close()
    upgraded = inspect_public_database(database)
    if upgraded.telemetry_schema_revision != TELEMETRY_SCHEMA_REVISION:
        raise PublicDatabaseOperationError(
            "Telemetry upgrade did not produce the expected schema revision."
        )
    return TelemetryUpgradeEvidence(
        database=upgraded,
        pre_upgrade_backup=backup,
        already_upgraded=False,
    )


def _before_telemetry_upgrade_commit(connection: sqlite3.Connection) -> None:
    """Fault-injection seam; production intentionally performs no work here."""

    del connection


def _print_json(value: object) -> None:
    print(json.dumps(asdict(value), indent=2, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Offline Public SQLite backup and validation operations."
    )
    subparsers = parser.add_subparsers(dest="operation", required=True)
    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("--database", required=True, type=Path)
    backup_parser = subparsers.add_parser("backup")
    backup_parser.add_argument("--database", required=True, type=Path)
    backup_parser.add_argument("--backup-root", required=True, type=Path)
    backup_parser.add_argument("--kind", choices=BACKUP_KINDS, default="daily")
    backup_parser.add_argument("--label")
    backup_parser.add_argument("--retain-daily", type=int, default=7)
    restore_parser = subparsers.add_parser("restore-validate")
    restore_parser.add_argument("--backup", required=True, type=Path)
    restore_parser.add_argument("--destination", required=True, type=Path)
    upgrade_parser = subparsers.add_parser("upgrade-batch1-v5")
    upgrade_parser.add_argument("--database", required=True, type=Path)
    upgrade_parser.add_argument("--backup-root", required=True, type=Path)
    upgrade_parser.add_argument(
        "--confirm-offline-upgrade", action="store_true"
    )
    telemetry_parser = subparsers.add_parser("upgrade-telemetry-v1")
    telemetry_parser.add_argument("--database", required=True, type=Path)
    telemetry_parser.add_argument("--backup-root", required=True, type=Path)
    telemetry_parser.add_argument(
        "--confirm-offline-upgrade", action="store_true"
    )
    arguments = parser.parse_args()
    try:
        if arguments.operation == "inspect":
            _print_json(inspect_public_database(arguments.database))
        elif arguments.operation == "backup":
            _print_json(
                backup_public_database(
                    arguments.database,
                    arguments.backup_root,
                    kind=arguments.kind,
                    label=arguments.label,
                    retain_daily=arguments.retain_daily,
                )
            )
        elif arguments.operation == "restore-validate":
            _print_json(
                restore_public_database_for_validation(
                    arguments.backup, arguments.destination
                )
            )
        elif arguments.operation == "upgrade-batch1-v5":
            _print_json(
                upgrade_batch1_public_v5(
                    arguments.database,
                    arguments.backup_root,
                    confirm=arguments.confirm_offline_upgrade,
                )
            )
        else:
            _print_json(
                upgrade_public_telemetry_v1(
                    arguments.database,
                    arguments.backup_root,
                    confirm=arguments.confirm_offline_upgrade,
                )
            )
    except (OSError, sqlite3.Error, PublicDatabaseOperationError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
