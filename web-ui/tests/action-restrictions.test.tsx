import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { BattleScreen } from "@/components/battle/BattleScreen";
import { createFormatFixture, MockBattleProvider } from "@/lib/battle/fixture";
import type { BattleSnapshot } from "@/lib/battle/types";

function restrictedSnapshot(
  disposition: "skip" | "automaticAction",
  reasonId: "stunned" | "scoff",
): BattleSnapshot {
  const snapshot = createFormatFixture(1);
  const actorId = snapshot.activeCombatantId!;
  snapshot.turnControl = {
    disposition,
    acceptsCommands: false,
    reasonId,
    actorCombatantId: actorId,
    sourceCombatantId: reasonId === "scoff" ? "enemy.nighthawk" : null,
    forcedTargetIds: reasonId === "scoff" ? ["enemy.nighthawk"] : [],
  };
  // Deliberately retain hostile legal-action data. The explicit control
  // directive must remain the sole UI interaction gate.
  expect(snapshot.legalActions.length).toBeGreaterThan(0);
  return snapshot;
}

describe("authoritative action restrictions", () => {
  it.each([
    ["skip", "stunned", "ACTION RESTRICTED · TURN SKIPPED"],
    ["automaticAction", "scoff", "ACTION RESOLVING AUTOMATICALLY"],
  ] as const)(
    "blocks ordinary controls for %s turns even if legal actions are present",
    async (disposition, reasonId, intent) => {
      const provider = new MockBattleProvider(
        restrictedSnapshot(disposition, reasonId),
      );
      const submit = vi.spyOn(provider, "submitCommand");
      render(<BattleScreen provider={provider} mode="live" />);

      expect(await screen.findByText(intent)).toBeVisible();
      expect(screen.getByRole("button", { name: "AUTOMATIC TURN" })).toBeDisabled();
      for (const skill of screen.getAllByRole("button", {
        name: /Fatal Strike|Armor Crush|Antivenom Potion/,
      })) {
        expect(skill).toBeDisabled();
        fireEvent.click(skill);
      }
      expect(screen.queryByRole("button", { name: "CAST SKILL" }))
        .not.toBeInTheDocument();
      expect(screen.queryByRole("button", { name: /selectable target/ }))
        .not.toBeInTheDocument();
      expect(submit).not.toHaveBeenCalled();
    },
  );

  it("gates intermediate automatic presentation and restores the final player boundary", async () => {
    const initial = createFormatFixture(1);
    const final = structuredClone(initial);
    final.round = 2;
    const provider = new MockBattleProvider(initial);
    vi.spyOn(provider, "submitCommand").mockResolvedValue({
      revision: 2,
      snapshot: final,
      events: [
        {
          id: "evt.auto.1",
          sequence: 1,
          type: "turnStarted",
          sourceId: "enemy.nighthawk",
          message: "Nighthawk's automatic turn started.",
        },
        {
          id: "evt.auto.2",
          sequence: 2,
          type: "skillStarted",
          sourceId: "enemy.nighthawk",
          targetIds: ["friendly.ragnar"],
          skillId: "skill.rogue.sharp_blade",
          message: "Nighthawk used Sharp Blade.",
        },
        {
          id: "evt.auto.3",
          sequence: 3,
          type: "turnEnded",
          sourceId: "enemy.nighthawk",
          message: "Nighthawk's automatic turn ended.",
        },
      ],
    });
    const { container } = render(<BattleScreen provider={provider} mode="live" />);

    await screen.findByText("CHOOSE AN AUTHORIZED SKILL");
    fireEvent.click(screen.getByRole("button", { name: "×2" }));
    fireEvent.click(screen.getByRole("button", { name: /Fatal Strike/i }));
    fireEvent.click(screen.getByRole("button", {
      name: "Nighthawk, selectable target",
    }));
    fireEvent.click(screen.getByRole("button", { name: "CAST SKILL" }));

    await waitFor(() => {
      expect(container.querySelector(".acting-card h2"))
        .toHaveTextContent("Nighthawk");
    });
    expect(screen.getByText("RESOLVING AUTHORITATIVE ACTION")).toBeVisible();
    expect(screen.queryByRole("button", { name: "CAST SKILL" }))
      .not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /selectable target/ }))
      .not.toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("CHOOSE AN AUTHORIZED SKILL")).toBeVisible();
      expect(screen.getByRole("button", { name: /Fatal Strike/i })).toBeEnabled();
    }, { timeout: 4000 });
  });

  it("presents a real restricted turnStarted-to-turnEnded sequence as a skip", async () => {
    const initial = createFormatFixture(1);
    const final = structuredClone(initial);
    final.round = 2;
    const provider = new MockBattleProvider(initial);
    vi.spyOn(provider, "submitCommand").mockResolvedValue({
      revision: 2,
      snapshot: final,
      events: [
        {
          id: "evt.skip.1",
          sequence: 1,
          type: "turnStarted",
          sourceId: "enemy.nighthawk",
          message: "Nighthawk's turn started.",
        },
        {
          id: "evt.skip.2",
          sequence: 2,
          type: "turnEnded",
          sourceId: "enemy.nighthawk",
          reasonId: "stunned",
          message: "Nighthawk is stunned and cannot act; their turn ended.",
        },
      ],
    });
    render(<BattleScreen provider={provider} mode="live" />);

    await screen.findByText("CHOOSE AN AUTHORIZED SKILL");
    fireEvent.click(screen.getByRole("button", { name: "×2" }));
    fireEvent.click(screen.getByRole("button", { name: /Fatal Strike/i }));
    fireEvent.click(screen.getByRole("button", {
      name: "Nighthawk, selectable target",
    }));
    fireEvent.click(screen.getByRole("button", { name: "CAST SKILL" }));

    expect(await screen.findByText("ACTION RESTRICTED · TURN SKIPPED"))
      .toBeVisible();
    expect(screen.queryByRole("button", { name: "CAST SKILL" }))
      .not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /selectable target/ }))
      .not.toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Fatal Strike/i })).toBeEnabled();
    }, { timeout: 3000 });
  });
});
