"""Tests for the S3.3 / O-4 process-memory RSS sampler."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# The gauge metric exists
# ---------------------------------------------------------------------------


def test_process_memory_rss_bytes_metric_exists():
    from services import metrics

    assert hasattr(metrics, "process_memory_rss_bytes")


# ---------------------------------------------------------------------------
# The sampler updates the gauge once per tick
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sampler_updates_gauge_on_each_tick():
    """One full cycle through the sampler updates the gauge."""
    import bot1

    fake_proc = MagicMock()
    fake_proc.memory_info.return_value = MagicMock(rss=2_500_000)
    set_calls: list[int] = []

    class _GaugeStub:
        def set(self, value):
            set_calls.append(value)

    with (
        patch("psutil.Process", return_value=fake_proc),
        patch(
            "services.metrics.process_memory_rss_bytes",
            new=_GaugeStub(),
        ),
        patch.object(bot1, "PROCESS_MEMORY_SAMPLE_INTERVAL", 0.01),
    ):
        task = asyncio.create_task(bot1._sample_process_memory())
        # Yield enough times for at least one set() call.
        for _ in range(5):
            await asyncio.sleep(0.005)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    assert set_calls, "sampler did not call gauge.set() at all"
    assert all(v == 2_500_000 for v in set_calls)


@pytest.mark.asyncio
async def test_sampler_swallows_psutil_failure_and_keeps_running():
    """A transient psutil error must not take the supervised task down."""
    import bot1

    fake_proc = MagicMock()
    fake_proc.memory_info.side_effect = [
        RuntimeError("psutil hiccup"),
        MagicMock(rss=999_999),
    ]
    set_calls: list[int] = []

    class _GaugeStub:
        def set(self, value):
            set_calls.append(value)

    with (
        patch("psutil.Process", return_value=fake_proc),
        patch(
            "services.metrics.process_memory_rss_bytes",
            new=_GaugeStub(),
        ),
        patch.object(bot1, "PROCESS_MEMORY_SAMPLE_INTERVAL", 0.01),
    ):
        task = asyncio.create_task(bot1._sample_process_memory())
        for _ in range(10):
            await asyncio.sleep(0.005)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    # First tick raised — second tick recovered and set the gauge.
    assert (
        999_999 in set_calls
    ), "sampler should recover from a transient psutil failure"
