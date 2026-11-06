import { fireEvent, render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { HeroCard } from "@/components/battle/HeroCard";
import { resolveAsset } from "@/lib/battle/assets";
import { createFormatFixture } from "@/lib/battle/fixture";

const professionIcons = [
  ["hero.warrior.weapon_master", "Warrior", "warrior_weapon_master_profession_v01.png"],
  ["hero.warrior.defence", "Warrior", "warrior_defence_profession_v01.png"],
  ["hero.warrior.berserker", "Warrior", "warrior_berserker_profession_v01.png"],
  ["hero.paladin.retribution", "Paladin", "paladin_retribution_profession_v01.png"],
  ["hero.paladin.protection", "Paladin", "paladin_protection_profession_v01.png"],
  ["hero.paladin.holy", "Paladin", "paladin_holy_profession_v01.png"],
] as const;

describe("UI-052 Battle profession badges", () => {
  it.each(professionIcons)("maps %s to its exact owner icon", (definitionId, faculty, file) => {
    expect(resolveAsset({ kind: "profession", key: definitionId, name: faculty, className: faculty })).toMatchObject({
      src: `/game-images/professions/icons/${file}`,
      fallback: "requested",
      status: "final",
    });
  });

  it("renders the same definition icon on friendly and enemy cards without changing the card hierarchy", () => {
    const template = createFormatFixture(1).combatants["friendly.ragnar"];
    const friendly = { ...template, id: "friendly.one", sideId: "friendly" as const, displayName: "Ragnar" };
    const enemy = { ...template, id: "enemy.one", sideId: "enemy" as const, displayName: "Galahad" };
    const { container } = render(<><HeroCard hero={friendly} active onViewStats={() => {}} /><HeroCard hero={enemy} /></>);
    const cards = [...container.querySelectorAll(".hero-card")];
    expect(cards).toHaveLength(2);
    expect(cards[0]).toHaveClass("friendly", "active");
    expect(cards[1]).toHaveClass("enemy");
    for (const card of cards) {
      expect(card.querySelector(".hero-title .class-icon")?.getAttribute("src")).toContain("/game-images/professions/icons/warrior_weapon_master_profession_v01.png");
      expect(card.querySelector(".meter-row")).toBeInTheDocument();
      expect(card.querySelector(".status-row")).toBeInTheDocument();
    }
    expect(cards[0].querySelector(".hero-stats-button")).toBeInTheDocument();
  });

  it("retains the class or initials fallback for unprovided heroes and failed art", () => {
    const template = createFormatFixture(1).combatants["friendly.ragnar"];
    const { container, rerender } = render(<HeroCard hero={{ ...template, definitionId: "hero.warrior.unknown" }} />);
    expect(container.querySelector(".hero-title .class-icon")?.getAttribute("src")).toContain("warrior.webp");

    rerender(<HeroCard hero={{ ...template, definitionId: "hero.priest.discipline", faculty: "Priest" }} />);
    expect(container.querySelector(".hero-title .class-icon.asset-fallback")).toHaveTextContent("P");

    rerender(<HeroCard hero={{ ...template, definitionId: "hero.warrior.defence" }} />);
    const icon = container.querySelector<HTMLImageElement>(".hero-title img.class-icon");
    expect(icon?.getAttribute("src")).toContain("/game-images/professions/icons/warrior_defence_profession_v01.png");
    fireEvent.error(icon!);
    expect(container.querySelector(".hero-title .class-icon.asset-fallback")).toHaveTextContent("W");
    expect(container.querySelector(".hero-title img.class-icon")).not.toBeInTheDocument();
  });
});
