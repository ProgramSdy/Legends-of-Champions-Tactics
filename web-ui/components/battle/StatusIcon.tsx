import { statusRegistry } from "@/lib/battle/assets";
import type { StatusState } from "@/lib/battle/types";

export function StatusIcon({ status }: { status: StatusState }) {
  const definition = statusRegistry[status.id] ?? { glyph: "?", name: "Unknown status", description: "Details unavailable.", harmful: status.kind === "debuff" };
  const duration = status.roundsRemaining === null ? "" : ` ${status.roundsRemaining} rounds remaining.`;
  return (
    <span className={`status-icon ${definition.harmful ? "harmful" : "helpful"}`} tabIndex={0} aria-label={`${definition.name}. ${definition.description}${duration}`}>
      {definition.glyph}
      <span role="tooltip"><strong>{definition.name}</strong>{definition.description}{duration}</span>
    </span>
  );
}
