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

export function HeroCard({ hero, active = false }: { hero: CombatantState; active?: boolean }) {
  const profession = hero.isSummon
    ? `${hero.specialization} · Summon`
    : `${hero.faculty} · ${hero.specialization}`;
  return (
    <article className={`hero-card ${hero.sideId} ${active ? "active" : ""} ${hero.alive ? "" : "defeated"}`} aria-label={`${hero.displayName}, ${profession}${active ? ", active hero" : ""}`}>
      <AssetImage request={{ kind: "portrait", key: hero.definitionId, name: hero.displayName, className: hero.faculty }} className="portrait" />
      <div className="hero-data">
        <div className="hero-title"><div><h3>{hero.displayName}</h3><p>{profession}</p></div><AssetImage request={{ kind: "class", key: hero.faculty, name: hero.faculty }} className="class-icon" /></div>
        <Meter value={hero.hp.current} maximum={hero.hp.maximum} kind="hp" label="Health" />
        {hero.resource && <Meter value={hero.resource.current} maximum={hero.resource.maximum} kind="resource" label={hero.resource.kind} />}
        <div className="status-row">{hero.statuses.map((status) => <StatusIcon key={status.instanceId} status={status} />)}{hero.isSummon && <span className="summon-rounds">{hero.summonRoundsRemaining}R</span>}</div>
      </div>
    </article>
  );
}
