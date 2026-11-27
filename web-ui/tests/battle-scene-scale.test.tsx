import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { BattleScreen } from "@/components/battle/BattleScreen";
import { BATTLE_BACKGROUND, BATTLE_BACKGROUND_DIMENSIONS } from "@/lib/battle/battleBackgrounds";
import { createFormatFixture, MockBattleProvider } from "@/lib/battle/fixture";
import { backgroundCoverScale, battleSceneRate, BATTLE_SCENE_REFERENCE } from "@/lib/battle/sceneScale";

afterEach(() => vi.restoreAllMocks());

describe("battlefield-relative scene scale", () => {
  const image = BATTLE_BACKGROUND_DIMENSIONS[BATTLE_BACKGROUND];
  const referenceField = { width: 1351, height: 560 };

  it("matches the approved windowed reference and uses the cover axis that actually dominates", () => {
    expect(BATTLE_SCENE_REFERENCE.heroRate).toBe(0.7);
    expect(backgroundCoverScale(referenceField, image)).toBeCloseTo(1351 / 1536);
    expect(battleSceneRate(referenceField, image)).toBeCloseTo(0.7);
    expect(backgroundCoverScale({ width: 458, height: 336 }, image)).toBeCloseTo(336 / 1024);
  });

  it("keeps the hero-to-rendered-background ratio constant through resize, cover crop, and background changes", () => {
    for (const art of Object.values(BATTLE_BACKGROUND_DIMENSIONS)) {
      const referenceCover = backgroundCoverScale(referenceField, art);
      for (const field of [
        referenceField,
        { width: 1238, height: 676 },
        { width: 1213, height: 620 },
        { width: 1118, height: 534 },
        { width: 526, height: 336 },
        { width: 427, height: 336 },
      ]) {
        const cover = backgroundCoverScale(field, art);
        expect(battleSceneRate(field, art) / cover).toBeCloseTo(0.7 / referenceCover);
      }
    }
  });

  it("produces one deterministic result for the same battlefield, independent of previous size", () => {
    const target = { width: 1238, height: 676 };
    const first = battleSceneRate(target, image);
    battleSceneRate({ width: 427, height: 336 }, image);
    expect(battleSceneRate(target, image)).toBe(first);
    expect(battleSceneRate({ width: 0, height: 0 }, image)).toBe(0.7);
  });

  it.each([1, 2, 3] as const)("applies one measured scene rate to %dv%d without changing formation multipliers", async (size) => {
    let field = referenceField;
    const original = HTMLElement.prototype.getBoundingClientRect;
    vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function () {
      if (this.classList.contains("battlefield")) return { width: field.width, height: field.height } as DOMRect;
      return original.call(this);
    });
    const { container } = render(<BattleScreen provider={new MockBattleProvider(createFormatFixture(size))} />);
    await screen.findByRole("region", { name: "Battlefield" });
    const shell = container.querySelector<HTMLElement>(".battle-shell")!;
    await waitFor(() => expect(Number(shell.style.getPropertyValue("--battle-scene-rate"))).toBeCloseTo(0.7));
    const formationScales = [...container.querySelectorAll<HTMLElement>(".formation-slot")].map(
      (slot) => slot.style.getPropertyValue("--figure-scale"),
    );

    field = { width: 1238, height: 676 };
    fireEvent(window, new Event("resize"));
    await waitFor(() => expect(Number(shell.style.getPropertyValue("--battle-scene-rate")))
      .toBeCloseTo(battleSceneRate(field, image)));
    expect([...container.querySelectorAll<HTMLElement>(".formation-slot")].map(
      (slot) => slot.style.getPropertyValue("--figure-scale"),
    )).toEqual(formationScales);
  });
});
