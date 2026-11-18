"use client";

import Link from "next/link";
import {
  clearPublicCsrfToken,
  onPublicAuthFailure,
  publicApiJson,
  publicApiRequest,
  setPublicCsrfToken,
  type PublicApiError,
} from "@/lib/publicApi";
import { isEngineeringMode } from "@/lib/releaseMode";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

export interface PublicPlayerSession {
  contractVersion: "1.0";
  playerId: string;
  playerName: string;
  expiresAt: string;
  recoveryConfirmed: boolean;
  csrfToken: string;
  recoveryCode?: string | null;
}

type PublicSessionPhase = "development" | "loading" | "anonymous" | "unconfirmed" | "authenticated";

interface PublicSessionContextValue {
  phase: PublicSessionPhase;
  session: PublicPlayerSession | null;
  disclosedRecoveryCode: string | null;
  error: string | null;
  enroll(playerName: string): Promise<void>;
  recover(recoveryCode: string): Promise<void>;
  acknowledgeRecoveryCode(): Promise<void>;
  replaceRecoveryCode(): Promise<void>;
  refresh(): Promise<void>;
  logout(): Promise<void>;
  clearError(): void;
}

const PublicSessionContext = createContext<PublicSessionContextValue | null>(null);
const SESSION_CHANNEL = "loct-public-session";
const AUTOMATIC_REFRESH_WINDOW_MS = 7 * 24 * 60 * 60 * 1000;
const MINIMUM_REFRESH_INTERVAL_MS = 6 * 60 * 60 * 1000;
const unsupportedDevelopmentAuth = async () => {
  throw new Error("Public player authentication is unavailable in Development mode.");
};
const DEVELOPMENT_SESSION_CONTEXT: PublicSessionContextValue = {
  phase: "development",
  session: null,
  disclosedRecoveryCode: null,
  error: null,
  enroll: unsupportedDevelopmentAuth,
  recover: unsupportedDevelopmentAuth,
  acknowledgeRecoveryCode: unsupportedDevelopmentAuth,
  replaceRecoveryCode: unsupportedDevelopmentAuth,
  refresh: unsupportedDevelopmentAuth,
  logout: unsupportedDevelopmentAuth,
  clearError: () => {},
};

function sessionPhase(session: PublicPlayerSession): PublicSessionPhase {
  return session.recoveryConfirmed ? "authenticated" : "unconfirmed";
}

function isSession(value: unknown): value is PublicPlayerSession {
  if (!value || typeof value !== "object") return false;
  const item = value as Record<string, unknown>;
  return item.contractVersion === "1.0"
    && typeof item.playerId === "string"
    && typeof item.playerName === "string"
    && typeof item.expiresAt === "string"
    && typeof item.recoveryConfirmed === "boolean"
    && typeof item.csrfToken === "string"
    && (item.recoveryCode === undefined || item.recoveryCode === null || typeof item.recoveryCode === "string");
}

