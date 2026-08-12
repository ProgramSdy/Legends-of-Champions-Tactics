from __future__ import annotations

from copy import deepcopy
import re
from types import SimpleNamespace

import pytest

from battle_api.adapter import (
    HERO_ROSTER,
    ROOT,
    STATUS_KINDS,
    BattleAdapter,
    BattleRegistry,
)
from game.hero_generator import HeroGenerator
from skills.skill import Buff, Debuff


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


def test_seeded_creation_instantiates_expected_definitions_with_faculty_names(adapter_session):
    adapter, session, envelope = adapter_session
    snapshot = envelope["data"]["snapshot"]
    names = HeroGenerator(adapter.engine_data)
    assert session.game.player_heroes[0].__class__.__name__ == "Warrior_Weapon_Master"
    assert session.game.opponent_heroes[0].__class__.__name__ == "Rogue_Comprehensiveness"
    assert snapshot["combatants"]["friendly.ragnar"]["displayName"] in names.warrior_names_list
    assert snapshot["combatants"]["enemy.nighthawk"]["displayName"] in names.rogue_names_list
    assert snapshot["sides"][0]["maxSlots"] == 3
    assert snapshot["phase"] == "awaitingCommand"


def test_enemy_first_creation_exposes_playable_opening_and_preserves_final_state():
    adapter = BattleAdapter()
    _session, envelope = adapter.create_battle(
        seed=42, battle_id="battle.opening.enemy", enemy_control_mode="computer"
    )
    data = envelope["data"]
    opening = data["openingSnapshot"]
    final = data["snapshot"]

    assert data["playOpening"] is True
    assert opening["phase"] != "ended"
    assert opening["activeCombatantId"] == "enemy.nighthawk"
    assert final["phase"] in {"awaitingCommand", "roundStart", "ended"}
    events = data["events"]
    assert [event["sequence"] for event in events] == sorted(event["sequence"] for event in events)
    assert len({event["id"] for event in events}) == len(events)
    assert any(event["sourceId"] == "enemy.nighthawk" for event in events if event.get("sourceId"))


def test_player_first_creation_keeps_opening_and_final_snapshots_reproducible():
    first = BattleAdapter().create_battle(
        seed=42, battle_id="battle.opening.player-a", enemy_control_mode="player"
    )[1]["data"]
    second = BattleAdapter().create_battle(
        seed=42, battle_id="battle.opening.player-b", enemy_control_mode="player"
    )[1]["data"]

    assert first["playOpening"] is False
    assert first["openingSnapshot"] == first["snapshot"]
    assert [
        (event["sequence"], event["type"], event["message"])
        for event in first["events"]
    ] == [
        (event["sequence"], event["type"], event["message"])
        for event in second["events"]
    ]
    assert first["openingSnapshot"] == second["openingSnapshot"]
    assert first["snapshot"] == second["snapshot"]


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


def test_full_hp_healing_skill_emits_zero_delta_presentation_event():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=13,
        battle_id="battle.full-hp-healing",
        player_team=["hero.priest.comprehensiveness"],
        enemy_team=["hero.rogue.comprehensiveness"],
    )
    healer = session.game.player_heroes[0]
    session.game.unactioned_sorted_heroes = [healer]
    snapshot = adapter.snapshot(session)
    action = next(
        action
        for action in snapshot["legalActions"]
        if action["skillId"] == "skill.priest.binding_heal"
    )
    target_id = action["validTargetIds"][0]
    hp_before = deepcopy(snapshot["combatants"][target_id]["hp"])

    result = adapter.submit(
        session,
        {
            "type": "useSkill",
            "commandId": "cmd.full-hp-healing",
            "expectedRevision": session.revision,
            "actorId": action["actorId"],
            "skillId": action["skillId"],
            "targetIds": [target_id],
        },
    )

    healing_events = [
        event
        for event in result["events"]
        if event["type"] == "healingApplied" and event.get("targetId") == target_id
    ]
    assert len(healing_events) == 1
    assert healing_events[0]["sourceId"] == action["actorId"]
    assert healing_events[0]["skillId"] == action["skillId"]
    assert healing_events[0]["amount"] == 0
    assert healing_events[0]["hpAfter"] == hp_before
    assert healing_events[0]["effectHint"] == "healing"
    assert result["snapshot"]["combatants"][target_id]["hp"] == hp_before


def test_binding_heal_does_not_emit_a_zero_delta_event_for_an_incidental_full_hp_caster():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=13,
        battle_id="battle.full-hp-binding-heal-ally",
        battle_size=2,
        player_team=[
            "hero.priest.comprehensiveness",
            "hero.priest.comprehensiveness",
        ],
        enemy_team=[
            "hero.rogue.comprehensiveness",
            "hero.rogue.comprehensiveness",
        ],
    )
    healer, selected_ally = session.game.player_heroes
    session.game.unactioned_sorted_heroes = [healer]
    snapshot = adapter.snapshot(session)
    action = next(
        action
        for action in snapshot["legalActions"]
        if action["skillId"] == "skill.priest.binding_heal"
    )
    selected_ally_id = adapter._combatant_id(session, selected_ally)
    assert selected_ally_id in action["validTargetIds"]

    result = adapter.submit(
        session,
        {
            "type": "useSkill",
            "commandId": "cmd.full-hp-binding-heal-ally",
            "expectedRevision": session.revision,
            "actorId": action["actorId"],
            "skillId": action["skillId"],
            "targetIds": [selected_ally_id],
        },
    )

    zero_delta_events = [
        event
        for event in result["events"]
        if event["type"] == "healingApplied"
        and event.get("skillId") == action["skillId"]
        and event.get("amount") == 0
    ]
    assert len(zero_delta_events) == 1
    assert zero_delta_events[0]["targetId"] == selected_ally_id


