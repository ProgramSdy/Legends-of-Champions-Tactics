import type { BattleCommand, BattleEvent, BattleProvider, BattleSnapshot, CombatantState, PresentationScript, SkillState } from "./types";

const skill = (id: string, displayName: string, description: string, cooldownRemaining = 0, available = true): SkillState => ({
  id, displayName, description, targetMode: "singleEnemy", maximumTargets: 1,
  cooldownRemaining, available, unavailableReason: available ? null : "Cooldown active",
  resourceCost: null,
});

const combatant = (partial: Partial<CombatantState> & Pick<CombatantState, "id" | "displayName" | "specialization" | "sideId" | "slot">): CombatantState => ({
  definitionId: `fixture.${partial.id}`, faculty: partial.specialization, isSummon: false,
  masterCombatantId: null, summonRoundsRemaining: null, isPlayerControlled: partial.sideId === "friendly",
  alive: true, hp: { current: 80, maximum: 80 }, resource: null, statuses: [], skills: [], ...partial,
});

export const fleshPuppet = combatant({
  id: "friendly.arthas.flesh_puppet.1", displayName: "Flesh Puppet", specialization: "Warrior",
  sideId: "friendly", slot: 2, isSummon: true, masterCombatantId: "friendly.arthas",
  summonRoundsRemaining: 3, hp: { current: 50, maximum: 50 },
  skills: [skill("skill.flesh_slam_single", "Flash Slam", "A brutal close-range strike.")],
});

export const initialSnapshot: BattleSnapshot = {
  phase: "awaitingCommand", round: 2, turn: { index: 1, total: 6 }, activeCombatantId: "friendly.arthas", outcome: null,
  turnControl: {
    disposition: "playerCommand", acceptsCommands: true,
    reasonId: null, actorCombatantId: "friendly.arthas",
    sourceCombatantId: null, forcedTargetIds: [],
  },
  sides: [
    { id: "friendly", combatantIds: ["friendly.arthas", "friendly.black_heart"], maxSlots: 3 },
    { id: "enemy", combatantIds: ["enemy.sashein", "enemy.andonidas"], maxSlots: 3 },
  ],
  combatants: {
    "friendly.arthas": combatant({
      id: "friendly.arthas", displayName: "Arthas", specialization: "Necromancer", sideId: "friendly", slot: 0,
      hp: { current: 61, maximum: 81 }, resource: { kind: "Placeholder focus", current: 2, maximum: 3 },
      statuses: [{ id: "status.arcane_guard", instanceId: "status.arcane_guard.1", kind: "buff", roundsRemaining: 2, stacks: null, sourceCombatantId: "friendly.arthas" }],
      skills: [
        skill("skill.life_drain", "Life Drain", "Deal magic damage, then receive engine-supplied healing."),
        skill("skill.stitch_of_agony", "Stitch of Agony", "Apply a damaging status for three rounds.", 2),
        { ...skill("skill.summon_flesh_puppet", "Summon Flesh Puppet", "Call a temporary warrior into an open team slot."), targetMode: "none" },
      ],
    }),
    "friendly.black_heart": combatant({
      id: "friendly.black_heart", displayName: "Black Heart", specialization: "Warlock", sideId: "friendly", slot: 1,
      hp: { current: 91, maximum: 91 }, skills: [skill("skill.shadow_bolt", "Shadow Bolt", "Launch a volatile bolt of shadow.")],
    }),
    "enemy.sashein": combatant({
      id: "enemy.sashein", displayName: "Sashein", specialization: "Necromancer", sideId: "enemy", slot: 0,
      hp: { current: 63, maximum: 81 },
      statuses: [{ id: "status.stitch_of_agony", instanceId: "status.stitch_of_agony.1", kind: "debuff", roundsRemaining: 2, stacks: null, sourceCombatantId: "friendly.arthas" }],
    }),
    "enemy.andonidas": combatant({
      id: "enemy.andonidas", displayName: "Andonidas", specialization: "Mage", sideId: "enemy", slot: 1,
      hp: { current: 49, maximum: 76 },
      statuses: [{ id: "status.arcane_guard", instanceId: "status.arcane_guard.2", kind: "buff", roundsRemaining: 1, stacks: null, sourceCombatantId: "enemy.andonidas" }],
    }),
  },
  turnOrder: [
    { combatantId: "friendly.arthas", hasActed: false, isCurrent: true },
    { combatantId: "enemy.sashein", hasActed: false, isCurrent: false },
    { combatantId: "friendly.black_heart", hasActed: false, isCurrent: false },
    { combatantId: "enemy.andonidas", hasActed: false, isCurrent: false },
  ],
  legalActions: [
    { skillId: "skill.life_drain", actorId: "friendly.arthas", minimumTargets: 1, maximumTargets: 1, validTargetIds: ["enemy.sashein", "enemy.andonidas"] },
    { skillId: "skill.stitch_of_agony", actorId: "friendly.arthas", minimumTargets: 1, maximumTargets: 1, validTargetIds: ["enemy.sashein", "enemy.andonidas"] },
    { skillId: "skill.summon_flesh_puppet", actorId: "friendly.arthas", minimumTargets: 0, maximumTargets: 0, validTargetIds: [] },
  ],
};

