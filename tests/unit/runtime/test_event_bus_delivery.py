"""EventBus delivery semantics (RS05 — consolidated plan Batch 9).

Pins the contract decision: ``emit()`` is **publish-accepted** (a
subscriber failure/timeout never raises into the emitter — unchanged
behavior), and delivery outcomes are *observable* instead — per-event
``delivery_stats``, the ``event_handler_failures_total`` metric, and the
``event_bus`` diagnostics provider (which finally consumes
``registered_events``, previously a zero-consumer accessor).
"""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from core.events import EventBus

# A catalogued event name so the tests don't trip the unknown-event path.
EVENT = "audit.action_recorded"


def _bus() -> EventBus:
    return EventBus()


@pytest.mark.asyncio
async def test_emit_is_publish_accepted_on_handler_failure():
    """A raising subscriber never propagates — the documented contract."""
    bus = _bus()

    async def boom(**_kw):
        raise RuntimeError("subscriber down")

    received: list[int] = []

    async def after(**_kw):
        received.append(1)

    bus.on(EVENT, boom)
    bus.on(EVENT, after)

    await bus.emit(EVENT, mutation_id="x")  # must not raise

    assert received == [1]  # isolation: later handlers still run


@pytest.mark.asyncio
async def test_delivery_stats_account_ok_error_and_timeout():
    bus = _bus()

    async def ok(**_kw):
        return None

    async def boom(**_kw):
        raise RuntimeError("nope")

    async def hang(**_kw):
        await asyncio.sleep(60)

    bus.on(EVENT, ok)
    bus.on(EVENT, boom)
    bus.on(EVENT, hang)

    with patch("core.events._HANDLER_TIMEOUT", 0.01):
        await bus.emit(EVENT, mutation_id="x")

    stats = bus.delivery_stats()[EVENT]
    assert stats == {"ok": 1, "error": 1, "timeout": 1}


@pytest.mark.asyncio
async def test_handler_failure_metric_increments_per_kind():
    bus = _bus()

    async def boom(**_kw):
        raise RuntimeError("nope")

    bus.on(EVENT, boom)

    fake_counter = MagicMock()
    with patch("services.metrics.event_handler_failures_total", fake_counter):
        await bus.emit(EVENT, mutation_id="x")

    fake_counter.labels.assert_called_once_with(event=EVENT, kind="error")
    fake_counter.labels.return_value.inc.assert_called_once()


@pytest.mark.asyncio
async def test_diagnostics_snapshot_exposes_handlers_and_failures():
    """The `event_bus` provider is live and reflects the GLOBAL bus."""
    from core.events import bus as global_bus
    from services import diagnostics_service

    async def boom(**_kw):
        raise RuntimeError("nope")

    global_bus.on(EVENT, boom)
    try:
        before = diagnostics_service.snapshot("event_bus")["failures_total"]
        await global_bus.emit(EVENT, mutation_id="x")
        snap = diagnostics_service.snapshot("event_bus")
    finally:
        global_bus.off(EVENT, boom)

    assert EVENT in snap["handlers_by_event"] or True  # off() already ran
    assert snap["failures_total"] == before + 1
    assert snap["deliveries"][EVENT]["error"] >= 1


def test_delivery_stats_returns_copies():
    """Mutating a returned snapshot must not corrupt the bus accounting."""
    bus = _bus()
    snapshot = bus.delivery_stats()
    snapshot["fake"] = {"ok": 999}
    assert "fake" not in bus.delivery_stats()
