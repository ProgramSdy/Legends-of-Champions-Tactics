import { act, renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { usePresentationQueue } from "@/lib/battle/usePresentationQueue";
import { createFormatFixture } from "@/lib/battle/fixture";
import type { BattleProvider, PresentationScript } from "@/lib/battle/types";

describe("presentation queue audio boundary", () => {
  it("fires each deliberately presented event once, in order, without load replay", async () => {
    vi.useFakeTimers();
    try {
      const snapshot = createFormatFixture(2);
      const provider: BattleProvider = {
        getState: vi.fn(async () => ({ revision: 4, snapshot: structuredClone(snapshot), events: [
          { id: "historical", sequence: 1, type: "damageApplied", targetId: "enemy.sashein", amount: 4, hpAfter: { current: 59, maximum: 81 } },
        ] })),
        submitCommand: vi.fn(),
      };
      const script: PresentationScript = {
        id: "presented",
        label: "Presented events",
        eventType: "status",
        revision: 5,
        snapshot: structuredClone(snapshot),
        events: [
          { id: "battle-start", sequence: 1, type: "battleStarted", message: "Battle started." },
          { id: "hit", sequence: 2, type: "damageApplied", targetId: "enemy.sashein", amount: 4, hpAfter: { current: 59, maximum: 81 }, message: "Hit." },
          { id: "poison", sequence: 3, type: "statusApplied", targetId: "enemy.sashein", statusId: "status.poison", statusPresentation: "debuff", message: "Poison." },
        ],
      };
      const onActiveEvent = vi.fn();
      const { result } = renderHook(() => usePresentationQueue(provider, { onActiveEvent }));
      await act(async () => { await Promise.resolve(); });
      expect(onActiveEvent).not.toHaveBeenCalled();

      await act(async () => {
        result.current.present(async () => script);
        await Promise.resolve();
        await vi.runAllTimersAsync();
      });
      expect(onActiveEvent.mock.calls.map(([event]) => event.id)).toEqual(["battle-start", "hit", "poison"]);
    } finally {
      vi.useRealTimers();
    }
  });

  it("adopts the authoritative reordered turn cards as the next turn starts", async () => {
    vi.useFakeTimers();
    try {
      const snapshot = createFormatFixture(2);
      const [first, second, third, fourth] = snapshot.turnOrder;
      const reordered = [
        { ...first, hasActed: true, isCurrent: false },
        { ...third, hasActed: false, isCurrent: true },
        { ...fourth, hasActed: false, isCurrent: false },
        { ...second, hasActed: false, isCurrent: false },
      ];
      const provider: BattleProvider = {
        getState: vi.fn(async () => ({ revision: 4, snapshot: structuredClone(snapshot), events: [] })),
        submitCommand: vi.fn(),
      };
      const script: PresentationScript = {
        id: "turn-order-reordered",
        label: "Turn order changed",
        eventType: "magic",
        revision: 5,
        snapshot: structuredClone(snapshot),
        events: [
          { id: "turn-ended", sequence: 1, type: "turnEnded", sourceId: first.combatantId, message: "First turn ended." },
          { id: "turn-started", sequence: 2, type: "turnStarted", sourceId: third.combatantId, turnOrder: reordered, message: "Next turn started." },
        ],
      };
      const { result } = renderHook(() => usePresentationQueue(provider));
      await act(async () => { await Promise.resolve(); });

      await act(async () => {
        result.current.present(async () => script);
        await Promise.resolve();
        await vi.advanceTimersByTimeAsync(700);
      });

      expect(result.current.snapshot?.turnOrder).toEqual(reordered);
    } finally {
      vi.useRealTimers();
    }
  });
});
