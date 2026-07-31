# UI-003 Action-Restriction Integration Study

**Date:** 2026-07-31
**Status:** Investigation complete; no production fix implemented.

## Executive Summary

The owner-reported Stun and Scoff failures do not reproduce on the current
backend or live-adapter happy path. Controlled submissions using the real
`Shield Bash`, `Shield Lash`, and engine-spelled `Heroric Charge` skills show
that:

- a Shield Bash target loses its restricted turn without executing a skill;
- a Shield Lash or Heroric Charge target, including a player-controlled target,
  automatically attacks the Scoff initiator; and
- the adapter returns the next unrestricted player turn rather than exposing
  controls for the restricted actor.

The current behavior appears to have been added in commit `d3dd376e` on
2026-07-30. The reported symptom may describe an earlier runtime, a stale
frontend/backend process, an evaded or immune application, or confusing
transient presentation. The investigation does not have evidence to select one
of those explanations.

The integration is nevertheless structurally fragile. The adapter duplicates
engine restriction rules, snapshots do not explicitly say whether a turn
accepts player commands or resolves automatically, Scoff source identity is
lost during serialization, and command validation does not independently
reject commands at a restricted boundary. React disables input during event
playback and uses the final legal-action list, but cannot faithfully present
the automatic intermediate turn. A future implementation should introduce an
engine-owned turn directive and serialize an explicit turn-control disposition.

## Owner-Reported Symptoms

- Shield Bash should Stun its target for one round, but the target was observed
  acting through the web UI.
- Shield Lash and Heroic Charge should apply Scoff and force the affected
  hero's next action against the initiator.
- A player-controlled Scoff target must not receive normal action controls.

These are investigation inputs, not confirmed current defects.

## Authoritative Engine Behavior

### Turn routing

- `game/game.py:254-333` pops the current actor and processes Scoff before the
  normal player/computer branch. A live initiator routes the actor through
  `Hero.ai_action()`. A defeated initiator clears Scoff and resumes the normal
  control path. The actor is marked actioned afterward.
- `heroes/hero.py:1124-1169` handles computer actions. Stun, Paralysis, Fear,
  and Glacier prevent skill execution. Scoff selects an available
  single-target damage or damage/healing skill and targets the stored Debuff
  initiator, with a multi-target damage fallback.
- `heroes/hero.py:1171-1233` handles player actions. Stun, Paralysis, and Fear
  return without accepting or executing a skill.

### Named skills

- `heroes/warrior.py:231-259` implements Shield Bash. After a successful hit it
  applies `stunned`, clears `normal`, increments `stun_duration`, and starts a
  three-turn cooldown. Its post-hit application chance is 100%; the attack can
  still be evaded before application.
- `heroes/warrior.py:281-352` implements Shield Lash. It sets `scoff` and stores
  a duration-one `Debuff` whose initiator is the caster.
- `heroes/paladin.py:262-307` implements the engine/API-spelled
  `Heroric Charge`. It stores the same Scoff initiator relationship.
- `skills/skill.py:84-116` resolves death, evasion, and immunity before effect
  application. `skills/skill.py:214-239` contains relevant control-immunity
  messaging.

### Status lifetime

`game/status_effect_manager.py:69-76` decrements Stun at round start. A duration
of one becomes zero while `stunned` remains true and is cleared only at the
following status tick. The resulting number of skipped scheduled actions can
depend on whether the target had already acted when Stun was applied. This is
legacy behavior and the phrase “one round” is not sufficiently precise to
change it safely.

`game/status_effect_manager.py:700-711` retains the Scoff Debuff while the flag
is true. The forced action clears the flag; a later status tick removes the
record.

## Current Web Integration Flow

1. The adapter creates or restores authoritative Python battle state.
2. `battle_api/adapter.py:386-413` validates a submitted command, resolves it,
   and drains automatic turns before returning.
