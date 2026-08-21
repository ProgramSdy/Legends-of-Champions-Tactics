import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { StartupScreen } from "@/components/startup/StartupScreen";
import {
  createSaveSlot,
  fetchSaveSlots,
  loadSaveSlot,
  overwriteSaveSlot,
} from "@/lib/battle/liveProvider";
import type { SaveSlotSummary } from "@/lib/battle/types";

const push = vi.fn();

vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));
vi.mock("@/lib/battle/liveProvider", () => ({
  fetchSaveSlots: vi.fn(),
  createSaveSlot: vi.fn(),
  loadSaveSlot: vi.fn(),
  overwriteSaveSlot: vi.fn(),
}));

const fetchSlots = vi.mocked(fetchSaveSlots);
const createSlot = vi.mocked(createSaveSlot);
const loadSlot = vi.mocked(loadSaveSlot);
const overwriteSlot = vi.mocked(overwriteSaveSlot);

function slots(occupied: readonly number[] = [], activeSlotId: number | null = null): SaveSlotSummary[] {
  return [1, 2, 3, 4, 5].map((slotId) => {
    const isOccupied = occupied.includes(slotId);
    return {
      slotId: slotId as SaveSlotSummary["slotId"],
      occupied: isOccupied,
      profileId: isOccupied ? `profile.local.slot.${slotId}` : null,
      createdAt: isOccupied ? "2026-08-20T10:00:00.000Z" : null,
      lastPlayedAt: isOccupied ? "2026-08-20T11:00:00.000Z" : null,
      active: activeSlotId === slotId,
    };
  });
}

function saveSlotResponse(slotId: 1 | 2 | 3 | 4 | 5) {
  const slot = slots([slotId], slotId)[slotId - 1];
  return {
    contractVersion: "1.0" as const,
    activeSlotId: slotId,
    slot,
    progression: {
      profileId: slot.profileId!,
      unlockedHeroDefinitionIds: ["hero.warrior.weapon_master"],
      stageProgress: [],
      grantedRewards: [],
    },
  };
}

async function openMenu(slotEntries: SaveSlotSummary[]) {
  fetchSlots.mockResolvedValueOnce({ contractVersion: "1.0", activeSlotId: null, slots: slotEntries });
  const user = userEvent.setup();
  render(<StartupScreen />);
  const start = screen.getByRole("button", { name: /start game/i });
  await user.click(start);
  await screen.findByRole("heading", { name: /choose your journey/i });
  return { user, start };
}

afterEach(() => {
  vi.clearAllMocks();
});

describe("UI-021 startup save-slot flow", () => {
  it("does not route directly from START GAME, disables Load Game for five empty slots, and restores focus on Escape", async () => {
    const { user, start } = await openMenu(slots());

    expect(push).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: /new game/i })).toBeEnabled();
    expect(screen.getByRole("button", { name: /load game/i })).toBeDisabled();
    expect(screen.getByText(/no saved games\. create a new game first/i)).toBeVisible();

    await waitFor(() => expect(screen.getByRole("button", { name: /new game/i })).toHaveFocus());
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    await waitFor(() => expect(start).toHaveFocus());
  });

  it("traps keyboard focus in the choice dialog and supports keyboard-only New Game selection", async () => {
    const { user } = await openMenu(slots());
    const newGame = screen.getByRole("button", { name: /new game/i });
    const cancel = screen.getByRole("button", { name: "CANCEL" });
    await waitFor(() => expect(newGame).toHaveFocus());

    fireEvent.keyDown(newGame, { key: "Tab", shiftKey: true });
    expect(cancel).toHaveFocus();
    fireEvent.keyDown(cancel, { key: "Tab" });
    expect(newGame).toHaveFocus();

    await user.keyboard("{Enter}");
    expect(await screen.findByRole("heading", { name: /choose a save slot/i })).toBeVisible();
    const slotOne = screen.getByRole("button", { name: /save slot 1, empty/i });
    await user.click(slotOne);
    expect(createSlot).toHaveBeenCalledWith(1);
  });

  it("routes only after a successful empty-slot creation", async () => {
    const { user } = await openMenu(slots());
    createSlot.mockResolvedValueOnce(saveSlotResponse(2));
    await user.click(screen.getByRole("button", { name: /new game/i }));
    await user.click(screen.getByRole("button", { name: /save slot 2, empty/i }));

    await waitFor(() => expect(push).toHaveBeenCalledWith("/stages"));
    expect(createSlot).toHaveBeenCalledTimes(1);
    expect(loadSlot).not.toHaveBeenCalled();
    expect(overwriteSlot).not.toHaveBeenCalled();
  });

  it("requires exact-slot overwrite confirmation and cancelling it performs no write", async () => {
    const { user } = await openMenu(slots([3]));
    await user.click(screen.getByRole("button", { name: /new game/i }));
    await user.click(screen.getByRole("button", { name: /save slot 3, occupied/i }));

    expect(await screen.findByRole("heading", { name: /overwrite save slot 3/i })).toBeVisible();
    expect(screen.getByText(/save slot 3's saved progression will be permanently replaced/i)).toBeVisible();
    await user.click(screen.getByRole("button", { name: /keep save slot 3/i }));
    expect(await screen.findByRole("heading", { name: /choose a save slot/i })).toBeVisible();
    expect(overwriteSlot).not.toHaveBeenCalled();
    expect(push).not.toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: /save slot 3, occupied/i }));
    overwriteSlot.mockResolvedValueOnce(saveSlotResponse(3));
    await user.click(screen.getByRole("button", { name: /overwrite slot 3/i }));
    await waitFor(() => expect(overwriteSlot).toHaveBeenCalledWith(3));
    expect(push).toHaveBeenCalledWith("/stages");
  });

  it("enables Load Game only for occupied slots and keeps an action failure in the dialog", async () => {
    const { user } = await openMenu(slots([2], 2));
    await user.click(screen.getByRole("button", { name: /load game/i }));
    const empty = screen.getByRole("button", { name: /save slot 1, empty/i });
    const occupied = screen.getByRole("button", { name: /save slot 2, occupied/i });
    expect(empty).toBeDisabled();
    expect(occupied).toBeEnabled();

    loadSlot.mockRejectedValueOnce(new Error("Save slot service unavailable."));
    await user.click(occupied);
    expect(await screen.findByRole("alert")).toHaveTextContent("Save slot service unavailable.");
    expect(push).not.toHaveBeenCalled();
  });
});
