"""Regression coverage for live agility changes within an active round."""

from battle_api.adapter import BattleAdapter


def test_frost_bolt_reschedules_remaining_turns_and_serialized_turn_cards():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        battle_id="battle.dynamic-turn-order",
        seed=41,
        battle_size=2,
        player_team=[
            "hero.mage.comprehensiveness",
            "hero.warrior.weapon_master",
        ],
        enemy_composition_mode="specified",
        enemy_team=[
            "hero.rogue.comprehensiveness",
            "hero.paladin.retribution",
        ],
        enemy_control_mode="player",
        player_formation="side-by-side",
        enemy_formation="side-by-side",
    )
    mage, ally = session.game.player_heroes
    frost_target, remaining_enemy = session.game.opponent_heroes

    # Make the initial schedule deterministic: Frost Bolt's target begins
    # second, then drops below the two other unacted combatants after Cold.
    for hero, agility in zip(
        (mage, frost_target, remaining_enemy, ally), (100, 80, 70, 60)
    ):
        hero.agility = agility
        hero.original_agility = agility
        hero.actioned = False
    session.game.sorted_heroes = [mage, frost_target, remaining_enemy, ally]
    session.game.unactioned_sorted_heroes = [
        mage,
        frost_target,
        remaining_enemy,
        ally,
    ]

    frost_bolt = next(skill for skill in mage.skills if skill.name == "Frost Bolt")
    frost_bolt.evasion_check = lambda _target: False
    before = adapter.snapshot(session)
    result = adapter.submit(
        session,
        {
            "type": "useSkill",
            "commandId": "dynamic-frost-order",
            "expectedRevision": session.revision,
            "actorId": before["activeCombatantId"],
            "skillId": adapter._skill_id(mage, frost_bolt),
            "targetIds": [adapter._combatant_id(session, frost_target)],
        },
    )

    mage_id = adapter._combatant_id(session, mage)
    target_id = adapter._combatant_id(session, frost_target)
    remaining_enemy_id = adapter._combatant_id(session, remaining_enemy)
    ally_id = adapter._combatant_id(session, ally)

    assert frost_target.agility == 24
    assert result["snapshot"]["activeCombatantId"] == remaining_enemy_id
    assert [
        entry["combatantId"] for entry in result["snapshot"]["turnOrder"]
    ] == [mage_id, remaining_enemy_id, ally_id, target_id]
    turn_started = next(
        event for event in result["events"] if event["type"] == "turnStarted"
    )
    assert [entry["combatantId"] for entry in turn_started["turnOrder"]] == [
        mage_id,
        remaining_enemy_id,
        ally_id,
        target_id,
    ]
    assert result["snapshot"]["turnOrder"][0]["hasActed"] is True
    assert all(
        not entry["hasActed"]
        for entry in result["snapshot"]["turnOrder"][1:]
    )
