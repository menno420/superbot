"""Typed access for the per-guild active-tournament flag.

PR B' classification: the ``ACTIVE_TOURNAMENT`` key is **runtime
tournament state**, not guild configuration:

* Written by tournament lifecycle code (start / cancel / end /
  startup-sweep) — never by operator-facing UI.
* Read at start time to prevent two tournaments overlapping in the
  same guild, and at startup to recover stale flags after a crash.
* Operators do not configure whether a tournament is "active" — it is
  a side effect of running a tournament command.

Per the post-#152 stabilization audit, this means the value must NOT
go through :class:`services.settings_mutation.SettingsMutationPipeline`
— that would pollute the settings audit log with per-match state and
emit cache-invalidation events for a flag that operator-facing settings
panels never expose. Instead, callers route through this thin service.

Storage today is the same ``settings`` table the previous direct
writes used (via :func:`utils.db.set_setting`); the service is the
canonical access boundary. A future PR may move the data to a
dedicated table without changing this API.

Public API
----------
* :func:`get_active` — return the current kind ("rps", "blackjack",
  or "" when no tournament is active).
* :func:`set_active` — mark a tournament of ``kind`` active; raises
  :class:`ValueError` for unknown kinds.
* :func:`clear_active` — clear the flag (called on completion or
  cancellation).

Invariant
---------
``tests/unit/services/test_tournament_state_service.py`` pins that
direct writes to :data:`utils.settings_keys.ACTIVE_TOURNAMENT` happen
ONLY inside this module. CI fails if a future caller adds a new
``db.set_setting(..., ACTIVE_TOURNAMENT, …)`` outside the service.
"""

from __future__ import annotations

import logging

from utils import db
from utils.settings_keys import ACTIVE_TOURNAMENT

logger = logging.getLogger("bot.tournament_state")

# Known tournament kinds. New kinds must be added here; ``set_active``
# rejects anything outside this allowlist so a typo can't silently
# wedge the "is a tournament active?" check.
_VALID_KINDS: frozenset[str] = frozenset({"rps", "blackjack"})


async def get_active(guild_id: int) -> str:
    """Return the current active-tournament kind for ``guild_id``.

    Returns the kind string (one of ``_VALID_KINDS``) or ``""`` when
    no tournament is active. Callers should compare against the kind
    they intend to start (e.g. ``if existing == "rps": ...``) so a
    foreign kind doesn't get clobbered by accident.
    """
    return await db.get_setting(guild_id, ACTIVE_TOURNAMENT, "")


async def set_active(guild_id: int, kind: str) -> None:
    """Mark ``kind`` as the active tournament for ``guild_id``.

    Raises :class:`ValueError` if ``kind`` is not in the known
    allowlist — that surfaces typos at the call site rather than as a
    silent miscategorization in the readers.
    """
    if kind not in _VALID_KINDS:
        raise ValueError(
            f"Unknown tournament kind {kind!r}. "
            f"Expected one of {sorted(_VALID_KINDS)!r}.",
        )
    await db.set_setting(guild_id, ACTIVE_TOURNAMENT, kind)


async def clear_active(guild_id: int) -> None:
    """Clear the active-tournament flag for ``guild_id``.

    Called on tournament completion, cancellation, or startup sweep
    to recover from a crash that left the flag set.
    """
    await db.set_setting(guild_id, ACTIVE_TOURNAMENT, "")


__all__ = [
    "clear_active",
    "get_active",
    "set_active",
]
