from __future__ import annotations

import random
import re

from battle_api.adapter import BattleAdapter
from game.hero_generator import HeroGenerator


ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def _create(
    *,
    seed: int | None,
    player_team: list[str],
    enemy_team: list[str],
):
    return BattleAdapter().create_battle(
        seed=seed,
        battle_id=f"battle.ui006.{seed}",
        battle_size=len(player_team),
        player_team=player_team,
        enemy_team=enemy_team,
        enemy_control_mode="player",
    )


def _display_names(envelope: dict) -> list[str]:
    snapshot = envelope["data"]["snapshot"]
    return [
        snapshot["combatants"][combatant_id]["displayName"]
        for side in snapshot["sides"]
        for combatant_id in side["combatantIds"]
    ]


def _submit_first_legal_action(adapter: BattleAdapter, session):
    snapshot = adapter.snapshot(session)
    action = snapshot["legalActions"][0]
    return adapter.submit(
        session,
        {
            "type": "useSkill",
            "commandId": "cmd.ui006.log.1",
            "expectedRevision": session.revision,
            "actorId": action["actorId"],
            "skillId": action["skillId"],
            "targetIds": action["validTargetIds"][: action["minimumTargets"]],
        },
    )


def test_runtime_names_use_faculty_pool_and_are_unique_while_names_remain():
    adapter = BattleAdapter()
    pool = set(HeroGenerator(adapter.engine_data).paladin_names_list)
    _, envelope = adapter.create_battle(
        seed=61,
        battle_id="battle.ui006.unique",
        battle_size=1,
        player_team=["hero.paladin.retribution"],
        enemy_team=["hero.paladin.protection"],
        enemy_control_mode="player",
    )

    names = _display_names(envelope)

    assert set(names) <= pool
    assert len(names) == len(set(names)) == 2


def test_runtime_name_pool_overflow_allows_repetition_without_creation_failure():
    team = [
        "hero.paladin.retribution",
        "hero.paladin.protection",
        "hero.paladin.retribution",
    ]
    adapter = BattleAdapter()
    pool = set(HeroGenerator(adapter.engine_data).paladin_names_list)

    _, envelope = adapter.create_battle(
        seed=62,
        battle_id="battle.ui006.overflow",
        battle_size=3,
        player_team=team,
        enemy_team=team,
        enemy_control_mode="player",
    )
    names = _display_names(envelope)

    assert len(names) == 6
    assert set(names) == pool
    assert len(set(names)) < len(names)


def test_priest_specializations_share_one_cross_team_faculty_pool_before_overflow():
    adapter = BattleAdapter()
    priest_pool = set(HeroGenerator(adapter.engine_data).priset_names_list)
    definitions = [
        "hero.priest.comprehensiveness",
        "hero.priest.discipline",
    ]

    _, envelope = adapter.create_battle(
        seed=42,
        battle_id="battle.ui006.priest-cross-team",
        battle_size=2,
        player_team=definitions,
        enemy_team=definitions,
        enemy_control_mode="player",
    )
    names = _display_names(envelope)

    assert set(names) == priest_pool
    assert len(set(names[: len(priest_pool)])) == len(priest_pool)
    assert names[3] in names[:3]


def test_seeded_runtime_names_are_reproducible_and_session_isolated():
    teams = {
        "player_team": [
            "hero.warrior.defence",
            "hero.warrior.weapon_master",
            "hero.paladin.protection",
        ],
        "enemy_team": [
            "hero.warrior.weapon_master",
            "hero.paladin.retribution",
            "hero.warrior.defence",
        ],
    }
    first_adapter = BattleAdapter()
    first_session, first = first_adapter.create_battle(
        seed=63,
        battle_id="battle.ui006.seeded.first",
        battle_size=3,
        enemy_control_mode="player",
        **teams,
    )
    before = _display_names(first)

    BattleAdapter().create_battle(
        seed=999,
        battle_id="battle.ui006.unrelated",
        battle_size=3,
        enemy_control_mode="player",
        **teams,
    )
    _, repeated = BattleAdapter().create_battle(
        seed=63,
        battle_id="battle.ui006.seeded.repeated",
        battle_size=3,
        enemy_control_mode="player",
        **teams,
    )

    assert _display_names(repeated) == before
    assert _display_names(first_adapter.envelope(first_session, {"snapshot": first_adapter.snapshot(first_session)}) ) == before


def test_unseeded_runtime_name_selection_does_not_leak_global_rng(monkeypatch):
    entropy = iter((101, 202))
    monkeypatch.setattr("battle_api.adapter.secrets.randbits", lambda _bits: next(entropy))
    global_state = random.getstate()

    first, _ = _create(
        seed=None,
        player_team=["hero.warrior.defence"],
        enemy_team=["hero.warrior.weapon_master"],
    )
    second, _ = _create(
        seed=None,
        player_team=["hero.warrior.defence"],
        enemy_team=["hero.warrior.weapon_master"],
    )

    assert first.rng_state != second.rng_state
    assert random.getstate() == global_state


