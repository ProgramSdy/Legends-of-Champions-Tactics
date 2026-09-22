"use client";

import { useEffect, useRef, useState, type CSSProperties, type KeyboardEvent } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { ManualDialog } from "@/components/manual/ManualDialog";
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
  const searchParams = useSearchParams();
  const [activeStageId, setActiveStageId] = useState<string | null>(null);
  const [manualOpen, setManualOpen] = useState(() => searchParams.get("manual") === "open");
  const manualTriggerRef = useRef<HTMLButtonElement>(null);
  const enabledStages = STAGE_DEFINITIONS.filter(isEnabledStage);

  useEffect(() => {
    if (searchParams.get("manual") !== "open") return;
    const params = new URLSearchParams(searchParams.toString());
    params.delete("manual");
    const query = params.toString();
    router.replace(query ? `/stages?${query}` : "/stages", { scroll: false });
  }, [router, searchParams]);

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
      >
        <nav className="stage-map-navigation" aria-label="Stage Map navigation">
          <Link className="stage-map-route title-route" href="/" aria-label="Return to Game Start">
            <span aria-hidden="true">⌂</span>
            <strong>Game Start</strong>
          </Link>
          <button
            className="stage-map-route manual-route"
            type="button"
            ref={manualTriggerRef}
            onClick={() => setManualOpen(true)}
            aria-label="Open Game Manual"
          >
            <span aria-hidden="true">⚙</span>
            <strong>Manual</strong>
          </button>
        </nav>
        <Link
          className="stage-map-route debug-route"
          href="/debug"
          aria-label="Open Engineering Test and Debugging"
        >
          <strong>Engineering Test &amp; Debugging</strong>
          <span aria-hidden="true">⚒</span>
        </Link>
        <ManualDialog open={manualOpen} onClose={() => setManualOpen(false)} triggerRef={manualTriggerRef} />
        <div className="stage-map-canvas" data-coordinate-system="map-percent">
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
      </div>
    </main>
  );
}
