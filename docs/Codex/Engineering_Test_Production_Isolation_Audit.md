# Engineering Test & Debugging Production Isolation Audit

**Date:** 2026-11-10 (Australia/Sydney)
**Scope:** Read-only repository and existing local-build audit. No implementation, new build, deployment, install, or runtime penetration test was performed.
**Revision inspected:** `2f2d5003` (`UI_Battle_Instruction_Update`).
**Roles:** Core coordinated and wrote this report; `ui-developer` independently traced the frontend; `game-engine-developer` independently traced the FastAPI/engine boundary; `reviewer` performed an independent security/quality pass. PM and test-automator were omitted because this was one read-only audit, not a delivery or test-implementation project.
**Instructions reviewed:** Owner brief, `docs/Codex/Current_Task.md`, `Project_Rules.md`, and `Agent_Roles.md`; repository source and existing documentation were checked against them.

## 1. Executive Summary

**Confirmed:** Engineering Test is not production-isolated today. The App Router has an unconditional `/debug` page and the Stage Map always links to it (`web-ui/app/debug/page.tsx:1-10`; `web-ui/components/stages/StageSelectionScreen.tsx:90-97`). FastAPI always registers `POST /api/v1/debug/battles` (`battle_api/app.py:281-298`). A pre-existing, ignored local production-build artifact contains the `/debug` route and a `DebugBattleExperience` client chunk (`web-ui/dist/server/index.js:15729-15741`; `web-ui/dist/client/assets/DebugBattleExperience-BlPCbDGu.js`). Hiding the link alone would not prevent direct URL or HTTP access.

**Confirmed:** The debug experience is mostly isolated at its entry points. It reuses normal battle construction, legal commands, preview, and presentation without a debug-only branch in the Python combat engine (`web-ui/components/battle/DebugBattleExperience.tsx:37-85`; `battle_api/app.py:285-298,637-716`). Debug sessions have no stage/Arena/profile context and do not themselves update progression; the existing regression test verifies unchanged slots/profiles/Arena tables (`tests/test_ui023_arena.py:164-194`). No direct debug endpoint or UI control for HP, MP, cooldown, status, outcome, reward, or unlock manipulation was found.

**Recommendation:** Use one repository and explicit, fail-closed engineering/public-release configurations. The public frontend build must **omit** the `/debug` route module before route discovery, not merely hide it; omit `/assets` as well if the owner classifies that diagnostics page as engineering-only. The public backend must **not register** the debug battle route. Keep the shared engine, battle screen, provider, Team Builder, and progression logic. Verify both artifacts and direct URLs/HTTP before release. A larger combat or UI rewrite is not indicated by the inspected code. This isolation project is **Medium implementation risk** because frontend build routing, backend route registration, startup configuration, and deployment checks must agree.

**Important separate release concern:** The current adapter has no authentication or authorization and uses a shared active save-slot model (`battle_api/app.py:52-85,189-278`; `docs/Technical/Networking.md:95-102`). CORS is not HTTP authorization. Debug isolation alone does not make the entire public API safe for Internet exposure. Actual Google Compute Engine ingress, proxy, TLS, identity, and artifact deployment were not available for inspection.

## 2. Current Architecture Findings

| Boundary | Confirmed implementation | Isolation implication |
|---|---|---|
| Frontend routing | `web-ui/app/debug/page.tsx:1-10` statically imports `DebugBattleExperience`; `web-ui/app/assets/page.tsx:21-33` is another direct development route. | Both are filesystem routes, not subviews of normal game pages. Direct URLs work if built/served. |
| Stage navigation | `StageSelectionScreen.tsx:90-97` always renders an Engineering link. `web-ui/app/stages/page.tsx:13-18` gates only `debugHotspots`. | Removing the link is necessary for presentation, insufficient for isolation. |
| Debug client | `DebugBattleExperience.tsx:21-42,63-85` fetches the static full roster, supplies `TeamBuilder mode="debug"`, and sets the `LiveBattleProvider` create path to `/api/v1/debug/battles`. | The page/wrapper is a narrow exclusion point. Shared components are not disposable. |
| Backend | `battle_api/app.py:52,281-298` creates one FastAPI app and unconditionally decorates the debug POST route. | The route is present in routing/OpenAPI whenever this app is used; there is no production registration switch. |
| Engine/session | `battle_api/adapter.py:934` owns battle construction; `BattleRegistry` stores process-local sessions in `_sessions` (`adapter.py:4099-4149`). Shared command/preview routes are `app.py:637-716`. | Debug uses normal legality/combat; no engine fork is needed. Registry has no observed TTL/quota. |
| Persistence | Debug creation passes no progression identity (`app.py:285-298`); stage completion rejects a non-stage session (`app.py:741-747`). | Debug battle creation cannot directly commit training/Arena rewards, but an exposed route can allocate sessions. |
| Build/runtime | `web-ui/package.json:11-15` invokes vinext; `web-ui/vite.config.ts:36-58` installs vinext/sites/Cloudflare plugins with no release-route filter; `web-ui/next.config.ts:1-7` is empty. `Makefile:9-25` starts the same backend app and frontend source in local development. | No verified public-release flavor currently excludes Engineering. |

