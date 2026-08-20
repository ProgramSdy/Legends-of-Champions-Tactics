"""Small async FastAPI transport for the process-local battle registry."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Path as ApiPath
from fastapi.middleware.cors import CORSMiddleware

from .adapter import CONTRACT_VERSION, BattleRegistry
from .models import (
    CreateBattleRequest,
    CreateStageBattleRequest,
    HeroRosterResponse,
    HttpErrorResponse,
    PlayerProgressionResponse,
    RetryableHttpErrorResponse,
    StageId,
    StructuredStagesResponse,
    UseSkillCommand,
    VictoryCommitResponse,
)
from .progression import (
    ProgressionStore,
    ProgressionStoreError,
    StageAccessError,
    stages_response,
)

app = FastAPI(title="Legends of Champions Tactics Battle API", version="1.0.0")

DEFAULT_CORS_ORIGINS = (
    "http://localhost:3001",
    "http://127.0.0.1:3001",
)


def _cors_origins() -> list[str]:
    configured = os.getenv("BATTLE_API_CORS_ORIGINS")
    if configured is None:
        return list(DEFAULT_CORS_ORIGINS)
    return [
        origin.strip()
        for origin in configured.split(",")
        if origin.strip() and origin.strip() != "*"
    ]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)
registry = BattleRegistry()
DEFAULT_PROGRESSION_DATABASE = (
    Path(__file__).resolve().parents[1] / "data" / "player_progression.sqlite3"
)
progression_store = ProgressionStore(
    Path(os.getenv("BATTLE_API_PROGRESSION_DB", DEFAULT_PROGRESSION_DATABASE))
)


def get_progression_store() -> ProgressionStore:
    return progression_store


def _store_unavailable(exc: ProgressionStoreError) -> HTTPException:
    return HTTPException(
        status_code=503,
        detail={
            "code": "progressionStoreUnavailable",
            "message": str(exc),
            "retryable": True,
        },
    )


def _access_error(exc: StageAccessError) -> HTTPException:
    status = 404 if exc.code in {"stageNotFound", "stageBattleNotFound"} else 409
    return HTTPException(
        status_code=status,
        detail={"code": exc.code, "message": exc.message},
    )


async def _read_progression(store: ProgressionStore) -> dict:
    try:
        return await asyncio.to_thread(store.read_progression)
    except ProgressionStoreError as exc:
        raise _store_unavailable(exc) from exc


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "contractVersion": "1.0"}


@app.get("/api/v1/heroes", response_model=HeroRosterResponse)
async def list_heroes() -> dict:
    return {
        "contractVersion": CONTRACT_VERSION,
        "heroes": registry.adapter.roster(),
    }


@app.get(
    "/api/v1/progression",
    response_model=PlayerProgressionResponse,
    responses={503: {"model": RetryableHttpErrorResponse}},
)
async def get_progression(
    store: Annotated[ProgressionStore, Depends(get_progression_store)],
) -> dict:
    return {
        "contractVersion": CONTRACT_VERSION,
        **await _read_progression(store),
    }


@app.get(
    "/api/v1/stages",
    response_model=StructuredStagesResponse,
    responses={503: {"model": RetryableHttpErrorResponse}},
)
async def list_stages(
    store: Annotated[ProgressionStore, Depends(get_progression_store)],
) -> dict:
    return stages_response(await _read_progression(store))


@app.post(
    "/api/v1/battles",
    responses={
        409: {"model": HttpErrorResponse},
        422: {"model": HttpErrorResponse},
        503: {"model": RetryableHttpErrorResponse},
    },
)
async def create_battle(
    request: CreateBattleRequest,
    store: Annotated[ProgressionStore, Depends(get_progression_store)],
) -> dict:
    try:
        await asyncio.to_thread(
            store.assert_player_team_unlocked, list(request.player_team)
        )
    except ProgressionStoreError as exc:
        raise _store_unavailable(exc) from exc
    except StageAccessError as exc:
        raise _access_error(exc) from exc
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


@app.post(
    "/api/v1/stages/{stage_id}/battles/{battle_index}",
    responses={
        404: {"model": HttpErrorResponse},
        409: {"model": HttpErrorResponse},
        422: {"model": HttpErrorResponse},
        503: {"model": RetryableHttpErrorResponse},
    },
)
async def create_stage_battle(
    stage_id: StageId,
    battle_index: Annotated[int, ApiPath(ge=1, le=9)],
    request: CreateStageBattleRequest,
    store: Annotated[ProgressionStore, Depends(get_progression_store)],
) -> dict:
    try:
        battle = await asyncio.to_thread(
            store.assert_stage_battle_access, stage_id, battle_index
        )
        await asyncio.to_thread(
            store.assert_player_team_unlocked, list(request.player_team)
        )
    except ProgressionStoreError as exc:
        raise _store_unavailable(exc) from exc
    except StageAccessError as exc:
        raise _access_error(exc) from exc

    if len(request.player_team) != battle.battle_size:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "invalidStageBattleConfiguration",
                "message": "playerTeam must contain exactly the fixed battle size.",
            },
        )
    valid_player_formations = {
        1: {None},
        2: {"front-rear", "side-by-side"},
        3: {"one-front-two-rear", "two-front-one-rear", "all-front"},
    }[battle.battle_size]
    if request.player_formation not in valid_player_formations:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "invalidStageBattleConfiguration",
                "message": "playerFormation must be valid for this stage battle size.",
            },
        )

    _, envelope = await asyncio.to_thread(
        registry.create,
        seed=request.seed,
        battle_size=battle.battle_size,
        player_team=list(request.player_team),
        enemy_composition_mode="specified",
        enemy_team=list(battle.enemy_definition_ids),
        enemy_control_mode="computer",
        player_formation=request.player_formation,
        enemy_formation=battle.formation,
        fixed_computer_formation=True,
        stage_id=stage_id,
        stage_battle_index=battle_index,
    )
    return envelope


@app.get(
    "/api/v1/battles/{battle_id}",
    responses={404: {"model": HttpErrorResponse}},
)
async def get_battle(battle_id: str) -> dict:
    session = registry.get(battle_id)
    if session is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "battleNotFound", "message": "Battle was not found."},
        )
    def locked_snapshot() -> dict:
        with session.lock:
            snapshot = registry.adapter.snapshot(session)
            return registry.adapter.envelope(session, snapshot)

    return await asyncio.to_thread(locked_snapshot)


@app.post(
    "/api/v1/battles/{battle_id}/commands",
    responses={404: {"model": HttpErrorResponse}},
)
async def submit_command(battle_id: str, command: UseSkillCommand) -> dict:
    session = registry.get(battle_id)
    if session is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "battleNotFound", "message": "Battle was not found."},
        )
    result = await asyncio.to_thread(
        registry.adapter.submit, session, command.model_dump(by_alias=True)
    )
    envelope = registry.adapter.envelope(session, result)
    # Cached idempotent responses retain their original revision and snapshot.
    # Keep the envelope internally consistent instead of pairing old data with
    # the session's newer revision.
    envelope["revision"] = result["revision"]
    return envelope


@app.post(
    "/api/v1/battles/{battle_id}/completion",
    response_model=VictoryCommitResponse,
    responses={
        404: {"model": HttpErrorResponse},
        409: {"model": HttpErrorResponse},
        503: {"model": RetryableHttpErrorResponse},
    },
)
async def commit_battle_completion(
    battle_id: str,
    store: Annotated[ProgressionStore, Depends(get_progression_store)],
) -> dict:
    session = registry.get(battle_id)
    if session is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "battleNotFound",
                "message": "Battle was not found.",
            },
        )
    if session.stage_id is None or session.stage_battle_index is None:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "battleNotStageScoped",
                "message": "Arena battles do not update structured-stage progression.",
            },
        )

    def commit_if_won() -> dict:
        with session.lock:
            snapshot = registry.adapter.snapshot(session)
            outcome = snapshot.get("outcome")
            if snapshot["phase"] != "ended" or outcome != {
                "kind": "victory",
                "winningSideId": "friendly",
            }:
                raise StageAccessError(
                    "friendlyVictoryRequired",
                    "Only an authoritative friendly victory can be committed.",
                )
            return store.commit_victory(
                battle_id=battle_id,
                stage_id=session.stage_id,
                battle_index=session.stage_battle_index,
            )

    try:
        result = await asyncio.to_thread(commit_if_won)
    except ProgressionStoreError as exc:
        raise _store_unavailable(exc) from exc
    except StageAccessError as exc:
        raise _access_error(exc) from exc
    return {
        "contractVersion": CONTRACT_VERSION,
        "battleId": battle_id,
        **result,
    }
