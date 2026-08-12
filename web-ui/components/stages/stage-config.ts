export type PercentageGeometry = {
  leftPercent: number;
  topPercent: number;
  widthPercent: number;
  heightPercent: number;
};

export type StageDefinition = {
  id: string;
  displayName: string;
  enabled: boolean;
  destination?: string;
  geometry?: PercentageGeometry;
};

export type EnabledStageDefinition = StageDefinition & {
  enabled: true;
  destination: string;
  geometry: PercentageGeometry;
};

export const DEFAULT_STAGE_ID = "arena";

/**
 * Presentation-only stage metadata. Geometry is measured against the complete
 * 1672 x 941 Valley of Champions map, never against the browser viewport.
 * Inactive locations intentionally omit geometry and a destination so they
 * cannot accidentally become interactive before their design is approved.
 */
export const STAGE_DEFINITIONS: readonly StageDefinition[] = [
  {
    id: "arena",
    displayName: "Arena",
    enabled: true,
    destination: "/game",
    geometry: {
      leftPercent: 39.3,
      topPercent: 43.2,
      widthPercent: 23.6,
      heightPercent: 16.5,
    },
  },
  {
    id: "warriors-barrack",
    displayName: "Warrior's Barrack",
    enabled: true,
    destination: "/game",
    geometry: {
      leftPercent: 11.5,
      topPercent: 13.2,
      widthPercent: 22.6,
      heightPercent: 21.8,
    },
  },
  { id: "mages-tower", displayName: "Mage's Tower", enabled: false },
  { id: "rogues-forest", displayName: "Rogue's Forest", enabled: false },
  { id: "paladins-altar", displayName: "Paladin's Altar", enabled: false },
  { id: "priests-cathedral", displayName: "Priest's Cathedral", enabled: false },
] as const;

export function isEnabledStage(stage: StageDefinition): stage is EnabledStageDefinition {
  return stage.enabled && Boolean(stage.destination && stage.geometry);
}

export function resolveEnabledStage(stageId?: string | null): EnabledStageDefinition {
  const fallback = STAGE_DEFINITIONS.find(
    (stage): stage is EnabledStageDefinition =>
      stage.id === DEFAULT_STAGE_ID && isEnabledStage(stage),
  );
  if (!fallback) {
    throw new Error("The default stage must be configured and enabled.");
  }
  return STAGE_DEFINITIONS.find(
    (stage): stage is EnabledStageDefinition => stage.id === stageId && isEnabledStage(stage),
  ) ?? fallback;
}
