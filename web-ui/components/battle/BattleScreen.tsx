"use client";

import { useEffect, useRef, useState, type CSSProperties } from "react";
import Link from "next/link";
import { usePresentationQueue } from "@/lib/battle/usePresentationQueue";
import type { BattleEvent, BattleEventType, BattleProvider, CombatantState, PresentationScript, SideId } from "@/lib/battle/types";
import { AssetImage } from "./AssetImage";
import { HeroCard, Meter } from "./HeroCard";
import { SkillCard } from "./SkillCard";
import { StatusIcon } from "./StatusIcon";
import { formationFor, getBattleFormat } from "@/lib/battle/formations";
import { BATTLE_BACKGROUND } from "@/lib/battle/battleBackgrounds";

const logGlyph: Record<BattleEventType, string> = {
  battleStarted: "◆", roundStarted: "◎", turnStarted: "▶", skillStarted: "✦",
  characterMoved: "➜", projectileLaunched: "◌", damageApplied: "✕",
  healingApplied: "+", statusApplied: "◇", statusRemoved: "○", attackEvaded: "↝",
  characterSummoned: "♟", characterDefeated: "☠", turnEnded: "■", battleEnded: "★",
  battleLog: "›",
};

function TeamPanel({ side, heroes, activeId }: { side: "friendly" | "enemy"; heroes: Array<CombatantState | null>; activeId: string | null }) {
  return (
    <aside className={`team-panel ${side}`} aria-label={`${side === "friendly" ? "Your" : "Enemy"} team`}>
      <header><span>{side === "friendly" ? "◈" : "◆"}</span>{side === "friendly" ? "YOUR TEAM" : "ENEMY TEAM"}<small>{heroes.filter(Boolean).length}/3</small></header>
      <div className="team-cards">
        {heroes.map((hero, index) => hero ? <HeroCard key={hero.id} hero={hero} active={hero.id === activeId} /> : <div className="empty-slot" key={`empty-${index}`}><span>◇</span><small>OPEN SLOT</small></div>)}
      </div>
      <div className="team-bonus"><strong>TEAM BOND</strong><span>{side === "friendly" ? "☽ +5% Vitality" : "✦ +5% Spell Power"}</span><span>{side === "friendly" ? "✧ +3% Resolve" : "◆ +5% Ward"}</span></div>
    </aside>
  );
}

type TargetEffect = "healing" | "buff" | "debuff";

function targetEffectFor(event: BattleEvent | null, combatantId: string): TargetEffect | null {
  if (!event || event.targetId !== combatantId) return null;
  if (event.type === "healingApplied") return "healing";
  if (event.type === "statusApplied" && (event.statusPresentation === "buff" || event.statusPresentation === "debuff")) {
    return event.statusPresentation;
  }
  return null;
}

