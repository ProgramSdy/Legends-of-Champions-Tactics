"use client";

import { useMemo, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { resolveEnabledStage } from "@/components/stages/stage-config";
import type {
  StructuredStageBattleDefinition,
  StructuredStageDefinition,
} from "@/components/stages/structured-stage-config";
import type {
  BattleCreateConfiguration,
  BattleFormationId,
  BattleSize,
  EnemyCompositionMode,
  EnemyControlMode,
  HeroDefinitionSummary,
} from "@/lib/battle/types";
import { AssetImage } from "./AssetImage";

interface TeamBuilderBaseProps {
  roster: HeroDefinitionSummary[];
  onStart: (configuration: BattleCreateConfiguration) => void;
}

interface ArenaTeamBuilderProps extends TeamBuilderBaseProps {
  mode?: "arena";
  selectedStageId?: string;
}

interface StructuredTeamBuilderProps extends TeamBuilderBaseProps {
  mode: "structured";
  stage: StructuredStageDefinition;
  battle: StructuredStageBattleDefinition;
}

export type TeamBuilderProps = ArenaTeamBuilderProps | StructuredTeamBuilderProps;

const FIXED_SLOT_INDICES = [0, 1, 2] as const;
const MATRIX_PAGE_SIZE = 6;
const FORMATIONS: ReadonlyArray<{ id: BattleFormationId; name: string; positions: string }> = [
  { id: "front-rear", name: "Front and Rear", positions: "Hero 1 Front · Hero 2 Rear" },
  { id: "side-by-side", name: "Side by Side", positions: "Hero 1 Front · Hero 2 Front" },
];

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

function FormationSelector({
  side,
  value,
  onChange,
}: {
  side: "friendly" | "enemy";
  value: BattleFormationId;
  onChange: (formation: BattleFormationId) => void;
}) {
  const sideLabel = side === "friendly" ? "Your" : "Enemy";
  return (
    <fieldset className={`formation-selector ${side}`}>
      <legend>{sideLabel} formation</legend>
      <div className="formation-choices">
        {FORMATIONS.map((formation) => (
          <label key={formation.id}>
            <input
              type="radio"
              name={`${side}-formation`}
              value={formation.id}
              checked={value === formation.id}
              onChange={() => onChange(formation.id)}
            />
            <span>
              <strong>{formation.name}</strong>
              <small>{formation.positions}</small>
            </span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

function FixedEnemyTeamSlot({
  index,
  enabled,
  hero,
  battleSize,
}: {
  index: number;
  enabled: boolean;
  hero?: HeroDefinitionSummary;
  battleSize: BattleSize;
}) {
  return (
    <article
      className={`enemy-slot-card fixed-enemy-slot${enabled ? "" : " disabled"}`}
      data-enemy-slot={index}
      data-slot-enabled={enabled}
    >
      <div className="builder-hero-media">
        {enabled && hero ? (
          <AssetImage request={portraitRequest(hero)} className="builder-hero-image" />
        ) : (
          <span className="disabled-slot-mark" aria-hidden="true">◇</span>
        )}
      </div>
      <span className="slot-number">HERO {index + 1}</span>
      <strong>{enabled && hero ? hero.faculty : "UNAVAILABLE"}</strong>
      <small className={enabled && hero ? "hero-specialization" : undefined}>{enabled && hero ? hero.specialization : `${battleSize}v${battleSize}`}</small>
    </article>
  );
}

export function TeamBuilder(props: TeamBuilderProps) {
  const { roster, onStart } = props;
  const structuredStage = props.mode === "structured" ? props.stage : null;
  const structuredBattle = props.mode === "structured" ? props.battle : null;
  const selectedStage = resolveEnabledStage(
    structuredStage?.stageId ?? (props.mode === "structured" ? undefined : props.selectedStageId),
  );
  const builderRoster = useMemo(() => {
    if (!structuredStage) return roster;
    return structuredStage.allowedPlayerDefinitionIds
      .map((definitionId) => roster.find((hero) => hero.definitionId === definitionId))
      .filter((hero): hero is HeroDefinitionSummary => Boolean(hero));
  }, [roster, structuredStage]);
  const initialBattleSize = structuredBattle?.battleSize ?? 1;
  const [battleSize, setBattleSize] = useState<BattleSize>(initialBattleSize);
  const [playerTeam, setPlayerTeam] = useState<string[]>(Array(initialBattleSize).fill(""));
  const [activePlayerSlot, setActivePlayerSlot] = useState(0);
  const [activeEnemySlot, setActiveEnemySlot] = useState(0);
  const [activeTeamSide, setActiveTeamSide] = useState<"player" | "enemy">("player");
  const [enemyCompositionMode, setEnemyCompositionMode] = useState<EnemyCompositionMode>(structuredBattle ? "specified" : "random");
  const [enemyTeam, setEnemyTeam] = useState<string[]>(structuredBattle ? [...structuredBattle.enemyDefinitionIds] : Array(1).fill(""));
  const [enemyControlMode, setEnemyControlMode] = useState<EnemyControlMode>("computer");
  const [playerFormation, setPlayerFormation] = useState<BattleFormationId>("front-rear");
  const [enemyFormation, setEnemyFormation] = useState<BattleFormationId>("front-rear");
  const [seedText, setSeedText] = useState("");
  const [selectedFaculty, setSelectedFaculty] = useState("All");
  const [matrixPage, setMatrixPage] = useState(0);

  const resize = (team: string[], size: BattleSize) =>
    Array.from({ length: size }, (_, index) => team[index] ?? "");

  const setSize = (size: BattleSize) => {
    setBattleSize(size);
    setPlayerTeam((team) => resize(team, size));
    setEnemyTeam((team) => resize(team, size));
    setActivePlayerSlot((slot) => Math.min(slot, size - 1));
    setActiveEnemySlot((slot) => Math.min(slot, size - 1));
  };

  const parsedSeed = seedText === "" ? undefined : Number(seedText);
  const validation = useMemo(() => {
    if (playerTeam.length !== battleSize || playerTeam.some((id) => !id)) return "Fill every player-team slot.";
    if (structuredStage && playerTeam.some((id) => !structuredStage.allowedPlayerDefinitionIds.includes(id))) {
      return "Choose every player hero from this stage's approved roster.";
    }
    if (enemyCompositionMode === "specified" && (enemyTeam.length !== battleSize || enemyTeam.some((id) => !id))) {
      return "Fill every specified enemy-team slot.";
    }
    if (seedText !== "" && (!Number.isSafeInteger(parsedSeed) || parsedSeed! < 0)) return "Seed must be a non-negative whole number.";
    return null;
  }, [battleSize, enemyCompositionMode, enemyTeam, parsedSeed, playerTeam, seedText, structuredStage]);

  const updateSlot = (team: string[], index: number, value: string) =>
    team.map((current, slot) => slot === index ? value : current);

  const launch = () => {
    if (validation) return;
    if (structuredBattle) {
      const structuredConfiguration = {
        playerTeam,
        enemyCompositionMode: "specified" as const,
        enemyTeam: [...structuredBattle.enemyDefinitionIds],
        enemyControlMode: "computer" as const,
      };
      if (structuredBattle.battleSize === 2) {
        onStart({ ...structuredConfiguration, battleSize: 2, playerFormation });
      } else {
        onStart({ ...structuredConfiguration, battleSize: structuredBattle.battleSize });
      }
      return;
    }
    const arenaConfiguration = {
      playerTeam,
      enemyCompositionMode,
      ...(enemyCompositionMode === "specified" ? { enemyTeam } : {}),
      ...(parsedSeed === undefined ? {} : { seed: parsedSeed }),
    };
    if (battleSize === 2) {
      if (enemyControlMode === "player") {
        onStart({ ...arenaConfiguration, battleSize: 2, enemyControlMode, playerFormation, enemyFormation });
      } else {
        onStart({ ...arenaConfiguration, battleSize: 2, enemyControlMode, playerFormation });
      }
      return;
    }
    onStart({ ...arenaConfiguration, battleSize, enemyControlMode });
  };

  const stagePosition = `${selectedStage.geometry.leftPercent + selectedStage.geometry.widthPercent / 2}% ${selectedStage.geometry.topPercent + selectedStage.geometry.heightPercent / 2}%`;
  const activeHeroId = activeTeamSide === "player"
    ? playerTeam[activePlayerSlot] ?? ""
    : enemyTeam[activeEnemySlot] ?? "";
  const faculties = useMemo(
    () => Array.from(new Set(builderRoster.map((hero) => hero.faculty))),
    [builderRoster],
  );
  const filteredRoster = useMemo(
    () => selectedFaculty === "All"
      ? builderRoster
      : builderRoster.filter((hero) => hero.faculty === selectedFaculty),
    [builderRoster, selectedFaculty],
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
          <span>{structuredBattle
            ? `Battle ${structuredBattle.displayOrder} of ${structuredStage?.battles.length}`
            : "Valley of Champions"}</span>
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

      {structuredBattle && structuredStage ? (
        <section className="structured-battle-summary" aria-labelledby="structured-battle-heading">
          <div>
            <small>STRUCTURED TRAINING</small>
            <h2 id="structured-battle-heading">Battle {structuredBattle.displayOrder}</h2>
            <p>Battle {structuredBattle.displayOrder} of {structuredStage.battles.length}</p>
          </div>
          <strong>{structuredBattle.battleSize}v{structuredBattle.battleSize}</strong>
          <span>Fixed format · predefined enemy team</span>
        </section>
      ) : <section className="builder-options" aria-labelledby="battle-rules-heading">
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
              <label key={mode}><input type="radio" name="enemy-composition" checked={enemyCompositionMode === mode} onChange={() => {
                setEnemyCompositionMode(mode);
                if (mode === "random" && activeTeamSide === "enemy") setActiveTeamSide("player");
              }} /><span>{mode === "random" ? "Random" : "Choose team"}</span></label>
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
      </section>}

      <section className="team-composer friendly" aria-labelledby="player-team-heading">
        <header><div><small>PLAYER CONTROLLED</small><h2 id="player-team-heading">Your Team</h2></div><strong>{battleSize} HERO{battleSize > 1 ? "ES" : ""}</strong></header>
        {battleSize === 2 ? <FormationSelector side="friendly" value={playerFormation} onChange={setPlayerFormation} /> : null}
        <div className="visual-team-slots player-slots" data-fixed-slot-count="3">
          {FIXED_SLOT_INDICES.map((index) => {
            const enabled = index < battleSize;
            const hero = enabled ? builderRoster.find((candidate) => candidate.definitionId === playerTeam[index]) : undefined;
            const active = enabled && index === activePlayerSlot;
            return (
              <button
                key={`player-${index}`}
                type="button"
                className={`player-slot-card${active ? " active" : ""}`}
                data-player-slot={index}
                data-slot-enabled={enabled}
                aria-label={enabled && hero
                  ? `Your Hero ${index + 1}: ${professionLabel(hero)}`
                  : enabled
                    ? `Select your Hero ${index + 1}`
                    : `Hero ${index + 1}: unavailable for ${battleSize}v${battleSize}`}
                aria-pressed={active}
                disabled={!enabled}
                onClick={() => { setActivePlayerSlot(index); setActiveTeamSide("player"); }}
              >
                <span className="builder-hero-media">
                  {enabled && hero ? (
                    <AssetImage request={portraitRequest(hero)} className="builder-hero-image" />
                  ) : (
                    <span className="empty-slot-prompt">SELECT YOUR HERO</span>
                  )}
                </span>
                <span className="slot-number">HERO {index + 1}</span>
                <strong>{hero?.faculty ?? (enabled ? "SELECT HERO" : "UNAVAILABLE")}</strong>
                <small className={hero ? "hero-specialization" : undefined}>{hero?.specialization ?? (enabled ? "MATRIX ASSIGNMENT" : `${battleSize}v${battleSize}`)}</small>
              </button>
            );
          })}
        </div>
      </section>

      <section className="team-composer enemy" aria-labelledby="enemy-team-heading">
        <header><div><small>{enemyControlMode === "computer" ? "ENGINE CONTROLLED" : "PLAYER CONTROLLED"}</small><h2 id="enemy-team-heading">Enemy Team</h2></div><strong>{enemyCompositionMode === "random" ? "RANDOM" : `${battleSize} HERO${battleSize > 1 ? "ES" : ""}`}</strong></header>
        {battleSize === 2 && enemyControlMode === "player"
          ? <FormationSelector side="enemy" value={enemyFormation} onChange={setEnemyFormation} />
          : battleSize === 2
            ? <p className="formation-computer-note" role="note"><strong>Computer formation</strong><span>The computer will choose Front and Rear or Side by Side when this battle is created.</span></p>
            : null}
        {structuredBattle
          ? <div
              className="enemy-slot-list fixed-enemy-team"
              data-fixed-slot-count="3"
              aria-label={`Predefined enemy team: ${structuredBattle.enemyDefinitionIds.map((definitionId) => {
                const hero = roster.find((candidate) => candidate.definitionId === definitionId);
                return hero ? professionLabel(hero) : definitionId;
              }).join(", ")}`}
            >
              {FIXED_SLOT_INDICES.map((index) => (
                <FixedEnemyTeamSlot
                  key={`fixed-enemy-${index}`}
                  index={index}
                  enabled={index < structuredBattle.battleSize}
                  hero={index < structuredBattle.battleSize
                    ? roster.find((candidate) => candidate.definitionId === structuredBattle.enemyDefinitionIds[index])
                    : undefined}
                  battleSize={structuredBattle.battleSize}
                />
              ))}
            </div>
          : enemyCompositionMode === "random"
          ? <div className="random-team-note" aria-label="Enemy composition: Python-selected random team"><div className="enemy-slot-list random-enemy-slots" data-fixed-slot-count="3">{FIXED_SLOT_INDICES.map((index) => { const enabled = index < battleSize; return <article className={`enemy-slot-card random-slot${enabled ? "" : " disabled"}`} data-enemy-slot={index} data-slot-enabled={enabled} key={index}><div className="builder-hero-media"><span className="disabled-slot-mark" aria-hidden="true">{enabled ? "?" : "◇"}</span></div><span className="slot-number">HERO {index + 1}</span><strong>{enabled ? "RANDOM" : "UNAVAILABLE"}</strong><small>{enabled ? "PYTHON SELECTED" : `${battleSize}v${battleSize}`}</small></article>; })}</div></div>
          : <div className="enemy-slot-list" data-fixed-slot-count="3">{FIXED_SLOT_INDICES.map((index) => {
            const enabled = index < battleSize;
            const hero = enabled ? roster.find((candidate) => candidate.definitionId === enemyTeam[index]) : undefined;
            const active = enabled && activeTeamSide === "enemy" && index === activeEnemySlot;
            return <button
              key={`enemy-${index}`}
              type="button"
              className={`enemy-slot-card selectable-enemy-slot${active ? " active" : ""}${enabled ? "" : " disabled"}`}
              data-enemy-slot={index}
              data-slot-enabled={enabled}
              aria-label={enabled && hero
                ? `Enemy Hero ${index + 1}: ${professionLabel(hero)}`
                : enabled
                  ? `Select enemy Hero ${index + 1}`
                  : `Hero ${index + 1}: unavailable for ${battleSize}v${battleSize}`}
              aria-pressed={active}
              disabled={!enabled}
              onClick={() => { setActiveEnemySlot(index); setActiveTeamSide("enemy"); }}
            >
              <span className="builder-hero-media">
                {hero ? <AssetImage request={portraitRequest(hero)} className="builder-hero-image" /> : <span className="empty-slot-prompt">SELECT ENEMY HERO</span>}
              </span>
              <span className="slot-number">HERO {index + 1}</span>
              <strong>{hero?.faculty ?? (enabled ? "SELECT HERO" : "UNAVAILABLE")}</strong>
              <small className={hero ? "hero-specialization" : undefined}>{hero?.specialization ?? (enabled ? "MATRIX ASSIGNMENT" : `${battleSize}v${battleSize}`)}</small>
            </button>;
          })}</div>}
      </section>

      <section className="hero-roster hero-selection-matrix" aria-labelledby="roster-heading">
        <header><div><small id="roster-heading">SELECT {activeTeamSide === "enemy" ? "ENEMY " : ""}HERO {(activeTeamSide === "player" ? activePlayerSlot : activeEnemySlot) + 1}</small></div><span>TOTAL HERO: {builderRoster.length}</span></header>
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
                aria-label={`Assign ${professionLabel(hero)} to ${activeTeamSide === "player" ? "your" : "enemy"} Hero ${(activeTeamSide === "player" ? activePlayerSlot : activeEnemySlot) + 1}`}
                aria-pressed={assigned}
                onClick={() => activeTeamSide === "player"
                  ? setPlayerTeam((team) => updateSlot(team, activePlayerSlot, hero.definitionId))
                  : setEnemyTeam((team) => updateSlot(team, activeEnemySlot, hero.definitionId))}
              >
                <span className="builder-hero-media">
                  <AssetImage request={portraitRequest(hero)} className="builder-hero-image" />
                </span>
                <strong>{hero.faculty}</strong>
                <small className="hero-specialization">{hero.specialization}</small>
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
