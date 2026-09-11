import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { afterEach, describe, expect, it, vi } from "vitest";
import { BattleScreen } from "@/components/battle/BattleScreen";
import { MockBattleProvider } from "@/lib/battle/fixture";
import { LiveBattleProvider } from "@/lib/battle/liveProvider";
import type { BattlePreview, BattlePreviewRequest, BattlePreviewTarget, BattleSnapshot } from "@/lib/battle/types";

function targetFact(targetId: string, overrides: Partial<BattlePreviewTarget> = {}): BattlePreviewTarget {
  return {
    targetId,
    currentHp: 41,
    maxHp: 97,
    primary: { kind: "damage", amountRange: { min: 17, max: 31 } },
    directHitChancePercent: 73,
    consequences: [],
    ...overrides,
  };
}

function responseFor(request: BattlePreviewRequest, targets = request.targetIds.map((id) => targetFact(id))): BattlePreview {
  return {
    revision: request.expectedRevision,
    actorId: request.actorId,
    skillId: request.skillId,
    requestedTargetIds: [...request.targetIds],
    selectedTargetIds: [...request.targetIds],
    coverage: "authoritative",
    targets,
  };
}

async function mageSnapshot(skillId = "skill.mage.fireball", displayName = "Fireball", targets = ["enemy.sashein", "enemy.andonidas"]): Promise<BattleSnapshot> {
  const snapshot = (await new MockBattleProvider().getState()).snapshot;
  const actor = snapshot.combatants[snapshot.activeCombatantId!];
  actor.definitionId = "hero.mage.comprehensiveness";
  actor.faculty = "Mage";
  actor.specialization = "Comprehensiveness";
  actor.skills = [{
    id: skillId,
    displayName,
    targetMode: skillId === "skill.mage.arcane_missiles" ? "multipleEnemies" : "singleEnemy",
    maximumTargets: skillId === "skill.mage.arcane_missiles" ? 2 : 1,
    cooldownRemaining: 0,
    available: true,
    unavailableReason: null,
    resourceCost: null,
  }];
  snapshot.legalActions = [{
    actorId: actor.id,
    skillId,
    minimumTargets: skillId === "skill.mage.arcane_missiles" ? 2 : 1,
    maximumTargets: skillId === "skill.mage.arcane_missiles" ? 2 : 1,
    validTargetIds: targets,
  }];
  return snapshot;
}

class PreviewProvider extends MockBattleProvider {
  previewAction = vi.fn(async (request: BattlePreviewRequest, _signal?: AbortSignal) => responseFor(request));
}

