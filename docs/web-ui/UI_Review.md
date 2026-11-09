# UI Review

## Purpose

Track UI observations, requested corrections, review evidence, and
implementation status.

## Review Entry Template

### Date

YYYY-MM-DD

### Screen or Feature

_Name and route._

### Evidence

_Link or filename in `screenshots/` or `screenshots_debug/`._

### Findings

- Finding 1

### Requested Changes

- Change 1

### Acceptance Criteria

- Criterion 1

### Status

Proposed / Approved / In Progress / Completed / Verified

## Reviews

### UI-REVIEW-001 — Battle Screen Layout and Data Binding

#### Date

2026-07-27

#### Screen or Feature

Web UI battle screen.

#### Evidence

- `docs/web-ui/screenshots_debug/battle_27_07_2026-01.png`
- Owner notes: `docs/web-ui/screenshots_debug/UI_Review_Human.md`

#### Findings

1. **Battle Log data source**
   - The displayed Battle Log must be populated from actual game-engine battle
     events rather than placeholder, duplicated, or independently reconstructed
     UI text.
   - The UI should consume the established battle/event data contract and
     preserve event order.
2. **Skill-card vertical stretching bug**
   - Skill cards/buttons increase in height as the Battle Log gains entries.
   - The lower skill area appears to share or inherit vertical sizing from the
     Battle Log container.
   - Skill cards and the Battle Log must use independent sizing and overflow
     behaviour.
3. **Battlefield hero information bar**
   - The information bar above each battlefield hero currently does not provide
     enough live combat information.
   - It should show the hero's current and maximum HP through a clear HP bar.
   - Active status icons should appear directly below the HP bar.
4. **Bottom-panel layout**
   - The bottom section gives too much width and height to skill cards and too
     little usable space to the Battle Log.
   - The Battle Log needs to be wider and easier to scan.
   - Skill cards should be smaller while remaining visually attractive,
     readable, and easy to click.
   - The acting-hero panel, skill-card area, and Battle Log should form a stable
     layout that does not shift as log content grows.
5. **Unknown status tooltip**
   - Hovering over a status icon displays `unknown status`.
   - Status identifiers, metadata, or tooltip mapping are not reaching the UI
     correctly.
   - The tooltip must resolve the actual status name and useful description
     from authoritative status data.

#### Requested Changes

- Bind the Battle Log to actual engine-generated battle events through the
  existing adapter/data-contract boundary.
- Keep Battle Log entries ordered and append new entries without rebuilding
  unrelated UI state.
- Make the Battle Log internally scrollable once its content exceeds the
  available height.
- Prevent the Battle Log's content height from affecting the height of skill
  cards, the acting-hero panel, or the overall bottom layout.
- Give skill cards a deliberate fixed or bounded height and a compact
  responsive width.
- Redesign the bottom panel to allocate more horizontal space to the Battle Log
  and less to skill cards.
- Add current/max HP presentation above each battlefield hero, using an HP bar
  and readable numeric values where space permits.
- Render active status icons below the battlefield HP bar.
- Resolve status tooltips from the authoritative status identifier/definition
  rather than a fallback `unknown status` label.
- Preserve existing authorised-skill, targeting, turn, and battle-control
  behaviour.
- Maintain keyboard focus visibility, pointer usability, tooltip
  accessibility, and responsive behaviour.

#### Acceptance Criteria

- Battle Log text is derived from real battle-engine event output; no separate
  placeholder log path remains active.
- Events appear in chronological order and new events become visible without
  disturbing the skill-card layout.
- The Battle Log scrolls inside its own container when necessary.
- Adding many Battle Log entries does not increase or distort skill-card
  height.
- Skill cards remain visually consistent, readable, clickable, and smaller
  than in the referenced screenshot.
- The Battle Log receives visibly more usable width than in the referenced
  screenshot.
- Each battlefield hero displays an HP bar representing current HP against
  maximum HP.
- Active status icons display below the corresponding battlefield HP bar.
- Hovering or focusing a known status icon shows its correct name and
  description; `unknown status` appears only for genuinely unmapped data and is
  reported as a data issue.
- Existing battle actions, skill selection, targeting, speed controls,
  auto-battle controls, and turn progression continue to work.
- Relevant automated tests cover log rendering/overflow, stable skill-card
  sizing, HP/status rendering, and status-tooltip mapping.
- The page passes the project's normal frontend validation, type-check, lint,
  and build commands.