Documentation was checked against source, not treated as proof. `docs/Technical/Architecture.md:185-197` describes the separate debug creation boundary; `docs/web-ui/WEB_UI_ARCHITECTURE.md:82-87` describes the route; `docs/web-ui/BATTLE_DATA_CONTRACT_V1.md:116-151` describes the API. The current `docs/web-ui/Style_Guide.md:70-75` describes hotspot debugging as development-only, but that statement applies to the overlay, not the `/debug` route/link.

## 3. Engineering Test & Debugging Feature Inventory

“Current build” below means the inspected local source and existing ignored build artifact, **not** a verified public deployment. The shared API paths after debug creation are ordinary battle routes, not special mutation endpoints.

| Feature / purpose | Frontend and backend evidence; API | Shared dependency | Current-build status; exclusion boundary |
|---|---|---|---|
| Engineering Battle Lab page | `web-ui/app/debug/page.tsx:1-10`; `DebugBattleExperience.tsx:15-85`; `battle_api/app.py:281-298`; `POST /api/v1/debug/battles` | `TeamBuilder`, `BattleScreen`, `LiveBattleProvider`, roster, `BattleRegistry` | **Confirmed present** as `/debug`; omit page/wrapper from public build and un-register backend POST, without deleting shared combat. |
| Full-roster test team/enemy selection | `DebugBattleExperience.tsx:21-35,63-71`; `TeamBuilder.tsx:268-271,340-371`; `GET /api/v1/heroes` (`app.py:167-174`) and debug POST | Normal roster and Team Builder | **Confirmed** in debug UI. Debug supplies no unlocked-ID filter; preserve shared roster/Builder for normal use. |
| Battle size, formations, random/specified enemy, enemy player/computer, optional deterministic seed | `TeamBuilder.tsx:285,300-371,505-535`; `battle_api/models.py:346-376,449-452`; debug POST | Shared typed battle configuration and adapter | **Confirmed** debug controls. Some configuration/seed fields also exist outside Debug; do not assume route removal strips all such fields. |
| Ordinary debug battle actions/preview | `DebugBattleExperience.tsx:37-42,74-85`; `battle_api/app.py:637-716`; `GET /api/v1/battles/{id}`, `POST .../commands`, `POST .../preview` | Normal engine/adapter/session registry | **Confirmed**; keep these shared routes for normal battles. Debug creation should be impossible in public mode. |
| Stage Map Engineering navigation | `StageSelectionScreen.tsx:90-97` | Normal Stage Map | **Confirmed always rendered**; conditionally omit link in public, but also remove route/API. |
| Asset Registry diagnostics | `web-ui/app/assets/page.tsx:1-33`; route `/assets`, no special API | Shared `lib/battle/assets.ts`, `AssetImage` | **Confirmed direct development page**, present in existing local build (`web-ui/dist/server/index.js:15704`). Omit page, retain shared asset registry/renderer. |
| Stage hotspot geometry overlay | `web-ui/app/stages/page.tsx:13-18`; `StageSelectionScreen.tsx:130-138`; query `?debugHotspots=1` | Normal Stage Map geometry | **Confirmed conditional** on `NODE_ENV !== "production"`; standard production disables the overlay, but branch/CSS remain in source. Prefer explicit release flavor for consistency. |
| Battle viewport/config readout | `web-ui/components/battle/BattleScreen.tsx:691-695`; `web-ui/app/globals.css:221` | Shared Battle Screen | **Confirmed always rendered**, developer-facing but read-only. Decide whether public users may see it; production-hide if not. No combat authority is exposed by the display itself. |
| Mock fixture/event demo tools | `web-ui/components/battle/MockBattleScreen.tsx:1-20`, `web-ui/lib/battle/fixture.ts`, `BattleScreen.tsx:797-798,854` | Shared Battle Screen presentation branches | **Confirmed source modules**; no App Router route or non-test importer was found for `MockBattleScreen`. Public reachability was not demonstrated. Keep test fixtures unless artifact policy requires pruning. |
| Forced skills, direct HP/MP/cooldown/status edits, forced outcomes, progression/reward overrides | No matching Debug control or dedicated API route was found in `DebugBattleExperience.tsx`, `TeamBuilder.tsx`, or the route inventory in `battle_api/app.py:162-728`. | Normal engine contains legitimate forced-action/status logic | **Not found in this audited HTTP/UI surface**, not proof that no internal Python test helper exists. Do not describe ordinary `forced.scoff` engine actions as a developer override. |

