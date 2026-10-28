"use client";

import { useEffect, useRef } from "react";
import type { CombatantState, CombatantStatValue } from "@/lib/battle/types";
import { statusRegistry } from "@/lib/battle/assets";
import { AssetImage } from "./AssetImage";
import { StatusIcon } from "./StatusIcon";

const FOCUSABLE_SELECTOR = "button:not(:disabled), [href], [tabindex='0']";

const ATTRIBUTE_ROWS: ReadonlyArray<{ key: "damage" | "defence" | "agility"; label: string }> = [
  { key: "damage", label: "Damage" },
  { key: "defence", label: "Defence" },
  { key: "agility", label: "Agility" },
];

const RESISTANCE_ROWS: ReadonlyArray<{
  key: keyof CombatantState["stats"]["resistances"];
  label: string;
}> = [
  { key: "fire", label: "Fire" },
  { key: "frost", label: "Frost" },
  { key: "arcane", label: "Arcane" },
  { key: "shadow", label: "Shadow" },
  { key: "death", label: "Death" },
  { key: "poison", label: "Poison" },
  { key: "nature", label: "Nature" },
];

function formatNumber(value: number): string {
  if (Object.is(value, -0) || value === 0) return "0";
  return String(value);
}

function StatValue({ stat, updating }: { stat: CombatantStatValue; updating: boolean }) {
  if (updating) return <span className="hero-stats-updating" aria-live="polite">Updating…</span>;
  const trend = stat.delta > 0 ? "positive" : stat.delta < 0 ? "negative" : "neutral";
  return <span className={`hero-stat-value ${trend}`} data-stat-trend={trend}>
    <strong>{formatNumber(stat.current)}</strong>
    {stat.delta !== 0 ? <small>({stat.delta > 0 ? "+" : "−"}{formatNumber(Math.abs(stat.delta))})</small> : null}
  </span>;
}

function focusableInDialog(dialog: HTMLDialogElement | null): HTMLElement[] {
  return Array.from(dialog?.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR) ?? [])
    .filter((element) => !element.hasAttribute("disabled") && element.getAttribute("aria-hidden") !== "true");
}

export function HeroStatsDialog({ hero, updating, onClose }: {
  hero: CombatantState;
  updating: boolean;
  onClose: () => void;
}) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const titleId = `hero-stats-title-${hero.id.replaceAll(".", "-")}`;

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (typeof dialog.showModal === "function" && !dialog.open) dialog.showModal();
    else if (!dialog.open) dialog.setAttribute("open", "");
    closeButtonRef.current?.focus();
  }, []);

  return <dialog
    ref={dialogRef}
    className="hero-stats-dialog"
    aria-modal="true"
    aria-labelledby={titleId}
    onCancel={(event) => {
      event.preventDefault();
      onClose();
    }}
    onKeyDown={(event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
        return;
      }
      if (event.key !== "Tab") return;
      const focusable = focusableInDialog(dialogRef.current);
      if (focusable.length === 0) {
        event.preventDefault();
        return;
      }
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }}
  >
    <header className="hero-stats-header">
      <AssetImage request={{ kind: "portrait", key: hero.definitionId, name: hero.displayName, className: hero.faculty }} className="hero-stats-portrait" />
      <div>
        <small>HERO STATS</small>
        <h2 id={titleId}>{hero.displayName}</h2>
        <p>{hero.faculty} · {hero.specialization}{hero.isSummon ? " · Summon" : ""}</p>
      </div>
      <button ref={closeButtonRef} className="hero-stats-close" type="button" data-audio-feedback="interactive" aria-label={`Close Hero Stats for ${hero.displayName}`} onClick={onClose}>×</button>
    </header>

    <div className="hero-stats-body">
      <section className="hero-stats-current-hp" aria-labelledby={`${titleId}-hp`}>
        <span id={`${titleId}-hp`}>CURRENT HP</span>
        <strong>{hero.hp.current}</strong>
      </section>

      <section className="hero-stats-section" aria-labelledby={`${titleId}-attributes`}>
        <h3 id={`${titleId}-attributes`}>ATTRIBUTES</h3>
        <dl>
          {ATTRIBUTE_ROWS.map(({ key, label }) => <div key={key}><dt>{label}</dt><dd><StatValue stat={hero.stats[key]} updating={updating} /></dd></div>)}
        </dl>
      </section>

      <section className="hero-stats-section" aria-labelledby={`${titleId}-resistances`}>
        <h3 id={`${titleId}-resistances`}>MAGIC RESISTANCES</h3>
        <dl className="hero-resistance-grid">
          {RESISTANCE_ROWS.map(({ key, label }) => <div key={key}><dt>{label}</dt><dd><StatValue stat={hero.stats.resistances[key]} updating={updating} /></dd></div>)}
        </dl>
      </section>

      <section className="hero-stats-section hero-stats-effects" aria-labelledby={`${titleId}-effects`}>
        <h3 id={`${titleId}-effects`}>ACTIVE EFFECTS</h3>
        {hero.statuses.length === 0
          ? <p>{updating ? <span className="hero-stats-updating" aria-live="polite">Updating…</span> : "No active effects"}</p>
          : <ul>{hero.statuses.map((status) => {
            const definition = statusRegistry[status.id] ?? {
              name: "Unknown status",
              description: "Details unavailable.",
              glyph: "?",
              harmful: status.kind === "debuff",
            };
            return <li key={status.instanceId}>
              <StatusIcon status={status} detailsUpdating={updating} />
              <span><strong>{definition.name}</strong><small>{definition.description}</small></span>
              <em>{updating
                ? <span className="hero-stats-updating" aria-live="polite">Updating…</span>
                : [
                    status.stacks !== null ? `${status.stacks} stack${status.stacks === 1 ? "" : "s"}` : null,
                    status.roundsRemaining !== null ? `${status.roundsRemaining} round${status.roundsRemaining === 1 ? "" : "s"}` : null,
                  ].filter(Boolean).join(" · ") || "Active"}</em>
            </li>;
          })}</ul>}
      </section>
    </div>
  </dialog>;
}
