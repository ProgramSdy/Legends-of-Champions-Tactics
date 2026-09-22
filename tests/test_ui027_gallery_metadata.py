from __future__ import annotations

import random

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from battle_api.adapter import (
    BattleAdapter,
    HERO_ROSTER,
    HERO_SKILL_INVENTORY,
    STARTING_RESISTANCE_RANGE_ROWS,
    STARTING_STAT_RANGE_ROWS,
)
from battle_api.app import app
from battle_api.models import HeroStartingStatRange
from battle_api.progression import hero_unlock_sources


client = TestClient(app)


def test_roster_publishes_configured_ranges_and_static_skill_inventory():
    response = client.get("/api/v1/heroes")

    assert response.status_code == 200
    heroes = response.json()["heroes"]
    assert len(heroes) == 10
    assert {hero["definitionId"] for hero in heroes} == set(HERO_ROSTER)

    for hero in heroes:
        assert [item["id"] for item in hero["startingStatRanges"]] == [
            "hp", "damage", "defence", "agility",
        ]
        assert [item["id"] for item in hero["startingResistanceRanges"]] == [
            "fire", "frost", "arcane", "shadow", "death", "poison", "nature",
        ]
        assert all(item["minimum"] <= item["maximum"] for item in (
            hero["startingStatRanges"] + hero["startingResistanceRanges"]
        ))
        assert hero["skills"] == [
            {
                "skillId": skill_id,
                "displayName": display_name,
                "isPassive": is_passive,
            }
            for skill_id, display_name, is_passive
            in HERO_SKILL_INVENTORY[hero["definitionId"]]
        ]

    protection = next(
        hero for hero in heroes
        if hero["definitionId"] == "hero.paladin.protection"
    )
    assert [skill for skill in protection["skills"] if skill["isPassive"]] == [
        {
            "skillId": "skill.paladin.holy_aura",
            "displayName": "Holy Aura",
            "isPassive": True,
        },
    ]
    assert all(
        not skill["isPassive"]
        for hero in heroes
        if hero["definitionId"] != "hero.paladin.protection"
        for skill in hero["skills"]
    )


def test_roster_ranges_match_engine_workbooks_without_constructing_heroes():
    adapter = BattleAdapter()
    heroes = {
        hero["definitionId"]: hero
        for hero in adapter.roster(hero_unlock_sources())
    }

    for definition_id, definition in HERO_ROSTER.items():
        profession = definition["class"].__name__
        for response_range, (_, _, minimum_row, maximum_row) in zip(
            heroes[definition_id]["startingStatRanges"],
            STARTING_STAT_RANGE_ROWS,
            strict=True,
        ):
            assert response_range["minimum"] == int(
                adapter.engine_data.df_hero_basic_property.loc[minimum_row, profession]
            )
            assert response_range["maximum"] == int(
                adapter.engine_data.df_hero_basic_property.loc[maximum_row, profession]
            )
        for response_range, (_, _, minimum_row, maximum_row) in zip(
            heroes[definition_id]["startingResistanceRanges"],
            STARTING_RESISTANCE_RANGE_ROWS,
            strict=True,
        ):
            assert response_range["minimum"] == int(
                adapter.engine_data.df_hero_resistance.loc[minimum_row, profession]
            )
            assert response_range["maximum"] == int(
                adapter.engine_data.df_hero_resistance.loc[maximum_row, profession]
            )


def test_gallery_roster_does_not_consume_randomness(monkeypatch):
    def unexpected_random(*_args, **_kwargs):
        raise AssertionError("Gallery roster metadata must not use RNG")

    monkeypatch.setattr(random, "choice", unexpected_random)
    monkeypatch.setattr(random, "randint", unexpected_random)
    monkeypatch.setattr(random, "shuffle", unexpected_random)

    heroes = BattleAdapter().roster(hero_unlock_sources())

    assert len(heroes) == 10


def test_skill_inventory_ids_match_the_adapter_canonical_ids():
    adapter = BattleAdapter()
    random_state = random.getstate()
    random.seed(2701)
    try:
        for definition_id, definition in HERO_ROSTER.items():
            hero = definition["class"](
                adapter.engine_data,
                "Gallery Audit",
                "Group_A",
                True,
            )
            assert tuple(
                (adapter._skill_id(hero, skill), skill.name, skill.is_passive)
                for skill in hero.skills
            ) == HERO_SKILL_INVENTORY[definition_id]
    finally:
        random.setstate(random_state)


def test_unlock_sources_are_derived_only_from_real_training_rewards():
    heroes = {
        hero["definitionId"]: hero
        for hero in BattleAdapter().roster(hero_unlock_sources())
    }

    assert heroes["hero.paladin.protection"]["unlockSource"] == {
        "kind": "stageReward",
        "stageId": "paladins-altar",
        "stageDisplayName": "Paladin's Altar",
        "battleIndex": 3,
    }
    assert heroes["hero.paladin.retribution"]["unlockSource"]["battleIndex"] == 6
    assert heroes["hero.paladin.holy"]["unlockSource"]["battleIndex"] == 9
    assert heroes["hero.warrior.berserker"]["unlockSource"]["battleIndex"] == 3
    assert heroes["hero.warrior.defence"]["unlockSource"]["battleIndex"] == 9
    assert heroes["hero.priest.discipline"]["unlockSource"] is None
    assert heroes["hero.priest.comprehensiveness"]["unlockSource"] == {
        "kind": "starter",
    }


def test_range_contract_rejects_inverted_bounds_with_stable_field_path():
    with pytest.raises(ValidationError) as error:
        HeroStartingStatRange(
            id="hp", label="HP", minimum=100, maximum=90
        )

    assert error.value.errors()[0]["loc"] == ()
    assert error.value.errors()[0]["msg"] == (
        "Value error, minimum must be less than or equal to maximum"
    )


def test_openapi_marks_gallery_metadata_as_part_of_hero_response():
    hero_schema = client.get("/openapi.json").json()["components"]["schemas"]["HeroDefinition"]

    assert {
        "startingStatRanges",
        "startingResistanceRanges",
        "skills",
        "unlockSource",
    }.issubset(set(hero_schema["required"]))