const ragnar = combatant({
  id: "friendly.ragnar", definitionId: "hero.warrior.weapon_master", displayName: "Ragnar",
  faculty: "Warrior", specialization: "Weapon Master", sideId: "friendly", slot: 0,
  hp: { current: 102, maximum: 102 },
  skills: [
    skill("skill.warrior.fatal_strike", "Fatal Strike", "A decisive weapon strike that can hinder healing."),
    skill("skill.warrior.armor_crush", "Armor Crush", "A crushing attack that can break armour."),
    { ...skill("skill.warrior.antivenom_potion", "Antivenom Potion", "Recover and resist poison."), targetMode: "none", maximumTargets: 0 },
  ],
});

const nighthawk = combatant({
  id: "enemy.nighthawk", definitionId: "hero.rogue.comprehensiveness", displayName: "Nighthawk",
  faculty: "Rogue", specialization: "Comprehensiveness", sideId: "enemy", slot: 0,
  hp: { current: 84, maximum: 84 }, isPlayerControlled: false,
  skills: [
    skill("skill.rogue.sharp_blade", "Sharp Blade", "A swift blade attack that can cause bleeding."),
    skill("skill.rogue.poisoned_dagger", "Poisoned Dagger", "A poisoned attack that can apply or stack poison."),
    { ...skill("skill.rogue.shadow_evasion", "Shadow Evasion", "Enter a heightened evasive stance."), targetMode: "none", maximumTargets: 0 },
  ],
});

export function createFormatFixture(size: 1 | 2 | 3): BattleSnapshot {
  const snapshot = clone(initialSnapshot);
  const friendlyIds = ["friendly.ragnar", "friendly.black_heart", "friendly.arthas"].slice(0, size);
  const enemyIds = ["enemy.nighthawk", "enemy.andonidas", "enemy.sashein"].slice(0, size);
  snapshot.combatants["friendly.ragnar"] = clone(ragnar);
  snapshot.combatants["enemy.nighthawk"] = clone(nighthawk);
  [...friendlyIds, ...enemyIds].forEach((id, index) => {
    snapshot.combatants[id].slot = index % size;
  });
  snapshot.sides = [
    { id: "friendly", combatantIds: friendlyIds, maxSlots: size },
    { id: "enemy", combatantIds: enemyIds, maxSlots: size },
  ];
  snapshot.activeCombatantId = "friendly.ragnar";
  snapshot.turnControl = {
    disposition: "playerCommand", acceptsCommands: true,
    reasonId: null, actorCombatantId: "friendly.ragnar",
    sourceCombatantId: null, forcedTargetIds: [],
  };
  snapshot.turnOrder = Array.from({ length: size }, (_, index) => [
    { combatantId: friendlyIds[index], hasActed: false, isCurrent: index === 0 },
    { combatantId: enemyIds[index], hasActed: false, isCurrent: false },
  ]).flat();
  snapshot.turn = { index: 1, total: size * 2 };
  snapshot.legalActions = ragnar.skills.map((item) => ({
    skillId: item.id,
    actorId: ragnar.id,
    minimumTargets: item.targetMode === "none" ? 0 : 1,
    maximumTargets: item.targetMode === "none" ? 0 : 1,
    validTargetIds: item.targetMode === "none" ? [] : enemyIds,
  }));
  return snapshot;
}

