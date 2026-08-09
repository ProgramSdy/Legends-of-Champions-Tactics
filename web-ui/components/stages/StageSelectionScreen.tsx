"use client";

import { useState, type CSSProperties, type KeyboardEvent } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import {
  STAGE_DEFINITIONS,
  isEnabledStage,
  type PercentageGeometry,
} from "./stage-config";

const STAGE_MAP = "/game-images/Stage_Map/valley_of_champions.png";

type StageSelectionScreenProps = {
  debugHotspots?: boolean;
};

type HotspotStyle = CSSProperties & {
  "--stage-left": string;
  "--stage-top": string;
  "--stage-width": string;
  "--stage-height": string;
};

function hotspotStyle(geometry: PercentageGeometry): HotspotStyle {
  return {
    "--stage-left": `${geometry.leftPercent}%`,
    "--stage-top": `${geometry.topPercent}%`,
    "--stage-width": `${geometry.widthPercent}%`,
    "--stage-height": `${geometry.heightPercent}%`,
  };
}

export function StageSelectionScreen({ debugHotspots = false }: StageSelectionScreenProps) {
  const router = useRouter();
  const [activeStageId, setActiveStageId] = useState<string | null>(null);
  const enabledStages = STAGE_DEFINITIONS.filter(isEnabledStage);

  function activateStage(stageId: string, destination: string) {
    router.push(`${destination}?stage=${encodeURIComponent(stageId)}`);
  }

  function handleStageKeyDown(
    event: KeyboardEvent<HTMLButtonElement>,
    stageId: string,
    destination: string,
  ) {
    if (event.key !== "Enter" && event.key !== " ") {
      return;
    }
    event.preventDefault();
    activateStage(stageId, destination);
  }

  return (
    <main className="stage-selection-screen">
      <h1 className="sr-only">Choose a stage</h1>
      <div
        className={`stage-map-frame${debugHotspots ? " debug-hotspots" : ""}`}
        data-coordinate-system="map-percent"
      >
        <Image
          className="stage-map-image"
          src={STAGE_MAP}
          alt=""
          aria-hidden="true"
          fill
          priority
          sizes="100vw"
          unoptimized
        />
        {enabledStages.map((stage) => (
          <button
            key={stage.id}
            type="button"
            className={`stage-hotspot${activeStageId === stage.id ? " is-active" : ""}`}
            data-stage-id={stage.id}
            aria-label={`Enter ${stage.displayName}`}
            style={hotspotStyle(stage.geometry)}
            onMouseEnter={() => setActiveStageId(stage.id)}
            onMouseLeave={() => setActiveStageId(null)}
            onFocus={() => setActiveStageId(stage.id)}
            onBlur={() => setActiveStageId(null)}
            onClick={() => activateStage(stage.id, stage.destination)}
            onKeyDown={(event) => handleStageKeyDown(event, stage.id, stage.destination)}
          >
            <span className="stage-hotspot-glow" aria-hidden="true" />
            <span className="stage-hotspot-label" aria-hidden="true">
              <strong>{stage.displayName}</strong>
              <small>Available</small>
            </span>
            {debugHotspots ? (
              <span
                className="stage-hotspot-debug"
                data-testid="stage-hotspot-debug"
                aria-hidden="true"
              >
                {stage.displayName}
              </span>
            ) : null}
          </button>
        ))}
      </div>
    </main>
  );
}