#### Status

Verified by the five-agent `QA-001` quality audit on 2026-07-28.

#### UI-001 Implementation Evidence

- The live provider retains the ordered session-opening events returned by the
  adapter.
- The presentation queue appends authoritative `BattleEvent.message` values in
  sequence and preserves unplayed events when animation playback is skipped.
- The Battle Log has bounded internal scrolling, while skill cards use
  independent compact sizing.
- Battlefield HP bars show current/max values, with active status icons
  directly below.
- The frontend status registry covers every status identifier currently emitted
  by the live adapter.
- Battlefield status icons can receive pointer and keyboard focus without being
  blocked by a disabled hero control.
- Frontend tests, type-check, lint, production build, Python adapter/API tests,
  and live browser review passed during UI-001.

#### QA-001 Audit Notes

- All five configured roles participated: project manager, UI developer,
  game-engine developer, test automator, and independent reviewer.
- The Battle Log now follows newly appended authoritative events, including
  events revealed by skipping presentation playback.
- Equal-revision accepted-command responses no longer replay already-presented
  events. Adapter status application/removal events use deterministic status-ID
  ordering.
- The frontend registry and adapter currently agree on all eight emitted status
  identifiers, with automated cross-boundary coverage.
- Battlefield statuses are structurally separate from native target buttons.
  Pointer targeting and explicit Enter/Space targeting are covered by tests;
  Enter targeting was also confirmed in a live browser.
- Live browser validation at 1280×720 produced 13 ordered log entries, an
  internally scrolling 120-pixel-high log list (`scrollHeight` 175,
  `scrollTop` 55), compact 94-pixel skill cards, and no document overflow.
  Focus displayed the mapped Antivenom Potion name, description, and duration.
- Frontend validation passed with 51 tests, TypeScript type checking, ESLint,
  and a production build. Python adapter/API validation passed with 31 tests
  and one non-failing Starlette test-client deprecation warning.
- The independent reviewer found no blocking correctness or scope issues.
  A non-blocking accessibility tradeoff remains: the explicit target-button
  workaround activates Space on keydown rather than the native keyup timing.

### UI-REVIEW-002 — Team Builder and Live Multi-Team Battles

#### Date

2026-07-29

#### Source and Authority

- Approved requirements: `docs/web-ui/UI_Review_002.md`
- Owner input: `docs/web-ui/screenshots_debug/UI_Review_Human.md` (read only)

#### Scope

Team Builder, eight approved heroes, configurable live 1v1/2v2/3v3, random or
specified enemies, player or computer enemy control, and finished-battle
return/reset.

#### Status

Implemented and independently reviewed on 2026-07-29. Detailed requirements,
acceptance criteria, and evidence are recorded in `UI_Review_002.md`.

### UI-034 — 2026-10-30 Owner Review

The authoritative implementation task is `docs/Codex/Current_Task.md` (UI-034).
Owner source is the read-only 2026-10-30 section, items 1–8, of
`docs/web-ui/screenshots_debug/UI_Review_Human.md`, with screenshots
`UI_30_10_2026-01.png` through `UI_30_10_2026-03.png` in the same folder.

The review requires locked Tactics alignment; target-selection counts in the
ACTING HERO card instead of an overlapped battlefield popup; removal of that
card's profession line and targetless effect popup; readable side-card
specializations; a relocated, functional Game Manual gear without disrupting
the active battle; Paladin Holy Gallery copy updates; and truthful Base Damage
references for all three Mage Comprehensiveness skills. Preserve existing
combat authority and validate each numbered item against the owner evidence.

**Status:** Implemented and independently reviewed on 2026-10-30. Focused
validation and the separate older full-suite failures are recorded in
`docs/Codex/Completed.md` and `docs/Codex/Current_Task.md`.

### UI-035 — 2026-10-31 Owner Review

The authoritative implementation task is `docs/Codex/Current_Task.md`
(UI-035). Owner source is the read-only 2026-10-31 section, items 1–4, of
`docs/web-ui/screenshots_debug/UI_Review_Human.md` (no screenshot).

The review requires the battle-origin Game Manual to return through Hero
Gallery or Battle Instruction without losing the active battle; removal of
three specified supplemental Mage damage-equation sentences; fixed side-card
status-icon/Stats-button placement during target highlighting; and no Acting
Hero self-preview overlay for Heroic Charge or Shield of Righteous. Preserve
the underlying engine facts, target-bound previews, and Stage Map-origin
Manual behaviour. Validate the complete nested navigation path, not merely
direct Manual open/close.

