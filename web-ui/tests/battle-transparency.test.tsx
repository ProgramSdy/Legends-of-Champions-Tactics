import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { BattleScreen } from "@/components/battle/BattleScreen";
import { MockBattleProvider } from "@/lib/battle/fixture";
import type { BattlePreview, BattleProvider } from "@/lib/battle/types";

function previewFixture(overrides: Partial<BattlePreview> = {}): BattlePreview {
  return {
    revision: 1,
    actorId: "friendly.arthas",
    skillId: "skill.mage.fireball",
    requestedTargetIds: ["enemy.sashein"],
    selectedTargetIds: ["enemy.sashein"],
    coverage: "authoritative",
    reasonId: null,
    targets: [{
      targetId: "enemy.sashein",
      currentHp: 61,
      maxHp: 81,
      primary: { kind: "damage", amountRange: { min: 18, max: 29 }, reasonId: null },
      directHitChancePercent: 85,
      consequences: [],
    }],
    ...overrides,
  };
}

function renderPreview(preview: BattlePreview = previewFixture()) {
  const source = new MockBattleProvider();
  return source.getState().then(async (result) => {
    const snapshot = structuredClone(result.snapshot);
    const actor = snapshot.combatants["friendly.arthas"];
    actor.skills[0] = {
      ...actor.skills[0], id: "skill.mage.fireball", displayName: "Fireball",
    };
    snapshot.legalActions[0] = {
      ...snapshot.legalActions[0], skillId: "skill.mage.fireball", actorId: "friendly.arthas",
      validTargetIds: ["enemy.sashein"], minimumTargets: 1, maximumTargets: 1,
    };
    const provider = new MockBattleProvider(snapshot) as MockBattleProvider & BattleProvider;
    provider.previewAction = vi.fn(async () => structuredClone(preview));
    render(<BattleScreen provider={provider} />);
    return { provider, previewAction: provider.previewAction };
  });
}

describe("battle transparency preview", () => {
  it("requests the authoritative preview for pointer hover and exposes compact facts", async () => {
    const { previewAction } = await renderPreview();
    fireEvent.click(await screen.findByRole("button", { name: /Fireball/i }));
    fireEvent.mouseEnter(screen.getByRole("button", { name: "Sashein, selectable target" }));

    await waitFor(() => expect(previewAction).toHaveBeenCalledWith(
      expect.objectContaining({
        expectedRevision: 1,
        actorId: "friendly.arthas",
        skillId: "skill.mage.fireball",
        targetIds: ["enemy.sashein"],
      }),
      expect.any(AbortSignal),
    ));
    expect(await screen.findByText("Damage")).toBeVisible();
    expect(screen.getByText("18–29")).toBeVisible();
    expect(screen.getByText("85%")).toBeVisible();
    expect(screen.getByText("61 / 81")).toBeVisible();
  });

  it("uses the same preview request for keyboard focus and clears it when the skill is not audited", async () => {
    const { previewAction } = await renderPreview();
    const skill = await screen.findByRole("button", { name: /Fireball/i });
    fireEvent.click(skill);
    fireEvent.focus(screen.getByRole("button", { name: "Sashein, selectable target" }));
    await waitFor(() => expect(previewAction).toHaveBeenCalled());

    fireEvent.click(skill);
    expect(screen.queryByText("18–29")).not.toBeInTheDocument();
  });
});
