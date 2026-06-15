"""``services.runtime`` orchestration tests.

Covers:

* :class:`BootIdFilter` stamps ``boot_id`` on every record.
* :func:`acquire_lock_or_exit` raises ``SystemExit(0)`` when another
  replica holds the lock, ``SystemExit(1)`` when the DB call fails.
* :func:`run_heartbeat_loop` calls ``runtime_lock.heartbeat`` on every
  tick and exits when the lock is stolen.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from services import runtime
from utils.db import runtime_lock as rl_db


def test_boot_id_is_a_uuid_and_stable_across_imports():
    assert isinstance(runtime.BOOT_ID, uuid.UUID)
    # Re-import shouldn't change it (module-level singleton).
    from services import runtime as second
    assert second.BOOT_ID == runtime.BOOT_ID


def test_boot_id_filter_stamps_boot_id():
    boot = uuid.uuid4()
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname=__file__, lineno=1,
        msg="hello", args=None, exc_info=None,
    )
    rf = runtime.BootIdFilter(boot)
    assert rf.filter(record) is True
    assert record.boot_id == str(boot)


def test_install_boot_id_logging_is_idempotent():
    handler = logging.StreamHandler()
    runtime.install_boot_id_logging([handler])
    runtime.install_boot_id_logging([handler])
    boot_filters = [f for f in handler.filters if isinstance(f, runtime.BootIdFilter)]
    assert len(boot_filters) == 1


@pytest.mark.asyncio
async def test_acquire_lock_or_exit_returns_when_acquired():
    fake_result = rl_db.AcquireResult(
        acquired=True,
        holder_boot_id=runtime.BOOT_ID,
        holder_heartbeat_at=None,
        reason="acquired",
    )
    with patch.object(rl_db, "try_acquire", AsyncMock(return_value=fake_result)):
        # No exception; returns normally.
        await runtime.acquire_lock_or_exit()


@pytest.mark.asyncio
async def test_acquire_lock_or_exit_exits_zero_when_held_by_peer():
    """LP-4: with ``boot_wait_seconds=0`` the loop short-circuits to
    the pre-LP-4 single-shot semantics — peer held → SystemExit(0)."""
    fake_result = rl_db.AcquireResult(
        acquired=False,
        holder_boot_id=uuid.uuid4(),
        holder_heartbeat_at=None,
        reason="row_fresh",
    )
    with patch.object(rl_db, "try_acquire", AsyncMock(return_value=fake_result)):
        with pytest.raises(SystemExit) as exc_info:
            await runtime.acquire_lock_or_exit(boot_wait_seconds=0)
        assert exc_info.value.code == 0


@pytest.mark.asyncio
async def test_acquire_lock_or_exit_exits_one_when_db_fails():
    with patch.object(
        rl_db,
        "try_acquire",
        AsyncMock(side_effect=RuntimeError("db down")),
    ):
        with pytest.raises(SystemExit) as exc_info:
            await runtime.acquire_lock_or_exit(boot_wait_seconds=0)
        assert exc_info.value.code == 1


@pytest.mark.asyncio
async def test_acquire_lock_or_exit_polls_until_peer_releases():
    """LP-4: when a fresh peer holds the lock, the loop should retry
    on each tick until the peer releases (acquired=True). The total
    wait is bounded by ``boot_wait_seconds`` but the loop exits as
    soon as acquisition succeeds."""
    held = rl_db.AcquireResult(
        acquired=False,
        holder_boot_id=uuid.uuid4(),
        holder_heartbeat_at=None,
        reason="row_fresh",
    )
    acquired = rl_db.AcquireResult(
        acquired=True,
        holder_boot_id=runtime.BOOT_ID,
        holder_heartbeat_at=None,
        reason="acquired",
    )
    # First two attempts: peer holds. Third: peer released, we acquire.
    try_acquire = AsyncMock(side_effect=[held, held, acquired])
    sleep_mock = AsyncMock()

    with (
        patch.object(rl_db, "try_acquire", try_acquire),
        patch("services.runtime.asyncio.sleep", sleep_mock),
    ):
        await runtime.acquire_lock_or_exit(
            boot_wait_seconds=60.0,
            boot_poll_seconds=0.01,
        )

    assert try_acquire.await_count == 3
    # Two retries → two sleeps.
    assert sleep_mock.await_count == 2


@pytest.mark.asyncio
async def test_acquire_lock_or_exit_exits_zero_after_wait_timeout():
    """LP-4: a peer that never releases causes the loop to give up
    after ``boot_wait_seconds`` and exit with code 0 (idle, not crash)."""
    fake_result = rl_db.AcquireResult(
        acquired=False,
        holder_boot_id=uuid.uuid4(),
        holder_heartbeat_at=None,
        reason="row_fresh",
    )
    try_acquire = AsyncMock(return_value=fake_result)
    sleep_mock = AsyncMock()

    with (
        patch.object(rl_db, "try_acquire", try_acquire),
        patch("services.runtime.asyncio.sleep", sleep_mock),
    ):
        with pytest.raises(SystemExit) as exc_info:
            # Use a tiny budget so the test finishes quickly without
            # mocking ``time.monotonic``.
            await runtime.acquire_lock_or_exit(
                boot_wait_seconds=0.05,
                boot_poll_seconds=0.01,
            )
        assert exc_info.value.code == 0
    # At least two attempts: one immediate + one after a sleep before
    # the deadline elapses.
    assert try_acquire.await_count >= 2


@pytest.mark.asyncio
async def test_acquire_lock_or_exit_reads_env_knobs_when_args_omitted(
    monkeypatch: pytest.MonkeyPatch,
):
    """Env vars supply the defaults when the caller doesn't pass
    explicit ``boot_wait_seconds`` / ``boot_poll_seconds``."""
    fake_result = rl_db.AcquireResult(
        acquired=False,
        holder_boot_id=uuid.uuid4(),
        holder_heartbeat_at=None,
        reason="row_fresh",
    )
    monkeypatch.setenv("RUNTIME_LOCK_BOOT_WAIT_SECONDS", "0")
    monkeypatch.setenv("RUNTIME_LOCK_BOOT_POLL_SECONDS", "0")

    with patch.object(rl_db, "try_acquire", AsyncMock(return_value=fake_result)):
        with pytest.raises(SystemExit) as exc_info:
            await runtime.acquire_lock_or_exit()
        assert exc_info.value.code == 0


@pytest.mark.asyncio
async def test_acquire_lock_or_exit_falls_back_to_safe_defaults_on_bad_poll(
    caplog: pytest.LogCaptureFixture,
):
    """If poll >= wait, fall back to a safe poll value and warn so the
    operator sees the misconfiguration in logs."""
    fake_result = rl_db.AcquireResult(
        acquired=False,
        holder_boot_id=uuid.uuid4(),
        holder_heartbeat_at=None,
        reason="row_fresh",
    )
    sleep_mock = AsyncMock()
    with (
        patch.object(rl_db, "try_acquire", AsyncMock(return_value=fake_result)),
        patch("services.runtime.asyncio.sleep", sleep_mock),
        caplog.at_level(logging.WARNING, logger="bot.services.runtime"),
    ):
        with pytest.raises(SystemExit):
            await runtime.acquire_lock_or_exit(
                boot_wait_seconds=0.05,
                boot_poll_seconds=10.0,  # poll > wait
            )
    assert any(
        "BOOT_POLL_SECONDS" in record.message for record in caplog.records
    )


@pytest.mark.asyncio
async def test_run_heartbeat_loop_stops_immediately_if_event_already_set():
    stop = asyncio.Event()
    stop.set()
    with patch.object(rl_db, "heartbeat", AsyncMock(return_value=True)) as hb:
        await runtime.run_heartbeat_loop(stop, interval_seconds=0)
    # Loop exits before the first heartbeat when stop is pre-set.
    assert hb.await_count == 0


@pytest.mark.asyncio
async def test_run_heartbeat_loop_calls_heartbeat_before_stopping():
    stop = asyncio.Event()
    call_count = 0

    async def _hb(*_a, **_kw):
        nonlocal call_count
        call_count += 1
        stop.set()
        return True

    with patch.object(rl_db, "heartbeat", side_effect=_hb):
        await runtime.run_heartbeat_loop(stop, interval_seconds=0)
    assert call_count == 1


@pytest.mark.asyncio
async def test_run_heartbeat_loop_exits_process_when_lock_lost():
    stop = asyncio.Event()
    with patch.object(rl_db, "heartbeat", AsyncMock(return_value=False)):
        with patch("services.runtime.os._exit") as exit_mock:
            # _exit is patched, so the loop returns instead of terminating.
            # The loop will hit the wait timeout next; we set the stop
            # event to short-circuit it.
            exit_mock.side_effect = lambda code: stop.set()
            await runtime.run_heartbeat_loop(stop, interval_seconds=0)
            exit_mock.assert_called_with(1)


@pytest.mark.asyncio
async def test_run_heartbeat_loop_tolerates_single_transient_failure():
    stop = asyncio.Event()
    side_effects = [RuntimeError("blip"), True]

    async def _hb(*_a, **_kw):
        if side_effects:
            v = side_effects.pop(0)
            if isinstance(v, Exception):
                raise v
            return v
        # After the recovery, stop the loop.
        stop.set()
        return True

    with patch.object(rl_db, "heartbeat", side_effect=_hb):
        with patch("services.runtime.os._exit") as exit_mock:
            await runtime.run_heartbeat_loop(stop, interval_seconds=0)
            exit_mock.assert_not_called()


@pytest.mark.asyncio
async def test_release_lock_best_effort_swallows_exceptions():
    with patch.object(
        rl_db,
        "release",
        AsyncMock(side_effect=RuntimeError("db down")),
    ):
        # Must not raise.
        await runtime.release_lock_best_effort()


# ---------------------------------------------------------------------------
# runtime_lock_heartbeat_total metric — increments on every loop iteration
# with one of three outcomes: ok / error / lost.  Operators alert on a
# sustained non-zero ``error`` rate (DB issues) or any ``lost`` observation
# (split-brain).
# ---------------------------------------------------------------------------


def _heartbeat_counter_value(outcome: str) -> float:
    from services import metrics as _metrics

    return _metrics.runtime_lock_heartbeat_total.labels(outcome=outcome)._value.get()


@pytest.mark.asyncio
async def test_heartbeat_metric_increments_ok_on_successful_refresh():
    stop = asyncio.Event()
    before = _heartbeat_counter_value("ok")

    async def _hb(*_a, **_kw):
        stop.set()
        return True

    with patch.object(rl_db, "heartbeat", side_effect=_hb):
        await runtime.run_heartbeat_loop(stop, interval_seconds=0)

    assert _heartbeat_counter_value("ok") == before + 1


@pytest.mark.asyncio
async def test_heartbeat_metric_increments_error_on_exception():
    """Transient DB exception must surface as outcome=error so operators
    can graph DB connectivity issues separately from healthy refreshes."""
    stop = asyncio.Event()
    before_error = _heartbeat_counter_value("error")
    before_ok = _heartbeat_counter_value("ok")
    side_effects = [RuntimeError("blip"), True]

    async def _hb(*_a, **_kw):
        v = side_effects.pop(0)
        if isinstance(v, Exception):
            raise v
        # Stop the loop on the successful recovery so the test's
        # observation count is precise (no extra iterations).
        stop.set()
        return v

    with patch.object(rl_db, "heartbeat", side_effect=_hb), patch(
        "services.runtime.os._exit",
    ):
        await runtime.run_heartbeat_loop(stop, interval_seconds=0)

    assert _heartbeat_counter_value("error") == before_error + 1
    # The retry succeeded, so ok also incremented exactly once.
    assert _heartbeat_counter_value("ok") == before_ok + 1


@pytest.mark.asyncio
async def test_heartbeat_metric_increments_lost_when_peer_reclaims():
    """``UPDATE 0`` (peer reclaimed the lock) must surface as outcome=lost
    immediately before os._exit so the metric captures the split-brain
    moment even if the next Prometheus scrape happens after exit."""
    stop = asyncio.Event()
    before = _heartbeat_counter_value("lost")

    with patch.object(rl_db, "heartbeat", AsyncMock(return_value=False)), patch(
        "services.runtime.os._exit",
    ) as exit_mock:
        exit_mock.side_effect = lambda code: stop.set()
        await runtime.run_heartbeat_loop(stop, interval_seconds=0)

    assert _heartbeat_counter_value("lost") == before + 1
    exit_mock.assert_called_with(1)


# ---------------------------------------------------------------------------
# runtime_lock_heartbeat_seconds — duration of each heartbeat UPDATE call,
# observed on every attempt (success AND exception) so DB latency trends
# are not blinded by exception-path samples being skipped.
# ---------------------------------------------------------------------------


def _heartbeat_seconds_count_and_sum() -> tuple[float, float]:
    """Return (count, sum) of the heartbeat-seconds histogram."""
    from services import metrics as _metrics

    samples = next(iter(_metrics.runtime_lock_heartbeat_seconds.collect())).samples
    count = next(s.value for s in samples if s.name.endswith("_count"))
    total = next(s.value for s in samples if s.name.endswith("_sum"))
    return count, total


@pytest.mark.asyncio
async def test_heartbeat_seconds_histogram_observes_each_successful_call():
    """Every successful heartbeat call observes a duration so operators
    can graph the latency distribution without gaps."""
    stop = asyncio.Event()
    before_count, _ = _heartbeat_seconds_count_and_sum()

    async def _hb(*_a, **_kw):
        stop.set()
        return True

    with patch.object(rl_db, "heartbeat", side_effect=_hb):
        await runtime.run_heartbeat_loop(stop, interval_seconds=0)

    after_count, after_sum = _heartbeat_seconds_count_and_sum()
    assert after_count == before_count + 1
    # Duration must be non-negative; a real DB UPDATE in a healthy
    # process completes in well under a second.
    assert after_sum >= 0


@pytest.mark.asyncio
async def test_heartbeat_seconds_histogram_observes_failed_calls_too():
    """Exception path must STILL observe the duration — the time spent
    inside an erroring DB call is itself a useful signal (e.g. a slow
    connection-pool timeout) and skipping it would bias the
    distribution towards the happy path only."""
    stop = asyncio.Event()
    before_count, _ = _heartbeat_seconds_count_and_sum()
    side_effects = [RuntimeError("blip"), True]

    async def _hb(*_a, **_kw):
        v = side_effects.pop(0)
        if isinstance(v, Exception):
            raise v
        stop.set()
        return v

    with patch.object(rl_db, "heartbeat", side_effect=_hb), patch(
        "services.runtime.os._exit",
    ):
        await runtime.run_heartbeat_loop(stop, interval_seconds=0)

    after_count, _ = _heartbeat_seconds_count_and_sum()
    # Two observations: one for the failed call, one for the recovery.
    assert after_count == before_count + 2
