export const BATTLE_BACKGROUNDS = [
  "/game-images/battle-scenes/backgrounds/Battle_Scene_BG01.png",
  "/game-images/battle-scenes/backgrounds/Battle_Scene_BG02.png",
  "/game-images/battle-scenes/backgrounds/Battle_Scene_BG03.png",
] as const;

export function pickRandomBattleBackground(random: () => number = Math.random): string {
  const index = Math.min(
    BATTLE_BACKGROUNDS.length - 1,
    Math.max(0, Math.floor(random() * BATTLE_BACKGROUNDS.length)),
  );
  return BATTLE_BACKGROUNDS[index];
}
