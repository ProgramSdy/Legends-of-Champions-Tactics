import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { BattleExperience } from "@/components/battle/BattleExperience";
import { BattleScreen } from "@/components/battle/BattleScreen";
import { TeamBuilder } from "@/components/battle/TeamBuilder";
import { createFormatFixture, MockBattleProvider } from "@/lib/battle/fixture";
import {
  fetchPlayerProgression,
  fetchStructuredStages,
  LiveBattleProvider,
} from "@/lib/battle/liveProvider";
import {
  STRUCTURED_STAGE_DEFINITIONS,
  type StructuredStageDefinition,
} from "@/components/stages/structured-stage-config";
import type {
  BattleOutcome,
  HeroDefinitionSummary,
  PlayerProgressionResponse,
} from "@/lib/battle/types";

const replace = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn(), replace }) }));

const roster: HeroDefinitionSummary[] = [
  ["hero.warrior.weapon_master", "Garran", "Warrior", "Weapon Master"],
  ["hero.mage.comprehensiveness", "Elyra", "Mage", "Comprehensiveness"],
  ["hero.priest.comprehensiveness", "Aldric", "Priest", "Comprehensiveness"],
  ["hero.rogue.comprehensiveness", "Hessa", "Rogue", "Comprehensiveness"],
  ["hero.warrior.defence", "Falk", "Warrior", "Defence"],
  ["hero.warrior.berserker", "Rogan", "Warrior", "Berserker"],
  ["hero.priest.discipline", "Brenna", "Priest", "Discipline"],
  ["hero.paladin.retribution", "Cael", "Paladin", "Retribution"],
  ["hero.paladin.protection", "Daria", "Paladin", "Protection"],
  ["hero.paladin.holy", "Galahad", "Paladin", "Holy"],
].map(([definitionId, displayName, faculty, specialization]) => ({
  definitionId,
  displayName,
  faculty,
  specialization,
}));

const initialUnlocked = [
  "hero.priest.comprehensiveness",
  "hero.priest.discipline",
  "hero.mage.comprehensiveness",
  "hero.warrior.weapon_master",
  "hero.rogue.comprehensiveness",
];

function progression(
  paladinCompleted = 0,
  paladinUnlocked = 1,
  unlockedHeroDefinitionIds = initialUnlocked,
): PlayerProgressionResponse {
  return {
    contractVersion: "1.0",
    profileId: "profile.local.default",
    unlockedHeroDefinitionIds,
    stageProgress: [
      {
        stageId: "paladins-altar",
        highestCompletedBattle: paladinCompleted,
        unlockedBattle: paladinUnlocked,
        completed: paladinCompleted === 9,
      },
      {
        stageId: "warriors-barrack",
        highestCompletedBattle: 0,
        unlockedBattle: 1,
        completed: false,
      },
    ],
    grantedRewards: [],
  };
}

function serverStage(
  stage: StructuredStageDefinition,
  highestCompletedBattle: number,
  unlockedBattle: number,
) {
  return {
    stageId: stage.stageId,
    displayName: stage.displayName,
    progress: {
      stageId: stage.stageId,
      highestCompletedBattle,
      unlockedBattle,
      completed: highestCompletedBattle === 9,
    },
    battles: stage.battles.map((battle) => ({
      id: battle.id,
      displayOrder: battle.displayOrder,
      battleSize: battle.battleSize,
      formation: battle.playerFormation,
      enemyDefinitionIds: [...battle.enemyDefinitionIds],
      reward: battle.completionReward ? {
        rewardId: battle.completionReward.id,
        kind: battle.completionReward.kind,
        heroDefinitionId: battle.completionReward.heroDefinitionId,
        notification: battle.completionReward.notificationMessage,
      } : null,
      unlocked: battle.displayOrder <= unlockedBattle,
      completed: battle.displayOrder <= highestCompletedBattle,
    })),
  };
}

