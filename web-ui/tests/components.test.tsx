import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { AssetImage } from "@/components/battle/AssetImage";
import { HeroCard, Meter } from "@/components/battle/HeroCard";
import { SkillCard } from "@/components/battle/SkillCard";
import { StatusIcon } from "@/components/battle/StatusIcon";
import { statusRegistry } from "@/lib/battle/assets";
import { initialSnapshot } from "@/lib/battle/fixture";
import type { SkillState, StatusState } from "@/lib/battle/types";

const adapterStatusIds = [
  "status.fatal_strike",
  "status.armor_breaker",
  "status.bleeding_armor_crush",
  "status.wound_armor_crush",
  "status.antivenom_potion",
  "status.bleeding_sharp_blade",
  "status.poisoned_dagger",
  "status.shadow_evasion",
] as const;

describe("battle components", () => {
  it("renders hero identity, active state, HP, resource, and bounded meter widths", () => {
    const arthas = initialSnapshot.combatants["friendly.arthas"];
    const { container } = render(<HeroCard hero={arthas} active />);

    expect(screen.getByRole("article", { name: /Arthas, Necromancer · Necromancer, active hero/i })).toHaveClass("active");
    expect(screen.getByText("61/81")).toBeVisible();
    expect(screen.getByText("2/3")).toBeVisible();
    expect(screen.getByText("Health: 75 percent")).toBeInTheDocument();
    expect(screen.getByText("Placeholder focus: 67 percent")).toBeInTheDocument();

    const fills = container.querySelectorAll<HTMLElement>(".meter > span");
    expect(fills[0]).toHaveStyle({ width: `${61 / 81 * 100}%` });
    expect(fills[1]).toHaveStyle({ width: `${2 / 3 * 100}%` });
  });

  it("clamps malformed bar values and handles a zero maximum", () => {
    const { rerender, container } = render(<Meter value={120} maximum={100} kind="hp" label="Health" />);
    expect(container.querySelector(".meter > span")).toHaveStyle({ width: "100%" });
    rerender(<Meter value={10} maximum={0} kind="resource" label="Focus" />);
    expect(container.querySelector(".meter > span")).toHaveStyle({ width: "0%" });
  });

  it("exposes enabled, selected, cooldown, and disabled skill states", () => {
    const base: SkillState = {
      id: "skill.test", displayName: "Test skill", description: "Test description",
      targetMode: "singleEnemy", maximumTargets: 1, cooldownRemaining: 0,
      available: true, unavailableReason: null, resourceCost: null,
    };
    const onSelect = vi.fn();
    const { rerender } = render(<SkillCard skill={base} selected legal disabled={false} onSelect={onSelect} />);
    const skill = screen.getByRole("button", { name: /Test skill/i });
    expect(skill).toBeEnabled();
    expect(skill).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(skill);
    expect(onSelect).toHaveBeenCalledOnce();

    rerender(<SkillCard skill={{ ...base, cooldownRemaining: 2, available: false, unavailableReason: "Cooldown active" }} selected={false} legal disabled={false} onSelect={onSelect} />);
    expect(screen.getByRole("button", { name: /Test skill/i })).toBeDisabled();
    expect(screen.getByText("Cooldown 2")).toBeVisible();
    expect(screen.getByText("Cooldown active")).toBeVisible();
  });

  it("makes status tooltip content keyboard reachable", () => {
    const status: StatusState = {
      id: "status.stitch_of_agony", instanceId: "status.1", kind: "debuff",
      roundsRemaining: 2, stacks: null, sourceCombatantId: "friendly.arthas",
    };
    render(<StatusIcon status={status} />);
    const icon = screen.getByLabelText(/Stitch of Agony.*2 rounds remaining/i);
    expect(icon).toHaveAttribute("tabindex", "0");
    expect(screen.getByRole("tooltip")).toHaveTextContent("Suffers authoritative damage at round start.");
  });

  it.each(adapterStatusIds)("maps adapter status %s to useful tooltip metadata", (statusId) => {
    const definition = statusRegistry[statusId];
    const status: StatusState = {
      id: statusId, instanceId: `${statusId}.test`, kind: definition.harmful ? "debuff" : "buff",
      roundsRemaining: 2, stacks: null, sourceCombatantId: null,
    };
    render(<StatusIcon status={status} />);

    expect(definition.name).not.toMatch(/unknown/i);
    expect(definition.description.trim().length).toBeGreaterThan(0);
    expect(screen.getByLabelText(
      `${definition.name}. ${definition.description} 2 rounds remaining.`,
    )).toBeVisible();
    expect(screen.getByRole("tooltip")).toHaveTextContent(definition.name);
    expect(screen.getByRole("tooltip")).toHaveTextContent(definition.description);
    expect(screen.queryByText("Unknown status")).not.toBeInTheDocument();
  });

  it("falls back for missing and failed artwork with readable identity", () => {
    const { container, rerender } = render(<AssetImage src={null} name="Flesh Puppet" />);
    expect(screen.getByRole("img", { name: "Flesh Puppet placeholder artwork" })).toHaveTextContent("FP");

    rerender(<AssetImage src="/missing.png" name="Sashein" />);
    fireEvent.error(container.querySelector("img")!);
    expect(screen.getByRole("img", { name: "Sashein placeholder artwork" })).toHaveTextContent("S");
  });
});
