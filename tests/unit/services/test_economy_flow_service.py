"""Faucet/sink read model over the economy audit ledger (#960 band slice).

Pins the pure aggregation in :mod:`services.economy_flow_service`: rows are
split into faucets (net mint) / sinks (net drain) by the *sign* of the summed
delta, totals and the mint:drain ratio are computed, and the edge cases
(empty ledger, sinks-only, zero-net reasons) never divide by zero or
mislabel. The classification is sign-driven so a brand-new reason is handled
automatically — the view never goes stale.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from services import economy_flow_service as flow
from services.economy_flow_service import ReasonFlow, _assemble


def test_assemble_splits_faucets_and_sinks_by_sign():
    rows = [
        ("mining:sell_ore", 5000, 120),
        ("mining:buy_gear", -1800, 30),
        ("mining:forge_build", -1200, 4),
        ("daily", 800, 16),
    ]
    report = _assemble(rows, "all time")

    assert [f.reason for f in report.faucets] == ["mining:sell_ore", "daily"]
    assert [s.reason for s in report.sinks] == [
        "mining:buy_gear",
        "mining:forge_build",
    ]
    assert report.total_minted == 5800
    assert report.total_drained == 3000
    assert report.net == 2800
    assert report.ratio == pytest.approx(5800 / 3000)
    assert report.window_label == "all time"


def test_faucets_and_sinks_sorted_by_magnitude():
    rows = [
        ("small_faucet", 10, 1),
        ("big_faucet", 9000, 1),
        ("small_sink", -5, 1),
        ("big_sink", -7000, 1),
    ]
    report = _assemble(rows, "all time")
    assert [f.reason for f in report.faucets] == ["big_faucet", "small_faucet"]
    assert [s.reason for s in report.sinks] == ["big_sink", "small_sink"]


def test_empty_ledger_is_no_activity_and_ratio_none():
    report = _assemble([], "all time")
    assert report.faucets == []
    assert report.sinks == []
    assert report.total_minted == 0
    assert report.total_drained == 0
    assert report.net == 0
    assert report.ratio is None
    assert report.verdict == "no activity"


def test_sinks_only_ratio_is_zero_not_division_error():
    report = _assemble([("mining:buy_gear", -500, 5)], "all time")
    assert report.faucets == []
    assert report.total_minted == 0
    assert report.total_drained == 500
    assert report.net == -500
    assert report.ratio == pytest.approx(0.0)
    assert report.verdict == "draining"


def test_faucets_only_no_drain_is_inflating():
    report = _assemble([("mining:sell_ore", 4000, 50)], "all time")
    assert report.sinks == []
    assert report.ratio is None  # nothing drained — no divide-by-zero
    assert report.verdict == "inflating ⚠"


def test_zero_net_reason_is_neither_faucet_nor_sink():
    # A reason that minted and drained equally over the window nets to 0 and
    # belongs in neither table (it is not coin pressure in either direction).
    report = _assemble([("wash", 0, 8)], "all time")
    assert report.faucets == []
    assert report.sinks == []
    assert report.total_minted == 0
    assert report.total_drained == 0
    assert report.verdict == "no activity"


def test_verdict_thresholds():
    # ratio >= 1.5 → inflating
    assert _assemble(
        [("f", 200, 1), ("s", -100, 1)], "all time"
    ).verdict == "inflating ⚠"
    # ratio <= 0.67 → draining
    assert _assemble([("f", 50, 1), ("s", -100, 1)], "all time").verdict == "draining"
    # in between → balanced
    assert _assemble([("f", 100, 1), ("s", -100, 1)], "all time").verdict == "balanced"


@pytest.mark.asyncio
async def test_build_flow_report_all_time_passes_no_since():
    with patch.object(
        flow.economy_db,
        "economy_flow_by_reason",
        new_callable=AsyncMock,
        return_value=[("mining:sell_ore", 100, 2)],
    ) as mock_db:
        report = await flow.build_flow_report(42, days=None)
    mock_db.assert_awaited_once()
    assert mock_db.await_args.kwargs["since"] is None
    assert report.window_label == "all time"
    assert report.faucets == [ReasonFlow("mining:sell_ore", 100, 2)]


@pytest.mark.asyncio
async def test_build_flow_report_windowed_passes_since_and_labels_days():
    with patch.object(
        flow.economy_db,
        "economy_flow_by_reason",
        new_callable=AsyncMock,
        return_value=[],
    ) as mock_db:
        report = await flow.build_flow_report(42, days=7)
    assert mock_db.await_args.kwargs["since"] is not None
    assert report.window_label == "last 7 days"


@pytest.mark.asyncio
async def test_build_flow_report_singular_day_label():
    with patch.object(
        flow.economy_db,
        "economy_flow_by_reason",
        new_callable=AsyncMock,
        return_value=[],
    ):
        report = await flow.build_flow_report(42, days=1)
    assert report.window_label == "last 1 day"
