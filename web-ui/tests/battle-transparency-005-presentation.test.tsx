import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { BattleScreen } from "@/components/battle/BattleScreen";
import { MockBattleProvider } from "@/lib/battle/fixture";
import { isAuditedPreviewSkill } from "@/lib/battle/useBattlePreview";
import type {
  BattlePreview,
  BattlePreviewRequest,
  BattlePreviewTarget,
  BattleProvider,
  SkillState,
} from "@/lib/battle/types";

type PreviewProvider = MockBattleProvider & BattleProvider & {
  previewAction: ReturnType<typeof vi.fn<(request: BattlePreviewRequest, signal?: AbortSignal) => Promise<BattlePreview>>>;
};

function responseFor(request: BattlePreviewRequest, targets: BattlePreviewTarget[]): BattlePreview {
  return {
    revision: request.expectedRevision,
    actorId: request.actorId,
    skillId: request.skillId,
    requestedTargetIds: [...request.targetIds],
    selectedTargetIds: [...request.targetIds],
    coverage: "authoritative",
    targets,
    selfPreview: null,
  };
}

type DisciplineProviderOptions = {
  skillId: string;
  displayName: string;
  targetMode: SkillState["targetMode"];
  maximumTargets: number;
  minimumTargets?: number;
  preview: (request: BattlePreviewRequest) => BattlePreview;
};

async function asyncDisciplineProvider({
  skillId,
  displayName,
  targetMode,
  maximumTargets,
  minimumTargets = maximumTargets,
  preview,
}: DisciplineProviderOptions): Promise<{ provider: PreviewProvider; actorId: string }> {
  const snapshot = (await new MockBattleProvider().getState()).snapshot;
  const actorId = snapshot.activeCombatantId!;
  const actor = snapshot.combatants[actorId];
  actor.definitionId = "hero.priest.discipline";
  actor.faculty = "Priest";
  actor.specialization = "Discipline";
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
  const validTargetIds = skillId.endsWith("punishment")
    ? ["enemy.sashein", "enemy.andonidas"]
    : skillId.endsWith("redemption")
      ? ["friendly.black_heart"]
      : ["friendly.black_heart", "enemy.sashein", "enemy.andonidas"];
  snapshot.legalActions = [{ actorId, skillId, minimumTargets, maximumTargets, validTargetIds }];
  const provider = new MockBattleProvider(snapshot) as PreviewProvider;
  provider.previewAction = vi.fn(async (request) => preview(request));
  return { provider, actorId };
}

