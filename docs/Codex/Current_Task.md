# Current Task

**Status:** Completed

**Completed:** 2026-10-28. All five roles participated in coordinated waves;
the independent reviewer approved after its dynamic-curriculum decoder finding
was fixed. Final relevant backend tests: 214 passed; frontend tests: 69 passed;
typecheck, lint (0 errors), production build, Python compilation, and diff
check passed. Locked/unlocked campaign and 720×650 browser paths were checked
against an isolated temporary save. Full evidence and the unrelated stale
background-test limitation are recorded in `docs/Codex/Completed.md`. No
commit or push was performed.

**Task:** MODE-001 — Learner and Tactics Modes for Structured Campaign Battles

**Owner request date:** 2026-10-27

## Objective

Introduce **Learner** and **Tactics** modes for the current structured campaigns, Warrior's Barrack and Paladin's Altar, and the shared structured-campaign path for future campaigns. Both modes use identical heroes, starting-stat generation, skills, damage/status/cooldown rules, enemy formations, and player team restrictions. Only the computer enemy's decision policy changes: Learner chooses randomly among legal actions/targets; Tactics retains the existing hero-specific strategic AI unchanged.

Learner is available and selected by default for a new save. Each campaign unlocks its own Tactics mode after that campaign's required Learner battles are complete. Unlocked Tactics battles may be entered in any order. Keep mode-specific completion records for future badges without implementing badges now.

## Current State and Scope Boundary

The previous task, UI-033, is **Completed** in `Current_Task.md` and `Completed.md`; it is not being overwritten while active. `battle_api/progression.py` currently has two authoritative `STAGE_BATTLES` curricula, profile-scoped SQLite `stage_progress`, completion receipts, and five existing hero unlock rewards. Stage access and `GET /api/v1/stages` currently use one sequential progress path. The stage creation route in `battle_api/app.py` creates a fixed computer enemy and stores stage/profile context; the completion route calls `commit_victory` for every friendly stage victory. `battle_api/adapter.py::_drain_automatic_turns` currently calls `actor.ai_choose_skill`/`ai_choose_target`, reconciles to `_legal_actions` and `_valid_target_ids`, and uses random fallback for invalid strategy output. `TeamBuilder.tsx` has a structured variant and a bottom footer with Enter Battle on the right; `BattleExperience.tsx` owns stage selection, launch, and completion. The attached owner screenshot marks the empty **bottom-left of that footer** for the new selector.

For this task, “campaign” means the backend-registered structured-stage curricula. **Arena Run and Engineering Test & Debugging are separate flows and retain their existing AI/default behavior and UI**; do not accidentally switch them to Learner. The normal generic battle API must remain backward-compatible. Preserve all unrelated uncommitted work.

## Pre-code Gate and Architectural Risks

**Core gate (2026-10-27, before implementation):** High-risk backend/UI/save
contract change; all five configured roles are selected for coordinated
dispatch: PM (sequence/contracts), engine developer (authority and
persistence), UI developer (typed structured flow/selector), test automator
(cross-boundary regression), reviewer (independent final gate). No role is
omitted. Sequence: (1) add a typed, session-bound mode and profile-scoped
campaign access/completion with existing stage rows interpreted as Learner;
(2) branch only the enemy computer decision policy at the adapter's legal
action boundary, using session RNG and preserving Tactics' existing path;
(3) consume server mode availability in structured Team Builder and bind mode
to launch/return/attempt identity; (4) validate migration, legality, rewards,
API security, UI accessibility, and unchanged Arena/Debug before review.
Risks/decisions: no client-derived unlocks, no stat/formula fork, no universal
campaign length; mode is immutable after stage launch and completion reads the
session, while Learner remains the compatibility default for legacy stage
create requests. Existing dirty files are preserved; no commit/push.

Before implementation edits, Core should write a **concise** implementation sequence and risk decisions in this task record: (1) mode field, stage access, save migration/completion ownership; (2) AI policy boundary and legal fallback; (3) selector/launch/return flow; (4) focused validation. No separate lengthy study or owner approval wait is required unless a real design ambiguity blocks safe implementation.

Key risks to resolve explicitly:

- The current adapter mixes hero-strategy selection with legality repair. Learner must skip the hero-specific strategy entirely and sample from the **already-authoritative legal actions and valid target IDs**, with the required distinct target count; forced turns, skips, casting, summons, and no-action cases must keep a legal resolution path. Do not introduce a client-side combat rule. Apply Learner to computer-controlled **enemy** decisions, not friendly auto-controlled summons or other player-side automatic behavior.
- The current stage/progression contract is sequential. Tactics needs campaign-scoped unlock and nonsequential per-battle completion, while Learner retains sequential access and all current rewards. Use the actual `STAGE_BATTLES[stage_id]` required set/count, not a new universal “nine battles” constant. Existing completed stage records represent Learner history and should unlock Tactics on migration/read without replay or data loss.
- A mode must be bound to the stage battle session/profile and included in the process-local `attemptId` fingerprint. A transport retry reuses the same mode/session; the same attempt ID cannot silently return or create a different mode. The completion route must use the **server session's mode**, not a mode supplied at completion time.
- `TeamBuilder` remounts when the selected stage battle changes. Keep the selected mode stable while navigating battles within a campaign entry, but default to Learner on entering a new campaign/save context. Do not let a stale UI state launch a locked Tactics battle.

