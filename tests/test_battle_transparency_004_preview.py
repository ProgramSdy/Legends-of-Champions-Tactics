"""Deterministic BTT-004 preview contract and purity coverage."""

from copy import deepcopy
import random

import pytest

from battle_api.adapter import BattleAdapter, BattleAdapterError


PALADIN_CASES = [
    ("hero.paladin.protection", "skill.paladin.hammer_of_revenge", "Hammer of Revenge"),
    ("hero.paladin.protection", "skill.paladin.shield_of_righteous", "Shield of Righteous"),
    ("hero.paladin.protection", "skill.paladin.heroric_charge", "Heroric Charge"),
    ("hero.paladin.holy", "skill.paladin.purify_healing", "Purify Healing"),
    ("hero.paladin.holy", "skill.paladin.holy_blast", "Holy Blast"),
    ("hero.paladin.holy", "skill.paladin.shield_of_protection", "Shield of Protection"),
]


def _session(definition, *, size=1, seed=404):
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=seed,
        battle_id=f"battle.preview-004.{definition}.{size}.{seed}",
        battle_size=size,
        player_team=[definition] * size,
        enemy_team=["hero.rogue.comprehensiveness"] * size,
        enemy_control_mode="player",
        player_formation="front-rear" if size == 2 else "one-front-two-rear" if size == 3 else None,
        enemy_formation="front-rear" if size == 2 else "one-front-two-rear" if size == 3 else None,
    )
    session.game.unactioned_sorted_heroes = [session.game.player_heroes[0]]
    return adapter, session


def _request(adapter, session, skill_id, target_ids):
    return {
        "expectedRevision": session.revision,
        "actorId": adapter.snapshot(session)["activeCombatantId"],
        "skillId": skill_id,
        "targetIds": list(target_ids),
    }


def _ids(adapter, session, heroes):
    return [adapter._combatant_id(session, hero) for hero in heroes]


def _consequences(result, *, self_preview=False):
    value = result["selfPreview"] if self_preview else result["targets"][0]
    return value["consequences"]


@pytest.mark.parametrize("definition,skill_id,name", PALADIN_CASES)
def test_all_six_paladin_skills_are_authoritative_and_read_only(definition, skill_id, name):
    adapter, session = _session(definition)
    if name == "Shield of Protection":
        target_ids = []
    elif name == "Purify Healing":
        target_ids = _ids(adapter, session, [session.game.player_heroes[0]])
    else:
        target_ids = _ids(adapter, session, [session.game.opponent_heroes[0]])
    before = deepcopy(adapter.snapshot(session))
    session_rng = session.rng_state
    global_rng = random.getstate()

    result = adapter.preview(session, _request(adapter, session, skill_id, target_ids))

    assert result["coverage"] == "authoritative"
    assert result["skillId"] == skill_id
    assert result["requestedTargetIds"] == target_ids
    assert result["selectedTargetIds"] == target_ids
    if name == "Shield of Protection":
        assert result["targets"] == []
        assert result["selfPreview"]["recipientId"] == result["actorId"]
    else:
        fact = result["targets"][0]
        assert fact["currentHp"] > 0
        assert fact["primary"]["amountRange"]["min"] <= fact["primary"]["amountRange"]["max"]
        if name == "Purify Healing":
            assert fact["primary"]["kind"] == "healing"
            assert fact["directHitChancePercent"] is None
        else:
            assert fact["primary"]["kind"] in {"damage", "prevented"}
            assert isinstance(fact["directHitChancePercent"], int)
    assert adapter.snapshot(session) == before
    assert session.rng_state == session_rng
    assert random.getstate() == global_rng


