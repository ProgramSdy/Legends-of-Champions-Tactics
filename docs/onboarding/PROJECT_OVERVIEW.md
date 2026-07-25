# Project Overview

## Scope and evidence

This document describes the repository at commit `f88fbb92` (`main`, tag
`v0.1-foundation`). It is an account of the implementation found in the
repository, not a target design. Source references use 1-based approximate line
numbers.

The review covered the active Python packages and entry points, backup and
notebook-checkpoint code, both Excel data files and their backups, the two-slide
`Developer_Note/Game_Key_Structure.pptx`, the RTF and text developer notes,
image assets, dependency manifest, release notes, and the three files whose
names begin with `test`.

## Purpose and current stage

Legends of Champions Tactics is a local, turn-based, two-team combat prototype.
Heroes have a faculty and specialization ("major"), randomized statistics,
skills, damage resistances, buffs/debuffs, and either player or AI control.
Combat proceeds by rounds and agility-ordered turns until only one group remains
or the 15-round cap is reached (`game/game.py:21-45, 208-359`).

The tag name, direct construction of sample teams in `main.py`, extensive
hard-coded combat rules, developer backup files, debug comments, and absence of
an automated test suite are consistent with a foundation/prototype release.
The engine is nevertheless executable: a headless one-versus-one smoke battle
completed during this review.

## Major capabilities

- Manual battle orchestration with a Pygame window, battle log, keyboard skill
  selection, and target selection (`main.py:19-124`;
  `system/game_interface.py:9-504`).
- Fully AI-driven battles using the same `Game` state transitions
  (`simulation_engine.py:23-67`).
- Eight hero faculties represented by 27 concrete specializations in the
  current simulation lists: Warrior, Mage, Paladin, Priest, Rogue,
  Necromancer, Warlock, and Death Knight
  (`simulation_engine.py:76-88`; `heroes/__init__.py:1-10`).
- Single-target and multi-target damage, healing, hybrid
  damage/healing, buffs, summons, evasion, immunity, interruption, casting
  delays, and cooldowns (`skills/skill.py:15-406`).
- A large status catalogue with round-start ticking, damage/healing-over-time,
  stat changes, control effects, expiry, and dispelling
  (`heroes/hero.py:25-107`; `game/status_effect_manager.py:15-987`;
  `game/status_dispell.py:15-268`).
- Summoned Skeleton Warriors, Skeleton Mages, Flesh Puppets, Void Ramblers, and
  Water Elementals, created through `SummonFactory`
  (`heroes/summon_factory.py:4-26`; `heroes/summon_unit.py:17-538`).
- Balance simulations for 1v1, 2v2, and 3v3; the active 2v2 path includes a
  shuffled group stage followed by knockout rounds
  (`simulation_engine.py:23-153, 288-590`).

No equipment or inventory system was found. Mentions of weapons and armor are
combat prose or skill names, not equippable objects.

## Main entry points and runtime modes

### `python main.py`

`main()` initializes `System_initialization`, creates a 1200x800
`GameInterface`, constructs two hard-coded teams, creates
`Game(..., mode="manual")`, and advances its state machine at 60 frames per
second (`main.py:19-114`). In the checked-in setup, both Group A heroes are
player-controlled and both Group B heroes are AI-controlled
(`main.py:43-74`).

Despite the name `manual`, control is per hero: `Hero.is_player_controlled`
selects `player_action` versus `ai_action` (`game/game.py:314-330`). The mode
primarily controls display/delay behavior and assumes an interface exists.

### `python simulation_engine.py [1v1|2v2|3v3]`

The default is `1v1`. Each simulator repeatedly instantiates a `Game` in
`simulation` mode and drives the same five states until `game_over`
(`simulation_engine.py:28-67, 294-335, 490-531, 594-612`).

- `1v1`: ordered pairwise profession tests, 20 battles per pairing in `main`.
- `2v2`: all two-profession combinations, randomized groups of 16, top two
  qualifiers per group, then a knockout tournament; 10 battles per group-stage
  matchup and twice that in knockout.
