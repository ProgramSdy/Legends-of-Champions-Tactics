import { fireEvent, render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { SkillReferenceCard } from "@/components/manual/HeroGalleryExperience";
import { SkillCard } from "@/components/battle/SkillCard";
import { StatusIcon } from "@/components/battle/StatusIcon";
import { skillPresentation, statusRegistry } from "@/lib/battle/assets";
import { fetchHeroGalleryRoster } from "@/lib/battle/liveProvider";
import { buildSkillReferenceRows } from "@/lib/manual/heroGalleryPresentation";
import type { HeroSkillInventoryItem, SkillState, StatusState } from "@/lib/battle/types";

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
    continuousDamage: { state: "notApplicable" },
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
  it("reuses the complete Priest Comprehensiveness artwork set across battle, Gallery, and Shadow Word Pain status", () => {
    const definitions = [
      ["skill.priest.holy_smite", "Holy Smite", "/game-images/heroes/Priest-Comprehensiveness/skills/Holy_Smite_128x128.png"],
      ["skill.priest.shadow_word_pain", "Shadow Word Pain", "/game-images/heroes/Priest-Comprehensiveness/skills/Shadow_Word_Pain_128x128.png"],
      ["skill.priest.binding_heal", "Binding Heal", "/game-images/heroes/Priest-Comprehensiveness/skills/Binding_Heal_128x128.png"],
    ] as const;
    const skills: SkillState[] = definitions.map(([id, displayName]) => ({
      id, displayName, targetMode: id === "skill.priest.binding_heal" ? "singleAlly" : "singleEnemy",
      maximumTargets: 1, cooldownRemaining: 0, available: true,
      unavailableReason: null, resourceCost: null,
    }));
    const gallerySkills = definitions.map(([skillId, displayName]) => ({ ...skill, skillId, displayName }));
    const shadowStatus: StatusState = {
      id: "status.shadow_word_pain", instanceId: "status.shadow.art", kind: "debuff",
      roundsRemaining: 4, stacks: null, sourceCombatantId: "friendly.priest.1",
    };

    const { container } = render(<>
      {skills.map((item) => <SkillCard key={`battle-${item.id}`} skill={item} selected={false} legal disabled={false} onSelect={() => undefined} />)}
      {gallerySkills.map((item) => <SkillReferenceCard key={`gallery-${item.skillId}`} skill={item} content={{ introduction: `${item.displayName} introduction.` }} />)}
      <StatusIcon status={shadowStatus} />
    </>);

    const battleArtwork = [...container.querySelectorAll<HTMLImageElement>(".skill-glyph-art")].map((image) => image.getAttribute("src"));
    const galleryArtwork = [...container.querySelectorAll<HTMLImageElement>(".skill-reference-summary-art img")].map((image) => image.getAttribute("src"));
    expect(battleArtwork).toEqual(definitions.map(([, , path]) => path));
    expect(galleryArtwork).toEqual(definitions.map(([, , path]) => path));
    expect(statusRegistry["status.shadow_word_pain"].asset).toBe(skillPresentation["skill.priest.shadow_word_pain"].asset);
    expect(statusRegistry["status.holy_smite"]).toBeUndefined();
    expect(statusRegistry["status.binding_heal"]).toBeUndefined();

    const statusArtwork = container.querySelector<HTMLImageElement>(".status-icon-art");
    expect(statusArtwork).toHaveAttribute("src", definitions[1][2]);
    const statusIcon = screen.getByLabelText(/Shadow Word: Pain.*4 rounds remaining/i);
    expect(statusIcon).toHaveClass("harmful");
    fireEvent.error(statusArtwork!);
    expect(statusIcon).toHaveTextContent(statusRegistry[shadowStatus.id].glyph);
  });

  it("reuses the complete Mage Comprehensiveness artwork set across battle, Gallery, and the shared Cold status", () => {
    const definitions = [
      ["skill.mage.fireball", "Fireball", "/game-images/heroes/Mage-Comprehensiveness/skills/Mage_Fireball_128x128.png"],
      ["skill.mage.arcane_missiles", "Arcane Missiles", "/game-images/heroes/Mage-Comprehensiveness/skills/arcane_missiles_128x128.png"],
      ["skill.mage.frost_bolt", "Frost Bolt", "/game-images/heroes/Mage-Comprehensiveness/skills/Mage_Frost_Bolt_128x128.png"],
    ] as const;
    const skills: SkillState[] = definitions.map(([id, displayName]) => ({
      id, displayName, targetMode: id === "skill.mage.arcane_missiles" ? "multiEnemy" : "singleEnemy",
      maximumTargets: id === "skill.mage.arcane_missiles" ? 2 : 1, cooldownRemaining: 0, available: true,
      unavailableReason: null, resourceCost: null,
    }));
    const gallerySkills = definitions.map(([skillId, displayName]) => ({ ...skill, skillId, displayName }));
    const coldStatus: StatusState = {
      id: "status.cold", instanceId: "status.cold.art", kind: "debuff",
      roundsRemaining: 2, stacks: null, sourceCombatantId: "friendly.mage.1",
    };

    const { container } = render(<>
      {skills.map((item) => <SkillCard key={`battle-${item.id}`} skill={item} selected={false} legal disabled={false} onSelect={() => undefined} />)}
      {gallerySkills.map((item) => <SkillReferenceCard key={`gallery-${item.skillId}`} skill={item} content={{ introduction: `${item.displayName} introduction.` }} />)}
      <StatusIcon status={coldStatus} />
    </>);

    const battleArtwork = [...container.querySelectorAll<HTMLImageElement>(".skill-glyph-art")].map((image) => image.getAttribute("src"));
    const galleryArtwork = [...container.querySelectorAll<HTMLImageElement>(".skill-reference-summary-art img")].map((image) => image.getAttribute("src"));
    expect(battleArtwork).toEqual(definitions.map(([, , path]) => path));
    expect(galleryArtwork).toEqual(definitions.map(([, , path]) => path));
    expect(statusRegistry["status.cold"].asset).toBe(skillPresentation["skill.mage.frost_bolt"].asset);
    expect(statusRegistry["status.fireball"]).toBeUndefined();
    expect(statusRegistry["status.arcane_missiles"]).toBeUndefined();

    const statusArtwork = container.querySelector<HTMLImageElement>(".status-icon-art");
    expect(statusArtwork).toHaveAttribute("src", definitions[2][2]);
    const statusIcon = screen.getByLabelText(/Cold.*2 rounds remaining/i);
    expect(statusIcon).toHaveClass("harmful");
    fireEvent.error(statusArtwork!);
    expect(statusIcon).toHaveTextContent(statusRegistry[coldStatus.id].glyph);
  });

  it("keeps Warrior Weapon Master skill art separate from its dedicated status-only artwork", () => {
    const skillDefinitions = [
      ["skill.warrior.fatal_strike", "Fatal Strike", "/game-images/heroes/Warrior-Weapon-Master/skills/Warrior_Fatal_Strike_128x128.png"],
      ["skill.warrior.armor_crush", "Armor Crush", "/game-images/heroes/Warrior-Weapon-Master/skills/Warrior_Armor_Crush_128x128.png"],
      ["skill.warrior.antivenom_potion", "Antivenom Potion", "/game-images/heroes/Warrior-Weapon-Master/skills/Warrior_Antivenom_Potion_128x128.png"],
    ] as const;
    const statusDefinitions = [
      ["status.fatal_strike", "/game-images/heroes/Warrior-Weapon-Master/skills/Warrior_Fatal_Strike_128x128.png", "debuff"],
      ["status.armor_breaker", "/game-images/heroes/Warrior-Weapon-Master/skills/Warrior_Armor_Break_128x128.png", "debuff"],
      ["status.wound_armor_crush", "/game-images/heroes/Warrior-Weapon-Master/skills/Warrior_Wound_Armor_Crush_128x128.png", "debuff"],
      ["status.bleeding_armor_crush", "/game-images/heroes/Warrior-Weapon-Master/skills/Warrior_Bleeding_Armor_Crush_128x128.png", "debuff"],
      ["status.antivenom_potion", "/game-images/heroes/Warrior-Weapon-Master/skills/Warrior_Antivenom_Potion_128x128.png", "buff"],
    ] as const;
    const skills: SkillState[] = skillDefinitions.map(([id, displayName]) => ({
      id, displayName, targetMode: id === "skill.warrior.antivenom_potion" ? "self" : "singleEnemy",
      maximumTargets: id === "skill.warrior.antivenom_potion" ? 0 : 1,
      cooldownRemaining: 0, available: true, unavailableReason: null, resourceCost: null,
    }));
    const gallerySkills = skillDefinitions.map(([skillId, displayName]) => ({ ...skill, skillId, displayName }));
    const statuses: StatusState[] = statusDefinitions.map(([id, , kind], index) => ({
      id, instanceId: `${id}.art`, kind, roundsRemaining: 2, stacks: index === 1 ? 2 : null,
      sourceCombatantId: "friendly.warrior.1",
    }));

    const { container } = render(<>
      {skills.map((item) => <SkillCard key={`battle-${item.id}`} skill={item} selected={false} legal disabled={false} onSelect={() => undefined} />)}
      {gallerySkills.map((item) => <SkillReferenceCard key={`gallery-${item.skillId}`} skill={item} content={{ introduction: `${item.displayName} introduction.` }} />)}
      {statuses.map((status) => <StatusIcon key={status.id} status={status} />)}
    </>);

    expect([...container.querySelectorAll<HTMLImageElement>(".skill-glyph-art")].map((image) => image.getAttribute("src")))
      .toEqual(skillDefinitions.map(([, , path]) => path));
    expect([...container.querySelectorAll<HTMLImageElement>(".skill-reference-summary-art img")].map((image) => image.getAttribute("src")))
      .toEqual(skillDefinitions.map(([, , path]) => path));
    expect(statusDefinitions.map(([id]) => statusRegistry[id].asset)).toEqual(statusDefinitions.map(([, path]) => path));
    expect(statusRegistry["status.fatal_strike"].asset).toBe(skillPresentation["skill.warrior.fatal_strike"].asset);
    expect(statusRegistry["status.antivenom_potion"].asset).toBe(skillPresentation["skill.warrior.antivenom_potion"].asset);
    expect(statusRegistry["status.armor_breaker"].asset).not.toBe(skillPresentation["skill.warrior.armor_crush"].asset);
    expect(Object.values(skillPresentation).map((entry) => entry.asset)).not.toContain(statusDefinitions[1][1]);
    expect(Object.values(skillPresentation).map((entry) => entry.asset)).not.toContain(statusDefinitions[2][1]);
    expect(Object.values(skillPresentation).map((entry) => entry.asset)).not.toContain(statusDefinitions[3][1]);

    const armorBreaker = screen.getByLabelText(/Armor Breaker.*Stack count: 2.*2 rounds remaining/i);
    expect(armorBreaker).toHaveClass("harmful");
    expect(screen.getByLabelText(/Antivenom Potion.*2 rounds remaining/i)).toHaveClass("helpful");
    const armorBreakArtwork = armorBreaker.querySelector<HTMLImageElement>(".status-icon-art");
    expect(armorBreakArtwork).toHaveAttribute("src", statusDefinitions[1][1]);
    fireEvent.error(armorBreakArtwork!);
    expect(armorBreaker).toHaveTextContent(statusRegistry["status.armor_breaker"].glyph);
  });

  it("keeps Paladin Retribution active art separate from the passive Wrath presentation", () => {
    const activeDefinitions = [
      ["skill.paladin.hammer_of_anger", "Hammer of Anger", "/game-images/heroes/Paladin-Retribution/skills/Paladin_Hammer_of_Anger_128x128.png"],
      ["skill.paladin.crusader_strike", "Crusader Strike", "/game-images/heroes/Paladin-Retribution/skills/Paladin_Crusader_Strike_128x128_Final.png"],
      ["skill.paladin.flash_of_light", "Flash of Light", "/game-images/heroes/Paladin-Retribution/skills/Paladin_Flash_of_Light_128x128.png"],
    ] as const;
    const passiveDefinition = [
      "skill.paladin.wrath_of_crusader",
      "Wrath of Crusader",
      "/game-images/heroes/Paladin-Retribution/skills/Paladin_Wrath_of_Crusader_Black_BG_128x128.png",
    ] as const;
    const activeSkills: SkillState[] = activeDefinitions.map(([id, displayName]) => ({
      id, displayName,
      targetMode: id === "skill.paladin.flash_of_light" ? "singleAlly" : "singleEnemy",
      maximumTargets: 1, cooldownRemaining: 0, available: true,
      unavailableReason: null, resourceCost: null,
    }));
    const passiveSkill: SkillState = {
      id: passiveDefinition[0], displayName: passiveDefinition[1], targetMode: "self",
      maximumTargets: 0, cooldownRemaining: 0, available: true,
      unavailableReason: null, resourceCost: null, isPassive: true,
    };
    const gallerySkills = [
      ...activeDefinitions.map(([skillId, displayName]) => ({ ...skill, skillId, displayName })),
      { ...skill, skillId: passiveDefinition[0], displayName: passiveDefinition[1], isPassive: true },
    ];
    const wrathStatus: StatusState = {
      id: "status.wrath_of_crusader", instanceId: "status.wrath_of_crusader.art", kind: "buff",
      roundsRemaining: 3, stacks: 2, sourceCombatantId: "friendly.paladin.1",
    };

    const { container } = render(<>
      {[...activeSkills, passiveSkill].map((item) => (
        <SkillCard key={`battle-${item.id}`} skill={item} selected={false} legal disabled={false} onSelect={() => undefined} />
      ))}
      {gallerySkills.map((item) => (
        <SkillReferenceCard key={`gallery-${item.skillId}`} skill={item} content={{ introduction: `${item.displayName} introduction.` }} />
      ))}
      <StatusIcon status={wrathStatus} />
    </>);

    const expectedPaths = [...activeDefinitions.map(([, , path]) => path), passiveDefinition[2]];
    expect([...container.querySelectorAll<HTMLImageElement>(".skill-glyph-art")].map((image) => image.getAttribute("src")))
      .toEqual(expectedPaths);
    expect([...container.querySelectorAll<HTMLImageElement>(".skill-reference-summary-art img")].map((image) => image.getAttribute("src")))
      .toEqual(expectedPaths);
    expect(container.querySelector<HTMLButtonElement>(".skill-card.passive")).toBeDisabled();
    expect(statusRegistry[wrathStatus.id].asset).toBe(skillPresentation[passiveDefinition[0]].asset);
    expect(statusRegistry[wrathStatus.id].asset).not.toBe(skillPresentation["skill.paladin.crusader_strike"].asset);
    expect(statusRegistry["status.hammer_of_anger"]).toBeUndefined();
    expect(statusRegistry["status.flash_of_light"]).toBeUndefined();

    const wrathIcon = screen.getByLabelText(/Wrath of Crusader.*Stack count: 2.*3 rounds remaining/i);
    expect(wrathIcon).toHaveClass("helpful");
    const wrathArtwork = wrathIcon.querySelector<HTMLImageElement>(".status-icon-art");
    expect(wrathArtwork).toHaveAttribute("src", passiveDefinition[2]);
    fireEvent.error(wrathArtwork!);
    expect(wrathIcon).toHaveTextContent(statusRegistry[wrathStatus.id].glyph);
  });

  it("shares Paladin Protection art across battle, Gallery, and only its own statuses", () => {
    const definitions = [
      ["skill.paladin.hammer_of_revenge", "Hammer of Revenge", "Paladin_Protection_Hammer_of_Revenge_128x128.png", false],
      ["skill.paladin.shield_of_righteous", "Shield of Righteous", "Paladin_Protection_Shield_of_Righteous_128x128.png", false],
      ["skill.paladin.heroric_charge", "Heroic Charge", "Paladin_Protection_Heroic_Charge_128x128.png", false],
      ["skill.paladin.holy_aura", "Holy Aura", "Paladin_Protection_Holy_Aura_128x128.png", true],
    ] as const;
    const statuses = [
      ["status.hammer_of_revenge", definitions[0][0], "debuff"],
      ["status.shield_of_righteous", definitions[1][0], "buff"],
      ["status.holy_aura", definitions[3][0], "buff"],
    ] as const;
    const { container } = render(<>
      {definitions.map(([id, displayName, , isPassive]) => (
        <SkillCard key={`battle-${id}`} skill={{
          id, displayName, isPassive, targetMode: isPassive ? "self" : "singleEnemy",
          maximumTargets: isPassive ? 0 : 1, cooldownRemaining: 0, available: true,
          unavailableReason: null, resourceCost: null,
        }} selected={false} legal={!isPassive} disabled={false} onSelect={() => undefined} />
      ))}
      {definitions.map(([skillId, displayName, , isPassive]) => (
        <SkillReferenceCard key={`gallery-${skillId}`} skill={{ ...skill, skillId, displayName, isPassive }} content={{ introduction: `${displayName} introduction.` }} />
      ))}
      {statuses.map(([id, , kind]) => <StatusIcon key={id} status={{
        id, instanceId: `${id}.art`, kind, roundsRemaining: 2, stacks: 1,
        sourceCombatantId: "friendly.paladin.1",
      }} />)}
    </>);

    const paths = definitions.map(([, , filename]) => `/game-images/heroes/Paladin-Protection/skills/${filename}`);
    expect([...container.querySelectorAll<HTMLImageElement>(".skill-glyph-art")].map((image) => image.getAttribute("src"))).toEqual(paths);
    expect([...container.querySelectorAll<HTMLImageElement>(".skill-reference-summary-art img")].map((image) => image.getAttribute("src"))).toEqual(paths);
    expect(container.querySelectorAll<HTMLButtonElement>(".skill-card:not(.passive)")).toHaveLength(3);
    expect(container.querySelector<HTMLButtonElement>(".skill-card.passive")).toBeDisabled();
    expect([...container.querySelectorAll<HTMLImageElement>(".status-icon-art")].map((image) => image.getAttribute("src")))
      .toEqual([paths[0], paths[1], paths[3]]);
    for (const [id, skillId, kind] of statuses) {
      expect(statusRegistry[id].asset).toBe(skillPresentation[skillId].asset);
      expect(screen.getByLabelText(new RegExp(`${statusRegistry[id].name}.*Stack count: 1.*2 rounds remaining`)))
        .toHaveClass(kind === "debuff" ? "harmful" : "helpful");
    }
    expect(statusRegistry["status.scoff"].asset).toBeUndefined();
    const aura = screen.getByLabelText(/Holy Aura.*Stack count: 1.*2 rounds remaining/);
    fireEvent.error(aura.querySelector<HTMLImageElement>(".status-icon-art")!);
    expect(aura).toHaveTextContent(statusRegistry["status.holy_aura"].glyph);
  });

  it("shares Paladin Holy skill art with only its two persistent statuses", () => {
    const definitions = [
      ["skill.paladin.purify_healing", "Purify Healing", "Paladin_Holy_Purify_Healing_128x128.png"],
      ["skill.paladin.holy_blast", "Holy Blast", "Paladin_Holy_Holy_Blast_128x128.png"],
      ["skill.paladin.shield_of_protection", "Shield of Protection", "Paladin_Holy_Shield_of_Protection_128x128.png"],
    ] as const;
    const statuses = [
      ["status.purify_healing", definitions[0][0]],
      ["status.shield_of_protection", definitions[2][0]],
    ] as const;
    const { container } = render(<>
      {definitions.map(([id, displayName]) => <SkillCard key={`battle-${id}`} skill={{
        id, displayName, targetMode: id === "skill.paladin.holy_blast" ? "multipleEnemies" : "singleAlly",
        maximumTargets: id === "skill.paladin.holy_blast" ? 2 : 1, cooldownRemaining: 0,
        available: true, unavailableReason: null, resourceCost: null,
      }} selected={false} legal disabled={false} onSelect={() => undefined} />)}
      {definitions.map(([skillId, displayName]) => <SkillReferenceCard key={`gallery-${skillId}`}
        skill={{ ...skill, skillId, displayName }} content={{ introduction: `${displayName} introduction.` }} />)}
      {statuses.map(([id]) => <StatusIcon key={id} status={{
        id, instanceId: `${id}.art`, kind: "buff", roundsRemaining: 2,
        stacks: 1, sourceCombatantId: "friendly.paladin.1",
      }} />)}
    </>);

    const paths = definitions.map(([, , filename]) => `/game-images/heroes/Paladin-Holy/skills/${filename}`);
    expect([...container.querySelectorAll<HTMLImageElement>(".skill-glyph-art")].map((image) => image.getAttribute("src"))).toEqual(paths);
    expect([...container.querySelectorAll<HTMLImageElement>(".skill-reference-summary-art img")].map((image) => image.getAttribute("src"))).toEqual(paths);
    expect(container.querySelectorAll<HTMLButtonElement>(".skill-card")).toHaveLength(3);
    expect([...container.querySelectorAll<HTMLImageElement>(".status-icon-art")].map((image) => image.getAttribute("src")))
      .toEqual([paths[0], paths[2]]);
    for (const [id, skillId] of statuses) {
      expect(statusRegistry[id].asset).toBe(skillPresentation[skillId].asset);
      expect(screen.getByLabelText(new RegExp(`${statusRegistry[id].name}.*Stack count: 1.*2 rounds remaining`)))
        .toHaveClass("helpful");
    }
    expect(statusRegistry["status.holy_blast"]).toBeUndefined();
    const shield = screen.getByLabelText(/Shield of Protection.*Stack count: 1.*2 rounds remaining/);
    fireEvent.error(shield.querySelector<HTMLImageElement>(".status-icon-art")!);
    expect(shield).toHaveTextContent(statusRegistry["status.shield_of_protection"].glyph);
  });

  it("keeps Warrior Defence skill art distinct from shared statuses and uses Thunder Pot for Shield Defence", () => {
    const definitions = [
      ["skill.warrior.devastate", "Devastate", "Warrior_Defence_Devastate_128x128.png"],
      ["skill.warrior.shield_bash", "Shield Bash", "Warrior_Defence_Shield_Bash_128x128.png"],
      ["skill.warrior.thunder_pot", "Thunder Pot", "Warrior_Defence_Thunder_Pot_128x128.png"],
    ] as const;
    const shieldDefence: StatusState = {
      id: "status.shield_defence", instanceId: "status.shield_defence.art", kind: "buff",
      roundsRemaining: 2, stacks: null, sourceCombatantId: "friendly.warrior.1",
    };
    const { container } = render(<>
      {definitions.map(([id, displayName]) => <SkillCard key={`battle-${id}`} skill={{
        id, displayName, targetMode: id === "skill.warrior.thunder_pot" ? "multipleEnemies" : "singleEnemy",
        maximumTargets: id === "skill.warrior.thunder_pot" ? 2 : 1, cooldownRemaining: 0,
        available: true, unavailableReason: null, resourceCost: null,
      }} selected={false} legal disabled={false} onSelect={() => undefined} />)}
      {definitions.map(([skillId, displayName]) => <SkillReferenceCard key={`gallery-${skillId}`}
        skill={{ ...skill, skillId, displayName }} content={{ introduction: `${displayName} introduction.` }} />)}
      <StatusIcon status={shieldDefence} />
    </>);

    const paths = definitions.map(([, , filename]) => `/game-images/heroes/Warrior-Defence/skills/${filename}`);
    expect([...container.querySelectorAll<HTMLImageElement>(".skill-glyph-art")].map((image) => image.getAttribute("src"))).toEqual(paths);
    expect([...container.querySelectorAll<HTMLImageElement>(".skill-reference-summary-art img")].map((image) => image.getAttribute("src"))).toEqual(paths);
    expect(statusRegistry[shieldDefence.id].asset).toBe(paths[2]);
    expect(statusRegistry["status.armor_breaker"].asset).toBe("/game-images/heroes/Warrior-Weapon-Master/skills/Warrior_Armor_Break_128x128.png");
    expect(statusRegistry["status.stunned"].asset).toBeUndefined();
    expect(statusRegistry["status.scoff"].asset).toBeUndefined();
    const statusIcon = screen.getByLabelText(/Shield Defence.*2 rounds remaining/);
    expect(statusIcon).toHaveClass("helpful");
    const artwork = statusIcon.querySelector<HTMLImageElement>(".status-icon-art");
    expect(artwork).toHaveAttribute("src", paths[2]);
    fireEvent.error(artwork!);
    expect(statusIcon).toHaveTextContent(statusRegistry[shieldDefence.id].glyph);
  });

  it("shares Warrior Berserker active and passive art with only its matching statuses", () => {
    const definitions = [
      ["skill.warrior.moon_slash", "Moon Slash", "Warrior_Berserker_Moon_Slash_128x128.png", false],
      ["skill.warrior.warlust", "Warlust", "Warrior_Berserker_Warlust_128x128.png", false],
      ["skill.warrior.strike_of_meteorite", "Strike of Meteorite", "Warrior_Berserker_Strike_of_Meteorite_128x128.png", false],
      ["skill.warrior.blood_frenzy", "Blood Frenzy", "Warrior_Berserker_Blood_Frenzy_128x128.png", true],
    ] as const;
    const statuses = [
      ["status.bleeding_moon_slash", definitions[0][0], "debuff"],
      ["status.warlust", definitions[1][0], "buff"],
      ["status.blood_frenzy", definitions[3][0], "buff"],
    ] as const;
    const { container } = render(<>
      {definitions.map(([id, displayName, , isPassive]) => <SkillCard key={`battle-${id}`} skill={{
        id, displayName, isPassive, targetMode: isPassive || id === "skill.warrior.warlust" ? "self" : "singleEnemy",
        maximumTargets: isPassive || id === "skill.warrior.warlust" ? 0 : 1, cooldownRemaining: 0,
        available: true, unavailableReason: null, resourceCost: null,
      }} selected={false} legal={!isPassive} disabled={false} onSelect={() => undefined} />)}
      {definitions.map(([skillId, displayName, , isPassive]) => <SkillReferenceCard key={`gallery-${skillId}`}
        skill={{ ...skill, skillId, displayName, isPassive }} content={{ introduction: `${displayName} introduction.` }} />)}
      {statuses.map(([id, , kind]) => <StatusIcon key={id} status={{
        id, instanceId: `${id}.art`, kind, roundsRemaining: 2,
        stacks: null, sourceCombatantId: "friendly.warrior.1",
      }} />)}
    </>);

    const paths = definitions.map(([, , filename]) => `/game-images/heroes/Warrior-Berserker/skills/${filename}`);
    expect([...container.querySelectorAll<HTMLImageElement>(".skill-glyph-art")].map((image) => image.getAttribute("src"))).toEqual(paths);
    expect([...container.querySelectorAll<HTMLImageElement>(".skill-reference-summary-art img")].map((image) => image.getAttribute("src"))).toEqual(paths);
    expect(container.querySelectorAll<HTMLButtonElement>(".skill-card:not(.passive)")).toHaveLength(3);
    expect(container.querySelector<HTMLButtonElement>(".skill-card.passive")).toBeDisabled();
    expect([...container.querySelectorAll<HTMLImageElement>(".status-icon-art")].map((image) => image.getAttribute("src")))
      .toEqual([paths[0], paths[1], paths[3]]);
    for (const [id, skillId, kind] of statuses) {
      expect(statusRegistry[id].asset).toBe(skillPresentation[skillId].asset);
      expect(screen.getByLabelText(new RegExp(`${statusRegistry[id].name}.*2 rounds remaining`)))
        .toHaveClass(kind === "debuff" ? "harmful" : "helpful");
    }
    expect(statusRegistry["status.armor_breaker"].asset).toBe("/game-images/heroes/Warrior-Weapon-Master/skills/Warrior_Armor_Break_128x128.png");
    const frenzy = screen.getByLabelText(/Blood Frenzy.*2 rounds remaining/);
    fireEvent.error(frenzy.querySelector<HTMLImageElement>(".status-icon-art")!);
    expect(frenzy).toHaveTextContent(statusRegistry["status.blood_frenzy"].glyph);
  });

  it("shows Priest Discipline active art and Gallery-only Holy Concentration without inventing a command or status", () => {
    const definitions = [
      ["skill.priest.penance", "Penance", "Priest_Discipline_Penance_128x128.png"],
      ["skill.priest.holy_word_redemption", "Holy Word Redemption", "Priest_Discipline_Holy_Word_Redemption_128x128.png"],
      ["skill.priest.holy_word_punishment", "Holy Word Punishment", "Priest_Discipline_Holy_Word_Punishment_128x128.png"],
      ["skill.priest.holy_concentration", "Holy Concentration", "Priest_Discipline_Holy_Concentration_128x128.png"],
    ] as const;
    const statuses = [
      ["status.holy_word_redemption", definitions[1][0], "buff"],
      ["status.holy_word_punishment", definitions[2][0], "debuff"],
    ] as const;
    const { container } = render(<>
      {definitions.slice(0, 3).map(([id, displayName]) => <SkillCard key={`battle-${id}`} skill={{
        id, displayName, targetMode: id === "skill.priest.holy_word_redemption" ? "singleAlly" : "singleEnemy",
        maximumTargets: 1, cooldownRemaining: 0, available: true,
        unavailableReason: null, resourceCost: null,
      }} selected={false} legal disabled={false} onSelect={() => undefined} />)}
      {definitions.map(([skillId, displayName], index) => <SkillReferenceCard key={`gallery-${skillId}`}
        skill={{ ...skill, skillId, displayName, isPassive: index === 3 }} content={{ introduction: `${displayName} introduction.` }} />)}
      {statuses.map(([id, , kind]) => <StatusIcon key={id} status={{
        id, instanceId: `${id}.art`, kind, roundsRemaining: 2,
        stacks: 1, sourceCombatantId: "friendly.priest.1",
      }} />)}
    </>);

    const paths = definitions.map(([, , filename]) => `/game-images/heroes/Priest-Discipline/skills/${filename}`);
    expect([...container.querySelectorAll<HTMLImageElement>(".skill-glyph-art")].map((image) => image.getAttribute("src"))).toEqual(paths.slice(0, 3));
    expect([...container.querySelectorAll<HTMLImageElement>(".skill-reference-summary-art img")].map((image) => image.getAttribute("src"))).toEqual(paths);
    expect(container.querySelectorAll<HTMLButtonElement>(".skill-card")).toHaveLength(3);
    expect([...container.querySelectorAll<HTMLImageElement>(".status-icon-art")].map((image) => image.getAttribute("src")))
      .toEqual([paths[1], paths[2]]);
    for (const [id, skillId, kind] of statuses) {
      expect(statusRegistry[id].asset).toBe(skillPresentation[skillId].asset);
      expect(screen.getByLabelText(new RegExp(`${statusRegistry[id].name}.*Stack count: 1.*2 rounds remaining`)))
        .toHaveClass(kind === "debuff" ? "harmful" : "helpful");
    }
    expect(statusRegistry["status.penance"]).toBeUndefined();
    expect(statusRegistry["status.holy_concentration"]).toBeUndefined();
    const punishment = screen.getByLabelText(/Holy Word: Punishment.*2 rounds remaining/);
    fireEvent.error(punishment.querySelector<HTMLImageElement>(".status-icon-art")!);
    expect(punishment).toHaveTextContent(statusRegistry["status.holy_word_punishment"].glyph);
  });

  it("places Protection healing after damage for Heroic Charge and before target for Holy Aura", () => {
    const chargeRows = buildSkillReferenceRows({
      ...skill.reference,
      baseDamage: { state: "unavailable", reasonId: "targetDependentBaseline", note: "" },
      baseHealing: {
        state: "available",
        amountRange: { minimum: 28, maximum: 32 },
        basis: "baselinePower",
        note: "",
        conditions: [],
      },
    });
    expect(chargeRows.map((row) => row.id).slice(0, 3)).toEqual(["base-damage", "base-healing", "target"]);
    expect(chargeRows[1].value).toBe("28–32");

    const auraRows = buildSkillReferenceRows({
      ...skill.reference,
      target: { mode: "self" },
      skillType: "effect",
      baseDamage: { state: "notApplicable" },
      baseHealing: {
        state: "available",
        amountRange: { minimum: 6, maximum: 8 },
        basis: "baselinePower",
        note: "",
        conditions: [],
      },
    });
    expect(auraRows.map((row) => row.id).slice(0, 2)).toEqual(["base-healing", "target"]);
    expect(auraRows[0].value).toBe("6–8");
  });

  it("places audited Continuous Damage directly after Base Damage and omits it when inapplicable", async () => {
    const punishment: HeroSkillInventoryItem = {
      ...skill,
      skillId: "skill.priest.holy_word_punishment",
      displayName: "Holy Word Punishment",
      reference: {
        ...skill.reference,
        skillType: "damage",
        baseDamage: {
          state: "available",
          amountRange: { minimum: 7, maximum: 11 },
          basis: "baselinePower",
          note: "",
          conditions: [],
        },
        continuousDamage: {
          state: "available",
          amountRange: { minimum: 9, maximum: 16 },
          basis: "baselinePower",
          note: "",
          conditions: [],
        },
        baseHealing: { state: "notApplicable" },
      },
    };
    render(<SkillReferenceCard skill={punishment} content={{ introduction: "Punishes multiple enemies." }} />);
    await userEvent.setup().click(screen.getByText("Holy Word Punishment"));

    const labels = screen.getAllByRole("term").map((term) => term.textContent);
    expect(labels.slice(0, 2)).toEqual(["Base Damage", "Continuous Damage"]);
    expect(screen.getByText("7–11")).toBeVisible();
    expect(screen.getByText("9–16")).toBeVisible();
    expect(screen.queryByText(/per activation/i)).not.toBeInTheDocument();
    expect(screen.queryByText("New debuff")).not.toBeInTheDocument();
    expect(screen.queryByText("Recycled debuff")).not.toBeInTheDocument();

    expect(buildSkillReferenceRows(skill.reference).some((row) => row.id === "continuous-damage")).toBe(false);
  });

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
          baseDamage: {
            state: "unavailable",
            reasonId: "targetDependentBaseline",
            displayLabel: "Target-dependent",
            note: "",
            calculation: {
              title: "Damage Calculation",
              formula: "Direct damage per target = max(ceil((Caster Damage + Skill Variation − Target Arcane Resistance) × 2 ÷ 3), 0)\nSkill Variation = −3 to +3; one roll is shared by all selected targets.\nEach target is calculated separately before formation and target-side effects.",
            },
          },
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
    expect(screen.getByText("Target-dependent")).toBeVisible();
    await userEvent.setup().click(screen.getByRole("button", { name: /open damage calculation/i }));
    expect(screen.getByRole("dialog", { name: "Damage Calculation" })).toHaveTextContent("Direct damage per target = max(ceil((Caster Damage + Skill Variation − Target Arcane Resistance) × 2 ÷ 3), 0)");
    expect(screen.queryByText("Base Healing")).not.toBeInTheDocument();
  });

  it.each([
    ["Fireball", "skill.mage.fireball", "Target Fire Resistance", "Skill Variation = −5 to +5"],
    ["Frost Bolt", "skill.mage.frost_bolt", "Target Frost Resistance", "Skill Variation = −2 to +2"],
  ] as const)("renders audited target-dependent Mage calculation for %s", async (displayName, skillId, resistance, variation) => {
    render(<SkillReferenceCard
      skill={{
        ...skill,
        skillId,
        displayName,
        reference: {
          ...skill.reference,
          skillType: "damage",
          attackType: { state: "classified", value: "rangedProjectile" },
          damageNature: { state: "classified", value: "magical" },
          damageType: { state: "classified", value: displayName === "Fireball" ? "fire" : "frost" },
          baseDamage: {
            state: "unavailable",
            reasonId: "targetDependentBaseline",
            displayLabel: "Target-dependent",
            note: "",
            calculation: {
              title: "Damage Calculation",
              formula: displayName === "Fireball"
                ? `Direct damage = max(Caster Damage + Skill Variation − ${resistance}, 0)\n${variation}`
                : `Direct damage = max(ceil((Caster Damage + Skill Variation − ${resistance}) × 4 ÷ 5), 0)\n${variation}`,
            },
          },
          baseHealing: { state: "notApplicable" },
        },
      }}
      content={{ introduction: `${displayName} reference.` }}
    />);
    const user = userEvent.setup();
    await user.click(screen.getByText(displayName));
    expect(screen.getByText("Target-dependent")).toBeVisible();
    await user.click(screen.getByRole("button", { name: /open damage calculation/i }));
    expect(screen.getByRole("dialog", { name: "Damage Calculation" })).toHaveTextContent(resistance);
    expect(screen.getByRole("dialog", { name: "Damage Calculation" })).toHaveTextContent(variation);
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
