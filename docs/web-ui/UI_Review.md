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
