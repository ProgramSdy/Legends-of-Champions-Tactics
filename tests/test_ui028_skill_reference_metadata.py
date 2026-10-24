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
    HERO_SKILL_COOLDOWN_ROUNDS,
    HERO_SKILL_REFERENCE_DEFINITIONS,
)
from battle_api.app import app, registry
from battle_api.models import (
    HeroSkillInventoryItem,
    HeroSkillReference,
    HeroSkillUnavailableNumericReference,
)
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
    assert len(expected_ids) == 32
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
    assert sum(len(hero["skills"]) for hero in body["heroes"]) == 32


def test_gallery_cooldowns_match_the_seven_audited_engine_counters():
    expected = {
        "skill.rogue.shadow_evasion": 2,
        "skill.warrior.shield_bash": 3,
        "skill.warrior.thunder_pot": 3,
        "skill.warrior.antivenom_potion": 3,
        "skill.warrior.warlust": 3,
        "skill.paladin.heroric_charge": 3,
        "skill.paladin.shield_of_protection": 3,
    }
    assert HERO_SKILL_COOLDOWN_ROUNDS == expected

    body = client.get("/api/v1/heroes").json()
    actual = {
        skill["skillId"]: skill["reference"]["cooldownRounds"]
        for hero in body["heroes"]
        for skill in hero["skills"]
    }
    assert len(actual) == 32
    assert actual == {skill_id: expected.get(skill_id) for skill_id in actual}


@pytest.mark.parametrize("invalid", [0, -1, 1.5, True])
def test_gallery_cooldown_contract_rejects_nonpositive_or_noninteger_values(invalid):
    body = client.get("/api/v1/heroes").json()
    reference = deepcopy(body["heroes"][0]["skills"][0]["reference"])
    reference["cooldownRounds"] = invalid
    with pytest.raises(ValidationError):
        HeroSkillReference.model_validate(reference)


