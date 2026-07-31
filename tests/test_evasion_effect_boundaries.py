from __future__ import annotations

from types import SimpleNamespace

from battle_api.adapter import BattleAdapter, _EngineData
from game.game import Game
from heroes.death_knight import Death_Knight_Blood
from heroes.rogue import Rogue_Comprehensiveness
from skills.skill import Skill


def _controlled_session(source_definition: str):
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=701,
        battle_id=f"battle.evasion.{source_definition}",
        battle_size=2,
        player_team=[
            source_definition,
            "hero.priest.comprehensiveness",
        ],
        enemy_team=[
            "hero.rogue.comprehensiveness",
            "hero.mage.comprehensiveness",
        ],
        enemy_control_mode="player",
    )
    source = session.game.player_heroes[0]
    target, next_actor = session.game.opponent_heroes
    next_actor.is_player_controlled = True
    for hero in session.game.heroes:
        hero.actioned = hero not in (source, next_actor)
    session.game.unactioned_sorted_heroes = [source, next_actor]
    return adapter, session, source, target


def _submit_named_skill(
    adapter: BattleAdapter,
    session,
    source,
    target,
    skill_name: str,
):
    skill = next(skill for skill in source.skills if skill.name == skill_name)
    action = next(
        action
        for action in adapter._legal_actions(session, source)
        if adapter._skill_by_id(source, action["skillId"]) is skill
    )
    result = adapter.submit(
        session,
        {
            "type": "useSkill",
            "commandId": f"cmd.evasion.{skill_name}",
            "expectedRevision": session.revision,
            "actorId": action["actorId"],
            "skillId": action["skillId"],
            "targetIds": [adapter._combatant_id(session, target)],
        },
    )
    return skill, result


def test_shield_bash_hit_applies_damage_and_stun():
    adapter, session, source, target = _controlled_session("hero.warrior.defence")
    skill = next(skill for skill in source.skills if skill.name == "Shield Bash")
    skill.evasion_check = lambda _target: False
    hp_before = target.hp

    _, result = _submit_named_skill(
        adapter, session, source, target, "Shield Bash"
    )

    target_id = adapter._combatant_id(session, target)
    assert result["accepted"] is True
    assert target.hp < hp_before
    assert target.status["stunned"] is True
    assert any(
        event["type"] == "damageApplied" and event.get("targetId") == target_id
        for event in result["events"]
    )
    assert any(
        event["type"] == "statusApplied"
        and event.get("statusId") == "status.stunned"
        and event.get("targetId") == target_id
        for event in result["events"]
    )


def test_zero_damage_shield_bash_is_a_landed_hit_not_an_evade():
    adapter, session, source, target = _controlled_session("hero.warrior.defence")
    skill = next(skill for skill in source.skills if skill.name == "Shield Bash")
    skill.evasion_check = lambda _target: False
    target.defense = 1_000_000
    hp_before = target.hp

    _, result = _submit_named_skill(
        adapter, session, source, target, "Shield Bash"
    )

    target_id = adapter._combatant_id(session, target)
    assert target.hp == hp_before
    assert target.status["stunned"] is True
    assert skill.last_target_outcomes[id(target)] == "hit"
    assert any(
        event["type"] == "statusApplied"
        and event.get("statusId") == "status.stunned"
        and event.get("targetId") == target_id
        for event in result["events"]
    )
    assert not any(
        event["type"] == "attackEvaded" and event.get("targetId") == target_id
        for event in result["events"]
    )


def test_shield_bash_evade_suppresses_damage_stun_and_adapter_status_event():
    adapter, session, source, target = _controlled_session("hero.warrior.defence")
    skill = next(skill for skill in source.skills if skill.name == "Shield Bash")
    skill.evasion_check = lambda _target: True
    hp_before = target.hp

    _, result = _submit_named_skill(
        adapter, session, source, target, "Shield Bash"
    )

    target_id = adapter._combatant_id(session, target)
    assert result["accepted"] is True
    assert target.hp == hp_before
    assert target.status["stunned"] is False
    assert any(
        event["type"] == "attackEvaded" and event.get("targetId") == target_id
        for event in result["events"]
    )
    assert not any(
        event["type"] in {"damageApplied", "statusApplied"}
        and event.get("targetId") == target_id
        for event in result["events"]
    )
    target_status_ids = {
        status["id"]
        for status in result["snapshot"]["combatants"][target_id]["statuses"]
    }
    assert "status.stunned" not in target_status_ids


