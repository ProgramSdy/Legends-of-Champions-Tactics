"""Truth and safety coverage for the second audited preview skill set."""

from __future__ import annotations

from copy import deepcopy
import random
import threading

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from battle_api.adapter import BattleAdapter, BattleAdapterError
from battle_api.app import app, registry
from battle_api.models import DamagePreviewTarget


def _session(player, enemy, *, seed=211):
    adapter = BattleAdapter()
    size = len(player)
    session, _ = adapter.create_battle(
        seed=seed,
        battle_id=f"battle.preview-002.{seed}",
        battle_size=size,
        player_team=player,
        enemy_team=enemy,
        enemy_control_mode="player",
        player_formation=(
            "front-rear" if size == 2 else "one-front-two-rear" if size == 3 else None
        ),
        enemy_formation=(
            "front-rear" if size == 2 else "one-front-two-rear" if size == 3 else None
        ),
    )
    session.game.unactioned_sorted_heroes = [session.game.player_heroes[0]]
    return adapter, session


def _request(adapter, session, skill_id, target_id):
    return {
        "expectedRevision": session.revision,
        "actorId": adapter.snapshot(session)["activeCombatantId"],
        "skillId": skill_id,
        "targetIds": [target_id],
    }


def _combatant_id(adapter, session, hero):
    return adapter._combatant_id(session, hero)


def _hero_mutable_state(hero):
    return {
        "hp": hero.hp,
        "agility": hero.agility,
        "status": deepcopy(hero.status),
        "buffs": [
            (buff.name, buff.duration, id(buff.initiator), buff.effect)
            for buff in hero.buffs
        ],
        "debuffs": [
            (debuff.name, debuff.duration, id(debuff.initiator), debuff.effect)
            for debuff in hero.debuffs
        ],
        "healingBoosts": deepcopy(hero.healing_boost_effects),
        "healingReductions": deepcopy(hero.healing_reduction_effects),
        "wrathStacks": hero.wrath_of_crusader_stacks,
        "wrathDuration": hero.wrath_of_crusader_duration,
        "painDuration": hero.shadow_word_pain_debuff_duration,
        "painDamage": hero.shadow_word_pain_continuous_damage,
        "skills": [
            (skill.name, skill.is_available, skill.if_cooldown, skill.cooldown)
            for skill in hero.skills
        ],
    }


@pytest.mark.parametrize(
    ("player", "skill_id", "expected"),
    [
        ("hero.priest.comprehensiveness", "skill.priest.holy_smite", (16, 22)),
        ("hero.paladin.retribution", "skill.paladin.crusader_strike", (18, 22)),
    ],
)
def test_defence_ignoring_damage_ranges(player, skill_id, expected):
    adapter, session = _session([player], ["hero.warrior.defence"])
    target = session.game.opponent_heroes[0]
    target.defense = 1_000
    target_id = _combatant_id(adapter, session, target)

    fact = adapter.preview(session, _request(adapter, session, skill_id, target_id))["targets"][0]

    assert fact["primary"]["amountRange"] == {"min": expected[0], "max": expected[1]}
    assert isinstance(fact["directHitChancePercent"], int)


def test_shadow_word_pain_uses_shadow_resistance_and_marks_even_at_zero_damage():
    adapter, session = _session(
        ["hero.priest.comprehensiveness"], ["hero.warrior.defence"]
    )
    target = session.game.opponent_heroes[0]
    target.shadow_resistance = 1_000
    target_id = _combatant_id(adapter, session, target)

    fact = adapter.preview(
        session,
        _request(adapter, session, "skill.priest.shadow_word_pain", target_id),
    )["targets"][0]

    assert fact["primary"]["amountRange"] == {"min": 0, "max": 0}
    assert fact["consequences"] == [
        {"kind": "shadowWordPain", "certainty": "onHit"}
    ]
    target.status["shadow_word_pain"] = True
    repeat = adapter.preview(
        session,
        _request(adapter, session, "skill.priest.shadow_word_pain", target_id),
    )["targets"][0]
    assert repeat["consequences"] == []


