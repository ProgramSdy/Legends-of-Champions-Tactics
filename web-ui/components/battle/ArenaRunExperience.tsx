"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { BATTLE_BACKGROUND } from "@/lib/battle/battleBackgrounds";
import {
  createArenaRun,
  abandonArenaRun,
  fetchArenaState,
  fetchHeroRoster,
  fetchPlayerProgression,
  LiveBattleProvider,
} from "@/lib/battle/liveProvider";
import type {
  ArenaRunNode,
  ArenaStateResponse,
  BattleOutcome,
  HeroDefinitionSummary,
  StructuredBattleCreateConfiguration,
} from "@/lib/battle/types";
import { AssetImage } from "./AssetImage";
import { BattleScreen } from "./BattleScreen";
import { TeamBuilder } from "./TeamBuilder";

type ArenaResources = {
  arena: ArenaStateResponse;
  roster: HeroDefinitionSummary[];
  unlockedDefinitionIds: string[];
};

type ActiveArenaBattle = {
  runId: string;
  node: ArenaRunNode;
  provider: LiveBattleProvider;
};

function portraitRequest(hero: HeroDefinitionSummary) {
  return {
    kind: "portrait" as const,
    key: hero.definitionId,
    className: hero.faculty,
    name: `${hero.faculty} ${hero.specialization}`,
  };
}

function ArenaSquadBuilder({
  roster,
  busy,
  onConfirm,
}: {
  roster: HeroDefinitionSummary[];
  busy: boolean;
  onConfirm: (definitionIds: string[]) => void;
}) {
  const [selected, setSelected] = useState<string[]>([]);
  const full = selected.length === 6;

  const toggleHero = (definitionId: string) => {
    setSelected((current) => current.includes(definitionId)
      ? current.filter((id) => id !== definitionId)
      : current.length < 6 ? [...current, definitionId] : current);
  };

  return (
    <section className="arena-squad-builder" aria-labelledby="arena-squad-heading">
      <header>
        <div><small>NEW ARENA RUN</small><h2 id="arena-squad-heading">Build your six-hero squad</h2></div>
        <strong>{selected.length} / 6 SELECTED</strong>
      </header>
      <p>This ordered squad is locked for all twelve battles. Choose exactly six distinct unlocked heroes.</p>
      <div className="arena-squad-grid">
        {roster.map((hero) => {
          const order = selected.indexOf(hero.definitionId);
          return (
            <button
              key={hero.definitionId}
              type="button"
              className={order >= 0 ? "selected" : ""}
              aria-pressed={order >= 0}
              aria-label={`${order >= 0 ? `Remove squad hero ${order + 1}` : "Add to Arena squad"}: ${hero.faculty} ${hero.specialization}`}
              onClick={() => toggleHero(hero.definitionId)}
            >
              <span className="arena-squad-portrait">
                <AssetImage request={portraitRequest(hero)} className="builder-hero-image" />
              </span>
              <strong>{hero.faculty}</strong>
              <small>{hero.specialization}</small>
              {order >= 0 ? <b aria-hidden="true">{order + 1}</b> : null}
            </button>
          );
        })}
      </div>
      <footer>
        <span aria-live="polite">{full ? "Squad ready. Confirm to generate the server-owned run." : `Choose ${6 - selected.length} more hero${6 - selected.length === 1 ? "" : "es"}.`}</span>
        <button type="button" disabled={!full || busy} onClick={() => onConfirm(selected)}>
          {busy ? "STARTING…" : "LOCK SQUAD & START RUN"}
        </button>
      </footer>
    </section>
  );
}

