"use client";

/* eslint-disable @next/next/no-img-element -- the manual uses audited local capture/status assets at their native paths */

import Link from "next/link";
import { useEffect, useRef, useState, type CSSProperties, type KeyboardEvent } from "react";
import { battleInstructionContent } from "@/lib/manual/battleInstructionContent";
import { skillPresentation, statusRegistry } from "@/lib/battle/assets";
import { duoFormationRegistry, formationRegistry, trioFormationRegistry, type FormationPosition } from "@/lib/battle/formations";
import {
  fetchFormationDemonstration,
  type FormationDemonstrationAttackType,
  type FormationDemonstrationCatalogue,
  type FormationDemonstrationFormation,
  type FormationDemonstrationId,
  type FormationDemonstrationTarget,
} from "@/lib/manual/formationDemonstration";
import type { SideId } from "@/lib/battle/types";
import type { BattleInstructionChapter, BattleInstructionChapterId, BattleInstructionItem } from "@/lib/manual/battleInstructionContentTypes";

type Props = { embedded?: boolean; onBackToManual?: () => void };

const FORMATS = [
  { size: "1v1", cap: 9, formations: ["No formation choice", "Front"] },
  { size: "2v2", cap: 13, formations: ["Front & Rear", "Side by Side"] },
  { size: "3v3", cap: 15, formations: ["One Front, Two Rear", "Two Front, One Rear", "All Front"] },
] as const;
const DUEL_FORMATION = { label: "1v1 · Duel", size: "duel", layout: formationRegistry.duel } as const;
const DEMONSTRATION_FORMATIONS = [
  { id: "front-rear", label: "2v2 · Front & Rear", shortLabel: "Front & Rear", size: "duo", layout: duoFormationRegistry["front-rear"] },
  { id: "side-by-side", label: "2v2 · Side by Side", shortLabel: "Side by Side", size: "duo", layout: duoFormationRegistry["side-by-side"] },
  { id: "one-front-two-rear", label: "3v3 · One Front, Two Rear", shortLabel: "One Front, Two Rear", size: "trio", layout: trioFormationRegistry["one-front-two-rear"] },
  { id: "two-front-one-rear", label: "3v3 · Two Front, One Rear", shortLabel: "Two Front, One Rear", size: "trio", layout: trioFormationRegistry["two-front-one-rear"] },
  { id: "all-front", label: "3v3 · All Front", shortLabel: "All Front", size: "trio", layout: trioFormationRegistry["all-front"] },
] as const;
const ATTACK_TYPES = [
  { id: "melee", title: "Melee" },
  { id: "rangedProjectile", title: "Ranged Projectile" },
  { id: "rangedInstant", title: "Ranged Instant" },
] as const;
const EFFECT_EXAMPLES: Record<string, readonly [string, string, string]> = {
  buffs: ["status.wrath_of_crusader", "skill.paladin.wrath_of_crusader", "⚔"],
  debuffs: ["status.shadow_word_pain", "skill.priest.shadow_word_pain", "☾"],
  control: ["status.stunned", "skill.warrior.shield_bash", "✹"],
  periodic: ["status.holy_aura", "skill.paladin.holy_aura", "✦"],
  casting: ["status.holy_word_punishment", "skill.priest.holy_word_punishment", "☀"],
  cooldowns: ["status.shadow_evasion", "skill.rogue.shadow_evasion", "◐"],
};

function diagramSlotDescription(slots: FormationPosition[]) {
  const heights = [...new Set(slots.map((slot) => slot.y))].sort((a, b) => a - b);
  const distances = [...new Set(slots.map((slot) => Math.abs(slot.x - 50)))].sort((a, b) => a - b);
  return slots.map((slot, index) => {
    const vertical = heights.length < 2 ? "" : slot.y === heights[0] ? "upper" : slot.y === heights[heights.length - 1] ? "lower" : "middle";
    const horizontal = distances.length < 2 ? "" : Math.abs(slot.x - 50) === distances[0] ? "near centre" : "farther out";
    const placement = [vertical, horizontal].filter(Boolean).join(", ");
    return `Hero ${index + 1} ${slot.slot === "rear" ? "Rear" : "Front"}${placement ? ` (${placement})` : ""}`;
  }).join(", ");
}