def test_zero_delta_healing_events_cover_each_full_hp_target_but_not_damage_skills():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=17,
        battle_id="battle.multi-full-hp-healing",
        battle_size=2,
        player_team=[
            "hero.priest.comprehensiveness",
            "hero.priest.comprehensiveness",
        ],
        enemy_team=[
            "hero.rogue.comprehensiveness",
            "hero.rogue.comprehensiveness",
        ],
    )
    actor = session.game.player_heroes[0]
    targets = session.game.player_heroes
    before = adapter._capture(session)
    healing_skill = SimpleNamespace(
        name="Test Group Heal",
        skill_type="healing",
        last_target_outcomes={},
    )

    healing_events = adapter._mutation_events(
        session, actor, healing_skill, targets, before, adapter._capture(session)
    )
    target_ids = {adapter._combatant_id(session, target) for target in targets}
    zero_delta_events = [
        event
        for event in healing_events
        if event["type"] == "healingApplied" and event["amount"] == 0
    ]
    zero_delta_targets = {
        event["targetId"]
        for event in zero_delta_events
    }
    assert len(zero_delta_events) == len(targets)
    assert zero_delta_targets == target_ids

    damage_skill = SimpleNamespace(
        name="Test Group Attack",
        skill_type="damage",
        last_target_outcomes={},
    )
    damage_events = adapter._mutation_events(
        session, actor, damage_skill, targets, before, adapter._capture(session)
    )
    assert not any(event["type"] == "healingApplied" for event in damage_events)


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


def test_status_delta_events_have_deterministic_status_id_order(adapter_session):
    adapter, session, _ = adapter_session
    actor = session.game.player_heroes[0]
    skill = actor.skills[0]
    combatant_id = adapter._combatant_id(session, actor)
    base = {"hp": actor.hp, "maximum": actor.hp_max}
    before = {
        combatant_id: {
            **base,
            "statuses": {
                "status.z_removed": {"roundsRemaining": 1},
                "status.y_removed": {"roundsRemaining": 1},
            },
        }
    }
    after = {
        combatant_id: {
            **base,
            "statuses": {
                "status.b_applied": {"roundsRemaining": 2},
                "status.a_applied": {"roundsRemaining": 3},
            },
        }
    }

    command_events = adapter._mutation_events(
        session, actor, skill, [], before, after
    )
    round_events = adapter._state_delta_events(session, before, after)

    assert [
        event["statusId"] for event in command_events
    ] == [
        "status.a_applied",
        "status.b_applied",
        "status.y_removed",
        "status.z_removed",
    ]
    assert [
        event["statusId"] for event in round_events
    ] == [
        "status.a_applied",
        "status.b_applied",
        "status.y_removed",
        "status.z_removed",
    ]


def test_status_application_events_add_authoritative_presentation_without_semantic_changes(
    adapter_session,
):
    adapter, session, _ = adapter_session
    actor = session.game.player_heroes[0]
    skill = actor.skills[0]
    combatant_id = adapter._combatant_id(session, actor)
    base = {"hp": actor.hp, "maximum": actor.hp_max}
    before = {
        combatant_id: {
            **base,
            "statuses": {
                "status.expiring": {"roundsRemaining": 1, "kind": "debuff"},
                "status.refresh": {"roundsRemaining": 1, "kind": "buff", "stacks": 1},
                "status.reduce": {"roundsRemaining": 4, "kind": "debuff", "stacks": 3},
                "status.tick": {"roundsRemaining": 4, "kind": "debuff", "stacks": 2},
            },
        }
    }
    after = {
        combatant_id: {
            **base,
            "statuses": {
                "status.beneficial": {"roundsRemaining": 3, "kind": "buff", "stacks": 2},
                "status.control": {"roundsRemaining": 2, "kind": "control", "stacks": 1},
                "status.unclassified": {"roundsRemaining": None, "stacks": None},
                "status.refresh": {"roundsRemaining": 2, "kind": "buff", "stacks": 3},
                "status.reduce": {"roundsRemaining": 1, "kind": "debuff", "stacks": 2},
                "status.tick": {"roundsRemaining": 3, "kind": "debuff", "stacks": 2},
            },
        }
    }
    before_unchanged = deepcopy(before)
    after_unchanged = deepcopy(after)

    command_events = adapter._mutation_events(
        session, actor, skill, [], before, after
    )
    round_events = adapter._state_delta_events(session, before, after)

    expected = [
        ("status.beneficial", "buff", 3, 2),
        ("status.control", "debuff", 2, 1),
        ("status.reduce", "debuff", 1, 2),
        ("status.refresh", "buff", 2, 3),
        ("status.unclassified", "neutral", None, None),
    ]
    for events in (command_events, round_events):
        applied = [event for event in events if event["type"] == "statusApplied"]
        assert [
            (
                event["statusId"],
                event["statusPresentation"],
                event.get("roundsRemaining"),
                event.get("stacks"),
            )
            for event in applied
        ] == expected
        assert all(event["targetId"] == combatant_id for event in applied)
        assert all(event["effectHint"] == "status" for event in applied)
        assert not any(event["statusId"] == "status.tick" for event in applied)
        removed = next(event for event in events if event["type"] == "statusRemoved")
        assert "statusPresentation" not in removed
        assert removed["effectHint"] == "status"

    assert before == before_unchanged
    assert after == after_unchanged


def test_every_adapter_status_has_frontend_tooltip_metadata():
    registry_source = (
        ROOT / "web-ui" / "lib" / "battle" / "assets.ts"
    ).read_text(encoding="utf-8")
    registry_ids = set(
        re.findall(r'^\s*"(?P<id>status\.[^"]+)":\s*\{', registry_source, re.MULTILINE)
    )

    assert {f"status.{status_key}" for status_key in STATUS_KINDS} <= registry_ids


