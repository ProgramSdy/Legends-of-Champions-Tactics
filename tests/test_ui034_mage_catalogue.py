"""UI-034 authoritative Mage Gallery damage references."""

from __future__ import annotations

import random

from fastapi.testclient import TestClient

from battle_api.app import app


client = TestClient(app)


def _mage_skill(body, skill_id):
    mage = next(
        hero
        for hero in body["heroes"]
        if hero["definitionId"] == "hero.mage.comprehensiveness"
    )
    return next(skill for skill in mage["skills"] if skill["skillId"] == skill_id)


EXPECTED_FORMULAS = {
    "skill.mage.fireball": (
        "Direct damage = max(Caster Damage + Skill Variation "
        "− Target Fire Resistance, 0)"
    ),
    "skill.mage.arcane_missiles": (
        "Direct damage per target = max(ceil((Caster Damage + Skill Variation "
        "− Target Arcane Resistance) × 2 ÷ 3), 0)"
    ),
    "skill.mage.frost_bolt": (
        "Direct damage = max(ceil((Caster Damage + Skill Variation "
        "− Target Frost Resistance) × 4 ÷ 5), 0)"
    ),
}


def test_mage_damage_skills_publish_target_dependent_calculations():
    body = client.get("/api/v1/heroes").json()

    for skill_id, formula in EXPECTED_FORMULAS.items():
        reference = _mage_skill(body, skill_id)["reference"]
        assert reference["baseDamage"] == {
            "state": "unavailable",
            "reasonId": "targetDependentBaseline",
            "note": "",
            "displayLabel": "Target-dependent",
            "calculation": {
                "title": "Damage Calculation",
                "formula": formula,
            },
        }
        assert reference["baseHealing"] == {"state": "notApplicable"}


def test_mage_catalogue_reads_are_repeatable_and_do_not_consume_rng():
    rng_before = random.getstate()

    first = client.get("/api/v1/heroes")
    second = client.get("/api/v1/heroes")

    assert first.status_code == second.status_code == 200
    assert [
        _mage_skill(first.json(), skill_id)["reference"]["baseDamage"]
        for skill_id in EXPECTED_FORMULAS
    ] == [
        _mage_skill(second.json(), skill_id)["reference"]["baseDamage"]
        for skill_id in EXPECTED_FORMULAS
    ]
    assert random.getstate() == rng_before