def test_paladin_preview_rejects_passive_and_invalid_requests_without_mutation():
    adapter, session = _session("hero.paladin.protection")
    target_id = _ids(adapter, session, [session.game.opponent_heroes[0]])[0]
    before = deepcopy(adapter.snapshot(session))
    cases = [
        {"skillId": "skill.paladin.holy_aura", "targetIds": []},
        {"skillId": "skill.paladin.hammer_of_revenge", "targetIds": [target_id, target_id]},
        {"skillId": "skill.paladin.hammer_of_revenge", "targetIds": []},
        {"skillId": "skill.paladin.hammer_of_revenge", "targetIds": ["enemy.missing"]},
        {"skillId": "skill.paladin.hammer_of_revenge", "targetIds": [target_id], "expectedRevision": 999},
    ]
    for override in cases:
        request = _request(adapter, session, override["skillId"], override["targetIds"])
        request.update(override)
        with pytest.raises(BattleAdapterError):
            adapter.preview(session, request)
        assert adapter.snapshot(session) == before


def test_shield_of_protection_is_targetless_and_uses_self_preview():
    adapter, session = _session("hero.paladin.holy")
    actor = session.game.player_heroes[0]
    result = adapter.preview(session, _request(adapter, session, "skill.paladin.shield_of_protection", []))
    self_preview = result["selfPreview"]
    assert result["targets"] == []
    assert self_preview["recipientId"] == result["actorId"]
    assert {item["kind"] for item in self_preview["consequences"]} >= {"damageImmunity", "cooldown"}

    with pytest.raises(BattleAdapterError, match="targetless self preview"):
        adapter.preview(
            session,
            _request(
                adapter,
                session,
                "skill.paladin.shield_of_protection",
                [_ids(adapter, session, [session.game.opponent_heroes[0]])[0]],
            ),
        )
    assert actor.status["shield_of_protection"] is False


def test_holy_blast_draft_full_and_ordered_per_target_facts():
    adapter, session = _session("hero.paladin.holy", size=2)
    target_ids = _ids(adapter, session, session.game.opponent_heroes)
    draft = adapter.preview(session, _request(adapter, session, "skill.paladin.holy_blast", target_ids[:1]))
    pair = adapter.preview(session, _request(adapter, session, "skill.paladin.holy_blast", target_ids))
    reverse = adapter.preview(session, _request(adapter, session, "skill.paladin.holy_blast", target_ids[::-1]))
    assert draft["selectedTargetIds"] == target_ids[:1]
    assert [item["targetId"] for item in draft["targets"]] == target_ids[:1]
    assert [item["targetId"] for item in pair["targets"]] == target_ids
    assert [item["targetId"] for item in reverse["targets"]] == target_ids[::-1]
    assert pair["targets"][0]["primary"]["amountRange"]["min"] >= 20
    assert all(item["primary"]["kind"] in {"damage", "prevented"} for item in pair["targets"])
    assert len(pair["targets"]) == 2

    with pytest.raises(BattleAdapterError, match="Duplicate"):
        adapter.preview(session, _request(adapter, session, "skill.paladin.holy_blast", [target_ids[0], target_ids[0]]))


def test_hammer_reports_live_debuff_band_and_first_only_damage_reduction():
    adapter, session = _session("hero.paladin.protection")
    actor = session.game.player_heroes[0]
    target = session.game.opponent_heroes[0]
    target_id = adapter._combatant_id(session, target)
    actor.status["shadow_word_pain"] = True
    actor.status["bleeding_moon_slash"] = True
    result = adapter.preview(session, _request(adapter, session, "skill.paladin.hammer_of_revenge", [target_id]))
    kinds = {item["kind"] for item in result["targets"][0]["consequences"]}
    bonus = next(item for item in result["targets"][0]["consequences"] if item["kind"] == "revengeDamageBonus")
    assert bonus["debuffCount"] == 2
    assert "damageReduction" not in kinds

    actor.status["shield_of_righteous"] = True
    result = adapter.preview(session, _request(adapter, session, "skill.paladin.hammer_of_revenge", [target_id]))
    assert any(item["kind"] == "damageReduction" for item in result["targets"][0]["consequences"])
    target.status["hammer_of_revenge"] = True
    result = adapter.preview(session, _request(adapter, session, "skill.paladin.hammer_of_revenge", [target_id]))
    assert not any(item["kind"] == "damageReduction" for item in result["targets"][0]["consequences"])


