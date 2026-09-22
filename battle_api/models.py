"""Versioned transport models for the Stage 2 battle API."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

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


class HeroConfiguredRange(StrictApiModel):
    id: str
    label: str
    minimum: int
    maximum: int

    @model_validator(mode="after")
    def validate_bounds(self) -> "HeroConfiguredRange":
        if self.minimum > self.maximum:
            raise ValueError("minimum must be less than or equal to maximum")
        return self


class HeroStartingStatRange(HeroConfiguredRange):
    id: Literal["hp", "damage", "defence", "agility"]


class HeroStartingResistanceRange(HeroConfiguredRange):
    id: Literal["fire", "frost", "arcane", "shadow", "death", "poison", "nature"]


class HeroSkillInventoryItem(StrictApiModel):
    skill_id: str = Field(alias="skillId", pattern=r"^skill\.[a-z0-9_]+\.[a-z0-9_]+$")
    display_name: str = Field(alias="displayName")
    is_passive: bool = Field(alias="isPassive")


class HeroStarterUnlockSource(StrictApiModel):
    kind: Literal["starter"]


class HeroStageRewardUnlockSource(StrictApiModel):
    kind: Literal["stageReward"]
    stage_id: Literal["paladins-altar", "warriors-barrack"] = Field(
        alias="stageId"
    )
    stage_display_name: str = Field(alias="stageDisplayName")
    battle_index: int = Field(alias="battleIndex", ge=1, le=9)


class HeroDefinition(ApiModel):
    definition_id: HeroDefinitionId = Field(alias="definitionId")
    display_name: str = Field(alias="displayName")
    faculty: str
    specialization: str
    starting_stat_ranges: list[HeroStartingStatRange] = Field(
        alias="startingStatRanges", min_length=4, max_length=4
    )
    starting_resistance_ranges: list[HeroStartingResistanceRange] = Field(
        alias="startingResistanceRanges", min_length=7, max_length=7
    )
    skills: list[HeroSkillInventoryItem] = Field(min_length=3)
    unlock_source: Annotated[
        HeroStarterUnlockSource | HeroStageRewardUnlockSource,
        Field(discriminator="kind"),
    ] | None = Field(alias="unlockSource")


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


class CreateDebugBattleRequest(CreateBattleRequest):
    """Free-form battle creation that forbids hidden progression fields."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class UseSkillCommand(ApiModel):
    type: Literal["useSkill"] = "useSkill"
    command_id: str = Field(alias="commandId", min_length=1, max_length=128)
    expected_revision: int = Field(alias="expectedRevision", ge=0)
    actor_id: str = Field(alias="actorId", min_length=1)
    skill_id: str = Field(alias="skillId", min_length=1)
    target_ids: list[str] = Field(alias="targetIds", max_length=3)


class BattlePreviewRequest(StrictApiModel):
    expected_revision: int = Field(alias="expectedRevision", ge=0)
    actor_id: str = Field(alias="actorId", min_length=1)
    skill_id: str = Field(alias="skillId", min_length=1)
    target_ids: list[str] = Field(alias="targetIds", min_length=0, max_length=2)


class DamageAmountRange(ApiModel):
    minimum: int = Field(alias="min", ge=0)
    maximum: int = Field(alias="max", ge=0)


class DamagePreviewPrimary(ApiModel):
    kind: Literal["damage", "healing", "prevented"]
    amount_range: DamageAmountRange = Field(alias="amountRange")
    reason_id: str | None = Field(default=None, alias="reasonId")


class DamagePreviewConsequence(ApiModel):
    kind: Literal["bleed", "poison", "cold"]
    certainty: Literal["conditional", "onHit"]
    chance_percent: int | None = Field(
        default=None, alias="chancePercent", ge=0, le=100
    )
    outcome: Literal["firstApplication", "durationRefresh"] | None = None


class ShadowWordPainPreviewConsequence(StrictApiModel):
    kind: Literal["shadowWordPain"]
    certainty: Literal["onHit"]


