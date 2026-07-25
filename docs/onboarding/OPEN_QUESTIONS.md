# Open Questions

These questions could not be answered confidently from commit `f88fbb92`. Each
entry distinguishes inspected evidence from what remains unknown.

## Product and rules

### 1. Which checked-in behaviors are canonical game rules?

- **Why it matters:** Architecture and tests cannot preserve intended behavior
  without separating rules from prototype accidents.
- **Evidence inspected:** All active hero/skill/status modules; release notes;
  `Developer_Note/Game_Quick_Notes.txt`; recent Git log.
- **Unclear:** The note explicitly names unresolved Flesh Puppet/Stitch of
  Agony/Void Rambler issues, while many debug comments and special cases remain.
- **Best owner:** Repository owner and designer.

### 2. What exactly should happen at the round limit?

- **Why it matters:** It defines battle outcomes and simulator rankings.
- **Evidence inspected:** `Game.round_counter_max = 15`,
  `end_round()`, and `game_over()` (`game/game.py:32-33, 337-359`).
- **Unclear:** Whether round 14 being the final action round is intended, and
  whether surviving teams at the cap should always draw or use a tiebreak.
- **Best owner:** Designer.

### 3. Are all listed specializations meant to be playable now?

- **Why it matters:** Generator and simulator coverage differs from implemented
  classes.
- **Evidence inspected:** `heroes/__init__.py`, all hero modules,
  `HeroGenerator.hero_classes`, and all three simulator profession lists.
- **Unclear:** `Necromancer_Flesh_Puppeteer` exists but is absent from the
  generator and simulators; `Necromancer_Bone_Master` is in the generator but
  absent from simulator lists. Several icon variants are also not loaded.
- **Best owner:** Repository owner/designer.

### 4. Is equipment a planned near-term system?

- **Why it matters:** The onboarding request mentions equipment, but it affects
  stats/data boundaries if expected.
- **Evidence inspected:** Full text/code search and all data columns.
- **Unclear:** No equipment, item, inventory, or equippable object model was
  found. Weapon/armor wording only occurs in skill mechanics and messages.
- **Best owner:** Designer.

## Battle semantics

### 5. Is round-start the intended timing for every status tick and casting completion?

- **Why it matters:** Ordering determines deaths, cooldown availability, and
  agility order.
- **Evidence inspected:** `Game.start_round()` and the complete
  `StatusEffectManager.check_heroes_status_effects()` dispatcher.
- **Unclear:** Whether every effect should resolve before defeat cleanup and
  action sorting, especially newly created summons and delayed casts.
- **Best owner:** Designer and tester.

### 6. What are the exact duration semantics?

- **Why it matters:** Comments such as “lasts for 2 rounds” often assign
  duration 3, relying on round-start decrement behavior.
- **Evidence inspected:** Skill application sites and status expiry branches
  across hero modules and `game/status_effect_manager.py`.
- **Unclear:** Whether the current off-by-one conventions are intentional for
  effects applied before versus after a round-start tick.
- **Best owner:** Designer/tester.

### 7. Should a newly summoned unit always act in the summoning round?

- **Why it matters:** It materially changes summon power and action-queue
  invariants.
- **Evidence inspected:** Summon methods append to
  `game.unactioned_sorted_heroes`; `Game.hero_action()` re-sorts that queue.
  Developer notes say a bug was fixed so summons act in the same round.
- **Unclear:** Whether this applies universally, including summons created by
  future effects outside a normal turn.
- **Best owner:** Designer.

### 8. What is the intended behavior when agility ties?

- **Why it matters:** Python's stable sort preserves list insertion order, which
  currently favors the original team/list ordering.
- **Evidence inspected:** `Game.start_round()` and `hero_action()` sorting
  (`game/game.py:245-250, 331-333`).
- **Unclear:** Whether ties should preserve roster order, randomize, alternate,
  or use another statistic.
- **Best owner:** Designer.

### 9. Are status classification lists authoritative?

- **Why it matters:** Dispel eligibility and immunity depend on these lists.
- **Evidence inspected:** `Hero.list_status_*` (`heroes/hero.py:95-107`) and
  `StatusDispell.dispell_status()`.
- **Unclear:** Several statuses appear in both buff/debuff categories by design
  or accident; the missing comma at lines 95-96 concatenates two names.
- **Best owner:** Designer and future implementation work.

## Data and balance

### 10. Are the Excel files source-of-truth runtime data or design workbooks?

- **Why it matters:** They include formula-heavy `Bar`/summary sheets as well as
  runtime sheets and backup copies.
- **Evidence inspected:** All workbook sheets/formulas and
  `System_initialization.initialize()`.
- **Unclear:** Change-control rules, whether formulas must be recalculated
  externally, and whether only the two named list sheets are stable API.
- **Best owner:** Repository owner.

### 11. What balance criteria determine acceptance?

- **Why it matters:** The simulators print win totals but encode no thresholds,
  persisted baselines, statistical confidence, or regression checks.
