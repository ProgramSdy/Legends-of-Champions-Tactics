export type PercentageGeometry = {
  leftPercent: number;
  topPercent: number;
  widthPercent: number;
  heightPercent: number;
};

export type StagePreviewFocus = {
  xPercent: number;
  yPercent: number;
  scale: number;
  offsetXPercent: number;
  offsetYPercent: number;
};

export type StageDefinition = {
  id: string;
  displayName: string;
  enabled: boolean;
  destination?: string;
  geometry?: PercentageGeometry;
  previewFocus?: StagePreviewFocus;
};

export type EnabledStageDefinition = StageDefinition & {
  enabled: true;
  destination: string;
  geometry: PercentageGeometry;
  previewFocus: StagePreviewFocus;
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
      leftPercent: 37.3,
      topPercent: 43.2,
      widthPercent: 23.6,
      heightPercent: 16.5,
    },
    previewFocus: {
      xPercent: 50,
      yPercent: 51.5,
      scale: 1.85,
      offsetXPercent: 0,
      offsetYPercent: 0,
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
    previewFocus: {
      xPercent: 22.8,
      yPercent: 23.5,
      scale: 1.85,
      offsetXPercent: 72,
      offsetYPercent: 53,
    },
  },
  { id: "mages-tower", displayName: "Mage's Tower", enabled: false },
  { id: "rogues-forest", displayName: "Rogue's Forest", enabled: false },
  {
    id: "paladins-altar",
    displayName: "Paladin's Altar",
    enabled: true,
    destination: "/game",
    geometry: {
      leftPercent: 74.5,
      topPercent: 11.5,
      widthPercent: 15,
      heightPercent: 18,
    },
    previewFocus: {
      xPercent: 80.5,
      yPercent: 20.5,
      scale: 1.85,
      offsetXPercent: -42,
      offsetYPercent: 56,
    },
  },
  { id: "priests-cathedral", displayName: "Priest's Cathedral", enabled: false },
] as const;

export function isEnabledStage(stage: StageDefinition): stage is EnabledStageDefinition {
  return stage.enabled && Boolean(stage.destination && stage.geometry && stage.previewFocus);
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
