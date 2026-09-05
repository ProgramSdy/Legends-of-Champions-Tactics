import { render, screen, waitFor } from "@testing-library/react";
import { readFileSync } from "node:fs";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ArenaRunExperience } from "@/components/battle/ArenaRunExperience";
import { DebugBattleExperience } from "@/components/battle/DebugBattleExperience";
import { StageSelectionScreen } from "@/components/stages/StageSelectionScreen";
import { createFormatFixture } from "@/lib/battle/fixture";
import type { ArenaStateResponse, HeroDefinitionSummary, PlayerProgressionResponse } from "@/lib/battle/types";

const routerReplace = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn(), replace: routerReplace }) }));

const roster: HeroDefinitionSummary[] = [
  ["hero.warrior.weapon_master", "Ragnar", "Warrior", "Weapon Master"],
  ["hero.warrior.defence", "Wrathe", "Warrior", "Defence"],
  ["hero.warrior.berserker", "Berserker", "Warrior", "Berserker"],
  ["hero.mage.comprehensiveness", "Mage", "Mage", "Comprehensiveness"],
  ["hero.rogue.comprehensiveness", "Rogue", "Rogue", "Comprehensiveness"],
  ["hero.priest.comprehensiveness", "Priest", "Priest", "Comprehensiveness"],
  ["hero.priest.discipline", "Discipline", "Priest", "Discipline"],
  ["hero.paladin.retribution", "Retribution", "Paladin", "Retribution"],
  ["hero.paladin.protection", "Protection", "Paladin", "Protection"],
  ["hero.paladin.holy", "Holy", "Paladin", "Holy"],
].map(([definitionId, displayName, faculty, specialization]) => ({
  definitionId, displayName, faculty, specialization,
}));

const unlockedIds = roster.slice(0, 6).map((hero) => hero.definitionId);

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function progression(ids = unlockedIds): PlayerProgressionResponse {
  return {
    contractVersion: "1.0",
    profileId: "profile.slot.1",
    unlockedHeroDefinitionIds: ids,
    stageProgress: [
      { stageId: "paladins-altar", highestCompletedBattle: 0, unlockedBattle: 1, completed: false },
      { stageId: "warriors-barrack", highestCompletedBattle: 0, unlockedBattle: 1, completed: false },
    ],
    grantedRewards: [],
  };
}

function arenaState({ eligible = true, run = null }: {
  eligible?: boolean;
  run?: ArenaStateResponse["run"];
} = {}): ArenaStateResponse {
  return {
    contractVersion: "1.0",
    profileId: "profile.slot.1",
    eligibility: {
      eligible,
      unlockedHeroCount: eligible ? 6 : 4,
      requiredHeroCount: 6,
    },
    run,
  };
}

function activeRun(): NonNullable<ArenaStateResponse["run"]> {
  return {
    runId: "arena.run.1",
    status: "active",
    squadDefinitionIds: unlockedIds,
    currentNodeIndex: 1,
    createdAt: "2026-08-31T00:00:00Z",
    completedAt: null,
    nodes: Array.from({ length: 12 }, (_, index) => ({
      nodeIndex: index + 1,
      battleSize: index === 0 ? 2 as const : 1 as const,
      enemyFormation: index === 0 ? "front-rear" as const : null,
      enemyDefinitionIds: index === 0
        ? ["hero.warrior.defence", "hero.mage.comprehensiveness"]
        : ["hero.paladin.holy"],
      completed: false,
    })),
  };
}

afterEach(() => {
  vi.restoreAllMocks();
  routerReplace.mockReset();
});

