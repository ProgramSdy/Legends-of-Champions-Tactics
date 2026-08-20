import type {
  BattleFormationId,
  BattleSize,
  AuthoritativeStructuredStageDefinition,
  HeroDefinitionSummary,
} from "@/lib/battle/types";

export type StructuredStageRewardDefinition = {
  id: string;
  kind: "heroUnlock" | "itemCard";
  heroDefinitionId: string | null;
  notificationMessage: string;
};

export type StructuredStageBattleDefinition = {
  id: string;
  displayOrder: number;
  battleSize: BattleSize;
  enemyDefinitionIds: readonly string[];
  playerFormation: BattleFormationId | null;
  enemyFormation: BattleFormationId | null;
  completionReward: StructuredStageRewardDefinition | null;
};

export type StructuredStageDefinition = {
  stageId: string;
  displayName: string;
  battles: readonly StructuredStageBattleDefinition[];
};

const reward = (
  id: string,
  kind: StructuredStageRewardDefinition["kind"],
  notificationMessage: string,
  heroDefinitionId: string | null = kind === "heroUnlock"
    ? id.replace(/^unlock\./, "")
    : null,
): StructuredStageRewardDefinition => ({ id, kind, heroDefinitionId, notificationMessage });

const PALADIN_PROTECTION_REWARD = reward(
  "unlock.hero.paladin.protection",
  "heroUnlock",
  "Paladin_Protection is unlocked",
);
const PALADIN_RETRIBUTION_REWARD = reward(
  "unlock.hero.paladin.retribution",
  "heroUnlock",
  "Paladin_Retribution is unlocked",
);
const PALADIN_HOLY_REWARD = reward(
  "unlock.hero.paladin.holy",
  "heroUnlock",
  "Paladin_Holy is unlocked",
);
const WARRIOR_BERSERKER_REWARD = reward(
  "unlock.hero.warrior.berserker",
  "heroUnlock",
  "Warrior_Baserker is unlocked",
);
const ITEM_CARD_REWARD = reward(
  "reward.item-card.basic",
  "itemCard",
  "You have granted an item card",
);
const WARRIOR_DEFENCE_REWARD = reward(
  "unlock.hero.warrior.defence",
  "heroUnlock",
  "Warrior_Defence is unlocked",
);

