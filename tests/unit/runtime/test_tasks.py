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


class TestCancelByPrefix:
    @pytest.mark.asyncio
    async def test_cancels_only_matching_prefix(self):
        async def waiter():
            await asyncio.sleep(60)

        a1 = tasks.spawn("counting:a", waiter())
        a2 = tasks.spawn("counting:b", waiter())
        b1 = tasks.spawn("rps:a", waiter())
        b2 = tasks.spawn("rps:b", waiter())

        cancelled = tasks.cancel_by_prefix("counting:")
        # Only wait on the counting:* tasks; rps:* must still be running.
        await asyncio.gather(a1, a2, return_exceptions=True)

        assert cancelled == 2
        assert a1.cancelled() and a2.cancelled()
        assert not b1.cancelled() and not b2.cancelled()

        # Cleanup the leftover rps:* tasks for the next test.
        b1.cancel()
        b2.cancel()
        await asyncio.gather(b1, b2, return_exceptions=True)

    @pytest.mark.asyncio
    async def test_skips_already_completed_tasks(self):
        async def done():
            return None

        finished = tasks.spawn("counting:finished", done())
        await finished

        cancelled = tasks.cancel_by_prefix("counting:")
        assert cancelled == 0  # already-done tasks not counted

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_match(self):
        async def waiter():
            await asyncio.sleep(60)

        t = tasks.spawn("counting:only", waiter())
        try:
            cancelled = tasks.cancel_by_prefix("rps:")
            assert cancelled == 0
            assert not t.cancelled()
        finally:
            t.cancel()
            await asyncio.gather(t, return_exceptions=True)


# ---------------------------------------------------------------------------
# PR-02a — on_error hook
# ---------------------------------------------------------------------------


class TestOnErrorHook:
    @pytest.mark.asyncio
    async def test_on_error_invoked_on_exception(self):
        async def boom():
            raise RuntimeError("kaboom")

        captured: list[tuple[str, str]] = []

        def hook(task: asyncio.Task, exc: BaseException) -> None:
            captured.append((task.get_name(), type(exc).__name__))

        t = tasks.spawn("test:on_error", boom(), on_error=hook)
        with pytest.raises(RuntimeError):
            await t
        await asyncio.sleep(0)  # let done callback run
        assert captured == [("test:on_error", "RuntimeError")]

    @pytest.mark.asyncio
    async def test_on_error_not_invoked_on_clean_exit(self):
        captured: list[object] = []

        def hook(task: asyncio.Task, exc: BaseException) -> None:
            captured.append(exc)

        async def ok():
            return None

        t = tasks.spawn("test:clean", ok(), on_error=hook)
        await t
        await asyncio.sleep(0)
        assert captured == []

    @pytest.mark.asyncio
    async def test_on_error_not_invoked_on_cancellation(self):
        captured: list[object] = []

        def hook(task: asyncio.Task, exc: BaseException) -> None:
            captured.append(exc)

        async def waiter():
            await asyncio.sleep(60)

        t = tasks.spawn("test:cancel", waiter(), on_error=hook)
        t.cancel()
        with pytest.raises(asyncio.CancelledError):
            await t
        await asyncio.sleep(0)
        assert captured == []

    @pytest.mark.asyncio
    async def test_on_error_exception_is_isolated(self, caplog):
        """A raising on_error hook must not propagate or mask the metric."""

        async def boom():
            raise RuntimeError("original")

        def bad_hook(task: asyncio.Task, exc: BaseException) -> None:
            raise ValueError("hook raised")

        with (
            patch("core.runtime.tasks.metrics.task_outcome_total") as m,
            caplog.at_level(logging.ERROR, logger="bot.runtime.tasks"),
        ):
            t = tasks.spawn("test:bad_hook", boom(), on_error=bad_hook)
            with pytest.raises(RuntimeError):
                await t
            await asyncio.sleep(0)

        m.labels.assert_called_with(name="test:bad_hook", outcome="error")
        # The hook's exception is logged but does not crash the loop.
        assert any("hook" in r.message.lower() for r in caplog.records)

    @pytest.mark.asyncio
    async def test_on_error_hook_dict_cleared_after_done(self):
        async def boom():
            raise RuntimeError("kaboom")

        def hook(task: asyncio.Task, exc: BaseException) -> None:
            pass

        t = tasks.spawn("test:cleanup", boom(), on_error=hook)
        with pytest.raises(RuntimeError):
            await t
        await asyncio.sleep(0)
        assert t not in tasks._ON_ERROR_HOOKS
