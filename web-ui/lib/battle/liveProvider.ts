import {
  BattleProviderError,
  type BattleCreateConfiguration,
  type BattleCommand,
  type BattleProvider,
  type BattleSnapshot,
  type BattleState,
  type HeroDefinitionSummary,
  type PlayerProgressionResponse,
  type PresentationScript,
  type SaveSlotActionResponse,
  type SaveSlotId,
  type SaveSlotSummary,
  type SaveSlotsResponse,
  type StructuredBattleCreateConfiguration,
  type StructuredStagesResponse,
  type VictoryCommitResponse,
} from "./types";

interface Envelope<T> {
  contractVersion: "1.0";
  battleId: string;
  revision: number;
  data: T;
}

interface CreateData {
  events?: PresentationScript["events"];
  openingSnapshot?: BattleSnapshot;
  playOpening?: boolean;
  snapshot: BattleSnapshot;
}

interface CommandAccepted {
  accepted: true;
  commandId: string;
  revision: number;
  events: PresentationScript["events"];
  snapshot: BattleSnapshot;
}

interface CommandRejected {
  accepted: false;
  commandId: string;
  revision: number;
  code: string;
  message: string;
  snapshot: BattleSnapshot;
}

const DEFAULT_BASE_URL = process.env.NEXT_PUBLIC_BATTLE_API_URL ?? "http://localhost:8001";

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