3. `battle_api/adapter.py:540-661` skips incapacitated actors, resolves Scoff,
   runs computer turns, and stops at an unrestricted player actor.
4. `battle_api/adapter.py:664-772` determines the Scoff source/action and
   incapacitation behavior. This duplicates, rather than calls, the engine
   decision logic.
5. `battle_api/adapter.py:344-384` serializes all non-ended snapshots with
   `phase: "awaitingCommand"`. `battle_api/adapter.py:1005-1038` suppresses
   legal actions for restricted actors.
6. `web-ui/lib/battle/liveProvider.ts` forwards and caches the returned
   envelope. It has no separate turn-control concept.
7. `web-ui/lib/battle/usePresentationQueue.ts` plays response events with input
   blocked, then reconciles to the final snapshot.
8. The battle screen derives skill and target controls from `legalActions`.

On the normal synchronous path, React receives only the final actionable
snapshot and cannot submit during event playback. It therefore does not
currently bypass a correctly drained Stun or Scoff turn.

Transient presentation is incomplete: event playback does not make
`turnStarted`/`turnEnded` authoritative for the displayed active actor and
does not fully reconcile status removal until the final snapshot. Automatic
turns can consequently appear opaque or be associated visually with stale
actor information even while controls remain disabled.

If an undrained restricted snapshot were ever returned, React would show a
generic “choose an authorized skill” active-hero prompt with no usable actions
and has no polling or automatic-step mechanism. That is a latent deadlock and
misrepresentation risk.

## Reproduction Method and Evidence

All experiments used temporary in-memory battle objects or scripts outside the
repository. Production files were not changed.

### Engine-only controlled scenarios

- Shield Bash against player- and computer-controlled targets applied
  `stunned=True`, duration one. The next `Game.hero_action()` emitted
  `Nighthawk is stunned and can't move.`, executed no skill, and marked the
  target actioned.
- Shield Lash against both control modes created
  `Scoff(Aegis, duration=1)`. `Game.hero_action()` ignored the target's control
  mode, chose Sharp Blade, targeted Aegis, cleared the Scoff flag, and marked
  the target actioned.
- A defeated Scoff initiator cleared the restriction and resumed the ordinary
  control path.
- Stun lifetime was observed as `(true, 1)` after application, `(true, 0)` on
  the first status tick, then `(false, 0)` on the second.
- Actual Heroric Charge created a duration-one Scoff record pointing to
  Bastion.

### Adapter actual-skill scenarios

- Shield Bash emitted `statusApplied: status.stunned`, followed by the target's
  `turnStarted` and `turnEnded` with “is stunned and cannot act”; no target skill
  event occurred.
- Shield Lash and Heroric Charge emitted Scoff application, an automatic target
  skill against the initiator, Scoff removal, and turn completion. This held
  for player- and computer-controlled targets.
- Final envelopes exposed legal actions only for the next unrestricted player
  actor.
- The serialized Scoff status had `sourceCombatantId: null` even though the
  server-side Debuff retained its initiator.

### Existing automated evidence

- Focused adapter suite: 6 relevant Stun/Scoff tests passed.
- Full Python suite: 59 tests passed with one Starlette deprecation warning.
- Relevant frontend suites: 38 tests passed.

The existing adapter tests at `tests/test_battle_adapter.py:513-712` primarily
inject status flags and Debuffs and call the private automatic-drain method.
They do not establish the complete real-skill HTTP-to-React chain.

## Findings and Root-Cause Assessment

### Not reproduced: current action-legality bypass

There is no evidence on the current happy path that a Stunned actor can submit
an action or that a player can choose a Scoff action. The current adapter drains
both before returning. The original observation therefore cannot be assigned
to a current engine or adapter defect without a precise runtime reproduction.

### Confirmed: duplicated gameplay authority

The original flow routes Scoff through `Hero.ai_action()`. The adapter instead
implements `_scoff_source()` and `_scoff_action()` and directly resolves its
choice. Its filters and fallback are similar but not identical to the legacy
engine. Restriction lists are also repeated. This creates drift whenever
existing rules change or new restrictions are added.

