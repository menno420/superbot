"""Behavioural tests for ``bot1._drive_close_on_lifecycle_request``.

The close-driver is the single executor for both SIGTERM-driven
shutdown and ``!restart``-driven restart: cogs and signal handlers
only record intent via ``core.runtime.lifecycle``; this watchdog turns
that intent into ``bot.close()`` so ``main()``'s finally block can run
cleanup.

These tests verify the close-driver contract without booting the real
bot, by monkeypatching the module-level ``bot`` and ``reporter`` that
the driver reads from globals at call time.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

import bot1
from core.runtime import lifecycle


@pytest.fixture(autouse=True)
def _reset_lifecycle_state() -> None:
    """Match the lifecycle test suite — autouse so module-level state
    cannot leak between cases (the lifecycle module holds a process-wide
    phase, pending request, and event buffer)."""
    lifecycle.reset_for_tests()
    yield
    lifecycle.reset_for_tests()


class _FakeBot:
    """Minimal stand-in for ``commands.Bot`` exposing only ``close``."""

    def __init__(self) -> None:
        self.close_calls = 0

    async def close(self) -> None:
        self.close_calls += 1


class _FakeReporter:
    def __init__(self) -> None:
        self.calls: list[Any] = []

    async def on_lifecycle_close_beginning(self, pending: Any) -> None:
        self.calls.append(("close_beginning", pending))


def _install_fast_poll(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make the driver loop iterate fast enough to fit a test."""
    monkeypatch.setattr(bot1, "_LIFECYCLE_CLOSE_POLL_INTERVAL", 0.01)


