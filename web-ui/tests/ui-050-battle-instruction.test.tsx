import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { BattleInstructionExperience } from "@/components/manual/BattleInstructionExperience";

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

  it("shows verified formation values and selectable attack-type explanations", async () => {
    const user = userEvent.setup();
    render(<BattleInstructionExperience />);
    await user.click(screen.getByRole("tab", { name: /Battle Formats/ }));
    expect(screen.getByText("9 completed rounds")).toBeVisible();
    expect(screen.getByText("13 completed rounds")).toBeVisible();
    expect(screen.getByText("15 completed rounds")).toBeVisible();
    await user.click(screen.getByRole("tab", { name: /Formations & Attack Types/ }));
    expect(screen.getByRole("img", { name: /3v3 · One Front, Two Rear: Friendly Hero 1 Front/ })).toBeVisible();
    expect(screen.getByText("Rear attacker: 70% direct damage")).toBeVisible();
    const melee = screen.getByRole("tab", { name: "Melee" });
    const projectile = screen.getByRole("tab", { name: "Ranged Projectile" });
    const attackPanel = screen.getByRole("tabpanel", { name: "Melee" });
    expect(melee).toHaveAttribute("aria-controls", attackPanel.id);
    expect(melee).toHaveAttribute("tabindex", "0");
    expect(projectile).toHaveAttribute("tabindex", "-1");
    melee.focus();
    fireEvent.keyDown(melee, { key: "ArrowRight" });
    expect(projectile).toHaveFocus();
    expect(projectile).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tabpanel", { name: "Ranged Projectile" })).toHaveAttribute("aria-labelledby", projectile.id);
    expect(screen.getByText("Rear → Rear: 60%")).toBeVisible();
    await user.click(screen.getByRole("tab", { name: "Ranged Instant" }));
    expect(screen.getByText("No formation damage adjustment: 100%")).toBeVisible();
  });

  it("places 2v2 Front/Rear near the enemy and Side by Side vertically from the battle registry", async () => {
    const user = userEvent.setup();
    const { container } = render(<BattleInstructionExperience />);
    await user.click(screen.getByRole("tab", { name: /Battle Formats/ }));
    expect(container.querySelectorAll(".instruction-format-grid .instruction-team-diagram")).toHaveLength(3);
    expect(container.querySelector(".instruction-format-grid .formation-map")).not.toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: /Formations & Attack Types/ }));
    const twoHeroBoards = container.querySelectorAll(".instruction-formation-board.formation-map:not(.formation-map--trio)");
    expect(twoHeroBoards).toHaveLength(2);
    expect(twoHeroBoards[0]).toHaveAccessibleName(/Friendly Hero 1 Front \(near centre\), Hero 2 Rear \(farther out\); Enemy Hero 1 Front \(near centre\), Hero 2 Rear \(farther out\)/);
    expect(twoHeroBoards[1]).toHaveAccessibleName(/Friendly Hero 1 Front \(upper\), Hero 2 Front \(lower\); Enemy Hero 1 Front \(upper\), Hero 2 Front \(lower\)/);
    const slot = (board: Element, side: string, number: number) => board.querySelector<HTMLElement>(`.instruction-formation-slot[data-side="${side}"][data-slot="${number}"]`)!;
    const x = (element: HTMLElement) => parseFloat(element.style.left);
    const y = (element: HTMLElement) => parseFloat(element.style.top);
    const frontRear = twoHeroBoards[0];
    expect(x(slot(frontRear, "friendly", 1))).toBeGreaterThan(x(slot(frontRear, "friendly", 2)));
    expect(x(slot(frontRear, "enemy", 1))).toBeLessThan(x(slot(frontRear, "enemy", 2)));
    expect(y(slot(frontRear, "friendly", 1))).toBe(y(slot(frontRear, "friendly", 2)));
    expect(y(slot(frontRear, "enemy", 1))).toBe(y(slot(frontRear, "enemy", 2)));
    const sideBySide = twoHeroBoards[1];
    for (const side of ["friendly", "enemy"]) {
      expect(x(slot(sideBySide, side, 1))).toBe(x(slot(sideBySide, side, 2)));
      expect(y(slot(sideBySide, side, 1))).toBeLessThan(y(slot(sideBySide, side, 2)));
    }
    for (const board of twoHeroBoards) {
      expect([...board.querySelectorAll(".instruction-formation-slot i")].map((icon) => [icon.textContent, icon.className])).toEqual([["1", ""], ["2", ""], ["1", "enemy"], ["2", "enemy"]]);
      expect(board.querySelectorAll(".instruction-formation-slot small")).toHaveLength(4);
      expect(board.querySelector(".instruction-formation-vs")?.textContent).toBe("VS");
    }
    expect([...frontRear.querySelectorAll(".instruction-formation-slot small")].map((label) => label.textContent)).toEqual(["Front", "Rear", "Front", "Rear"]);
    expect(container.querySelectorAll(".instruction-formation-board.formation-map--trio")).toHaveLength(3);
  });

  it("maps all three 3v3 diagrams to the side-specific battle slot coordinates", async () => {
    const user = userEvent.setup();
    const { container } = render(<BattleInstructionExperience />);
    await user.click(screen.getByRole("tab", { name: /Formations & Attack Types/ }));
    const boards = [...container.querySelectorAll(".instruction-formation-board.formation-map--trio")];
    expect(boards).toHaveLength(3);
    const slot = (board: Element, side: string, number: number) => board.querySelector<HTMLElement>(`.instruction-formation-slot[data-side="${side}"][data-slot="${number}"]`)!;
    const x = (element: HTMLElement) => parseFloat(element.style.left);
    const y = (element: HTMLElement) => parseFloat(element.style.top);
    for (const board of boards) {
      expect(board).toHaveAttribute("role", "img");
      expect(board.querySelectorAll(".instruction-formation-slot i")).toHaveLength(6);
      expect(board.querySelectorAll(".instruction-formation-slot i.enemy")).toHaveLength(3);
      expect(board.querySelectorAll(".instruction-formation-slot small")).toHaveLength(6);
      expect(board.querySelectorAll(":scope > span")).toHaveLength(0);
      expect(board.querySelector(".instruction-formation-vs")?.textContent).toBe("VS");
    }
    const [oneFront, twoFront, allFront] = boards;
    expect(oneFront).toHaveAccessibleName(/Hero 3 Rear \(upper, farther out\); Enemy Hero 1 Front.*Hero 2 Rear \(upper, farther out\)/);
    expect(x(slot(oneFront, "friendly", 1))).toBeGreaterThan(x(slot(oneFront, "friendly", 2)));
    expect(x(slot(oneFront, "friendly", 2))).toBe(x(slot(oneFront, "friendly", 3)));
    expect(y(slot(oneFront, "friendly", 3))).toBeLessThan(y(slot(oneFront, "friendly", 1)));
    expect(y(slot(oneFront, "friendly", 1))).toBeLessThan(y(slot(oneFront, "friendly", 2)));
    expect(x(slot(oneFront, "enemy", 1))).toBeLessThan(x(slot(oneFront, "enemy", 2)));
    expect(x(slot(oneFront, "enemy", 2))).toBe(x(slot(oneFront, "enemy", 3)));
    expect(y(slot(oneFront, "enemy", 2))).toBeLessThan(y(slot(oneFront, "enemy", 1)));
    expect(y(slot(oneFront, "enemy", 1))).toBeLessThan(y(slot(oneFront, "enemy", 3)));

    expect(twoFront).toHaveAccessibleName(/Friendly Hero 1 Front \(upper, near centre\).*Hero 3 Rear \(middle, farther out\); Enemy Hero 1 Front \(lower, near centre\).*Hero 2 Front \(upper, near centre\)/);
    expect(x(slot(twoFront, "friendly", 1))).toBe(x(slot(twoFront, "friendly", 2)));
    expect(x(slot(twoFront, "friendly", 1))).toBeGreaterThan(x(slot(twoFront, "friendly", 3)));
    expect(y(slot(twoFront, "friendly", 1))).toBeLessThan(y(slot(twoFront, "friendly", 3)));
    expect(y(slot(twoFront, "friendly", 3))).toBeLessThan(y(slot(twoFront, "friendly", 2)));
    expect(x(slot(twoFront, "enemy", 1))).toBe(x(slot(twoFront, "enemy", 2)));
    expect(x(slot(twoFront, "enemy", 1))).toBeLessThan(x(slot(twoFront, "enemy", 3)));
    expect(y(slot(twoFront, "enemy", 2))).toBeLessThan(y(slot(twoFront, "enemy", 3)));
    expect(y(slot(twoFront, "enemy", 3))).toBeLessThan(y(slot(twoFront, "enemy", 1)));
    expect(slot(twoFront, "friendly", 3)).toHaveAttribute("data-position", "rear");
    expect(slot(twoFront, "enemy", 3)).toHaveAttribute("data-position", "rear");

    expect(allFront).toHaveAccessibleName(/Friendly Hero 1 Front \(upper\), Hero 2 Front \(middle\), Hero 3 Front \(lower\); Enemy Hero 1 Front \(lower\), Hero 2 Front \(middle\), Hero 3 Front \(upper\)/);
    for (const side of ["friendly", "enemy"]) {
      expect(x(slot(allFront, side, 1))).toBe(x(slot(allFront, side, 2)));
      expect(x(slot(allFront, side, 2))).toBe(x(slot(allFront, side, 3)));
      for (const number of [1, 2, 3]) expect(slot(allFront, side, number)).toHaveAttribute("data-position", "front");
    }
    expect(y(slot(allFront, "friendly", 1))).toBeLessThan(y(slot(allFront, "friendly", 2)));
    expect(y(slot(allFront, "friendly", 2))).toBeLessThan(y(slot(allFront, "friendly", 3)));
    expect(y(slot(allFront, "enemy", 3))).toBeLessThan(y(slot(allFront, "enemy", 2)));
    expect(y(slot(allFront, "enemy", 2))).toBeLessThan(y(slot(allFront, "enemy", 1)));
  });

  it("operates interface markers and preserves the embedded Back callback", async () => {
    const user = userEvent.setup();
    const onBack = vi.fn();
    render(<BattleInstructionExperience embedded onBackToManual={onBack} />);
    expect(screen.getByRole("button", { name: /Back to Manual/i })).toHaveAttribute("data-manual-back");
    await user.click(screen.getByRole("tab", { name: /Battle Interface/ }));
    const marker = screen.getByRole("button", { name: "7. Battle Log" });
    await user.click(marker);
    expect(marker).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("heading", { name: "Battle Log" })).toBeVisible();
    await user.click(screen.getByRole("button", { name: /Back to Manual/i }));
    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it("keeps all nine image markers selectable and retains the failed-image schematic", async () => {
    const user = userEvent.setup();
    const { container } = render(<BattleInstructionExperience />);
    await user.click(screen.getByRole("tab", { name: /Battle Interface/ }));
    const image = screen.getByAltText("Current battle screen showing its principal controls");
    expect(image).toHaveAttribute("src", "/game-images/manual/Battle_Instruction_Interface.png");
    const topics = ["Team Information", "Round & Turn Order", "Battlefield Targets", "Acting Hero", "Skill Cards", "Preview & Confirmation", "Battle Log", "Speed & Auto Battle", "Resign"];
    for (const [index, topic] of topics.entries()) {
      const button = screen.getByRole("button", { name: `${index + 1}. ${topic}` });
      await user.click(button);
      expect(button).toHaveAttribute("aria-pressed", "true");
      expect(container.querySelector(".instruction-marker-detail h3")).toHaveTextContent(topic);
    }
    await user.click(screen.getByRole("button", { name: "6. Preview & Confirmation" }));
    expect(screen.getByText(/bottom command button changes with selection/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "9. Resign" }));
    fireEvent.error(image);
    expect(screen.getByRole("img", { name: "Battle screen layout schematic" })).toBeVisible();
    expect(screen.getByRole("button", { name: "9. Resign" })).toHaveAttribute("aria-pressed", "true");
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
