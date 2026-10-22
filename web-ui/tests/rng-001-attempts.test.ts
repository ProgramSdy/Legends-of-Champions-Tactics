import { describe, expect, it, vi } from "vitest";
import { createFormatFixture } from "@/lib/battle/fixture";
import { createBattleAttemptId, LiveBattleProvider } from "@/lib/battle/liveProvider";

describe("RNG-001 player battle attempt boundary", () => {
  it("reuses the provider attempt ID when creation is retried after a transport failure", async () => {
    const snapshot = createFormatFixture(1);
    const attemptId = "stage-attempt-test-1";
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify({ message: "lost response" }), { status: 503 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        contractVersion: "1.0",
        battleId: "battle.retry-safe",
        revision: 0,
        data: { events: [], snapshot },
      }), { status: 200, headers: { "Content-Type": "application/json" } }));
    const provider = new LiveBattleProvider(
      "http://adapter.test",
      {
        battleSize: 1,
        playerTeam: ["hero.warrior.weapon_master"],
        enemyCompositionMode: "specified",
        enemyTeam: ["hero.rogue.comprehensiveness"],
        enemyControlMode: "computer",
      },
      "/api/v1/stages/warriors-barrack/battles/1",
      attemptId,
    );

    await expect(provider.getState()).rejects.toThrow();
    await expect(provider.getState()).resolves.toMatchObject({ revision: 0 });

    const bodies = fetchMock.mock.calls.map(([, init]) => JSON.parse(String(init?.body)));
    expect(bodies).toEqual([
      expect.objectContaining({ attemptId }),
      expect.objectContaining({ attemptId }),
    ]);
    fetchMock.mockRestore();
  });

  it("keeps deliberate legacy/debug providers seedless and refuses an unsupported null attempt ID", async () => {
    const snapshot = createFormatFixture(1);
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({
      contractVersion: "1.0",
      battleId: "battle.legacy",
      revision: 0,
      data: { events: [], snapshot },
    }), { status: 200, headers: { "Content-Type": "application/json" } }));

    const legacyProvider = new LiveBattleProvider("http://adapter.test", {
      battleSize: 1,
      playerTeam: ["hero.warrior.weapon_master"],
      enemyCompositionMode: "specified",
      enemyTeam: ["hero.rogue.comprehensiveness"],
      enemyControlMode: "player",
      seed: 9191,
    });
    await legacyProvider.getState();
    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).not.toHaveProperty("attemptId");

    const unsupportedProvider = new LiveBattleProvider("http://adapter.test", undefined, undefined, null);
    await expect(unsupportedProvider.getState()).rejects.toMatchObject({ kind: "adapter" });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    fetchMock.mockRestore();
  });

  it("creates distinct opaque IDs for distinct intentional providers when crypto supports UUIDs", () => {
    const first = createBattleAttemptId();
    const second = createBattleAttemptId();
    if (first !== null && second !== null) expect(first).not.toBe(second);
  });

  it("uses secure getRandomValues when randomUUID is unavailable and fails closed without secure entropy", () => {
    const getRandomValues = vi.fn((bytes: Uint8Array) => {
      bytes.fill(0x11);
      return bytes;
    });
    vi.stubGlobal("crypto", { getRandomValues });
    const fallbackId = createBattleAttemptId();
    expect(fallbackId).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
    expect(getRandomValues).toHaveBeenCalledTimes(1);

    vi.stubGlobal("crypto", {});
    expect(createBattleAttemptId()).toBeNull();
    vi.unstubAllGlobals();
  });

  it("single-flights concurrent creation calls and returns one authoritative state", async () => {
    const snapshot = createFormatFixture(1);
    let release!: (response: Response) => void;
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(() => (
      new Promise<Response>((resolve) => { release = resolve; })
    ));
    const provider = new LiveBattleProvider(
      "http://adapter.test",
      {
        battleSize: 1,
        playerTeam: ["hero.warrior.weapon_master"],
        enemyCompositionMode: "specified",
        enemyTeam: ["hero.rogue.comprehensiveness"],
        enemyControlMode: "computer",
      },
      "/api/v1/battles",
      "concurrent-attempt",
    );
    const first = provider.getState();
    const second = provider.getState();
    await Promise.resolve();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    release(new Response(JSON.stringify({
      contractVersion: "1.0",
      battleId: "battle.single-flight",
      revision: 0,
      data: { events: [], snapshot },
    }), { status: 200, headers: { "Content-Type": "application/json" } }));
    await expect(Promise.all([first, second])).resolves.toEqual([
      { revision: 0, snapshot, events: [] },
      { revision: 0, snapshot, events: [] },
    ]);
    fetchMock.mockRestore();
  });
});
