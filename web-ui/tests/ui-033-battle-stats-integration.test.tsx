import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeAll, describe, expect, it, vi } from "vitest";
import { BattleScreen } from "@/components/battle/BattleScreen";
import { MockBattleProvider } from "@/lib/battle/fixture";
import type { BattleProvider, BattleSnapshot } from "@/lib/battle/types";

// jsdom exposes dialog semantics but does not implement the browser's modal
// top-layer methods. Keep this integration suite exercising the same public
// open/close contract without coupling it to a browser-only implementation.
beforeAll(() => {
  const prototype = HTMLDialogElement.prototype as HTMLDialogElement & { showModal?: () => void };
  if (typeof prototype.showModal !== "function" || !Object.prototype.hasOwnProperty.call(prototype.showModal, "__ui033Patched")) {
    const showModal = function (this: HTMLDialogElement) {
      this.setAttribute("open", "");
    };
    Object.defineProperty(showModal, "__ui033Patched", { value: true });
    prototype.showModal = showModal;
  }
});

async function renderStatsBattle(provider = new MockBattleProvider(), extra: Partial<React.ComponentProps<typeof BattleScreen>> = {}) {
  render(<BattleScreen provider={provider} {...extra} />);
  await screen.findByRole("main");
  await screen.findByRole("complementary", { name: "Your team" });
  return provider;
}

async function snapshotOf(provider: MockBattleProvider): Promise<BattleSnapshot> {
  return (await provider.getState()).snapshot;
}

