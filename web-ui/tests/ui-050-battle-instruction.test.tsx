import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { BattleInstructionExperience } from "@/components/manual/BattleInstructionExperience";
import { duoFormationRegistry, trioFormationRegistry } from "@/lib/battle/formations";
import { createFormationCatalogue } from "./fixtures/formationCatalogue";

afterEach(() => vi.unstubAllGlobals());

function mockFormationCatalogue() {
  vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(createFormationCatalogue()), { status: 200 })));
}

describe("UI-050 Battle Instruction compendium", () => {
  it("keeps the standalone Back route and shows one of six ordered chapters", () => {
    const { container } = render(<BattleInstructionExperience />);
    expect(screen.getByRole("link", { name: /Back to Manual/i })).toHaveAttribute("href", "/stages?manual=open");
    expect(screen.getAllByRole("tab").map((tab) => tab.textContent)).toEqual([
      "01Quick Start", "02Battle Formats", "03Formations & Attack Types", "04Battle Interface", "05Turns, Rounds & Victory", "06Effects & Tactics",
    ]);
    expect(screen.getByRole("heading", { name: "Quick Start" })).toBeVisible();
    expect(screen.queryByRole("heading", { name: "Battle Formats" })).not.toBeInTheDocument();
    expect(container.querySelector(".manual-close")).not.toBeInTheDocument();
  });

  it("switches chapters through tabs, Previous/Next, keyboard, and the compact select", async () => {
    const user = userEvent.setup();
    render(<BattleInstructionExperience />);
    await user.click(screen.getByRole("button", { name: /Next Chapter/ }));
    expect(screen.getByRole("heading", { name: "Battle Formats" })).toBeVisible();
    await user.click(screen.getByRole("button", { name: /Previous Chapter/ }));
    expect(screen.getByRole("heading", { name: "Quick Start" })).toBeVisible();

    const quickStart = screen.getByRole("tab", { name: /Quick Start/ });
    quickStart.focus();
    fireEvent.keyDown(quickStart, { key: "ArrowDown" });
    expect(screen.getByRole("tab", { name: /Battle Formats/ })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tab", { name: /Battle Formats/ })).toHaveFocus();

    fireEvent.change(screen.getByLabelText("Chapter"), { target: { value: "turns-victory" } });
    expect(screen.getByRole("heading", { name: "Turns, Rounds & Victory" })).toBeVisible();
    expect(screen.getByText("Gold: 45 ÷ 100 = 45%")).toBeVisible();
    expect(screen.getByText("Crimson: 70 ÷ 200 = 35%")).toBeVisible();
  });

  it("keeps Chapter 02 formats and presents one authoritative Chapter 03 demonstration", async () => {
    mockFormationCatalogue();
    const user = userEvent.setup();
    const { container } = render(<BattleInstructionExperience />);
    await user.click(screen.getByRole("tab", { name: /Battle Formats/ }));
    expect(container.querySelectorAll(".instruction-format-grid .instruction-team-diagram")).toHaveLength(3);
    expect(screen.getAllByText("Battle Formation Options")).toHaveLength(3);
    expect(screen.getAllByText("Maximum Battle Rounds")).toHaveLength(3);
    expect([...container.querySelectorAll(".instruction-format-facts>div:last-child dd")].map((item) => item.textContent)).toEqual(["9", "13", "15"]);
    expect(container.querySelectorAll(".instruction-format-grid header span")).toHaveLength(0);
    expect(screen.getByText("No formation choice")).toBeVisible();
    expect(screen.getByText("One Front, Two Rear")).toBeVisible();
    await user.click(screen.getByRole("tab", { name: /Formations & Attack Types/ }));
    expect(screen.queryByText(/Formation position can affect legal targets/)).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "2v2 & 3v3 Battle Formation" })).toBeVisible();
    expect(screen.queryByText("INTERACTIVE DIRECT-DAMAGE GUIDE")).not.toBeInTheDocument();
    expect(await screen.findByText("front melee explanation")).toBeVisible();
    expect(container.querySelectorAll(".instruction-demo-board")).toHaveLength(1);
    expect(container.querySelectorAll(".instruction-attack-types")).toHaveLength(0);
    await user.click(screen.getByRole("button", { name: "Ranged Projectile" }));
    expect(screen.getByText("front rangedProjectile explanation")).toBeVisible();
  });

  it("keeps the non-selectable 1v1 Duel reference", async () => {
    mockFormationCatalogue();
    const user = userEvent.setup();
    const { container } = render(<BattleInstructionExperience />);
    await user.click(screen.getByRole("tab", { name: /Formations & Attack Types/ }));
    const duel = container.querySelector(".instruction-duel-reference")!;
    expect(duel).toHaveTextContent("No formation choice");
    const board = duel.querySelector<HTMLElement>(".formation-map--duel")!;
    expect(board).toHaveAccessibleName("1v1 · Duel: Friendly Hero 1 Front versus Enemy Hero 1 Front; no formation choice");
    expect([...board.querySelectorAll(".instruction-formation-slot i")].map((icon) => [icon.textContent, icon.className])).toEqual([["1", ""], ["1", "enemy"]]);
    expect([...board.querySelectorAll(".instruction-formation-slot small")].map((label) => label.textContent)).toEqual(["Front", "Front"]);
    expect(board.querySelector(".instruction-formation-vs")?.textContent).toBe("VS");
    expect(duel.querySelectorAll("button")).toHaveLength(0);
  });

  it("uses the existing side-specific coordinates for each selected 2v2 and 3v3 formation", async () => {
    mockFormationCatalogue();
    const user = userEvent.setup();
    const { container } = render(<BattleInstructionExperience />);
    await user.click(screen.getByRole("tab", { name: /Formations & Attack Types/ }));
    await screen.findByText("front melee explanation");
    const cases = [
      ["Front & Rear", duoFormationRegistry["front-rear"]],
      ["Side by Side", duoFormationRegistry["side-by-side"]],
      ["One Front, Two Rear", trioFormationRegistry["one-front-two-rear"]],
      ["Two Front, One Rear", trioFormationRegistry["two-front-one-rear"]],
      ["All Front", trioFormationRegistry["all-front"]],
    ] as const;
    for (const [label, layout] of cases) {
      await user.click(screen.getByRole("button", { name: new RegExp(`(?:2v2|3v3).*${label}`) }));
      const board = container.querySelector(".instruction-demo-board")!;
      expect(container.querySelectorAll(".instruction-demo-board")).toHaveLength(1);
      for (const side of ["friendly", "enemy"] as const) {
        const slots = [...board.querySelectorAll<HTMLElement>(`.instruction-demo-slot[data-side="${side}"]`)];
        expect(slots).toHaveLength(layout[side].length);
        for (const [index, position] of layout[side].entries()) {
          expect(slots[index]).toHaveAttribute("data-slot", String(index + 1));
          expect(slots[index]).toHaveAttribute("data-position", position.slot);
          expect(slots[index].style.left).toBe(`${position.x}%`);
        }
      }
      expect(board.querySelector(".instruction-formation-vs")?.textContent).toBe("VS");
    }
  });

  it("operates interface markers and preserves the embedded Back callback", async () => {
    const user = userEvent.setup();
    const onBack = vi.fn();
    render(<BattleInstructionExperience embedded onBackToManual={onBack} />);
    expect(screen.getByRole("button", { name: /Back to Manual/i })).toHaveAttribute("data-manual-back");
    expect(screen.queryByText("FIELD GUIDE · SIX CHAPTERS")).not.toBeInTheDocument();
    await user.click(screen.getByRole("tab", { name: /Battle Interface/ }));
    const marker = screen.getByRole("button", { name: "9. Battle Log" });
    await user.click(marker);
    expect(marker).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("heading", { name: "Battle Log" })).toBeVisible();
    await user.click(screen.getByRole("button", { name: /Back to Manual/i }));
    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it("keeps all eleven image markers selectable and retains the failed-image schematic", async () => {
    const user = userEvent.setup();
    const { container } = render(<BattleInstructionExperience />);
    await user.click(screen.getByRole("tab", { name: /Battle Interface/ }));
    const image = screen.getByAltText("Current battle screen showing its principal controls");
    expect(image).toHaveAttribute("src", "/game-images/manual/Battle_Instruction_Interface.png");
    const topics = ["Team Information", "Round & Turn Order", "Battlefield Targets", "Target Preview", "Hero Stats", "Acting Hero", "Skill Cards", "Command Confirmation", "Battle Log", "Battle Speed", "Resign"];
    for (const [index, topic] of topics.entries()) {
      const button = screen.getByRole("button", { name: `${index + 1}. ${topic}` });
      await user.click(button);
      expect(button).toHaveAttribute("aria-pressed", "true");
      expect(container.querySelector(".instruction-marker-detail h3")).toHaveTextContent(topic);
    }
    await user.click(screen.getByRole("button", { name: "4. Target Preview" }));
    expect(screen.getByText(/current target HP and estimates of direct damage and hit chance/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "5. Hero Stats" }));
    expect(screen.getByText(/gold bar-chart button/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "8. Command Confirmation" }));
    expect(screen.getByText(/Activate Cast Skill/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "10. Battle Speed" }));
    expect(screen.getByText(/Use ×1, ×1.5, or ×2/)).toBeInTheDocument();
    expect(screen.queryByText(/Auto Battle lets/)).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "11. Resign" }));
    fireEvent.error(image);
    expect(screen.getByRole("img", { name: "Battle screen layout schematic" })).toBeVisible();
    expect(screen.getByRole("button", { name: "11. Resign" })).toHaveAttribute("aria-pressed", "true");
  });

  it("keeps the embedded Gallery handoff inside the Manual menu", async () => {
    const user = userEvent.setup();
    const onBack = vi.fn();
    render(<BattleInstructionExperience embedded onBackToManual={onBack} />);
    await user.click(screen.getByRole("tab", { name: /Effects & Tactics/ }));
    const effects = screen.getByRole("tabpanel");
    expect(within(effects).getByText("Buffs")).toBeVisible();
    expect(screen.queryByRole("link", { name: /Open Hero Gallery/ })).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /Back to Manual → Hero Gallery/ }));
    expect(onBack).toHaveBeenCalledTimes(1);
  });
});