def test_ui016_statuses_serialize_kind_duration_source_and_application_events():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=1601,
        battle_id="battle.ui016.status-contract",
        battle_size=2,
        player_team=["hero.paladin.holy", "hero.warrior.berserker"],
        enemy_team=[
            "hero.rogue.comprehensiveness",
            "hero.warrior.berserker",
        ],
    )
    paladin, berserker = session.game.player_heroes
    moon_target = session.game.opponent_heroes[0]
    before = adapter._capture(session)

    paladin.status["purify_healing"] = True
    paladin.add_buff(Buff("Purify Healing", 2, paladin, 1.0))
    paladin.status["shield_of_protection"] = True
    paladin.shield_of_protection_duration = 2
    berserker.status["warlust"] = True
    berserker.warlust_duration = 2
    berserker.status["blood_frenzy"] = True
    berserker.blood_frenzy_duration = 2
    moon_target.status["bleeding_moon_slash"] = True
    moon_target.bleeding_moon_slash_duration = 2
    moon_target.add_debuff(Debuff("Moon Slash", 2, berserker, 8))

    after = adapter._capture(session)
    events = adapter._mutation_events(
        session,
        berserker,
        berserker.skills[0],
        [],
        before,
        after,
    )
    applied = {
        event["statusId"]: event
        for event in events
        if event["type"] == "statusApplied"
    }
    paladin_id = adapter._combatant_id(session, paladin)
    berserker_id = adapter._combatant_id(session, berserker)
    moon_target_id = adapter._combatant_id(session, moon_target)
    expected = {
        "status.purify_healing": ("buff", 2, paladin_id, paladin_id),
        "status.shield_of_protection": ("buff", 2, paladin_id, paladin_id),
        "status.warlust": ("buff", 2, berserker_id, berserker_id),
        "status.blood_frenzy": ("buff", 2, berserker_id, berserker_id),
        "status.bleeding_moon_slash": (
            "debuff",
            2,
            berserker_id,
            moon_target_id,
        ),
    }

    assert set(applied) == set(expected)
    for status_id, (kind, duration, source_id, target_id) in expected.items():
        event = applied[status_id]
        serialized = after[target_id]["statuses"][status_id]
        assert serialized["kind"] == kind
        assert serialized["roundsRemaining"] == duration
        assert serialized["sourceCombatantId"] == source_id
        assert event["sourceId"] == source_id
        assert event["targetId"] == target_id
        assert event["roundsRemaining"] == duration
        assert event["statusPresentation"] == (
            "debuff" if kind == "debuff" else "buff"
        )


def test_blood_frenzy_has_one_activation_and_restoration_path(monkeypatch):
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=1602,
        battle_id="battle.ui016.blood-frenzy",
        player_team=["hero.warrior.berserker"],
        enemy_team=["hero.rogue.comprehensiveness"],
    )
    berserker = session.game.player_heroes[0]
    berserker.hp = int(berserker.hp_max * 0.5)
    defense_before = berserker.defense
    agility_before = berserker.agility
    monkeypatch.setattr("heroes.warrior.random.randint", lambda _low, _high: 1)

    berserker.take_damage(1)
    assert berserker.status["blood_frenzy"] is True
    assert berserker.blood_frenzy_duration == 2
    activated_stats = (berserker.defense, berserker.agility)
    assert activated_stats == (
        max(0, defense_before - round(defense_before / 2)),
        agility_before + 20,
    )
    assert berserker.trigger_blood_frenzy() is False
    assert (berserker.defense, berserker.agility) == activated_stats

    session.game.status_manager.check_heroes_status_effects(berserker)
    assert berserker.blood_frenzy_duration == 1
    session.game.status_manager.check_heroes_status_effects(berserker)

    assert berserker.status["blood_frenzy"] is False
    assert berserker.blood_frenzy_duration == 0
    assert (berserker.defense, berserker.agility) == (
        defense_before,
        agility_before,
    )
    assert berserker.defense_decreased_amount_by_blood_frenzy == 0
    assert berserker.agility_increased_amount_by_blood_frenzy == 0


def test_moon_slash_uses_own_duration_and_orders_tick_before_removal(monkeypatch):
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=1603,
        battle_id="battle.ui016.moon-slash",
        player_team=["hero.warrior.berserker"],
        enemy_team=["hero.rogue.comprehensiveness"],
    )
    source = session.game.player_heroes[0]
    target = session.game.opponent_heroes[0]
    target.status["bleeding_moon_slash"] = True
    target.bleeding_moon_slash_duration = 2
    target.bleeding_slash_duration = 7
    target.bleeding_moon_slash_continuous_damage = 8
    target.add_debuff(Debuff("Moon Slash", 2, source, 8))
    monkeypatch.setattr(
        "game.status_effect_manager.random.randint", lambda _low, _high: 0
    )

    before_tick = adapter._capture(session)
    session.game.status_manager.check_heroes_status_effects(target)
    after_tick = adapter._capture(session)
    tick_events = adapter._state_delta_events(session, before_tick, after_tick)
    before_removal = adapter._capture(session)
    session.game.status_manager.check_heroes_status_effects(target)
    after_removal = adapter._capture(session)
    removal_events = adapter._state_delta_events(
        session, before_removal, after_removal
    )

    assert target.bleeding_slash_duration == 7
    assert target.status["bleeding_moon_slash"] is False
    assert [event["type"] for event in tick_events] == ["damageApplied"]
    assert tick_events[0]["amount"] == 8
    assert [event["type"] for event in removal_events] == ["statusRemoved"]
    assert removal_events[0]["statusId"] == "status.bleeding_moon_slash"
    assert removal_events[0]["sourceId"] == adapter._combatant_id(
        session, source
    )
    assert tick_events[0]["sequence"] < removal_events[0]["sequence"]