def test_binding_heal_shows_target_power_and_identifies_separate_caster_heal():
    adapter, session = _session(
        ["hero.priest.comprehensiveness", "hero.warrior.defence"],
        ["hero.rogue.comprehensiveness", "hero.rogue.comprehensiveness"],
    )
    actor, ally = session.game.player_heroes
    actor.hp = actor.hp_max - 10
    ally.hp = ally.hp_max - 5
    ally_id = _combatant_id(adapter, session, ally)
    actor_id = _combatant_id(adapter, session, actor)

    fact = adapter.preview(
        session,
        _request(adapter, session, "skill.priest.binding_heal", ally_id),
    )["targets"][0]

    assert fact["primary"] == {
        "kind": "healing",
        "amountRange": {"min": 22, "max": 28},
        "reasonId": None,
    }
    assert fact["directHitChancePercent"] is None
    assert fact["consequences"] == [
        {
            "kind": "secondaryHealing",
            "certainty": "always",
            "recipientId": actor_id,
            "amountRange": {"min": 17, "max": 23},
        }
    ]

    actor.hp = actor.hp_max
    no_caster_change = adapter.preview(
        session,
        _request(adapter, session, "skill.priest.binding_heal", ally_id),
    )["targets"][0]
    assert no_caster_change["consequences"] == []


def test_healing_receipt_enumerates_modifier_without_a_missing_hp_cap_or_hit_chance():
    adapter, session = _session(
        ["hero.paladin.retribution"], ["hero.rogue.comprehensiveness"]
    )
    target = session.game.player_heroes[0]
    target.hp = 1
    target.healing_boost_effects["test"] = 0.5
    target.healing_reduction_effects["test"] = 0.7
    target_id = _combatant_id(adapter, session, target)
    fact = adapter.preview(
        session,
        _request(adapter, session, "skill.paladin.flash_of_light", target_id),
    )["targets"][0]
    expected = [round(value * 0.8) for value in range(19, 22)]
    assert fact["primary"]["amountRange"] == {
        "min": min(expected), "max": max(expected)
    }
    assert fact["directHitChancePercent"] is None

    target.hp = target.hp_max
    full = adapter.preview(
        session,
        _request(adapter, session, "skill.paladin.flash_of_light", target_id),
    )["targets"][0]
    assert full["primary"]["amountRange"] == {
        "min": min(expected), "max": max(expected)
    }


@pytest.mark.parametrize(
    ("stacks", "expected_range", "expected_bonus"),
    [
        (0, (19, 21), []),
        (1, (24, 26), [(5, 7)]),
        (2, (30, 32), [(11, 13)]),
    ],
)
def test_flash_of_light_uses_live_wrath_state_and_reports_its_bonus(
    stacks, expected_range, expected_bonus
):
    adapter, session = _session(
        ["hero.paladin.retribution"], ["hero.rogue.comprehensiveness"]
    )
    actor = session.game.player_heroes[0]
    actor.hp = 1
    actor.status["wrath_of_crusader"] = stacks > 0
    actor.wrath_of_crusader_stacks = stacks
    actor_id = _combatant_id(adapter, session, actor)

    fact = adapter.preview(
        session,
        _request(adapter, session, "skill.paladin.flash_of_light", actor_id),
    )["targets"][0]

    assert fact["primary"]["amountRange"] == {
        "min": expected_range[0], "max": expected_range[1]
    }
    assert fact["consequences"] == [
        {
            "kind": "wrathHealingBonus",
            "certainty": "always",
            "stacks": stacks,
            "amountRange": {"min": minimum, "max": maximum},
        }
        for minimum, maximum in expected_bonus
    ]


@pytest.mark.parametrize(
    ("active", "stacks", "outcome", "resulting_stacks"),
    [
        (False, 0, "firstApplication", 1),
        (True, 1, "nextStack", 2),
        (True, 2, "durationRefresh", 2),
    ],
)
def test_crusader_strike_reports_actor_owned_guaranteed_wrath(
    active, stacks, outcome, resulting_stacks
):
    adapter, session = _session(
        ["hero.paladin.retribution"], ["hero.rogue.comprehensiveness"]
    )
    actor = session.game.player_heroes[0]
    target = session.game.opponent_heroes[0]
    actor.status["wrath_of_crusader"] = active
    actor.wrath_of_crusader_stacks = stacks
    target.status["shield_of_protection"] = True
    actor_id = _combatant_id(adapter, session, actor)
    target_id = _combatant_id(adapter, session, target)

    fact = adapter.preview(
        session,
        _request(adapter, session, "skill.paladin.crusader_strike", target_id),
    )["targets"][0]

    assert fact["primary"]["kind"] == "prevented"
    assert fact["consequences"] == [
        {
            "kind": "wrathOfCrusader",
            "certainty": "always",
            "recipientId": actor_id,
            "stacks": resulting_stacks,
            "outcome": outcome,
        }
    ]


