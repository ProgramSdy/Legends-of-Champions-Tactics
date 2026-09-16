# Current Task

**Status:** Completed

**Task:** BATTLE-TRANSPARENCY-002 — Priest Comprehensiveness and Paladin Retribution

**Owner request date:** 2026-09-15

## Objective

Extend Battle Information Transparency from the current Mage and Rogue scope to
Priest Comprehensiveness and Paladin Retribution. Before confirming an action,
players must see truthful, compact information for each selected target,
including immediate healing or damage range, direct hit chance only where it
applies, target HP, and a concise material effect when it changes the decision.

## Background

BATTLE-TRANSPARENCY-001 established an engine-owned, non-mutating, RNG-free,
revision-bound preview operation. The Battle Screen displays the returned facts
for Mage and Rogue only. Its client code currently assumes every preview is
damage and labels its primary value `Damage`.

Priest Comprehensiveness has Holy Smite, Shadow Word Pain, and Binding Heal.
Paladin Retribution has Hammer of Anger, Crusader Strike, and Flash of Light.
Their direct damage, healing, status state, secondary healing, and Wrath of
Crusader interactions must be audited from live code before the preview
contract or player copy is extended. Do not derive formulae or status meaning
in React.

## Required Player Experience

### General rules

- Apply the existing target hover and keyboard-focus preview interaction to all
  six approved skills when they are selected and a legal target is highlighted.
- For direct damage, show `Damage`, `Hit Chance`, and `Target HP`, using the
  same direct-evasion meaning of Hit Chance established by BATTLE-TRANSPARENCY-001.
- For healing, show `Healing` and `Target HP`; do not show a Hit Chance because
  the current healing action has no direct-evasion chance.
- Healing information shows the authoritative post-modifier skill power before
  the live maximum-HP cap. It accounts for deterministic healing
  reductions/prevention but does not reduce the displayed range to missing HP;
  actual battle HP remains capped at maximum.
- A material effect belongs on a separate concise row. Do not combine it with
  damage, healing, or Hit Chance and do not expose internal formula inputs.
- If an edge case cannot be supported truthfully, show `Preview unavailable`.
  It must never block a legal command.

### Priest Comprehensiveness

| Skill | Preview requirements |
| --- | --- |
| Holy Smite | Immediate direct holy-damage range, direct Hit Chance, and target HP. Use the actual live rule, including its resistance/defence treatment. |
| Shadow Word Pain | Immediate direct-damage range, direct Hit Chance, target HP, and a concise material Shadow Word Pain consequence only when the current live rule can newly apply it. Do not show or estimate future DoT tick damage; do not imply refresh/strengthening when live code does neither. |
| Binding Heal | Immediate selected-target healing range and target HP. When a non-self ally is selected, truthfully show the Priest’s separate material self-healing consequence only if it can change HP; do not pretend it is a second heal on the selected target. For a self target, show only the applicable self-heal result. |

### Paladin Retribution

| Skill | Preview requirements |
| --- | --- |
| Hammer of Anger | Immediate direct-damage range, direct Hit Chance, target HP, and the live Wrath of Crusader stack contribution where it materially changes the direct range. Do not present a fabricated fixed damage value. |
| Crusader Strike | Immediate direct-damage range, direct Hit Chance, and target HP. Show the material Wrath of Crusader outcome using clear player language: first application, increase to the next valid stack, or duration refresh, exactly as live action semantics permit. |
| Flash of Light | Immediate selected-target healing range and target HP. The range must use the live current Wrath of Crusader state, including its stack-specific bonus/healing behaviour, missing-HP cap, and any applicable deterministic receipt rule. Do not show a Hit Chance. |

## Engine and Contract Requirements

- Keep the preview engine-owned, read-only, deterministic, and free of all
  random consumption. It must not execute mutating callbacks, clone/restore a
  live battle, alter HP/status/stack/duration/cooldown/log/events/turn/revision,
  or consume session/global RNG.
- Audit the six live skill paths first. Add narrowly scoped pure range/outcome
  primitives only where they can be shared with, or demonstrably mirror, the
  existing live calculation. Preserve current mechanics, including legacy
  behaviour. Escalate a discovered rules inconsistency rather than correcting
  it inside preview work.
- Extend the additive typed preview contract so a target’s primary fact can be
  unambiguously `damage`, `healing`, or deterministic `prevented`. Include the
  truthful immediate range after current-state constraints and separately typed
  material consequences. Do not overload a damage-only field for healing.
- Preserve compatibility for the current Mage/Rogue consumers and all existing
  preview requests/responses. Do not alter commands, snapshots, event order,
  current skill execution, or save/progression data.
- Validate actor, active revision, available approved skill, legal target side,
  cardinality, liveness, duplicate IDs, and complete multi-target selection at
  the existing session lock. Out-of-scope/stale/invalid requests must fail
  safely with no mutation.

