import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { StageSelectionScreen } from "@/components/stages/StageSelectionScreen";
import { TeamBuilder } from "@/components/battle/TeamBuilder";
import { BattleScreen } from "@/components/battle/BattleScreen";
import { createFormatFixture, MockBattleProvider } from "@/lib/battle/fixture";
import type { BattleOutcome, HeroDefinitionSummary } from "@/lib/battle/types";
import { STAGE_DEFINITIONS } from "@/components/stages/stage-config";
import {
  STRUCTURED_STAGE_DEFINITIONS,
  missingStructuredStageRosterIds,
  resolveStructuredStage,
} from "@/components/stages/structured-stage-config";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push, replace: vi.fn() }) }));

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

afterEach(() => {
  push.mockReset();
  vi.restoreAllMocks();
});

describe("structured-stage compatibility contracts", () => {
  it("keeps only Arena and the two approved training locations interactive", async () => {
    expect(STAGE_DEFINITIONS.filter((stage) => stage.enabled).map((stage) => stage.id)).toEqual([
      "arena",
      "warriors-barrack",
      "paladins-altar",
    ]);
    expect(STAGE_DEFINITIONS.filter((stage) => !stage.enabled).map((stage) => stage.id)).toEqual([
      "mages-tower",
      "rogues-forest",
      "priests-cathedral",
    ]);
    render(<StageSelectionScreen />);
    const altar = screen.getByRole("button", { name: "Enter Paladin's Altar" });
    await userEvent.click(altar);
    fireEvent.keyDown(altar, { key: "Enter" });
    expect(push).toHaveBeenCalledWith("/game?stage=paladins-altar");
    expect(screen.getAllByRole("button")).toHaveLength(3);
  });

  it("defines two reusable, ordered nine-battle curricula", () => {
    expect(STRUCTURED_STAGE_DEFINITIONS.map((stage) => stage.stageId)).toEqual([
      "warriors-barrack",
      "paladins-altar",
    ]);
    for (const stage of STRUCTURED_STAGE_DEFINITIONS) {
      expect(stage.battles).toHaveLength(9);
      expect(stage.battles.map((battle) => battle.displayOrder)).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9]);
      expect(stage.battles.map((battle) => battle.battleSize)).toEqual([2, 1, 3, 2, 1, 3, 2, 1, 3]);
      expect(stage.battles.map((battle) => battle.playerFormation)).toEqual([
        "front-rear", null, "two-front-one-rear", "side-by-side", null,
        "two-front-one-rear",
        stage.stageId === "paladins-altar" ? "side-by-side" : "front-rear",
        null,
        "all-front",
      ]);
      expect(stage.battles.map((battle) => battle.enemyFormation)).toEqual(
        stage.battles.map((battle) => battle.playerFormation),
      );
    }
  });

  it("reports missing fixed-enemy definitions instead of substituting", () => {
    const stage = resolveStructuredStage("paladins-altar")!;
    const missing = missingStructuredStageRosterIds(stage, roster.slice(0, 4));
    expect(missing).toContain("hero.paladin.protection");
    expect(missing).toContain("hero.paladin.holy");
    expect(missing).not.toContain("hero.mage.comprehensiveness");
  });

  it("keeps fixed enemies visible while filtering the friendly matrix by authoritative IDs", () => {
    const stage = resolveStructuredStage("paladins-altar")!;
    render(
      <TeamBuilder
        mode="structured"
        stage={stage}
        battle={stage.battles[0]}
        roster={roster}
        availableDefinitionIds={[
          "hero.warrior.weapon_master",
          "hero.mage.comprehensiveness",
        ]}
        onStart={vi.fn()}
      />,
    );
    expect(document.querySelectorAll("[data-hero-id]")).toHaveLength(2);
    expect(screen.queryByRole("button", { name: /Assign Paladin · Protection/i })).not.toBeInTheDocument();
    expect(screen.getByLabelText(/Predefined enemy team/i)).toHaveTextContent(/Paladin.*Protection.*Mage.*Comprehensiveness/i);
  });

  it.each([
    [{ kind: "victory", winningSideId: "friendly" }, "CONTINUE TRAINING"],
    [{ kind: "victory", winningSideId: "enemy" }, "RETRY BATTLE"],
    [{ kind: "draw", winningSideId: null }, "RETRY BATTLE"],
    [{ kind: "roundLimit", winningSideId: null }, "RETRY BATTLE"],
  ] satisfies Array<[BattleOutcome, string]>) (
    "forwards authoritative $kind completion without interpreting the result",
    async (outcome, label) => {
      const snapshot = createFormatFixture(1);
      snapshot.phase = "ended";
      snapshot.activeCombatantId = null;
      snapshot.legalActions = [];
      snapshot.outcome = outcome;
      const onComplete = vi.fn();
      render(
        <BattleScreen
          provider={new MockBattleProvider(snapshot)}
          mode="live"
          onBattleComplete={onComplete}
          completionActionLabel={() => label}
        />,
      );
      await userEvent.click(await screen.findByRole("button", { name: label }));
      expect(onComplete).toHaveBeenCalledWith(outcome);
    },
  );
});
