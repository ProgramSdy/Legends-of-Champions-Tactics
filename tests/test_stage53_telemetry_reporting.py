import json
import sqlite3

import pytest

from battle_api.telemetry_reporting import load_core_kpi_facts
from battle_api.telemetry_store import create_telemetry_schema
from tests.test_stage53_telemetry_ops import make_database


def add_battle_fact(database, battle_id, outcome, terminal_reason=None):
    connection = sqlite3.connect(database)
    connection.execute(
        "INSERT INTO battle_diagnostics VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (battle_id, "player-1", None, None, "launch", 1, "seed", "build", "2026-11-02T00:00:00Z",
         "2v2", "{}", None, None, outcome, "2026-11-02T00:01:00Z",
         "settled", terminal_reason, None, None),
    )
    connection.execute(
        """INSERT INTO telemetry_battles(
          battle_id, player_id, activated_at, mode, encounter_id, stage_id, attempt_id,
          player_team_json, enemy_team_json, player_formation, enemy_formation,
          available_roster_json, control_mode, ruleset_version, completed_rounds)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (battle_id, "player-1", "2026-11-02T00:00:00Z", "tactics", "stage.1", None, None,
         '["hero.a"]', '["hero.b"]', None, None, '["hero.a"]', "player", "rules", 1),
    )
    connection.commit()
    connection.close()


def test_reporting_joins_canonical_outcome_and_does_not_use_telemetry_duplicate(tmp_path):
    database = make_database(tmp_path)
    add_battle_fact(database, "battle-victory", '{"kind":"victory","winningSideId":"friendly"}')
    add_battle_fact(database, "battle-defeat", '{"kind":"victory","winningSideId":"hostile"}')
    add_battle_fact(database, "battle-draw", '{"kind":"draw"}')
    connection = sqlite3.connect(database)
    facts = load_core_kpi_facts(connection)
    outcomes = {battle.battle_id: battle.outcome for battle in facts["battles"]}
    assert outcomes["battle-victory"] == "victory"
    assert outcomes["battle-defeat"] == "defeat"
    assert outcomes["battle-draw"] == "draw"
    connection.close()


def test_reporting_rejects_malformed_captured_team(tmp_path):
    database = make_database(tmp_path)
    connection = sqlite3.connect(database)
    connection.execute("UPDATE telemetry_battles SET player_team_json=?", (json.dumps({"not": "a list"}),))
    connection.commit()
    with pytest.raises(ValueError, match="malformed"):
        load_core_kpi_facts(connection)
    connection.close()


def test_reporting_excludes_linked_internal_visitor_and_analytics_session(tmp_path):
    database = make_database(tmp_path)
    connection = sqlite3.connect(database)
    connection.execute(
        "INSERT INTO telemetry_internal_accounts VALUES (?, ?, ?)",
        ("player-1", "load_test", "2026-11-01T00:00:00Z"),
    )
    connection.execute(
        "INSERT INTO telemetry_visitors VALUES (?, ?, ?, ?, ?)",
        ("visitor-internal", "2026-11-01T00:00:00Z", "direct", None, "player-1"),
    )
    connection.execute(
        "INSERT INTO telemetry_sessions VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("session-internal", "visitor-internal", "player-1", "2026-11-01T00:00:00Z",
         "2026-11-01T00:00:00Z", "direct", "test", "public"),
    )
    connection.execute(
        """INSERT INTO telemetry_events(
          event_id, event_type, schema_version, timestamp_utc, occurred_at_utc,
          player_id, visitor_id, session_id, battle_id, producer, environment,
          game_version, event_data_json)
          VALUES (?, 'landing_view', 1, ?, NULL, ?, ?, ?, NULL, 'ui', 'public', 'test', '{}')""",
        ("event-internal", "2026-11-01T00:00:00Z", "player-1", "visitor-internal", "session-internal"),
    )
    connection.commit()
    facts = load_core_kpi_facts(connection)
    assert facts["internal_player_ids"] == frozenset({"player-1"})
    assert facts["visitors"] == []
    assert facts["sessions"] == []
    connection.close()
