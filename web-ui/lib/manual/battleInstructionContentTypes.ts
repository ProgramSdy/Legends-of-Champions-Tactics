export const BATTLE_INSTRUCTION_CHAPTER_IDS = [
  "quick-start",
  "battle-formats",
  "formations",
  "interface",
  "turns-victory",
  "effects-tactics",
] as const;

export type BattleInstructionChapterId = typeof BATTLE_INSTRUCTION_CHAPTER_IDS[number];
export type BattleInstructionItem = { id?: string; title: string; text: string };

export type BattleInstructionChapter = {
  id: BattleInstructionChapterId;
  title: string;
  kicker: string;
  introduction: string;
  steps?: readonly BattleInstructionItem[];
  callout?: string;
  legalTargeting?: string;
  positionDamage?: string;
  hitChance?: string;
  otherEffects?: string;
  markers?: readonly BattleInstructionItem[];
  agility?: string;
  victory?: string;
  example?: string;
  effects?: readonly BattleInstructionItem[];
  scenarios?: readonly BattleInstructionItem[];
};

export type BattleInstructionContent = {
  title: string;
  subtitle: string;
  chapters: readonly BattleInstructionChapter[];
};
