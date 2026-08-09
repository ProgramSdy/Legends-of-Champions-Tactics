import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import StartupPage from "@/app/page";
import StagesPage from "@/app/stages/page";
import { StageSelectionScreen } from "@/components/stages/StageSelectionScreen";
import { STAGE_DEFINITIONS } from "@/components/stages/stage-config";

const push = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("UI-012 stage-selection flow", () => {
  it("routes startup into stages while preserving the existing game destination", () => {
    render(<StartupPage />);
    expect(screen.getByRole("link", { name: /start game/i })).toHaveAttribute("href", "/stages");
  });

  it("uses the supplied map exactly once and keeps map-percent geometry on its parent", async () => {
    render(await StagesPage({ searchParams: Promise.resolve({}) }));
    const map = document.querySelector(".stage-map-image");
    expect(map).toHaveAttribute("src", "/game-images/Stage_Map/valley_of_champions.png");
    expect(document.querySelectorAll(".stage-map-image")).toHaveLength(1);
    expect(document.querySelector(".stage-map-frame")).toHaveAttribute("data-coordinate-system", "map-percent");
  });

  it("defines the extensible six-location roster with only Arena enabled", () => {
    expect(STAGE_DEFINITIONS.map((stage) => stage.id)).toEqual([
      "arena",
      "warriors-barrack",
      "mages-tower",
      "rogues-forest",
      "paladins-altar",
      "priests-cathedral",
    ]);
    expect(STAGE_DEFINITIONS.filter((stage) => stage.enabled).map((stage) => stage.id)).toEqual(["arena"]);
    const arena = STAGE_DEFINITIONS.find((stage) => stage.id === "arena");
    expect(arena?.geometry).toEqual(expect.objectContaining({ leftPercent: expect.any(Number), topPercent: expect.any(Number), widthPercent: expect.any(Number), heightPercent: expect.any(Number) }));
    expect(arena?.geometry?.leftPercent).toBeGreaterThan(0);
    expect(arena?.geometry?.leftPercent).toBeLessThan(100);
  });

  it("renders only Arena as a native interactive control", () => {
    render(<StageSelectionScreen />);
    expect(screen.getByRole("button", { name: "Enter Arena" })).toBeVisible();
    expect(screen.getAllByRole("button")).toHaveLength(1);
    for (const name of ["Warrior's Barrack", "Mage's Tower", "Rogue's Forest", "Paladin's Altar", "Priest's Cathedral"]) {
      expect(screen.queryByRole("button", { name: new RegExp(name, "i") })).not.toBeInTheDocument();
    }
  });

  it("shares hover and focus semantics for the Arena label/effect", () => {
    render(<StageSelectionScreen />);
    const arena = screen.getByRole("button", { name: "Enter Arena" });
    const label = document.querySelector<HTMLElement>(".stage-hotspot-label");
    expect(label).not.toBeNull();
    expect(label).toHaveAttribute("aria-hidden", "true");
    fireEvent.mouseEnter(arena);
    expect(label).toHaveTextContent("Arena");
    expect(arena).toHaveClass("is-active");
    fireEvent.mouseLeave(arena);
    expect(label).toHaveTextContent("Arena");
    expect(arena).not.toHaveClass("is-active");
    fireEvent.focus(arena);
    expect(label).toHaveTextContent("Arena");
    expect(arena).toHaveClass("is-active");
    fireEvent.blur(arena);
  });

  it("activates the Team Builder route with click and keyboard", async () => {
    render(<StageSelectionScreen />);
    const arena = screen.getByRole("button", { name: "Enter Arena" });
    const user = userEvent.setup();
    await user.click(arena);
    push.mockClear();
    arena.focus();
    fireEvent.keyDown(arena, { key: "Enter" });
    fireEvent.keyDown(arena, { key: " " });
    expect(push).toHaveBeenCalledWith("/game?stage=arena");
    expect(push).toHaveBeenCalledTimes(2);
  });

  it("keeps debug geometry hidden by default and exposes only Arena when enabled", () => {
    const { rerender } = render(<StageSelectionScreen />);
    expect(screen.queryByTestId("stage-hotspot-debug")).not.toBeInTheDocument();
    rerender(<StageSelectionScreen debugHotspots />);
    const debug = screen.getByTestId("stage-hotspot-debug");
    expect(debug).not.toBeNull();
    expect(debug).toHaveTextContent("Arena");
    expect(screen.getAllByTestId("stage-hotspot-debug")).toHaveLength(1);
  });

  it("keeps query-string debug geometry disabled in production", async () => {
    vi.stubEnv("NODE_ENV", "production");
    render(await StagesPage({ searchParams: Promise.resolve({ debugHotspots: "1" }) }));
    expect(document.querySelector(".stage-map-frame")).not.toHaveClass("debug-hotspots");
    expect(screen.queryByTestId("stage-hotspot-debug")).not.toBeInTheDocument();
  });
});
