import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { StageSelectionScreen } from "@/components/stages/StageSelectionScreen";
import { SoundPreferenceProvider, useSoundPreference } from "@/components/audio/SoundPreferenceProvider";
import HeroGalleryPage from "@/app/manual/heroes/page";
import BattleInstructionPage from "@/app/manual/battle-instruction/page";
import { fetchHeroGalleryRoster } from "@/lib/battle/liveProvider";
import type { HeroGalleryDefinition } from "@/lib/battle/types";

const push = vi.fn();
const replace = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push, replace }),
  useSearchParams: () => new URLSearchParams(),
}));

const ids = [
  ["hero.warrior.weapon_master", "Ragnar", "Warrior", "Weapon Master"],
  ["hero.warrior.defence", "Wrathe", "Warrior", "Defence"],
  ["hero.warrior.berserker", "Berserker", "Warrior", "Berserker"],
  ["hero.mage.comprehensiveness", "Mage", "Mage", "Comprehensiveness"],
  ["hero.paladin.retribution", "Retribution", "Paladin", "Retribution"],
  ["hero.paladin.protection", "Protection", "Paladin", "Protection"],
  ["hero.paladin.holy", "Holy", "Paladin", "Holy"],
  ["hero.priest.comprehensiveness", "Priest", "Priest", "Comprehensiveness"],
  ["hero.priest.discipline", "Discipline", "Priest", "Discipline"],
  ["hero.rogue.comprehensiveness", "Rogue", "Rogue", "Comprehensiveness"],
] as const;

const skillIds: Record<string, string[]> = {
  "hero.warrior.weapon_master": ["skill.warrior.fatal_strike", "skill.warrior.armor_crush", "skill.warrior.antivenom_potion"],
  "hero.warrior.defence": ["skill.warrior.devastate", "skill.warrior.shield_bash", "skill.warrior.thunder_pot"],
  "hero.warrior.berserker": ["skill.warrior.moon_slash", "skill.warrior.warlust", "skill.warrior.strike_of_meteorite"],
  "hero.mage.comprehensiveness": ["skill.mage.fireball", "skill.mage.arcane_missiles", "skill.mage.frost_bolt"],
  "hero.paladin.retribution": ["skill.paladin.hammer_of_anger", "skill.paladin.crusader_strike", "skill.paladin.flash_of_light"],
  "hero.paladin.protection": ["skill.paladin.hammer_of_revenge", "skill.paladin.shield_of_righteous", "skill.paladin.heroric_charge", "skill.paladin.holy_aura"],
  "hero.paladin.holy": ["skill.paladin.purify_healing", "skill.paladin.holy_blast", "skill.paladin.shield_of_protection"],
  "hero.priest.comprehensiveness": ["skill.priest.holy_smite", "skill.priest.shadow_word_pain", "skill.priest.binding_heal"],
  "hero.priest.discipline": ["skill.priest.penance", "skill.priest.holy_word_redemption", "skill.priest.holy_word_punishment"],
  "hero.rogue.comprehensiveness": ["skill.rogue.sharp_blade", "skill.rogue.poisoned_dagger", "skill.rogue.shadow_evasion"],
};

const unavailableReference = {
  target: { mode: "singleEnemy" as const },
  skillType: "damage" as const,
  attackType: { state: "classified" as const, value: "melee" as const },
  damageNature: { state: "classified" as const, value: "physical" as const },
  damageType: { state: "unclassified" as const, reasonId: "definitionMissing" as const },
  baseDamage: { state: "unavailable" as const, reasonId: "notAudited" as const, note: "Reference power has not yet been audited." },
  baseHealing: { state: "notApplicable" as const },
};

