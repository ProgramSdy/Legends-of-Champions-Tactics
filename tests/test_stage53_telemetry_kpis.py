from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from battle_api.telemetry_kpis import (
    ApiRequestCounts,
    BattleFact,
    ClientErrorFact,
    PlayerFact,
    SessionFact,
    VisitorObservation,
    calculate_core_kpis,
)


BASE = datetime(2026, 1, 1, tzinfo=UTC)
PERIOD_END = BASE + timedelta(days=20)


def player(player_id: str, day: int) -> PlayerFact:
    return PlayerFact(player_id, BASE + timedelta(days=day))


def battle(
    battle_id: str,
    player_id: str,
    day: int,
    *,
    outcome: str = "victory",
    ended_day: int | None = None,
    encounter: str = "stage.1",
    team: tuple[str, ...] | None = ("hero.a",),
    mode: str = "learner",
    formation: str | None = "front",
) -> BattleFact:
    started = BASE + timedelta(days=day)
    ended = BASE + timedelta(days=ended_day) if ended_day is not None else None
    return BattleFact(
        battle_id=battle_id,
        player_id=player_id,
        activated_at=started,
        mode=mode,
        encounter_id=encounter,
        team=team,
        outcome=outcome,  # type: ignore[arg-type]
        ended_at=ended,
        formation=formation,
    )


def calculate(*, players, battles, visitors=(), sessions=(), client_errors=(), now=PERIOD_END, period_end=PERIOD_END):
    return calculate_core_kpis(
        players=players,
        battles=battles,
        visitors=visitors,
        sessions=sessions,
        client_errors=client_errors,
        api_requests=ApiRequestCounts(total=10, failed=2),
        period_start=BASE,
        period_end=period_end,
        observed_until=now,
        telemetry_cutover=BASE,
        internal_player_ids=frozenset({"internal"}),
    )


def test_exact_activation_completion_second_start_retry_and_internal_exclusion():
    players = [
        player("p1", 0),  # mature, first battle completes and second starts
        player("p2", 1),  # mature, first battle defeats and retries inside 24h
        player("p3", 14),  # included in new-player period but not yet mature
        player("internal", 0),  # never enters public denominators
    ]
    battles = [
        battle("p1-first", "p1", 2, ended_day=3),
        battle("p1-second", "p1", 5, team=("hero.b",)),
        replace(
            battle("p2-first", "p2", 3, outcome="defeat", ended_day=4),
            ended_at=BASE + timedelta(days=4, hours=-1),
        ),
        battle("p2-retry", "p2", 4, encounter="stage.1"),
        battle("p3-first", "p3", 15),
        battle("internal-first", "internal", 1),
    ]
    result = calculate(players=players, battles=battles)

    assert result["new_players"] == 3
    assert result["first_battle_start_rate"] == {"numerator": 2, "denominator": 2, "value": 1.0}
    assert result["first_battle_completion_rate"] == {"numerator": 2, "denominator": 3, "value": pytest.approx(2 / 3)}
    assert result["second_battle_start_rate"] == {"numerator": 2, "denominator": 2, "value": 1.0}
    assert result["retry_after_defeat_rate"] == {"numerator": 1, "denominator": 1, "value": 1.0}
    assert result["average_battles_per_player"]["players"] == 3
    assert result["average_battles_per_player"]["battles"] == 5


def test_retry_requires_same_encounter_and_strictly_less_than_24_hours():
    players = [player("p1", 0)]
    battles = [
        battle("first", "p1", 1, outcome="defeat", ended_day=2, encounter="stage.1"),
        battle("different", "p1", 2, encounter="stage.2"),
        battle("at-boundary", "p1", 3, encounter="stage.1"),
    ]
    result = calculate(players=players, battles=battles)
    assert result["retry_after_defeat_rate"] == {"numerator": 0, "denominator": 1, "value": 0.0}