def test_runtime_names_do_not_change_stable_definition_or_combatant_ids():
    _, envelope = _create(
        seed=64,
        player_team=["hero.warrior.weapon_master"],
        enemy_team=["hero.rogue.comprehensiveness"],
    )
    snapshot = envelope["data"]["snapshot"]

    assert snapshot["sides"][0]["combatantIds"] == ["friendly.ragnar"]
    assert snapshot["sides"][1]["combatantIds"] == ["enemy.nighthawk"]
    assert snapshot["combatants"]["friendly.ragnar"]["definitionId"] == "hero.warrior.weapon_master"
    assert snapshot["combatants"]["enemy.nighthawk"]["definitionId"] == "hero.rogue.comprehensiveness"
    assert snapshot["combatants"]["friendly.ragnar"]["displayName"] in HeroGenerator(BattleAdapter().engine_data).warrior_names_list
    assert snapshot["combatants"]["enemy.nighthawk"]["displayName"] in HeroGenerator(BattleAdapter().engine_data).rogue_names_list


def test_engine_authored_log_events_are_ordered_sanitized_and_keep_mutation_events():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=65,
        battle_id="battle.ui006.logs",
        player_team=["hero.warrior.weapon_master"],
        enemy_team=["hero.rogue.comprehensiveness"],
        enemy_control_mode="player",
    )

    result = _submit_first_legal_action(adapter, session)
    log_events = [event for event in result["events"] if event["type"] == "battleLog"]

    assert log_events
    assert [event["sequence"] for event in result["events"]] == sorted(
        event["sequence"] for event in result["events"]
    )
    assert all(event["message"].strip() for event in log_events)
    assert {event["channel"] for event in log_events} == {"battleInfo"}
    assert all(ANSI_ESCAPE.search(event["message"]) is None for event in log_events)
    assert len([event["message"] for event in log_events]) == len(
        set(event["message"] for event in log_events)
    )
    mutations = [
        event
        for event in result["events"]
        if event["type"] in {"damageApplied", "healingApplied", "statusApplied", "statusRemoved", "attackEvaded"}
    ]
    assert mutations
    assert all(event["visibleInLog"] is False for event in mutations)
    assert not any(
        "status." in event["message"] or "friendly." in event["message"] or "enemy." in event["message"]
        for event in log_events
    )


def test_presentation_log_channels_preserve_order_strip_ansi_and_drain_once():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=66,
        battle_id="battle.ui006.log-channels",
        player_team=["hero.warrior.weapon_master"],
        enemy_team=["hero.rogue.comprehensiveness"],
        enemy_control_mode="player",
    )
    session.game.display_battle_info("\x1b[91mFirst action line\x1b[0m")
    session.game.display_status_updates("\x1b[94mCooldown becomes available\x1b[0m")

    events = adapter._drain_presentation_log(session)

    assert [(event["channel"], event["message"]) for event in events] == [
        ("battleInfo", "First action line"),
        ("statusUpdate", "Cooldown becomes available"),
    ]
    assert [event["sequence"] for event in events] == sorted(
        event["sequence"] for event in events
    )
    assert adapter._drain_presentation_log(session) == []


def test_real_round_transition_emits_sanitized_status_log_and_typed_mutations():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=67,
        battle_id="battle.ui006.real-round-log",
        player_team=["hero.paladin.protection"],
        enemy_team=["hero.warrior.weapon_master"],
        enemy_control_mode="player",
    )
    all_events = []
    used_shield = False

    while session.game.round_counter == 1:
        snapshot = adapter.snapshot(session)
        actor_id = snapshot["activeCombatantId"]
        actor = snapshot["combatants"][actor_id]
        if actor["definitionId"] == "hero.paladin.protection":
            shield = next(
                skill
                for skill in actor["skills"]
                if skill["displayName"] == "Shield of Righteous"
            )
            action = next(
                action
                for action in snapshot["legalActions"]
                if action["skillId"] == shield["id"]
            )
            used_shield = True
        else:
            action = snapshot["legalActions"][0]
        result = adapter.submit(
            session,
            {
                "type": "useSkill",
                "commandId": f"cmd.ui006.round.{session.revision}",
                "expectedRevision": session.revision,
                "actorId": action["actorId"],
                "skillId": action["skillId"],
                "targetIds": action["validTargetIds"][: action["minimumTargets"]],
            },
        )
        assert result["accepted"] is True
        all_events.extend(result["events"])

    status_logs = [
        event
        for event in all_events
        if event["type"] == "battleLog" and event["channel"] == "statusUpdate"
    ]
    typed_mutations = [
        event
        for event in all_events
        if event["type"]
        in {"damageApplied", "healingApplied", "statusApplied", "statusRemoved", "attackEvaded"}
    ]

    assert used_shield is True
    assert session.game.round_counter == 2
    assert any("Shield of Righteous effect duration" in event["message"] for event in status_logs)
    assert all(ANSI_ESCAPE.search(event["message"]) is None for event in status_logs)
    assert [event["sequence"] for event in all_events] == sorted(
        event["sequence"] for event in all_events
    )
    assert len({event["id"] for event in all_events}) == len(all_events)
    assert typed_mutations
    assert all(event["visibleInLog"] is False for event in typed_mutations)
    assert len([event["message"] for event in status_logs]) == len(
        set(event["message"] for event in status_logs)
    )
