"""Pure, UTC-only Pre-Alpha KPI calculations over captured telemetry facts.

This module never reconstructs a missing start, roster, or session from older
diagnostics. Callers must supply only post-cutover, server-accepted facts and
exclude exact internal-player IDs. Database loading/export is kept separate.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from statistics import median
from typing import Iterable, Literal


Outcome = Literal["victory", "defeat", "draw", "abandoned", "error", "unknown"]


@dataclass(frozen=True)
class PlayerFact:
    player_id: str
    created_at: datetime


@dataclass(frozen=True)
class BattleFact:
    battle_id: str
    player_id: str
    activated_at: datetime
    mode: str
    encounter_id: str
    team: tuple[str, ...] | None
    outcome: Outcome = "unknown"
    ended_at: datetime | None = None
    formation: str | None = None


@dataclass(frozen=True)
class VisitorObservation:
    visitor_id: str
    observed_at: datetime


@dataclass(frozen=True)
class SessionFact:
    session_id: str
    started_at: datetime


@dataclass(frozen=True)
class ClientErrorFact:
    session_id: str
    received_at: datetime


@dataclass(frozen=True)
class ApiRequestCounts:
    total: int
    failed: int


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("KPI timestamps must be timezone-aware")
    return value.astimezone(UTC)


def _in_period(value: datetime, start: datetime, end: datetime) -> bool:
    return start <= _utc(value) < end


def _metric(numerator: int, denominator: int) -> dict[str, int | float | None]:
    return {
        "numerator": numerator,
        "denominator": denominator,
        "value": numerator / denominator if denominator else None,
    }


def calculate_core_kpis(
    *,
    players: Iterable[PlayerFact],
    battles: Iterable[BattleFact],
    visitors: Iterable[VisitorObservation],
    sessions: Iterable[SessionFact],
    client_errors: Iterable[ClientErrorFact],
    api_requests: ApiRequestCounts,
    period_start: datetime,
    period_end: datetime,
    observed_until: datetime,
    telemetry_cutover: datetime,
    internal_player_ids: frozenset[str],
) -> dict[str, object]:
    """Return the twelve Marketing KPIs with explicit denominators/caveats.

    Windows are half-open: ``[start, start + seven days)`` and
    ``[defeat, defeat + 24 hours)``. Only matured windows enter denominators.
    D1/D7 use UTC calendar days and require the complete target day. A
    zero-denominator rate returns ``None`` rather than a fabricated zero.
    """
    start, end, now, cutover = map(
        _utc, (period_start, period_end, observed_until, telemetry_cutover)
    )
    if not (cutover <= start < end <= now):
        raise ValueError("KPI period must be post-cutover and fully observed")
    if api_requests.total < 0 or api_requests.failed < 0 or api_requests.failed > api_requests.total:
        raise ValueError("API request counters are inconsistent")

    eligible_players = {
        player.player_id: PlayerFact(player.player_id, _utc(player.created_at))
        for player in players
        if player.player_id not in internal_player_ids
    }
    starts = sorted(
        (
            BattleFact(
                battle_id=battle.battle_id,
                player_id=battle.player_id,
                activated_at=_utc(battle.activated_at),
                mode=battle.mode,
                encounter_id=battle.encounter_id,
                team=battle.team,
                outcome=battle.outcome,
                ended_at=_utc(battle.ended_at) if battle.ended_at else None,
                formation=battle.formation,
            )
            for battle in battles
            if battle.player_id in eligible_players
            and _utc(battle.activated_at) >= cutover
        ),
        key=lambda battle: (battle.activated_at, battle.battle_id),
    )
    by_player: dict[str, list[BattleFact]] = {}
    for battle in starts:
        by_player.setdefault(battle.player_id, []).append(battle)

    new_players = [player for player in eligible_players.values() if player.created_at >= cutover and _in_period(player.created_at, start, end)]
    mature_new = [player for player in new_players if player.created_at + timedelta(days=7) <= now]
    first_starts = {player_id: rows[0] for player_id, rows in by_player.items()}
    first_start_num = sum(
        1 for player in mature_new
        if (first := first_starts.get(player.player_id)) is not None
        and player.created_at <= first.activated_at < player.created_at + timedelta(days=7)
    )
    new_player_ids = {player.player_id for player in eligible_players.values() if player.created_at >= cutover}
    first_in_period = [
        battle for battle in first_starts.values()
        if battle.player_id in new_player_ids and _in_period(battle.activated_at, start, end)
    ]
    valid_outcomes = {"victory", "defeat", "draw"}
    first_completed = [
        battle for battle in first_in_period
        if battle.outcome in valid_outcomes and battle.ended_at is not None
    ]
    # Completion is a separate cohort from the first-start cohort: a battle
    # can start just before the reporting period and complete within it.
    completed_in_period = [
        battle for battle in first_starts.values()
        if battle.player_id in new_player_ids
        and battle.outcome in valid_outcomes and battle.ended_at is not None
        and _in_period(battle.ended_at, start, end)
    ]
    mature_completed = [
        battle for battle in completed_in_period
        if battle.ended_at is not None and battle.ended_at + timedelta(days=7) <= now
    ]
    second_start_num = sum(
        1 for battle in mature_completed
        if any(
            battle.ended_at < later.activated_at < battle.ended_at + timedelta(days=7)
            for later in by_player[battle.player_id][1:]
        )
    )

    period_starts = [battle for battle in starts if _in_period(battle.activated_at, start, end)]
    active_players = {battle.player_id for battle in period_starts}
    defeats = [
        battle for battle in starts
        if battle.outcome == "defeat" and battle.ended_at is not None
        and _in_period(battle.ended_at, start, end)
        and battle.ended_at + timedelta(hours=24) <= now
    ]
    retries = sum(
        1 for defeat in defeats
        if any(
            defeat.ended_at < later.activated_at < defeat.ended_at + timedelta(hours=24)
            and later.mode == defeat.mode
            and later.encounter_id == defeat.encounter_id
            for later in by_player[defeat.player_id]
        )
    )

    compositions: dict[tuple[str, str], set[tuple[str, ...]]] = {}
    for battle in period_starts:
        if battle.team is not None:
            compositions.setdefault((battle.player_id, battle.mode), set()).add(tuple(sorted(battle.team)))
    diversity_values = sorted(len(teams) for teams in compositions.values())
    switched = pairs = formation_only = 0
    for rows in by_player.values():
        per_mode: dict[str, list[BattleFact]] = {}
        for row in rows:
            per_mode.setdefault(row.mode, []).append(row)
        for same_mode in per_mode.values():
            for prior, current in zip(same_mode, same_mode[1:]):
                if not _in_period(current.activated_at, start, end):
                    continue
                if prior.team is None or current.team is None:
                    continue
                pairs += 1
                if sorted(prior.team) != sorted(current.team):
                    switched += 1
                elif prior.formation != current.formation:
                    formation_only += 1

    retention: dict[str, dict[str, int | float | None]] = {}
    for offset, label in ((1, "d1_retention"), (7, "d7_retention")):
        cohort = [
            battle for battle in first_in_period
            if datetime.combine(
                battle.activated_at.date() + timedelta(days=offset + 1),
                datetime.min.time(), tzinfo=UTC,
            ) <= now
        ]
        returning = sum(
            1 for first in cohort
            if any(
                later.activated_at.date() == first.activated_at.date() + timedelta(days=offset)
                for later in by_player[first.player_id][1:]
            )
        )
        retention[label] = _metric(returning, len(cohort))

    observed_sessions = {
        session.session_id for session in sessions if _in_period(session.started_at, start, end)
    }
    error_sessions = {
        error.session_id for error in client_errors
        if error.session_id in observed_sessions and _in_period(error.received_at, start, end)
    }
    battle_errors = sum(1 for battle in period_starts if battle.outcome == "error")
    return {
        "unique_visitors": len({
            visit.visitor_id for visit in visitors if _in_period(visit.observed_at, start, end)
        }),
        "new_players": len(new_players),
        "first_battle_start_rate": _metric(first_start_num, len(mature_new)),
        "first_battle_completion_rate": _metric(len(first_completed), len(first_in_period)),
        "second_battle_start_rate": _metric(second_start_num, len(mature_completed)),
        "average_battles_per_player": {
            "battles": len(period_starts),
            "players": len(active_players),
            "mean": len(period_starts) / len(active_players) if active_players else None,
            "median": median(
                [sum(1 for battle in period_starts if battle.player_id == player_id) for player_id in active_players]
            ) if active_players else None,
        },
        "retry_after_defeat_rate": _metric(retries, len(defeats)),
        "composition_diversity": {
            "player_mode_count": len(diversity_values),
            "median": median(diversity_values) if diversity_values else None,
            "distribution": diversity_values,
            "missing_team_starts": sum(1 for battle in period_starts if battle.team is None),
        },
        "team_switching_rate": {
            **_metric(switched, pairs), "formation_only_pairs": formation_only,
        },
        **retention,
        "technical_error_rate": {
            "api": _metric(api_requests.failed, api_requests.total),
            "battle": _metric(battle_errors, len(period_starts)),
            "client": _metric(len(error_sessions), len(observed_sessions)),
        },
    }
