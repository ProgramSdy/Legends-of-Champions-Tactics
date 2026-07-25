"use client";

import { useState } from "react";
import Link from "next/link";
import { usePresentationQueue } from "@/lib/battle/usePresentationQueue";
import type { BattleEventType, BattleProvider, CombatantState, PresentationScript } from "@/lib/battle/types";
import { AssetImage } from "./AssetImage";
import { HeroCard, Meter } from "./HeroCard";
import { SkillCard } from "./SkillCard";
import { StatusIcon } from "./StatusIcon";

const logGlyph: Record<BattleEventType, string> = {
  battleStarted: "◆", roundStarted: "◎", turnStarted: "▶", skillStarted: "✦",
  characterMoved: "➜", projectileLaunched: "◌", damageApplied: "✕",
  healingApplied: "+", statusApplied: "◇", statusRemoved: "○", attackEvaded: "↝",
  characterSummoned: "♟", characterDefeated: "☠", turnEnded: "■", battleEnded: "★",
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

function BattlefieldFigure({ hero, active, eventType, eventAmount, eventTarget, showAmount, selectable, selected, onSelect }: {
  hero: CombatantState; active: boolean; eventType: BattleEventType | null; eventAmount?: number; eventTarget: boolean; showAmount: boolean;
  selectable: boolean; selected: boolean; onSelect: () => void;
}) {
  const effect = eventTarget ? eventType : null;
  return (
    <button className={`battle-figure slot-${hero.slot} ${hero.sideId} ${active ? "acting" : ""} ${effect ? `fx-${effect}` : ""} ${selectable ? "selectable" : ""} ${selected ? "targeted" : ""}`}
      onClick={onSelect} disabled={!selectable} aria-label={`${hero.displayName}${selectable ? ", selectable target" : ""}`}>
      <div className="overhead"><Meter value={hero.hp.current} maximum={hero.hp.maximum} kind="hp" label={`${hero.displayName} health`} /><div>{hero.statuses.map((status) => <StatusIcon key={status.instanceId} status={status} />)}</div></div>
      <span className="figure-aura" />
      <AssetImage request={{ kind: "figure", key: hero.id, name: hero.displayName, className: hero.specialization }} className="figure-art" />
      <span className="figure-name">{hero.displayName}</span>
      {effect === "damageApplied" && showAmount && eventAmount !== undefined && <span className="combat-text damage">−{eventAmount}</span>}
      {effect === "healingApplied" && showAmount && eventAmount !== undefined && <span className="combat-text heal">+{eventAmount}</span>}
      {effect === "attackEvaded" && <span className="combat-text evade">EVADE</span>}
    </button>
  );
}

interface BattleScreenProps {
  provider: BattleProvider;
  mockDemos?: ReadonlyArray<{ id: string; label: string; run: () => Promise<PresentationScript> }>;
}

export function BattleScreen({ provider, mockDemos }: BattleScreenProps) {
  const { snapshot, revision, activeEvent, log, setLog, speed, setSpeed, isPlaying, canSkip, error, present, skip } = usePresentationQueue(provider);
  const [selectedSkill, setSelectedSkill] = useState<string | null>(null);
  const [selectedTarget, setSelectedTarget] = useState<string | null>(null);
  const [autoBattle, setAutoBattle] = useState(false);
  const [fullscreenError, setFullscreenError] = useState<string | null>(null);

  const combatants = snapshot?.combatants ?? {};
  const active = snapshot?.activeCombatantId ? combatants[snapshot.activeCombatantId] : null;
  const legal = snapshot?.legalActions.find((action) => action.skillId === selectedSkill);
  const sideHeroes = (side: "friendly" | "enemy") => {
    const definition = snapshot?.sides.find((item) => item.id === side);
    const items = definition?.combatantIds.map((id) => combatants[id]) ?? [];
    return [...items, ...Array(Math.max(0, (definition?.maxSlots ?? 3) - items.length)).fill(null)] as Array<CombatantState | null>;
  };
  const battlefield = Object.values(combatants).filter((hero) => hero.alive);

  if (!snapshot || !active) return <main className="loading-screen">Opening the battlefield…</main>;

  const triggerSkill = () => {
    if (!selectedSkill || !snapshot.activeCombatantId) return;
    const targetIds = selectedTarget ? [selectedTarget] : [];
    void present(() => provider.submitCommand({
      type: "useSkill",
      commandId: `cmd.${crypto.randomUUID()}`,
      expectedRevision: revision,
      actorId: snapshot.activeCombatantId!,
      skillId: selectedSkill,
      targetIds,
    }));
    setSelectedSkill(null); setSelectedTarget(null);
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
    <main className="battle-shell">
      <header className="battle-header">
        <div className="header-tools"><button aria-label="Open menu">☰</button><button aria-label="Settings">⚙</button></div>
        <div className="side-banner friendly"><span className="crest">L</span><strong>YOUR TEAM</strong><i>READY</i></div>
        <div className="round"><strong>ROUND {snapshot.round}</strong><span>TURN {snapshot.turn.index} / {snapshot.turn.total}</span></div>
        <div className="side-banner enemy"><strong>ENEMY TEAM</strong><i>HOSTILE</i><span className="crest">☠</span></div>
        <div className="header-tools right"><Link href="/assets" aria-label="Open asset gallery">◆</Link><button aria-label="Toggle fullscreen" onClick={() => void toggleFullscreen()}>⛶</button></div>
        <nav className="turn-order" aria-label="Turn order">
          {snapshot.turnOrder.map((turn, index) => {
            const hero = combatants[turn.combatantId];
            return <span className={`${turn.isCurrent ? "current" : ""} ${turn.hasActed ? "acted" : ""}`} key={turn.combatantId}><AssetImage request={{ kind: "thumbnail", key: hero.id, name: hero.displayName, className: hero.specialization }} /><b>{index + 1}</b><small>{hero.displayName}</small></span>;
          })}
        </nav>
      </header>

      <section className="battle-layout">
        <TeamPanel side="friendly" heroes={sideHeroes("friendly")} activeId={snapshot.activeCombatantId} />
        <section className={`battlefield ${activeEvent ? "event-active" : ""}`} aria-label="Battlefield">
          <div className="sky-glow" /><div className="moon" /><div className="ruins left" /><div className="ruins right" />
          <div className={`effect-layer ${activeEvent?.effectHint ?? ""}`} aria-hidden="true"><span /></div>
          {battlefield.map((hero) => (
            <BattlefieldFigure key={hero.id} hero={hero} active={hero.id === snapshot.activeCombatantId}
              eventType={activeEvent?.type ?? null} eventAmount={activeEvent?.amount} eventTarget={activeEvent?.targetId === hero.id || activeEvent?.sourceId === hero.id}
              showAmount={activeEvent?.targetId === hero.id}
              selectable={Boolean(legal?.validTargetIds.includes(hero.id)) && !isPlaying} selected={selectedTarget === hero.id}
              onSelect={() => setSelectedTarget(hero.id)} />
          ))}
          <div className="battlefield-caption"><span>THE FALLEN CITADEL</span><small>STAGE 1 · MOCK PROVIDER</small></div>
        </section>
        <TeamPanel side="enemy" heroes={sideHeroes("enemy")} activeId={snapshot.activeCombatantId} />
      </section>

      <section className="command-deck">
        <div className="acting-card"><AssetImage request={{ kind: "portrait", key: active.id, name: active.displayName, className: active.specialization }} className="portrait" /><div><small>ACTING HERO</small><h2>{active.displayName}</h2><p>{active.specialization}</p><span className="focus-pips">◆ ◆ ◇</span></div></div>
        <div className="skills" aria-label="Skills">
          {active.skills.map((item) => (
            <SkillCard key={item.id} skill={item} selected={selectedSkill === item.id}
              legal={snapshot.legalActions.some((action) => action.skillId === item.id)}
              disabled={isPlaying} onSelect={() => { setSelectedSkill(item.id); setSelectedTarget(null); }} />
          ))}
        </div>
        <div className="battle-log">
          <header><strong>BATTLE LOG</strong><button onClick={() => setLog([])}>Clear</button></header>
          <ol aria-live="polite">
            {log.length === 0 && <li className="system"><span>◎</span>Choose a demo or select a skill.</li>}
            {log.map((item, index) => <li className={item.type} key={`${item.id}.${index}`}><span>{logGlyph[item.type]}</span>{item.message}</li>)}
          </ol>
        </div>
      </section>

      <footer className="battle-controls">
        <div className="speed"><span>SPEED</span>{[1, 1.5, 2].map((value) => <button className={speed === value ? "selected" : ""} key={value} onClick={() => setSpeed(value)}>×{value}</button>)}</div>
        {mockDemos && <div className="demo-controls" aria-label="Mock presentation demos">
          <span>MOCK EVENT DEMOS</span>{mockDemos.map((demo) => <button key={demo.id} disabled={isPlaying} onClick={() => void present(demo.run)}>{demo.label}</button>)}
        </div>}
        <label className="toggle">AUTO BATTLE <input type="checkbox" checked={autoBattle} onChange={(event) => setAutoBattle(event.target.checked)} /><span /></label>
        {isPlaying ? <button className="end-turn" onClick={skip} disabled={!canSkip}>{canSkip ? "SKIP EFFECT" : "RESOLVING…"}</button> : <button className="end-turn" onClick={triggerSkill} disabled={!selectedSkill || Boolean(legal && legal.minimumTargets > 0 && !selectedTarget)}>{selectedSkill ? "CAST SKILL" : "END TURN"}</button>}
      </footer>
      {(error || fullscreenError) && <p className="ui-error" role="alert">{error ?? fullscreenError}</p>}
      <p className="fixture-note">MOCK MODE · Values, outcomes, and placeholder focus are fixture data. Python remains gameplay authority.</p>
    </main>
  );
}
