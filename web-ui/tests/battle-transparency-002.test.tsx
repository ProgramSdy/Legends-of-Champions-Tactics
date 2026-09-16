import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { BattleScreen } from "@/components/battle/BattleScreen";
import { MockBattleProvider } from "@/lib/battle/fixture";
import type { BattlePreview, BattlePreviewRequest, BattleProvider } from "@/lib/battle/types";

type PreviewFactory = (request: BattlePreviewRequest, actorId: string) => BattlePreview;

function makeProvider(
  skillId: string,
  displayName: string,
  targetMode: "singleAlly" | "singleEnemy",
  previewFactory?: PreviewFactory,
) {
  return new MockBattleProvider().getState().then(({ snapshot }) => {
    const actor = snapshot.combatants[snapshot.activeCombatantId!];
    actor.definitionId = skillId.startsWith("skill.priest") ? "hero.priest.comprehensiveness" : "hero.paladin.retribution";
    actor.faculty = skillId.startsWith("skill.priest") ? "Priest" : "Paladin";
    actor.specialization = skillId.startsWith("skill.priest") ? "Comprehensiveness" : "Retribution";
    actor.skills = [{
      id: skillId, displayName, targetMode, maximumTargets: 1, cooldownRemaining: 0,
      available: true, unavailableReason: null, resourceCost: null,
    }];
    const targetId = targetMode === "singleAlly" ? "friendly.black_heart" : "enemy.sashein";
    snapshot.legalActions = [{
      actorId: actor.id, skillId, minimumTargets: 1, maximumTargets: 1, validTargetIds: [targetId],
    }];
    const provider = new MockBattleProvider(snapshot) as MockBattleProvider & BattleProvider;
    provider.previewAction = vi.fn(async (request) => previewFactory?.(request, actor.id) ?? ({
      revision: request.expectedRevision,
      actorId: request.actorId,
      skillId: request.skillId,
      requestedTargetIds: [...request.targetIds],
      selectedTargetIds: [...request.targetIds],
      coverage: "authoritative",
      targets: [{
        targetId: request.targetIds[0], currentHp: 41, maxHp: 97,
        primary: { kind: "healing", amountRange: { min: 12, max: 19 }, reasonId: null },
        directHitChancePercent: null,
        consequences: skillId === "skill.priest.binding_heal" ? [{
          kind: "secondaryHealing", certainty: "always", recipientId: actor.id,
          amountRange: { min: 17, max: 23 },
        }] : [],
      }],
    } satisfies BattlePreview));
    return { provider, targetId };
  });
}

