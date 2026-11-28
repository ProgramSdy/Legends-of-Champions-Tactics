"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  type ReactNode,
} from "react";
import {
  TELEMETRY_ACTIVITY_PERSIST_MS,
  TELEMETRY_ACTIVITY_THROTTLE_MS,
  TELEMETRY_CLIENT_ERROR_LIMIT,
  TELEMETRY_SCHEMA_VERSION,
  TELEMETRY_SESSION_TIMEOUT_MS,
  acquisitionFromSearch,
  isAcquisitionSource,
  postTelemetryEvent,
  telemetryCollectionEnabled,
  validCampaign,
  type AcquisitionSource,
  type ClientTelemetryEvent,
  type TelemetryEventType,
} from "@/lib/telemetry";

const VISITOR_KEY = "loct.telemetry.visitor.v1";
const SESSION_KEY = "loct.telemetry.session.v1";

interface StoredVisitor {
  id: string;
  firstSource: AcquisitionSource;
  firstCampaign: string | null;
}

interface StoredSession {
  id: string;
  startedAtMs: number;
  lastActivityAtMs: number;
  lastActivityEventAtMs: number;
  source: AcquisitionSource;
  campaign: string | null;
  landingEventId: string;
  landingAcknowledged: boolean;
  homeEventId: string;
  homeAcknowledged: boolean;
  clientErrorCount: number;
}

interface RuntimeState {
  visitor: StoredVisitor;
  session: StoredSession;
}

interface TelemetryContextValue {
  enabled: boolean;
  recordHomeView(): void;
}

const DISABLED_CONTEXT: TelemetryContextValue = {
  enabled: false,
  recordHomeView: () => {},
};
const TelemetryContext = createContext<TelemetryContextValue>(DISABLED_CONTEXT);

function safeRead<T>(key: string): T | null {
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? JSON.parse(raw) as T : null;
  } catch {
    return null;
  }
}

function safeWrite(key: string, value: unknown): void {
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Storage denial is a telemetry failure, never an application failure.
  }
}

function uuid(): string {
  if (typeof crypto.randomUUID === "function") return crypto.randomUUID();
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = Array.from(bytes, (value) => value.toString(16).padStart(2, "0"));
  return `${hex.slice(0, 4).join("")}-${hex.slice(4, 6).join("")}-${hex.slice(6, 8).join("")}-${hex.slice(8, 10).join("")}-${hex.slice(10).join("")}`;
}

function validId(value: unknown): value is string {
  return typeof value === "string"
    && /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value);
}

function validVisitor(value: StoredVisitor | null): value is StoredVisitor {
  return Boolean(value
    && validId(value.id)
    && isAcquisitionSource(value.firstSource)
    && validCampaign(value.firstCampaign));
}

function validSession(value: StoredSession | null, now: number): value is StoredSession {
  return Boolean(value
    && validId(value.id)
    && validId(value.landingEventId)
    && validId(value.homeEventId)
    && isAcquisitionSource(value.source)
    && validCampaign(value.campaign)
    && Number.isFinite(value.startedAtMs)
    && Number.isFinite(value.lastActivityAtMs)
    && Number.isFinite(value.lastActivityEventAtMs)
    && Number.isInteger(value.clientErrorCount)
    && value.clientErrorCount >= 0
    && now - value.lastActivityAtMs >= 0
    && now - value.lastActivityAtMs < TELEMETRY_SESSION_TIMEOUT_MS);
}

function routeIdForPath(pathname: string): string {
  if (pathname === "/") return "startup";
  if (pathname === "/stages") return "stage_map";
  if (pathname === "/game") return "battle";
  if (pathname === "/manual/heroes") return "hero_gallery";
  if (pathname === "/manual/battle-instruction") return "battle_instruction";
  if (pathname.startsWith("/game/")) return "team_builder";
  return "unknown";
}

function loadRuntime(now: number): RuntimeState {
  const acquisition = acquisitionFromSearch(window.location.search);
  const storedVisitor = safeRead<StoredVisitor>(VISITOR_KEY);
  const visitor: StoredVisitor = validVisitor(storedVisitor)
    ? storedVisitor
    : { id: uuid(), firstSource: acquisition.source, firstCampaign: acquisition.campaign };
  safeWrite(VISITOR_KEY, visitor);

  const storedSession = safeRead<StoredSession>(SESSION_KEY);
  const session: StoredSession = validSession(storedSession, now) ? storedSession : {
    id: uuid(),
    startedAtMs: now,
    lastActivityAtMs: now,
    lastActivityEventAtMs: 0,
    source: acquisition.source,
    campaign: acquisition.campaign,
    landingEventId: uuid(),
    landingAcknowledged: false,
    homeEventId: uuid(),
    homeAcknowledged: false,
    clientErrorCount: 0,
  };
  safeWrite(SESSION_KEY, session);
  return { visitor, session };
}