def test_hammer_wrath_bonus_is_added_before_projectile_formation_receipt():
    adapter, session = _session(
        ["hero.paladin.retribution", "hero.warrior.defence"],
        ["hero.rogue.comprehensiveness", "hero.rogue.comprehensiveness"],
    )
    actor = session.game.player_heroes[0]
    target = session.game.opponent_heroes[1]
    actor.position = "rear"
    target.position = "rear"
    actor.status["wrath_of_crusader"] = True
    actor.wrath_of_crusader_stacks = 1
    target_id = _combatant_id(adapter, session, target)
    raw = actor.audited_direct_damage_range("Hammer of Anger", target)
    expected = [target.take_damage_calculation(value, "ranged_projectile", actor) for value in raw]

    fact = adapter.preview(
        session,
        _request(adapter, session, "skill.paladin.hammer_of_anger", target_id),
    )["targets"][0]

    assert fact["primary"]["amountRange"] == {
        "min": min(expected), "max": max(expected)
    }
    assert fact["consequences"] == [
        {
            "kind": "wrathDamageBonus",
            "certainty": "always",
            "stacks": 1,
            "amountRange": {"min": 1, "max": 3},
        }
    ]


@pytest.mark.parametrize(
    ("player", "enemy", "skill_id", "side"),
    [
        ("hero.priest.comprehensiveness", "hero.rogue.comprehensiveness", "skill.priest.holy_smite", "enemy"),
        ("hero.priest.comprehensiveness", "hero.rogue.comprehensiveness", "skill.priest.shadow_word_pain", "enemy"),
        ("hero.priest.comprehensiveness", "hero.rogue.comprehensiveness", "skill.priest.binding_heal", "friendly"),
        ("hero.paladin.retribution", "hero.rogue.comprehensiveness", "skill.paladin.hammer_of_anger", "enemy"),
        ("hero.paladin.retribution", "hero.rogue.comprehensiveness", "skill.paladin.crusader_strike", "enemy"),
        ("hero.paladin.retribution", "hero.rogue.comprehensiveness", "skill.paladin.flash_of_light", "friendly"),
    ],
)
def test_all_six_previews_are_rng_free_and_state_preserving(
    player, enemy, skill_id, side, monkeypatch
):
    adapter, session = _session([player], [enemy])
    actor = session.game.player_heroes[0]
    if side == "friendly":
        actor.hp -= 20
        target = actor
    else:
        target = session.game.opponent_heroes[0]
    target_id = _combatant_id(adapter, session, target)
    before = deepcopy(adapter.snapshot(session))
    actor_state = _hero_mutable_state(actor)
    target_state = _hero_mutable_state(target)
    rng_before = session.rng_state
    global_before = random.getstate()

    def fail(*_args, **_kwargs):
        raise AssertionError("preview consumed RNG")

    for name in ("random", "randint", "choice", "sample", "shuffle"):
        monkeypatch.setattr(random, name, fail)
    result = adapter.preview(session, _request(adapter, session, skill_id, target_id))

    assert result["coverage"] == "authoritative"
    assert adapter.snapshot(session) == before
    assert _hero_mutable_state(actor) == actor_state
    assert _hero_mutable_state(target) == target_state
    assert session.rng_state == rng_before
    assert random.getstate() == global_before


def test_healing_wrong_side_and_stale_revision_are_rejected_without_state_change():
    adapter, session = _session(
        ["hero.priest.comprehensiveness"], ["hero.rogue.comprehensiveness"]
    )
    before = deepcopy(adapter.snapshot(session))
    enemy_id = _combatant_id(adapter, session, session.game.opponent_heroes[0])
    wrong_side = _request(adapter, session, "skill.priest.binding_heal", enemy_id)
    with pytest.raises(BattleAdapterError, match="illegal"):
        adapter.preview(session, wrong_side)
    stale = _request(
        adapter,
        session,
        "skill.priest.holy_smite",
        enemy_id,
    )
    stale["expectedRevision"] += 1
    with pytest.raises(BattleAdapterError, match="stale"):
        adapter.preview(session, stale)
    assert adapter.snapshot(session) == before


