import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { BattleScreen } from "@/components/battle/BattleScreen";
import { MockBattleProvider } from "@/lib/battle/fixture";
import { LiveBattleProvider } from "@/lib/battle/liveProvider";
import { isAuditedPreviewSkill } from "@/lib/battle/useBattlePreview";
import type {
  BattlePreview,
  BattlePreviewConsequence,
  BattlePreviewRequest,
  BattlePreviewTarget,
  BattleProvider,
  BattleSnapshot,
  SkillState,
} from "@/lib/battle/types";

type PreviewingProvider = MockBattleProvider & BattleProvider & {
  previewAction: ReturnType<typeof vi.fn<(request: BattlePreviewRequest, signal?: AbortSignal) => Promise<BattlePreview>>>;
};

function responseFor(
  request: BattlePreviewRequest,
  targets: BattlePreviewTarget[] = [],
  selfPreview: BattlePreview["selfPreview"] = null,
): BattlePreview {
  return {
    revision: request.expectedRevision,
    actorId: request.actorId,
    skillId: request.skillId,
    requestedTargetIds: [...request.targetIds],
    selectedTargetIds: [...request.targetIds],
    coverage: "authoritative",
    targets,
    selfPreview,
  };
}

function damageTarget(targetId: string, min = 18, max = 22): BattlePreviewTarget {
  return {
    targetId,
    currentHp: 49,
    maxHp: 76,
    primary: { kind: "damage", amountRange: { min, max }, reasonId: null },
    directHitChancePercent: 79,
    consequences: [],
  };
}

async function paladinProvider({
  skillId,
  displayName,
  targetMode,
  maximumTargets,
  side,
  preview,
}: {
  skillId: string;
  displayName: string;
  targetMode: SkillState["targetMode"];
  maximumTargets: number;
  side: "ally" | "enemy" | "none";
  preview: (request: BattlePreviewRequest, snapshot: BattleSnapshot) => BattlePreview;
}): Promise<{ provider: PreviewingProvider; actorId: string }> {
  const snapshot = (await new MockBattleProvider().getState()).snapshot;
  const actorId = snapshot.activeCombatantId!;
  const actor = snapshot.combatants[actorId];
  const holy = skillId.includes("purify") || skillId.includes("holy_blast") || skillId.includes("shield_of_protection");
  actor.definitionId = holy ? "hero.paladin.holy" : "hero.paladin.protection";
  actor.faculty = "Paladin";
  actor.specialization = holy ? "Holy" : "Protection";
  actor.skills = [{
    id: skillId,
    displayName,
    targetMode,
    maximumTargets,
    cooldownRemaining: 0,
    available: true,
    unavailableReason: null,
    resourceCost: null,
  }];
  const validTargetIds = side === "ally"
    ? ["friendly.black_heart"]
    : side === "enemy"
      ? ["enemy.sashein", "enemy.andonidas"]
      : [];
  const targetCount = maximumTargets === 0 ? 0 : Math.min(maximumTargets, validTargetIds.length);
  snapshot.legalActions = [{
    actorId,
    skillId,
    minimumTargets: targetCount,
    maximumTargets: targetCount,
    validTargetIds,
  }];
  const provider = new MockBattleProvider(snapshot) as PreviewingProvider;
  provider.previewAction = vi.fn(async (request) => preview(request, snapshot));
  return { provider, actorId };
}

function readyCard(selector: string): Promise<HTMLElement> {
  return waitFor(() => {
    const result = document.querySelector<HTMLElement>(selector);
    expect(result).toBeInTheDocument();
    return result!;
  });
}

