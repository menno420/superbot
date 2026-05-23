"""Behavioural tests for ``bot1._drive_close_on_lifecycle_request`` — LP-5.

Covers:
  * SIGTERM (shutdown) intent drives ``bot.close()``.
  * Restart intent drives ``bot.close()`` (LP-3 path preserved).
  * No pending intent → driver keeps polling, never calls close.
  * Driver is a no-op once the phase has moved past DRAINING (the
    finally block is already running).
  * Webhook ``on_lifecycle_close_beginning`` is invoked once before
    the close, with the pending request as its argument.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import bot1
from core.runtime import lifecycle


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    """Each test runs against a fresh lifecycle state and a tiny poll
    interval so the driver loops quickly."""
    lifecycle.reset_for_tests()
    with patch.object(bot1, "_LIFECYCLE_CLOSE_POLL_INTERVAL", 0.01):
        yield
    lifecycle.reset_for_tests()


async def _run_driver_until_done(timeout: float = 1.0) -> None:
    """Invoke the driver coroutine with a real loop, bounded so a
    misconfigured test does not hang."""
    await asyncio.wait_for(
        bot1._drive_close_on_lifecycle_request(),
        timeout=timeout,
    )


@pytest.mark.asyncio
async def test_driver_closes_bot_when_shutdown_pending() -> None:
    """LP-5: a pending shutdown request drives ``bot.close()`` to
    completion. The close coroutine is awaited; the driver returns
    cleanly afterwards."""
    close_mock = AsyncMock()
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    lifecycle.request_shutdown("sigterm", actor="signal_handler")

    with (
        patch.object(bot1, "bot", MagicMock(close=close_mock)),
        patch.object(bot1, "reporter", None),
    ):
        await _run_driver_until_done()

    close_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_driver_closes_bot_when_restart_pending() -> None:
    """LP-3 (preserved through LP-5): a pending restart request also
    drives ``bot.close()``."""
    close_mock = AsyncMock()
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    lifecycle.request_restart("!restart", actor="alice#0001")

    with (
        patch.object(bot1, "bot", MagicMock(close=close_mock)),
        patch.object(bot1, "reporter", None),
    ):
        await _run_driver_until_done()

    close_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_driver_is_noop_when_phase_already_past_draining() -> None:
    """If the finally block is already running (phase is
    ``SHUTTING_DOWN`` or later), the driver must not call ``bot.close()``
    again — that would race the cleanup."""
    close_mock = AsyncMock()
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    lifecycle.request_shutdown("sigterm")
    # Simulate the finally block having already taken over.
    lifecycle.set_phase(lifecycle.Phase.SHUTTING_DOWN, reason="main_finally")

    with (
        patch.object(bot1, "bot", MagicMock(close=close_mock)),
        patch.object(bot1, "reporter", None),
    ):
        await _run_driver_until_done()

    close_mock.assert_not_called()


@pytest.mark.asyncio
async def test_driver_fires_webhook_before_closing() -> None:
    """Operator alert: ``reporter.on_lifecycle_close_beginning`` is
    invoked exactly once, with the pending request, before
    ``bot.close()`` is awaited."""
    close_mock = AsyncMock()
    webhook_mock = AsyncMock()
    reporter = MagicMock()
    reporter.on_lifecycle_close_beginning = webhook_mock

    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    lifecycle.request_shutdown("sigterm", actor="signal_handler")
    pending = lifecycle.get_pending()

    with (
        patch.object(bot1, "bot", MagicMock(close=close_mock)),
        patch.object(bot1, "reporter", reporter),
    ):
        await _run_driver_until_done()

    webhook_mock.assert_awaited_once_with(pending)
    close_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_driver_loops_until_cancelled_when_no_pending() -> None:
    """With no pending request the driver keeps polling; cancellation
    causes the driver to return cleanly (the inner ``except
    CancelledError: return`` swallows the cancel by design so the
    supervised-task supervisor records ``cancelled`` cleanly rather
    than ``error``)."""
    close_mock = AsyncMock()
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    # No request issued.

    with (
        patch.object(bot1, "bot", MagicMock(close=close_mock)),
        patch.object(bot1, "reporter", None),
    ):
        task = asyncio.create_task(bot1._drive_close_on_lifecycle_request())
        # Yield a few times so the driver enters its sleep, then cancel.
        for _ in range(3):
            await asyncio.sleep(0.01)
        task.cancel()
        # Driver returns cleanly on cancellation (intentional design —
        # cancellation is the shutdown signal, not an error).
        await task

    close_mock.assert_not_called()
    assert task.done()
    # No exception raised by the driver itself.
    assert task.exception() is None
