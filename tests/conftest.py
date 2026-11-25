"""Keep repository-root packages importable with either pytest entry point."""

from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def restore_battle_app_globals():
    """Keep mode-isolation tests from leaking a reloaded app into later tests.

    Release-boundary tests intentionally reload ``battle_api.app`` under a
    disposable mode/database.  Reload mutates the existing module object, so
    module-level ``app``/registry imports held by ordinary tests would
    otherwise point at the disposable application after that test completes.
    Restore the process-local globals at each test boundary; this is test
    isolation only and does not alter production runtime behavior.
    """
    import battle_api.app as app_module

    names = (
        "app",
        "registry",
        "battle_attempt_registry",
        "progression_store",
        "_player_battle_locks",
    )
    saved = {name: getattr(app_module, name) for name in names}
    try:
        yield
    finally:
        for name, value in saved.items():
            setattr(app_module, name, value)
