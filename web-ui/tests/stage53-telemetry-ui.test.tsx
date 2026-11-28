import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useEffect, useRef, useState } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { SoundPreferenceProvider } from "@/components/audio/SoundPreferenceProvider";
import { ManualDialog } from "@/components/manual/ManualDialog";
import { TelemetryProvider, useTelemetry } from "@/components/telemetry/TelemetryProvider";
import { configuredFeedbackUrl } from "@/lib/telemetry";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

function accepted() {
  return new Response(JSON.stringify({
    contractVersion: "1.0",
    accepted: true,
    duplicate: false,
  }), { status: 200, headers: { "Content-Type": "application/json" } });
}

function TelemetryHarness() {
  const { recordHomeView } = useTelemetry();
  return <button type="button" onClick={recordHomeView}>Home</button>;
}

function ManualHarness() {
  const triggerRef = useRef<HTMLButtonElement>(null);
  const [open, setOpen] = useState(true);
  return <SoundPreferenceProvider>
    <button ref={triggerRef} type="button">Settings</button>
    <ManualDialog open={open} onClose={() => setOpen(false)} triggerRef={triggerRef} />
  </SoundPreferenceProvider>;
}

function HomeOnRender() {
  const { recordHomeView } = useTelemetry();
  useEffect(() => recordHomeView(), [recordHomeView]);
  return null;
}

beforeEach(() => {
  const values = new Map<string, string>();
  Object.defineProperty(window, "localStorage", {
    configurable: true,
    value: {
      get length() { return values.size; },
      clear: () => values.clear(),
      getItem: (key: string) => values.get(key) ?? null,
      key: (index: number) => Array.from(values.keys())[index] ?? null,
      removeItem: (key: string) => values.delete(key),
      setItem: (key: string, value: string) => values.set(key, String(value)),
    },
  });
  window.history.replaceState({}, "", "/");
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllEnvs();
  vi.useRealTimers();
  window.localStorage.clear();
  window.history.replaceState({}, "", "/");
});

describe("Stage 5.3 bounded frontend telemetry", () => {
  it("is completely inert when the explicit frontend collection flag is absent", () => {
    const request = vi.spyOn(globalThis, "fetch");
    render(<TelemetryProvider><TelemetryHarness /></TelemetryProvider>);
    fireEvent.click(screen.getByRole("button", { name: "Home" }));
    fireEvent.pointerDown(window);
    fireEvent(window, new Event("error"));
    expect(request).not.toHaveBeenCalled();
    expect(window.localStorage.length).toBe(0);
  });

  it("emits bounded contract events without messages, stacks, or full URLs", async () => {
    vi.stubEnv("NEXT_PUBLIC_TELEMETRY_ENABLED", "true");
    window.history.replaceState({}, "", "/?source=reddit&campaign=pre_alpha-1&secret=drop-me");
    const request = vi.spyOn(globalThis, "fetch").mockImplementation(async () => accepted());
    render(<TelemetryProvider><TelemetryHarness /></TelemetryProvider>);

    await waitFor(() => expect(request).toHaveBeenCalledTimes(1));
    fireEvent.pointerDown(window);
    fireEvent.click(screen.getByRole("button", { name: "Home" }));
    await waitFor(() => expect(request).toHaveBeenCalledTimes(3));
    fireEvent(window, new Event("error"));
    await waitFor(() => expect(request).toHaveBeenCalledTimes(4));

    const events = request.mock.calls.map(([, init]) => JSON.parse(String(init?.body)) as {
      eventType: string;
      visitorId: string;
      sessionId: string;
      eventData: Record<string, unknown>;
    });
    expect(events.map((event) => event.eventType)).toEqual([
      "landing_view", "session_activity", "home_view", "client_error",
    ]);
    expect(events[0].eventData).toEqual({ source: "reddit", campaign: "pre_alpha-1" });
    expect(events[1].eventData).toEqual({ activity: "interaction" });
    expect(events[3].eventData).toEqual({ code: "window_error", routeId: "startup" });
    expect(JSON.stringify(events)).not.toContain("secret");
    expect(JSON.stringify(events)).not.toContain("drop-me");
    expect(new Set(events.map((event) => event.visitorId)).size).toBe(1);
    expect(new Set(events.map((event) => event.sessionId)).size).toBe(1);

    for (let index = 0; index < 10; index += 1) fireEvent(window, new Event("error"));
    await waitFor(() => expect(request).toHaveBeenCalledTimes(8));
    expect(request.mock.calls.map(([, init]) => JSON.parse(String(init?.body)))
      .filter((event) => event.eventType === "client_error")).toHaveLength(5);
  });

  it("reuses an active analytics session and starts a new one after 30 minutes", async () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-11-28T00:00:00.000Z"));
    vi.stubEnv("NEXT_PUBLIC_TELEMETRY_ENABLED", "true");
    vi.spyOn(globalThis, "fetch").mockImplementation(async () => accepted());

    const first = render(<TelemetryProvider><HomeOnRender /></TelemetryProvider>);
    await act(async () => { await Promise.resolve(); });
    const firstSession = JSON.parse(window.localStorage.getItem("loct.telemetry.session.v1")!).id;
    first.unmount();

    vi.setSystemTime(new Date("2026-11-28T00:29:59.000Z"));
    const second = render(<TelemetryProvider><HomeOnRender /></TelemetryProvider>);
    await act(async () => { await Promise.resolve(); });
    expect(JSON.parse(window.localStorage.getItem("loct.telemetry.session.v1")!).id).toBe(firstSession);
    second.unmount();

    vi.setSystemTime(new Date("2026-11-28T00:30:00.000Z"));
    render(<TelemetryProvider><HomeOnRender /></TelemetryProvider>);
    await act(async () => { await Promise.resolve(); });
    expect(JSON.parse(window.localStorage.getItem("loct.telemetry.session.v1")!).id).not.toBe(firstSession);
  });
});

describe("external feedback settings link", () => {
  it("accepts only credential-free HTTPS destinations", () => {
    expect(configuredFeedbackUrl("https://feedback.example/report")).toBe("https://feedback.example/report");
    expect(configuredFeedbackUrl("http://feedback.example/report")).toBeNull();
    expect(configuredFeedbackUrl("https://user:secret@feedback.example/report")).toBeNull();
    expect(configuredFeedbackUrl("not a URL")).toBeNull();
  });

  it("opens a configured destination in a safe new tab and omits missing configuration", () => {
    vi.stubEnv("NEXT_PUBLIC_FEEDBACK_URL", "https://feedback.example/report");
    const view = render(<ManualHarness />);
    const link = screen.getByRole("link", { name: /Feedback & Bug Report/i });
    expect(link).toHaveAttribute("href", "https://feedback.example/report");
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");

    view.unmount();
    vi.stubEnv("NEXT_PUBLIC_FEEDBACK_URL", "");
    render(<ManualHarness />);
    expect(screen.queryByRole("link", { name: /Feedback & Bug Report/i })).not.toBeInTheDocument();
  });
});
