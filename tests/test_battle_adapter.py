from __future__ import annotations

from copy import deepcopy

import pytest

from battle_api.adapter import BattleAdapter, BattleRegistry


@pytest.fixture()
def adapter_session():
    adapter = BattleAdapter()
    session, envelope = adapter.create_battle(seed=42, battle_id="battle.test")
    return adapter, session, envelope


def command_for(adapter, session, command_id="cmd.1", action_index=0):
    snapshot = adapter.snapshot(session)
    action = snapshot["legalActions"][action_index]
    return {
        "type": "useSkill",
        "commandId": command_id,
        "expectedRevision": session.revision,
        "actorId": snapshot["activeCombatantId"],
        "skillId": action["skillId"],
        "targetIds": action["validTargetIds"][: action["minimumTargets"]],
    }


def test_seeded_creation_instantiates_ragnar_and_nighthawk(adapter_session):
    _, session, envelope = adapter_session
    snapshot = envelope["data"]["snapshot"]
    assert session.game.player_heroes[0].__class__.__name__ == "Warrior_Weapon_Master"
    assert session.game.opponent_heroes[0].__class__.__name__ == "Rogue_Comprehensiveness"
    assert snapshot["combatants"]["friendly.ragnar"]["displayName"] == "Ragnar"
    assert snapshot["combatants"]["enemy.nighthawk"]["displayName"] == "Nighthawk"
    assert snapshot["sides"][0]["maxSlots"] == 3
    assert snapshot["phase"] == "awaitingCommand"


def test_seed_is_reproducible_without_leaking_global_random_state():
    first = BattleAdapter().create_battle(seed=17, battle_id="battle.a")[1]
    second = BattleAdapter().create_battle(seed=17, battle_id="battle.b")[1]
    a = first["data"]["snapshot"]
    b = second["data"]["snapshot"]
    for combatant_id in ("friendly.ragnar", "enemy.nighthawk"):
        assert a["combatants"][combatant_id]["hp"] == b["combatants"][combatant_id]["hp"]
    assert a["activeCombatantId"] == b["activeCombatantId"]


def test_unseeded_creation_uses_fresh_entropy_without_leaking_global_state(monkeypatch):
    entropy = iter((101, 202))
    monkeypatch.setattr("battle_api.adapter.secrets.randbits", lambda _bits: next(entropy))
    global_state = __import__("random").getstate()

    first = BattleAdapter().create_battle(seed=None, battle_id="battle.random-a")[0]
    second = BattleAdapter().create_battle(seed=None, battle_id="battle.random-b")[0]

    assert first.seed is None
    assert second.seed is None
    assert first.rng_state != second.rng_state
    assert __import__("random").getstate() == global_state


def test_stable_definition_instance_and_skill_ids(adapter_session):
    adapter, session, _ = adapter_session
    first = adapter.snapshot(session)
    second = adapter.snapshot(session)
    assert first["combatants"].keys() == second["combatants"].keys()
    assert first["combatants"]["friendly.ragnar"]["definitionId"] == "hero.warrior.weapon_master"
    assert first["combatants"]["enemy.nighthawk"]["definitionId"] == "hero.rogue.comprehensiveness"
    assert {
        skill["id"] for skill in first["combatants"]["friendly.ragnar"]["skills"]
    } == {
        "skill.warrior.fatal_strike",
        "skill.warrior.armor_crush",
        "skill.warrior.antivenom_potion",
    }


def test_valid_command_returns_ordered_unique_events_and_reconciled_snapshot(adapter_session):
    adapter, session, _ = adapter_session
    result = adapter.submit(session, command_for(adapter, session))
    assert result["accepted"] is True
    assert result["revision"] == 1
    sequences = [event["sequence"] for event in result["events"]]
    ids = [event["id"] for event in result["events"]]
    assert sequences == sorted(sequences)
    assert len(ids) == len(set(ids))
    assert result["snapshot"] == adapter.snapshot(session)
    damage = next(event for event in result["events"] if event["type"] == "damageApplied")
    target = result["snapshot"]["combatants"][damage["targetId"]]
    assert damage["hpAfter"] == target["hp"]
    assert damage["amount"] > 0


@pytest.mark.parametrize(
    ("mutate", "code"),
    [
        (lambda c: c.update(expectedRevision=99), "staleRevision"),
        (lambda c: c.update(actorId="friendly.not-current"), "notYourTurn"),
        (lambda c: c.update(skillId="skill.does.not.exist"), "illegalSkill"),
        (lambda c: c.update(targetIds=[]), "illegalTargets"),
        (lambda c: c.update(targetIds=["friendly.ragnar", "enemy.nighthawk"]), "illegalTargets"),
        (lambda c: c.update(targetIds=["friendly.ragnar", "friendly.ragnar"]), "illegalTargets"),
        (lambda c: c.update(targetIds=["combatant.unknown"]), "illegalTargets"),
    ],
)
def test_rejections_do_not_mutate_authoritative_state(adapter_session, mutate, code):
    adapter, session, _ = adapter_session
    command = command_for(adapter, session)
    before = deepcopy(adapter.snapshot(session))
    mutate(command)
    result = adapter.submit(session, command)
    assert result["accepted"] is False
    assert result["code"] == code
    assert session.revision == 0
    assert adapter.snapshot(session) == before


