import type { BattleSize, HeroDefinitionSummary } from "@/lib/battle/types";

export type StructuredStageBattleDefinition = {
  id: string;
  displayOrder: number;
  battleSize: BattleSize;
  enemyDefinitionIds: readonly string[];
};

export type StructuredStageDefinition = {
  stageId: string;
  displayName: string;
  allowedPlayerDefinitionIds: readonly string[];
  battles: readonly StructuredStageBattleDefinition[];
};

export const STRUCTURED_STAGE_DEFINITIONS: readonly StructuredStageDefinition[] = [
  {
    stageId: "warriors-barrack",
    displayName: "Warrior's Barrack",
    allowedPlayerDefinitionIds: [
      "hero.warrior.weapon_master",
      "hero.mage.comprehensiveness",
      "hero.priest.comprehensiveness",
      "hero.rogue.comprehensiveness",
    ],
    battles: [
      {
        id: "warriors-barrack.battle-1",
        displayOrder: 1,
        battleSize: 2,
        enemyDefinitionIds: [
          "hero.warrior.defence",
          "hero.priest.comprehensiveness",
        ],
      },
      {
        id: "warriors-barrack.battle-2",
        displayOrder: 2,
        battleSize: 1,
        enemyDefinitionIds: ["hero.warrior.weapon_master"],
      },
      {
        id: "warriors-barrack.battle-3",
        displayOrder: 3,
        battleSize: 3,
        enemyDefinitionIds: [
          "hero.warrior.defence",
          "hero.warrior.berserker",
          "hero.priest.comprehensiveness",
        ],
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
  const configuredIds = [
    ...stage.allowedPlayerDefinitionIds,
    ...stage.battles.flatMap((battle) => battle.enemyDefinitionIds),
  ];
  return [...new Set(configuredIds)].filter((definitionId) => !rosterIds.has(definitionId));
}
