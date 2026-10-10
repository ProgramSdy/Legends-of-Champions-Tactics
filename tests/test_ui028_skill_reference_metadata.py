"""Authoritative, RNG-free UI-028 Hero Gallery skill references."""

from __future__ import annotations

from copy import deepcopy
import random

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from battle_api.adapter import (
    BattleAdapter,
    HERO_ROSTER,
    HERO_SKILL_INVENTORY,
    HERO_SKILL_REFERENCE_DEFINITIONS,
)
from battle_api.app import app, registry
from battle_api.models import HeroSkillInventoryItem
from battle_api.progression import hero_unlock_sources


client = TestClient(app)


def _skill(response, definition_id, skill_id):
    hero = next(
        item for item in response["heroes"] if item["definitionId"] == definition_id
    )
    return next(item for item in hero["skills"] if item["skillId"] == skill_id)


def test_reference_registry_and_response_cover_every_approved_skill_exactly():
    assert len(HERO_ROSTER) == 10
    expected_ids = {
        skill_id
        for skills in HERO_SKILL_INVENTORY.values()
        for skill_id, _display_name, _passive in skills
    }
    assert len(expected_ids) == 31
    assert set(HERO_SKILL_REFERENCE_DEFINITIONS) == expected_ids

    response = client.get("/api/v1/heroes")

    assert response.status_code == 200
    body = response.json()
    assert body["contractVersion"] == "1.0"
    published_ids = {
        skill["skillId"] for hero in body["heroes"] for skill in hero["skills"]
    }
    assert published_ids == expected_ids
    assert all(
        "reference" in skill for hero in body["heroes"] for skill in hero["skills"]
    )
    assert sum(len(hero["skills"]) for hero in body["heroes"]) == 31


def test_pilot_reference_ranges_and_conditions_are_exact():
    body = client.get("/api/v1/heroes").json()

    holy_smite = _skill(
        body, "hero.priest.comprehensiveness", "skill.priest.holy_smite"
    )["reference"]
    assert holy_smite["target"] == {"mode": "singleEnemy"}
    assert holy_smite["skillType"] == "damage"
    assert holy_smite["attackType"] == {
        "state": "classified",
        "value": "rangedInstant",
    }
    assert holy_smite["damageNature"] == {
        "state": "classified",
        "value": "magical",
    }
    assert holy_smite["damageType"] == {
        "state": "classified",
        "value": "holy",
    }
    assert holy_smite["baseDamage"]["amountRange"] == {
        "minimum": 16,
        "maximum": 22,
    }
    assert holy_smite["baseHealing"] == {"state": "notApplicable"}

    shadow_pain = _skill(
        body, "hero.priest.comprehensiveness", "skill.priest.shadow_word_pain"
    )["reference"]
    assert shadow_pain["baseDamage"]["state"] == "unavailable"
    assert shadow_pain["baseDamage"]["reasonId"] == "targetDependentBaseline"
    assert "Shadow Resistance" in shadow_pain["baseDamage"]["note"]

    binding_heal = _skill(
        body, "hero.priest.comprehensiveness", "skill.priest.binding_heal"
    )["reference"]
    assert binding_heal["target"] == {"mode": "singleAlly"}
    assert binding_heal["baseDamage"] == {"state": "notApplicable"}
    assert binding_heal["baseHealing"]["amountRange"] == {
        "minimum": 22,
        "maximum": 28,
    }
    assert binding_heal["baseHealing"]["conditions"] == [
        {
            "label": "Caster healing when another ally is selected",
            "amountRange": {"minimum": 17, "maximum": 23},
        }
    ]

    hammer = _skill(
        body, "hero.paladin.protection", "skill.paladin.hammer_of_revenge"
    )["reference"]
    assert hammer["target"] == {"mode": "singleEnemy"}
    assert hammer["baseDamage"]["amountRange"] == {
        "minimum": 51,
        "maximum": 64,
    }
    assert hammer["baseDamage"]["conditions"] == [
        {
            "label": "Bonus with 1 self debuff",
            "amountRange": {"minimum": 3, "maximum": 5},
        },
        {
            "label": "Bonus with 2 self debuffs",
            "amountRange": {"minimum": 6, "maximum": 8},
        },
        {
            "label": "Bonus with 3 or more self debuffs",
            "amountRange": {"minimum": 9, "maximum": 11},
        },
    ]
    assert hammer["damageNature"] == {
        "state": "unclassified",
        "reasonId": "definitionMissing",
    }
    assert hammer["damageType"] == {
        "state": "unclassified",
        "reasonId": "definitionMissing",
    }


