import { LiveBattleProvider } from "./liveProvider";
import {
  BattleProviderError,
  type BattleSnapshot,
  type PresentationScript,
} from "./types";

interface DebugAutoActionResult {
  accepted: boolean;
  commandId: string;
  revision: number;
  events?: PresentationScript["events"];
  snapshot: BattleSnapshot;
  code?: string;
  message?: string;
}

/** Development-only provider extension. This module is imported by /debug only. */
export class DebugBattleProvider extends LiveBattleProvider {
  async submitAutoAction(expectedRevision: number): Promise<PresentationScript> {
    if (!this.battleId) throw new BattleProviderError("The live battle session has not initialized.", "adapter");
    const envelope = await this.request<DebugAutoActionResult>(
      `/api/v1/debug/battles/${encodeURIComponent(this.battleId)}/auto-actions`,
      { method: "POST", body: JSON.stringify({ expectedRevision }) },
    );
    const result = envelope.data;
    if (!result
      || typeof result.accepted !== "boolean"
      || !Number.isInteger(result.revision)
      || typeof result.snapshot !== "object"
      || result.snapshot === null) {
      throw new BattleProviderError("The debug service returned an unsupported automatic action result.", "adapter");
    }
    this.state = { revision: result.revision, snapshot: result.snapshot };
    if (!result.accepted) {
      throw new BattleProviderError(
        result.message ?? "The automatic action was rejected.",
        result.code === "staleRevision" ? "stale" : "rejected",
        result.snapshot,
        result.revision,
        result.code,
      );
    }
    if (!Array.isArray(result.events)) {
      throw new BattleProviderError("The debug service returned an invalid automatic action event list.", "adapter");
    }
    return {
      id: result.commandId || `auto.${result.revision}`,
      label: result.events.at(0)?.message ?? "Automatic battle action",
      eventType: result.events.find((event) => event.effectHint)?.effectHint ?? "magic",
      events: result.events,
      snapshot: result.snapshot,
      revision: result.revision,
    };
  }
}
