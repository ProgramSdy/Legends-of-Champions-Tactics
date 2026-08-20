import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { readFileSync } from "node:fs";
import { afterEach, describe, expect, it, vi } from "vitest";
import { BattleScreen } from "@/components/battle/BattleScreen";
import { TeamBuilder } from "@/components/battle/TeamBuilder";
import { resolveStructuredStage } from "@/components/stages/structured-stage-config";
import { createFormatFixture, MockBattleProvider } from "@/lib/battle/fixture";
import { duoFormationRegistry, formationFor, formationRegistry, trioFormationFor, trioFormationRegistry } from "@/lib/battle/formations";
import { LiveBattleProvider } from "@/lib/battle/liveProvider";
import type { BattleCreateConfiguration, CombatantPosition, HeroDefinitionSummary, TrioFormationId } from "@/lib/battle/types";

const roster: HeroDefinitionSummary[] = [
  ["hero.warrior.weapon_master", "Garran", "Warrior", "Weapon Master"],
  ["hero.mage.comprehensiveness", "Elyra", "Mage", "Comprehensiveness"],
  ["hero.priest.comprehensiveness", "Aldric", "Priest", "Comprehensiveness"],
  ["hero.rogue.comprehensiveness", "Hessa", "Rogue", "Comprehensiveness"],
  ["hero.warrior.defence", "Falk", "Warrior", "Defence"],
  ["hero.warrior.berserker", "Rogan", "Warrior", "Berserker"],
].map(([definitionId, displayName, faculty, specialization]) => ({ definitionId, displayName, faculty, specialization }));

const trioPositions: Record<TrioFormationId, CombatantPosition[]> = {
  "one-front-two-rear": ["front", "rear", "rear"],
  "two-front-one-rear": ["front", "front", "rear"],
  "all-front": ["front", "front", "front"],
};

afterEach(() => vi.restoreAllMocks());

async function assignThreePlayers(user: ReturnType<typeof userEvent.setup>) {
  for (const [index, label] of [
    [1, "Warrior · Weapon Master"],
    [2, "Mage · Comprehensiveness"],
    [3, "Priest · Comprehensiveness"],
  ] as const) {
    await user.click(screen.getByRole("button", { name: new RegExp(`Select your Hero ${index}`, "i") }));
    await user.click(screen.getByRole("button", { name: new RegExp(`Assign ${label} to your Hero ${index}`, "i") }));
  }
}

function applyFormationPositions(snapshot: ReturnType<typeof createFormatFixture>, side: "friendly" | "enemy", formation: TrioFormationId) {
  const ids = snapshot.sides.find((candidate) => candidate.id === side)!.combatantIds;
  ids.forEach((id, slot) => {
    snapshot.combatants[id].position = trioPositions[formation][slot];
  });
}