function eventFor(
  runtime: RuntimeState,
  eventId: string,
  eventType: TelemetryEventType,
  eventData: ClientTelemetryEvent["eventData"],
): ClientTelemetryEvent {
  return {
    eventId,
    eventType,
    schemaVersion: TELEMETRY_SCHEMA_VERSION,
    visitorId: runtime.visitor.id,
    sessionId: runtime.session.id,
    occurredAtUtc: new Date().toISOString(),
    eventData,
  };
}

export function TelemetryProvider({ children }: { children: ReactNode }) {
  const enabled = telemetryCollectionEnabled();
  const runtimeRef = useRef<RuntimeState | null>(null);

  const ensureRuntime = useCallback(() => {
    const now = Date.now();
    const current = runtimeRef.current;
    if (current && now - current.session.lastActivityAtMs < TELEMETRY_SESSION_TIMEOUT_MS) return current;
    const next = loadRuntime(now);
    runtimeRef.current = next;
    return next;
  }, []);

  const sendLanding = useCallback((runtime: RuntimeState) => {
    if (runtime.session.landingAcknowledged) return;
    const payload = eventFor(runtime, runtime.session.landingEventId, "landing_view", {
      source: runtime.session.source,
      ...(runtime.session.campaign ? { campaign: runtime.session.campaign } : {}),
    });
    void postTelemetryEvent(payload).then((accepted) => {
      if (!accepted || runtimeRef.current?.session.id !== runtime.session.id) return;
      runtime.session.landingAcknowledged = true;
      safeWrite(SESSION_KEY, runtime.session);
    });
  }, []);

  const recordHomeView = useCallback(() => {
    if (!enabled) return;
    const runtime = ensureRuntime();
    sendLanding(runtime);
    if (runtime.session.homeAcknowledged) return;
    const payload = eventFor(runtime, runtime.session.homeEventId, "home_view", {});
    void postTelemetryEvent(payload).then((accepted) => {
      if (!accepted || runtimeRef.current?.session.id !== runtime.session.id) return;
      runtime.session.homeAcknowledged = true;
      safeWrite(SESSION_KEY, runtime.session);
    });
  }, [enabled, ensureRuntime, sendLanding]);

  useEffect(() => {
    if (!enabled) return;
    const initial = ensureRuntime();
    sendLanding(initial);

    const recordActivity = () => {
      const now = Date.now();
      const runtime = ensureRuntime();
      sendLanding(runtime);
      if (now - runtime.session.lastActivityAtMs >= TELEMETRY_ACTIVITY_PERSIST_MS) {
        runtime.session.lastActivityAtMs = now;
        safeWrite(SESSION_KEY, runtime.session);
      }
      if (now - runtime.session.lastActivityEventAtMs < TELEMETRY_ACTIVITY_THROTTLE_MS) return;
      runtime.session.lastActivityEventAtMs = now;
      safeWrite(SESSION_KEY, runtime.session);
      void postTelemetryEvent(eventFor(runtime, uuid(), "session_activity", {
        activity: "interaction",
      }));
    };
    const recordClientError = (kind: "error" | "unhandledrejection") => {
      const runtime = ensureRuntime();
      if (runtime.session.clientErrorCount >= TELEMETRY_CLIENT_ERROR_LIMIT) return;
      runtime.session.clientErrorCount += 1;
      safeWrite(SESSION_KEY, runtime.session);
      // Never transmit messages, stacks, URLs, filenames, or rejected values.
      void postTelemetryEvent(eventFor(runtime, uuid(), "client_error", {
        code: kind === "error" ? "window_error" : "unhandled_rejection",
        routeId: routeIdForPath(window.location.pathname),
      }));
    };
    const onError = () => recordClientError("error");
    const onUnhandledRejection = () => recordClientError("unhandledrejection");
    window.addEventListener("pointerdown", recordActivity, { passive: true });
    window.addEventListener("keydown", recordActivity);
    window.addEventListener("error", onError);
    window.addEventListener("unhandledrejection", onUnhandledRejection);
    return () => {
      window.removeEventListener("pointerdown", recordActivity);
      window.removeEventListener("keydown", recordActivity);
      window.removeEventListener("error", onError);
      window.removeEventListener("unhandledrejection", onUnhandledRejection);
    };
  }, [enabled, ensureRuntime, sendLanding]);

  const value = useMemo<TelemetryContextValue>(
    () => enabled ? { enabled: true, recordHomeView } : DISABLED_CONTEXT,
    [enabled, recordHomeView],
  );
  return <TelemetryContext.Provider value={value}>{children}</TelemetryContext.Provider>;
}

export function useTelemetry(): TelemetryContextValue {
  return useContext(TelemetryContext);
}