## Frontend Requirements

- Extend the allowlist and typed provider/client handling for exactly these six
  skills. The frontend must not calculate damage, healing, Wrath stacks,
  secondary healing, status eligibility, prevention, hit chance, or legality.
- Update the preview card and compact dock to render the authoritative primary
  label/value. It must show `Healing` with no Hit Chance for a healing primary,
  while retaining current damage treatment for existing skills.
- Render secondary Binding Heal and status/Wrath facts only from typed server
  consequences. Copy must identify a separate recipient where relevant.
- Preserve pointer, keyboard, touch, multi-target, target highlighting,
  compact-layout, loading/unavailable, stale-response, command, auto-battle,
  formation, and accessibility behaviour from BATTLE-TRANSPARENCY-001.

## Out of Scope

- Priest Discipline, other Paladins, all remaining heroes, targetless skills,
  general healing preview fallback, future DoT totals, chains, spreads,
  summons, generic proc simulation, and unapproved status effects.
- Changes to game formulas, healing reduction, Wrath of Crusader, status
  durations/stacks, targeting, cooldowns, Accuracy/Evasion, battle rules, API
  commands, save data, or player progression.
- Client-side formula copies, previewing the next random roll, raw formula
  explanations, aggregate multi-target totals, or UI redesign.

## Relevant Files

- `heroes/priest.py` and `heroes/paladin.py` — audit six live skills and add
  safe shared pure preview primitives only when justified.
- `battle_api/adapter.py`, `battle_api/app.py`, and `battle_api/models.py` —
  authoritative evaluation, validation, and additive response transport.
- `web-ui/lib/battle/types.ts`, `liveProvider.ts`, and `useBattlePreview.ts` —
  typed contract and six-skill allowlist.
- `web-ui/components/battle/BattleScreen.tsx` and `web-ui/app/globals.css` —
  authoritative damage/healing presentation, compact dock, and accessibility.
- `tests/test_battle_transparency_preview.py`, relevant adapter/API tests, and
  `web-ui/tests/battle-transparency*.test.tsx` — focused no-mutation, truth,
  interaction, and regression coverage.
- `docs/web-ui/BATTLE_DATA_CONTRACT_V1.md`, `PYTHON_ADAPTER_API.md`,
  `WEB_UI_ARCHITECTURE.md`, `Style_Guide.md`, `docs/Technical/Architecture.md`,
  and `docs/Codex/Completed.md` — contract, architecture, player presentation,
  and completion evidence.

## Acceptance Criteria

1. Priest Comprehensiveness and Paladin Retribution can request authoritative
   hover/focus previews for all their legal targetable skills.
2. Damage previews retain precise immediate ranges, direct Hit Chance, target
   HP, prevention truthfulness, and separate material effects.
3. Binding Heal and Flash of Light display truthful immediate healing values
   without a Hit Chance and never imply health above the target maximum.
4. Binding Heal’s separate caster heal and Shadow Word Pain/Wrath outcomes are
   presented only when current live state makes them material and truthful.
5. Existing Mage/Rogue preview data, UI, commands, combat results, event order,
   RNG determinism, formation, and responsive behaviour remain unchanged.
6. Preview consumes no RNG and mutates no engine/session/UI command state;
   matching later seeded actions have the same result with or without preview.
7. Invalid/stale/unavailable requests remain safe, and the UI clears stale data
   without blocking a legal command.
8. Contract, architecture, style, API, and completion documents describe the
   expanded audited scope without claiming full healing/full-roster support.

## Validation Required

- Add direct engine/adapter/API tests for all six skills covering minimum and
  maximum range, live resistance/defence treatment, evasion/direct Hit Chance,
  healing missing-HP caps, reduction/prevention, self versus ally Binding Heal,
  Priest secondary healing, Wrath absent/one/two stacks/refresh, and status
  new-versus-already-active boundaries.
- Deep-compare snapshot/session/RNG before and after preview; patch random
  helpers to fail during preview; prove later same-seed commands equal an
  untouched control.
- Test stale actor/revision, unavailable/out-of-scope skills, wrong side,
  dead targets, duplicate/invalid target IDs, and existing Mage/Rogue contract
  compatibility.
- Add frontend tests for `Healing` versus `Damage`, Hit Chance visibility,
  post-modifier healing power/prevented states, target-only Binding Heal copy,
  Wrath/Shadow Word copy,
  hover/focus/touch/compact behavior, stale clearing, and no client formula
  duplication.
- Run focused backend/frontend suites, typecheck, lint, production build,
  py_compile where relevant, and `git diff --check`. Manually test 1v1, 2v2,
  and 3v3 with Priest and Paladin player turns, including injured/full targets,
  Wrath states, and a status boundary. Record exact results and any browser
  limitation honestly.

