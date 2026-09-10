from __future__ import annotations

from battle_api.adapter import BattleAdapter


def _battle(player_team, enemy_team, *, enemy_formation="front-rear"):
    session, _ = BattleAdapter().create_battle(
        battle_size=2,
        player_team=player_team,
        enemy_team=enemy_team,
        player_formation="front-rear",
        enemy_formation=enemy_formation,
        seed=2701,
    )
    return session.game.player_heroes[0], session.game.player_heroes, session.game.opponent_heroes


def _choose(actor):
    skill = actor.ai_choose_skill(actor.opponents, actor.allies)
    return skill, actor.ai_choose_target(skill, actor.opponents, actor.allies)


def test_retribution_saves_a_critical_ally_before_attacking():
    actor, allies, _enemies = _battle(
        ["hero.paladin.retribution", "hero.mage.comprehensiveness"],
        ["hero.mage.comprehensiveness", "hero.rogue.comprehensiveness"],
    )
    allies[1].hp = int(allies[1].hp_max * 0.25)

    skill, target = _choose(actor)

    assert skill.name == "Flash of Light"
    assert target is allies[1]


def test_retribution_finishes_soft_high_threat_before_emergency_healing():
    actor, allies, enemies = _battle(
        ["hero.paladin.retribution", "hero.mage.comprehensiveness"],
        ["hero.mage.comprehensiveness", "hero.warrior.defence"],
    )
    allies[1].hp = int(allies[1].hp_max * 0.25)
    enemies[0].hp = int(enemies[0].hp_max * 0.20)
    enemies[0].defense = actor.damage

    skill, target = _choose(actor)

    assert skill.name == "Hammer of Anger"
    assert target is enemies[0]


def test_retribution_builds_wrath_only_against_reachable_front_target():
    actor, _allies, enemies = _battle(
        ["hero.paladin.retribution", "hero.mage.comprehensiveness"],
        ["hero.mage.comprehensiveness", "hero.rogue.comprehensiveness"],
    )

    skill, target = _choose(actor)

    assert skill.name == "Crusader Strike"
    assert target is enemies[0]
    assert target.position == "front"


def test_retribution_uses_two_stack_flash_for_a_wounded_ally():
    actor, allies, _enemies = _battle(
        ["hero.paladin.retribution", "hero.mage.comprehensiveness"],
        ["hero.mage.comprehensiveness", "hero.rogue.comprehensiveness"],
    )
    actor.wrath_of_crusader_stacks = 2
    actor.wrath_of_crusader_duration = 3
    allies[1].hp = int(allies[1].hp_max * 0.50)

    skill, target = _choose(actor)

    assert skill.name == "Flash of Light"
    assert target is allies[1]


def test_retribution_uses_crusader_strike_against_an_armoured_frontliner():
    actor, _allies, enemies = _battle(
        ["hero.paladin.retribution", "hero.mage.comprehensiveness"],
        ["hero.paladin.protection", "hero.rogue.comprehensiveness"],
    )
    actor.wrath_of_crusader_stacks = 2
    actor.wrath_of_crusader_duration = 3
    enemies[0].defense = actor.damage + 20
    enemies[1].defense = actor.damage + 20

    skill, target = _choose(actor)

    assert skill.name == "Crusader Strike"
    assert target is enemies[0]


def test_protection_charge_interrupts_a_rear_caster_with_ranged_legality():
    actor, _allies, enemies = _battle(
        ["hero.paladin.protection", "hero.warrior.weapon_master"],
        ["hero.warrior.defence", "hero.mage.comprehensiveness"],
    )
    enemies[1].status["magic_casting"] = True

    skill, target = _choose(actor)

    assert skill.name == "Heroric Charge"
    assert target is enemies[1]
    assert target.position == "rear"


def test_protection_uses_hammer_of_revenge_aggressively_at_three_debuffs():
    actor, _allies, enemies = _battle(
        ["hero.paladin.protection", "hero.warrior.weapon_master"],
        ["hero.mage.comprehensiveness", "hero.rogue.comprehensiveness"],
    )
    actor.status["shadow_word_pain"] = True
    actor.status["poisoned_dagger"] = True
    actor.status["bleeding_moon_slash"] = True

    skill, target = _choose(actor)

    assert skill.name == "Hammer of Revenge"
    assert target is enemies[0]


def test_protection_shield_targets_front_when_melee_is_screened():
    actor, _allies, enemies = _battle(
        ["hero.paladin.protection", "hero.warrior.weapon_master"],
        ["hero.warrior.defence", "hero.mage.comprehensiveness"],
    )
    next(skill for skill in actor.skills if skill.name == "Heroric Charge").if_cooldown = True

    skill, target = _choose(actor)

    assert skill.name == "Shield of Righteous"
    assert target is enemies[0]
    assert target.position == "front"


def test_holy_protects_and_cleanses_itself_before_other_actions():
    actor, _allies, _enemies = _battle(
        ["hero.paladin.holy", "hero.warrior.weapon_master"],
        ["hero.mage.comprehensiveness", "hero.rogue.comprehensiveness"],
    )
    actor.status["poisoned_dagger"] = True

    skill, target = _choose(actor)

    assert skill.name == "Shield of Protection"
    assert target is None


def test_holy_uses_two_target_blast_when_team_is_stable():
    actor, _allies, enemies = _battle(
        ["hero.paladin.holy", "hero.warrior.weapon_master"],
        ["hero.mage.comprehensiveness", "hero.rogue.comprehensiveness"],
    )

    skill, targets = _choose(actor)

    assert skill.name == "Holy Blast"
    assert targets == enemies
