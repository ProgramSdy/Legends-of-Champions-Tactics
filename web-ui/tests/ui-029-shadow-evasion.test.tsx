import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { BattleScreen } from "@/components/battle/BattleScreen";
import { createFormatFixture, MockBattleProvider } from "@/lib/battle/fixture";

const shadowStatus = (sourceCombatantId: string) => ({
  id: "status.shadow_evasion",
  instanceId: "status.shadow_evasion.test",
  kind: "buff" as const,
  roundsRemaining: 1,
  stacks: null,
  sourceCombatantId,
});

describe("UI-029 Shadow Evasion battlefield presentation", () => {
  it("fades only an active friendly Rogue and restores it when the status leaves the snapshot", async () => {
    const snapshot = createFormatFixture(1);
    const rogue = snapshot.combatants["friendly.ragnar"];
    rogue.definitionId = "hero.rogue.comprehensiveness";
    rogue.faculty = "Rogue";
    rogue.specialization = "Comprehensiveness";
    rogue.statuses = [shadowStatus(rogue.id)];
    const view = render(<BattleScreen provider={new MockBattleProvider(snapshot)} />);
    await screen.findByRole("region", { name: "Battlefield" });

    const figure = document.querySelector(".battle-figure[data-combatant-id='friendly.ragnar']")!;
    expect(figure).toHaveClass("shadow-evasion-active");
    expect(figure).toHaveAttribute("data-shadow-evasion", "active");
    expect(figure.querySelector(".figure-art")).toBeInTheDocument();
    expect(document.querySelector(".team-panel .shadow-evasion-active")).not.toBeInTheDocument();

    const cleared = structuredClone(snapshot);
    cleared.combatants["friendly.ragnar"].statuses = [];
    view.unmount();
    render(<BattleScreen provider={new MockBattleProvider(cleared)} />);
    await screen.findByRole("region", { name: "Battlefield" });
    const restored = document.querySelector(".battle-figure[data-combatant-id='friendly.ragnar']")!;
    expect(restored).not.toHaveClass("shadow-evasion-active");
    expect(restored).not.toHaveAttribute("data-shadow-evasion");
  });

  it("fades an enemy Rogue in a 2v2 battle while preserving status icon and target control", async () => {
    const snapshot = createFormatFixture(2);
    const enemy = snapshot.combatants["enemy.nighthawk"];
    enemy.statuses = [shadowStatus(enemy.id)];
    const provider = new MockBattleProvider(snapshot);
    render(<BattleScreen provider={provider} />);
    await screen.findByRole("region", { name: "Battlefield" });

    const figure = document.querySelector(".battle-figure[data-combatant-id='enemy.nighthawk']")!;
    expect(figure).toHaveClass("shadow-evasion-active");
    expect(document.querySelector(".team-panel.enemy [data-status-id='status.shadow_evasion']")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Fatal Strike/i }));
    const target = screen.getByRole("button", { name: /Nighthawk, selectable target/i });
    expect(target).toBeEnabled();
    expect(figure).toHaveClass("shadow-evasion-active");
  });

  it("does not fade a non-Rogue or a defeated Rogue even when the raw status is present", async () => {
    const snapshot = createFormatFixture(3);
    snapshot.combatants["friendly.ragnar"].statuses = [shadowStatus("friendly.ragnar")];
    snapshot.combatants["enemy.nighthawk"].statuses = [shadowStatus("enemy.nighthawk")];
    snapshot.combatants["enemy.nighthawk"].alive = false;
    const defeatedEnemy = snapshot.combatants["enemy.nighthawk"];
    defeatedEnemy.hp.current = 0;
    render(<BattleScreen provider={new MockBattleProvider(snapshot)} />);
    await screen.findByRole("region", { name: "Battlefield" });

    expect(document.querySelector(".battle-figure[data-combatant-id='friendly.ragnar']"))
      .not.toHaveClass("shadow-evasion-active");
    expect(document.querySelector(".battle-figure[data-combatant-id='enemy.nighthawk']"))
      .not.toBeInTheDocument();
  });

  it.each(["one-front-two-rear", "two-front-one-rear", "all-front"] as const)(
    "keeps the status-derived class local to the Rogue figure in 3v3 %s formation",
    async (formation) => {
      const snapshot = createFormatFixture(3);
      snapshot.formations = { friendly: formation, enemy: formation };
      snapshot.combatants["enemy.nighthawk"].statuses = [shadowStatus("enemy.nighthawk")];
      render(<BattleScreen provider={new MockBattleProvider(snapshot)} />);
      await screen.findByRole("region", { name: "Battlefield" });

      const figure = document.querySelector(".battle-figure[data-combatant-id='enemy.nighthawk']")!;
      expect(figure).toHaveClass("shadow-evasion-active");
      expect(figure.closest(".formation-slot")).toHaveAttribute("data-position", "front");
      expect(document.querySelectorAll(".shadow-evasion-active")).toHaveLength(1);
    },
  );
});
