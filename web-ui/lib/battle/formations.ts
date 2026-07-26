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
    friendly: [{ slot: "centre", x: 29, y: 45, scale: 1.28 }],
    enemy: [{ slot: "centre", x: 71, y: 45, scale: 1.28 }],
  },
  duo: {
    friendly: [
      { slot: "front", x: 35, y: 40, scale: 1.02 },
      { slot: "rear", x: 20, y: 54, scale: .94 },
    ],
    enemy: [
      { slot: "front", x: 65, y: 40, scale: 1.02 },
      { slot: "rear", x: 80, y: 54, scale: .94 },
    ],
  },
  trio: {
    friendly: [
      { slot: "front", x: 38, y: 37, scale: .9 },
      { slot: "centre", x: 23, y: 48, scale: .86 },
      { slot: "rear", x: 10, y: 59, scale: .8 },
    ],
    enemy: [
      { slot: "front", x: 62, y: 37, scale: .9 },
      { slot: "centre", x: 77, y: 48, scale: .86 },
      { slot: "rear", x: 90, y: 59, scale: .8 },
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
