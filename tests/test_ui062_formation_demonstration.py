"""Focused parity and isolation checks for UI-062's static formation catalogue."""

from copy import deepcopy

from fastapi.testclient import TestClient

from battle_api.app import app
from game.formation_rules import (
    direct_damage_formation_multiplier,
    direct_damage_target_is_eligible,
    formation_demonstration_catalogue,
)


client = TestClient(app)


def test_catalogue_is_complete_and_repeatable_without_live_state():
    first = client.get("/api/v1/manual/formation-demonstration")
    second = client.get("/api/v1/manual/formation-demonstration")

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    body = first.json()
    assert body["contractVersion"] == "1.0"
    assert body["attackTypes"] == ["melee", "rangedProjectile", "rangedInstant"]
    assert [item["id"] for item in body["formations"]] == [
        "front-rear", "side-by-side", "one-front-two-rear",
        "two-front-one-rear", "all-front",
    ]
    assert [item["battleSize"] for item in body["formations"]] == [2, 2, 3, 3, 3]


def test_every_evaluation_covers_attacker_types_and_defeat_states():
    body = client.get("/api/v1/manual/formation-demonstration").json()
    for formation in body["formations"]:
        expected_states = 2 if formation["hasRearEnemies"] else 1
        assert len(formation["evaluations"]) == len(formation["friendlySlots"]) * 3 * expected_states
        for evaluation in formation["evaluations"]:
            assert len(evaluation["targets"]) == len(formation["enemySlots"])
            for target in evaluation["targets"]:
                assert target["eligible"] == (target["reason"] == "eligible")
                if target["eligible"]:
                    assert target["multiplierPercent"] in {60, 70, 80, 100}
                else:
                    assert target["multiplierPercent"] is None
                if evaluation["enemyFrontDefeated"] and target["targetPosition"] == "front":
                    assert target["reason"] == "defeated"


def test_every_target_row_matches_shared_rule_helpers_and_declared_slots():
    body = client.get("/api/v1/manual/formation-demonstration").json()
    api_type = {"melee": "melee", "rangedProjectile": "ranged_projectile", "rangedInstant": "ranged_instant"}
    for formation in body["formations"]:
        friendly = {slot["slot"]: slot["position"] for slot in formation["friendlySlots"]}
        expected_states = (False, True) if formation["hasRearEnemies"] else (False,)
        seen = set()
        for evaluation in formation["evaluations"]:
            key = (evaluation["attackerSlot"], evaluation["attackType"], evaluation["enemyFrontDefeated"])
            assert key not in seen
            seen.add(key)
            assert evaluation["attackerPosition"] == friendly[evaluation["attackerSlot"]]
            assert evaluation["enemyFrontDefeated"] in expected_states
            defeated = {
                slot["slot"] for slot in formation["enemySlots"]
                if evaluation["enemyFrontDefeated"] and slot["position"] == "front"
            }
            living_positions = [
                slot["position"] for slot in formation["enemySlots"]
                if slot["slot"] not in defeated
            ]
            assert {target["targetSlot"] for target in evaluation["targets"]} == {
                slot["slot"] for slot in formation["enemySlots"]
            }
            for target in evaluation["targets"]:
                if target["targetSlot"] in defeated:
                    assert target["reason"] == "defeated"
                    assert target["eligible"] is False
                    assert target["multiplierPercent"] is None
                    continue
                eligible = direct_damage_target_is_eligible(
                    api_type[evaluation["attackType"]], target["targetPosition"], living_positions
                )
                assert target["eligible"] is eligible
                assert target["reason"] == ("eligible" if eligible else "protectedByFrontLine")
                expected_percent = round(100 * direct_damage_formation_multiplier(
                    evaluation["attackerPosition"], target["targetPosition"], api_type[evaluation["attackType"]]
                )) if eligible else None
                assert target["multiplierPercent"] == expected_percent


def test_known_screening_and_multipliers_match_live_rules():
    body = client.get("/api/v1/manual/formation-demonstration").json()
    front_rear = next(item for item in body["formations"] if item["id"] == "front-rear")

    def evaluation(attacker_slot, attack_type, defeated=False):
        return next(item for item in front_rear["evaluations"] if (
            item["attackerSlot"] == attacker_slot
            and item["attackType"] == attack_type
            and item["enemyFrontDefeated"] == defeated
        ))

    rear_melee = evaluation(2, "melee")
    assert [target["reason"] for target in rear_melee["targets"]] == ["eligible", "protectedByFrontLine"]
    assert rear_melee["targets"][0]["multiplierPercent"] == 70
    rear_melee_after_defeat = evaluation(2, "melee", True)
    assert rear_melee_after_defeat["targets"][0]["reason"] == "defeated"
    assert rear_melee_after_defeat["targets"][1]["multiplierPercent"] == 70

    projectile = evaluation(2, "rangedProjectile")
    assert [target["multiplierPercent"] for target in projectile["targets"]] == [80, 60]
    instant = evaluation(2, "rangedInstant")
    assert [target["multiplierPercent"] for target in instant["targets"]] == [100, 100]


def test_catalogue_builder_is_pure_and_does_not_construct_sessions_or_use_rng(monkeypatch):
    import random

    monkeypatch.setattr(random, "random", lambda: (_ for _ in ()).throw(AssertionError("RNG used")))
    before = deepcopy(formation_demonstration_catalogue())
    after = formation_demonstration_catalogue()
    assert after == before


def test_endpoint_does_not_touch_live_registry_or_random(monkeypatch):
    import random
    import battle_api.app as app_module

    registry = app_module.registry
    monkeypatch.setattr(random, "choice", lambda *_args: (_ for _ in ()).throw(AssertionError("RNG used")))
    monkeypatch.setattr(random, "randint", lambda *_args: (_ for _ in ()).throw(AssertionError("RNG used")))
    assert client.get("/api/v1/manual/formation-demonstration").status_code == 200
    assert app_module.registry is registry
    assert not getattr(registry, "sessions", {})
