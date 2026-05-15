from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable, Coroutine
from typing import Any

logger = logging.getLogger("core.events")

Handler = Callable[..., Coroutine[Any, Any, None]]


class EventBus:
    """Lightweight in-process async event bus.

    Events represent facts that already occurred — they are not commands.
    Use domain.action naming (e.g. "user.level_up", "economy.daily_claimed").
    Handlers respond independently; failures are isolated.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = defaultdict(list)

    def on(self, event: str, handler: Handler) -> None:
        self._handlers[event].append(handler)

    def off(self, event: str, handler: Handler) -> None:
        self._handlers[event] = [
            h for h in self._handlers[event] if h is not handler
        ]

    async def emit(self, event: str, **payload: Any) -> None:
        for handler in list(self._handlers.get(event, [])):
            try:
                await handler(**payload)
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
        return {event: len(handlers) for event, handlers in self._handlers.items() if handlers}


bus = EventBus()
