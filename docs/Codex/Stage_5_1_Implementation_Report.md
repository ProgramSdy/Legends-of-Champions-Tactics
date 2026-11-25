# Stage 5.1 — Batches A–D implementation and release-candidate handoff

**Date:** 2026-11-25 (Australia/Sydney)
**Scope:** Owner-authorized BUG-001–003 implementation, local verification, and candidate preparation only. **Batch E is not authorized or performed.** Stage 5.1 remains open until an actual Owner-approved deployment, rollback, and redeployment have been observed.

## Change and authority

- **BUG-001:** Player-authored battle teams cannot repeat a stable Hero Profession definition ID. The adapter and generic, Debug, Stage, and Arena launch boundaries reject a crafted duplicate with HTTP 422 `duplicatePlayerProfession`. The Team Builder matrix explains an already-assigned player definition while retaining keyboard focus and replacement/unselection. Different specializations of one faculty and enemy-side repetitions remain legal; saved roster and progression records are not rewritten.
- **BUG-002:** Status details and target previews use viewport-bounded, anchored overlays. Placement flips/shifts at an 8px visible edge, constrains content, and follows resize, scroll, and anchor/content changes. The battle shell's narrow min-content overflow was corrected without changing battlefield formation/target rules.
- **BUG-003:** Development Debug alone exposes Auto Battle. Each accepted, revision-bound request resolves at most one friendly turn with that hero's existing specialization AI, session RNG, and engine legality; there is no new Tactics Level or React AI. The UI avoids overlapping requests and starts no new action after disable/departure/error/terminal state. Public server route registration and Public build exclude the Debug operation; Stage/Arena controls do not expose it.

No database schema, combat statistic/formula, capacity setting, Production configuration, or normal enemy AI policy was changed. Source inspection found no new persisted field or migration. Old and proposed code against a preserved copy of the actual live database have **not** been rehearsed; that compatibility evidence remains a Batch E pre-deployment gate.

## Ownership and review

The Owner authorized the team. Core owned sequencing, integration, browser evidence, documentation, and final gates. Game-engine developer owned backend validation/Debug action authority; UI developer owned selection, popup positioning, and Debug lifecycle; test automator owned focused regression tests and later stale-fixture updates. An independent reviewer inspected the integrated production diff and Public boundary and **approved with no P0/P1 finding**. Project-manager was omitted because the approved batch plan already supplied the dependency map and Core coordinated the workstreams. The reviewer noted one non-blocking hardening opportunity: a direct target-preview portal unit test in addition to status-tooltip tests and real-browser preview checks.

## Local validation

- Before edits, explicit-Development backend baseline: 79 passed, one existing Starlette/httpx deprecation warning. Relevant frontend baseline: 55 passed.
- Focused backend Stage 5.1/adapter/Public-isolation group: 91 passed; Stage/Arena/Debug integration group: 26 passed; AI strategy group: 35 passed. Public route/OpenAPI isolation: 6 passed under Public mode.
- Frontend full suite after updating the old always-mounted status-tooltip expectations: **59 files, 555 passed**. Generated-content check and TypeScript typecheck passed. ESLint passed with zero errors and one pre-existing unused `_signal` warning in `battle-transparency-preview.test.tsx:60`.
- Development and Public frontend production builds passed. Development route list contains `/debug` and `/assets`; Public route list excludes both. The Public artifact policy verified its output, and no `auto-actions`/Debug battle URL occurs in `web-ui/dist`.
- Python compilation of changed backend/new test modules and `git diff --check` passed.
- The broad backend suite initially exposed older fixtures that deliberately repeated player definitions plus order-dependent global app/registry test contamination. Test-only duplicate fixtures were migrated without weakening BUG-001; `tests/conftest.py` now restores app globals after mode-reload tests. The final explicit-Development full backend suite passed **746/746** with one existing Starlette/httpx deprecation warning.

### Browser layout evidence

In an isolated local Development browser at `http://10.0.0.137:3001/debug`, a new no-save 3v3 battle exercised status-icon hover/focus and target-preview focus. Rendered bounding rectangles (CSS px) were checked against each viewport, with no landscape document horizontal overflow:

| Mode / viewport | Right enemy status bounds | Target preview bounds |
| --- | --- | --- |
| monitor 1920×1080 | x 1619–1809, y 253–341 | x 991–1189, y 212–295 |
| monitor boundary 1600×900 | x 1353–1543, y 198–286 | x 818–1016, y 129–212 |
| laptop-large 1450×800 | x 1252–1442, y 158–246 | x 741–939, y 147–230 |
| laptop-medium 1280×720 | x 1065–1255, y 117–205 | x 633–831, y 101–184 |
| pad 1000×650 | x 802–992, y 94–182 | x 180–390, y 82–165 |
| pad-mini 800×600 | x 602–792, y 85–173 | x 146–356, y 82–165 |
| phone 650×400 | x 452–642, y 85–173 | x 121–331, y 82–165 |

At 800×600, keyboard focus on the left friendly Poisoned Dagger status produced a readable popup at x 8–198, y 99–173, with document width exactly 800. The 390×844 portrait mode showed the intended rotate-device guard; normal battle popup placement is not available there. Resize/orientation transitions were exercised across the matrix. The browser's screenshot capture timed out, so this evidence is live rendered DOM/accessible-state and bounding rectangles, not saved screenshots. Lower-edge long-content and zoom-specific checks were not independently captured; CSS constrains those paths, but the planned visual sign-off remains incomplete until they are checked before Batch E.

One early no-save Debug 1v1 attempt lost its ephemeral battle while local build/test work was still changing files and returned `battleNotFound`. After file changes stopped, a fresh browser battle confirmed Mage selection, Auto Battle enabled on a manual turn, one authoritative Mage Frost Bolt action, and successful disable while that action finished. The enemy completed its turn, Round 2 began, and the next Mage turn remained manual with the toggle unchecked. No save/progression data was involved. Automated tests separately cover revision, error, and Public-denial paths.

## Release-candidate and Production boundary

This is a **reviewed mutable worktree candidate**, not an immutable release: base HEAD is `230c00b9`, with uncommitted source/test/doc changes. No commit, tag, push, artifact hash, release ID, backup reference, or deployment was created or asserted. `RELEASE-004-<approved-short-commit>` remains only the plan's proposed identifier; the Owner must approve an immutable candidate and Batch E separately. The prior deployed release remains `RELEASE-003-db7f3395`. The installed Production battle capacity of 200 must be preserved, not treated as demonstrated capacity.

Before any Production operation, freeze/commit the reviewed candidate with Owner authorization, rebuild and hash Development/Public artifacts, recheck the final diff and schema compatibility, confirm backup and old-artifact recovery against the installed environment, and obtain Batch E's explicit maintenance/rollback approval. Nothing in this report authorizes Production access, deployment, database changes, or actual rollback.
