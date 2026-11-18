import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { PublicSessionProvider } from "@/components/session/PublicSessionProvider";
import { StartupScreen } from "@/components/startup/StartupScreen";
import { BattleScreen } from "@/components/battle/BattleScreen";
import { SoundPreferenceProvider } from "@/components/audio/SoundPreferenceProvider";
import { MockBattleProvider } from "@/lib/battle/fixture";
import type { BattleAuthorityState } from "@/lib/battle/types";

const push = vi.fn();

vi.mock("next/navigation", () => ({ useRouter: () => ({ push, replace: vi.fn() }) }));

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const authenticatedSession = {
  contractVersion: "1.0",
  playerId: "player-1",
  playerName: "Alpha_1",
  expiresAt: "2030-01-01T00:00:00Z",
  recoveryConfirmed: true,
  csrfToken: "csrf-authenticated",
};

const emptySlots = {
  contractVersion: "1.0",
  activeSlotId: null,
  slots: [1, 2, 3, 4, 5].map((slotId) => ({
    slotId,
    occupied: false,
    profileId: null,
    createdAt: null,
    lastPlayedAt: null,
    active: false,
  })),
};

afterEach(() => {
  vi.clearAllMocks();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("RELEASE-002 Public onboarding UI", () => {
  it("validates a player name, presents the one-time code, requires acknowledgement, then exposes all five slots", async () => {
    vi.stubEnv("LOCT_RELEASE_MODE", "public");
    const unconfirmed = {
      ...authenticatedSession,
      recoveryConfirmed: false,
      csrfToken: "csrf-unconfirmed",
      recoveryCode: "ABCD-EFGH-IJKL-MNOP",
    };
    const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
      if (url === "/api/v1/sessions/current") return json({ detail: "anonymous" }, 401);
      if (url === "/api/v1/players") return json(unconfirmed);
      if (url === "/api/v1/recovery-code/acknowledge") return json(authenticatedSession);
      if (url === "/api/v1/save-slots") return json(emptySlots);
      throw new Error(`Unexpected request ${init?.method ?? "GET"} ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    render(<PublicSessionProvider><StartupScreen /></PublicSessionProvider>);
    await user.click(screen.getByRole("button", { name: /start game/i }));
    await user.click(await screen.findByRole("button", { name: /create new player/i }));
    const name = screen.getByLabelText("PLAYER NAME");
    await user.type(name, "ab");
    await user.click(screen.getByRole("button", { name: "CREATE PLAYER" }));
    expect(screen.getByRole("alert")).toHaveTextContent("3–20 ASCII");
    await user.clear(name);
    await user.type(name, "Alpha_1");
    await user.click(screen.getByRole("button", { name: "CREATE PLAYER" }));

    expect(await screen.findByLabelText("Recovery Code")).toHaveTextContent("ABCD-EFGH-IJKL-MNOP");
    const confirm = screen.getByRole("button", { name: "CONFIRM & CONTINUE" });
    expect(confirm).toBeDisabled();
    await user.click(screen.getByRole("checkbox"));
    await user.click(confirm);

    expect(await screen.findByRole("heading", { name: "Choose your journey" })).toBeVisible();
    await user.click(screen.getByRole("button", { name: /new game/i }));
    expect(await screen.findAllByRole("button", { name: /save slot [1-5], empty/i })).toHaveLength(5);
    expect(fetchMock.mock.calls.find(([url]) => url === "/api/v1/players")?.[1]).toEqual(expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ playerName: "Alpha_1" }),
    }));
  });

  it("recovers with code only and makes the recovered five-slot account available", async () => {
    vi.stubEnv("LOCT_RELEASE_MODE", "public");
    const fetchMock = vi.fn(async (url: string) => {
      if (url === "/api/v1/sessions/current") return json({ detail: "anonymous" }, 401);
      if (url === "/api/v1/sessions/recover") return json(authenticatedSession);
      if (url === "/api/v1/save-slots") return json(emptySlots);
      throw new Error(`Unexpected request ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    render(<PublicSessionProvider><StartupScreen /></PublicSessionProvider>);
    await user.click(screen.getByRole("button", { name: /start game/i }));
    await user.click(await screen.findByRole("button", { name: /recover player/i }));
    await user.type(screen.getByLabelText("RECOVERY CODE"), "abcd-efgh-ijkl-mnop");
    await user.click(screen.getByRole("button", { name: "RECOVER PLAYER" }));

    expect(await screen.findByRole("heading", { name: "Choose your journey" })).toBeVisible();
    const recoveryRequest = fetchMock.mock.calls.find(([url]) => url === "/api/v1/sessions/recover")?.[1] as RequestInit;
    expect(recoveryRequest.body).toBe(JSON.stringify({ recoveryCode: "ABCD-EFGH-IJKL-MNOP" }));
  });

  it("replaces a forgotten code only inside an authenticated session and requires a new acknowledgement", async () => {
    vi.stubEnv("LOCT_RELEASE_MODE", "public");
    const fetchMock = vi.fn(async (url: string) => {
      if (url === "/api/v1/sessions/current") return json(authenticatedSession);
      if (url === "/api/v1/save-slots") return json(emptySlots);
      if (url === "/api/v1/recovery-code/forgot") return json({ recoveryCode: "NEWW-CODE-ONLY-ONCE" });
      if (url === "/api/v1/recovery-code/acknowledge") return json(authenticatedSession);
      throw new Error(`Unexpected request ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    render(<PublicSessionProvider><StartupScreen /></PublicSessionProvider>);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith("/api/v1/sessions/current", expect.anything()));
    await user.click(screen.getByRole("button", { name: /start game/i }));
    await user.click(await screen.findByRole("button", { name: "FORGOT RECOVERY CODE" }));

    expect(await screen.findByLabelText("Recovery Code")).toHaveTextContent("NEWW-CODE-ONLY-ONCE");
    expect(screen.getByRole("button", { name: "CONFIRM & CONTINUE" })).toBeDisabled();
  });
});

class AuthorityProvider extends MockBattleProvider {
  private listener: ((authority: BattleAuthorityState | null) => void) | null = null;

  constructor(private authority: BattleAuthorityState) {
    super();
  }

  getAuthority() { return this.authority; }
  subscribeAuthority(listener: (authority: BattleAuthorityState | null) => void) {
    this.listener = listener;
    listener(this.authority);
    return () => { this.listener = null; };
  }
  emit(authority: BattleAuthorityState) {
    this.authority = authority;
    this.listener?.(authority);
  }
}

describe("RELEASE-002 Public battle safeguards", () => {
  it("keeps Resign local on NO and keeps the dialog retryable after a server failure", async () => {
    const resign = vi.fn()
      .mockRejectedValueOnce(new Error("Resign could not be confirmed."))
      .mockResolvedValueOnce(undefined);
    const user = userEvent.setup();
    render(<SoundPreferenceProvider><BattleScreen provider={new MockBattleProvider()} onResign={resign} /></SoundPreferenceProvider>);

    await user.click(await screen.findByRole("button", { name: "RESIGN" }));
    await user.click(screen.getByRole("button", { name: "NO" }));
    expect(resign).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: "RESIGN" }));
    await user.click(screen.getByRole("button", { name: "YES" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Resign could not be confirmed");
    expect(screen.getByRole("dialog", { name: "Give up this battle?" })).toBeVisible();
    await user.click(screen.getByRole("button", { name: "RETRY" }));
    await waitFor(() => expect(resign).toHaveBeenCalledTimes(2));
  });

  it("uses server clock skew for one warning per five- and one-minute threshold and accepts a new deadline", async () => {
    const serverNow = new Date("2026-11-18T00:00:00Z");
    const expiry = new Date(serverNow.getTime() + 4 * 60_000);
    const provider = new AuthorityProvider({
      serverNow: serverNow.toISOString(),
      expiresAt: expiry.toISOString(),
      lifecycleStatus: "active",
      settlementStatus: "none",
    });
    render(<SoundPreferenceProvider><BattleScreen provider={provider} /></SoundPreferenceProvider>);

    expect(await screen.findByRole("status")).toHaveTextContent("five more minutes");
    provider.emit({
      serverNow: new Date(serverNow.getTime() + 10_000).toISOString(),
      expiresAt: expiry.toISOString(),
      lifecycleStatus: "active",
      settlementStatus: "none",
    });
    expect(screen.getByRole("status")).toHaveTextContent("five more minutes");
    provider.emit({
      serverNow: new Date(expiry.getTime() - 50_000).toISOString(),
      expiresAt: expiry.toISOString(),
      lifecycleStatus: "active",
      settlementStatus: "none",
    });
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("one more minute"));
    provider.emit({
      serverNow: serverNow.toISOString(),
      expiresAt: new Date(serverNow.getTime() + 4 * 60_000 + 1).toISOString(),
      lifecycleStatus: "active",
      settlementStatus: "none",
    });
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("five more minutes"));
  });
});