describe("BATTLE-TRANSPARENCY-002 healer presentation", () => {
  it.each([
    ["skill.priest.binding_heal", "Binding Heal", "singleAlly" as const],
    ["skill.paladin.flash_of_light", "Flash of Light", "singleAlly" as const],
  ])("renders typed healing facts for %s without Hit Chance", async (skillId, displayName, targetMode) => {
    const { provider, targetId } = await makeProvider(skillId, displayName, targetMode);
    render(<BattleScreen provider={provider} mode="live" />);
    fireEvent.click(await screen.findByRole("button", { name: new RegExp(displayName, "i") }));
    fireEvent.mouseEnter(screen.getByRole("button", { name: new RegExp(targetId.includes("black") ? "Black Heart" : "Sashein") }));

    const card = await waitFor(() => {
      const result = document.querySelector(".target-preview-card.ready");
      expect(result).toBeInTheDocument();
      return result as HTMLElement;
    });
    expect(card).toHaveTextContent("Healing");
    expect(card).toHaveTextContent("12–19");
    expect(card).not.toHaveTextContent("Hit Chance");
    if (skillId === "skill.priest.binding_heal") {
      expect(card).not.toHaveTextContent("Separate healing");
      expect(card).not.toHaveTextContent("17–23");
    }
  });

  it("keeps stale healer preview responses from appearing after leaving the target", async () => {
    const { provider, targetId } = await makeProvider("skill.paladin.flash_of_light", "Flash of Light", "singleAlly");
    render(<BattleScreen provider={provider} mode="live" />);
    fireEvent.click(await screen.findByRole("button", { name: /Flash of Light/i }));
    const target = screen.getByRole("button", { name: /Black Heart/ });
    fireEvent.mouseEnter(target);
    await waitFor(() => expect(provider.previewAction).toHaveBeenCalledWith(
      expect.objectContaining({ targetIds: [targetId] }), expect.any(AbortSignal),
    ));
    fireEvent.mouseLeave(target);
    await waitFor(() => expect(document.querySelector(".target-preview-card.ready")).not.toBeInTheDocument());
  });

  it("renders Flash of Light's typed live Wrath healing contribution", async () => {
    const { provider } = await makeProvider(
      "skill.paladin.flash_of_light",
      "Flash of Light",
      "singleAlly",
      (request) => ({
        revision: request.expectedRevision,
        actorId: request.actorId,
        skillId: request.skillId,
        requestedTargetIds: [...request.targetIds],
        selectedTargetIds: [...request.targetIds],
        coverage: "authoritative",
        targets: [{
          targetId: request.targetIds[0], currentHp: 41, maxHp: 97,
          primary: { kind: "healing", amountRange: { min: 30, max: 32 }, reasonId: null },
          directHitChancePercent: null,
          consequences: [{
            kind: "wrathHealingBonus", certainty: "always", stacks: 2,
            amountRange: { min: 11, max: 13 },
          }],
        }],
      }),
    );
    render(<BattleScreen provider={provider} mode="live" />);
    fireEvent.click(await screen.findByRole("button", { name: /Flash of Light/i }));
    fireEvent.mouseEnter(screen.getByRole("button", { name: /Black Heart, selectable target/ }));

    const card = await waitFor(() => {
      const result = document.querySelector(".target-preview-card.ready");
      expect(result).toBeInTheDocument();
      return result as HTMLElement;
    });
    expect(card).toHaveTextContent("Healing");
    expect(card).toHaveTextContent("30–32");
    expect(card).toHaveTextContent("Wrath bonus");
    expect(card).toHaveTextContent("11–13 · 2 stacks");
  });

  it("renders Shadow Word Pain's server-authored material effect through keyboard focus", async () => {
    const { provider } = await makeProvider(
      "skill.priest.shadow_word_pain",
      "Shadow Word Pain",
      "singleEnemy",
      (request) => ({
        revision: request.expectedRevision,
        actorId: request.actorId,
        skillId: request.skillId,
        requestedTargetIds: [...request.targetIds],
        selectedTargetIds: [...request.targetIds],
        coverage: "authoritative",
        targets: [{
          targetId: request.targetIds[0], currentHp: 41, maxHp: 97,
          primary: { kind: "damage", amountRange: { min: 9, max: 13 }, reasonId: null },
          directHitChancePercent: 74,
          consequences: [{ kind: "shadowWordPain", certainty: "onHit" }],
        }],
      }),
    );
    render(<BattleScreen provider={provider} mode="live" />);
    fireEvent.click(await screen.findByRole("button", { name: /Shadow Word Pain/i }));
    const target = screen.getByRole("button", { name: /Sashein, selectable target/ });

    fireEvent.focus(target);
    const card = await waitFor(() => {
      const result = document.querySelector(".target-preview-card.ready");
      expect(result).toBeInTheDocument();
      return result as HTMLElement;
    });
    expect(card).toHaveTextContent("Damage");
    expect(card).toHaveTextContent("9–13");
    expect(card).toHaveTextContent("Hit Chance");
    expect(card).toHaveTextContent("Shadow Debuff");
    expect(card).toHaveTextContent("100% chance");

    fireEvent.keyDown(target, { key: "Enter" });
    expect(target).toHaveAttribute("aria-pressed", "true");
  });

  it("renders Crusader Strike's caster buff with the concise shared presentation", async () => {
    const { provider } = await makeProvider(
      "skill.paladin.crusader_strike",
      "Crusader Strike",
      "singleEnemy",
      (request) => ({
        revision: request.expectedRevision,
        actorId: request.actorId,
        skillId: request.skillId,
        requestedTargetIds: [...request.targetIds],
        selectedTargetIds: [...request.targetIds],
        coverage: "authoritative",
        targets: [{
          targetId: request.targetIds[0], currentHp: 41, maxHp: 97,
          primary: { kind: "damage", amountRange: { min: 18, max: 22 }, reasonId: null },
          directHitChancePercent: 80,
          consequences: [{
            kind: "wrathOfCrusader", certainty: "always", recipientId: request.actorId,
            stacks: 2, outcome: "nextStack",
          }],
        }],
      }),
    );
    render(<BattleScreen provider={provider} mode="live" />);
    fireEvent.click(await screen.findByRole("button", { name: /Crusader Strike/i }));
    fireEvent.mouseEnter(screen.getByRole("button", { name: /Sashein, selectable target/ }));

    const card = await waitFor(() => {
      const result = document.querySelector(".target-preview-card.ready");
      expect(result).toBeInTheDocument();
      return result as HTMLElement;
    });
    expect(card).toHaveTextContent("Buff Self");
    expect(card).toHaveTextContent("Wrath of Crusader");
    expect(card).not.toHaveTextContent("Increases to");
    expect(card).not.toHaveTextContent("2 stacks");
  });

  it("renders Hammer's Wrath contribution in the compact dock and keeps touch selection intact", async () => {
    const oldWidth = window.innerWidth;
    const oldHeight = window.innerHeight;
    Object.defineProperty(window, "innerWidth", { configurable: true, value: 900 });
    Object.defineProperty(window, "innerHeight", { configurable: true, value: 700 });
    try {
      const { provider } = await makeProvider(
        "skill.paladin.hammer_of_anger",
        "Hammer of Anger",
        "singleEnemy",
        (request) => ({
          revision: request.expectedRevision,
          actorId: request.actorId,
          skillId: request.skillId,
          requestedTargetIds: [...request.targetIds],
          selectedTargetIds: [...request.targetIds],
          coverage: "authoritative",
          targets: [{
            targetId: request.targetIds[0], currentHp: 41, maxHp: 97,
            primary: { kind: "damage", amountRange: { min: 18, max: 29 }, reasonId: null },
            directHitChancePercent: 80,
            consequences: [{
              kind: "wrathDamageBonus", certainty: "always", stacks: 2,
              amountRange: { min: 5, max: 7 },
            }],
          }],
        }),
      );
      render(<BattleScreen provider={provider} mode="live" />);
      fireEvent.click(await screen.findByRole("button", { name: /Hammer of Anger/i }));
      const target = screen.getByRole("button", { name: /Sashein, selectable target/ });

      fireEvent.mouseEnter(target);
      const dock = await waitFor(() => {
        const result = document.querySelector<HTMLElement>(".target-preview-dock");
        expect(result).toBeInTheDocument();
        return result!;
      });
      expect(dock).toHaveTextContent("Wrath bonus");
      expect(dock).toHaveTextContent("5–7 · 2 stacks");

      fireEvent.touchStart(target);
      fireEvent.click(target);
      expect(target).toHaveAttribute("aria-pressed", "true");
      expect(screen.getByRole("button", { name: "CAST SKILL" })).toBeEnabled();
    } finally {
      Object.defineProperty(window, "innerWidth", { configurable: true, value: oldWidth });
      Object.defineProperty(window, "innerHeight", { configurable: true, value: oldHeight });
      fireEvent(window, new Event("resize"));
    }
  });
});