@pytest.mark.parametrize(
    ("definition_id", "skill_name", "expected_rounds"),
    [
        ("hero.rogue.comprehensiveness", "Shadow Evasion", 2),
        ("hero.warrior.defence", "Shield Bash", 3),
        ("hero.warrior.defence", "Thunder Pot", 3),
        ("hero.warrior.weapon_master", "Antivenom Potion", 3),
        ("hero.warrior.berserker", "Warlust", 3),
        ("hero.paladin.protection", "Heroric Charge", 3),
        ("hero.paladin.holy", "Shield of Protection", 3),
    ],
)
def test_gallery_cooldown_value_is_set_by_live_skill_execution(
    definition_id, skill_name, expected_rounds
):
    adapter = BattleAdapter()
    enemy_id = (
        "hero.warrior.weapon_master"
        if definition_id == "hero.rogue.comprehensiveness"
        else "hero.rogue.comprehensiveness"
    )
    session, _ = adapter.create_battle(
        seed=28031,
        player_team=[definition_id],
        enemy_team=[enemy_id],
        enemy_control_mode="player",
    )
    actor = session.game.player_heroes[0]
    target = session.game.opponent_heroes[0]
    skill = next(item for item in actor.skills if item.name == skill_name)
    skill.evasion_check = lambda _target: False

    if skill.target_qty == 0:
        skill.execute(["none"])
    elif skill.target_type == "multi":
        skill.execute([target])
    else:
        skill.execute(target)

    assert skill.if_cooldown is True
    assert skill.cooldown == expected_rounds


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
    assert holy_smite["baseDamage"]["note"] == ""
    assert holy_smite["baseHealing"] == {"state": "notApplicable"}

    shadow_pain = _skill(
        body, "hero.priest.comprehensiveness", "skill.priest.shadow_word_pain"
    )["reference"]
    assert shadow_pain["baseDamage"]["state"] == "unavailable"
    assert shadow_pain["baseDamage"]["reasonId"] == "targetDependentBaseline"
    assert "Shadow Resistance" in shadow_pain["baseDamage"]["note"]
    assert shadow_pain["baseDamage"]["displayLabel"] == "Target-dependent"
    assert shadow_pain["baseDamage"]["calculation"] == {
        "title": "Damage Calculation",
        "formula": (
            "Direct damage = round((Caster Damage + Skill Variation "
            "− Target Shadow Resistance) ÷ 2)\n"
            "Continuous damage = max(1, round((Caster Original Damage "
            "− Target Shadow Resistance) ÷ 3) + Skill Variation)"
        ),
    }

    binding_heal = _skill(
        body, "hero.priest.comprehensiveness", "skill.priest.binding_heal"
    )["reference"]
    assert binding_heal["target"] == {"mode": "singleAlly"}
    assert binding_heal["baseDamage"] == {"state": "notApplicable"}
    assert binding_heal["baseHealing"]["amountRange"] == {
        "minimum": 22,
        "maximum": 28,
    }
    assert binding_heal["baseHealing"]["note"] == ""
    assert binding_heal["baseHealing"]["conditions"] == [
        {
            "label": "Healing received by caster",
            "amountRange": {"minimum": 17, "maximum": 23},
        }
    ]

    sharp_blade = _skill(
        body, "hero.rogue.comprehensiveness", "skill.rogue.sharp_blade"
    )["reference"]
    assert sharp_blade["baseDamage"] == {
        "state": "unavailable",
        "reasonId": "targetDependentBaseline",
        "note": "Direct damage depends on the selected target's Defence.",
        "displayLabel": "Target-dependent",
        "calculation": {
            "title": "Damage Calculation",
            "formula": (
                "Direct damage = max(Caster Damage + Skill Variation "
                "− Target Defence, 0)\n"
                "Bleeding damage per activation = 5–8 when Direct Damage "
                "is 20 or less; otherwise 9–14"
            ),
        },
    }

    poisoned_dagger = _skill(
        body, "hero.rogue.comprehensiveness", "skill.rogue.poisoned_dagger"
    )["reference"]
    assert poisoned_dagger["baseDamage"] == {
        "state": "unavailable",
        "reasonId": "targetDependentBaseline",
        "note": "Direct damage depends on the selected target's Defence.",
        "displayLabel": "Target-dependent",
        "calculation": {
            "title": "Damage Calculation",
            "formula": (
                "Direct damage = max(round((Caster Damage + Skill Variation "
                "− Target Defence) ÷ 2), 0)\n"
                "Poison damage per stack = ceil((Caster Damage + Skill "
                "Variation − Target Poison Resistance) ÷ 4)"
            ),
        },
    }

    fatal_strike = _skill(
        body, "hero.warrior.weapon_master", "skill.warrior.fatal_strike"
    )["reference"]
    assert fatal_strike["target"] == {"mode": "singleEnemy"}
    assert fatal_strike["baseDamage"] == {
        "state": "unavailable",
        "reasonId": "targetDependentBaseline",
        "note": "Direct damage depends on the selected target's Defence.",
        "displayLabel": "Target-dependent",
        "calculation": {
            "title": "Damage Calculation",
            "formula": (
                "Direct damage = max(Caster Damage + Skill Variation "
                "− Target Defence, 1)"
            ),
        },
    }
    assert fatal_strike["baseHealing"] == {"state": "notApplicable"}

    armor_crush = _skill(
        body, "hero.warrior.weapon_master", "skill.warrior.armor_crush"
    )["reference"]
    assert armor_crush["target"] == {"mode": "singleEnemy"}
    assert armor_crush["baseDamage"] == {
        "state": "unavailable",
        "reasonId": "targetDependentBaseline",
        "note": "Direct damage depends on the selected target's Defence and Armor Breaker state.",
        "displayLabel": "Target-dependent",
        "calculation": {
            "title": "Damage Calculation",
            "formula": (
                "Direct damage = max(ceil((Caster Damage + Skill Variation "
                "− Target Defence) × Armor Breaker multiplier), 1)\n"
                "Armor Breaker multiplier: no Armor Breaker or 0 stacks = 55%; "
                "1 stack = 65%; "
                "2 or more stacks = 75%"
            ),
        },
    }
    assert armor_crush["baseHealing"] == {"state": "notApplicable"}

    antivenom = _skill(
        body, "hero.warrior.weapon_master", "skill.warrior.antivenom_potion"
    )["reference"]
    assert antivenom["target"] == {"mode": "self"}
    assert antivenom["skillType"] == "buff"
    assert antivenom["baseDamage"] == {"state": "notApplicable"}
    assert antivenom["baseHealing"] == {
        "state": "available",
        "amountRange": {"minimum": 18, "maximum": 20},
        "basis": "baselinePower",
        "note": "",
        "conditions": [],
    }

