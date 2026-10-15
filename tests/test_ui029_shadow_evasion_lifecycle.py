"""UI-029: authoritative Shadow Evasion lifecycle coverage."""

from __future__ import annotations

from battle_api.adapter import BattleAdapter


def _command(adapter, session, action, command_id):
    return {
        "type": "useSkill",
        "commandId": command_id,
        "expectedRevision": session.revision,
        "actorId": action["actorId"],
        "skillId": action["skillId"],
        "targetIds": action["validTargetIds"][: action["minimumTargets"]],
    }


def test_shadow_evasion_is_published_then_removed_at_authoritative_expiry():
    adapter = BattleAdapter()
    session, envelope = adapter.create_battle(
        seed=42,
        battle_id="battle.ui029.shadow-evasion.lifecycle",
        enemy_control_mode="player",
    )
    opening = envelope["data"]["snapshot"]
    shadow_action = next(
        action
        for action in opening["legalActions"]
        if action["skillId"] == "skill.rogue.shadow_evasion"
    )

    applied = adapter.submit(
        session,
        _command(adapter, session, shadow_action, "cmd.ui029.shadow.apply"),
    )
    rogue_id = shadow_action["actorId"]
    rogue = applied["snapshot"]["combatants"][rogue_id]
    assert any(status["id"] == "status.shadow_evasion" for status in rogue["statuses"])
    assert next(
        event for event in applied["events"]
        if event["type"] == "statusApplied" and event.get("statusId") == "status.shadow_evasion"
    )["roundsRemaining"] == 1
    assert adapter._hero_by_id(session, rogue_id).evasion_capability == 100

    # The next player command completes the round. The status manager removes
    # the one-round status and emits the authoritative removal event.
    next_action = applied["snapshot"]["legalActions"][0]
    expired = adapter.submit(
        session,
        _command(adapter, session, next_action, "cmd.ui029.shadow.expire"),
    )
    expired_rogue = expired["snapshot"]["combatants"][rogue_id]
    assert not any(status["id"] == "status.shadow_evasion" for status in expired_rogue["statuses"])
    assert adapter._hero_by_id(session, rogue_id).evasion_capability == 0
    assert any(
        event["type"] == "statusRemoved"
        and event.get("statusId") == "status.shadow_evasion"
        and event.get("targetId") == rogue_id
        for event in expired["events"]
    )
