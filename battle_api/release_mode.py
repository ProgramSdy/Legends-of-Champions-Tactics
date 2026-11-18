"""Fail-closed Development/Public Release mode selection."""

from __future__ import annotations

from enum import Enum
import os


RELEASE_MODE_ENV = "LOCT_RELEASE_MODE"


class ReleaseMode(str, Enum):
    DEVELOPMENT = "development"
    PUBLIC = "public"


def resolve_release_mode(value: str | None) -> ReleaseMode:
    """Resolve only an explicit Development value; everything else is Public."""

    if value == ReleaseMode.DEVELOPMENT.value:
        return ReleaseMode.DEVELOPMENT
    return ReleaseMode.PUBLIC


def current_release_mode() -> ReleaseMode:
    """Read the server-controlled process environment with a safe default."""

    return resolve_release_mode(os.getenv(RELEASE_MODE_ENV))


def engineering_enabled() -> bool:
    return current_release_mode() is ReleaseMode.DEVELOPMENT


if __name__ == "__main__":
    print(current_release_mode().value)
