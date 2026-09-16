import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { TeamBuilder } from "@/components/battle/TeamBuilder";
import { resolveStructuredStage } from "@/components/stages/structured-stage-config";
import type { BattleSize, HeroDefinitionSummary } from "@/lib/battle/types";
import { UiAudioBoundary } from "@/components/audio/UiAudioBoundary";

const roster: HeroDefinitionSummary[] = [
  ["hero.warrior.weapon_master", "Garran", "Warrior", "Weapon Master"],
  ["hero.warrior.defence", "Falk", "Warrior", "Defence"],
  ["hero.warrior.berserker", "Rogan", "Warrior", "Berserker"],
  ["hero.mage.comprehensiveness", "Elyra", "Mage", "Comprehensiveness"],
  ["hero.rogue.comprehensiveness", "Hessa", "Rogue", "Comprehensiveness"],
  ["hero.paladin.retribution", "Cael", "Paladin", "Retribution"],
].map(([definitionId, displayName, faculty, specialization]) => ({
  definitionId, displayName, faculty, specialization,
}));

function playerSlot(index: number) {
  return document.querySelector<HTMLElement>(`[data-player-slot="${index}"]`)!;
}

function matrixCard(label: RegExp) {
  return screen.getByRole("button", { name: label });
}

async function choosePlayerSlot(user: ReturnType<typeof userEvent.setup>, slot: number, hero: RegExp) {
  await user.click(playerSlot(slot));
  await user.click(matrixCard(new RegExp(`Assign ${hero.source} to your Hero ${slot + 1}`, "i")));
}

