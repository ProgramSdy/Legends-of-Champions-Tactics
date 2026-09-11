from __future__ import annotations

import pytest

from battle_api.adapter import BattleAdapter
from skills.skill import Buff


HEROES = {
    "rogue": "hero.rogue.comprehensiveness",
    "mage": "hero.mage.comprehensiveness",
    "priest": "hero.priest.comprehensiveness",
    "discipline": "hero.priest.discipline",
}


def _battle(
    player_team,
    enemy_team,
    *,
    battle_size=None,
    player_formation=None,
    enemy_formation=None,
    enemy_control_mode="player",
    seed=4101,
):
    battle_size = battle_size or len(player_team)
    return BattleAdapter().create_battle(
        battle_size=battle_size,
        player_team=player_team,
        enemy_team=enemy_team,
        player_formation=player_formation,
        enemy_formation=enemy_formation,
        enemy_control_mode=enemy_control_mode,
        fixed_computer_formation=True,
        seed=seed,
    )


def _choose(actor):
    skill = actor.ai_choose_skill(actor.opponents, actor.allies)
    return skill, actor.ai_choose_target(skill, actor.opponents, actor.allies)


def _skill(hero, name):
    return next(skill for skill in hero.skills if skill.name == name)


def test_rogue_uses_ranged_poison_on_a_screened_low_health_rear_target():
    session, _ = _battle(
        [HEROES["rogue"], "hero.warrior.weapon_master"],
        ["hero.mage.comprehensiveness", "hero.priest.comprehensiveness"],
        battle_size=2,
        player_formation="front-rear",
        enemy_formation="front-rear",
    )
    actor = session.game.player_heroes[0]
    front, rear = session.game.opponent_heroes
    front.hp = front.hp_max
    rear.hp = int(rear.hp_max * 0.20)

    skill, target = _choose(actor)

    assert skill.name == "Poisoned Dagger"
    assert target is rear


def test_rogue_excludes_dead_targets_and_falls_back_when_poison_is_on_cooldown():
    session, _ = _battle(
        [HEROES["rogue"], "hero.warrior.weapon_master"],
        ["hero.mage.comprehensiveness", "hero.priest.comprehensiveness"],
        battle_size=2,
        player_formation="front-rear",
        enemy_formation="front-rear",
    )
    actor = session.game.player_heroes[0]
    front, rear = session.game.opponent_heroes
    rear.hp = 0
    _skill(actor, "Poisoned Dagger").if_cooldown = True

    skill, target = _choose(actor)

    assert skill.name == "Sharp Blade"
    assert target is front
    assert target.hp > 0


def test_rogue_does_not_waste_the_capped_second_poison_stack():
    session, _ = _battle(
        [HEROES["rogue"]],
        ["hero.mage.comprehensiveness"],
        battle_size=1,
    )
    actor = session.game.player_heroes[0]
    target = session.game.opponent_heroes[0]
    target.status["poisoned_dagger"] = True
    target.poisoned_dagger_stacks = 2
    target.poisoned_dagger_debuff_duration = 3

    skill, chosen = _choose(actor)

    assert skill.name != "Poisoned Dagger"
    assert chosen is target


def test_mage_arcane_missiles_requires_and_returns_exactly_two_live_targets():
    session, _ = _battle(
        [HEROES["mage"], "hero.warrior.weapon_master"],
        ["hero.rogue.comprehensiveness", "hero.priest.comprehensiveness"],
        battle_size=2,
        player_formation="front-rear",
        enemy_formation="front-rear",
    )
    actor = session.game.player_heroes[0]
    enemies = session.game.opponent_heroes
    _skill(actor, "Fireball").if_cooldown = True
    _skill(actor, "Frost Bolt").if_cooldown = True
    for enemy in enemies:
        enemy.status["cold"] = True

    skill, targets = _choose(actor)

    assert skill.name == "Arcane Missiles"
    assert targets == enemies
    assert len({id(target) for target in targets}) == 2


def test_mage_never_selects_arcane_missiles_for_a_single_target_battle():
    session, _ = _battle(
        [HEROES["mage"]],
        ["hero.rogue.comprehensiveness"],
        battle_size=1,
    )
    actor = session.game.player_heroes[0]
    _skill(actor, "Frost Bolt").if_cooldown = True

    skill, target = _choose(actor)

    assert skill.name == "Fireball"
    assert target is session.game.opponent_heroes[0]


