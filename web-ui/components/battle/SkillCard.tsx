import { skillPresentation } from "@/lib/battle/assets";
import type { SkillState } from "@/lib/battle/types";

export function SkillCard({ skill, selected, legal, disabled, onSelect }: { skill: SkillState; selected: boolean; legal: boolean; disabled: boolean; onSelect: () => void }) {
  const visual = skillPresentation[skill.id] ?? { glyph: "?", tone: "violet" };
  const unavailable = disabled || !legal || !skill.available;
  return (
    <button className={`skill-card ${visual.tone} ${selected ? "selected" : ""}`} disabled={unavailable} onClick={onSelect} aria-pressed={selected} aria-describedby={`${skill.id}-detail`}>
      <span className="skill-glyph" aria-hidden="true">{visual.glyph}</span>
      <span className="skill-copy"><strong>{skill.displayName}</strong><span id={`${skill.id}-detail`}>{skill.description || visual.description || "Presentation details unavailable."}</span><em>{visual.targetStyle ?? skill.targetMode.replace(/([A-Z])/g, " $1")}</em></span>
      <span className="skill-ornament" aria-hidden="true"><i /><i /><i /></span>
      <span className="skill-meta">{skill.cooldownRemaining > 0 ? `Cooldown ${skill.cooldownRemaining}` : skill.resourceCost ? `${skill.resourceCost.amount} ${skill.resourceCost.kind}` : "Ready"}</span>
      {unavailable && <span className="locked">{skill.unavailableReason ?? "Unavailable"}</span>}
    </button>
  );
}
