export const FORMATION_DEMONSTRATION_IDS = [
  "front-rear",
  "side-by-side",
  "one-front-two-rear",
  "two-front-one-rear",
  "all-front",
] as const;

export const FORMATION_DEMONSTRATION_ATTACK_TYPES = [
  "melee",
  "rangedProjectile",
  "rangedInstant",
] as const;

export type FormationDemonstrationId = typeof FORMATION_DEMONSTRATION_IDS[number];
export type FormationDemonstrationAttackType = typeof FORMATION_DEMONSTRATION_ATTACK_TYPES[number];
export type FormationDemonstrationPosition = "front" | "rear";

export type FormationDemonstrationSlot = {
  slot: number;
  position: FormationDemonstrationPosition;
};

export type FormationDemonstrationTarget = {
  targetSlot: number;
  targetPosition: FormationDemonstrationPosition;
  eligible: boolean;
  multiplierPercent: 60 | 70 | 80 | 100 | null;
  reason: "eligible" | "protectedByFrontLine" | "defeated";
};

export type FormationDemonstrationEvaluation = {
  attackerSlot: number;
  attackerPosition: FormationDemonstrationPosition;
  attackType: FormationDemonstrationAttackType;
  enemyFrontDefeated: boolean;
  explanation: string;
  targets: FormationDemonstrationTarget[];
};

export type FormationDemonstrationFormation = {
  id: FormationDemonstrationId;
  battleSize: 2 | 3;
  hasRearEnemies: boolean;
  friendlySlots: FormationDemonstrationSlot[];
  enemySlots: FormationDemonstrationSlot[];
  evaluations: FormationDemonstrationEvaluation[];
};

export type FormationDemonstrationCatalogue = {
  contractVersion: "1.0";
  attackTypes: FormationDemonstrationAttackType[];
  formations: FormationDemonstrationFormation[];
};

const DEFAULT_BASE_URL = process.env.NEXT_PUBLIC_BATTLE_API_URL ?? "http://localhost:8001";

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function isSlot(value: unknown): value is FormationDemonstrationSlot {
  return isRecord(value)
    && Number.isInteger(value.slot)
    && (value.position === "front" || value.position === "rear");
}

function isTarget(value: unknown): value is FormationDemonstrationTarget {
  return isRecord(value)
    && Number.isInteger(value.targetSlot)
    && (value.targetPosition === "front" || value.targetPosition === "rear")
    && typeof value.eligible === "boolean"
    && (value.multiplierPercent === null || typeof value.multiplierPercent === "number" && [60, 70, 80, 100].includes(value.multiplierPercent))
    && (value.reason === "eligible" || value.reason === "protectedByFrontLine" || value.reason === "defeated");
}

function isEvaluation(value: unknown): value is FormationDemonstrationEvaluation {
  return isRecord(value)
    && Number.isInteger(value.attackerSlot)
    && (value.attackerPosition === "front" || value.attackerPosition === "rear")
    && FORMATION_DEMONSTRATION_ATTACK_TYPES.includes(value.attackType as FormationDemonstrationAttackType)
    && typeof value.enemyFrontDefeated === "boolean"
    && typeof value.explanation === "string"
    && Array.isArray(value.targets)
    && value.targets.every(isTarget);
}

function isFormation(value: unknown): value is FormationDemonstrationFormation {
  return isRecord(value)
    && FORMATION_DEMONSTRATION_IDS.includes(value.id as FormationDemonstrationId)
    && (value.battleSize === 2 || value.battleSize === 3)
    && typeof value.hasRearEnemies === "boolean"
    && Array.isArray(value.friendlySlots)
    && value.friendlySlots.every(isSlot)
    && Array.isArray(value.enemySlots)
    && value.enemySlots.every(isSlot)
    && Array.isArray(value.evaluations)
    && value.evaluations.every(isEvaluation);
}

const FORMATION_SHAPE: Record<FormationDemonstrationId, { battleSize: 2 | 3; hasRearEnemies: boolean; positions: FormationDemonstrationPosition[] }> = {
  "front-rear": { battleSize: 2, hasRearEnemies: true, positions: ["front", "rear"] },
  "side-by-side": { battleSize: 2, hasRearEnemies: false, positions: ["front", "front"] },
  "one-front-two-rear": { battleSize: 3, hasRearEnemies: true, positions: ["front", "rear", "rear"] },
  "two-front-one-rear": { battleSize: 3, hasRearEnemies: true, positions: ["front", "front", "rear"] },
  "all-front": { battleSize: 3, hasRearEnemies: false, positions: ["front", "front", "front"] },
};

function unique<T>(values: T[]) {
  return new Set(values).size === values.length;
}