function FormationSlot({ side, slot, position }: { side: SideId; slot: number; position: FormationPosition }) {
  // Spread the battle registry's x/y coordinates into a compact Manual board without changing their relative order.
  const x = 50 + (position.x - 50) * 1.4;
  const y = 20 + ((position.y - 52) / 38) * 60;
  return <div className="instruction-formation-slot" data-side={side} data-slot={slot} data-position={position.slot} style={{ left: `${x}%`, top: `${y}%` }}>
    <i className={side === "enemy" ? "enemy" : undefined} aria-hidden="true">{slot}</i><small>{position.slot === "rear" ? "Rear" : "Front"}</small>
  </div>;
}

function FormationDiagram({ label, layout }: typeof DUEL_FORMATION) {
  return <article className="instruction-formation-card"><h3>{label}</h3>
    <p className="instruction-formation-note">No formation choice</p>
    <div className="instruction-formation-board instruction-team-diagram formation-map formation-map--duel" role="img" aria-label={`${label}: Friendly ${diagramSlotDescription(layout.friendly)} versus Enemy ${diagramSlotDescription(layout.enemy)}; no formation choice`}>
      {layout.friendly.map((position, index) => <FormationSlot key={`friendly-${index}`} side="friendly" slot={index + 1} position={position} />)}
      <b className="instruction-formation-vs" aria-hidden="true">VS</b>
      {layout.enemy.map((position, index) => <FormationSlot key={`enemy-${index}`} side="enemy" slot={index + 1} position={position} />)}
    </div>
  </article>;
}

function demonstrationPosition(position: FormationPosition): CSSProperties {
  const y = 18 + ((position.y - 52) / 38) * 64;
  return { left: `${position.x}%`, top: `${y}%` };
}

function targetResultLabel(result: FormationDemonstrationTarget) {
  if (result.reason === "defeated") return "Defeated";
  if (result.reason === "protectedByFrontLine") return "Protected by front line";
  return `${result.multiplierPercent}% damage`;
}

function DemonstrationBoard({
  formation,
  layout,
  attackerSlot,
  evaluation,
  onSelectAttacker,
}: {
  formation: FormationDemonstrationFormation;
  layout: (typeof DEMONSTRATION_FORMATIONS)[number]["layout"];
  attackerSlot: number;
  evaluation: FormationDemonstrationFormation["evaluations"][number] | undefined;
  onSelectAttacker: (slot: number) => void;
}) {
  const targets = formation.enemySlots.map((slot) => evaluation?.targets.find((target) => target.targetSlot === slot.slot)).filter((target): target is FormationDemonstrationTarget => Boolean(target));
  return <><div className={`instruction-formation-board instruction-team-diagram instruction-demo-board${formation.battleSize === 3 ? " is-trio" : ""}`} aria-label="Interactive formation demonstration">
    {formation.friendlySlots.map((slot) => {
      const position = layout.friendly[slot.slot - 1];
      if (!position) return null;
      const selected = attackerSlot === slot.slot;
      return <button
        className={`instruction-demo-slot friendly${selected ? " is-attacker" : ""}`}
        data-side="friendly"
        data-slot={slot.slot}
        data-position={slot.position}
        key={`friendly-${slot.slot}`}
        type="button"
        aria-pressed={selected}
        aria-label={`Friendly Hero ${slot.slot}, ${slot.position}, ${selected ? "selected attacker" : "select as attacker"}`}
        style={demonstrationPosition(position)}
        onClick={() => onSelectAttacker(slot.slot)}
      >
        <i aria-hidden="true">{slot.slot}</i>
        <small>{slot.position === "rear" ? "Rear" : "Front"}</small>
        <strong>{selected ? "Attacker" : "Select"}</strong>
      </button>;
    })}
    <b className="instruction-formation-vs" aria-hidden="true">VS</b>
    {formation.enemySlots.map((slot) => {
      const position = layout.enemy[slot.slot - 1];
      const result = evaluation?.targets.find((target) => target.targetSlot === slot.slot);
      if (!position || !result) return null;
      const label = targetResultLabel(result);
      return <div
        className={`instruction-demo-slot enemy is-${result.reason}${result.eligible && result.multiplierPercent !== 100 ? " is-reduced" : ""}`}
        data-side="enemy"
        data-slot={slot.slot}
        data-position={slot.position}
        key={`enemy-${slot.slot}`}
        style={demonstrationPosition(position)}
        aria-label={`Enemy Hero ${slot.slot}, ${slot.position}: ${label}`}
      >
        <i className="enemy" aria-hidden="true">{slot.slot}</i>
        <small>{slot.position === "rear" ? "Rear" : "Front"}</small>
        <strong className="instruction-demo-state-symbol" aria-hidden="true">{result.reason === "eligible" ? "✓" : result.reason === "protectedByFrontLine" ? "×" : "—"}</strong>
      </div>;
    })}
  </div>
  <div className="instruction-demo-results" aria-label="Enemy target results">{targets.map((result) => <div className={`instruction-demo-result is-${result.reason}${result.eligible && result.multiplierPercent !== 100 ? " is-reduced" : ""}`} key={result.targetSlot}>
    <strong>Enemy Hero {result.targetSlot}</strong><small>{result.targetPosition === "rear" ? "Rear" : "Front"}</small><span><b aria-hidden="true">{result.reason === "eligible" ? "✓" : result.reason === "protectedByFrontLine" ? "×" : "—"}</b>{targetResultLabel(result)}</span>
  </div>)}</div></>;
}

