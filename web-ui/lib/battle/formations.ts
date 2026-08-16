import type { BattleSnapshot, CombatantPosition, DuoFormationId, SideId, TrioFormationId } from "./types";

export type BattleFormat = "duel" | "duo" | "trio";
export type FormationSlot = "front" | "centre" | "rear";

export interface FormationPosition {
  slot: FormationSlot;
  x: number;
  y: number;
  scale: number;
  /** Visual depth only: higher values render nearer figures above lower ones. */
  depth?: number;
  /** Horizontal panel lane in pixels; keeps an overhead clear of neighbouring art. */
  panelOffsetX?: number;
}

export const duoFormationRegistry: Record<DuoFormationId, Record<SideId, FormationPosition[]>> = {
  "front-rear": {
    friendly: [
      { slot: "front", x: 42, y: 68, scale: 1.02 },
      { slot: "rear", x: 22, y: 68, scale: .94 },
    ],
    enemy: [
      { slot: "front", x: 59, y: 68, scale: 1.04 },
      { slot: "rear", x: 78, y: 68, scale: .94 },
    ],
  },
  "side-by-side": {
    friendly: [
      { slot: "front", x: 33, y: 54, scale: .94 },
      { slot: "front", x: 33, y: 85, scale: 1.02, panelOffsetX: -105 },
    ],
    enemy: [
      { slot: "front", x: 68, y: 54, scale: .94 },
      { slot: "front", x: 68, y: 85, scale: 1.04, panelOffsetX: 105 },
    ],
  },
};

export const trioFormationRegistry: Record<TrioFormationId, Record<SideId, FormationPosition[]>> = {
  "one-front-two-rear": {
    friendly: [
      { slot: "front", x: 42, y: 68, scale: .94, depth: 4 },
      { slot: "rear", x: 28, y: 80, scale: 1.04, depth: 5, panelOffsetX: -105 },
      { slot: "rear", x: 28, y: 53, scale: .8, depth: 3, panelOffsetX: -105 },
    ],
    enemy: [
      { slot: "front", x: 59, y: 68, scale: .94, depth: 4 },
      { slot: "rear", x: 73, y: 53, scale: .8, depth: 3, panelOffsetX: 105 },
      { slot: "rear", x: 73, y: 80, scale: 1.04, depth: 5, panelOffsetX: 105 },
    ],
  },
  "two-front-one-rear": {
    friendly: [
      { slot: "front", x: 42, y: 54, scale: .8, depth: 3 },
      { slot: "front", x: 42, y: 81, scale: 1.04, depth: 5, panelOffsetX: 105 },
      { slot: "rear", x: 23, y: 67, scale: .94, depth: 4, panelOffsetX: -105 },
    ],
    enemy: [
      { slot: "front", x: 59, y: 81, scale: 1.04, depth: 5, panelOffsetX: -105 },
      { slot: "front", x: 59, y: 54, scale: .8, depth: 3 },
      { slot: "rear", x: 78, y: 67, scale: .94, depth: 4, panelOffsetX: 105 },
    ],
  },
  "all-front": {
    friendly: [
      { slot: "front", x: 39.5, y: 52, scale: .8, depth: 3 },
      { slot: "front", x: 39.5, y: 71, scale: .94, depth: 4, panelOffsetX: 105 },
      { slot: "front", x: 39.5, y: 90, scale: 1.04, depth: 5, panelOffsetX: -105 },
    ],
    enemy: [
      { slot: "front", x: 60.5, y: 90, scale: 1.04, depth: 5, panelOffsetX: 105 },
      { slot: "front", x: 60.5, y: 71, scale: .94, depth: 4, panelOffsetX: -105 },
      { slot: "front", x: 60.5, y: 52, scale: .8, depth: 3 },
    ],
  },
};

export const formationRegistry: Record<BattleFormat, Record<SideId, FormationPosition[]>> = {
  duel: {
    friendly: [{ slot: "centre", x: 29, y: 80, scale: 1.5 }],
    enemy: [{ slot: "centre", x: 71, y: 80, scale: 1.5 }],
  },
  duo: {
    friendly: duoFormationRegistry["front-rear"].friendly,
    enemy: duoFormationRegistry["front-rear"].enemy,
  },
  trio: {
    friendly: trioFormationRegistry["one-front-two-rear"].friendly,
    enemy: trioFormationRegistry["one-front-two-rear"].enemy,
  },
};

export function getBattleFormat(snapshot: BattleSnapshot): BattleFormat {
  const largestTeam = Math.max(...snapshot.sides.map((side) =>
    side.combatantIds.filter((id) => !snapshot.combatants[id]?.isSummon).length,
  ));
  return largestTeam <= 1 ? "duel" : largestTeam === 2 ? "duo" : "trio";
}

export function duoFormationFor(snapshot: BattleSnapshot, sideId: SideId): DuoFormationId {
  const positions = snapshot.sides
    .find((side) => side.id === sideId)
    ?.combatantIds
    .map((id) => snapshot.combatants[id])
    .filter((combatant) => combatant && !combatant.isSummon)
    .slice(0, 2)
    .map((combatant) => combatant.position) ?? [];
  return positions.length === 2 && positions.every((position) => position === "front")
    ? "side-by-side"
    : "front-rear";
}

export function trioFormationFor(snapshot: BattleSnapshot, sideId: SideId): TrioFormationId {
  const formation = snapshot.formations[sideId];
  return formation === "one-front-two-rear"
    || formation === "two-front-one-rear"
    || formation === "all-front"
    ? formation
    : "one-front-two-rear";
}

export function formationFor(
  snapshot: BattleSnapshot,
  sideId: SideId,
  slot: number,
  position?: CombatantPosition,
): FormationPosition {
  const format = getBattleFormat(snapshot);
  if (format === "duel") {
    return formationRegistry.duel[sideId][slot] ?? formationRegistry.duel[sideId][0];
  }
  const layout = format === "duo"
    ? duoFormationRegistry[duoFormationFor(snapshot, sideId)][sideId]
    : trioFormationRegistry[trioFormationFor(snapshot, sideId)][sideId];
  const coordinate = layout[slot] ?? formationRegistry.trio[sideId][Math.min(slot, 2)];
  const authoritativePosition = position
    ?? snapshot.sides.find((side) => side.id === sideId)?.combatantIds
      .map((id) => snapshot.combatants[id])
      .find((combatant) => combatant?.slot === slot)?.position;
  return { ...coordinate, slot: authoritativePosition === "rear" ? "rear" : "front" };
}
