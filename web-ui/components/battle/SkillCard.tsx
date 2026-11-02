import { useState } from "react";
import { skillPresentation, type SkillPresentation } from "@/lib/battle/assets";
import type { SkillState } from "@/lib/battle/types";

function SkillGlyph({ asset, glyph }: { asset?: string; glyph: string }) {
  const [failedAsset, setFailedAsset] = useState<string | null>(null);
  const visibleAsset = asset && failedAsset !== asset ? asset : null;

  return (
    <span className="skill-glyph" aria-hidden="true">
      {visibleAsset ? (
        // eslint-disable-next-line @next/next/no-img-element -- local game art uses its natural 128px source and a glyph fallback.
        <img
          className="skill-glyph-art"
          src={visibleAsset}
          alt=""
          width={128}
          height={128}
          decoding="async"
          onError={() => setFailedAsset(visibleAsset)}
        />
      ) : glyph}
    </span>
  );
}

export function SkillCard({ skill, selected, legal, disabled, onSelect }: { skill: SkillState; selected: boolean; legal: boolean; disabled: boolean; onSelect: () => void }) {
  const visual: SkillPresentation = skillPresentation[skill.id] ?? { glyph: "?", tone: "violet", effect: "magic" };
  const passive = Boolean(skill.isPassive);
  const unavailable = passive || disabled || !legal || !skill.available;
  return (
    <button className={`skill-card ${visual.tone} ${passive ? "passive" : ""} ${selected ? "selected" : ""}`} data-audio-feedback="interactive" disabled={unavailable} onClick={onSelect} aria-pressed={selected} aria-describedby={`${skill.id}-detail`}>
      <SkillGlyph asset={visual.asset} glyph={visual.glyph} />
      <span className="skill-copy"><strong>{skill.displayName}</strong><span id={`${skill.id}-detail`}>{skill.description || visual.description || "Presentation details unavailable."}</span><em>{visual.targetStyle ?? skill.targetMode.replace(/([A-Z])/g, " $1")}</em></span>
      <span className="skill-ornament" aria-hidden="true"><i /><i /><i /></span>
      <span className="skill-meta">{passive ? "Passive Aura" : skill.cooldownRemaining > 0 ? `Cooldown ${skill.cooldownRemaining}` : skill.resourceCost ? `${skill.resourceCost.amount} ${skill.resourceCost.kind}` : "Ready"}</span>
      {unavailable && !passive && <span className="locked">{skill.unavailableReason ?? "Unavailable"}</span>}
    </button>
  );
}

/** A visual deck slot only—deliberately not a SkillState or interactive control. */
export function NoFourthSkillCard() {
  return (
    <article className="skill-card skill-placeholder" aria-label="No Fourth Skill. No additional skill is available for this hero. N/A.">
      <span className="skill-glyph" aria-hidden="true">◇</span>
      <span className="skill-copy"><strong>No Fourth Skill</strong><span>No additional skill is available for this hero.</span><em>N/A</em></span>
      <span className="skill-ornament" aria-hidden="true"><i /><i /><i /></span>
      <span className="skill-meta">N/A</span>
    </article>
  );
}

/** Presentation-only passive; it never enters the battle skill/action state. */
export function WrathOfCrusaderCard() {
  const visual = skillPresentation["skill.paladin.wrath_of_crusader"];
  return (
    <article className="skill-card passive passive-display" aria-label="Wrath of Crusader. Passive skill, not selectable.">
      <SkillGlyph asset={visual.asset} glyph={visual.glyph} />
      <span className="skill-copy"><strong>Wrath of Crusader</strong><span>Crusader Strike builds Wrath, empowering Hammer of Anger and Flash of Light.</span><em>Passive</em></span>
      <span className="skill-ornament" aria-hidden="true"><i /><i /><i /></span>
      <span className="skill-meta">PASSIVE</span>
    </article>
  );
}
