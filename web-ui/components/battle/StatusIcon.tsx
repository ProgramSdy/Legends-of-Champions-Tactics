import { statusRegistry } from "@/lib/battle/assets";
import type { StatusState } from "@/lib/battle/types";

export function StatusIcon({ status, detailsUpdating = false }: { status: StatusState; detailsUpdating?: boolean }) {
  const definition = statusRegistry[status.id] ?? { glyph: "?", name: "Unknown status", description: "Details unavailable.", harmful: status.kind === "debuff" };
  const duration = detailsUpdating || status.roundsRemaining === null ? "" : ` ${status.roundsRemaining} rounds remaining.`;
  const stacks = detailsUpdating ? null : typeof status.stacks === "number" && Number.isInteger(status.stacks) && status.stacks > 0 ? status.stacks : null;
  const stackDetail = stacks === null ? "" : ` Stack count: ${stacks}.`;
  const updatingDetail = detailsUpdating ? " Status details updating." : "";
  const stackBadge = stacks === null ? null : stacks > 99 ? "99+" : String(stacks);
  return (
    <span className={`status-icon ${definition.harmful ? "harmful" : "helpful"}`} tabIndex={0}
      data-status-id={status.id}
      onClick={(event) => event.stopPropagation()}
      onKeyDown={(event) => event.stopPropagation()}
      aria-label={`${definition.name}. ${definition.description}${updatingDetail}${stackDetail}${duration}`}>
      {definition.glyph}
      {stackBadge && <span className="status-stack-badge" aria-hidden="true">{stackBadge}</span>}
      <span role="tooltip"><strong>{definition.name}</strong>{definition.description}{updatingDetail}{stackDetail}{duration}</span>
    </span>
  );
}
