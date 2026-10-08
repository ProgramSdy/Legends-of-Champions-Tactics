"""Deterministic BTT-005 Priest Discipline preview coverage."""

from __future__ import annotations

from copy import deepcopy
import random

import pytest
from fastapi.testclient import TestClient

from battle_api.adapter import BattleAdapter, BattleAdapterError
from battle_api.app import app, registry
from battle_api.models import BattlePreviewResponse
from skills.skill import Buff


def _session(*, size=1, seed=5005):
    adapter = BattleAdapter()
    friendly = ["hero.priest.discipline"] + [
        "hero.warrior.weapon_master"
    ] * (size - 1)
    enemies = ["hero.rogue.comprehensiveness"] * size
    formation = "front-rear" if size == 2 else "one-front-two-rear" if size == 3 else None
    session, _ = adapter.create_battle(
        seed=seed,
        battle_id=f"battle.preview-005.{size}.{seed}",
        battle_size=size,
        player_team=friendly,
        enemy_team=enemies,
        enemy_control_mode="player",
        player_formation=formation,
        enemy_formation=formation,
    )
    actor = session.game.player_heroes[0]
    session.game.unactioned_sorted_heroes = [actor]
    return adapter, session, actor


def _id(adapter, session, hero):
    return adapter._combatant_id(session, hero)


def _request(adapter, session, skill_id, targets):
    return {
        "expectedRevision": session.revision,
        "actorId": _id(adapter, session, session.game.player_heroes[0]),
        "skillId": skill_id,
        "targetIds": [_id(adapter, session, target) for target in targets],
    }


def _consequence(result, kind):
    return next(
        item for item in result["targets"][0]["consequences"] if item["kind"] == kind
    )


def _state_fingerprint(adapter, session):
    heroes = []
    for hero in session.game.heroes:
        heroes.append(
            {
                "id": _id(adapter, session, hero),
                "hp": hero.hp,
                "status": deepcopy(hero.status),
                "buffs": [
                    (item.name, item.duration, id(item.initiator), item.effect)
                    for item in hero.buffs
                ],
                "debuffs": [
                    (item.name, item.duration, id(item.initiator), item.effect)
                    for item in hero.debuffs
                ],
                "skills": [
                    (item.name, item.is_available, item.if_cooldown, item.cooldown)
                    for item in hero.skills
                ],
                "actioned": hero.actioned,
            }
        )
    return {
        "revision": session.revision,
        "rng": session.rng_state,
        "events": session.event_sequence,
        "commands": deepcopy(session.command_results),
        "presentationCursor": session.presentation_log_cursor,
        "presentationLog": deepcopy(session.game.presentation_log),
        "statusEvents": list(session.game.status_effect_events),
        "turnOrder": [id(hero) for hero in session.game.unactioned_sorted_heroes],
        "heroes": heroes,
    }


def test_penance_ally_and_opponent_branches_are_server_authored():
    adapter, session, actor = _session(size=2)
    ally = session.game.player_heroes[1]
    rear_enemy = session.game.opponent_heroes[1]

    healing = adapter.preview(
        session,
        _request(adapter, session, "skill.priest.penance", [ally]),
    )
    healing_fact = healing["targets"][0]
    assert healing_fact["primary"] == {
        "kind": "healing",
        "amountRange": {"min": 21, "max": 25},
        "reasonId": None,
    }
    assert healing_fact["directHitChancePercent"] is None

    damage = adapter.preview(
        session,
        _request(adapter, session, "skill.priest.penance", [rear_enemy]),
    )
    damage_fact = damage["targets"][0]
    assert damage_fact["primary"]["kind"] == "damage"
    assert damage_fact["primary"]["amountRange"] == {"min": 17, "max": 21}
    assert isinstance(damage_fact["directHitChancePercent"], int)

    # Hybrid Penance owns its Shield of Protection boundary explicitly rather
    # than inheriting the generic damage-skill immunity path. Its
    # ranged-instant receipt remains legal against a rear target.
    rear_enemy.status["shield_of_protection"] = True
    immune_state = adapter.preview(
        session,
        _request(adapter, session, "skill.priest.penance", [rear_enemy]),
    )
    assert immune_state["targets"][0]["primary"] == {
        "kind": "prevented",
        "amountRange": {"min": 0, "max": 0},
        "reasonId": "prevention.allDamage",
    }
    assert immune_state["targets"][0]["consequences"] == []
    assert actor.position == "front" and rear_enemy.position == "rear"


