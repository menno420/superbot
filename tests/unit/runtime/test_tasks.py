"""Regression tests for core.runtime.tasks (managed background-task helper).

Covers CRIT-1 (unmanaged asyncio.create_task) from the platform-hardening
plan.  Verifies:

- spawn() returns an asyncio.Task and holds a strong reference until done
- completed tasks are removed from active()
- exceptions in spawned tasks are logged and emit task_outcome_total{outcome="error"}
- cancelled tasks emit task_outcome_total{outcome="cancelled"}
- successful tasks emit task_outcome_total{outcome="ok"}
- cancel_all() cancels every still-running task
"""

from __future__ import annotations

import asyncio
import logging
from unittest.mock import patch

import pytest

from core.runtime import tasks


@pytest.fixture(autouse=True)
def _clear_tasks_set():
    """Each test starts with an empty task registry."""
    tasks._TASKS.clear()
    yield
    tasks._TASKS.clear()


class TestSpawn:
    @pytest.mark.asyncio
    async def test_returns_task_and_holds_reference(self):
        evt = asyncio.Event()

        async def waiter():
            await evt.wait()

        t = tasks.spawn("test:waiter", waiter())
        assert isinstance(t, asyncio.Task)
        assert t in tasks._TASKS
        assert t.get_name() == "test:waiter"

        evt.set()
        await t

    @pytest.mark.asyncio
    async def test_removes_from_active_when_done(self):
        async def quick():
            return None

        t = tasks.spawn("test:quick", quick())
        await t
        assert t not in tasks._TASKS
        assert t not in tasks.active()

    @pytest.mark.asyncio
    async def test_count_and_active_track_running(self):
        evt = asyncio.Event()

        async def waiter():
            await evt.wait()

        a = tasks.spawn("test:a", waiter())
        b = tasks.spawn("test:b", waiter())
        assert tasks.count() == 2
        assert {t.get_name() for t in tasks.active()} == {"test:a", "test:b"}

        evt.set()
        await asyncio.gather(a, b)
        assert tasks.count() == 0


class TestOutcomes:
    @pytest.mark.asyncio
    async def test_success_increments_ok_metric(self):
        async def ok():
            return None

        with patch("core.runtime.tasks.metrics.task_outcome_total") as m:
            t = tasks.spawn("test:ok", ok())
            await t
            # Allow done_callback to fire.
            await asyncio.sleep(0)
            m.labels.assert_called_with(name="test:ok", outcome="ok")
            m.labels.return_value.inc.assert_called()

    @pytest.mark.asyncio
    async def test_exception_logs_and_increments_error_metric(self, caplog):
        async def boom():
            raise RuntimeError("kaboom")

        with (
            patch("core.runtime.tasks.metrics.task_outcome_total") as m,
            caplog.at_level(
                logging.ERROR,
                logger="bot.runtime.tasks",
            ),
        ):
            t = tasks.spawn("test:boom", boom())
            with pytest.raises(RuntimeError):
                await t
            await asyncio.sleep(0)
            m.labels.assert_called_with(name="test:boom", outcome="error")
            assert any("test:boom" in r.message for r in caplog.records)

    @pytest.mark.asyncio
    async def test_cancellation_increments_cancelled_metric(self):
        async def waiter():
            await asyncio.sleep(60)

        with patch("core.runtime.tasks.metrics.task_outcome_total") as m:
            t = tasks.spawn("test:cancelled", waiter())
            t.cancel()
            with pytest.raises(asyncio.CancelledError):
                await t
            await asyncio.sleep(0)
            m.labels.assert_called_with(name="test:cancelled", outcome="cancelled")


class TestCancelAll:
    @pytest.mark.asyncio
    async def test_cancels_running_tasks_only(self):
        async def waiter():
            await asyncio.sleep(60)

        async def done():
            return None

        long1 = tasks.spawn("test:long1", waiter())
        long2 = tasks.spawn("test:long2", waiter())
        short = tasks.spawn("test:short", done())
        await short  # finished naturally

        tasks.cancel_all()
        # Give the event loop a tick to process cancellations.
        await asyncio.gather(long1, long2, return_exceptions=True)
        assert long1.cancelled()
        assert long2.cancelled()
        assert not short.cancelled()
