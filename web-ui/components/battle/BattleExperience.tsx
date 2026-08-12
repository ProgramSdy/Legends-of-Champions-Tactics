"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { BattleScreen } from "./BattleScreen";
import { fetchHeroRoster, LiveBattleProvider } from "@/lib/battle/liveProvider";
import type { BattleCreateConfiguration, BattleOutcome, HeroDefinitionSummary } from "@/lib/battle/types";
import { BATTLE_BACKGROUND } from "@/lib/battle/battleBackgrounds";
import { TeamBuilder } from "./TeamBuilder";
import {
  missingStructuredStageRosterIds,
  resolveStructuredStage,
  type StructuredStageDefinition,
} from "@/components/stages/structured-stage-config";

type BattleExperienceProps = {
  countdownStepMs?: number;
  selectedStageId?: string;
};

export function BattleExperience(props: BattleExperienceProps) {
  const structuredStage = resolveStructuredStage(props.selectedStageId);
  return structuredStage
    ? <StructuredBattleExperience {...props} structuredStage={structuredStage} />
    : <BattleSession {...props} structuredStage={null} />;
}

function StructuredBattleExperience({
  structuredStage,
  ...props
}: BattleExperienceProps & { structuredStage: StructuredStageDefinition }) {
  const router = useRouter();
  return <BattleSession
    {...props}
    structuredStage={structuredStage}
    onStructuredStageComplete={() => router.replace("/stages")}
  />;
}

function BattleSession({
  countdownStepMs = 1000,
  selectedStageId,
  structuredStage,
  onStructuredStageComplete,
}: BattleExperienceProps & {
  structuredStage: StructuredStageDefinition | null;
  onStructuredStageComplete?: () => void;
}) {
  const [currentBattleIndex, setCurrentBattleIndex] = useState(0);
  const [configuration, setConfiguration] = useState<BattleCreateConfiguration | null>(null);
  const [sessionKey, setSessionKey] = useState(0);
  const [roster, setRoster] = useState<HeroDefinitionSummary[] | null>(null);
  const [rosterError, setRosterError] = useState<string | null>(null);
  const [rosterAttempt, setRosterAttempt] = useState(0);
  const [battleBackground, setBattleBackground] = useState<string | null>(null);
  useEffect(() => {
    let current = true;
    fetchHeroRoster()
      .then((heroes) => { if (current) { setRoster(heroes); setRosterError(null); } })
      .catch((reason: unknown) => { if (current) setRosterError(reason instanceof Error ? reason.message : "Unable to load hero roster."); });
    return () => { current = false; };
  }, [rosterAttempt]);
  const provider = useMemo(() => configuration ? new LiveBattleProvider(undefined, configuration) : null, [configuration]);
  const missingStructuredRosterIds = useMemo(
    () => structuredStage && roster
      ? missingStructuredStageRosterIds(structuredStage, roster)
      : [],
    [roster, structuredStage],
  );
  const currentStructuredBattle = structuredStage?.battles[currentBattleIndex] ?? null;

  const retryRoster = () => {
    setRoster(null);
    setRosterError(null);
    setRosterAttempt((attempt) => attempt + 1);
  };

  const closeLiveBattle = () => {
    setConfiguration(null);
    setBattleBackground(null);
  };

  const completeBattle = (outcome: BattleOutcome) => {
    closeLiveBattle();
    if (!structuredStage || !currentStructuredBattle) return;
    const friendlyVictory = outcome.kind === "victory" && outcome.winningSideId === "friendly";
    if (!friendlyVictory) return;
    const nextBattleIndex = currentBattleIndex + 1;
    if (nextBattleIndex < structuredStage.battles.length) {
      setCurrentBattleIndex(nextBattleIndex);
      return;
    }
    setCurrentBattleIndex(0);
    onStructuredStageComplete?.();
  };

  const completionLabel = (outcome: BattleOutcome) => {
    if (!structuredStage || !currentStructuredBattle) return "RETURN TO TEAM BUILDER";
    if (outcome.kind !== "victory" || outcome.winningSideId !== "friendly") return "RETRY BATTLE";
    const nextBattle = structuredStage.battles[currentBattleIndex + 1];
    return nextBattle ? `CONTINUE TO BATTLE ${nextBattle.displayOrder}` : "RETURN TO STAGE MAP";
  };

  if (!provider && rosterError) return <main className="loading-screen"><section className="connection-state" role="alert"><strong>HERO ROSTER UNAVAILABLE</strong><p>{rosterError}</p><button onClick={retryRoster}>Retry connection</button></section></main>;
  if (!provider && !roster) return <main className="loading-screen" aria-live="polite"><span className="loading-rune">◇</span>Loading approved heroes…</main>;
  if (!provider && structuredStage && missingStructuredRosterIds.length > 0) return (
    <main className="loading-screen">
      <section className="connection-state" role="alert">
        <strong>STAGE CONFIGURATION UNAVAILABLE</strong>
        <p>{structuredStage.displayName} cannot start because the approved roster is missing: {missingStructuredRosterIds.join(", ")}.</p>
        <button onClick={retryRoster}>Retry roster</button>
      </section>
    </main>
  );
  if (!provider) {
    const startBattle = (next: BattleCreateConfiguration) => {
      setSessionKey((key) => key + 1);
      setBattleBackground(BATTLE_BACKGROUND);
      setConfiguration(next);
    };
    return structuredStage && currentStructuredBattle
      ? <TeamBuilder
          key={currentStructuredBattle.id}
          mode="structured"
          roster={roster!}
          stage={structuredStage}
          battle={currentStructuredBattle}
          onStart={startBattle}
        />
      : <TeamBuilder roster={roster!} selectedStageId={selectedStageId} onStart={startBattle} />;
  }
  return <BattleScreen
    key={sessionKey}
    provider={provider}
    mode="live"
    backgroundImage={battleBackground ?? undefined}
    entryCountdownStepMs={countdownStepMs}
    completionActionLabel={completionLabel}
    onBattleComplete={completeBattle}
  />;
}