def test_penance_shield_prevention_matches_live_execution_without_linked_preview():
    adapter, session, actor = _session(size=2, seed=5013)
    ally = session.game.player_heroes[1]
    target = session.game.opponent_heroes[0]
    ally.status["holy_word_redemption"] = True
    ally.add_buff(Buff("Holy Word Redemption", 5, actor, 0.7))
    target.status["shield_of_protection"] = True
    target_hp = target.hp

    preview = adapter.preview(
        session,
        _request(adapter, session, "skill.priest.penance", [target]),
    )
    fact = preview["targets"][0]
    assert fact["primary"]["kind"] == "prevented"
    assert fact["primary"]["amountRange"] == {"min": 0, "max": 0}
    assert not any(
        consequence["kind"] == "secondaryHealing"
        for consequence in fact["consequences"]
    )

    skill = adapter._skill_by_id(actor, "skill.priest.penance")
    assert skill is not None
    skill.evasion_check = lambda _target: False
    result = adapter.submit(
        session,
        {
            "type": "useSkill",
            "commandId": "cmd.penance.shield",
            **_request(adapter, session, "skill.priest.penance", [target]),
        },
    )

    assert result["accepted"] is True
    assert target.hp == target_hp
    assert not any(
        event["type"] == "damageApplied"
        and event.get("targetId") == _id(adapter, session, target)
        for event in result["events"]
    )
    assert any(
        event["type"] == "damagePrevented"
        and event.get("targetId") == _id(adapter, session, target)
        and event.get("reasonId") == "status.shield_of_protection"
        and event.get("amount") == 0
        for event in result["events"]
    )
    assert not any(
        event["type"] == "healingApplied"
        and event.get("targetId") == _id(adapter, session, ally)
        for event in result["events"]
    )


def test_penance_evasion_remains_probabilistic_not_deterministically_prevented():
    adapter, session, actor = _session(seed=5014)
    target = session.game.opponent_heroes[0]
    target_hp = target.hp

    preview = adapter.preview(
        session,
        _request(adapter, session, "skill.priest.penance", [target]),
    )
    fact = preview["targets"][0]
    assert fact["primary"]["kind"] == "damage"
    assert 0 <= fact["directHitChancePercent"] <= 100

    skill = adapter._skill_by_id(actor, "skill.priest.penance")
    assert skill is not None
    skill.evasion_check = lambda _target: True
    result = adapter.submit(
        session,
        {
            "type": "useSkill",
            "commandId": "cmd.penance.evaded",
            **_request(adapter, session, "skill.priest.penance", [target]),
        },
    )

    assert result["accepted"] is True
    assert target.hp == target_hp
    assert any(
        event["type"] == "attackEvaded"
        and event.get("targetId") == _id(adapter, session, target)
        for event in result["events"]
    )


def test_penance_opponent_reports_same_caster_redemption_healing_per_recipient():
    adapter, session, actor = _session(size=2)
    ally = session.game.player_heroes[1]
    target = session.game.opponent_heroes[0]
    ally.status["holy_word_redemption"] = True
    ally.add_buff(Buff("Holy Word Redemption", 5, actor, 0.7))

    result = adapter.preview(
        session,
        _request(adapter, session, "skill.priest.penance", [target]),
    )

    linked = _consequence(result, "secondaryHealing")
    assert linked == {
        "kind": "secondaryHealing",
        "certainty": "onHit",
        "recipientId": _id(adapter, session, ally),
        "amountRange": {"min": 12, "max": 15},
    }

    # A fully absorbed receipt is not a landed hit, so the linked Redemption
    # heal must not be advertised by preview.
    target.status["holy_word_shell"] = True
    target.holy_word_shell_absorption = 999
    absorbed = adapter.preview(
        session,
        _request(adapter, session, "skill.priest.penance", [target]),
    )
    assert absorbed["targets"][0]["primary"]["kind"] == "prevented"
    assert not any(
        consequence["kind"] == "secondaryHealing"
        for consequence in absorbed["targets"][0]["consequences"]
    )


