import { readFile, readdir, writeFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
import { parseDocument } from "yaml";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const WEB_UI_DIR = path.resolve(SCRIPT_DIR, "..");
const CONTENT_DIR = path.join(WEB_UI_DIR, "content", "hero-gallery");
const OUTPUT_FILE = path.join(WEB_UI_DIR, "lib", "manual", "heroGalleryContent.generated.ts");

export const APPROVED_HERO_SKILLS = Object.freeze({
  "hero.mage.comprehensiveness": ["skill.mage.fireball", "skill.mage.arcane_missiles", "skill.mage.frost_bolt"],
  "hero.paladin.holy": ["skill.paladin.purify_healing", "skill.paladin.holy_blast", "skill.paladin.shield_of_protection"],
  "hero.paladin.protection": ["skill.paladin.hammer_of_revenge", "skill.paladin.shield_of_righteous", "skill.paladin.heroric_charge", "skill.paladin.holy_aura"],
  "hero.paladin.retribution": ["skill.paladin.hammer_of_anger", "skill.paladin.crusader_strike", "skill.paladin.flash_of_light"],
  "hero.priest.comprehensiveness": ["skill.priest.holy_smite", "skill.priest.shadow_word_pain", "skill.priest.binding_heal"],
  "hero.priest.discipline": ["skill.priest.penance", "skill.priest.holy_word_redemption", "skill.priest.holy_word_punishment"],
  "hero.rogue.comprehensiveness": ["skill.rogue.sharp_blade", "skill.rogue.poisoned_dagger", "skill.rogue.shadow_evasion"],
  "hero.warrior.berserker": ["skill.warrior.moon_slash", "skill.warrior.warlust", "skill.warrior.strike_of_meteorite"],
  "hero.warrior.defence": ["skill.warrior.devastate", "skill.warrior.shield_bash", "skill.warrior.thunder_pot"],
  "hero.warrior.weapon_master": ["skill.warrior.fatal_strike", "skill.warrior.armor_crush", "skill.warrior.antivenom_potion"],
});

const ROOT_KEYS = new Set(["schemaVersion", "definitionId", "introduction", "battleStyle", "skills"]);
const SKILL_KEYS = new Set(["skillId", "introduction", "tips"]);
const TIP_KEYS = new Set(["label", "text"]);

function isRecord(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function assertRecord(value, location) {
  if (!isRecord(value)) throw new Error(`${location}: expected a mapping.`);
  return value;
}

function assertKnownKeys(value, allowed, location) {
  for (const key of Object.keys(value)) {
    if (!allowed.has(key)) {
      throw new Error(`${location}: unknown field '${key}'. Mechanical values do not belong in Gallery editorial YAML.`);
    }
  }
}

function requireText(value, location) {
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new Error(`${location}: expected non-empty text.`);
  }
  return value;
}

export function validateHeroGalleryDocuments(documents) {
  const registry = {};
  for (const { sourceName, value } of documents) {
    const root = assertRecord(value, sourceName);
    assertKnownKeys(root, ROOT_KEYS, sourceName);
    if (root.schemaVersion !== 1) throw new Error(`${sourceName}.schemaVersion: expected 1.`);
    const definitionId = requireText(root.definitionId, `${sourceName}.definitionId`);
    const expectedSkills = APPROVED_HERO_SKILLS[definitionId];
    if (!expectedSkills) throw new Error(`${sourceName}.definitionId: unknown or stale hero ID '${definitionId}'.`);
    if (registry[definitionId]) throw new Error(`${sourceName}.definitionId: duplicate hero ID '${definitionId}'.`);
    if (!Array.isArray(root.skills)) throw new Error(`${sourceName}.skills: expected a sequence.`);

    const skills = {};
    for (const [index, rawSkill] of root.skills.entries()) {
      const location = `${sourceName}.skills[${index}]`;
      const skill = assertRecord(rawSkill, location);
      assertKnownKeys(skill, SKILL_KEYS, location);
      const skillId = requireText(skill.skillId, `${location}.skillId`);
      if (!expectedSkills.includes(skillId)) {
        throw new Error(`${location}.skillId: unknown or stale skill ID '${skillId}' for '${definitionId}'.`);
      }
      if (skills[skillId]) throw new Error(`${location}.skillId: duplicate skill ID '${skillId}'.`);
      let tips;
      if (skill.tips !== undefined) {
        if (!Array.isArray(skill.tips) || skill.tips.length === 0) {
          throw new Error(`${location}.tips: expected a non-empty sequence when provided.`);
        }
        tips = skill.tips.map((rawTip, tipIndex) => {
          const tipLocation = `${location}.tips[${tipIndex}]`;
          const tip = assertRecord(rawTip, tipLocation);
          assertKnownKeys(tip, TIP_KEYS, tipLocation);
          return {
            label: requireText(tip.label, `${tipLocation}.label`),
            text: requireText(tip.text, `${tipLocation}.text`),
          };
        });
      }
      skills[skillId] = {
        introduction: requireText(skill.introduction, `${location}.introduction`),
        ...(tips ? { tips } : {}),
      };
    }
    const actualSkillIds = Object.keys(skills);
    const missingSkills = expectedSkills.filter((skillId) => !actualSkillIds.includes(skillId));
    if (missingSkills.length) throw new Error(`${sourceName}.skills: missing required skill IDs: ${missingSkills.join(", ")}.`);

    registry[definitionId] = {
      introduction: requireText(root.introduction, `${sourceName}.introduction`),
      battleStyle: requireText(root.battleStyle, `${sourceName}.battleStyle`),
      skills,
    };
  }

  const missingHeroes = Object.keys(APPROVED_HERO_SKILLS).filter((definitionId) => !registry[definitionId]);
  if (missingHeroes.length) throw new Error(`Hero Gallery content is missing required hero IDs: ${missingHeroes.join(", ")}.`);
  return Object.fromEntries(Object.entries(registry).sort(([left], [right]) => left.localeCompare(right)));
}

export function parseHeroGallerySource(sourceName, source) {
  const document = parseDocument(source, { strict: true, uniqueKeys: true, prettyErrors: true });
  if (document.errors.length) {
    throw new Error(`${sourceName}: ${document.errors.map((error) => error.message).join("; ")}`);
  }
  return { sourceName, value: document.toJS({ maxAliasCount: 0 }) };
}

export async function readAndValidateHeroGalleryContent(contentDir = CONTENT_DIR) {
  const fileNames = (await readdir(contentDir)).filter((fileName) => fileName.endsWith(".yaml")).sort();
  const documents = [];
  for (const fileName of fileNames) {
    const source = await readFile(path.join(contentDir, fileName), "utf8");
    documents.push(parseHeroGallerySource(fileName, source));
  }
  return validateHeroGalleryDocuments(documents);
}

export function renderGeneratedModule(registry) {
  return `/* This file is generated from content/hero-gallery/*.yaml. Do not edit it directly. */\nimport type { HeroGalleryContentRegistry } from "./heroGalleryContentTypes";\n\nexport const heroGalleryContent = ${JSON.stringify(registry, null, 2)} as const satisfies HeroGalleryContentRegistry;\n`;
}

export async function buildHeroGalleryContent({ check = false } = {}) {
  const registry = await readAndValidateHeroGalleryContent();
  const generated = renderGeneratedModule(registry);
  if (check) {
    let existing = "";
    try { existing = await readFile(OUTPUT_FILE, "utf8"); } catch { /* actionable error below */ }
    if (existing !== generated) {
      throw new Error("Generated Hero Gallery content is stale. Run `npm run content:build` from web-ui.");
    }
    return registry;
  }
  await writeFile(OUTPUT_FILE, generated, "utf8");
  return registry;
}

const isDirectRun = process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href;
if (isDirectRun) {
  buildHeroGalleryContent({ check: process.argv.includes("--check") }).catch((error) => {
    console.error(error instanceof Error ? error.message : error);
    process.exitCode = 1;
  });
}