- `3v3`: all three-profession combinations, randomized groups of 16, five
  battles per matchup, and a printed top-20 group-stage summary. It does not
  implement a knockout stage.

The simulation entry point still initializes a Pygame window and loads image
assets before running (`simulation_engine.py:594-598`), even though simulation
output methods are no-ops.

### Other executable-looking files

- `test.py` is a standalone Pygame blitting experiment, not an assertion test.
- `test_game_log.py` manually demonstrates `GameInterface` log rendering.
- `interface_test.py` is a curses UI experiment with a local mock `Hero`.

## High-level directory map

| Path | Current responsibility |
|---|---|
| `game/` | `Game` orchestration, hero generation, status ticking, dispelling |
| `heroes/` | Base `Hero`, faculty/specialization classes, skill effects, AI overrides, summons |
| `skills/` | Generic `Skill` execution pipeline and lightweight `Buff`/`Debuff` records |
| `system/` | Excel/image initialization and Pygame presentation/input |
| `data/` | Hero stat and seven-school resistance ranges in Excel |
| `images/icons_profession/` | Profession portraits used by initialization/UI |
| `Developer_Note/` | Original structural diagram, Pygame notes, and developer reminders |
| `game/backup/`, `heroes/backup/`, `*_backup.py`, `.ipynb_checkpoints/` | Historical copies; not imported by active entry points |
| repository root | Manual and simulation entry points plus experimental UI scripts |

The repository also tracks a full `codespace-venv/`, while a separate hidden
`.venv/` exists locally. This makes the tracked tree much larger than the game
source and creates environment reproducibility/maintenance risk.

## Data and external dependencies

`requirements.txt` is UTF-16LE and pins Pygame 2.6.1, pandas 2.3.2, NumPy,
openpyxl, tqdm, and their transitive packages. Runtime code directly uses:

- `pygame` for the window, input, fonts, rendering, and image loading;
- `pandas` to load the two Excel workbooks;
- `openpyxl` indirectly as pandas' `.xlsx` engine;
- `tqdm` for simulation progress bars.

`System_initialization.initialize()` loads `Property List` and
`Resistance List`, indexes both by their first column, and loads a subset of
profession icons (`system/system_initialization.py:7-75`). The active worksheets
contain 34 profession/summon columns. `Hero` looks up a column using its
`faculty + "_" + major` profession string, selects correlated random values
inside min/max ranges, then generates and compensates seven resistances
(`heroes/hero.py:109-141, 298-504`).

Relative paths are resolved from the process working directory. The apparent
supported invocation location is therefore the repository root.

## Confirmed findings

- `Game` is the central battle controller and its `game_state` is externally
  advanced by both entry points.
- The same mutable domain objects implement battle rules, AI, and manual input
  delegation.
- Round-start processing performs cooldown and status updates before checking
  defeat and establishing turn order.
- Concrete hero constructors register bound-method callbacks in `Skill`
  instances.
- Summons are full hero subclasses with their own skills and AI and are inserted
  into the live game/team lists.
- Randomness is used for generated stats, resistances, AI choices, hit/evasion
  behavior, target choice, and damage variation. No seed or RNG injection was
  found.
- No Godot project, bridge/protocol, serializer, network code, equipment model,
  package metadata, CI configuration, or conventional unit-test framework was
  found.

## Unresolved questions

- Which behavior in the current prototype is authoritative game design versus
  temporary tuning or known bug behavior?
- Is the Pygame client intended to remain supported after a Godot client exists?
- Are Excel workbooks runtime production data, balancing workspaces, or both?
- Should simulations be reproducible, and what constitutes an accepted balance
  result?
- Is a draw at the round cap intended to be decided only by surviving groups,
  with no HP/tiebreak score?

See `OPEN_QUESTIONS.md` for the evidence and ownership of these and other
questions.

## Validation performed

On the reviewed checkout:

- AST parsing succeeded for all 44 repository Python files (including backups
  and checkpoints, excluding virtual-environment dependencies).
- A headless smoke battle using `Warrior_Comprehensiveness` versus
  `Mage_Comprehensiveness` completed in eight state-machine steps; Group B
  survived in round 2.

This validates one execution path, not combat correctness or balance.