**Status:** Implemented and independently reviewed on 2026-10-31. The full
nested battle-origin Manual path, Stage Map route behavior, Mage copy,
highlight placement, and Paladin preview presentation were validated;
evidence and manual limits are recorded in `docs/Codex/Completed.md`.

### UI-036 — Battle-Embedded Manual Content Frame

The owner's 2026-10-31 follow-up screenshot shows a redundant outer Game
Manual title/header and frame around the embedded Hero Gallery. The owner
reports the same issue for Battle Instruction, only when opened from the
battle's Manual icon. `docs/Codex/Current_Task.md` defines the focused fix:
remove that competing chrome in both embedded views while preserving a direct
close control, Back to Manual, the mounted battle, and Stage Map-origin
appearance/navigation.

**Status:** Complete. Both embedded views omit the redundant menu shell. The
owner's follow-up removes the embedded ×, leaving Back and direct Escape;
the initial menu still has its ×. Focused tests and live desktop/compact
browser checks passed; Stage Map still navigates to the standalone pages.

### UI-037 — Enemy Formation Cards in Team Builder

The owner's 2026-11-01 screenshot shows a wide predefined-enemy formation note
beside the existing compact Your Formation cards. Replace that note with
enemy-themed, size-valid formation cards under **ENEMY FORMATION**. Highlight
the known fixed computer formation in red; when the computer's formation is
unknown before battle, highlight none. Preserve editable player-controlled
enemy formation choices and existing battle configuration. The authoritative
implementation and validation criteria are in `docs/Codex/Current_Task.md`.

**Status:** Completed on 2026-11-01. Read-only 2v2/3v3 enemy cards use a
known structured-stage formation for a single red highlight; Arena Run and
unknown free-form computer formations show no highlight. Editable Player enemy radios
and 1v1 behavior were preserved. Focused tests, typecheck, and desktop/compact
browser comparison passed; evidence is in `docs/Codex/Completed.md`.
The owner follow-up keeps Arena Run enemy cards unselected and removes the
visible “PREDEFINED · NOT EDITABLE” label beneath fixed enemy formation cards.

### UI-039 — Rogue Skill Icons in Hero Gallery

The owner approved UI-038's three Rogue battle-card skill icons and requests
the same artwork in the Hero Gallery Skill Introduction cards. The compact
accordion summary row should show each icon beside its skill name, in both
collapsed and expanded states. Preserve non-Rogue cards, editorial text,
reference facts, and accordion interaction. See `docs/Codex/Current_Task.md`.

**Status:** Completed on 2026-11-01. Core recorded the focused Gallery visual
check and completion details in `docs/Codex/Completed.md`.

### UI-040 — Rogue Status Artwork in Battle and Hero Stats

The owner's 2026-11-01 battle and Hero Stats screenshots show the old Poisoned
Dagger status glyph despite approved Rogue skill artwork in battle cards and
Hero Gallery. Use the corresponding artwork for Sharp Blade Bleeding, Poisoned
Dagger, and Shadow Evasion status IDs through the shared status icon renderer;
preserve status semantics, tooltip, stacks, and durations. See
`docs/Codex/Current_Task.md` for acceptance and validation.

**Status:** Completed on 2026-11-01. Core recorded the focused shared-component
and browser checks in `docs/Codex/Completed.md`.

### UI-041 — Priest Comprehensiveness Skill Artwork

The owner supplied 128×128 icons for Holy Smite, Shadow Word Pain, and Binding
Heal. Integrate each into Battle skill cards and Hero Gallery skill summaries;
map only the lasting `status.shadow_word_pain` to the matching art in Team
Information and Hero Stats. The complete requirements are in
`docs/Codex/Current_Task.md`.

**Status:** Completed on 2026-11-01. Core recorded the focused integrated and
browser checks in `docs/Codex/Completed.md`.

### UI-042 — Mage Comprehensiveness Skill Artwork

The owner supplied 128×128 icons for Fireball, Arcane Missiles, and Frost Bolt.
Integrate each into Battle skill cards and Hero Gallery skill summaries.
Frost Bolt applies the shared `status.cold`; map its status icon only after
confirming the artwork is suitable for the shared effect and its tiny display
size. Fireball and Arcane Missiles have no lasting status to map. See
`docs/Codex/Current_Task.md` for the exact scope and checks.