### Confirmed: implicit and incomplete contract

The contract communicates command acceptance indirectly through
`legalActions`, while every active snapshot says `awaitingCommand`. It cannot
represent “skip automatically,” “choose and resolve automatically,” or the
reason/source of that decision. `sourceCombatantId` is currently null for
Scoff.

### Confirmed: validation defense gap

`battle_api/adapter.py:415-443` validates actor, skill, and targets but does not
first assert that the authoritative turn boundary accepts a player command or
that the submitted action exactly matches a published legal action. Synchronous
draining normally hides the gap, but future endpoints or a failed drain could
make it reachable.

### Confirmed: presentation ambiguity

React blocks interaction while playing automatic events, but intermediate
events do not fully update displayed actor/control semantics. This can make a
correct forced or skipped action difficult to understand. The final snapshot
corrects state but does not explain the transient control decision.

### Coverage gaps

There are no committed end-to-end tests that cast all three named skills
through the public adapter/API for both control modes and then assert frontend
controls and presentation. Exact Stun lifetime, evasion/immunity, dead source,
no valid forced attack, refreshed Scoff, and multi-target fallback boundaries
also lack complete coverage.

## Architecture Options Considered

### React infers restrictions from status IDs

Rejected. It would duplicate Python gameplay rules in the client, cannot
reliably recover source/target policy, and would drift as statuses evolve.

### Keep adapter rules and add a turn-control field

This improves contract clarity and command safety but leaves two Python rule
implementations. It is a useful migration step, not the preferred end state.

### Route the adapter through the complete legacy `Game.hero_action()`

This maximizes reuse but couples a request/response service to legacy
interactive input, output, and presentation behavior. It would require broad
refactoring and is not the safest narrow integration seam.

### Engine-owned turn directive consumed by both flows

Recommended. Extract a non-interactive engine decision primitive that
classifies the current turn and, where applicable, supplies the authoritative
automatic action intent. Both legacy `Game.hero_action()` and the adapter would
consume it. React would receive the resulting disposition but never evaluate
status rules.

## Recommended Solution

Introduce an engine-owned current-turn directive with dispositions such as:

- `playerCommand` — normal player intent is accepted;
- `automaticAction` — engine supplies skill and forced/selected targets;
- `skip` — actor cannot act, with a stable reason;
- `ended` — no further actor action.

The directive should carry stable reason identifiers, actor identity, and
source/forced target identities where meaningful. Python remains responsible
for skill eligibility, randomness, target selection, restriction consumption,
and action completion.

The adapter should drain `automaticAction` and `skip` directives and stop only
at `playerCommand` or `ended`. Command validation should reject every other
disposition and require an exact match to the published legal action shape.

The snapshot should add an explicit control object. A possible shape, subject
to contract-version approval, is:

```json
{
  "turnControl": {
    "disposition": "playerCommand",
    "acceptsCommands": true,
    "reasonId": null,
    "actorCombatantId": "combatant-1",
    "sourceCombatantId": null,
    "forcedTargetIds": []
  }
}
```

Automatic resolution events should carry sufficient reason/source metadata for
presentation. Status serialization should populate Scoff's
`sourceCombatantId`. The client should render interactive controls only when
`acceptsCommands` is true, display concise automatic/skip feedback from
authoritative events, and never infer legality from status names.

## Proposed Regression Matrix

### Engine

- Directive classification for unrestricted player, computer, Stun,
  Paralysis, Fear, Glacier, Scoff, defeated Scoff source, and ended battle.
- Actual Shield Bash, Shield Lash, and Heroric Charge applications.
- Player/computer targets, both initiative orders, evasion and immunity.
- Exact Stun expiry across round boundaries.
- Scoff with no single-target attack, fallback attack, no legal attack,
  refreshed application, and defeated initiator.

### Adapter/API

