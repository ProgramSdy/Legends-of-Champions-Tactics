"""Small async FastAPI transport for the process-local battle registry."""

from __future__ import annotations

import asyncio
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .adapter import BattleRegistry
from .models import CreateBattleRequest, HttpErrorResponse, UseSkillCommand

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


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "contractVersion": "1.0"}


@app.post(
    "/api/v1/battles",
    responses={422: {"model": HttpErrorResponse}},
)
async def create_battle(request: CreateBattleRequest) -> dict:
    _, envelope = await asyncio.to_thread(registry.create, seed=request.seed)
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