def test_non_pilot_numeric_states_are_explicit_and_relevant():
    body = client.get("/api/v1/heroes").json()
    pilot_ids = {
        "skill.priest.holy_smite",
        "skill.priest.shadow_word_pain",
        "skill.priest.binding_heal",
        "skill.rogue.sharp_blade",
        "skill.rogue.poisoned_dagger",
        "skill.paladin.hammer_of_revenge",
        "skill.warrior.fatal_strike",
        "skill.warrior.armor_crush",
        "skill.warrior.antivenom_potion",
        "skill.warrior.devastate",
        "skill.warrior.shield_bash",
        "skill.warrior.thunder_pot",
        "skill.warrior.moon_slash",
        "skill.warrior.strike_of_meteorite",
        "skill.paladin.hammer_of_anger",
        "skill.paladin.crusader_strike",
        "skill.paladin.shield_of_righteous",
        "skill.paladin.heroric_charge",
        "skill.paladin.holy_blast",
        "skill.priest.penance",
        "skill.priest.holy_word_punishment",
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


def test_target_dependent_inventory_is_limited_to_formula_audited_skills():
    body = client.get("/api/v1/heroes").json()

    target_dependent_ids = {
        skill["skillId"]
        for hero in body["heroes"]
        for skill in hero["skills"]
        if skill["reference"]["baseDamage"].get("reasonId")
        == "targetDependentBaseline"
    }

    assert target_dependent_ids == {
        "skill.priest.shadow_word_pain",
        "skill.rogue.sharp_blade",
        "skill.rogue.poisoned_dagger",
        "skill.warrior.fatal_strike",
        "skill.warrior.armor_crush",
        "skill.warrior.devastate",
        "skill.warrior.shield_bash",
        "skill.warrior.thunder_pot",
        "skill.warrior.moon_slash",
        "skill.warrior.strike_of_meteorite",
        "skill.paladin.hammer_of_anger",
        "skill.paladin.hammer_of_revenge",
        "skill.paladin.heroric_charge",
    }


@pytest.mark.parametrize(
    ("definition_id", "skill_id", "formula"),
    [
        (
            "hero.warrior.defence",
            "skill.warrior.devastate",
            "Direct damage = max(ceil((Caster Damage + Skill Variation − Target Defence) × 75%), 1)",
        ),
        (
            "hero.warrior.defence",
            "skill.warrior.shield_bash",
            "Direct damage = max(int((Caster Damage + Skill Variation − Target Defence) ÷ 4), 1)",
        ),
        (
            "hero.warrior.defence",
            "skill.warrior.thunder_pot",
            "Direct damage per target = max(1, round((Caster Damage − Target Defence) ÷ 3) + Skill Variation)",
        ),
        (
            "hero.warrior.berserker",
            "skill.warrior.moon_slash",
            "Direct damage per target = max(ceil((Caster Damage + Skill Variation − Target Defence) × 2 ÷ 3), 1)",
        ),
        (
            "hero.warrior.berserker",
            "skill.warrior.strike_of_meteorite",
            "Direct damage = max(Caster Damage + Skill Variation − Target Defence, 0)",
        ),
    ],
)
def test_warrior_defence_and_berserker_damage_references(
    definition_id, skill_id, formula
):
    body = client.get("/api/v1/heroes").json()
    reference = _skill(body, definition_id, skill_id)["reference"]

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


@pytest.mark.parametrize(
    ("definition_id", "skill_id", "formula"),
    [
        (
            "hero.paladin.retribution",
            "skill.paladin.hammer_of_anger",
            "Direct damage = max(Caster Damage + Skill Variation − Target Defence, 0) + Wrath of Crusader bonus\n"
            "Wrath of Crusader bonus: active 1 stack = 3–5; active 2 stacks = 6–8; otherwise = 0",
        ),
        (
            "hero.paladin.protection",
            "skill.paladin.hammer_of_revenge",
            "Direct damage = max(Caster Damage + Skill Variation − Target Defence, 0) + self-debuff bonus\n"
            "Self-debuff bonus (distinct eligible active statuses): 0 = 0; 1 = 3–5; 2 = 6–8; 3 or more = 9–11",
        ),
        (
            "hero.paladin.protection",
            "skill.paladin.heroric_charge",
            "Direct damage = max(1, round((Caster Damage − Target Defence) × 1) + Skill Variation)",
        ),
    ],
)
def test_paladin_target_dependent_damage_uses_audited_popup(
    definition_id, skill_id, formula
):
    body = client.get("/api/v1/heroes").json()
    reference = _skill(body, definition_id, skill_id)["reference"]

    assert reference["baseDamage"] == {
        "state": "unavailable",
        "reasonId": "targetDependentBaseline",
        "note": "",
        "displayLabel": "Target-dependent",
        "calculation": {"title": "Damage Calculation", "formula": formula},
    }
    assert reference["baseHealing"] == {"state": "notApplicable"}


@pytest.mark.parametrize(
    ("definition_id", "skill_id", "minimum", "maximum", "conditions"),
    [
        ("hero.paladin.retribution", "skill.paladin.crusader_strike", 18, 22, []),
        ("hero.paladin.protection", "skill.paladin.shield_of_righteous", 18, 22, []),
        (
            "hero.paladin.holy",
            "skill.paladin.holy_blast",
            20,
            25,
            [{"label": "Second target", "amountRange": {"minimum": 14, "maximum": 17}}],
        ),
        ("hero.priest.discipline", "skill.priest.penance", 17, 21, []),
        ("hero.priest.discipline", "skill.priest.holy_word_punishment", 7, 11, []),
    ],
)
def test_paladin_and_discipline_fixed_direct_power_ranges(
    definition_id, skill_id, minimum, maximum, conditions
):
    body = client.get("/api/v1/heroes").json()
    reference = _skill(body, definition_id, skill_id)["reference"]

    assert reference["baseDamage"] == {
        "state": "available",
        "amountRange": {"minimum": minimum, "maximum": maximum},
        "basis": "baselinePower",
        "note": "",
        "conditions": conditions,
    }
    if skill_id == "skill.priest.penance":
        assert reference["baseHealing"] == {
            "state": "available",
            "amountRange": {"minimum": 21, "maximum": 25},
            "basis": "baselinePower",
            "note": "",
            "conditions": [],
        }
    else:
        assert reference["baseHealing"] == {"state": "notApplicable"}


def test_holy_word_punishment_continuous_damage_reference_matches_live_branches():
    body = client.get("/api/v1/heroes").json()
    reference = _skill(
        body,
        "hero.priest.discipline",
        "skill.priest.holy_word_punishment",
    )["reference"]

    assert reference["continuousDamage"] == {
        "state": "available",
        "amountRange": {"minimum": 9, "maximum": 16},
        "basis": "baselinePower",
        "note": "",
        "conditions": [],
    }

    unrelated = _skill(
        body,
        "hero.priest.discipline",
        "skill.priest.penance",
    )["reference"]
    assert unrelated["continuousDamage"] == {"state": "notApplicable"}


@pytest.mark.parametrize(
    ("direct_variation", "tick_variation", "stored_effect", "tick_power"),
    [(-2, -1, 10, 9), (2, 1, 15, 16)],
)
def test_holy_word_punishment_new_debuff_rounding_and_tick_bounds(
    monkeypatch, direct_variation, tick_variation, stored_effect, tick_power
):
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=32001,
        player_team=["hero.priest.discipline"],
        enemy_team=["hero.warrior.weapon_master"],
        enemy_control_mode="player",
    )
    source = session.game.player_heroes[0]
    target = session.game.opponent_heroes[0]

    monkeypatch.setattr(random, "randint", lambda _minimum, _maximum: direct_variation)
    source.holy_word_punishment(target)
    debuff = next(item for item in target.debuffs if item.name == "Holy Word Punishment")
    assert debuff.effect == stored_effect
    assert debuff.duration == 4

    received = []
    target.take_damage = lambda amount, *_args, **_kwargs: received.append(amount) or "captured"
    monkeypatch.setattr(random, "randint", lambda _minimum, _maximum: tick_variation)
    session.game.status_manager.check_heroes_status_effects(target)

    assert received == [tick_power]
    assert debuff.duration == 3


