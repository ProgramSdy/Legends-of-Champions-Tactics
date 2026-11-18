import { afterEach, describe, expect, it, vi } from "vitest";
import {
  clearPublicCsrfToken,
  onPublicAuthFailure,
  publicApiJson,
  publicApiRequest,
  setPublicCsrfToken,
} from "@/lib/publicApi";
import { fetchFormationDemonstration } from "@/lib/manual/formationDemonstration";

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  clearPublicCsrfToken();
});

function response(body: unknown, init: ResponseInit = {}) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
    ...init,
  });
}

describe("RELEASE-002 Public transport boundary", () => {
  it("uses same-origin credentialed transport and in-memory CSRF only in Public", async () => {
    vi.stubEnv("LOCT_RELEASE_MODE", "public");
    setPublicCsrfToken("csrf-memory-only");
    const fetchMock = vi.fn().mockResolvedValue(response({ ok: true }));
    vi.stubGlobal("fetch", fetchMock);

    await publicApiRequest("/api/v1/save-slots", {
      method: "POST",
      body: JSON.stringify({ slotId: 1 }),
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/save-slots",
      expect.objectContaining({
        credentials: "include",
        cache: "no-store",
        headers: expect.any(Headers),
      }),
    );
    const request = fetchMock.mock.calls[0][1] as RequestInit;
    const headers = request.headers as Headers;
    expect(headers.get("X-CSRF-Token")).toBe("csrf-memory-only");
    expect(headers.get("Content-Type")).toBe("application/json");
  });

  it("retains the Development localhost boundary and does not add Public CSRF", async () => {
    vi.stubEnv("LOCT_RELEASE_MODE", "development");
    setPublicCsrfToken("dev-token");
    const fetchMock = vi.fn().mockResolvedValue(response({ ok: true }));
    vi.stubGlobal("fetch", fetchMock);

    await publicApiRequest("/api/v1/battles", { method: "POST", body: "{}" });

    expect(fetchMock.mock.calls[0][0]).toBe("http://localhost:8001/api/v1/battles");
    const request = fetchMock.mock.calls[0][1] as RequestInit;
    const headers = request.headers as Headers;
    expect(headers.get("X-CSRF-Token")).toBeNull();
    expect(request.credentials).toBeUndefined();
  });

  it("notifies the session boundary on authentication or CSRF rejection", async () => {
    vi.stubEnv("LOCT_RELEASE_MODE", "public");
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(response({ detail: { code: "sessionRevoked", message: "revoked" } }, { status: 401 }))
      .mockResolvedValueOnce(response({ detail: { code: "csrfInvalid", message: "bad csrf" } }, { status: 403 }));
    vi.stubGlobal("fetch", fetchMock);
    const failures: string[] = [];
    const unsubscribe = onPublicAuthFailure((error) => failures.push(error.code));

    await expect(publicApiJson("/api/v1/sessions/current")).rejects.toMatchObject({
      code: "sessionRevoked",
      kind: "authentication",
    });
    await expect(publicApiJson("/api/v1/save-slots", { method: "POST", body: "{}" })).rejects.toMatchObject({
      code: "csrfInvalid",
      kind: "csrf",
    });
    unsubscribe();
    expect(failures).toEqual(["sessionRevoked", "csrfInvalid"]);
  });

  it("maps an unreachable service to a retryable network error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));

    await expect(publicApiJson("/api/v1/sessions/current")).rejects.toMatchObject({
      code: "networkUnavailable",
      status: 0,
      kind: "network",
    });
  });

  it("keeps the player-facing Manual formation rules on the same-origin Public transport", async () => {
    vi.stubEnv("LOCT_RELEASE_MODE", "public");
    const fetchMock = vi.fn().mockResolvedValue(response({ detail: "unavailable" }, { status: 503 }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchFormationDemonstration()).rejects.toThrow("Formation demonstration is unavailable");
    expect(fetchMock.mock.calls[0][0]).toBe("/api/v1/manual/formation-demonstration");
    expect(fetchMock.mock.calls[0][1]).toEqual(expect.objectContaining({
      credentials: "include",
      cache: "no-store",
    }));
  });
});
