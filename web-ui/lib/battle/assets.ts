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
  "hero.paladin.protection": { className: "Paladin", tone: "amber", assets: { figure: "/game-images/heroes/Paladin-Protection/figures/Paladin_Protection.png" }, placeholder: false },
  "hero.paladin.retribution": { className: "Paladin", tone: "amber", assets: { figure: "/game-images/heroes/Paladin-Retribution/figures/Paladin_Retribution.png" }, placeholder: false },
  "hero.priest.comprehensiveness": { className: "Priest", tone: "blue", assets: { figure: "/game-images/heroes/Priest-Comprehensiveness/figures/Priest_Comprehensiveness.png" }, placeholder: false },
  "hero.priest.discipline": { className: "Priest", tone: "blue", assets: { figure: "/game-images/heroes/Priest-Discipline/figures/Priest_Discipline.png" }, placeholder: false },
  "hero.warrior.defence": { className: "Warrior", tone: "amber", assets: { figure: "/game-images/heroes/Warrior-Defence/figures/Warrior_Defence.png" }, placeholder: false },
  "hero.warrior.weapon_master": { className: "Warrior", tone: "amber", assets: { class: classAssets.Warrior, figure: "/game-images/heroes/Warrior-Weapon-Master/figures/Warrior_Weapon_Master.png" }, placeholder: false, animation: { idle: "idle", active: "weapon-ready", defeated: "defeated" } },
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
  "status.fatal_strike": { glyph: "✕", name: "Fatal Strike", description: "Healing received is reduced while this wound persists.", harmful: true },
  "status.armor_breaker": { glyph: "⬢", name: "Armor Breaker", description: "Armor is reduced by Armor Crush.", harmful: true },
  "status.bleeding_armor_crush": { glyph: "◒", name: "Armor Crush Bleeding", description: "Bleeding damage from Armor Crush remains active.", harmful: true },
  "status.wound_armor_crush": { glyph: "⌁", name: "Armor Crush Wound", description: "A wound inflicted by Armor Crush remains active.", harmful: true },
  "status.antivenom_potion": { glyph: "✚", name: "Antivenom Potion", description: "Antivenom protection is currently active.", harmful: false },
  "status.bleeding_sharp_blade": { glyph: "╱", name: "Sharp Blade Bleeding", description: "Bleeding damage from Sharp Blade remains active.", harmful: true },
  "status.poisoned_dagger": { glyph: "◆", name: "Poisoned Dagger", description: "Poison from Poisoned Dagger remains active.", harmful: true },
  "status.shadow_evasion": { glyph: "◐", name: "Shadow Evasion", description: "Evasion is increased by Shadow Evasion.", harmful: false },
  "status.cold": { glyph: "❄", name: "Cold", description: "Speed is reduced by an authoritative frost effect.", harmful: true },
  "status.stunned": { glyph: "✹", name: "Stunned", description: "Cannot act while the authoritative stun persists.", harmful: true },
  "status.shadow_word_pain": { glyph: "☾", name: "Shadow Word: Pain", description: "Suffers shadow damage over time.", harmful: true },
  "status.holy_word_redemption": { glyph: "✚", name: "Holy Word: Redemption", description: "Receives healing from a holy effect.", harmful: false },
  "status.holy_word_punishment": { glyph: "☀", name: "Holy Word: Punishment", description: "Suffers punishment from a holy effect.", harmful: true },
  "status.wrath_of_crusader": { glyph: "⚔", name: "Wrath of Crusader", description: "Crusader wrath modifies authoritative combat strength.", harmful: false },
  "status.hammer_of_revenge": { glyph: "◆", name: "Hammer of Revenge", description: "Affected by the authoritative Hammer of Revenge effect.", harmful: true },
  "status.shield_of_righteous": { glyph: "⬡", name: "Shield of Righteous", description: "Protected by an authoritative righteous shield.", harmful: false },
  "status.shield_lash": { glyph: "⌁", name: "Shield Lash", description: "Empowered by the authoritative Shield Lash effect.", harmful: false },
  "status.scoff": { glyph: "!", name: "Scoff", description: "Forced to direct hostility toward the status source.", harmful: true },
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
