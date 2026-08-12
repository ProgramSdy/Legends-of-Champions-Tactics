import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { BattleScreen } from "@/components/battle/BattleScreen";
import { MockBattleProvider } from "@/lib/battle/fixture";
import type { BattleEvent, DamagePreventedEvent, StatusState } from "@/lib/battle/types";

const newStatuses = [
  ["status.purify_healing", "Purify Healing", "buff"],
  ["status.shield_of_protection", "Shield of Protection", "buff"],
  ["status.warlust", "Warlust", "buff"],
  ["status.bleeding_moon_slash", "Moon Slash Bleeding", "debuff"],
  ["status.blood_frenzy", "Blood Frenzy", "buff"],
] as const;

const statusState = (id: string, kind: StatusState["kind"], index: number): StatusState => ({
  id,
  instanceId: `ui-016.status.${index}`,
  kind,
  roundsRemaining: 2,
  stacks: null,
  sourceCombatantId: "friendly.arthas",
});

describe("UI-016 status presentation", () => {
  it("uses shared readable metadata in both team panels and battlefield overheads", async () => {
    const provider = new MockBattleProvider();
    const snapshot = (await provider.getState()).snapshot;
    Object.values(snapshot.combatants).forEach((combatant) => { combatant.statuses = []; });
    snapshot.combatants["friendly.arthas"].statuses = newStatuses.slice(0, 3).map(([id, , kind], index) => statusState(id, kind, index));
    snapshot.combatants["enemy.sashein"].statuses = newStatuses.slice(3).map(([id, , kind], index) => statusState(id, kind, index + 3));

    render(<BattleScreen provider={new MockBattleProvider(snapshot)} />);
    await screen.findByRole("region", { name: "Battlefield" });

    for (const [id, name, kind] of newStatuses) {
      const icons = document.querySelectorAll<HTMLElement>(`[data-status-id='${id}']`);
      expect(icons).toHaveLength(2);
      expect([...icons].every((icon) => icon.getAttribute("aria-label")?.includes(name))).toBe(true);
      expect([...icons].every((icon) => icon.getAttribute("aria-label")?.includes("2 rounds remaining"))).toBe(true);
      expect([...icons].every((icon) => !icon.getAttribute("aria-label")?.includes("Unknown status"))).toBe(true);
      expect([...icons].every((icon) => icon.classList.contains(kind === "debuff" ? "harmful" : "helpful"))).toBe(true);
    }

    expect(document.querySelectorAll(".team-panel.friendly [data-status-id]")).toHaveLength(3);
    expect(document.querySelectorAll(".team-panel.enemy [data-status-id]")).toHaveLength(2);
    expect(document.querySelectorAll(".battlefield-statuses [data-status-id]")).toHaveLength(5);
  });

  it.each(newStatuses)("anchors %s application using the supplied %s presentation contract", async (statusId, _name, presentation) => {
    const provider = new MockBattleProvider();
    const snapshot = (await provider.getState()).snapshot;
    const targetId = presentation === "debuff" ? "enemy.sashein" : "friendly.arthas";
    const event = {
      id: `ui-016.apply.${statusId}`,
      sequence: 1,
      type: "statusApplied",
      sourceId: "friendly.arthas",
      targetId,
      statusId,
      roundsRemaining: 2,
      statusPresentation: presentation,
      effectHint: "status",
      message: `${statusId} applied.`,
    } satisfies BattleEvent;

    render(<BattleScreen provider={provider} mockDemos={[{
      id: statusId,
      label: `Apply ${statusId}`,
      run: async () => ({ id: statusId, label: statusId, eventType: "status", events: [event], snapshot, revision: 2 }),
    }]} />);
    await screen.findByRole("region", { name: "Battlefield" });
    fireEvent.click(screen.getByRole("button", { name: "×2" }));
    fireEvent.click(screen.getByRole("button", { name: `Apply ${statusId}` }));

    await waitFor(() => expect(document.querySelector(
      `[data-combatant-id='${targetId}'] .target-effect.effect-${presentation}`,
    )).toBeInTheDocument());
  });
});

