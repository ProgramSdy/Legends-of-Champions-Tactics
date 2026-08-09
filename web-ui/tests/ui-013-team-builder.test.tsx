import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { TeamBuilder } from "@/components/battle/TeamBuilder";
import GamePage from "@/app/game/page";

vi.mock("@/components/battle/BattleExperience", () => ({
  BattleExperience: ({ selectedStageId }: { selectedStageId?: string }) => (
    <div data-testid="battle-experience-stage">{selectedStageId}</div>
  ),
}));

const roster = [
  ["hero.priest.comprehensiveness", "Aldric", "Priest", "Comprehensiveness"],
  ["hero.priest.discipline", "Brenna", "Priest", "Discipline"],
  ["hero.paladin.retribution", "Cael", "Paladin", "Retribution"],
  ["hero.paladin.protection", "Daria", "Paladin", "Protection"],
  ["hero.mage.comprehensiveness", "Elyra", "Mage", "Comprehensiveness"],
  ["hero.warrior.defence", "Falk", "Warrior", "Defence"],
  ["hero.warrior.weapon_master", "Garran", "Warrior", "Weapon Master"],
  ["hero.rogue.comprehensiveness", "Hessa", "Rogue", "Comprehensiveness"],
].map(([definitionId, displayName, faculty, specialization]) => ({ definitionId, displayName, faculty, specialization }));