**Status:** Completed on 2026-11-02. Core recorded the focused integrated and
browser checks in `docs/Codex/Completed.md`.

### UI-043 — Warrior Weapon Master Skill and Status Artwork

The owner supplied three skill images (Fatal Strike, Armor Crush, Antivenom
Potion) and three dedicated Armor Crush debuff images (Armor Break, Wound,
Bleeding). Armor Crush uses its own image only as a skill; the three dedicated
debuff images are status-only. Fatal Strike's debuff and Antivenom Potion's
buff reuse their matching skill images. See `docs/Codex/Current_Task.md` for
the exact stable-ID mapping, acceptance, and validation.

**Status:** Completed on 2026-11-02. Core recorded the focused integrated and
browser checks in `docs/Codex/Completed.md`.

### UI-044 — Paladin Retribution Skill and Passive Artwork

The owner supplied three active skill images for Hammer of Anger, Crusader
Strike, and Flash of Light, plus a Wrath of Crusader passive image. The passive
image also represents the active `status.wrath_of_crusader` buff produced by
Crusader Strike; it must not turn the passive into a selectable fourth skill.
See `docs/Codex/Current_Task.md` for the exact mapping and validation.

**Status:** Completed on 2026-11-02. Core recorded focused integrated and
browser checks in `docs/Codex/Completed.md`.

### UI-045 — Paladin Protection Skill and Passive Artwork

The owner supplied three active skill images (Hammer of Revenge, Shield of
Righteous, Heroic Charge) and one Holy Aura passive image. Integrate them in
Battle and Gallery, with matching art for the applicable Hammer debuff, Shield
buff, and Holy Aura recipient buff. Keep Holy Aura non-commandable. Heroic
Charge's Scoff status is shared with other hero skills and retains its generic
status icon until a source-specific visual rule is approved. See
`docs/Codex/Current_Task.md` for exact IDs and validation.

**Status:** Completed on 2026-11-02. Core recorded the focused integrated and
browser checks in `docs/Codex/Completed.md`.

### UI-046 — Paladin Holy Skill and Status Artwork

The owner supplied three active skill images: Purify Healing, Holy Blast, and
Shield of Protection. Integrate all three in Battle skill cards and the Hero
Gallery. Reuse the corresponding skill art for the lasting Purify Healing and
Shield of Protection buffs in Battle Team Information and Hero Stats. Holy
Blast has no lasting status to map. See `docs/Codex/Current_Task.md` for exact
IDs, scope, and validation.

**Status:** Completed on 2026-11-03. Core recorded focused integration and
limited browser checks in `docs/Codex/Completed.md`.

### UI-047 — Warrior Defence Skill and Status Artwork

The owner supplied three active skill images: Devastate, Shield Bash, and
Thunder Pot. Show all three in Battle skill cards and Hero Gallery skill
summaries. Thunder Pot's Shield Defence buff can reuse its image if legible at
status size. Preserve the existing dedicated Armor Breaker image and generic
Stunned/Scoff icons because those statuses are shared across skills. See
`docs/Codex/Current_Task.md` for exact IDs, scope, and validation.

**Status:** Completed on 2026-11-03. Core recorded the focused integration and
limited browser checks in `docs/Codex/Completed.md`.

### UI-048 — Warrior Berserker Skill, Passive, and Status Artwork

The owner supplied three active skill images (Moon Slash, Warlust, Strike of
Meteorite) and a Blood Frenzy passive image. Integrate them in Battle and
Gallery, then reuse the matching art for Moon Slash Bleeding, Warlust, and
Blood Frenzy status icons. Keep Blood Frenzy non-commandable. Strike of
Meteorite's Armor Breaker status retains its existing dedicated Armor Break
image. See `docs/Codex/Current_Task.md` for exact IDs and validation.

**Status:** Completed on 2026-11-03. Core recorded focused integration and
browser checks in `docs/Codex/Completed.md`.

### UI-049 — Priest Discipline Skill, Passive, and Status Artwork

The owner supplied three active skill images (Penance, Holy Word Redemption,
Holy Word Punishment) and a Holy Concentration passive image. Show the active
images in Battle and Gallery, and the passive in the Gallery. Reuse the
matching Redemption and Punishment images for their persistent status icons.
Holy Concentration is Gallery-only reference metadata, not a fourth Battle
command or a persistent status. See `docs/Codex/Current_Task.md` for exact
IDs, scope, and validation.