def test_moon_slash_named_record_tracks_latest_duplicate_berserker_source(
    monkeypatch,
):
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=1606,
        battle_id="battle.ui016.moon-source",
        battle_size=2,
        player_team=[
            "hero.warrior.berserker",
            "hero.warrior.berserker",
        ],
        enemy_team=[
            "hero.rogue.comprehensiveness",
            "hero.priest.comprehensiveness",
        ],
    )
    first_source, second_source = session.game.player_heroes
    target = session.game.opponent_heroes[0]
    target.status["armor_breaker"] = True
    monkeypatch.setattr("heroes.warrior.random.randint", lambda low, _high: low)

    first_source.moon_slash(target)
    first = adapter._active_statuses(session, target)[
        "status.bleeding_moon_slash"
    ]
    second_source.moon_slash(target)
    second = adapter._active_statuses(session, target)[
        "status.bleeding_moon_slash"
    ]
    moon_records = [
        debuff for debuff in target.debuffs if debuff.name == "Moon Slash"
    ]

    assert first["sourceCombatantId"] == adapter._combatant_id(
        session, first_source
    )
    assert second["sourceCombatantId"] == adapter._combatant_id(
        session, second_source
    )
    assert second["roundsRemaining"] == 2
    assert len(moon_records) == 1
    assert moon_records[0].initiator is second_source


def test_purify_healing_refreshes_and_dispels_only_eligible_category(monkeypatch):
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=1604,
        battle_id="battle.ui016.purify",
        battle_size=2,
        player_team=[
            "hero.paladin.holy",
            "hero.rogue.comprehensiveness",
        ],
        enemy_team=[
            "hero.warrior.weapon_master",
            "hero.mage.comprehensiveness",
        ],
    )
    paladin, ally = session.game.player_heroes
    ally.hp -= 40
    ally.status["bleeding_moon_slash"] = True
    ally.bleeding_moon_slash_duration = 2
    ally.bleeding_moon_slash_continuous_damage = 8
    ally.add_debuff(Debuff("Moon Slash", 2, session.game.opponent_heroes[0], 8))
    ally.status["stunned"] = True
    ally.stun_duration = 1
    monkeypatch.setattr("heroes.paladin.random.randint", lambda _low, _high: 0)

    paladin.purify_healing(ally)
    purify_buffs = [buff for buff in ally.buffs if buff.name == "Purify Healing"]
    assert ally.status["purify_healing"] is True
    assert ally.status["bleeding_moon_slash"] is False
    assert ally.status["stunned"] is True
    assert len(purify_buffs) == 1
    assert purify_buffs[0].duration == 2

    purify_buffs[0].duration = 1
    paladin.purify_healing(ally)
    assert len([buff for buff in ally.buffs if buff.name == "Purify Healing"]) == 1
    assert purify_buffs[0].duration == 2
    serialized = adapter._active_statuses(session, ally)["status.purify_healing"]
    assert serialized["roundsRemaining"] == 2
    assert serialized["sourceCombatantId"] == adapter._combatant_id(
        session, paladin
    )
    before_removal = adapter._capture(session)
    session.game.status_manager.check_heroes_status_effects(ally)
    session.game.status_manager.check_heroes_status_effects(ally)
    removal_events = adapter._state_delta_events(
        session, before_removal, adapter._capture(session)
    )
    assert ally.status["purify_healing"] is False
    assert not any(buff.name == "Purify Healing" for buff in ally.buffs)
    assert any(
        event["type"] == "statusRemoved"
        and event["statusId"] == "status.purify_healing"
        and event["sourceId"] == adapter._combatant_id(session, paladin)
        for event in removal_events
    )


def test_shield_of_protection_activation_and_cleanup_remain_engine_owned():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=1607,
        battle_id="battle.ui016.shield-lifecycle",
        player_team=["hero.paladin.holy"],
        enemy_team=["hero.rogue.comprehensiveness"],
    )
    paladin = session.game.player_heroes[0]
    shield_skill = next(
        skill for skill in paladin.skills if skill.name == "Shield of Protection"
    )
    before = adapter._capture(session)

    paladin.shield_of_protection()
    applied = adapter._state_delta_events(
        session, before, adapter._capture(session)
    )

    assert paladin.status["shield_of_protection"] is True
    assert paladin.shield_of_protection_duration == 2
    assert shield_skill.if_cooldown is True
    assert shield_skill.cooldown == 3
    assert any(
        event["type"] == "statusApplied"
        and event["statusId"] == "status.shield_of_protection"
        and event["sourceId"] == adapter._combatant_id(session, paladin)
        for event in applied
    )

    before_removal = adapter._capture(session)
    session.game.status_manager.check_heroes_status_effects(paladin)
    session.game.status_manager.check_heroes_status_effects(paladin)
    removed = adapter._state_delta_events(
        session, before_removal, adapter._capture(session)
    )

    assert paladin.status["shield_of_protection"] is False
    assert paladin.shield_of_protection_duration == 0
    assert any(
        event["type"] == "statusRemoved"
        and event["statusId"] == "status.shield_of_protection"
        and event["sourceId"] == adapter._combatant_id(session, paladin)
        for event in removed
    )


def test_warlust_control_immunity_expires_and_restores_damage():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=1605,
        battle_id="battle.ui016.warlust",
        player_team=["hero.warrior.berserker"],
        enemy_team=["hero.rogue.comprehensiveness"],
    )
    berserker = session.game.player_heroes[0]
    damage_before = berserker.damage

    berserker.warlust()
    assert berserker.status["warlust"] is True
    assert berserker.is_immunity_condition_control is True
    assert berserker.damage > damage_before
    session.game.status_manager.check_heroes_status_effects(berserker)
    session.game.status_manager.check_heroes_status_effects(berserker)

    assert berserker.status["warlust"] is False
    assert berserker.is_immunity_condition_control is False
    assert berserker.damage == damage_before


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


