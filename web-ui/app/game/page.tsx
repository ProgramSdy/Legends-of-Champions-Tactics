import type { Metadata } from "next";
import { BattleExperience } from "@/components/battle/BattleExperience";
import { resolveEnabledStage } from "@/components/stages/stage-config";

export const metadata: Metadata = {
  title: "Team Builder · Legends of Champions Tactics",
  description: "Build a team and enter an engine-backed tactical battle.",
};

type GamePageProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

export default async function GamePage({ searchParams }: GamePageProps) {
  const query = await searchParams;
  const requestedStageId = typeof query.stage === "string" ? query.stage : null;
  const selectedStage = resolveEnabledStage(requestedStageId);
  return <BattleExperience key={selectedStage.id} selectedStageId={selectedStage.id} />;
}
