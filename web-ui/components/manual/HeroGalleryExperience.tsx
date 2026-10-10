"use client";

import { useCallback, useEffect, useMemo, useState, type KeyboardEvent } from "react";
import Link from "next/link";
import { AssetImage } from "@/components/battle/AssetImage";
import { fetchHeroGalleryRoster, fetchPlayerProgression } from "@/lib/battle/liveProvider";
import type { HeroGalleryDefinition, HeroSkillInventoryItem } from "@/lib/battle/types";
import { heroGalleryContent } from "@/lib/manual/heroGalleryContent";
import type { HeroGallerySkillContent } from "@/lib/manual/heroGalleryContentTypes";
import { buildSkillReferenceRows } from "@/lib/manual/heroGalleryPresentation";

type State = { heroes: HeroGalleryDefinition[]; owned: Set<string> | null; error: string | null };
type SkillTab = "active" | "passive";

const ACTIVE_TAB_ID = "hero-skill-tab-active";
const PASSIVE_TAB_ID = "hero-skill-tab-passive";

export function SkillReferenceCard({ skill, content }: { skill: HeroSkillInventoryItem; content: HeroGallerySkillContent }) {
  const rows = buildSkillReferenceRows(skill.reference);
  return (
    <details>
      <summary>{skill.displayName}</summary>
      <div className="skill-reference-copy">
        <p>{content.introduction}</p>
        <dl className="skill-reference-grid">
          {rows.map((row) => (
            <div key={row.id}>
              <dt>{row.label}</dt>
              <dd>
                <strong>{row.value}</strong>
                {row.note && <small>{row.note}</small>}
                {!!row.conditions?.length && (
                  <ul aria-label={`${row.label} conditions`}>
                    {row.conditions.map((condition) => (
                      <li key={condition.label}>
                        <span>{condition.label}</span>
                        <strong>{condition.amountRange.minimum === condition.amountRange.maximum
                          ? condition.amountRange.minimum
                          : `${condition.amountRange.minimum}–${condition.amountRange.maximum}`}</strong>
                      </li>
                    ))}
                  </ul>
                )}
              </dd>
            </div>
          ))}
        </dl>
        {!!content.tips?.length && (
          <aside className="skill-reference-tips" aria-label={`${skill.displayName} strategy tips`}>
            {content.tips.map((tip) => <p key={`${tip.label}:${tip.text}`}><strong>{tip.label}</strong>{tip.text}</p>)}
          </aside>
        )}
      </div>
    </details>
  );
}