def test_approved_roster_constructs_with_stable_definition_and_skill_ids():
    adapter = BattleAdapter()

    for index, definition_id in enumerate(HERO_ROSTER):
        session, envelope = adapter.create_battle(
            seed=100 + index,
            battle_id=f"battle.roster.{index}",
            player_team=[definition_id],
            enemy_team=["hero.rogue.comprehensiveness"],
        )
        friendly_id = envelope["data"]["snapshot"]["sides"][0]["combatantIds"][0]
        combatant = envelope["data"]["snapshot"]["combatants"][friendly_id]

        assert combatant["definitionId"] == definition_id
        assert combatant["isPlayerControlled"] is True
        assert len(combatant["skills"]) == 3
        assert all(skill["id"].startswith("skill.") for skill in combatant["skills"])
        assert adapter.snapshot(session)["combatants"][friendly_id]["skills"] == combatant["skills"]


@pytest.mark.parametrize(
    ("definition_id", "class_name", "expected_skill_ids"),
    [
        (
            "hero.warrior.berserker",
            "Warrior_Berserker",
            {
                "skill.warrior.moon_slash",
                "skill.warrior.warlust",
                "skill.warrior.hammer_of_meteorite",
            },
        ),
        (
            "hero.paladin.holy",
            "Paladin_Holy",
            {
                "skill.paladin.purify_healing",
                "skill.paladin.holy_blast",
                "skill.paladin.shield_of_protection",
            },
        ),
    ],
)
def test_new_roster_heroes_serialize_and_execute_live_actions(
    definition_id, class_name, expected_skill_ids
):
    adapter = BattleAdapter()
    session, envelope = adapter.create_battle(
        seed=47,
        battle_id=f"battle.new-roster.{definition_id}",
        player_team=[definition_id],
        enemy_team=["hero.rogue.comprehensiveness"],
    )
    actor = session.game.player_heroes[0]
    session.game.unactioned_sorted_heroes = [actor]
    snapshot = adapter.snapshot(session)
    actor_id = snapshot["sides"][0]["combatantIds"][0]
    combatant = snapshot["combatants"][actor_id]

    assert actor.__class__.__name__ == class_name
    assert combatant["definitionId"] == definition_id
    assert {skill["id"] for skill in combatant["skills"]} == expected_skill_ids

    action = snapshot["legalActions"][0]
    result = adapter.submit(
        session,
        {
            "type": "useSkill",
            "commandId": f"cmd.new-roster.{definition_id}",
            "expectedRevision": 0,
            "actorId": actor_id,
            "skillId": action["skillId"],
            "targetIds": action["validTargetIds"][: action["minimumTargets"]],
        },
    )

    assert result["accepted"] is True
    assert result["snapshot"]["combatants"][actor_id]["definitionId"] == definition_id


@pytest.mark.parametrize("definition_id", list(HERO_ROSTER))
def test_every_approved_hero_can_submit_a_legal_live_action(definition_id):
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=101,
        battle_id=f"battle.action.{definition_id}",
        player_team=[definition_id],
        enemy_team=["hero.rogue.comprehensiveness"],
    )
    actor = session.game.player_heroes[0]
    session.game.unactioned_sorted_heroes = [actor]
    snapshot = adapter.snapshot(session)
    action = snapshot["legalActions"][0]

    result = adapter.submit(
        session,
        {
            "type": "useSkill",
            "commandId": f"cmd.action.{definition_id}",
            "expectedRevision": session.revision,
            "actorId": action["actorId"],
            "skillId": action["skillId"],
            "targetIds": action["validTargetIds"][: action["minimumTargets"]],
        },
    )

    assert result["accepted"] is True
    assert result["revision"] == 1
    assert result["snapshot"] == adapter.snapshot(session)


@pytest.mark.parametrize("battle_size", [1, 2, 3])
def test_configured_battle_preserves_slots_duplicates_and_control_mode(battle_size):
    adapter = BattleAdapter()
    repeated = ["hero.priest.comprehensiveness"] * battle_size
    session, envelope = adapter.create_battle(
        seed=7,
        battle_id=f"battle.size.{battle_size}",
        battle_size=battle_size,
        player_team=repeated,
        enemy_team=repeated,
        enemy_control_mode="player",
    )
    snapshot = envelope["data"]["snapshot"]

    assert len(snapshot["sides"][0]["combatantIds"]) == battle_size
    assert len(snapshot["sides"][1]["combatantIds"]) == battle_size
    assert len(set(snapshot["combatants"])) == battle_size * 2
    assert all(
        combatant["isPlayerControlled"]
        for combatant in snapshot["combatants"].values()
    )
    assert session.battle_size == battle_size


def test_player_controlled_enemy_turn_exposes_and_accepts_legal_actions():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=19,
        battle_id="battle.enemy-player",
        battle_size=2,
        player_team=[
            "hero.priest.comprehensiveness",
            "hero.warrior.weapon_master",
        ],
        enemy_team=[
            "hero.mage.comprehensiveness",
            "hero.rogue.comprehensiveness",
        ],
        enemy_control_mode="player",
    )
    enemy_actor = session.game.opponent_heroes[0]
    session.game.unactioned_sorted_heroes = [enemy_actor]
    snapshot = adapter.snapshot(session)
    action = snapshot["legalActions"][0]

    assert snapshot["combatants"][action["actorId"]]["sideId"] == "enemy"
    assert snapshot["combatants"][action["actorId"]]["isPlayerControlled"] is True
    result = adapter.submit(
        session,
        {
            "type": "useSkill",
            "commandId": "cmd.enemy-player",
            "expectedRevision": session.revision,
            "actorId": action["actorId"],
            "skillId": action["skillId"],
            "targetIds": action["validTargetIds"][: action["minimumTargets"]],
        },
    )
    assert result["accepted"] is True


