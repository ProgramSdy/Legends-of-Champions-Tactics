import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { CHAPTER_IDS, parseBattleInstructionSource, validateBattleInstructionContent } from "../scripts/build-battle-instruction-content.mjs";

const source = readFileSync(path.join(process.cwd(), "content", "battle-instruction", "manual.yaml"), "utf8");

describe("UI-050 Battle Instruction editorial schema", () => {
  it("accepts the owner-editable six-chapter source in its fixed order", () => {
    const content = parseBattleInstructionSource("manual.yaml", source);
    expect(content.chapters.map((chapter) => chapter.id)).toEqual(CHAPTER_IDS);
    expect(content.chapters.find((chapter) => chapter.id === "formations")?.introduction).toBeUndefined();
    expect(content.chapters.find((chapter) => chapter.id === "effects-tactics")?.effects?.map((effect) => effect.id))
      .toEqual(["buffs", "debuffs", "control", "periodic", "casting", "cooldowns"]);
  });

  it("rejects stale chapter order and unstable effect identifiers", () => {
    expect(() => parseBattleInstructionSource("wrong-order.yaml", source.replace("id: quick-start", "id: battle-formats"))).toThrow(/expected 'quick-start'/);
    expect(() => parseBattleInstructionSource("wrong-effect.yaml", source.replace("id: buffs", "id: bonus"))).toThrow(/expected stable effect IDs/);
  });

  it("rejects missing chapter-specific prose and incomplete illustrated content", () => {
    const valid = parseBattleInstructionSource("manual.yaml", source);
    const validSource = () => ({ schemaVersion: 1, ...structuredClone(valid) });
    const missingFormationCopy = validSource();
    delete missingFormationCopy.chapters[2].positionDamage;
    expect(() => validateBattleInstructionContent(missingFormationCopy, "missing-formation-copy.yaml")).toThrow(/positionDamage: required for 'formations'/);

    const missingIntroduction = validSource();
    delete missingIntroduction.chapters[1].introduction;
    expect(() => validateBattleInstructionContent(missingIntroduction, "missing-introduction.yaml")).toThrow(/introduction: required for 'battle-formats'/);

    const incompleteQuickStart = validSource();
    incompleteQuickStart.chapters[0].steps.pop();
    expect(() => validateBattleInstructionContent(incompleteQuickStart, "incomplete-quick-start.yaml")).toThrow(/steps: expected exactly 5 items/);

    const incompleteInterface = validSource();
    incompleteInterface.chapters[3].markers.pop();
    expect(() => validateBattleInstructionContent(incompleteInterface, "incomplete-interface.yaml")).toThrow(/markers: expected exactly 11 items/);

    const missingTurnCopy = validSource();
    delete missingTurnCopy.chapters[4].agility;
    expect(() => validateBattleInstructionContent(missingTurnCopy, "missing-turn-copy.yaml")).toThrow(/agility: required for 'turns-victory'/);

    const incompleteTactics = validSource();
    incompleteTactics.chapters[5].scenarios.pop();
    expect(() => validateBattleInstructionContent(incompleteTactics, "incomplete-tactics.yaml")).toThrow(/scenarios: expected exactly 3 items/);
  });
});