## Agent Assignments

**Complexity/risk assessment:** High. This extends a live authoritative
information feature across stateful healing, secondary recipients, status and
stack interactions, existing compatibility requirements, an additive contract,
and responsive/accessibility UI. All five roles are required.

- **project-manager:** own study-before-build sequencing, cross-boundary scope,
  agent dispatch, documentation, and evidence.
- **game-engine-developer:** own live-skill audit, pure preview primitives,
  no-mutation/RNG guarantees, adapter/API contract, and backend tests.
- **ui-developer:** own typed client consumption, healer-aware presentation,
  hover/focus/compact accessibility, and frontend documentation.
- **test-automator:** own deterministic engine/API/UI truth, non-mutation,
  stale/legality, interaction, and regression coverage.
- **reviewer:** independently assess formula/receipt/status truthfulness,
  scope, compatibility, RNG guarantees, UI clarity, documentation, and tests.

## Completion Notes

Completed 2026-09-15. Battle Information Transparency now has one finite,
engine-owned audited scope: the original Mage/Rogue skills plus Priest
Comprehensiveness Holy Smite, Shadow Word Pain, Binding Heal and Paladin
Retribution Hammer of Anger, Crusader Strike, Flash of Light. No generic
healing or full-roster preview fallback was added.

**Agent contributions:**

- **project-manager:** completed the mandatory pre-build audit, fixed the
  cross-boundary scope, and recorded the live-rule/receipt truth table.
- **game-engine-developer:** added pure audited primitives, typed adapter/model
  transport, no-mutation/no-RNG tests, API coverage, and the dated engine audit.
- **ui-developer:** completed the frontend contract/presentation study; the
  agreed typed-client and Battle Screen integration was applied in the shared
  worktree without client-side combat calculations.
- **test-automator:** added the initial focused Priest/Paladin presentation
  coverage and supplied the deterministic backend/adapter test matrix; final
  keyboard, compact, and touch assertions were expanded in the shared suite.
- **reviewer:** independently reviewed formulas, receipt/cap behavior, scope,
  contract compatibility, documentation, and the final tests; result approved.

**Files changed:**

- `heroes/priest.py`
- `heroes/paladin.py`
- `battle_api/adapter.py`
- `battle_api/models.py`
- `tests/test_battle_transparency_002_preview.py`
- `docs/Codex/Analysis/2026-09-15_BATTLE-TRANSPARENCY-002_Engine_Audit.md`
- `web-ui/lib/battle/types.ts`
- `web-ui/lib/battle/liveProvider.ts`
- `web-ui/lib/battle/useBattlePreview.ts`
- `web-ui/components/battle/BattleScreen.tsx`
- `web-ui/tests/battle-transparency-002.test.tsx`
- `docs/web-ui/BATTLE_DATA_CONTRACT_V1.md`
- `docs/web-ui/PYTHON_ADAPTER_API.md`
- `docs/web-ui/WEB_UI_ARCHITECTURE.md`
- `docs/web-ui/Style_Guide.md`
- `docs/Technical/Architecture.md`
- `docs/Codex/Current_Task.md`
- `docs/Codex/Completed.md`

**Validation:**

- `./.venv/bin/python -m pytest -q tests/test_battle_transparency_preview.py tests/test_battle_transparency_002_preview.py` — 79 passed; one existing Starlette/httpx deprecation warning.
- `cd web-ui && npm test -- --run tests/battle-transparency-preview.test.tsx tests/battle-transparency-002.test.tsx` — 18 passed.
- `cd web-ui && npm run typecheck` — passed.
- `cd web-ui && npm run lint` — 0 errors; one existing unused `_signal` warning in `tests/battle-transparency-preview.test.tsx`.
- `cd web-ui && npm run build` — passed; Vinext emitted only its existing dynamic-route-classification notice.
- `./.venv/bin/python -m py_compile battle_api/adapter.py battle_api/models.py heroes/priest.py heroes/paladin.py` and `git diff --check` — passed.
- Isolated Ego browser smoke on `/debug`: 1v1 Holy Smite showed an authoritative Damage/Hit Chance card; the later owner follow-up changed full-health healing presentation from `0–0` to post-modifier skill power without Hit Chance; 2v2 Shadow Word Pain showed its distinct effect row; 3v3 loaded all six combatants without layout or runtime error.

**Remaining manual limitation:**

The deterministic test suites cover injured/full recipients, Wrath states,
status boundaries, and 1v1/2v2/3v3 contracts. The isolated live 3v3 smoke
opened on a Mage turn, so an additional release-playtest should exercise a
live Priest/Paladin 3v3 turn with the desired seeded turn order for visual
polish; this is not a correctness or contract blocker.