const clone = <T,>(value: T): T => structuredClone(value);
const event = (sequence: number, type: BattleEvent["type"], message: string, rest: Partial<BattleEvent> = {}): BattleEvent =>
  ({ id: `evt.demo.${sequence}`, sequence, type, message, ...rest });

function script(id: string, current: BattleSnapshot, revision: number, selectedTargetId?: string): PresentationScript {
  const snapshot = clone(current);
  const enemyTargetId = selectedTargetId && snapshot.combatants[selectedTargetId]?.sideId === "enemy" ? selectedTargetId : "enemy.sashein";
  const enemyTarget = snapshot.combatants[enemyTargetId];
  let events: BattleEvent[] = [];
  let label = "";
  let eventType: PresentationScript["eventType"] = "magic";
  if (id === "magic") {
    label = "Life Drain"; eventType = "magic";
    const damageAfter = Math.max(0, enemyTarget.hp.current - 18);
    const healingAfter = Math.min(snapshot.combatants["friendly.arthas"].hp.maximum, snapshot.combatants["friendly.arthas"].hp.current + 12);
    enemyTarget.hp.current = damageAfter;
    snapshot.combatants["friendly.arthas"].hp.current = healingAfter;
    events = [
      event(1, "skillStarted", `Arthas casts Life Drain on ${enemyTarget.displayName}.`, { sourceId: "friendly.arthas", targetId: enemyTargetId, skillId: "skill.life_drain", effectHint: "magic" }),
      event(2, "projectileLaunched", `Necrotic energy arcs toward ${enemyTarget.displayName}.`, { sourceId: "friendly.arthas", targetId: enemyTargetId, effectHint: "magic" }),
      event(3, "damageApplied", `${enemyTarget.displayName} takes 18 magic damage.`, { targetId: enemyTargetId, amount: 18, hpAfter: { current: damageAfter, maximum: enemyTarget.hp.maximum }, effectHint: "magic" }),
      event(4, "healingApplied", "Life Drain restores 12 health to Arthas.", { sourceId: "friendly.arthas", targetId: "friendly.arthas", amount: 12, hpAfter: { current: healingAfter, maximum: snapshot.combatants["friendly.arthas"].hp.maximum }, effectHint: "healing" }),
    ];
  } else if (id === "healing") {
    label = "Life Drain heal"; eventType = "healing";
    const healingAfter = Math.min(snapshot.combatants["friendly.arthas"].hp.maximum, snapshot.combatants["friendly.arthas"].hp.current + 12);
    snapshot.combatants["friendly.arthas"].hp.current = healingAfter;
    events = [
      event(1, "skillStarted", "Life Drain restores Arthas.", { sourceId: "friendly.arthas", effectHint: "healing" }),
      event(2, "healingApplied", "Arthas recovers 12 health.", { targetId: "friendly.arthas", amount: 12, hpAfter: { current: healingAfter, maximum: 81 }, effectHint: "healing" }),
    ];
  } else if (id === "melee") {
    label = "Flash Slam"; eventType = "melee";
    if (!snapshot.combatants[fleshPuppet.id]) { snapshot.sides[0].combatantIds.push(fleshPuppet.id); snapshot.combatants[fleshPuppet.id] = clone(fleshPuppet); }
    const meleeAfter = Math.max(0, snapshot.combatants["enemy.andonidas"].hp.current - 22);
    snapshot.combatants["enemy.andonidas"].hp.current = meleeAfter;
    events = [
      event(1, "characterMoved", "Flesh Puppet lunges forward.", { sourceId: fleshPuppet.id, targetId: "enemy.andonidas", movement: "lunge", effectHint: "melee" }),
      event(2, "damageApplied", "Andonidas takes 22 damage.", { sourceId: fleshPuppet.id, targetId: "enemy.andonidas", amount: 22, hpAfter: { current: meleeAfter, maximum: 76 }, effectHint: "melee" }),
      event(3, "characterMoved", "Flesh Puppet returns to formation.", { sourceId: fleshPuppet.id, movement: "return", effectHint: "melee" }),
    ];
  } else if (id === "status") {
    label = "Stitch of Agony"; eventType = "status";
    const existing = enemyTarget.statuses.find((item) => item.id === "status.stitch_of_agony");
    if (existing) existing.roundsRemaining = 3;
    else enemyTarget.statuses.push({ id: "status.stitch_of_agony", instanceId: `status.stitch_of_agony.${revision}`, kind: "debuff", roundsRemaining: 3, stacks: null, sourceCombatantId: "friendly.arthas" });
    events = [
      event(1, "skillStarted", `Arthas casts Stitch of Agony on ${enemyTarget.displayName}.`, { sourceId: "friendly.arthas", targetId: enemyTargetId, effectHint: "status" }),
      event(2, "statusApplied", `Stitch of Agony afflicts ${enemyTarget.displayName} for 3 rounds.`, { sourceId: "friendly.arthas", targetId: enemyTargetId, statusId: "status.stitch_of_agony", roundsRemaining: 3, effectHint: "status", statusPresentation: "debuff" }),
    ];
  } else if (id === "evade") {
    label = "Shadow Bolt evade"; eventType = "evade";
    events = [
      event(1, "projectileLaunched", "Black Heart launches Shadow Bolt.", { sourceId: "friendly.black_heart", targetId: "enemy.andonidas", effectHint: "magic" }),
      event(2, "attackEvaded", "Andonidas evades Shadow Bolt.", { sourceId: "friendly.black_heart", targetId: "enemy.andonidas", movement: "offset", effectHint: "magic" }),
    ];
  } else {
    label = "Summon Flesh Puppet"; eventType = "summon";
    if (!snapshot.combatants[fleshPuppet.id]) {
      snapshot.sides[0].combatantIds.push(fleshPuppet.id); snapshot.combatants[fleshPuppet.id] = clone(fleshPuppet);
      snapshot.turnOrder.splice(1, 0, { combatantId: fleshPuppet.id, hasActed: false, isCurrent: false });
    }
    events = [
      event(1, "skillStarted", "Arthas opens a forbidden summoning seal.", { sourceId: "friendly.arthas", skillId: "skill.summon_flesh_puppet", effectHint: "summon" }),
      event(2, "characterSummoned", "Flesh Puppet joins the friendly team.", { sourceId: "friendly.arthas", targetId: fleshPuppet.id, combatant: clone(fleshPuppet), effectHint: "summon" }),
    ];
  }
  return { id, label, eventType, events, snapshot, revision };
}

