import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { BattleExperience } from "@/components/battle/BattleExperience";
import {
  BATTLE_BACKGROUNDS,
  pickRandomBattleBackground,
} from "@/lib/battle/battleBackgrounds";
import { createFormatFixture } from "@/lib/battle/fixture";

const roster = [
  ["hero.priest.comprehensiveness", "Aurelia", "Priest", "Comprehensiveness"],
  ["hero.priest.discipline", "Seraphine", "Priest", "Discipline"],
  ["hero.paladin.retribution", "Valerius", "Paladin", "Retribution"],
  ["hero.paladin.protection", "Bastion", "Paladin", "Protection"],
  ["hero.mage.comprehensiveness", "Lyra", "Mage", "Comprehensiveness"],
  ["hero.warrior.defence", "Aegis", "Warrior", "Defence"],
  ["hero.warrior.weapon_master", "Ragnar", "Warrior", "Weapon Master"],
  ["hero.rogue.comprehensiveness", "Nighthawk", "Rogue", "Comprehensiveness"],
].map(([definitionId, displayName, faculty, specialization]) => ({
  definitionId,
  displayName,
  faculty,
  specialization,
}));

function endedEnvelope(battleId: string) {
  const snapshot = createFormatFixture(1);
  snapshot.phase = "ended";
  snapshot.activeCombatantId = null;
  snapshot.legalActions = [];
  snapshot.outcome = { kind: "victory", winningSideId: "friendly" };
  return {
    contractVersion: "1.0",
    battleId,
    revision: 1,
    data: { events: [], snapshot },
  };
}

describe("random battle backgrounds", () => {
  it.each([
    [0, BATTLE_BACKGROUNDS[0]],
    [1 / 3 - Number.EPSILON, BATTLE_BACKGROUNDS[0]],
    [1 / 3, BATTLE_BACKGROUNDS[1]],
    [2 / 3 - Number.EPSILON, BATTLE_BACKGROUNDS[1]],
    [2 / 3, BATTLE_BACKGROUNDS[2]],
    [0.999999, BATTLE_BACKGROUNDS[2]],
  ])("maps random value %s to a registered background", (value, expected) => {
    expect(pickRandomBattleBackground(() => value)).toBe(expected);
    expect(BATTLE_BACKGROUNDS).toContain(expected);
  });

  it("keeps one background through rerenders and selects again for a new battle", async () => {
    const user = userEvent.setup();
    const random = vi.spyOn(Math, "random")
      .mockReturnValueOnce(0)
      .mockReturnValueOnce(0.999999);
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify({
        contractVersion: "1.0",
        heroes: roster,
      }), { status: 200, headers: { "Content-Type": "application/json" } }))
      .mockResolvedValueOnce(new Response(JSON.stringify(endedEnvelope("battle.background.1")), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }))
      .mockResolvedValueOnce(new Response(JSON.stringify(endedEnvelope("battle.background.2")), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }));

    render(<BattleExperience />);
    await user.click(await screen.findByRole("button", { name: "ENTER BATTLE" }));

    const firstBattlefield = await screen.findByRole("region", { name: "Battlefield" });
    expect(firstBattlefield).toHaveAttribute("data-background", BATTLE_BACKGROUNDS[0]);
    expect(firstBattlefield.style.getPropertyValue("--battle-background-image"))
      .toBe(`url("${BATTLE_BACKGROUNDS[0]}")`);
    expect(random).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole("button", { name: "×2" }));
    expect(screen.getByRole("region", { name: "Battlefield" }))
      .toHaveAttribute("data-background", BATTLE_BACKGROUNDS[0]);
    expect(random).toHaveBeenCalledTimes(1);

    await user.click(await screen.findByRole("button", { name: "RETURN TO TEAM BUILDER" }));
    await user.click(await screen.findByRole("button", { name: "ENTER BATTLE" }));

    expect(await screen.findByRole("region", { name: "Battlefield" }))
      .toHaveAttribute("data-background", BATTLE_BACKGROUNDS[2]);
    expect(random).toHaveBeenCalledTimes(2);

    fetchMock.mockRestore();
    random.mockRestore();
  });
});
