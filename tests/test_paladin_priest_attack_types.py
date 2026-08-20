"""Owner-authorized Paladin/Priest attack classifications.

The table below is deliberately explicit: these are supplied values, not
inferences from skill names.  The tests also exercise formation legality at
the adapter boundary and the positional adjustment seam once per hit.
"""

import pytest

from battle_api.adapter import BattleAdapter
from heroes.hero import Hero


AUTHORIZED_ATTACK_TYPES = {
    "hero.paladin.retribution": {
        "Hammer of Anger": "ranged_projectile",
        "Crusader Strike": "melee",
    },
    "hero.paladin.protection": {
        "Hammer of Revenge": "ranged_instant",
        "Shield of Righteous": "melee",
        "Heroric Charge": "ranged_instant",
    },
    "hero.paladin.holy": {"Holy Blast": "ranged_projectile"},
    "hero.priest.comprehensiveness": {
        "Holy Smite": "ranged_instant",
        "Shadow Word Pain": "ranged_instant",
    },
    "hero.priest.discipline": {
        "Penance": "ranged_instant",
        "Holy Word Punishment": "ranged_instant",
    },
}


@pytest.mark.parametrize("definition_id", AUTHORIZED_ATTACK_TYPES)
def test_supplied_paladin_priest_attack_type_table_is_exact(definition_id):
    adapter = BattleAdapter()
    hero = adapter._create_team(
        [definition_id],
        ["classification-check"],
        group="Group_A",
        player_controlled=True,
        positions=("front",),
    )[0]
    actual = {skill.name: skill.attack_type for skill in hero.skills}
    assert {
        name: attack_type
        for name, attack_type in actual.items()
        if attack_type != "NA"
    } == AUTHORIZED_ATTACK_TYPES[definition_id]


def test_paladin_melee_legality_filters_rear_targets_in_three_vs_three():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        battle_size=3,
        player_team=["hero.paladin.retribution", "hero.priest.comprehensiveness", "hero.paladin.holy"],
        enemy_team=["hero.rogue.comprehensiveness"] * 3,
        player_formation="two-front-one-rear",
        enemy_formation="one-front-two-rear",
        seed=1921,
    )
    actor = session.game.player_heroes[0]
    skill = next(skill for skill in actor.skills if skill.name == "Crusader Strike")
    actions = adapter._legal_actions(session, actor)
    action = next(item for item in actions if item["skillId"] == adapter._skill_id(actor, skill))
    front, rear_a, rear_b = session.game.opponent_heroes
    assert action["validTargetIds"] == [adapter._combatant_id(session, front)]
    assert adapter._combatant_id(session, rear_a) not in action["validTargetIds"]
    assert adapter._combatant_id(session, rear_b) not in action["validTargetIds"]


@pytest.mark.parametrize(
    ("battle_size", "player_formation", "enemy_formation"),
    [
        (2, "front-rear", "front-rear"),
        (3, "two-front-one-rear", "one-front-two-rear"),
    ],
)
def test_paladin_priest_ranged_actions_reach_rear_targets_in_2v2_and_3v3(
    battle_size, player_formation, enemy_formation
):
    adapter = BattleAdapter()
    player_team = ["hero.paladin.retribution", "hero.priest.comprehensiveness"]
    enemy_team = ["hero.rogue.comprehensiveness"] * battle_size
    if battle_size == 3:
        player_team.append("hero.paladin.holy")
    session, _ = adapter.create_battle(
        battle_size=battle_size,
        player_team=player_team,
        enemy_team=enemy_team,
        player_formation=player_formation,
        enemy_formation=enemy_formation,
        seed=1922 + battle_size,
    )
    actor = session.game.player_heroes[0]
    skill = next(skill for skill in actor.skills if skill.name == "Hammer of Anger")
    action = next(
        item
        for item in adapter._legal_actions(session, actor)
        if item["skillId"] == adapter._skill_id(actor, skill)
    )
    assert len(action["validTargetIds"]) == battle_size


@pytest.mark.parametrize(
    ("attack_type", "attacker_position", "defender_position", "expected"),
    [
        ("melee", "rear", "front", 70),
        ("ranged_projectile", "rear", "front", 80),
        ("ranged_instant", "rear", "front", 100),
    ],
)
def test_paladin_priest_attack_classification_applies_one_position_modifier(
    attack_type, attacker_position, defender_position, expected
):
    attacker = object.__new__(Hero)
    defender = object.__new__(Hero)
    attacker.position = attacker_position
    defender.position = defender_position
    assert defender.take_damage_calculation(100, attack_type, attacker) == expected


def test_non_damage_skill_keeps_legacy_dispatch_without_attack_type_injection():
    calls = []

    def legacy_heal(target):
        calls.append(target)
        return "healed"

    from skills.skill import Skill

    skill = Skill(None, "Binding Heal", legacy_heal, "single", "healing")
    assert skill.execute("ally") == "healed"
    assert calls == ["ally"]


def test_holy_word_punishment_periodic_tick_has_no_attack_metadata():
    """Status ticks are not a fresh skill attack and must keep the old seam."""
    from skills.skill import Debuff

    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        battle_size=2,
        player_team=["hero.priest.discipline", "hero.paladin.holy"],
        enemy_team=["hero.rogue.comprehensiveness", "hero.paladin.retribution"],
        player_formation="front-rear",
        enemy_formation="front-rear",
        seed=1925,
    )
    source = session.game.player_heroes[0]
    target = session.game.opponent_heroes[0]
    target.status["holy_word_punishment"] = True
    target.add_debuff(Debuff("Holy Word Punishment", 2, source, 11))
    calls = []

    def capture(damage, *args, **kwargs):
        calls.append((damage, args, kwargs))
        return "captured"

    target.take_damage = capture
    session.game.status_manager.check_heroes_status_effects(target)

    assert len(calls) == 1
    assert calls[0][1:] == ((), {})
