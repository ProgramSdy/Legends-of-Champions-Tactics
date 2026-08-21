import { readFileSync } from "node:fs";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { StartupScreen } from "@/components/startup/StartupScreen";
import { TeamBuilder } from "@/components/battle/TeamBuilder";
import { STAGE_DEFINITIONS } from "@/components/stages/stage-config";
import type {
  HeroDefinitionSummary,
  PlayerProgression,
  SaveSlotId,
  SaveSlotSummary,
} from "@/lib/battle/types";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));

const roster: HeroDefinitionSummary[] = [
  { definitionId: "hero.warrior.weapon_master", displayName: "Garran", faculty: "Warrior", specialization: "Weapon Master" },
  { definitionId: "hero.mage.comprehensiveness", displayName: "Elyra", faculty: "Mage", specialization: "Comprehensiveness" },
  { definitionId: "hero.priest.comprehensiveness", displayName: "Aldric", faculty: "Priest", specialization: "Comprehensiveness" },
  { definitionId: "hero.rogue.comprehensiveness", displayName: "Hessa", faculty: "Rogue", specialization: "Comprehensiveness" },
];

const starterIds = roster.map((hero) => hero.definitionId);

function slot(slotId: SaveSlotId, occupied = false, active = false): SaveSlotSummary {
  return {
    slotId,
    occupied,
    profileId: occupied ? `profile.local.slot-${slotId}` : null,
    createdAt: occupied ? "2026-08-20T00:00:00Z" : null,
    lastPlayedAt: occupied ? "2026-08-20T01:00:00Z" : null,
    active: occupied && active,
  };
}

function fiveSlots(occupiedIds: SaveSlotId[] = [], activeSlotId: SaveSlotId | null = null) {
  return ([1, 2, 3, 4, 5] as SaveSlotId[]).map((slotId) => (
    slot(slotId, occupiedIds.includes(slotId), activeSlotId === slotId)
  ));
}

function progression(slotId: SaveSlotId): PlayerProgression {
  return {
    profileId: `profile.local.slot-${slotId}`,
    unlockedHeroDefinitionIds: starterIds,
    stageProgress: [
      { stageId: "paladins-altar", highestCompletedBattle: 0, unlockedBattle: 1, completed: false },
      { stageId: "warriors-barrack", highestCompletedBattle: 0, unlockedBattle: 1, completed: false },
    ],
    grantedRewards: [],
  };
}

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function listResponse(occupiedIds: SaveSlotId[] = [], activeSlotId: SaveSlotId | null = null) {
  return {
    contractVersion: "1.0",
    activeSlotId,
    slots: fiveSlots(occupiedIds, activeSlotId),
  };
}

function actionResponse(slotId: SaveSlotId) {
  return {
    contractVersion: "1.0",
    activeSlotId: slotId,
    slot: slot(slotId, true, true),
    progression: progression(slotId),
  };
}

afterEach(() => {
  push.mockReset();
  vi.restoreAllMocks();
});