export function PublicSessionProvider({ children }: { children: ReactNode }) {
  const development = isEngineeringMode();
  const [phase, setPhase] = useState<PublicSessionPhase>(development ? "development" : "loading");
  const [session, setSession] = useState<PublicPlayerSession | null>(null);
  const [disclosedRecoveryCode, setDisclosedRecoveryCode] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const channelRef = useRef<BroadcastChannel | null>(null);
  const lastAutomaticRefreshRef = useRef(0);

  const applySession = useCallback((next: PublicPlayerSession, disclose = false) => {
    setPublicCsrfToken(next.csrfToken);
    setSession(next);
    setPhase(sessionPhase(next));
    setDisclosedRecoveryCode(disclose ? next.recoveryCode ?? null : null);
    setError(null);
  }, []);

  const becomeAnonymous = useCallback((message: string | null = null) => {
    clearPublicCsrfToken();
    setSession(null);
    setDisclosedRecoveryCode(null);
    setPhase("anonymous");
    setError(message);
  }, []);

  const loadCurrent = useCallback(async (quiet = false) => {
    if (development) return;
    if (!quiet) setPhase("loading");
    try {
      const next = await publicApiJson<unknown>("/api/v1/sessions/current");
      if (!isSession(next)) throw new Error("The player session response is invalid.");
      applySession(next);
    } catch (reason: unknown) {
      const typed = reason as PublicApiError;
      if (typed?.status === 401) becomeAnonymous();
      else if (quiet) {
        setError(reason instanceof Error ? reason.message : "Unable to revalidate player session.");
      }
      else {
        becomeAnonymous(reason instanceof Error ? reason.message : "Unable to check player session.");
      }
    }
  }, [applySession, becomeAnonymous, development]);

  useEffect(() => {
    if (development) return;
    const unsubscribe = onPublicAuthFailure((failure) => {
      if (failure.kind === "authentication") {
        becomeAnonymous(failure.message);
        channelRef.current?.postMessage({ type: "session-invalidated" });
        return;
      }
      // A CSRF mismatch rejects the unsafe request but does not prove the
      // HttpOnly session was revoked. Revalidate read-only; never replay the
      // mutation (especially a battle command with a new command ID).
      setError(failure.message);
      void loadCurrent(true).then(() => setError(failure.message));
    });
    if (typeof BroadcastChannel !== "undefined") {
      const channel = new BroadcastChannel(SESSION_CHANNEL);
      channelRef.current = channel;
      channel.addEventListener("message", (event: MessageEvent) => {
        const type = event.data?.type;
        if (type === "session-invalidated") becomeAnonymous("This player session is no longer active.");
        if (type === "session-changed") void loadCurrent(true);
      });
    }
    // Defer bootstrap out of the effect body so the effect remains an external
    // subscription boundary rather than synchronously cascading state writes.
    const bootstrapTimer = window.setTimeout(() => void loadCurrent(), 0);
    return () => {
      window.clearTimeout(bootstrapTimer);
      unsubscribe();
      channelRef.current?.close();
      channelRef.current = null;
      clearPublicCsrfToken();
    };
  }, [becomeAnonymous, development, loadCurrent]);

  const enroll = useCallback(async (playerName: string) => {
    const next = await publicApiJson<unknown>("/api/v1/players", {
      method: "POST",
      body: JSON.stringify({ playerName }),
    });
    if (!isSession(next) || !next.recoveryCode) throw new Error("The server did not issue a Recovery Code.");
    applySession(next, true);
    channelRef.current?.postMessage({ type: "session-changed" });
  }, [applySession]);

  const recover = useCallback(async (recoveryCode: string) => {
    const next = await publicApiJson<unknown>("/api/v1/sessions/recover", {
      method: "POST",
      body: JSON.stringify({ recoveryCode }),
    });
    if (!isSession(next)) throw new Error("The recovered player session is invalid.");
    applySession(next);
    channelRef.current?.postMessage({ type: "session-changed" });
  }, [applySession]);

  const acknowledgeRecoveryCode = useCallback(async () => {
    const next = await publicApiJson<unknown>("/api/v1/recovery-code/acknowledge", {
      method: "POST",
      body: "{}",
    });
    if (!isSession(next)) throw new Error("The Recovery Code acknowledgment is invalid.");
    applySession(next);
    channelRef.current?.postMessage({ type: "session-changed" });
  }, [applySession]);

  const replaceRecoveryCode = useCallback(async () => {
    const result = await publicApiJson<unknown>("/api/v1/recovery-code/forgot", {
      method: "POST",
      body: "{}",
    });
    if (!result || typeof result !== "object" || typeof (result as { recoveryCode?: unknown }).recoveryCode !== "string") {
      throw new Error("The replacement Recovery Code response is invalid.");
    }
    const replacement = (result as { recoveryCode: string }).recoveryCode;
    setSession((current) => current ? { ...current, recoveryConfirmed: false } : current);
    setPhase("unconfirmed");
    setDisclosedRecoveryCode(replacement);
    setError(null);
    channelRef.current?.postMessage({ type: "session-changed" });
  }, []);

  const refresh = useCallback(async () => {
    const next = await publicApiJson<unknown>("/api/v1/sessions/refresh", {
      method: "POST",
      body: "{}",
    });
    if (!isSession(next)) throw new Error("The refreshed player session is invalid.");
    applySession(next);
    channelRef.current?.postMessage({ type: "session-changed" });
  }, [applySession]);

  useEffect(() => {
    if (development || phase !== "authenticated" || !session) return;
    const refreshIfNeeded = () => {
      if (document.visibilityState !== "visible") return;
      const now = Date.now();
      const expiresAt = Date.parse(session.expiresAt);
      if (!Number.isFinite(expiresAt)
        || expiresAt - now > AUTOMATIC_REFRESH_WINDOW_MS
        || now - lastAutomaticRefreshRef.current < MINIMUM_REFRESH_INTERVAL_MS) return;
      lastAutomaticRefreshRef.current = now;
      // This explicit protected POST is the only automatic sliding refresh.
      // Ordinary current-session GETs remain read-only server-side.
      void refresh().catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : "Unable to refresh player session.");
      });
    };
    refreshIfNeeded();
    document.addEventListener("visibilitychange", refreshIfNeeded);
    return () => document.removeEventListener("visibilitychange", refreshIfNeeded);
  }, [development, phase, refresh, session]);

  const logout = useCallback(async () => {
    await publicApiRequest("/api/v1/sessions/logout", { method: "POST", body: "{}" });
    becomeAnonymous();
    channelRef.current?.postMessage({ type: "session-invalidated" });
  }, [becomeAnonymous]);

  const value = useMemo<PublicSessionContextValue>(() => ({
    phase,
    session,
    disclosedRecoveryCode,
    error,
    enroll,
    recover,
    acknowledgeRecoveryCode,
    replaceRecoveryCode,
    refresh,
    logout,
    clearError: () => setError(null),
  }), [acknowledgeRecoveryCode, disclosedRecoveryCode, enroll, error, logout, phase, recover, refresh, replaceRecoveryCode, session]);

  return <PublicSessionContext.Provider value={value}>{children}</PublicSessionContext.Provider>;
}