export class MockBattleProvider implements BattleProvider {
  private snapshot: BattleSnapshot;
  private revision = 1;

  constructor(snapshot: BattleSnapshot = initialSnapshot) {
    this.snapshot = clone(snapshot);
  }

  async getState() { return { snapshot: clone(this.snapshot), revision: this.revision }; }

  async submitCommand(command: BattleCommand): Promise<PresentationScript> {
    if (command.expectedRevision !== this.revision) throw new Error("The battle state changed. Please select the action again.");
    if (!this.snapshot.turnControl.acceptsCommands || this.snapshot.turnControl.disposition !== "playerCommand") {
      throw new Error("The current turn does not accept player commands.");
    }
    if (command.actorId !== this.snapshot.activeCombatantId) throw new Error("That combatant is not the active actor.");
    const legal = this.snapshot.legalActions.find((action) => action.actorId === command.actorId && command.type === "useSkill" && action.skillId === command.skillId);
    if (command.type === "useSkill" && (
      !legal
      || command.targetIds.length < legal.minimumTargets
      || command.targetIds.length > legal.maximumTargets
      || new Set(command.targetIds).size !== command.targetIds.length
      || command.targetIds.some((id) => !legal.validTargetIds.includes(id))
    )) throw new Error("That command is not legal in the current snapshot.");
    const id = command.type === "endTurn" ? "magic" :
      command.skillId === "skill.life_drain" ? "magic" :
      command.skillId === "skill.stitch_of_agony" ? "status" : "summon";
    return this.resolve(id, command.type === "useSkill" ? command.targetIds[0] : undefined);
  }

  async runDemo(id: string): Promise<PresentationScript> { return this.resolve(id); }

  private resolve(id: string, targetId?: string) {
    const result = script(id, this.snapshot, this.revision + 1, targetId);
    this.snapshot = clone(result.snapshot);
    this.revision = result.revision;
    return result;
  }
}
