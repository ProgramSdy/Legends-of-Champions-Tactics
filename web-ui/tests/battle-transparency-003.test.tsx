import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { BattleScreen } from "@/components/battle/BattleScreen";
import { MockBattleProvider } from "@/lib/battle/fixture";
import { isAuditedPreviewSkill } from "@/lib/battle/useBattlePreview";
import type { BattlePreview, BattlePreviewConsequence, BattlePreviewRequest, BattleProvider } from "@/lib/battle/types";

type PreviewingProvider = MockBattleProvider & BattleProvider & {
  previewAction: ReturnType<typeof vi.fn<(request: BattlePreviewRequest, signal?: AbortSignal) => Promise<BattlePreview>>>;
};

async function warriorProvider({
  skillId,
  displayName,
  targetMode,
  preview,
}: {
  skillId: string;
  displayName: string;
  targetMode: "none" | "singleEnemy";
  preview: (request: BattlePreviewRequest, actorId: string) => BattlePreview;
}): Promise<{ provider: PreviewingProvider; actorId: string }> {
  const { snapshot } = await new MockBattleProvider().getState();
  const actorId = snapshot.activeCombatantId!;
  const actor = snapshot.combatants[actorId];
  actor.definitionId = skillId === "skill.warrior.warlust" ? "hero.warrior.berserker" : "hero.warrior.weapon_master";
  actor.faculty = "Warrior";
  actor.specialization = skillId === "skill.warrior.warlust" ? "Berserker" : "Weapon Master";
  actor.skills = [{
    id: skillId,
    displayName,
    targetMode,
    maximumTargets: targetMode === "none" ? 0 : 1,
    cooldownRemaining: 0,
    available: true,
    unavailableReason: null,
    resourceCost: null,
  }];
  snapshot.legalActions = [{
    actorId,
    skillId,
    minimumTargets: targetMode === "none" ? 0 : 1,
    maximumTargets: targetMode === "none" ? 0 : 1,
    validTargetIds: targetMode === "none" ? [] : ["enemy.sashein"],
  }];
  const provider = new MockBattleProvider(snapshot) as PreviewingProvider;
  provider.previewAction = vi.fn(async (request) => preview(request, actorId));
  return { provider, actorId };
}

function selfResponse(
  request: BattlePreviewRequest,
  actorId: string,
  consequences: BattlePreviewConsequence[],
  primary: BattlePreview["selfPreview"] extends infer Self
    ? Self extends { primary: infer Primary } ? Primary : never
    : never = null,
): BattlePreview {
  return {
    revision: request.expectedRevision,
    actorId: request.actorId,
    skillId: request.skillId,
    requestedTargetIds: [],
    selectedTargetIds: [],
    coverage: "authoritative",
    targets: [],
    selfPreview: {
      recipientId: actorId,
      currentHp: 63,
      maxHp: 97,
      primary,
      consequences,
    },
  };
}