function QuickStart({ chapter }: { chapter: BattleInstructionChapter }) {
  return <><div className="instruction-command-flow" aria-label="Battle command walkthrough">
    {chapter.steps?.map((step, index) => <article key={step.title}><span>{index + 1}</span><div><h3>{step.title}</h3><p>{step.text}</p></div></article>)}
  </div>{chapter.callout && <aside className="instruction-callout"><strong>Remember</strong><p>{chapter.callout}</p></aside>}</>;
}

function BattleFormats() {
  return <div className="instruction-format-grid">{FORMATS.map((format) => <article key={format.size}>
    <header><strong>{format.size}</strong></header>
    <div className="instruction-team-diagram" aria-hidden="true">{Array.from({ length: Number(format.size[0]) }, (_, index) => <i key={`f-${index}`}>L</i>)}<b>VS</b>{Array.from({ length: Number(format.size[0]) }, (_, index) => <i className="enemy" key={`e-${index}`}>E</i>)}</div>
    <dl className="instruction-format-facts">
      <div><dt>Battle Formation Options</dt><dd>{format.formations.map((formation) => <span key={formation}>{formation}</span>)}</dd></div>
      <div><dt>Maximum Battle Rounds</dt><dd><strong>{format.cap}</strong></dd></div>
    </dl>
  </article>)}</div>;
}