def test_api_serializes_healing_without_hit_chance_and_typed_secondary_recipient():
    client = TestClient(app)
    created = client.post(
        "/api/v1/battles",
        json={
            "battleSize": 2,
            "playerTeam": [
                "hero.priest.comprehensiveness",
                "hero.warrior.defence",
            ],
            "playerFormation": "side-by-side",
            "enemyTeam": [
                "hero.rogue.comprehensiveness",
                "hero.rogue.comprehensiveness",
            ],
            "enemyControlMode": "player",
            "enemyFormation": "side-by-side",
            "seed": 991,
        },
    )
    assert created.status_code == 200
    battle_id = created.json()["battleId"]
    session = registry.get(battle_id)
    actor, ally = session.game.player_heroes
    actor.hp -= 10
    ally.hp -= 10
    session.game.unactioned_sorted_heroes = [actor]
    snapshot = registry.adapter.snapshot(session)
    response = client.post(
        f"/api/v1/battles/{battle_id}/preview",
        json={
            "expectedRevision": session.revision,
            "actorId": snapshot["activeCombatantId"],
            "skillId": "skill.priest.binding_heal",
            "targetIds": [_combatant_id(registry.adapter, session, ally)],
        },
    )

    assert response.status_code == 200
    fact = response.json()["data"]["targets"][0]
    assert fact["primary"]["kind"] == "healing"
    assert fact["directHitChancePercent"] is None
    assert fact["consequences"][0]["kind"] == "secondaryHealing"


@pytest.mark.parametrize(
    ("player", "skill_id", "side"),
    [
        ("hero.priest.comprehensiveness", "skill.priest.holy_smite", "enemy"),
        ("hero.priest.comprehensiveness", "skill.priest.shadow_word_pain", "enemy"),
        ("hero.priest.comprehensiveness", "skill.priest.binding_heal", "friendly"),
        ("hero.paladin.retribution", "skill.paladin.hammer_of_anger", "enemy"),
        ("hero.paladin.retribution", "skill.paladin.crusader_strike", "enemy"),
        ("hero.paladin.retribution", "skill.paladin.flash_of_light", "friendly"),
    ],
)
def test_preview_leaves_same_seed_live_command_identical(player, skill_id, side):
    with_preview_adapter, with_preview = _session(
        [player], ["hero.rogue.comprehensiveness"], seed=817
    )
    control_adapter, control = _session(
        [player], ["hero.rogue.comprehensiveness"], seed=817
    )
    if side == "friendly":
        with_preview.game.player_heroes[0].hp -= 30
        control.game.player_heroes[0].hp -= 30
        target_with = with_preview.game.player_heroes[0]
        target_control = control.game.player_heroes[0]
    else:
        target_with = with_preview.game.opponent_heroes[0]
        target_control = control.game.opponent_heroes[0]
    target_with_id = _combatant_id(with_preview_adapter, with_preview, target_with)
    target_control_id = _combatant_id(control_adapter, control, target_control)
    assert target_with_id == target_control_id
    before = with_preview_adapter.snapshot(with_preview)
    assert before == control_adapter.snapshot(control)

    with_preview_adapter.preview(
        with_preview,
        _request(with_preview_adapter, with_preview, skill_id, target_with_id),
    )
    assert with_preview_adapter.snapshot(with_preview) == before
    assert with_preview.rng_state == control.rng_state

    command = {
        "type": "useSkill",
        "commandId": "cmd.preview-002.same-seed",
        "expectedRevision": with_preview.revision,
        "actorId": before["activeCombatantId"],
        "skillId": skill_id,
        "targetIds": [target_with_id],
    }
    evaluated = with_preview_adapter.submit(with_preview, command)
    untouched = control_adapter.submit(control, command)

    assert evaluated["accepted"] is True
    assert untouched["accepted"] is True
    assert evaluated == untouched
    assert with_preview.rng_state == control.rng_state


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        ("wrongSide", "illegalTargets"),
        ("deadTarget", "illegalTargets"),
        ("cooldown", "illegalSkill"),
        ("wrongActor", "notYourTurn"),
        ("staleRevision", "staleRevision"),
        ("outOfScope", "previewUnavailable"),
    ],
)
def test_validation_rejections_preserve_issued_state(mutation, expected_code):
    adapter, session = _session(
        ["hero.paladin.retribution", "hero.priest.comprehensiveness"],
        ["hero.rogue.comprehensiveness", "hero.rogue.comprehensiveness"],
    )
    actor = session.game.player_heroes[0]
    enemy = session.game.opponent_heroes[0]
    target_id = _combatant_id(adapter, session, enemy)
    request = _request(
        adapter, session, "skill.paladin.hammer_of_anger", target_id
    )
    if mutation == "wrongSide":
        request["targetIds"] = [_combatant_id(adapter, session, actor)]
    elif mutation == "deadTarget":
        enemy.hp = 0
    elif mutation == "cooldown":
        actor.skills[0].if_cooldown = True
    elif mutation == "wrongActor":
        request["actorId"] = "friendly.not-current"
    elif mutation == "staleRevision":
        request["expectedRevision"] += 1
    else:
        actor.skills[0].name = "Not Approved"
        request["skillId"] = adapter._skill_id(actor, actor.skills[0])

    before_snapshot = deepcopy(adapter.snapshot(session))
    actor_before = _hero_mutable_state(actor)
    enemy_before = _hero_mutable_state(enemy)
    rng_before = session.rng_state
    global_before = random.getstate()
    command_cache_before = deepcopy(session.command_results)
    event_sequence_before = session.event_sequence

    with pytest.raises(BattleAdapterError) as error:
        adapter.preview(session, request)
    assert error.value.code == expected_code
    assert adapter.snapshot(session) == before_snapshot
    assert _hero_mutable_state(actor) == actor_before
    assert _hero_mutable_state(enemy) == enemy_before
    assert session.rng_state == rng_before
    assert random.getstate() == global_before
    assert session.command_results == command_cache_before
    assert session.event_sequence == event_sequence_before


