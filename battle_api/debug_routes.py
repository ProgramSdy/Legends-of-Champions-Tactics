"""Development-only HTTP routes for process-local engineering battles."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter

from .adapter import BattleRegistry
from .models import CreateDebugBattleRequest, HttpErrorResponse


def create_debug_router(registry: BattleRegistry) -> APIRouter:
    """Build the Engineering router around the process-local battle registry."""

    router = APIRouter()

    @router.post(
        "/api/v1/debug/battles",
        responses={422: {"model": HttpErrorResponse}},
    )
    async def create_debug_battle(request: CreateDebugBattleRequest) -> dict:
        """Create a full-roster battle without player-data access."""

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

    return router
