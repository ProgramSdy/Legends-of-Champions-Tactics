# Current Task

**Status:** Queued — wait for Core Project Team to complete its current task before starting
**Task ID:** UI-026
**Title:** Refine the Paladin Healing Target Animation
**Prepared:** 2026-09-09

## Objective

Replace the current Paladin healing target beam, which reads as a hard golden rectangle/block moving over the hero, with a polished target-bound effect based on the successful Priest healing target animation.

## Background

UI-025 introduced a distinct Paladin target effect for `healingApplied` events authored by a Paladin. Its current tall, clipped linear-gradient beam (`effect-paladin-healing`) is visually too solid and geometric. The owner prefers the existing Priest target treatment: a contained, soft radial light that rises from the target rather than a large opaque shape.

The improved Paladin treatment should begin from that same proven visual language but remain recognisably Paladin: brighter, warmer gold and a clear top-to-bottom light movement. It must be a target effect only; the Priest caster rune presentation is unrelated and must not be copied into Paladin healing.

## Requirements

### 1. Visual direction

- Use the existing Priest **target** effect (`effect-priest-healing`) as the starting reference for scale, soft-edge radial light, containment within the hero footprint, and overall polish.
- Replace the current Paladin clipped beam/flare design. The final Paladin effect must not read as a rectangle, solid colour block, triangle, or a hard-edged light column.
- Make the Paladin palette visibly brighter and warmer than the Priest soft gold: use a controlled white-gold highlight with rich sun-gold edges, while preserving battlefield readability and the dark-fantasy style.
- Convey the requested top-to-bottom motion through a soft, rounded light treatment: it should begin above/at the target hero's head and descend over the target into a gentle lower-body/ground glow. Use opacity, blur, radial gradients, and/or small soft light layers rather than a large opaque beam.
- Keep the effect brief, restrained, and legible. It should feel like a blessing/sunlight settling onto the healed target—not an attack, projectile, explosion, or fullscreen flash.

### 2. Presentation behaviour

- Continue to select the treatment only for authoritative `healingApplied` events whose source combatant faculty is `Paladin`.
- Preserve the existing event timing, queue ordering, target identity, `+healing` floating text, and healing mechanics.
- Keep the effect entirely target-bound inside the shared battlefield figure footprint so it follows 1v1, 2v2, and 3v3 formation depth, hero scale, side mirroring, and UI-024 responsive presentation rules.
- Preserve the existing Priest target effect and Priest caster runes exactly. Preserve generic green healing and all non-healing feedback exactly.
- Update reduced-motion handling so the Paladin effect becomes a visible, non-moving soft golden target glow—without reviving the current beam/block appearance.

### 3. Implementation hygiene

- Simplify/remove obsolete Paladin beam-specific CSS and keyframes once the replacement is in place; do not leave duplicate/competing `target-effect` or Paladin healing definitions.
- Do not change the battle API, adapter, game engine, hero/skill data, event schema, or faculty classification logic for this visual-only refinement.

## Out of Scope

- Priest caster animation or Priest target-effect changes.
- New art assets, particle libraries, audio, gameplay balance, healing calculations, or status-event changes.
- Changes to other Paladin effects, skill cards, battle layout, formation rules, or UI-024 configuration.

## Relevant Files

- `web-ui/app/globals.css` — replace `.target-effect.effect-paladin-healing`, its pseudo-elements/keyframes, and reduced-motion rule with the refined treatment.
- `web-ui/components/battle/BattleScreen.tsx` — inspect only to preserve the existing target-effect mounting and Paladin source-faculty selection; no behavioural rewrite is expected.
- `web-ui/tests/battle-screen.test.tsx` and `web-ui/tests/ui-007-regressions.test.tsx` — retain/add target-classification and Paladin/Priest separation coverage.
- `docs/web-ui/Style_Guide.md` — update only if its brief feedback description needs to reflect the final approved direction.
- `docs/Codex/Completed.md` — record the completed visual refinement and validation evidence after acceptance.

## Acceptance Criteria

1. A Paladin healing event no longer displays a rectangular, triangular, hard-edged, or block-like golden beam.
2. The effect clearly takes the Priest target animation’s soft, contained light language as its base while appearing brighter and warmer gold.
3. The Paladin light visibly travels from above the healed hero downward, ending in a soft target/ground glow without obscuring the hero.
4. The effect is mounted only on the healed target and remains correctly aligned in 1v1, 2v2, and 3v3 at desktop and responsive viewports.
5. Priest target soft-gold treatment and Priest caster runes remain unchanged; generic healing remains green and unchanged.
6. `healingApplied` selection, combat state, logs, event ordering, and API/backend contracts are unchanged.
7. Reduced-motion renders a stable soft gold target indication with no movement and no hard beam/block.
8. No obsolete duplicate Paladin-beam CSS/keyframes remain after the replacement.

## Validation Required

- Run the focused Battle Screen and UI regression tests that cover Paladin, Priest, and generic healing classification.
- Add or update regression coverage for the refined Paladin target class without weakening the Priest-separation assertions.
- Manually verify Paladin healing in 1v1, 2v2, and 3v3, including a different formation depth and a narrower responsive viewport.
- Compare a Paladin heal and Priest heal side by side: Paladin must be brighter warm gold with descending motion; Priest must retain its existing soft-gold rise and caster runes.
- Verify `prefers-reduced-motion` renders a non-moving soft gold Paladin target glow, not the prior beam.
- Run `npm run typecheck`, relevant frontend tests, and `git diff --check`; record exact commands/results in `Completed.md`.

## Documentation / Handoff Requirements

- Do not notify Core Project Team about this task until its current task has completed.
- After Core completes this queued task, update `docs/Codex/Completed.md` with the final visual description, changed files, and validation evidence.

## Agent Assignments

- **UI developer:** Design and implement the refined Paladin target-only effect by adapting the Priest target-effect language; remove the block-like beam implementation.
- **Test automator:** Maintain classification/separation coverage and validate animation/reduced-motion regressions.
- **Reviewer:** Compare the effect against the acceptance criteria, focusing on softness, downward readability, target anchoring, Priest isolation, and responsive formation alignment.
- **Game-engine developer:** Not required unless a verified presentation data gap appears; do not alter engine/API behaviour for this task.
- **Project manager:** Wait for the current Core task to finish before dispatching UI-026, then coordinate validation and documentation handoff.

## Completion Notes

To be completed by the implementation team after acceptance.
