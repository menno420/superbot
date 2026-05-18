"""Typed per-user participation accessors (Phase 2c, PR-8).

Cog / service code reads per-user participation through these typed
helpers so the storage shape stays an implementation detail.  PR-8
ships the read path; PR-9 adds the corresponding mutation pipeline.

Why these are separate from
:mod:`utils.guild_config_accessors` (which covers guild-level state):

* Per-user and per-guild are different runtime domains with different
  authority models, audit semantics, and lifecycle hooks.  The
  consistency ledger forbids mixing them.
* Per-user participation is read on the user-message hot path (XP
  opt-out gate, etc.) so a dedicated cache layer
  (:mod:`core.runtime.user_config`) keeps the read O(1) after warm.

Four typed accessors, one per concern:

* :func:`get_participation` — opt-in / opt-out state per subsystem
* :func:`is_subscribed` — topic-level subscription with schema-default
* :func:`get_preference` — JSONB preference with caller-supplied default
* :func:`get_visibility` — public / hidden surface toggle per subsystem

Missing-row semantics:

* ``user_participation`` → :class:`ParticipationState.NOT_SET`
* ``user_subscriptions`` → the schema's declared default for that topic
* ``user_preferences`` → the ``default`` argument supplied by the caller
* ``user_visibility_overrides`` → :class:`VisibilityState.DEFAULT`
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ParticipationState(str, Enum):
    """Per-user participation state in a subsystem.

    ``NOT_SET`` is the implicit default returned when no row exists —
    callers interpret it via their schema's ``requires_optin`` flag.
    """

    OPTED_IN = "opted_in"
    OPTED_OUT = "opted_out"
    NOT_SET = "not_set"


class VisibilityState(str, Enum):
    """User-controlled visibility surface for a subsystem."""

    PUBLIC = "public"
    HIDDEN = "hidden"
    DEFAULT = "default"


@dataclass(frozen=True)
class PreferenceResult:
    """A user preference read result + provenance.

    ``found`` distinguishes "no row" (default returned) from "row
    with explicit value".  Callers that need to know whether the user
    has ever set this preference inspect ``found``.
    """

    value: Any
    found: bool


# ---------------------------------------------------------------------------
# Accessors
# ---------------------------------------------------------------------------


async def get_participation(
    user_id: int,
    guild_id: int,
    subsystem: str,
) -> ParticipationState:
    """Return the user's participation state in ``subsystem`` for ``guild_id``.

    Returns :class:`ParticipationState.NOT_SET` when no row exists.
    """
    from core.runtime import user_config

    bundle = await user_config.get(user_id, guild_id)
    for row in bundle.participation:
        if row.get("subsystem") == subsystem:
            state = row.get("state")
            if state == ParticipationState.OPTED_IN.value:
                return ParticipationState.OPTED_IN
            if state == ParticipationState.OPTED_OUT.value:
                return ParticipationState.OPTED_OUT
    return ParticipationState.NOT_SET


async def is_subscribed(
    user_id: int,
    guild_id: int,
    subsystem: str,
    topic: str,
    *,
    default: bool = False,
) -> bool:
    """Return the user's subscription state for ``(subsystem, topic)``.

    ``default`` is returned when no row exists.  The schema layer
    typically supplies the spec's declared default here; callers that
    do not have a schema in scope (rare) can pass ``False`` to mean
    "treat as opted-out".
    """
    from core.runtime import user_config

    bundle = await user_config.get(user_id, guild_id)
    for row in bundle.subscriptions:
        if row.get("subsystem") == subsystem and row.get("topic") == topic:
            return bool(row.get("enabled"))
    return default


async def get_preference(
    user_id: int,
    guild_id: int,
    key: str,
    *,
    default: Any = None,
) -> PreferenceResult:
    """Return the user's preference value for ``key``, or ``default``.

    Wrapped in :class:`PreferenceResult` so callers can distinguish
    "no row" (``found=False``) from "explicit row with value ==
    default" (``found=True``).
    """
    from core.runtime import user_config

    bundle = await user_config.get(user_id, guild_id)
    for row in bundle.preferences:
        if row.get("key") == key:
            return PreferenceResult(value=row.get("value"), found=True)
    return PreferenceResult(value=default, found=False)


async def get_visibility(
    user_id: int,
    guild_id: int,
    subsystem: str,
) -> VisibilityState:
    """Return the user's visibility override for ``subsystem``.

    Returns :class:`VisibilityState.DEFAULT` when no row exists —
    callers fall back to the schema's declared default visibility.
    """
    from core.runtime import user_config

    bundle = await user_config.get(user_id, guild_id)
    for row in bundle.visibility_overrides:
        if row.get("subsystem") == subsystem:
            visibility = row.get("visibility")
            if visibility == VisibilityState.PUBLIC.value:
                return VisibilityState.PUBLIC
            if visibility == VisibilityState.HIDDEN.value:
                return VisibilityState.HIDDEN
    return VisibilityState.DEFAULT


__all__ = [
    "ParticipationState",
    "PreferenceResult",
    "VisibilityState",
    "get_participation",
    "get_preference",
    "get_visibility",
    "is_subscribed",
]