def test_shield_of_righteous_evade_preserves_independent_caster_buff():
    adapter, session, source, target = _controlled_session(
        "hero.paladin.protection"
    )
    skill = next(
        skill for skill in source.skills if skill.name == "Shield of Righteous"
    )
    skill.evasion_check = lambda _target: True
    target_hp_before = target.hp
    source_defense_before = source.defense

    _, result = _submit_named_skill(
        adapter, session, source, target, "Shield of Righteous"
    )

    source_id = adapter._combatant_id(session, source)
    target_id = adapter._combatant_id(session, target)
    assert target.hp == target_hp_before
    assert source.defense > source_defense_before
    assert source.status["shield_of_righteous"] is True
    assert any(
        event["type"] == "attackEvaded" and event.get("targetId") == target_id
        for event in result["events"]
    )
    assert any(
        event["type"] == "statusApplied"
        and event.get("statusId") == "status.shield_of_righteous"
        and event.get("targetId") == source_id
        for event in result["events"]
    )
    assert not any(
        event["type"] in {"damageApplied", "statusApplied"}
        and event.get("targetId") == target_id
        for event in result["events"]
    )


def test_crusader_strike_evade_preserves_independent_caster_agility_buff():
    adapter, session, source, target = _controlled_session(
        "hero.paladin.retribution"
    )
    skill = next(skill for skill in source.skills if skill.name == "Crusader Strike")
    skill.evasion_check = lambda _target: True
    target_hp_before = target.hp
    agility_before = source.agility

    _submit_named_skill(adapter, session, source, target, "Crusader Strike")

    assert target.hp == target_hp_before
    assert source.status["wrath_of_crusader"] is True
    assert source.agility > agility_before


def test_heroric_charge_evade_preserves_independent_caster_heal():
    adapter, session, source, target = _controlled_session(
        "hero.paladin.protection"
    )
    skill = next(skill for skill in source.skills if skill.name == "Heroric Charge")
    skill.evasion_check = lambda _target: True
    source.hp = source.hp_max - 40
    source_hp_before = source.hp
    target_hp_before = target.hp

    _submit_named_skill(adapter, session, source, target, "Heroric Charge")

    assert target.hp == target_hp_before
    assert target.status["scoff"] is False
    assert source.hp > source_hp_before
    assert skill.if_cooldown is True
    assert skill.cooldown == 3


def test_shield_lash_evade_preserves_independent_caster_resistance_buff():
    adapter, session, source, target = _controlled_session("hero.warrior.defence")
    skill = next(skill for skill in source.skills if skill.name == "Shield Lash")
    skill.evasion_check = lambda _target: True
    fire_resistance_before = source.fire_resistance
    target_hp_before = target.hp

    _submit_named_skill(adapter, session, source, target, "Shield Lash")

    assert target.hp == target_hp_before
    assert target.status["scoff"] is False
    assert source.status["shield_lash"] is True
    assert source.fire_resistance == fire_resistance_before + 45
    assert skill.if_cooldown is True
    assert skill.cooldown == 3


def test_cumbrous_axe_evade_preserves_independent_caster_healing_buff():
    engine_data = _EngineData()
    source = Death_Knight_Blood(engine_data, "Blood Knight", "player", True)
    target = Rogue_Comprehensiveness(engine_data, "Target", "enemy", True)
    game = Game([source], [target], "simulation")
    game.grouping()
    game.update_allies_opponents_list()
    game.pass_game_instance(game.heroes)
    skill = next(skill for skill in source.skills if skill.name == "Cumbrous Axe")
    skill.evasion_check = lambda _target: True
    target_hp_before = target.hp

    skill.execute(target)

    assert target.hp == target_hp_before
    assert target.status["scoff"] is False
    assert source.status["cumbrous_axe"] is True
    assert source.healing_boost_effects["cumbrous_axe"] == 1.0
    assert skill.if_cooldown is True
    assert skill.cooldown == 3


