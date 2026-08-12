import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { readFileSync } from "node:fs";
import { TeamBuilder } from "@/components/battle/TeamBuilder";

const roster = [
  ["hero.priest.comprehensiveness", "Aldric", "Priest", "Comprehensiveness"],
  ["hero.paladin.retribution", "Cael", "Paladin", "Retribution"],
  ["hero.mage.comprehensiveness", "Elyra", "Mage", "Comprehensiveness"],
  ["hero.warrior.defence", "Falk", "Warrior", "Defence"],
  ["hero.rogue.comprehensiveness", "Hessa", "Rogue", "Comprehensiveness"],
].map(([definitionId, displayName, faculty, specialization]) => ({
  definitionId,
  displayName,
  faculty,
  specialization,
}));

const css = () => readFileSync("app/globals.css", "utf8").replace(/\s+/g, "");

describe("UI-015 Team Builder vertical-flow contracts", () => {
  it("keeps one bounded vertical scroll area without fixed row compression", () => {
    render(<TeamBuilder roster={roster} onStart={vi.fn()} />);
    const builder = document.querySelector<HTMLElement>(".team-builder");
    expect(builder).toHaveAttribute("tabindex", "0");

    const source = css();
    expect(source).toMatch(/\.team-builder\{[^}]*height:100dvh/);
    expect(source).toMatch(/\.team-builder\{[^}]*min-height:0/);
    expect(source).toMatch(/\.team-builder\{[^}]*overflow-y:auto/);
    expect(source).toMatch(/\.team-builder\{[^}]*overflow-x:hidden/);
    expect(source).toMatch(/\.team-builder\{[^}]*scrollbar-gutter:stable/);
    expect(source).toMatch(/\.team-builder\{[^}]*grid-auto-rows:max-content/);
    expect(source).not.toMatch(/\.team-builder\{[^}]*grid-template-rows:/);
    expect(source).not.toMatch(/\.team-composer\{[^}]*position:(?:absolute|fixed)/);
    expect(source).not.toMatch(/\.hero-selection-matrix\{[^}]*position:(?:absolute|fixed)/);
  });

  it("retains non-compressible hero card floors and places the matrix and action after both teams", () => {
    render(<TeamBuilder roster={roster} onStart={vi.fn()} />);
    const builder = document.querySelector<HTMLElement>(".team-builder")!;
    const ordered = [
      builder.querySelector(".builder-title"),
      builder.querySelector(".current-stage"),
      builder.querySelector(".builder-options"),
      builder.querySelector(".team-composer.friendly"),
      builder.querySelector(".team-composer.enemy"),
      builder.querySelector(".hero-selection-matrix"),
      builder.querySelector(".builder-footer"),
    ];
    expect(ordered.every(Boolean)).toBe(true);
    const childPositions = ordered.map((node) => [...builder.children].indexOf(node!));
    expect(childPositions.every((position, index) => index === 0 || position > childPositions[index - 1])).toBe(true);

    const source = css();
    expect(source).toMatch(/\.player-slot-card\{[^}]*min-height:440px/);
    expect(source).toMatch(/\.enemy-slot-card\{[^}]*min-height:440px/);
    expect(source).toMatch(/\.matrix-hero-card\{[^}]*min-height:360px/);
  });

  it.each([1, 2, 3] as const)("keeps Enter Battle reachable after the matrix for %iv%i", (size) => {
    render(<TeamBuilder roster={roster} onStart={vi.fn()} />);
    const radio = screen.getByRole("radio", { name: `${size}v${size}` });
    if (size !== 1) (radio as HTMLInputElement).click();
    const matrix = document.querySelector(".hero-selection-matrix")!;
    const enter = screen.getByRole("button", { name: "ENTER BATTLE" });
    expect(matrix.compareDocumentPosition(enter) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });
});