describe("UI-013 Team Builder slot and matrix contracts", () => {
  it("passes the selected stage from /game?stage=arena into BattleExperience", async () => {
    render(await GamePage({ searchParams: Promise.resolve({ stage: "arena" }) }));
    expect(screen.getByTestId("battle-experience-stage")).toHaveTextContent("arena");
  });

  it.each([
    [1, 1],
    [2, 2],
    [3, 3],
  ] as const)("renders %iv%i player slots and keeps active assignment within the resized team", async (size, expected) => {
    const user = userEvent.setup();
    render(<TeamBuilder roster={roster} onStart={vi.fn()} />);
    await user.click(screen.getByRole("radio", { name: `${size}v${size}` }));
    const slots = [...document.querySelectorAll<HTMLElement>("[data-player-slot]")];
    expect(slots).toHaveLength(3);
    expect(slots.filter((slot) => slot.dataset.slotEnabled === "true")).toHaveLength(expected);
    expect(slots.some((slot) => slot.getAttribute("aria-pressed") === "true")).toBe(true);
    expect(screen.getByRole("heading", { name: "Hero Selection Matrix" })).toBeVisible();
  });

  it("assigns matrix cards only to the active player slot, preserves duplicates, and submits ordered IDs", async () => {
    const user = userEvent.setup();
    const onStart = vi.fn();
    render(<TeamBuilder roster={roster} onStart={onStart} />);
    await user.click(screen.getByRole("radio", { name: "3v3" }));
    const slot = (index: number) => document.querySelector<HTMLElement>(`[data-player-slot="${index}"]`)!;
    await user.click(slot(0));
    await user.click(document.querySelector<HTMLElement>('[data-hero-id="hero.paladin.retribution"]')!);
    await user.click(slot(1));
    await user.click(document.querySelector<HTMLElement>('[data-hero-id="hero.paladin.retribution"]')!);
    await user.click(slot(2));
    await user.click(document.querySelector<HTMLElement>('[data-hero-id="hero.mage.comprehensiveness"]')!);
    expect(slot(0)).toHaveAttribute("aria-pressed", "false");
    expect(slot(2)).toHaveAttribute("aria-pressed", "true");
    await user.click(screen.getByRole("button", { name: "ENTER BATTLE" }));
    expect(onStart).toHaveBeenCalledWith(expect.objectContaining({
      battleSize: 3,
      playerTeam: ["hero.paladin.retribution", "hero.paladin.retribution", "hero.mage.comprehensiveness"],
      enemyCompositionMode: "random",
      enemyControlMode: "computer",
    }));
  });

  it("supports keyboard activation of a player slot and matrix card", async () => {
    const user = userEvent.setup();
    const onStart = vi.fn();
    render(<TeamBuilder roster={roster} onStart={onStart} />);
    await user.click(screen.getByRole("radio", { name: "2v2" }));
    const slot = document.querySelector<HTMLElement>('[data-player-slot="0"]')!;
    const secondSlot = document.querySelector<HTMLElement>('[data-player-slot="1"]')!;
    secondSlot.focus();
    await user.keyboard("{Enter}");
    expect(slot).toHaveAttribute("aria-pressed", "false");
    expect(secondSlot).toHaveAttribute("aria-pressed", "true");
    screen.getByRole("button", { name: /Assign Paladin · Retribution to Hero 2/i }).focus();
    await user.keyboard("{Enter}");
    expect(document.querySelector<HTMLElement>('[data-player-slot="1"]')).toHaveTextContent(/Paladin\s*Retribution/);
  });

  it("preserves specified enemy payload, enemy control, seed, and validation", async () => {
    const user = userEvent.setup();
    const onStart = vi.fn();
    render(<TeamBuilder roster={roster} onStart={onStart} />);
    await user.click(screen.getByRole("radio", { name: "2v2" }));
    await user.click(screen.getByRole("radio", { name: "Choose team" }));
    await user.click(screen.getByRole("radio", { name: "Player" }));
    fireEvent.change(screen.getByLabelText("Hero 1"), { target: { value: roster[7].definitionId } });
    fireEvent.change(screen.getByLabelText("Hero 2"), { target: { value: roster[6].definitionId } });
    fireEvent.change(screen.getByLabelText(/Seed/i), { target: { value: "42" } });
    await user.click(screen.getByRole("button", { name: "ENTER BATTLE" }));
    expect(onStart).toHaveBeenCalledWith(expect.objectContaining({
      battleSize: 2,
      enemyCompositionMode: "specified",
      enemyTeam: [roster[7].definitionId, roster[6].definitionId],
      enemyControlMode: "player",
      seed: 42,
    }));
  });

  it("keeps random mode free of enemyTeam and explains Python authority", () => {
    render(<TeamBuilder roster={roster} onStart={vi.fn()} />);
    expect(screen.getByText("PYTHON SELECTED")).toBeVisible();
    expect(screen.queryByLabelText("Hero 1")).not.toBeInTheDocument();
  });

  it("shows the canonical Arena stage preview, direct-visit fallback, and back navigation", () => {
    render(<TeamBuilder roster={roster} onStart={vi.fn()} />);
    expect(screen.getByRole("heading", { name: "Arena" })).toBeVisible();
    expect(screen.getByRole("link", { name: /Back to Stage Map/i })).toHaveAttribute("href", "/stages");
    const map = document.querySelector(".current-stage-map");
    expect(map).toHaveAttribute("src", "/game-images/Stage_Map/valley_of_champions.png");
  });

  it("renders every roster entry across bounded matrix pages with fallback-safe media", async () => {
    const user = userEvent.setup();
    render(<TeamBuilder roster={roster} onStart={vi.fn()} />);
    const seen = new Set<string>();
    let page = 0;
    while (true) {
      for (const card of [...document.querySelectorAll<HTMLElement>("[data-hero-id]")]) {
        const id = card.dataset.heroId;
        if (id) seen.add(id);
        expect(card.querySelector(".asset-fallback, img")).not.toBeNull();
      }
      const next = screen.getByRole("button", { name: "Next heroes" });
      if (next.hasAttribute("disabled")) break;
      await user.click(next);
      page += 1;
      expect(page).toBeLessThan(10);
    }
    expect(seen).toEqual(new Set(roster.map((hero) => hero.definitionId)));
  });

  it("replaces a failed matrix image with the established fallback instead of a broken image", () => {
    render(<TeamBuilder roster={roster} onStart={vi.fn()} />);
    const card = document.querySelector<HTMLElement>('[data-hero-id="hero.mage.comprehensiveness"]')!;
    const image = card.querySelector<HTMLImageElement>("img");
    expect(image).not.toBeNull();
    fireEvent.error(image!);
    expect(card.querySelector(".asset-fallback")).not.toBeNull();
    expect(card.querySelector("img")).toBeNull();
  });
});
