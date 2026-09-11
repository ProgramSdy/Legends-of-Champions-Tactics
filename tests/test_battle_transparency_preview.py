"""Regression coverage for the audited, read-only battle preview boundary."""

from __future__ import annotations

from copy import deepcopy
import random

import pytest
from fastapi.testclient import TestClient

from battle_api.adapter import BattleAdapter, BattleAdapterError
from battle_api.app import app, registry


def _session(player: list[str], enemy: list[str], *, seed: int = 73):
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=seed,
        battle_id=f"battle.preview.{seed}",
        battle_size=len(player),
        player_team=player,
        enemy_team=enemy,
        enemy_control_mode="player",
        player_formation="front-rear" if len(player) == 2 else "one-front-two-rear" if len(player) == 3 else None,
        enemy_formation="front-rear" if len(enemy) == 2 else "one-front-two-rear" if len(enemy) == 3 else None,
    )
    # Creation can leave a faster enemy first.  This is a test fixture setup,
    # not a production shortcut: the preview itself must only inspect state.
    friendly = session.game.player_heroes[0]
    session.game.unactioned_sorted_heroes = [friendly]
    return adapter, session


def _request(adapter, session, skill_id: str, targets: list[str]):
    snapshot = adapter.snapshot(session)
    return {
        "expectedRevision": session.revision,
        "actorId": snapshot["activeCombatantId"],
        "skillId": skill_id,
        "targetIds": targets,
    }


def test_each_mage_and_rogue_skill_returns_target_specific_authoritative_facts():
    cases = [
        ("hero.mage.comprehensiveness", "hero.rogue.comprehensiveness", [
            "skill.mage.fireball", "skill.mage.frost_bolt",
        ]),
        ("hero.rogue.comprehensiveness", "hero.mage.comprehensiveness", [
            "skill.rogue.sharp_blade", "skill.rogue.poisoned_dagger",
        ]),
    ]
    for player, enemy, skills in cases:
        adapter, session = _session([player], [enemy])
        target = adapter.snapshot(session)["sides"][1]["combatantIds"][0]
        for skill_id in skills:
            result = adapter.preview(session, _request(adapter, session, skill_id, [target]))
            assert result["coverage"] == "authoritative"
            assert result["revision"] == session.revision
            assert len(result["targets"]) == 1
            fact = result["targets"][0]
            assert fact["targetId"] == target
            assert fact["currentHp"] > 0
            assert fact["primary"]["amountRange"]["min"] <= fact["primary"]["amountRange"]["max"]
            assert 0 <= fact["directHitChancePercent"] <= 100
            expected = {
                "skill.mage.fireball": {"min": 51, "max": 61},
                "skill.mage.frost_bolt": {"min": 49, "max": 52},
                "skill.rogue.sharp_blade": {"min": 54, "max": 59},
                "skill.rogue.poisoned_dagger": {"min": 28, "max": 30},
            }[skill_id]
            assert fact["primary"]["amountRange"] == expected


def test_arcane_missiles_requires_exact_distinct_pair_and_returns_per_target_facts():
    adapter, session = _session(
        ["hero.mage.comprehensiveness", "hero.rogue.comprehensiveness"],
        ["hero.rogue.comprehensiveness", "hero.paladin.retribution"],
    )
    snapshot = adapter.snapshot(session)
    targets = snapshot["sides"][1]["combatantIds"]
    result = adapter.preview(session, _request(adapter, session, "skill.mage.arcane_missiles", targets))
    assert result["coverage"] == "authoritative"
    assert result["selectedTargetIds"] == targets
    assert [fact["targetId"] for fact in result["targets"]] == targets
    with pytest.raises(BattleAdapterError, match="exactly 2"):
        adapter.preview(session, _request(adapter, session, "skill.mage.arcane_missiles", targets[:1]))
    with pytest.raises(BattleAdapterError, match="Duplicate"):
        adapter.preview(session, _request(adapter, session, "skill.mage.arcane_missiles", [targets[0], targets[0]]))


