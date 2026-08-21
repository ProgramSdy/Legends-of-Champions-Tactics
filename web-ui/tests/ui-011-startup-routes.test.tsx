import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import StartupPage from "@/app/page";
import GamePage from "@/app/game/page";
import AssetRegistryPage from "@/app/assets/page";

// Route tests should verify the route boundary without starting the live API-backed
// battle provider. Existing BattleExperience tests cover that component directly.
vi.mock("@/components/battle/BattleExperience", () => ({
  BattleExperience: () => <main aria-label="Existing team builder">Team Builder</main>,
}));
vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }) }));

describe("UI-011 startup and route boundaries", () => {
  it("renders the supplied startup assets and an accessible save-selection entry", () => {
    render(<StartupPage />);

    screen.getByRole("img", { name: /legends of champions/i });
    // The cinematic layer may be an <img> or a CSS background; either way the
    // route must reference the owner-supplied public asset directly.
    // Next/Image may percent-encode slashes in its optimizer URL. Decode only
    // that stable delimiter so unrelated percent signs in generated markup do
    // not make the assertion itself throw.
    const renderedMarkup = document.body.innerHTML.replaceAll("%2F", "/");
    expect(renderedMarkup).toContain("/game-images/Game_Startup/Game_Startup_01.png");
    expect(renderedMarkup).toContain("/game-images/Game_Logo/Game_Logo_01.png");

    const start = screen.getByRole("button", { name: /start game/i });
    expect(start).toBeVisible();
  });

  it("keeps /game pointed at the existing team-builder experience", async () => {
    render(await GamePage({ searchParams: Promise.resolve({}) }));

    expect(screen.getByRole("main", { name: "Existing team builder" })).toBeVisible();
    expect(screen.queryByRole("button", { name: /start game/i })).not.toBeInTheDocument();
  });

  it("returns from the Asset Registry to /game rather than the startup route", () => {
    render(<AssetRegistryPage />);

    expect(screen.getByRole("link", { name: /return to battle/i })).toHaveAttribute("href", "/game");
  });
});
