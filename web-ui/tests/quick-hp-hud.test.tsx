import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { act } from "react";
import { describe, expect, it, vi } from "vitest";
import { BattleScreen } from "@/components/battle/BattleScreen";
import { createFormatFixture, MockBattleProvider } from "@/lib/battle/fixture";
import type { BattleEvent, BattleSnapshot, PresentationScript } from "@/lib/battle/types";

const clone = <T,>(value: T): T => structuredClone(value);

async function renderDemo(event: BattleEvent, snapshotMutator?: (snapshot: BattleSnapshot) => void, useFakeTimers = false, battleSize?: 1 | 2 | 3, initialSnapshotMutator?: (snapshot: BattleSnapshot) => void) {
  const initialProvider = battleSize ? new MockBattleProvider(createFormatFixture(battleSize)) : new MockBattleProvider();
  const initialState = await initialProvider.getState();
  initialSnapshotMutator?.(initialState.snapshot);
  const provider = initialSnapshotMutator ? new MockBattleProvider(initialState.snapshot) : initialProvider;
  const state = initialSnapshotMutator ? await provider.getState() : initialState;
  const snapshot = clone(state.snapshot);
  snapshotMutator?.(snapshot);
  render(<BattleScreen provider={provider} mockDemos={[{
    id: "quick-hp",
    label: "Quick HP event",
    run: async (): Promise<PresentationScript> => ({
      id: "quick-hp", label: "Quick HP event", eventType: event.type === "healingApplied" ? "healing" : "melee",
      events: [event], snapshot, revision: 2,
    }),
  }]} />);
  await screen.findByRole("region", { name: "Battlefield" });
  if (useFakeTimers) vi.useFakeTimers();
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: "Quick HP event" }));
    await Promise.resolve();
  });
  return { provider, snapshot };
}

function hpEvent(type: "damageApplied" | "healingApplied", amount: number, hpAfter = { current: 76, maximum: 76 }): BattleEvent {
  return {
    id: `evt.quick.${type}.${amount}`, sequence: 1, type, targetId: "enemy.sashein", amount,
    hpAfter, effectHint: type === "healingApplied" ? "healing" : "melee",
    ...(type === "healingApplied" ? { healingPresentation: "cast" as const } : {}),
    message: "HP update.",
  } as BattleEvent;
}

