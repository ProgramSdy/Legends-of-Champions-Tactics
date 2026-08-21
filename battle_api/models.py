"""Versioned transport models for the Stage 2 battle API."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


HeroDefinitionId = Literal[
    "hero.priest.comprehensiveness",
    "hero.priest.discipline",
    "hero.paladin.retribution",
    "hero.paladin.protection",
    "hero.paladin.holy",
    "hero.mage.comprehensiveness",
    "hero.warrior.defence",
    "hero.warrior.weapon_master",
    "hero.warrior.berserker",
    "hero.rogue.comprehensiveness",
]

TwoHeroFormationId = Literal["front-rear", "side-by-side"]
ThreeHeroFormationId = Literal[
    "one-front-two-rear",
    "two-front-one-rear",
    "all-front",
]
FormationId = TwoHeroFormationId | ThreeHeroFormationId

TWO_HERO_FORMATION_IDS: tuple[TwoHeroFormationId, ...] = (
    "front-rear",
    "side-by-side",
)
THREE_HERO_FORMATION_IDS: tuple[ThreeHeroFormationId, ...] = (
    "one-front-two-rear",
    "two-front-one-rear",
    "all-front",
)


class ApiModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class StrictApiModel(ApiModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


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
    player_formation: FormationId | None = Field(
        default=None, alias="playerFormation"
    )
    enemy_formation: FormationId | None = Field(
        default=None, alias="enemyFormation"
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
        if self.battle_size == 2:
            if self.player_formation is None:
                raise ValueError("playerFormation is required for a 2v2 battle")
            if self.player_formation not in TWO_HERO_FORMATION_IDS:
                raise ValueError(
                    "playerFormation must be front-rear or side-by-side "
                    "for a 2v2 battle"
                )
            if (
                self.enemy_control_mode == "player"
                and self.enemy_formation is None
            ):
                raise ValueError(
                    "enemyFormation is required for a player-controlled 2v2 enemy"
                )
            if (
                self.enemy_formation is not None
                and self.enemy_formation not in TWO_HERO_FORMATION_IDS
            ):
                raise ValueError(
                    "enemyFormation must be front-rear or side-by-side "
                    "for a 2v2 battle"
                )
        elif self.battle_size == 3:
            if self.player_formation is None:
                raise ValueError("playerFormation is required for a 3v3 battle")
            if self.player_formation not in THREE_HERO_FORMATION_IDS:
                raise ValueError(
                    "playerFormation must be one-front-two-rear, "
                    "two-front-one-rear, or all-front for a 3v3 battle"
                )
            if self.enemy_control_mode == "player":
                if self.enemy_formation is None:
                    raise ValueError(
                        "enemyFormation is required for a player-controlled 3v3 enemy"
                    )
                if self.enemy_formation not in THREE_HERO_FORMATION_IDS:
                    raise ValueError(
                        "enemyFormation must be one-front-two-rear, "
                        "two-front-one-rear, or all-front for a 3v3 battle"
                    )
            elif self.enemy_formation is not None:
                raise ValueError(
                    "enemyFormation must be omitted for a computer-controlled "
                    "3v3 enemy"
                )
        elif (
            self.player_formation is not None
            or self.enemy_formation is not None
        ):
            raise ValueError("formation fields are only valid for 2v2 or 3v3 battles")
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


class RetryableErrorResponse(ErrorResponse):
    retryable: Literal[True] = True


class RetryableHttpErrorResponse(ApiModel):
    detail: RetryableErrorResponse


StageId = Literal["paladins-altar", "warriors-barrack"]
RewardKind = Literal["heroUnlock", "itemCard"]


class GrantedReward(ApiModel):
    reward_id: str = Field(alias="rewardId")
    count: int = Field(ge=1)


class StageProgress(ApiModel):
    stage_id: StageId = Field(alias="stageId")
    highest_completed_battle: int = Field(alias="highestCompletedBattle", ge=0, le=9)
    unlocked_battle: int = Field(alias="unlockedBattle", ge=1, le=9)
    completed: bool


class PlayerProgression(ApiModel):
    profile_id: str = Field(alias="profileId", min_length=1)
    unlocked_hero_definition_ids: list[HeroDefinitionId] = Field(
        alias="unlockedHeroDefinitionIds"
    )
    stage_progress: list[StageProgress] = Field(alias="stageProgress")
    granted_rewards: list[GrantedReward] = Field(alias="grantedRewards")


class PlayerProgressionResponse(PlayerProgression):
    contract_version: Literal["1.0"] = Field(default="1.0", alias="contractVersion")


class StageReward(ApiModel):
    reward_id: str = Field(alias="rewardId")
    kind: RewardKind
    hero_definition_id: HeroDefinitionId | None = Field(alias="heroDefinitionId")
    notification: str


class StageBattleDefinition(ApiModel):
    id: str
    display_order: int = Field(alias="displayOrder", ge=1, le=9)
    battle_size: Literal[1, 2, 3] = Field(alias="battleSize")
    formation: FormationId | None
    enemy_definition_ids: list[HeroDefinitionId] = Field(alias="enemyDefinitionIds")
    reward: StageReward | None
    unlocked: bool
    completed: bool


class StructuredStageDefinition(ApiModel):
    stage_id: StageId = Field(alias="stageId")
    display_name: str = Field(alias="displayName")
    progress: StageProgress
    battles: list[StageBattleDefinition]


class StructuredStagesResponse(ApiModel):
    contract_version: Literal["1.0"] = Field(default="1.0", alias="contractVersion")
    stages: list[StructuredStageDefinition]


class CreateStageBattleRequest(ApiModel):
    player_team: list[HeroDefinitionId] = Field(
        alias="playerTeam", min_length=1, max_length=3
    )
    player_formation: FormationId | None = Field(
        default=None, alias="playerFormation"
    )
    seed: int | None = None


class VictoryCommitResponse(ApiModel):
    contract_version: Literal["1.0"] = Field(default="1.0", alias="contractVersion")
    battle_id: str = Field(alias="battleId")
    already_committed: bool = Field(alias="alreadyCommitted")
    newly_granted_rewards: list[StageReward] = Field(alias="newlyGrantedRewards")
    progression: PlayerProgression


SaveSlotId = Literal[1, 2, 3, 4, 5]


class EmptySaveSlotRequest(StrictApiModel):
    """Explicitly forbids client-authored progression in create/load actions."""


class ConfirmSaveSlotOverwriteRequest(StrictApiModel):
    confirm_overwrite: bool = Field(alias="confirmOverwrite")


class SaveSlotSummary(ApiModel):
    slot_id: SaveSlotId = Field(alias="slotId")
    occupied: bool
    profile_id: str | None = Field(alias="profileId")
    created_at: datetime | None = Field(alias="createdAt")
    last_played_at: datetime | None = Field(alias="lastPlayedAt")
    active: bool


class SaveSlotListResponse(ApiModel):
    contract_version: Literal["1.0"] = Field(default="1.0", alias="contractVersion")
    active_slot_id: SaveSlotId | None = Field(alias="activeSlotId")
    slots: list[SaveSlotSummary] = Field(min_length=5, max_length=5)


class SaveSlotActionResponse(ApiModel):
    contract_version: Literal["1.0"] = Field(default="1.0", alias="contractVersion")
    active_slot_id: SaveSlotId = Field(alias="activeSlotId")
    slot: SaveSlotSummary
    progression: PlayerProgression
