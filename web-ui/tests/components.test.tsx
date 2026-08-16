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

  it.each([
    [null, null], [0, null], [-1, null], [1.5, null], [Number.NaN, null],
    [1, "1"], [2, "2"], [99, "99"], [100, "99+"], [999, "99+"],
  ] as const)("renders stack badge %s as %s and exposes exact accessible count", (stacks, badge) => {
    const status: StatusState = {
      id: "status.poisoned_dagger", instanceId: `status.stack.${stacks}`, kind: "debuff",
      roundsRemaining: 2, stacks, sourceCombatantId: null,
    };
    const { container } = render(<StatusIcon status={status} />);
    const icon = screen.getByLabelText(/Poisoned Dagger/);
    if (badge) expect(container.querySelector(".status-stack-badge")).toHaveTextContent(badge);
    else expect(container.querySelector(".status-stack-badge")).not.toBeInTheDocument();
    const validStack = typeof stacks === "number" && Number.isInteger(stacks) && stacks > 0;
    if (validStack) {
      expect(icon).toHaveAccessibleName(new RegExp(`Stack count: ${stacks}\\.`));
      expect(screen.getByRole("tooltip")).toHaveTextContent(`Stack count: ${stacks}.`);
    } else {
      expect(icon).not.toHaveAccessibleName(/Stack count/);
    }
  });

  it("renders stack badges consistently in hero cards", () => {
    const hero = structuredClone(initialSnapshot.combatants["friendly.arthas"]);
    hero.statuses = [{
      id: "status.poisoned_dagger", instanceId: "hero.stack", kind: "debuff",
      roundsRemaining: 2, stacks: 3, sourceCombatantId: null,
    }];
    const { container } = render(<HeroCard hero={hero} />);
    expect(container.querySelector(".status-stack-badge")).toHaveTextContent("3");
  });

  it("renders helpful stack counts with the same accessible contract", () => {
    const status: StatusState = {
      id: "status.wrath_of_crusader", instanceId: "status.buff.stack", kind: "buff",
      roundsRemaining: 3, stacks: 4, sourceCombatantId: null,
    };
    const { container } = render(<StatusIcon status={status} />);
    expect(screen.getByLabelText(/Wrath of Crusader.*Stack count: 4/)).toBeInTheDocument();
    expect(container.querySelector(".status-stack-badge")).toHaveTextContent("4");
    expect(screen.getByRole("tooltip")).toHaveTextContent("Stack count: 4.");
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

  it("loads registered portrait artwork directly rather than through a fixed Next image candidate", () => {
    render(<AssetImage request={{ kind: "portrait", key: "hero.warrior.weapon_master", name: "Ragnar", className: "Warrior" }} className="portrait" />);

    const portrait = screen.getByLabelText("Ragnar portrait");
    expect(portrait).toHaveAttribute("src", "/game-images/heroes/Warrior-Weapon-Master/portraits/Avatar_Warrior_Weapon_Master.png");
    expect(portrait).not.toHaveAttribute("srcset");
    expect(portrait).toHaveAttribute("width", "160");
    expect(portrait).toHaveAttribute("height", "160");
  });
});
