"""Central catalogue of every EventBus event the platform emits.

The catalogue exists so that:

1. Every ``bus.emit(event_name, ...)`` and ``bus.on(event_name, ...)``
   callsite has a single place to verify the event name against — no more
   accidental drift between emitter and listener strings.
2. ``bus`` itself can warn (and surface a metric) when production code
   touches an event name not in the catalogue, catching typos and
   leftovers from removed cogs at runtime.
3. A future migration to typed event payloads can extend this module
   without changing emit/on signatures.

Naming convention
-----------------
``<domain>.<noun_phrase>``, dots only, lowercase, no underscores in the
domain portion.  Examples:

    governance.visibility.changed
    governance.cache.invalidated
    economy.daily_claimed       (future)

Adding an event
---------------
Add the literal string to ``KNOWN_EVENTS`` below and emit it from a cog
or service.  Subscribers listen via ``bus.on("…", handler)`` or via the
``EVT_*`` constants exported from the governance package.

Implements INV-A from the platform-hardening plan.
"""

from __future__ import annotations

from governance.events import (
    EVT_CACHE_INVALIDATED,
    EVT_CLEANUP_CHANGED,
    EVT_EXECUTION_ALLOWED,
    EVT_EXECUTION_DENIED,
    EVT_VISIBILITY_CHANGED,
)

# Every event name the platform may emit.  Adding an event without
# adding it here triggers a "unknown_event_total" metric increment and
# a one-shot WARNING in the bus.
KNOWN_EVENTS: frozenset[str] = frozenset(
    {
        # ── Governance (governance/events.py) ────────────────────────────
        EVT_VISIBILITY_CHANGED,
        EVT_CACHE_INVALIDATED,
        EVT_CLEANUP_CHANGED,
        EVT_EXECUTION_ALLOWED,
        EVT_EXECUTION_DENIED,
        # ── Economy (services/economy_service.py) ────────────────────────
        "economy.balance_changed",
        # ── Future cog-emitted facts (uncomment when first emitter lands):
        # "economy.daily_claimed",
        # "xp.awarded",
        # "xp.level_up",
        # "mining.harvested",
    },
)


def is_known(event_name: str) -> bool:
    """True if *event_name* appears in :data:`KNOWN_EVENTS`."""
    return event_name in KNOWN_EVENTS
