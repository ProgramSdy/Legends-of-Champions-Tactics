import { describe, expect, it } from "vitest";
import { heroGalleryContent } from "@/lib/manual/heroGalleryContent";
import {
  APPROVED_HERO_SKILLS,
  parseHeroGallerySource,
  validateHeroGalleryDocuments,
} from "../scripts/build-hero-gallery-content.mjs";

function validDocuments() {
  return Object.entries(heroGalleryContent).map(([definitionId, content]) => ({
    sourceName: `${definitionId}.yaml`,
    value: {
      schemaVersion: 1,
      definitionId,
      introduction: content.introduction,
      battleStyle: content.battleStyle,
      skills: Object.entries(content.skills).map(([skillId, skill]) => ({
        skillId,
        introduction: skill.introduction,
        ...(skill.tips ? { tips: skill.tips.map((tip) => ({ ...tip })) } : {}),
      })),
    },
  }));
}

describe("UI-028 Hero Gallery editorial content", () => {
  it("covers every approved stable hero and skill ID and preserves migrated wording", () => {
    expect(Object.keys(heroGalleryContent).sort()).toEqual(Object.keys(APPROVED_HERO_SKILLS).sort());
    for (const [definitionId, expectedSkillIds] of Object.entries(APPROVED_HERO_SKILLS)) {
      expect(Object.keys(heroGalleryContent[definitionId].skills)).toEqual(expectedSkillIds);
    }
    expect(heroGalleryContent["hero.priest.comprehensiveness"].introduction).toBe(
      "A versatile priest who balances holy restoration with shadow pressure.",
    );
    expect(heroGalleryContent["hero.paladin.protection"].skills["skill.paladin.hammer_of_revenge"].introduction).toBe(
      "A ranged holy retaliation that responds to the caster's debuffs.",
    );
  });

  it("rejects duplicate YAML keys and malformed YAML with the source name", () => {
    expect(() => parseHeroGallerySource("duplicate.yaml", "schemaVersion: 1\nschemaVersion: 1\n"))
      .toThrow(/duplicate\.yaml:.*Map keys must be unique/s);
    expect(() => parseHeroGallerySource("malformed.yaml", "skills: [\n"))
      .toThrow(/malformed\.yaml:/);
  });

  it("rejects mechanical fields, duplicate skills, and missing heroes with actionable IDs", () => {
    const mechanical = validDocuments();
    Object.assign(mechanical[0].value.skills[0], { baseDamage: 99 });
    expect(() => validateHeroGalleryDocuments(mechanical)).toThrow(/unknown field 'baseDamage'.*do not belong/s);

    const duplicate = validDocuments();
    duplicate[0].value.skills.push({ ...duplicate[0].value.skills[0] });
    expect(() => validateHeroGalleryDocuments(duplicate)).toThrow(/duplicate skill ID/);

    expect(() => validateHeroGalleryDocuments(validDocuments().slice(1))).toThrow(/missing required hero IDs/);
  });

  it("rejects stale skill IDs and missing required editorial copy", () => {
    const stale = validDocuments();
    stale[0].value.skills[0].skillId = "skill.stale.unknown";
    expect(() => validateHeroGalleryDocuments(stale)).toThrow(/unknown or stale skill ID/);

    const missingCopy = validDocuments();
    delete missingCopy[0].value.skills[0].introduction;
    expect(() => validateHeroGalleryDocuments(missingCopy)).toThrow(/introduction: expected non-empty text/);
  });

  it("accepts multiline editorial copy and optional labelled tips", () => {
    const documents = validDocuments();
    documents[0].value.introduction = "First line.\nSecond line.";
    documents[0].value.skills[0].tips = [{ label: "Strategy Tip", text: "Keep pressure.\nThen reposition." }];
    const registry = validateHeroGalleryDocuments(documents);
    expect(registry[documents[0].value.definitionId].introduction).toContain("\n");
    expect(registry[documents[0].value.definitionId].skills[documents[0].value.skills[0].skillId].tips[0].text).toContain("\n");
  });
});
