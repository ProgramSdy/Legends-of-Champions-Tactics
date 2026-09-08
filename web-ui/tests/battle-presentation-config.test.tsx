import { readFileSync } from "node:fs";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { BattleScreen } from "@/components/battle/BattleScreen";
import { MockBattleProvider } from "@/lib/battle/fixture";
import { battlePresentationConfigFor } from "@/lib/battle/presentationConfig";

describe("battle presentation configuration", () => {
  it.each([
    [{ width: 1920, height: 1080 }, "monitor", 1],
    [{ width: 1440, height: 900 }, "laptop-large", 0.7],
    [{ width: 1280, height: 720 }, "laptop-medium", 0.6],
    [{ width: 1024, height: 768 }, "pad", 0.5],
    [{ width: 800, height: 600 }, "pad-mini", 0.84],
    [{ width: 844, height: 390 }, "phone", 0.4],
  ] as const)("maps %o to %s", (viewport, mode, browserSizeRate) => {
    expect(battlePresentationConfigFor(viewport)).toMatchObject({
      mode,
      browserSizeRate,
      orientation: "landscape",
      viewport,
    });
  });

  it("distinguishes a short wide screen and reserves portrait for a rotate-device state", () => {
    expect(battlePresentationConfigFor({ width: 1920, height: 700 })).toMatchObject({
      mode: "laptop-medium", browserSizeRate: 0.6,
    });
    expect(battlePresentationConfigFor({ width: 390, height: 844 })).toMatchObject({
      mode: "portrait", orientation: "portrait",
    });
  });

  it("keeps browser scaling at the figure boundary and leaves formation positions untouched", () => {
    const battleScreen = readFileSync("components/battle/BattleScreen.tsx", "utf8");
    const css = readFileSync("app/globals.css", "utf8").replace(/\s+/g, "");

    expect(battleScreen).toContain('style={{ "--browser-size-rate": presentationConfig.browserSizeRate } as CSSProperties}');
    expect(battleScreen).toContain('style={{ left: `${position.x}%`, top: `${position.y}%`, zIndex: position.depth, "--figure-scale": position.scale } as CSSProperties}');
    expect(css).toContain('scale(calc(var(--figure-scale)*var(--browser-size-rate)))');
    expect(css).toContain('bottom:calc((var(--figure-frame-height)+17px)*var(--figure-scale)*var(--browser-size-rate)+12px)');
  });

  it("marks the existing battlefield ownership boundaries without adding a page-scale canvas", () => {
    const battleScreen = readFileSync("components/battle/BattleScreen.tsx", "utf8");
    expect(battleScreen).toContain('data-battle-layer-context="world"');
    expect(battleScreen).toContain('data-battle-layer="combat-actor"');
    expect(battleScreen).toContain('data-battle-layer="combat-vfx"');
    expect(battleScreen).toContain('data-battle-layer="world-ui"');
  });

  it("keeps the battlefield non-scrolling without a broad minimum-width canvas", () => {
    const css = readFileSync("app/globals.css", "utf8").replace(/\s+/g, "");
    expect(css).toContain('.battle-shell{--browser-size-rate:1;');
    expect(css).toContain('min-width:0;overflow:hidden;display:grid;');
    expect(css).toContain('.battle-shell[data-presentation-mode="phone"]');
  });

  it("reduces only Laptop Large side panels, acting column, and command-deck height", () => {
    const css = readFileSync("app/globals.css", "utf8").replace(/\s+/g, "");
    expect(css).toContain('.battle-shell[data-presentation-mode="laptop-large"]{--battle-side-panel-width:calc(var(--battle-side-panel-base-width)*.8);--battle-command-deck-height:calc(var(--battle-command-deck-base-height)*.75);--battle-command-acting-width:calc(var(--battle-command-acting-base-width)*.75)}');
  });

  it("uses explicit Monitor-only three-pixel HUD font adjustments", () => {
    const css = readFileSync("app/globals.css", "utf8");
    expect(css).not.toContain("battle-hud-font-increase");
    expect(css).toContain('.battle-shell[data-presentation-mode="monitor"] .team-panel > header { font-size: 15px; }');
    expect(css).toContain('.battle-shell[data-presentation-mode="monitor"] .acting-card h2 { font-size: 23px; }');
    expect(css).toContain('.battle-shell[data-presentation-mode="monitor"] .battle-log ol { font-size: 14px; }');
    expect(css).toContain('.battle-shell[data-presentation-mode="monitor"] .battle-viewport-readout strong { font-size: 14px; }');
  });

  it("increases only the Monitor header height by fifty percent from its active responsive base", () => {
    const css = readFileSync("app/globals.css", "utf8").replace(/\s+/g, "");
    expect(css).toContain('--battle-header-base-height:82px;--battle-header-height:var(--battle-header-base-height);');
    expect(css).toContain('grid-template-rows:var(--battle-header-height)minmax(0,1fr)var(--battle-command-deck-height)55px;');
    expect(css).toContain('.battle-shell[data-presentation-mode="monitor"]{--battle-header-height:calc(var(--battle-header-base-height)*1.5)}');
  });

  it("rearranges only Monitor header content for the taller header row", () => {
    const css = readFileSync("app/globals.css", "utf8");
    expect(css).toContain('.battle-shell[data-presentation-mode="monitor"] .battle-header { grid-template-columns: 120px 1fr 300px 1fr 120px; align-items: center; }');
    expect(css).toContain('.battle-shell[data-presentation-mode="monitor"] .side-banner { height: 80px; gap: 18px; padding: 0 32px; }');
    expect(css).toContain('.battle-shell[data-presentation-mode="monitor"] .round { height: 100px; padding-top: 16px; }');
    expect(css).toContain('.battle-shell[data-presentation-mode="monitor"] .turn-order { top: 92px; gap: 5px; padding: 8px 18px 9px; }');
  });

  it("mirrors the damage reaction for enemy figures", () => {
    const css = readFileSync("app/globals.css", "utf8").replace(/\s+/g, "");
    expect(css).toContain('.battle-figure.friendly.fx-damageApplied{animation:target-shake-friendly.35s}');
    expect(css).toContain('.battle-figure.enemy.fx-damageApplied{animation:target-shake-enemy.35s}');
    expect(css).toContain('@keyframestarget-shake-friendly{25%{transform:translateX(-7px)}60%{transform:translateX(6px)}}');
    expect(css).toContain('@keyframestarget-shake-enemy{25%{transform:translateX(7px)}60%{transform:translateX(-6px)}}');
  });


  it("shows the live browser dimensions and active configuration in the battlefield readout", async () => {
    render(<BattleScreen provider={new MockBattleProvider()} />);
    const readout = await screen.findByLabelText("Battle viewport configuration");
    expect(readout).toHaveTextContent(`${window.innerWidth} × ${window.innerHeight}`);
    expect(readout).toHaveTextContent(battlePresentationConfigFor({ width: window.innerWidth, height: window.innerHeight }).mode.replaceAll("-", " ").toUpperCase());
  });

  it("omits Team Bond from both battle team panels at every viewport", async () => {
    render(<BattleScreen provider={new MockBattleProvider()} />);
    await screen.findByLabelText("Your team");
    expect(screen.queryByText("TEAM BOND")).not.toBeInTheDocument();
    expect(document.querySelectorAll(".team-bonus")).toHaveLength(0);
  });
});
