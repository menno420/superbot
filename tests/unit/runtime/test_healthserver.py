"""Tests for healthserver bind-failure semantics — Phase S2.4 / O-2b.

The crucial property is that the bind step (``runner.setup`` /
``site.start``) is INSIDE the try/finally so:

  1. ``runner.cleanup`` always runs even if the bind raises.
  2. The exception propagates to the supervised task's done-callback
     (validated indirectly via the exception escaping the coroutine).
  3. ``ready_event`` is set ONLY after successful bind, never on
     failure — so bot1.main's bind-ready wait can fail-fast.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_bot() -> MagicMock:
    bot = MagicMock()
    bot.guilds = []
    bot.latency = 0.0
    bot.is_ready = MagicMock(return_value=True)
    bot.user = MagicMock()
    return bot


@pytest.mark.asyncio
async def test_successful_bind_sets_ready_event():
    """Happy path: bind succeeds, ready_event is set."""
    from healthserver import start_health_server

    runner = MagicMock()
    runner.setup = AsyncMock()
    runner.cleanup = AsyncMock()
    site = MagicMock()
    site.start = AsyncMock()

    ready = asyncio.Event()

    with (
        patch("healthserver.web.AppRunner", return_value=runner),
        patch("healthserver.web.TCPSite", return_value=site),
    ):
        # Schedule start_health_server and cancel it once ready fires —
        # otherwise it would block forever on the create_future() sleep.
        task = asyncio.create_task(start_health_server(_make_bot(), ready_event=ready))
        await asyncio.wait_for(ready.wait(), timeout=1.0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    assert ready.is_set()
    runner.setup.assert_awaited_once()
    site.start.assert_awaited_once()
    # Cleanup runs on the cancellation finally-path.
    runner.cleanup.assert_awaited_once()


@pytest.mark.asyncio
async def test_bind_failure_does_not_set_ready_event():
    """site.start raising means bot1.main's bind-ready wait must NOT proceed."""
    from healthserver import start_health_server

    runner = MagicMock()
    runner.setup = AsyncMock()
    runner.cleanup = AsyncMock()
    site = MagicMock()
    site.start = AsyncMock(side_effect=OSError("port 8080 already in use"))

    ready = asyncio.Event()

    with (
        patch("healthserver.web.AppRunner", return_value=runner),
        patch("healthserver.web.TCPSite", return_value=site),
        pytest.raises(OSError, match="already in use"),
    ):
        await start_health_server(_make_bot(), ready_event=ready)

    assert not ready.is_set()  # the crucial assertion
    runner.cleanup.assert_awaited_once()  # cleanup ran despite the raise


@pytest.mark.asyncio
async def test_setup_failure_still_runs_cleanup():
    """runner.setup raising — cleanup still runs and exception propagates."""
    from healthserver import start_health_server

    runner = MagicMock()
    runner.setup = AsyncMock(side_effect=RuntimeError("aiohttp setup blew up"))
    runner.cleanup = AsyncMock()

    ready = asyncio.Event()

    with (
        patch("healthserver.web.AppRunner", return_value=runner),
        pytest.raises(RuntimeError, match="aiohttp setup blew up"),
    ):
        await start_health_server(_make_bot(), ready_event=ready)

    assert not ready.is_set()
    runner.cleanup.assert_awaited_once()


@pytest.mark.asyncio
async def test_no_ready_event_arg_does_not_crash():
    """The ready_event argument is optional — must still bind cleanly."""
    from healthserver import start_health_server

    runner = MagicMock()
    runner.setup = AsyncMock()
    runner.cleanup = AsyncMock()
    site = MagicMock()
    site.start = AsyncMock()

    with (
        patch("healthserver.web.AppRunner", return_value=runner),
        patch("healthserver.web.TCPSite", return_value=site),
    ):
        # No ready_event passed; cancel after a quick scheduler tick.
        task = asyncio.create_task(start_health_server(_make_bot()))
        await asyncio.sleep(0)  # let setup + start run
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    site.start.assert_awaited_once()


# ---------------------------------------------------------------------------
# Webhook reporter — new methods added in S2.4
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_webhook_reporter_has_health_failure_and_task_died_methods():
    """Static check that bot1's _on_app_task_done has the methods to call."""
    from services.webhook_reporter import WebhookReporter

    assert hasattr(WebhookReporter, "on_health_startup_failed")
    assert hasattr(WebhookReporter, "on_app_task_died")


@pytest.mark.asyncio
async def test_on_app_task_died_posts_embed():
    """Verify the dead-task webhook actually sends an embed."""
    from services.webhook_reporter import WebhookReporter

    reporter = WebhookReporter(url="https://example/wh")
    reporter._send = AsyncMock()  # type: ignore[method-assign]

    error = RuntimeError("session_gc crashed")
    await reporter.on_app_task_died("session_gc", error)

    reporter._send.assert_awaited_once()
    embed = reporter._send.await_args.args[0]
    assert "session_gc" in embed.description
    assert "RuntimeError" in embed.description


@pytest.mark.asyncio
async def test_on_health_startup_failed_posts_embed():
    from services.webhook_reporter import WebhookReporter

    reporter = WebhookReporter(url="https://example/wh")
    reporter._send = AsyncMock()  # type: ignore[method-assign]

    error = OSError("port in use")
    await reporter.on_health_startup_failed(error)

    reporter._send.assert_awaited_once()
    embed = reporter._send.await_args.args[0]
    assert "Aborting" in embed.description
    assert "port in use" in embed.description
