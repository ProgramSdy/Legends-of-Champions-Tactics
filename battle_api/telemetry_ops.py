"""Owner/operator-only telemetry export and bounded retention operations.

This is an offline CLI, never an HTTP route. It uses only allowlisted query
projections, refuses repository paths and public output directories, and
requires the invoking Unix UID in an explicit operator allowlist. It does not
modify canonical player, save, progression, or battle tables.
"""

from __future__ import annotations

import argparse
import csv
from datetime import UTC, datetime, timedelta
import json
import os
from pathlib import Path
import sqlite3
import stat
from typing import Any, Iterable
from urllib.parse import quote

from .telemetry_reporting import calculate_sqlite_kpis
from .telemetry_store import validate_telemetry_schema


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EXPORT_LIMIT = 100_000
PRUNE_BATCH_LIMIT = 1000
PRUNE_BATCHES_LIMIT = 100


class TelemetryOperationError(RuntimeError):
    """A restricted telemetry operation did not pass its safety gate."""


def _external_absolute(path: Path, *, description: str) -> Path:
    if not path.is_absolute():
        raise TelemetryOperationError(f"{description} must be an absolute path.")
    resolved = path.resolve(strict=False)
    if resolved == REPOSITORY_ROOT or REPOSITORY_ROOT in resolved.parents:
        raise TelemetryOperationError(f"{description} must be outside the repository.")
    return resolved


def _authorize_operator() -> None:
    configured = os.environ.get("LOCT_TELEMETRY_OPERATOR_UIDS", "")
    allowed = {value.strip() for value in configured.split(",") if value.strip().isdecimal()}
    if str(os.geteuid()) not in allowed:
        raise TelemetryOperationError("Telemetry operator UID is not authorized.")


def _open_database(path: Path, *, writable: bool) -> sqlite3.Connection:
    database = _external_absolute(path, description="Telemetry database")
    if not database.is_file():
        raise TelemetryOperationError("Telemetry database does not exist.")
    mode = "rw" if writable else "ro"
    uri = f"file:{quote(str(database))}?mode={mode}"
    connection = sqlite3.connect(uri, uri=True, timeout=0.25)
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 250")
        if not writable:
            connection.execute("PRAGMA query_only = ON")
        validate_telemetry_schema(connection)
        return connection
    except BaseException:
        connection.close()
        raise


def _private_output(path: Path) -> Path:
    if path.is_symlink():
        raise TelemetryOperationError("Export destination must not be a symlink.")
    output = _external_absolute(path, description="Telemetry export")
    parent = output.parent
    if not parent.is_dir():
        raise TelemetryOperationError("Export directory does not exist.")
    metadata = parent.stat()
    if metadata.st_uid != os.geteuid() or stat.S_IMODE(metadata.st_mode) & 0o077:
        raise TelemetryOperationError("Export directory must be owned by the operator and private (0700).")
    if output.exists() or output.is_symlink():
        raise TelemetryOperationError("Refusing to overwrite an existing export.")
    return output


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise TelemetryOperationError("Timestamp must be ISO 8601 with UTC offset.") from exc
    if parsed.tzinfo is None:
        raise TelemetryOperationError("Timestamp must have a timezone offset.")
    return parsed.astimezone(UTC)


def _stamp(value: datetime) -> str:
    if value.tzinfo is None:
        raise TelemetryOperationError("Timestamp must have a timezone offset.")
    return value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def _export_rows(
    output: Path, *, format_name: str, columns: tuple[str, ...], rows: Iterable[tuple[Any, ...]],
    sql_table: str,
) -> int:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(output, flags, 0o600)
    written = 0
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
            if format_name == "csv":
                writer = csv.writer(stream)
                writer.writerow(columns)
                for row in rows:
                    written += 1
                    if written > EXPORT_LIMIT:
                        raise TelemetryOperationError("Export row limit exceeded.")
                    writer.writerow(row)
            else:
                definitions = ", ".join(f'"{name}" TEXT' for name in columns)
                stream.write(f'CREATE TABLE "{sql_table}" ({definitions});\n')
                column_sql = ", ".join(f'"{name}"' for name in columns)
                for row in rows:
                    written += 1
                    if written > EXPORT_LIMIT:
                        raise TelemetryOperationError("Export row limit exceeded.")
                    values_sql = ", ".join(_sql_literal(value) for value in row)
                    stream.write(
                        f'INSERT INTO "{sql_table}" ({column_sql}) VALUES ({values_sql});\n'
                    )
        os.chmod(output, 0o600)
        return written
    except BaseException:
        output.unlink(missing_ok=True)
        raise


