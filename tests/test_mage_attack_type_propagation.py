"""Regression coverage for Mage Comprehensiveness projectile dispatch.

These tests intentionally observe the Hero.take_damage seam rather than damage
numbers: the latter include seeded/random skill variation and resistance.  The
contract under test is that the declared Skill.attack_type survives adapter
target selection and Skill execution for every projectile spell.
"""

import pytest

from battle_api.adapter import BattleAdapter


MAGE = "hero.mage.comprehensiveness"
ENEMIES = ["hero.rogue.comprehensiveness", "hero.priest.comprehensiveness"]


@pytest.mark.parametrize(
    ("skill_name", "expected_targets"),
    [
        ("Fireball", 1),
        ("Arcane Missiles", 2),
        ("Frost Bolt", 1),
    ],
)
def test_mage_projectile_attack_type_survives_legal_action_and_execution(
    skill_name, expected_targets
):
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        battle_size=2,
        player_team=[MAGE, "hero.priest.comprehensiveness"],
        enemy_team=ENEMIES,
        player_formation="front-rear",
        enemy_formation="front-rear",
        seed=1910,
    )
    actor = session.game.player_heroes[0]
    target_front, target_rear = session.game.opponent_heroes
    for hero in session.game.heroes:
        hero.actioned = hero is not actor
    session.game.unactioned_sorted_heroes = [actor]

    skill = next(skill for skill in actor.skills if skill.name == skill_name)
    assert skill.attack_type == "ranged_projectile"
    action = next(
        action
        for action in adapter._legal_actions(session, actor)
        if action["skillId"] == adapter._skill_id(actor, skill)
    )
    # Unlike melee actions, a projectile can legally target a living rear unit
    # while a front unit remains alive.
    rear_id = adapter._combatant_id(session, target_rear)
    assert rear_id in action["validTargetIds"]

    captured = []

    def capture(damage, attack_type="NA", attacker=None):
        captured.append((damage, attack_type, attacker))
        return "captured"

    target_front.take_damage = capture
    target_rear.take_damage = capture
    target_ids = [rear_id]
    if expected_targets == 2:
        target_ids.insert(0, adapter._combatant_id(session, target_front))
    result = adapter.submit(
        session,
        {
            "type": "useSkill",
            "commandId": f"cmd.mage-projectile.{skill_name}",
            "expectedRevision": session.revision,
            "actorId": action["actorId"],
            "skillId": action["skillId"],
            "targetIds": target_ids,
        },
    )

    assert result["accepted"] is True
    assert len(captured) == expected_targets
    assert all(attack_type == "ranged_projectile" for _, attack_type, _ in captured)
    assert all(attacker is actor for _, _, attacker in captured)