export function ArenaRunExperience({ countdownStepMs = 1000 }: { countdownStepMs?: number }) {
  const router = useRouter();
  const [resources, setResources] = useState<ArenaResources | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [busy, setBusy] = useState(false);
  const [newRunRequested, setNewRunRequested] = useState(false);
  const [activeBattle, setActiveBattle] = useState<ActiveArenaBattle | null>(null);
  const [sessionKey, setSessionKey] = useState(0);
  const [giveUpConfirmationOpen, setGiveUpConfirmationOpen] = useState(false);

  useEffect(() => {
    let current = true;
    void Promise.all([fetchArenaState(), fetchHeroRoster(), fetchPlayerProgression()])
      .then(([arena, roster, progression]) => {
        if (!current) return;
        if (arena.profileId !== progression.profileId) {
          throw new Error("Arena and progression belong to different active save slots.");
        }
        setResources({
          arena,
          roster,
          unlockedDefinitionIds: progression.unlockedHeroDefinitionIds,
        });
      })
      .catch((reason: unknown) => {
        if (current) setError(reason instanceof Error ? reason.message : "Unable to load Arena Run.");
      });
    return () => { current = false; };
  }, [attempt]);

  const provider = useMemo(() => activeBattle?.provider ?? null, [activeBattle]);

  if (!resources && !error) return (
    <main className="loading-screen" aria-live="polite"><span className="loading-rune">◇</span>Loading Arena Run…</main>
  );
  if (!resources) return (
    <main className="loading-screen"><section className="connection-state" role="alert">
      <strong>ARENA RUN UNAVAILABLE</strong><p>{error}</p>
      <button type="button" onClick={() => {
        setResources(null);
        setError(null);
        setAttempt((value) => value + 1);
      }}>Retry Arena</button>
    </section></main>
  );

  const { arena, roster, unlockedDefinitionIds } = resources;
  const run = arena.run;
  const unlockedRoster = roster.filter((hero) => unlockedDefinitionIds.includes(hero.definitionId));
  const currentNode = run?.nodes.find((node) => node.nodeIndex === run.currentNodeIndex) ?? null;

  const startRun = async (squadDefinitionIds: string[]) => {
    setBusy(true);
    setError(null);
    try {
      const nextArena = await createArenaRun(squadDefinitionIds);
      setResources((current) => current ? { ...current, arena: nextArena } : current);
      setNewRunRequested(false);
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "Unable to create Arena Run.");
    } finally {
      setBusy(false);
    }
  };

  const launchNode = (configuration: StructuredBattleCreateConfiguration) => {
    if (!run || !currentNode || run.status !== "active") return;
    const nextProvider = new LiveBattleProvider(
      undefined,
      configuration,
      `/api/v1/arena/runs/${encodeURIComponent(run.runId)}/nodes/${currentNode.nodeIndex}/battles`,
    );
    setSessionKey((key) => key + 1);
    setActiveBattle({ runId: run.runId, node: currentNode, provider: nextProvider });
  };

  const finishBattle = async (outcome: BattleOutcome) => {
    if (!activeBattle || !provider) return;
    const friendlyVictory = outcome.kind === "victory" && outcome.winningSideId === "friendly";
    if (!friendlyVictory) {
      setActiveBattle(null);
      return;
    }
    const completion = await provider.commitArenaVictory();
    setResources((current) => current ? { ...current, arena: completion.arena } : current);
    setActiveBattle(null);
  };

  const giveUpCurrentRun = async () => {
    if (!run) return;
    setBusy(true);
    setError(null);
    try {
      const nextArena = await abandonArenaRun(run.runId);
      setResources((current) => current ? { ...current, arena: nextArena } : current);
      setGiveUpConfirmationOpen(false);
      router.replace("/stages");
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "Unable to give up the Arena Run.");
    } finally {
      setBusy(false);
    }
  };

  if (provider) return (
    <BattleScreen
      key={sessionKey}
      provider={provider}
      mode="live"
      backgroundImage={BATTLE_BACKGROUND}
      entryCountdownStepMs={countdownStepMs}
      completionActionLabel={(outcome) => outcome.kind === "victory" && outcome.winningSideId === "friendly"
        ? "CONTINUE ARENA RUN"
        : "RETRY CURRENT NODE"}
      onBattleComplete={finishBattle}
      onResign={() => setActiveBattle(null)}
    />
  );

  const showSquadBuilder = (!run && arena.eligibility.eligible)
    || (run?.status === "completed" && newRunRequested);

  if (run?.status === "active" && currentNode) return (
    <>
      <TeamBuilder
        key={`${run.runId}.${currentNode.nodeIndex}`}
        mode="arena-run"
        roster={roster}
        availableDefinitionIds={run.squadDefinitionIds}
        node={currentNode}
        squadDefinitionIds={run.squadDefinitionIds}
        arenaProgress={run.nodes.map((node) => ({
          nodeIndex: node.nodeIndex,
          battleSize: node.battleSize,
          completed: node.completed,
          current: node.nodeIndex === run.currentNodeIndex,
        }))}
        onStart={launchNode}
        onGiveUpCurrentRun={() => setGiveUpConfirmationOpen(true)}
      />
      {giveUpConfirmationOpen ? <div className="arena-give-up-backdrop" role="presentation">
        <section className="arena-give-up-dialog" role="dialog" aria-modal="true" aria-labelledby="arena-give-up-heading">
          <small>ABANDON ARENA RUN</small>
          <h2 id="arena-give-up-heading">Give up your current run?</h2>
          <p>Your locked squad and all twelve node results for this run will be deleted. This cannot be undone.</p>
          <div>
            <button type="button" disabled={busy} onClick={giveUpCurrentRun}>{busy ? "GIVING UP…" : "YES"}</button>
            <button type="button" disabled={busy} onClick={() => setGiveUpConfirmationOpen(false)}>NO</button>
          </div>
        </section>
      </div> : null}
    </>
  );

  return (
    <div className="arena-run-hub">
      <Link className="arena-back" href="/stages">← BACK TO STAGE MAP</Link>
      <header className="arena-run-title">
        <div><small>VALLEY OF CHAMPIONS</small><h1>Arena Run</h1></div>
        <span>{run ? `${run.nodes.filter((node) => node.completed).length} / 12 VICTORIES` : "12 BATTLES"}</span>
      </header>

      {error ? <p className="arena-inline-error" role="alert">{error}</p> : null}

      {!arena.eligibility.eligible ? (
        <section className="arena-eligibility" aria-labelledby="arena-locked-heading">
          <span aria-hidden="true">◇</span><small>ARENA LOCKED</small>
          <h2 id="arena-locked-heading">Six unlocked heroes required</h2>
          <strong>{arena.eligibility.unlockedHeroCount} / {arena.eligibility.requiredHeroCount}</strong>
          <p>Continue structured training to unlock enough distinct registered heroes for a fixed Arena squad.</p>
        </section>
      ) : showSquadBuilder ? (
        <ArenaSquadBuilder roster={unlockedRoster} busy={busy} onConfirm={startRun} />
      ) : run?.status === "completed" ? (
            <section className="arena-completed" aria-labelledby="arena-completed-heading">
              <small>RUN COMPLETE</small><h2 id="arena-completed-heading">Twelve victories secured</h2>
              <p>This completed run remains recorded in the active save slot.</p>
              <button type="button" onClick={() => setNewRunRequested(true)}>NEW ARENA RUN</button>
            </section>
      ) : <section className="arena-inline-error" role="alert">The active run has no matching current node.</section>}
    </div>
  );
}
