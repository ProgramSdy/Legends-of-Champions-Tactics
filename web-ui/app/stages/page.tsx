import type { Metadata } from "next";
import { StageSelectionScreen } from "@/components/stages/StageSelectionScreen";
import { isEngineeringMode } from "@/lib/releaseMode";
import { PublicSessionGate } from "@/components/session/PublicSessionProvider";

export const metadata: Metadata = {
  title: "Stage Selection · Legends of Champions Tactics",
  description: "Choose a destination in the Valley of Champions.",
};

type StagesPageProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

export default async function StagesPage({ searchParams }: StagesPageProps) {
  const query = await searchParams;
  const engineeringMode = isEngineeringMode();
  const debugHotspots =
    engineeringMode && query.debugHotspots === "1";

  return <PublicSessionGate>
    <StageSelectionScreen
      debugHotspots={debugHotspots}
      showEngineeringRoute={engineeringMode}
    />
  </PublicSessionGate>;
}
