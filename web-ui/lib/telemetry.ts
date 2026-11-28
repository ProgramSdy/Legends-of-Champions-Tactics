import { publicApiJson } from "@/lib/publicApi";

export const TELEMETRY_SCHEMA_VERSION = 1 as const;
export const TELEMETRY_SESSION_TIMEOUT_MS = 30 * 60 * 1000;
export const TELEMETRY_ACTIVITY_THROTTLE_MS = 5 * 60 * 1000;
export const TELEMETRY_ACTIVITY_PERSIST_MS = 60 * 1000;
export const TELEMETRY_CLIENT_ERROR_LIMIT = 5;

export type TelemetryEventType =
  | "landing_view"
  | "home_view"
  | "session_activity"
  | "client_error";

export type AcquisitionSource =
  | "itch.io"
  | "reddit"
  | "x"
  | "threads"
  | "taptap"
  | "direct"
  | "other"
  | "unknown";

export interface ClientTelemetryEvent {
  eventId: string;
  eventType: TelemetryEventType;
  schemaVersion: typeof TELEMETRY_SCHEMA_VERSION;
  visitorId: string;
  sessionId: string;
  occurredAtUtc: string;
  eventData: Record<string, string | number | boolean | null>;
}

const SOURCE_ALLOWLIST = new Set<AcquisitionSource>([
  "itch.io",
  "reddit",
  "x",
  "threads",
  "taptap",
  "direct",
  "other",
  "unknown",
]);
const CAMPAIGN_PATTERN = /^[A-Za-z0-9._-]{1,64}$/;

export function isAcquisitionSource(value: unknown): value is AcquisitionSource {
  return typeof value === "string" && SOURCE_ALLOWLIST.has(value as AcquisitionSource);
}

export function validCampaign(value: unknown): value is string | null {
  return value === null || (typeof value === "string" && CAMPAIGN_PATTERN.test(value));
}

export function telemetryCollectionEnabled(
  value = process.env.NEXT_PUBLIC_TELEMETRY_ENABLED,
): boolean {
  return value === "true";
}

export function configuredFeedbackUrl(
  value = process.env.NEXT_PUBLIC_FEEDBACK_URL,
): string | null {
  if (!value) return null;
  try {
    const parsed = new URL(value);
    if (parsed.protocol !== "https:" || parsed.username || parsed.password) return null;
    return parsed.toString();
  } catch {
    return null;
  }
}

export function acquisitionFromSearch(search: string): {
  source: AcquisitionSource;
  campaign: string | null;
} {
  const params = new URLSearchParams(search);
  const candidate = params.get("source")?.trim().toLowerCase() as AcquisitionSource | undefined;
  const source = candidate && isAcquisitionSource(candidate) ? candidate : candidate ? "unknown" : "direct";
  const campaignCandidate = params.get("campaign")?.trim() ?? "";
  return {
    source,
    campaign: CAMPAIGN_PATTERN.test(campaignCandidate) ? campaignCandidate : null,
  };
}

/**
 * Telemetry delivery is deliberately best effort. A failed request must never
 * enter an authentication, save, battle, reward, or navigation error path.
 */
export async function postTelemetryEvent(event: ClientTelemetryEvent): Promise<boolean> {
  if (!telemetryCollectionEnabled()) return false;
  try {
    const result = await publicApiJson<{
      contractVersion: "1.0";
      accepted: boolean;
      duplicate: boolean;
      reason?: string | null;
    }>("/api/v1/telemetry/events", {
      method: "POST",
      body: JSON.stringify(event),
    });
    return result.contractVersion === "1.0" && (result.accepted || result.duplicate);
  } catch {
    return false;
  }
}