def test_penance_redemption_linked_healing_matches_hit_and_absorption_execution():
    """Preview and execution agree on whether Penance actually landed.

    Redemption is a consequence of a successful Penance damage receipt.  A
    Shield of Protection or a fully absorbing Holy Word Shell prevents the
    hit, while a partial shell and an ordinary hit still produce the linked
    heal event.  Each branch uses a fresh seeded session so RNG and mutable
    status state cannot leak between cases.
    """

    def prepare(seed, absorption=None):
        adapter, session, actor = _session(size=2, seed=seed)
        ally = session.game.player_heroes[1]
        ally.hp = ally.hp_max - 20
        ally.status["holy_word_redemption"] = True
        ally.add_buff(Buff("Holy Word Redemption", 5, actor, 0.7))
        target = session.game.opponent_heroes[0]
        target.defense = 0
        if absorption is not None:
            target.status["holy_word_shell"] = True
            target.holy_word_shell_absorption = absorption
        skill = adapter._skill_by_id(actor, "skill.priest.penance")
        assert skill is not None
        skill.evasion_check = lambda _target: False
        return adapter, session, actor, ally, target

    def execute(seed, absorption=None):
        adapter, session, actor, ally, target = prepare(seed, absorption)
        preview = adapter.preview(
            session,
            _request(adapter, session, "skill.priest.penance", [target]),
        )
        result = adapter.submit(
            session,
            {
                "type": "useSkill",
                "commandId": f"cmd.penance.receipt.{seed}",
                **_request(adapter, session, "skill.priest.penance", [target]),
            },
        )
        return preview, result, adapter, session, ally, target

    full_preview, full_result, full_adapter, full_session, full_ally, full_target = execute(5021, 999)
    assert full_preview["targets"][0]["primary"]["kind"] == "prevented"
    assert not any(
        item["kind"] == "secondaryHealing"
        for item in full_preview["targets"][0]["consequences"]
    )
    assert full_target.hp == full_target.hp_max
    assert not any(
        event["type"] == "healingApplied"
        and event.get("targetId") == _id(full_adapter, full_session, full_ally)
        for event in full_result["events"]
    )

    partial_preview, partial_result, partial_adapter, partial_session, partial_ally, partial_target = execute(5022, 5)
    assert partial_preview["targets"][0]["primary"]["kind"] == "damage"
    assert _consequence(partial_preview, "secondaryHealing")["recipientId"] == _id(
        partial_adapter, partial_session, partial_ally
    )
    assert any(
        event["type"] == "damageApplied"
        and event.get("targetId") == _id(partial_adapter, partial_session, partial_target)
        and event.get("amount", 0) > 0
        for event in partial_result["events"]
    )
    assert any(
        event["type"] == "healingApplied"
        and event.get("targetId") == _id(partial_adapter, partial_session, partial_ally)
        and event.get("amount", 0) > 0
        for event in partial_result["events"]
    )

    normal_preview, normal_result, normal_adapter, normal_session, normal_ally, normal_target = execute(5023)
    assert normal_preview["targets"][0]["primary"]["kind"] == "damage"
    assert _consequence(normal_preview, "secondaryHealing")["recipientId"] == _id(
        normal_adapter, normal_session, normal_ally
    )
    assert any(
        event["type"] == "healingApplied"
        and event.get("targetId") == _id(normal_adapter, normal_session, normal_ally)
        and event.get("amount", 0) > 0
        for event in normal_result["events"]
    )


