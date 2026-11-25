"""Development-only HTTP routes for process-local engineering battles."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException

from .adapter import (
    BattleRegistry,
    PlayerTeamValidationError,
    validate_distinct_player_professions,
)
from .models import (
    CreateDebugBattleRequest,
    DebugAutoActionRequest,
    HttpErrorResponse,
)


def create_debug_router(registry: BattleRegistry) -> APIRouter:
    """Build the Engineering router around the process-local battle registry."""

    router = APIRouter()

    @router.post(
        "/api/v1/debug/battles",
        responses={422: {"model": HttpErrorResponse}},
    )
    async def create_debug_battle(request: CreateDebugBattleRequest) -> dict:
        """Create a full-roster battle without player-data access."""

        try:
            validate_distinct_player_professions(list(request.player_team))
        except PlayerTeamValidationError as exc:
            raise HTTPException(
                status_code=422,
                detail={"code": exc.code, "message": exc.message},
            ) from exc

        _, envelope = await asyncio.to_thread(
            registry.create,
            seed=request.seed,
            battle_size=request.battle_size,
            player_team=list(request.player_team),
            enemy_composition_mode=request.enemy_composition_mode,
            enemy_team=list(request.enemy_team) if request.enemy_team else None,
            enemy_control_mode=request.enemy_control_mode,
            player_formation=request.player_formation,
            enemy_formation=request.enemy_formation,
        )
        return envelope

    @router.post(
        "/api/v1/debug/battles/{battle_id}/auto-actions",
        responses={404: {"model": HttpErrorResponse}},
    )
    async def submit_debug_auto_action(
        battle_id: str, request: DebugAutoActionRequest
    ) -> dict:
        """Resolve exactly one friendly turn through existing specialization AI."""

        battle = registry.get(battle_id)
        if battle is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "battleNotFound",
                    "message": "Battle was not found.",
                },
            )
        result = await asyncio.to_thread(
            registry.adapter.submit_player_ai_turn,
            battle,
            expected_revision=request.expected_revision,
        )
        envelope = registry.adapter.envelope(battle, result)
        envelope["revision"] = result["revision"]
        return envelope

    return router