**Status:** Completed on 2026-11-03. Core recorded focused integration and
browser checks in `docs/Codex/Completed.md`.

### UI-050 — Battle Instruction Visual Manual

Redesign the existing Battle Instruction **content** as six concise, visual,
fact-checked chapters with responsive internal navigation, diagrams, a
current Battle Interface illustration, and editable validated prose. Preserve
the existing standalone and battle-embedded Manual entry/exit flow and the
working Back to Manual action; in particular, embedded reading must not
unmount or lose the active battle. See `docs/Codex/Current_Task.md` for the
approved content, exact boundaries, role assignments, and validation.

**Status:** Completed on 2026-11-06. Core recorded the content, navigation,
validation, and browser checks in `docs/Codex/Completed.md`.

### UI-051 — Portraits and Name Popups in Battle Turn Order

Replace the initial-letter image in each Battle action-sequence card with its
hero's existing `portraits_sidebar` avatar. Hovering a card shows a small
popup beneath it containing only that combatant's runtime name. Preserve the
sequence number, current-actor gold highlight, acted state, layout, and all
battle behaviour. See `docs/Codex/Current_Task.md` for scope and validation.

**Status:** Completed on 2026-11-06. Core recorded the focused tests and
browser checks in `docs/Codex/Completed.md`.

### UI-052 — Warrior and Paladin Profession Icons in Battle Cards

The owner supplied six 128×128 PNGs in `game-images/professions/icons`: one
for each approved Warrior and Paladin specialization. Replace the top-right
profession badge's empty/letter artwork in friendly and enemy Battle hero
cards using the exact hero definition ID. Preserve all existing card styling,
placement, behaviour, and safe fallback for heroes without supplied art. See
`docs/Codex/Current_Task.md` for exact paths and validation.

**Status:** Completed on 2026-11-06. Core recorded focused tests and browser
checks in `docs/Codex/Completed.md`.

### UI-053 — Complete Profession Icons in Battle and Hero Gallery Intro

The owner supplied four more 128×128 profession icons for Mage
Comprehensiveness, Rogue Comprehensiveness, Priest Comprehensiveness, and Priest
Discipline. Add those to the Battle hero-card badges, preserving the six
Warrior/Paladin mappings from UI-052. Also display each of the ten approved
heroes' matching profession icons in a restrained, responsive position beside
the Hero Gallery intro heading. See `docs/Codex/Current_Task.md` for exact
paths, scope, and validation.

**Status:** Completed on 2026-11-06. Core recorded focused tests and browser
checks in `docs/Codex/Completed.md`.

### UI-054 — Vertical Profession Icon Placement in Hero Gallery Intro

Move the existing Gallery profession icon from the far-right badge to a
borderless, left-aligned 96×96px desktop area above the faculty heading.
Keep faculty, specialization, and introduction in one vertical column with
full-width heading lines and natural wrapping for long names. Preserve the
hero figure, dark-fantasy typography, downstream content, and Battle badge.
See `docs/Codex/Current_Task.md` for exact spacing and validation.

**Status:** Completed on 2026-11-06. Core recorded focused checks and browser
inspection in `docs/Codex/Completed.md`.

### UI-055 — Compact Profession Icon and Faculty Row

Place the Hero Gallery profession icon immediately left of the faculty heading
in a compact first row. Put the specialization on a full-width second line
aligned to the information column's left edge, followed by the introduction.
Use a 64–72px desktop icon area and 12–16px row gap; preserve transparent,
borderless artwork and responsive wrapping. Only the UI engineer is assigned;
no separate test or review agent. See `docs/Codex/Current_Task.md`.

**Status:** Completed on 2026-11-06. Core recorded focused visual and
integration checks in `docs/Codex/Completed.md`.

### UI-056 — Corner-Only Battle Profession Frames

Replace the continuous gold square around the profession icon in each Battle
hero card with four short gold L-shaped corner accents and open sides. Keep
icon art, footprint, placement, fallback, and all other Battle/Gallery
presentation unchanged. See `docs/Codex/Current_Task.md` for the exact scope
and focused validation.

**Status:** Completed on 2026-11-06. Core recorded focused visual checks in
`docs/Codex/Completed.md`.

### UI-057 — Status Tooltip Remaining-Rounds Wording

