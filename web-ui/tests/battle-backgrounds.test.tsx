import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { BattleExperience } from "@/components/battle/BattleExperience";
import { BATTLE_BACKGROUND } from "@/lib/battle/battleBackgrounds";
import { createFormatFixture } from "@/lib/battle/fixture";

const roster = [
  ["hero.priest.comprehensiveness", "Aurelia", "Priest", "Comprehensiveness"],
  ["hero.priest.discipline", "Seraphine", "Priest", "Discipline"],
  ["hero.paladin.retribution", "Valerius", "Paladin", "Retribution"],
  ["hero.paladin.protection", "Bastion", "Paladin", "Protection"],
  ["hero.paladin.holy", "Galahad", "Paladin", "Holy"],
  ["hero.mage.comprehensiveness", "Lyra", "Mage", "Comprehensiveness"],
  ["hero.warrior.defence", "Aegis", "Warrior", "Defence"],
  ["hero.warrior.weapon_master", "Ragnar", "Warrior", "Weapon Master"],
  ["hero.warrior.berserker", "Wrathe", "Warrior", "Berserker"],
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

describe("fixed battle background", () => {
  it("uses BG03 through rerenders and each new battle", async () => {
    const user = userEvent.setup();
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

    render(<BattleExperience countdownStepMs={0} />);
    await user.click(await screen.findByRole("button", { name: "ENTER BATTLE" }));

    const firstBattlefield = await screen.findByRole("region", { name: "Battlefield" });
    expect(BATTLE_BACKGROUND).toBe("/game-images/battle-scenes/backgrounds/Battle_Scene_BG03.png");
    expect(firstBattlefield).toHaveAttribute("data-background", BATTLE_BACKGROUND);
    expect(firstBattlefield.style.getPropertyValue("--battle-background-image"))
      .toBe(`url("${BATTLE_BACKGROUND}")`);

    fireEvent.click(screen.getByRole("button", { name: "×2" }));
    expect(screen.getByRole("region", { name: "Battlefield" }))
      .toHaveAttribute("data-background", BATTLE_BACKGROUND);

    await user.click(await screen.findByRole("button", { name: "RETURN TO TEAM BUILDER" }));
    await user.click(await screen.findByRole("button", { name: "ENTER BATTLE" }));

    expect(await screen.findByRole("region", { name: "Battlefield" }))
      .toHaveAttribute("data-background", BATTLE_BACKGROUND);

    fetchMock.mockRestore();
  });

  it("renders 3, 2, 1, and START over the composed live scene", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify({ contractVersion: "1.0", heroes: roster }), { status: 200, headers: { "Content-Type": "application/json" } }))
      .mockResolvedValueOnce(new Response(JSON.stringify(endedEnvelope("battle.countdown.1")), { status: 200, headers: { "Content-Type": "application/json" } }));

    render(<BattleExperience countdownStepMs={20} />);
    await user.click(await screen.findByRole("button", { name: "ENTER BATTLE" }));

    expect(await screen.findByRole("status", { name: "Battle begins in 3" })).toHaveTextContent("3");
    expect(screen.getByRole("region", { name: "Battlefield" })).toBeVisible();
    expect(await screen.findByRole("status", { name: "Battle start" })).toHaveTextContent("START");

    await screen.findByRole("dialog", { name: "YOUR TEAM VICTORIOUS" });
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    fetchMock.mockRestore();
  });
});
