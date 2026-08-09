import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { describe, expect, it, vi } from "vitest";
import { BattleScreen } from "@/components/battle/BattleScreen";
import { SkillCard } from "@/components/battle/SkillCard";
import { TeamBuilder } from "@/components/battle/TeamBuilder";
import { createFormatFixture, MockBattleProvider } from "@/lib/battle/fixture";
import { formationRegistry } from "@/lib/battle/formations";
import type { BattleEvent, HeroDefinitionSummary } from "@/lib/battle/types";

const roster: HeroDefinitionSummary[] = [
  { definitionId: "hero.paladin.protection", displayName: "Bastion", faculty: "Paladin", specialization: "Protection" },
  { definitionId: "hero.warrior.weapon_master", displayName: "Ragnar", faculty: "Warrior", specialization: "Weapon Master" },
];

describe("UI-006 identity presentation", () => {
  it("shows faculty and specialization on friendly and enemy side cards", async () => {
    render(<BattleScreen provider={new MockBattleProvider(createFormatFixture(1))} />);

    const friendly = await screen.findByRole("article", { name: /Ragnar/i });
    const enemy = screen.getByRole("article", { name: /Nighthawk/i });
    expect(friendly).toHaveTextContent("Warrior · Weapon Master");
    expect(enemy).toHaveTextContent("Rogue · Comprehensiveness");
  });

  it("shows faculty and specialization on the visual player slot", () => {
    render(<TeamBuilder roster={roster} onStart={vi.fn()} />);

    const player = screen.getByRole("button", { name: "Hero 1: Paladin · Protection" });
    expect(player).not.toHaveTextContent("Bastion");
    expect(player).toHaveTextContent(/Paladin\s*Protection/);
  });
});

describe("UI-006 engine-authored battle log", () => {
  it("renders ordered engine prose once, hides generic semantic copy, auto-follows, and clears", async () => {
    const originalScrollHeight = Object.getOwnPropertyDescriptor(HTMLElement.prototype, "scrollHeight");
    Object.defineProperty(HTMLElement.prototype, "scrollHeight", { configurable: true, get: () => 640 });
    const snapshot = createFormatFixture(1);
    const events: BattleEvent[] = [
      {
        id: "event.3", sequence: 3, type: "damageApplied", sourceId: "friendly.ragnar",
        targetId: "enemy.nighthawk", amount: 9, hpAfter: { current: 75, maximum: 84 },
        message: "enemy.nighthawk took 9 damage.", visibleInLog: false,
      },
      {
        id: "event.2", sequence: 2, type: "battleLog", channel: "battleInfo",
        message: "Nighthawk takes 9 damage from Ragnar's strike.",
      },
      {
        id: "event.1", sequence: 1, type: "battleLog", channel: "battleInfo",
        message: "Ragnar attacks Nighthawk with Fatal Strike.",
      },
    ];
    const provider = new MockBattleProvider(snapshot);
    vi.spyOn(provider, "getState").mockResolvedValue({ revision: 1, snapshot, events });
    render(<BattleScreen provider={provider} />);

    const log = await screen.findByRole("list", { name: "Battle events" });
    const first = await screen.findByText("Ragnar attacks Nighthawk with Fatal Strike.");
    const second = screen.getByText("Nighthawk takes 9 damage from Ragnar's strike.");
    expect(first.compareDocumentPosition(second) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(screen.getAllByText("Ragnar attacks Nighthawk with Fatal Strike.")).toHaveLength(1);
    expect(screen.queryByText("enemy.nighthawk took 9 damage.")).not.toBeInTheDocument();
    await waitFor(() => expect(log.scrollTop).toBe(640));

    fireEvent.click(screen.getByRole("button", { name: "Clear" }));
    expect(within(log).queryAllByRole("listitem")).toHaveLength(0);
    if (originalScrollHeight) Object.defineProperty(HTMLElement.prototype, "scrollHeight", originalScrollHeight);
    else delete (HTMLElement.prototype as unknown as { scrollHeight?: number }).scrollHeight;
  });
});

describe("UI-006 grounded formations and skill hierarchy", () => {
  it("moves every supported formation slot below its former vertical coordinate", () => {
    const former = {
      duel: [45],
      duo: [40, 54],
      trio: [37, 48, 59],
    } as const;

    for (const format of ["duel", "duo", "trio"] as const) {
      for (const side of ["friendly", "enemy"] as const) {
        const positions = formationRegistry[format][side];
        expect(new Set(positions.map(({ x, y }) => `${x}:${y}`)).size).toBe(positions.length);
        positions.forEach((position, index) => {
          expect(position.y).toBeGreaterThan(former[format][index]);
        });
      }
    }
  });

  it("keeps a square icon and complete accessible skill information in the expanded card", () => {
    const { container } = render(
      <SkillCard
        skill={{
          id: "skill.test", displayName: "Shield Test", description: "A structured test skill.",
          targetMode: "singleEnemy", maximumTargets: 1, cooldownRemaining: 0,
          available: true, unavailableReason: null, resourceCost: null,
        }}
        selected={false}
        legal
        disabled={false}
        onSelect={vi.fn()}
      />,
    );

    const card = screen.getByRole("button", { name: /Shield Test/i });
    expect(card).toHaveAccessibleDescription("A structured test skill.");
    expect(card.querySelector(".skill-glyph")).toHaveAttribute("aria-hidden", "true");
    expect(card).toHaveTextContent("single Enemy");
    expect(card).toHaveTextContent("Ready");
    expect(container.querySelectorAll(".skill-glyph")).toHaveLength(1);
  });

  it("styles logs above the former 9px size and lets cards fill while icons stay square", () => {
    const css = readFileSync("app/globals.css", "utf8");
    const logRule = css.match(/\.battle-log ol\{[^}]*font-size:([0-9.]+)px/);
    expect(Number(logRule?.[1])).toBeGreaterThan(9);
    expect(css).toMatch(/\.skill-card\{[^}]*height:100%/);
    expect(css).toMatch(/\.skill-glyph\{[^}]*aspect-ratio:1(?:\s*\/\s*1)?/);
  });
});