def test_penance_mixed_buff_loop_effect_is_reported_as_unavailable():
    adapter, session, actor = _session(size=3, seed=5015)
    protected_ally = session.game.player_heroes[1]
    later_ally = session.game.player_heroes[2]
    target = session.game.opponent_heroes[0]
    protected_ally.status["holy_word_redemption"] = True
    protected_ally.add_buff(Buff("Holy Word Redemption", 5, actor, 0.7))
    # The legacy Penance implementation later reads its leaked loop variable.
    # This unrelated final record would author the linked heal, so a precise
    # recipient-specific preview would be false confidence.
    later_ally.add_buff(Buff("Unrelated Aura", 2, actor, 0.25))
    before = _state_fingerprint(adapter, session)

    result = adapter.preview(
        session,
        _request(adapter, session, "skill.priest.penance", [target]),
    )

    assert result["coverage"] == "unavailable"
    assert result["reasonId"] == "preview.unauditedState"
    assert _state_fingerprint(adapter, session) == before


def test_redemption_application_refresh_and_ambiguous_states():
    adapter, session, actor = _session()
    target = actor

    application = adapter.preview(
        session,
        _request(adapter, session, "skill.priest.holy_word_redemption", [target]),
    )
    fact = application["targets"][0]
    assert fact["primary"] is None
    assert fact["directHitChancePercent"] is None
    assert _consequence(application, "holyWordRedemption") == {
        "kind": "holyWordRedemption",
        "certainty": "always",
        "recipientId": _id(adapter, session, target),
        "duration": 5,
        "outcome": "firstApplication",
    }
    BattlePreviewResponse.model_validate(adapter.envelope(session, application))

    target.status["holy_word_redemption"] = True
    target.add_buff(Buff("Holy Word Redemption", 2, actor, 0.7))
    refresh = adapter.preview(
        session,
        _request(adapter, session, "skill.priest.holy_word_redemption", [target]),
    )
    assert _consequence(refresh, "holyWordRedemption")["outcome"] == "durationRefresh"

    target.buffs.clear()
    foreign = session.game.opponent_heroes[0]
    target.add_buff(Buff("Holy Word Redemption", 3, foreign, 0.7))
    unavailable = adapter.preview(
        session,
        _request(adapter, session, "skill.priest.holy_word_redemption", [target]),
    )
    assert unavailable["coverage"] == "unavailable"

    adapter_two, session_two, actor_two = _session(size=2, seed=5006)
    actor_two.hp = round(actor_two.hp_max * 0.75)
    low_hp = adapter_two.preview(
        session_two,
        _request(
            adapter_two,
            session_two,
            "skill.priest.holy_word_redemption",
            [session_two.game.player_heroes[1]],
        ),
    )
    assert low_hp["coverage"] == "unavailable"
    assert low_hp["reasonId"] == "preview.unauditedState"


