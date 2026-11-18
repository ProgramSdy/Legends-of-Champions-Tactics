import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  PublicSessionGate,
  PublicSessionProvider,
  usePublicSession,
} from "@/components/session/PublicSessionProvider";

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

function SessionProbe() {
  const { phase, session, disclosedRecoveryCode, error, replaceRecoveryCode } = usePublicSession();
  return <>
    <output data-testid="session">{JSON.stringify({ phase, playerId: session?.playerId, disclosedRecoveryCode, error })}</output>
    <button type="button" onClick={() => void replaceRecoveryCode().catch(() => {})}>Replace code</button>
  </>;
}

const session = {
  contractVersion: "1.0",
  playerId: "player-1",
  playerName: "Tester",
  expiresAt: "2030-01-01T00:00:00Z",
  recoveryConfirmed: true,
  csrfToken: "csrf",
};

describe("RELEASE-002 Public session boundary", () => {
  it("bypasses Public authentication only in explicit Development mode", async () => {
    vi.stubEnv("LOCT_RELEASE_MODE", "development");
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    render(<PublicSessionProvider><PublicSessionGate><SessionProbe /></PublicSessionGate></PublicSessionProvider>);

    expect(screen.getByTestId("session")).toHaveTextContent('"phase":"development"');
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("returns an anonymous Public session to onboarding instead of claiming access", async () => {
    vi.stubEnv("LOCT_RELEASE_MODE", "public");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "unauthorized" }), { status: 401 })));

    render(<PublicSessionProvider><PublicSessionGate><SessionProbe /></PublicSessionGate></PublicSessionProvider>);

    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("PLAYER SESSION REQUIRED"));
    expect(screen.getByRole("link", { name: /return to game start/i })).toHaveAttribute("href", "/");
  });

  it("loads an authenticated Public session without disclosing a code from current-session bootstrap", async () => {
    vi.stubEnv("LOCT_RELEASE_MODE", "public");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(session), { status: 200 })));

    render(<PublicSessionProvider><PublicSessionGate><SessionProbe /></PublicSessionGate></PublicSessionProvider>);

    await waitFor(() => expect(screen.getByTestId("session")).toHaveTextContent('"phase":"authenticated"'));
    expect(screen.getByTestId("session")).not.toHaveTextContent("recoveryCode");
  });

  it("retains an authenticated player after a CSRF rejection and revalidates read-only without replaying the mutation", async () => {
    vi.stubEnv("LOCT_RELEASE_MODE", "public");
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(session), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail: { code: "csrfInvalid", message: "CSRF mismatch" } }), { status: 403 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(session), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    render(<PublicSessionProvider><SessionProbe /></PublicSessionProvider>);
    await waitFor(() => expect(screen.getByTestId("session")).toHaveTextContent('"phase":"authenticated"'));
    fireEvent.click(screen.getByRole("button", { name: "Replace code" }));

    await waitFor(() => expect(screen.getByTestId("session")).toHaveTextContent("CSRF mismatch"));
    expect(screen.getByTestId("session")).toHaveTextContent('"phase":"authenticated"');
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(fetchMock.mock.calls.filter(([url]) => url === "/api/v1/recovery-code/forgot")).toHaveLength(1);
  });

  it("performs one deliberate protected refresh near expiry while ordinary bootstrap remains a read-only GET", async () => {
    vi.stubEnv("LOCT_RELEASE_MODE", "public");
    const nearExpiry = { ...session, expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString() };
    const refreshed = { ...session, expiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString() };
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(nearExpiry), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(refreshed), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    Object.defineProperty(document, "visibilityState", { configurable: true, value: "visible" });

    render(<PublicSessionProvider><SessionProbe /></PublicSessionProvider>);

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(fetchMock.mock.calls[0][0]).toBe("/api/v1/sessions/current");
    expect((fetchMock.mock.calls[0][1] as RequestInit).method).toBeUndefined();
    expect(fetchMock.mock.calls[1][0]).toBe("/api/v1/sessions/refresh");
    expect(fetchMock.mock.calls[1][1]).toEqual(expect.objectContaining({ method: "POST", credentials: "include" }));
  });
});
