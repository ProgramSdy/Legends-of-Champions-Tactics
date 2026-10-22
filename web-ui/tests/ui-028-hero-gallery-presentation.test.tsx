import { render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { SkillReferenceCard } from "@/components/manual/HeroGalleryExperience";
import { fetchHeroGalleryRoster } from "@/lib/battle/liveProvider";
import { buildSkillReferenceRows } from "@/lib/manual/heroGalleryPresentation";
import type { HeroSkillInventoryItem } from "@/lib/battle/types";

const skill: HeroSkillInventoryItem = {
  skillId: "skill.priest.binding_heal",
  displayName: "Binding Heal",
  isPassive: false,
  reference: {
    target: { mode: "singleAlly" },
    skillType: "damageHealing",
    attackType: { state: "notApplicable" },
    damageNature: { state: "unclassified", reasonId: "definitionMissing" },
    damageType: { state: "notApplicable" },
    baseDamage: { state: "unavailable", reasonId: "targetDependentBaseline", note: "Depends on the selected target." },
    baseHealing: {
      state: "available",
      amountRange: { minimum: 22, maximum: 28 },
      basis: "baselinePower",
      note: "",
      conditions: [{ label: "Healing received by caster", amountRange: { minimum: 17, maximum: 23 } }],
    },
  },
};

describe("UI-028 expanded skill reference card", () => {
  it("shows the audited Cool Down box only for skills with an engine cooldown", async () => {
    const user = userEvent.setup();
    const { rerender } = render(<SkillReferenceCard
      skill={{ ...skill, skillId: "skill.rogue.shadow_evasion", displayName: "Shadow Evasion", reference: {
        ...skill.reference, cooldownRounds: 2,
      } }}
      content={{ introduction: "Enter an evasive stance." }}
    />);
    await user.click(screen.getByText("Shadow Evasion"));
    expect(screen.getByText("Cool Down")).toBeVisible();
    expect(screen.getByText("2 Rounds")).toBeVisible();
    expect(buildSkillReferenceRows({ ...skill.reference, cooldownRounds: 2 }).at(-1)?.id).toBe("cooldown");

    rerender(<SkillReferenceCard
      skill={{ ...skill, reference: { ...skill.reference, cooldownRounds: null } }}
      content={{ introduction: "Restore an ally." }}
    />);
    expect(screen.queryByText("Cool Down")).not.toBeInTheDocument();
    expect(screen.queryByText("2 Rounds")).not.toBeInTheDocument();
  });

  it("rejects a catalogue response whose skill reference shape is incomplete", async () => {
    const malformed = {
      contractVersion: "1.0",
      heroes: [{
        definitionId: "hero.priest.comprehensiveness", displayName: "Priest",
        faculty: "Priest", specialization: "Comprehensiveness",
        startingStatRanges: [], startingResistanceRanges: [], skills: [{ ...skill, reference: {} }],
        unlockSource: null,
      }],
    };
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(malformed), { status: 200 })));
    await expect(fetchHeroGalleryRoster("http://adapter.test")).rejects.toThrow(/unsupported hero roster/);
    vi.unstubAllGlobals();
  });

  it("keeps the native accordion and presents only relevant friendly facts", async () => {
    render(<SkillReferenceCard skill={skill} content={{
      introduction: "Restores an ally and also helps the caster.",
      tips: [{ label: "Strategy Tip", text: "Support the most wounded ally." }],
    }} />);
    const summary = screen.getByText("Binding Heal");
    expect(summary.closest("details")).not.toHaveAttribute("open");
    await userEvent.setup().click(summary);
    expect(summary.closest("details")).toHaveAttribute("open");
    expect(screen.getByText("22–28")).toBeVisible();
    expect(screen.getByText("Damage & Healing")).toBeVisible();
    expect(screen.getByText("One Ally")).toBeVisible();
    expect(screen.getByText("Unclassified")).toBeVisible();
    expect(screen.getByText("Unavailable")).toBeVisible();
    expect(screen.getByText("17–23")).toBeVisible();
    expect(screen.getByText("Healing received by caster")).toBeVisible();
    expect(screen.queryByText("Healing power before the target's missing-HP cap.")).not.toBeInTheDocument();
    expect(screen.getByText("Support the most wounded ally.")).toBeVisible();
    expect(screen.queryByText("Attack Type")).not.toBeInTheDocument();
    expect(screen.queryByText("Damage Type")).not.toBeInTheDocument();
    expect(screen.queryByText("ranged_instant")).not.toBeInTheDocument();
  });

  it("renders the Warrior weapon classification with a player-friendly label", async () => {
    render(<SkillReferenceCard
      skill={{
        ...skill,
        skillId: "skill.warrior.fatal_strike",
        displayName: "Fatal Strike",
        reference: {
          ...skill.reference,
          skillType: "damage",
          attackType: { state: "classified", value: "melee" },
          damageNature: { state: "classified", value: "physical" },
          damageType: { state: "classified", value: "weapon" },
          baseDamage: {
            state: "unavailable",
            reasonId: "targetDependentBaseline",
            displayLabel: "Target-dependent",
            note: "Direct damage depends on the selected target's Defence.",
            calculation: {
              title: "Damage Calculation",
              formula: "Direct damage = max(Caster Damage + Skill Variation − Target Defence, 1)",
            },
          },
          baseHealing: { state: "notApplicable" },
        },
      }}
      content={{ introduction: "A decisive weapon strike." }}
    />);
    const user = userEvent.setup();
    await user.click(screen.getByText("Fatal Strike"));
    expect(screen.getByText("Physical")).toBeVisible();
    expect(screen.getByText("Weapon")).toBeVisible();
    expect(screen.getByText("Target-dependent")).toBeVisible();
    await user.click(screen.getByRole("button", { name: /open damage calculation/i }));
    expect(screen.getByRole("dialog", { name: "Damage Calculation" })).toHaveTextContent(
      "Direct damage = max(Caster Damage + Skill Variation − Target Defence, 1)",
    );
    await user.click(screen.getByRole("button", { name: "Close damage calculation" }));
    expect(screen.queryByRole("dialog", { name: "Damage Calculation" })).not.toBeInTheDocument();
  });

  it("renders the Armor Crush target-dependent formula and all Armor Breaker bands", async () => {
    render(<SkillReferenceCard
      skill={{
        ...skill,
        skillId: "skill.warrior.armor_crush",
        displayName: "Armor Crush",
        reference: {
          ...skill.reference,
          skillType: "damage",
          attackType: { state: "classified", value: "melee" },
          damageNature: { state: "classified", value: "physical" },
          damageType: { state: "classified", value: "weapon" },
          baseDamage: {
            state: "unavailable",
            reasonId: "targetDependentBaseline",
            displayLabel: "Target-dependent",
            note: "Direct damage depends on the selected target's Defence and Armor Breaker state.",
            calculation: {
              title: "Damage Calculation",
              formula: "Direct damage = max(ceil((Caster Damage + Skill Variation − Target Defence) × Armor Breaker multiplier), 1)\nArmor Breaker multiplier: no Armor Breaker or 0 stacks = 55%; 1 stack = 65%; 2 or more stacks = 75%",
            },
          },
          baseHealing: { state: "notApplicable" },
        },
      }}
      content={{ introduction: "A crushing strike that weakens armour." }}
    />);
    const user = userEvent.setup();
    await user.click(screen.getByText("Armor Crush"));
    expect(screen.getByText("Target-dependent")).toBeVisible();
    await user.click(screen.getByRole("button", { name: /open damage calculation/i }));
    expect(screen.getByRole("dialog", { name: "Damage Calculation" })).toHaveTextContent(
      "Direct damage = max(ceil((Caster Damage + Skill Variation − Target Defence) × Armor Breaker multiplier), 1) Armor Breaker multiplier: no Armor Breaker or 0 stacks = 55%; 1 stack = 65%; 2 or more stacks = 75%",
    );
  });

  it("renders Antivenom Potion self-healing and omits inapplicable damage", async () => {
    render(<SkillReferenceCard
      skill={{
        ...skill,
        skillId: "skill.warrior.antivenom_potion",
        displayName: "Antivenom Potion",
        reference: {
          ...skill.reference,
          target: { mode: "self" },
          skillType: "buff",
          attackType: { state: "notApplicable" },
          damageNature: { state: "notApplicable" },
          damageType: { state: "notApplicable" },
          baseDamage: { state: "notApplicable" },
          baseHealing: {
            state: "available",
            amountRange: { minimum: 18, maximum: 20 },
            basis: "baselinePower",
            note: "",
            conditions: [],
          },
        },
      }}
      content={{ introduction: "Drink a potion to recover health." }}
    />);
    await userEvent.setup().click(screen.getByText("Antivenom Potion"));
    expect(screen.getByText("Self")).toBeVisible();
    expect(screen.getByText("18–20")).toBeVisible();
    expect(screen.queryByText("Self-healing power before healing modifiers and HP cap.")).not.toBeInTheDocument();
    expect(screen.queryByText("Base Damage")).not.toBeInTheDocument();
  });

  it("renders the backend-owned Shadow Word Pain calculation dialog", async () => {
    render(<SkillReferenceCard
      skill={{
        ...skill,
        skillId: "skill.priest.shadow_word_pain",
        displayName: "Shadow Word Pain",
        reference: {
          ...skill.reference,
          skillType: "damage",
          attackType: { state: "classified", value: "rangedInstant" },
          damageNature: { state: "classified", value: "magical" },
          damageType: { state: "classified", value: "shadow" },
          baseDamage: {
            state: "unavailable",
            reasonId: "targetDependentBaseline",
            displayLabel: "Target-dependent",
            note: "The target's Shadow Resistance is part of the immediate formula.",
            calculation: {
              title: "Damage Calculation",
              formula: "Direct damage = round((Caster Damage + Skill Variation − Target Shadow Resistance) ÷ 2)\nContinuous damage = max(1, round((Caster Original Damage − Target Shadow Resistance) ÷ 3) + Skill Variation)",
            },
          },
          baseHealing: { state: "notApplicable" },
        },
      }}
      content={{ introduction: "Marks one enemy with a continuing shadow affliction." }}
    />);
    const user = userEvent.setup();
    await user.click(screen.getByText("Shadow Word Pain"));
    expect(screen.getByText("Target-dependent")).toBeVisible();
    expect(screen.queryByText("The target's Shadow Resistance is part of the immediate formula.")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /open damage calculation/i }));
    expect(screen.getByRole("dialog", { name: "Damage Calculation" })).toHaveTextContent(
      "Direct damage = round((Caster Damage + Skill Variation − Target Shadow Resistance) ÷ 2) Continuous damage = max(1, round((Caster Original Damage − Target Shadow Resistance) ÷ 3) + Skill Variation)",
    );
    await user.click(screen.getByRole("button", { name: "Close damage calculation" }));
    expect(screen.queryByRole("dialog", { name: "Damage Calculation" })).not.toBeInTheDocument();
  });

  it("renders the backend-owned Rogue target-dependent formula dialog", async () => {
    render(<SkillReferenceCard
      skill={{
        ...skill,
        skillId: "skill.rogue.poisoned_dagger",
        displayName: "Poisoned Dagger",
        reference: {
          ...skill.reference,
          skillType: "damage",
          attackType: { state: "classified", value: "rangedInstant" },
          damageNature: { state: "classified", value: "physical" },
          damageType: { state: "classified", value: "weapon" },
          baseDamage: {
            state: "unavailable",
            reasonId: "targetDependentBaseline",
            displayLabel: "Target-dependent",
            note: "Direct damage depends on the selected target's Defence.",
            calculation: {
              title: "Damage Calculation",
              formula: "Direct damage = max(round((Caster Damage + Skill Variation − Target Defence) ÷ 2), 0)\nPoison damage per stack = ceil((Caster Damage + Skill Variation − Target Poison Resistance) ÷ 4)",
            },
          },
          baseHealing: { state: "notApplicable" },
        },
      }}
      content={{ introduction: "A ranged dagger attack that can apply poison." }}
    />);
    const user = userEvent.setup();
    await user.click(screen.getByText("Poisoned Dagger"));
    expect(screen.getByText("Target-dependent")).toBeVisible();
    await user.click(screen.getByRole("button", { name: /open damage calculation/i }));
    expect(screen.getByRole("dialog", { name: "Damage Calculation" })).toHaveTextContent(
      "Direct damage = max(round((Caster Damage + Skill Variation − Target Defence) ÷ 2), 0) Poison damage per stack = ceil((Caster Damage + Skill Variation − Target Poison Resistance) ÷ 4)",
    );
  });

  it("formats multi-target and classified values without exposing raw enums", async () => {
    render(<SkillReferenceCard
      skill={{
        ...skill,
        skillId: "skill.mage.arcane_missiles",
        displayName: "Arcane Missiles",
        reference: {
          ...skill.reference,
          target: { mode: "multipleEnemies", maximumTargets: 2 },
          skillType: "damage",
          attackType: { state: "classified", value: "rangedProjectile" },
          damageNature: { state: "classified", value: "magical" },
          damageType: { state: "classified", value: "arcane" },
          baseDamage: { state: "unavailable", reasonId: "notAudited", note: "Reference power has not yet been audited." },
          baseHealing: { state: "notApplicable" },
        },
      }}
      content={{ introduction: "Arcane projectiles directed at multiple enemies." }}
    />);
    await userEvent.setup().click(screen.getByText("Arcane Missiles"));
    expect(screen.getByText("Up to 2 Enemies")).toBeVisible();
    expect(screen.getByText("Ranged Projectile")).toBeVisible();
    expect(screen.getByText("Magical")).toBeVisible();
    expect(screen.getByText("Arcane")).toBeVisible();
    expect(screen.queryByText("Base Healing")).not.toBeInTheDocument();
  });

  it("keeps responsive facts two-column on wide cards and one-column on narrow cards", () => {
    const css = readFileSync("app/globals.css", "utf8");
    expect(css).toMatch(/\.hero-profile \.skill-reference-grid\{[^}]*grid-template-columns:repeat\(2,minmax\(0,1fr\)\)/);
    expect(css).toMatch(/@media\(max-width:620px\)\{[^}]*\.hero-profile \.skill-reference-grid\{grid-template-columns:1fr\}/s);
  });

  it("preserves authored line breaks and indentation in a skill introduction", async () => {
    const introduction = "A crushing strike that weakens armour.\n Special Effect:\n   Two stacks apply Wound.\n   Three stacks apply Bleeding.";
    render(<SkillReferenceCard
      skill={{ ...skill, displayName: "Armor Crush" }}
      content={{ introduction }}
    />);
    await userEvent.setup().click(screen.getByText("Armor Crush"));
    expect(screen.getByText(/Special Effect:/).textContent).toBe(introduction);
    const css = readFileSync("app/globals.css", "utf8");
    expect(css).toMatch(/\.hero-gallery-page \.skill-reference-copy>p\{white-space:pre-wrap;overflow-wrap:anywhere\}/);
  });
});