def export_kpis(
    *, database_path: Path, output_path: Path, format_name: str,
    period_start: datetime, period_end: datetime, observed_until: datetime,
    telemetry_cutover: datetime,
) -> int:
    """Export only aggregate KPI rows; no credentials or free text."""
    _authorize_operator()
    if format_name not in {"csv", "sql"}:
        raise TelemetryOperationError("Export format must be csv or sql.")
    output = _private_output(output_path)
    connection = _open_database(database_path, writable=False)
    try:
        report = calculate_sqlite_kpis(
            connection, period_start=period_start, period_end=period_end,
            observed_until=observed_until, telemetry_cutover=telemetry_cutover,
        )
    finally:
        connection.close()
    columns = ("metric", "numerator", "denominator", "value", "details_json")
    rows: list[tuple[Any, ...]] = []
    for name, value in report.items():
        if isinstance(value, dict):
            numerator = value.get("numerator")
            denominator = value.get("denominator")
            numeric = value.get("value")
            details = {key: item for key, item in value.items() if key not in {"numerator", "denominator", "value"}}
        else:
            numerator = denominator = None
            numeric = value
            details = {}
        rows.append((name, numerator, denominator, numeric, json.dumps(details, sort_keys=True)))
    return _export_rows(output, format_name=format_name, columns=columns, rows=rows,
                        sql_table="telemetry_kpi_export")


def export_battles(
    *, database_path: Path, output_path: Path, format_name: str,
    period_start: datetime, period_end: datetime,
) -> int:
    """Export an allowlisted pseudonymous battle projection for restricted analysis."""
    _authorize_operator()
    if format_name not in {"csv", "sql"}:
        raise TelemetryOperationError("Export format must be csv or sql.")
    output = _private_output(output_path)
    connection = _open_database(database_path, writable=False)
    try:
        columns = (
            "battle_id", "player_id", "activated_at", "mode", "encounter_id",
            "player_team_json", "enemy_team_json", "player_formation",
            "enemy_formation", "available_roster_json", "completed_rounds",
            "canonical_outcome_json", "canonical_outcome_at", "terminal_reason",
        )
        cursor = connection.execute(
            """SELECT t.battle_id, t.player_id, t.activated_at, t.mode,
                      t.encounter_id, t.player_team_json, t.enemy_team_json,
                      t.player_formation, t.enemy_formation,
                      t.available_roster_json, t.completed_rounds,
                      d.outcome, d.outcome_at, d.terminal_reason
               FROM telemetry_battles AS t
               JOIN battle_diagnostics AS d ON d.battle_id = t.battle_id
               WHERE t.activated_at >= ? AND t.activated_at < ?
               ORDER BY t.activated_at, t.battle_id LIMIT ?""",
            (_stamp(period_start), _stamp(period_end), EXPORT_LIMIT + 1),
        )
        return _export_rows(
            output, format_name=format_name, columns=columns,
            rows=(tuple(row) for row in cursor), sql_table="telemetry_battle_export",
        )
    finally:
        connection.close()


def prune_raw_telemetry(
    *, database_path: Path, now: datetime, retention_days: int = 90,
    batch_size: int = 500, max_batches: int = 10,
) -> dict[str, int]:
    """Bounded deletion of telemetry tables only; never canonical player data."""
    _authorize_operator()
    if not (1 <= retention_days <= 3650):
        raise TelemetryOperationError("Retention days must be between 1 and 3650.")
    if not (1 <= batch_size <= PRUNE_BATCH_LIMIT and 1 <= max_batches <= PRUNE_BATCHES_LIMIT):
        raise TelemetryOperationError("Prune batch limits are invalid.")
    if now.tzinfo is None:
        raise TelemetryOperationError("Retention clock must be timezone-aware.")
    cutoff = _stamp(now - timedelta(days=retention_days))
    connection = _open_database(database_path, writable=True)
    counts = {table: 0 for table in (
        "telemetry_events", "telemetry_sessions", "telemetry_visitors",
        "telemetry_battles", "telemetry_api_metrics",
    )}
    # Each batch is its own short transaction. Static table/column names only.
    statements = (
        ("telemetry_events", "event_id", "timestamp_utc", ""),
        ("telemetry_sessions", "session_id", "last_activity_at", ""),
        ("telemetry_visitors", "visitor_id", "first_seen_at",
         "AND NOT EXISTS (SELECT 1 FROM telemetry_sessions s WHERE s.visitor_id = telemetry_visitors.visitor_id)"),
        ("telemetry_battles", "battle_id", "activated_at", ""),
        ("telemetry_api_metrics", "rowid", "bucket_utc", ""),
    )
    try:
        for table, key, stamp, condition in statements:
            if table == "telemetry_api_metrics" and connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
            ).fetchone() is None:
                continue
            for _ in range(max_batches):
                connection.execute("BEGIN IMMEDIATE")
                try:
                    cursor = connection.execute(
                        f"DELETE FROM {table} WHERE {key} IN "
                        f"(SELECT {key} FROM {table} WHERE {stamp} < ? {condition} LIMIT ?)",
                        (cutoff, batch_size),
                    )
                    changed = cursor.rowcount
                    connection.commit()
                except BaseException:
                    connection.rollback()
                    raise
                counts[table] += changed
                if changed < batch_size:
                    break
        return counts
    finally:
        connection.close()


