"""RC-15 — counting state persistence must not swallow failures.

``CountingCog._save_guild`` previously wrapped its DB write in a bare
``except Exception: pass``, so a guild could silently lose its counting
progress.  Every caller spawns it through ``core.runtime.tasks.spawn``, whose
done-callback logs failures at ERROR and increments
``task_outcome_total{outcome="error"}`` — the swallow defeated that built-in
observability.

These tests pin that a forced persistence failure is surfaced rather than
discarded.
"""

from __future__ import annotations

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

import cogs.counting_cog as counting_cog
from cogs.counting_cog import CountingCog


def _cog_with_failing_save(monkeypatch) -> CountingCog:
    cog = CountingCog(MagicMock())
    cog.count_data = {"123": {"channels": {}}}
    monkeypatch.setattr(
        counting_cog.db,
        "set_counting_state",
        AsyncMock(side_effect=RuntimeError("db down")),
    )
    return cog


@pytest.mark.asyncio
async def test_save_guild_propagates_persistence_failure(monkeypatch):
    """_save_guild must propagate persistence errors, not swallow them."""
    cog = _cog_with_failing_save(monkeypatch)

    with pytest.raises(RuntimeError, match="db down"):
        await cog._save_guild("123")


@pytest.mark.asyncio
async def test_save_guild_failure_surfaced_by_managed_task(monkeypatch, caplog):
    """Spawned via tasks.spawn, a forced failure is surfaced: the managed-task
    done-callback records it on the task and logs it at ERROR (instead of the
    failure being silently swallowed inside _save_guild)."""
    from core.runtime import tasks

    cog = _cog_with_failing_save(monkeypatch)

    with caplog.at_level(logging.ERROR):
        task = tasks.spawn("counting:save:123", cog._save_guild("123"))
        with pytest.raises(RuntimeError, match="db down"):
            await task
        # Let the loop run the task's done-callback (scheduled via call_soon).
        for _ in range(3):
            await asyncio.sleep(0)

    # The failure reached the managed-task seam...
    assert isinstance(task.exception(), RuntimeError)
    # ...and was surfaced at ERROR rather than swallowed.
    assert any(
        rec.levelno == logging.ERROR and "counting:save:123" in rec.getMessage()
        for rec in caplog.records
    ), "managed-task layer must log the failed counting save at ERROR"