@pytest.mark.parametrize("stacks,expected", [(0, "firstApplication"), (1, "nextStack"), (2, "durationRefresh")])
def test_shield_of_righteous_reports_stack_and_cap_outcomes(stacks, expected):
    adapter, session = _session("hero.paladin.protection")
    actor = session.game.player_heroes[0]
    actor.status["shield_of_righteous"] = stacks > 0
    actor.shield_of_righteous_stacks = stacks
    actor.shield_of_righteous_duration = 1
    target_id = _ids(adapter, session, [session.game.opponent_heroes[0]])[0]
    result = adapter.preview(session, _request(adapter, session, "skill.paladin.shield_of_righteous", [target_id]))
    consequence = next(item for item in result["selfPreview"]["consequences"] if item["kind"] == "defenceIncrease")
    assert consequence["outcome"] == expected
    assert consequence["resultingStacks"] == min(stacks + 1, 2)


def test_purify_multiple_candidates_is_uncertain_and_never_specific():
    adapter, session = _session("hero.paladin.holy")
    target = session.game.player_heroes[0]
    target.status["poisoned_dagger"] = True
    target.status["bleeding_moon_slash"] = True
    target_id = adapter._combatant_id(session, target)
    before = deepcopy(adapter.snapshot(session))
    result = adapter.preview(session, _request(adapter, session, "skill.paladin.purify_healing", [target_id]))
    removal = next(item for item in result["targets"][0]["consequences"] if item["kind"] == "randomStatusRemoval")
    assert set(removal["candidateStatusIds"]) >= {"status.poisoned_dagger", "status.bleeding_moon_slash"}
    assert removal["maximumRemovals"] == 1
    assert removal["mayRemoveNone"] is False
    assert adapter.snapshot(session) == before


@pytest.mark.parametrize("immune,casting", [(False, False), (False, True), (True, False), (True, True)])
def test_heroric_charge_control_and_casting_boundaries(immune, casting):
    adapter, session = _session("hero.paladin.protection")
    target = session.game.opponent_heroes[0]
    target.is_immunity_condition_control = immune
    target.status["warlust"] = immune
    target.status["magic_casting"] = casting
    target_id = adapter._combatant_id(session, target)
    result = adapter.preview(session, _request(adapter, session, "skill.paladin.heroric_charge", [target_id]))
    kinds = {item["kind"] for item in result["targets"][0]["consequences"]}
    if not immune:
        assert "scoff" in kinds
    else:
        assert "scoff" not in kinds
    if casting:
        assert "castingInterrupted" in kinds
    else:
        assert "castingInterrupted" not in kinds


@pytest.mark.parametrize(
    "warlust,control_flag",
    [(True, False), (False, True)],
)
def test_heroric_charge_rejects_mismatched_warlust_control_state(warlust, control_flag):
    adapter, session = _session("hero.paladin.protection")
    target = session.game.opponent_heroes[0]
    target.status["warlust"] = warlust
    target.is_immunity_condition_control = control_flag
    target_id = adapter._combatant_id(session, target)
    result = adapter.preview(
        session,
        _request(adapter, session, "skill.paladin.heroric_charge", [target_id]),
    )
    assert result["coverage"] == "unavailable"
    assert result["reasonId"] == "preview.unauditedState"
    assert result["targets"] == []
    assert result["selfPreview"] is None