def test_seeded_random_enemy_composition_is_complete_and_reproducible():
    kwargs = {
        "seed": 29,
        "battle_size": 3,
        "player_team": list(HERO_ROSTER)[:3],
        "enemy_composition_mode": "random",
        "enemy_control_mode": "player",
    }
    first = BattleAdapter().create_battle(battle_id="battle.random.1", **kwargs)[1]
    second = BattleAdapter().create_battle(battle_id="battle.random.2", **kwargs)[1]

    def enemy_definitions(envelope):
        snapshot = envelope["data"]["snapshot"]
        return [
            snapshot["combatants"][combatant_id]["definitionId"]
            for combatant_id in snapshot["sides"][1]["combatantIds"]
        ]

    assert enemy_definitions(first) == enemy_definitions(second)
    assert len(enemy_definitions(first)) == 3


def test_equal_seed_random_creation_can_select_new_heroes_with_deterministic_names():
    kwargs = {
        "seed": 17,
        "battle_size": 3,
        "player_team": [
            "hero.priest.comprehensiveness",
            "hero.mage.comprehensiveness",
            "hero.rogue.comprehensiveness",
        ],
        "enemy_composition_mode": "random",
        "enemy_control_mode": "player",
    }
    first = BattleAdapter().create_battle(battle_id="battle.new-random.1", **kwargs)[1]
    second = BattleAdapter().create_battle(battle_id="battle.new-random.2", **kwargs)[1]

    def enemy_identity(envelope):
        snapshot = envelope["data"]["snapshot"]
        return [
            (
                snapshot["combatants"][combatant_id]["definitionId"],
                snapshot["combatants"][combatant_id]["displayName"],
            )
            for combatant_id in snapshot["sides"][1]["combatantIds"]
        ]

    first_identity = enemy_identity(first)
    assert {definition_id for definition_id, _name in first_identity} >= {
        "hero.warrior.berserker",
        "hero.paladin.holy",
    }
    assert first_identity == enemy_identity(second)


def test_computer_enemy_turns_are_drained_to_human_or_battle_end():
    adapter = BattleAdapter()
    session, envelope = adapter.create_battle(
        seed=3,
        battle_id="battle.computer",
        battle_size=3,
        player_team=list(HERO_ROSTER)[:3],
        enemy_composition_mode="random",
        enemy_control_mode="computer",
    )
    snapshot = envelope["data"]["snapshot"]

    assert snapshot["phase"] == "ended" or snapshot["combatants"][
        snapshot["activeCombatantId"]
    ]["isPlayerControlled"]
    assert all(
        not snapshot["combatants"][combatant_id]["isPlayerControlled"]
        for combatant_id in snapshot["sides"][1]["combatantIds"]
    )

    if snapshot["phase"] != "ended":
        action = snapshot["legalActions"][0]
        result = adapter.submit(
            session,
            {
                "type": "useSkill",
                "commandId": "cmd.before-ai",
                "expectedRevision": session.revision,
                "actorId": action["actorId"],
                "skillId": action["skillId"],
                "targetIds": action["validTargetIds"][: action["minimumTargets"]],
            },
        )
        final = result["snapshot"]
        assert final["phase"] == "ended" or final["combatants"][
            final["activeCombatantId"]
        ]["isPlayerControlled"]
        assert result["revision"] == session.revision


def test_stunned_player_turn_is_skipped_before_legal_actions_are_exposed():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=31,
        battle_id="battle.stunned-player",
        battle_size=2,
        player_team=[
            "hero.warrior.defence",
            "hero.priest.comprehensiveness",
        ],
        enemy_team=[
            "hero.rogue.comprehensiveness",
            "hero.mage.comprehensiveness",
        ],
        enemy_control_mode="player",
    )
    stunned = session.game.player_heroes[0]
    next_actor = session.game.player_heroes[1]
    stunned.status["stunned"] = True
    stunned.stun_duration = 1
    session.game.unactioned_sorted_heroes = [stunned, next_actor]

    assert adapter.snapshot(session)["legalActions"] == []
    events = adapter._drain_automatic_turns(session)
    snapshot = adapter.snapshot(session)

    assert [event["type"] for event in events] == ["turnEnded", "turnStarted"]
    assert events[0]["sourceId"] == adapter._combatant_id(session, stunned)
    assert "stunned" in events[0]["message"]
    assert stunned.actioned is True
    assert snapshot["activeCombatantId"] == adapter._combatant_id(session, next_actor)
    assert snapshot["legalActions"]
    assert session.revision == 1


def test_stunned_computer_turn_skips_without_executing_a_skill():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=37,
        battle_id="battle.stunned-computer",
        player_team=["hero.priest.comprehensiveness"],
        enemy_team=["hero.warrior.defence"],
        enemy_control_mode="computer",
    )
    computer = session.game.opponent_heroes[0]
    player = session.game.player_heroes[0]
    computer.status["stunned"] = True
    computer.stun_duration = 1
    computer.actioned = False
    player.actioned = False
    session.game.unactioned_sorted_heroes = [computer, player]
    revision_before = session.revision

    events = adapter._drain_automatic_turns(session)
    snapshot = adapter.snapshot(session)

    assert not any(event["type"] == "skillStarted" for event in events)
    assert [event["type"] for event in events] == ["turnEnded", "turnStarted"]
    assert events[0]["sourceId"] == adapter._combatant_id(session, computer)
    assert computer.actioned is True
    assert snapshot["activeCombatantId"] == adapter._combatant_id(session, player)
    assert snapshot["legalActions"]
    assert session.revision == revision_before + 1


