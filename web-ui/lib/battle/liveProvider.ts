import {
  BattleProviderError,
  type BattleCreateConfiguration,
  type BattleCommand,
  type BattleProvider,
  type BattleSnapshot,
  type BattleState,
  type HeroDefinitionSummary,
  type PresentationScript,
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

export async function fetchHeroRoster(
  baseUrl = process.env.NEXT_PUBLIC_BATTLE_API_URL ?? "http://localhost:8001",
): Promise<HeroDefinitionSummary[]> {
  let response: Response;
  try {
    response = await fetch(`${baseUrl}/api/v1/heroes`);
  } catch {
    throw new BattleProviderError("Battle service is disconnected. Start the Python adapter and retry.", "disconnected");
  }
  if (!response.ok) throw new BattleProviderError(`Battle adapter returned HTTP ${response.status}.`, "adapter");
  const body = await response.json() as { contractVersion: string; heroes: HeroDefinitionSummary[] };
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
  return body.heroes;
}

export class LiveBattleProvider implements BattleProvider {
  private battleId: string | null = null;
  private state: BattleState | null = null;

  constructor(
    private readonly baseUrl = process.env.NEXT_PUBLIC_BATTLE_API_URL ?? "http://localhost:8001",
    private readonly configuration: BattleCreateConfiguration = {
      battleSize: 1,
      playerTeam: ["hero.warrior.weapon_master"],
      enemyCompositionMode: "specified",
      enemyTeam: ["hero.rogue.comprehensiveness"],
      enemyControlMode: "player",
    },
  ) {}

  private async request<T>(path: string, init?: RequestInit): Promise<Envelope<T>> {
    let response: Response;
    try {
      response = await fetch(`${this.baseUrl}${path}`, {
        ...init,
        headers: { "Content-Type": "application/json", ...init?.headers },
      });
    } catch {
      throw new BattleProviderError("Battle service is disconnected. Start the Python adapter and retry.", "disconnected");
    }
    if (!response.ok) {
      const body = await response.json().catch(() => null) as { detail?: { message?: string } } | null;
      throw new BattleProviderError(body?.detail?.message ?? `Battle adapter returned HTTP ${response.status}.`, "adapter");
    }
    const envelope = await response.json() as Envelope<T>;
    if (envelope.contractVersion !== "1.0") {
      throw new BattleProviderError(`Unsupported battle contract ${envelope.contractVersion}.`, "adapter");
    }
    return envelope;
  }

  async getState(): Promise<BattleState> {
    if (this.state) return structuredClone(this.state);
    const envelope = await this.request<CreateData>("/api/v1/battles", {
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
