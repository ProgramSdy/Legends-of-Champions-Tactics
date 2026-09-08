from __future__ import annotations

from battle_api.adapter import BattleAdapter


PLAYER_TEAM = [
    "hero.warrior.weapon_master",
    "hero.mage.comprehensiveness",
]
ENEMY_TEAM = [
    "hero.paladin.protection",
    "hero.priest.comprehensiveness",
]


def _battle(*, enemy_formation="front-rear", enemy_team=ENEMY_TEAM):
    session, _ = BattleAdapter().create_battle(
        battle_size=2,
        player_team=PLAYER_TEAM,
        enemy_team=enemy_team,
        player_formation="front-rear",
        enemy_formation=enemy_formation,
        seed=2401,
    )
    return session.game.player_heroes[0], session.game.opponent_heroes


def _choose(actor):
    skill = actor.ai_choose_skill(actor.opponents, actor.allies)
    return skill, actor.ai_choose_target(skill, actor.opponents, actor.allies)


def test_weapon_master_collects_live_formation_status_and_cooldown_information():
    actor, enemies = _battle()
    potion = next(skill for skill in actor.skills if skill.name == "Antivenom Potion")
    potion.if_cooldown = True
    potion.cooldown = 2

    information = actor.collect_battle_information(actor.opponents, actor.allies)

    assert information["formations"] == {
        "ally_positions": ("front", "rear"),
        "opponent_positions": ("front", "rear"),
    }
    assert [item["hero"] for item in information["reachable_opponents"]] == [enemies[0]]
    assert "Antivenom Potion" not in information["skills"]
    assert information["self"]["skill_cooldowns"]["Antivenom Potion"] == {
        "available": False,
        "rounds_remaining": 2,
    }


def test_weapon_master_uses_antivenom_when_toxic_or_critically_low():
    actor, _enemies = _battle()
    actor.status["poisoned_dagger"] = True

    skill, target = _choose(actor)

    assert skill.name == "Antivenom Potion"
    assert target is None


def test_weapon_master_finisher_priority_precedes_antivenom():
    actor, enemies = _battle()
    actor.status["poisoned_dagger"] = True
    enemies[0].hp = int(enemies[0].hp_max * 0.30)

    skill, target = _choose(actor)

    assert skill.name == "Fatal Strike"
    assert target is enemies[0]


def test_weapon_master_finishes_a_reachable_low_health_target_not_a_rear_target():
    actor, enemies = _battle()
    front, rear = enemies
    front.hp = int(front.hp_max * 0.30)
    rear.hp = 1

    skill, target = _choose(actor)

    assert skill.name == "Fatal Strike"
    assert target is front


def test_weapon_master_uses_armor_crush_on_reachable_armored_frontliner():
    actor, enemies = _battle(
        enemy_team=["hero.paladin.protection", "hero.mage.comprehensiveness"]
    )
    front, _rear = enemies
    front.hp = front.hp_max
    front.status["armor_breaker"] = False
    front.armor_breaker_stacks = 0

    skill, target = _choose(actor)

    assert skill.name == "Armor Crush"
    assert target is front


def test_weapon_master_one_armor_crush_stack_uses_owner_65_35_split(monkeypatch):
    actor, enemies = _battle(
        enemy_team=["hero.paladin.protection", "hero.mage.comprehensiveness"]
    )
    front = enemies[0]
    front.status["armor_breaker"] = True
    front.armor_breaker_stacks = 1

    monkeypatch.setattr("heroes.warrior.random.random", lambda: 0.64)
    skill, target = _choose(actor)
    assert skill.name == "Armor Crush"
    assert target is front

    monkeypatch.setattr("heroes.warrior.random.random", lambda: 0.65)
    skill, target = _choose(actor)
    assert skill.name == "Fatal Strike"
    assert target is front


def test_weapon_master_two_armor_crush_stacks_uses_owner_50_50_split(monkeypatch):
    actor, enemies = _battle(
        enemy_team=["hero.paladin.protection", "hero.mage.comprehensiveness"]
    )
    front = enemies[0]
    front.status["armor_breaker"] = True
    front.armor_breaker_stacks = 2

    monkeypatch.setattr("heroes.warrior.random.random", lambda: 0.49)
    skill, target = _choose(actor)
    assert skill.name == "Armor Crush"
    assert target is front

    monkeypatch.setattr("heroes.warrior.random.random", lambda: 0.50)
    skill, target = _choose(actor)
    assert skill.name == "Fatal Strike"
    assert target is front


def test_weapon_master_marks_reachable_target_when_enemy_priest_can_heal():
    actor, enemies = _battle()
    front, priest_rear = enemies
    front.faculty = "Warrior"
    front.major = "Defence"
    front.status["fatal_strike"] = False
    priest_rear.hp = priest_rear.hp_max

    skill, target = _choose(actor)

    assert skill.name == "Fatal Strike"
    assert target is front


def test_live_computer_weapon_master_keeps_strategy_target_within_melee_legality():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        battle_size=2,
        player_team=["hero.paladin.protection", "hero.priest.comprehensiveness"],
        enemy_team=["hero.warrior.weapon_master", "hero.mage.comprehensiveness"],
        player_formation="front-rear",
        enemy_formation="front-rear",
        enemy_control_mode="computer",
        seed=2402,
    )
    friendly_front, friendly_rear = session.game.player_heroes
    actor = session.game.opponent_heroes[0]
    friendly_front.status["fatal_strike"] = True
    friendly_rear.hp = 1
    for hero in session.game.heroes:
        hero.actioned = hero is not actor
    session.game.unactioned_sorted_heroes = [actor]

    events = adapter._drain_automatic_turns(session)
    skill_event = next(event for event in events if event["type"] == "skillStarted")

    assert skill_event["skillId"] == "skill.warrior.armor_crush"
    assert skill_event["targetIds"] == [adapter._combatant_id(session, friendly_front)]