def test_targetless_self_skill_accepts_zero_targets(adapter_session):
    adapter, session, _ = adapter_session
    snapshot = adapter.snapshot(session)
    # Seed 42 makes Nighthawk act first.
    action_index = next(
        index
        for index, action in enumerate(snapshot["legalActions"])
        if action["skillId"] == "skill.rogue.shadow_evasion"
    )
    command = command_for(adapter, session, action_index=action_index)
    assert command["targetIds"] == []
    result = adapter.submit(session, command)
    assert result["accepted"] is True
    state = result["snapshot"]["combatants"]["enemy.nighthawk"]
    assert any(status["id"] == "status.shadow_evasion" for status in state["statuses"])


def test_duplicate_command_is_idempotent(adapter_session):
    adapter, session, _ = adapter_session
    command = command_for(adapter, session)
    first = adapter.submit(session, command)
    state_after = deepcopy(adapter.snapshot(session))
    second = adapter.submit(session, command)
    assert second == first
    assert session.revision == 1
    assert adapter.snapshot(session) == state_after


def test_defeated_target_is_rejected_without_mutation(adapter_session, monkeypatch):
    adapter, session, _ = adapter_session
    snapshot = adapter.snapshot(session)
    actor_id = snapshot["activeCombatantId"]
    actor = adapter._hero_by_id(session, actor_id)
    opponent = next(hero for hero in session.game.heroes if hero.group != actor.group)
    opponent.hp = 0
    # The only current live format is 1v1, so defeating the sole opponent also
    # ends the battle. Hold the phase open to exercise the target-membership
    # guard that multi-combatant sessions will use.
    monkeypatch.setattr(adapter, "_is_ended", lambda _game: False)
    before = deepcopy(adapter.snapshot(session))
    command = {
        "type": "useSkill",
        "commandId": "cmd.defeated-target",
        "expectedRevision": session.revision,
        "actorId": actor_id,
        "skillId": next(
            skill["id"]
            for skill in before["combatants"][actor_id]["skills"]
            if skill["targetMode"] != "none"
        ),
        "targetIds": [adapter._combatant_id(session, opponent)],
    }

    result = adapter.submit(session, command)

    assert result["accepted"] is False
    assert result["code"] == "illegalTargets"
    assert result["snapshot"] == before
    assert adapter.snapshot(session) == before
    assert session.revision == 0


def test_duplicate_rejection_is_idempotent_and_keeps_original_snapshot(adapter_session):
    adapter, session, _ = adapter_session
    command = command_for(adapter, session, command_id="cmd.rejected")
    command["expectedRevision"] = 99

    first = adapter.submit(session, command)
    session.game.player_heroes[0].hp -= 1
    second = adapter.submit(session, {**command, "expectedRevision": 0})

    assert second == first
    assert second["code"] == "staleRevision"


def test_event_ids_remain_unique_across_multiple_commands(adapter_session):
    adapter, session, _ = adapter_session
    event_ids = []
    for index in range(4):
        result = adapter.submit(
            session, command_for(adapter, session, command_id=f"cmd.unique.{index}")
        )
        assert result["accepted"] is True
        event_ids.extend(event["id"] for event in result["events"])

    assert len(event_ids) == len(set(event_ids))


def test_legal_actions_reference_current_actor_and_only_living_targets(adapter_session):
    adapter, session, _ = adapter_session
    snapshot = adapter.snapshot(session)
    actor_id = snapshot["activeCombatantId"]

    assert snapshot["legalActions"]
    for action in snapshot["legalActions"]:
        assert action["actorId"] == actor_id
        assert action["minimumTargets"] <= action["maximumTargets"]
        for target_id in action["validTargetIds"]:
            assert snapshot["combatants"][target_id]["alive"] is True
            assert target_id != actor_id


def test_evade_event_has_no_amount_or_hp_mutation(adapter_session):
    adapter, session, _ = adapter_session
    nighthawk = session.game.opponent_heroes[0]
    ragnar = session.game.player_heroes[0]
    # Put Ragnar first and force Nighthawk's engine evasion branch.
    session.game.unactioned_sorted_heroes = [ragnar, nighthawk]
    nighthawk.evasion_capability = 100
    before_hp = nighthawk.hp
    result = adapter.submit(session, command_for(adapter, session))
    evade = next(event for event in result["events"] if event["type"] == "attackEvaded")
    assert "amount" not in evade
    assert "hpAfter" not in evade
    assert result["snapshot"]["combatants"]["enemy.nighthawk"]["hp"]["current"] == before_hp


def test_battle_can_progress_to_authoritative_end_and_reject_later_commands():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(seed=42, battle_id="battle.end")
    for index in range(60):
        snapshot = adapter.snapshot(session)
        if snapshot["phase"] == "ended":
            break
        result = adapter.submit(session, command_for(adapter, session, f"cmd.{index}"))
        assert result["accepted"]
    else:
        pytest.fail("seeded battle did not end")
    assert adapter.snapshot(session)["outcome"]["kind"] in {"victory", "draw", "roundLimit"}
    ended = adapter.snapshot(session)
    rejected = adapter.submit(
        session,
        {
            "type": "useSkill",
            "commandId": "cmd.after-end",
            "expectedRevision": session.revision,
            "actorId": ended["activeCombatantId"] or "friendly.ragnar",
            "skillId": "skill.warrior.fatal_strike",
            "targetIds": ["enemy.nighthawk"],
        },
    )
    assert rejected["code"] == "battleEnded"


def test_registry_is_process_local_and_returns_created_session():
    registry = BattleRegistry()
    session, _ = registry.create(seed=3)
    assert registry.get(session.battle_id) is session
    assert registry.get("missing") is None
