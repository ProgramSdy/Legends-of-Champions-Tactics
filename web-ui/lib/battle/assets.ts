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

export const skillPresentation: Record<string, { glyph: string; tone: string; effect: "magic" | "healing" | "melee" | "status" | "summon"; asset?: string }> = {
  "skill.life_drain": { glyph: "☠", tone: "green", effect: "magic" },
  "skill.stitch_of_agony": { glyph: "✦", tone: "red", effect: "status" },
  "skill.summon_flesh_puppet": { glyph: "♟", tone: "violet", effect: "summon" },
  "skill.shadow_bolt": { glyph: "◈", tone: "violet", effect: "magic" },
  "skill.flesh_slam_single": { glyph: "✊", tone: "red", effect: "melee" },
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
  if (request.kind === "class") {
    const src = classAssets[request.key];
    return src ? { src, fallback: "requested", label: request.name } : { src: null, fallback: "initials", label: `${request.name} placeholder` };
  }
  if (request.kind === "skill") {
    const src = skillPresentation[request.key]?.asset;
    return src ? { src, fallback: "requested", label: request.name } : { src: null, fallback: "generic", label: `${request.name} skill placeholder` };
  }
  if (request.kind === "status") {
    const src = statusRegistry[request.key]?.asset;
    return src ? { src, fallback: "requested", label: request.name } : { src: null, fallback: "generic", label: `${request.name} status placeholder` };
  }
  if (request.kind === "effect") return { src: null, fallback: "generic", label: `${request.name} CSS effect placeholder` };
  const className = request.className ?? heroClasses[request.key];
  const classAsset = className ? classAssets[className] : null;
  return classAsset
    ? { src: classAsset, fallback: "class", label: `${request.name} ${request.kind} — class placeholder` }
    : { src: null, fallback: "initials", label: `${request.name} ${request.kind} placeholder` };
}

export function initials(name: string): string {
  return name.split(/\s+/).map((part) => part[0]).join("").slice(0, 2).toUpperCase();
}