describe("UI-026 automatic matrix slot advance", () => {
  it.each([1, 2, 3] as BattleSize[])("advances forward for %iv%i player teams", async (size) => {
    const user = userEvent.setup();
    render(<TeamBuilder roster={roster} onStart={vi.fn()} />);
    await user.click(screen.getByRole("radio", { name: `${size}v${size}` }));
    await choosePlayerSlot(user, 0, /Warrior · Weapon Master/);
    expect(playerSlot(Math.min(1, size - 1))).toHaveAttribute("aria-pressed", "true");
    if (size > 1) {
      await user.click(matrixCard(/Assign Warrior · Defence to your Hero 2/i));
      expect(playerSlot(2)).toHaveAttribute("aria-pressed", size === 3 ? "true" : "false");
    }
  });

  it("wraps once to the first empty slot when filling out of order", async () => {
    const user = userEvent.setup();
    render(<TeamBuilder roster={roster} onStart={vi.fn()} />);
    await user.click(screen.getByRole("radio", { name: "3v3" }));
    await choosePlayerSlot(user, 2, /Warrior · Berserker/);
    expect(playerSlot(0)).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("SELECT HERO 1")).toBeVisible();
  });

  it("keeps the filled slot active for replacement and after completing a team", async () => {
    const user = userEvent.setup();
    render(<TeamBuilder roster={roster} onStart={vi.fn()} />);
    await user.click(screen.getByRole("radio", { name: "2v2" }));
    await choosePlayerSlot(user, 0, /Warrior · Weapon Master/);
    await user.click(playerSlot(0));
    await user.click(matrixCard(/Assign Mage · Comprehensiveness to your Hero 1/i));
    expect(playerSlot(0)).toHaveAttribute("aria-pressed", "true");
    await user.click(playerSlot(1));
    await user.click(matrixCard(/Assign Warrior · Defence to your Hero 2/i));
    expect(playerSlot(1)).toHaveAttribute("aria-pressed", "true");
  });

  it("advances specified enemy slots independently and keeps player selection unchanged", async () => {
    const user = userEvent.setup();
    render(<TeamBuilder roster={roster} onStart={vi.fn()} />);
    await user.click(screen.getByRole("radio", { name: "2v2" }));
    await user.click(screen.getByRole("radio", { name: "Choose team" }));
    await user.click(screen.getByRole("radio", { name: "Player" }));
    await user.click(screen.getByRole("button", { name: /Select enemy Hero 1/i }));
    await user.click(matrixCard(/Assign Warrior · Weapon Master to enemy Hero 1/i));
    expect(document.querySelector('[data-enemy-slot="1"]')).toHaveAttribute("aria-pressed", "true");
    expect(playerSlot(0)).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("SELECT ENEMY HERO 2")).toBeVisible();
  });

  it("does not expose selectable enemy slots for random enemies", async () => {
    render(<TeamBuilder roster={roster} onStart={vi.fn()} />);
    expect(document.querySelectorAll(".selectable-enemy-slot")).toHaveLength(0);
    expect(screen.getByText("PYTHON SELECTED")).toBeVisible();
  });

  it("keeps predefined structured enemies fixed while advancing the player matrix", async () => {
    const user = userEvent.setup();
    const stage = resolveStructuredStage("warriors-barrack")!;
    render(<TeamBuilder mode="structured" stage={stage} battle={stage.battles[0]} roster={roster} onStart={vi.fn()} />);
    await user.click(matrixCard(/Assign Warrior · Weapon Master to your Hero 1/i));
    expect(playerSlot(1)).toHaveAttribute("aria-pressed", "true");
    expect(document.querySelectorAll(".selectable-enemy-slot")).toHaveLength(0);
    expect(screen.getByLabelText(/Predefined enemy team/i)).toBeVisible();
  });

  it("advances Arena TeamBuilder player slots but keeps the locked enemy fixed", async () => {
    const user = userEvent.setup();
    render(
      <TeamBuilder
        mode="arena-run"
        roster={roster}
        squadDefinitionIds={roster.slice(0, 3).map((hero) => hero.definitionId)}
        node={{ nodeIndex: 1, battleSize: 2, enemyFormation: "front-rear", enemyDefinitionIds: [roster[3].definitionId, roster[4].definitionId] }}
        arenaProgress={[{ nodeIndex: 1, battleSize: 2, completed: false, current: true }]}
        onStart={vi.fn()}
        onGiveUpCurrentRun={vi.fn()}
      />,
    );
    await user.click(matrixCard(/Assign Warrior · Weapon Master to your Hero 1/i));
    expect(playerSlot(1)).toHaveAttribute("aria-pressed", "true");
    expect(document.querySelectorAll(".selectable-enemy-slot")).toHaveLength(0);
  });

  it.each(["pointer", "Enter", "Space", "touch"])("uses the same assignment result for %s activation", async (interaction) => {
    const user = userEvent.setup();
    render(<TeamBuilder roster={roster} onStart={vi.fn()} />);
    const card = matrixCard(/Assign Warrior · Weapon Master to your Hero 1/i);
    if (interaction === "pointer") await user.click(card);
    if (interaction === "Enter") { card.focus(); await user.keyboard("{Enter}"); }
    if (interaction === "Space") { card.focus(); await user.keyboard(" "); }
    if (interaction === "touch") {
      fireEvent.pointerDown(card, { pointerType: "touch" });
      fireEvent.click(card, { pointerType: "touch" });
    }
    expect(playerSlot(0)).toHaveTextContent(/Warrior.*Weapon Master/);
    expect(playerSlot(1)).toHaveAttribute("aria-pressed", "false");
    if (interaction !== "touch") expect(document.activeElement).toBe(card);
  });

  it("updates matrix labels and preserves one AUDIO-002 click cue", async () => {
    const user = userEvent.setup();
    const audio = { unlock: vi.fn(), play: vi.fn() };
    render(<UiAudioBoundary manager={audio} as never><TeamBuilder roster={roster} onStart={vi.fn()} /></UiAudioBoundary>);
    await user.click(screen.getByRole("radio", { name: "2v2" }));
    audio.play.mockClear();
    const card = matrixCard(/Assign Warrior · Weapon Master to your Hero 1/i);
    card.focus();
    await user.keyboard("{Enter}");
    expect(screen.getByText("SELECT HERO 2")).toBeVisible();
    expect(document.activeElement).toBe(card);
    expect(audio.play.mock.calls.filter(([id]) => id === "ui.click")).toHaveLength(1);
  });
});
