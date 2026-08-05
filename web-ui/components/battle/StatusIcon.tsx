import { statusRegistry } from "@/lib/battle/assets";
import type { StatusState } from "@/lib/battle/types";

export function StatusIcon({ status }: { status: StatusState }) {
  const definition = statusRegistry[status.id] ?? { glyph: "?", name: "Unknown status", description: "Details unavailable.", harmful: status.kind === "debuff" };
  const duration = status.roundsRemaining === null ? "" : ` ${status.roundsRemaining} rounds remaining.`;
  const stacks = typeof status.stacks === "number" && Number.isInteger(status.stacks) && status.stacks > 0 ? status.stacks : null;
  const stackDetail = stacks === null ? "" : ` Stack count: ${stacks}.`;
  const stackBadge = stacks === null ? null : stacks > 99 ? "99+" : String(stacks);
  return (
    <span className={`status-icon ${definition.harmful ? "harmful" : "helpful"}`} tabIndex={0}
      onClick={(event) => event.stopPropagation()}
      onKeyDown={(event) => event.stopPropagation()}
      aria-label={`${definition.name}. ${definition.description}${stackDetail}${duration}`}>
      {definition.glyph}
      {stackBadge && <span className="status-stack-badge" aria-hidden="true">{stackBadge}</span>}
      <span role="tooltip"><strong>{definition.name}</strong>{definition.description}{stackDetail}{duration}</span>
    </span>
  );
}
