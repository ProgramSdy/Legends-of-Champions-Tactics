import { afterEach, describe, expect, it, vi } from "vitest";
import { createFormatFixture } from "@/lib/battle/fixture";
import { LiveBattleProvider } from "@/lib/battle/liveProvider";

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllEnvs();
});

describe("RELEASE-002 durable battle receipt recovery", () => {
  it("retries an uncertain command with the exact same command ID and recovers a terminal settlement without replay events", async () => {
    vi.stubEnv("LOCT_RELEASE_MODE", "development");
    const snapshot = createFormatFixture(1);
    const command = {
      type: "useSkill" as const,
      commandId: "cmd.retry-same-id",
      expectedRevision: 1,
      actorId: snapshot.activeCombatantId!,
      skillId: snapshot.legalActions[0].skillId,
      targetIds: [snapshot.legalActions[0].validTargetIds[0]],
    };
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify({
        contractVersion: "1.0",
        battleId: "battle.receipt",
        revision: 1,
        data: { events: [], snapshot },
      }), { status: 200, headers: { "Content-Type": "application/json" } }))
      .mockRejectedValueOnce(new TypeError("connection lost after acceptance"))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        contractVersion: "1.0",
        battleId: "battle.receipt",
        revision: 2,
        data: null,
        lifecycleStatus: "settled",
        settlementStatus: "settled",
        serverNow: "2026-11-18T00:00:00Z",
        expiresAt: "2026-11-18T00:00:00Z",
        settlement: { outcome: { kind: "victory", winningSideId: "friendly" } },
      }), { status: 200, headers: { "Content-Type": "application/json" } }));
    const provider = new LiveBattleProvider("http://adapter.test");
    await provider.getState();

    await expect(provider.submitCommand(command)).rejects.toMatchObject({ kind: "disconnected" });
    const recovered = await provider.retryPendingCommand();

    expect(recovered.events).toEqual([]);
    expect(recovered.revision).toBe(2);
    expect(recovered.snapshot).toMatchObject({
      phase: "ended",
      outcome: { kind: "victory", winningSideId: "friendly" },
    });
    const firstBody = (fetchMock.mock.calls[1][1] as RequestInit).body;
    const retryBody = (fetchMock.mock.calls[2][1] as RequestInit).body;
    expect(firstBody).toBe(JSON.stringify(command));
    expect(retryBody).toBe(firstBody);
  });
});