function Formations({ chapter }: { chapter: BattleInstructionChapter }) {
  const [catalogue, setCatalogue] = useState<FormationDemonstrationCatalogue | null>(null);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const [formationId, setFormationId] = useState<FormationDemonstrationId>("front-rear");
  const [attackerSlot, setAttackerSlot] = useState(1);
  const [attackType, setAttackType] = useState<FormationDemonstrationAttackType>("melee");
  const [enemyFrontDefeated, setEnemyFrontDefeated] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    fetchFormationDemonstration(controller.signal).then(setCatalogue).catch((reason: unknown) => {
      if (reason instanceof DOMException && reason.name === "AbortError") return;
      setError(reason instanceof Error ? reason.message : "Formation demonstration is unavailable.");
    });
    return () => controller.abort();
  }, [retry]);

  const formationOption = DEMONSTRATION_FORMATIONS.find((item) => item.id === formationId)!;
  const formation = catalogue?.formations.find((item) => item.id === formationId);
  const evaluation = formation?.evaluations.find((item) => item.attackerSlot === attackerSlot
    && item.attackType === attackType
    && item.enemyFrontDefeated === enemyFrontDefeated);

  function selectFormation(nextId: FormationDemonstrationId) {
    const next = catalogue?.formations.find((item) => item.id === nextId);
    setFormationId(nextId);
    setEnemyFrontDefeated(false);
    if (!next?.friendlySlots.some((slot) => slot.slot === attackerSlot)) {
      setAttackerSlot(next?.friendlySlots.find((slot) => slot.position === "front")?.slot ?? 1);
    }
  }

  return <><section className="instruction-duel-reference" aria-label="1v1 formation reference"><FormationDiagram {...DUEL_FORMATION} /></section>
    <section className="instruction-formation-demo" aria-labelledby="instruction-demo-title">
      <header><div><h3 id="instruction-demo-title">2v2 &amp; 3v3 Battle Formation</h3><p>Select a blue hero, then choose an attack type.</p></div></header>
      <fieldset className="instruction-demo-control instruction-demo-formations"><legend>Formation</legend>{DEMONSTRATION_FORMATIONS.map((item) => <button key={item.id} type="button" aria-pressed={formationId === item.id} onClick={() => selectFormation(item.id)}><span>{item.size === "duo" ? "2v2" : "3v3"}</span>{item.shortLabel}</button>)}</fieldset>
      <fieldset className="instruction-demo-control instruction-demo-attacks"><legend>Attack type</legend>{ATTACK_TYPES.map((item) => <button key={item.id} type="button" aria-pressed={attackType === item.id} onClick={() => setAttackType(item.id)}>{item.title}</button>)}</fieldset>
      {!catalogue && !error && <div className="instruction-demo-message" role="status">Loading authoritative formation rules…</div>}
      {error && <div className="instruction-demo-message is-error" role="alert"><p>{error}</p><button type="button" onClick={() => { setError(""); setCatalogue(null); setRetry((value) => value + 1); }}>Retry</button></div>}
      {formation && <>
        <div className="instruction-demo-heading"><h3>{formationOption.label}</h3>{formation.hasRearEnemies && <label className="instruction-demo-switch"><input type="checkbox" role="switch" checked={enemyFrontDefeated} onChange={(event) => setEnemyFrontDefeated(event.target.checked)} /><span>Enemy front line defeated</span></label>}</div>
        <DemonstrationBoard formation={formation} layout={formationOption.layout} attackerSlot={attackerSlot} evaluation={evaluation} onSelectAttacker={setAttackerSlot} />
        <p className="sr-only" aria-live="polite">{evaluation ? evaluation.targets.map((target) => `Enemy Hero ${target.targetSlot}: ${targetResultLabel(target)}`).join(". ") : "Authoritative target results unavailable."}</p>
        <p className="instruction-demo-explanation" aria-live="polite">{evaluation?.explanation ?? "Authoritative formation result unavailable for this selection."}</p>
      </>}
    </section>
    <section className="instruction-rule-separation" aria-label="Formation rule boundaries">
      <article><strong>1 · Legal target?</strong><p>{chapter.legalTargeting}</p></article>
      <article><strong>2 · Position damage?</strong><p>{chapter.positionDamage}</p></article>
      <article><strong>3 · Does it hit?</strong><p>{chapter.hitChance}</p></article>
    </section>
    <p className="instruction-fine-print">{chapter.otherEffects}</p></>;
}