function stagesResponse(paladinCompleted = 0, paladinUnlocked = 1) {
  return {
    contractVersion: "1.0",
    stages: STRUCTURED_STAGE_DEFINITIONS.map((stage) => serverStage(
      stage,
      stage.stageId === "paladins-altar" ? paladinCompleted : 0,
      stage.stageId === "paladins-altar" ? paladinUnlocked : 1,
    )),
  };
}

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function endedEnvelope(size: 1 | 2 | 3, outcome: BattleOutcome, battleId: string) {
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

async function assignPlayers(labels: string[]) {
  const user = userEvent.setup();
  for (const [index, label] of labels.entries()) {
    await user.click(screen.getByRole("button", { name: new RegExp(`Select your Hero ${index + 1}`, "i") }));
    await user.click(screen.getByRole("button", { name: new RegExp(`Assign ${label} to your Hero ${index + 1}`, "i") }));
  }
  return user;
}

afterEach(() => {
  replace.mockReset();
  vi.restoreAllMocks();
});

describe("UI-020 authoritative progression boundary", () => {
  it("validates typed progression and two exact server stage curricula", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const path = String(input);
      return path.endsWith("/api/v1/progression")
        ? json(progression())
        : json(stagesResponse());
    });
    await expect(fetchPlayerProgression("http://adapter.test")).resolves.toEqual(progression());
    const stages = await fetchStructuredStages("http://adapter.test");
    expect(stages.stages).toHaveLength(2);
    expect(stages.stages.flatMap((stage) => stage.battles)).toHaveLength(18);
  });

  it("uses the additive one-based stage launch route and completion contract", async () => {
    const battleId = "battle.ui-020.stage";
    const snapshot = createFormatFixture(2);
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(json({
        contractVersion: "1.0",
        battleId,
        revision: 0,
        data: { events: [], snapshot },
      }))
      .mockResolvedValueOnce(json({
        contractVersion: "1.0",
        battleId,
        alreadyCommitted: false,
        newlyGrantedRewards: [],
        progression: progression(),
      }));
    const body = {
      playerTeam: ["hero.warrior.weapon_master", "hero.mage.comprehensiveness"],
      playerFormation: "front-rear" as const,
    };
    const provider = new LiveBattleProvider(
      "http://adapter.test",
      body,
      "/api/v1/stages/paladins-altar/battles/1",
    );
    await provider.getState();
    await provider.commitStageVictory();
    expect(fetchMock).toHaveBeenNthCalledWith(1,
      "http://adapter.test/api/v1/stages/paladins-altar/battles/1",
      expect.objectContaining({ method: "POST", body: JSON.stringify(body) }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(2,
      `http://adapter.test/api/v1/battles/${battleId}/completion`,
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("renders server-locked steps and filters Arena/training choices to unlocked IDs", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const path = String(input);
      if (path.endsWith("/api/v1/heroes")) return json({ contractVersion: "1.0", heroes: roster });
      if (path.endsWith("/api/v1/progression")) return json(progression());
      return json(stagesResponse());
    });
    render(<BattleExperience selectedStageId="paladins-altar" />);
    expect(await screen.findByRole("heading", { name: "Battle 1" })).toBeVisible();
    expect(screen.getByRole("button", { name: "Battle 1, available" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Battle 2, locked" })).toBeDisabled();
    expect(document.querySelectorAll("[data-hero-id]")).toHaveLength(5);
    expect(screen.queryByRole("button", { name: /Assign Paladin · Protection/i })).not.toBeInTheDocument();
    expect(screen.getByLabelText(/Predefined enemy team/i)).toHaveTextContent(/Paladin.*Protection/);
  });

  it("lets the player choose a structured formation without sending enemies or control from React", async () => {
    const calls: Array<{ path: string; body?: unknown }> = [];
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const path = String(input);
      calls.push({ path, body: init?.body ? JSON.parse(String(init.body)) : undefined });
      if (path.endsWith("/api/v1/heroes")) return json({ contractVersion: "1.0", heroes: roster });
      if (path.endsWith("/api/v1/progression")) return json(progression());
      if (path.endsWith("/api/v1/stages")) return json(stagesResponse());
      return json(endedEnvelope(2, { kind: "draw", winningSideId: null }, "battle.stage.1"));
    });
    render(<BattleExperience selectedStageId="paladins-altar" countdownStepMs={0} />);
    await screen.findByRole("heading", { name: "Battle 1" });
    const user = await assignPlayers(["Warrior · Weapon Master", "Mage · Comprehensiveness"]);
    await user.click(screen.getByRole("radio", { name: /Side by Side/i }));
    await user.click(screen.getByRole("button", { name: "ENTER BATTLE" }));
    await screen.findByRole("button", { name: "RETRY BATTLE" });
    const launch = calls.find((call) => call.path.includes("/stages/paladins-altar/battles/1"));
    expect(launch?.body).toEqual({
      playerTeam: ["hero.warrior.weapon_master", "hero.mage.comprehensiveness"],
      playerFormation: "side-by-side",
    });
    expect(launch?.body).not.toHaveProperty("enemyTeam");
    expect(launch?.body).not.toHaveProperty("enemyControlMode");
  });

  it("shows player formation choices for structured 2v2 and 3v3 only", async () => {
    const stage = STRUCTURED_STAGE_DEFINITIONS.find((entry) => entry.stageId === "paladins-altar")!;
    const onStart = vi.fn();
    const builder = (battleIndex: number) => (
      <TeamBuilder
        key={stage.battles[battleIndex].id}
        mode="structured"
        roster={roster}
        availableDefinitionIds={initialUnlocked}
        stage={stage}
        battle={stage.battles[battleIndex]}
        onStart={onStart}
      />
    );
    const { rerender } = render(builder(0));
    expect(screen.getAllByRole("radio")).toHaveLength(2);

    rerender(builder(1));
    expect(screen.queryByRole("radio")).not.toBeInTheDocument();

    rerender(builder(2));
    expect(screen.getAllByRole("radio")).toHaveLength(3);
    const user = await assignPlayers([
      "Warrior · Weapon Master",
      "Mage · Comprehensiveness",
      "Priest · Comprehensiveness",
    ]);
    await user.click(screen.getByRole("radio", { name: /All Front/i }));
    await user.click(screen.getByRole("button", { name: "ENTER BATTLE" }));
    expect(onStart).toHaveBeenLastCalledWith({
      playerTeam: [
        "hero.warrior.weapon_master",
        "hero.mage.comprehensiveness",
        "hero.priest.comprehensiveness",
      ],
      playerFormation: "all-front",
    });
  });

  it("preserves a committed reward across refetch retry, announces it, then continues", async () => {
    let committed = false;
    let failFirstRefresh = true;
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const path = String(input);
      if (path.endsWith("/api/v1/heroes")) return json({ contractVersion: "1.0", heroes: roster });
      if (path.endsWith("/api/v1/progression")) {
        if (committed && failFirstRefresh) {
          failFirstRefresh = false;
          return json({ detail: { message: "Refresh failed." } }, 503);
        }
        return json(committed
          ? progression(3, 4, [...initialUnlocked, "hero.paladin.protection"])
          : progression(2, 3));
      }
      if (path.endsWith("/api/v1/stages")) {
        return json(committed ? stagesResponse(3, 4) : stagesResponse(2, 3));
      }
      if (path.includes("/api/v1/stages/paladins-altar/battles/3")) {
        return json(endedEnvelope(3, { kind: "victory", winningSideId: "friendly" }, "battle.stage.3"));
      }
      if (path.endsWith("/api/v1/battles/battle.stage.3/completion")) {
        committed = true;
        const refreshed = progression(3, 4, [...initialUnlocked, "hero.paladin.protection"]);
        return json({
          contractVersion: "1.0",
          battleId: "battle.stage.3",
          alreadyCommitted: false,
          newlyGrantedRewards: [{
            rewardId: "unlock.hero.paladin.protection",
            kind: "heroUnlock",
            heroDefinitionId: "hero.paladin.protection",
            notification: "Paladin_Protection is unlocked",
          }],
          progression: { ...refreshed, contractVersion: undefined },
        });
      }
      throw new Error(`Unexpected request ${path}`);
    });
    render(<BattleExperience selectedStageId="paladins-altar" countdownStepMs={0} />);
    expect(await screen.findByRole("heading", { name: "Battle 3" })).toBeVisible();
    const user = await assignPlayers([
      "Warrior · Weapon Master",
      "Mage · Comprehensiveness",
      "Priest · Comprehensiveness",
    ]);
    await user.click(screen.getByRole("button", { name: "ENTER BATTLE" }));
    await user.click(await screen.findByRole("button", { name: "CONTINUE TRAINING" }));
    expect(await screen.findByRole("button", { name: "RETRY SAVE" })).toBeVisible();
    await user.click(screen.getByRole("button", { name: "RETRY SAVE" }));
    const dialog = await screen.findByRole("dialog", { name: "Reward granted" });
    expect(dialog).toHaveTextContent("Paladin_Protection is unlocked");
    expect(screen.getByRole("button", { name: "CONTINUE" })).toHaveFocus();
    await user.click(screen.getByRole("button", { name: "CONTINUE" }));
    expect(await screen.findByRole("heading", { name: "Battle 4" })).toBeVisible();
    expect(screen.getByRole("button", { name: /Assign Paladin · Protection/i })).toBeVisible();
    expect(fetchMock.mock.calls.filter(([input]) => String(input).endsWith("/api/v1/progression"))).toHaveLength(3);
    expect(fetchMock.mock.calls.filter(([input]) => String(input).endsWith("/completion"))).toHaveLength(1);
  });

  it("keeps progression storage failures visible and retryable", async () => {
    let unavailable = true;
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const path = String(input);
      if (path.endsWith("/api/v1/heroes")) return json({ contractVersion: "1.0", heroes: roster });
      if (path.endsWith("/api/v1/progression") && unavailable) {
        return json({
          detail: {
            code: "progressionStoreUnavailable",
            message: "Persistent progression is unavailable or corrupt. Retry later.",
            retryable: true,
          },
        }, 503);
      }
      if (path.endsWith("/api/v1/progression")) return json(progression());
      return json(stagesResponse());
    });
    render(<BattleExperience selectedStageId="paladins-altar" />);
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/unavailable or corrupt/i);
    unavailable = false;
    await userEvent.click(screen.getByRole("button", { name: "Retry progression" }));
    await waitFor(() => expect(screen.getByRole("heading", { name: "Battle 1" })).toBeVisible());
  });

  it("keeps an ended battle open with an explicit retry when completion fails", async () => {
    const snapshot = createFormatFixture(1);
    snapshot.phase = "ended";
    snapshot.activeCombatantId = null;
    snapshot.legalActions = [];
    snapshot.outcome = { kind: "victory", winningSideId: "friendly" };
    const complete = vi.fn().mockRejectedValue(new Error("Progress could not be saved."));
    render(
      <BattleScreen
        provider={new MockBattleProvider(snapshot)}
        mode="live"
        completionActionLabel={() => "CONTINUE TRAINING"}
        onBattleComplete={complete}
      />,
    );
    await userEvent.click(await screen.findByRole("button", { name: "CONTINUE TRAINING" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Progress could not be saved.");
    await userEvent.click(screen.getByRole("button", { name: "RETRY SAVE" }));
    expect(complete).toHaveBeenCalledTimes(2);
  });
});
