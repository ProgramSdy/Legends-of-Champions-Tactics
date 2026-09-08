from __future__ import annotations

from battle_api.adapter import BattleAdapter


def _battle(player_team, enemy_team, *, enemy_formation="front-rear"):
    session, _ = BattleAdapter().create_battle(
        battle_size=2,
        player_team=player_team,
        enemy_team=enemy_team,
        player_formation="front-rear",
        enemy_formation=enemy_formation,
        seed=2501,
    )
    return session.game.player_heroes[0], session.game.opponent_heroes


def _choose(actor):
    skill = actor.ai_choose_skill(actor.opponents, actor.allies)
    return skill, actor.ai_choose_target(skill, actor.opponents, actor.allies)


def _disable(actor, skill_name):
    next(skill for skill in actor.skills if skill.name == skill_name).if_cooldown = True


def test_defence_interrupts_a_reachable_active_caster():
    actor, enemies = _battle(
        ["hero.warrior.defence", "hero.mage.comprehensiveness"],
        ["hero.mage.comprehensiveness", "hero.paladin.protection"],
    )
    enemies[0].status["magic_casting"] = True

    skill, target = _choose(actor)

    assert skill.name == "Shield Bash"
    assert target is enemies[0]


def test_defence_uses_thunder_pot_to_control_two_live_high_threat_enemies():
    actor, enemies = _battle(
        ["hero.warrior.defence", "hero.mage.comprehensiveness"],
        ["hero.mage.comprehensiveness", "hero.rogue.comprehensiveness"],
    )

    skill, targets = _choose(actor)

    assert skill.name == "Thunder Pot"
    assert targets == enemies


def test_defence_devastates_high_defence_target_when_control_skills_are_unavailable():
    actor, enemies = _battle(
        ["hero.warrior.defence", "hero.mage.comprehensiveness"],
        ["hero.paladin.protection", "hero.mage.comprehensiveness"],
        enemy_formation="side-by-side",
    )
    _disable(actor, "Shield Bash")
    _disable(actor, "Thunder Pot")

    skill, target = _choose(actor)

    assert skill.name == "Devastate"
    assert target is enemies[0]


def test_berserker_interrupts_a_reachable_active_caster_with_meteorite():
    actor, enemies = _battle(
        ["hero.warrior.berserker", "hero.mage.comprehensiveness"],
        ["hero.mage.comprehensiveness", "hero.paladin.protection"],
    )
    enemies[0].status["magic_casting"] = True

    skill, target = _choose(actor)

    assert skill.name == "Strike of Meteorite"
    assert target is enemies[0]


def test_berserker_moon_slash_prioritises_armor_broken_target_across_formation():
    actor, enemies = _battle(
        ["hero.warrior.berserker", "hero.mage.comprehensiveness"],
        ["hero.paladin.protection", "hero.rogue.comprehensiveness"],
    )
    enemies[1].status["armor_breaker"] = True

    skill, targets = _choose(actor)

    assert skill.name == "Moon Slash"
    assert targets == [enemies[1], enemies[0]]


def test_berserker_establishes_warlust_before_a_multi_enemy_engagement():
    actor, _enemies = _battle(
        ["hero.warrior.berserker", "hero.mage.comprehensiveness"],
        ["hero.paladin.protection", "hero.rogue.comprehensiveness"],
    )

    skill, target = _choose(actor)

    assert skill.name == "Warlust"
    assert target is None


def test_berserker_meteorite_respects_front_rear_melee_legality():
    actor, enemies = _battle(
        ["hero.warrior.berserker", "hero.mage.comprehensiveness"],
        ["hero.paladin.protection", "hero.rogue.comprehensiveness"],
    )
    _disable(actor, "Warlust")
    enemies[1].hp = 1

    skill, target = _choose(actor)

    assert skill.name == "Strike of Meteorite"
    assert target is enemies[0]
