import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { UiAudioBoundary } from "@/components/audio/UiAudioBoundary";
import { TeamBuilder } from "@/components/battle/TeamBuilder";

type AudioSpy = {
  unlock: ReturnType<typeof vi.fn>;
  play: ReturnType<typeof vi.fn>;
};

function makeAudioSpy(): AudioSpy {
  return { unlock: vi.fn(), play: vi.fn() };
}

function RouteControlFixture({ onAction }: { onAction: () => void }) {
  return (
    <>
      <section aria-label="Startup">
        <button onClick={onAction}>START GAME</button>
        <button disabled>RETRY</button>
      </section>
      <section aria-label="Stage Map">
        <a href="/game?stage=arena">Arena</a>
        <span>Inactive artwork</span>
      </section>
      <section aria-label="Team Builder">
        <button onClick={onAction}>ENTER BATTLE</button>
        <label htmlFor="battle-size">Battle size</label>
        <select id="battle-size" defaultValue="1v1" onChange={onAction}>
          <option>1v1</option>
          <option>2v2</option>
        </select>
        <input aria-label="Seed" onChange={() => undefined} />
      </section>
      <section aria-label="Arena Run">
        <button onClick={onAction}>LOCK SQUAD &amp; START RUN</button>
        <button aria-disabled="true" onClick={onAction}>GIVE UP CURRENT RUN</button>
      </section>
      <section aria-label="Battle">
        <button onClick={onAction}>RESIGN</button>
      </section>
      <section aria-label="Debug">
        <button onClick={onAction}>Retry roster</button>
      </section>
      <section aria-label="Asset Registry">
        <a href="/game">Return to battle</a>
      </section>
    </>
  );
}

describe("shared UI audio boundary", () => {
  it("integrates the real Team Builder controls without changing selection", async () => {
    const audio = makeAudioSpy();
    const onStart = vi.fn();
    const roster = [{
      definitionId: "hero.warrior.weapon_master",
      displayName: "Ragnar",
      faculty: "Warrior",
      specialization: "Weapon Master",
    }];
    render(
      <UiAudioBoundary manager={audio as never}>
        <TeamBuilder mode="debug" roster={roster} onStart={onStart} />
      </UiAudioBoundary>,
    );
    const slot = screen.getByRole("button", { name: /select your hero 1/i });
    await userEvent.setup().click(slot);
    expect(audio.play).toHaveBeenCalledWith("ui.click");
    expect(screen.getByRole("button", { name: /assign warrior.*weapon master to your hero 1/i })).toBeVisible();
    expect(onStart).not.toHaveBeenCalled();
  });

  it("covers eligible controls across every shipped route family and preserves actions", () => {
    const audio = makeAudioSpy();
    const action = vi.fn();
    render(
      <UiAudioBoundary manager={audio as never}>
        <RouteControlFixture onAction={action} />
      </UiAudioBoundary>,
    );

    const controls = [
      "START GAME", "Arena", "ENTER BATTLE", "Battle size", "LOCK SQUAD & START RUN",
      "RESIGN", "Retry roster", "Return to battle",
    ];
    for (const name of controls) {
      const role = name === "Arena" || name === "Return to battle"
        ? "link"
        : name === "Battle size" ? "combobox" : "button";
      const control = screen.getByRole(role, { name });
      fireEvent.pointerOver(control, { relatedTarget: null });
      fireEvent.click(control);
    }

    expect(audio.play).toHaveBeenCalledWith("ui.hover");
    expect(audio.play).toHaveBeenCalledWith("ui.click");
    expect(audio.unlock).toHaveBeenCalled();
    expect(action).toHaveBeenCalled();
  });

  it("keeps disabled, aria-disabled, decorative, and text-entry interactions silent", () => {
    const audio = makeAudioSpy();
    render(
      <UiAudioBoundary manager={audio as never}>
        <button disabled>Disabled</button>
        <button aria-disabled="true">Unavailable</button>
        <span>Decorative label</span>
        <input aria-label="Seed" />
      </UiAudioBoundary>,
    );

    fireEvent.pointerOver(screen.getByRole("button", { name: "Disabled" }));
    fireEvent.click(screen.getByRole("button", { name: "Disabled" }));
    fireEvent.pointerOver(screen.getByRole("button", { name: "Unavailable" }));
    fireEvent.click(screen.getByRole("button", { name: "Unavailable" }));
    fireEvent.pointerOver(screen.getByText("Decorative label"));
    fireEvent.change(screen.getByRole("textbox", { name: "Seed" }), { target: { value: "42" } });

    expect(audio.play).not.toHaveBeenCalled();
    expect(audio.unlock).not.toHaveBeenCalled();
  });

  it.each(["Enter", " "]) ("plays one activation cue for keyboard %s", async (key) => {
    const audio = makeAudioSpy();
    const action = vi.fn();
    render(
      <UiAudioBoundary manager={audio as never}>
        <button onClick={action}>Next</button>
      </UiAudioBoundary>,
    );
    const button = screen.getByRole("button", { name: "Next" });
    button.focus();
    fireEvent.focus(button);
    await userEvent.setup().keyboard(key === "Enter" ? "{Enter}" : " ");

    expect(audio.play.mock.calls.filter(([id]) => id === "ui.click")).toHaveLength(1);
    expect(action).toHaveBeenCalledTimes(1);
  });

  it("unlocks and clicks on touch without a hover cue", () => {
    const audio = makeAudioSpy();
    const action = vi.fn();
    render(
      <UiAudioBoundary manager={audio as never}>
        <button onClick={action}>Touch action</button>
      </UiAudioBoundary>,
    );
    const button = screen.getByRole("button", { name: "Touch action" });
    fireEvent.pointerOver(button, { pointerType: "touch", relatedTarget: null });
    fireEvent.pointerDown(button, { pointerType: "touch" });
    fireEvent.click(button, { pointerType: "touch" });
    expect(audio.unlock).toHaveBeenCalled();
    expect(audio.play).toHaveBeenCalledTimes(1);
    expect(audio.play).toHaveBeenCalledWith("ui.click");
    expect(audio.play).not.toHaveBeenCalledWith("ui.hover");
    expect(action).toHaveBeenCalledTimes(1);
  });
});
