"""Authoritative, non-mutating preview coverage for the published Warrior roster."""

from __future__ import annotations

from copy import deepcopy
import random

import pytest

from battle_api.adapter import BattleAdapter, BattleAdapterError


WARRIOR_SKILLS = (
    ("hero.warrior.defence", "skill.warrior.devastate", "Devastate", False),
    ("hero.warrior.defence", "skill.warrior.shield_bash", "Shield Bash", False),
    ("hero.warrior.defence", "skill.warrior.thunder_pot", "Thunder Pot", False),
    ("hero.warrior.weapon_master", "skill.warrior.fatal_strike", "Fatal Strike", False),
    ("hero.warrior.weapon_master", "skill.warrior.armor_crush", "Armor Crush", False),
    ("hero.warrior.weapon_master", "skill.warrior.antivenom_potion", "Antivenom Potion", True),
    ("hero.warrior.berserker", "skill.warrior.moon_slash", "Moon Slash", False),
    ("hero.warrior.berserker", "skill.warrior.warlust", "Warlust", True),
    ("hero.warrior.berserker", "skill.warrior.strike_of_meteorite", "Strike of Meteorite", False),
)


def _session(player_definition, *, size=1, seed=303):
    adapter = BattleAdapter()
    player_team = [player_definition] * size
    enemy_team = ["hero.rogue.comprehensiveness"] * size
    session, _ = adapter.create_battle(
        seed=seed,
        battle_id=f"battle.preview-003.{player_definition}.{size}.{seed}",
        battle_size=size,
        player_team=player_team,
        enemy_team=enemy_team,
        enemy_control_mode="player",
        player_formation="front-rear" if size == 2 else None,
        enemy_formation="front-rear" if size == 2 else None,
    )
    session.game.unactioned_sorted_heroes = [session.game.player_heroes[0]]
    return adapter, session


def _request(adapter, session, skill_id, target_ids):
    return {
        "expectedRevision": session.revision,
        "actorId": adapter.snapshot(session)["activeCombatantId"],
        "skillId": skill_id,
        "targetIds": target_ids,
    }


def _skill(actor, name):
    return next(skill for skill in actor.skills if skill.name == name)


@pytest.mark.parametrize(
    ("definition_id", "skill_id", "name", "targetless"), WARRIOR_SKILLS
)
def test_every_published_warrior_skill_has_a_finite_authoritative_preview(
    definition_id, skill_id, name, targetless
):
    adapter, session = _session(definition_id)
    actor = session.game.player_heroes[0]
    target = session.game.opponent_heroes[0]
    target_id = adapter._combatant_id(session, target)
    request = _request(adapter, session, skill_id, [] if targetless else [target_id])
    before_snapshot = deepcopy(adapter.snapshot(session))
    before_rng = session.rng_state
    global_rng = random.getstate()

    preview = adapter.preview(session, request)

    assert preview["coverage"] == "authoritative"
    assert preview["actorId"] == request["actorId"]
    assert preview["skillId"] == skill_id
    assert preview["requestedTargetIds"] == request["targetIds"]
    assert preview["selectedTargetIds"] == request["targetIds"]
    if targetless:
        assert preview["targets"] == []
        assert preview["selfPreview"]["recipientId"] == request["actorId"]
        assert preview["selfPreview"]["currentHp"] == actor.hp
    else:
        fact = preview["targets"][0]
        assert fact["targetId"] == target_id
        assert fact["primary"]["kind"] in {"damage", "prevented"}
        assert fact["primary"]["amountRange"]["min"] <= fact["primary"]["amountRange"]["max"]
        assert isinstance(fact["directHitChancePercent"], int)
    assert adapter.snapshot(session) == before_snapshot
    assert session.rng_state == before_rng
    assert random.getstate() == global_rng


def test_warrior_targetless_preview_facts_and_empty_shape_are_explicit():
    adapter, session = _session("hero.warrior.weapon_master")
    actor = session.game.player_heroes[0]
    antivenom = adapter.preview(
        session, _request(adapter, session, "skill.warrior.antivenom_potion", [])
    )
    assert antivenom["selfPreview"]["primary"] == {
        "kind": "healing",
        "amountRange": {"min": 18, "max": 20},
        "reasonId": None,
    }
    kinds = {item["kind"] for item in antivenom["selfPreview"]["consequences"]}
    assert {"resistanceBoost", "cooldown"} <= kinds

    with pytest.raises(BattleAdapterError, match="targetless self preview"):
        adapter.preview(
            session,
            _request(
                adapter,
                session,
                "skill.warrior.antivenom_potion",
                [adapter._combatant_id(session, session.game.opponent_heroes[0])],
            ),
        )

    adapter, session = _session("hero.warrior.berserker")
    warlust = adapter.preview(
        session, _request(adapter, session, "skill.warrior.warlust", [])
    )
    assert warlust["targets"] == []
    assert warlust["selfPreview"]["primary"] is None
    kinds = {item["kind"] for item in warlust["selfPreview"]["consequences"]}
    assert {"controlImmunity", "damageIncrease", "cooldown"} <= kinds


