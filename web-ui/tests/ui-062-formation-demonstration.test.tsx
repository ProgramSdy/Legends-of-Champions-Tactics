import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { BattleInstructionExperience } from "@/components/manual/BattleInstructionExperience";
import { createFormationCatalogue } from "./fixtures/formationCatalogue";

afterEach(() => vi.unstubAllGlobals());

describe("UI-062 interactive formation demonstration", () => {
  it("selects attackers and attack types from authoritative result rows", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(createFormationCatalogue()), { status: 200 })));
    const user = userEvent.setup();
    render(<BattleInstructionExperience />);
    await user.click(screen.getByRole("tab", { name: /Formations & Attack Types/ }));
    await waitFor(() => expect(screen.getByText("front melee explanation")).toBeVisible());
    expect(screen.getByRole("button", { name: /Friendly Hero 1, front, selected attacker/i })).toHaveAttribute("aria-pressed", "true");
    await user.click(screen.getByRole("button", { name: "Ranged Projectile" }));
    expect(screen.getByText("front rangedProjectile explanation")).toBeVisible();
    await user.click(screen.getByRole("button", { name: /Friendly Hero 2, rear, select as attacker/i }));
    expect(screen.getByText("rear rangedProjectile explanation")).toBeVisible();
  });

  it("marks defeated fronts and clears the state when changing formation", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(createFormationCatalogue()), { status: 200 })));
    const user = userEvent.setup();
    render(<BattleInstructionExperience />);
    await user.click(screen.getByRole("tab", { name: /Formations & Attack Types/ }));
    await waitFor(() => expect(screen.getByText("front melee explanation")).toBeVisible());
    const switchControl = screen.getByRole("switch", { name: /Enemy front line defeated/ });
    await user.click(switchControl);
    expect(screen.getByText("front melee explanation")).toBeVisible();
    expect(screen.getByLabelText(/Enemy Hero 1, front: Defeated/)).toBeVisible();
    await user.click(screen.getByRole("button", { name: /3v3.*All Front/ }));
    expect(screen.queryByRole("switch", { name: /Enemy front line defeated/ })).not.toBeInTheDocument();
    expect(screen.queryByText("rear melee explanation")).not.toBeInTheDocument();
    expect(screen.getByText("front melee explanation")).toBeVisible();
  });

  it("supports keyboard attacker selection and resets an invalid slot after 3v3 to 2v2", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(createFormationCatalogue()), { status: 200 })));
    const user = userEvent.setup();
    render(<BattleInstructionExperience />);
    await user.click(screen.getByRole("tab", { name: /Formations & Attack Types/ }));
    await waitFor(() => expect(screen.getByText("front melee explanation")).toBeVisible());
    await user.click(screen.getByRole("button", { name: /3v3.*Two Front, One Rear/ }));
    const third = screen.getByRole("button", { name: /Friendly Hero 3, rear, select as attacker/ });
    third.focus();
    await user.keyboard("{Enter}");
    expect(screen.getByRole("button", { name: /Friendly Hero 3, rear, selected attacker/ })).toHaveAttribute("aria-pressed", "true");
    await user.click(screen.getByRole("switch", { name: /Enemy front line defeated/ }));
    await user.click(screen.getByRole("button", { name: /2v2.*Front & Rear/ }));
    expect(screen.getByRole("button", { name: /Friendly Hero 1, front, selected attacker/ })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("switch", { name: /Enemy front line defeated/ })).not.toBeChecked();
    expect(screen.queryByRole("button", { name: /Friendly Hero 3/ })).not.toBeInTheDocument();
  });

  it("rejects missing or duplicated authoritative scenarios instead of showing partial rules", async () => {
    const incomplete = createFormationCatalogue();
    incomplete.formations[0].evaluations.pop();
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(incomplete), { status: 200 })));
    const user = userEvent.setup();
    render(<BattleInstructionExperience />);
    await user.click(screen.getByRole("tab", { name: /Formations & Attack Types/ }));
    expect(await screen.findByRole("alert")).toHaveTextContent("incomplete rule data");
    expect(screen.queryByText(/% damage/)).not.toBeInTheDocument();
  });

  it("rejects a string multiplier instead of coercing it into a rule percentage", async () => {
    const malformed = createFormationCatalogue();
    malformed.formations[0].evaluations[0].targets[0].multiplierPercent = "100" as unknown as number;
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(malformed), { status: 200 })));
    const user = userEvent.setup();
    render(<BattleInstructionExperience />);
    await user.click(screen.getByRole("tab", { name: /Formations & Attack Types/ }));
    expect(await screen.findByRole("alert")).toHaveTextContent("invalid rule data");
  });

  it("shows an unavailable alert instead of inferring malformed rule data", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ contractVersion: "1.0", attackTypes: ["melee", "rangedProjectile", "rangedInstant"], formations: [] }), { status: 200 })));
    const user = userEvent.setup();
    render(<BattleInstructionExperience />);
    await user.click(screen.getByRole("tab", { name: /Formations & Attack Types/ }));
    expect(await screen.findByRole("alert")).toHaveTextContent("invalid rule data");
    expect(screen.queryByText(/% damage/)).not.toBeInTheDocument();
  });
});