def test_api_preview_validation_failure_and_stale_failure_are_nonmutating():
    client = TestClient(app)
    created = client.post(
        "/api/v1/battles",
        json={
            "battleSize": 1,
            "playerTeam": ["hero.paladin.retribution"],
            "enemyTeam": ["hero.rogue.comprehensiveness"],
            "enemyControlMode": "player",
            "seed": 994,
        },
    )
    assert created.status_code == 200
    battle_id = created.json()["battleId"]
    session = registry.get(battle_id)
    session.game.unactioned_sorted_heroes = [session.game.player_heroes[0]]
    snapshot = registry.adapter.snapshot(session)
    enemy_id = snapshot["sides"][1]["combatantIds"][0]
    request = {
        "expectedRevision": session.revision,
        "actorId": snapshot["activeCombatantId"],
        "skillId": "skill.paladin.flash_of_light",
        "targetIds": [enemy_id],
    }
    before_state = _hero_mutable_state(session.game.player_heroes[0])
    before_rng = session.rng_state
    wrong_side = client.post(f"/api/v1/battles/{battle_id}/preview", json=request)
    assert wrong_side.status_code == 422
    assert wrong_side.json()["detail"]["code"] == "illegalTargets"
    stale = client.post(
        f"/api/v1/battles/{battle_id}/preview",
        json={**request, "expectedRevision": session.revision + 1},
    )
    assert stale.status_code == 409
    assert stale.json()["detail"]["code"] == "staleRevision"
    invalid_target_shape = client.post(
        f"/api/v1/battles/{battle_id}/preview",
        json={**request, "targetIds": []},
    )
    # The transport now accepts an empty list so the two audited targetless
    # Warrior skills can use it.  A targeted Paladin skill remains rejected by
    # the adapter's legal target-shape validation.
    assert invalid_target_shape.status_code == 422
    assert invalid_target_shape.json()["detail"]["code"] == "illegalTargets"
    assert registry.adapter.snapshot(session) == snapshot
    assert _hero_mutable_state(session.game.player_heroes[0]) == before_state
    assert session.rng_state == before_rng


