"""Versioned transport models for the Stage 2 battle API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class CreateBattleRequest(ApiModel):
    scenario_id: Literal["ragnar-vs-nighthawk"] = Field(
        default="ragnar-vs-nighthawk", alias="scenarioId"
    )
    seed: int | None = None


class UseSkillCommand(ApiModel):
    type: Literal["useSkill"] = "useSkill"
    command_id: str = Field(alias="commandId", min_length=1, max_length=128)
    expected_revision: int = Field(alias="expectedRevision", ge=0)
    actor_id: str = Field(alias="actorId", min_length=1)
    skill_id: str = Field(alias="skillId", min_length=1)
    target_ids: list[str] = Field(alias="targetIds", max_length=3)


class ErrorResponse(ApiModel):
    code: str
    message: str


class HttpErrorResponse(ApiModel):
    detail: ErrorResponse
