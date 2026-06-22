"""Farm workflow tests — the fresh-start fix + the get_status return-moment deltas.

The headline pin is the regression guard: a brand-new farm must start **empty**,
not full. ``chicken_farm.eggs_updated_at`` defaults to epoch 0, and settling from
1970 would instantly cap the coop (a free full collect for every new player), so
``_stored_state`` normalizes a zero timestamp to *now*.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from services import farm_workflow
from utils import farm as farm_mod

_NOW = 1_000_000_000


# --------------------------------------------------------------- fresh-start fix


def test_fresh_farm_starts_empty_not_full():
    # Fresh row defaults (chickens=1, eggs=0, eggs_updated_at=0, coop_level=0).
    stored = farm_workflow._stored_state(_NOW, 1, 0, 0, 0)
    assert stored.updated_at == _NOW  # epoch-0 normalized to now, not 1970
    settled = farm_mod.settle(stored, _NOW)
    assert settled.eggs == 0  # empty coop — no free full collect
    assert farm_mod.collect_value(settled.eggs) == 0


def test_real_timestamp_is_preserved():
    earlier = _NOW - 5 * farm_mod.LAY_INTERVAL_SECONDS
    stored = farm_workflow._stored_state(_NOW, 1, 0, earlier, 0)
    assert stored.updated_at == earlier  # a real timestamp is untouched
    settled = farm_mod.settle(stored, _NOW)
    assert settled.eggs == 5  # 5 intervals × 1 hen → 5 eggs accrued


# ------------------------------------------------------------------- get_status


@pytest.mark.asyncio
async def test_get_status_fresh_farm_reports_no_away_progress():
    with patch(
        "services.farm_workflow.db.get_chicken_farm",
        new=AsyncMock(return_value=(1, 0, 0, 0)),
    ):
        status = await farm_workflow.get_status(123, 456)
    assert status.eggs_gained == 0
    assert status.elapsed_seconds == 0
    assert status.state.eggs == 0
    assert status.at_capacity is False


@pytest.mark.asyncio
async def test_get_status_reports_accrued_delta():
    # 2 hens, last action 3 intervals ago, started with 1 stored egg.
    interval = farm_mod.LAY_INTERVAL_SECONDS
    ts = 1_700_000_000
    with (
        patch(
            "services.farm_workflow.db.get_chicken_farm",
            new=AsyncMock(return_value=(2, 1, ts, 0)),
        ),
        patch("services.farm_workflow.time.time", return_value=ts + 3 * interval),
    ):
        status = await farm_workflow.get_status(123, 456)
    # 2 hens × 3 intervals = 6 new eggs on top of the 1 stored.
    assert status.eggs_gained == 6
    assert status.state.eggs == 7
    assert status.elapsed_seconds == 3 * interval


@pytest.mark.asyncio
async def test_get_status_flags_capacity():
    with (
        patch(
            "services.farm_workflow.db.get_chicken_farm",
            new=AsyncMock(return_value=(1, 0, 1, 0)),
        ),
        patch("services.farm_workflow.time.time", return_value=10**9),
    ):
        status = await farm_workflow.get_status(123, 456)
    assert status.at_capacity is True
    assert status.state.eggs == farm_mod.coop_capacity(0)
