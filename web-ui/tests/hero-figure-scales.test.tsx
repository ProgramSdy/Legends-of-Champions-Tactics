import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { BattleScreen } from "@/components/battle/BattleScreen";
import { heroFigureScaleFor, heroFigureScales } from "@/lib/battle/assets";
import { createFormatFixture, MockBattleProvider } from "@/lib/battle/fixture";

const OWNER_CONFIGURED_SCALES = {
  "hero.paladin.protection": 1.2,
  "hero.paladin.retribution": 1.2,
  "hero.priest.comprehensiveness": 1,
  "hero.priest.discipline": 1,
  "hero.mage.comprehensiveness": 0.9,
  "hero.warrior.defence": 1.2,
  "hero.warrior.weapon_master": 1.1,
  "hero.rogue.comprehensiveness": 1,
} as const;

const originalScales = { ...heroFigureScales };

afterEach(() => {
  for (const key of Object.keys(heroFigureScales)) delete heroFigureScales[key];
  Object.assign(heroFigureScales, originalScales);
});

describe("per-definition hero figure scales", () => {
  it.each(Object.entries(OWNER_CONFIGURED_SCALES))("uses the owner-configured scale for %s", (definitionId, expectedScale) => {
    expect(heroFigureScales[definitionId]).toBe(expectedScale);
  });

  it("uses 1.0 for an unknown definition id", () => {
    expect(heroFigureScaleFor("hero.unknown.definition")).toBe(1);
    heroFigureScales["hero.invalid"] = 0;
    expect(heroFigureScaleFor("hero.invalid")).toBe(1);
  });

  it("multiplies formation scale by each hero's configured scale", async () => {
    heroFigureScales["hero.warrior.defence"] = 1.2;
    heroFigureScales["hero.mage.comprehensiveness"] = 0.9;
    const snapshot = createFormatFixture(3);
    Object.assign(snapshot.combatants["friendly.ragnar"], {
      definitionId: "hero.warrior.defence", displayName: "Scaled Warrior", faculty: "Warrior",
    });
    Object.assign(snapshot.combatants["enemy.andonidas"], {
      definitionId: "hero.mage.comprehensiveness", displayName: "Scaled Mage", faculty: "Mage",
    });

    render(<BattleScreen provider={new MockBattleProvider(snapshot)} />);
    await screen.findByRole("region", { name: "Battlefield" });

    const readFigureScale = (name: string) => {
      const figure = screen.getByRole("button", { name }) .closest(".battle-figure")!;
      const owner = figure.style.getPropertyValue("--figure-scale") ? figure : figure.parentElement!;
      return Number(owner.style.getPropertyValue("--figure-scale"));
    };

    // Trio front formation is 1.02; enemy centre formation is .94.
    expect(readFigureScale("Scaled Warrior")).toBeCloseTo(1.02 * 1.2);
    expect(readFigureScale("Scaled Mage")).toBeCloseTo(0.94 * 0.9);
  });

  it("does not alter final-image dimensions or enemy mirroring", async () => {
    const snapshot = createFormatFixture(1);
    Object.assign(snapshot.combatants["friendly.ragnar"], { definitionId: "hero.warrior.defence", displayName: "Friendly Figure", faculty: "Warrior" });
    Object.assign(snapshot.combatants["enemy.nighthawk"], { definitionId: "hero.warrior.defence", displayName: "Enemy Figure", faculty: "Warrior" });

    render(<BattleScreen provider={new MockBattleProvider(snapshot)} />);
    const friendly = await screen.findByLabelText("Friendly Figure figure");
    const enemy = screen.getByLabelText("Enemy Figure figure");
    expect(friendly).toHaveAttribute("width", "160");
    expect(friendly).toHaveAttribute("height", "160");
    expect(enemy).toHaveAttribute("width", "160");
    expect(enemy).toHaveAttribute("height", "160");
    expect(enemy.closest(".battle-figure")).toHaveClass("enemy");
  });
});