## Requirements

### AI and shared combat rules

1. Add a shared authoritative decision-policy boundary at the adapter/engine layer without duplicating the battle engine. In Learner, randomly select one currently legal skill action and, where required, a legal distinct target set of the exact published cardinality from that action's `validTargetIds` (including 0-target and multi-target skills). Use the session's isolated RNG. Do not optimize skill choice, heal targets, status combinations, or tactical priorities. Honor all existing cooldown, availability, target, forced-action, and control restrictions. If no ordinary action is legal, audit and use the existing lawful skip/fallback path; never fabricate an illegal command.
2. Tactics must run the present hero-specific strategy and its existing legality reconciliation unchanged. Do not rewrite or rebalance those hero strategies. Preserve initial stat generation and all combat formulas/rules in both modes. With the same seed/configuration, mode selection itself must not alter hero construction or stats before AI decisions; divergent decisions/results afterward are expected. Preserve established fresh per-attempt randomness and explicit seeded debug/test reproducibility.
3. Preserve the selected stage mode immutably for the whole session, including opening automatic turns, later turns, completion, and retries. Generic, Arena, and Debug creation retain their existing behavior unless a narrow compatibility field is required; do not expose an unlocked Tactics bypass via another route.

### Campaign progression and persistence

4. New save slots expose Learner as available/default and Tactics as locked **per campaign**. Completing every required battle in one campaign's Learner progression unlocks only that campaign's Tactics. Learner remains playable afterward. In an unlocked Tactics campaign, any listed battle may launch in any order, while Learner remains sequential. Backend stage access and stage-list/progression responses must publish/validate mode-specific availability; React must not infer unlock authority from a local counter.
5. Extend the profile-scoped SQLite save system with durable mode unlock/completion state and safe migration/backward-compatible handling for existing schema versions and save slots. Existing stage completion is Learner completion. Completed legacy campaigns must gain Tactics access without altering their hero/reward records; incomplete ones remain locked. New slot creation/overwrite, reload, and switching slots must preserve isolation. Do not hardcode one campaign's completion count into new mode logic.
6. On authoritative friendly Learner victory, retain exactly the current sequential progress, hero unlocks, item-card reward, once-only grants, and profile-switch protection. A Tactics friendly victory records only that campaign/battle's Tactics completion, safely and idempotently, without increasing Learner progress or granting/duplicating hero or item rewards. Defeat, draw, resign, repeated completion, transport retry, and slot switch must not grant or leak progress. Persist enough stage/battle/profile/mode completion identity for later badge work, but do not implement badges. Priest Discipline remains without an unlock route; Hero Gallery and existing hero ownership rules remain unchanged.

### Typed API and UI

7. Add a typed `learner`/`tactics` mode field to the structured-stage battle-create request and immutable server session. Validate unknown values and locked Tactics launches server-side, including manipulated requests. Provide a safe Learner default for omitted mode on legacy **structured-stage** callers; do not let a default bypass Tactics authorization. Expose typed campaign-specific mode availability/completion to the frontend through the existing authoritative progression/stage response, and update strict client decoding/contracts. Bind mode into the attempt fingerprint and authoritative completion path; retain compatible 1v1/2v2/3v3 launch and fixed enemy configuration.
8. In the **structured Team Builder footer only**, place a compact horizontal `[ Learner ] [ Tactics ]` segmented selector at the screenshot's bottom-left, with Enter Battle remaining on the right. Use dark charcoal/near-black, thin muted gold/bronze edge, subtle premium fantasy treatment, compact typography, a small book icon for Learner and crossed swords for Tactics. Selected mode is clearly gold. A locked Tactics option has a small lock, muted disabled styling, and cannot select or launch. Use accessible radio/segmented semantics, focus and keyboard/touch behavior, and clear selected/locked state without relying only on colour. No descriptions, tooltips, instructional text, confirmation dialogs, or additional modes. Keep the two options and footer usable on the project's responsive sizes without disturbing hero assignment, formation, validation, stage selection, or Enter Battle.
9. When Tactics is selected and unlocked, stage battle selection offers **every** battle in that campaign regardless of Learner sequence; Learner keeps its existing access and completion display. Carry the selected mode through the existing Team Builder → battle provider → stage-create API path; switching mode or battle before launch must not create a session. On return from a battle, preserve a coherent mode/selection state and never mislabel Tactics completion as a Learner reward. Do not display a new reward screen for Tactics.