@pytest.mark.parametrize("player_controlled", [True, False])
def test_scoff_forces_python_ai_attack_on_initiator_without_client_choice(
    player_controlled,
):
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=41,
        battle_id=f"battle.scoff.{player_controlled}",
        battle_size=2,
        player_team=[
            "hero.warrior.defence",
            "hero.priest.comprehensiveness",
        ],
        enemy_team=[
            "hero.rogue.comprehensiveness",
            "hero.mage.comprehensiveness",
        ],
        enemy_control_mode="player" if player_controlled else "computer",
    )
    source = session.game.player_heroes[0]
    other_target = session.game.player_heroes[1]
    scoffed = session.game.opponent_heroes[0]
    next_actor = session.game.opponent_heroes[1]
    next_actor.is_player_controlled = True
    scoffed.status["scoff"] = True
    scoffed.add_debuff(Debuff("Scoff", 1, source, 1))
    for hero in session.game.heroes:
        hero.actioned = hero not in {scoffed, next_actor}
    session.game.unactioned_sorted_heroes = [scoffed, next_actor]
    revision_before = session.revision

    snapshot_before = adapter.snapshot(session)
    assert snapshot_before["activeCombatantId"] == adapter._combatant_id(
        session, scoffed
    )
    assert snapshot_before["legalActions"] == []

    events = adapter._drain_automatic_turns(session)
    skill_event = next(event for event in events if event["type"] == "skillStarted")
    status_removed = next(
        event
        for event in events
        if event["type"] == "statusRemoved"
        and event.get("statusId") == "status.scoff"
    )
    snapshot_after = adapter.snapshot(session)

    assert skill_event["sourceId"] == adapter._combatant_id(session, scoffed)
    assert skill_event["targetIds"] == [adapter._combatant_id(session, source)]
    assert adapter._combatant_id(session, other_target) not in skill_event["targetIds"]
    assert status_removed["targetId"] == adapter._combatant_id(session, scoffed)
    assert scoffed.status["scoff"] is False
    assert scoffed.actioned is True
    assert snapshot_after["activeCombatantId"] == adapter._combatant_id(
        session, next_actor
    )
    assert snapshot_after["legalActions"]
    assert session.revision == revision_before + 1


@pytest.mark.parametrize("player_controlled", [True, False])
def test_dead_scoff_source_is_removed_before_normal_control_resumes(
    player_controlled,
):
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=43,
        battle_id=f"battle.scoff-dead-source.{player_controlled}",
        battle_size=2,
        player_team=[
            "hero.warrior.defence",
            "hero.priest.comprehensiveness",
        ],
        enemy_team=[
            "hero.rogue.comprehensiveness",
            "hero.mage.comprehensiveness",
        ],
        enemy_control_mode="player" if player_controlled else "computer",
    )
    dead_source = session.game.player_heroes[0]
    living_target = session.game.player_heroes[1]
    scoffed = session.game.opponent_heroes[0]
    next_actor = session.game.opponent_heroes[1]
    dead_source.hp = 0
    scoffed.status["scoff"] = True
    scoffed.add_debuff(Debuff("Scoff", 1, dead_source, 1))
    for skill in scoffed.skills:
        if skill.target_qty == 0:
            skill.if_cooldown = True
    next_actor.is_player_controlled = True
    for hero in session.game.heroes:
        hero.actioned = hero not in {scoffed, next_actor}
    session.game.unactioned_sorted_heroes = [scoffed, next_actor]
    session.game.update_allies_opponents_list()
    revision_before = session.revision
    dead_source_id = adapter._combatant_id(session, dead_source)
    living_target_id = adapter._combatant_id(session, living_target)
    scoffed_id = adapter._combatant_id(session, scoffed)

    assert adapter.snapshot(session)["legalActions"] == []
    events = adapter._drain_automatic_turns(session)
    snapshot = adapter.snapshot(session)
    removed = [
        event
        for event in events
        if event["type"] == "statusRemoved"
        and event.get("statusId") == "status.scoff"
    ]

    assert len(removed) == 1
    assert removed[0]["targetId"] == scoffed_id
    assert scoffed.status["scoff"] is False
    assert all(dead_source_id not in event.get("targetIds", []) for event in events)
    assert [event["sequence"] for event in events] == sorted(
        event["sequence"] for event in events
    )

    if player_controlled:
        assert not any(event["type"] == "skillStarted" for event in events)
        assert snapshot["activeCombatantId"] == scoffed_id
        assert snapshot["legalActions"]
        assert all(
            dead_source_id not in action["validTargetIds"]
            for action in snapshot["legalActions"]
        )
        assert scoffed.actioned is False
        assert session.revision == revision_before + 1
    else:
        skill_event = next(
            event for event in events if event["type"] == "skillStarted"
        )
        assert skill_event["sourceId"] == scoffed_id
        selected_skill = adapter._skill_by_id(
            scoffed, skill_event["skillId"]
        )
        assert selected_skill is not None
        assert skill_event["targetIds"] in (
            [],
            [living_target_id],
        )
        assert bool(skill_event["targetIds"]) is bool(
            selected_skill.target_qty
        )
        assert scoffed.actioned is True
        assert snapshot["activeCombatantId"] == adapter._combatant_id(
            session, next_actor
        )
        assert session.revision == revision_before + 2


def test_multi_target_skill_contracts_to_available_living_targets():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=4,
        battle_id="battle.multi-target",
        player_team=["hero.mage.comprehensiveness"],
        enemy_team=["hero.rogue.comprehensiveness"],
    )
    mage = session.game.player_heroes[0]
    session.game.unactioned_sorted_heroes = [mage]
    snapshot = adapter.snapshot(session)
    action = next(
        action
        for action in snapshot["legalActions"]
        if action["skillId"] == "skill.mage.arcane_missiles"
    )

    assert action["minimumTargets"] == action["maximumTargets"] == 1
    result = adapter.submit(
        session,
        {
            "type": "useSkill",
            "commandId": "cmd.arcane",
            "expectedRevision": 0,
            "actorId": snapshot["activeCombatantId"],
            "skillId": action["skillId"],
            "targetIds": action["validTargetIds"],
        },
    )
    assert result["accepted"] is True


