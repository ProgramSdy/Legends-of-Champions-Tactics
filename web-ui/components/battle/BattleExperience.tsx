"use client";

import { useEffect, useMemo, useState } from "react";
import { BattleScreen } from "./BattleScreen";
import { fetchHeroRoster, LiveBattleProvider } from "@/lib/battle/liveProvider";
import type { BattleCreateConfiguration, HeroDefinitionSummary } from "@/lib/battle/types";
import { TeamBuilder } from "./TeamBuilder";

export function BattleExperience() {
  const [configuration, setConfiguration] = useState<BattleCreateConfiguration | null>(null);
  const [sessionKey, setSessionKey] = useState(0);
  const [roster, setRoster] = useState<HeroDefinitionSummary[] | null>(null);
  const [rosterError, setRosterError] = useState<string | null>(null);
  const [rosterAttempt, setRosterAttempt] = useState(0);
  useEffect(() => {
    let current = true;
    fetchHeroRoster()
      .then((heroes) => { if (current) { setRoster(heroes); setRosterError(null); } })
      .catch((reason: unknown) => { if (current) setRosterError(reason instanceof Error ? reason.message : "Unable to load hero roster."); });
    return () => { current = false; };
  }, [rosterAttempt]);
  const provider = useMemo(() => configuration ? new LiveBattleProvider(undefined, configuration) : null, [configuration]);

  if (!provider && rosterError) return <main className="loading-screen"><section className="connection-state" role="alert"><strong>HERO ROSTER UNAVAILABLE</strong><p>{rosterError}</p><button onClick={() => { setRosterError(null); setRosterAttempt((attempt) => attempt + 1); }}>Retry connection</button></section></main>;
  if (!provider && !roster) return <main className="loading-screen" aria-live="polite"><span className="loading-rune">◇</span>Loading approved heroes…</main>;
  if (!provider) return <TeamBuilder roster={roster!} onStart={(next) => { setSessionKey((key) => key + 1); setConfiguration(next); }} />;
  return <BattleScreen key={sessionKey} provider={provider} mode="live" onReturnToBuilder={() => setConfiguration(null)} />;
}
