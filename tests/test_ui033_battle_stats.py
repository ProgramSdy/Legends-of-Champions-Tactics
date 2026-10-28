from __future__ import annotations

from dataclasses import FrozenInstanceError
import random

import pytest
from pydantic import ValidationError

from battle_api.adapter import BattleAdapter
from battle_api.models import BattleCombatantStatValue
from heroes.summon_unit import SkeletonWarrior


STAT_NAMES = ("damage", "defence", "agility")
RESISTANCE_NAMES = (
    "fire",
    "frost",
    "arcane",
    "shadow",
    "death",
    "poison",
    "nature",
)


def _create_session(*, battle_size=1, player_team=None, enemy_team=None):
    adapter = BattleAdapter()
    kwargs = {
        "seed": 3301,
        "battle_id": f"battle.ui033.{battle_size}",
        "battle_size": battle_size,
        "player_team": player_team or ["hero.warrior.weapon_master"],
        "enemy_team": enemy_team or ["hero.rogue.comprehensiveness"],
        "enemy_control_mode": "player",
    }
    if battle_size == 2:
        kwargs.update(
            player_formation="side-by-side",
            enemy_formation="side-by-side",
        )
    session, _envelope = adapter.create_battle(**kwargs)
    return adapter, session


def test_snapshot_exposes_complete_neutral_stats_from_frozen_starting_baseline():
    adapter, session = _create_session()
    hero = session.game.player_heroes[0]
    combatant = adapter.snapshot(session)["combatants"][
        adapter._combatant_id(session, hero)
    ]

    assert set(combatant["stats"]) == {*STAT_NAMES, "resistances"}
    assert set(combatant["stats"]["resistances"]) == set(RESISTANCE_NAMES)
    assert combatant["stats"]["damage"] == {
        "current": hero.damage,
        "delta": 0,
    }
    assert combatant["stats"]["defence"] == {
        "current": hero.defense,
        "delta": 0,
    }
    assert combatant["stats"]["agility"] == {
        "current": hero.agility,
        "delta": 0,
    }
    with pytest.raises(FrozenInstanceError):
        hero.battle_stat_baseline.damage = 999


def test_snapshot_preserves_signed_fractional_deltas_without_display_rounding():
    adapter, session = _create_session()
    hero = session.game.player_heroes[0]
    changes = {
        "damage": 0.125,
        "defense": -2,
        "agility": 1.75,
        "fire_resistance": -0.375,
        "frost_resistance": 2.5,
        "arcane_resistance": -3,
        "shadow_resistance": 4.125,
        "death_resistance": -5.25,
        "poison_resistance": 6,
        "nature_resistance": 1.5,
    }
    for attribute, change in changes.items():
        setattr(hero, attribute, getattr(hero, attribute) + change)

    stats = adapter.snapshot(session)["combatants"][
        adapter._combatant_id(session, hero)
    ]["stats"]

    assert stats["damage"]["delta"] == pytest.approx(0.125)
    assert stats["defence"] == {"current": hero.defense, "delta": -2}
    assert stats["agility"]["delta"] == pytest.approx(1.75)
    expected_resistance_deltas = {
        "fire": -0.375,
        "frost": 2.5,
        "arcane": -3,
        "shadow": 4.125,
        "death": -5.25,
        "poison": 6,
        "nature": 1.5,
    }
    for resistance, expected in expected_resistance_deltas.items():
        assert stats["resistances"][resistance]["delta"] == pytest.approx(
            expected
        )


def test_overlapping_mutations_report_one_net_delta_without_effect_inference():
    adapter, session = _create_session()
    hero = session.game.player_heroes[0]
    hero.damage += 9.5
    hero.damage -= 3.25
    hero.status["warlust"] = True
    hero.status["hammer_of_revenge"] = True

    combatant = adapter.snapshot(session)["combatants"][
        adapter._combatant_id(session, hero)
    ]

    assert combatant["stats"]["damage"]["delta"] == pytest.approx(6.25)
    assert {status["id"] for status in combatant["statuses"]} >= {
        "status.warlust",
        "status.hammer_of_revenge",
    }


def test_repeated_definitions_keep_independent_instance_baselines():
    adapter, session = _create_session(
        battle_size=2,
        player_team=[
            "hero.warrior.weapon_master",
            "hero.warrior.weapon_master",
        ],
        enemy_team=[
            "hero.rogue.comprehensiveness",
            "hero.rogue.comprehensiveness",
        ],
    )
    first, second = session.game.player_heroes
    first.damage += 7
    second.agility -= 3

    combatants = adapter.snapshot(session)["combatants"]
    first_stats = combatants[adapter._combatant_id(session, first)]["stats"]
    second_stats = combatants[adapter._combatant_id(session, second)]["stats"]

    assert first.battle_stat_baseline is not second.battle_stat_baseline
    assert first_stats["damage"]["delta"] == 7
    assert first_stats["agility"]["delta"] == 0
    assert second_stats["damage"]["delta"] == 0
    assert second_stats["agility"]["delta"] == -3


def test_summon_uses_its_own_finalized_construction_baseline():
    adapter, session = _create_session()
    master = session.game.player_heroes[0]
    summon = SkeletonWarrior(
        adapter.engine_data,
        "UI-033 Skeleton",
        "Group_A",
        master,
        3,
        "undead",
    )
    summon.take_game_instance(session.game)
    session.game.player_heroes.append(summon)
    session.game.heroes.append(summon)
    starting_defence = summon.defense
    summon.defense -= 4

    combatant = adapter._serialize_combatant(session, summon)

    assert summon.battle_stat_baseline.defence == starting_defence
    assert combatant["isSummon"] is True
    assert combatant["stats"]["defence"] == {
        "current": starting_defence - 4,
        "delta": -4,
    }


def test_defeated_combatant_retains_read_only_stats():
    adapter, session = _create_session()
    hero = session.game.opponent_heroes[0]
    hero.damage += 2
    hero.hp = 0

    combatant = adapter.snapshot(session)["combatants"][
        adapter._combatant_id(session, hero)
    ]

    assert combatant["alive"] is False
    assert combatant["hp"]["current"] == 0
    assert combatant["stats"]["damage"]["delta"] == 2


def test_serializing_stats_consumes_no_rng_and_mutates_no_session_state():
    adapter, session = _create_session()
    session_state = session.rng_state
    global_state = random.getstate()
    revision = session.revision
    event_sequence = session.event_sequence
    command_results = dict(session.command_results)

    first = adapter.snapshot(session)
    second = adapter.snapshot(session)

    assert first == second
    assert session.rng_state == session_state
    assert random.getstate() == global_state
    assert session.revision == revision
    assert session.event_sequence == event_sequence
    assert session.command_results == command_results


@pytest.mark.parametrize("invalid", [True, float("nan"), float("inf")])
def test_typed_stat_value_rejects_non_numeric_or_non_finite_values(invalid):
    with pytest.raises(ValidationError):
        BattleCombatantStatValue(current=invalid, delta=0)