function BattleInterface({ chapter }: { chapter: BattleInstructionChapter }) {
  const [marker, setMarker] = useState(0);
  const [screenshotFailed, setScreenshotFailed] = useState(false);
  const markers = chapter.markers ?? [];
  return <div className="instruction-interface-guide"><div className={`instruction-battle-reference${screenshotFailed ? " is-schematic" : ""}`}>
    {!screenshotFailed && <img src="/game-images/manual/Battle_Instruction_Interface.png" alt="Current battle screen showing its principal controls" onError={() => setScreenshotFailed(true)} />}
    {screenshotFailed && <div className="instruction-battle-schematic" role="img" aria-label="Battle screen layout schematic"><span className="top">ROUND · TURN ORDER</span><span className="left">YOUR TEAM · HERO STATS</span><span className="field">BATTLEFIELD TARGETS · TARGET PREVIEW</span><span className="right">ENEMY TEAM</span><span className="acting">ACTING HERO</span><span className="skills">SKILL CARDS</span><span className="log">BATTLE LOG</span><span className="controls">BATTLE SPEED · COMMAND · RESIGN</span></div>}
    <small>{screenshotFailed ? "Battle screen guide · layout schematic" : "Battle screen guide · current game capture"}</small>
    {markers.map((item, index) => <button key={item.title} type="button" className={`instruction-marker marker-${index + 1}`} aria-label={`${index + 1}. ${item.title}`} aria-pressed={marker === index} onClick={() => setMarker(index)}>{index + 1}</button>)}
  </div>
  {markers[marker] && <article className="instruction-marker-detail" aria-live="polite"><span>{marker + 1}</span><div><h3>{markers[marker].title}</h3><p>{markers[marker].text}</p></div></article>}
  <div className="instruction-marker-list" aria-label="Battle interface regions">{markers.map((item, index) => <button key={item.title} type="button" aria-pressed={marker === index} onClick={() => setMarker(index)}><span>{index + 1}</span>{item.title}</button>)}</div></div>;
}

function TurnsVictory({ chapter }: { chapter: BattleInstructionChapter }) {
  return <><div className="instruction-turn-grid"><article><span>TURN</span><h3>One hero acts</h3><p>Choose and resolve one available action for the acting hero.</p></article><article><span>ROUND</span><h3>Eligible heroes act</h3><p>A full round completes after its eligible living heroes finish their turns.</p></article></div>
    <aside className="instruction-callout"><strong>Live Agility order</strong><p>{chapter.agility}</p></aside>
    <section className="instruction-timeout-order"><h3>Victory and timeout order</h3><ol><li>Elimination</li><li>Living hero count</li><li>Exact average living-hero HP percentage</li><li>Exact equality → Draw</li></ol><p>{chapter.victory}</p></section>
    <article className="instruction-worked-example"><span>Worked example</span><p>{chapter.example}</p><div><strong>Gold: 45 ÷ 100 = 45%</strong><strong>Crimson: 70 ÷ 200 = 35%</strong></div></article></>;
}

function EffectCard({ item }: { item: BattleInstructionItem }) {
  const example = item.id ? EFFECT_EXAMPLES[item.id] : undefined;
  const definition = example ? statusRegistry[example[0]] : undefined;
  const asset = definition?.asset ?? (example ? skillPresentation[example[1]]?.asset : undefined);
  return <article className="instruction-effect-card"><span className={definition?.harmful ? "harmful" : "helpful"}>{asset ? <img src={asset} alt="" /> : definition?.glyph ?? example?.[2] ?? "◆"}</span><div><h3>{item.title}</h3><p>{item.text}</p></div></article>;
}

function EffectsTactics({ chapter, embedded, onBackToManual }: { chapter: BattleInstructionChapter; embedded: boolean; onBackToManual?: () => void }) {
  return <><div className="instruction-effect-grid">{chapter.effects?.map((item) => <EffectCard key={item.id ?? item.title} item={item} />)}</div>
    <section className="instruction-scenario-grid">{chapter.scenarios?.map((item) => <article key={item.title}><h3>{item.title}</h3><p>{item.text}</p><small>Practical advice · outcomes depend on the battle</small></article>)}</section>
    <aside className="instruction-gallery-link"><div><strong>Need an individual skill?</strong><p>Hero Gallery lists each approved hero&apos;s skills, target style, cooldowns, and audited reference facts.</p></div>{embedded ? <button type="button" onClick={onBackToManual}>Back to Manual → Hero Gallery</button> : <Link href="/manual/heroes">Open Hero Gallery</Link>}</aside></>;
}

function ChapterBody({ chapter, embedded, onBackToManual }: { chapter: BattleInstructionChapter; embedded: boolean; onBackToManual?: () => void }) {
  if (chapter.id === "quick-start") return <QuickStart chapter={chapter} />;
  if (chapter.id === "battle-formats") return <BattleFormats />;
  if (chapter.id === "formations") return <Formations chapter={chapter} />;
  if (chapter.id === "interface") return <BattleInterface chapter={chapter} />;
  if (chapter.id === "turns-victory") return <TurnsVictory chapter={chapter} />;
  return <EffectsTactics chapter={chapter} embedded={embedded} onBackToManual={onBackToManual} />;
}

