import type { Metadata } from "next";
import { StageSelectionScreen } from "@/components/stages/StageSelectionScreen";

export const metadata: Metadata = {
  title: "Stage Selection · Legends of Champions Tactics",
  description: "Choose a destination in the Valley of Champions.",
};

type StagesPageProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

export default async function StagesPage({ searchParams }: StagesPageProps) {
  const query = await searchParams;
  const debugHotspots =
    process.env.NODE_ENV !== "production" && query.debugHotspots === "1";

  return <StageSelectionScreen debugHotspots={debugHotspots} />;
}