class SecondaryHealingPreviewConsequence(StrictApiModel):
    kind: Literal["secondaryHealing"]
    certainty: Literal["always", "onHit"]
    recipient_id: str = Field(alias="recipientId", min_length=1)
    amount_range: DamageAmountRange = Field(alias="amountRange")


class WrathDamageBonusPreviewConsequence(StrictApiModel):
    kind: Literal["wrathDamageBonus"]
    certainty: Literal["always"]
    stacks: Literal[1, 2]
    amount_range: DamageAmountRange = Field(alias="amountRange")


class WrathHealingBonusPreviewConsequence(StrictApiModel):
    kind: Literal["wrathHealingBonus"]
    certainty: Literal["always"]
    stacks: Literal[1, 2]
    amount_range: DamageAmountRange = Field(alias="amountRange")


class WrathOfCrusaderPreviewConsequence(StrictApiModel):
    kind: Literal["wrathOfCrusader"]
    certainty: Literal["always"]
    recipient_id: str = Field(alias="recipientId", min_length=1)
    stacks: int = Field(ge=0)
    outcome: Literal["firstApplication", "nextStack", "durationRefresh"]


class ArmorBreakerPreviewConsequence(StrictApiModel):
    kind: Literal["armorBreaker"]
    certainty: Literal["onHit"]
    resulting_stacks: int = Field(alias="resultingStacks", ge=0, le=3)
    outcome: Literal["firstApplication", "nextStack", "durationRefresh"]


class StunPreviewConsequence(StrictApiModel):
    kind: Literal["stun"]
    certainty: Literal["onHit"]
    resulting_duration: int = Field(alias="resultingDuration", ge=1)
    outcome: Literal["firstApplication", "durationExtension"]


class CastingInterruptedPreviewConsequence(StrictApiModel):
    kind: Literal["castingInterrupted"]
    certainty: Literal["onHit"]


class ScoffPreviewConsequence(StrictApiModel):
    kind: Literal["scoff"]
    certainty: Literal["onHit"]
    outcome: Literal["firstApplication", "durationRefresh", "sourceReplacement"]


class HealingReductionPreviewConsequence(StrictApiModel):
    kind: Literal["healingReduction"]
    certainty: Literal["onHit"]
    percent: Literal[70]
    outcome: Literal["firstApplication", "alreadyActive"]


class WoundPreviewConsequence(StrictApiModel):
    kind: Literal["wound"]
    certainty: Literal["onHit"]
    agility_reduction: int = Field(alias="agilityReduction", ge=0)
    outcome: Literal["firstApplication"]


class ResistanceBoostPreviewConsequence(StrictApiModel):
    kind: Literal["resistanceBoost"]
    certainty: Literal["always", "onHit"]
    recipient_id: str = Field(alias="recipientId", min_length=1)
    resistances: list[Literal["fire", "frost", "death", "nature", "poison"]]
    amount: Literal[45]
    duration: Literal[2]
    outcome: Literal["firstApplication", "additionalApplication"]


class ControlImmunityPreviewConsequence(StrictApiModel):
    kind: Literal["controlImmunity"]
    certainty: Literal["always"]
    recipient_id: str = Field(alias="recipientId", min_length=1)
    duration: Literal[2]
    outcome: Literal["firstApplication", "durationRefresh"]


class DamageIncreasePreviewConsequence(StrictApiModel):
    kind: Literal["damageIncrease"]
    certainty: Literal["always"]
    recipient_id: str = Field(alias="recipientId", min_length=1)
    amount: int = Field(ge=0)
    outcome: Literal["firstApplication", "additionalApplication"]


class StatusRemovalPreviewConsequence(StrictApiModel):
    kind: Literal["statusRemoval"]
    certainty: Literal["always"]
    recipient_id: str = Field(alias="recipientId", min_length=1)
    status_ids: list[str] = Field(alias="statusIds")


class CooldownPreviewConsequence(StrictApiModel):
    kind: Literal["cooldown"]
    certainty: Literal["always"]
    recipient_id: str = Field(alias="recipientId", min_length=1)
    rounds: Literal[3]


