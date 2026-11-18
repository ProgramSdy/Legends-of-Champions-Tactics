import { isEngineeringMode } from "@/lib/releaseMode";

export type PublicApiFailureKind = "authentication" | "csrf" | "network" | "server";

export class PublicApiError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly status: number,
    public readonly kind: PublicApiFailureKind,
  ) {
    super(message);
    this.name = "PublicApiError";
  }
}

type PublicAuthFailureListener = (error: PublicApiError) => void;

let csrfToken: string | null = null;
const authFailureListeners = new Set<PublicAuthFailureListener>();

export function setPublicCsrfToken(token: string | null): void {
  csrfToken = token;
}

export function clearPublicCsrfToken(): void {
  csrfToken = null;
}

export function onPublicAuthFailure(listener: PublicAuthFailureListener): () => void {
  authFailureListeners.add(listener);
  return () => authFailureListeners.delete(listener);
}

function apiFailureKind(status: number, code: string): PublicApiFailureKind {
  if (status === 401) return "authentication";
  if (status === 403 && code.toLowerCase().includes("csrf")) return "csrf";
  return "server";
}

/**
 * Public mode is same-origin. Development deliberately retains the existing
 * localhost adapter boundary. No session or Recovery Code is persisted here.
 */
export function battleApiBaseUrl(): string {
  // Keep the release-mode check directly at this boundary. Vite replaces
  // LOCT_RELEASE_MODE at build time, allowing the Public artifact to remove
  // the entire Development-origin branch (including any configured URL).
  if (process.env.LOCT_RELEASE_MODE === "development") {
    return process.env.NEXT_PUBLIC_BATTLE_API_URL ?? "http://localhost:8001";
  }
  return "";
}

export async function publicApiRequest(
  path: string,
  init: RequestInit = {},
  baseUrl = battleApiBaseUrl(),
): Promise<Response> {
  const method = (init.method ?? "GET").toUpperCase();
  const unsafe = !["GET", "HEAD", "OPTIONS"].includes(method);
  const headers = new Headers(init.headers);
  if (init.body !== undefined && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (!isEngineeringMode() && unsafe && csrfToken && !headers.has("X-CSRF-Token")) {
    headers.set("X-CSRF-Token", csrfToken);
  }

  let response: Response;
  try {
    response = await fetch(`${baseUrl}${path}`, {
      ...init,
      headers,
      credentials: isEngineeringMode() ? init.credentials : "include",
      cache: "no-store",
    });
  } catch {
    throw new PublicApiError(
      "The game service is unreachable. Check your connection and retry.",
      "networkUnavailable",
      0,
      "network",
    );
  }

  if (!response.ok) {
    const body = await response.clone().json().catch(() => null) as {
      detail?: { code?: string; message?: string } | string;
    } | null;
    const detail = body?.detail;
    const code = typeof detail === "object" && detail?.code
      ? detail.code
      : `http${response.status}`;
    const message = typeof detail === "object" && detail?.message
      ? detail.message
      : typeof detail === "string" ? detail : `Game service returned HTTP ${response.status}.`;
    const error = new PublicApiError(message, code, response.status, apiFailureKind(response.status, code));
    if (error.kind === "authentication" || error.kind === "csrf") {
      for (const listener of authFailureListeners) listener(error);
    }
    throw error;
  }
  return response;
}

export async function publicApiJson<T>(
  path: string,
  init: RequestInit = {},
  baseUrl = battleApiBaseUrl(),
): Promise<T> {
  const response = await publicApiRequest(path, init, baseUrl);
  try {
    return await response.json() as T;
  } catch {
    throw new PublicApiError(
      "The game service returned invalid data.",
      "invalidJson",
      response.status,
      "server",
    );
  }
}
