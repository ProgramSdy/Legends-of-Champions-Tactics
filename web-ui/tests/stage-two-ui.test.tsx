import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { BattleScreen } from "@/components/battle/BattleScreen";
import { createFormatFixture, MockBattleProvider } from "@/lib/battle/fixture";
import { formationRegistry, getBattleFormat } from "@/lib/battle/formations";
import { LiveBattleProvider } from "@/lib/battle/liveProvider";
import { BattleProviderError } from "@/lib/battle/types";

describe("Stage 1.5 formations", () => {
  it.each([
    [1, "duel", 2],
    [2, "duo", 4],
    [3, "trio", 6],
  ] as const)("derives %dv%d as %s with every combatant represented", (size, format, count) => {
    const fixture = createFormatFixture(size);
    expect(getBattleFormat(fixture)).toBe(format);
    expect(fixture.turnOrder).toHaveLength(count);
    expect(formationRegistry[format].friendly).toHaveLength(size);
    expect(formationRegistry[format].enemy).toHaveLength(size);
  });

  it.each([[1, 2], [2, 4], [3, 6]] as const)("renders exactly %d versus %d referenced battlefield figures", async (size, figureCount) => {
    const { container } = render(<BattleScreen provider={new MockBattleProvider(createFormatFixture(size))} mode="mock" />);
    const battlefield = await screen.findByRole("region", { name: "Battlefield" });
    expect(battlefield.closest("main")).toHaveAttribute("data-format", size === 1 ? "duel" : size === 2 ? "duo" : "trio");
    expect(container.querySelectorAll(".formation-slot .battle-figure")).toHaveLength(figureCount);
    if (size === 1) expect(screen.queryByText("OPEN SLOT")).not.toBeInTheDocument();
  });
});

describe("live provider boundary", () => {
  it("creates the approved scenario and preserves the authoritative snapshot", async () => {
    const snapshot = createFormatFixture(1);
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({
      contractVersion: "1.0", battleId: "battle.1", revision: 0, data: { events: [], snapshot },
    }), { status: 200, headers: { "Content-Type": "application/json" } }));
    const provider = new LiveBattleProvider("http://adapter.test", 42);
    expect(await provider.getState()).toEqual({ revision: 0, snapshot, events: [] });
    expect(fetchMock).toHaveBeenCalledWith("http://adapter.test/api/v1/battles", expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ scenarioId: "ragnar-vs-nighthawk", seed: 42 }),
    }));
    fetchMock.mockRestore();
  });

  it("classifies network failure as disconnected", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("network"));
    await expect(new LiveBattleProvider("http://offline.test").getState()).rejects.toMatchObject<Partial<BattleProviderError>>({
      kind: "disconnected",
    });
    fetchMock.mockRestore();
  });

  it("does not regress authoritative state when an old command response is replayed", async () => {
    const revisionOne = createFormatFixture(1);
    revisionOne.combatants["enemy.nighthawk"].hp.current = 70;
    const revisionTwo = structuredClone(revisionOne);
    revisionTwo.combatants["friendly.ragnar"].hp.current = 65;
    const accepted = (revision: number, snapshot: typeof revisionOne) => ({
      contractVersion: "1.0", battleId: "battle.1", revision,
      data: { accepted: true, commandId: `cmd.${revision}`, revision, events: [], snapshot },
    });
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify({
        contractVersion: "1.0", battleId: "battle.1", revision: 0,
        data: { events: [], snapshot: createFormatFixture(1) },
      }), { status: 200, headers: { "Content-Type": "application/json" } }))
      .mockResolvedValueOnce(new Response(JSON.stringify(accepted(1, revisionOne)), { status: 200, headers: { "Content-Type": "application/json" } }))
      .mockResolvedValueOnce(new Response(JSON.stringify(accepted(2, revisionTwo)), { status: 200, headers: { "Content-Type": "application/json" } }))
      .mockResolvedValueOnce(new Response(JSON.stringify(accepted(1, revisionOne)), { status: 200, headers: { "Content-Type": "application/json" } }));
    const provider = new LiveBattleProvider("http://adapter.test");
    await provider.getState();
    const command = {
      type: "useSkill" as const,
      commandId: "cmd.1",
      expectedRevision: 0,
      actorId: "friendly.ragnar",
      skillId: "skill.warrior.fatal_strike",
      targetIds: ["enemy.nighthawk"],
    };

    await provider.submitCommand(command);
    await provider.submitCommand({ ...command, commandId: "cmd.2", expectedRevision: 1 });
    const replay = await provider.submitCommand(command);

    expect(replay.revision).toBe(2);
    expect(replay.events).toEqual([]);
    expect(replay.snapshot).toEqual(revisionTwo);
    fetchMock.mockRestore();
  });

  it("does not replay events when an accepted command is immediately repeated", async () => {
    const initial = createFormatFixture(1);
    const resolved = structuredClone(initial);
    resolved.combatants["enemy.nighthawk"].hp.current = 70;
    const events = [{
      id: "battle.1.evt.000004",
      sequence: 4,
      type: "damageApplied" as const,
      targetId: "enemy.nighthawk",
      amount: 14,
      hpAfter: { current: 70, maximum: 84 },
      message: "Nighthawk took 14 damage.",
    }];
    const accepted = {
      contractVersion: "1.0",
      battleId: "battle.1",
      revision: 1,
      data: {
        accepted: true,
        commandId: "cmd.same",
        revision: 1,
        events,
        snapshot: resolved,
      },
    };
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify({
        contractVersion: "1.0",
        battleId: "battle.1",
        revision: 0,
        data: { events: [], snapshot: initial },
      }), { status: 200, headers: { "Content-Type": "application/json" } }))
      .mockResolvedValueOnce(new Response(JSON.stringify(accepted), { status: 200, headers: { "Content-Type": "application/json" } }))
      .mockResolvedValueOnce(new Response(JSON.stringify(accepted), { status: 200, headers: { "Content-Type": "application/json" } }));
    const provider = new LiveBattleProvider("http://adapter.test");
    const command = {
      type: "useSkill" as const,
      commandId: "cmd.same",
      expectedRevision: 0,
      actorId: "friendly.ragnar",
      skillId: "skill.warrior.fatal_strike",
      targetIds: ["enemy.nighthawk"],
    };

    await provider.getState();
    const first = await provider.submitCommand(command);
    const replay = await provider.submitCommand(command);

    expect(first.events).toEqual(events);
    expect(replay).toMatchObject({
      id: "cmd.same",
      label: "Command already applied",
      events: [],
      revision: 1,
      snapshot: resolved,
    });
    expect(fetchMock).toHaveBeenCalledTimes(3);
    fetchMock.mockRestore();
  });
});