Change the shared Battle status-icon tooltip and accessible label from
`N rounds remaining.` to `Remaining rounds: N.`. Keep the same number, stack
information, null/updating behaviour, icon, and presentation. This also
updates the shared Hero Stats status tooltip. See `docs/Codex/Current_Task.md`
for focused scope and validation.

**Status:** Completed on 2026-11-07. Core recorded focused results in
`docs/Codex/Completed.md`.

### UI-058 — Replace Battle Instruction Interface Image and Markers

Use the owner's new full 1913×954 battle screenshot in Battle Instruction
chapter 04. Remove the current 16:9 `cover` crop, keep the full image
proportional, and visually realign all nine clickable bubbles to the correct
regions at desktop, tablet, and narrow widths. Preserve chapter/Manual
navigation and marker accessibility. See `docs/Codex/Current_Task.md`.

**Status:** Completed on 2026-11-07. Core recorded focused results in
`docs/Codex/Completed.md`.

### UI-059 — Battle Formats Shapes for Chapter 03's 2v2 Diagrams

Replace only Chapter 03's two 2v2 oval hero-position markers with the existing
blue/red hero-slot silhouette from Chapter 02 Battle Formats. Keep the Front &
Rear and Side by Side positions, labels, sides, and slot numbering clear. Leave
Chapter 02 and Chapter 03's 3v3 diagrams unchanged. See
`docs/Codex/Current_Task.md`.

**Status:** Completed on 2026-11-08, with the owner-observed placement corrections
tracked in UI-060 below. See `docs/Codex/Completed.md` for UI-059's original scope.

### UI-060 — Correct 2v2 and Extend Formation Shapes to 3v3

In Battle Instruction chapter 03, correct 2v2 Front & Rear so Front 1 is
nearest the opposing team on both sides, and arrange Side by Side vertically.
Check both against real Battle positions. Once correct, extend the same
blue/red hero-slot shape to all three 3v3 formations, matching each side's
actual slot, Front/Rear, and vertical order. Preserve Chapter 02, combat logic,
and Manual navigation. See `docs/Codex/Current_Task.md`.

**Status:** Completed on 2026-11-08. Core recorded results in
`docs/Codex/Completed.md`.

### UI-061 — Add 1v1 Duel to Chapter 03 Formation Diagrams

Add one blue friendly Hero 1 and one red enemy Hero 1, both labelled Front,
with `VS` between them and no formation choice. Match the existing Chapter 03
hero-slot shape; preserve all 2v2 and 3v3 diagrams. See
`docs/Codex/Current_Task.md`.

**Status:** Completed on 2026-11-08. Core recorded focused results in
`docs/Codex/Completed.md`.

### UI-062 — Interactive Formations & Attack Types Demonstration

Replace Chapter 03's stacked 2v2/3v3 diagrams and separate attack-type table
with one selectable formation diagram. Select a friendly attacker and attack
type to see Python-authoritative enemy target eligibility and direct-damage
formation multipliers. Demonstrate defeated Front defenders, preserve the
new 1v1 Duel as a non-interactive reference, and keep Manual navigation
unchanged. See the owner's attached brief and `docs/Codex/Current_Task.md`.

**Status:** Completed on 2026-11-09. Core recorded implementation and validation
in `docs/Codex/Completed.md`.

### UI-063 — Battle Instruction Layout and Legibility Refinement

Balance the Previous/Next footer widths; move Battle Formats' formation options
and 9/13/15 maximum rounds into two labelled rows below each hero diagram;
remove Chapter 03's specified introductory paragraph and gold demo kicker;
rename the demo `2v2 & 3v3 Battle Formation`; enlarge the small diagram/result
text without responsive collisions. Preserve UI-062's rule results and Manual
navigation. See `docs/Codex/Current_Task.md`.

**Status:** Completed on 2026-11-09. Core recorded focused results in
`docs/Codex/Completed.md`.

### UI-064 — Refresh Battle Interface Screenshot and Bubbles

Use the owner's new Battle Interface capture, add separate bubbles for the
target-hover information panel and clickable gold Hero Stats button, separate
command confirmation from preview, and make the speed bubble cover Battle
Speed only—not Auto Battle. Realign all 11 markers to the new image, and remove
the decorative `FIELD GUIDE · SIX CHAPTERS` line from the Manual header. See
`docs/Codex/Current_Task.md`.

**Status:** Ready for Core.