## 4. Frontend Isolation Findings

The Stage Map link is always rendered (`StageSelectionScreen.tsx:90-97`) and `/debug` is a normal App Router page (`app/debug/page.tsx:1-10`). Direct navigation would remain possible after a link-only change. Likewise `/assets` is a direct route (`app/assets/page.tsx:21-33`). No middleware, auth, environment guard, or route-pruning build setting was found in the current frontend entry/config (`app/layout.tsx`, `next.config.ts:1-7`, `vite.config.ts:36-58`, `package.json:11-15`).

**Build evidence, with limitation:** An existing ignored local vinext production artifact dated 2026-11-09 contains `/debug` and `/assets` route entries (`web-ui/dist/server/index.js:15704,15729-15741`) and a `DebugBattleExperience` client chunk (`web-ui/dist/client/assets/DebugBattleExperience-BlPCbDGu.js`). This is direct evidence of current build behavior. It is not evidence of what is deployed publicly, and no fresh build was run for this audit.

Normal `BattleExperience` does not import `DebugBattleExperience`; Debug imports the shared `TeamBuilder`, `BattleScreen`, and `LiveBattleProvider` (`DebugBattleExperience.tsx:3-8`). These shared modules also serve public stage/Arena flows (`BattleExperience.tsx:51-58`; `ArenaRunExperience.tsx`), so removing them would break gameplay. Dormant debug-specific conditionals in shared `TeamBuilder` and mock presentation code are not, by themselves, callable developer privileges once the route and backend creation boundary are absent. If policy requires *zero* debug strings in any client chunk, that stricter artifact requirement needs a separate bundle audit and perhaps a later local split; it is not necessary to block access to Debug.

**Least invasive public-build method:** Use an explicit, fail-closed release flavor in the build pipeline that removes `app/debug/` and `app/assets/` from a **disposable staging copy** before vinext filesystem-route discovery, or first prove a supported vinext route-exclusion hook with equivalent verified output. Keep the working source and local development build intact. A runtime `notFound()`, client-side flag, hidden link, or `NODE_ENV=production` conditional is insufficient for the owner's stricter requirement that Engineering pages not be included in the public artifact. The production artifact check must confirm both route absence and no debug page/client chunk. Gate the Stage Map link using a server-supplied release-mode value; do not treat a `NEXT_PUBLIC_*` value as security authority.

The release build must still render `/`, `/stages`, `/game`, the Manual, Hero Gallery, normal Team Builder, Arena Run, and Battle UI. Validate initial server render and client navigation so link gating causes no hydration mismatch. The exact frontend hosting pipeline for Google Compute Engine was not present in inspected source; the current Vite config includes a Cloudflare plugin, so do not assume the eventual frontend runtime from backend GCE plans alone.

## 5. Backend Isolation Findings

