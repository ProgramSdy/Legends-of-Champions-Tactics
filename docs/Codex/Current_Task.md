# Current Task

**Status:** Completed

**Task:** UI-032 — Holy Word Punishment Continuous Damage Gallery Fact

**Owner request date:** 2026-10-24

## Objective

In the expanded Hero Gallery card for Priest Discipline's **Holy Word Punishment**, add a **Continuous Damage** fact box immediately after **Base Damage** in the existing responsive facts grid. It must describe the skill's audited ongoing damage separately from its existing 7–11 immediate Base Damage. Keep the established Gallery presentation and authoritative-data pattern.

## Background and Confirmed State

`Current_Task.md` previously held completed UI-031, recorded in `Completed.md`; no active task is being displaced. Holy Word Punishment currently has an engine-authored 7–11 immediate-damage reference but no structured ongoing-damage fact. The Gallery's generic row builder renders typed catalogue facts, not YAML-derived mechanics. Live skill code attaches the debuff only when the target's Punishment status is inactive; a new or recycled debuff derives its stored effect from the direct-damage roll with different rounding, and the round-start status code then adds a separate random variation per activation. The effect lasts across later round starts, and an already-active target can still receive direct damage without refreshing the debuff. These details make a guessed fixed number or total misleading.

The owner calls this a debuff skill because of its ongoing effect. That request does **not** itself authorise changing the current engine `skill_type="damage"`, attack classifications, status behaviour, or battle rules.

## Requirements

1. Audit the live Holy Word Punishment application and round-start activation paths, including first application versus recycled debuff, rounding, per-activation variation, target receipt/mitigation, status duration, and already-active status. Establish the truthful **per-target, per-activation baseline power range** if possible. Do not infer it solely from 7–11 or random sampling. If the branches cannot be expressed as one reliable range, use an explicit unavailable/conditional presentation instead of inventing a number; explain the branch distinction concisely.
2. Extend the existing read-only hero catalogue with a typed, additive ongoing/continuous-damage reference for this skill. Prefer the existing numeric-reference conventions where suitable. Keep mechanics and formulas engine-owned; React and editable YAML must not calculate or define this value. Catalogue reads must remain deterministic, non-mutating, and RNG-free.
3. Render a **Continuous Damage** box directly after **Base Damage** in the generic Gallery fact order, but only when an authoritative applicable continuous-damage reference is supplied. Preserve the current two-column flow and narrow-screen collapse. Label the value as damage **per activation/tick**, not a guaranteed total or actual HP lost. Use a short note or formula popup if needed to make conditional/new-versus-reused behaviour honest; do not overload the box with a multi-round total.
4. Preserve the existing Base Damage 7–11, Target Type, Skill Type, Attack Type, Damage Nature, Damage Type, and Cool Down conventions. Do not show Continuous Damage for unrelated skills without an audited reference, and do not change combat, status, RNG, or battle-preview behaviour to satisfy a static Gallery display.
5. Update only directly affected GDD/web-UI/API contract documentation and add a concise completion note stating the audited presentation and any limitation. Preserve unrelated dirty owner YAML/generated content and the read-only `UI_Review_Human.md`.

## Out of Scope

- Damage-balancing or correction of the live skill's different new/recycled rounding rules; flag a true mechanics defect separately instead of silently changing gameplay.
- Aggregate damage across the debuff's lifetime, guaranteed application to an already-affected target, battle-scene transparency preview, or new boxes for other periodic skills.
- A Gallery redesign, editorial introduction rewrite, commits, pushes, or PRs without a separate owner request.

## Relevant Files and Boundaries

- Engine truth: `heroes/priest.py` (`holy_word_punishment`) and `game/status_effect_manager.py` (Punishment tick).
- Read-only catalogue: `battle_api/adapter.py` reference generation and `battle_api/models.py` typed reference; affected focused Python catalogue tests.
- Client contract and display: `web-ui/lib/battle/types.ts`, strict catalogue decoding in `web-ui/lib/battle/liveProvider.ts`, `web-ui/lib/manual/heroGalleryPresentation.ts`, `web-ui/components/manual/HeroGalleryExperience.tsx`, and focused Gallery tests. CSS only if existing grid cannot present the new row cleanly.
- Documentation: `docs/GDD/Skill_System.md`, `docs/web-ui/PYTHON_ADAPTER_API.md`, `docs/web-ui/WEB_UI_ARCHITECTURE.md`, `docs/web-ui/Style_Guide.md`, and the relevant catalogue contract if its schema is documented there. Update only what actually changes.
- Historical status: `docs/Codex/Completed.md`; current task: this file.