describe("quick HP HUD contract", () => {
  it.each([
    ["damage", hpEvent("damageApplied", 0)],
    ["full-health healing", hpEvent("healingApplied", 0)],
  ])("shows the HP box for %s even when the displayed HP amount is zero", async (_label, event) => {
    await renderDemo(event);
    const figure = document.querySelector("[data-combatant-id='enemy.sashein']")!;
    await waitFor(() => expect(figure.querySelector(".event-hud")).toBeInTheDocument());
  });

  it("shows +0 when a full-health healing event resolves", async () => {
    try {
      await renderDemo(hpEvent("healingApplied", 0), undefined, true);
      const figure = document.querySelector("[data-combatant-id='enemy.sashein']")!;
      await act(async () => { await vi.advanceTimersByTimeAsync(300); });
      expect(figure.querySelector(".combat-text.heal")).toHaveTextContent("+0");
    } finally {
      vi.useRealTimers();
    }
  });

  it("does not show the HP box for a status-only event", async () => {
    const event = {
      id: "evt.quick.status", sequence: 1, type: "statusApplied", targetId: "enemy.sashein",
      statusId: "status.stitch_of_agony", statusPresentation: "debuff", effectHint: "status", message: "Debuff.",
    } as BattleEvent;
    await renderDemo(event);
    expect(document.querySelector("[data-combatant-id='enemy.sashein'] .event-hud")).not.toBeInTheDocument();
  });

  it("does not show the HP box for prevented damage without an HP mutation", async () => {
    const event = {
      id: "evt.quick.prevented", sequence: 1, type: "damagePrevented", targetId: "enemy.sashein",
      amount: 0, reasonId: "status.shield_of_protection", effectHint: "melee", message: "Blocked.",
    } as BattleEvent;
    await renderDemo(event);
    expect(document.querySelector("[data-combatant-id='enemy.sashein'] .event-hud")).not.toBeInTheDocument();
  });

  it.each([
    [1, "enemy.nighthawk"], [2, "enemy.andonidas"], [3, "enemy.sashein"],
  ] as const)("mounts a %s battle HP HUD only on the affected figure", async (battleSize, targetId) => {
    const event = hpEvent("damageApplied", 7, { current: 69, maximum: 76 });
    event.targetId = targetId;
    await renderDemo(event, undefined, false, battleSize);
    await waitFor(() => expect(document.querySelector(`[data-combatant-id='${targetId}'] .event-hud`)).toBeInTheDocument());
    expect(document.querySelectorAll(".battle-figure .event-hud")).toHaveLength(1);
    expect(document.querySelector("[data-combatant-id='friendly.ragnar'] .event-hud")).not.toBeInTheDocument();
  });

  it("keeps the HP HUD mounted through the 300ms lead and 300ms trailing windows", async () => {
    try {
      await renderDemo(hpEvent("damageApplied", 12, { current: 64, maximum: 76 }), undefined, true);
      const figure = document.querySelector("[data-combatant-id='enemy.sashein']")!;
      expect(figure.querySelector(".event-hud")).toBeInTheDocument();
      expect(figure.querySelector(".combat-text.damage")).not.toBeInTheDocument();
      await act(async () => { await vi.advanceTimersByTimeAsync(299); });
      expect(figure.querySelector(".event-hud")).toBeInTheDocument();
      await act(async () => { await vi.advanceTimersByTimeAsync(1); });
      expect(figure.querySelector(".combat-text.damage")).toBeInTheDocument();
      await act(async () => { await vi.advanceTimersByTimeAsync(299); });
      expect(figure.querySelector(".event-hud")).toBeInTheDocument();
    } finally {
      vi.useRealTimers();
    }
  });

  it("gives a Priest healer a 500ms pair-of-runes caster cue before the soft-gold target effect", async () => {
    try {
      const event = hpEvent("healingApplied", 12, { current: 76, maximum: 76 });
      event.sourceId = "friendly.arthas";
      const makeCasterPriest = (snapshot: BattleSnapshot) => {
        snapshot.combatants["friendly.arthas"].faculty = "Priest";
      };
      await renderDemo(event, makeCasterPriest, true, undefined, makeCasterPriest);
      await act(async () => { await Promise.resolve(); });
      const caster = document.querySelector("[data-combatant-id='friendly.arthas']")!;
      const target = document.querySelector("[data-combatant-id='enemy.sashein']")!;
      expect(caster.querySelector(".priest-healing-caster .priest-rune-crown")).toBeInTheDocument();
      expect(caster.querySelector(".priest-healing-caster .priest-rune-foot")).toBeInTheDocument();
      expect(target.querySelector(".effect-priest-healing")).not.toBeInTheDocument();
      await act(async () => { await vi.advanceTimersByTimeAsync(499); });
      expect(caster.querySelector(".priest-healing-caster")).toBeInTheDocument();
      expect(target.querySelector(".effect-priest-healing")).not.toBeInTheDocument();
      await act(async () => { await vi.advanceTimersByTimeAsync(1); });
      expect(caster.querySelector(".priest-healing-caster")).not.toBeInTheDocument();
      expect(target.querySelector(".effect-priest-healing")).toBeInTheDocument();
      expect(target).toHaveClass("priest-healing-target");
    } finally {
      vi.useRealTimers();
    }
  });

  it("keeps a Priest-authored status heal on the target without replaying the healer cast", async () => {
    try {
      const event = hpEvent("healingApplied", 12, { current: 76, maximum: 76 });
      event.sourceId = "friendly.arthas";
      event.healingPresentation = "status";
      const makePriest = (snapshot: BattleSnapshot) => {
        snapshot.combatants["friendly.arthas"].faculty = "Priest";
      };
      await renderDemo(event, makePriest, true, undefined, makePriest);
      const caster = document.querySelector("[data-combatant-id='friendly.arthas']")!;
      const target = document.querySelector("[data-combatant-id='enemy.sashein']")!;
      expect(caster.querySelector(".priest-healing-caster")).not.toBeInTheDocument();
      await act(async () => { await vi.advanceTimersByTimeAsync(300); });
      expect(target.querySelector(".effect-priest-healing")).toBeInTheDocument();
      expect(caster.querySelector(".priest-healing-caster")).not.toBeInTheDocument();
    } finally {
      vi.useRealTimers();
    }
  });

  it("stacks the left-aligned enlarged name above the meter without a status-icon row", async () => {
    await renderDemo(hpEvent("damageApplied", 12));
    const css = await import("node:fs").then(({ readFileSync }) => readFileSync("app/globals.css", "utf8")).then((value) => value.replace(/\s+/g, ""));
    const nameRule = css.match(/\.overhead-name\{([^}]*)\}/)?.[1] ?? "";
    const healthRule = css.match(/\.overhead-health\{([^}]*)\}/)?.[1] ?? "";
    expect(nameRule).toMatch(/text-align:left/);
    expect(nameRule).toMatch(/font-size:1[0-9]px/);
    expect(healthRule).toMatch(/grid-template-columns:minmax\(0,1fr\)/);
    expect(healthRule).not.toMatch(/\.65fr/);
    const figure = document.querySelector("[data-combatant-id='enemy.sashein']")!;
    expect(figure.querySelector(".event-hud .battlefield-statuses")).not.toBeInTheDocument();
  });
});
