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


# ---------------------------------------------------------------------------
# /ready lifecycle-awareness
#
# /ready must consult lifecycle.can_accept_commands() in addition to
# bot.is_ready() so the orchestrator stops routing traffic to a replica
# that is draining for SIGTERM / restart.  Without this, bot.is_ready()
# stays True for the early part of the DRAINING window and the load
# balancer keeps sending requests at a replica that has stopped
# admitting commands.
# ---------------------------------------------------------------------------


def _ready_request_for(bot) -> MagicMock:
    """Build a minimal aiohttp Request mock for ``_ready_handler``."""
    request = MagicMock()
    request.app = {"bot": bot}
    return request


@pytest.fixture(autouse=False)
def _reset_lifecycle():
    """Reset lifecycle state around lifecycle-aware /ready tests so they
    cannot leak phase or pending state into one another."""
    from core.runtime import lifecycle

    lifecycle.reset_for_tests()
    yield
    lifecycle.reset_for_tests()


@pytest.mark.asyncio
async def test_ready_returns_200_when_ready_and_lifecycle_accepts_commands(
    _reset_lifecycle,
):
    """Happy path: gateway up + lifecycle RUNNING → 200 with phase
    and ``accepting_commands: True`` in the payload."""
    import json as _json

    from core.runtime import lifecycle
    from healthserver import _ready_handler

    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    bot = _make_bot()  # is_ready=True

    response = await _ready_handler(_ready_request_for(bot))

    assert response.status == 200
    body = _json.loads(response.text)
    assert body["status"] == "ready"
    assert body["phase"] == "RUNNING"
    assert body["accepting_commands"] is True


@pytest.mark.asyncio
async def test_ready_returns_503_when_gateway_not_ready(_reset_lifecycle):
    """Existing behavior preserved: bot.is_ready() False → 503 with
    ``gateway_not_ready`` reason regardless of lifecycle state."""
    import json as _json

    from core.runtime import lifecycle
    from healthserver import _ready_handler

    lifecycle.set_phase(lifecycle.Phase.STARTING)
    bot = _make_bot()
    bot.is_ready = MagicMock(return_value=False)

    response = await _ready_handler(_ready_request_for(bot))

    assert response.status == 503
    body = _json.loads(response.text)
    assert body["status"] == "not_ready"
    assert body["reason"] == "gateway_not_ready"
    assert body["phase"] == "STARTING"
    assert body["accepting_commands"] is True  # STARTING still admits


@pytest.mark.asyncio
async def test_ready_returns_503_when_lifecycle_draining(_reset_lifecycle):
    """The regression this PR is preventing: SIGTERM moves lifecycle into
    DRAINING but bot.is_ready() can still be True for part of the window.
    /ready must return 503 in that window so the load balancer stops
    routing traffic."""
    import json as _json

    from core.runtime import lifecycle
    from healthserver import _ready_handler

    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    lifecycle.request_shutdown(reason="sigterm")
    assert lifecycle.get_phase() is lifecycle.Phase.DRAINING

    bot = _make_bot()  # is_ready still True
    response = await _ready_handler(_ready_request_for(bot))

    assert response.status == 503
    body = _json.loads(response.text)
    assert body["status"] == "not_ready"
    assert body["phase"] == "DRAINING"
    assert body["accepting_commands"] is False
    assert body["reason"] == "lifecycle_DRAINING"


@pytest.mark.parametrize(
    "phase",
    [
        "SHUTTING_DOWN",
        "RESTARTING",
        "STOPPED",
    ],
)
@pytest.mark.asyncio
async def test_ready_returns_503_in_every_terminal_phase(_reset_lifecycle, phase: str):
    """All non-admitting phases past DRAINING must also produce 503.
    Belt-and-suspenders parametrization so a future lifecycle-state
    addition does not silently re-enable 200 in a draining phase."""
    import json as _json

    from core.runtime import lifecycle
    from healthserver import _ready_handler

    lifecycle.set_phase(getattr(lifecycle.Phase, phase))
    bot = _make_bot()
    response = await _ready_handler(_ready_request_for(bot))

    assert response.status == 503
    body = _json.loads(response.text)
    assert body["accepting_commands"] is False
    assert body["phase"] == phase
    assert body["reason"] == f"lifecycle_{phase}"


# ---------------------------------------------------------------------------
# /lifecycle — diagnostic dump of full lifecycle snapshot
#
# Always 200 (not a probe, just a diagnostic).  Operators curl this
# during incidents when Discord is wedged but HTTP is still serving.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_lifecycle_endpoint_returns_full_snapshot_as_json(_reset_lifecycle):
    """The endpoint returns 200 with the same payload shape as
    ``diagnostics_snapshot()`` — phase, pending, recent_events, etc."""
    import json as _json

    from core.runtime import lifecycle
    from healthserver import _lifecycle_handler

    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    lifecycle.request_shutdown("sigterm", actor="signal_handler")

    request = MagicMock()
    response = await _lifecycle_handler(request)

    assert response.status == 200
    body = _json.loads(response.text)
    assert body["phase"] == "DRAINING"
    assert body["pending"]["kind"] == "shutdown"
    assert body["pending"]["actor"] == "signal_handler"
    # Recent events should include the shutdown_requested and DRAINING
    # transition.
    event_names = [e["name"] for e in body["recent_events"]]
    assert "shutdown_requested" in event_names
    assert "phase:DRAINING" in event_names


@pytest.mark.asyncio
async def test_lifecycle_endpoint_returns_200_even_in_terminal_phase(_reset_lifecycle):
    """Unlike /ready (which returns 503 in terminal phases), /lifecycle
    is always 200 — operators need to query it precisely WHEN the bot
    is in a terminal phase, to understand why."""
    import json as _json

    from core.runtime import lifecycle
    from healthserver import _lifecycle_handler

    lifecycle.set_phase(lifecycle.Phase.STOPPED)

    request = MagicMock()
    response = await _lifecycle_handler(request)

    assert response.status == 200
    body = _json.loads(response.text)
    assert body["phase"] == "STOPPED"
    assert body["can_accept_commands"] is False
    assert body["is_shutting_down"] is True


@pytest.mark.asyncio
async def test_lifecycle_endpoint_is_registered_on_the_router():
    """Belt-and-suspenders: assert the route is actually registered so a
    future refactor doesn't quietly drop the endpoint."""
    import asyncio

    from healthserver import start_health_server

    runner = MagicMock()
    runner.setup = AsyncMock()
    runner.cleanup = AsyncMock()
    site = MagicMock()
    site.start = AsyncMock()
    app_captured: list = []

    real_app_runner_cls = None

    def _capture_app(app, *args, **kwargs):
        app_captured.append(app)
        return runner

    with (
        patch("healthserver.web.AppRunner", side_effect=_capture_app),
        patch("healthserver.web.TCPSite", return_value=site),
    ):
        ready = asyncio.Event()
        task = asyncio.create_task(
            start_health_server(_make_bot(), ready_event=ready),
        )
        await asyncio.wait_for(ready.wait(), timeout=1.0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    assert app_captured, "AppRunner was not constructed"
    app = app_captured[0]
    paths = {route.resource.canonical for route in app.router.routes()}
    assert "/lifecycle" in paths
