import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { StatusIcon } from "@/components/battle/StatusIcon";

describe("Stage 5.1 battle popup bounds", () => {
  it("uses a viewport-bound portal for status tooltips and keeps keyboard focus usable", async () => {
    render(<StatusIcon status={{
      id: "status.shadow_word_pain",
      instanceId: "status.shadow_word_pain.enemy.1",
      kind: "debuff",
      roundsRemaining: 2,
      stacks: 1,
      sourceCombatantId: "friendly.1",
    }} />);

    const icon = screen.getByLabelText(/Shadow Word: Pain.*Remaining rounds: 2/i);
    fireEvent.focus(icon);

    const tooltip = await screen.findByRole("tooltip");
    await waitFor(() => expect(tooltip).toHaveAttribute("data-positioned", "true"));
    expect(tooltip.parentElement).toBe(document.body);
    expect(icon).toHaveAttribute("aria-describedby", tooltip.id);

    fireEvent.blur(icon!);
    await waitFor(() => expect(screen.queryByRole("tooltip")).not.toBeInTheDocument());
  });
});