def classify_internal_account(
    *, database_path: Path, player_id: str, classification: str,
) -> bool:
    """Permanently exclude one exact, existing player ID from public cohorts.

    An existing different classification is never silently rewritten. Removing
    an exclusion would alter historical cohort reports and needs separate
    Owner review, so this deliberately has no generic undo operation.
    """
    _authorize_operator()
    if not player_id or len(player_id) > 128 or classification not in {
        "load_test", "owner_test", "automation"
    }:
        raise TelemetryOperationError("Internal-account classification is invalid.")
    connection = _open_database(database_path, writable=True)
    try:
        connection.execute("BEGIN IMMEDIATE")
        if connection.execute(
            "SELECT 1 FROM players WHERE player_id = ?", (player_id,)
        ).fetchone() is None:
            raise TelemetryOperationError("Player ID does not exist.")
        existing = connection.execute(
            "SELECT classification FROM telemetry_internal_accounts WHERE player_id = ?",
            (player_id,),
        ).fetchone()
        if existing is not None:
            if existing[0] != classification:
                raise TelemetryOperationError("Existing classification differs; Owner review required.")
            connection.commit()
            return False
        connection.execute(
            "INSERT INTO telemetry_internal_accounts(player_id, classification, created_at) "
            "VALUES (?, ?, ?)",
            (player_id, classification, _stamp(datetime.now(UTC))),
        )
        connection.commit()
        return True
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Restricted offline Pre-Alpha telemetry operations")
    parser.add_argument("operation", choices=("export-kpis", "export-battles", "prune", "classify-internal"))
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--format", choices=("csv", "sql"), default="csv")
    parser.add_argument("--period-start")
    parser.add_argument("--period-end")
    parser.add_argument("--observed-until")
    parser.add_argument("--cutover")
    parser.add_argument("--retention-days", type=int, default=90)
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--max-batches", type=int, default=10)
    parser.add_argument("--player-id")
    parser.add_argument("--classification", choices=("load_test", "owner_test", "automation"))
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    if not args.execute:
        raise TelemetryOperationError("Use --execute after reviewing paths and bounds.")
    if args.operation == "classify-internal":
        if args.player_id is None or args.classification is None:
            raise TelemetryOperationError("Classification requires exact player ID and class.")
        created = classify_internal_account(
            database_path=args.database, player_id=args.player_id,
            classification=args.classification,
        )
        print(json.dumps({"classification_recorded": created}, sort_keys=True))
        return 0
    if args.operation == "prune":
        result = prune_raw_telemetry(
            database_path=args.database, now=datetime.now(UTC),
            retention_days=args.retention_days, batch_size=args.batch_size,
            max_batches=args.max_batches,
        )
        print(json.dumps({"deleted_rows_by_telemetry_table": result}, sort_keys=True))
        return 0
    if args.output is None or args.period_start is None or args.period_end is None:
        raise TelemetryOperationError("Export requires output and period bounds.")
    start, end = _timestamp(args.period_start), _timestamp(args.period_end)
    if not start < end:
        raise TelemetryOperationError("Export period is invalid.")
    if args.operation == "export-battles":
        count = export_battles(
            database_path=args.database, output_path=args.output, format_name=args.format,
            period_start=start, period_end=end,
        )
    else:
        if args.cutover is None or args.observed_until is None:
            raise TelemetryOperationError("KPI export requires cutover and observed-until.")
        count = export_kpis(
            database_path=args.database, output_path=args.output, format_name=args.format,
            period_start=start, period_end=end,
            observed_until=_timestamp(args.observed_until),
            telemetry_cutover=_timestamp(args.cutover),
        )
    print(json.dumps({"exported_rows": count, "format": args.format}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