def test_preview_does_not_mutate_session_or_consume_randomness():
    adapter, session = _session(["hero.mage.comprehensiveness"], ["hero.rogue.comprehensiveness"])
    snapshot_before = deepcopy(adapter.snapshot(session))
    rng_before = session.rng_state
    global_before = random.getstate()
    target = snapshot_before["sides"][1]["combatantIds"][0]

    def fail(*_args, **_kwargs):
        raise AssertionError("preview consumed RNG")

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(random, "random", fail)
        patch.setattr(random, "randint", fail)
        patch.setattr(random, "choice", fail)
        patch.setattr(random, "sample", fail)
        adapter.preview(session, _request(adapter, session, "skill.mage.fireball", [target]))
    assert adapter.snapshot(session) == snapshot_before
    assert session.rng_state == rng_before
    assert random.getstate() == global_before


@pytest.mark.parametrize("bad_request", [
    {"expectedRevision": 999},
    {"skillId": "skill.mage.shadow_evasion"},
])
def test_preview_rejects_stale_or_out_of_scope_without_mutation(bad_request):
    adapter, session = _session(["hero.mage.comprehensiveness"], ["hero.rogue.comprehensiveness"])
    before = deepcopy(adapter.snapshot(session))
    target = before["sides"][1]["combatantIds"][0]
    request = _request(adapter, session, bad_request.get("skillId", "skill.mage.fireball"), [target])
    request.update(bad_request)
    with pytest.raises(BattleAdapterError):
        adapter.preview(session, request)
    assert adapter.snapshot(session) == before


def test_preview_separates_rogue_material_proc_consequences():
    adapter, session = _session(["hero.rogue.comprehensiveness"], ["hero.mage.comprehensiveness"])
    target = adapter.snapshot(session)["sides"][1]["combatantIds"][0]
    sharp = adapter.preview(session, _request(adapter, session, "skill.rogue.sharp_blade", [target]))
    poison = adapter.preview(session, _request(adapter, session, "skill.rogue.poisoned_dagger", [target]))
    assert sharp["targets"][0]["consequences"] == [{"kind": "bleed", "certainty": "conditional", "chancePercent": 50}]
    assert poison["targets"][0]["consequences"] == [{"kind": "poison", "certainty": "conditional", "chancePercent": 85}]


def test_preview_hides_rogue_poison_when_stack_cap_blocks_new_application():
    adapter, session = _session(["hero.rogue.comprehensiveness"], ["hero.mage.comprehensiveness"])
    target = session.game.opponent_heroes[0]
    target.status["poisoned_dagger"] = True
    target.poisoned_dagger_stacks = 2
    target_id = adapter.snapshot(session)["sides"][1]["combatantIds"][0]
    result = adapter.preview(session, _request(adapter, session, "skill.rogue.poisoned_dagger", [target_id]))
    assert result["targets"][0]["consequences"] == []


def test_preview_omits_frost_cold_consequence_when_cold_is_already_active():
    adapter, session = _session(["hero.mage.comprehensiveness"], ["hero.rogue.comprehensiveness"])
    target = session.game.opponent_heroes[0]
    target.status["cold"] = True
    target_id = adapter.snapshot(session)["sides"][1]["combatantIds"][0]
    result = adapter.preview(session, _request(adapter, session, "skill.mage.frost_bolt", [target_id]))
    assert result["targets"][0]["consequences"] == []


def test_preview_reports_deterministic_prevention_and_never_uses_random_helpers():
    adapter, session = _session(["hero.mage.comprehensiveness"], ["hero.rogue.comprehensiveness"])
    target = session.game.opponent_heroes[0]
    target.status["shield_of_protection"] = True
    target_id = adapter.snapshot(session)["sides"][1]["combatantIds"][0]

    def fail(*_args, **_kwargs):
        raise AssertionError("preview consumed RNG")

    with pytest.MonkeyPatch.context() as patch:
        for name in ("random", "randint", "choice", "sample", "shuffle"):
            patch.setattr(random, name, fail)
        result = adapter.preview(session, _request(adapter, session, "skill.mage.fireball", [target_id]))
    fact = result["targets"][0]
    assert fact["primary"] == {
        "kind": "prevented", "amountRange": {"min": 0, "max": 0},
        "reasonId": "prevention.allDamage",
    }