describe("UI-016 Shield of Protection prevention feedback", () => {
  it("renders the typed zero-damage outcome and golden shield on the supplied target in event order", async () => {
    const provider = new MockBattleProvider();
    const snapshot = (await provider.getState()).snapshot;
    const preventionEvent = {
      id: "ui-016.prevented",
      sequence: 2,
      type: "damagePrevented",
      sourceId: "enemy.sashein",
      targetId: "friendly.arthas",
      skillId: "skill.test.attack",
      amount: 0,
      reasonId: "status.shield_of_protection",
      effectHint: "melee",
      message: "Shield of Protection prevents all damage to Arthas.",
    } satisfies DamagePreventedEvent;
    const events = [
      {
        id: "ui-016.attack", sequence: 1, type: "skillStarted", sourceId: "enemy.sashein",
        targetId: "friendly.arthas", skillId: "skill.test.attack", effectHint: "melee",
        message: "Sashein attacks Arthas.",
      },
      preventionEvent,
    ] satisfies BattleEvent[];

    render(<BattleScreen provider={provider} mockDemos={[{
      id: "shield-prevention",
      label: "Shield prevention",
      run: async () => ({ id: "shield-prevention", label: "Shield prevention", eventType: "melee", events, snapshot, revision: 2 }),
    }]} />);
    await screen.findByRole("region", { name: "Battlefield" });
    fireEvent.click(screen.getByRole("button", { name: "×2" }));
    fireEvent.click(screen.getByRole("button", { name: "Shield prevention" }));

    const target = document.querySelector("[data-combatant-id='friendly.arthas']")!;
    await waitFor(() => expect(target.querySelector(".target-effect.effect-damage-prevented.gold")).toBeInTheDocument());
    expect(target.querySelector("[data-effect-target='friendly.arthas']")).toBeInTheDocument();
    expect(target.querySelector(".combat-text.prevented")).toHaveTextContent("0");
    expect(target.querySelector(".combat-text.prevented")).toHaveAccessibleName("0 damage");
    expect(document.querySelector(".battlefield > .effect-damage-prevented")).not.toBeInTheDocument();

    const attackLog = await screen.findByText("Sashein attacks Arthas.");
    const preventionLog = await screen.findByText("Shield of Protection prevents all damage to Arthas.");
    expect(attackLog.compareDocumentPosition(preventionLog) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("does not infer shield feedback from shield state, unchanged HP, a landed zero, or an evade", async () => {
    const provider = new MockBattleProvider();
    const snapshot = (await provider.getState()).snapshot;
    snapshot.combatants["friendly.arthas"].statuses.push(statusState("status.shield_of_protection", "buff", 9));
    const events = [
      {
        id: "ui-016.zero", sequence: 1, type: "damageApplied", sourceId: "enemy.sashein",
        targetId: "friendly.arthas", skillId: "skill.zero", amount: 0,
        hpAfter: { ...snapshot.combatants["friendly.arthas"].hp }, effectHint: "melee",
        message: "The landed hit deals zero damage.",
      },
      {
        id: "ui-016.evade", sequence: 2, type: "attackEvaded", sourceId: "enemy.sashein",
        targetId: "friendly.arthas", skillId: "skill.evade", effectHint: "melee",
        message: "Arthas evades the attack.",
      },
    ] satisfies BattleEvent[];

    render(<BattleScreen provider={new MockBattleProvider(snapshot)} mockDemos={[{
      id: "false-positive-boundaries",
      label: "False-positive boundaries",
      run: async () => ({ id: "false-positive-boundaries", label: "Boundaries", eventType: "melee", events, snapshot, revision: 2 }),
    }]} />);
    await screen.findByRole("region", { name: "Battlefield" });
    expect(document.querySelector(".effect-damage-prevented")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("0 damage")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "×2" }));
    fireEvent.click(screen.getByRole("button", { name: "False-positive boundaries" }));
    expect(await screen.findByText("−0")).toBeVisible();
    expect(document.querySelector(".effect-damage-prevented")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("0 damage")).not.toBeInTheDocument();
    expect(await screen.findByText("EVADE")).toBeVisible();
    expect(document.querySelector(".effect-damage-prevented")).not.toBeInTheDocument();
  });

  it("keeps prevention feedback visible without motion when reduced motion is requested", () => {
    const css = readFileSync("app/globals.css", "utf8").replace(/\s+/g, "");
    expect(css).toMatch(/@media\(prefers-reduced-motion:reduce\)[^{]*\{[^}]*\*[^}]*animation-duration:\.01ms!important/);
    expect(css).toMatch(/\.target-effect\.effect-damage-prevented,\.combat-text\.prevented\{animation:none!important;opacity:1!important\}/);
  });
});
