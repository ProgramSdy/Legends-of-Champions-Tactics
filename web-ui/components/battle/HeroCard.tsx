import type { CombatantState } from "@/lib/battle/types";
import { AssetImage } from "./AssetImage";
import { StatusIcon } from "./StatusIcon";

export function Meter({ value, maximum, kind, label }: { value: number; maximum: number; kind: "hp" | "resource"; label: string }) {
  const percent = maximum > 0 ? Math.max(0, Math.min(100, value / maximum * 100)) : 0;
  return (
    <div className="meter-row">
      <span className={`meter ${kind}`}><span style={{ width: `${percent}%` }} /></span>
      <span>{value}/{maximum}</span>
      <span className="sr-only">{label}: {percent.toFixed(0)} percent</span>
    </div>
  );
}

export function HeroCard({ hero, active = false, targetHighlighted = false, onViewStats }: { hero: CombatantState; active?: boolean; targetHighlighted?: boolean; onViewStats?: (trigger: HTMLButtonElement) => void }) {
  const profession = hero.isSummon
    ? `${hero.specialization} · Summon`
    : `${hero.faculty} · ${hero.specialization}`;
  return (
    <article className={`hero-card ${hero.sideId} ${active ? "active" : ""} ${targetHighlighted ? "target-highlighted" : ""} ${hero.alive ? "" : "defeated"}`} aria-label={`${hero.displayName}, ${profession}${active ? ", active hero" : ""}`}>
      <AssetImage request={{ kind: "sidebarPortrait", key: hero.definitionId, name: hero.displayName, className: hero.faculty }} className="portrait" />
      <div className="hero-data">
        <div className="hero-title"><div><h3>{hero.displayName}</h3><p>{profession}</p></div><AssetImage request={{ kind: "class", key: hero.faculty, name: hero.faculty }} className="class-icon" /></div>
        <Meter value={hero.hp.current} maximum={hero.hp.maximum} kind="hp" label="Health" />
        {hero.resource && <Meter value={hero.resource.current} maximum={hero.resource.maximum} kind="resource" label={hero.resource.kind} />}
        <div className="status-row">{hero.statuses.map((status) => <StatusIcon key={status.instanceId} status={status} />)}{hero.isSummon && <span className="summon-rounds">{hero.summonRoundsRemaining}R</span>}</div>
      </div>
      {onViewStats ? <button
        className="hero-stats-button"
        type="button"
        data-audio-feedback="interactive"
        title="View Hero Stats"
        aria-label={`View Hero Stats for ${hero.displayName}, ${hero.sideId} slot ${hero.slot + 1}`}
        onClick={(event) => {
          event.preventDefault();
          event.stopPropagation();
          onViewStats(event.currentTarget);
        }}
        onKeyDown={(event) => event.stopPropagation()}
      >
        <svg aria-hidden="true" viewBox="0 0 20 20" focusable="false">
          <path d="M3 17V9h3v8H3Zm5.5 0V3h3v14h-3Zm5.5 0V6h3v11h-3Z" />
        </svg>
      </button> : null}
    </article>
  );
}