describe("BATTLE-TRANSPARENCY-003 Warrior presentation", () => {
  it("keeps the audited scope finite while covering all nine published Warrior skills", () => {
    [
      "skill.warrior.devastate",
      "skill.warrior.shield_bash",
      "skill.warrior.thunder_pot",
      "skill.warrior.fatal_strike",
      "skill.warrior.armor_crush",
      "skill.warrior.antivenom_potion",
      "skill.warrior.moon_slash",
      "skill.warrior.warlust",
      "skill.warrior.strike_of_meteorite",
    ].forEach((skillId) => expect(isAuditedPreviewSkill(skillId)).toBe(true));
    expect(isAuditedPreviewSkill("skill.warrior.slash")).toBe(false);
    expect(isAuditedPreviewSkill("skill.rogue.shadow_evasion")).toBe(false);
  });

  it("requests and renders Antivenom Potion as an explicit targetless self preview", async () => {
    const { provider, actorId } = await warriorProvider({
      skillId: "skill.warrior.antivenom_potion",
      displayName: "Antivenom Potion",
      targetMode: "none",
      preview: (request, recipientId) => selfResponse(request, recipientId, [
        { kind: "statusRemoval", certainty: "always", recipientId, statusIds: ["status.poisoned_dagger"] },
        { kind: "resistanceBoost", certainty: "always", recipientId, resistances: ["poison"], amount: 45, duration: 2, outcome: "firstApplication" },
        { kind: "cooldown", certainty: "always", recipientId, rounds: 3 },
      ], { kind: "healing", amountRange: { min: 18, max: 20 }, reasonId: null }),
    });
    render(<BattleScreen provider={provider} mode="live" />);

    fireEvent.click(await screen.findByRole("button", { name: /Antivenom Potion/i }));

    const card = await waitFor(() => {
      const result = document.querySelector<HTMLElement>(".self-preview-card.ready");
      expect(result).toBeInTheDocument();
      return result!;
    });
    expect(provider.previewAction).toHaveBeenCalledWith({
      expectedRevision: 1,
      actorId,
      skillId: "skill.warrior.antivenom_potion",
      targetIds: [],
    }, expect.any(AbortSignal));
    expect(card).toHaveTextContent("SELF");
    expect(card).toHaveTextContent("Healing18–20");
    expect(card).toHaveTextContent("Current HP63 / 97");
    expect(card).toHaveTextContent("RemovesPoisoned Dagger");
    expect(card).toHaveTextContent("Poison Resistance+45 · 2 rounds");
    expect(card).toHaveTextContent("Cooldown3 rounds");
    expect(screen.queryByRole("button", { name: /selectable target/ })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "CAST SKILL" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "CAST SKILL" })).toHaveAttribute("aria-describedby", "battle-self-preview");
  });

  it("renders Warlust's consequence-only self preview without inventing a primary fact", async () => {
    const { provider } = await warriorProvider({
      skillId: "skill.warrior.warlust",
      displayName: "Warlust",
      targetMode: "none",
      preview: (request, recipientId) => selfResponse(request, recipientId, [
        { kind: "controlImmunity", certainty: "always", recipientId, duration: 2, outcome: "firstApplication" },
        { kind: "damageIncrease", certainty: "always", recipientId, amount: 12, outcome: "firstApplication" },
        { kind: "cooldown", certainty: "always", recipientId, rounds: 3 },
      ]),
    });
    render(<BattleScreen provider={provider} mode="live" />);
    fireEvent.click(await screen.findByRole("button", { name: /Warlust/i }));

    const card = await waitFor(() => {
      const result = document.querySelector<HTMLElement>(".self-preview-card.ready");
      expect(result).toBeInTheDocument();
      return result!;
    });
    expect(card).toHaveTextContent("Control Immunity2 rounds");
    expect(card).toHaveTextContent("Damage Increase+12");
    expect(card).toHaveTextContent("Cooldown3 rounds");
    expect(within(card).queryByText("Healing")).not.toBeInTheDocument();
    expect(within(card).queryByText("Damage", { exact: true })).not.toBeInTheDocument();
  });

  it("renders finite Warrior target consequences without changing target selection", async () => {
    const consequences: BattlePreviewConsequence[] = [
      { kind: "armorBreaker", certainty: "onHit", resultingStacks: 2, outcome: "nextStack" },
      { kind: "stun", certainty: "onHit", resultingDuration: 1, outcome: "firstApplication" },
      { kind: "castingInterrupted", certainty: "onHit" },
      { kind: "scoff", certainty: "onHit", outcome: "sourceReplacement" },
      { kind: "healingReduction", certainty: "onHit", percent: 70, outcome: "firstApplication" },
      { kind: "wound", certainty: "onHit", agilityReduction: 8, outcome: "firstApplication" },
      { kind: "bleed", certainty: "onHit", outcome: "durationRefresh" },
    ];
    const { provider } = await warriorProvider({
      skillId: "skill.warrior.devastate",
      displayName: "Devastate",
      targetMode: "singleEnemy",
      preview: (request) => ({
        revision: request.expectedRevision,
        actorId: request.actorId,
        skillId: request.skillId,
        requestedTargetIds: [...request.targetIds],
        selectedTargetIds: [...request.targetIds],
        coverage: "authoritative",
        targets: [{
          targetId: request.targetIds[0],
          currentHp: 41,
          maxHp: 97,
          primary: { kind: "damage", amountRange: { min: 7, max: 11 }, reasonId: null },
          directHitChancePercent: 76,
          consequences,
        }],
        selfPreview: null,
      }),
    });
    render(<BattleScreen provider={provider} mode="live" />);
    fireEvent.click(await screen.findByRole("button", { name: /Devastate/i }));
    const target = screen.getByRole("button", { name: /Sashein, selectable target/ });
    fireEvent.mouseEnter(target);

    const card = await waitFor(() => {
      const result = document.querySelector<HTMLElement>(".target-preview-card.ready");
      expect(result).toBeInTheDocument();
      return result!;
    });
    expect(card).toHaveTextContent("Armor BreakerIncreases to 2 stacks");
    expect(card).toHaveTextContent("StunApplies 1 round");
    expect(card).toHaveTextContent("CastingInterrupted on hit");
    expect(card).toHaveTextContent("ScoffReplaces source on hit");
    expect(card).toHaveTextContent("Healing Reduction70% on hit");
    expect(card).toHaveTextContent("Wound−8 Agility on hit");
    expect(card).toHaveTextContent("BleedingRefreshes on hit");
    fireEvent.click(target);
    expect(target).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: "CAST SKILL" })).toBeEnabled();
  });

  it("shows an unavailable self preview without blocking the legal targetless command", async () => {
    const { provider } = await warriorProvider({
      skillId: "skill.warrior.antivenom_potion",
      displayName: "Antivenom Potion",
      targetMode: "none",
      preview: (request) => ({
        revision: request.expectedRevision,
        actorId: request.actorId,
        skillId: request.skillId,
        requestedTargetIds: [],
        selectedTargetIds: [],
        coverage: "unavailable",
        reasonId: "preview.unauditedState",
        targets: [],
        selfPreview: null,
      }),
    });
    render(<BattleScreen provider={provider} mode="live" />);
    fireEvent.click(await screen.findByRole("button", { name: /Antivenom Potion/i }));

    expect(await screen.findByText("Preview unavailable")).toBeVisible();
    expect(screen.getByRole("button", { name: "CAST SKILL" })).toBeEnabled();
  });
});
