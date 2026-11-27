export const BATTLE_BACKGROUND =
  "/game-images/battle-scenes/backgrounds/Battle_Scene_BG03.png";

/** Source dimensions only; each scene is independently calibrated at the same
 * approved battlefield reference rather than treating source pixels as world units. */
export const BATTLE_BACKGROUND_DIMENSIONS: Record<string, { width: number; height: number }> = {
  "/game-images/battle-scenes/backgrounds/Battle_Scene_BG01.png": { width: 1672, height: 941 },
  "/game-images/battle-scenes/backgrounds/Battle_Scene_BG02.png": { width: 1652, height: 952 },
  [BATTLE_BACKGROUND]: { width: 1536, height: 1024 },
};