describe("BATTLE-TRANSPARENCY-004 Paladin presentation", () => {
  it("allows exactly the six active Paladin skills and excludes passive Holy Aura", () => {
    [
      "skill.paladin.hammer_of_revenge",
      "skill.paladin.shield_of_righteous",
      "skill.paladin.heroric_charge",
      "skill.paladin.purify_healing",
      "skill.paladin.holy_blast",
      "skill.paladin.shield_of_protection",
    ].forEach((skillId) => expect(isAuditedPreviewSkill(skillId)).toBe(true));
    expect(isAuditedPreviewSkill("skill.paladin.holy_aura")).toBe(false);
    expect(isAuditedPreviewSkill("skill.paladin.unknown")).toBe(false);
  });

  it("accepts all seven new finite consequences at the live transport boundary", async () => {
    const snapshot = (await new MockBattleProvider().getState()).snapshot;
    const request: BattlePreviewRequest = {
      expectedRevision: 1,
      actorId: snapshot.activeCombatantId!,
      skillId: "skill.paladin.hammer_of_revenge",
      targetIds: ["enemy.sashein"],
    };
    const consequences: BattlePreviewConsequence[] = [
      { kind: "revengeDamageBonus", certainty: "always", debuffCount: 2, amountRange: { min: 6, max: 8 } },
      { kind: "damageReduction", certainty: "onHit", recipientId: "enemy.sashein", percent: 20, amount: 7, duration: 3, outcome: "firstApplication" },
      { kind: "defenceIncrease", certainty: "always", recipientId: request.actorId, amount: 5, resultingStacks: 2, duration: 3, outcome: "nextStack" },
      { kind: "controlPrevented", certainty: "onHit", recipientId: "enemy.sashein", reasonId: "status.warlust" },
      { kind: "purifyHealing", certainty: "always", recipientId: request.actorId, duration: 2, outcome: "durationRefresh" },
      { kind: "randomStatusRemoval", certainty: "always", recipientId: request.actorId, candidateStatusIds: ["status.poisoned_dagger", "status.bleeding_sharp_blade"], maximumRemovals: 1, mayRemoveNone: false },
      { kind: "damageImmunity", certainty: "always", recipientId: request.actorId, duration: 2, outcome: "firstApplication" },
    ];
    const preview = responseFor(request, [{ ...damageTarget("enemy.sashein"), consequences }]);
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify({
        contractVersion: "1.0", battleId: "battle.paladin-preview", revision: 1, data: { events: [], snapshot },
      }), { status: 200, headers: { "Content-Type": "application/json" } }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        contractVersion: "1.0", battleId: "battle.paladin-preview", revision: 1, data: preview,
      }), { status: 200, headers: { "Content-Type": "application/json" } }));
    const provider = new LiveBattleProvider("http://adapter.test");
    await provider.getState();

    await expect(provider.previewAction(request)).resolves.toEqual(preview);
  });

  it("renders Purify healing and random-removal uncertainty without predicting a status", async () => {
    const { provider } = await paladinProvider({
      skillId: "skill.paladin.purify_healing",
      displayName: "Purify Healing",
      targetMode: "singleAlly",
      maximumTargets: 1,
      side: "ally",
      preview: (request) => responseFor(request, [{
        targetId: request.targetIds[0],
        currentHp: 41,
        maxHp: 91,
        primary: { kind: "healing", amountRange: { min: 23, max: 27 }, reasonId: null },
        directHitChancePercent: null,
        consequences: [
          { kind: "purifyHealing", certainty: "always", recipientId: request.targetIds[0], duration: 2, outcome: "durationRefresh" },
          { kind: "randomStatusRemoval", certainty: "always", recipientId: request.targetIds[0], candidateStatusIds: ["status.poisoned_dagger", "status.bleeding_sharp_blade"], maximumRemovals: 1, mayRemoveNone: true },
        ],
      }]),
    });
    render(<BattleScreen provider={provider} mode="live" />);
    fireEvent.click(await screen.findByRole("button", { name: /Purify Healing/i }));
    const target = screen.getByRole("button", { name: /Black Heart, selectable target/i });
    fireEvent.focus(target);

    const card = await readyCard(".target-preview-card.ready");
    expect(card).toHaveTextContent("Healing23–27");
    expect(card).not.toHaveTextContent("Hit Chance");
    expect(card).toHaveTextContent("Buff RefreshPurify Healing · 2 rounds");
    expect(card).toHaveTextContent("RemovesUp to one eligible status (random)");
    expect(card).not.toHaveTextContent("Poisoned Dagger");
    expect(card).not.toHaveTextContent("Bleeding");
    fireEvent.keyDown(target, { key: "Enter" });
    expect(target).toHaveAttribute("aria-pressed", "true");
  });

  it("preserves Holy Blast's ordered draft/full selection and per-target display", async () => {
    const { provider } = await paladinProvider({
      skillId: "skill.paladin.holy_blast",
      displayName: "Holy Blast",
      targetMode: "multipleEnemies",
      maximumTargets: 2,
      side: "enemy",
      preview: (request) => responseFor(request, request.targetIds.map((targetId, index) => damageTarget(
        targetId,
        index === 0 ? 20 : 14,
        index === 0 ? 25 : 17,
      ))),
    });
    render(<BattleScreen provider={provider} mode="live" />);
    fireEvent.click(await screen.findByRole("button", { name: /Holy Blast/i }));
    const first = screen.getByRole("button", { name: /Sashein, selectable target/i });
    const second = screen.getByRole("button", { name: /Andonidas, selectable target/i });
    fireEvent.mouseEnter(first);
    await waitFor(() => expect(provider.previewAction).toHaveBeenCalledOnce());
    expect(provider.previewAction.mock.calls[0][0].targetIds).toEqual(["enemy.sashein"]);
    expect(await screen.findByText("20–25")).toBeVisible();

    fireEvent.click(first);
    fireEvent.mouseLeave(first);
    fireEvent.mouseEnter(second);
    await waitFor(() => expect(provider.previewAction).toHaveBeenCalledTimes(2));
    expect(provider.previewAction.mock.calls[1][0].targetIds).toEqual(["enemy.sashein", "enemy.andonidas"]);
    expect(await screen.findByText("14–17")).toBeVisible();
    expect(screen.queryByText("20–25")).not.toBeInTheDocument();
    expect(screen.queryByText(/total damage/i)).not.toBeInTheDocument();
    fireEvent.click(second);
    expect(screen.getByRole("button", { name: "CAST SKILL" })).toBeEnabled();
  });

  it("reuses targetless selfPreview for Shield of Protection without a fake target", async () => {
    const { provider, actorId } = await paladinProvider({
      skillId: "skill.paladin.shield_of_protection",
      displayName: "Shield of Protection",
      targetMode: "self",
      maximumTargets: 0,
      side: "none",
      preview: (request) => responseFor(request, [], {
        recipientId: request.actorId,
        currentHp: 61,
        maxHp: 81,
        primary: null,
        consequences: [
          { kind: "damageImmunity", certainty: "always", recipientId: request.actorId, duration: 2, outcome: "durationRefresh" },
          { kind: "statusRemoval", certainty: "always", recipientId: request.actorId, statusIds: ["status.scoff"] },
          { kind: "cooldown", certainty: "always", recipientId: request.actorId, rounds: 3 },
        ],
      }),
    });
    render(<BattleScreen provider={provider} mode="live" />);
    fireEvent.click(await screen.findByRole("button", { name: /Shield of Protection/i }));

    const card = await readyCard(".self-preview-card.ready");
    expect(provider.previewAction).toHaveBeenCalledWith({
      expectedRevision: 1,
      actorId,
      skillId: "skill.paladin.shield_of_protection",
      targetIds: [],
    }, expect.any(AbortSignal));
    expect(card).toHaveTextContent("Buff RefreshDamage Immunity · 2 rounds");
    expect(card).toHaveTextContent("RemovesScoff");
    expect(card).toHaveTextContent("Cooldown3 rounds");
    expect(screen.queryByRole("button", { name: /selectable target/i })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "CAST SKILL" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "CAST SKILL" })).toHaveAttribute("aria-describedby", "battle-self-preview");
  });

  it.each([
    {
      skillId: "skill.paladin.shield_of_righteous",
      displayName: "Shield of Righteous",
      consequences: [{
        kind: "defenceIncrease", certainty: "always", recipientId: "friendly.arthas",
        amount: 5, resultingStacks: 2, duration: 3, outcome: "nextStack",
      }] satisfies BattlePreviewConsequence[],
      expected: "Buff StackShield of Righteous · +5 Defence · 2 stacks · 3 rounds",
    },
    {
      skillId: "skill.paladin.heroric_charge",
      displayName: "Heroric Charge",
      consequences: [
        { kind: "secondaryHealing", certainty: "always", recipientId: "friendly.arthas", amountRange: { min: 20, max: 32 } },
        { kind: "cooldown", certainty: "always", recipientId: "friendly.arthas", rounds: 3 },
      ] satisfies BattlePreviewConsequence[],
      expected: "Self Healing20–32Cooldown3 rounds",
    },
  ])("shows $displayName actor facts beside the target preview", async ({ skillId, displayName, consequences, expected }) => {
    const { provider, actorId } = await paladinProvider({
      skillId,
      displayName,
      targetMode: "singleEnemy",
      maximumTargets: 1,
      side: "enemy",
      preview: (request) => responseFor(request, [damageTarget(request.targetIds[0])], {
        recipientId: actorId,
        currentHp: 61,
        maxHp: 81,
        primary: null,
        consequences,
      }),
    });
    const view = render(<BattleScreen provider={provider} mode="live" />);
    fireEvent.click(await screen.findByRole("button", { name: new RegExp(displayName, "i") }));
    const target = screen.getByRole("button", { name: /Sashein, selectable target/i });
    fireEvent.mouseEnter(target);

    await readyCard(".target-preview-card.ready");
    const selfCard = await readyCard(".self-preview-card.ready");
    expect(selfCard).toHaveTextContent(expected);
    fireEvent.click(target);
    expect(target).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: "CAST SKILL" })).toBeEnabled();
    view.unmount();
  });

  it("renders Hammer of Revenge facts and Warlust control prevention verbatim", async () => {
    const consequences: BattlePreviewConsequence[] = [
      { kind: "revengeDamageBonus", certainty: "always", debuffCount: 3, amountRange: { min: 9, max: 11 } },
      { kind: "damageReduction", certainty: "onHit", recipientId: "enemy.sashein", percent: 20, amount: 7, duration: 3, outcome: "firstApplication" },
      { kind: "controlPrevented", certainty: "onHit", recipientId: "enemy.sashein", reasonId: "status.warlust" },
    ];
    const { provider } = await paladinProvider({
      skillId: "skill.paladin.hammer_of_revenge",
      displayName: "Hammer of Revenge",
      targetMode: "singleEnemy",
      maximumTargets: 1,
      side: "enemy",
      preview: (request) => responseFor(request, [{ ...damageTarget(request.targetIds[0]), consequences }]),
    });
    render(<BattleScreen provider={provider} mode="live" />);
    fireEvent.click(await screen.findByRole("button", { name: /Hammer of Revenge/i }));
    fireEvent.mouseEnter(screen.getByRole("button", { name: /Sashein, selectable target/i }));

    const card = await readyCard(".target-preview-card.ready");
    expect(card).toHaveTextContent("Debuff Bonus+9–11 · 3 active debuffs");
    expect(card).toHaveTextContent("Debuff ApplyDamage −20% (−7) · 3 rounds");
    expect(card).toHaveTextContent("ScoffBlocked by Warlust");
  });
});
