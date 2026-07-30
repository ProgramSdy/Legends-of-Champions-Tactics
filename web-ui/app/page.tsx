import type { Metadata } from "next";
import { BattleExperience } from "@/components/battle/BattleExperience";

export const metadata: Metadata = {
  title: "Team Builder · Legends of Champions Tactics",
  description: "Build a team and enter an engine-backed tactical battle.",
};

export default function Home() {
  return <BattleExperience />;
}
