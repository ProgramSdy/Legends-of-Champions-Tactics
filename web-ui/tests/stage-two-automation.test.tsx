import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { BattleScreen } from "@/components/battle/BattleScreen";
import { resolveAsset } from "@/lib/battle/assets";
import { createFormatFixture } from "@/lib/battle/fixture";
import { formationFor } from "@/lib/battle/formations";
import { LiveBattleProvider } from "@/lib/battle/liveProvider";
import {
  BattleProviderError,
  type BattleCommand,
  type BattleProvider,
  type BattleState,
  type PresentationScript,
} from "@/lib/battle/types";

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((yes, no) => {
    resolve = yes;
    reject = no;
  });
  return { promise, resolve, reject };
}

const initial = createFormatFixture(1);

class ControlledProvider implements BattleProvider {
  state = structuredClone(initial);
  revision = 0;
  submit = vi.fn<(command: BattleCommand) => Promise<PresentationScript>>();

  async getState(): Promise<BattleState> {
    return { revision: this.revision, snapshot: structuredClone(this.state) };
  }

  submitCommand(command: BattleCommand) {
    return this.submit(command);
  }
}

describe("independent live battle UI coverage", () => {
  it("shows loading until the provider returns, then renders the approved live duel", async () => {
    const load = deferred<BattleState>();
    const provider: BattleProvider = {
      getState: () => load.promise,
      submitCommand: vi.fn(),
    };
    render(<BattleScreen provider={provider} mode="live" />);

    expect(screen.getByText("Opening the battlefield…")).toBeVisible();
    load.resolve({ revision: 0, snapshot: structuredClone(initial) });

    expect(await screen.findByRole("main")).toHaveAttribute("data-format", "duel");
    expect(screen.getAllByText("Ragnar").length).toBeGreaterThan(1);
    expect(screen.getAllByText("Nighthawk").length).toBeGreaterThan(1);
    expect(screen.getByRole("article", { name: /Ragnar, Weapon Master, active hero/i })).toBeVisible();
    expect(screen.getByRole("region", { name: "Battlefield" }).querySelectorAll(".battle-figure")).toHaveLength(2);
  });

  it("renders authoritative session-opening events in sequence without placeholder log text", async () => {
    const provider: BattleProvider = {
      getState: async () => ({
        revision: 0,
        snapshot: structuredClone(initial),
        events: [
          { id: "event.2", sequence: 2, type: "roundStarted", message: "Round 1 started." },
          { id: "event.1", sequence: 1, type: "battleStarted", message: "Battle started." },
        ],
      }),
      submitCommand: vi.fn(),
    };
    const { container } = render(<BattleScreen provider={provider} mode="live" />);

    await screen.findByText("Battle started.");
    const entries = [...container.querySelectorAll(".battle-log li")].map((item) => item.textContent);
    expect(entries).toEqual(["◆Battle started.", "◎Round 1 started."]);
    expect(screen.queryByText("Choose a demo or select a skill.")).not.toBeInTheDocument();
  });

  it("submits selected intent without optimistic HP mutation, then reconciles", async () => {
    const user = userEvent.setup();
    const provider = new ControlledProvider();
    const pending = deferred<PresentationScript>();
    provider.submit.mockReturnValue(pending.promise);
    render(<BattleScreen provider={provider} mode="live" />);
    await screen.findByRole("main");

    const hpBefore = screen.getAllByText("84/84").length;
    await user.click(screen.getByRole("button", { name: /Fatal Strike/i }));
    await user.click(screen.getByRole("button", { name: "Nighthawk, selectable target" }));
    await user.click(screen.getByRole("button", { name: "CAST SKILL" }));

    expect(provider.submit).toHaveBeenCalledWith(expect.objectContaining({
      type: "useSkill",
      expectedRevision: 0,
      actorId: "friendly.ragnar",
      skillId: "skill.warrior.fatal_strike",
      targetIds: ["enemy.nighthawk"],
    }));
    expect(screen.getAllByText("84/84")).toHaveLength(hpBefore);

    const final = structuredClone(initial);
    final.combatants["enemy.nighthawk"].hp.current = 70;
    pending.resolve({
      id: "cmd.live",
      label: "Fatal Strike",
      eventType: "melee",
      revision: 1,
      events: [{
        id: "battle.1.event.1",
        sequence: 1,
        type: "damageApplied",
        targetId: "enemy.nighthawk",
        amount: 14,
        hpAfter: { current: 70, maximum: 84 },
        message: "Nighthawk took 14 damage.",
      }],
      snapshot: final,
    });

    expect(await screen.findByText("Nighthawk took 14 damage.")).toBeVisible();
    await waitFor(() => expect(screen.getAllByText("70/84").length).toBeGreaterThan(0), { timeout: 1500 });
  });

  it("keeps the authoritative final board visible when the battle has ended", async () => {
    const ended = structuredClone(initial);
    ended.phase = "ended";
    ended.activeCombatantId = null;
    ended.legalActions = [];
    ended.outcome = { kind: "victory", winningSideId: "friendly" };
    ended.combatants["enemy.nighthawk"].alive = false;
    ended.combatants["enemy.nighthawk"].hp.current = 0;
    const provider: BattleProvider = {
      getState: async () => ({ revision: 4, snapshot: ended }),
      submitCommand: vi.fn(),
    };

    render(<BattleScreen provider={provider} mode="live" />);

    expect(await screen.findByText("YOUR TEAM VICTORIOUS")).toBeVisible();
    expect(screen.getByRole("region", { name: "Battlefield" })).toBeVisible();
    expect(screen.queryByText("Opening the battlefield…")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "BATTLE ENDED" })).toBeDisabled();
    expect(screen.getByText("0/84")).toBeVisible();
  });

  it.each([
    ["rejected", "COMMAND REJECTED"],
    ["stale", "STATE RECONCILED"],
  ] as const)("shows %s command errors and applies their authoritative snapshot", async (kind, heading) => {
    const provider = new ControlledProvider();
    const reconciled = structuredClone(initial);
    reconciled.combatants["enemy.nighthawk"].hp.current = 73;
    provider.submit.mockRejectedValue(
      new BattleProviderError("Authoritative rejection.", kind, reconciled, 4),
    );
    render(<BattleScreen provider={provider} mode="live" />);
    await screen.findByRole("main");

    fireEvent.click(screen.getByRole("button", { name: /Fatal Strike/i }));
    fireEvent.click(screen.getByRole("button", { name: "Nighthawk, selectable target" }));
    fireEvent.click(screen.getByRole("button", { name: "CAST SKILL" }));

    expect(await screen.findByText(heading)).toBeVisible();
    expect(screen.getByText("Authoritative rejection.")).toBeVisible();
    expect(screen.getAllByText("73/84").length).toBeGreaterThan(0);
  });
});