export function usePublicSession(): PublicSessionContextValue {
  const value = useContext(PublicSessionContext);
  if (!value && (isEngineeringMode()
    || (process.env.NODE_ENV === "test" && process.env.LOCT_RELEASE_MODE === undefined))) {
    // Legacy component tests render route bodies without the root layout. The
    // test-only unspecified-mode fallback preserves that seam; explicit Public
    // tests still require a provider and production remains fail closed.
    return DEVELOPMENT_SESSION_CONTEXT;
  }
  if (!value) throw new Error("usePublicSession must be used within PublicSessionProvider.");
  return value;
}

export function PublicSessionGate({ children }: { children: ReactNode }) {
  const { phase } = usePublicSession();
  if (phase === "development" || phase === "authenticated") return children;
  if (phase === "loading") return (
    <main className="loading-screen" aria-live="polite"><span className="loading-rune">◇</span>Checking player session…</main>
  );
  return (
    <main className="loading-screen">
      <section className="connection-state" role="alert">
        <strong>{phase === "unconfirmed" ? "RECOVERY CODE CONFIRMATION REQUIRED" : "PLAYER SESSION REQUIRED"}</strong>
        <p>{phase === "unconfirmed"
          ? "Return to Game Start and confirm that you saved the Recovery Code."
          : "Create or recover a player from Game Start before opening protected game data."}</p>
        <Link href="/">RETURN TO GAME START</Link>
      </section>
    </main>
  );
}