`POST /api/v1/debug/battles` is an unconditional FastAPI decorator in `battle_api/app.py:281-298`. The `CreateDebugBattleRequest` inherits ordinary creation fields but rejects extra hidden fields (`battle_api/models.py:346-376,449-452`). It forwards user-selected roster, enemy, formation, and seed to `BattleRegistry.create` without calling progression access checks. Normal generic creation checks the active profile's unlocked player team (`app.py:508-542`); stage and Arena creation have separate server-owned access/formation logic (`app.py:375-405,554-606`). Thus the debug route is a real roster-gating bypass for **non-persistent test sessions**, not a direct reward bypass.

Once created, a debug battle uses the same process-local registry, legal command pipeline, and preview as ordinary sessions (`app.py:637-716`; `adapter.py:4099-4149`). No separate debug-only damage/status formula or engine mutation switch was found. Stage completion rejects sessions lacking stage context (`app.py:741-747`), and the existing test checks that debug creation does not alter slots, profiles, or Arena runs (`tests/test_ui023_arena.py:164-194`). `BattleRegistry._sessions` has no observed expiry or quota (`adapter.py:4102-4149`), so an unauthenticated exposed debug POST creates an availability risk even without reward writes.

The FastAPI app has no route-level authentication dependency and uses default documentation/OpenAPI registration (`app.py:52,281-298`); a test explicitly asserts the debug path appears in OpenAPI (`tests/test_ui023_arena.py:380-385`). CORS only limits permitted browser origins (`app.py:54-77`), not curl or direct HTTP requests. A browser-hidden debug page cannot protect the API. The production route should be registered only under an explicit server-private engineering enablement setting that defaults **off**. A small dedicated debug `APIRouter` conditionally included at app startup is one clear approach; a similarly conditional `add_api_route` is acceptable. Disabled mode must yield 404 and omit the path from OpenAPI. Local development startup must explicitly enable it so the current lab remains usable. Neither route registration nor this flag should be controlled by request parameters.

**Related but distinct request-surface issue:** The normal generic battle endpoint forwards a client `seed` (`app.py:531-541`; `models.py:346-376`), and stage creation accepts optional client `seed` (`models.py:860-869`; `app.py:593-606`). Arena node launch instead draws server entropy (`app.py:393-405`). Client seed support does not disable legal targeting or directly award rewards, but a manually constructed stage request can make combat randomness predictable. Whether public release must reject client seeds is a product-integrity decision separate from removing Engineering. The public generic `/api/v1/battles` route also offers free-form battles to callers with an active unlocked team; it does not itself have stage/Arena completion context. Decide whether it is a supported public mode or a legacy/development route before conditionally removing it.

## 6. Shared Dependencies and Coupling

| Dependency | Evidence | Disposition |
|---|---|---|
| `TeamBuilder`, `BattleScreen`, `LiveBattleProvider`, typed battle config | Debug wrapper imports these (`DebugBattleExperience.tsx:3-8`); normal Battle/Arena also uses them (`BattleExperience.tsx:51-58`, `ArenaRunExperience.tsx`). | **Preserve shared runtime.** Remove only Engineering route/wrapper from public artifact. Do not duplicate or fork combat UI. |
| `GET /api/v1/heroes` and hero/skill/asset registries | Debug fetches full roster (`DebugBattleExperience.tsx:21-35`); normal Gallery and battle UI use catalogues. | **Preserve shared runtime.** Full roster visibility is not the same as unlocked roster use. |
| `BattleRegistry`, `BattleAdapter`, `Game`/`Hero`/`Skill` | Debug and ordinary creation call the same registry/adapter (`app.py:285-298,531-541`; `adapter.py:4099-4149`). | **Preserve shared runtime.** Isolate route registration; no combat engine change indicated. |
| SQLite progression store | Global store constructed in `app.py:80-85`; debug route does not call it. | **Preserve**, while separately addressing public identity/auth risks. |
| Asset registry page | `app/assets/page.tsx:1-33` imports production asset metadata/rendering. | Exclude **page only**; preserve `lib/battle/assets.ts` and `AssetImage`. |
| Stage hotspot overlay and viewport readout | `app/stages/page.tsx:13-18`; `BattleScreen.tsx:691-695`. | Overlay behind explicit engineering release boundary; classify readout as safe diagnostics or hide in public. No engine changes. |

