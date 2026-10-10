import { render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { SkillReferenceCard } from "@/components/manual/HeroGalleryExperience";
import { fetchHeroGalleryRoster } from "@/lib/battle/liveProvider";
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
      note: "Healing power before the target's missing-HP cap.",
      conditions: [{ label: "Self-heal when healing another ally", amountRange: { minimum: 17, maximum: 23 } }],
    },
  },
};

describe("UI-028 expanded skill reference card", () => {
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
    expect(screen.getByText("Support the most wounded ally.")).toBeVisible();
    expect(screen.queryByText("Attack Type")).not.toBeInTheDocument();
    expect(screen.queryByText("Damage Type")).not.toBeInTheDocument();
    expect(screen.queryByText("ranged_instant")).not.toBeInTheDocument();
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
});