export function BattleInstructionExperience({ embedded = false, onBackToManual }: Props) {
  const chapters = battleInstructionContent.chapters;
  const [chapterId, setChapterId] = useState<BattleInstructionChapterId>(chapters[0].id);
  const headingRef = useRef<HTMLHeadingElement>(null);
  const index = chapters.findIndex((chapter) => chapter.id === chapterId);
  const chapter = chapters[index];
  function selectChapter(next: BattleInstructionChapterId, focusHeading = true) {
    setChapterId(next);
    window.requestAnimationFrame(() => {
      const reader = document.querySelector<HTMLElement>(".instruction-reader");
      if (typeof reader?.scrollTo === "function") reader.scrollTo({ top: 0 });
      if (focusHeading) headingRef.current?.focus();
    });
  }
  function onTabKeyDown(event: KeyboardEvent<HTMLButtonElement>, tabIndex: number) {
    const delta = event.key === "ArrowDown" || event.key === "ArrowRight" ? 1 : event.key === "ArrowUp" || event.key === "ArrowLeft" ? -1 : 0;
    const target = event.key === "Home" ? 0 : event.key === "End" ? chapters.length - 1 : delta ? (tabIndex + delta + chapters.length) % chapters.length : -1;
    if (target < 0) return;
    event.preventDefault(); selectChapter(chapters[target].id, false); document.querySelector<HTMLButtonElement>(`#instruction-tab-${chapters[target].id}`)?.focus();
  }
  return <main className={`manual-page instruction-page${embedded ? " manual-page-embedded" : ""}`}>
    <header className="instruction-header">{embedded ? <button type="button" className="manual-back" data-manual-back onClick={onBackToManual}>← Back to Manual</button> : <Link className="manual-back" href="/stages?manual=open">← Back to Manual</Link>}
      <h1>{battleInstructionContent.title}</h1><p>{battleInstructionContent.subtitle}</p></header>
    <div className="instruction-mobile-select"><label htmlFor="instruction-chapter-select">Chapter</label><select id="instruction-chapter-select" value={chapterId} onChange={(event) => selectChapter(event.target.value as BattleInstructionChapterId)}>{chapters.map((item, chapterIndex) => <option key={item.id} value={item.id}>{chapterIndex + 1}. {item.title}</option>)}</select></div>
    <div className="instruction-compendium"><nav className="instruction-chapters" aria-label="Battle Instruction chapters" role="tablist" aria-orientation="vertical">{chapters.map((item, chapterIndex) => <button id={`instruction-tab-${item.id}`} key={item.id} role="tab" type="button" aria-selected={chapterId === item.id} aria-controls="instruction-chapter-panel" tabIndex={chapterId === item.id ? 0 : -1} onClick={() => selectChapter(item.id)} onKeyDown={(event) => onTabKeyDown(event, chapterIndex)}><span>{String(chapterIndex + 1).padStart(2, "0")}</span>{item.title}</button>)}</nav>
      <section className="instruction-reader" id="instruction-chapter-panel" role="tabpanel" aria-labelledby={`instruction-tab-${chapter.id}`}><div className="instruction-chapter-heading"><small>CHAPTER {String(index + 1).padStart(2, "0")} · {chapter.kicker}</small><h2 ref={headingRef} tabIndex={-1}>{chapter.title}</h2>{chapter.introduction && <p>{chapter.introduction}</p>}</div>
        <ChapterBody chapter={chapter} embedded={embedded} onBackToManual={onBackToManual} />
        <footer className="instruction-pagination"><button type="button" disabled={index === 0} onClick={() => selectChapter(chapters[index - 1].id)}>← Previous Chapter</button><span>{index + 1} / {chapters.length}</span><button type="button" disabled={index === chapters.length - 1} onClick={() => selectChapter(chapters[index + 1].id)}>Next Chapter →</button></footer>
      </section></div>
  </main>;
}
