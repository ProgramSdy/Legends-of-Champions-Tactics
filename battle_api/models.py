"""Versioned transport models for the Stage 2 battle API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


HeroDefinitionId = Literal[
    "hero.priest.comprehensiveness",
    "hero.priest.discipline",
    "hero.paladin.retribution",
    "hero.paladin.protection",
    "hero.mage.comprehensiveness",
    "hero.warrior.defence",
    "hero.warrior.weapon_master",
    "hero.rogue.comprehensiveness",
]


class ApiModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class HeroDefinition(ApiModel):
    definition_id: HeroDefinitionId = Field(alias="definitionId")
    display_name: str = Field(alias="displayName")
    faculty: str
    specialization: str


class HeroRosterResponse(ApiModel):
    contract_version: Literal["1.0"] = Field(default="1.0", alias="contractVersion")
    heroes: list[HeroDefinition]


class CreateBattleRequest(ApiModel):
    # ``scenarioId`` remains accepted for the existing Stage 2 caller. The
    # typed team fields are the additive UI-002 creation contract.
    scenario_id: Literal["ragnar-vs-nighthawk"] | None = Field(
        default="ragnar-vs-nighthawk", alias="scenarioId"
    )
    battle_size: Literal[1, 2, 3] = Field(default=1, alias="battleSize")
    player_team: list[HeroDefinitionId] = Field(
        default_factory=lambda: ["hero.warrior.weapon_master"],
        alias="playerTeam",
        min_length=1,
        max_length=3,
    )
    enemy_composition_mode: Literal["random", "specified"] = Field(
        default="specified", alias="enemyCompositionMode"
    )
    enemy_team: list[HeroDefinitionId] | None = Field(
        default=None,
        alias="enemyTeam",
        max_length=3,
    )
    enemy_control_mode: Literal["computer", "player"] = Field(
        default="player", alias="enemyControlMode"
    )
    seed: int | None = None

    @model_validator(mode="after")
    def validate_teams(self) -> "CreateBattleRequest":
        if (
            self.scenario_id == "ragnar-vs-nighthawk"
            and self.enemy_team is None
            and "enemy_composition_mode" not in self.model_fields_set
        ):
            self.enemy_team = ["hero.rogue.comprehensiveness"]
        if len(self.player_team) != self.battle_size:
            raise ValueError("playerTeam must contain exactly battleSize heroes")
        if self.enemy_composition_mode == "specified":
            if self.enemy_team is None or len(self.enemy_team) != self.battle_size:
                raise ValueError(
                    "enemyTeam must contain exactly battleSize heroes when specified"
                )
        elif self.enemy_team not in (None, []):
            raise ValueError("enemyTeam must be omitted when enemyCompositionMode is random")
        return self


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