## Out of Scope

- Stat/HP/resistance/skill/damage/cooldown/formation balance changes, AI strategy rewrites, hero-unlock changes, or a new Priest Discipline reward.
- Arena/Debug mode selectors or difficulty changes; Hero Gallery changes; additional difficulty tiers.
- Badge art, inventory, badge reward grants/screens, or unrelated progression systems.
- Commits, pushes, or PRs without a separate explicit owner request.

## Relevant Files and Documentation

- Engine/AI: `battle_api/adapter.py` (`BattleSession`, `_drain_automatic_turns`, `_legal_actions`, `_valid_target_ids`), approved hero strategy methods under `heroes/`, and existing seeded AI/formation tests.
- Campaign/API/save: `battle_api/progression.py` (`STAGE_BATTLES`, migration, access, `commit_victory`, stage response), `battle_api/app.py` (stage create/completion and route boundaries), `battle_api/models.py`, `battle_api/attempts.py`, and focused progression/migration/API tests.
- Client: `web-ui/components/battle/TeamBuilder.tsx`, `BattleExperience.tsx`, `web-ui/lib/battle/types.ts`, `liveProvider.ts`, `web-ui/app/globals.css`, and focused Team Builder/structured-stage tests. Attached screenshot is placement reference, not a source of game rules.
- Stable docs to reconcile: `docs/GDD/Hero_System.md`, `Skill_System.md`, `Game_Design_Document.md` (as affected); `docs/Technical/Architecture.md`, `Player_Data_and_Save_System.md`; `docs/web-ui/WEB_UI_ARCHITECTURE.md`, `Style_Guide.md`, `Screen_Flow.md`, `BATTLE_DATA_CONTRACT_V1.md`, `PYTHON_ADAPTER_API.md`. Completion evidence belongs in `docs/Codex/Completed.md` and this task's status.

## Acceptance and Validation

- New and migrated saves have correct campaign-specific Learner/Tactics access; Tactics unlocks only after the corresponding Learner curriculum, persists across restart, and never leaks across slots. Direct API attempts at locked Tactics and invalid modes are rejected. Any-order Tactics selection works; Learner remains sequential.
- Learner choices are random among only authoritative legal actions/targets, including no-target and multi-target actions, and cannot produce an invalid command. Forced/skip/no-action cases remain lawful. Tactics seeded action/target behavior matches its pre-change path. Both modes share all combat data and rules; no difficulty stat modifiers appear.
- Learner victory grants existing rewards once. Tactics victory records its own mode/battle completion once and grants no Learner progress, hero unlock, item card, or badge. Defeat/draw/resign/duplicate completion and profile switch behave safely. Attempt-ID retries cannot cross modes.
- Structured footer matches the marked bottom-left area and stays responsive; locked Tactics is visibly disabled, accessible, and non-selectable; unlocked switching is exclusive and sent to backend. Arena/Debug remain unchanged.
- Test new-save defaults, legacy migration and completed/incomplete profiles, both campaign unlock paths, save isolation/reload/overwrite, direct-route security, mode-bound retries/session/completion, randomized legal targeting and strategic parity, unchanged stat/formula/hero rewards, and UI pointer/touch/keyboard/responsive flows. Run relevant backend/frontend regressions, typecheck, lint, production build, and diff check. Use a concise browser walkthrough for one locked and one unlocked campaign if feasible; report unavailable cases honestly. Avoid unrelated full-suite repetition.

## Complexity and Agent Assignments

**Assessment:** High-risk cross-system feature affecting AI legality, profile migrations/rewards, API security, and campaign UI. All five configured roles have concrete ownership, with coordinated waves if concurrency is limited.

- **project-manager:** Own brief pre-code sequence/risk gate and cross-boundary contract decision, track mode/progression/attempt invariants and agent dispatch, coordinate final documentation and completion record.
- **game-engine-developer:** Own policy branching, mode-bound session/API authority, stage access/save migration/completion isolation, and focused backend tests; preserve Tactics strategy and all combat rules.
- **ui-developer:** Own mode selector and mode-aware structured-stage flow, typed provider consumption, responsive/accessibility behavior, and focused frontend checks; no client AI or unlock calculation.
- **test-automator:** Own targeted cross-boundary seeded/legal-AI, persistence/migration/profile/reward/security, and UI integration regressions without duplicating specialist unit tests.
- **reviewer:** Independently inspect fairness/parity, legal fallback, migration and reward safety, mode-locked API, attempt identity, UI accessibility, and validation evidence; actionable findings only.

Core should report one concise completion result or a genuine owner-decision blocker. Do not send routine internal progress across chats, and do not commit or push without explicit owner instruction.