describe("UI-019 size-specific Team Builder formation contract", () => {
  it("shows exactly the three accessible 3v3 choices and keeps 2v2 choices separate", async () => {
    const user = userEvent.setup();
    render(<TeamBuilder roster={roster} onStart={vi.fn()} />);
    expect(screen.queryByRole("group", { name: "Your formation" })).not.toBeInTheDocument();

    await user.click(screen.getByRole("radio", { name: "3v3" }));
    const friendly = screen.getByRole("group", { name: "Your formation" });
    const choices = within(friendly).getAllByRole("radio");
    expect(choices).toHaveLength(3);
    expect(choices.map((choice) => (choice as HTMLInputElement).value)).toEqual([
      "one-front-two-rear", "two-front-one-rear", "all-front",
    ]);
    expect(within(friendly).getByRole("radio", { name: /One Front, Two Rear.*Hero 1 Front.*Hero 2 Rear.*Hero 3 Rear/i })).toBeChecked();
    expect(within(friendly).getByRole("radio", { name: /Two Front, One Rear.*Hero 1 Front.*Hero 2 Front.*Hero 3 Rear/i })).toBeEnabled();
    expect(within(friendly).getByRole("radio", { name: /All Front.*Hero 1 Front.*Hero 2 Front.*Hero 3 Front/i })).toBeEnabled();
    expect(within(friendly).queryByRole("radio", { name: /Side by Side/i })).not.toBeInTheDocument();
    expect(screen.getByRole("note")).toHaveTextContent(/choose one of three formations/i);

    await user.click(screen.getByRole("radio", { name: "Player" }));
    const enemy = screen.getByRole("group", { name: "Enemy formation" });
    const first = within(enemy).getByRole("radio", { name: /One Front, Two Rear/i });
    const second = within(enemy).getByRole("radio", { name: /Two Front, One Rear/i });
    first.focus();
    await user.keyboard("{ArrowRight}");
    expect(second).toHaveFocus();
    expect(second).toBeChecked();

    await user.click(screen.getByRole("radio", { name: "2v2" }));
    expect(within(screen.getByRole("group", { name: "Your formation" })).getAllByRole("radio")).toHaveLength(2);
    expect(within(screen.getByRole("group", { name: "Your formation" })).queryByRole("radio", { name: /All Front/i })).not.toBeInTheDocument();
  });

  it("submits a friendly 3v3 choice and omits the computer-owned enemy formation", async () => {
    const user = userEvent.setup();
    const onStart = vi.fn();
    render(<TeamBuilder roster={roster} onStart={onStart} />);
    await user.click(screen.getByRole("radio", { name: "3v3" }));
    await user.click(within(screen.getByRole("group", { name: "Your formation" })).getByRole("radio", { name: /All Front/i }));
    await assignThreePlayers(user);
    await user.click(screen.getByRole("button", { name: "ENTER BATTLE" }));

    expect(onStart).toHaveBeenCalledWith({
      battleSize: 3,
      playerTeam: ["hero.warrior.weapon_master", "hero.mage.comprehensiveness", "hero.priest.comprehensiveness"],
      playerFormation: "all-front",
      enemyCompositionMode: "random",
      enemyControlMode: "computer",
    });
    expect(onStart.mock.calls[0][0]).not.toHaveProperty("enemyFormation");
  });

  it("submits independently selected friendly and player-controlled enemy 3v3 formations", async () => {
    const user = userEvent.setup();
    const onStart = vi.fn();
    render(<TeamBuilder roster={roster} onStart={onStart} />);
    await user.click(screen.getByRole("radio", { name: "3v3" }));
    await user.click(within(screen.getByRole("group", { name: "Your formation" })).getByRole("radio", { name: /Two Front, One Rear/i }));
    await user.click(screen.getByRole("radio", { name: "Player" }));
    await user.click(within(screen.getByRole("group", { name: "Enemy formation" })).getByRole("radio", { name: /All Front/i }));
    await assignThreePlayers(user);
    await user.click(screen.getByRole("button", { name: "ENTER BATTLE" }));

    expect(onStart).toHaveBeenCalledWith(expect.objectContaining({
      battleSize: 3,
      playerFormation: "two-front-one-rear",
      enemyControlMode: "player",
      enemyFormation: "all-front",
    }));
  });

  it("hides formation selection for structured duels and sends the player's 3v3 choice", async () => {
    const stage = resolveStructuredStage("warriors-barrack")!;
    const battleTwo = render(<TeamBuilder mode="structured" stage={stage} battle={stage.battles[1]} roster={roster} onStart={vi.fn()} />);
    expect(screen.queryByRole("group", { name: /formation/i })).not.toBeInTheDocument();
    expect(screen.getByRole("note")).toHaveTextContent(/duel uses no formation selection/i);
    battleTwo.unmount();

    const user = userEvent.setup();
    const onStart = vi.fn();
    render(<TeamBuilder mode="structured" stage={stage} battle={stage.battles[2]} roster={roster} onStart={onStart} />);
    expect(screen.getByRole("group", { name: "Your formation" })).toBeVisible();
    expect(screen.getByRole("note")).toHaveTextContent(/enemy uses two front one rear/i);
    expect(screen.getByLabelText(/Predefined enemy team/i)).toHaveTextContent(/Warrior.*Berserker.*Rogue.*Comprehensiveness.*Mage.*Comprehensiveness/i);
    await assignThreePlayers(user);
    await user.click(screen.getByRole("radio", { name: /All Front/i }));
    await user.click(screen.getByRole("button", { name: "ENTER BATTLE" }));

    expect(onStart).toHaveBeenCalledWith({
      playerFormation: "all-front",
      playerTeam: ["hero.warrior.weapon_master", "hero.mage.comprehensiveness", "hero.priest.comprehensiveness"],
    });
  });

  it("passes the typed 3v3 payload and returned formations through the live provider unchanged", async () => {
    const snapshot = createFormatFixture(3);
    snapshot.formations = { friendly: "two-front-one-rear", enemy: "all-front" };
    const configuration = {
      battleSize: 3,
      playerTeam: ["hero.warrior.weapon_master", "hero.mage.comprehensiveness", "hero.priest.comprehensiveness"],
      playerFormation: "two-front-one-rear",
      enemyCompositionMode: "random",
      enemyControlMode: "player",
      enemyFormation: "all-front",
    } satisfies BattleCreateConfiguration;
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(new Response(JSON.stringify({
      contractVersion: "1.0", battleId: "battle.ui-019", revision: 0, data: { events: [], snapshot },
    }), { status: 200, headers: { "Content-Type": "application/json" } }));

    const state = await new LiveBattleProvider("http://adapter.test", configuration).getState();
    expect(fetchMock).toHaveBeenCalledWith("http://adapter.test/api/v1/battles", expect.objectContaining({
      method: "POST",
      body: JSON.stringify(configuration),
    }));
    expect(state.snapshot.formations).toEqual({ friendly: "two-front-one-rear", enemy: "all-front" });
  });
});

