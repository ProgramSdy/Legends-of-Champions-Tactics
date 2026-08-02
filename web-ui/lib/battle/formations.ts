import type { BattleSnapshot, SideId } from "./types";

export type BattleFormat = "duel" | "duo" | "trio";
export type FormationSlot = "front" | "centre" | "rear";

export interface FormationPosition {
  slot: FormationSlot;
  x: number;
  y: number;
  scale: number;
}

export const formationRegistry: Record<BattleFormat, Record<SideId, FormationPosition[]>> = {
  duel: {
    friendly: [{ slot: "centre", x: 29, y: 80, scale: 1.5 }],
    enemy: [{ slot: "centre", x: 71, y: 80, scale: 1.5 }],
  },
  duo: {
    friendly: [
      { slot: "front", x: 38, y: 90, scale: 1.02 },
      { slot: "rear", x: 25, y: 65, scale: .94 },
    ],
    enemy: [
      { slot: "front", x: 62, y: 90, scale: 1.04 },
      { slot: "rear", x: 75, y: 65, scale: .94 },
    ],
  },
  trio: {
    friendly: [
      { slot: "front", x: 31, y: 90, scale: 1.02 },
      { slot: "centre", x: 20, y: 65, scale: .94 },
      { slot: "rear", x: 42, y: 55, scale: .8 },
    ],
    enemy: [
      { slot: "front", x: 69, y: 90, scale: 1.02 },
      { slot: "centre", x: 80, y: 65, scale: .94 },
      { slot: "rear", x: 58, y: 55, scale: .8 },
    ],
  },
};

export function getBattleFormat(snapshot: BattleSnapshot): BattleFormat {
  const largestTeam = Math.max(...snapshot.sides.map((side) =>
    side.combatantIds.filter((id) => !snapshot.combatants[id]?.isSummon).length,
  ));
  return largestTeam <= 1 ? "duel" : largestTeam === 2 ? "duo" : "trio";
}

export function formationFor(snapshot: BattleSnapshot, sideId: SideId, slot: number): FormationPosition {
  const format = getBattleFormat(snapshot);
  return formationRegistry[format][sideId][slot] ?? formationRegistry.trio[sideId][Math.min(slot, 2)];
}
