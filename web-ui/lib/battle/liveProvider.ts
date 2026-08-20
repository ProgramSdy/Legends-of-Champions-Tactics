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
    && value.profileId === "profile.local.default"
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
