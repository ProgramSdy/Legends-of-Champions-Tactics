import csv
import os
import sqlite3
import stat
from datetime import UTC, datetime, timedelta

import pytest

from battle_api.progression import ProgressionStore
from battle_api.telemetry_ops import (
    TelemetryOperationError,
    classify_internal_account,
    export_battles,
    prune_raw_telemetry,
)
from battle_api.telemetry_store import create_telemetry_schema


NOW = datetime(2026, 11, 28, 12, tzinfo=UTC)


def make_database(tmp_path):
    database = tmp_path / "public.sqlite3"
    progression = ProgressionStore(database, public_mode=True, allow_public_initialize=True)
    progression.ensure_initialized()
    connection = sqlite3.connect(database)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("INSERT INTO players VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       ("player-1", "Test_Player_1", b"mac", 1, "2026-01-01T00:00:00Z", None, 1,
                        "2026-01-01T00:00:00Z"))
    connection.execute(
        "INSERT INTO battle_diagnostics VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("battle-1", "player-1", None, None, "launch", 1, "seed", "build", "2026-11-01T00:00:00Z",
         "2v2", "{}", None, None, None, None, "active", None, None, None),
    )
    create_telemetry_schema(connection)
    connection.execute(
        """INSERT INTO telemetry_battles(
          battle_id, player_id, activated_at, mode, encounter_id, stage_id, attempt_id,
          player_team_json, enemy_team_json, player_formation, enemy_formation,
          available_roster_json, control_mode, ruleset_version, completed_rounds)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("battle-1", "player-1", "2026-01-01T00:00:00Z", "tactics", "stage.1", "stage.1", "attempt-1",
         '["hero.a"]', '["hero.b"]', "front", "front", '["hero.a"]', "player", "rules", 1),
    )
    connection.execute(
        "UPDATE battle_diagnostics SET outcome=?, outcome_at=?, terminal_reason=? WHERE battle_id=?",
        ('{"kind":"victory","winningSideId":"friendly"}', "2026-11-01T00:01:00Z", None, "battle-1"),
    )
    connection.commit()
    connection.close()
    return database


def authorize_operator(monkeypatch):
    monkeypatch.setenv("LOCT_TELEMETRY_OPERATOR_UIDS", str(os.geteuid()))


def test_battle_export_is_private_allowlisted_and_never_includes_credentials(tmp_path, monkeypatch):
    database = make_database(tmp_path)
    output_dir = tmp_path / "exports"
    output_dir.mkdir(mode=0o700)
    output = output_dir / "battles.csv"
    authorize_operator(monkeypatch)

    assert export_battles(
        database_path=database, output_path=output, format_name="csv",
        period_start=datetime(2026, 1, 1, tzinfo=UTC), period_end=NOW,
    ) == 1
    assert stat.S_IMODE(output.stat().st_mode) == 0o600
    text = output.read_text()
    assert "recovery_mac" not in text
    assert "token_mac" not in text
    assert "battle-1" in text
    with output.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert set(rows[0]) == {
        "battle_id", "player_id", "activated_at", "mode", "encounter_id",
        "player_team_json", "enemy_team_json", "player_formation", "enemy_formation",
        "available_roster_json", "completed_rounds", "canonical_outcome_json",
        "canonical_outcome_at", "terminal_reason",
    }


def test_export_rejects_repository_or_non_private_destination(tmp_path, monkeypatch):
    database = make_database(tmp_path)
    authorize_operator(monkeypatch)
    public_dir = tmp_path / "public"
    public_dir.mkdir(mode=0o755)
    with pytest.raises(TelemetryOperationError, match="private"):
        export_battles(database_path=database, output_path=public_dir / "x.csv", format_name="csv",
                       period_start=NOW - timedelta(days=1), period_end=NOW)


def test_prune_is_bounded_and_only_removes_expired_telemetry(tmp_path, monkeypatch):
    database = make_database(tmp_path)
    authorize_operator(monkeypatch)
    connection = sqlite3.connect(database)
    connection.execute("INSERT INTO telemetry_visitors VALUES (?, ?, ?, ?, ?)",
                       ("visitor-old", "2026-01-01T00:00:00Z", "direct", None, None))
    connection.execute("INSERT INTO telemetry_visitors VALUES (?, ?, ?, ?, ?)",
                       ("visitor-new", NOW.isoformat(), "direct", None, None))
    connection.commit()
    connection.close()

    counts = prune_raw_telemetry(database_path=database, now=NOW, retention_days=90,
                                 batch_size=1, max_batches=1)
    assert counts["telemetry_visitors"] == 1
    assert counts["telemetry_battles"] == 1
    connection = sqlite3.connect(database)
    assert connection.execute("SELECT COUNT(*) FROM telemetry_visitors").fetchone()[0] == 1
    # Canonical identity and diagnostics are outside the retention operation.
    assert connection.execute("SELECT COUNT(*) FROM players").fetchone()[0] == 1
    assert connection.execute("SELECT COUNT(*) FROM battle_diagnostics").fetchone()[0] == 1
    connection.close()


def test_exact_internal_classification_is_restricted_idempotent_and_never_relabels(tmp_path, monkeypatch):
    database = make_database(tmp_path)
    with pytest.raises(TelemetryOperationError, match="not authorized"):
        classify_internal_account(database_path=database, player_id="player-1", classification="load_test")
    authorize_operator(monkeypatch)
    assert classify_internal_account(database_path=database, player_id="player-1", classification="load_test") is True
    assert classify_internal_account(database_path=database, player_id="player-1", classification="load_test") is False
    with pytest.raises(TelemetryOperationError, match="differs"):
        classify_internal_account(database_path=database, player_id="player-1", classification="owner_test")
    with pytest.raises(TelemetryOperationError, match="does not exist"):
        classify_internal_account(database_path=database, player_id="other", classification="load_test")
    connection = sqlite3.connect(database)
    assert connection.execute("SELECT classification FROM telemetry_internal_accounts").fetchall() == [("load_test",)]
    connection.close()
