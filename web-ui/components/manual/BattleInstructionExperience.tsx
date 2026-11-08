"use client";

/* eslint-disable @next/next/no-img-element -- the manual uses audited local capture/status assets at their native paths */

import Link from "next/link";
import { useRef, useState, type KeyboardEvent } from "react";
import { battleInstructionContent } from "@/lib/manual/battleInstructionContent";
import { skillPresentation, statusRegistry } from "@/lib/battle/assets";
import { duoFormationRegistry, trioFormationRegistry, type FormationPosition } from "@/lib/battle/formations";
import type { SideId } from "@/lib/battle/types";
import type { BattleInstructionChapter, BattleInstructionChapterId, BattleInstructionItem } from "@/lib/manual/battleInstructionContentTypes";

type Props = { embedded?: boolean; onBackToManual?: () => void };

const FORMATS = [
  { size: "1v1", cap: 9, formations: "Duel — no formation choice", slots: ["Front"] },
  { size: "2v2", cap: 13, formations: "2 formations", slots: ["Front & Rear", "Side by Side"] },
  { size: "3v3", cap: 15, formations: "3 formations", slots: ["One Front, Two Rear", "Two Front, One Rear", "All Front"] },
] as const;
const FORMATIONS = [
  { label: "2v2 · Front & Rear", size: "duo", layout: duoFormationRegistry["front-rear"] },
  { label: "2v2 · Side by Side", size: "duo", layout: duoFormationRegistry["side-by-side"] },
  { label: "3v3 · One Front, Two Rear", size: "trio", layout: trioFormationRegistry["one-front-two-rear"] },
  { label: "3v3 · Two Front, One Rear", size: "trio", layout: trioFormationRegistry["two-front-one-rear"] },
  { label: "3v3 · All Front", size: "trio", layout: trioFormationRegistry["all-front"] },
] as const;
const ATTACK_TYPES = [
  { id: "melee", title: "Melee", lead: "A living Front defender screens a Rear defender from classified Melee damage skills.", details: ["Front attacker: 100%", "Rear attacker: 70% direct damage"] },
  { id: "projectile", title: "Ranged Projectile", lead: "Can lawfully reach Front or Rear targets.", details: ["Front → Front: 100%", "Front → Rear: 80%", "Rear → Front: 80%", "Rear → Rear: 60%"] },
  { id: "instant", title: "Ranged Instant", lead: "Can lawfully reach Front or Rear targets.", details: ["No formation damage adjustment: 100%"] },
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

function FormationDiagram({ label, size, layout }: (typeof FORMATIONS)[number]) {
  return <article className="instruction-formation-card"><h3>{label}</h3>
    <div className={`instruction-formation-board instruction-team-diagram formation-map${size === "trio" ? " formation-map--trio" : ""}`} role="img" aria-label={`${label}: Friendly ${diagramSlotDescription(layout.friendly)}; Enemy ${diagramSlotDescription(layout.enemy)}`}>
      {layout.friendly.map((position, index) => <FormationSlot key={`friendly-${index}`} side="friendly" slot={index + 1} position={position} />)}
      <b className="instruction-formation-vs" aria-hidden="true">VS</b>
      {layout.enemy.map((position, index) => <FormationSlot key={`enemy-${index}`} side="enemy" slot={index + 1} position={position} />)}
    </div>
  </article>;
}

function QuickStart({ chapter }: { chapter: BattleInstructionChapter }) {
  return <><div className="instruction-command-flow" aria-label="Battle command walkthrough">
    {chapter.steps?.map((step, index) => <article key={step.title}><span>{index + 1}</span><div><h3>{step.title}</h3><p>{step.text}</p></div></article>)}
  </div>{chapter.callout && <aside className="instruction-callout"><strong>Remember</strong><p>{chapter.callout}</p></aside>}</>;
}

function BattleFormats() {
  return <div className="instruction-format-grid">{FORMATS.map((format) => <article key={format.size}>
    <header><strong>{format.size}</strong><span>{format.cap} completed rounds</span></header>
    <div className="instruction-team-diagram" aria-hidden="true">{Array.from({ length: Number(format.size[0]) }, (_, index) => <i key={`f-${index}`}>L</i>)}<b>VS</b>{Array.from({ length: Number(format.size[0]) }, (_, index) => <i className="enemy" key={`e-${index}`}>E</i>)}</div>
    <p>{format.formations}</p><ul>{format.slots.map((slot) => <li key={slot}>{slot}</li>)}</ul>
  </article>)}</div>;
}

function Formations({ chapter }: { chapter: BattleInstructionChapter }) {
  const [attackType, setAttackType] = useState<(typeof ATTACK_TYPES)[number]["id"]>("melee");
  const selected = ATTACK_TYPES.find((item) => item.id === attackType)!;
  function onAttackTypeKeyDown(event: KeyboardEvent<HTMLButtonElement>, tabIndex: number) {
    const delta = event.key === "ArrowRight" || event.key === "ArrowDown" ? 1 : event.key === "ArrowLeft" || event.key === "ArrowUp" ? -1 : 0;
    const target = event.key === "Home" ? 0 : event.key === "End" ? ATTACK_TYPES.length - 1 : delta ? (tabIndex + delta + ATTACK_TYPES.length) % ATTACK_TYPES.length : -1;
    if (target < 0) return;
    event.preventDefault();
    const next = ATTACK_TYPES[target];
    setAttackType(next.id);
    document.querySelector<HTMLButtonElement>(`#instruction-attack-tab-${next.id}`)?.focus();
  }
  return <><div className="instruction-formation-grid">{FORMATIONS.map((formation) => <FormationDiagram key={formation.label} {...formation} />)}</div>
    <section className="instruction-rule-separation" aria-label="Formation rule boundaries">
      <article><strong>1 · Legal target?</strong><p>{chapter.legalTargeting}</p></article>
      <article><strong>2 · Position damage?</strong><p>{chapter.positionDamage}</p></article>
      <article><strong>3 · Does it hit?</strong><p>{chapter.hitChance}</p></article>
    </section>
    <section className="instruction-attack-types"><div role="tablist" aria-label="Attack type explanations">{ATTACK_TYPES.map((item, tabIndex) => <button id={`instruction-attack-tab-${item.id}`} key={item.id} type="button" role="tab" aria-selected={attackType === item.id} aria-controls="instruction-attack-panel" tabIndex={attackType === item.id ? 0 : -1} onClick={() => setAttackType(item.id)} onKeyDown={(event) => onAttackTypeKeyDown(event, tabIndex)}>{item.title}</button>)}</div>
      <article id="instruction-attack-panel" role="tabpanel" aria-labelledby={`instruction-attack-tab-${selected.id}`}><h3>{selected.title}</h3><p>{selected.lead}</p><ul>{selected.details.map((detail) => <li key={detail}>{detail}</li>)}</ul></article></section>
    <p className="instruction-fine-print">{chapter.otherEffects}</p></>;
}

function BattleInterface({ chapter }: { chapter: BattleInstructionChapter }) {
  const [marker, setMarker] = useState(0);
  const [screenshotFailed, setScreenshotFailed] = useState(false);
  const markers = chapter.markers ?? [];
  return <div className="instruction-interface-guide"><div className={`instruction-battle-reference${screenshotFailed ? " is-schematic" : ""}`}>
    {!screenshotFailed && <img src="/game-images/manual/Battle_Instruction_Interface.png" alt="Current battle screen showing its principal controls" onError={() => setScreenshotFailed(true)} />}
    {screenshotFailed && <div className="instruction-battle-schematic" role="img" aria-label="Battle screen layout schematic"><span className="top">ROUND · TURN ORDER</span><span className="left">YOUR TEAM</span><span className="field">BATTLEFIELD TARGETS</span><span className="right">ENEMY TEAM</span><span className="acting">ACTING HERO</span><span className="skills">SKILL CARDS</span><span className="log">BATTLE LOG</span><span className="controls">SPEED · AUTO · RESIGN</span></div>}
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
      <small>FIELD GUIDE · SIX CHAPTERS</small><h1>{battleInstructionContent.title}</h1><p>{battleInstructionContent.subtitle}</p></header>
    <div className="instruction-mobile-select"><label htmlFor="instruction-chapter-select">Chapter</label><select id="instruction-chapter-select" value={chapterId} onChange={(event) => selectChapter(event.target.value as BattleInstructionChapterId)}>{chapters.map((item, chapterIndex) => <option key={item.id} value={item.id}>{chapterIndex + 1}. {item.title}</option>)}</select></div>
    <div className="instruction-compendium"><nav className="instruction-chapters" aria-label="Battle Instruction chapters" role="tablist" aria-orientation="vertical">{chapters.map((item, chapterIndex) => <button id={`instruction-tab-${item.id}`} key={item.id} role="tab" type="button" aria-selected={chapterId === item.id} aria-controls="instruction-chapter-panel" tabIndex={chapterId === item.id ? 0 : -1} onClick={() => selectChapter(item.id)} onKeyDown={(event) => onTabKeyDown(event, chapterIndex)}><span>{String(chapterIndex + 1).padStart(2, "0")}</span>{item.title}</button>)}</nav>
      <section className="instruction-reader" id="instruction-chapter-panel" role="tabpanel" aria-labelledby={`instruction-tab-${chapter.id}`}><div className="instruction-chapter-heading"><small>CHAPTER {String(index + 1).padStart(2, "0")} · {chapter.kicker}</small><h2 ref={headingRef} tabIndex={-1}>{chapter.title}</h2><p>{chapter.introduction}</p></div>
        <ChapterBody chapter={chapter} embedded={embedded} onBackToManual={onBackToManual} />
        <footer className="instruction-pagination"><button type="button" disabled={index === 0} onClick={() => selectChapter(chapters[index - 1].id)}>← Previous Chapter</button><span>{index + 1} / {chapters.length}</span><button type="button" disabled={index === chapters.length - 1} onClick={() => selectChapter(chapters[index + 1].id)}>Next Chapter →</button></footer>
      </section></div>
  </main>;
}