const gallery: HeroGalleryDefinition[] = ids.map(([definitionId, displayName, faculty, specialization], index) => ({
  definitionId,
  displayName,
  faculty,
  specialization,
  startingStatRanges: ["HP", "Damage", "Defence", "Agility"].map((label, rangeIndex) => ({ id: label.toLowerCase(), label, minimum: 10 + rangeIndex, maximum: 20 + rangeIndex })),
  startingResistanceRanges: ["Fire", "Frost", "Arcane", "Shadow", "Death", "Poison", "Nature"].map((label) => ({ id: label.toLowerCase(), label, minimum: 1, maximum: 5 })),
  skills: skillIds[definitionId].map((skillId) => ({
    skillId,
    displayName: skillId === "skill.paladin.holy_aura" ? "Holy Aura" : skillId.split(".").at(-1)?.replaceAll("_", " ") ?? skillId,
    isPassive: skillId === "skill.paladin.holy_aura",
    reference: skillId === "skill.paladin.holy_aura"
      ? {
        target: { mode: "multipleAllies" as const, maximumTargets: 3 },
        skillType: "healing" as const,
        attackType: { state: "notApplicable" as const },
        damageNature: { state: "notApplicable" as const },
        damageType: { state: "notApplicable" as const },
        baseDamage: { state: "notApplicable" as const },
        baseHealing: { state: "unavailable" as const, reasonId: "notAudited" as const, note: "Reference power has not yet been audited." },
      }
      : unavailableReference,
  })),
  unlockSource: index < 4 ? { kind: "starter" } : index === 5 ? { kind: "stageReward", stageId: "paladins-altar", stageDisplayName: "Paladin's Altar", battleIndex: 3 } : null,
}));

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function progression() {
  return { contractVersion: "1.0", profileId: "profile.1", unlockedHeroDefinitionIds: ids.slice(0, 4).map(([id]) => id), stageProgress: [
    { stageId: "paladins-altar", highestCompletedBattle: 0, unlockedBattle: 1, completed: false },
    { stageId: "warriors-barrack", highestCompletedBattle: 0, unlockedBattle: 1, completed: false },
  ], grantedRewards: [] };
}

function renderManual() {
  return render(<SoundPreferenceProvider><StageSelectionScreen /></SoundPreferenceProvider>);
}

afterEach(() => {
  vi.restoreAllMocks();
  push.mockReset();
  replace.mockReset();
});