describe("UI-019 authoritative trio presentation", () => {
  it.each(Object.keys(trioPositions) as TrioFormationId[])("maps %s by snapshot formation, ordered slot, and supplied position", (formation) => {
    const snapshot = createFormatFixture(3);
    snapshot.formations = { friendly: formation, enemy: formation };
    applyFormationPositions(snapshot, "friendly", formation);
    applyFormationPositions(snapshot, "enemy", formation);
    expect(trioFormationFor(snapshot, "friendly")).toBe(formation);
    expect(snapshot.sides.flatMap((side) => side.combatantIds.map((id) => {
      const combatant = snapshot.combatants[id];
      return formationFor(snapshot, side.id, combatant.slot, combatant.position);
    }))).toEqual([
      ...trioFormationRegistry[formation].friendly,
      ...trioFormationRegistry[formation].enemy,
    ]);
  });

  it.each([
    ["one-front-two-rear", "friendly", [1, 0, 2]],
    ["one-front-two-rear", "enemy", [2, 0, 1]],
    ["two-front-one-rear", "friendly", [1, 2, 0]],
    ["two-front-one-rear", "enemy", [0, 2, 1]],
    ["all-front", "friendly", [2, 1, 0]],
    ["all-front", "enemy", [0, 1, 2]],
  ] as const)("uses the owner-approved nearest-to-furthest scale and layer order for %s %s", (formation, side, nearestToFurthest) => {
    const positions = trioFormationRegistry[formation][side];
    const [nearest, middle, furthest] = nearestToFurthest.map((slot) => positions[slot]);
    expect(nearest.scale).toBeGreaterThan(middle.scale);
    expect(middle.scale).toBeGreaterThan(furthest.scale);
    expect(nearest.depth).toBeGreaterThan(middle.depth!);
    expect(middle.depth).toBeGreaterThan(furthest.depth!);
  });

  it("assigns documented safe overhead lanes to every crowded formation", () => {
    expect(duoFormationRegistry["side-by-side"].friendly.map(({ panelOffsetX = 0 }) => panelOffsetX)).toEqual([0, -105]);
    expect(duoFormationRegistry["side-by-side"].enemy.map(({ panelOffsetX = 0 }) => panelOffsetX)).toEqual([0, 105]);
    expect(trioFormationRegistry["one-front-two-rear"].friendly.map(({ panelOffsetX = 0 }) => panelOffsetX)).toEqual([0, -105, -105]);
    expect(trioFormationRegistry["one-front-two-rear"].enemy.map(({ panelOffsetX = 0 }) => panelOffsetX)).toEqual([0, 105, 105]);
    expect(trioFormationRegistry["two-front-one-rear"].friendly.map(({ panelOffsetX = 0 }) => panelOffsetX)).toEqual([0, 105, -105]);
    expect(trioFormationRegistry["two-front-one-rear"].enemy.map(({ panelOffsetX = 0 }) => panelOffsetX)).toEqual([-105, 0, 105]);
    expect(trioFormationRegistry["all-front"].friendly.map(({ panelOffsetX = 0 }) => panelOffsetX)).toEqual([0, 105, -105]);
    expect(trioFormationRegistry["all-front"].enemy.map(({ panelOffsetX = 0 }) => panelOffsetX)).toEqual([105, -105, 0]);
  });

  it.each([
    ["one-front-two-rear", "friendly"], ["one-front-two-rear", "enemy"],
    ["two-front-one-rear", "friendly"], ["two-front-one-rear", "enemy"],
    ["all-front", "friendly"], ["all-front", "enemy"],
  ] as const)("keeps each %s %s overhead inside its own positioned figure layer", async (formation, side) => {
    const snapshot = createFormatFixture(3);
    snapshot.formations = { friendly: formation, enemy: formation };
    applyFormationPositions(snapshot, "friendly", formation);
    applyFormationPositions(snapshot, "enemy", formation);
    render(<BattleScreen provider={new MockBattleProvider(snapshot)} />);
    await screen.findByRole("region", { name: "Battlefield" });

    const ids = snapshot.sides.find((candidate) => candidate.id === side)!.combatantIds;
    ids.forEach((id, slot) => {
      const layer = document.querySelector(`[data-combatant-id='${id}']`)?.closest<HTMLElement>(".formation-slot");
      expect(layer?.querySelector(".overhead")).toBeInTheDocument();
      expect(layer?.style.getPropertyValue("--overhead-offset-x"))
        .toBe(`${trioFormationRegistry[formation][side][slot].panelOffsetX ?? 0}px`);
    });
  });

  it("renders trio depth on the formation slot so figure-owned overlays stay with it", async () => {
    const snapshot = createFormatFixture(3);
    snapshot.formations = { friendly: "one-front-two-rear", enemy: "one-front-two-rear" };
    applyFormationPositions(snapshot, "friendly", "one-front-two-rear");
    applyFormationPositions(snapshot, "enemy", "one-front-two-rear");
    render(<BattleScreen provider={new MockBattleProvider(snapshot)} />);
    await screen.findByRole("region", { name: "Battlefield" });

    for (const side of ["friendly", "enemy"] as const) {
      for (const id of snapshot.sides.find((candidate) => candidate.id === side)!.combatantIds) {
        const hero = snapshot.combatants[id];
        const placement = formationFor(snapshot, side, hero.slot, hero.position);
        const slot = document.querySelector(`[data-combatant-id='${id}']`)?.closest<HTMLElement>(".formation-slot");
        expect(slot).toHaveStyle({ zIndex: String(placement.depth) });
        expect(slot?.querySelector(".overhead")).toBeInTheDocument();
      }
    }
  });

  it("renders independent friendly/enemy trio layouts and position-owned depth labels", async () => {
    const snapshot = createFormatFixture(3);
    snapshot.formations = { friendly: "all-front", enemy: "two-front-one-rear" };
    applyFormationPositions(snapshot, "friendly", "all-front");
    applyFormationPositions(snapshot, "enemy", "two-front-one-rear");
    render(<BattleScreen provider={new MockBattleProvider(snapshot)} />);
    await screen.findByRole("region", { name: "Battlefield" });

    const assertPlacement = (id: string, x: number, y: number, position: CombatantPosition) => {
      const slot = document.querySelector(`[data-combatant-id='${id}']`)?.closest<HTMLElement>(".formation-slot");
      expect(slot).toHaveStyle({ left: `${x}%`, top: `${y}%` });
      expect(slot).toHaveAttribute("data-position", position);
      expect(slot).toHaveAttribute("data-slot", position);
    };
    assertPlacement("friendly.ragnar", 39.5, 52, "front");
    assertPlacement("friendly.black_heart", 39.5, 71, "front");
    assertPlacement("friendly.arthas", 39.5, 90, "front");
    assertPlacement("enemy.nighthawk", 59, 81, "front");
    assertPlacement("enemy.andonidas", 59, 54, "front");
    assertPlacement("enemy.sashein", 78, 67, "rear");
  });

  it("never derives the trio presentation choice from a combatant position pattern", () => {
    const snapshot = createFormatFixture(3);
    snapshot.formations.friendly = "all-front";
    expect(snapshot.sides[0].combatantIds.map((id) => snapshot.combatants[id].position))
      .toEqual(["front", "rear", "rear"]);
    expect(trioFormationFor(snapshot, "friendly")).toBe("all-front");
    expect(formationFor(snapshot, "friendly", 1, "rear"))
      .toEqual({ ...trioFormationRegistry["all-front"].friendly[1], slot: "rear" });
  });

  it("uses only adapter validTargetIds when the supplied 3v3 target is rear", async () => {
    const user = userEvent.setup();
    const snapshot = createFormatFixture(3);
    snapshot.legalActions = snapshot.legalActions.map((action) => action.skillId === "skill.warrior.fatal_strike"
      ? { ...action, validTargetIds: ["enemy.sashein"] }
      : action);
    render(<BattleScreen provider={new MockBattleProvider(snapshot)} />);
    await screen.findByRole("region", { name: "Battlefield" });
    await user.click(screen.getByRole("button", { name: /Fatal Strike/i }));

    expect(screen.getByRole("button", { name: "Sashein, selectable target" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Nighthawk" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Andonidas" })).toBeDisabled();
  });

  it("keeps duel and duo presentation registries unchanged", () => {
    const duel = createFormatFixture(1);
    const duo = createFormatFixture(2);
    expect(formationFor(duel, "friendly", 0, "front")).toEqual(formationRegistry.duel.friendly[0]);
    expect(formationFor(duel, "enemy", 0, "front")).toEqual(formationRegistry.duel.enemy[0]);
    expect(formationFor(duo, "friendly", 0, "front")).toEqual({ slot: "front", x: 42, y: 68, scale: 1.02 });
    expect(formationFor(duo, "enemy", 1, "rear")).toEqual({ slot: "rear", x: 78, y: 68, scale: .94 });
  });

  it("uses a responsive three-column selector without rendering reference markers", () => {
    const css = readFileSync("app/globals.css", "utf8").replace(/\s+/g, "");
    expect(css).toMatch(/\.formation-choices\.options-3\{grid-template-columns:repeat\(3,minmax\(0,1fr\)\)\}/);
    expect(css).toMatch(/@media\(max-width:720px\)[\s\S]*\.formation-choices,\.formation-choices\.options-3\{grid-template-columns:1fr\}/);
    expect(css).not.toMatch(/\.formation-(?:selector|choices)[^{]*::(?:before|after)\{[^}]*content:["']?[1-6]/);
  });
});
