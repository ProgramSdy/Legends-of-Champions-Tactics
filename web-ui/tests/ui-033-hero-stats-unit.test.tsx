import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { HeroCard } from "@/components/battle/HeroCard";
import { HeroStatsDialog } from "@/components/battle/HeroStatsDialog";
import { createFormatFixture } from "@/lib/battle/fixture";

describe("UI-033 Hero Stats components", () => {
  it("offers one isolated inspection control only when a card is occupied", async () => {
    const hero = structuredClone(createFormatFixture(1).combatants["friendly.ragnar"]);
    const open = vi.fn();
    const parentClick = vi.fn();
    const view = render(<div onClick={parentClick}><HeroCard hero={hero} onViewStats={(trigger) => open(trigger)} /></div>);

    const button = screen.getByRole("button", { name: "View Hero Stats for Ragnar, friendly slot 1" });
    expect(button).toHaveAttribute("title", "View Hero Stats");
    await userEvent.setup().click(button);
    expect(open).toHaveBeenCalledWith(button);
    expect(parentClick).not.toHaveBeenCalled();

    view.rerender(<HeroCard hero={hero} />);
    expect(screen.queryByRole("button", { name: /View Hero Stats/ })).not.toBeInTheDocument();
  });

  it("renders current authoritative values, signed deltas, active effects, and no maximum HP", async () => {
    const hero = structuredClone(createFormatFixture(1).combatants["friendly.ragnar"]);
    hero.hp = { current: 47, maximum: 102 };
    hero.stats.damage = { current: 53.5, delta: 11.5 };
    hero.stats.defence = { current: 20, delta: -11 };
    hero.stats.agility = { current: 27, delta: 0 };
    hero.stats.resistances.shadow = { current: 10.0001, delta: 0.0001 };
    hero.statuses = [{
      id: "status.warlust", instanceId: "status.warlust.1", kind: "buff",
      roundsRemaining: 2, stacks: 1, sourceCombatantId: hero.id,
    }];
    const close = vi.fn();
    render(<HeroStatsDialog hero={hero} updating={false} onClose={close} />);

    const dialog = await screen.findByRole("dialog", { name: "Ragnar" });
    expect(within(dialog).getByText("47")).toBeVisible();
    expect(within(dialog).queryByText("102")).not.toBeInTheDocument();
    expect(within(dialog).queryByRole("progressbar")).not.toBeInTheDocument();
    expect(within(dialog).getByText("53.5").closest(".hero-stat-value")).toHaveClass("positive");
    expect(within(dialog).getByText("(+11.5)")).toBeInTheDocument();
    expect(within(dialog).getByText("20").closest(".hero-stat-value")).toHaveClass("negative");
    expect(within(dialog).getByText("(−11)")).toBeInTheDocument();
    expect(within(dialog).getByText("27").closest(".hero-stat-value")).toHaveClass("neutral");
    expect(within(dialog).getByText("(+0.0001)")).toBeInTheDocument();
    expect(within(dialog).getAllByText("Warlust")).not.toHaveLength(0);
    expect(within(dialog).getByText("1 stack · 2 rounds")).toBeInTheDocument();

    fireEvent.keyDown(dialog, { key: "Escape" });
    expect(close).toHaveBeenCalledTimes(1);
  });

  it("marks attributes and effect counters as updating while keeping presented HP and effect identity", async () => {
    const hero = structuredClone(createFormatFixture(1).combatants["friendly.ragnar"]);
    hero.hp.current = 71;
    hero.statuses = [{
      id: "status.warlust", instanceId: "status.warlust.1", kind: "buff",
      roundsRemaining: 2, stacks: 1, sourceCombatantId: hero.id,
    }];
    render(<HeroStatsDialog hero={hero} updating onClose={vi.fn()} />);

    const dialog = await screen.findByRole("dialog", { name: "Ragnar" });
    expect(within(dialog).getByText("71")).toBeVisible();
    expect(within(dialog).getAllByText("Warlust")).not.toHaveLength(0);
    expect(within(dialog).queryByText("1 stack · 2 rounds")).not.toBeInTheDocument();
    expect(within(dialog).getAllByText("Updating…")).toHaveLength(11);
    expect(within(dialog).getByLabelText(/Warlust.*Status details updating/i)).not.toHaveAccessibleName(/stack|rounds remaining/i);
  });

  it("traps focus at the modal edges and starts at the close control", async () => {
    const hero = structuredClone(createFormatFixture(1).combatants["friendly.ragnar"]);
    hero.statuses = [{
      id: "status.warlust", instanceId: "status.warlust.1", kind: "buff",
      roundsRemaining: 2, stacks: null, sourceCombatantId: hero.id,
    }];
    render(<HeroStatsDialog hero={hero} updating={false} onClose={vi.fn()} />);
    const dialog = await screen.findByRole("dialog", { name: "Ragnar" });
    const close = within(dialog).getByRole("button", { name: "Close Hero Stats for Ragnar" });
    const status = within(dialog).getByLabelText(/Warlust/);
    await waitFor(() => expect(close).toHaveFocus());

    close.focus();
    fireEvent.keyDown(dialog, { key: "Tab", shiftKey: true });
    expect(status).toHaveFocus();
    fireEvent.keyDown(dialog, { key: "Tab" });
    expect(close).toHaveFocus();
  });
});