## Acceptance Criteria

- Expanding Holy Word Punishment shows **Base Damage 7–11** followed immediately by **Continuous Damage**, with truthful per-activation wording and an audited value or explicit unavailable/conditional explanation.
- Other facts and the existing responsive layout remain intact; unrelated skills do not gain an unjustified box.
- Typed API/client validation accepts the additive field and rejects malformed supplied values. Catalogue evaluation remains read-only and RNG-free.
- Focused tests cover new/recycled and already-active cases, range boundaries/rounding or the reason for an unavailable state, row order/conditional rendering, and no change to live combat outcomes.

## Validation Required

Run focused backend catalogue/skill-reference tests and focused frontend Gallery presentation tests, plus TypeScript typecheck and a scoped diff check. Inspect one expanded card at desktop and a narrow width if the local Gallery is available. Do not run broad combat suites or repeat extensive review for this narrow static-reference addition. Record any existing unrelated content-check limitation without rewriting owner content.

## Complexity and Agent Assignments

**Assessment:** Small cross-boundary typed-data/UI change with moderate numeric-truth risk. Use only three roles, in sequence where needed.

- **game-engine-developer:** Audit authoritative skill/status formulas and branches; own the additive typed catalogue reference and a focused backend test. No gameplay changes.
- **ui-developer:** Consume the typed fact in the existing generic row builder/client contract; own focused UI coverage, responsive check, and directly affected UI docs.
- **reviewer:** One targeted independent check of numeric truth, typed compatibility, row order, scope, and validation evidence.
- **Omitted:** `project-manager` is unnecessary for this small handoff; `test-automator` is unnecessary because each implementation specialist owns the few focused tests at their boundary. Core still records the role-selection gate and final completion evidence.

Core should report only completion or a genuine owner-decision blocker; avoid intermediate cross-chat traffic.

## Completion — 2026-10-24

Holy Word Punishment now publishes an engine-authored, per-activation
Continuous Damage reference immediately after Base Damage in the Gallery.
The original UI-032 audit recorded 8–16 because new/recycled debuffs had
different rounding. The owner subsequently changed the recycled path to
`math.ceil`, so the current baseline power is 9–16 for both paths after the
tick's ±1 variation. The displayed fact is not guaranteed HP loss or a
multi-round total; an already-active target receives direct damage without
refreshing the debuff. Other skills publish not-applicable references and do
not gain a box. Live mechanics and RNG are unchanged.

The game-engine-developer owned the formula audit, additive typed catalogue,
focused backend tests, and engine/API/contract documentation. The ui-developer
owned the strict client type/decoder, generic Gallery row, focused frontend
tests, UI documentation, and desktop/narrow inspection. The reviewer
independently approved the numeric truth, compatibility, scope, and row order
with no blocking finding. PM and test-automator were omitted because this
small handoff had focused validation at each specialist boundary.

Focused backend catalogue tests: 47 passed; focused Gallery tests: 25 passed;
Python compilation, TypeScript typecheck, and scoped diff-check passed.
Browser inspection at 1440×900 and 390×844 confirmed first-two fact order,
two-/one-column layouts, and no horizontal overflow. The normal npm test
wrapper remains blocked by pre-existing stale owner-generated Gallery content;
direct Vitest passed without rewriting it. Unrelated dirty owner files were
preserved. No commit or push was performed.

**Owner follow-up:** The engine change to recycled rounding was owner-authored.
The catalogue, box, focused tests, and authoritative documentation were
aligned to 9–16; the box now displays only the range, without a suffix,
explanatory note, or new/recycled conditions.

## Core pre-code dispatch gate — 2026-10-24

This is a small additive catalogue/UI change with moderate risk of misstating
the two live Punishment rounding branches. The game-engine-developer owns the
read-only audited reference, typed server model, focused backend tests, and
directly affected engine/API documentation. The ui-developer owns typed client
decoding, generic Gallery row placement, focused frontend tests, responsive
inspection, and directly affected UI documentation. The reviewer independently
checks numeric truth, compatibility, row order, scope, and evidence after both
changes land. Project-manager and test-automator are omitted for the narrow
handoff because each specialist can validate its own boundary. Core owns the
final task and completion record. All prior dirty Gallery, owner review, and
rule-document edits remain outside UI-032 and must be preserved.