@pytest.mark.asyncio
async def test_shutdown_pending_drives_bot_close(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SIGTERM intent (``request_shutdown``) must reach ``bot.close()``.

    This is the regression this PR exists to fix: previously the driver
    only acted on restart intent, so a plain shutdown left the bot in
    DRAINING with ``bot.start(...)`` never unwinding.
    """
    fake_bot = _FakeBot()
    monkeypatch.setattr(bot1, "bot", fake_bot)
    monkeypatch.setattr(bot1, "reporter", None)
    _install_fast_poll(monkeypatch)

    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    lifecycle.request_shutdown(reason="sigterm")
    assert lifecycle.get_phase() is lifecycle.Phase.DRAINING

    await asyncio.wait_for(bot1._drive_close_on_lifecycle_request(), timeout=2.0)

    assert fake_bot.close_calls == 1


@pytest.mark.asyncio
async def test_restart_pending_drives_bot_close(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``!restart`` intent (``request_restart``) must still reach
    ``bot.close()`` — the generalised driver must not regress the
    behaviour the old restart-only driver provided."""
    fake_bot = _FakeBot()
    monkeypatch.setattr(bot1, "bot", fake_bot)
    monkeypatch.setattr(bot1, "reporter", None)
    _install_fast_poll(monkeypatch)

    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    lifecycle.request_restart(reason="!restart", actor="op")
    assert lifecycle.get_phase() is lifecycle.Phase.DRAINING

    await asyncio.wait_for(bot1._drive_close_on_lifecycle_request(), timeout=2.0)

    assert fake_bot.close_calls == 1


@pytest.mark.asyncio
async def test_no_close_when_phase_past_draining(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A pending request alone is not enough — the driver must wait
    until the phase reaches DRAINING.  Once cleanup has already started
    (SHUTTING_DOWN), firing close again would re-enter the teardown
    path."""
    fake_bot = _FakeBot()
    monkeypatch.setattr(bot1, "bot", fake_bot)
    monkeypatch.setattr(bot1, "reporter", None)
    _install_fast_poll(monkeypatch)

    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    lifecycle.request_shutdown(reason="sigterm")
    lifecycle.set_phase(
        lifecycle.Phase.SHUTTING_DOWN,
        reason="finalizer_started",
    )
    assert lifecycle.get_pending() is not None
    assert lifecycle.get_phase() is lifecycle.Phase.SHUTTING_DOWN

    task = asyncio.create_task(bot1._drive_close_on_lifecycle_request())
    await asyncio.sleep(0.05)
    task.cancel()
    result = await task

    assert result is None
    assert fake_bot.close_calls == 0


@pytest.mark.asyncio
async def test_webhook_fires_before_bot_close(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Operators must see the close-beginning embed before the bot
    starts tearing down — verifies call ordering and that the
    reporter receives the actual ``PendingShutdown`` object."""
    order: list[str] = []

    class OrderedBot:
        async def close(self) -> None:
            order.append("close")

    class OrderedReporter:
        async def on_lifecycle_close_beginning(self, pending: Any) -> None:
            order.append("webhook")
            assert pending.kind == "shutdown"
            assert pending.reason == "sigterm"

    monkeypatch.setattr(bot1, "bot", OrderedBot())
    monkeypatch.setattr(bot1, "reporter", OrderedReporter())
    _install_fast_poll(monkeypatch)

    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    lifecycle.request_shutdown(reason="sigterm")

    await asyncio.wait_for(bot1._drive_close_on_lifecycle_request(), timeout=2.0)

    assert order == ["webhook", "close"]


@pytest.mark.asyncio
async def test_close_driver_records_close_executing_lifecycle_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The close-driver records a ``close_executing`` lifecycle event
    right before ``bot.close()`` so ``!platform runtime`` distinguishes
    "intent recorded but executor never ran" from "executor ran".

    Asserts both that the event exists and that it carries the kind in
    metadata, so the event is informative without requiring a custom
    embed.
    """
    fake_bot = _FakeBot()
    monkeypatch.setattr(bot1, "bot", fake_bot)
    monkeypatch.setattr(bot1, "reporter", None)
    _install_fast_poll(monkeypatch)

    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    lifecycle.request_shutdown(reason="sigterm", actor="signal_handler")

    await asyncio.wait_for(bot1._drive_close_on_lifecycle_request(), timeout=2.0)

    event_names = [e.name for e in lifecycle.get_recent_events()]
    assert "close_executing" in event_names
    close_event = next(
        e for e in lifecycle.get_recent_events() if e.name == "close_executing"
    )
    assert close_event.metadata == {"kind": "shutdown"}
    assert close_event.actor == "signal_handler"
    assert close_event.reason == "sigterm"


@pytest.mark.asyncio
async def test_idle_cancellation_exits_cleanly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With no pending lifecycle request the driver polls indefinitely;
    cancellation while idle must exit cleanly (no exception escapes).

    The supervisor's ``cancel_all()`` calls ``task.cancel()`` on every
    supervised task at shutdown and then awaits them in a 5 s drain
    window.  Catching ``CancelledError`` and returning ``None`` keeps
    the supervisor's drain summary clean (no spurious failures in the
    on-error hook)."""
    fake_bot = _FakeBot()
    monkeypatch.setattr(bot1, "bot", fake_bot)
    monkeypatch.setattr(bot1, "reporter", None)
    _install_fast_poll(monkeypatch)

    assert lifecycle.get_pending() is None

    task = asyncio.create_task(bot1._drive_close_on_lifecycle_request())
    await asyncio.sleep(0.05)
    task.cancel()
    result = await task

    assert result is None
    assert fake_bot.close_calls == 0


@pytest.mark.asyncio
async def test_close_timeout_force_exits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When ``bot.close()`` hangs past the timeout the driver must
    invoke ``os._exit(1)`` so the orchestrator respawns rather than
    leaving the runtime lock wedged until its 90 s TTL."""

    class HangingBot:
        async def close(self) -> None:
            await asyncio.sleep(60.0)

    monkeypatch.setattr(bot1, "bot", HangingBot())
    monkeypatch.setattr(bot1, "reporter", None)
    monkeypatch.setattr(bot1, "LIFECYCLE_CLOSE_TIMEOUT_SECONDS", 0.05)
    _install_fast_poll(monkeypatch)

    exit_calls: list[int] = []

    class _ForceExit(BaseException):
        """Sentinel so the test process itself does not exit."""

    def _fake_exit(code: int) -> None:
        exit_calls.append(code)
        raise _ForceExit

    monkeypatch.setattr(bot1.os, "_exit", _fake_exit)

    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    lifecycle.request_shutdown(reason="sigterm")

    with pytest.raises(_ForceExit):
        await asyncio.wait_for(
            bot1._drive_close_on_lifecycle_request(),
            timeout=2.0,
        )

    assert exit_calls == [1]


def test_should_drive_lifecycle_close_predicate() -> None:
    """Predicate-level coverage so the eligibility logic is exercised
    independently of the polling loop.  Used by tests and source
    invariants to keep the driver logic in one place."""
    assert bot1._should_drive_lifecycle_close() is False

    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    assert bot1._should_drive_lifecycle_close() is False

    lifecycle.request_shutdown(reason="sigterm")
    assert lifecycle.get_phase() is lifecycle.Phase.DRAINING
    assert bot1._should_drive_lifecycle_close() is True

    lifecycle.set_phase(lifecycle.Phase.SHUTTING_DOWN)
    assert bot1._should_drive_lifecycle_close() is False