def test_mage_does_not_select_arcane_missiles_when_only_one_opponent_is_alive():
    session, _ = _battle(
        [HEROES["mage"], "hero.warrior.weapon_master"],
        ["hero.rogue.comprehensiveness", "hero.priest.comprehensiveness"],
        battle_size=2,
        player_formation="front-rear",
        enemy_formation="front-rear",
    )
    actor = session.game.player_heroes[0]
    live, dead = session.game.opponent_heroes
    dead.hp = 0
    _skill(actor, "Fireball").if_cooldown = True
    _skill(actor, "Frost Bolt").if_cooldown = True
    live.status["cold"] = True

    skill, target = _choose(actor)

    assert skill is None
    assert target is None


def test_mage_cold_active_uses_resistance_tie_break_and_ignores_dead_target():
    session, _ = _battle(
        [HEROES["mage"], "hero.warrior.weapon_master"],
        ["hero.rogue.comprehensiveness", "hero.priest.comprehensiveness"],
        battle_size=2,
        player_formation="front-rear",
        enemy_formation="front-rear",
    )
    actor = session.game.player_heroes[0]
    live, dead = session.game.opponent_heroes
    live.status["cold"] = True
    live.fire_resistance = 5
    live.frost_resistance = 5
    dead.hp = 0

    skill, target = _choose(actor)

    assert skill.name == "Fireball"
    assert target is live


def test_mage_three_vs_three_arcane_pair_reaches_adapter_without_repair():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        battle_size=3,
        player_team=[HEROES["mage"], "hero.warrior.weapon_master", "hero.priest.comprehensiveness"],
        enemy_team=["hero.rogue.comprehensiveness", "hero.priest.discipline", "hero.paladin.protection"],
        player_formation="all-front",
        enemy_formation="one-front-two-rear",
        enemy_control_mode="player",
        fixed_computer_formation=True,
        seed=4120,
    )
    actor = session.game.player_heroes[0]
    for skill_name in ("Fireball", "Frost Bolt"):
        _skill(actor, skill_name).if_cooldown = True
    for target in actor.opponents:
        target.status["cold"] = True
    skill, targets = _choose(actor)
    assert skill.name == "Arcane Missiles"
    target_ids = [adapter._combatant_id(session, target) for target in targets]
    assert len(target_ids) == 2
    assert set(target_ids).issubset(set(adapter._valid_target_ids(session, actor, skill)))
    for hero in session.game.heroes:
        hero.actioned = hero is not actor
    session.game.unactioned_sorted_heroes = [actor]

    result = adapter._resolve(
        session,
        {
            "type": "useSkill",
            "commandId": "ai.test.mage.arcane-pair",
            "expectedRevision": session.revision,
            "actorId": adapter._combatant_id(session, actor),
            "skillId": adapter._skill_id(actor, skill),
            "targetIds": target_ids,
        },
    )
    assert not [event for event in result["events"] if event["type"] == "actionRejected"]


def test_priest_comprehensiveness_triages_the_lowest_critical_ally():
    session, _ = _battle(
        [HEROES["priest"], "hero.warrior.weapon_master"],
        ["hero.mage.comprehensiveness", "hero.rogue.comprehensiveness"],
        battle_size=2,
        player_formation="front-rear",
        enemy_formation="front-rear",
    )
    actor, ally = session.game.player_heroes
    ally.hp = int(ally.hp_max * 0.25)

    skill, target = _choose(actor)

    assert skill.name == "Binding Heal"
    assert target is ally


def test_priest_comprehensiveness_uses_shadow_word_pain_before_direct_pressure():
    session, _ = _battle(
        [HEROES["priest"]],
        ["hero.warrior.defence"],
        battle_size=1,
    )
    actor = session.game.player_heroes[0]
    target = session.game.opponent_heroes[0]
    target.hp = int(target.hp_max * 0.8)

    skill, chosen = _choose(actor)

    assert skill.name == "Shadow Word Pain"
    assert chosen is target


