"use client";

import { MockBattleProvider } from "@/lib/battle/fixture";
import { BattleScreen } from "./BattleScreen";

const provider = new MockBattleProvider();
const demos = [
  ["magic", "Magic attack"], ["healing", "Healing"], ["melee", "Melee"],
  ["status", "Apply status"], ["evade", "Evade"], ["summon", "Summon"],
] as const;

export function MockBattleScreen() {
  return (
    <BattleScreen
      provider={provider}
      mode="mock"
      mockDemos={demos.map(([id, label]) => ({ id, label, run: () => provider.runDemo(id) }))}
    />
  );
}