async function renderPreviewBattle(provider: PreviewProvider) {
  render(<BattleScreen provider={provider} mode="live" />);
  await screen.findByRole("region", { name: "Battlefield" });
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("BATTLE-TRANSPARENCY-001 target preview", () => {
  it("posts the revision-bound request through LiveBattleProvider and validates the echoed result", async () => {
    const snapshot = await mageSnapshot();
    const request: BattlePreviewRequest = {
      expectedRevision: 1,
      actorId: "friendly.arthas",
      skillId: "skill.mage.fireball",
      targetIds: ["enemy.sashein"],
    };
    const preview = responseFor(request);
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify({
        contractVersion: "1.0", battleId: "battle.preview", revision: 1, data: { events: [], snapshot },
      }), { status: 200, headers: { "Content-Type": "application/json" } }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        contractVersion: "1.0", battleId: "battle.preview", revision: 1, data: preview,
      }), { status: 200, headers: { "Content-Type": "application/json" } }));
    const provider = new LiveBattleProvider("http://adapter.test");
    await provider.getState();
    const controller = new AbortController();

    await expect(provider.previewAction(request, controller.signal)).resolves.toEqual(preview);
    expect(fetchMock).toHaveBeenLastCalledWith(
      "http://adapter.test/api/v1/battles/battle.preview/preview",
      expect.objectContaining({ method: "POST", body: JSON.stringify(request), signal: controller.signal }),
    );
  });

  it("requests and renders verbatim server-authored facts on pointer hover", async () => {
    const provider = new PreviewProvider(await mageSnapshot());
    provider.previewAction.mockImplementation(async (request) => responseFor(request, [targetFact(request.targetIds[0], {
      consequences: [{ kind: "bleed", certainty: "conditional", chancePercent: 50 }],
    })]));
    await renderPreviewBattle(provider);

    fireEvent.click(screen.getByRole("button", { name: /Fireball/i }));
    const target = screen.getByRole("button", { name: "Sashein, selectable target" });
    fireEvent.mouseEnter(target);

    await waitFor(() => expect(document.querySelector(".target-preview-card.ready")).toBeInTheDocument());
    const panel = document.querySelector<HTMLElement>(".target-preview-card.ready")!;
    expect(panel).toHaveTextContent("Damage17–31");
    expect(panel).toHaveTextContent("Hit Chance73%");
    expect(panel).toHaveTextContent("Target HP41 / 97");
    expect(panel).toHaveTextContent("Bleed50% chance");
    expect(provider.previewAction).toHaveBeenCalledWith({
      expectedRevision: 1,
      actorId: "friendly.arthas",
      skillId: "skill.mage.fireball",
      targetIds: ["enemy.sashein"],
    }, expect.any(AbortSignal));
    expect(target.getAttribute("aria-describedby")).toMatch(/target-preview/);
  });

  it("uses keyboard focus for the same request and keeps Enter target selection unchanged", async () => {
    const provider = new PreviewProvider(await mageSnapshot());
    await renderPreviewBattle(provider);
    fireEvent.click(screen.getByRole("button", { name: /Fireball/i }));
    const target = screen.getByRole("button", { name: "Sashein, selectable target" });

    fireEvent.focus(target);
    expect(await screen.findByText(/FIREBALL/)).toBeVisible();
    fireEvent.keyDown(target, { key: "Enter" });
    expect(target).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: "CAST SKILL" })).toBeEnabled();
  });

  it("does not request previews for skills outside the five-skill audited allowlist", async () => {
    const snapshot = (await new MockBattleProvider().getState()).snapshot;
    const provider = new PreviewProvider(snapshot);
    await renderPreviewBattle(provider);
    fireEvent.click(screen.getByRole("button", { name: /Life Drain/i }));
    fireEvent.mouseEnter(screen.getByRole("button", { name: "Sashein, selectable target" }));

    await new Promise((resolve) => window.setTimeout(resolve, 120));
    expect(provider.previewAction).not.toHaveBeenCalled();
    expect(screen.queryByText("Preview unavailable")).not.toBeInTheDocument();
  });

  it.each([
    ["skill.rogue.poisoned_dagger", "Poisoned Dagger", { kind: "poison" as const, certainty: "conditional" as const, chancePercent: 85 }, "Poison85% chance"],
    ["skill.mage.frost_bolt", "Frost Bolt", { kind: "cold" as const, certainty: "onHit" as const }, "On hitApplies Cold"],
  ])("renders the separate server-authored consequence for %s", async (skillId, displayName, consequence, expected) => {
    const provider = new PreviewProvider(await mageSnapshot(skillId, displayName));
    provider.previewAction.mockImplementation(async (request) => responseFor(request, [targetFact(request.targetIds[0], {
      consequences: [consequence],
    })]));
    await renderPreviewBattle(provider);
    fireEvent.click(screen.getByRole("button", { name: new RegExp(displayName, "i") }));
    fireEvent.mouseEnter(screen.getByRole("button", { name: "Sashein, selectable target" }));

    await waitFor(() => expect(document.querySelector(".target-preview-card.ready")).toHaveTextContent(expected));
  });

  it("requires a complete Arcane Missiles pair and displays per-target facts without an aggregate", async () => {
    const provider = new PreviewProvider(await mageSnapshot("skill.mage.arcane_missiles", "Arcane Missiles"));
    provider.previewAction.mockImplementation(async (request) => responseFor(request, [
      targetFact(request.targetIds[0], { primary: { kind: "damage", amountRange: { min: 11, max: 19 } } }),
      targetFact(request.targetIds[1], { currentHp: 64, maxHp: 81, primary: { kind: "damage", amountRange: { min: 7, max: 14 } }, directHitChancePercent: 88 }),
    ]));
    await renderPreviewBattle(provider);

    fireEvent.click(screen.getByRole("button", { name: /Arcane Missiles/i }));
    const first = screen.getByRole("button", { name: "Sashein, selectable target" });
    const second = screen.getByRole("button", { name: "Andonidas, selectable target" });
    fireEvent.mouseEnter(first);
    await new Promise((resolve) => window.setTimeout(resolve, 120));
    expect(provider.previewAction).not.toHaveBeenCalled();
    expect(screen.getByText("SELECT 2 TARGETS · 0 SELECTED")).toBeVisible();

    fireEvent.click(first);
    fireEvent.focus(first);
    fireEvent.mouseLeave(first);
    fireEvent.mouseEnter(second);
    await waitFor(() => expect(provider.previewAction).toHaveBeenCalledOnce());
    expect(provider.previewAction.mock.calls[0][0].targetIds).toEqual(["enemy.sashein", "enemy.andonidas"]);
    expect(await screen.findByText("11–19")).toBeVisible();
    expect(screen.getByText("7–14")).toBeVisible();
    expect(screen.queryByText(/total damage/i)).not.toBeInTheDocument();
  });

  it("discards a superseded response and aborts its request", async () => {
    const provider = new PreviewProvider(await mageSnapshot());
    const pending: Array<{ request: BattlePreviewRequest; signal?: AbortSignal; resolve: (preview: BattlePreview) => void }> = [];
    provider.previewAction.mockImplementation((request, signal) => new Promise((resolve) => pending.push({ request, signal, resolve })));
    await renderPreviewBattle(provider);
    fireEvent.click(screen.getByRole("button", { name: /Fireball/i }));
    const first = screen.getByRole("button", { name: "Sashein, selectable target" });
    const second = screen.getByRole("button", { name: "Andonidas, selectable target" });

    fireEvent.mouseEnter(first);
    await waitFor(() => expect(pending).toHaveLength(1));
    fireEvent.mouseLeave(first);
    fireEvent.mouseEnter(second);
    await waitFor(() => expect(pending).toHaveLength(2));
    expect(pending[0].signal?.aborted).toBe(true);

    pending[0].resolve(responseFor(pending[0].request, [targetFact("enemy.sashein", { currentHp: 9 })]));
    pending[1].resolve(responseFor(pending[1].request, [targetFact("enemy.andonidas", { currentHp: 52 })]));
    expect(await screen.findByText("52 / 97")).toBeVisible();
    expect(screen.queryByText("9 / 97")).not.toBeInTheDocument();
  });

  it("shows a non-blocking unavailable state and a truthful prevented result", async () => {
    const unavailable = new PreviewProvider(await mageSnapshot());
    unavailable.previewAction.mockRejectedValueOnce(new Error("network unavailable"));
    const view = render(<BattleScreen provider={unavailable} mode="live" />);
    await screen.findByRole("region", { name: "Battlefield" });
    fireEvent.click(screen.getByRole("button", { name: /Fireball/i }));
    const target = screen.getByRole("button", { name: "Sashein, selectable target" });
    fireEvent.mouseEnter(target);
    expect(await screen.findByText("Preview unavailable")).toBeVisible();
    fireEvent.click(target);
    expect(screen.getByRole("button", { name: "CAST SKILL" })).toBeEnabled();

    view.unmount();
    const prevented = new PreviewProvider(await mageSnapshot());
    prevented.previewAction.mockImplementation(async (request) => responseFor(request, [targetFact(request.targetIds[0], {
      primary: { kind: "prevented", amountRange: { min: 0, max: 0 }, reasonId: "status.shield_of_protection" },
      directHitChancePercent: 62,
    })]));
    await renderPreviewBattle(prevented);
    fireEvent.click(screen.getByRole("button", { name: /Fireball/i }));
    fireEvent.mouseEnter(screen.getByRole("button", { name: "Sashein, selectable target" }));
    const blocked = await screen.findByText("0 · Blocked");
    expect(blocked).toBeVisible();
    expect(within(blocked.closest("dl")!).queryByText("Hit Chance")).not.toBeInTheDocument();
  });

  it("pins selected-target facts in the compact battlefield dock", async () => {
    const oldWidth = window.innerWidth;
    const oldHeight = window.innerHeight;
    Object.defineProperty(window, "innerWidth", { configurable: true, value: 900 });
    Object.defineProperty(window, "innerHeight", { configurable: true, value: 700 });
    try {
      const provider = new PreviewProvider(await mageSnapshot());
      await renderPreviewBattle(provider);
      fireEvent.click(screen.getByRole("button", { name: /Fireball/i }));
      const target = screen.getByRole("button", { name: "Sashein, selectable target" });
      fireEvent.mouseEnter(target);
      fireEvent.click(target);
      fireEvent.mouseLeave(target);

      await waitFor(() => expect(document.querySelector(".target-preview-dock")).toBeInTheDocument());
      const dock = document.querySelector<HTMLElement>(".target-preview-dock")!;
      await waitFor(() => expect(dock.querySelector(".target-preview-card.ready")).toBeInTheDocument());
      expect(dock).toHaveAttribute("id", "battle-target-preview-dock");
      expect(dock).toHaveTextContent("Damage17–31");
      expect(target).toHaveAttribute("aria-describedby", "battle-target-preview-dock");
    } finally {
      Object.defineProperty(window, "innerWidth", { configurable: true, value: oldWidth });
      Object.defineProperty(window, "innerHeight", { configurable: true, value: oldHeight });
      fireEvent(window, new Event("resize"));
    }
  });

  it("keeps both preview presentations outside pointer hit testing", () => {
    const css = readFileSync("app/globals.css", "utf8").replace(/\s+/g, "");
    expect(css).toMatch(/\.target-preview-card\{[^}]*pointer-events:none/);
    expect(css).toMatch(/\.target-preview-dock\{[^}]*pointer-events:none/);
  });
});
