"""Tests for the EventBus catalogue check (INV-A).

Covers:
- Every governance EVT_* constant is in KNOWN_EVENTS
- bus.emit on a known event is silent (no warning, no metric)
- bus.emit on an unknown event logs a one-shot WARNING and emits the metric
- bus.on on an unknown event triggers the same path with op="on"
- The one-shot WARNING fires once per (event, op), not per emission
"""

from __future__ import annotations

import logging
from unittest.mock import patch

import pytest

from core import events as bus_module
from core.events import EventBus
from core.events_catalogue import KNOWN_EVENTS, is_known


class TestCatalogueContents:
    def test_governance_events_are_catalogued(self):
        from governance.events import (
            EVT_CACHE_INVALIDATED,
            EVT_CLEANUP_CHANGED,
            EVT_EXECUTION_ALLOWED,
            EVT_EXECUTION_DENIED,
            EVT_VISIBILITY_CHANGED,
        )

        for evt in (
            EVT_VISIBILITY_CHANGED,
            EVT_CACHE_INVALIDATED,
            EVT_CLEANUP_CHANGED,
            EVT_EXECUTION_ALLOWED,
            EVT_EXECUTION_DENIED,
        ):
            assert is_known(evt), f"Missing from KNOWN_EVENTS: {evt!r}"
            assert evt in KNOWN_EVENTS


class TestBusCheck:
    @pytest.fixture(autouse=True)
    def _reset_warned(self):
        bus_module._WARNED_UNKNOWN.clear()
        yield
        bus_module._WARNED_UNKNOWN.clear()

    @pytest.mark.asyncio
    async def test_known_event_emit_is_silent(self, caplog):
        from governance.events import EVT_VISIBILITY_CHANGED

        b = EventBus()
        with (
            patch("services.metrics.unknown_event_total") as m,
            caplog.at_level(logging.WARNING, logger="core.events"),
        ):
            await b.emit(EVT_VISIBILITY_CHANGED, guild_id=1, subsystem="test")
            m.labels.assert_not_called()
            assert not any("uncatalogued" in r.message for r in caplog.records)

    @pytest.mark.asyncio
    async def test_unknown_event_emit_warns_and_increments(self, caplog):
        b = EventBus()
        with (
            patch("services.metrics.unknown_event_total") as m,
            caplog.at_level(logging.WARNING, logger="core.events"),
        ):
            await b.emit("ghost.event", x=1)
            m.labels.assert_called_with(event="ghost.event", op="emit")
            m.labels.return_value.inc.assert_called_once()
            assert any("ghost.event" in r.message for r in caplog.records)
            assert any("uncatalogued" in r.message for r in caplog.records)

    def test_unknown_event_on_warns_and_increments(self, caplog):
        b = EventBus()

        async def handler(**_):
            return None

        with (
            patch("services.metrics.unknown_event_total") as m,
            caplog.at_level(logging.WARNING, logger="core.events"),
        ):
            b.on("ghost.event", handler)
            m.labels.assert_called_with(event="ghost.event", op="on")
            assert any("uncatalogued" in r.message for r in caplog.records)

    @pytest.mark.asyncio
    async def test_warning_is_one_shot_metric_is_not(self, caplog):
        b = EventBus()
        with (
            patch("services.metrics.unknown_event_total") as m,
            caplog.at_level(logging.WARNING, logger="core.events"),
        ):
            await b.emit("ghost.event", x=1)
            await b.emit("ghost.event", x=2)
            await b.emit("ghost.event", x=3)
            # Three increments, one warning.
            assert m.labels.return_value.inc.call_count == 3
            warnings = [r for r in caplog.records if "uncatalogued" in r.message]
            assert len(warnings) == 1
