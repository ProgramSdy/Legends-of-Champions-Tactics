import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { BattleScreen } from "@/components/battle/BattleScreen";
import { TeamBuilder } from "@/components/battle/TeamBuilder";
import { createFormatFixture, MockBattleProvider } from "@/lib/battle/fixture";
import { formationRegistry } from "@/lib/battle/formations";
import type { BattleEvent, BattleSize, HeroDefinitionSummary } from "@/lib/battle/types";
import { readFileSync } from "node:fs";

const roster: HeroDefinitionSummary[] = [
  { definitionId: "hero.one", displayName: "Definition Name", faculty: "Faculty", specialization: "Major" },
  { definitionId: "hero.two", displayName: "Another Definition", faculty: "Other Faculty", specialization: "Minor" },
];

describe("UI-007 battlefield geometry contracts", () => {
  it.each([[1], [2], [3]] as const)("keeps shared figure footprint hooks for size %d formations", async (size) => {
    render(<BattleScreen provider={new MockBattleProvider(createFormatFixture(size))} />);
    const battlefield = await screen.findByRole("region", { name: "Battlefield" });
    expect(battlefield.closest("main")).toHaveAttribute("data-format", ["duel", "duo", "trio"][size - 1]);
    const figures = battlefield.querySelectorAll<HTMLElement>(".battle-figure");
    expect(figures.length).toBe(size * 2);
    figures.forEach((figure) => {
      expect(figure).toHaveAttribute("data-combatant-id");
      expect(figure).toHaveAttribute("data-figure-footprint", "shared");
      const footprint = figure.querySelector(".figure-footprint");
      expect(footprint).toBeInTheDocument();
      expect(footprint?.querySelector(".figure-aura")).toBeInTheDocument();
      expect(figure.querySelector(".figure-art")).toBeInTheDocument();
      // Overhead remains a child of the same figure so health/status cues do
      // not drift into a format-wide overlay as formations change.
      expect(figure.querySelector(".overhead")).toBeInTheDocument();
      expect(figure.querySelector(".figure-name")).not.toBeInTheDocument();
      const heroName = figure.querySelector(".battle-target-control")?.getAttribute("aria-label")?.split(",")[0];
      expect(figure.querySelector(".overhead")).toHaveTextContent(heroName ?? "");
    });
  });

  it("uses the doubled logical footprint and preserves footing/clearance CSS hooks", () => {
    // Normalize formatting so this contract checks geometry values rather than
    // a particular CSS minification/line-break style.
    const css = readFileSync("app/globals.css", "utf8").replace(/\s+/g, "");
    const footprint = css.match(/\.figure-footprint\{([^}]*)\}/)?.[1] ?? "";
    const aura = css.match(/\.figure-aura\{([^}]*)\}/)?.[1] ?? "";
    const overhead = css.match(/\.overhead\{([^}]*)\}/)?.[1] ?? "";

    expect(footprint).toMatch(/(?:^|;)width:172px(?:;|$)/);
    expect(footprint).toMatch(/(?:^|;)height:var\(--figure-frame-height\)(?:;|$)/);
    expect(footprint).toMatch(/(?:^|;)bottom:17px(?:;|$)/);
    expect(aura).toMatch(/(?:^|;)bottom:-12px(?:;|$)/);
    expect(aura).toMatch(/(?:^|;)left:50%(?:;|$)/);
    // Overhead is positioned from the measured frame, footprint baseline, and
    // the required 12px clearance in scaled formation coordinates.
    expect(overhead).toMatch(/(?:^|;)bottom:calc\(\(var\(--figure-frame-height\)\+17px\)\*var\(--figure-scale\)\+12px\)(?:;|$)/);
    expect(overhead).toMatch(/(?:^|;)left:59px(?:;|$)/);
    const duelOverhead = css.match(/\.format-duel\.overhead\{([^}]*)\}/)?.[1] ?? "";
    expect(duelOverhead).toMatch(/(?:^|;)transform:scale\(1\.5\)(?:;|$)/);
    expect(duelOverhead).toMatch(/(?:^|;)transform-origin:centerbottom(?:;|$)/);
  });

  it("fills the dynamic frame for fallback figures while preserving image containment", () => {
    const css = readFileSync("app/globals.css", "utf8").replace(/\s+/g, "");
    const fallback = css.match(/\.figure-art\.asset-fallback\{([^}]*)\}/)?.[1] ?? "";
    const finalImage = css.match(/img\.figure-art\.fallback-requested\{([^}]*)\}/)?.[1] ?? "";

    // Fallback silhouettes fill the measured frame and use the default
    // 202px metric when no intrinsic dimensions are available.
    expect(fallback).toMatch(/(?:^|;)height:100%(?:;|$)/);
    expect(fallback).toMatch(/(?:^|;)inset:0(?:;|$)/);

    // Real figure images continue to preserve their source proportions.
    expect(finalImage).toMatch(/(?:^|;)object-fit:contain(?:;|$)/);
    expect(finalImage).toMatch(/(?:^|;)object-position:centerbottom(?:;|$)/);
  });

  it("derives the figure frame from loaded artwork dimensions", async () => {
    const { container } = render(<BattleScreen provider={new MockBattleProvider(createFormatFixture(1))} />);
    await screen.findByRole("region", { name: "Battlefield" });
    const figure = container.querySelector<HTMLElement>(".battle-figure")!;
    const image = figure.querySelector<HTMLImageElement>("img.figure-art.fallback-requested")!;
    Object.defineProperty(image, "naturalWidth", { configurable: true, value: 1200 });
    Object.defineProperty(image, "naturalHeight", { configurable: true, value: 1800 });

    fireEvent.load(image);
    await waitFor(() => expect(figure.style.getPropertyValue("--figure-frame-height")).toBe("258px"));
    // The image is bottom anchored in the shared footprint; only its frame
    // height changes when intrinsic dimensions become available.
    expect(figure.querySelector(".figure-footprint")).toBeInTheDocument();
    expect(figure.querySelector(".overhead")).toBeInTheDocument();
  });

  it("retains the fallback frame metric after a missing figure errors", async () => {
    const { container } = render(<BattleScreen provider={new MockBattleProvider(createFormatFixture(1))} />);
    await screen.findByRole("region", { name: "Battlefield" });
    const figure = container.querySelector<HTMLElement>(".battle-figure")!;
    const image = figure.querySelector<HTMLImageElement>("img.figure-art.fallback-requested")!;
    fireEvent.error(image);

    await waitFor(() => expect(figure.querySelector(".asset-fallback.figure-art")).toBeInTheDocument());
    expect(figure.style.getPropertyValue("--figure-frame-height")).toBe("202px");
  });

  it("keeps overhead clearance dynamic while preserving footing and enemy mirroring", () => {
    const css = readFileSync("app/globals.css", "utf8").replace(/\s+/g, "");
    const overhead = css.match(/\.overhead\{([^}]*)\}/)?.[1] ?? "";
    expect(overhead).toMatch(/(?:^|;)bottom:calc\(\(var\(--figure-frame-height\)\+17px\)\*var\(--figure-scale\)\+12px\)(?:;|$)/);
    const targetControl = css.match(/\.battle-target-control\{([^}]*)\}/)?.[1] ?? "";
    expect(targetControl).toMatch(/(?:^|;)height:calc\(var\(--figure-frame-height\)\+48px\)(?:;|$)/);
    const footprint = css.match(/\.figure-footprint\{([^}]*)\}/)?.[1] ?? "";
    expect(footprint).toMatch(/(?:^|;)bottom:17px(?:;|$)/);
    expect(css).toMatch(/\.battle-figure\.enemyimg\.figure-art\.fallback-requested\{[^}]*transform:scaleX\(-1\)/);
  });

  it("keeps aura ownership and active animation side-aware", () => {
    const css = readFileSync("app/globals.css", "utf8").replace(/\s+/g, "");
    expect(css).toMatch(/\.figure-aura\{[^}]*background:#2584ff2e/);
    expect(css).toMatch(/\.enemy\.figure-aura\{[^}]*background:#e3403025/);
    expect(css).toMatch(/\.battle-figure\.acting\.figure-aura\{[^}]*animation:pulse-centered/);
  });

  it("layers front formation figures above rear figures in duo and trio", async () => {
    const css = readFileSync("app/globals.css", "utf8").replace(/\s+/g, "");
    const zIndex = (slot: string) => Number(css.match(new RegExp(`\\.formation-slot\\[data-slot=${slot}\\]\\{[^}]*z-index:(\\d+)`))?.[1]);
    expect(zIndex("front")).toBeGreaterThan(zIndex("rear"));
    for (const size of [2, 3] as const) {
      const { container } = render(<BattleScreen provider={new MockBattleProvider(createFormatFixture(size))} />);
      await screen.findByRole("region", { name: "Battlefield" });
      expect(container.querySelectorAll(`.formation-slot[data-slot="front"]`)).toHaveLength(2);
      expect(container.querySelectorAll(`.formation-slot[data-slot="rear"]`)).toHaveLength(2);
    }
  });

  it("keeps formation slots distinct and aligned to a common figure baseline", () => {
    for (const format of ["duel", "duo", "trio"] as const) {
      const friendly = formationRegistry[format].friendly;
      const enemy = formationRegistry[format].enemy;
      expect(new Set([...friendly, ...enemy].map(({ x, y }) => `${x}:${y}`)).size).toBe(friendly.length + enemy.length);
      if (format === "duel") {
        expect(friendly[0].y).toBe(enemy[0].y);
        expect(friendly[0].scale).toBe(1.5);
        expect(enemy[0].scale).toBe(1.5);
      }
    }
  });
});