def test_heroric_charge_control_immunity_suppresses_scoff_but_keeps_caster_heal():
    adapter, session, source, target = _controlled_session(
        "hero.paladin.protection"
    )
    target.status["warlust"] = True
    target.is_immunity_condition_control = True
    source.hp = source.hp_max - 60
    source_hp_before = source.hp
    skill = next(skill for skill in source.skills if skill.name == "Heroric Charge")
    skill.evasion_check = lambda _target: False

    _, result = _submit_named_skill(
        adapter, session, source, target, "Heroric Charge"
    )

    target_id = adapter._combatant_id(session, target)
    assert target.status["scoff"] is False
    assert source.hp > source_hp_before
    assert skill.if_cooldown is True
    assert skill.cooldown == 3
    assert not any(
        event["type"] == "statusApplied"
        and event.get("statusId") == "status.scoff"
        and event.get("targetId") == target_id
        for event in result["events"]
    )


def test_shield_lash_control_immunity_keeps_historical_double_resistance_buff():
    adapter, session, source, target = _controlled_session("hero.warrior.defence")
    target.status["warlust"] = True
    target.is_immunity_condition_control = True
    resistance_before = {
        nature: getattr(source, f"{nature}_resistance")
        for nature in ("fire", "frost", "death", "nature")
    }
    skill = next(skill for skill in source.skills if skill.name == "Shield Lash")
    skill.evasion_check = lambda _target: False

    _, result = _submit_named_skill(
        adapter, session, source, target, "Shield Lash"
    )

    target_id = adapter._combatant_id(session, target)
    assert target.status["scoff"] is False
    assert source.status["shield_lash"] is True
    assert {
        nature: getattr(source, f"{nature}_resistance") - before
        for nature, before in resistance_before.items()
    } == {
        "fire": 90,
        "frost": 90,
        "death": 90,
        "nature": 90,
    }
    assert skill.if_cooldown is True
    assert skill.cooldown == 3
    assert not any(
        event["type"] == "statusApplied"
        and event.get("statusId") == "status.scoff"
        and event.get("targetId") == target_id
        for event in result["events"]
    )


def test_cumbrous_axe_control_immunity_suppresses_scoff_but_keeps_caster_buff():
    engine_data = _EngineData()
    source = Death_Knight_Blood(engine_data, "Blood Knight", "player", True)
    target = Rogue_Comprehensiveness(engine_data, "Target", "enemy", True)
    game = Game([source], [target], "simulation")
    game.grouping()
    game.update_allies_opponents_list()
    game.pass_game_instance(game.heroes)
    target.status["warlust"] = True
    target.is_immunity_condition_control = True
    skill = next(skill for skill in source.skills if skill.name == "Cumbrous Axe")
    skill.evasion_check = lambda _target: False

    skill.execute(target)

    assert target.status["scoff"] is False
    assert source.status["cumbrous_axe"] is True
    assert source.healing_boost_effects["cumbrous_axe"] == 1.0
    assert skill.if_cooldown is True
    assert skill.cooldown == 3


def test_multi_target_skill_action_receives_only_individual_hit_targets():
    class Target:
        pass

    inactive_statuses = {
        "shield_of_protection": False,
        "glacier": False,
        "anti_magic_shield": False,
        "warlust": False,
    }
    hit = Target()
    hit.name = "Hit"
    hit.hp = 100
    hit.agility = 0
    hit.evasion_capability = 0
    hit.status = dict(inactive_statuses)
    evaded = Target()
    evaded.name = "Evaded"
    evaded.hp = 100
    evaded.agility = 0
    evaded.evasion_capability = 0
    evaded.status = dict(inactive_statuses)
    acted_on = []
    initiator = SimpleNamespace(
        name="Source",
        status={"magic_casting": False},
        game=SimpleNamespace(display_battle_info=lambda _message: None),
    )

    def harmful_action(targets):
        acted_on.extend(targets)
        for target in targets:
            target.hp -= 10
        return "resolved"

    skill = Skill(
        initiator,
        "Mixed Multi",
        harmful_action,
        target_type="multi",
        skill_type="damage",
    )
    skill.evasion_check = lambda target: target is evaded

    result = skill.execute([hit, evaded])

    assert result == "resolved"
    assert acted_on == [hit]
    assert skill.last_target_outcomes == {id(hit): "hit", id(evaded): "evaded"}
    assert hit.hp == 90
    assert evaded.hp == 100
