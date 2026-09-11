"""Regression coverage for battle-size round caps and timeout outcomes."""

from __future__ import annotations

import pytest

from battle_api.adapter import BattleAdapter
from game.game import MAX_COMPLETED_ROUNDS_BY_BATTLE_SIZE


PLAYER_TEAM = [
    "hero.warrior.weapon_master",
    "hero.mage.comprehensiveness",
    "hero.priest.comprehensiveness",
]
ENEMY_TEAM = [
    "hero.rogue.comprehensiveness",
    "hero.warrior.defence",
    "hero.paladin.retribution",
]


def create_session(battle_size: int):
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=104,
        battle_id=f"battle.round-limit.{battle_size}",
        battle_size=battle_size,
        player_team=PLAYER_TEAM[:battle_size],
        enemy_team=ENEMY_TEAM[:battle_size],
        player_formation="front-rear" if battle_size == 2 else (
            "one-front-two-rear" if battle_size == 3 else None
        ),
        enemy_formation="front-rear" if battle_size == 2 else (
            "one-front-two-rear" if battle_size == 3 else None
        ),
    )
    return adapter, session


def timeout(adapter: BattleAdapter, session):
    session.game.round_counter = session.game.round_counter_max
    session.game.game_state = "game_over"
    return adapter.snapshot(session)["outcome"]


@pytest.mark.parametrize("battle_size, expected_limit", [(1, 9), (2, 13), (3, 15)])
def test_validated_battle_size_sets_the_authoritative_completed_round_limit(
    battle_size, expected_limit
):
    _adapter, session = create_session(battle_size)

    assert session.game.battle_size == battle_size
    assert session.game.round_counter_max == expected_limit
    assert MAX_COMPLETED_ROUNDS_BY_BATTLE_SIZE[battle_size] == expected_limit


def test_final_allowed_round_completes_without_starting_an_extra_round():
    _adapter, session = create_session(1)
    game = session.game

    game.round_counter = game.round_counter_max - 1
    game.end_round()
    assert game.round_counter == game.round_counter_max
    assert game.game_state == "round_start"

    game.end_round()
    assert game.round_counter == game.round_counter_max
    assert game.game_state == "game_over"


def test_final_round_emits_a_resolved_timeout_victory_event_and_snapshot():
    adapter, session = create_session(1)
    game = session.game
    actor = adapter._current_actor(game)
    assert actor is not None
    for hero, hp in zip(game.heroes, (100_000, 90_000)):
        hero.hp = hp
        hero.hp_max = 100_000
    game.round_counter = game.round_counter_max
    game.unactioned_sorted_heroes = [actor]
    snapshot = adapter.snapshot(session)
    action = snapshot["legalActions"][0]

    result = adapter.submit(
        session,
        {
            "type": "useSkill",
            "commandId": "cmd.final-round",
            "expectedRevision": session.revision,
            "actorId": snapshot["activeCombatantId"],
            "skillId": action["skillId"],
            "targetIds": action["validTargetIds"][: action["minimumTargets"]],
        },
    )

    ended = next(event for event in result["events"] if event["type"] == "battleEnded")
    assert ended["message"] == (
        "Round limit reached. friendly won the battle by the timeout hierarchy."
    )
    assert result["snapshot"]["outcome"] == {
        "kind": "victory",
        "winningSideId": "friendly",
    }


def test_elimination_takes_precedence_over_timeout_hierarchy():
    adapter, session = create_session(1)
    session.game.opponent_heroes[0].hp = 0

    assert timeout(adapter, session) == {
        "kind": "victory",
        "winningSideId": "friendly",
    }


def test_timeout_more_living_heroes_wins_before_hp_comparison():
    adapter, session = create_session(2)
    for hero in session.game.player_heroes:
        hero.hp = 1
    session.game.opponent_heroes[0].hp = 1
    session.game.opponent_heroes[1].hp = 0

    assert timeout(adapter, session) == {
        "kind": "victory",
        "winningSideId": "friendly",
    }


def test_timeout_compares_exact_average_living_hp_percent_not_raw_hp():
    adapter, session = create_session(1)
    friendly = session.game.player_heroes[0]
    enemy = session.game.opponent_heroes[0]
    friendly.hp, friendly.hp_max = 45, 100
    enemy.hp, enemy.hp_max = 70, 200

    assert timeout(adapter, session) == {
        "kind": "victory",
        "winningSideId": "friendly",
    }
    assert "timeout hierarchy" in adapter._outcome_message(session.game)


def test_timeout_selects_enemy_on_higher_exact_average_living_hp_percent():
    adapter, session = create_session(1)
    friendly = session.game.player_heroes[0]
    enemy = session.game.opponent_heroes[0]
    friendly.hp, friendly.hp_max = 40, 100
    enemy.hp, enemy.hp_max = 90, 200

    assert timeout(adapter, session) == {
        "kind": "victory",
        "winningSideId": "enemy",
    }


def test_timeout_exact_average_living_hp_percent_is_a_draw():
    adapter, session = create_session(1)
    friendly = session.game.player_heroes[0]
    enemy = session.game.opponent_heroes[0]
    friendly.hp, friendly.hp_max = 50, 100
    enemy.hp, enemy.hp_max = 100, 200

    assert timeout(adapter, session) == {"kind": "draw", "winningSideId": None}
    assert adapter._outcome_message(session.game) == (
        "Round limit reached. The battle ended in an exact draw."
    )


def test_simultaneous_elimination_is_a_draw_even_at_the_timeout_boundary():
    adapter, session = create_session(1)
    session.game.player_heroes[0].hp = 0
    session.game.opponent_heroes[0].hp = 0

    assert timeout(adapter, session) == {"kind": "draw", "winningSideId": None}