def test_preview_hit_chance_matches_skill_evasion_rule_at_agility_cap_boundary():
    adapter, session = _session(["hero.mage.comprehensiveness"], ["hero.rogue.comprehensiveness"])
    target = session.game.opponent_heroes[0]
    # Skill.evasion_check uses half agility when explicit evasion is lower,
    # with the evasion chance capped at 50%; the preview reports its inverse.
    target.agility = 40
    target.evasion_capability = 0
    target_id = adapter.snapshot(session)["sides"][1]["combatantIds"][0]
    result = adapter.preview(session, _request(adapter, session, "skill.mage.fireball", [target_id]))
    assert result["targets"][0]["directHitChancePercent"] == 80


@pytest.mark.parametrize("mutation", ["wrong_actor", "dead_target", "cooldown"])
def test_preview_rejects_invalid_actor_target_or_skill(mutation):
    adapter, session = _session(["hero.mage.comprehensiveness"], ["hero.rogue.comprehensiveness"])
    snapshot = adapter.snapshot(session)
    target_id = snapshot["sides"][1]["combatantIds"][0]
    request = _request(adapter, session, "skill.mage.fireball", [target_id])
    if mutation == "wrong_actor":
        request["actorId"] = "enemy.nighthawk"
    elif mutation == "dead_target":
        session.game.opponent_heroes[0].hp = 0
    else:
        session.game.player_heroes[0].skills[0].if_cooldown = True
    with pytest.raises(BattleAdapterError):
        adapter.preview(session, request)


def test_preview_does_not_change_same_seed_command_result():
    first_adapter, first = _session(["hero.mage.comprehensiveness"], ["hero.rogue.comprehensiveness"], seed=91)
    second_adapter, second = _session(["hero.mage.comprehensiveness"], ["hero.rogue.comprehensiveness"], seed=91)
    target = first_adapter.snapshot(first)["sides"][1]["combatantIds"][0]
    first_adapter.preview(first, _request(first_adapter, first, "skill.mage.fireball", [target]))
    first_result = first_adapter.submit(first, {
        "type": "useSkill", "commandId": "cmd.preview-control", "expectedRevision": first.revision,
        "actorId": first_adapter.snapshot(first)["activeCombatantId"],
        "skillId": "skill.mage.fireball", "targetIds": [target],
    })
    second_result = second_adapter.submit(second, {
        "type": "useSkill", "commandId": "cmd.preview-untouched", "expectedRevision": second.revision,
        "actorId": second_adapter.snapshot(second)["activeCombatantId"],
        "skillId": "skill.mage.fireball", "targetIds": [target],
    })
    assert [(e["type"], e.get("amount"), e.get("targetId")) for e in first_result["events"]] == [
        (e["type"], e.get("amount"), e.get("targetId")) for e in second_result["events"]
    ]
    assert first_result["snapshot"] == second_result["snapshot"]


def test_preview_api_success_stale_out_of_scope_and_missing_battle():
    client = TestClient(app)
    created = client.post("/api/v1/battles", json={
        "battleSize": 1,
        "playerTeam": ["hero.mage.comprehensiveness"],
        "enemyTeam": ["hero.rogue.comprehensiveness"],
        "enemyControlMode": "player",
        "seed": 17,
    })
    assert created.status_code == 200
    battle_id = created.json()["battleId"]
    session = registry.get(battle_id)
    assert session is not None
    session.game.unactioned_sorted_heroes = [session.game.player_heroes[0]]
    snapshot = registry.adapter.snapshot(session)
    target_id = snapshot["sides"][1]["combatantIds"][0]
    request = {
        "expectedRevision": session.revision,
        "actorId": snapshot["activeCombatantId"],
        "skillId": "skill.mage.fireball",
        "targetIds": [target_id],
    }
    success = client.post(f"/api/v1/battles/{battle_id}/preview", json=request)
    assert success.status_code == 200
    assert success.json()["data"]["coverage"] == "authoritative"
    assert success.json()["revision"] == request["expectedRevision"]

    stale = client.post(f"/api/v1/battles/{battle_id}/preview", json={**request, "expectedRevision": 99})
    assert stale.status_code == 409
    assert stale.json()["detail"]["code"] == "staleRevision"
    unsupported = client.post(f"/api/v1/battles/{battle_id}/preview", json={**request, "skillId": "skill.rogue.shadow_evasion"})
    assert unsupported.status_code == 422
    assert unsupported.json()["detail"]["code"] in {"illegalSkill", "previewUnavailable"}
    missing = client.post("/api/v1/battles/not-found/preview", json=request)
    assert missing.status_code == 404
