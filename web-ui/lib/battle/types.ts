export type SideId = "friendly" | "enemy";
export type EffectHint = "magic" | "healing" | "melee" | "status" | "summon";

export interface StatusState {
  id: string;
  instanceId: string;
  kind: "buff" | "debuff" | "control" | "other";
  roundsRemaining: number | null;
  stacks: number | null;
  sourceCombatantId: string | null;
}

export interface SkillState {
  id: string;
  displayName: string;
  description?: string;
  targetMode: "none" | "self" | "singleAlly" | "singleEnemy" | "multipleAllies" | "multipleEnemies" | "flexible";
  maximumTargets: number;
  cooldownRemaining: number;
  available: boolean;
  unavailableReason: string | null;
  resourceCost: null | { kind: string; amount: number };
}

export interface CombatantState {
  id: string;
  definitionId: string;
  sideId: SideId;
  slot: number;
  displayName: string;
  faculty: string;
  specialization: string;
  isSummon: boolean;
  masterCombatantId: string | null;
  summonRoundsRemaining: number | null;
  isPlayerControlled: boolean;
  alive: boolean;
  hp: { current: number; maximum: number };
  resource: null | { kind: string; current: number; maximum: number };
  statuses: StatusState[];
  skills: SkillState[];
}

export interface LegalAction {
  skillId: string;
  actorId: string;
  minimumTargets: number;
  maximumTargets: number;
  validTargetIds: string[];
}

export interface BattleSnapshot {
  phase: "initializing" | "roundStart" | "awaitingCommand" | "resolving" | "roundEnd" | "ended";
  round: number;
  turn: { index: number; total: number };
  activeCombatantId: string | null;
  outcome: null | { kind: "victory" | "draw" | "roundLimit"; winningSideId: SideId | null };
  sides: Array<{ id: SideId; combatantIds: string[]; maxSlots: number }>;
  combatants: Record<string, CombatantState>;
  turnOrder: Array<{ combatantId: string; hasActed: boolean; isCurrent: boolean }>;
  legalActions: LegalAction[];
}

export type BattleEventType =
  | "battleStarted" | "roundStarted" | "turnStarted" | "skillStarted"
  | "characterMoved" | "projectileLaunched" | "damageApplied" | "healingApplied"
  | "statusApplied" | "statusRemoved" | "attackEvaded" | "characterSummoned"
  | "characterDefeated" | "turnEnded" | "battleEnded";

export interface BattleEvent {
  id: string;
  sequence: number;
  type: BattleEventType;
  sourceId?: string;
  targetId?: string;
  targetIds?: string[];
  skillId?: string;
  statusId?: string;
  amount?: number;
  hpAfter?: { current: number; maximum: number };
  roundsRemaining?: number | null;
  combatant?: CombatantState;
  movement?: "lunge" | "return" | "offset";
  effectHint?: EffectHint;
  message: string;
}

export interface PresentationScript {
  id: string;
  label: string;
  eventType: EffectHint | "evade";
  events: BattleEvent[];
  snapshot: BattleSnapshot;
  revision: number;
}

export type BattleCommand =
  | { type: "useSkill"; commandId: string; expectedRevision: number; actorId: string; skillId: string; targetIds: string[] }
  | { type: "endTurn"; commandId: string; expectedRevision: number; actorId: string };

export interface BattleState {
  revision: number;
  snapshot: BattleSnapshot;
  events?: BattleEvent[];
}

export interface BattleProvider {
  getState(): Promise<BattleState>;
  submitCommand(command: BattleCommand): Promise<PresentationScript>;
}

export type ProviderErrorKind = "disconnected" | "rejected" | "stale" | "adapter";

export class BattleProviderError extends Error {
  constructor(
    message: string,
    public readonly kind: ProviderErrorKind,
    public readonly snapshot?: BattleSnapshot,
    public readonly revision?: number,
  ) {
    super(message);
    this.name = "BattleProviderError";
  }
}
