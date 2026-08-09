import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { TeamBuilder } from "@/components/battle/TeamBuilder";
import { fetchHeroRoster } from "@/lib/battle/liveProvider";

const roster = [
  ["hero.priest.comprehensiveness", "Aurelia", "Priest", "Comprehensiveness"],
  ["hero.priest.discipline", "Seraphine", "Priest", "Discipline"],
  ["hero.paladin.retribution", "Valerius", "Paladin", "Retribution"],
  ["hero.paladin.protection", "Bastion", "Paladin", "Protection"],
  ["hero.paladin.holy", "Galahad", "Paladin", "Holy"],
  ["hero.mage.comprehensiveness", "Lyra", "Mage", "Comprehensiveness"],
  ["hero.warrior.defence", "Aegis", "Warrior", "Defence"],
  ["hero.warrior.weapon_master", "Ragnar", "Warrior", "Weapon Master"],
  ["hero.warrior.berserker", "Wrathe", "Warrior", "Berserker"],
  ["hero.rogue.comprehensiveness", "Nighthawk", "Rogue", "Comprehensiveness"],
].map(([definitionId, displayName, faculty, specialization]) => ({ definitionId, displayName, faculty, specialization }));

describe("UI-014 fixed slots and roster exploration", () => {
  it("accepts the complete ten-hero adapter roster, including new definitions", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(new Response(JSON.stringify({
      contractVersion: "1.0",
      heroes: roster,
    }), { status: 200, headers: { "Content-Type": "application/json" } }));

    await expect(fetchHeroRoster("http://adapter.test")).resolves.toEqual(roster);
    expect(fetchMock).toHaveBeenCalledOnce();
    fetchMock.mockRestore();
  });

  it.each([[1, 1], [2, 2], [3, 3]] as const)("renders three fixed player and enemy positions with only %i enabled", async (size, enabled) => {
    const user = userEvent.setup();
    render(<TeamBuilder roster={roster} onStart={vi.fn()} />);
    await user.click(screen.getByRole("radio", { name: `${size}v${size}` }));
    expect(document.querySelector(".player-slots")).toHaveAttribute("data-fixed-slot-count", "3");
    expect(document.querySelectorAll("[data-player-slot]")).toHaveLength(3);
    expect(document.querySelectorAll("[data-player-slot][data-slot-enabled='true']")).toHaveLength(enabled);
    expect(document.querySelectorAll("[data-player-slot][disabled]")).toHaveLength(3 - enabled);
    expect(document.querySelectorAll("[data-enemy-slot]")).toHaveLength(3);
    expect(document.querySelectorAll("[data-enemy-slot][data-slot-enabled='true']")).toHaveLength(enabled);
    expect(document.querySelectorAll("[data-enemy-slot].disabled")).toHaveLength(3 - enabled);
    expect(document.querySelector(".enemy-slot-list, .random-enemy-slots")?.parentElement).not.toBeNull();
  });

  it("uses Hero 1–3 terminology and never exposes catalogue names in slot or matrix controls", () => {
    render(<TeamBuilder roster={roster} onStart={vi.fn()} />);
    expect(screen.getAllByText("HERO 1")).toHaveLength(2);
    expect(screen.getAllByText("HERO 2")).toHaveLength(2);
    expect(screen.getAllByText("HERO 3")).toHaveLength(2);
    expect(screen.queryByText("Aurelia")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Aurelia|Galahad|Ragnar/i })).not.toBeInTheDocument();
    for (const button of screen.getAllByRole("button", { name: /Assign /i })) {
      expect(button).toHaveAccessibleName(/(Priest|Paladin|Mage|Warrior|Rogue) · /);
      expect(button).not.toHaveAccessibleName(/Aurelia|Galahad|Ragnar|Wrathe|Nighthawk/);
    }
  });

  it("filters by roster-derived faculty and All restores all entries without changing active selection", async () => {
    const user = userEvent.setup();
    render(<TeamBuilder roster={roster} onStart={vi.fn()} />);
    const activeBefore = document.querySelector("[data-player-slot='0']")?.getAttribute("aria-pressed");
    expect(screen.getAllByRole("button", { name: /Assign /i })).toHaveLength(5);
    await user.click(screen.getByRole("button", { name: "Paladin" }));
    expect(screen.getAllByRole("button", { name: /Assign /i })).toHaveLength(3);
    expect(screen.getAllByRole("button", { name: /Assign /i }).every((button) => button.textContent?.includes("Paladin"))).toBe(true);
    await user.click(screen.getByRole("button", { name: "All" }));
    expect(screen.getAllByRole("button", { name: /Assign /i })).toHaveLength(5);
    expect(document.querySelector("[data-player-slot='0']")).toHaveAttribute("aria-pressed", activeBefore ?? "true");
  });

  it("pages the filtered matrix with accessible bounded previous/next arrows", async () => {
    const user = userEvent.setup();
    render(<TeamBuilder roster={roster} onStart={vi.fn()} />);
    const previous = screen.getByRole("button", { name: "Previous heroes" });
    const next = screen.getByRole("button", { name: "Next heroes" });
    expect(previous).toBeDisabled();
    expect(next).not.toBeDisabled();
    await user.click(next);
    expect(screen.getByText(/2\s*\/\s*2/)).toBeVisible();
    expect(previous).not.toBeDisabled();
    await user.click(next);
    expect(next).toBeDisabled();
    await user.click(previous);
    expect(screen.getByText(/1\s*\/\s*2/)).toBeVisible();
  });

  it("keeps random mode compact and Python-owned, while specified mode retains accessible enemy selects", async () => {
    const user = userEvent.setup();
    render(<TeamBuilder roster={roster} onStart={vi.fn()} />);
    expect(screen.getByText("PYTHON SELECTED")).toBeVisible();
    expect(screen.queryByText(/Python will assemble the enemy team/i)).not.toBeInTheDocument();
    await user.click(screen.getByRole("radio", { name: "Choose team" }));
    expect(screen.getAllByRole("combobox", { name: /Hero [123]/i })).toHaveLength(1);
    expect(screen.queryByRole("combobox", { name: "Hero 2" })).not.toBeInTheDocument();
  });

  it("does not submit disabled player slots and keeps new hero IDs in ordered payloads", async () => {
    const user = userEvent.setup();
    const onStart = vi.fn();
    render(<TeamBuilder roster={roster} onStart={onStart} />);
    await user.click(screen.getByRole("button", { name: "Warrior" }));
    await user.click(screen.getByRole("button", { name: /Assign Warrior · Berserker/i }));
    await user.click(screen.getByRole("button", { name: "ENTER BATTLE" }));
    expect(onStart).toHaveBeenCalledWith(expect.objectContaining({ playerTeam: ["hero.warrior.berserker"] }));
    expect(onStart.mock.calls[0][0].playerTeam).toHaveLength(1);
  });

  it("replaces failed new-hero imagery with the standard fallback", () => {
    render(<TeamBuilder roster={roster} onStart={vi.fn()} />);
    const card = document.querySelector<HTMLElement>('[data-hero-id="hero.paladin.holy"]')!;
    const image = card.querySelector<HTMLImageElement>("img");
    if (image) {
      fireEvent.error(image);
      expect(card.querySelector(".asset-fallback")).not.toBeNull();
      expect(card.querySelector("img")).toBeNull();
    } else {
      expect(card.querySelector(".asset-fallback")).not.toBeNull();
    }
  });
});