@pytest.mark.parametrize("battle_size", [1, 2, 3])
@pytest.mark.parametrize(
    ("player", "skill_id", "target_side"),
    [
        ("hero.priest.comprehensiveness", "skill.priest.holy_smite", "enemy"),
        ("hero.priest.comprehensiveness", "skill.priest.shadow_word_pain", "enemy"),
        ("hero.priest.comprehensiveness", "skill.priest.binding_heal", "friendly"),
        ("hero.paladin.retribution", "skill.paladin.hammer_of_anger", "enemy"),
        ("hero.paladin.retribution", "skill.paladin.crusader_strike", "enemy"),
        ("hero.paladin.retribution", "skill.paladin.flash_of_light", "friendly"),
    ],
)
def test_all_six_skills_preview_through_live_size_scoped_formation_authority(
    battle_size, player, skill_id, target_side
):
    adapter, session = _session(
        [player] * battle_size,
        ["hero.rogue.comprehensiveness"] * battle_size,
        seed=825 + battle_size,
    )
    actor = session.game.player_heroes[0]
    if target_side == "friendly":
        actor.hp -= 10
        target = actor
    else:
        target = session.game.opponent_heroes[0]
    target_id = _combatant_id(adapter, session, target)
    published = next(
        action
        for action in adapter.snapshot(session)["legalActions"]
        if action["skillId"] == skill_id
    )
    assert target_id in published["validTargetIds"]

    result = adapter.preview(session, _request(adapter, session, skill_id, target_id))

    assert result["coverage"] == "authoritative"
    assert result["selectedTargetIds"] == [target_id]
    fact = result["targets"][0]
    assert fact["primary"]["amountRange"]["min"] <= fact["primary"]["amountRange"]["max"]
    if target_side == "friendly":
        assert fact["primary"]["kind"] == "healing"
        assert fact["directHitChancePercent"] is None
    else:
        assert fact["primary"]["kind"] == "damage"
        assert isinstance(fact["directHitChancePercent"], int)


def test_damage_immunity_uses_the_live_skill_damage_nature():
    adapter, session = _session(
        ["hero.priest.comprehensiveness"], ["hero.rogue.comprehensiveness"]
    )
    target = session.game.opponent_heroes[0]
    target_id = _combatant_id(adapter, session, target)
    target.status["anti_magic_shield"] = True
    smite = adapter.preview(
        session,
        _request(adapter, session, "skill.priest.holy_smite", target_id),
    )["targets"][0]
    assert smite["primary"] == {
        "kind": "prevented",
        "amountRange": {"min": 0, "max": 0},
        "reasonId": "prevention.magicalDamage",
    }

    target.status["glacier"] = True
    pain = adapter.preview(
        session,
        _request(adapter, session, "skill.priest.shadow_word_pain", target_id),
    )["targets"][0]
    assert pain["primary"] == {
        "kind": "prevented",
        "amountRange": {"min": 0, "max": 0},
        "reasonId": "prevention.allDamage",
    }
    assert pain["consequences"] == []


def test_crusader_screened_rear_illegal_but_hammer_ranged_rear_legal():
    adapter, session = _session(
        ["hero.paladin.retribution", "hero.paladin.retribution"],
        ["hero.rogue.comprehensiveness", "hero.rogue.comprehensiveness"],
    )
    rear = session.game.opponent_heroes[1]
    rear.position = "rear"
    rear_id = _combatant_id(adapter, session, rear)
    before = deepcopy(adapter.snapshot(session))
    with pytest.raises(BattleAdapterError) as error:
        adapter.preview(
            session,
            _request(adapter, session, "skill.paladin.crusader_strike", rear_id),
        )
    assert error.value.code == "illegalTargets"
    assert adapter.snapshot(session) == before

    hammer = adapter.preview(
        session,
        _request(adapter, session, "skill.paladin.hammer_of_anger", rear_id),
    )["targets"][0]
    assert hammer["targetId"] == rear_id


@pytest.mark.parametrize("stacks", [0, 1, 2])
def test_hammer_current_wrath_bonus_can_overcome_high_defence(stacks):
    adapter, session = _session(
        ["hero.paladin.retribution"], ["hero.warrior.defence"]
    )
    actor = session.game.player_heroes[0]
    target = session.game.opponent_heroes[0]
    target.defense = actor.damage + 1_000
    actor.status["wrath_of_crusader"] = stacks > 0
    actor.wrath_of_crusader_stacks = stacks
    target_id = _combatant_id(adapter, session, target)
    fact = adapter.preview(
        session,
        _request(adapter, session, "skill.paladin.hammer_of_anger", target_id),
    )["targets"][0]
    expected = {0: (0, 0), 1: (3, 5), 2: (6, 8)}[stacks]
    assert fact["primary"]["amountRange"] == {
        "min": expected[0], "max": expected[1]
    }
    if stacks == 0:
        assert fact["consequences"] == []
    else:
        assert fact["consequences"][0]["amountRange"] == {
            "min": expected[0], "max": expected[1]
        }


