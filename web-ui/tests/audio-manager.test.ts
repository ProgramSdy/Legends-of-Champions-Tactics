import { describe, expect, it, vi } from "vitest";
import { AudioManager } from "@/lib/audio/AudioManager";
import { soundDefinitions, type SoundDefinition } from "@/lib/audio/soundDefinitions";

describe("central audio boundary", () => {
  it("keeps the complete stable catalogue and provider definitions separate from callers", () => {
    expect(Object.keys(soundDefinitions)).toEqual([
      "ui.click", "ui.hover", "battle.event", "battle.skill", "battle.damage",
      "battle.evade", "battle.buff", "battle.debuff", "battle.defeated",
    ]);
    expect(soundDefinitions["battle.damage"].provider.type).toBe("jsfxr");
    expect(soundDefinitions["battle.damage"].provider).toHaveProperty("preset");
  });

  it("plays a future file provider shape without changing the stable caller contract", () => {
    const futureFileSound: SoundDefinition = {
      category: "battle", cooldownMs: 0,
      provider: { type: "file", src: "/sounds/future-hit.ogg", volume: 0.1 },
    };
    const fileAudio = { volume: 0, play: vi.fn() };
    const createFileAudio = vi.fn(() => fileAudio);
    const loadJsfxr = vi.fn(async () => ({ generate: vi.fn(), play: vi.fn() }));
    const manager = new AudioManager({
      isBrowser: () => true,
      createFileAudio,
      loadJsfxr,
      definitions: { ...soundDefinitions, "ui.click": futureFileSound },
    });

    manager.unlock();
    manager.play("ui.click");

    expect(createFileAudio).toHaveBeenCalledWith("/sounds/future-hit.ogg");
    expect(fileAudio.volume).toBe(0.1);
    expect(fileAudio.play).toHaveBeenCalledTimes(1);
    expect(loadJsfxr).not.toHaveBeenCalled();
  });

  it("plays an injected file provider without loading jsfxr", async () => {
    const play = vi.fn();
    const fileAudio = { volume: 0, play };
    const loadJsfxr = vi.fn(async () => ({ generate: vi.fn(), play: vi.fn() }));
    const manager = new AudioManager({
      isBrowser: () => true,
      loadJsfxr,
      createFileAudio: vi.fn(() => fileAudio),
      definitions: {
        ...soundDefinitions,
        "ui.click": { category: "ui", cooldownMs: 0, provider: { type: "file", src: "/sounds/click.ogg", volume: 0.2 } },
      },
    });
    manager.unlock();
    manager.play("ui.click");
    await Promise.resolve();
    await Promise.resolve();
    expect(fileAudio.volume).toBe(0.2);
    expect(play).toHaveBeenCalledOnce();
    expect(loadJsfxr).not.toHaveBeenCalled();
  });

  it("does not touch browser or load jsfxr during SSR construction", () => {
    const loadJsfxr = vi.fn(async () => ({ generate: vi.fn(), play: vi.fn() }));
    const manager = new AudioManager({ isBrowser: () => false, loadJsfxr });
    manager.unlock();
    manager.play("battle.damage");
    expect(loadJsfxr).not.toHaveBeenCalled();
  });

  it("lazily unlocks after trusted interaction and generates a sound once", async () => {
    const generate = vi.fn(() => ({ generated: true }));
    const play = vi.fn();
    const loadJsfxr = vi.fn(async () => ({ generate, play }));
    const manager = new AudioManager({ isBrowser: () => true, loadJsfxr });

    manager.play("ui.click");
    expect(loadJsfxr).not.toHaveBeenCalled();
    manager.unlock();
    manager.play("ui.click");
    await Promise.resolve();
    await Promise.resolve();
    expect(loadJsfxr).toHaveBeenCalledTimes(1);
    expect(generate).toHaveBeenCalledTimes(1);
    expect(play).toHaveBeenCalledTimes(1);
  });

  it("quietly tolerates provider load and playback failures", async () => {
    const manager = new AudioManager({
      isBrowser: () => true,
      loadJsfxr: async () => { throw new Error("autoplay blocked"); },
    });
    expect(() => manager.unlock()).not.toThrow();
    expect(() => manager.play("battle.event")).not.toThrow();
    await Promise.resolve();
  });

  it("deduplicates an occurrence while allowing later distinct occurrences", async () => {
    let now = 1000;
    const play = vi.fn();
    const manager = new AudioManager({
      isBrowser: () => true,
      now: () => now,
      loadJsfxr: async () => ({ generate: vi.fn(() => ({})), play }),
    });
    manager.unlock();
    manager.play("battle.damage", { dedupeKey: "event-1" });
    manager.play("battle.damage", { dedupeKey: "event-1" });
    await Promise.resolve();
    await Promise.resolve();
    expect(play).toHaveBeenCalledTimes(1);
    now += 1;
    manager.play("battle.damage", { dedupeKey: "event-2" });
    await Promise.resolve();
    expect(play).toHaveBeenCalledTimes(2);
  });

  it("does not suppress adjacent battle events because battle cues have no cooldown", async () => {
    const play = vi.fn();
    const manager = new AudioManager({
      isBrowser: () => true,
      loadJsfxr: async () => ({ generate: vi.fn(() => ({})), play }),
    });
    manager.unlock();
    manager.play("battle.damage", { dedupeKey: "sequence-10" });
    manager.play("battle.debuff", { dedupeKey: "sequence-11" });
    await Promise.resolve();
    await Promise.resolve();
    expect(play).toHaveBeenCalledTimes(2);
  });
});