class RevengeDamageBonusPreviewConsequence(StrictApiModel):
    kind: Literal["revengeDamageBonus"]
    certainty: Literal["always"]
    debuff_count: int = Field(alias="debuffCount", ge=1)
    amount_range: DamageAmountRange = Field(alias="amountRange")


class DamageReductionPreviewConsequence(StrictApiModel):
    kind: Literal["damageReduction"]
    certainty: Literal["onHit"]
    recipient_id: str = Field(alias="recipientId", min_length=1)
    percent: Literal[20]
    amount: int = Field(ge=0)
    duration: Literal[3]
    outcome: Literal["firstApplication"]


class DefenceIncreasePreviewConsequence(StrictApiModel):
    kind: Literal["defenceIncrease"]
    certainty: Literal["always"]
    recipient_id: str = Field(alias="recipientId", min_length=1)
    amount: int = Field(ge=0)
    resulting_stacks: int = Field(alias="resultingStacks", ge=1, le=2)
    duration: Literal[3]
    outcome: Literal["firstApplication", "nextStack", "durationRefresh"]


class ControlPreventedPreviewConsequence(StrictApiModel):
    kind: Literal["controlPrevented"]
    certainty: Literal["onHit"]
    recipient_id: str = Field(alias="recipientId", min_length=1)
    reason_id: Literal["status.warlust"] = Field(alias="reasonId")


class PurifyHealingPreviewConsequence(StrictApiModel):
    kind: Literal["purifyHealing"]
    certainty: Literal["always"]
    recipient_id: str = Field(alias="recipientId", min_length=1)
    duration: Literal[2]
    outcome: Literal["firstApplication", "durationRefresh", "alreadyActive"]


class RandomStatusRemovalPreviewConsequence(StrictApiModel):
    kind: Literal["randomStatusRemoval"]
    certainty: Literal["always"]
    recipient_id: str = Field(alias="recipientId", min_length=1)
    candidate_status_ids: list[str] = Field(
        alias="candidateStatusIds", min_length=1
    )
    maximum_removals: Literal[1] = Field(alias="maximumRemovals")
    may_remove_none: bool = Field(alias="mayRemoveNone")


class DamageImmunityPreviewConsequence(StrictApiModel):
    kind: Literal["damageImmunity"]
    certainty: Literal["always"]
    recipient_id: str = Field(alias="recipientId", min_length=1)
    duration: Literal[2]
    outcome: Literal["firstApplication", "durationRefresh"]


BattlePreviewConsequence = Annotated[
    DamagePreviewConsequence
    | ShadowWordPainPreviewConsequence
    | SecondaryHealingPreviewConsequence
    | WrathDamageBonusPreviewConsequence
    | WrathHealingBonusPreviewConsequence
    | WrathOfCrusaderPreviewConsequence
    | ArmorBreakerPreviewConsequence
    | StunPreviewConsequence
    | CastingInterruptedPreviewConsequence
    | ScoffPreviewConsequence
    | HealingReductionPreviewConsequence
    | WoundPreviewConsequence
    | ResistanceBoostPreviewConsequence
    | ControlImmunityPreviewConsequence
    | DamageIncreasePreviewConsequence
    | StatusRemovalPreviewConsequence
    | CooldownPreviewConsequence
    | RevengeDamageBonusPreviewConsequence
    | DamageReductionPreviewConsequence
    | DefenceIncreasePreviewConsequence
    | ControlPreventedPreviewConsequence
    | PurifyHealingPreviewConsequence
    | RandomStatusRemovalPreviewConsequence
    | DamageImmunityPreviewConsequence,
    Field(discriminator="kind"),
]


class DamagePreviewTarget(ApiModel):
    target_id: str = Field(alias="targetId")
    current_hp: int = Field(alias="currentHp", ge=0)
    max_hp: int = Field(alias="maxHp", ge=1)
    primary: DamagePreviewPrimary
    direct_hit_chance_percent: int | None = Field(
        default=None, alias="directHitChancePercent", ge=0, le=100
    )
    consequences: list[BattlePreviewConsequence]

    @model_validator(mode="after")
    def validate_hit_chance_for_primary(self):
        if self.primary.kind == "healing":
            if self.direct_hit_chance_percent is not None:
                raise ValueError("healing preview cannot include direct Hit Chance")
        elif self.direct_hit_chance_percent is None:
            raise ValueError("damage preview requires direct Hit Chance")
        return self