def test_binding_self_heals_only_self_and_reduction_with_boost_is_combined():
    adapter, session = _session(
        ["hero.priest.comprehensiveness"], ["hero.rogue.comprehensiveness"]
    )
    actor = session.game.player_heroes[0]
    actor.hp -= 40
    actor.healing_reduction_effects["complete"] = 1.0
    actor.healing_boost_effects["partial"] = 0.25
    actor_id = _combatant_id(adapter, session, actor)

    fact = adapter.preview(
        session,
        _request(adapter, session, "skill.priest.binding_heal", actor_id),
    )["targets"][0]
    amounts = [round(base * 0.25) for base in range(22, 29)]
    assert fact["primary"]["amountRange"] == {
        "min": min(amounts), "max": max(amounts)
    }
    assert fact["consequences"] == []

    actor.healing_boost_effects.clear()
    blocked = adapter.preview(
        session,
        _request(adapter, session, "skill.priest.binding_heal", actor_id),
    )["targets"][0]
    assert blocked["primary"]["kind"] == "healing"
    assert blocked["primary"]["amountRange"] == {"min": 0, "max": 0}


def test_invalid_and_duplicate_target_ids_are_rejected_for_new_skills():
    adapter, session = _session(
        ["hero.priest.comprehensiveness", "hero.priest.comprehensiveness"],
        ["hero.rogue.comprehensiveness", "hero.rogue.comprehensiveness"],
    )
    target_id = _combatant_id(adapter, session, session.game.opponent_heroes[0])
    before = deepcopy(adapter.snapshot(session))
    for target_ids in ([target_id, target_id], ["enemy.unknown"]):
        request = _request(
            adapter, session, "skill.priest.holy_smite", target_id
        )
        request["targetIds"] = target_ids
        with pytest.raises(BattleAdapterError) as error:
            adapter.preview(session, request)
        assert error.value.code == "illegalTargets"
        assert adapter.snapshot(session) == before


def test_typed_preview_response_rejects_wrong_hit_or_consequence_variant():
    target = {
        "targetId": "friendly.priest.1",
        "currentHp": 50,
        "maxHp": 100,
        "primary": {
            "kind": "healing",
            "amountRange": {"min": 5, "max": 8},
            "reasonId": None,
        },
        "directHitChancePercent": None,
        "consequences": [
            {
                "kind": "secondaryHealing",
                "certainty": "always",
                "recipientId": "friendly.priest.2",
                "amountRange": {"min": 4, "max": 6},
            }
        ],
    }
    assert DamagePreviewTarget.model_validate(target).primary.kind == "healing"
    with pytest.raises(ValidationError):
        DamagePreviewTarget.model_validate(
            {**target, "directHitChancePercent": 100}
        )
    with pytest.raises(ValidationError):
        DamagePreviewTarget.model_validate(
            {
                **target,
                "consequences": [
                    {
                        "kind": "secondaryHealing",
                        "certainty": "always",
                        "recipientId": "friendly.priest.2",
                        "amountRange": {"min": 4, "max": 6},
                        "chancePercent": 50,
                    }
                ],
            }
        )


def test_evaluator_failure_releases_lock_without_mutating_battle(monkeypatch):
    adapter, session = _session(
        ["hero.priest.comprehensiveness"], ["hero.rogue.comprehensiveness"]
    )
    actor = session.game.player_heroes[0]
    actor.hp -= 10
    actor_id = _combatant_id(adapter, session, actor)
    request = _request(adapter, session, "skill.priest.binding_heal", actor_id)
    before = deepcopy(adapter.snapshot(session))
    actor_before = _hero_mutable_state(actor)
    rng_before = session.rng_state
    global_before = random.getstate()
    command_cache_before = deepcopy(session.command_results)
    event_sequence_before = session.event_sequence

    def fail(_skill_name):
        raise RuntimeError("injected evaluator failure")

    monkeypatch.setattr(actor, "audited_healing_range", fail)
    with pytest.raises(RuntimeError, match="injected"):
        adapter.preview(session, request)
    assert adapter.snapshot(session) == before
    assert _hero_mutable_state(actor) == actor_before
    assert session.rng_state == rng_before
    assert random.getstate() == global_before
    assert session.command_results == command_cache_before
    assert session.event_sequence == event_sequence_before
    lock_available = []

    def verify_other_thread():
        acquired = session.lock.acquire(blocking=False)
        lock_available.append(acquired)
        if acquired:
            session.lock.release()

    verifier = threading.Thread(target=verify_other_thread)
    verifier.start()
    verifier.join(timeout=2)
    assert lock_available == [True]
