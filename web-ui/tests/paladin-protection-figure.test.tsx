import { render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { BattleScreen } from "@/components/battle/BattleScreen";
import { resolveAsset } from "@/lib/battle/assets";
import { createFormatFixture, MockBattleProvider } from "@/lib/battle/fixture";

const MIRROR_SELECTOR = ".battle-figure.enemy img.figure-art.fallback-requested";

const FINAL_FIGURES = [
  { id: "hero.paladin.protection", faculty: "Paladin", specialization: "Protection", path: "/game-images/heroes/Paladin-Protection/figures/Paladin_Protection.png" },
  { id: "hero.paladin.retribution", faculty: "Paladin", specialization: "Retribution", path: "/game-images/heroes/Paladin-Retribution/figures/Paladin_Retribution.png" },
  { id: "hero.priest.comprehensiveness", faculty: "Priest", specialization: "Comprehensiveness", path: "/game-images/heroes/Priest-Comprehensiveness/figures/Priest_Comprehensiveness.png" },
  { id: "hero.warrior.defence", faculty: "Warrior", specialization: "Defence", path: "/game-images/heroes/Warrior-Defence/figures/Warrior_Defence.png" },
  { id: "hero.warrior.weapon_master", faculty: "Warrior", specialization: "Weapon Master", path: "/game-images/heroes/Warrior-Weapon-Master/figures/Warrior_Weapon_Master.png" },
] as const;

describe("final registered battlefield figures", () => {
  it.each(FINAL_FIGURES)("resolves $id as its requested final direct asset", ({ id, faculty, path }) => {
    expect(resolveAsset({ kind: "figure", key: id, name: "Figure", className: faculty })).toMatchObject({
      src: path,
      resolvedPath: path,
      fallback: "requested",
      status: "final",
    });
  });

  it.each(FINAL_FIGURES)("renders $id as direct images on both sides and mirrors only the enemy", async ({ id, faculty, specialization, path }) => {
    const snapshot = createFormatFixture(1);
    const friendly = snapshot.combatants["friendly.ragnar"];
    const enemy = snapshot.combatants["enemy.nighthawk"];
    Object.assign(friendly, { definitionId: id, displayName: "Friendly Figure", faculty, specialization });
    Object.assign(enemy, { definitionId: id, displayName: "Enemy Figure", faculty, specialization });

    render(<BattleScreen provider={new MockBattleProvider(snapshot)} mode="live" />);

    const friendlyImage = await screen.findByLabelText("Friendly Figure figure");
    const enemyImage = screen.getByLabelText("Enemy Figure figure");
    for (const image of [friendlyImage, enemyImage]) {
      expect(image.tagName).toBe("IMG");
      expect(image).toHaveClass("figure-art", "fallback-requested");
      const source = image.getAttribute("src") ?? "";
      expect(new URL(source, "http://localhost").pathname).toBe(path);
      expect(source).not.toMatch(/\/(?:_next|_vinext)\/image/);
    }

    expect(friendlyImage.matches(MIRROR_SELECTOR)).toBe(false);
    expect(enemyImage.matches(MIRROR_SELECTOR)).toBe(true);
  });

  it("keeps the initial-based fallback available for an unknown hero", () => {
    expect(resolveAsset({ kind: "figure", key: "hero.unknown", name: "Unknown Hero" })).toMatchObject({
      src: null,
      resolvedPath: null,
      fallback: "initials",
      status: "placeholder",
    });
  });

  it("restricts mirroring to requested enemy figure images", () => {
    const css = readFileSync("app/globals.css", "utf8");
    expect(css).toContain(`${MIRROR_SELECTOR}{transform:scaleX(-1)}`);
    expect(css).not.toContain(".battle-figure.friendly img.figure-art.fallback-requested{transform:");
  });
});
