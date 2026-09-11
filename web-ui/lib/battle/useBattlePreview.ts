"use client";

import { useEffect, useRef, useState } from "react";
import type { BattlePreview, BattlePreviewRequest, BattleProvider } from "./types";

const AUDITED_PREVIEW_SKILL_IDS = new Set([
  "skill.mage.fireball",
  "skill.mage.arcane_missiles",
  "skill.mage.frost_bolt",
  "skill.rogue.sharp_blade",
  "skill.rogue.poisoned_dagger",
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
  const targetIdsKey = request?.targetIds.join("\u0000") ?? "";

  useEffect(() => {
    sequence.current += 1;
    const requestSequence = sequence.current;
    if (expectedRevision === undefined || !actorId || !skillId || !targetIdsKey
      || !provider.previewAction || !isAuditedPreviewSkill(skillId)) {
      return;
    }
    const activeRequest: BattlePreviewRequest = {
      expectedRevision,
      actorId,
      skillId,
      targetIds: targetIdsKey.split("\u0000"),
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
  }, [actorId, debounceMs, expectedRevision, key, provider, skillId, targetIdsKey]);

  return state.key === key ? { phase: state.phase, preview: state.preview } : IDLE_PREVIEW;
}