function BattlefieldFigure({ hero, active, event, eventSourceSide, selectable, targetSelectionPending, selected, onSelect }: {
  hero: CombatantState; active: boolean; event: BattleEvent | null; eventSourceSide: SideId | null;
  selectable: boolean; targetSelectionPending: boolean; selected: boolean; onSelect: () => void;
}) {
  const eventTarget = event?.targetId === hero.id;
  const moved = event?.type === "characterMoved" && event.sourceId === hero.id;
  const effect = eventTarget || moved ? event?.type ?? null : null;
  const targetEffect = targetEffectFor(event, hero.id);
  const movementClass = moved && event?.movement === "lunge"
    ? `movement-lunge lunge-${hero.sideId}`
    : moved && event?.movement ? `movement-${event.movement}` : "";
  const evadeClass = event?.type === "attackEvaded" && eventTarget && eventSourceSide
    ? `evade-${eventSourceSide}` : "";
  const assetKey = hero.definitionId;
  return (
    <div
      className={`battle-figure slot-${hero.slot} ${hero.sideId} ${active ? "acting" : ""} ${effect ? `fx-${effect}` : ""} ${movementClass} ${evadeClass} ${selectable ? "selectable" : ""} ${selected ? "targeted" : ""}`}
      data-combatant-id={hero.id}
      data-figure-footprint="shared"
    >
      <div className="overhead">
        <Meter value={hero.hp.current} maximum={hero.hp.maximum} kind="hp" label={`${hero.displayName} health`} />
        <div className="battlefield-statuses">{hero.statuses.map((status) => <StatusIcon key={status.instanceId} status={status} />)}</div>
      </div>
      <button className={`battle-target-control ${targetSelectionPending ? "target-selection-pending" : ""}`} type="button" disabled={!selectable} onClick={onSelect}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            onSelect();
          }
        }}
        aria-label={`${hero.displayName}${selectable ? ", selectable target" : ""}`}>
        <span className="figure-footprint">
          <span className="figure-aura" />
          <AssetImage request={{ kind: "figure", key: assetKey, name: hero.displayName, className: hero.faculty }} className="figure-art" />
          {targetEffect && <span className={`target-effect effect-${targetEffect} ${targetEffect === "debuff" ? "red" : targetEffect === "buff" ? "blue" : "green"}`} data-effect-target={hero.id} aria-hidden="true" />}
        </span>
        <span className="figure-name">{hero.displayName}</span>
        {effect === "damageApplied" && eventTarget && event?.amount !== undefined && <span className="combat-text damage">−{event.amount}</span>}
        {effect === "healingApplied" && eventTarget && event?.amount !== undefined && <span className="combat-text heal">+{event.amount}</span>}
        {effect === "attackEvaded" && <span className="combat-text evade">EVADE</span>}
      </button>
    </div>
  );
}

interface BattleScreenProps {
  provider: BattleProvider;
  mockDemos?: ReadonlyArray<{ id: string; label: string; run: () => Promise<PresentationScript> }>;
  mode?: "live" | "mock";
  backgroundImage?: string;
  entryCountdownStepMs?: number;
  onReturnToBuilder?: () => void;
}

type EntryCountdown = 3 | 2 | 1 | "start" | null;