describe("UI-033 battle stats cross-boundary integration", () => {
  it("keeps duplicate-definition heroes independently addressable, including a defeated occupied card", async () => {
    const base = await snapshotOf(new MockBattleProvider());
    const duplicate = structuredClone(base.combatants["enemy.andonidas"]);
    duplicate.id = "enemy.andonidas.copy";
    duplicate.displayName = "Andonidas";
    duplicate.slot = 2;
    duplicate.hp = { current: 0, maximum: duplicate.hp.maximum };
    duplicate.alive = false;
    base.combatants[duplicate.id] = duplicate;
    base.sides[1].combatantIds.push(duplicate.id);
    base.sides[1].maxSlots = 3;

    await renderStatsBattle(new MockBattleProvider(base));
    const buttons = screen.getAllByRole("button", { name: /View Hero Stats for Andonidas/i });
    expect(buttons).toHaveLength(2);
    expect(buttons[0]).toHaveAttribute("aria-label", expect.stringContaining("slot 2"));
    expect(buttons[1]).toHaveAttribute("aria-label", expect.stringContaining("slot 3"));

    await userEvent.setup().click(buttons[1]);
    const dialog = screen.getByRole("dialog", { name: /Andonidas/i });
    expect(dialog).toHaveTextContent("CURRENT HP");
    expect(dialog).toHaveTextContent("0");
    expect(dialog).not.toHaveTextContent("0/76");
  });

  it("keeps a summon runtime identity and its stats independently inspectable after summon playback", async () => {
    const provider = new MockBattleProvider();
    const submit = vi.spyOn(provider, "submitCommand");
    const user = userEvent.setup();
    await renderStatsBattle(provider, {
      mockDemos: [{ id: "summon", label: "Summon", run: () => provider.runDemo("summon") }],
    });

    await user.click(screen.getByRole("button", { name: "Summon" }));
    await screen.findByRole("button", { name: /View Hero Stats for Flesh Puppet/i });
    const summonButton = screen.getByRole("button", { name: /View Hero Stats for Flesh Puppet/i });
    await user.click(summonButton);
    const dialog = screen.getByRole("dialog", { name: /Flesh Puppet/i });
    expect(dialog).toHaveTextContent("Warrior · Summon");
    expect(dialog).toHaveTextContent("CURRENT HP");
    expect(submit).not.toHaveBeenCalled();
  });

  it("shows Updating during ordinary playback, then reconciles to the visible event/final state", async () => {
    const provider = new MockBattleProvider();
    const user = userEvent.setup();
    await renderStatsBattle(provider, {
      mockDemos: [{
        id: "status",
        label: "Status",
        run: async () => {
          const script = await provider.runDemo("status");
          await new Promise((resolve) => window.setTimeout(resolve, 100));
          const sashein = script.snapshot.combatants["enemy.sashein"];
          sashein.statuses = sashein.statuses.map((status) => status.id === "status.stitch_of_agony"
            ? { ...status, roundsRemaining: 3 }
            : status);
          return { ...script, events: [], snapshot: script.snapshot };
        },
      }],
    });

    // Start playback before opening inspection. The modal must consume the
    // currently presented boundary while the underlying demo remains active.
    await user.click(screen.getByRole("button", { name: "Status" }));
    await user.click(screen.getByRole("button", { name: /View Hero Stats for Sashein/i }));
    const dialog = screen.getByRole("dialog", { name: /Sashein/i });
    expect(await within(dialog).findAllByText("Updating…")).not.toHaveLength(0);
    expect(screen.queryByText("Choose a demo or select a skill.")).not.toBeInTheDocument();

    await waitFor(() => expect(within(dialog).getByText("3 rounds")).toBeVisible(), { timeout: 2000 });
    expect(within(dialog).queryByText("Updating…")).not.toBeInTheDocument();
  });

  it("shows Updating while the opening playback is still resolving", async () => {
    const base = new MockBattleProvider();
    const state = await base.getState();
    const openingSnapshot = structuredClone(state.snapshot);
    const finalSnapshot = structuredClone(state.snapshot);
    const futureDamage = openingSnapshot.combatants["friendly.arthas"].stats.damage.current + 13;
    finalSnapshot.combatants["friendly.arthas"].stats.damage = {
      current: futureDamage,
      delta: 13,
    };
    const provider: BattleProvider = {
      getState: async () => ({
        ...state,
        snapshot: finalSnapshot,
        playOpening: true,
        openingSnapshot,
        events: [{ id: "opening.1", sequence: 1, type: "battleStarted", message: "Battle started." }],
      }),
      submitCommand: (command) => base.submitCommand(command),
    };
    const user = userEvent.setup();
    await renderStatsBattle(provider, { entryCountdownStepMs: 0 });
    await user.click(screen.getByRole("button", { name: /View Hero Stats for Arthas/i }));
    const dialog = screen.getByRole("dialog", { name: /Arthas/i });
    expect(await within(dialog).findAllByText("Updating…")).not.toHaveLength(0);
    expect(within(dialog).queryByText(String(futureDamage))).not.toBeInTheDocument();
    await waitFor(() => expect(within(dialog).getByText(String(futureDamage))).toBeVisible(), { timeout: 3000 });
    expect(within(dialog).queryByText("Updating…")).not.toBeInTheDocument();
  });

  it("preserves selection and does not issue a provider command when opening or closing inspection", async () => {
    const provider = new MockBattleProvider();
    const submit = vi.spyOn(provider, "submitCommand");
    const user = userEvent.setup();
    await renderStatsBattle(provider);

    const skill = screen.getByRole("button", { name: /Life Drain/i });
    await user.click(skill);
    expect(skill).toHaveAttribute("aria-pressed", "true");

    const trigger = screen.getByRole("button", { name: /View Hero Stats for Arthas/i });
    await user.click(trigger);
    const dialog = screen.getByRole("dialog", { name: /Arthas/i });
    expect(submit).not.toHaveBeenCalled();
    expect(skill).toHaveAttribute("aria-pressed", "true");

    await user.click(within(dialog).getByRole("button", { name: "Close Hero Stats for Arthas" }));
    await waitFor(() => expect(screen.queryByRole("dialog", { name: /Arthas/i })).not.toBeInTheDocument());
    await waitFor(() => expect(document.activeElement).toBe(trigger));
    expect(skill).toHaveAttribute("aria-pressed", "true");
    expect(submit).not.toHaveBeenCalled();
  });

  it("keeps stats inspection read-only when a status event is active", async () => {
    const provider = new MockBattleProvider();
    const submit = vi.spyOn(provider, "submitCommand");
    const user = userEvent.setup();
    await renderStatsBattle(provider, {
      mockDemos: [{ id: "magic", label: "Magic", run: () => provider.runDemo("magic") }],
    });

    await user.click(screen.getByRole("button", { name: "Magic" }));
    await user.click(screen.getByRole("button", { name: /View Hero Stats for Sashein/i }));
    const dialog = screen.getByRole("dialog", { name: /Sashein/i });
    expect(await within(dialog).findAllByText("Updating…")).not.toHaveLength(0);
    expect(submit).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Close Hero Stats for Sashein" })).toBeVisible();
  });
});
