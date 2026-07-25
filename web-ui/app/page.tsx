import type { Metadata } from "next";
import { MockBattleScreen } from "@/components/battle/MockBattleScreen";

export const metadata: Metadata = {
  title: "Battle · Legends of Champions Tactics",
  description: "Stage 1 battle presentation vertical slice.",
};

export default function Home() {
  return <MockBattleScreen />;
}