def test_priest_comprehensiveness_does_not_recast_active_pain_when_smite_is_ready():
    session, _ = _battle(
        [HEROES["priest"]],
        ["hero.warrior.defence"],
        battle_size=1,
    )
    actor = session.game.player_heroes[0]
    target = session.game.opponent_heroes[0]
    target.status["shadow_word_pain"] = True
    target.shadow_word_pain_debuff_duration = 3

    skill, chosen = _choose(actor)

    assert skill.name == "Holy Smite"
    assert chosen is target


def test_priest_comprehensiveness_uses_shadow_pain_fallback_when_smite_is_unavailable():
    session, _ = _battle(
        [HEROES["priest"]],
        ["hero.warrior.defence"],
        battle_size=1,
    )
    actor = session.game.player_heroes[0]
    target = session.game.opponent_heroes[0]
    target.status["shadow_word_pain"] = True
    target.shadow_word_pain_debuff_duration = 3
    _skill(actor, "Holy Smite").if_cooldown = True
    _skill(actor, "Binding Heal").if_cooldown = True

    skill, chosen = _choose(actor)

    assert skill.name == "Shadow Word Pain"
    assert chosen is target


def test_priest_comprehensiveness_does_not_choose_full_hp_binding_heal_as_value_action():
    session, _ = _battle(
        [HEROES["priest"]],
        ["hero.warrior.defence"],
        battle_size=1,
    )
    actor = session.game.player_heroes[0]
    _skill(actor, "Holy Smite").if_cooldown = True
    _skill(actor, "Shadow Word Pain").if_cooldown = True

    skill, target = _choose(actor)

    assert skill is None or skill.name != "Binding Heal"
    assert target is None


def test_priest_comprehensiveness_binding_heal_passes_ally_target_through_adapter():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        battle_size=2,
        player_team=[HEROES["priest"], "hero.warrior.weapon_master"],
        enemy_team=["hero.mage.comprehensiveness", "hero.rogue.comprehensiveness"],
        player_formation="front-rear",
        enemy_formation="front-rear",
        seed=4140,
    )
    actor, ally = session.game.player_heroes
    ally.hp = int(ally.hp_max * 0.25)
    skill, target = _choose(actor)
    assert skill.name == "Binding Heal"
    target_id = adapter._combatant_id(session, target)
    for hero in session.game.heroes:
        hero.actioned = hero is not actor
    session.game.unactioned_sorted_heroes = [actor]
    result = adapter._resolve(
        session,
        {
            "type": "useSkill",
            "commandId": "ai.test.priest.binding",
            "expectedRevision": session.revision,
            "actorId": adapter._combatant_id(session, actor),
            "skillId": adapter._skill_id(actor, skill),
            "targetIds": [target_id],
        },
    )
    assert any(event["type"] == "healingApplied" for event in result["events"])


def test_priest_discipline_penance_uses_ally_side_for_critical_healing():
    session, _ = _battle(
        [HEROES["discipline"], "hero.warrior.weapon_master"],
        ["hero.mage.comprehensiveness", "hero.rogue.comprehensiveness"],
        battle_size=2,
        player_formation="front-rear",
        enemy_formation="front-rear",
    )
    actor, ally = session.game.player_heroes
    ally.hp = int(ally.hp_max * 0.2)

    skill, target = _choose(actor)

    assert skill.name == "Penance"
    assert target is ally
    assert target in actor.allies


def test_priest_discipline_penance_uses_enemy_side_for_finishing_damage():
    session, _ = _battle(
        [HEROES["discipline"]],
        ["hero.warrior.defence"],
        battle_size=1,
    )
    actor = session.game.player_heroes[0]
    target = session.game.opponent_heroes[0]
    target.hp = 17

    skill, chosen = _choose(actor)

    assert skill.name == "Penance"
    assert chosen is target
    assert chosen in actor.opponents


def test_priest_discipline_never_uses_punishment_with_one_opponent():
    session, _ = _battle(
        [HEROES["discipline"]],
        ["hero.warrior.defence"],
        battle_size=1,
    )
    actor = session.game.player_heroes[0]
    _skill(actor, "Penance").if_cooldown = True
    _skill(actor, "Holy Word Redemption").if_cooldown = True

    skill, target = _choose(actor)

    assert skill is None or skill.name != "Holy Word Punishment"
    assert target is None


