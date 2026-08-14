import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { readFileSync } from "node:fs";
import { afterEach, describe, expect, it, vi } from "vitest";
import { BattleScreen } from "@/components/battle/BattleScreen";
import { TeamBuilder } from "@/components/battle/TeamBuilder";
import { resolveStructuredStage } from "@/components/stages/structured-stage-config";
import { createFormatFixture, MockBattleProvider } from "@/lib/battle/fixture";
import { duoFormationFor, duoFormationRegistry, formationFor } from "@/lib/battle/formations";
import { LiveBattleProvider } from "@/lib/battle/liveProvider";
import type { BattleCreateConfiguration, HeroDefinitionSummary } from "@/lib/battle/types";

const roster: HeroDefinitionSummary[] = [
  ["hero.warrior.weapon_master", "Garran", "Warrior", "Weapon Master"],
  ["hero.mage.comprehensiveness", "Elyra", "Mage", "Comprehensiveness"],
  ["hero.priest.comprehensiveness", "Aldric", "Priest", "Comprehensiveness"],
  ["hero.rogue.comprehensiveness", "Hessa", "Rogue", "Comprehensiveness"],
  ["hero.warrior.defence", "Falk", "Warrior", "Defence"],
  ["hero.warrior.berserker", "Rogan", "Warrior", "Berserker"],
].map(([definitionId, displayName, faculty, specialization]) => ({ definitionId, displayName, faculty, specialization }));

afterEach(() => vi.restoreAllMocks());

async function assignTwoPlayers(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole("button", { name: /Assign Warrior · Weapon Master to your Hero 1/i }));
  await user.click(screen.getByRole("button", { name: /Select your Hero 2/i }));
  await user.click(screen.getByRole("button", { name: /Assign Mage · Comprehensiveness to your Hero 2/i }));
}

