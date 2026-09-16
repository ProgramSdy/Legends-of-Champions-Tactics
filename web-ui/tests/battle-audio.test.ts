import { describe, expect, it } from "vitest";
import { soundIdForBattleEvent } from "@/lib/audio/battleAudio";
import type { BattleEvent } from "@/lib/battle/types";

const event = (type: BattleEvent["type"], extra: Partial<BattleEvent> = {}) => ({
  id: `event-${type}`,
  sequence: 1,
  type,
  ...extra,
} as BattleEvent);

describe("ordered battle audio mapping", () => {
  it.each([
    ["battleStarted", "battle.event"], ["characterMoved", "battle.skill"],
    ["damageApplied", "battle.damage"], ["attackEvaded", "battle.evade"],
    ["characterDefeated", "battle.defeated"],
  ] as const)("maps %s to %s", (type, soundId) => {
    expect(soundIdForBattleEvent(event(type, type === "characterMoved" ? { movement: "lunge" } : {}))).toBe(soundId);
  });

  it("keeps intent-only and return movement events silent so the attack cue aligns with the lunge", () => {
    expect(soundIdForBattleEvent(event("skillStarted"))).toBeNull();
    expect(soundIdForBattleEvent(event("characterMoved", { movement: "return" }))).toBeNull();
  });

  it("uses only authoritative status presentation and leaves neutral status silent", () => {
    expect(soundIdForBattleEvent(event("statusApplied", { statusPresentation: "buff" }))).toBe("battle.buff");
    expect(soundIdForBattleEvent(event("statusApplied", { statusPresentation: "debuff" }))).toBe("battle.debuff");
    expect(soundIdForBattleEvent(event("statusApplied"))).toBeNull();
  });

  it("does not infer sounds from unrelated snapshot/log event types", () => {
    expect(soundIdForBattleEvent(event("battleLog"))).toBeNull();
    expect(soundIdForBattleEvent(event("turnStarted"))).toBeNull();
    expect(soundIdForBattleEvent(event("turnEnded"))).toBeNull();
    expect(soundIdForBattleEvent(event("healingApplied"))).toBeNull();
  });

  it("keeps adjacent same-target damage and status events distinct for queue dedupe keys", () => {
    const first = event("damageApplied", { id: "damage-1", sequence: 20, targetId: "hero-1" });
    const second = event("statusApplied", { id: "poison-1", sequence: 21, targetId: "hero-1", statusPresentation: "debuff" });
    expect(soundIdForBattleEvent(first)).toBe("battle.damage");
    expect(soundIdForBattleEvent(second)).toBe("battle.debuff");
    expect(`${first.sequence}.${first.id}`).not.toBe(`${second.sequence}.${second.id}`);
  });
});
