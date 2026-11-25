"""Focused regression coverage for Stage 5.1 team validation.

These tests deliberately exercise the transport model and the authoritative
adapter boundary separately: UI validation is useful feedback, but crafted
launch requests must be rejected even when no browser is involved.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from battle_api.adapter import BattleAdapter, BattleRegistry
from battle_api.app import _validate_player_team
from battle_api.debug_routes import create_debug_router


PLAYER = "hero.warrior.weapon_master"
OTHER_WARRIOR = "hero.warrior.defence"
MAGE = "hero.mage.comprehensiveness"
ENEMY = ["hero.rogue.comprehensiveness"]


def _adapter_creation_kwargs(**overrides):
    values = {
        "battle_size": 2,
        "player_team": [PLAYER, MAGE],
        "enemy_composition_mode": "specified",
        "enemy_team": ENEMY + ["hero.priest.comprehensiveness"],
        "enemy_control_mode": "player",
        "player_formation": "front-rear",
        "enemy_formation": "front-rear",
    }
    values.update(overrides)
    return values


def test_api_boundary_rejects_duplicate_player_profession_definition_ids():
    with pytest.raises(HTTPException) as error:
        _validate_player_team([PLAYER, PLAYER])
    assert error.value.status_code == 422
    assert error.value.detail == {
        "code": "duplicatePlayerProfession",
        "message": "playerTeam must not contain the same Hero Profession more than once.",
    }


def test_authoritative_adapter_rejects_duplicate_player_profession_ids():
    with pytest.raises(ValueError, match="duplicate|distinct|Profession"):
        BattleAdapter._validate_creation(
            **_adapter_creation_kwargs(player_team=[PLAYER, PLAYER])
        )


def test_same_faculty_different_specializations_remain_legal():
    BattleAdapter._validate_creation(
        **_adapter_creation_kwargs(player_team=[PLAYER, OTHER_WARRIOR])
    )


def test_duplicate_profession_is_allowed_across_opposing_sides():
    BattleAdapter._validate_creation(
        **_adapter_creation_kwargs(
            player_team=[PLAYER, MAGE],
            enemy_team=[PLAYER, "hero.priest.comprehensiveness"],
        )
    )


def test_debug_api_returns_stable_duplicate_profession_error():
    debug_app = FastAPI()
    debug_app.include_router(create_debug_router(BattleRegistry()))
    response = TestClient(debug_app).post(
        "/api/v1/debug/battles",
        json={
            "battleSize": 2,
            "playerTeam": [PLAYER, PLAYER],
            "enemyCompositionMode": "specified",
            "enemyTeam": [PLAYER, PLAYER],
            "enemyControlMode": "player",
            "playerFormation": "front-rear",
            "enemyFormation": "front-rear",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == {
        "code": "duplicatePlayerProfession",
        "message": "playerTeam must not contain the same Hero Profession more than once.",
    }


def test_debug_auto_action_uses_existing_specialization_ai_and_revision_guard():
    """Development route resolves one friendly AI action, then rejects stale input."""

    debug_app = FastAPI()
    debug_registry = BattleRegistry()
    debug_app.include_router(create_debug_router(debug_registry))
    # Recreate the session in the isolated Engineering router's registry.
    debug_session, debug_envelope = debug_registry.create(
        seed=5104,
        battle_size=1,
        player_team=[PLAYER],
        enemy_composition_mode="specified",
        enemy_team=ENEMY,
        enemy_control_mode="computer",
    )
    debug_player = debug_session.game.player_heroes[0]
    debug_enemy = debug_session.game.opponent_heroes[0]
    debug_player.actioned = False
    debug_enemy.actioned = True
    debug_session.game.unactioned_sorted_heroes = [debug_player]
    debug_session.game.game_state = "hero_action"
    client = TestClient(debug_app)

    response = client.post(
        f"/api/v1/debug/battles/{debug_session.battle_id}/auto-actions",
        json={"expectedRevision": debug_envelope["revision"]},
    )
    assert response.status_code == 200
    result = response.json()["data"]
    assert result["accepted"] is True
    assert result["events"]

    revision_after_action = debug_session.revision
    retry = client.post(
        f"/api/v1/debug/battles/{debug_session.battle_id}/auto-actions",
        json={"expectedRevision": debug_envelope["revision"]},
    )
    assert retry.status_code == 200
    assert retry.json() == response.json()
    assert debug_session.revision == revision_after_action

    stale = client.post(
        f"/api/v1/debug/battles/{debug_session.battle_id}/auto-actions",
        json={"expectedRevision": 0},
    )
    assert stale.status_code == 200
    assert stale.json()["data"]["accepted"] is False
    assert stale.json()["data"]["code"] == "staleRevision"