function hasCompleteSlotSet(slots: FormationDemonstrationSlot[], size: number) {
  return slots.length === size
    && unique(slots.map((slot) => slot.slot))
    && slots.every((slot) => slot.slot >= 1 && slot.slot <= size);
}

function hasConsistentTarget(
  target: FormationDemonstrationTarget,
  evaluation: FormationDemonstrationEvaluation,
) {
  if (target.eligible) {
    return target.reason === "eligible" && target.multiplierPercent !== null;
  }
  if (target.multiplierPercent !== null || target.reason === "eligible") return false;
  if (target.reason === "defeated") {
    return evaluation.enemyFrontDefeated && target.targetPosition === "front";
  }
  return target.reason === "protectedByFrontLine" && target.targetPosition === "rear";
}

function hasCompleteEvaluations(formation: FormationDemonstrationFormation) {
  const frontStates = formation.hasRearEnemies ? [false, true] : [false];
  const expectedKeys = formation.friendlySlots.flatMap((attacker) =>
    FORMATION_DEMONSTRATION_ATTACK_TYPES.flatMap((attackType) =>
      frontStates.map((frontDefeated) => `${attacker.slot}:${attackType}:${frontDefeated}`)));
  const actualKeys = formation.evaluations.map((evaluation) =>
    `${evaluation.attackerSlot}:${evaluation.attackType}:${evaluation.enemyFrontDefeated}`);
  if (actualKeys.length !== expectedKeys.length || !unique(actualKeys)
    || expectedKeys.some((key) => !actualKeys.includes(key))) return false;

  return formation.evaluations.every((evaluation) => {
    const attacker = formation.friendlySlots.find((slot) => slot.slot === evaluation.attackerSlot);
    if (!attacker || attacker.position !== evaluation.attackerPosition || !evaluation.explanation.trim()) return false;
    if (evaluation.targets.length !== formation.enemySlots.length
      || !unique(evaluation.targets.map((target) => target.targetSlot))) return false;
    return formation.enemySlots.every((enemy) => {
      const target = evaluation.targets.find((item) => item.targetSlot === enemy.slot);
      if (!target || target.targetPosition !== enemy.position || !hasConsistentTarget(target, evaluation)) return false;
      return evaluation.enemyFrontDefeated ? enemy.position !== "front" || target.reason === "defeated" : target.reason !== "defeated";
    });
  });
}

function hasCompleteFormation(formation: FormationDemonstrationFormation) {
  const shape = FORMATION_SHAPE[formation.id];
  return formation.battleSize === shape.battleSize
    && formation.hasRearEnemies === shape.hasRearEnemies
    && hasCompleteSlotSet(formation.friendlySlots, shape.battleSize)
    && hasCompleteSlotSet(formation.enemySlots, shape.battleSize)
    && shape.positions.every((position, index) => formation.friendlySlots.find((slot) => slot.slot === index + 1)?.position === position)
    && shape.positions.every((position, index) => formation.enemySlots.find((slot) => slot.slot === index + 1)?.position === position)
    && formation.hasRearEnemies === formation.enemySlots.some((slot) => slot.position === "rear")
    && hasCompleteEvaluations(formation);
}

function parseCatalogue(value: unknown): FormationDemonstrationCatalogue {
  if (!isRecord(value)
    || value.contractVersion !== "1.0"
    || !Array.isArray(value.attackTypes)
    || value.attackTypes.length !== FORMATION_DEMONSTRATION_ATTACK_TYPES.length
    || !unique(value.attackTypes)
    || !FORMATION_DEMONSTRATION_ATTACK_TYPES.every((item) => (value.attackTypes as unknown[]).includes(item))
    || !Array.isArray(value.formations)
    || value.formations.length !== FORMATION_DEMONSTRATION_IDS.length
    || !value.formations.every(isFormation)) {
    throw new Error("The formation demonstration service returned invalid rule data.");
  }
  const catalogue = value as FormationDemonstrationCatalogue;
  if (!unique(catalogue.formations.map((formation) => formation.id))
    || FORMATION_DEMONSTRATION_IDS.some((id) => !catalogue.formations.some((formation) => formation.id === id))
    || !catalogue.formations.every(hasCompleteFormation)) {
    throw new Error("The formation demonstration service returned incomplete rule data.");
  }
  return catalogue;
}

export async function fetchFormationDemonstration(
  signal?: AbortSignal,
  baseUrl = DEFAULT_BASE_URL,
): Promise<FormationDemonstrationCatalogue> {
  let response: Response;
  try {
    response = await fetch(`${baseUrl}/api/v1/manual/formation-demonstration`, { signal });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new Error("Formation demonstration is unavailable. Start the battle service and retry.");
  }
  if (!response.ok) throw new Error(`Formation demonstration is unavailable (HTTP ${response.status}).`);
  return parseCatalogue(await response.json());
}