def test_holy_blast_second_target_exposes_full_capable_union_when_first_can_evade():
    adapter, session = _session("hero.paladin.holy", size=2)
    first, second = session.game.opponent_heroes
    # 50% Hit Chance makes the first selected target capable of either
    # evading or landing; the second target can therefore be first successful.
    first.agility = 100
    first.evasion_capability = 50
    first.position = "front"
    second.position = "front"
    target_ids = _ids(adapter, session, [first, second])
    result = adapter.preview(
        session,
        _request(adapter, session, "skill.paladin.holy_blast", target_ids),
    )
    assert result["selectedTargetIds"] == target_ids
    assert result["targets"][0]["directHitChancePercent"] == 50
    assert result["targets"][1]["primary"]["amountRange"] == {"min": 14, "max": 25}


def test_holy_blast_preview_preserves_same_seed_command_result():
    preview_adapter, preview_session = _session("hero.paladin.holy", size=2, seed=944)
    control_adapter, control_session = _session("hero.paladin.holy", size=2, seed=944)
    preview_ids = _ids(preview_adapter, preview_session, preview_session.game.opponent_heroes)
    control_ids = _ids(control_adapter, control_session, control_session.game.opponent_heroes)
    assert preview_ids == control_ids
    request = _request(preview_adapter, preview_session, "skill.paladin.holy_blast", preview_ids)
    before = preview_adapter.snapshot(preview_session)
    preview_adapter.preview(preview_session, request)
    assert preview_adapter.snapshot(preview_session) == before
    assert preview_session.rng_state == control_session.rng_state

    command = {
        "type": "useSkill",
        "commandId": "cmd.preview-004.holy-blast-same-seed",
        "expectedRevision": preview_session.revision,
        "actorId": request["actorId"],
        "skillId": request["skillId"],
        "targetIds": preview_ids,
    }
    with_preview = preview_adapter.submit(preview_session, command)
    untouched = control_adapter.submit(control_session, command)
    assert with_preview == untouched
    assert preview_session.rng_state == control_session.rng_state


def test_purify_unsupported_sole_candidate_is_authoritative_without_specific_removal():
    adapter, session = _session("hero.paladin.holy")
    target = session.game.player_heroes[0]
    target.status["frost_fever"] = True  # listed disease, but no live record to clear
    target_id = adapter._combatant_id(session, target)
    result = adapter.preview(
        session,
        _request(adapter, session, "skill.paladin.purify_healing", [target_id]),
    )
    assert result["coverage"] == "authoritative"
    assert all(item["kind"] != "statusRemoval" for item in result["targets"][0]["consequences"])
    assert all(item["kind"] != "randomStatusRemoval" for item in result["targets"][0]["consequences"])


def test_purify_unstable_compound_is_unavailable_without_dispeller_or_rng_use():
    adapter, session = _session("hero.paladin.holy")
    target = session.game.player_heroes[0]
    target.status["unstable_compound"] = True
    target_id = adapter._combatant_id(session, target)
    before = deepcopy(adapter.snapshot(session))
    session_rng = session.rng_state
    global_rng = random.getstate()
    result = adapter.preview(
        session,
        _request(adapter, session, "skill.paladin.purify_healing", [target_id]),
    )
    assert result["coverage"] == "unavailable"
    assert result["selfPreview"] is None
    assert adapter.snapshot(session) == before
    assert session.rng_state == session_rng
    assert random.getstate() == global_rng


def test_paladin_preview_calls_no_random_helpers_on_success_or_rejection(monkeypatch):
    adapter, session = _session("hero.paladin.protection")
    target_id = _ids(adapter, session, [session.game.opponent_heroes[0]])[0]

    def fail(*_args, **_kwargs):
        raise AssertionError("preview consumed randomness")

    for name in ("random", "randint", "choice", "sample", "shuffle"):
        monkeypatch.setattr(random, name, fail)
    adapter.preview(
        session,
        _request(adapter, session, "skill.paladin.hammer_of_revenge", [target_id]),
    )
    rejected = _request(adapter, session, "skill.paladin.hammer_of_revenge", [target_id, target_id])
    with pytest.raises(BattleAdapterError):
        adapter.preview(session, rejected)
