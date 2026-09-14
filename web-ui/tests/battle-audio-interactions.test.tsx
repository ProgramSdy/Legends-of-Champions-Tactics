import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { BattleScreen } from "@/components/battle/BattleScreen";
import { UiAudioBoundary } from "@/components/audio/UiAudioBoundary";
import { MockBattleProvider } from "@/lib/battle/fixture";
import { audioManager } from "@/lib/audio/AudioManager";

describe("battle audio interaction boundary", () => {
  afterEach(() => vi.restoreAllMocks());

  it("uses scoped focus/click feedback without blocking skill selection", async () => {
    const play = vi.spyOn(audioManager, "play").mockImplementation(() => undefined);
    const unlock = vi.spyOn(audioManager, "unlock").mockImplementation(() => undefined);
    render(<UiAudioBoundary><BattleScreen provider={new MockBattleProvider()} /></UiAudioBoundary>);
    const skill = await screen.findByRole("button", { name: /Life Drain/i });

    fireEvent.pointerOver(skill, { relatedTarget: null });
    expect(play).toHaveBeenCalledWith("ui.hover");
    fireEvent.click(skill);
    expect(unlock).toHaveBeenCalled();
    expect(play).toHaveBeenCalledWith("ui.click");
    expect(skill).toHaveAttribute("aria-pressed", "true");
  });

  it("does not emit hover feedback for pointer movement within one control", async () => {
    const play = vi.spyOn(audioManager, "play").mockImplementation(() => undefined);
    render(<UiAudioBoundary><BattleScreen provider={new MockBattleProvider()} /></UiAudioBoundary>);
    const skill = await screen.findByRole("button", { name: /Life Drain/i });
    const child = document.createElement("span");
    skill.appendChild(child);

    fireEvent.pointerOver(skill, { relatedTarget: null });
    fireEvent.pointerOver(child, { relatedTarget: skill });
    expect(play).toHaveBeenCalledTimes(1);
  });

  it.each(["Enter", "Space"] as const)("plays one click cue for keyboard %s activation", async (key) => {
    const play = vi.spyOn(audioManager, "play").mockImplementation(() => undefined);
    const unlock = vi.spyOn(audioManager, "unlock").mockImplementation(() => undefined);
    render(<UiAudioBoundary><BattleScreen provider={new MockBattleProvider()} /></UiAudioBoundary>);
    const skill = await screen.findByRole("button", { name: /Life Drain/i });
    const user = userEvent.setup();

    skill.focus();
    fireEvent.focus(skill);
    expect(play).toHaveBeenCalledWith("ui.hover");
    await user.keyboard(key === "Space" ? " " : "{Enter}");

    expect(unlock).toHaveBeenCalled();
    expect(play.mock.calls.filter(([id]) => id === "ui.click")).toHaveLength(1);
    expect(skill).toHaveAttribute("aria-pressed", "true");
  });
});