## 7. Security and Production Exposure Risks

1. **Confirmed application exposure, public ingress unverified:** Source and local build include `/debug`; FastAPI registers debug POST. If those artifacts/app are exposed on the Internet, direct URL and manual HTTP access work regardless of a hidden navigation button. Actual deployed hosts, firewall, and reverse-proxy rules were not inspected.
2. **High current abuse potential if publicly reachable:** No API authentication, default OpenAPI discoverability, and unbounded process-local session creation permit arbitrary debug session allocation (`app.py:52,281-298`; `adapter.py:4099-4149`; `docs/Technical/Networking.md:95-102`). This is an availability and rule-access risk; it is not evidence of direct progression corruption.
3. **Shared active save state is a separate release blocker:** Save-slot create/load/overwrite and progression APIs are global, unauthenticated operations (`app.py:189-278`; `docs/Technical/Architecture.md:229-235`). Engineering isolation does not solve player identity, account isolation, or public persistence safety. Authentication/authorization/transport and abuse controls require an owner-approved release plan.
4. **Deterministic request inputs:** Optional stage/generic seeds and the generic free-form creation endpoint merit a production policy review, even with debug POST removed (`app.py:508-606`). Do not claim they are debug-only or currently bypass legal action checks.
5. **CORS is not authorization:** Exact-origin CORS and `NEXT_PUBLIC_BATTLE_API_URL` affect browser connectivity/configuration, not whether a direct HTTP client can call routes (`app.py:54-77`; `docs/web-ui/WEB_UI_ARCHITECTURE.md:542-552`). Public TLS, ingress, and API identity remain unverified.

Safe production diagnostics should remain: `GET /api/v1/health` (`app.py:162-164`), server-side error logging, and externally configured monitoring. Removing these is not part of this proposal. Public docs/OpenAPI exposure is a separate policy choice; disabling docs alone would not disable a route.

## 8. Recommended Isolation Architecture

Use one source repository with **two explicit build/start modes** and fail-closed public defaults:

1. **Frontend engineering mode:** existing local `npm run dev` retains `/debug`, `/assets`, Engineering link, hotspot tuning, and no-save battle lab. Normal game pages remain shared.
2. **Frontend public-release mode:** route discovery runs against a controlled staged source tree without `app/debug/` and `app/assets/`. Render no Stage Engineering link; turn off hotspot geometry; hide the viewport diagnostic if owner classifies it as engineering-only. Validate artifact route manifest and chunks, then deploy only that artifact. A verified native vinext exclusion mechanism can replace staging; none is established by this audit.
3. **Backend engineering mode:** explicitly register the debug route while preserving its full-roster/no-save behavior and ordinary action pipeline.
4. **Backend public mode:** do not register debug route, even if a caller manually sends the old POST. Do not rely on frontend gating or CORS. Leave health, catalogues, stage/Arena creation, legal actions, preview, and progression behavior intact pending broader security decisions.
5. **Release gate:** treat frontend build flavor and backend engineering enablement as separately asserted deployment inputs. A public artifact must fail validation if either debug surface remains. Google Compute Engine deployment instructions must explicitly select the backend mode and the vetted frontend artifact. A permanent release branch is unnecessary.

## 9. Required Code Changes (File-by-File)

These are **proposals only**; no changes were made by this audit.

