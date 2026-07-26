export type AssetKind = "portrait" | "figure" | "thumbnail" | "class" | "skill" | "status" | "effect";

export interface AssetRequest {
  kind: AssetKind;
  key: string;
  className?: string;
  name: string;
}

export interface ResolvedAsset {
  src: string | null;
  fallback: "requested" | "class" | "generic" | "initials";
  label: string;
  status: "placeholder" | "final";
  resolvedPath: string | null;
  association: string;
}

const classAssets: Record<string, string> = {
  Necromancer: "/game-assets/classes/necromancer.webp",
  Warlock: "/game-assets/classes/warlock.png",
  Warrior: "/game-assets/classes/warrior.webp",
  Mage: "/game-assets/classes/mage.png",
};

const heroClasses: Record<string, string> = {
  "friendly.arthas": "Necromancer", "friendly.black_heart": "Warlock",
  "friendly.arthas.flesh_puppet.1": "Warrior", "enemy.sashein": "Necromancer",
  "enemy.andonidas": "Mage",
};

export const heroPresentation: Record<string, { className: string; tone: string; assets: Partial<Record<"portrait" | "figure" | "thumbnail" | "class", string>>; placeholder: boolean; animation?: { idle: string; active: string; defeated: string } }> = {
  "hero.warrior.weapon_master": { className: "Warrior", tone: "amber", assets: { class: classAssets.Warrior }, placeholder: true, animation: { idle: "idle", active: "weapon-ready", defeated: "defeated" } },
  "hero.rogue.comprehensiveness": { className: "Rogue", tone: "violet", assets: {}, placeholder: true, animation: { idle: "idle", active: "shadow-ready", defeated: "defeated" } },
};

export interface SkillPresentation {
  glyph: string;
  tone: string;
  effect: "magic" | "healing" | "melee" | "status" | "summon";
  description?: string;
  targetStyle?: string;
  projectile?: string;
  impact?: string;
  movement?: "lunge" | "return" | "offset";
  asset?: string;
}

export const skillPresentation: Record<string, SkillPresentation> = {
  "skill.life_drain": { glyph: "☠", tone: "green", effect: "magic" },
  "skill.stitch_of_agony": { glyph: "✦", tone: "red", effect: "status" },
  "skill.summon_flesh_puppet": { glyph: "♟", tone: "violet", effect: "summon" },
  "skill.shadow_bolt": { glyph: "◈", tone: "violet", effect: "magic" },
  "skill.flesh_slam_single": { glyph: "✊", tone: "red", effect: "melee" },
  "skill.warrior.fatal_strike": { glyph: "⚔", tone: "red", effect: "melee", description: "A decisive strike that can hinder healing.", targetStyle: "Single enemy", impact: "heavy", movement: "lunge" },
  "skill.warrior.armor_crush": { glyph: "⬢", tone: "amber", effect: "melee", description: "A crushing blow that can break armour.", targetStyle: "Single enemy", impact: "armour-break", movement: "lunge" },
  "skill.warrior.antivenom_potion": { glyph: "✚", tone: "green", effect: "healing", description: "Recover and resist poison.", targetStyle: "Self", impact: "healing-glow" },
  "skill.rogue.sharp_blade": { glyph: "⟋", tone: "red", effect: "melee", description: "A swift attack that can cause bleeding.", targetStyle: "Single enemy", impact: "blade", movement: "lunge" },
  "skill.rogue.poisoned_dagger": { glyph: "◆", tone: "green", effect: "status", description: "A poisoned attack that can stack poison.", targetStyle: "Single enemy", projectile: "dagger", impact: "poison" },
  "skill.rogue.shadow_evasion": { glyph: "◒", tone: "violet", effect: "magic", description: "Enter a heightened evasive stance.", targetStyle: "Self", impact: "shadow", movement: "offset" },
};

export const statusRegistry: Record<string, { glyph: string; name: string; description: string; harmful: boolean; asset?: string }> = {
  "status.stitch_of_agony": { glyph: "✦", name: "Stitch of Agony", description: "Suffers authoritative damage at round start.", harmful: true },
  "status.shadow_bolt": { glyph: "◈", name: "Shadow Mark", description: "A hostile shadow effect supplied by the battle engine.", harmful: true },
  "status.arcane_guard": { glyph: "⬡", name: "Arcane Guard", description: "Protected by an arcane ward.", harmful: false },
};

export const effectRegistry = {
  magic: { className: "magic", asset: null },
  healing: { className: "healing", asset: null },
  melee: { className: "melee", asset: null },
  status: { className: "status", asset: null },
  summon: { className: "summon", asset: null },
} as const;

export function resolveAsset(request: AssetRequest): ResolvedAsset {
  const base = { status: "placeholder" as const, association: request.key };
  if (request.kind === "class") {
    const src = classAssets[request.key];
    return src ? { ...base, src, resolvedPath: src, fallback: "requested", label: request.name, status: "final" } : { ...base, src: null, resolvedPath: null, fallback: "initials", label: `${request.name} placeholder` };
  }
  if (request.kind === "skill") {
    const src = skillPresentation[request.key]?.asset;
    return src ? { ...base, src, resolvedPath: src, fallback: "requested", label: request.name, status: "final" } : { ...base, src: null, resolvedPath: null, fallback: "generic", label: `${request.name} skill placeholder` };
  }
  if (request.kind === "status") {
    const src = statusRegistry[request.key]?.asset;
    return src ? { ...base, src, resolvedPath: src, fallback: "requested", label: request.name, status: "final" } : { ...base, src: null, resolvedPath: null, fallback: "generic", label: `${request.name} status placeholder` };
  }
  if (request.kind === "effect") return { ...base, src: null, resolvedPath: null, fallback: "generic", label: `${request.name} CSS effect placeholder` };
  const hero = heroPresentation[request.key];
  const requested = hero?.assets[request.kind as "portrait" | "figure" | "thumbnail" | "class"];
  if (requested) return { ...base, src: requested, resolvedPath: requested, fallback: "requested", label: `${request.name} ${request.kind}`, status: hero.placeholder ? "placeholder" : "final" };
  const className = request.className ?? hero?.className ?? heroClasses[request.key];
  const classAsset = className ? classAssets[className] : null;
  return classAsset
    ? { ...base, src: classAsset, resolvedPath: classAsset, fallback: "class", label: `${request.name} ${request.kind} — class placeholder` }
    : { ...base, src: null, resolvedPath: null, fallback: "initials", label: `${request.name} ${request.kind} placeholder` };
}

export function initials(name: string): string {
  return name.split(/\s+/).map((part) => part[0]).join("").slice(0, 2).toUpperCase();
}