def test_punishment_preserves_live_cardinality_draft_and_status_boundary():
    adapter_one, session_one, _ = _session()
    only_target = session_one.game.opponent_heroes[0]
    single = adapter_one.preview(
        session_one,
        _request(
            adapter_one,
            session_one,
            "skill.priest.holy_word_punishment",
            [only_target],
        ),
    )
    assert single["targets"][0]["primary"]["amountRange"] == {"min": 7, "max": 11}
    status = _consequence(single, "holyWordPunishment")
    assert status["outcome"] == "firstApplication"
    assert status["duration"] == 4

    adapter, session, _ = _session(size=2)
    targets = session.game.opponent_heroes
    draft = adapter.preview(
        session,
        _request(adapter, session, "skill.priest.holy_word_punishment", targets[:1]),
    )
    pair = adapter.preview(
        session,
        _request(adapter, session, "skill.priest.holy_word_punishment", targets),
    )
    assert len(draft["targets"]) == 1
    assert len(pair["targets"]) == 2
    rejected = adapter.submit(
        session,
        {
            "type": "useSkill",
            "commandId": "cmd.punishment.draft",
            **_request(
                adapter,
                session,
                "skill.priest.holy_word_punishment",
                targets[:1],
            ),
        },
    )
    assert rejected["accepted"] is False
    assert rejected["code"] == "illegalTargets"

    targets[0].status["holy_word_punishment"] = True
    active = adapter.preview(
        session,
        _request(adapter, session, "skill.priest.holy_word_punishment", targets[:1]),
    )
    active_status = _consequence(active, "holyWordPunishment")
    assert active_status["outcome"] == "alreadyActive"
    assert active_status["duration"] is None

    targets[0].status["shield_of_protection"] = True
    prevented = adapter.preview(
        session,
        _request(adapter, session, "skill.priest.holy_word_punishment", targets[:1]),
    )
    assert prevented["targets"][0]["primary"]["kind"] == "prevented"
    assert prevented["targets"][0]["consequences"] == []

    with pytest.raises(BattleAdapterError, match="Duplicate"):
        adapter.preview(
            session,
            _request(
                adapter,
                session,
                "skill.priest.holy_word_punishment",
                [targets[1], targets[1]],
            ),
        )


def test_punishment_linked_healing_is_per_target_and_recipient_not_aggregate():
    adapter, session, actor = _session(size=2)
    ally = session.game.player_heroes[1]
    ally.status["holy_word_redemption"] = True
    ally.add_buff(Buff("Holy Word Redemption", 5, actor, 0.7))
    targets = session.game.opponent_heroes

    result = adapter.preview(
        session,
        _request(adapter, session, "skill.priest.holy_word_punishment", targets),
    )

    assert len(result["targets"]) == 2
    for fact in result["targets"]:
        linked = next(
            item for item in fact["consequences"] if item["kind"] == "secondaryHealing"
        )
        assert linked["recipientId"] == _id(adapter, session, ally)
        assert linked["amountRange"] == {"min": 4, "max": 9}


@pytest.mark.parametrize(
    "skill_id,target_kind",
    [
        ("skill.priest.penance", "ally"),
        ("skill.priest.penance", "enemy"),
        ("skill.priest.holy_word_redemption", "ally"),
        ("skill.priest.holy_word_punishment", "enemy"),
    ],
)
def test_discipline_preview_never_mutates_or_consumes_rng(skill_id, target_kind):
    adapter, session, _ = _session()
    target = (
        session.game.player_heroes[0]
        if target_kind == "ally"
        else session.game.opponent_heroes[0]
    )
    request = _request(adapter, session, skill_id, [target])
    before = _state_fingerprint(adapter, session)
    global_rng = random.getstate()

    def fail(*_args, **_kwargs):
        raise AssertionError("preview consumed RNG")

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(random, "random", fail)
        patch.setattr(random, "randint", fail)
        patch.setattr(random, "choice", fail)
        patch.setattr(random, "sample", fail)
        adapter.preview(session, request)

    assert _state_fingerprint(adapter, session) == before
    assert random.getstate() == global_rng


@pytest.mark.parametrize(
    "skill_id,target_index",
    [
        ("skill.priest.penance", 0),
        ("skill.priest.holy_word_punishment", 0),
    ],
)
def test_preview_does_not_change_same_seed_discipline_command(skill_id, target_index):
    preview_adapter, preview_session, _ = _session(size=2, seed=5010)
    control_adapter, control_session, _ = _session(size=2, seed=5010)
    preview_targets = preview_session.game.opponent_heroes
    control_targets = control_session.game.opponent_heroes
    target_count = 2 if skill_id.endswith("holy_word_punishment") else 1
    selected_preview = preview_targets[target_index:target_index + target_count]
    selected_control = control_targets[target_index:target_index + target_count]
    preview_adapter.preview(
        preview_session,
        _request(preview_adapter, preview_session, skill_id, selected_preview),
    )

    def submit(adapter, session, targets, command_id):
        request = _request(adapter, session, skill_id, targets)
        return adapter.submit(
            session,
            {
                "type": "useSkill",
                "commandId": command_id,
                **request,
            },
        )

    after_preview = submit(
        preview_adapter, preview_session, selected_preview, "cmd.discipline.previewed"
    )
    untouched = submit(
        control_adapter, control_session, selected_control, "cmd.discipline.control"
    )
    assert [
        (event["type"], event.get("amount"), event.get("targetId"), event.get("statusId"))
        for event in after_preview["events"]
    ] == [
        (event["type"], event.get("amount"), event.get("targetId"), event.get("statusId"))
        for event in untouched["events"]
    ]
    assert after_preview["snapshot"] == untouched["snapshot"]


