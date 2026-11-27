import { readFileSync } from "node:fs";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { BattleScreen } from "@/components/battle/BattleScreen";
import { createFormatFixture, MockBattleProvider } from "@/lib/battle/fixture";
import { duoFormationRegistry, formationRegistry, trioFormationRegistry } from "@/lib/battle/formations";

describe("BUG-005 battle layout", () => {
  it("moves both 1v1 foot anchors to the existing 2v2 Front/Rear ground line only", () => {
    for (const [side, x] of [["friendly", 29], ["enemy", 71]] as const) {
      expect(formationRegistry.duel[side][0]).toMatchObject({
        slot: "centre",
        x,
        y: duoFormationRegistry["front-rear"][side][0].y,
        scale: 1.5,
      });
      expect(duoFormationRegistry["front-rear"][side].map(({ y }) => y)).toEqual([68, 68]);
    }
    expect(formationRegistry.duo.friendly).toBe(duoFormationRegistry["front-rear"].friendly);
    expect(formationRegistry.trio.enemy).toBe(trioFormationRegistry["one-front-two-rear"].enemy);
  });

  it("keeps the full name in the Acting Hero markup and provides a wrapping layout", async () => {
    const snapshot = createFormatFixture(1);
    snapshot.combatants[snapshot.activeCombatantId!].displayName = "Seraphina Dawnbringer";
    const { container } = render(<BattleScreen provider={new MockBattleProvider(snapshot)} />);
    await screen.findByRole("region", { name: "Battlefield" });
    expect(container.querySelector(".acting-card h2")).toHaveTextContent("Seraphina Dawnbringer");

    const css = readFileSync("app/globals.css", "utf8").replace(/\s+/g, "");
    expect(css).toContain(".acting-card{position:relative;display:grid;grid-template-columns:92pxminmax(0,1fr)");
    expect(css).toContain(".acting-cardh2{font:60020px/1.1Georgia,serif;margin:4px0;overflow-wrap:anywhere}");
    expect(css).toContain(".skills{display:grid;grid-template-columns:repeat(4,minmax(0,1fr))");
    expect(css).toContain('.battle-shell[data-presentation-mode="phone"].acting-card{grid-template-columns:minmax(0,1fr);');
  });
});
