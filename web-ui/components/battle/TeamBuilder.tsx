"use client";

import { useMemo, useState } from "react";
import type {
  BattleCreateConfiguration,
  BattleSize,
  EnemyCompositionMode,
  EnemyControlMode,
  HeroDefinitionSummary,
} from "@/lib/battle/types";

interface TeamBuilderProps {
  roster: HeroDefinitionSummary[];
  onStart: (configuration: BattleCreateConfiguration) => void;
}

function TeamSelect({
  id,
  label,
  value,
  onChange,
  roster,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  roster: HeroDefinitionSummary[];
}) {
  return (
    <label className="team-slot" htmlFor={id}>
      <span>{label}</span>
      <select id={id} value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">Choose a hero</option>
        {roster.map((hero) => (
          <option key={hero.definitionId} value={hero.definitionId}>{hero.displayName} · {hero.specialization}</option>
        ))}
      </select>
    </label>
  );
}

export function TeamBuilder({ roster, onStart }: TeamBuilderProps) {
  const defaultPlayer = roster.map((hero) => hero.definitionId);
  const defaultEnemy = [...defaultPlayer].reverse();
  const [battleSize, setBattleSize] = useState<BattleSize>(1);
  const [playerTeam, setPlayerTeam] = useState<string[]>(defaultPlayer.slice(0, 1));
  const [enemyCompositionMode, setEnemyCompositionMode] = useState<EnemyCompositionMode>("random");
  const [enemyTeam, setEnemyTeam] = useState<string[]>(defaultEnemy.slice(0, 1));
  const [enemyControlMode, setEnemyControlMode] = useState<EnemyControlMode>("computer");
  const [seedText, setSeedText] = useState("");

  const resize = (team: string[], size: BattleSize, defaults: readonly string[]) =>
    Array.from({ length: size }, (_, index) => team[index] ?? defaults[index] ?? "");

  const setSize = (size: BattleSize) => {
    setBattleSize(size);
    setPlayerTeam((team) => resize(team, size, defaultPlayer));
    setEnemyTeam((team) => resize(team, size, defaultEnemy));
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

  return (
    <main className="team-builder">
      <header className="builder-title">
        <span className="builder-crest" aria-hidden="true">L</span>
        <div><p>LEGENDS OF CHAMPIONS TACTICS</p><h1>Team Builder</h1><span>Assemble both sides, then enter the Fallen Citadel.</span></div>
      </header>

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
        <div className="team-slot-list">
          {playerTeam.map((heroId, index) => <TeamSelect roster={roster} key={`player-${index}`} id={`player-slot-${index}`} label={`Player slot ${index + 1}`} value={heroId} onChange={(value) => setPlayerTeam((team) => updateSlot(team, index, value))} />)}
        </div>
      </section>

      <section className="team-composer enemy" aria-labelledby="enemy-team-heading">
        <header><div><small>{enemyControlMode === "computer" ? "ENGINE CONTROLLED" : "PLAYER CONTROLLED"}</small><h2 id="enemy-team-heading">Enemy Team</h2></div><strong>{enemyCompositionMode === "random" ? "RANDOM" : `${battleSize} HERO${battleSize > 1 ? "ES" : ""}`}</strong></header>
        {enemyCompositionMode === "random"
          ? <div className="random-team-note"><span aria-hidden="true">?</span><p>Python will assemble the enemy team when the battle begins. A seed makes this choice repeatable.</p></div>
          : <div className="team-slot-list">{enemyTeam.map((heroId, index) => <TeamSelect roster={roster} key={`enemy-${index}`} id={`enemy-slot-${index}`} label={`Enemy slot ${index + 1}`} value={heroId} onChange={(value) => setEnemyTeam((team) => updateSlot(team, index, value))} />)}</div>}
      </section>

      <section className="hero-roster" aria-labelledby="roster-heading">
        <header><h2 id="roster-heading">Approved roster</h2><span>8 HERO DEFINITIONS</span></header>
        <div>{roster.map((hero) => <article key={hero.definitionId}><i aria-hidden="true">{hero.displayName.slice(0, 1)}</i><strong>{hero.displayName}</strong><span>{hero.specialization}</span></article>)}</div>
      </section>

      <footer className="builder-footer">
        <p className={validation ? "validation-error" : ""} aria-live="polite">{validation ?? `${battleSize}v${battleSize} configuration ready.`}</p>
        <button type="button" onClick={launch} disabled={Boolean(validation)}>ENTER BATTLE</button>
      </footer>
    </main>
  );
}