def test_priest_discipline_never_uses_punishment_with_only_one_survivor():
    session, _ = _battle(
        [HEROES["discipline"], "hero.warrior.weapon_master"],
        ["hero.mage.comprehensiveness", "hero.rogue.comprehensiveness"],
        battle_size=2,
        player_formation="front-rear",
        enemy_formation="front-rear",
    )
    actor = session.game.player_heroes[0]
    session.game.opponent_heroes[1].hp = 0
    _skill(actor, "Holy Word Redemption").if_cooldown = True

    skill, target = _choose(actor)

    assert skill.name == "Penance"
    assert target is session.game.opponent_heroes[0]


def test_priest_discipline_distinguishes_other_caster_redemption():
    session, _ = _battle(
        [HEROES["discipline"], "hero.warrior.weapon_master"],
        ["hero.mage.comprehensiveness", "hero.rogue.comprehensiveness"],
        battle_size=2,
        player_formation="front-rear",
        enemy_formation="front-rear",
    )
    actor, ally = session.game.player_heroes
    other_caster = session.game.opponent_heroes[0]
    ally.status["holy_word_redemption"] = True
    ally.add_buff(Buff("Holy Word Redemption", 5, other_caster, 0.7))

    skill, target = _choose(actor)

    assert skill.name == "Holy Word Redemption"
    assert target is actor


def test_priest_discipline_refreshes_same_caster_redemption_at_duration_boundary():
    session, _ = _battle(
        [HEROES["discipline"], "hero.warrior.weapon_master"],
        ["hero.mage.comprehensiveness", "hero.rogue.comprehensiveness"],
        battle_size=2,
        player_formation="front-rear",
        enemy_formation="front-rear",
    )
    actor, ally = session.game.player_heroes
    ally.status["holy_word_redemption"] = True
    ally.add_buff(Buff("Holy Word Redemption", 1, actor, 0.7))

    skill, target = _choose(actor)

    assert skill.name == "Holy Word Redemption"
    assert target is ally


def test_priest_discipline_punishment_returns_exactly_two_enemy_targets():
    session, _ = _battle(
        [HEROES["discipline"], "hero.warrior.weapon_master", "hero.paladin.holy"],
        ["hero.mage.comprehensiveness", "hero.rogue.comprehensiveness", "hero.paladin.protection"],
        battle_size=3,
        player_formation="one-front-two-rear",
        enemy_formation="two-front-one-rear",
    )
    actor = session.game.player_heroes[0]
    protected = actor.allies[0]
    protected.status["holy_word_redemption"] = True
    protected.add_buff(Buff("Holy Word Redemption", 5, actor, 0.7))

    skill, targets = _choose(actor)

    assert skill.name == "Holy Word Punishment"
    assert len(targets) == 2
    assert len({id(target) for target in targets}) == 2
    assert all(target in actor.opponents and target.hp > 0 for target in targets)


@pytest.mark.parametrize(
    ("hero_key", "player_team", "enemy_team"),
    [
        ("rogue", [HEROES["rogue"]], ["hero.warrior.weapon_master"]),
        ("mage", [HEROES["mage"]], ["hero.warrior.weapon_master"]),
        ("priest", [HEROES["priest"]], ["hero.warrior.weapon_master"]),
        ("discipline", [HEROES["discipline"]], ["hero.warrior.weapon_master"]),
    ],
)
@pytest.mark.parametrize("battle_size", [1, 2, 3])
def test_seeded_computer_turns_use_legal_actions_for_all_sizes(
    hero_key, player_team, enemy_team, battle_size
):
    fillers = [
        "hero.warrior.weapon_master",
        "hero.warrior.defence",
        "hero.paladin.protection",
    ]
    player_team = fillers[:battle_size]
    enemy_fillers = [
        "hero.warrior.weapon_master",
        "hero.mage.comprehensiveness",
        "hero.rogue.comprehensiveness",
    ]
    enemy_team = ([HEROES[hero_key]] + enemy_fillers)[:battle_size]
    formations = {
        1: (None, None),
        2: ("front-rear", "side-by-side"),
        3: ("one-front-two-rear", "two-front-one-rear"),
    }
    player_formation, enemy_formation = formations[battle_size]
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        battle_size=battle_size,
        player_team=player_team,
        enemy_team=enemy_team,
        player_formation=player_formation,
        enemy_formation=enemy_formation,
        enemy_control_mode="computer",
        fixed_computer_formation=True,
        seed=4300 + battle_size,
    )
    actor = session.game.opponent_heroes[0]
    initial_legal_actions = {
        adapter._skill_id(actor, skill): adapter._valid_target_ids(session, actor, skill)
        for skill in actor.skills
    }
    for hero in session.game.heroes:
        hero.actioned = hero is not actor
    session.game.unactioned_sorted_heroes = [actor]

    events = adapter._drain_automatic_turns(session)

    rejected = [event for event in events if event["type"] == "actionRejected"]
    assert not rejected
    started = next(event for event in events if event["type"] == "skillStarted")
    skill = next(
        skill for skill in actor.skills
        if adapter._skill_id(actor, skill) == started["skillId"]
    )
    valid_ids = initial_legal_actions[started["skillId"]]
    assert len(started["targetIds"]) == min(skill.target_qty, len(valid_ids))
    assert len(set(started["targetIds"])) == len(started["targetIds"])
    assert set(started["targetIds"]).issubset(set(valid_ids))


