"""World registry — the federated open-world spine seam (Explore-hub PR 1).

The federated Explore hub (the "town square") routes a player into each game's
own world — Mine, Fish, and (later) pets / survival. Rather than hard-code that
list in the hub view, each subsystem **registers a** :class:`WorldEntry` here, so
a new world docks into the spine by registering one entry — no edit to the hub.

Plan: ``docs/planning/explore-hub-federated-world-plan-2026-06-19.md`` §4 (PR 1).

Layer note (``docs/architecture.md``): this registry lives in ``services/`` and is
read by the ``views/explore/`` hub and written by view/cog setup. It stores the
``opener`` as an **opaque callable** and imports no view module, so it never
creates a ``services → views`` edge (the layer's hardest rule). The opener
closure is built in the view layer (where it may import view classes) and passed
in — the registry only holds and returns it.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

import discord

# An opener receives the live interaction (already deferred by the hub button)
# and the hosting hub view, and edits the panel in place to enter that world.
# Typed against ``discord.ui.View`` (not the concrete hub) to keep this module
# free of any view import — the closure is supplied by the view layer.
WorldOpener = Callable[[discord.Interaction, discord.ui.View], Awaitable[None]]


@dataclass(frozen=True)
class WorldEntry:
    """One game's entry in the federated Explore world.

    Attributes:
        key: stable identifier (e.g. ``"mining"``). De-duplicates entries.
        label: short button/field label (e.g. ``"Mine"``).
        emoji: a leading emoji for the button/field.
        description: one-line "what this world is" blurb for the hub embed.
        opener: optional coroutine that enters the world in place. ``None``
            renders a generic "coming soon" card built from ``description``.
        order: ascending sort key for deterministic hub ordering (ties break
            on ``label``).
    """

    key: str
    label: str
    emoji: str
    description: str
    opener: WorldOpener | None = None
    order: int = 100
    # Kept for forward-compat metadata without breaking the frozen dataclass
    # equality contract used by tests.
    _extra: dict[str, object] = field(default_factory=dict, compare=False, repr=False)


# Module-level registry. Mutated only through the helpers below so registration
# stays idempotent and the ordering deterministic.
_ENTRIES: dict[str, WorldEntry] = {}


def register_world_entry(entry: WorldEntry, *, replace: bool = False) -> bool:
    """Register ``entry`` under ``entry.key``.

    Idempotent by default: re-registering a key that already exists is a no-op
    (returns ``False``) so a subsystem can safely call this every time its hub
    is constructed. Pass ``replace=True`` to overwrite an existing entry.

    Returns ``True`` if the registry changed, ``False`` if the call was a
    no-op (key already present and ``replace`` is ``False``).
    """
    if entry.key in _ENTRIES and not replace:
        return False
    _ENTRIES[entry.key] = entry
    return True


def get_world_entries() -> list[WorldEntry]:
    """All registered entries, sorted by ``(order, label)`` — deterministic."""
    return sorted(_ENTRIES.values(), key=lambda e: (e.order, e.label))


def get_world_entry(key: str) -> WorldEntry | None:
    """Return the entry registered under ``key``, or ``None``."""
    return _ENTRIES.get(key)


def clear_world_entries() -> None:
    """Drop all registered entries. Test-only helper (resets module state)."""
    _ENTRIES.clear()


__all__ = [
    "WorldEntry",
    "WorldOpener",
    "register_world_entry",
    "get_world_entries",
    "get_world_entry",
    "clear_world_entries",
]
