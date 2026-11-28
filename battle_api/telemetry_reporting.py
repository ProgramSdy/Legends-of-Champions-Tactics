"""Restricted, read-only loading of post-cutover Public telemetry facts.

The battle outcome comes from canonical diagnostics, never from a second
telemetry outcome field. Missing sidecar facts remain missing; this loader does
not turn provisional RELEASE-004 diagnostics into historical battle starts.
"""

from __future__ import annotations

from datetime import UTC, datetime
import json
import sqlite3
from typing import Any

from .telemetry_kpis import (
    ApiRequestCounts,
    BattleFact,
    ClientErrorFact,
    PlayerFact,
    SessionFact,
    VisitorObservation,
    calculate_core_kpis,
)


def _time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Telemetry timestamp lacks a timezone")
    return parsed.astimezone(UTC)


def _classify_outcome(outcome_json: str | None, terminal_reason: str | None) -> str:
    if terminal_reason in {"serverRestart", "engineError", "settlementError"}:
        return "error"
    if not outcome_json:
        return "unknown"
    try:
        outcome = json.loads(outcome_json)
    except (TypeError, ValueError):
        return "error"
    if not isinstance(outcome, dict):
        return "error"
    kind = outcome.get("kind")
    if kind == "victory":
        side = outcome.get("winningSideId")
        if side == "friendly":
            return "victory"
        if side == "hostile":
            return "defeat"
        return "unknown"
    if kind == "draw":
        return "draw"
    if kind == "abandoned":
        return "abandoned"
    return "error" if kind == "error" else "unknown"


def load_core_kpi_facts(connection: sqlite3.Connection) -> dict[str, Any]:
    """Read only allowlisted analytical fields from a migrated SQLite copy."""

    connection.row_factory = sqlite3.Row
    players = [
        PlayerFact(row["player_id"], _time(row["created_at"]))
        for row in connection.execute("SELECT player_id, created_at FROM players")
    ]
    battles: list[BattleFact] = []
    for row in connection.execute(
        """SELECT t.battle_id, t.player_id, t.activated_at, t.mode,
                  t.encounter_id, t.player_team_json, t.player_formation,
                  d.outcome, d.outcome_at, d.terminal_reason
           FROM telemetry_battles AS t
           JOIN battle_diagnostics AS d ON d.battle_id = t.battle_id"""
    ):
        team = json.loads(row["player_team_json"])
        if not isinstance(team, list) or not all(isinstance(hero, str) for hero in team):
            raise ValueError("Captured battle team is malformed")
        battles.append(
            BattleFact(
                battle_id=row["battle_id"],
                player_id=row["player_id"],
                activated_at=_time(row["activated_at"]),
                mode=row["mode"],
                encounter_id=row["encounter_id"],
                team=tuple(team),
                outcome=_classify_outcome(row["outcome"], row["terminal_reason"]),
                ended_at=_time(row["outcome_at"]) if row["outcome_at"] else None,
                formation=row["player_formation"],
            )
        )
    internal_ids = frozenset(
        row["player_id"]
        for row in connection.execute("SELECT player_id FROM telemetry_internal_accounts")
    )
    visitors = [
        VisitorObservation(row["visitor_id"], _time(row["timestamp_utc"]))
        for row in connection.execute(
            """SELECT e.visitor_id, e.timestamp_utc
               FROM telemetry_events AS e
               JOIN telemetry_visitors AS v ON v.visitor_id = e.visitor_id
               WHERE e.event_type = 'landing_view'
                 AND (v.linked_player_id IS NULL OR v.linked_player_id NOT IN
                      (SELECT player_id FROM telemetry_internal_accounts))"""
        )
    ]
    sessions = [
        SessionFact(row["session_id"], _time(row["started_at"]))
        for row in connection.execute(
            """SELECT session_id, started_at FROM telemetry_sessions
               WHERE player_id IS NULL OR player_id NOT IN
                     (SELECT player_id FROM telemetry_internal_accounts)"""
        )
    ]
    client_errors = [
        ClientErrorFact(row["session_id"], _time(row["timestamp_utc"]))
        for row in connection.execute(
            """SELECT session_id, timestamp_utc FROM telemetry_events
               WHERE event_type = 'client_error'"""
        )
    ]
    metric_table = connection.execute(
        """SELECT 1 FROM sqlite_master
           WHERE type = 'table' AND name = 'telemetry_api_metrics'"""
    ).fetchone()
    if metric_table is None:
        # A missing request denominator is reported as N/A, not zero failures.
        api_metrics = []
    else:
        api_metrics = [
            dict(row)
            for row in connection.execute(
                "SELECT bucket_utc, request_count, failed_count FROM telemetry_api_metrics"
            )
        ]
    return {
        "players": players,
        "battles": battles,
        "visitors": visitors,
        "sessions": sessions,
        "client_errors": client_errors,
        "internal_player_ids": internal_ids,
        "api_metrics": api_metrics,
    }


def calculate_sqlite_kpis(
    connection: sqlite3.Connection,
    *,
    period_start: datetime,
    period_end: datetime,
    observed_until: datetime,
    telemetry_cutover: datetime,
) -> dict[str, object]:
    facts = load_core_kpi_facts(connection)
    total = failed = 0
    for metric in facts["api_metrics"]:
        bucket = _time(metric["bucket_utc"])
        if period_start <= bucket < period_end:
            total += metric["request_count"]
            failed += metric["failed_count"]
    return calculate_core_kpis(
        players=facts["players"],
        battles=facts["battles"],
        visitors=facts["visitors"],
        sessions=facts["sessions"],
        client_errors=facts["client_errors"],
        api_requests=ApiRequestCounts(total=total, failed=failed),
        period_start=period_start,
        period_end=period_end,
        observed_until=observed_until,
        telemetry_cutover=telemetry_cutover,
        internal_player_ids=facts["internal_player_ids"],
    )