def test_same_seed_reproduces_ai_selection_and_initial_snapshot():
    kwargs = dict(
        battle_size=3,
        player_team=[HEROES["mage"], "hero.warrior.weapon_master", "hero.priest.comprehensiveness"],
        enemy_team=["hero.rogue.comprehensiveness", "hero.paladin.protection", "hero.warrior.defence"],
        player_formation="all-front",
        enemy_formation="one-front-two-rear",
        enemy_control_mode="computer",
        fixed_computer_formation=True,
        seed=4401,
    )
    first, envelope_first = BattleAdapter().create_battle(**kwargs)
    second, envelope_second = BattleAdapter().create_battle(**kwargs)
    first_actor = first.game.opponent_heroes[0]
    second_actor = second.game.opponent_heroes[0]
    first_skill, first_target = _choose(first_actor)
    second_skill, second_target = _choose(second_actor)

    assert envelope_first["data"]["snapshot"] == envelope_second["data"]["snapshot"]
    assert first_skill.name == second_skill.name
    first_targets = first_target if isinstance(first_target, list) else [first_target]
    second_targets = second_target if isinstance(second_target, list) else [second_target]
    assert [target.name for target in first_targets] == [target.name for target in second_targets]


def test_valid_strategy_target_does_not_need_adapter_random_repair(monkeypatch):
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        battle_size=2,
        player_team=[HEROES["mage"], "hero.warrior.weapon_master"],
        enemy_team=["hero.rogue.comprehensiveness", "hero.priest.comprehensiveness"],
        player_formation="front-rear",
        enemy_formation="front-rear",
        enemy_control_mode="computer",
        fixed_computer_formation=True,
        seed=4501,
    )
    actor = session.game.opponent_heroes[0]
    for hero in session.game.heroes:
        hero.actioned = hero is not actor
    session.game.unactioned_sorted_heroes = [actor]

    chosen_skill = actor.ai_choose_skill(actor.opponents, actor.allies)
    chosen_target = actor.ai_choose_target(
        chosen_skill, actor.opponents, actor.allies
    )
    chosen_targets = (
        chosen_target if isinstance(chosen_target, list) else [chosen_target]
    )
    valid_target_ids = adapter._valid_target_ids(session, actor, chosen_skill)
    target_ids = [
        adapter._combatant_id(session, target)
        for target in chosen_targets
        if target is not None
    ]
    assert target_ids
    assert set(target_ids).issubset(set(valid_target_ids))

    def unexpected_random_use(*_args, **_kwargs):
        raise AssertionError("adapter used random repair for a valid AI action")

    monkeypatch.setattr("battle_api.adapter.random.choice", unexpected_random_use)
    monkeypatch.setattr("battle_api.adapter.random.sample", unexpected_random_use)

    result = adapter._resolve(
        session,
        {
            "type": "useSkill",
            "commandId": "ai.test.valid-target",
            "expectedRevision": session.revision,
            "actorId": adapter._combatant_id(session, actor),
            "skillId": adapter._skill_id(actor, chosen_skill),
            "targetIds": target_ids,
        },
    )
    events = result["events"]
    assert any(event["type"] == "skillStarted" for event in events)