export function BattleScreen({ provider, mockDemos, mode = "mock", backgroundImage, entryCountdownStepMs, onReturnToBuilder }: BattleScreenProps) {
  const mountedBackground = backgroundImage ?? BATTLE_BACKGROUND;
  const { snapshot, revision, activeEvent, log, setLog, speed, setSpeed, isPlaying, isOpening, hasPendingOpening, canSkip, error, errorKind, present, playOpening, skip, retry } = usePresentationQueue(provider);
  const [entryCountdown, setEntryCountdown] = useState<EntryCountdown>(entryCountdownStepMs === undefined ? null : 3);
  const [selectedSkill, setSelectedSkill] = useState<string | null>(null);
  const [selectedTargets, setSelectedTargets] = useState<string[]>([]);
  const [autoBattle, setAutoBattle] = useState(false);
  const [fullscreenError, setFullscreenError] = useState<string | null>(null);
  const logListRef = useRef<HTMLOListElement>(null);
  const completionButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!snapshot || entryCountdown === null || entryCountdownStepMs === undefined) return;
    const next: EntryCountdown = entryCountdown === 3 ? 2 : entryCountdown === 2 ? 1 : entryCountdown === 1 ? "start" : null;
    const timer = window.setTimeout(() => setEntryCountdown(next), entryCountdownStepMs);
    return () => window.clearTimeout(timer);
  }, [entryCountdown, entryCountdownStepMs, snapshot]);

  useEffect(() => {
    if (snapshot && entryCountdown === null && hasPendingOpening) void playOpening();
  }, [entryCountdown, hasPendingOpening, playOpening, snapshot]);

  useEffect(() => {
    const list = logListRef.current;
    if (list) list.scrollTop = list.scrollHeight;
  }, [log.length]);

  useEffect(() => {
    if (snapshot?.phase === "ended" && entryCountdown === null && !isOpening) completionButtonRef.current?.focus();
  }, [entryCountdown, isOpening, snapshot?.phase]);

  const combatants = snapshot?.combatants ?? {};
  const active = snapshot?.activeCombatantId ? combatants[snapshot.activeCombatantId] : null;
  const entryLocked = entryCountdown !== null || isOpening;
  const acceptsCommands = Boolean(
    snapshot
    && !entryLocked
    && !isPlaying
    && snapshot.turnControl.disposition === "playerCommand"
    && snapshot.turnControl.acceptsCommands
    && snapshot.turnControl.actorCombatantId === snapshot.activeCombatantId,
  );
  const legal = acceptsCommands
    ? snapshot?.legalActions.find((action) => action.skillId === selectedSkill)
    : undefined;
  const targetSelectionPending = Boolean(legal && selectedTargets.length < legal.maximumTargets);
  const sideHeroes = (side: "friendly" | "enemy") => {
    const definition = snapshot?.sides.find((item) => item.id === side);
    const items = definition?.combatantIds.map((id) => combatants[id]) ?? [];
    return [...items, ...Array(Math.max(0, (definition?.maxSlots ?? 3) - items.length)).fill(null)] as Array<CombatantState | null>;
  };
  const battlefieldIds = [...new Set(snapshot?.sides.flatMap((side) => side.combatantIds) ?? [])];
  const battlefield = battlefieldIds
    .map((id) => combatants[id])
    .filter((hero): hero is CombatantState => Boolean(hero?.alive));
  const eventSourceSide = activeEvent?.sourceId ? combatants[activeEvent.sourceId]?.sideId ?? null : null;

  if (!snapshot) return <main className="loading-screen" aria-live="polite">
    {error ? <section className={`connection-state ${errorKind ?? "adapter"}`} role="alert"><strong>{errorKind === "disconnected" ? "BATTLE SERVICE OFFLINE" : "BATTLE COULD NOT OPEN"}</strong><p>{error}</p><button onClick={retry}>Retry connection</button></section> : <><span className="loading-rune">◇</span>Opening the battlefield…</>}
  </main>;

  const outcomeLabel = snapshot.outcome?.kind === "victory"
    ? `${snapshot.outcome.winningSideId === "friendly" ? "YOUR TEAM" : "ENEMY TEAM"} VICTORIOUS`
    : snapshot.outcome?.kind === "roundLimit" ? "ROUND LIMIT REACHED" : "BATTLE ENDED IN A DRAW";

  const triggerSkill = () => {
    if (!acceptsCommands || !selectedSkill || !legal || !snapshot.activeCombatantId) return;
    void present(() => provider.submitCommand({
      type: "useSkill",
      commandId: `cmd.${crypto.randomUUID()}`,
      expectedRevision: revision,
      actorId: snapshot.activeCombatantId!,
      skillId: selectedSkill,
      targetIds: selectedTargets,
    }));
    setSelectedSkill(null); setSelectedTargets([]);
  };

  const toggleTarget = (heroId: string) => {
    if (!legal) return;
    setSelectedTargets((current) => {
      if (current.includes(heroId)) return current.filter((id) => id !== heroId);
      if (legal.maximumTargets <= 1) return [heroId];
      if (current.length >= legal.maximumTargets) return current;
      return [...current, heroId];
    });
  };

  const toggleFullscreen = async () => {
    setFullscreenError(null);
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await document.documentElement.requestFullscreen();
    } catch {
      setFullscreenError("Fullscreen is unavailable in this browser.");
    }
  };

  return (
    <main className={`battle-shell format-${getBattleFormat(snapshot)}`} data-format={getBattleFormat(snapshot)}>
      <header className="battle-header">
        <div className="header-tools"><button aria-label="Open menu">☰</button><button aria-label="Settings">⚙</button></div>
        <div className="side-banner friendly"><span className="crest">L</span><strong>YOUR TEAM</strong><i>READY</i></div>
        <div className="round"><strong>ROUND {snapshot.round}</strong><span>TURN {snapshot.turn.index} / {snapshot.turn.total}</span></div>
        <div className="side-banner enemy"><strong>ENEMY TEAM</strong><i>HOSTILE</i><span className="crest">☠</span></div>
        <div className="header-tools right"><Link href="/assets" aria-label="Open asset gallery">◆</Link><button aria-label="Toggle fullscreen" onClick={() => void toggleFullscreen()}>⛶</button></div>
        <nav className="turn-order" aria-label="Turn order">
          {snapshot.turnOrder.map((turn, index) => {
            const hero = combatants[turn.combatantId];
            return <span className={`${turn.isCurrent ? "current" : ""} ${turn.hasActed ? "acted" : ""}`} key={turn.combatantId}><AssetImage request={{ kind: "thumbnail", key: hero.definitionId, name: hero.displayName, className: hero.faculty }} /><b>{index + 1}</b><small>{hero.displayName}</small></span>;
          })}
        </nav>
      </header>

      <section className="battle-layout">
        <TeamPanel side="friendly" heroes={sideHeroes("friendly")} activeId={snapshot.activeCombatantId} />
        <section
          className={`battlefield ${activeEvent ? "event-active" : ""}`}
          aria-label="Battlefield"
          data-background={mountedBackground}
          style={{ "--battle-background-image": `url("${mountedBackground}")` } as CSSProperties}
        >
          {(activeEvent?.effectHint === "magic" || activeEvent?.effectHint === "summon")
            && <div className={`effect-layer ${activeEvent.effectHint}`} aria-hidden="true"><span /></div>}
          {battlefield.map((hero) => {
            const position = formationFor(snapshot, hero.sideId, hero.slot);
            return <div className="formation-slot" key={hero.id} data-slot={position.slot} style={{ left: `${position.x}%`, top: `${position.y}%`, "--figure-scale": position.scale } as CSSProperties}>
            <BattlefieldFigure hero={hero} active={hero.id === snapshot.activeCombatantId}
              event={activeEvent} eventSourceSide={eventSourceSide}
              selectable={acceptsCommands && Boolean(legal?.validTargetIds.includes(hero.id)) && !isPlaying}
              targetSelectionPending={acceptsCommands && Boolean(legal?.validTargetIds.includes(hero.id)) && !isPlaying && targetSelectionPending}
              selected={selectedTargets.includes(hero.id)}
              onSelect={() => toggleTarget(hero.id)} />
            </div>;
          })}
          <div className="battlefield-caption"><span>THE FALLEN CITADEL</span><small>{getBattleFormat(snapshot).toUpperCase()} FORMATION</small></div>
        </section>
        <TeamPanel side="enemy" heroes={sideHeroes("enemy")} activeId={snapshot.activeCombatantId} />
      </section>

      <section className="command-deck">
        {active
          ? <div className="acting-card"><AssetImage request={{ kind: "portrait", key: active.definitionId, name: active.displayName, className: active.faculty }} className="portrait" /><div><small>ACTING HERO</small><h2>{active.displayName}</h2><p>{active.faculty} · {active.specialization}</p><span className="turn-intent">{
            snapshot.turnControl.disposition === "skip"
              ? "ACTION RESTRICTED · TURN SKIPPED"
              : isPlaying && activeEvent
                ? "RESOLVING AUTHORITATIVE ACTION"
                : acceptsCommands
                ? selectedSkill
                  ? `READYING ${active.skills.find((skill) => skill.id === selectedSkill)?.displayName}`
                  : "CHOOSE AN AUTHORIZED SKILL"
                : snapshot.turnControl.disposition === "automaticAction"
                    ? "ACTION RESOLVING AUTOMATICALLY"
                    : "PLAYER COMMANDS UNAVAILABLE"
          }</span></div></div>
          : <div className="acting-card battle-ended" role="status"><div className="ended-crest">◇</div><div><small>BATTLE COMPLETE</small><h2>{outcomeLabel}</h2><p>The final board reflects the authoritative Python result.</p><span className="turn-intent">NO FURTHER COMMANDS ARE LEGAL</span></div></div>}
        <div className="skills" aria-label="Skills">
          {active?.skills.map((item) => (
            <SkillCard key={item.id} skill={item} selected={selectedSkill === item.id}
              legal={acceptsCommands && snapshot.legalActions.some((action) => action.skillId === item.id)}
              disabled={isPlaying || !acceptsCommands} onSelect={() => { setSelectedSkill(item.id); setSelectedTargets([]); }} />
          ))}
        </div>
        <div className="battle-log">
          <header><strong>BATTLE LOG</strong><button disabled={entryLocked} onClick={() => setLog([])}>Clear</button></header>
          <ol ref={logListRef} aria-live="polite" aria-label="Battle events">
            {log.map((item, index) => <li className={item.type} key={`${item.id}.${index}`}><span>{logGlyph[item.type]}</span>{item.message}</li>)}
          </ol>
        </div>
      </section>

      <footer className="battle-controls">
        <div className="speed"><span>SPEED</span>{[1, 1.5, 2].map((value) => <button className={speed === value ? "selected" : ""} disabled={entryLocked} key={value} onClick={() => setSpeed(value)}>×{value}</button>)}</div>
        {mockDemos && <div className="demo-controls" aria-label="Mock presentation demos">
          <span>MOCK EVENT DEMOS</span>{mockDemos.map((demo) => <button key={demo.id} disabled={isPlaying || entryLocked} onClick={() => void present(demo.run)}>{demo.label}</button>)}
        </div>}
        <label className="toggle">AUTO BATTLE <input type="checkbox" checked={autoBattle} disabled={entryLocked || isPlaying} onChange={(event) => setAutoBattle(event.target.checked)} /><span /></label>
        {!active ? <button className="end-turn" disabled>BATTLE ENDED</button> : isPlaying ? <button className="end-turn" onClick={skip} disabled={!canSkip || isOpening}>{isOpening ? "OPENING BATTLE…" : canSkip ? "SKIP EFFECT" : "RESOLVING…"}</button> : !acceptsCommands ? <button className="end-turn" disabled>{entryLocked ? "BATTLE OPENING" : "AUTOMATIC TURN"}</button> : <button className="end-turn" onClick={triggerSkill} disabled={!selectedSkill || !legal || selectedTargets.length < legal.minimumTargets || selectedTargets.length > legal.maximumTargets}>{selectedSkill ? "CAST SKILL" : "SELECT SKILL"}</button>}
      </footer>
      {(error || fullscreenError) && <div className={`ui-error ${errorKind ?? ""}`} role="alert"><strong>{errorKind === "stale" ? "STATE RECONCILED" : errorKind === "rejected" ? "COMMAND REJECTED" : "BATTLE NOTICE"}</strong><span>{error ?? fullscreenError}</span></div>}
      {entryCountdown !== null && (
        <div className="battle-entry-countdown" data-countdown-step={entryCountdown}>
          <section
            key={entryCountdown}
            className={`entry-countdown-value ${entryCountdown === "start" ? "start" : "numeric"}`}
            role="status"
            aria-live="assertive"
            aria-atomic="true"
            aria-label={entryCountdown === "start" ? "Battle start" : `Battle begins in ${entryCountdown}`}
          >
            {entryCountdown === "start" ? "START" : entryCountdown}
          </section>
        </div>
      )}
      {snapshot.phase === "ended" && !entryLocked && onReturnToBuilder && (
        <div className="completion-backdrop">
          <section className="completion-dialog" role="dialog" aria-modal="true" aria-labelledby="battle-result-title"
            onKeyDown={(event) => {
              if (event.key === "Tab") {
                event.preventDefault();
                completionButtonRef.current?.focus();
              }
            }}>
            <span className="completion-crest" aria-hidden="true">★</span>
            <small>BATTLE COMPLETE</small>
            <h2 id="battle-result-title">{outcomeLabel}</h2>
            <p>The Python battle engine has declared the final result.</p>
            <button ref={completionButtonRef} type="button" onClick={onReturnToBuilder}>RETURN TO TEAM BUILDER</button>
          </section>
        </div>
      )}
      {mode === "mock" && <p className="fixture-note">FIXTURE PREVIEW · Outcomes are scripted; Python remains gameplay authority.</p>}
    </main>
  );
}
