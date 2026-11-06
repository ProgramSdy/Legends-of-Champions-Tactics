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
    expect(screen.getByLabelText("3v3 · One Front, Two Rear: Front, Rear, Rear")).toBeVisible();
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