@pytest.mark.parametrize(
    ("direct_variation", "tick_variation", "stored_effect", "tick_power"),
    [(-2, -1, 10, 9), (2, 1, 15, 16)],
)
def test_holy_word_punishment_recycled_debuff_matches_new_tick_bounds(
    monkeypatch, direct_variation, tick_variation, stored_effect, tick_power
):
    from skills.skill import Debuff

    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=32002,
        player_team=["hero.priest.discipline"],
        enemy_team=["hero.warrior.weapon_master"],
        enemy_control_mode="player",
    )
    source = session.game.player_heroes[0]
    target = session.game.opponent_heroes[0]
    recycled = Debuff("Holy Word Punishment", 0, source, 999)
    target.buffs_debuffs_recycle_pool.append(recycled)

    monkeypatch.setattr(random, "randint", lambda _minimum, _maximum: direct_variation)
    source.holy_word_punishment(target)
    assert recycled in target.debuffs
    assert recycled not in target.buffs_debuffs_recycle_pool
    assert recycled.effect == stored_effect
    assert recycled.duration == 4

    received = []
    target.take_damage = lambda amount, *_args, **_kwargs: received.append(amount) or "captured"
    monkeypatch.setattr(random, "randint", lambda _minimum, _maximum: tick_variation)
    session.game.status_manager.check_heroes_status_effects(target)

    assert received == [tick_power]
    assert recycled.duration == 3