describe("UI-007 target-bound battle effects", () => {
  async function renderDemos() {
    const provider = new MockBattleProvider();
    render(<BattleScreen provider={provider} mockDemos={[
      { id: "healing", label: "Healing", run: () => provider.runDemo("healing") },
      { id: "status", label: "Debuff", run: () => provider.runDemo("status") },
    ]} />);
    await screen.findByRole("region", { name: "Battlefield" });
    fireEvent.click(screen.getByRole("button", { name: "×2" }));
    return { provider };
  }

  it("anchors healing to the friendly recipient rather than a global layer", async () => {
    await renderDemos();
    fireEvent.click(screen.getByRole("button", { name: "Healing" }));
    await waitFor(() => expect(document.querySelector("[data-combatant-id='friendly.arthas'] .target-effect.effect-healing")).toBeInTheDocument());
    const figure = document.querySelector("[data-combatant-id='friendly.arthas']")!;
    expect(figure).toHaveAttribute("data-combatant-id", "friendly.arthas");
    expect(document.querySelector(".effect-layer")).toBeNull();
  });

  it("plays the healing target effect without misleading +0 text at full HP", async () => {
    const provider = new MockBattleProvider();
    const snapshot = (await provider.getState()).snapshot;
    const target = snapshot.combatants["friendly.arthas"];
    target.hp.current = target.hp.maximum;
    const healingEvent = {
      id: "evt.full-hp-heal", sequence: 1, type: "healingApplied", sourceId: "friendly.arthas",
      targetId: "friendly.arthas", amount: 0, hpAfter: { ...target.hp }, effectHint: "healing",
      message: "Arthas is already at full health.",
    } satisfies BattleEvent;
    render(<BattleScreen provider={provider} mockDemos={[{
      id: "full-hp-heal", label: "Full HP healing", run: async () => ({
        id: "full-hp-heal", label: "Full HP healing", eventType: "healing",
        events: [healingEvent], snapshot, revision: 2,
      }),
    }]} />);
    await screen.findByRole("region", { name: "Battlefield" });
    fireEvent.click(screen.getByRole("button", { name: "×2" }));
    fireEvent.click(screen.getByRole("button", { name: "Full HP healing" }));

    await waitFor(() => expect(document.querySelector("[data-combatant-id='friendly.arthas'] .target-effect.effect-healing")).toBeInTheDocument());
    expect(screen.queryByText("+0")).not.toBeInTheDocument();
  });

  it("anchors a harmful status as a red debuff effect to the enemy target", async () => {
    await renderDemos();
    fireEvent.click(screen.getByRole("button", { name: "Debuff" }));
    await waitFor(() => expect(document.querySelector("[data-combatant-id='enemy.sashein'] .target-effect.effect-debuff")).toBeInTheDocument());
    const figure = document.querySelector("[data-combatant-id='enemy.sashein']")!;
    expect(figure).toHaveAttribute("data-combatant-id", "enemy.sashein");
    expect(figure.querySelector(".target-effect.effect-debuff")).toHaveClass("red");
  });

  it("renders an authoritative beneficial status cue as a blue buff on its recipient", async () => {
    const provider = new MockBattleProvider();
    const snapshot = (await provider.getState()).snapshot;
    const buffEvent = {
      id: "evt.buff", sequence: 1, type: "statusApplied", sourceId: "enemy.sashein",
      targetId: "friendly.arthas", statusId: "status.arcane_guard", roundsRemaining: 2,
      statusPresentation: "buff", effectHint: "status", message: "Arcane Guard strengthens Arthas.",
    } as BattleEvent & { statusPresentation: "buff" };
    render(<BattleScreen provider={provider} mockDemos={[{
      id: "buff", label: "Buff", run: async () => ({ id: "buff", label: "Buff", eventType: "status", events: [buffEvent], snapshot, revision: 2 }),
    }]} />);
    await screen.findByRole("region", { name: "Battlefield" });
    fireEvent.click(screen.getByRole("button", { name: "×2" }));
    fireEvent.click(screen.getByRole("button", { name: "Buff" }));
    await waitFor(() => expect(document.querySelector("[data-combatant-id='friendly.arthas'] .target-effect.effect-buff")).toBeInTheDocument());
    expect(document.querySelector("[data-combatant-id='friendly.arthas'] .target-effect.effect-buff")).toHaveClass("blue");
  });

  it.each([
    [2, "friendly.black_heart", "debuff"],
    [2, "enemy.andonidas", "buff"],
    [3, "friendly.arthas", "debuff"],
    [3, "enemy.sashein", "buff"],
  ] as const)("anchors %s effect to %s in supported formations", async (size: BattleSize, targetId: string, presentation: "buff" | "debuff") => {
    const provider = new MockBattleProvider(createFormatFixture(size));
    const snapshot = (await provider.getState()).snapshot;
    const event = {
      id: `evt.${size}.${targetId}.${presentation}`, sequence: 1, type: "statusApplied",
      sourceId: targetId.startsWith("friendly") ? "enemy.nighthawk" : "friendly.ragnar", targetId,
      statusId: presentation === "buff" ? "status.arcane_guard" : "status.stitch_of_agony",
      roundsRemaining: 2, statusPresentation: presentation, effectHint: "status",
      message: `${presentation} applied to ${targetId}`,
    } satisfies BattleEvent;
    render(<BattleScreen provider={provider} mockDemos={[{
      id: "target-effect", label: "Target effect", run: async () => ({ id: "target-effect", label: "Target effect", eventType: "status", events: [event], snapshot, revision: 2 }),
    }]} />);
    await screen.findByRole("region", { name: "Battlefield" });
    fireEvent.click(screen.getByRole("button", { name: "×2" }));
    fireEvent.click(screen.getByRole("button", { name: "Target effect" }));
    await waitFor(() => expect(document.querySelector(`[data-combatant-id='${targetId}'] .target-effect.effect-${presentation}`)).toBeInTheDocument());
  });

  it.each([
    ["friendly.ragnar", "enemy.nighthawk", "lunge-friendly"],
    ["enemy.nighthawk", "friendly.ragnar", "lunge-enemy"],
  ] as const)("applies side-aware movement class for %s attacker", async (sourceId, targetId, movementClass) => {
    const provider = new MockBattleProvider(createFormatFixture(1));
    const snapshot = (await provider.getState()).snapshot;
    const event = {
      id: `evt.lunge.${sourceId}`, sequence: 1, type: "characterMoved", sourceId, targetId,
      movement: "lunge", effectHint: "melee", message: `${sourceId} lunges.`,
    } satisfies BattleEvent;
    render(<BattleScreen provider={provider} mockDemos={[{
      id: "lunge", label: "Lunge", run: async () => ({ id: "lunge", label: "Lunge", eventType: "melee", events: [event], snapshot, revision: 2 }),
    }]} />);
    await screen.findByRole("region", { name: "Battlefield" });
    fireEvent.click(screen.getByRole("button", { name: "×2" }));
    fireEvent.click(screen.getByRole("button", { name: "Lunge" }));
    await waitFor(() => expect(document.querySelector(`[data-combatant-id='${sourceId}']`)).toHaveClass("movement-lunge", movementClass));
  });

  it("derives lunge direction from the acting side", () => {
    const css = readFileSync("app/globals.css", "utf8");
    expect(css).toMatch(/\.movement-lunge\.lunge-friendly[^}]*animation:[^;]*lunge-friendly/);
    expect(css).toMatch(/\.movement-lunge\.lunge-enemy[^}]*animation:[^;]*lunge-enemy/);
  });
});

