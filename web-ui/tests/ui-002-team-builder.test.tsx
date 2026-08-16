import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { BattleExperience } from "@/components/battle/BattleExperience";
import { BattleScreen } from "@/components/battle/BattleScreen";
import { TeamBuilder } from "@/components/battle/TeamBuilder";
import { createFormatFixture, MockBattleProvider } from "@/lib/battle/fixture";
import { fetchHeroRoster } from "@/lib/battle/liveProvider";

const roster = [
  ["hero.priest.comprehensiveness", "Priest", "Comprehensiveness"],
  ["hero.priest.discipline", "Priest", "Discipline"],
  ["hero.paladin.retribution", "Paladin", "Retribution"],
  ["hero.paladin.protection", "Paladin", "Protection"],
  ["hero.mage.comprehensiveness", "Mage", "Comprehensiveness"],
  ["hero.warrior.defence", "Warrior", "Defence"],
  ["hero.warrior.weapon_master", "Warrior", "Weapon Master"],
  ["hero.rogue.comprehensiveness", "Rogue", "Comprehensiveness"],
  ["hero.paladin.holy", "Paladin", "Holy"],
  ["hero.warrior.berserker", "Warrior", "Berserker"],
].map(([definitionId, displayName, specialization]) => ({ definitionId, displayName, specialization, faculty: displayName }));

