import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { TeamBuilder } from "@/components/battle/TeamBuilder";
import { STRUCTURED_STAGE_DEFINITIONS } from "@/components/stages/structured-stage-config";
import { fetchStructuredStages } from "@/lib/battle/liveProvider";
import type { HeroDefinitionSummary, StructuredBattleMode } from "@/lib/battle/types";

const roster: HeroDefinitionSummary[] = [
  { definitionId: "hero.warrior.weapon_master", displayName: "Garran", faculty: "Warrior", specialization: "Weapon Master" },
  { definitionId: "hero.mage.comprehensiveness", displayName: "Elyra", faculty: "Mage", specialization: "Comprehensiveness" },
];

const stage = STRUCTURED_STAGE_DEFINITIONS[0];
const learnerOnly = {
  learner: { available: true, completed: false, completedBattleIndices: [] },
  tactics: { available: false, completed: false, completedBattleIndices: [] },
};
const tacticsUnlocked = {
  learner: { available: true, completed: true, completedBattleIndices: [1, 2, 3, 4, 5, 6, 7, 8, 9] },
  tactics: { available: true, completed: false, completedBattleIndices: [] },
};

function structuredProps(
  modeProgress = learnerOnly,
  battleMode: StructuredBattleMode = "learner",
  onStart = vi.fn(),
) {
  return {
    mode: "structured" as const,
    roster,
    availableDefinitionIds: roster.map((hero) => hero.definitionId),
    stage,
    battle: stage.battles[0],
    highestCompletedBattle: modeProgress.learner.completedBattleIndices.length,
    highestUnlockedBattle: modeProgress.learner.completedBattleIndices.length + 1,
    battleMode,
    modeProgress,
    onBattleModeChange: vi.fn(),
    onSelectBattle: vi.fn(),
    onStart,
  };
}

afterEach(() => vi.restoreAllMocks());

describe("MODE-001 structured mode boundary", () => {
  it("decodes a dynamic contiguous curriculum and rejects out-of-range mode completion", async () => {
    const modeProgress = {
      learner: { available: true, completed: false, completedBattleIndices: [1] },
      tactics: { available: false, completed: false, completedBattleIndices: [] },
    };
    const dynamicStage = {
      stageId: "warriors-barrack",
      displayName: "Warrior's Barrack",
      progress: {
        stageId: "warriors-barrack",
        highestCompletedBattle: 1,
        unlockedBattle: 2,
        completed: false,
        modes: modeProgress,
      },
      modes: modeProgress,
      battles: stage.battles.slice(0, 2).map((battle, index) => ({
        id: battle.id,
        displayOrder: index + 1,
        battleSize: battle.battleSize,
        formation: battle.playerFormation,
        enemyDefinitionIds: [...battle.enemyDefinitionIds],
        reward: null,
        unlocked: true,
        completed: index === 0,
      })),
    };
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(new Response(JSON.stringify({
      contractVersion: "1.0",
      stages: [dynamicStage],
    }), { status: 200, headers: { "Content-Type": "application/json" } }));
    await expect(fetchStructuredStages("http://adapter.test")).resolves.toMatchObject({
      stages: [{ battles: [{ displayOrder: 1 }, { displayOrder: 2 }] }],
    });

    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(new Response(JSON.stringify({
      contractVersion: "1.0",
      stages: [{
        ...dynamicStage,
        modes: {
          ...modeProgress,
          tactics: { available: true, completed: false, completedBattleIndices: [3] },
        },
      }],
    }), { status: 200, headers: { "Content-Type": "application/json" } }));
    await expect(fetchStructuredStages("http://adapter.test")).rejects.toThrow(
      "unsupported structured-stage data",
    );

    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(new Response(JSON.stringify({
      contractVersion: "1.0",
      stages: [{
        ...dynamicStage,
        battles: dynamicStage.battles.map((battle, index) => index === 1
          ? { ...battle, displayOrder: 3 }
          : battle),
      }],
    }), { status: 200, headers: { "Content-Type": "application/json" } }));
    await expect(fetchStructuredStages("http://adapter.test")).rejects.toThrow(
      "unsupported structured-stage data",
    );
  });

  it("defaults to Learner, locks Tactics, and exposes accessible mode controls", () => {
    render(<TeamBuilder {...structuredProps()} />);

    const group = screen.getByRole("group", { name: "Training mode" });
    expect(within(group).getByRole("radio", { name: "Learner" })).toBeChecked();
    expect(within(group).getByRole("radio", { name: /Tactics.*Locked/i })).toBeDisabled();
  });

  it("allows an unlocked Tactics mode and keeps every battle selectable", async () => {
    const onSelectBattle = vi.fn();
    const user = userEvent.setup();
    render(<TeamBuilder {...structuredProps(tacticsUnlocked, "tactics")} onSelectBattle={onSelectBattle} />);

    const group = screen.getByRole("group", { name: "Training mode" });
    expect(within(group).getByRole("radio", { name: "Tactics" })).toBeChecked();
    const battleButtons = screen.getAllByRole("button", { name: /Battle \d+/i });
    expect(battleButtons.length).toBe(stage.battles.length);
    await user.click(battleButtons.at(-1)!);
    expect(onSelectBattle).toHaveBeenCalledWith(stage.battles.length - 1);
  });

  it("sends the selected mode in the structured launch payload", async () => {
    const onStart = vi.fn();
    const user = userEvent.setup();
    render(<TeamBuilder {...structuredProps(tacticsUnlocked, "tactics", onStart)} />);

    await user.click(screen.getByRole("button", { name: /Select your Hero 1/i }));
    await user.click(screen.getByRole("button", { name: /Assign Warrior · Weapon Master to your Hero 1/i }));
    await user.click(screen.getByRole("button", { name: /Select your Hero 2/i }));
    await user.click(screen.getByRole("button", { name: /Assign Mage · Comprehensiveness to your Hero 2/i }));
    await user.click(screen.getByRole("button", { name: "ENTER BATTLE" }));

    expect(onStart).toHaveBeenCalledWith(expect.objectContaining({ mode: "tactics" }));
  });

  it("does not render a structured mode selector for Arena or Debug", () => {
    const onStart = vi.fn();
    const { unmount } = render(<TeamBuilder mode="arena" roster={roster} onStart={onStart} />);
    expect(screen.queryByRole("group", { name: "Training mode" })).not.toBeInTheDocument();
    unmount();
    render(<TeamBuilder mode="debug" roster={roster} onStart={onStart} />);
    expect(screen.queryByRole("group", { name: "Training mode" })).not.toBeInTheDocument();
  });
});