describe("BATTLE-TRANSPARENCY-005 Priest Discipline presentation", () => {
  it("keeps the audited preview boundary exact", () => {
    expect(isAuditedPreviewSkill("skill.priest.penance")).toBe(true);
    expect(isAuditedPreviewSkill("skill.priest.holy_word_redemption")).toBe(true);
    expect(isAuditedPreviewSkill("skill.priest.holy_word_punishment")).toBe(true);
    expect(isAuditedPreviewSkill("skill.priest.holy_aura")).toBe(false);
    expect(isAuditedPreviewSkill("skill.priest.purification")).toBe(false);
  });

  it("renders Penance as healing for an ally and damage for an enemy", async () => {
    const { provider } = await asyncDisciplineProvider({
      skillId: "skill.priest.penance",
      displayName: "Penance",
      targetMode: "flexible",
      maximumTargets: 1,
      preview: (request) => responseFor(request, [{
        targetId: request.targetIds[0], currentHp: request.targetIds[0].startsWith("friendly") ? 60 : 49, maxHp: 91,
        primary: request.targetIds[0].startsWith("friendly")
          ? { kind: "healing", amountRange: { min: 21, max: 25 }, reasonId: null }
          : { kind: "damage", amountRange: { min: 17, max: 21 }, reasonId: null },
        directHitChancePercent: request.targetIds[0].startsWith("friendly") ? null : 82,
        consequences: [],
      }]),
    });
    render(<BattleScreen provider={provider} mode="live" />);
    fireEvent.click(await screen.findByRole("button", { name: /Penance/i }));
    const ally = screen.getByRole("button", { name: /Black Heart, selectable target/i });
    fireEvent.mouseEnter(ally);
    await waitFor(() => expect(provider.previewAction).toHaveBeenCalledWith(expect.objectContaining({ targetIds: ["friendly.black_heart"] }), expect.anything()));
    expect(await screen.findByText("21–25")).toBeVisible();
    expect(screen.getByText("Healing")).toBeVisible();
    expect(screen.queryByText("Hit Chance")).not.toBeInTheDocument();

    fireEvent.mouseLeave(ally);
    const enemy = screen.getByRole("button", { name: /Sashein, selectable target/i });
    fireEvent.mouseEnter(enemy);
    await waitFor(() => expect(provider.previewAction).toHaveBeenCalledWith(expect.objectContaining({ targetIds: ["enemy.sashein"] }), expect.anything()));
    expect(await screen.findByText("17–21")).toBeVisible();
    expect(screen.getByText("Hit Chance")).toBeVisible();
  });

  it("renders Redemption as a target-only linked status consequence", async () => {
    const { provider } = await asyncDisciplineProvider({
      skillId: "skill.priest.holy_word_redemption",
      displayName: "Holy Word Redemption",
      targetMode: "singleAlly",
      maximumTargets: 1,
      preview: (request) => responseFor(request, [{
        targetId: request.targetIds[0], currentHp: 70, maxHp: 91,
        primary: null, directHitChancePercent: null,
        consequences: [{ kind: "holyWordRedemption", certainty: "always", recipientId: request.targetIds[0], duration: 5, outcome: "firstApplication" }],
      }]),
    });
    render(<BattleScreen provider={provider} mode="live" />);
    fireEvent.click(await screen.findByRole("button", { name: /Holy Word Redemption/i }));
    const ally = screen.getByRole("button", { name: /Black Heart, selectable target/i });
    fireEvent.mouseEnter(ally);
    expect(await screen.findByText("Holy Word Redemption · linked healing")).toBeVisible();
    expect(screen.queryByText(/Damage|Healing/)).not.toBeInTheDocument();
  });

  it("keeps Punishment draft previews ordered and per-target", async () => {
    const { provider } = await asyncDisciplineProvider({
      skillId: "skill.priest.holy_word_punishment",
      displayName: "Holy Word Punishment",
      targetMode: "multipleEnemies",
      maximumTargets: 2,
      minimumTargets: 2,
      preview: (request) => responseFor(request, request.targetIds.map((targetId) => ({
        targetId, currentHp: 49, maxHp: 76,
        primary: { kind: "damage", amountRange: { min: 7, max: 11 }, reasonId: null },
        directHitChancePercent: 80, consequences: [{ kind: "holyWordPunishment", certainty: "onHit", recipientId: targetId, duration: 4, outcome: "firstApplication" }],
      }))),
    });
    render(<BattleScreen provider={provider} mode="live" />);
    fireEvent.click(await screen.findByRole("button", { name: /Holy Word Punishment/i }));
    const first = screen.getByRole("button", { name: /Sashein, selectable target/i });
    const second = screen.getByRole("button", { name: /Andonidas, selectable target/i });
    fireEvent.mouseEnter(first);
    await waitFor(() => expect(provider.previewAction).toHaveBeenCalledWith(expect.objectContaining({ targetIds: ["enemy.sashein"] }), expect.anything()));
    expect(await screen.findByText("7–11")).toBeVisible();
    fireEvent.click(first);
    fireEvent.mouseLeave(first);
    fireEvent.mouseEnter(second);
    await waitFor(() => expect(provider.previewAction).toHaveBeenCalledWith(expect.objectContaining({ targetIds: ["enemy.sashein", "enemy.andonidas"] }), expect.anything()));
    // The card follows the current hover anchor; the request carries the
    // complete ordered draft and the UI does not invent an aggregate total.
    expect(screen.getByText("7–11")).toBeVisible();
    expect(screen.getByText("SELECT 2 TARGETS · 1 SELECTED")).toBeVisible();
    fireEvent.click(second);
    expect(screen.getByRole("button", { name: "CAST SKILL" })).toBeEnabled();
  });
});
