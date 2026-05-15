"""Governance event constants and the internal event emitter.

Layer: models → events (imports only from models, nothing else in governance/).
"""

from __future__ import annotations

import logging

from core.events import bus as _event_bus

logger = logging.getLogger("bot")

# ---------------------------------------------------------------------------
# Canonical governance event names
# Do NOT rename after v1 — external consumers may depend on these strings.
# ---------------------------------------------------------------------------

EVT_VISIBILITY_CHANGED = "governance.visibility.changed"
EVT_CLEANUP_CHANGED = "governance.cleanup.changed"
EVT_EXECUTION_DENIED = "governance.execution.denied"
EVT_EXECUTION_ALLOWED = "governance.execution.allowed"
EVT_CACHE_INVALIDATED = "governance.cache.invalidated"


async def _emit_governance_event(event_name: str, payload: dict) -> None:
    """Emit a governance fact to the in-process EventBus.

    Subscribers register via core.events.bus.on(event_name, handler).
    The governance package does not handle analytics, UI refresh, or audit
    logging directly — those concerns subscribe to these events instead.
    """
    logger.debug("governance_event %s %s", event_name, payload)
    await _event_bus.emit(event_name, **payload)
