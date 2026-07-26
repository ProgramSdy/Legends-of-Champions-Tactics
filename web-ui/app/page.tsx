import type { Metadata } from "next";
import { BattleExperience } from "@/components/battle/BattleExperience";

export const metadata: Metadata = {
  title: "Battle · Legends of Champions Tactics",
  description: "Engine-backed tactical battle interface.",
};

export default function Home() {
  return <BattleExperience />;
}