| File/module | Minimum proposed later change | Why / guard |
|---|---|---|
| `web-ui/app/debug/page.tsx`, `web-ui/app/assets/page.tsx` | Omit from public build input; retain in engineering source/build. | Filesystem route absence, not a runtime `notFound()` page, satisfies the strict artifact requirement. |
| `web-ui/components/stages/StageSelectionScreen.tsx` and `web-ui/app/stages/page.tsx` | Supply a server-derived release mode and omit Engineering link/hotspot overlay publicly. | Hiding link is presentation defense-in-depth; direct route must also be absent. Avoid client/server mismatch. |
| `web-ui/components/battle/BattleScreen.tsx` | Only if owner chooses: suppress viewport/config readout publicly. | Developer-facing display is currently always visible, but not an authority bypass. |
| `web-ui/package.json`, `web-ui/vite.config.ts`, and/or new release-build script/staging configuration | Introduce explicit build flavor and route-exclusion staging; assert the artifact. Keep local dev command unchanged. | No verified existing exclusion setting; do not hand-edit `dist/` or modify the source worktree destructively during a build. |
| `battle_api/app.py` and a small `battle_api/debug_routes.py` (or equivalent) | Move/conditionally register only debug POST under a server-private, default-off setting. | Public routing and OpenAPI must omit it; shared endpoints remain. |
| `Makefile` and future GCE startup/deploy configuration | Explicitly enable engineering route for local dev targets; explicitly disable for public backend and deploy the public frontend artifact. | Keep the local lab available without fail-open public defaults. Direct manual `uvicorn` users would need the documented engineering flag. |
| Focused frontend/backend/deployment tests | Assert both build flavors, link/direct-route behavior, disabled OpenAPI/HTTP debug path, enabled no-save test battle, and normal gameplay smoke paths. | Prevent release-flavor drift or accidental re-exposure. |
| `battle_api/models.py`, `battle_api/app.py` normal creation paths | **Conditional on owner policy:** reject public client seeds and decide fate of generic free-form `/api/v1/battles`. | Separate integrity policy; do not silently change contracts under debug isolation. |
| `battle_api/adapter.py`, `battle_api/progression.py`, `game/`, hero/skill classes | **No isolation change recommended.** | Shared authoritative rules/persistence are not debug-only modules. |

## 10. Implementation Risk Assessment

**Overall: Medium.** Frontend route omission and Stage link gating are localized; backend route registration is localized; no engine/persistence structural change is required. The risk rises above Low because the release build, backend startup, and deployment must agree, and build artifacts must be tested rather than inferred from `NODE_ENV`.

| Risk area | Assessment | Regression concern |
|---|---|---|
| Shared game logic | Low if preserved | Deleting `TeamBuilder`, `BattleScreen`, provider, assets, or adapter would break normal play; do not do so. |
| Public frontend artifact | Medium | File-based route discovery may still bundle excluded page modules unless the release artifact is inspected. A stale `dist/` could be deployed accidentally. |
| Backend route/config | Medium | A fail-open default or wrong startup command could leave debug POST registered; enabled local dev must still work. |
| Existing player data | Low for the proposed isolation | Debug route does not write progression; broader unauthenticated save APIs are a separate high-impact public-release concern. |
| GCE deployment | Unverified | No committed frontend packaging, reverse-proxy, TLS, firewall, or production startup specification was found. Real deployment behavior requires environment verification. |

No numerical effort estimate is justified by repository evidence. The main architectural blocker is **not** engine coupling; it is the absent, verified public-release build/deploy boundary and unresolved public API identity/security policy.

## 11. Proposed Implementation Phases

1. **Approve production policy.** Confirm whether `/assets`, viewport readout, generic free-form battles, and client seed support are engineering-only; define public API identity/ingress separately. No code change until this is explicit.
2. **Frontend artifact boundary.** Add a fail-closed public build flavor using a disposable staging source tree or a verified vinext exclusion mechanism. Omit `/debug` and `/assets`; gate Stage link/overlay; assert route/chunk absence. Keep engineering dev build unchanged.
3. **Backend route boundary.** Register debug POST only in explicit engineering mode. Update local startup so the full-roster lab still works. Keep engine, ordinary battle endpoints, and progression untouched.
4. **Integrity decisions, if approved.** Apply any separate public seed/generic-route policy with contract tests. Do not smuggle this into the route-isolation patch.
5. **Deployment and verification.** On the intended Google Compute Engine topology, deploy only the public artifact and production backend mode. Verify direct URLs, OpenAPI, HTTP POST rejection, normal gameplay, CORS/origin, TLS/ingress, and rollback. Keep safe health/log monitoring.

Each phase has an independently checkable result. No separate permanent release branch or large combat refactor is recommended.

## 12. Verification and Regression Test Plan

No tests or builds were run during this read-only audit. The following are **future implementation gates**:

