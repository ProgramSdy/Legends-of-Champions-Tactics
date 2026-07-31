from __future__ import annotations

import pytest

from battle_api.adapter import BattleAdapter
from skills.skill import Debuff


def _controlled_session(source_definition: str):
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=202,
        battle_id=f"battle.restriction.{source_definition}",
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
    return adapter, session, source, target, next_actor


def _put_in_order(session, *actors):
    for hero in session.game.heroes:
        hero.actioned = hero not in actors
    session.game.unactioned_sorted_heroes = list(actors)


def _submit_named_skill(adapter, session, actor, target, skill_name):
    action = next(
        action
        for action in adapter._legal_actions(session, actor)
        if adapter._skill_by_id(actor, action["skillId"]).name == skill_name
    )
    return adapter.submit(
        session,
        {
            "type": "useSkill",
            "commandId": f"cmd.restriction.{skill_name}",
            "expectedRevision": session.revision,
            "actorId": action["actorId"],
            "skillId": action["skillId"],
            "targetIds": [adapter._combatant_id(session, target)],
        },
    )


@pytest.mark.parametrize("target_player_controlled", [True, False])
def test_actual_shield_bash_skips_restricted_target_for_either_control_mode(
    target_player_controlled,
):
    adapter, session, source, target, next_actor = _controlled_session(
        "hero.warrior.defence"
    )
    target.is_player_controlled = target_player_controlled
    _put_in_order(session, source, target, next_actor)
    target_id = adapter._combatant_id(session, target)

    result = _submit_named_skill(adapter, session, source, target, "Shield Bash")

    assert result["accepted"] is True
    assert any(
        event["type"] == "statusApplied"
        and event.get("statusId") == "status.stunned"
        and event.get("targetId") == target_id
        for event in result["events"]
    )
    target_turn = next(
        index
        for index, event in enumerate(result["events"])
        if event["type"] == "turnStarted" and event.get("sourceId") == target_id
    )
    target_end = next(
        index
        for index, event in enumerate(result["events"])
        if index > target_turn
        and event["type"] == "turnEnded"
        and event.get("sourceId") == target_id
    )
    assert "stunned" in result["events"][target_end]["message"]
    assert not any(
        event["type"] == "skillStarted" and event.get("sourceId") == target_id
        for event in result["events"][target_turn:target_end]
    )
    assert result["snapshot"]["activeCombatantId"] == adapter._combatant_id(
        session, next_actor
    )
    assert result["snapshot"]["turnControl"]["disposition"] == "playerCommand"
    assert result["snapshot"]["turnControl"]["acceptsCommands"] is True


@pytest.mark.parametrize(
    ("source_definition", "skill_name"),
    [
        ("hero.warrior.defence", "Shield Lash"),
        ("hero.paladin.protection", "Heroric Charge"),
    ],
)
@pytest.mark.parametrize("target_player_controlled", [True, False])
def test_actual_scoff_skills_force_the_engine_selected_attack_on_the_source(
    source_definition,
    skill_name,
    target_player_controlled,
):
    adapter, session, source, target, next_actor = _controlled_session(
        source_definition
    )
    target.is_player_controlled = target_player_controlled
    _put_in_order(session, source, target, next_actor)
    source_id = adapter._combatant_id(session, source)
    target_id = adapter._combatant_id(session, target)

    result = _submit_named_skill(adapter, session, source, target, skill_name)

    applied = next(
        event
        for event in result["events"]
        if event["type"] == "statusApplied"
        and event.get("statusId") == "status.scoff"
    )
    forced = next(
        event
        for event in result["events"]
        if event["type"] == "skillStarted" and event.get("sourceId") == target_id
    )
    removed = next(
        event
        for event in result["events"]
        if event["type"] == "statusRemoved"
        and event.get("statusId") == "status.scoff"
    )
    assert applied["targetId"] == target_id
    assert forced["targetIds"] == [source_id]
    assert removed["targetId"] == target_id
    assert target.status["scoff"] is False
    assert target.actioned is True
    assert result["snapshot"]["activeCombatantId"] == adapter._combatant_id(
        session, next_actor
    )


@pytest.mark.parametrize(
    ("restriction", "expected_disposition", "expected_reason"),
    [
        ("stunned", "skip", "stunned"),
        ("scoff", "automaticAction", "scoff"),
    ],
)
def test_turn_control_blocks_an_ordinary_command_at_the_public_adapter_boundary(
    restriction,
    expected_disposition,
    expected_reason,
):
    adapter, session, source, target, _ = _controlled_session(
        "hero.warrior.defence"
    )
    _put_in_order(session, target)
    if restriction == "stunned":
        target.status["stunned"] = True
        target.stun_duration = 1
    else:
        target.status["scoff"] = True
        target.add_debuff(Debuff("Scoff", 1, source, 1))
    target_id = adapter._combatant_id(session, target)
    source_id = adapter._combatant_id(session, source)
    snapshot = adapter.snapshot(session)
    skill = target.skills[0]

    result = adapter.submit(
        session,
        {
            "type": "useSkill",
            "commandId": f"cmd.illegal.{restriction}",
            "expectedRevision": session.revision,
            "actorId": target_id,
            "skillId": adapter._skill_id(target, skill),
            "targetIds": [source_id],
        },
    )

    assert snapshot["turnControl"] == {
        "disposition": expected_disposition,
        "acceptsCommands": False,
        "reasonId": expected_reason,
        "actorCombatantId": target_id,
        "sourceCombatantId": source_id if restriction == "scoff" else None,
        "forcedTargetIds": [source_id] if restriction == "scoff" else [],
    }
    assert snapshot["legalActions"] == []
    assert result["accepted"] is False
    assert result["code"] == "notYourTurn"
    assert session.revision == 0
    assert target.actioned is False


def test_scoff_directive_takes_precedence_over_an_in_progress_magic_cast():
    _, session, source, target, _ = _controlled_session(
        "hero.warrior.defence"
    )
    target.status["scoff"] = True
    target.status["magic_casting"] = True
    target.add_debuff(Debuff("Scoff", 1, source, 1))

    directive = target.turn_directive(
        target.opponents,
        target.allies,
        select_action=False,
    )

    assert directive.disposition == "automaticAction"
    assert directive.accepts_commands is False
    assert directive.reason_id == "scoff"
    assert directive.source is source
    assert directive.consume_scoff is True
