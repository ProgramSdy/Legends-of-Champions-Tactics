/** Measured from the Owner-approved 1897×868 windowed Laptop Large battle. */
export const BATTLE_SCENE_REFERENCE = {
  battlefieldWidth: 1351,
  battlefieldHeight: 560,
  heroRate: 0.7,
} as const;

export type SceneDimensions = { width: number; height: number };

/** CSS background-size: cover uses the larger dimension ratio, including crop. */
export function backgroundCoverScale(field: SceneDimensions, image: SceneDimensions): number {
  if (field.width <= 0 || field.height <= 0 || image.width <= 0 || image.height <= 0) return 0;
  return Math.max(field.width / image.width, field.height / image.height);
}

/** The same rendered scene scale drives artwork and its attached geometry. */
export function battleSceneRate(field: SceneDimensions, image: SceneDimensions): number {
  const referenceCover = backgroundCoverScale(
    { width: BATTLE_SCENE_REFERENCE.battlefieldWidth, height: BATTLE_SCENE_REFERENCE.battlefieldHeight },
    image,
  );
  const currentCover = backgroundCoverScale(field, image);
  return currentCover > 0 && referenceCover > 0
    ? BATTLE_SCENE_REFERENCE.heroRate * currentCover / referenceCover
    : BATTLE_SCENE_REFERENCE.heroRate;
}