@pytest.mark.parametrize(
    ("definition_id", "skill_id", "name", "expected_kind"),
    [
        ("hero.warrior.defence", "skill.warrior.devastate", "Devastate", "armorBreaker"),
        ("hero.warrior.defence", "skill.warrior.shield_bash", "Shield Bash", "stun"),
        ("hero.warrior.defence", "skill.warrior.thunder_pot", "Thunder Pot", "scoff"),
        ("hero.warrior.weapon_master", "skill.warrior.fatal_strike", "Fatal Strike", "healingReduction"),
        ("hero.warrior.weapon_master", "skill.warrior.armor_crush", "Armor Crush", "armorBreaker"),
        ("hero.warrior.berserker", "skill.warrior.strike_of_meteorite", "Strike of Meteorite", "armorBreaker"),
    ],
)
def test_warrior_targeted_material_fact_is_server_authored(
    definition_id, skill_id, name, expected_kind
):
    adapter, session = _session(definition_id)
    target = session.game.opponent_heroes[0]
    preview = adapter.preview(
        session,
        _request(adapter, session, skill_id, [adapter._combatant_id(session, target)]),
    )
    assert expected_kind in {item["kind"] for item in preview["targets"][0]["consequences"]}


@pytest.mark.parametrize(
    ("definition_id", "skill_id"),
    [
        ("hero.warrior.defence", "skill.warrior.thunder_pot"),
        ("hero.warrior.berserker", "skill.warrior.moon_slash"),
    ],
)
def test_warrior_multi_target_preview_accepts_draft_and_full_legal_sets(
    definition_id, skill_id
):
    adapter, session = _session(definition_id, size=2)
    target_ids = [
        adapter._combatant_id(session, hero) for hero in session.game.opponent_heroes
    ]
    draft = adapter.preview(session, _request(adapter, session, skill_id, target_ids[:1]))
    complete = adapter.preview(session, _request(adapter, session, skill_id, target_ids))
    assert [item["targetId"] for item in draft["targets"]] == target_ids[:1]
    assert [item["targetId"] for item in complete["targets"]] == target_ids
    with pytest.raises(BattleAdapterError, match="Duplicate targets"):
        adapter.preview(session, _request(adapter, session, skill_id, [target_ids[0], target_ids[0]]))


def test_moon_slash_only_reports_bleeding_for_an_armor_broken_target():
    adapter, session = _session("hero.warrior.berserker")
    target = session.game.opponent_heroes[0]
    target_id = adapter._combatant_id(session, target)
    absent = adapter.preview(session, _request(adapter, session, "skill.warrior.moon_slash", [target_id]))
    assert "bleed" not in {item["kind"] for item in absent["targets"][0]["consequences"]}
    target.status["armor_breaker"] = True
    target.armor_breaker_stacks = 1
    present = adapter.preview(session, _request(adapter, session, "skill.warrior.moon_slash", [target_id]))
    assert "bleed" in {item["kind"] for item in present["targets"][0]["consequences"]}


def test_known_ambiguous_warrior_legacy_states_return_nonblocking_unavailable():
    adapter, session = _session("hero.warrior.defence")
    target = session.game.opponent_heroes[0]
    target.status["warlust"] = True
    thunder = adapter.preview(
        session,
        _request(adapter, session, "skill.warrior.thunder_pot", [adapter._combatant_id(session, target)]),
    )
    assert thunder["coverage"] == "unavailable"
    assert thunder["reasonId"] == "preview.unauditedState"

    adapter, session = _session("hero.warrior.weapon_master")
    session.game.player_heroes[0].status["unstable_compound"] = True
    antivenom = adapter.preview(
        session, _request(adapter, session, "skill.warrior.antivenom_potion", [])
    )
    assert antivenom["coverage"] == "unavailable"
    assert antivenom["selfPreview"] is None


def test_warrior_preview_does_not_consume_global_rng(monkeypatch):
    adapter, session = _session("hero.warrior.weapon_master")
    target = session.game.opponent_heroes[0]
    target_id = adapter._combatant_id(session, target)

    def fail(*_args, **_kwargs):
        raise AssertionError("preview consumed RNG")

    for name in ("random", "randint", "choice", "sample", "shuffle"):
        monkeypatch.setattr(random, name, fail)
    preview = adapter.preview(
        session, _request(adapter, session, "skill.warrior.armor_crush", [target_id])
    )
    assert preview["coverage"] == "authoritative"