def test_turn_control_serializes_engine_directive_and_scoff_source():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=71,
        battle_id="battle.turn-control",
        battle_size=2,
        player_team=[
            "hero.warrior.defence",
            "hero.priest.comprehensiveness",
        ],
        enemy_team=[
            "hero.rogue.comprehensiveness",
            "hero.mage.comprehensiveness",
        ],
    )
    source = session.game.player_heroes[0]
    actor = session.game.opponent_heroes[0]
    session.game.unactioned_sorted_heroes = [actor]
    actor.status["scoff"] = True
    actor.add_debuff(Debuff("Scoff", 1, source, 1))

    snapshot = adapter.snapshot(session)
    actor_id = adapter._combatant_id(session, actor)
    source_id = adapter._combatant_id(session, source)

    assert snapshot["turnControl"] == {
        "disposition": "automaticAction",
        "acceptsCommands": False,
        "reasonId": "scoff",
        "actorCombatantId": actor_id,
        "sourceCombatantId": source_id,
        "forcedTargetIds": [source_id],
    }
    scoff = next(
        status
        for status in snapshot["combatants"][actor_id]["statuses"]
        if status["id"] == "status.scoff"
    )
    assert scoff["sourceCombatantId"] == source_id
    assert snapshot["legalActions"] == []


def test_stun_precedes_scoff_without_consuming_scoff():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=73,
        battle_id="battle.stun-before-scoff",
        player_team=["hero.warrior.defence"],
        enemy_team=["hero.rogue.comprehensiveness"],
    )
    source = session.game.player_heroes[0]
    actor = session.game.opponent_heroes[0]
    session.game.unactioned_sorted_heroes = [actor, source]
    actor.status["stunned"] = True
    actor.stun_duration = 1
    actor.status["scoff"] = True
    actor.add_debuff(Debuff("Scoff", 1, source, 1))

    before = adapter.snapshot(session)
    events = adapter._drain_automatic_turns(session)

    assert before["turnControl"]["disposition"] == "skip"
    assert before["turnControl"]["reasonId"] == "stunned"
    assert events[0]["reasonId"] == "stunned"
    assert not any(event["type"] == "skillStarted" for event in events)
    assert actor.status["scoff"] is True


def test_stun_consumes_stacked_shadow_word_insanity_in_adapter():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=74,
        battle_id="battle.stun-insanity",
        player_team=["hero.warrior.defence"],
        enemy_team=["hero.rogue.comprehensiveness"],
    )
    source = session.game.player_heroes[0]
    actor = session.game.opponent_heroes[0]
    session.game.unactioned_sorted_heroes = [actor, source]
    actor.status["stunned"] = True
    actor.stun_duration = 1
    actor.status["shadow_word_insanity"] = True

    events = adapter._drain_automatic_turns(session)

    assert actor.status["shadow_word_insanity"] is False
    assert actor.status["stunned"] is True
    assert any(
        event["type"] == "statusRemoved"
        and event.get("statusId") == "status.shadow_word_insanity"
        and event.get("reasonId") == "stunned"
        for event in events
    )
    assert not any(event["type"] == "skillStarted" for event in events)


def test_scoff_precedes_an_existing_magic_cast():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=75,
        battle_id="battle.scoff-before-cast",
        player_team=["hero.warrior.defence"],
        enemy_team=["hero.rogue.comprehensiveness"],
    )
    source = session.game.player_heroes[0]
    actor = session.game.opponent_heroes[0]
    actor.status["magic_casting"] = True
    actor.magic_casting_duration = 0
    actor.casting_magic = actor.skills[0]
    actor.casting_magic_target = source
    actor.status["scoff"] = True
    actor.add_debuff(Debuff("Scoff", 1, source, 1))

    directive = actor.turn_directive(actor.opponents, actor.allies)

    assert directive.reason_id == "scoff"
    assert directive.source is source
    assert directive.targets is source


def test_ready_magic_cast_directive_consumes_casting_status():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=76,
        battle_id="battle.magic-ready",
        player_team=["hero.warrior.defence"],
        enemy_team=["hero.mage.comprehensiveness"],
    )
    target = session.game.player_heroes[0]
    actor = session.game.opponent_heroes[0]
    actor.status["magic_casting"] = True
    actor.magic_casting_duration = 0
    actor.casting_magic = actor.skills[0]
    actor.casting_magic_target = target

    directive = actor.turn_directive(actor.opponents, actor.allies)

    assert directive.reason_id == "magicCastingReady"
    assert directive.consume_statuses == ("magic_casting",)


def test_scoff_preserves_legacy_selection_of_unavailable_off_cooldown_skill():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=77,
        battle_id="battle.scoff-unavailable",
        player_team=["hero.warrior.defence"],
        enemy_team=["hero.rogue.comprehensiveness"],
    )
    source = session.game.player_heroes[0]
    actor = session.game.opponent_heroes[0]
    session.game.unactioned_sorted_heroes = [actor, source]
    chosen = actor.skills[0]
    chosen.is_available = False
    chosen.if_cooldown = False
    for skill in actor.skills[1:]:
        skill.if_cooldown = True
    actor.status["scoff"] = True
    actor.add_debuff(Debuff("Scoff", 1, source, 1))

    events = adapter._drain_automatic_turns(session)
    skill_event = next(event for event in events if event["type"] == "skillStarted")

    assert skill_event["skillId"] == adapter._skill_id(actor, chosen)
    assert skill_event["targetIds"] == [adapter._combatant_id(session, source)]


def test_restricted_turn_rejects_direct_command_without_mutation():
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=79,
        battle_id="battle.restricted-command",
    )
    snapshot = adapter.snapshot(session)
    action = snapshot["legalActions"][0]
    actor = adapter._hero_by_id(session, action["actorId"])
    actor.status["stunned"] = True
    actor.stun_duration = 1
    before = deepcopy(adapter.snapshot(session))

    result = adapter.submit(
        session,
        {
            "type": "useSkill",
            "commandId": "cmd.restricted",
            "expectedRevision": session.revision,
            "actorId": action["actorId"],
            "skillId": action["skillId"],
            "targetIds": action["validTargetIds"][: action["minimumTargets"]],
        },
    )

    assert result["accepted"] is False
    assert result["code"] == "notYourTurn"
    assert adapter.snapshot(session) == before
