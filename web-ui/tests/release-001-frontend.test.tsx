import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import StagesPage from "@/app/stages/page";
import { StageSelectionScreen } from "@/components/stages/StageSelectionScreen";
import { isEngineeringMode, resolveReleaseMode } from "@/lib/releaseMode";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));
vi.mock("@/components/audio/SoundPreferenceProvider", () => ({
  SoundPreferenceProvider: ({ children }: { children: React.ReactNode }) => children,
  useSoundPreference: () => ({ enabled: true, toggle: vi.fn() }),
}));
// This suite isolates the release-surface toggle. Public session gating is
// covered independently by RELEASE-002 session/route tests.
vi.mock("@/components/session/PublicSessionProvider", () => ({
  PublicSessionGate: ({ children }: { children: React.ReactNode }) => children,
}));

afterEach(() => vi.unstubAllEnvs());

describe("RELEASE-001 frontend release boundary", () => {
  it("fails closed for missing, blank, and invalid mode values", () => {
    expect(resolveReleaseMode(undefined)).toBe("public");
    expect(resolveReleaseMode("")).toBe("public");
    expect(resolveReleaseMode("production")).toBe("public");
    expect(resolveReleaseMode("PUBLIC")).toBe("public");
    expect(isEngineeringMode("development")).toBe(true);
    expect(isEngineeringMode("public")).toBe(false);
  });

  it("omits the Engineering route and hotspot diagnostics in public mode", async () => {
    vi.stubEnv("LOCT_RELEASE_MODE", "public");
    render(await StagesPage({ searchParams: Promise.resolve({ debugHotspots: "1" }) }));

    expect(screen.queryByRole("link", { name: /engineering test/i })).not.toBeInTheDocument();
    expect(document.querySelector(".stage-map-frame")).not.toHaveClass("debug-hotspots");
    expect(screen.queryByTestId("stage-hotspot-debug")).not.toBeInTheDocument();
  });

  it("retains Engineering navigation and diagnostics in explicit Development mode", async () => {
    vi.stubEnv("LOCT_RELEASE_MODE", "development");
    render(await StagesPage({ searchParams: Promise.resolve({ debugHotspots: "1" }) }));

    expect(screen.getByRole("link", { name: /engineering test/i })).toHaveAttribute("href", "/debug");
    expect(document.querySelector(".stage-map-frame")).toHaveClass("debug-hotspots");
    expect(screen.getAllByTestId("stage-hotspot-debug")).toHaveLength(3);
  });

  it("keeps the component-level default safe when no release mode is supplied", () => {
    render(<StageSelectionScreen />);
    expect(screen.queryByRole("link", { name: /engineering test/i })).not.toBeInTheDocument();
    expect(screen.queryByTestId("stage-hotspot-debug")).not.toBeInTheDocument();
  });
});
