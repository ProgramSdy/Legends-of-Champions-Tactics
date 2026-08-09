"use client";

import { useMemo, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { resolveEnabledStage } from "@/components/stages/stage-config";
import type {
  BattleCreateConfiguration,
  BattleSize,
  EnemyCompositionMode,
  EnemyControlMode,
  HeroDefinitionSummary,
} from "@/lib/battle/types";
import { AssetImage } from "./AssetImage";

interface TeamBuilderProps {
  roster: HeroDefinitionSummary[];
  onStart: (configuration: BattleCreateConfiguration) => void;
  selectedStageId?: string;
}

const FIXED_SLOT_INDICES = [0, 1, 2] as const;
const MATRIX_PAGE_SIZE = 5;

function professionLabel(hero: HeroDefinitionSummary) {
  return `${hero.faculty} · ${hero.specialization}`;
}

function portraitRequest(hero: HeroDefinitionSummary) {
  return {
    kind: "portrait" as const,
    key: hero.definitionId,
    className: hero.faculty,
    name: `${hero.faculty} ${hero.specialization}`,
  };
}

function EnemyTeamSlot({
  index,
  enabled,
  value,
  onChange,
  roster,
}: {
  index: number;
  enabled: boolean;
  value: string;
  onChange: (value: string) => void;
  roster: HeroDefinitionSummary[];
}) {
  const id = `enemy-slot-${index}`;
  const selectedHero = roster.find((hero) => hero.definitionId === value);
  return (
    <article
      className={`enemy-slot-card${enabled ? "" : " disabled"}`}
      data-enemy-slot={index}
      data-slot-enabled={enabled}
    >
      <div className="builder-hero-media">
        {enabled && selectedHero ? (
          <AssetImage request={portraitRequest(selectedHero)} className="builder-hero-image" />
        ) : (
          <span className="disabled-slot-mark" aria-hidden="true">◇</span>
        )}
      </div>
      <span className="slot-number">HERO {index + 1}</span>
      {enabled && selectedHero ? <strong>{professionLabel(selectedHero)}</strong> : <strong>UNAVAILABLE</strong>}
      <label className="team-slot" htmlFor={id}>
        <span className="sr-only">Hero {index + 1}</span>
        {enabled ? <select id={id} value={value} onChange={(event) => onChange(event.target.value)}>
          <option value="">Choose a hero</option>
          {roster.map((hero) => (
            <option key={hero.definitionId} value={hero.definitionId}>
              {professionLabel(hero)}
            </option>
          ))}
        </select> : null}
      </label>
    </article>
  );
}

export function TeamBuilder({ roster, onStart, selectedStageId }: TeamBuilderProps) {
  const selectedStage = resolveEnabledStage(selectedStageId);
  const defaultPlayer = roster.map((hero) => hero.definitionId);
  const defaultEnemy = [...defaultPlayer].reverse();
  const [battleSize, setBattleSize] = useState<BattleSize>(1);
  const [playerTeam, setPlayerTeam] = useState<string[]>(defaultPlayer.slice(0, 1));
  const [activePlayerSlot, setActivePlayerSlot] = useState(0);
  const [enemyCompositionMode, setEnemyCompositionMode] = useState<EnemyCompositionMode>("random");
  const [enemyTeam, setEnemyTeam] = useState<string[]>(defaultEnemy.slice(0, 1));
  const [enemyControlMode, setEnemyControlMode] = useState<EnemyControlMode>("computer");
  const [seedText, setSeedText] = useState("");
  const [selectedFaculty, setSelectedFaculty] = useState("All");
  const [matrixPage, setMatrixPage] = useState(0);

  const resize = (team: string[], size: BattleSize, defaults: readonly string[]) =>
    Array.from({ length: size }, (_, index) => team[index] ?? defaults[index] ?? "");

  const setSize = (size: BattleSize) => {
    setBattleSize(size);
    setPlayerTeam((team) => resize(team, size, defaultPlayer));
    setEnemyTeam((team) => resize(team, size, defaultEnemy));
    setActivePlayerSlot((slot) => Math.min(slot, size - 1));
  };

  const parsedSeed = seedText === "" ? undefined : Number(seedText);
  const validation = useMemo(() => {
    if (playerTeam.length !== battleSize || playerTeam.some((id) => !id)) return "Fill every player-team slot.";
    if (enemyCompositionMode === "specified" && (enemyTeam.length !== battleSize || enemyTeam.some((id) => !id))) {
      return "Fill every specified enemy-team slot.";
    }
    if (seedText !== "" && (!Number.isSafeInteger(parsedSeed) || parsedSeed! < 0)) return "Seed must be a non-negative whole number.";
    return null;
  }, [battleSize, enemyCompositionMode, enemyTeam, parsedSeed, playerTeam, seedText]);

  const updateSlot = (team: string[], index: number, value: string) =>
    team.map((current, slot) => slot === index ? value : current);

  const launch = () => {
    if (validation) return;
    onStart({
      battleSize,
      playerTeam,
      enemyCompositionMode,
      ...(enemyCompositionMode === "specified" ? { enemyTeam } : {}),
      enemyControlMode,
      ...(parsedSeed === undefined ? {} : { seed: parsedSeed }),
    });
  };

  const stagePosition = `${selectedStage.geometry.leftPercent + selectedStage.geometry.widthPercent / 2}% ${selectedStage.geometry.topPercent + selectedStage.geometry.heightPercent / 2}%`;
  const activeHeroId = playerTeam[activePlayerSlot] ?? "";
  const faculties = useMemo(
    () => Array.from(new Set(roster.map((hero) => hero.faculty))),
    [roster],
  );
  const filteredRoster = useMemo(
    () => selectedFaculty === "All"
      ? roster
      : roster.filter((hero) => hero.faculty === selectedFaculty),
    [roster, selectedFaculty],
  );
  const matrixPageCount = Math.max(1, Math.ceil(filteredRoster.length / MATRIX_PAGE_SIZE));
  const visibleMatrixHeroes = filteredRoster.slice(
    matrixPage * MATRIX_PAGE_SIZE,
    (matrixPage + 1) * MATRIX_PAGE_SIZE,
  );

  const selectFaculty = (faculty: string) => {
    setSelectedFaculty(faculty);
    setMatrixPage(0);
  };

  return (
    <main className="team-builder" tabIndex={0} aria-label="Team Builder scroll area">
      <Link className="builder-back" href="/stages">← <span>BACK TO STAGE MAP</span></Link>

      <header className="builder-title">
        <span className="builder-crest" aria-hidden="true">L</span>
        <div><p>LEGENDS OF CHAMPIONS TACTICS</p><h1>Team Builder</h1></div>
      </header>

      <section className="current-stage" aria-labelledby="current-stage-heading">
        <div className="current-stage-copy">
          <small>CURRENT STAGE</small>
          <h2 id="current-stage-heading">{selectedStage.displayName}</h2>
          <span>Valley of Champions</span>
        </div>
        <div className="current-stage-media">
          <Image
            className="current-stage-map"
            src="/game-images/Stage_Map/valley_of_champions.png"
            alt=""
            aria-hidden="true"
            fill
            sizes="(max-width: 1100px) 100vw, 48vw"
            style={{ objectPosition: stagePosition }}
            unoptimized
          />
        </div>
      </section>

      <section className="builder-options" aria-labelledby="battle-rules-heading">
        <h2 id="battle-rules-heading">Battle rules</h2>
        <fieldset>
          <legend>Battle size</legend>
          <div className="choice-row">
            {([1, 2, 3] as const).map((size) => (
              <label key={size}><input type="radio" name="battle-size" checked={battleSize === size} onChange={() => setSize(size)} /><span>{size}v{size}</span></label>
            ))}
          </div>
        </fieldset>
        <fieldset>
          <legend>Enemy composition</legend>
          <div className="choice-row">
            {(["random", "specified"] as const).map((mode) => (
              <label key={mode}><input type="radio" name="enemy-composition" checked={enemyCompositionMode === mode} onChange={() => setEnemyCompositionMode(mode)} /><span>{mode === "random" ? "Random" : "Choose team"}</span></label>
            ))}
          </div>
        </fieldset>
        <fieldset>
          <legend>Enemy control</legend>
          <div className="choice-row">
            {(["computer", "player"] as const).map((mode) => (
              <label key={mode}><input type="radio" name="enemy-control" checked={enemyControlMode === mode} onChange={() => setEnemyControlMode(mode)} /><span>{mode === "computer" ? "Computer" : "Player"}</span></label>
            ))}
          </div>
        </fieldset>
        <label className="seed-field" htmlFor="battle-seed"><span>Seed <small>optional</small></span><input id="battle-seed" inputMode="numeric" value={seedText} onChange={(event) => setSeedText(event.target.value)} placeholder="Random" /></label>
      </section>

      <section className="team-composer friendly" aria-labelledby="player-team-heading">
        <header><div><small>PLAYER CONTROLLED</small><h2 id="player-team-heading">Your Team</h2></div><strong>{battleSize} HERO{battleSize > 1 ? "ES" : ""}</strong></header>
        <div className="visual-team-slots player-slots" data-fixed-slot-count="3">
          {FIXED_SLOT_INDICES.map((index) => {
            const enabled = index < battleSize;
            const hero = enabled ? roster.find((candidate) => candidate.definitionId === playerTeam[index]) : undefined;
            const active = enabled && index === activePlayerSlot;
            return (
              <button
                key={`player-${index}`}
                type="button"
                className={`player-slot-card${active ? " active" : ""}`}
                data-player-slot={index}
                data-slot-enabled={enabled}
                aria-label={enabled && hero
                  ? `Hero ${index + 1}: ${professionLabel(hero)}`
                  : `Hero ${index + 1}: unavailable for ${battleSize}v${battleSize}`}
                aria-pressed={active}
                disabled={!enabled}
                onClick={() => setActivePlayerSlot(index)}
              >
                <span className="builder-hero-media">
                  {enabled && hero ? (
                    <AssetImage request={portraitRequest(hero)} className="builder-hero-image" />
                  ) : (
                    <span className="disabled-slot-mark" aria-hidden="true">◇</span>
                  )}
                </span>
                <span className="slot-number">HERO {index + 1}</span>
                <strong>{hero?.faculty ?? "UNAVAILABLE"}</strong>
                <small>{hero?.specialization ?? `${battleSize}v${battleSize}`}</small>
              </button>
            );
          })}
        </div>
      </section>

      <section className="team-composer enemy" aria-labelledby="enemy-team-heading">
        <header><div><small>{enemyControlMode === "computer" ? "ENGINE CONTROLLED" : "PLAYER CONTROLLED"}</small><h2 id="enemy-team-heading">Enemy Team</h2></div><strong>{enemyCompositionMode === "random" ? "RANDOM" : `${battleSize} HERO${battleSize > 1 ? "ES" : ""}`}</strong></header>
        {enemyCompositionMode === "random"
          ? <div className="random-team-note" aria-label="Enemy composition: Python-selected random team"><div className="enemy-slot-list random-enemy-slots" data-fixed-slot-count="3">{FIXED_SLOT_INDICES.map((index) => { const enabled = index < battleSize; return <article className={`enemy-slot-card random-slot${enabled ? "" : " disabled"}`} data-enemy-slot={index} data-slot-enabled={enabled} key={index}><div className="builder-hero-media"><span className="disabled-slot-mark" aria-hidden="true">{enabled ? "?" : "◇"}</span></div><span className="slot-number">HERO {index + 1}</span><strong>{enabled ? "RANDOM" : "UNAVAILABLE"}</strong><small>{enabled ? "PYTHON SELECTED" : `${battleSize}v${battleSize}`}</small></article>; })}</div></div>
          : <div className="enemy-slot-list" data-fixed-slot-count="3">{FIXED_SLOT_INDICES.map((index) => <EnemyTeamSlot roster={roster} key={`enemy-${index}`} index={index} enabled={index < battleSize} value={enemyTeam[index] ?? ""} onChange={(value) => setEnemyTeam((team) => updateSlot(team, index, value))} />)}</div>}
      </section>

      <section className="hero-roster hero-selection-matrix" aria-labelledby="roster-heading">
        <header><div><small>ASSIGNING HERO {activePlayerSlot + 1}</small><h2 id="roster-heading">Hero Selection Matrix</h2></div><span>{roster.length} HERO DEFINITIONS</span></header>
        <div className="matrix-toolbar">
          <div className="faculty-filter" role="group" aria-label="Filter heroes by faculty">
            {["All", ...faculties].map((faculty) => (
              <button
                key={faculty}
                type="button"
                data-faculty-filter={faculty}
                aria-pressed={selectedFaculty === faculty}
                onClick={() => selectFaculty(faculty)}
              >
                {faculty}
              </button>
            ))}
          </div>
          <div className="matrix-navigation">
            <button type="button" aria-label="Previous heroes" disabled={matrixPage === 0} onClick={() => setMatrixPage((page) => page - 1)}>←</button>
            <span className="matrix-page-status" aria-live="polite">{matrixPage + 1} / {matrixPageCount}</span>
            <button type="button" aria-label="Next heroes" disabled={matrixPage >= matrixPageCount - 1} onClick={() => setMatrixPage((page) => page + 1)}>→</button>
          </div>
        </div>
        <div className="hero-matrix-grid">
          {visibleMatrixHeroes.map((hero) => {
            const assigned = hero.definitionId === activeHeroId;
            return (
              <button
                key={hero.definitionId}
                type="button"
                className={`matrix-hero-card${assigned ? " assigned" : ""}`}
                data-hero-id={hero.definitionId}
                aria-label={`Assign ${professionLabel(hero)} to Hero ${activePlayerSlot + 1}`}
                aria-pressed={assigned}
                onClick={() => setPlayerTeam((team) => updateSlot(team, activePlayerSlot, hero.definitionId))}
              >
                <span className="builder-hero-media">
                  <AssetImage request={portraitRequest(hero)} className="builder-hero-image" />
                </span>
                <strong>{hero.faculty}</strong>
                <small>{hero.specialization}</small>
                {assigned ? <span className="matrix-assigned" aria-hidden="true">✓</span> : null}
              </button>
            );
          })}
        </div>
      </section>

      <footer className="builder-footer">
        <p className={validation ? "validation-error" : ""} aria-live="polite">{validation ?? `${battleSize}v${battleSize} configuration ready.`}</p>
        <button type="button" onClick={launch} disabled={Boolean(validation)}>ENTER BATTLE</button>
      </footer>
    </main>
  );
}