describe("UI-023 Stage Map and debug boundary", () => {
  it("adds keyboard-reachable Game Start and Engineering routes without changing hotspots", () => {
    render(<StageSelectionScreen />);
    expect(screen.getByRole("link", { name: "Return to Game Start" })).toHaveAttribute("href", "/");
    expect(screen.getByRole("link", { name: "Open Engineering Test and Debugging" })).toHaveAttribute("href", "/debug");
    expect(screen.getAllByRole("button")).toHaveLength(3);
  });

  it("loads only the full roster and keeps a clear Stage Map return route", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(json({ contractVersion: "1.0", heroes: roster }));
    render(<DebugBattleExperience />);
    expect(await screen.findByRole("heading", { name: "Engineering Test & Debugging" })).toBeVisible();
    expect(screen.getByText("TOTAL HERO: 10")).toBeVisible();
    expect(screen.getByRole("link", { name: /back to stage map/i })).toHaveAttribute("href", "/stages");
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(String(fetchMock.mock.calls[0][0])).toMatch(/\/api\/v1\/heroes$/);
    expect(fetchMock.mock.calls.some(([input]) => /progression|save-slots|arena/.test(String(input)))).toBe(false);
  });

  it("creates a test battle only through the debug endpoint", async () => {
    const paths: string[] = [];
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const path = String(input);
      paths.push(path);
      if (path.endsWith("/api/v1/heroes")) return json({ contractVersion: "1.0", heroes: roster });
      const snapshot = createFormatFixture(1);
      snapshot.phase = "ended";
      snapshot.outcome = { kind: "draw", winningSideId: null };
      return json({ contractVersion: "1.0", battleId: "debug.battle.1", revision: 1, data: { events: [], snapshot } });
    });
    render(<DebugBattleExperience countdownStepMs={0} />);
    const user = userEvent.setup();
    await user.click(await screen.findByRole("button", { name: /Select your Hero 1/i }));
    await user.click(screen.getByRole("button", { name: /Assign Warrior · Weapon Master to your Hero 1/i }));
    await user.click(screen.getByRole("button", { name: "ENTER BATTLE" }));
    expect(await screen.findByRole("button", { name: "RETURN TO DEBUG BUILDER" })).toBeVisible();
    expect(paths.some((path) => path.endsWith("/api/v1/debug/battles"))).toBe(true);
    expect(paths.some((path) => /progression|save-slots|arena/.test(path))).toBe(false);
  });
});

