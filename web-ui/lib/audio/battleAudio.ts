import { useCallback, useEffect, useId } from "react";
import type { BattleEvent } from "@/lib/battle/types";
import { audioManager, type AudioManager } from "./AudioManager";
import type { SoundId } from "./soundDefinitions";

export function soundIdForBattleEvent(event: BattleEvent): SoundId | null {
  if (event.type === "battleStarted") return "battle.event";
  if (event.type === "skillStarted") return "battle.skill";
  if (event.type === "damageApplied") return "battle.damage";
  if (event.type === "attackEvaded") return "battle.evade";
  if (event.type === "characterDefeated") return "battle.defeated";
  if (event.type === "statusApplied") {
    if (event.statusPresentation === "buff") return "battle.buff";
    if (event.statusPresentation === "debuff") return "battle.debuff";
  }
  return null;
}

/**
 * Battle semantic feedback. Event audio enters only through onActiveEvent,
 * which usePresentationQueue calls for its current ordered event. Ordinary UI
 * interaction feedback belongs to the shared UiAudioBoundary.
 */
export function useBattleAudio(manager: AudioManager = audioManager) {
  const instanceId = useId();

  useEffect(() => {
    const activation = typeof navigator === "undefined"
      ? undefined
      : (navigator as Navigator & { userActivation?: { hasBeenActive: boolean } }).userActivation;
    // Entering a live battle normally follows an explicit Team Builder action.
    // Sticky user activation lets the opening queue use that real interaction
    // without installing a global listener or manufacturing autoplay.
    if (activation?.hasBeenActive) manager.unlock();
  }, [manager]);

  const onActiveEvent = useCallback((event: BattleEvent) => {
    const soundId = soundIdForBattleEvent(event);
    if (!soundId) return;
    manager.play(soundId, { dedupeKey: `${instanceId}.${event.sequence}.${event.id}` });
  }, [instanceId, manager]);

  return { onActiveEvent };
}