describe("UI-002 Team Builder", () => {
  it("is keyboard accessible and submits a typed specified 3v3 configuration", async () => {
    const user = userEvent.setup();
    const onStart = vi.fn();
    render(<TeamBuilder roster={roster} onStart={onStart} />);

    expect(screen.getByRole("heading", { name: "Team Builder" })).toBeVisible();
    expect(screen.getAllByRole("button", { name: /Assign .* to your Hero 1/i })).toHaveLength(6);
    expect(roster).toHaveLength(10);

    await user.click(screen.getByRole("radio", { name: "3v3" }));
    await user.click(screen.getByRole("button", { name: /Assign Priest · Comprehensiveness to your Hero 1/i }));
    await user.click(screen.getByRole("button", { name: /Select your Hero 2/i }));
    await user.click(screen.getByRole("button", { name: /Assign Priest · Discipline to your Hero 2/i }));
    await user.click(screen.getByRole("button", { name: /Select your Hero 3/i }));
    await user.click(screen.getByRole("button", { name: /Assign Paladin · Retribution to your Hero 3/i }));
    await user.click(screen.getByRole("radio", { name: "Choose team" }));
    await user.click(screen.getByRole("radio", { name: "Player" }));
    await user.click(screen.getByRole("button", { name: /Select enemy Hero 1/i }));
    await user.click(screen.getByRole("button", { name: /Assign Warrior · Defence to enemy Hero 1/i }));
    await user.click(screen.getByRole("button", { name: /Select enemy Hero 2/i }));
    await user.click(screen.getByRole("button", { name: /Assign Mage · Comprehensiveness to enemy Hero 2/i }));
    await user.click(screen.getByRole("button", { name: /Select enemy Hero 3/i }));
    await user.click(screen.getByRole("button", { name: /Assign Priest · Comprehensiveness to enemy Hero 3/i }));
    await user.type(screen.getByLabelText(/Seed/i), "42");
    await user.click(screen.getByRole("button", { name: "ENTER BATTLE" }));

    expect(onStart).toHaveBeenCalledWith({
      battleSize: 3,
      playerFormation: "one-front-two-rear",
      playerTeam: [
        "hero.priest.comprehensiveness",
        "hero.priest.discipline",
        "hero.paladin.retribution",
      ],
      enemyCompositionMode: "specified",
      enemyTeam: ["hero.warrior.defence", "hero.mage.comprehensiveness", "hero.priest.comprehensiveness"],
      enemyControlMode: "player",
      enemyFormation: "one-front-two-rear",
      seed: 42,
    });
  });

  it("sends no enemy team in random mode and supports duplicate selections", () => {
    const onStart = vi.fn();
    render(<TeamBuilder roster={roster} onStart={onStart} />);
    fireEvent.click(screen.getByRole("radio", { name: "2v2" }));
    fireEvent.click(screen.getByRole("button", { name: /Assign Paladin · Retribution to your Hero 1/i }));
    fireEvent.click(screen.getByRole("button", { name: /Select your Hero 2/i }));
    fireEvent.click(screen.getByRole("button", { name: /Assign Paladin · Retribution to your Hero 2/i }));
    fireEvent.click(document.querySelector<HTMLElement>('[data-player-slot="0"]')!);
    fireEvent.click(document.querySelector<HTMLElement>('[data-hero-id="hero.paladin.retribution"]')!);
    fireEvent.click(document.querySelector<HTMLElement>('[data-player-slot="1"]')!);
    fireEvent.click(document.querySelector<HTMLElement>('[data-hero-id="hero.paladin.retribution"]')!);
    fireEvent.click(screen.getByRole("button", { name: "ENTER BATTLE" }));

    expect(onStart).toHaveBeenCalledWith({
      battleSize: 2,
      playerTeam: ["hero.paladin.retribution", "hero.paladin.retribution"],
      playerFormation: "front-rear",
      enemyCompositionMode: "random",
      enemyControlMode: "computer",
    });
  });

  it("prevents launch when a required team slot or seed is invalid", () => {
    render(<TeamBuilder roster={roster} onStart={vi.fn()} />);
    fireEvent.click(screen.getByRole("radio", { name: "Choose team" }));
    expect(screen.getByText("Fill every player-team slot.")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: /Select your Hero 1/i }));
    fireEvent.click(screen.getByRole("button", { name: /Assign Priest · Comprehensiveness to your Hero 1/i }));
    fireEvent.click(screen.getByRole("button", { name: /Select enemy Hero 1/i }));
    expect(screen.getByText("Fill every specified enemy-team slot.")).toBeVisible();
    expect(screen.getByRole("button", { name: "ENTER BATTLE" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: /Assign Warrior · Defence to enemy Hero 1/i }));

    fireEvent.change(screen.getByLabelText(/Seed/i), { target: { value: "-1" } });
    expect(screen.getByText("Seed must be a non-negative whole number.")).toBeVisible();
    expect(screen.getByRole("button", { name: "ENTER BATTLE" })).toBeDisabled();
  });

  it("shows the authoritative outcome in a modal and returns to Team Builder", async () => {
    const snapshot = createFormatFixture(1);
    snapshot.phase = "ended";
    snapshot.activeCombatantId = null;
    snapshot.legalActions = [];
    snapshot.outcome = { kind: "victory", winningSideId: "friendly" };
    const onReturn = vi.fn();
    render(<BattleScreen provider={new MockBattleProvider(snapshot)} mode="live" onReturnToBuilder={onReturn} />);

    const dialog = await screen.findByRole("dialog", { name: "YOUR TEAM VICTORIOUS" });
    expect(dialog).toBeVisible();
    const returnButton = screen.getByRole("button", { name: "RETURN TO TEAM BUILDER" });
    await waitFor(() => expect(returnButton).toHaveFocus());
    await userEvent.keyboard("{Tab}");
    expect(returnButton).toHaveFocus();
    fireEvent.click(returnButton);
    expect(onReturn).toHaveBeenCalledOnce();
  });

  it("loads the backend roster and creates a fresh session after returning", async () => {
    const user = userEvent.setup();
    const ended = createFormatFixture(1);
    ended.phase = "ended";
    ended.activeCombatantId = null;
    ended.legalActions = [];
    ended.outcome = { kind: "victory", winningSideId: "friendly" };
    const battleEnvelope = {
      contractVersion: "1.0",
      battleId: "battle.ui-002",
      revision: 9,
      data: { events: [], snapshot: ended },
    };
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify({
        contractVersion: "1.0",
        heroes: roster,
      }), { status: 200, headers: { "Content-Type": "application/json" } }))
      .mockResolvedValueOnce(new Response(JSON.stringify(battleEnvelope), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        ...battleEnvelope,
        battleId: "battle.ui-002.relaunch",
      }), { status: 200, headers: { "Content-Type": "application/json" } }));

    render(<BattleExperience countdownStepMs={0} />);

    expect(await screen.findByRole("heading", { name: "Team Builder" })).toBeVisible();
    await user.click(screen.getByRole("button", { name: /Assign Priest · Comprehensiveness to your Hero 1/i }));
    await user.click(screen.getByRole("button", { name: "ENTER BATTLE" }));
    expect(await screen.findByRole("dialog", { name: "YOUR TEAM VICTORIOUS" })).toBeVisible();

    await user.click(screen.getByRole("button", { name: "RETURN TO TEAM BUILDER" }));
    expect(await screen.findByRole("heading", { name: "Team Builder" })).toBeVisible();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Assign Priest · Comprehensiveness to your Hero 1/i }));
    await user.click(screen.getByRole("button", { name: "ENTER BATTLE" }));
    expect(await screen.findByRole("dialog", { name: "YOUR TEAM VICTORIOUS" })).toBeVisible();

    const createCalls = fetchMock.mock.calls.filter(([url, init]) =>
      String(url).endsWith("/api/v1/battles") && init?.method === "POST"
    );
    expect(createCalls).toHaveLength(2);
    expect(createCalls[0]?.[1]?.body).toBe(createCalls[1]?.[1]?.body);
    fetchMock.mockRestore();
  });

  it("rejects malformed roster responses at the frontend contract boundary", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({
      contractVersion: "1.0",
      heroes: Array.from({ length: 8 }, () => ({
        definitionId: null,
        displayName: "Invalid",
        faculty: "Unknown",
        specialization: "Unknown",
      })),
    }), { status: 200, headers: { "Content-Type": "application/json" } }));

    await expect(fetchHeroRoster("http://adapter.test")).rejects.toMatchObject({
      kind: "adapter",
      message: "The battle service returned an unsupported hero roster.",
    });
    fetchMock.mockRestore();
  });
});