describe("UI-021 startup save-slot flow", () => {
  it("opens choices, disables Load Game for five empty slots, and restores focus on Escape", async () => {
    const user = userEvent.setup();
    vi.spyOn(globalThis, "fetch").mockResolvedValue(json(listResponse()));
    render(<StartupScreen />);

    const start = screen.getByRole("button", { name: "START GAME" });
    await user.click(start);
    const dialog = await screen.findByRole("dialog", { name: "Choose your journey" });
    const newGame = screen.getByRole("button", { name: /NEW GAME/i });
    const loadGame = screen.getByRole("button", { name: /LOAD GAME/i });
    expect(dialog).toBeVisible();
    expect(newGame).toBeEnabled();
    expect(loadGame).toBeDisabled();
    expect(screen.getByText(/No saved games/i)).toBeVisible();
    await waitFor(() => expect(newGame).toHaveFocus());

    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    await waitFor(() => expect(start).toHaveFocus());
  });

  it("keeps a failed slot listing actionable and moves focus to Retry", async () => {
    const user = userEvent.setup();
    vi.spyOn(globalThis, "fetch").mockRejectedValueOnce(new Error("Save slot service unavailable."));
    render(<StartupScreen />);

    await user.click(screen.getByRole("button", { name: "START GAME" }));
    const retry = await screen.findByRole("button", { name: "RETRY" });
    expect(screen.getByRole("alert")).toHaveTextContent("Battle service is disconnected.");
    expect(screen.getByRole("button", { name: /NEW GAME/i })).toBeDisabled();
    expect(screen.getByRole("button", { name: /LOAD GAME/i })).toBeDisabled();
    await waitFor(() => expect(retry).toHaveFocus());
  });

  it("creates an empty slot with no client progression payload and routes only after success", async () => {
    const user = userEvent.setup();
    let resolveCreate!: (response: Response) => void;
    const createResponse = new Promise<Response>((resolve) => { resolveCreate = resolve; });
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(json(listResponse()))
      .mockReturnValueOnce(createResponse);
    render(<StartupScreen />);

    await user.click(screen.getByRole("button", { name: "START GAME" }));
    await user.click(await screen.findByRole("button", { name: /NEW GAME/i }));
    expect(screen.getAllByRole("button", { name: /Save Slot [1-5]/i })).toHaveLength(5);
    await user.click(screen.getByRole("button", { name: /Save Slot 2, Empty/i }));
    expect(push).not.toHaveBeenCalled();
    expect(fetchMock).toHaveBeenLastCalledWith(
      expect.stringMatching(/\/api\/v1\/save-slots\/2\/create$/),
      expect.objectContaining({ method: "POST" }),
    );
    expect(fetchMock.mock.calls[1][1]?.body).toBeUndefined();

    resolveCreate(json(actionResponse(2)));
    await waitFor(() => expect(push).toHaveBeenCalledWith("/stages"));
  });

  it("loads only an occupied slot without reinitializing it", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(json(listResponse([3], 3)))
      .mockResolvedValueOnce(json(actionResponse(3)));
    render(<StartupScreen />);

    await user.click(screen.getByRole("button", { name: "START GAME" }));
    await user.click(await screen.findByRole("button", { name: /LOAD GAME/i }));
    expect(screen.getByRole("button", { name: /Save Slot 1, Empty/i })).toBeDisabled();
    const occupied = screen.getByRole("button", { name: /Save Slot 3, Occupied/i });
    expect(occupied).toBeEnabled();
    await user.click(occupied);

    expect(fetchMock).toHaveBeenLastCalledWith(
      expect.stringMatching(/\/api\/v1\/save-slots\/3\/load$/),
      expect.objectContaining({ method: "POST" }),
    );
    expect(fetchMock.mock.calls[1][1]?.body).toBeUndefined();
    await waitFor(() => expect(push).toHaveBeenCalledWith("/stages"));
  });

  it("requires exact-slot overwrite confirmation and cancellation performs no write", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(json(listResponse([4])))
      .mockResolvedValueOnce(json(actionResponse(4)));
    render(<StartupScreen />);

    await user.click(screen.getByRole("button", { name: "START GAME" }));
    await user.click(await screen.findByRole("button", { name: /NEW GAME/i }));
    await user.click(screen.getByRole("button", { name: /Save Slot 4, Occupied/i }));
    expect(screen.getByRole("heading", { name: "Overwrite Save Slot 4?" })).toBeVisible();
    expect(screen.getByText(/permanently replaced/i)).toBeVisible();
    await user.click(screen.getByRole("button", { name: "KEEP SAVE SLOT 4" }));
    expect(fetchMock).toHaveBeenCalledTimes(1);

    await user.click(screen.getByRole("button", { name: /Save Slot 4, Occupied/i }));
    await user.click(screen.getByRole("button", { name: "OVERWRITE SLOT 4" }));
    expect(fetchMock).toHaveBeenLastCalledWith(
      expect.stringMatching(/\/api\/v1\/save-slots\/4\/overwrite$/),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ confirmOverwrite: true }),
      }),
    );
    await waitFor(() => expect(push).toHaveBeenCalledWith("/stages"));
  });
});

describe("UI-021 stage-preview focus boundary", () => {
  it("keeps hotspot geometry separate from stage-specific preview focus metadata", () => {
    const enabled = STAGE_DEFINITIONS.filter((stage) => stage.enabled);
    expect(enabled).toHaveLength(3);
    const arena = enabled.find((stage) => stage.id === "arena")!;
    const barrack = enabled.find((stage) => stage.id === "warriors-barrack")!;
    const altar = enabled.find((stage) => stage.id === "paladins-altar")!;
    expect(barrack.geometry).toEqual({ leftPercent: 11.5, topPercent: 13.2, widthPercent: 22.6, heightPercent: 21.8 });
    expect(altar.geometry).toEqual({ leftPercent: 81.2, topPercent: 34.8, widthPercent: 13.8, heightPercent: 22.7 });
    expect(barrack.previewFocus).not.toEqual(arena.previewFocus);
    expect(altar.previewFocus).not.toEqual(arena.previewFocus);
    expect(barrack.previewFocus).not.toEqual(altar.previewFocus);
  });

  it.each([
    ["arena", "50% 51.5%", "0%"],
    ["warriors-barrack", "22.8% 23.5%", "72%"],
    ["paladins-altar", "87.2% 43.2%", "-46%"],
  ])("passes the %s preview focus into responsive crop hooks", (stageId, objectPosition, offsetX) => {
    render(<TeamBuilder roster={roster} selectedStageId={stageId} onStart={vi.fn()} />);
    const image = document.querySelector<HTMLElement>(".current-stage-map")!;
    expect(image).toHaveStyle({ objectPosition });
    expect(image.style.getPropertyValue("--stage-preview-scale")).toBe("1.85");
    expect(image.style.getPropertyValue("--stage-preview-offset-x")).toBe(offsetX);
    const css = readFileSync("app/globals.css", "utf8");
    expect(css).toContain(".current-stage-media>.current-stage-map");
    expect(css).toContain("var(--stage-preview-offset-x)");
    expect(css).toContain("var(--stage-preview-scale)");
  });
});