class BattleSelfPreview(ApiModel):
    recipient_id: str = Field(alias="recipientId", min_length=1)
    current_hp: int = Field(alias="currentHp", ge=0)
    max_hp: int = Field(alias="maxHp", ge=1)
    primary: DamagePreviewPrimary | None = None
    consequences: list[BattlePreviewConsequence]


class BattlePreviewData(ApiModel):
    revision: int = Field(ge=0)
    actor_id: str = Field(alias="actorId")
    skill_id: str = Field(alias="skillId")
    requested_target_ids: list[str] = Field(alias="requestedTargetIds")
    selected_target_ids: list[str] = Field(alias="selectedTargetIds")
    coverage: Literal["authoritative", "unavailable"]
    reason_id: str | None = Field(default=None, alias="reasonId")
    targets: list[DamagePreviewTarget]
    self_preview: BattleSelfPreview | None = Field(default=None, alias="selfPreview")


class BattlePreviewResponse(ApiModel):
    contract_version: Literal["1.0"] = Field(default="1.0", alias="contractVersion")
    battle_id: str = Field(alias="battleId")
    revision: int = Field(ge=0)
    data: BattlePreviewData


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


class ArenaEligibility(ApiModel):
    eligible: bool
    unlocked_hero_count: int = Field(alias="unlockedHeroCount", ge=0)
    required_hero_count: Literal[6] = Field(
        default=6, alias="requiredHeroCount"
    )


class ArenaNode(ApiModel):
    node_index: int = Field(alias="nodeIndex", ge=1, le=12)
    battle_size: Literal[1, 2, 3] = Field(alias="battleSize")
    enemy_formation: FormationId | None = Field(alias="enemyFormation")
    enemy_definition_ids: list[HeroDefinitionId] = Field(
        alias="enemyDefinitionIds", min_length=1, max_length=3
    )
    completed: bool


class ArenaRun(ApiModel):
    run_id: str = Field(alias="runId", min_length=1)
    status: Literal["active", "completed"]
    squad_definition_ids: list[HeroDefinitionId] = Field(
        alias="squadDefinitionIds", min_length=6, max_length=6
    )
    current_node_index: int | None = Field(
        alias="currentNodeIndex", default=None, ge=1, le=12
    )
    created_at: datetime = Field(alias="createdAt")
    completed_at: datetime | None = Field(alias="completedAt")
    nodes: list[ArenaNode] = Field(min_length=12, max_length=12)


class ArenaStateResponse(ApiModel):
    contract_version: Literal["1.0"] = Field(default="1.0", alias="contractVersion")
    profile_id: str = Field(alias="profileId", min_length=1)
    eligibility: ArenaEligibility
    run: ArenaRun | None


class CreateArenaRunRequest(StrictApiModel):
    squad_definition_ids: list[HeroDefinitionId] = Field(
        alias="squadDefinitionIds", min_length=6, max_length=6
    )

    @model_validator(mode="after")
    def validate_distinct_squad(self) -> "CreateArenaRunRequest":
        if len(set(self.squad_definition_ids)) != 6:
            raise ValueError("squadDefinitionIds must contain 6 distinct heroes")
        return self


class CreateArenaBattleRequest(StrictApiModel):
    player_team: list[HeroDefinitionId] = Field(
        alias="playerTeam", min_length=1, max_length=3
    )
    player_formation: FormationId | None = Field(
        default=None, alias="playerFormation"
    )


class ArenaVictoryCommitResponse(ApiModel):
    contract_version: Literal["1.0"] = Field(default="1.0", alias="contractVersion")
    battle_id: str = Field(alias="battleId", min_length=1)
    already_committed: bool = Field(alias="alreadyCommitted")
    arena: ArenaStateResponse
