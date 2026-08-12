import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { StageSelectionScreen } from "@/components/stages/StageSelectionScreen";
import { TeamBuilder } from "@/components/battle/TeamBuilder";
import { BattleScreen } from "@/components/battle/BattleScreen";
import { BattleExperience } from "@/components/battle/BattleExperience";
import { createFormatFixture, MockBattleProvider } from "@/lib/battle/fixture";
import type { BattleOutcome, BattleSize } from "@/lib/battle/types";
import { STAGE_DEFINITIONS } from "@/components/stages/stage-config";
import {
  STRUCTURED_STAGE_DEFINITIONS,
  missingStructuredStageRosterIds,
  resolveStructuredStage,
} from "@/components/stages/structured-stage-config";

const push = vi.fn();
const replace = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push, replace }) }));

afterEach(() => {
  push.mockReset();
  replace.mockReset();
  vi.restoreAllMocks();
});

describe("UI-017 stage and structured battle contracts", () => {
  const roster = [
    ["hero.warrior.weapon_master", "Garran", "Warrior", "Weapon Master"],
    ["hero.mage.comprehensiveness", "Elyra", "Mage", "Comprehensiveness"],
    ["hero.priest.comprehensiveness", "Aldric", "Priest", "Comprehensiveness"],
    ["hero.rogue.comprehensiveness", "Hessa", "Rogue", "Comprehensiveness"],
    ["hero.warrior.defence", "Falk", "Warrior", "Defence"],
    ["hero.warrior.berserker", "Rogan", "Warrior", "Berserker"],
  ].map(([definitionId, displayName, faculty, specialization]) => ({ definitionId, displayName, faculty, specialization }));
  const adapterRoster = [
    ...roster,
    ["hero.priest.discipline", "Brenna", "Priest", "Discipline"],
    ["hero.paladin.retribution", "Cael", "Paladin", "Retribution"],
    ["hero.paladin.protection", "Daria", "Paladin", "Protection"],
    ["hero.paladin.holy", "Galahad", "Paladin", "Holy"],
  ].map((hero) => Array.isArray(hero)
    ? { definitionId: hero[0], displayName: hero[1], faculty: hero[2], specialization: hero[3] }
    : hero);

  function endedEnvelope(battleId: string, size: BattleSize, outcome: BattleOutcome) {
    const snapshot = createFormatFixture(size);
    snapshot.phase = "ended";
    snapshot.activeCombatantId = null;
    snapshot.legalActions = [];
    snapshot.outcome = outcome;
    return {
      contractVersion: "1.0",
      battleId,
      revision: 1,
      data: { events: [], snapshot },
    };
  }

  function response(body: unknown) {
    return new Response(JSON.stringify(body), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  }

  async function assignStructuredPlayers(user: ReturnType<typeof userEvent.setup>, size: BattleSize) {
    const ids = ["hero.warrior.weapon_master", "hero.mage.comprehensiveness", "hero.priest.comprehensiveness"];
    for (let index = 0; index < size; index += 1) {
      await user.click(screen.getByRole("button", { name: new RegExp(`Select your Hero ${index + 1}`, "i") }));
      const hero = roster.find((candidate) => candidate.definitionId === ids[index])!;
      await user.click(screen.getByRole("button", { name: new RegExp(`Assign ${hero.faculty} · ${hero.specialization} to your Hero ${index + 1}`, "i") }));
    }
  }

  it("activates Barrack with map-percent geometry while keeping other locations inactive", () => {
    expect(STAGE_DEFINITIONS.filter((stage) => stage.enabled).map((stage) => stage.id))
      .toEqual(["arena", "warriors-barrack"]);
    const barrack = STAGE_DEFINITIONS.find((stage) => stage.id === "warriors-barrack");
    expect(barrack?.destination).toBe("/game");
    expect(barrack?.geometry).toEqual({ leftPercent: 11.5, topPercent: 13.2, widthPercent: 22.6, heightPercent: 21.8 });
    expect(STAGE_DEFINITIONS.filter((stage) => !stage.enabled)).toHaveLength(4);
  });

  it("routes Arena and Barrack by click and keyboard without exposing inactive controls", async () => {
    const user = userEvent.setup();
    render(<StageSelectionScreen />);
    const arena = screen.getByRole("button", { name: "Enter Arena" });
    const barrack = screen.getByRole("button", { name: "Enter Warrior's Barrack" });
    await user.click(barrack);
    expect(push).toHaveBeenLastCalledWith("/game?stage=warriors-barrack");
    fireEvent.keyDown(arena, { key: "Enter" });
    fireEvent.keyDown(barrack, { key: " " });
    expect(push.mock.calls).toEqual([
      ["/game?stage=warriors-barrack"],
      ["/game?stage=arena"],
      ["/game?stage=warriors-barrack"],
    ]);
    expect(screen.getAllByRole("button")).toHaveLength(2);
    for (const name of ["Mage's Tower", "Rogue's Forest", "Paladin's Altar", "Priest's Cathedral"]) {
      expect(screen.queryByRole("button", { name: new RegExp(name, "i") })).not.toBeInTheDocument();
    }
  });

  it("defines the exact four-player roster and ordered fixed Barrack battles", () => {
    const stage = resolveStructuredStage("warriors-barrack");
    expect(stage).not.toBeNull();
    expect(stage?.allowedPlayerDefinitionIds).toEqual([
      "hero.warrior.weapon_master",
      "hero.mage.comprehensiveness",
      "hero.priest.comprehensiveness",
      "hero.rogue.comprehensiveness",
    ]);
    expect(stage?.battles).toEqual([
      { id: "warriors-barrack.battle-1", displayOrder: 1, battleSize: 2, enemyDefinitionIds: ["hero.warrior.defence", "hero.priest.comprehensiveness"] },
      { id: "warriors-barrack.battle-2", displayOrder: 2, battleSize: 1, enemyDefinitionIds: ["hero.warrior.weapon_master"] },
      { id: "warriors-barrack.battle-3", displayOrder: 3, battleSize: 3, enemyDefinitionIds: ["hero.warrior.defence", "hero.warrior.berserker", "hero.priest.comprehensiveness"] },
    ]);
    expect(STRUCTURED_STAGE_DEFINITIONS).toHaveLength(1);
  });

  it("reports missing configured roster IDs instead of silently substituting", () => {
    const stage = resolveStructuredStage("warriors-barrack")!;
    const missing = missingStructuredStageRosterIds(stage, [
      { definitionId: "hero.warrior.weapon_master", displayName: "Garran", faculty: "Warrior", specialization: "Weapon Master" },
    ]);
    expect(missing).toContain("hero.mage.comprehensiveness");
    expect(missing).toContain("hero.warrior.defence");
    expect(missing).not.toContain("hero.warrior.weapon_master");
  });

  it("blocks a structured builder on missing configured IDs and retries the roster boundary", async () => {
    const user = userEvent.setup();
    const incompleteRoster = adapterRoster.map((hero) => hero.definitionId === "hero.warrior.berserker"
      ? { definitionId: "hero.unconfigured.extra", displayName: "Extra", faculty: "Extra", specialization: "Extra" }
      : hero);
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(response({ contractVersion: "1.0", heroes: incompleteRoster }))
      .mockResolvedValueOnce(response({ contractVersion: "1.0", heroes: adapterRoster }));

    render(<BattleExperience selectedStageId="warriors-barrack" countdownStepMs={0} />);

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("STAGE CONFIGURATION UNAVAILABLE");
    expect(alert).toHaveTextContent("hero.warrior.berserker");
    expect(screen.queryByRole("heading", { name: "Team Builder" })).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Retry roster" }));
    expect(await screen.findByRole("heading", { name: "Battle 1" })).toBeVisible();
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("renders immutable structured Battle 1 controls and emits the existing fixed-enemy payload", async () => {
    const user = userEvent.setup();
    const onStart = vi.fn();
    const stage = resolveStructuredStage("warriors-barrack")!;
    render(<TeamBuilder mode="structured" stage={stage} battle={stage.battles[0]} roster={roster} onStart={onStart} />);
    expect(screen.getByRole("heading", { name: "Warrior's Barrack" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "Battle 1" })).toBeVisible();
    expect(screen.getAllByText("2v2", { exact: true }).length).toBeGreaterThan(0);
    expect(screen.getByLabelText(/Predefined enemy team/i)).toHaveTextContent(/Warrior.*Defence/);
    expect(screen.queryByRole("radio", { name: /1v1|2v2|3v3|Random|Choose team|Computer|Player/i })).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Hero 1")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /Select your Hero 1/i }));
    await user.click(screen.getByRole("button", { name: /Assign Warrior · Weapon Master to your Hero 1/i }));
    await user.click(screen.getByRole("button", { name: /Select your Hero 2/i }));
    await user.click(screen.getByRole("button", { name: /Assign Mage · Comprehensiveness to your Hero 2/i }));
    await user.click(screen.getByRole("button", { name: /ENTER BATTLE/i }));
    expect(onStart).toHaveBeenCalledWith({
      battleSize: 2,
      playerTeam: ["hero.warrior.weapon_master", "hero.mage.comprehensiveness"],
      enemyCompositionMode: "specified",
      enemyTeam: ["hero.warrior.defence", "hero.priest.comprehensiveness"],
      enemyControlMode: "computer",
    });
  });

  it("keeps predefined enemy cards accessible when requested artwork fails", () => {
    const stage = resolveStructuredStage("warriors-barrack")!;
    render(<TeamBuilder mode="structured" stage={stage} battle={stage.battles[0]} roster={roster} onStart={vi.fn()} />);
    const predefinedTeam = screen.getByLabelText(/Predefined enemy team/i);
    const firstEnabledEnemy = predefinedTeam.querySelector<HTMLElement>("[data-enemy-slot='0']")!;
    const image = firstEnabledEnemy.querySelector<HTMLImageElement>("img");
    expect(image).not.toBeNull();
    fireEvent.error(image!);
    expect(firstEnabledEnemy.querySelector(".asset-fallback")).not.toBeNull();
    expect(firstEnabledEnemy.querySelector('[role="img"]')).toHaveAccessibleName(/placeholder artwork/i);
  });

  it("keeps Arena mode configurable with its full roster", () => {
    render(<TeamBuilder roster={roster} onStart={vi.fn()} />);
    expect(screen.getByRole("heading", { name: "Arena" })).toBeVisible();
    expect(screen.getByRole("radio", { name: "3v3" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Choose team" })).toBeInTheDocument();
    expect(document.querySelectorAll("[data-hero-id]")).toHaveLength(6);
  });

  it.each([
    [{ kind: "victory", winningSideId: "friendly" }, "CONTINUE TO BATTLE 2"],
    [{ kind: "victory", winningSideId: "enemy" }, "RETRY BATTLE"],
    [{ kind: "draw" }, "RETRY BATTLE"],
    [{ kind: "roundLimit" }, "RETRY BATTLE"],
  ] as const)("uses the authoritative %s outcome for completion action", async (outcome, label) => {
    const snapshot = createFormatFixture(1);
    snapshot.phase = "ended";
    snapshot.activeCombatantId = null;
    snapshot.legalActions = [];
    snapshot.outcome = outcome;
    const onComplete = vi.fn();
    render(<BattleScreen provider={new MockBattleProvider(snapshot)} mode="live" onBattleComplete={onComplete} completionActionLabel={() => label} />);
    const button = await screen.findByRole("button", { name: label });
    await userEvent.click(button);
    expect(onComplete).toHaveBeenCalledWith(outcome);
  });

  it("orchestrates authoritative friendly victories through all three battles and returns to the Stage Map", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(response({ contractVersion: "1.0", heroes: adapterRoster }))
      .mockResolvedValueOnce(response(endedEnvelope("battle.structured.1", 2, { kind: "victory", winningSideId: "friendly" })))
      .mockResolvedValueOnce(response(endedEnvelope("battle.structured.2", 1, { kind: "victory", winningSideId: "friendly" })))
      .mockResolvedValueOnce(response(endedEnvelope("battle.structured.3", 3, { kind: "victory", winningSideId: "friendly" })));

    render(<BattleExperience selectedStageId="warriors-barrack" countdownStepMs={0} />);

    expect(await screen.findByRole("heading", { name: "Battle 1" })).toBeVisible();
    await assignStructuredPlayers(user, 2);
    await user.click(screen.getByRole("button", { name: "ENTER BATTLE" }));
    await user.click(await screen.findByRole("button", { name: "CONTINUE TO BATTLE 2" }));
    expect(await screen.findByRole("heading", { name: "Battle 2" })).toBeVisible();
    await assignStructuredPlayers(user, 1);
    await user.click(screen.getByRole("button", { name: "ENTER BATTLE" }));
    await user.click(await screen.findByRole("button", { name: "CONTINUE TO BATTLE 3" }));
    expect(await screen.findByRole("heading", { name: "Battle 3" })).toBeVisible();
    await assignStructuredPlayers(user, 3);
    await user.click(screen.getByRole("button", { name: "ENTER BATTLE" }));
    await user.click(await screen.findByRole("button", { name: "RETURN TO STAGE MAP" }));

    expect(replace).toHaveBeenCalledOnce();
    expect(replace).toHaveBeenCalledWith("/stages");
    const payloads = fetchMock.mock.calls
      .filter(([, init]) => init?.method === "POST")
      .map(([, init]) => JSON.parse(String(init?.body)));
    expect(payloads).toEqual([
      expect.objectContaining({ battleSize: 2, enemyTeam: ["hero.warrior.defence", "hero.priest.comprehensiveness"] }),
      expect.objectContaining({ battleSize: 1, enemyTeam: ["hero.warrior.weapon_master"] }),
      expect.objectContaining({ battleSize: 3, enemyTeam: ["hero.warrior.defence", "hero.warrior.berserker", "hero.priest.comprehensiveness"] }),
    ]);
  });

  it.each([
    { kind: "victory", winningSideId: "enemy" },
    { kind: "draw", winningSideId: null },
    { kind: "roundLimit", winningSideId: null },
  ] satisfies BattleOutcome[])("retries Battle 1 without advancement after $kind", async (outcome) => {
    const user = userEvent.setup();
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(response({ contractVersion: "1.0", heroes: adapterRoster }))
      .mockResolvedValueOnce(response(endedEnvelope(`battle.retry.${outcome.kind}`, 2, outcome)));

    render(<BattleExperience selectedStageId="warriors-barrack" countdownStepMs={0} />);
    await screen.findByRole("heading", { name: "Battle 1" });
    await assignStructuredPlayers(user, 2);
    await user.click(await screen.findByRole("button", { name: "ENTER BATTLE" }));
    await user.click(await screen.findByRole("button", { name: "RETRY BATTLE" }));

    expect(await screen.findByRole("heading", { name: "Battle 1" })).toBeVisible();
    expect(screen.getAllByText("Battle 1 of 3")).toHaveLength(2);
    expect(screen.queryByRole("heading", { name: "Battle 2" })).not.toBeInTheDocument();
    expect(replace).not.toHaveBeenCalled();
  });
});
