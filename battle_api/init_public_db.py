"""Explicit one-time initializer for an empty RELEASE-002 Public database."""

from __future__ import annotations

import argparse
from pathlib import Path

from .progression import ProgressionStore


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def initialize_public_database(path: Path) -> None:
    if not path.is_absolute():
        raise ValueError("The Public database path must be absolute.")
    resolved = path.resolve(strict=False)
    if resolved == REPOSITORY_ROOT or REPOSITORY_ROOT in resolved.parents:
        raise ValueError(
            "The Public database must be outside the repository and release artifacts."
        )
    if resolved.exists():
        raise FileExistsError(
            "Refusing to replace an existing Public database. Validate it through API startup."
        )
    if not resolved.parent.is_dir():
        raise FileNotFoundError("The Public database directory does not exist.")
    store = ProgressionStore(
        resolved, public_mode=True, allow_public_initialize=True
    )
    store.ensure_initialized()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a new empty Public player database exactly once."
    )
    parser.add_argument("path", type=Path)
    arguments = parser.parse_args()
    initialize_public_database(arguments.path)
    print(f"Initialized empty Public database: {arguments.path}")


if __name__ == "__main__":
    main()
