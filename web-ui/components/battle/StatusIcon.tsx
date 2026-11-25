import { useId, useRef, useState } from "react";
import { statusRegistry } from "@/lib/battle/assets";
import type { StatusState } from "@/lib/battle/types";
import { ViewportBoundOverlay } from "./ViewportBoundOverlay";

function StatusArtwork({ asset, glyph }: { asset?: string; glyph: string }) {
  const [failedAsset, setFailedAsset] = useState<string | null>(null);
  const visibleAsset = asset && failedAsset !== asset ? asset : null;

  return visibleAsset ? (
    // eslint-disable-next-line @next/next/no-img-element -- registered local status art needs an immediate glyph fallback.
    <img
      className="status-icon-art"
      src={visibleAsset}
      alt=""
      width={128}
      height={128}
      decoding="async"
      onError={() => setFailedAsset(visibleAsset)}
    />
  ) : glyph;
}

export function StatusIcon({ status, detailsUpdating = false }: { status: StatusState; detailsUpdating?: boolean }) {
  const anchorRef = useRef<HTMLSpanElement>(null);
  const tooltipId = useId();
  const [tooltipOpen, setTooltipOpen] = useState(false);
  const definition = statusRegistry[status.id] ?? { glyph: "?", name: "Unknown status", description: "Details unavailable.", harmful: status.kind === "debuff", asset: undefined };
  const duration = detailsUpdating || status.roundsRemaining === null ? "" : ` Remaining rounds: ${status.roundsRemaining}.`;
  const stacks = detailsUpdating ? null : typeof status.stacks === "number" && Number.isInteger(status.stacks) && status.stacks > 0 ? status.stacks : null;
  const stackDetail = stacks === null ? "" : ` Stack count: ${stacks}.`;
  const updatingDetail = detailsUpdating ? " Status details updating." : "";
  const stackBadge = stacks === null ? null : stacks > 99 ? "99+" : String(stacks);
  return (
    <span ref={anchorRef} className={`status-icon ${definition.harmful ? "harmful" : "helpful"}`} tabIndex={0}
      data-status-id={status.id}
      aria-describedby={tooltipOpen ? tooltipId : undefined}
      onPointerEnter={() => setTooltipOpen(true)}
      onPointerLeave={() => setTooltipOpen(false)}
      onFocus={() => setTooltipOpen(true)}
      onBlur={() => setTooltipOpen(false)}
      onClick={(event) => event.stopPropagation()}
      onKeyDown={(event) => event.stopPropagation()}
      aria-label={`${definition.name}. ${definition.description}${updatingDetail}${stackDetail}${duration}`}>
      <StatusArtwork asset={definition.asset} glyph={definition.glyph} />
      {stackBadge && <span className="status-stack-badge" aria-hidden="true">{stackBadge}</span>}
      {tooltipOpen ? <ViewportBoundOverlay anchorRef={anchorRef} id={tooltipId} role="tooltip" className="status-tooltip-overlay">
        <strong>{definition.name}</strong>{definition.description}{updatingDetail}{stackDetail}{duration}
      </ViewportBoundOverlay> : null}
    </span>
  );
}