async function requestAdapterJson(
  baseUrl: string,
  path: string,
  init?: RequestInit,
): Promise<unknown> {
  let response: Response;
  try {
    response = await fetch(`${baseUrl}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new BattleProviderError(
      "Battle service is disconnected. Start the Python adapter and retry.",
      "disconnected",
    );
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null) as {
      detail?: { message?: string };
    } | null;
    throw new BattleProviderError(
      body?.detail?.message ?? `Battle adapter returned HTTP ${response.status}.`,
      "adapter",
    );
  }
  try {
    return await response.json();
  } catch {
    throw new BattleProviderError("The battle service returned invalid JSON.", "adapter");
  }
}

function isStageProgress(value: unknown): boolean {
  return isRecord(value)
    && (value.stageId === "paladins-altar" || value.stageId === "warriors-barrack")
    && Number.isInteger(value.highestCompletedBattle)
    && Number(value.highestCompletedBattle) >= 0
    && Number(value.highestCompletedBattle) <= 9
    && Number.isInteger(value.unlockedBattle)
    && Number(value.unlockedBattle) >= 1
    && Number(value.unlockedBattle) <= 9
    && typeof value.completed === "boolean";
}

function isStageReward(value: unknown): boolean {
  return isRecord(value)
    && typeof value.rewardId === "string"
    && (value.kind === "heroUnlock" || value.kind === "itemCard")
    && (value.heroDefinitionId === null || typeof value.heroDefinitionId === "string")
    && typeof value.notification === "string";
}

function isProgression(value: unknown, withVersion: boolean): boolean {
  return isRecord(value)
    && (!withVersion || value.contractVersion === "1.0")
    && typeof value.profileId === "string"
    && value.profileId.length > 0
    && Array.isArray(value.unlockedHeroDefinitionIds)
    && value.unlockedHeroDefinitionIds.every((id) => typeof id === "string")
    && Array.isArray(value.stageProgress)
    && value.stageProgress.length === 2
    && value.stageProgress.every(isStageProgress)
    && Array.isArray(value.grantedRewards)
    && value.grantedRewards.every((reward) => isRecord(reward)
      && typeof reward.rewardId === "string"
      && Number.isInteger(reward.count)
      && Number(reward.count) >= 1);
}

const SAVE_SLOT_IDS = [1, 2, 3, 4, 5] as const;

function isSaveSlotId(value: unknown): value is SaveSlotId {
  return SAVE_SLOT_IDS.includes(value as SaveSlotId);
}

function isNullableString(value: unknown): value is string | null {
  return value === null || typeof value === "string";
}

function isSaveSlotSummary(value: unknown): value is SaveSlotSummary {
  if (!isRecord(value)
    || !isSaveSlotId(value.slotId)
    || typeof value.occupied !== "boolean"
    || !isNullableString(value.profileId)
    || !isNullableString(value.createdAt)
    || !isNullableString(value.lastPlayedAt)
    || typeof value.active !== "boolean") {
    return false;
  }
  return value.occupied
    ? Boolean(value.profileId && value.createdAt && value.lastPlayedAt)
    : value.profileId === null
      && value.createdAt === null
      && value.lastPlayedAt === null
      && value.active === false;
}

function isSaveSlotsResponse(value: unknown): value is SaveSlotsResponse {
  if (!isRecord(value)
    || value.contractVersion !== "1.0"
    || !(value.activeSlotId === null || isSaveSlotId(value.activeSlotId))
    || !Array.isArray(value.slots)
    || value.slots.length !== SAVE_SLOT_IDS.length
    || !value.slots.every(isSaveSlotSummary)) {
    return false;
  }
  const slotIds = value.slots.map((slot) => slot.slotId);
  if (!SAVE_SLOT_IDS.every((slotId, index) => slotIds[index] === slotId)) return false;
  const activeSlots = value.slots.filter((slot) => slot.active);
  return value.activeSlotId === null
    ? activeSlots.length === 0
    : activeSlots.length === 1 && activeSlots[0].slotId === value.activeSlotId;
}

function isSaveSlotActionResponse(
  value: unknown,
  expectedSlotId: SaveSlotId,
): value is SaveSlotActionResponse {
  return isRecord(value)
    && value.contractVersion === "1.0"
    && value.activeSlotId === expectedSlotId
    && isSaveSlotSummary(value.slot)
    && value.slot.slotId === expectedSlotId
    && value.slot.occupied
    && value.slot.active
    && isProgression(value.progression, false)
    && value.slot.profileId === (value.progression as Record<string, unknown>).profileId;
}

function assertSaveSlotId(slotId: number): asserts slotId is SaveSlotId {
  if (!isSaveSlotId(slotId)) {
    throw new BattleProviderError("Save slot must be between 1 and 5.", "adapter");
  }
}

export async function fetchHeroRoster(
  baseUrl = DEFAULT_BASE_URL,
): Promise<HeroDefinitionSummary[]> {
  const body = await requestAdapterJson(baseUrl, "/api/v1/heroes") as {
    contractVersion?: unknown;
    heroes?: unknown;
  };
  const validHeroes = Array.isArray(body.heroes) && body.heroes.length === 10 && body.heroes.every((hero) =>
    hero !== null
    && typeof hero === "object"
    && typeof hero.definitionId === "string"
    && typeof hero.displayName === "string"
    && typeof hero.faculty === "string"
    && typeof hero.specialization === "string"
  );
  if (body.contractVersion !== "1.0" || !validHeroes) {
    throw new BattleProviderError("The battle service returned an unsupported hero roster.", "adapter");
  }
  return body.heroes as HeroDefinitionSummary[];
}

export async function fetchPlayerProgression(
  baseUrl = DEFAULT_BASE_URL,
): Promise<PlayerProgressionResponse> {
  const body = await requestAdapterJson(baseUrl, "/api/v1/progression");
  if (!isProgression(body, true)) {
    throw new BattleProviderError(
      "The battle service returned unsupported player progression.",
      "adapter",
    );
  }
  return body as PlayerProgressionResponse;
}

export async function fetchSaveSlots(
  baseUrl = DEFAULT_BASE_URL,
): Promise<SaveSlotsResponse> {
  const body = await requestAdapterJson(baseUrl, "/api/v1/save-slots");
  if (!isSaveSlotsResponse(body)) {
    throw new BattleProviderError(
      "The battle service returned unsupported save-slot data.",
      "adapter",
    );
  }
  return body;
}

async function runSaveSlotAction(
  slotId: SaveSlotId,
  action: "create" | "load" | "overwrite",
  baseUrl: string,
): Promise<SaveSlotActionResponse> {
  assertSaveSlotId(slotId);
  const body = await requestAdapterJson(
    baseUrl,
    `/api/v1/save-slots/${slotId}/${action}`,
    {
      method: "POST",
      ...(action === "overwrite"
        ? { body: JSON.stringify({ confirmOverwrite: true }) }
        : {}),
    },
  );
  if (!isSaveSlotActionResponse(body, slotId)) {
    throw new BattleProviderError(
      "The battle service returned an unsupported save-slot result.",
      "adapter",
    );
  }
  return body;
}

export function createSaveSlot(
  slotId: SaveSlotId,
  baseUrl = DEFAULT_BASE_URL,
): Promise<SaveSlotActionResponse> {
  return runSaveSlotAction(slotId, "create", baseUrl);
}

export function loadSaveSlot(
  slotId: SaveSlotId,
  baseUrl = DEFAULT_BASE_URL,
): Promise<SaveSlotActionResponse> {
  return runSaveSlotAction(slotId, "load", baseUrl);
}

export function overwriteSaveSlot(
  slotId: SaveSlotId,
  baseUrl = DEFAULT_BASE_URL,
): Promise<SaveSlotActionResponse> {
  return runSaveSlotAction(slotId, "overwrite", baseUrl);
}

export async function fetchStructuredStages(
  baseUrl = DEFAULT_BASE_URL,
): Promise<StructuredStagesResponse> {
  const body = await requestAdapterJson(baseUrl, "/api/v1/stages");
  const valid = isRecord(body)
    && body.contractVersion === "1.0"
    && Array.isArray(body.stages)
    && body.stages.length === 2
    && body.stages.every((stage) => isRecord(stage)
      && (stage.stageId === "paladins-altar" || stage.stageId === "warriors-barrack")
      && typeof stage.displayName === "string"
      && isStageProgress(stage.progress)
      && Array.isArray(stage.battles)
      && stage.battles.length === 9
      && stage.battles.every((battle) => isRecord(battle)
        && typeof battle.id === "string"
        && Number.isInteger(battle.displayOrder)
        && Number(battle.displayOrder) >= 1
        && Number(battle.displayOrder) <= 9
        && (battle.battleSize === 1 || battle.battleSize === 2 || battle.battleSize === 3)
        && (battle.formation === null || typeof battle.formation === "string")
        && Array.isArray(battle.enemyDefinitionIds)
        && battle.enemyDefinitionIds.every((id) => typeof id === "string")
        && (battle.reward === null || isStageReward(battle.reward))
        && typeof battle.unlocked === "boolean"
        && typeof battle.completed === "boolean"));
  if (!valid) {
    throw new BattleProviderError(
      "The battle service returned unsupported structured-stage data.",
      "adapter",
    );
  }
  return body as unknown as StructuredStagesResponse;
}

export class LiveBattleProvider implements BattleProvider {
  private battleId: string | null = null;
  private state: BattleState | null = null;

  constructor(
    private readonly baseUrl = DEFAULT_BASE_URL,
    private readonly configuration: BattleCreateConfiguration | StructuredBattleCreateConfiguration = {
      battleSize: 1,
      playerTeam: ["hero.warrior.weapon_master"],
      enemyCompositionMode: "specified",
      enemyTeam: ["hero.rogue.comprehensiveness"],
      enemyControlMode: "player",
    },
    private readonly createPath = "/api/v1/battles",
  ) {}

  private async request<T>(path: string, init?: RequestInit): Promise<Envelope<T>> {
    const envelope = await requestAdapterJson(this.baseUrl, path, init) as Envelope<T>;
    if (envelope.contractVersion !== "1.0") {
      throw new BattleProviderError(`Unsupported battle contract ${envelope.contractVersion}.`, "adapter");
    }
    return envelope;
  }

  async getState(): Promise<BattleState> {
    if (this.state) return structuredClone(this.state);
    const envelope = await this.request<CreateData>(this.createPath, {
      method: "POST",
      body: JSON.stringify(this.configuration),
    });
    this.battleId = envelope.battleId;
    this.state = {
      revision: envelope.revision,
      snapshot: envelope.data.snapshot,
      events: envelope.data.events ?? [],
      ...(envelope.data.playOpening === true && envelope.data.openingSnapshot
        ? { openingSnapshot: envelope.data.openingSnapshot, playOpening: true }
        : {}),
    };
    return structuredClone(this.state);
  }

  async commitStageVictory(): Promise<VictoryCommitResponse> {
    if (!this.battleId) {
      throw new BattleProviderError("The live battle session has not initialized.", "adapter");
    }
    const body = await requestAdapterJson(
      this.baseUrl,
      `/api/v1/battles/${encodeURIComponent(this.battleId)}/completion`,
      { method: "POST" },
    );
    const valid = isRecord(body)
      && body.contractVersion === "1.0"
      && body.battleId === this.battleId
      && typeof body.alreadyCommitted === "boolean"
      && Array.isArray(body.newlyGrantedRewards)
      && body.newlyGrantedRewards.every(isStageReward)
      && isProgression(body.progression, false);
    if (!valid) {
      throw new BattleProviderError(
        "The battle service returned an unsupported completion result.",
        "adapter",
      );
    }
    return body as unknown as VictoryCommitResponse;
  }

  async submitCommand(command: BattleCommand): Promise<PresentationScript> {
    if (!this.battleId) throw new BattleProviderError("The live battle session has not initialized.", "adapter");
    const envelope = await this.request<CommandAccepted | CommandRejected>(
      `/api/v1/battles/${encodeURIComponent(this.battleId)}/commands`,
      { method: "POST", body: JSON.stringify(command) },
    );
    const result = envelope.data;
    if (this.state && result.accepted && result.revision <= this.state.revision) {
      return {
        id: command.commandId,
        label: "Command already applied",
        eventType: "magic",
        events: [],
        snapshot: structuredClone(this.state.snapshot),
        revision: this.state.revision,
      };
    }
    if (this.state && !result.accepted && result.revision < this.state.revision) {
      throw new BattleProviderError(
        result.message,
        result.code === "staleRevision" ? "stale" : "rejected",
        this.state.snapshot,
        this.state.revision,
      );
    }
    this.state = { revision: result.revision, snapshot: result.snapshot };
    if (!result.accepted) {
      throw new BattleProviderError(
        result.message,
        result.code === "staleRevision" ? "stale" : "rejected",
        result.snapshot,
        result.revision,
      );
    }
    return {
      id: command.commandId,
      label: result.events.at(0)?.message ?? "Battle action",
      eventType: result.events.find((event) => event.effectHint)?.effectHint ?? "magic",
      events: result.events,
      snapshot: result.snapshot,
      revision: result.revision,
    };
  }
}