def test_non_pilot_numeric_states_are_explicit_and_relevant():
    body = client.get("/api/v1/heroes").json()
    pilot_ids = {
        "skill.priest.holy_smite",
        "skill.priest.shadow_word_pain",
        "skill.priest.binding_heal",
        "skill.paladin.hammer_of_revenge",
    }
    for hero in body["heroes"]:
        for skill in hero["skills"]:
            if skill["skillId"] in pilot_ids:
                continue
            reference = skill["reference"]
            if reference["skillType"] == "damage":
                assert reference["baseDamage"]["state"] == "unavailable"
                assert reference["baseHealing"] == {"state": "notApplicable"}
            elif reference["skillType"] == "healing":
                assert reference["baseDamage"] == {"state": "notApplicable"}
                assert reference["baseHealing"]["state"] == "unavailable"
            elif reference["skillType"] == "damageHealing":
                assert reference["baseDamage"]["state"] == "unavailable"
                assert reference["baseHealing"]["state"] == "unavailable"
            else:
                assert reference["baseDamage"] == {"state": "notApplicable"}
                assert reference["baseHealing"] == {"state": "notApplicable"}


def test_target_semantics_share_live_adapter_policy_and_multi_quantity():
    adapter = BattleAdapter()
    global_state = random.getstate()
    random.seed(2801)
    try:
        for definition_id, definition in HERO_ROSTER.items():
            hero = definition["class"](
                adapter.engine_data,
                "Reference Parity",
                "Group_A",
                True,
            )
            published_hero = next(
                item
                for item in adapter.roster(hero_unlock_sources())
                if item["definitionId"] == definition_id
            )
            published = {item["skillId"]: item for item in published_hero["skills"]}
            for skill in hero.skills:
                skill_id = adapter._skill_id(hero, skill)
                static = HERO_SKILL_REFERENCE_DEFINITIONS[skill_id]
                assert (
                    static.skill_type,
                    static.target_type,
                    static.target_quantity,
                    static.attack_type,
                    static.damage_nature,
                    static.damage_type,
                ) == (
                    skill.skill_type,
                    skill.target_type,
                    skill.target_qty,
                    skill.attack_type,
                    skill.damage_nature,
                    skill.damage_type,
                )
                target = published[skill_id]["reference"]["target"]
                assert target["mode"] == adapter._target_mode(skill)
                if skill.target_qty > 1:
                    assert target["maximumTargets"] == skill.target_qty
                else:
                    assert "maximumTargets" not in target
    finally:
        random.setstate(global_state)


def test_catalogue_is_deterministic_rng_free_and_constructs_no_heroes(monkeypatch):
    adapter = BattleAdapter()
    adapter.engine_data  # Load workbook data before random/constructor guards.
    basic_before = adapter.engine_data.df_hero_basic_property.copy(deep=True)
    resistance_before = adapter.engine_data.df_hero_resistance.copy(deep=True)
    unlocks = hero_unlock_sources()
    unlocks_before = deepcopy(unlocks)
    rng_before = random.getstate()

    def forbidden(*_args, **_kwargs):
        raise AssertionError("catalogue must not construct heroes or consume RNG")

    for definition in HERO_ROSTER.values():
        monkeypatch.setattr(definition["class"], "__init__", forbidden)
    for name in ("choice", "randint", "shuffle", "sample", "random"):
        monkeypatch.setattr(random, name, forbidden)

    first = adapter.roster(unlocks)
    second = adapter.roster(unlocks)

    assert first == second
    assert random.getstate() == rng_before
    assert unlocks == unlocks_before
    assert adapter.engine_data.df_hero_basic_property.equals(basic_before)
    assert adapter.engine_data.df_hero_resistance.equals(resistance_before)


def test_http_catalogue_does_not_create_battle_sessions():
    before = set(registry._sessions)

    first = client.get("/api/v1/heroes")
    second = client.get("/api/v1/heroes")

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert set(registry._sessions) == before


@pytest.mark.parametrize(
    "mutate,expected_path",
    [
        (
            lambda value: value["reference"]["baseDamage"]["amountRange"].update(
                minimum=30, maximum=20
            ),
            ("reference", "baseDamage", "available", "amountRange"),
        ),
        (
            lambda value: value["reference"]["damageNature"].update(
                value="magical"
            ),
            ("reference", "damageNature", "unclassified", "value"),
        ),
        (
            lambda value: value["reference"]["target"].pop("maximumTargets"),
            ("reference", "target", "multipleEnemies", "maximumTargets"),
        ),
    ],
)
def test_reference_contract_rejects_invalid_discriminated_states(
    mutate, expected_path
):
    body = client.get("/api/v1/heroes").json()
    if "maximumTargets" in str(expected_path):
        payload = deepcopy(
            _skill(body, "hero.mage.comprehensiveness", "skill.mage.arcane_missiles")
        )
    elif "damageNature" in str(expected_path):
        payload = deepcopy(
            _skill(body, "hero.paladin.protection", "skill.paladin.hammer_of_revenge")
        )
    else:
        payload = deepcopy(
            _skill(body, "hero.priest.comprehensiveness", "skill.priest.holy_smite")
        )
    mutate(payload)

    with pytest.raises(ValidationError) as error:
        HeroSkillInventoryItem.model_validate(payload)

    assert error.value.errors()[0]["loc"][: len(expected_path)] == expected_path