describe("UI-007 builder identity and scrolling contracts", () => {
  it("uses Faculty - Major labels for specified enemy selections", () => {
    render(<TeamBuilder roster={roster} onStart={() => undefined} />);
    fireEvent.click(screen.getByRole("radio", { name: "Choose team" }));
    const enemy = screen.getByLabelText("Hero 1");
    expect(within(enemy).getAllByRole("option").map((option) => option.textContent)).toEqual([
      "Choose a hero", "Faculty · Major", "Other Faculty · Minor",
    ]);
    expect(within(enemy).getAllByRole("option").map((option) => option.textContent)).toContain("Faculty · Major");
  });

  it("exposes explicit desktop overflow containers for keyboard and gutter scrolling", () => {
    render(<TeamBuilder roster={roster} onStart={() => undefined} />);
    expect(document.querySelector(".team-builder")).toHaveAttribute("tabindex", "0");
    const css = readFileSync("app/globals.css", "utf8");
    expect(css).toMatch(/\.team-builder\{[^}]*overflow-y:auto/);
    expect(css).toMatch(/\.team-builder\{[^}]*scrollbar-gutter:stable/);
    expect(css).toMatch(/\.gallery-shell\{[^}]*overflow-y:auto/);
    expect(css).toMatch(/\.gallery-shell\{[^}]*scrollbar-gutter:stable/);
  });
});
