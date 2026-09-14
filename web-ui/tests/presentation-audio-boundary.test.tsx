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
});
