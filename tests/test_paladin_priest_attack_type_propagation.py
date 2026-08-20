"""Regression coverage for declared Paladin and Priest attack types."""

from types import SimpleNamespace

import pytest

from battle_api.adapter import BattleAdapter
from skills.skill import Skill


ENEMIES = ["hero.rogue.comprehensiveness", "hero.mage.comprehensiveness"]


@pytest.mark.parametrize(
    ("definition_id", "skill_name", "expected_attack_type", "expected_targets"),
    [
        (
            "hero.paladin.retribution",
            "Hammer of Anger",
            "ranged_projectile",
            1,
        ),
        ("hero.paladin.retribution", "Crusader Strike", "melee", 1),
        ("hero.paladin.protection", "Hammer of Revenge", "ranged_instant", 1),
        ("hero.paladin.protection", "Shield of Righteous", "melee", 1),
        ("hero.paladin.protection", "Heroric Charge", "ranged_instant", 1),
        ("hero.paladin.holy", "Holy Blast", "ranged_projectile", 2),
        ("hero.priest.comprehensiveness", "Holy Smite", "ranged_instant", 1),
        (
            "hero.priest.comprehensiveness",
            "Shadow Word Pain",
            "ranged_instant",
            1,
        ),
        ("hero.priest.discipline", "Penance", "ranged_instant", 1),
        (
            "hero.priest.discipline",
            "Holy Word Punishment",
            "ranged_instant",
            2,
        ),
    ],
)
def test_declared_attack_type_survives_adapter_execution(
    definition_id,
    skill_name,
    expected_attack_type,
    expected_targets,
):
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        battle_size=2,
        player_team=[definition_id, "hero.priest.comprehensiveness"],
        enemy_team=ENEMIES,
        player_formation="front-rear",
        enemy_formation="front-rear",
        seed=1911,
    )
    actor = session.game.player_heroes[0]
    for hero in session.game.heroes:
        hero.actioned = hero is not actor
    session.game.unactioned_sorted_heroes = [actor]

    skill = next(skill for skill in actor.skills if skill.name == skill_name)
    assert skill.attack_type == expected_attack_type
    skill.evasion_check = lambda _target: False
    action = next(
        action
        for action in adapter._legal_actions(session, actor)
        if action["skillId"] == adapter._skill_id(actor, skill)
    )

    captured = []

    def capture(damage, attack_type="NA", attacker=None):
        captured.append((damage, attack_type, attacker))
        return "captured"

    for target in session.game.opponent_heroes:
        target.take_damage = capture

    result = adapter.submit(
        session,
        {
            "type": "useSkill",
            "commandId": f"cmd.attack-type.{definition_id}.{skill_name}",
            "expectedRevision": session.revision,
            "actorId": action["actorId"],
            "skillId": action["skillId"],
            "targetIds": action["validTargetIds"][:expected_targets],
        },
    )

    assert result["accepted"] is True
    initial_skill_damage = [call for call in captured if call[2] is actor]
    assert len(initial_skill_damage) == expected_targets
    assert all(call[1] == expected_attack_type for call in initial_skill_damage)


def test_damage_healing_dispatch_preserves_legacy_callback_signature():
    target = object()
    calls = []

    def legacy_action(selected_target, target_type):
        calls.append((selected_target, target_type))
        return "legacy"

    initiator = SimpleNamespace(allies=[], name="Legacy")
    skill = Skill(
        initiator,
        "Legacy Damage Healing",
        legacy_action,
        target_type="single",
        skill_type="damage_healing",
        attack_type="ranged_instant",
    )
    skill.evasion_check = lambda _target: False

    assert skill.execute(target) == "legacy"
    assert calls == [(target, "opponent")]


def test_penance_ally_branch_remains_healing_only():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        battle_size=2,
        player_team=[
            "hero.priest.discipline",
            "hero.priest.comprehensiveness",
        ],
        enemy_team=ENEMIES,
        player_formation="front-rear",
        enemy_formation="front-rear",
        seed=1912,
    )
    actor, ally = session.game.player_heroes
    for hero in session.game.heroes:
        hero.actioned = hero is not actor
    session.game.unactioned_sorted_heroes = [actor]
    skill = next(skill for skill in actor.skills if skill.name == "Penance")
    action = next(
        action
        for action in adapter._legal_actions(session, actor)
        if action["skillId"] == adapter._skill_id(actor, skill)
    )
    healing = []
    ally.take_healing = lambda amount: healing.append(amount) or "healed"
    ally.take_damage = lambda *args, **kwargs: pytest.fail(
        "Penance's ally branch must not apply damage"
    )

    result = adapter.submit(
        session,
        {
            "type": "useSkill",
            "commandId": "cmd.attack-type.penance-healing",
            "expectedRevision": session.revision,
            "actorId": action["actorId"],
            "skillId": action["skillId"],
            "targetIds": [adapter._combatant_id(session, ally)],
        },
    )

    assert result["accepted"] is True
    assert len(healing) == 1
