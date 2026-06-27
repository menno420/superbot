"""The `!platform economytrend` embed + its pure render helpers.

Pins the per-day faucet/sink trend embed (the time-series companion to the
`!platform economy` aggregate view): the dependency-free unicode sparkline, the
recent-days table, and that the builder forwards the window to the read model
and renders the summary/verdict/trend without touching Discord I/O.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, patch

import pytest

from services import diagnostic_embeds as de
from services.economy_flow_service import DayFlow, EconomyFlowTimeseries


def test_sparkline_empty_is_blank():
    assert de._sparkline([]) == ""


def test_sparkline_flat_series_is_single_mid_glyph_no_div_by_zero():
    out = de._sparkline([5, 5, 5])
    assert len(out) == 3
    assert set(out) == {de._SPARK_BLOCKS[len(de._SPARK_BLOCKS) // 2]}


def test_sparkline_maps_min_low_max_high():
    out = de._sparkline([-100, 0, 100])
    assert len(out) == 3
    assert out[0] == de._SPARK_BLOCKS[0]  # min → lowest block
    assert out[-1] == de._SPARK_BLOCKS[-1]  # max → highest block


def test_format_day_rows_is_newest_first_and_caps():
    days = [DayFlow(date(2026, 6, d), d * 100, d * 10, d * 90, d) for d in range(1, 20)]
    out = de._format_day_rows(days, limit=14)
    lines = out.splitlines()
    # 14 rendered rows newest-first + one "earlier day(s)" line.
    assert lines[0].startswith("`2026-06-19`")
    assert "earlier day(s)" in lines[-1]


@pytest.mark.asyncio
async def test_trend_embed_renders_summary_and_series():
    ts = EconomyFlowTimeseries(
        days=[
            DayFlow(date(2026, 6, 1), 5000, 1000, 4000, 40),
            DayFlow(date(2026, 6, 2), 1000, 1500, -500, 22),
        ],
        total_minted=6000,
        total_drained=2500,
        net=3500,
        ratio=2.4,
        window_label="last 7 days",
        verdict="inflating ⚠",
        trend="rising ⬆",
    )
    # The builder imports economy_flow_service lazily, so patch at the source.
    with patch(
        "services.economy_flow_service.build_flow_timeseries",
        new_callable=AsyncMock,
        return_value=ts,
    ):
        embed = await de.build_economy_trend_embed(123, days=7)

    blob = (
        embed.description + " " + " ".join(f"{f.name} {f.value}" for f in embed.fields)
    )
    assert "last 7 days" in blob
    assert "inflating ⚠" in blob
    assert "rising ⬆" in blob
    assert "2026-06-01" in blob


@pytest.mark.asyncio
async def test_trend_embed_no_activity_path():
    ts = EconomyFlowTimeseries(
        days=[],
        total_minted=0,
        total_drained=0,
        net=0,
        ratio=None,
        window_label="all time",
        verdict="no activity",
        trend="n/a",
    )
    with patch(
        "services.economy_flow_service.build_flow_timeseries",
        new_callable=AsyncMock,
        return_value=ts,
    ):
        embed = await de.build_economy_trend_embed(123, days=None)
    names = [f.name for f in embed.fields]
    assert "No activity" in names
