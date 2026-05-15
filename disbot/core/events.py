from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable, Coroutine
from typing import Any

logger = logging.getLogger("core.events")

Handler = Callable[..., Coroutine[Any, Any, None]]

# Maximum seconds a single handler may block before it is cancelled.
# Prevents a slow or hung subscriber from delaying all downstream handlers.
_HANDLER_TIMEOUT: float = 5.0


class EventBus:
    """Lightweight in-process async event bus.

    Events represent facts that already occurred — they are not commands.
    Use domain.action naming (e.g. "user.level_up", "economy.daily_claimed").
    Handlers respond independently; failures are isolated.

    Phase 2.5 hardening
    ────────────────────
    Each handler executes under a timeout (_HANDLER_TIMEOUT = 5 s).  A timed-out
    handler is logged at ERROR level and subsequent handlers continue normally.
    This prevents a hung subscriber from cascading into a full event-bus stall.

    Future sharding note
    ─────────────────────
    The bus is currently in-process only.  All module-level process-local state
    (handler registrations, etc.) must be migrated to a shared backend
    (e.g. Redis pub/sub) before multi-process sharding is introduced.
    The emit() signature is kept stable for that transition.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = defaultdict(list)

    def on(self, event: str, handler: Handler) -> None:
        self._handlers[event].append(handler)

    def off(self, event: str, handler: Handler) -> None:
        self._handlers[event] = [h for h in self._handlers[event] if h is not handler]

    async def emit(self, event: str, **payload: Any) -> None:
        for handler in list(self._handlers.get(event, [])):
            try:
                await asyncio.wait_for(handler(**payload), timeout=_HANDLER_TIMEOUT)
            except asyncio.TimeoutError:
                logger.error(
                    "Handler %r timed out (>%.1fs) for event %r — "
                    "handler detached for this emission; bus continues.",
                    handler,
                    _HANDLER_TIMEOUT,
                    event,
                )
            except Exception as exc:
                logger.error(
                    "Handler %r failed for event %r: %s",
                    handler,
                    event,
                    exc,
                    exc_info=True,
                )

    def registered_events(self) -> dict[str, int]:
        """Return event names and handler counts for observability."""
        return {
            event: len(handlers)
            for event, handlers in self._handlers.items()
            if handlers
        }


bus = EventBus()
