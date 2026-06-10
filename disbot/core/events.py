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

# One-shot WARNING set so the catalogue-drift log doesn't spam on every
# call.  Cleared at process restart.  Metric increments unconditionally.
_WARNED_UNKNOWN: set[tuple[str, str]] = set()


def _check_catalogue(event: str, op: str) -> None:
    """Emit a metric (and one-shot WARNING) if *event* isn't catalogued.

    Imports are deferred so this module stays free of governance/services
    imports at module-load time (avoids circular import risk during the
    governance → core.events → governance.events chain).
    """
    try:
        from core.events_catalogue import is_known
    except Exception:  # pragma: no cover — catalogue should always import
        return
    if is_known(event):
        return
    try:
        from services import metrics

        metrics.unknown_event_total.labels(event=event, op=op).inc()
    except Exception:  # pragma: no cover — metric is best-effort
        pass
    key = (event, op)
    if key not in _WARNED_UNKNOWN:
        _WARNED_UNKNOWN.add(key)
        logger.warning(
            "EventBus %s on uncatalogued event %r — add it to "
            "disbot/core/events_catalogue.py KNOWN_EVENTS.",
            op,
            event,
        )


class EventBus:
    """Lightweight in-process async event bus.

    Events represent facts that already occurred — they are not commands.
    Use domain.action naming (e.g. "user.level_up", "economy.daily_claimed").
    Handlers respond independently; failures are isolated.

    Catalogue enforcement
    ──────────────────────
    Every event name passed to :meth:`emit` and :meth:`on` is checked
    against :data:`core.events_catalogue.KNOWN_EVENTS`.  Unknown names log
    a one-shot WARNING and increment ``unknown_event_total{event, op}``;
    no exception is raised, so an uncatalogued emit never breaks runtime.
    Adding new event names to the catalogue is required before they can
    fire silently.

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
        # RS05 delivery accounting (process-local, per event name):
        # {"ok": n, "error": n, "timeout": n}. emit() stays
        # **publish-accepted** (a subscriber failure never raises — the
        # documented contract); these counters are how delivery outcomes
        # become observable instead.
        self._delivery_stats: dict[str, dict[str, int]] = defaultdict(
            lambda: {"ok": 0, "error": 0, "timeout": 0},
        )

    def on(self, event: str, handler: Handler) -> None:
        _check_catalogue(event, "on")
        self._handlers[event].append(handler)

    def off(self, event: str, handler: Handler) -> None:
        self._handlers[event] = [h for h in self._handlers[event] if h is not handler]

    async def emit(self, event: str, **payload: Any) -> None:
        """Publish ``event`` to every subscriber — **publish-accepted**.

        Returning normally means the bus accepted and dispatched the
        emission; it does **not** mean every subscriber succeeded
        (failures/timeouts are isolated per handler — RS05 contract,
        ``docs/runtime_contracts.md`` §2). Result fields like
        ``audit_emitted`` / ``event_emitted`` on mutation results carry
        exactly this publish-accepted meaning. Subscriber outcomes are
        observable via :meth:`delivery_stats`, the ``event_bus``
        diagnostics provider, and ``event_handler_failures_total``.
        """
        _check_catalogue(event, "emit")
        stats = self._delivery_stats[event]
        for handler in list(self._handlers.get(event, [])):
            try:
                await asyncio.wait_for(handler(**payload), timeout=_HANDLER_TIMEOUT)
                stats["ok"] += 1
            except asyncio.TimeoutError:
                stats["timeout"] += 1
                _count_handler_failure(event, "timeout")
                logger.error(
                    "Handler %r timed out (>%.1fs) for event %r — "
                    "handler detached for this emission; bus continues.",
                    handler,
                    _HANDLER_TIMEOUT,
                    event,
                )
            except Exception as exc:
                stats["error"] += 1
                _count_handler_failure(event, "error")
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

    def delivery_stats(self) -> dict[str, dict[str, int]]:
        """Per-event subscriber outcomes since process start (RS05).

        ``{event: {"ok": n, "error": n, "timeout": n}}`` — the observable
        counterpart to emit's publish-accepted return. Process-lifetime,
        in-memory (the same scope as the metrics counters).
        """
        return {event: dict(stats) for event, stats in self._delivery_stats.items()}


def _count_handler_failure(event: str, kind: str) -> None:
    """Best-effort ``event_handler_failures_total`` increment (RS05).

    Deferred import + swallow, exactly like :func:`_check_catalogue`'s
    metric — a metrics outage must never affect dispatch.
    """
    try:
        from services import metrics

        metrics.event_handler_failures_total.labels(event=event, kind=kind).inc()
    except Exception:  # pragma: no cover — metric is best-effort
        pass


bus = EventBus()


def _register_diagnostics_provider() -> None:
    """Expose the bus on the ``!platform runtime`` surface (RS05).

    The snapshot finally consumes :meth:`EventBus.registered_events`
    (previously an accessor with zero consumers) plus the new delivery
    stats. Registration failure is loud, not silent — a missing provider
    is the RS04 no-op class this batch exists to kill.
    """
    try:
        from services import diagnostics_service

        def _snapshot() -> dict[str, Any]:
            deliveries = bus.delivery_stats()
            return {
                "handlers_by_event": bus.registered_events(),
                "deliveries": deliveries,
                "failures_total": sum(
                    s["error"] + s["timeout"] for s in deliveries.values()
                ),
            }

        diagnostics_service.register("event_bus", _snapshot)
    except Exception:  # noqa: BLE001 — never block core.events import
        logger.warning(
            "EventBus diagnostics provider registration failed — "
            "!platform runtime will not show event delivery stats.",
            exc_info=True,
        )


_register_diagnostics_provider()
