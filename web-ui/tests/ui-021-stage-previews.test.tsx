import { render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { describe, expect, it, vi } from "vitest";
import { TeamBuilder } from "@/components/battle/TeamBuilder";
import {
  STAGE_DEFINITIONS,
  resolveEnabledStage,
} from "@/components/stages/stage-config";
import type { HeroDefinitionSummary } from "@/lib/battle/types";

const roster: HeroDefinitionSummary[] = [{
  definitionId: "hero.warrior.weapon_master",
  displayName: "Garran",
  faculty: "Warrior",
  specialization: "Weapon Master",
}];

describe("UI-021 Current Stage preview focus", () => {
  it("keeps preview focus as explicit presentation data, independent from map hotspot geometry", () => {
    const enabled = STAGE_DEFINITIONS.filter((stage) => stage.enabled);
    expect(enabled).toHaveLength(3);
    for (const stage of enabled) {
      expect(stage.previewFocus).toEqual(expect.objectContaining({
        xPercent: expect.any(Number),
        yPercent: expect.any(Number),
        scale: expect.any(Number),
        offsetXPercent: expect.any(Number),
        offsetYPercent: expect.any(Number),
      }));
    }
    expect(resolveEnabledStage("warriors-barrack").previewFocus).toEqual({
      xPercent: 22.8, yPercent: 23.5, scale: 1.85, offsetXPercent: 72, offsetYPercent: 53,
    });
    expect(resolveEnabledStage("paladins-altar").previewFocus).toEqual({
      xPercent: 87.2, yPercent: 43.2, scale: 1.85, offsetXPercent: -46, offsetYPercent: 16,
    });
  });

  it.each([
    ["arena", "Arena", "50% 51.5%", "1.85", "0%", "0%"],
    ["warriors-barrack", "Warrior's Barrack", "22.8% 23.5%", "1.85", "72%", "53%"],
    ["paladins-altar", "Paladin's Altar", "87.2% 43.2%", "1.85", "-46%", "16%"],
  ] as const)("renders the %s preview using its own landmark focus", (stageId, name, position, scale, offsetX, offsetY) => {
    render(<TeamBuilder roster={roster} selectedStageId={stageId} onStart={vi.fn()} />);

    expect(screen.getByRole("heading", { name })).toBeVisible();
    const image = document.querySelector<HTMLElement>(".current-stage-map")!;
    expect(image).toHaveStyle({ objectPosition: position });
    expect(image.style.getPropertyValue("--stage-preview-scale")).toBe(scale);
    expect(image.style.getPropertyValue("--stage-preview-offset-x")).toBe(offsetX);
    expect(image.style.getPropertyValue("--stage-preview-offset-y")).toBe(offsetY);
  });

  it("uses the presentation metadata in desktop and narrow responsive crop CSS", () => {
    const css = readFileSync("app/globals.css", "utf8").replace(/\s+/g, "");
    expect(css).toMatch(/\.current-stage-map\{[^}]*scale\(var\(--stage-preview-scale\)\)/);
    expect(css).toMatch(/\.current-stage-map\{[^}]*translate\(var\(--stage-preview-offset-x\),var\(--stage-preview-offset-y\)\)/);
    expect(css).toContain("@media(max-width:720px){.current-stage");
  });
});