- **Evidence inspected:** Entire `simulation_engine.py` and both workbooks.
- **Unclear:** Desired matchup volume, allowable win-rate bands, team-size
  priorities, and whether mirror matches should be included.
- **Best owner:** Designer/tester.

### 12. Must battles and tournaments be reproducible?

- **Why it matters:** Debugging and balance comparisons currently cannot replay
  a run.
- **Evidence inspected:** All uses of `random`; no `random.seed`, injected RNG,
  seed CLI option, or recorded random decisions was found.
- **Unclear:** Required reproducibility and replay guarantees.
- **Best owner:** Repository owner/tester.

### 13. How should tournament ties and incomplete groups be handled?

- **Why it matters:** Knockout ties currently advance team A; group ranking uses
  wins only; the final group can be smaller.
- **Evidence inspected:** `BattleTester_2v2.run_group_stage`,
  `run_knockout`, and `run_profession_tests`
  (`simulation_engine.py:363-482`).
- **Unclear:** Intended seeding, tiebreaks, byes, and fairness guarantees.
- **Best owner:** Designer.

## UI and client boundary

### 14. Will Pygame remain a supported client?

- **Why it matters:** This determines whether its observer/input contracts are
  transitional or permanent.
- **Evidence inspected:** `main.py`, `system/game_interface.py`, Pygame RTF
  notes, and the stated future Godot direction.
- **Unclear:** Desired coexistence, migration period, and feature parity.
- **Best owner:** Repository owner.

### 15. What Python–Godot deployment model is intended?

- **Why it matters:** In-process embedding, a local child process, and a remote
  authoritative server impose different serialization and lifecycle needs.
- **Evidence inspected:** Full repository search found no Godot project,
  protocol, API, IPC, or network code.
- **Unclear:** Process boundary, supported platforms, latency budget, and who
  owns persistence/session lifecycle.
- **Best owner:** Repository owner/future implementation work.

### 16. What state and event information must a client receive?

- **Why it matters:** Current output is ANSI prose plus live object access,
  neither of which defines animation-ready events.
- **Evidence inspected:** `Game.output_buffer`, display methods,
  `GameInterface` rendering, and `Skill`/hero mutation paths.
- **Unclear:** Required snapshot fields, hidden information, animation events,
  stable IDs, localization, and pacing acknowledgements.
- **Best owner:** Designer and future implementation work.

### 17. Is online multiplayer server-authoritative?

- **Why it matters:** Trust, reconnection, command validation, and deterministic
  resolution requirements depend on authority.
- **Evidence inspected:** No network, account, persistence, serialization, or
  concurrency implementation was found.
- **Unclear:** Multiplayer topology and security model.
- **Best owner:** Repository owner.

## Engineering and quality

### 18. Which Python version and platforms are supported?

- **Why it matters:** The repo tracks a Linux Python 3.12 environment, the local
  smoke test used Python 3.13, and Pygame/filesystem behavior is
  platform-sensitive.
- **Evidence inspected:** `codespace-venv`, local `.venv`, requirements, and
  `os.system('cls')` in `Game.clear_screen()`.
- **Unclear:** Official version matrix and whether Windows is the primary
  manual-play target.
- **Best owner:** Repository owner.

### 19. What automated behavior is already considered regression-critical?

- **Why it matters:** No assertion-based suite currently establishes a
  correctness baseline.
- **Evidence inspected:** `test.py`, `test_game_log.py`, `interface_test.py`,
  full search for pytest/unittest, and a headless smoke battle.
- **Unclear:** Expected outcomes for representative skills, statuses, summons,
  and battle fixtures.
- **Best owner:** Tester/repository owner.
### 20. Are backup/checkpoint files intentionally versioned?

- **Why it matters:** They substantially enlarge search results and preserve
  conflicting old implementations.
- **Evidence inspected:** `game/backup`, `heroes/backup`, `*_backup.py`,
  `.ipynb_checkpoints`, tracked file list, and imports.
- **Unclear:** Whether they are historical references that must remain or
  accidental artifacts.
- **Best owner:** Repository owner.

### 21. Is the tracked `codespace-venv/` intentional?

- **Why it matters:** It accounts for most of the 5,074 tracked paths and
  embeds platform-specific binaries and third-party sources.
- **Evidence inspected:** `git ls-files`, `.gitignore`, and dependency manifest.
- **Unclear:** Whether it is an intentional portable environment artifact.
- **Best owner:** Repository owner.

### 22. What does “passing” mean for the known status and summon edge cases?

- **Why it matters:** Developer notes mention Flesh Puppet/Stitch of Agony and
  Void Rambler disappearance defects without expected test cases.
- **Evidence inspected:** `Developer_Note/Game_Quick_Notes.txt`, recent commit
  history, `Necromancer_Flesh_Puppeteer`, `FleshPuppet`, `VoidRambler`,
  `Hero.take_damage`, and status-manager summon logic.
- **Unclear:** Reproduction steps and expected outcomes.
- **Best owner:** Tester/repository owner.
