"use client";

import { useEffect, useMemo, useState } from "react";
import { BATTLE_BACKGROUND } from "@/lib/battle/battleBackgrounds";
import { fetchHeroRoster, LiveBattleProvider } from "@/lib/battle/liveProvider";
import type { BattleCreateConfiguration, HeroDefinitionSummary } from "@/lib/battle/types";
import { BattleScreen } from "./BattleScreen";
import { TeamBuilder } from "./TeamBuilder";

type DebugResourceState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; roster: HeroDefinitionSummary[] };

export function DebugBattleExperience({ countdownStepMs = 1000 }: { countdownStepMs?: number }) {
  const [resources, setResources] = useState<DebugResourceState>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);
  const [configuration, setConfiguration] = useState<BattleCreateConfiguration | null>(null);
  const [sessionKey, setSessionKey] = useState(0);

  useEffect(() => {
    let current = true;
    void fetchHeroRoster()
      .then((roster) => {
        if (current) setResources({ status: "ready", roster });
      })
      .catch((reason: unknown) => {
        if (!current) return;
        setResources({
          status: "error",
          message: reason instanceof Error ? reason.message : "Unable to load the debug roster.",
        });
      });
    return () => { current = false; };
  }, [attempt]);

  const provider = useMemo(
    () => configuration
      ? new LiveBattleProvider(undefined, configuration, "/api/v1/debug/battles")
      : null,
    [configuration],
  );

  if (resources.status === "loading") return (
    <main className="loading-screen" aria-live="polite">
      <span className="loading-rune">◇</span>Loading registered debug roster…
    </main>
  );

  if (resources.status === "error") return (
    <main className="loading-screen">
      <section className="connection-state" role="alert">
        <strong>DEBUG ROSTER UNAVAILABLE</strong>
        <p>{resources.message}</p>
        <button type="button" onClick={() => {
          setResources({ status: "loading" });
          setAttempt((value) => value + 1);
        }}>Retry roster</button>
      </section>
    </main>
  );

  if (!provider) return (
    <TeamBuilder
      mode="debug"
      roster={resources.roster}
      onStart={(nextConfiguration) => {
        setSessionKey((key) => key + 1);
        setConfiguration(nextConfiguration);
      }}
    />
  );

  const closeDebugBattle = () => setConfiguration(null);
  return (
    <BattleScreen
      key={sessionKey}
      provider={provider}
      mode="live"
      backgroundImage={BATTLE_BACKGROUND}
      entryCountdownStepMs={countdownStepMs}
      completionActionLabel={() => "RETURN TO DEBUG BUILDER"}
      onBattleComplete={closeDebugBattle}
      onResign={closeDebugBattle}
    />
  );
}