def test_holy_word_punishment_already_active_does_not_refresh_debuff(monkeypatch):
    adapter = BattleAdapter()
    session, _ = adapter.create_battle(
        seed=32003,
        player_team=["hero.priest.discipline"],
        enemy_team=["hero.warrior.weapon_master"],
        enemy_control_mode="player",
    )
    source = session.game.player_heroes[0]
    target = session.game.opponent_heroes[0]

    monkeypatch.setattr(random, "randint", lambda _minimum, _maximum: 2)
    source.holy_word_punishment(target)
    debuff = next(item for item in target.debuffs if item.name == "Holy Word Punishment")
    assert (debuff.effect, debuff.duration) == (15, 4)

    monkeypatch.setattr(random, "randint", lambda _minimum, _maximum: -2)
    source.holy_word_punishment(target)

    punishment_debuffs = [
        item for item in target.debuffs if item.name == "Holy Word Punishment"
    ]
    assert punishment_debuffs == [debuff]
    assert (debuff.effect, debuff.duration) == (15, 4)


def test_berserker_blood_frenzy_is_a_passive_self_effect_not_an_action():
    body = client.get("/api/v1/heroes").json()
    passive = _skill(
        body, "hero.warrior.berserker", "skill.warrior.blood_frenzy"
    )

    assert passive["displayName"] == "Blood Frenzy"
    assert passive["isPassive"] is True
    assert passive["reference"] == {
        "target": {"mode": "self"},
        "skillType": "effect",
        "cooldownRounds": None,
        "attackType": {"state": "notApplicable"},
        "damageNature": {"state": "notApplicable"},
        "damageType": {"state": "notApplicable"},
        "baseDamage": {"state": "notApplicable"},
        "continuousDamage": {"state": "notApplicable"},
        "baseHealing": {"state": "notApplicable"},
    }