def test_unavailable_low_hp_redemption_preview_preserves_extra_target_rng_stream():
    preview_adapter, preview_session, preview_actor = _session(size=2, seed=5011)
    control_adapter, control_session, control_actor = _session(size=2, seed=5011)
    preview_actor.hp = round(preview_actor.hp_max * 0.75)
    control_actor.hp = round(control_actor.hp_max * 0.75)
    preview_target = preview_session.game.player_heroes[1]
    control_target = control_session.game.player_heroes[1]
    skill_id = "skill.priest.holy_word_redemption"

    result = preview_adapter.preview(
        preview_session,
        _request(preview_adapter, preview_session, skill_id, [preview_target]),
    )
    assert result["coverage"] == "unavailable"

    def submit(adapter, session, target, command_id):
        return adapter.submit(
            session,
            {
                "type": "useSkill",
                "commandId": command_id,
                **_request(adapter, session, skill_id, [target]),
            },
        )

    after_preview = submit(
        preview_adapter, preview_session, preview_target, "cmd.redemption.previewed"
    )
    untouched = submit(
        control_adapter, control_session, control_target, "cmd.redemption.control"
    )
    assert [
        (event["type"], event.get("targetId"), event.get("statusId"))
        for event in after_preview["events"]
    ] == [
        (event["type"], event.get("targetId"), event.get("statusId"))
        for event in untouched["events"]
    ]
    assert after_preview["snapshot"] == untouched["snapshot"]


@pytest.mark.parametrize("invalid", ["stale", "dead", "wrongSide"])
def test_discipline_preview_rejects_stale_dead_and_wrong_side(invalid):
    adapter, session, actor = _session(size=2)
    enemy = session.game.opponent_heroes[0]
    request = _request(
        adapter, session, "skill.priest.holy_word_punishment", [enemy]
    )
    if invalid == "stale":
        request["expectedRevision"] += 1
    elif invalid == "dead":
        enemy.hp = 0
    else:
        request["targetIds"] = [_id(adapter, session, actor)]
    before = _state_fingerprint(adapter, session)
    with pytest.raises(BattleAdapterError):
        adapter.preview(session, request)
    assert _state_fingerprint(adapter, session) == before


def test_preview_http_contract_accepts_redemption_status_only_primary():
    client = TestClient(app)
    created = client.post(
        "/api/v1/battles",
        json={
            "battleSize": 1,
            "playerTeam": ["hero.priest.discipline"],
            "enemyTeam": ["hero.rogue.comprehensiveness"],
            "enemyControlMode": "player",
            "seed": 5012,
        },
    )
    assert created.status_code == 200
    battle_id = created.json()["battleId"]
    session = registry.get(battle_id)
    assert session is not None
    actor = session.game.player_heroes[0]
    session.game.unactioned_sorted_heroes = [actor]
    request = _request(
        registry.adapter,
        session,
        "skill.priest.holy_word_redemption",
        [actor],
    )

    response = client.post(f"/api/v1/battles/{battle_id}/preview", json=request)

    assert response.status_code == 200
    body = response.json()
    assert body["contractVersion"] == "1.0"
    assert body["data"]["targets"][0]["primary"] is None
    assert body["data"]["targets"][0]["consequences"][0]["kind"] == "holyWordRedemption"