describe("UI-027 Manual and Gallery", () => {
  it("opens exactly three ordered Manual options and routes its first two actions", async () => {
    renderManual();
    const trigger = screen.getByRole("button", { name: "Open Game Manual" });
    await userEvent.setup().click(trigger);
    const dialog = screen.getByRole("dialog", { name: "Game Manual" });
    expect(dialog).toBeVisible();
    expect(within(dialog).getAllByRole("button").map((button) => button.textContent?.replace(/\s+/g, " ").trim())).toEqual([
      "×", "♜Hero GalleryBrowse every approved specialization", "⚔Battle InstructionLearn the battlefield fundamentals", "♫Sound OnUI and battle effects enabled",
    ]);
    await userEvent.setup().click(within(dialog).getByRole("button", { name: /Hero Gallery/i }));
    expect(push).toHaveBeenCalledWith("/manual/heroes");
  });

  it("restores focus after Escape and traps Tab at the dialog edges", async () => {
    renderManual();
    const user = userEvent.setup();
    const trigger = screen.getByRole("button", { name: "Open Game Manual" });
    await user.click(trigger);
    const dialog = screen.getByRole("dialog");
    await waitFor(() => expect(document.activeElement).toBe(within(dialog).getByRole("button", { name: /Hero Gallery/i })));
    const close = within(dialog).getByRole("button", { name: "Close Game Manual" });
    close.focus();
    fireEvent.keyDown(dialog, { key: "Tab" });
    expect(document.activeElement).toBe(within(dialog).getByRole("button", { name: /Hero Gallery/i }));
    fireEvent.keyDown(window, { key: "Escape" });
    await waitFor(() => expect(document.activeElement).toBe(trigger));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("renders all ten catalogue definitions, filters by faculty, and shows ownership/profile facts", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => String(input).endsWith("/heroes")
      ? json({ contractVersion: "1.0", heroes: gallery })
      : json(progression()));
    render(<HeroGalleryPage />);
    const cards = await screen.findByRole("region", { name: "Approved heroes" });
    expect(within(cards).getAllByRole("button")).toHaveLength(10);
    expect(screen.getByText("Starting values are randomized within these configured ranges, not fixed battle results.")).toBeVisible();
    expect(screen.getByText("Owned in the active save slot.")).toBeVisible();
    await userEvent.setup().click(screen.getByRole("button", { name: "Paladin" }));
    expect(within(screen.getByRole("region", { name: "Approved heroes" })).getAllByRole("button")).toHaveLength(3);
    await userEvent.setup().click(screen.getByRole("button", { name: /Protection/ }));
    await userEvent.setup().click(screen.getByRole("tab", { name: /Passive/ }));
    expect(screen.getByText("Holy Aura")).toBeVisible();
    expect(screen.getByText(/Reward from Paladin's Altar, Battle 3/)).toBeVisible();
    await userEvent.setup().click(screen.getByRole("button", { name: "Priest" }));
    await userEvent.setup().click(screen.getByRole("button", { name: /Discipline/ }));
    expect(screen.getByText("Locked · No current unlock route.")).toBeVisible();
  });

  it("shows a recoverable Gallery error and keeps the Instruction route readable", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("offline"));
    render(<HeroGalleryPage />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Hero Gallery data is unavailable");
    render(<BattleInstructionPage />);
    expect(screen.getByRole("heading", { name: "Battle Instruction" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "Victory and Formations" })).toBeVisible();
    expect(screen.getByText(/Tips are suggestions, not extra combat rules/)).toBeVisible();
    expect(screen.getByRole("link", { name: /Back to Game Manual/ })).toHaveAttribute("href", "/stages?manual=open");
  });

  it("rejects API/editorial hero or skill ID drift before the Gallery can render", async () => {
    const unknownHero = gallery.map((hero, index) => index === 0
      ? { ...hero, definitionId: "hero.unknown" }
      : hero);
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(json({ contractVersion: "1.0", heroes: unknownHero }));
    await expect(fetchHeroGalleryRoster()).rejects.toMatchObject({ kind: "adapter" });

    const unknownSkill = gallery.map((hero, index) => index === 0
      ? { ...hero, skills: hero.skills.map((skill, skillIndex) => skillIndex === 0
        ? { ...skill, skillId: "skill.warrior.unknown" }
        : skill) }
      : hero);
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(json({ contractVersion: "1.0", heroes: unknownSkill }));
    await expect(fetchHeroGalleryRoster()).rejects.toMatchObject({ kind: "adapter" });

    const duplicateKnownHero = gallery.map(() => gallery[0]);
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(json({ contractVersion: "1.0", heroes: duplicateKnownHero }));
    await expect(fetchHeroGalleryRoster()).rejects.toMatchObject({ kind: "adapter" });
  });
});

describe("UI-027 sound preference", () => {
  function Probe() {
    const preference = useSoundPreference();
    return <button type="button" onClick={preference.toggle}>{preference.enabled ? "Sound On" : "Sound Off"}</button>;
  }

  it("defaults on, persists toggles, and applies the central manager gate", async () => {
    const storage = { getItem: vi.fn(() => null), setItem: vi.fn() };
    Object.defineProperty(window, "localStorage", { configurable: true, value: storage });
    const manager = { setEnabled: vi.fn(), isEnabled: vi.fn(() => true) };
    render(<SoundPreferenceProvider manager={manager}><Probe /></SoundPreferenceProvider>);
    const toggle = screen.getByRole("button", { name: "Sound On" });
    await waitFor(() => expect(manager.setEnabled).toHaveBeenCalledWith(true));
    await userEvent.setup().click(toggle);
    expect(screen.getByRole("button", { name: "Sound Off" })).toBeVisible();
    expect(manager.setEnabled).toHaveBeenLastCalledWith(false);
    expect(storage.setItem).toHaveBeenCalledWith("legends-of-champions-tactics.sound-enabled", "false");
  });

  it("restores a persisted mute after mount and permits only future re-enabled cues", async () => {
    const storage = { getItem: vi.fn(() => "false"), setItem: vi.fn() };
    Object.defineProperty(window, "localStorage", { configurable: true, value: storage });
    const manager = { setEnabled: vi.fn(), isEnabled: vi.fn(() => false) };
    render(<SoundPreferenceProvider manager={manager}><Probe /></SoundPreferenceProvider>);
    await waitFor(() => expect(screen.getByRole("button", { name: "Sound Off" })).toBeVisible());
    expect(manager.setEnabled).toHaveBeenLastCalledWith(false);
    await userEvent.setup().click(screen.getByRole("button", { name: "Sound Off" }));
    expect(manager.setEnabled).toHaveBeenLastCalledWith(true);
    expect(storage.setItem).toHaveBeenCalledWith("legends-of-champions-tactics.sound-enabled", "true");
  });

  it("survives unavailable local storage without blocking rendering", async () => {
    const getItem = vi.fn(() => { throw new Error("blocked"); });
    Object.defineProperty(window, "localStorage", { configurable: true, value: { getItem, setItem: vi.fn() } });
    const manager = { setEnabled: vi.fn(), isEnabled: vi.fn(() => true) };
    render(<SoundPreferenceProvider manager={manager}><Probe /></SoundPreferenceProvider>);
    expect(screen.getByRole("button", { name: "Sound On" })).toBeVisible();
    await waitFor(() => expect(getItem).toHaveBeenCalled());
  });
});