@pytest.mark.parametrize(
    ("reason_id", "calculation"),
    [
        ("notAudited", {"title": "Damage Calculation", "formula": "Formula"}),
        ("targetDependentBaseline", None),
    ],
)
def test_blank_unavailable_note_requires_target_dependent_formula(
    reason_id, calculation
):
    with pytest.raises(ValidationError):
        HeroSkillUnavailableNumericReference.model_validate(
            {
                "state": "unavailable",
                "reasonId": reason_id,
                "note": "",
                "displayLabel": "Target-dependent",
                "calculation": calculation,
            }
        )


def test_warrior_damage_skills_publish_authoritative_physical_weapon_facts():
    body = client.get("/api/v1/heroes").json()
    warrior_damage_skills = {
        "hero.warrior.defence": {
            "skill.warrior.devastate",
            "skill.warrior.shield_bash",
            "skill.warrior.thunder_pot",
        },
        "hero.warrior.weapon_master": {
            "skill.warrior.fatal_strike",
            "skill.warrior.armor_crush",
        },
        "hero.warrior.berserker": {
            "skill.warrior.moon_slash",
            "skill.warrior.strike_of_meteorite",
        },
    }
    expected = {
        "damageNature": {"state": "classified", "value": "physical"},
        "damageType": {"state": "classified", "value": "weapon"},
    }
    for definition_id, skill_ids in warrior_damage_skills.items():
        for skill_id in skill_ids:
            reference = _skill(body, definition_id, skill_id)["reference"]
            assert {key: reference[key] for key in expected} == expected


def test_paladin_and_discipline_damage_skills_publish_updated_classifications():
    body = client.get("/api/v1/heroes").json()
    expected_classifications = {
        ("hero.paladin.retribution", "skill.paladin.hammer_of_anger"): ("physical", "weapon"),
        ("hero.paladin.retribution", "skill.paladin.crusader_strike"): ("physical", "holy"),
        ("hero.paladin.protection", "skill.paladin.hammer_of_revenge"): ("physical", "weapon"),
        ("hero.paladin.protection", "skill.paladin.shield_of_righteous"): ("physical", "holy"),
        ("hero.paladin.protection", "skill.paladin.heroric_charge"): ("physical", "weapon"),
        ("hero.paladin.holy", "skill.paladin.holy_blast"): ("magical", "holy"),
        ("hero.priest.discipline", "skill.priest.penance"): ("magical", "holy"),
        ("hero.priest.discipline", "skill.priest.holy_word_punishment"): ("magical", "holy"),
        ("hero.rogue.comprehensiveness", "skill.rogue.sharp_blade"): ("physical", "weapon"),
        ("hero.rogue.comprehensiveness", "skill.rogue.poisoned_dagger"): ("physical", "weapon"),
    }
    for (definition_id, skill_id), (nature, damage_type) in expected_classifications.items():
        reference = _skill(body, definition_id, skill_id)["reference"]
        assert reference["damageNature"] == {"state": "classified", "value": nature}
        assert reference["damageType"] == {"state": "classified", "value": damage_type}


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
            lambda value: value["reference"]["continuousDamage"].update(
                state="available",
                amountRange={"minimum": 17, "maximum": 16},
                basis="baselinePower",
                note="",
                conditions=[],
            ),
            ("reference", "continuousDamage", "available", "amountRange"),
        ),
        (
            lambda value: value["reference"]["damageNature"].update(
                value="not-a-classification"
            ),
            ("reference", "damageNature", "classified", "value"),
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
