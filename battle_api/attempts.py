"""Process-local idempotency for player-facing battle launch attempts.

Battle sessions are process-local, so launch idempotency intentionally has the
same lifetime.  A stable client attempt ID can safely retry a lost creation
response without constructing a second session, while a new ID represents a
new player-intended attempt.
"""

from __future__ import annotations

from collections.abc import Callable, Hashable
from copy import deepcopy
from dataclasses import dataclass
import threading
from typing import Any, TypeVar


SessionT = TypeVar("SessionT")
LaunchResult = tuple[SessionT, dict[str, Any]]


class BattleAttemptConflict(ValueError):
    """An attempt ID was reused for a different launch configuration."""


@dataclass(frozen=True)
class _BattleAttempt:
    profile_id: str
    fingerprint: Hashable
    session: Any
    envelope: dict[str, Any]


class BattleAttemptRegistry:
    """Atomically bind an attempt ID, its owning profile, and one session."""

    def __init__(self) -> None:
        self._attempts: dict[str, _BattleAttempt] = {}
        self._lock = threading.RLock()

    def get_or_create(
        self,
        *,
        profile_id: str,
        attempt_id: str | None,
        fingerprint: Hashable,
        factory: Callable[[], LaunchResult[SessionT]],
    ) -> LaunchResult[SessionT]:
        if attempt_id is None:
            return factory()

        with self._lock:
            existing = self._attempts.get(attempt_id)
            if existing is not None:
                if existing.profile_id != profile_id:
                    raise BattleAttemptConflict(
                        "attemptId is already bound to a different active save profile."
                    )
                if existing.fingerprint != fingerprint:
                    raise BattleAttemptConflict(
                        "attemptId is already bound to a different battle "
                        "launch configuration."
                    )
                return existing.session, deepcopy(existing.envelope)

            session, envelope = factory()
            cached_envelope = deepcopy(envelope)
            self._attempts[attempt_id] = _BattleAttempt(
                profile_id=profile_id,
                fingerprint=fingerprint,
                session=session,
                envelope=cached_envelope,
            )
            return session, deepcopy(cached_envelope)

    def clear(self) -> None:
        """Clear process-local bindings; intended for isolated tests."""

        with self._lock:
            self._attempts.clear()