describe("provider failure and contract edges", () => {
  it("rejects unsupported contracts and server errors as adapter failures", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify({
        contractVersion: "2.0",
        battleId: "battle.bad",
        revision: 0,
        data: { snapshot: initial },
      }), { status: 200, headers: { "Content-Type": "application/json" } }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        detail: { message: "Adapter exploded safely." },
      }), { status: 500, headers: { "Content-Type": "application/json" } }));

    await expect(new LiveBattleProvider("http://adapter.test").getState()).rejects.toMatchObject({
      kind: "adapter",
      message: "Unsupported battle contract 2.0.",
    });
    await expect(new LiveBattleProvider("http://adapter.test").getState()).rejects.toMatchObject({
      kind: "adapter",
      message: "Adapter exploded safely.",
    });
    fetchMock.mockRestore();
  });

  it("maps stale rejection snapshots and never retries a rejected command", async () => {
    const snapshot = structuredClone(initial);
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify({
        contractVersion: "1.0", battleId: "battle.1", revision: 0,
        data: { events: [], snapshot },
      }), { status: 200, headers: { "Content-Type": "application/json" } }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        contractVersion: "1.0", battleId: "battle.1", revision: 2,
        data: {
          accepted: false,
          commandId: "cmd.stale",
          revision: 2,
          code: "staleRevision",
          message: "Refresh required.",
          snapshot,
        },
      }), { status: 200, headers: { "Content-Type": "application/json" } }));
    const provider = new LiveBattleProvider("http://adapter.test");
    await provider.getState();

    await expect(provider.submitCommand({
      type: "useSkill",
      commandId: "cmd.stale",
      expectedRevision: 0,
      actorId: "friendly.ragnar",
      skillId: "skill.warrior.fatal_strike",
      targetIds: ["enemy.nighthawk"],
    })).rejects.toMatchObject({ kind: "stale", snapshot, revision: 2 });
    expect(fetchMock).toHaveBeenCalledTimes(2);
    fetchMock.mockRestore();
  });

  it("preserves create-response events in provider state", async () => {
    const snapshot = structuredClone(initial);
    const events = [
      { id: "event.1", sequence: 1, type: "battleStarted" as const, message: "Battle started." },
    ];
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(new Response(JSON.stringify({
      contractVersion: "1.0", battleId: "battle.1", revision: 0,
      data: { events, snapshot },
    }), { status: 200, headers: { "Content-Type": "application/json" } }));

    await expect(new LiveBattleProvider("http://adapter.test").getState()).resolves.toMatchObject({ events });
    fetchMock.mockRestore();
  });
});

describe("format and fallback invariants", () => {
  it.each([1, 2, 3] as const)("%dv%d has exact cards, turn entries, and distinct formation coordinates", (size) => {
    const snapshot = createFormatFixture(size);
    const ids = snapshot.sides.flatMap((side) => side.combatantIds);
    const coordinates = ids.map((id) => {
      const hero = snapshot.combatants[id];
      const position = formationFor(snapshot, hero.sideId, hero.slot);
      return `${position.x},${position.y}`;
    });

    expect(ids).toHaveLength(size * 2);
    expect(snapshot.turnOrder).toHaveLength(size * 2);
    expect(new Set(coordinates)).toHaveProperty("size", size * 2);
  });

  it("uses class fallback for Ragnar and initials fallback for Nighthawk", () => {
    expect(resolveAsset({
      kind: "portrait", key: "hero.warrior.weapon_master", name: "Ragnar", className: "Warrior",
    })).toMatchObject({ fallback: "class", status: "placeholder" });
    expect(resolveAsset({
      kind: "portrait", key: "hero.rogue.comprehensiveness", name: "Nighthawk", className: "Rogue",
    })).toMatchObject({ fallback: "initials", src: null, status: "placeholder" });
  });
});
