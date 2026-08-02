import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { BattleScreen } from "@/components/battle/BattleScreen";
import { createFormatFixture } from "@/lib/battle/fixture";
import type { BattleEvent, BattleProvider, BattleState } from "@/lib/battle/types";

const openingSnapshot = () => {
  const snapshot = createFormatFixture(1);
  snapshot.phase = "resolving";
  snapshot.activeCombatantId = "enemy.nighthawk";
  snapshot.turnControl = {
    disposition: "automaticAction",
    acceptsCommands: false,
    reasonId: "automaticResolution",
    actorCombatantId: "enemy.nighthawk",
    sourceCombatantId: null,
    forcedTargetIds: [],
  };
  snapshot.legalActions = [];
  snapshot.turnOrder = snapshot.turnOrder.map((turn) => ({
    ...turn,
    isCurrent: turn.combatantId === "enemy.nighthawk",
  }));
  return snapshot;
};

const openingEvents = (): BattleEvent[] => [
  { id: "opening.1", sequence: 1, type: "turnStarted", sourceId: "enemy.nighthawk", message: "Nighthawk begins the opening turn." },
  { id: "opening.2", sequence: 2, type: "characterMoved", sourceId: "enemy.nighthawk", targetId: "friendly.ragnar", movement: "lunge", effectHint: "melee", message: "Nighthawk lunges toward Ragnar." },
  { id: "opening.3", sequence: 3, type: "damageApplied", sourceId: "enemy.nighthawk", targetId: "friendly.ragnar", amount: 32, hpAfter: { current: 70, maximum: 102 }, effectHint: "melee", message: "Ragnar takes 32 opening damage." },
  { id: "opening.4", sequence: 4, type: "turnEnded", sourceId: "enemy.nighthawk", message: "Nighthawk ends the opening turn." },
  { id: "opening.5", sequence: 5, type: "turnStarted", sourceId: "friendly.ragnar", message: "Ragnar is ready for a command." },
];

function openingState(): BattleState {
  const opening = openingSnapshot();
  const final = createFormatFixture(1);
  final.combatants["friendly.ragnar"].hp.current = 70;
  return {
    revision: 1,
    openingSnapshot: opening,
    playOpening: true,
    events: openingEvents(),
    snapshot: final,
  };
}

function providerFor(state: BattleState): BattleProvider {
  return {
    getState: vi.fn(async () => structuredClone(state)),
    submitCommand: vi.fn(),
  };
}

async function flushPromises() {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
}

async function advanceTimerSteps(milliseconds: number, count: number) {
  for (let index = 0; index < count; index += 1) {
    await act(async () => { await vi.advanceTimersByTimeAsync(milliseconds); });
  }
}

afterEach(() => {
  vi.useRealTimers();
});

describe("UI-008 opening presentation lifecycle", () => {
  it("shows the composed opening board with an empty log and gates commands through countdown", async () => {
    vi.useFakeTimers();
    const provider = providerFor(openingState());
    render(<BattleScreen provider={provider} mode="live" entryCountdownStepMs={20} />);
    await flushPromises();

    expect(screen.getByRole("region", { name: "Battlefield" })).toBeVisible();
    expect(screen.getByRole("complementary", { name: "Your team" })).toBeVisible();
    expect(screen.getByRole("status", { name: "Battle begins in 3" })).toHaveClass("entry-countdown-value", "numeric");
    expect(screen.getByRole("list", { name: "Battle events" })).toBeEmptyDOMElement();
    expect(screen.getAllByText("102/102").length).toBeGreaterThan(0);
    expect([...document.querySelectorAll<HTMLButtonElement>(".skill-card")].every((button) => button.disabled)).toBe(true);
    expect(provider.submitCommand).not.toHaveBeenCalled();

    await act(async () => { await vi.advanceTimersByTimeAsync(20); });
    expect(screen.getByRole("status", { name: "Battle begins in 2" })).toHaveClass("entry-countdown-value", "numeric");
    await act(async () => { await vi.advanceTimersByTimeAsync(20); });
    expect(screen.getByRole("status", { name: "Battle begins in 1" })).toHaveClass("entry-countdown-value", "numeric");
    await act(async () => { await vi.advanceTimersByTimeAsync(20); });
    expect(screen.getByRole("status", { name: "Battle start" })).toHaveClass("entry-countdown-value", "start");
    expect(screen.getByRole("list", { name: "Battle events" })).toBeEmptyDOMElement();
  });

  it("applies opening events once in sequence and reconciles to the final player boundary", async () => {
    vi.useFakeTimers();
    const provider = providerFor(openingState());
    const { container } = render(<BattleScreen provider={provider} mode="live" entryCountdownStepMs={10} />);
    await flushPromises();

    await advanceTimerSteps(10, 4);
    expect(screen.getByText("Nighthawk begins the opening turn.")).toBeVisible();
    expect(screen.getAllByText("102/102").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "OPENING BATTLE…" })).toBeDisabled();

    await advanceTimerSteps(620, 2);
    expect(screen.getByText("Ragnar takes 32 opening damage.")).toBeVisible();
    expect(screen.getAllByText("70/102").length).toBeGreaterThan(0);

    await advanceTimerSteps(620, 3);
    const messages = [...container.querySelectorAll(".battle-log li")].map((item) => item.textContent?.slice(1));
    expect(messages).toEqual(openingEvents().map((event) => event.message));
    expect(new Set(messages).size).toBe(messages.length);
    expect(screen.getByRole("button", { name: /Fatal Strike/i })).toBeEnabled();
    expect(screen.getByRole("button", { name: "SELECT SKILL" })).toBeDisabled();
  });

  it("cancels stale opening timers when a new battle mounts", async () => {
    vi.useFakeTimers();
    const staleProvider = providerFor(openingState());
    const currentState = createFormatFixture(1);
    const currentProvider = providerFor({ revision: 0, snapshot: currentState, events: [], playOpening: false });
    const view = render(<BattleScreen key="stale" provider={staleProvider} mode="live" />);
    await flushPromises();
    expect(screen.getByText("Nighthawk begins the opening turn.")).toBeVisible();

    view.rerender(<BattleScreen key="current" provider={currentProvider} mode="live" />);
    await flushPromises();
    await advanceTimerSteps(620, 6);

    expect(screen.queryByText("Ragnar takes 32 opening damage.")).not.toBeInTheDocument();
    expect(screen.getByRole("list", { name: "Battle events" })).toBeEmptyDOMElement();
    expect(screen.getAllByText("102/102").length).toBeGreaterThan(0);
  });

  it("retries a failed load and presents the recovered opening without duplicates", async () => {
    vi.useFakeTimers();
    const state = openingState();
    const getState = vi.fn()
      .mockRejectedValueOnce(new Error("Opening unavailable."))
      .mockResolvedValueOnce(structuredClone(state));
    const provider: BattleProvider = { getState, submitCommand: vi.fn() };
    const { container } = render(<BattleScreen provider={provider} mode="live" />);
    await flushPromises();

    fireEvent.click(screen.getByRole("button", { name: "Retry connection" }));
    await flushPromises();
    expect(screen.getByText("Nighthawk begins the opening turn.")).toBeVisible();
    await advanceTimerSteps(620, 6);

    const ids = [...container.querySelectorAll(".battle-log li")].map((item) => item.textContent);
    expect(ids).toHaveLength(openingEvents().length);
    expect(new Set(ids).size).toBe(ids.length);
    expect(getState).toHaveBeenCalledTimes(2);
    expect(screen.getAllByText("70/102").length).toBeGreaterThan(0);
  });
});
