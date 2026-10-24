import type {
  HeroSkillClassificationReference,
  HeroSkillClassificationValue,
  HeroSkillNumericReference,
  HeroSkillReference,
  HeroSkillReferenceCondition,
  HeroSkillTargetReference,
} from "@/lib/battle/types";

export interface HeroGalleryFactRow {
  id: string;
  label: string;
  value: string;
  note?: string;
  conditions?: readonly HeroSkillReferenceCondition[];
  calculation?: { title: string; formula: string };
}

const CLASSIFICATION_LABELS: Record<HeroSkillClassificationValue, string> = {
  melee: "Melee",
  rangedInstant: "Ranged Instant",
  rangedProjectile: "Ranged Projectile",
  physical: "Physical",
  magical: "Magical",
  fire: "Fire",
  frost: "Frost",
  arcane: "Arcane",
  shadow: "Shadow",
  holy: "Holy",
  poison: "Poison",
  nature: "Nature",
  death: "Death",
  weapon: "Weapon",
};

const SKILL_TYPE_LABELS: Record<HeroSkillReference["skillType"], string> = {
  damage: "Damage",
  healing: "Healing",
  damageHealing: "Damage & Healing",
  buff: "Buff",
  effect: "Effect",
};

function targetLabel(target: HeroSkillTargetReference): string {
  switch (target.mode) {
    case "self": return "Self";
    case "singleAlly": return "One Ally";
    case "singleEnemy": return "One Enemy";
    case "flexible": return "One Ally or Enemy";
    case "multipleAllies": return `Up to ${target.maximumTargets} Allies`;
    case "multipleEnemies": return `Up to ${target.maximumTargets} Enemies`;
  }
}

function classificationRow(
  id: string,
  label: string,
  reference: HeroSkillClassificationReference,
): HeroGalleryFactRow | null {
  if (reference.state === "notApplicable") return null;
  return {
    id,
    label,
    value: reference.state === "unclassified" ? "Unclassified" : CLASSIFICATION_LABELS[reference.value],
  };
}

function amountLabel(range: { minimum: number; maximum: number }): string {
  return range.minimum === range.maximum ? String(range.minimum) : `${range.minimum}–${range.maximum}`;
}

function numericRow(
  id: string,
  label: string,
  reference: HeroSkillNumericReference,
): HeroGalleryFactRow | null {
  if (reference.state === "notApplicable") return null;
  if (reference.state === "unavailable") {
    return {
      id,
      label,
      value: reference.displayLabel ?? "Unavailable",
      // A calculation dialog supplies the explanatory detail without making
      // the compact Base Damage card repeat it.
      note: reference.calculation ? undefined : reference.note,
      calculation: reference.calculation ?? undefined,
    };
  }
  return {
    id,
    label,
    value: amountLabel(reference.amountRange),
    note: reference.note,
    conditions: reference.conditions,
  };
}

export function buildSkillReferenceRows(reference: HeroSkillReference): HeroGalleryFactRow[] {
  return [
    numericRow("base-damage", "Base Damage", reference.baseDamage),
    numericRow("continuous-damage", "Continuous Damage", reference.continuousDamage),
    numericRow("base-healing", "Base Healing", reference.baseHealing),
    { id: "target", label: "Target Type", value: targetLabel(reference.target) },
    { id: "skill-type", label: "Skill Type", value: SKILL_TYPE_LABELS[reference.skillType] },
    classificationRow("attack-type", "Attack Type", reference.attackType),
    classificationRow("damage-nature", "Damage Nature", reference.damageNature),
    classificationRow("damage-type", "Damage Type", reference.damageType),
    reference.cooldownRounds != null
      ? { id: "cooldown", label: "Cool Down", value: `${reference.cooldownRounds} Rounds` }
      : null,
  ].filter((row): row is HeroGalleryFactRow => row !== null);
}