- **Public frontend:** inspect compiled route manifest/server bundle for absence of `/debug` and `/assets`; inspect client chunks for no `DebugBattleExperience`; verify Stage Map has no Engineering link on server render or client navigation; direct GET `/debug` and `/assets` return 404; hotspot query is inert; retained public screens (`/`, `/stages`, `/game`, Manual/Gallery) load normally. Test missing/invalid build flavor fails closed.
- **Engineering frontend:** `/debug`, `/assets`, Stage link, and hotspot geometry remain usable. Full-roster team/enemy selection, seed, and normal test battle completion/resign still work.
- **Public backend:** debug POST returns 404 and is absent from OpenAPI under a manually constructed request; health, roster, formation catalogue, save/progression, stage/Arena, legal command, preview, and completion routes remain available. Confirm no debug route can be enabled by client payload/query/header.
- **Engineering backend:** debug POST accepts full-roster legal test configurations and remains save/progression neutral; ordinary validation and illegal-command rejection still apply.
- **Cross-boundary:** run a public 1v1/2v2/3v3 and structured/Arena smoke pass, including a stage victory commit, while independently checking no debug route. Use isolated test data; do not test against real player saves.
- **Security/deployment:** inspect GCE process env, proxy/firewall, exact frontend artifact, public DNS/TLS, CORS origin, and API auth/abuse controls. If client seeds remain, document the integrity policy and test it explicitly. Verify safe health/log diagnostics remain.

## 13. Open Questions and Unverified Assumptions

1. **No public deployment was inspected.** The repository and local ignored build prove application/build inclusion, not live Internet reachability. GCE service definitions, reverse proxy, TLS, firewall, startup env, frontend hosting/runtime, and rollback procedure were not found in committed project configuration.
2. **Frontend route-pruning mechanism is not proven.** Current vinext/Vite config has no route filter. A disposable staged source copy is the most concrete recommendation; a native hook may exist but must be demonstrated by an actual public build before adoption.
3. **Authentication and save ownership are unresolved.** The current API and five-slot model are documented as unauthenticated shared development state (`docs/Technical/Networking.md:95-102`; `docs/Technical/Architecture.md:229-235`). Owner direction is required before an Internet-facing release with player persistence.
4. **Generic battle and seed policy needs owner direction.** The current frontend Stage Map appears to use Arena Run or structured flows (`BattleExperience.tsx:51-58`), while `POST /api/v1/battles` and optional stage seed remain published. Their intended public product status must be confirmed before changing either contract.
5. **Developer diagnostics classification:** Decide whether `/assets` and the viewport readout must be excluded/hidden; the former is explicitly labelled a development route, the latter is read-only but always visible. The hotspot overlay is already gated in standard production by `NODE_ENV`, though an explicit engineering flavor would be clearer.
6. **No runtime abuse test was performed.** Registry capacity, session expiry, rate limits, and real proxy controls were not measured. No direct HP/MP/cooldown/status/outcome setter was found in the audited API/UI route surface, but this is not a formal proof about every internal Python test helper.

## 14. Final Recommendation

**A. Can Engineering Test and Debugging be excluded from the Production Build without a major frontend refactor?** **Yes.** The public pages are localized at `/debug` and `/assets`; their shared UI dependencies must stay. Strict exclusion requires a verified route-pruned public artifact, not just a hidden link or runtime 404.

**B. Can backend debugging capabilities be disabled/excluded without changing the core Python battle engine?** **Yes.** Conditionally register the dedicated debug creation route. Normal legal command/preview processing and combat engine remain shared and unchanged.

**C. What is the minimum set of changes required?** Add one fail-closed public frontend build flavor that omits Engineering pages, hide the Stage link/overlay, conditionally register debug POST behind a server-private default-off setting, explicitly enable it in local development, and add artifact/API/direct-access regression gates. A production diagnostic/readout and seed/generic-battle policy require explicit owner decisions; they should not be silently changed.

**D. Overall implementation risk?** **Medium** for isolation. The current **security exposure if the existing app/API were publicly reachable is high** because the debug route is unauthenticated and sessions are unbounded; implementation risk and present exposure are different measures.

**E. Proceed minimally or refactor?** **Proceed with minimal-invasive isolation.** No larger frontend, engine, or persistence refactor is technically required for the Engineering boundary. Do **not** equate this with overall public-release readiness: authentication/slot ownership, transport/ingress, abuse controls, and the public seed policy still need separate approval and verification before Internet exposure.