export const STRUCTURED_STAGE_DEFINITIONS: readonly StructuredStageDefinition[] = [
  {
    stageId: "warriors-barrack",
    displayName: "Warrior's Barrack",
    battles: [
      {
        id: "warriors-barrack.battle-1",
        displayOrder: 1,
        battleSize: 2,
        enemyDefinitionIds: ["hero.warrior.berserker", "hero.priest.comprehensiveness"],
        playerFormation: "front-rear",
        enemyFormation: "front-rear",
        completionReward: null,
      },
      {
        id: "warriors-barrack.battle-2",
        displayOrder: 2,
        battleSize: 1,
        enemyDefinitionIds: ["hero.warrior.berserker"],
        playerFormation: null,
        enemyFormation: null,
        completionReward: null,
      },
      {
        id: "warriors-barrack.battle-3",
        displayOrder: 3,
        battleSize: 3,
        enemyDefinitionIds: [
          "hero.warrior.berserker",
          "hero.rogue.comprehensiveness",
          "hero.mage.comprehensiveness",
        ],
        playerFormation: "two-front-one-rear",
        enemyFormation: "two-front-one-rear",
        completionReward: WARRIOR_BERSERKER_REWARD,
      },
      {
        id: "warriors-barrack.battle-4",
        displayOrder: 4,
        battleSize: 2,
        enemyDefinitionIds: ["hero.warrior.berserker", "hero.warrior.weapon_master"],
        playerFormation: "side-by-side",
        enemyFormation: "side-by-side",
        completionReward: null,
      },
      {
        id: "warriors-barrack.battle-5",
        displayOrder: 5,
        battleSize: 1,
        enemyDefinitionIds: ["hero.warrior.weapon_master"],
        playerFormation: null,
        enemyFormation: null,
        completionReward: null,
      },
      {
        id: "warriors-barrack.battle-6",
        displayOrder: 6,
        battleSize: 3,
        enemyDefinitionIds: [
          "hero.warrior.weapon_master",
          "hero.paladin.retribution",
          "hero.priest.discipline",
        ],
        playerFormation: "two-front-one-rear",
        enemyFormation: "two-front-one-rear",
        completionReward: ITEM_CARD_REWARD,
      },
      {
        id: "warriors-barrack.battle-7",
        displayOrder: 7,
        battleSize: 2,
        enemyDefinitionIds: ["hero.warrior.defence", "hero.priest.discipline"],
        playerFormation: "front-rear",
        enemyFormation: "front-rear",
        completionReward: null,
      },
      {
        id: "warriors-barrack.battle-8",
        displayOrder: 8,
        battleSize: 1,
        enemyDefinitionIds: ["hero.warrior.defence"],
        playerFormation: null,
        enemyFormation: null,
        completionReward: null,
      },
      {
        id: "warriors-barrack.battle-9",
        displayOrder: 9,
        battleSize: 3,
        enemyDefinitionIds: [
          "hero.warrior.weapon_master",
          "hero.warrior.defence",
          "hero.warrior.berserker",
        ],
        playerFormation: "all-front",
        enemyFormation: "all-front",
        completionReward: WARRIOR_DEFENCE_REWARD,
      },
    ],
  },
  {
    stageId: "paladins-altar",
    displayName: "Paladin's Altar",
    battles: [
      {
        id: "paladins-altar.battle-1",
        displayOrder: 1,
        battleSize: 2,
        enemyDefinitionIds: ["hero.paladin.protection", "hero.mage.comprehensiveness"],
        playerFormation: "front-rear",
        enemyFormation: "front-rear",
        completionReward: null,
      },
      {
        id: "paladins-altar.battle-2",
        displayOrder: 2,
        battleSize: 1,
        enemyDefinitionIds: ["hero.paladin.protection"],
        playerFormation: null,
        enemyFormation: null,
        completionReward: null,
      },
      {
        id: "paladins-altar.battle-3",
        displayOrder: 3,
        battleSize: 3,
        enemyDefinitionIds: [
          "hero.paladin.protection",
          "hero.warrior.defence",
          "hero.mage.comprehensiveness",
        ],
        playerFormation: "two-front-one-rear",
        enemyFormation: "two-front-one-rear",
        completionReward: PALADIN_PROTECTION_REWARD,
      },
      {
        id: "paladins-altar.battle-4",
        displayOrder: 4,
        battleSize: 2,
        enemyDefinitionIds: ["hero.paladin.retribution", "hero.warrior.weapon_master"],
        playerFormation: "side-by-side",
        enemyFormation: "side-by-side",
        completionReward: null,
      },
      {
        id: "paladins-altar.battle-5",
        displayOrder: 5,
        battleSize: 1,
        enemyDefinitionIds: ["hero.paladin.retribution"],
        playerFormation: null,
        enemyFormation: null,
        completionReward: null,
      },
      {
        id: "paladins-altar.battle-6",
        displayOrder: 6,
        battleSize: 3,
        enemyDefinitionIds: [
          "hero.paladin.protection",
          "hero.paladin.retribution",
          "hero.priest.discipline",
        ],
        playerFormation: "two-front-one-rear",
        enemyFormation: "two-front-one-rear",
        completionReward: PALADIN_RETRIBUTION_REWARD,
      },
      {
        id: "paladins-altar.battle-7",
        displayOrder: 7,
        battleSize: 2,
        enemyDefinitionIds: ["hero.paladin.holy", "hero.rogue.comprehensiveness"],
        playerFormation: "side-by-side",
        enemyFormation: "side-by-side",
        completionReward: null,
      },
      {
        id: "paladins-altar.battle-8",
        displayOrder: 8,
        battleSize: 1,
        enemyDefinitionIds: ["hero.paladin.holy"],
        playerFormation: null,
        enemyFormation: null,
        completionReward: null,
      },
      {
        id: "paladins-altar.battle-9",
        displayOrder: 9,
        battleSize: 3,
        enemyDefinitionIds: [
          "hero.paladin.retribution",
          "hero.paladin.protection",
          "hero.paladin.holy",
        ],
        playerFormation: "all-front",
        enemyFormation: "all-front",
        completionReward: PALADIN_HOLY_REWARD,
      },
    ],
  },
] as const;

export function resolveStructuredStage(
  stageId?: string | null,
): StructuredStageDefinition | null {
  return STRUCTURED_STAGE_DEFINITIONS.find((stage) => stage.stageId === stageId) ?? null;
}

export function missingStructuredStageRosterIds(
  stage: StructuredStageDefinition,
  roster: readonly HeroDefinitionSummary[],
): string[] {
  const rosterIds = new Set(roster.map((hero) => hero.definitionId));
  const configuredIds = stage.battles.flatMap((battle) => battle.enemyDefinitionIds);
  return [...new Set(configuredIds)].filter((definitionId) => !rosterIds.has(definitionId));
}

export function structuredStageMatchesAuthority(
  stage: StructuredStageDefinition,
  authoritative: AuthoritativeStructuredStageDefinition,
): boolean {
  return stage.stageId === authoritative.stageId
    && stage.displayName === authoritative.displayName
    && stage.battles.length === authoritative.battles.length
    && stage.battles.every((battle, index) => {
      const serverBattle = authoritative.battles[index];
      return Boolean(serverBattle)
        && battle.id === serverBattle.id
        && battle.displayOrder === serverBattle.displayOrder
        && battle.battleSize === serverBattle.battleSize
        && battle.enemyFormation === serverBattle.formation
        && battle.enemyDefinitionIds.length === serverBattle.enemyDefinitionIds.length
        && battle.enemyDefinitionIds.every(
          (definitionId, slot) => definitionId === serverBattle.enemyDefinitionIds[slot],
        )
        && (battle.completionReward === null
          ? serverBattle.reward === null
          : serverBattle.reward !== null
            && battle.completionReward.id === serverBattle.reward.rewardId
            && battle.completionReward.kind === serverBattle.reward.kind
            && battle.completionReward.heroDefinitionId === serverBattle.reward.heroDefinitionId
            && battle.completionReward.notificationMessage === serverBattle.reward.notification);
    });
}