export function HeroGalleryExperience() {
  const [state, setState] = useState<State>({ heroes: [], owned: null, error: null });
  const [faculty, setFaculty] = useState("All");
  const [selected, setSelected] = useState<string | null>(null);
  const [skillTab, setSkillTab] = useState<SkillTab>("active");

  const loadGallery = useCallback(() => {
    Promise.all([fetchHeroGalleryRoster(), fetchPlayerProgression().catch(() => null)])
      .then(([heroes, progress]) => setState({
        heroes,
        owned: progress ? new Set(progress.unlockedHeroDefinitionIds) : null,
        error: null,
      }))
      .catch(() => setState({
        heroes: [],
        owned: null,
        error: "Hero Gallery data is unavailable. Please retry.",
      }));
  }, []);

  useEffect(() => { loadGallery(); }, [loadGallery]);

  const faculties = useMemo(
    () => ["All", "Warrior", "Mage", "Paladin", "Rogue", "Priest"].filter(
      (value) => value === "All" || state.heroes.some((hero) => hero.faculty === value),
    ),
    [state.heroes],
  );
  const heroes = state.heroes.filter((hero) => faculty === "All" || hero.faculty === faculty);
  const hero = state.heroes.find((item) => item.definitionId === (selected ?? heroes[0]?.definitionId)) ?? null;
  const content = hero ? heroGalleryContent[hero.definitionId] : null;
  const active = hero?.skills.filter((skill) => !skill.isPassive) ?? [];
  const passive = hero?.skills.filter((skill) => skill.isPassive) ?? [];
  const panelId = `hero-skill-panel-${skillTab}`;

  function onSkillTabKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight" && event.key !== "Home" && event.key !== "End") return;
    event.preventDefault();
    const next: SkillTab = event.key === "ArrowLeft" || event.key === "Home" ? "active" : "passive";
    setSkillTab(next);
    window.requestAnimationFrame(() => document.getElementById(next === "active" ? ACTIVE_TAB_ID : PASSIVE_TAB_ID)?.focus());
  }

  return (
    <main className="manual-page hero-gallery-page">
      <Link className="manual-back" href="/stages?manual=open">← Back to Manual</Link>
      {state.error ? (
        <section className="manual-error" role="alert">
          <p>{state.error}</p>
          <button type="button" onClick={loadGallery}>Retry Gallery</button>
        </section>
      ) : !state.heroes.length ? (
        <p className="manual-loading">Loading the approved hero definitions…</p>
      ) : (
        <div className="gallery-compendium">
          <section className="gallery-browser">
            <header>
              <small>GAME MANUAL</small>
              <h1>Hero Gallery</h1>
              <p>Meet the champions. Explore their battle styles and find your favourites.</p>
            </header>
            <div className="manual-filter" aria-label="Filter heroes by faculty">
              {faculties.map((value) => (
                <button key={value} type="button" aria-pressed={faculty === value} onClick={() => setFaculty(value)}>{value}</button>
              ))}
            </div>
            <section className="gallery-cards" aria-label="Approved heroes">
              {heroes.map((item) => {
                const ownership = state.owned === null ? "Ownership unavailable" : state.owned.has(item.definitionId) ? "Owned" : "Locked";
                return (
                  <button key={item.definitionId} type="button" aria-pressed={hero?.definitionId === item.definitionId} onClick={() => setSelected(item.definitionId)}>
                    <AssetImage request={{ kind: "portrait", key: item.definitionId, name: item.displayName, className: item.faculty }} />
                    <span><strong>{item.faculty}</strong><small>{item.specialization}</small><em>{ownership}</em></span>
                  </button>
                );
              })}
            </section>
            <blockquote>“Different paths. A greater purpose.”</blockquote>
          </section>
          {hero && content && (
            <article className="hero-profile" aria-live="polite">
              <AssetImage request={{ kind: "figure", key: hero.definitionId, name: hero.displayName, className: hero.faculty }} className="hero-profile-art" />
              <div className="hero-profile-copy">
                <small>{hero.faculty}</small><h2>{hero.specialization}</h2><p>{content.introduction}</p>
                <section className="battle-style"><h3>Battle Style</h3><p>{content.battleStyle}</p></section>
                <section className="base-properties">
                  <h3>Properties <span>(Base Range)</span></h3>
                  <p className="range-note">Starting values are randomized within these configured ranges, not fixed battle results.</p>
                  <dl>{hero.startingStatRanges.map((range) => <div key={range.id}><dt>{range.label}</dt><dd>{range.minimum}–{range.maximum}</dd></div>)}</dl>
                  <h4>Magic Resistance Schools</h4>
                  <dl>{hero.startingResistanceRanges.map((range) => <div key={range.id}><dt>{range.label}</dt><dd>{range.minimum}–{range.maximum}</dd></div>)}</dl>
                </section>
              </div>
              <section className="skill-tabs">
                <div role="tablist" aria-label="Hero skills">
                  <button id={ACTIVE_TAB_ID} role="tab" type="button" tabIndex={skillTab === "active" ? 0 : -1} aria-selected={skillTab === "active"} aria-controls="hero-skill-panel-active" onKeyDown={onSkillTabKeyDown} onClick={() => setSkillTab("active")}>Active Skills ({active.length})</button>
                  <button id={PASSIVE_TAB_ID} role="tab" type="button" tabIndex={skillTab === "passive" ? 0 : -1} aria-selected={skillTab === "passive"} aria-controls="hero-skill-panel-passive" onKeyDown={onSkillTabKeyDown} onClick={() => setSkillTab("passive")}>Passive ({passive.length})</button>
                </div>
                <div id={panelId} role="tabpanel" aria-labelledby={skillTab === "active" ? ACTIVE_TAB_ID : PASSIVE_TAB_ID} tabIndex={0}>
                  {skillTab === "active"
                    ? active.map((skill) => <SkillReferenceCard key={skill.skillId} skill={skill} content={content.skills[skill.skillId]} />)
                    : passive.length
                      ? passive.map((skill) => <SkillReferenceCard key={skill.skillId} skill={skill} content={content.skills[skill.skillId]} />)
                      : <p className="manual-na">N/A</p>}
                </div>
                <p className="ownership-copy">{state.owned === null ? "Ownership unavailable without an active save slot." : state.owned.has(hero.definitionId) ? "Owned in the active save slot." : hero.unlockSource?.kind === "stageReward" ? `Locked · Reward from ${hero.unlockSource.stageDisplayName}, Battle ${hero.unlockSource.battleIndex}.` : hero.unlockSource?.kind === "starter" ? "Starter definition for a new save slot." : "Locked · No current unlock route."}</p>
              </section>
            </article>
          )}
        </div>
      )}
    </main>
  );
}
