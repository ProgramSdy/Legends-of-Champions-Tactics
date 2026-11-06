import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
import { parseDocument } from "yaml";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const WEB_UI_DIR = path.resolve(SCRIPT_DIR, "..");
const SOURCE_FILE = path.join(WEB_UI_DIR, "content", "battle-instruction", "manual.yaml");
const OUTPUT_FILE = path.join(WEB_UI_DIR, "lib", "manual", "battleInstructionContent.generated.ts");
export const CHAPTER_IDS = ["quick-start", "battle-formats", "formations", "interface", "turns-victory", "effects-tactics"];
const ROOT_KEYS = new Set(["schemaVersion", "title", "subtitle", "chapters"]);
const CHAPTER_KEYS = new Set(["id", "title", "kicker", "introduction", "steps", "callout", "legalTargeting", "positionDamage", "hitChance", "otherEffects", "markers", "agility", "victory", "example", "effects", "scenarios"]);
const ITEM_KEYS = new Set(["id", "title", "text"]);
const EFFECT_IDS = ["buffs", "debuffs", "control", "periodic", "casting", "cooldowns"];
const REQUIRED_TEXT_FIELDS = {
  "quick-start": ["callout"],
  formations: ["legalTargeting", "positionDamage", "hitChance", "otherEffects"],
  "turns-victory": ["agility", "victory", "example"],
};
const REQUIRED_ITEM_COUNTS = {
  "quick-start": { steps: 5 },
  interface: { markers: 9 },
  "effects-tactics": { effects: 6, scenarios: 3 },
};

function record(value, location) {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error(`${location}: expected a mapping.`);
  return value;
}
function knownKeys(value, allowed, location) {
  for (const key of Object.keys(value)) if (!allowed.has(key)) throw new Error(`${location}: unknown field '${key}'.`);
}
function text(value, location) {
  if (typeof value !== "string" || !value.trim()) throw new Error(`${location}: expected non-empty text.`);
  return value;
}
function items(value, location) {
  if (!Array.isArray(value) || value.length === 0) throw new Error(`${location}: expected a non-empty sequence.`);
  return value.map((raw, index) => {
    const item = record(raw, `${location}[${index}]`);
    knownKeys(item, ITEM_KEYS, `${location}[${index}]`);
    return { ...(item.id === undefined ? {} : { id: text(item.id, `${location}[${index}].id`) }), title: text(item.title, `${location}[${index}].title`), text: text(item.text, `${location}[${index}].text`) };
  });
}

export function validateBattleInstructionContent(value, sourceName = "manual.yaml") {
  const root = record(value, sourceName);
  knownKeys(root, ROOT_KEYS, sourceName);
  if (root.schemaVersion !== 1) throw new Error(`${sourceName}.schemaVersion: expected 1.`);
  if (!Array.isArray(root.chapters)) throw new Error(`${sourceName}.chapters: expected a sequence.`);
  const chapters = root.chapters.map((raw, index) => {
    const location = `${sourceName}.chapters[${index}]`;
    const chapter = record(raw, location);
    knownKeys(chapter, CHAPTER_KEYS, location);
    const id = text(chapter.id, `${location}.id`);
    if (id !== CHAPTER_IDS[index]) throw new Error(`${location}.id: expected '${CHAPTER_IDS[index]}'.`);
    const result = { id, title: text(chapter.title, `${location}.title`), kicker: text(chapter.kicker, `${location}.kicker`), introduction: text(chapter.introduction, `${location}.introduction`) };
    for (const key of ["callout", "legalTargeting", "positionDamage", "hitChance", "otherEffects", "agility", "victory", "example"]) {
      if (chapter[key] !== undefined) result[key] = text(chapter[key], `${location}.${key}`);
    }
    for (const key of ["steps", "markers", "effects", "scenarios"]) {
      if (chapter[key] !== undefined) result[key] = items(chapter[key], `${location}.${key}`);
    }
    for (const key of REQUIRED_TEXT_FIELDS[id] ?? []) {
      if (result[key] === undefined) throw new Error(`${location}.${key}: required for '${id}'.`);
    }
    for (const [key, count] of Object.entries(REQUIRED_ITEM_COUNTS[id] ?? {})) {
      if (result[key] === undefined) throw new Error(`${location}.${key}: required for '${id}'.`);
      if (result[key].length !== count) throw new Error(`${location}.${key}: expected exactly ${count} items.`);
    }
    if (id === "effects-tactics" && JSON.stringify(result.effects?.map((item) => item.id)) !== JSON.stringify(EFFECT_IDS)) {
      throw new Error(`${location}.effects: expected stable effect IDs ${EFFECT_IDS.join(", ")}.`);
    }
    return result;
  });
  if (chapters.length !== CHAPTER_IDS.length) throw new Error(`${sourceName}.chapters: expected exactly ${CHAPTER_IDS.length} chapters.`);
  return { title: text(root.title, `${sourceName}.title`), subtitle: text(root.subtitle, `${sourceName}.subtitle`), chapters };
}

export function parseBattleInstructionSource(sourceName, source) {
  const document = parseDocument(source, { strict: true, uniqueKeys: true, prettyErrors: true });
  if (document.errors.length) throw new Error(`${sourceName}: ${document.errors.map((error) => error.message).join("; ")}`);
  return validateBattleInstructionContent(document.toJS({ maxAliasCount: 0 }), sourceName);
}
export function renderGeneratedModule(content) {
  return `/* Generated from content/battle-instruction/manual.yaml. Do not edit directly. */\nimport type { BattleInstructionContent } from "./battleInstructionContentTypes";\n\nexport const battleInstructionContent = ${JSON.stringify(content, null, 2)} as const satisfies BattleInstructionContent;\n`;
}
export async function buildBattleInstructionContent({ check = false } = {}) {
  const source = await readFile(SOURCE_FILE, "utf8");
  const generated = renderGeneratedModule(parseBattleInstructionSource("manual.yaml", source));
  if (check) {
    let existing = "";
    try { existing = await readFile(OUTPUT_FILE, "utf8"); } catch { /* actionable error below */ }
    if (existing !== generated) throw new Error("Generated Battle Instruction content is stale. Run `npm run content:build` from web-ui.");
  } else await writeFile(OUTPUT_FILE, generated, "utf8");
}

const isDirectRun = process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href;
if (isDirectRun) buildBattleInstructionContent({ check: process.argv.includes("--check") }).catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
});