- Public create/submit flows with the real named skills and deterministic seeds.
- No response exposes command acceptance for a restricted actor.
- Malicious/stale commands at automatic or skipped boundaries are rejected.
- Legal-action submissions match the published action exactly.
- Scoff source and forced targets survive serialization.
- Event order, revision increments, idempotency, and session restore remain
  correct for 1v1, 2v2, and 3v3.

### Frontend

- Controls render only for `playerCommand`.
- Skip and automatic-action events never enable selection or submission.
- Forced actor, source, target, status removal, and captions reconcile during
  presentation.
- Existing unrestricted skill/target selection remains unchanged.
- Failure/retry and stale-envelope behavior cannot strand a restricted actor
  behind a normal command prompt.

## Migration and Risks

- Decide whether `turnControl` is an additive v1 field or requires a new
  contract version before implementation.
- Preserve existing envelope/event ordering while adding explicit semantics.
- Do not silently alter legacy Stun duration during the integration refactor.
- Centralizing decisions can change seeded randomness if call order changes;
  capture deterministic baselines first.
- Legacy `Hero.ai_action()` mixes decision and execution concerns. Extracting a
  pure decision boundary requires careful compatibility tests.
- Scoff refresh and Debuff cleanup mutate legacy collections and deserve
  focused characterization before refactoring.
- Keep the misspelled `Heroric Charge` identifier compatible until a separately
  approved migration defines aliases or renaming.

## Scoped Follow-up Implementation Plan

1. Obtain owner decisions on the unresolved contract and gameplay questions.
2. Add characterization tests for current engine and adapter behavior,
   including the real named skills.
3. Define and implement the engine-owned turn directive without changing
   gameplay outcomes.
4. Refactor legacy Game and adapter automatic draining to consume it.
5. Add explicit contract fields, Scoff source serialization, and strict command
   boundary validation.
6. Update React control rendering and automatic-turn presentation.
7. Add public API and frontend integration regressions, then update the
   authoritative technical and web-UI documentation.

## Questions Requiring Owner Approval

1. Exactly how many scheduled actions should duration-one Stun skip for each
   initiative timing? The current round-tick behavior is timing-sensitive.
2. Should explicit `turnControl` be a backward-compatible v1 addition or start
   a new contract version?
3. What should the UI visibly show during skipped and forced turns: a caption,
   actor highlight, battle-log entry, animation, or a defined combination?
4. If a Scoff target has no legal attack against a live initiator, should it
   skip, use a multi-target fallback, or follow another approved rule?
5. Can the owner reproduce the original symptom on the current build, and if
   so, what seed, teams, initiative order, skill outcome, and runtime revisions
   were used?

## Scope Confirmation

This task produced documentation and investigation evidence only. It did not
change Python, adapter, API, React, CSS, tests, configuration, or assets. The
owner-controlled `UI_Review_Human.md` was treated as read-only.

## Validation Results

- Focused adapter Stun/Scoff tests: 6 passed, 39 deselected.
- Full Python suite: 59 passed; one existing Starlette deprecation warning.
- Relevant frontend suites: 38 passed.
- Full frontend Vitest suite: 64 passed across six files.
- TypeScript type check: passed.
- ESLint: passed.
- Production web build: passed; vinext emitted only its informational
  route-classification note.
- Owner-controlled file SHA-256 before and after:
  `5c93e620ae0cd28ce0f48885bede782e94686d1ec6fe20d5c4bcc121725e78d3`.
- Task-scoped Markdown whitespace validation: passed.
- Repository-wide `git diff --check` reports trailing whitespace in the
  owner's pre-existing change to `UI_Review_Human.md:65`. It was not corrected
  because that file is owner-controlled and must remain byte-for-byte unchanged.
- Final task changes are limited to this report, `docs/Codex/Completed.md`, and
  resetting `docs/Codex/Current_Task.md`. Other dirty files shown by Git predate
  UI-003 and were not modified by this investigation.
