import type { Metadata } from "next";
import { StartupScreen } from "@/components/startup/StartupScreen";

export const metadata: Metadata = {
  title: "Legends of Champions Tactics · Start",
  description: "Enter the dark-fantasy world of Legends of Champions Tactics.",
};

export default function Home() {
  return <StartupScreen />;
}
