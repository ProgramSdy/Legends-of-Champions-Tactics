import type { Metadata } from "next";
import { DebugBattleExperience } from "@/components/battle/DebugBattleExperience";

export const metadata: Metadata = {
  title: "Engineering Test & Debugging · Legends of Champions Tactics",
  description: "A save-independent environment for testing registered heroes and battles.",
};

export default function DebugPage() {
  return <DebugBattleExperience />;
}