describe("UI-018 Team Builder formation contract", () => {
  it("shows keyboard-native formation choices only for 2v2 and explains computer authority", async () => {
    const user = userEvent.setup();
    render(<TeamBuilder roster={roster} onStart={vi.fn()} />);
    expect(screen.queryByRole("group", { name: "Your formation" })).not.toBeInTheDocument();

    await user.click(screen.getByRole("radio", { name: "2v2" }));
    const friendly = screen.getByRole("group", { name: "Your formation" });
    expect(within(friendly).getByRole("radio", { name: /Front and Rear.*Hero 1 Front.*Hero 2 Rear/i })).toBeChecked();
    expect(within(friendly).getByRole("radio", { name: /Side by Side.*Hero 1 Front.*Hero 2 Front/i })).toBeEnabled();
    expect(screen.getByRole("note")).toHaveTextContent("The computer will choose Front and Rear or Side by Side");
    expect(screen.queryByRole("group", { name: "Enemy formation" })).not.toBeInTheDocument();

    await user.click(screen.getByRole("radio", { name: "3v3" }));
    expect(screen.queryByRole("group", { name: /formation/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("note")).not.toBeInTheDocument();
  });

  it("submits friendly 2v2 formation while omitting the computer-selected enemy formation", async () => {
    const user = userEvent.setup();
    const onStart = vi.fn();
    render(<TeamBuilder roster={roster} onStart={onStart} />);
    await user.click(screen.getByRole("radio", { name: "2v2" }));
    await user.click(within(screen.getByRole("group", { name: "Your formation" })).getByRole("radio", { name: /Side by Side/i }));
    await assignTwoPlayers(user);
    await user.click(screen.getByRole("button", { name: "ENTER BATTLE" }));

    expect(onStart).toHaveBeenCalledWith({
      battleSize: 2,
      playerTeam: ["hero.warrior.weapon_master", "hero.mage.comprehensiveness"],
      playerFormation: "side-by-side",
      enemyCompositionMode: "random",
      enemyControlMode: "computer",
    });
    expect(onStart.mock.calls[0][0]).not.toHaveProperty("enemyFormation");
  });

  it("allows a player-controlled enemy formation and sends both stable IDs", async () => {
    const user = userEvent.setup();
    const onStart = vi.fn();
    render(<TeamBuilder roster={roster} onStart={onStart} />);
    await user.click(screen.getByRole("radio", { name: "2v2" }));
    await user.click(screen.getByRole("radio", { name: "Player" }));
    const enemy = screen.getByRole("group", { name: "Enemy formation" });
    const frontRear = within(enemy).getByRole("radio", { name: /Front and Rear/i });
    const sideBySide = within(enemy).getByRole("radio", { name: /Side by Side/i });
    frontRear.focus();
    await user.keyboard("{ArrowRight}");
    expect(sideBySide).toHaveFocus();
    expect(sideBySide).toBeChecked();
    await assignTwoPlayers(user);
    await user.click(screen.getByRole("button", { name: "ENTER BATTLE" }));

    expect(onStart).toHaveBeenCalledWith(expect.objectContaining({
      battleSize: 2,
      playerFormation: "front-rear",
      enemyControlMode: "player",
      enemyFormation: "side-by-side",
    }));
  });

  it("keeps structured Barrack Battle 1 enemy composition immutable and computer formation omitted", async () => {
    const user = userEvent.setup();
    const onStart = vi.fn();
    const stage = resolveStructuredStage("warriors-barrack")!;
    render(<TeamBuilder mode="structured" stage={stage} battle={stage.battles[0]} roster={roster} onStart={onStart} />);
    expect(screen.getByRole("group", { name: "Your formation" })).toBeVisible();
    expect(screen.getByRole("note")).toHaveTextContent(/computer will choose/i);
    expect(screen.queryByRole("group", { name: "Enemy formation" })).not.toBeInTheDocument();
    expect(screen.getByLabelText(/Predefined enemy team/i)).toBeVisible();
    await user.click(within(screen.getByRole("group", { name: "Your formation" })).getByRole("radio", { name: /Side by Side/i }));
    await assignTwoPlayers(user);
    await user.click(screen.getByRole("button", { name: "ENTER BATTLE" }));

    expect(onStart).toHaveBeenCalledWith({
      battleSize: 2,
      playerTeam: ["hero.warrior.weapon_master", "hero.mage.comprehensiveness"],
      playerFormation: "side-by-side",
      enemyCompositionMode: "specified",
      enemyTeam: ["hero.warrior.defence", "hero.priest.comprehensiveness"],
      enemyControlMode: "computer",
    });
    expect(onStart.mock.calls[0][0]).not.toHaveProperty("enemyFormation");
  });

  it("passes the typed 2v2 payload unchanged through the live provider", async () => {
    const snapshot = createFormatFixture(2);
    snapshot.formations = { friendly: "front-rear", enemy: "side-by-side" };
    const configuration = {
      battleSize: 2,
      playerTeam: ["hero.warrior.weapon_master", "hero.mage.comprehensiveness"],
      playerFormation: "front-rear",
      enemyCompositionMode: "specified",
      enemyTeam: ["hero.warrior.defence", "hero.priest.comprehensiveness"],
      enemyControlMode: "player",
      enemyFormation: "side-by-side",
    } satisfies BattleCreateConfiguration;
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(new Response(JSON.stringify({
      contractVersion: "1.0", battleId: "battle.ui-018", revision: 0, data: { events: [], snapshot },
    }), { status: 200, headers: { "Content-Type": "application/json" } }));

    const state = await new LiveBattleProvider("http://adapter.test", configuration).getState();
    expect(fetchMock).toHaveBeenCalledWith("http://adapter.test/api/v1/battles", expect.objectContaining({
      method: "POST",
      body: JSON.stringify(configuration),
    }));
    expect(state.snapshot.formations).toEqual({ friendly: "front-rear", enemy: "side-by-side" });
  });
});

describe("UI-018 authoritative duo placement and targeting", () => {
  it("keeps the adapter-authored formation keys present for every battle size", () => {
    expect(createFormatFixture(1).formations).toEqual({ friendly: null, enemy: null });
    expect(createFormatFixture(2).formations).toEqual({ friendly: "front-rear", enemy: "front-rear" });
    expect(createFormatFixture(3).formations).toEqual({ friendly: null, enemy: null });
  });

  it("maps independent friendly and enemy snapshot positions to the approved percentage pairs", () => {
    const snapshot = createFormatFixture(2);
    snapshot.combatants["friendly.ragnar"].position = "front";
    snapshot.combatants["friendly.black_heart"].position = "rear";
    snapshot.combatants["enemy.nighthawk"].position = "front";
    snapshot.combatants["enemy.andonidas"].position = "front";

    expect(duoFormationFor(snapshot, "friendly")).toBe("front-rear");
    expect(duoFormationFor(snapshot, "enemy")).toBe("side-by-side");
    expect(snapshot.sides.flatMap((side) => side.combatantIds.map((id) => {
      const combatant = snapshot.combatants[id];
      return formationFor(snapshot, side.id, combatant.slot, combatant.position);
    }))).toEqual([
      ...duoFormationRegistry["front-rear"].friendly,
      ...duoFormationRegistry["side-by-side"].enemy,
    ]);
  });

  it("renders coordinates and depth labels from snapshot position plus ordered slot", async () => {
    const snapshot = createFormatFixture(2);
    snapshot.combatants["friendly.ragnar"].position = "front";
    snapshot.combatants["friendly.black_heart"].position = "front";
    snapshot.combatants["enemy.nighthawk"].position = "front";
    snapshot.combatants["enemy.andonidas"].position = "rear";
    render(<BattleScreen provider={new MockBattleProvider(snapshot)} />);
    await screen.findByRole("region", { name: "Battlefield" });

    const assertPlacement = (id: string, x: number, y: number, position: "front" | "rear") => {
      const slot = document.querySelector(`[data-combatant-id='${id}']`)?.closest<HTMLElement>(".formation-slot");
      expect(slot).toHaveStyle({ left: `${x}%`, top: `${y}%` });
      expect(slot).toHaveAttribute("data-position", position);
      expect(slot).toHaveAttribute("data-slot", position);
    };
    assertPlacement("friendly.ragnar", 33, 54, "front");
    assertPlacement("friendly.black_heart", 33, 85, "front");
    assertPlacement("enemy.nighthawk", 59, 68, "front");
    assertPlacement("enemy.andonidas", 78, 68, "rear");
  });

  it("uses only adapter validTargetIds even when the sole valid target is rear", async () => {
    const user = userEvent.setup();
    const snapshot = createFormatFixture(2);
    snapshot.combatants["enemy.nighthawk"].position = "front";
    snapshot.combatants["enemy.andonidas"].position = "rear";
    snapshot.legalActions = snapshot.legalActions.map((action) => action.skillId === "skill.warrior.fatal_strike"
      ? { ...action, validTargetIds: ["enemy.andonidas"] }
      : action);
    render(<BattleScreen provider={new MockBattleProvider(snapshot)} />);
    await screen.findByRole("region", { name: "Battlefield" });
    await user.click(screen.getByRole("button", { name: /Fatal Strike/i }));

    expect(screen.getByRole("button", { name: "Andonidas, selectable target" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Nighthawk" })).toBeDisabled();
    expect(screen.queryByRole("button", { name: "Nighthawk, selectable target" })).not.toBeInTheDocument();
  });

  it("keeps formation controls responsive without introducing placement markers", () => {
    const css = readFileSync("app/globals.css", "utf8").replace(/\s+/g, "");
    expect(css).toMatch(/@media\(max-width:720px\)[\s\S]*\.formation-choices\{grid-template-columns:1fr\}/);
    expect(css).toMatch(/\.formation-choices\{[^}]*grid-template-columns:repeat\(2,minmax\(0,1fr\)\)/);
    expect(css).not.toMatch(/\.formation-(?:selector|choices)[^{]*::(?:before|after)\{[^}]*content:["']?[1-4]/);
  });
});
