"use client";

import { useEffect, useRef, useState } from "react";
import type { BattlePreview, BattlePreviewRequest, BattleProvider } from "./types";

const AUDITED_PREVIEW_SKILL_IDS = new Set([
  "skill.mage.fireball",
  "skill.mage.arcane_missiles",
  "skill.mage.frost_bolt",
  "skill.rogue.sharp_blade",
  "skill.rogue.poisoned_dagger",
  "skill.priest.holy_smite",
  "skill.priest.shadow_word_pain",
  "skill.priest.binding_heal",
  "skill.paladin.hammer_of_anger",
  "skill.paladin.crusader_strike",
  "skill.paladin.flash_of_light",
  "skill.warrior.devastate",
  "skill.warrior.shield_bash",
  "skill.warrior.thunder_pot",
  "skill.warrior.fatal_strike",
  "skill.warrior.armor_crush",
  "skill.warrior.antivenom_potion",
  "skill.warrior.moon_slash",
  "skill.warrior.warlust",
  "skill.warrior.strike_of_meteorite",
  "skill.paladin.hammer_of_revenge",
  "skill.paladin.shield_of_righteous",
  "skill.paladin.heroric_charge",
  "skill.paladin.purify_healing",
  "skill.paladin.holy_blast",
  "skill.paladin.shield_of_protection",
]);

type PreviewPhase = "idle" | "loading" | "ready" | "unavailable";

type PreviewState = {
  key: string;
  phase: PreviewPhase;
  preview: BattlePreview | null;
};

const IDLE_PREVIEW: PreviewState = { key: "", phase: "idle", preview: null };

export function isAuditedPreviewSkill(skillId: string | null): boolean {
  return skillId !== null && AUDITED_PREVIEW_SKILL_IDS.has(skillId);
}

function requestKey(request: BattlePreviewRequest | null): string {
  if (!request) return "";
  return [request.expectedRevision, request.actorId, request.skillId, ...request.targetIds].join("\u0000");
}

function sameIds(actual: readonly string[], expected: readonly string[]): boolean {
  return actual.length === expected.length && actual.every((id, index) => id === expected[index]);
}

/**
 * Debounced, revision-bound display lifecycle for server-authored preview facts.
 * This hook deliberately owns no combat formulas or target-legality rules.
 */
export function useBattlePreview(
  provider: BattleProvider,
  request: BattlePreviewRequest | null,
  debounceMs = 90,
): { phase: PreviewPhase; preview: BattlePreview | null } {
  const [state, setState] = useState<PreviewState>(IDLE_PREVIEW);
  const sequence = useRef(0);
  const key = requestKey(request);
  const expectedRevision = request?.expectedRevision;
  const actorId = request?.actorId;
  const skillId = request?.skillId;
  const hasRequest = request !== null;
  // JSON keeps an intentional empty target list distinct from no request.
  // Antivenom Potion and Warlust are authoritative targetless self actions.
  const targetIdsKey = request ? JSON.stringify(request.targetIds) : "";

  useEffect(() => {
    sequence.current += 1;
    const requestSequence = sequence.current;
    if (!hasRequest || expectedRevision === undefined || !actorId || !skillId
      || !provider.previewAction || !isAuditedPreviewSkill(skillId)) {
      return;
    }
    const activeRequest: BattlePreviewRequest = {
      expectedRevision,
      actorId,
      skillId,
      targetIds: JSON.parse(targetIdsKey) as string[],
    };

    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      setState({ key, phase: "loading", preview: null });
      void provider.previewAction!(activeRequest, controller.signal).then((preview) => {
        if (controller.signal.aborted || sequence.current !== requestSequence) return;
        const matchesRequest = preview.revision === activeRequest.expectedRevision
          && preview.actorId === activeRequest.actorId
          && preview.skillId === activeRequest.skillId
          && sameIds(preview.requestedTargetIds, activeRequest.targetIds)
          && sameIds(preview.selectedTargetIds, activeRequest.targetIds);
        if (!matchesRequest) {
          setState(IDLE_PREVIEW);
          return;
        }
        setState({
          key,
          phase: preview.coverage === "authoritative" ? "ready" : "unavailable",
          preview,
        });
      }).catch(() => {
        if (controller.signal.aborted || sequence.current !== requestSequence) return;
        setState({ key, phase: "unavailable", preview: null });
      });
    }, debounceMs);

    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [actorId, debounceMs, expectedRevision, hasRequest, key, provider, skillId, targetIdsKey]);

  return state.key === key ? { phase: state.phase, preview: state.preview } : IDLE_PREVIEW;
}