def test_utc_d1_d7_need_complete_target_day_and_count_battle_starts():
    players = [player("p1", 0), player("p2", 0)]
    battles = [
        battle("p1-first", "p1", 0, ended_day=0),
        battle("p1-d1", "p1", 1),
        battle("p1-d7", "p1", 7),
        battle("p2-first", "p2", 0, ended_day=0),
        battle("p2-d1", "p2", 2),
    ]
    # At UTC day 7, D1 is mature; the UTC day-7 target for D7 is not complete.
    result = calculate(
        players=players,
        battles=battles,
        now=BASE + timedelta(days=7),
        period_end=BASE + timedelta(days=7),
    )
    assert result["d1_retention"] == {"numerator": 1, "denominator": 2, "value": 0.5}
    assert result["d7_retention"] == {"numerator": 0, "denominator": 0, "value": None}


def test_composition_uses_unordered_multisets_and_tracks_formation_only_changes():
    players = [player("p1", 0)]
    battles = [
        battle("one", "p1", 1, team=("hero.a", "hero.b"), formation="front-rear"),
        battle("two", "p1", 2, team=("hero.b", "hero.a"), formation="side-by-side"),
        battle("three", "p1", 3, team=("hero.a", "hero.c"), formation="side-by-side"),
    ]
    result = calculate(players=players, battles=battles)
    assert result["composition_diversity"]["distribution"] == [2]
    assert result["team_switching_rate"]["numerator"] == 1
    assert result["team_switching_rate"]["denominator"] == 2
    assert result["team_switching_rate"]["formation_only_pairs"] == 1


def test_zero_denominators_are_n_a_and_counters_must_be_consistent():
    result = calculate(players=[], battles=[])
    assert result["first_battle_start_rate"] == {"numerator": 0, "denominator": 0, "value": None}
    assert result["second_battle_start_rate"] == {"numerator": 0, "denominator": 0, "value": None}
    assert result["average_battles_per_player"]["mean"] is None
    with pytest.raises(ValueError, match="API request counters"):
        calculate_core_kpis(
            players=[], battles=[], visitors=[], sessions=[], client_errors=[],
            api_requests=ApiRequestCounts(total=1, failed=2), period_start=BASE,
            period_end=PERIOD_END, observed_until=PERIOD_END,
            telemetry_cutover=BASE, internal_player_ids=frozenset(),
        )


def test_existing_player_post_cutover_battles_count_without_new_player_cohort():
    result = calculate_core_kpis(
        players=[PlayerFact("existing", BASE - timedelta(days=30))],
        battles=[battle("post-cutover", "existing", 2, ended_day=3)],
        visitors=[], sessions=[], client_errors=[],
        api_requests=ApiRequestCounts(total=0, failed=0),
        period_start=BASE, period_end=PERIOD_END,
        observed_until=PERIOD_END, telemetry_cutover=BASE,
        internal_player_ids=frozenset(),
    )
    assert result["new_players"] == 0
    assert result["first_battle_start_rate"]["denominator"] == 0
    assert result["first_battle_completion_rate"]["denominator"] == 0
    assert result["average_battles_per_player"]["battles"] == 1


def test_visitor_and_client_error_rates_are_separate_from_api_and_battle_rates():
    result = calculate(
        players=[player("p1", 0)],
        battles=[battle("error", "p1", 1, outcome="error")],
        visitors=[VisitorObservation("v1", BASE + timedelta(days=1)), VisitorObservation("v1", BASE + timedelta(days=2))],
        sessions=[SessionFact("s1", BASE + timedelta(days=1)), SessionFact("s2", BASE + timedelta(days=1))],
        client_errors=[ClientErrorFact("s1", BASE + timedelta(days=2))],
    )
    assert result["unique_visitors"] == 1
    assert result["technical_error_rate"]["api"]["value"] == 0.2
    assert result["technical_error_rate"]["battle"] == {"numerator": 1, "denominator": 1, "value": 1.0}
    assert result["technical_error_rate"]["client"] == {"numerator": 1, "denominator": 2, "value": 0.5}