describe("UI-023 Arena Run frontend authority", () => {
  function installArenaFetch(state: ArenaStateResponse, onCreate?: (body: unknown) => ArenaStateResponse) {
    return vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const path = String(input);
      if (path.endsWith("/api/v1/arena") && !init?.method) return json(state);
      if (path.endsWith("/api/v1/heroes")) return json({ contractVersion: "1.0", heroes: roster });
      if (path.endsWith("/api/v1/progression")) return json(progression());
      if (path.endsWith("/api/v1/arena/runs") && init?.method === "POST") {
        return json(onCreate?.(JSON.parse(String(init.body))) ?? state);
      }
      throw new Error(`Unexpected request ${path}`);
    });
  }

  it("shows the exact eligibility count and does not offer squad selection below six", async () => {
    installArenaFetch(arenaState({ eligible: false }));
    render(<ArenaRunExperience />);
    expect(await screen.findByRole("heading", { name: "Six unlocked heroes required" })).toBeVisible();
    expect(screen.getByText("4 / 6")).toBeVisible();
    expect(screen.queryByRole("button", { name: /add to arena squad/i })).not.toBeInTheDocument();
  });

  it("requires six ordered owned heroes and renders the stable server-authored path", async () => {
    let requestBody: unknown;
    installArenaFetch(arenaState(), (body) => {
      requestBody = body;
      return arenaState({ run: activeRun() });
    });
    render(<ArenaRunExperience />);
    const user = userEvent.setup();
    const choices = await screen.findAllByRole("button", { name: /add to arena squad/i });
    expect(choices).toHaveLength(6);
    for (const choice of choices) await user.click(choice);
    await user.click(screen.getByRole("button", { name: "LOCK SQUAD & START RUN" }));
    await waitFor(() => expect(document.querySelectorAll("[data-node-index]")).toHaveLength(12));
    expect(requestBody).toEqual({ squadDefinitionIds: unlockedIds });
    expect(screen.getByRole("heading", { name: "Battle 1 · 2v2" })).toBeVisible();
    expect(screen.getByRole("radio", { name: /Front and Rear/ })).toBeVisible();
    expect(screen.getByRole("heading", { name: "Your Team" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "Enemy Team" })).toBeVisible();
    expect(screen.getByText("TOTAL HERO: 6")).toBeVisible();
    expect(screen.queryByRole("radio", { name: /battle size/i })).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/seed/i)).not.toBeInTheDocument();
  });

  it("uses a square frame for each Arena squad portrait", async () => {
    installArenaFetch(arenaState());
    render(<ArenaRunExperience />);
    await screen.findAllByRole("button", { name: /add to arena squad/i });

    expect(document.querySelectorAll(".arena-squad-portrait")).toHaveLength(6);
    const css = readFileSync("app/globals.css", "utf8");
    expect(css).toContain(".arena-squad-grid>button{grid-template-rows:auto auto auto}");
    expect(css).toContain(".arena-squad-portrait{width:100%;aspect-ratio:1}");
  });

  it("keeps the Arena Run hub vertically scrollable like the Team Builder", () => {
    const css = readFileSync("app/globals.css", "utf8");
    expect(css).toContain(".arena-run-hub{height:100dvh;min-height:0;");
    expect(css).toContain("overflow-y:auto;scrollbar-gutter:stable;overscroll-behavior-y:contain");
    expect(css).toContain(".arena-run-hub::-webkit-scrollbar{width:12px}");
  });

  it("launches only the current node and advances from the authoritative completion response", async () => {
    const initial = activeRun();
    const advanced = structuredClone(initial);
    advanced.currentNodeIndex = 2;
    advanced.nodes[0].completed = true;
    const calls: Array<{ path: string; body?: unknown }> = [];
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const path = String(input);
      calls.push({ path, body: init?.body ? JSON.parse(String(init.body)) : undefined });
      if (path.endsWith("/api/v1/arena") && !init?.method) return json(arenaState({ run: initial }));
      if (path.endsWith("/api/v1/heroes")) return json({ contractVersion: "1.0", heroes: roster });
      if (path.endsWith("/api/v1/progression")) return json(progression());
      if (path.endsWith("/api/v1/arena/runs/arena.run.1/nodes/1/battles")) {
        const snapshot = createFormatFixture(2);
        snapshot.phase = "ended";
        snapshot.outcome = { kind: "victory", winningSideId: "friendly" };
        return json({ contractVersion: "1.0", battleId: "arena.battle.1", revision: 1, data: { events: [], snapshot } });
      }
      if (path.endsWith("/api/v1/arena/battles/arena.battle.1/completion")) {
        return json({
          contractVersion: "1.0",
          battleId: "arena.battle.1",
          alreadyCommitted: false,
          arena: arenaState({ run: advanced }),
        });
      }
      throw new Error(`Unexpected request ${path}`);
    });

    render(<ArenaRunExperience countdownStepMs={0} />);
    const user = userEvent.setup();
    await screen.findByRole("heading", { name: "Your Team" });
    await user.click(screen.getAllByRole("button", { name: /Assign .* to your Hero 1/i })[0]);
    await user.click(screen.getByRole("button", { name: "Select your Hero 2" }));
    await user.click(screen.getAllByRole("button", { name: /Assign .* to your Hero 2/i })[1]);
    await user.click(screen.getByRole("radio", { name: /Side by Side/ }));
    await user.click(screen.getByRole("button", { name: "ENTER BATTLE" }));
    await user.click(await screen.findByRole("button", { name: "CONTINUE ARENA RUN" }));
    expect(await screen.findByRole("heading", { name: "Battle 2 · 1v1" })).toBeVisible();
    expect(calls.find((call) => call.path.endsWith("/nodes/1/battles"))?.body).toEqual({
      playerTeam: unlockedIds.slice(0, 2),
      playerFormation: "side-by-side",
    });
    expect(calls.some((call) => call.path.includes("/nodes/2/battles"))).toBe(false);
    expect(calls.filter((call) => call.path.endsWith("/completion"))).toHaveLength(1);
  });

  it("acknowledges the twelfth victory with OK and returns to the Stage Map", async () => {
    const initial = activeRun();
    const completed = structuredClone(initial);
    completed.status = "completed";
    completed.currentNodeIndex = null;
    completed.completedAt = "2026-08-31T01:00:00Z";
    completed.nodes.forEach((node) => { node.completed = true; });
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const path = String(input);
      if (path.endsWith("/api/v1/arena") && !init?.method) return json(arenaState({ run: initial }));
      if (path.endsWith("/api/v1/heroes")) return json({ contractVersion: "1.0", heroes: roster });
      if (path.endsWith("/api/v1/progression")) return json(progression());
      if (path.endsWith("/api/v1/arena/runs/arena.run.1/nodes/1/battles")) {
        const snapshot = createFormatFixture(2);
        snapshot.phase = "ended";
        snapshot.outcome = { kind: "victory", winningSideId: "friendly" };
        return json({ contractVersion: "1.0", battleId: "arena.battle.12", revision: 1, data: { events: [], snapshot } });
      }
      if (path.endsWith("/api/v1/arena/battles/arena.battle.12/completion")) {
        return json({ contractVersion: "1.0", battleId: "arena.battle.12", alreadyCommitted: false, arena: arenaState({ run: completed }) });
      }
      throw new Error(`Unexpected request ${path}`);
    });

    render(<ArenaRunExperience countdownStepMs={0} />);
    const user = userEvent.setup();
    await screen.findByRole("heading", { name: "Your Team" });
    await user.click(screen.getAllByRole("button", { name: /Assign .* to your Hero 1/i })[0]);
    await user.click(screen.getByRole("button", { name: "Select your Hero 2" }));
    await user.click(screen.getAllByRole("button", { name: /Assign .* to your Hero 2/i })[1]);
    await user.click(screen.getByRole("button", { name: "ENTER BATTLE" }));
    await user.click(await screen.findByRole("button", { name: "CONTINUE ARENA RUN" }));
    expect(await screen.findByRole("heading", { name: "Twelve victories secured" })).toBeVisible();
    await user.click(screen.getByRole("button", { name: "OK" }));
    expect(routerReplace).toHaveBeenCalledWith("/stages");
  });

  it("only abandons an Arena Run after YES, then returns to the Stage Map", async () => {
    const calls: string[] = [];
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const path = String(input);
      calls.push(path);
      if (path.endsWith("/api/v1/arena") && !init?.method) return json(arenaState({ run: activeRun() }));
      if (path.endsWith("/api/v1/heroes")) return json({ contractVersion: "1.0", heroes: roster });
      if (path.endsWith("/api/v1/progression")) return json(progression());
      if (path.endsWith("/api/v1/arena/runs/arena.run.1/abandon") && init?.method === "POST") {
        return json(arenaState({ run: null }));
      }
      throw new Error(`Unexpected request ${path}`);
    });

    render(<ArenaRunExperience />);
    const user = userEvent.setup();
    await user.click(await screen.findByRole("button", { name: "GIVE UP CURRENT RUN" }));
    expect(screen.getByRole("dialog", { name: "Give up your current run?" })).toBeVisible();
    await user.click(screen.getByRole("button", { name: "NO" }));
    expect(calls.some((path) => path.endsWith("/abandon"))).toBe(false);

    await user.click(screen.getByRole("button", { name: "GIVE UP CURRENT RUN" }));
    await user.click(screen.getByRole("button", { name: "YES" }));
    await waitFor(() => expect(calls.some((path) => path.endsWith("/arena.run.1/abandon"))).toBe(true));
    expect(routerReplace).toHaveBeenCalledWith("/stages");
  });

  it("opens the six-hero squad builder when the player re-enters Arena after a completed run", async () => {
    const completed = activeRun();
    completed.status = "completed";
    completed.currentNodeIndex = null;
    completed.completedAt = "2026-08-31T01:00:00Z";
    completed.nodes.forEach((node) => { node.completed = true; });
    installArenaFetch(arenaState({ run: completed }));

    render(<ArenaRunExperience />);
    expect(await screen.findByRole("heading", { name: "Build your six-hero squad" })).toBeVisible();
    expect(screen.getAllByRole("button", { name: /add to arena squad/i })).toHaveLength(6);
    expect(screen.queryByRole("heading", { name: "Twelve victories secured" })).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: /Battle \d+ ·/ })).not.toBeInTheDocument();
  });
});
