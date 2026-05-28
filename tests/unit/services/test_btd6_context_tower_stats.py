"""The AI grounding includes per-tier tower stats, tagged normal."""

from __future__ import annotations

import pytest

from services import btd6_context_service as ctx
from services import btd6_data_service as ds
from services import btd6_stats_service as ss


@pytest.fixture(autouse=True)
def _fresh():
    ds.reset_cache()
    ss.reset_cache()
    yield
    ds.reset_cache()
    ss.reset_cache()


def test_combat_tower_emits_tagged_stat_lines():
    lines = ctx._render_fixture_tower(ds.get_tower("bomb_shooter"))
    stat_lines = [ln for ln in lines if "[btd6_tower_stats normal]" in ln]
    assert len(stat_lines) == 16  # base + 15 single-path tiers
    assert all("source: bloonswiki" in ln for ln in stat_lines)
    assert any("Bloon Crush" in ln and "Normal" in ln for ln in stat_lines)


def test_income_and_infinity_render():
    lines = ctx._render_fixture_tower(ds.get_tower("druid"))
    sof = next(ln for ln in lines if "0-5-0" in ln)
    assert "Income $1,000/round" in sof
    assert "∞" in sof  # 9,999,999 sentinel rendered as infinity
    assert "9999999" not in sof


def test_economy_tower_emits_no_combat_stat_lines():
    lines = ctx._render_fixture_tower(ds.get_tower("banana_farm"))
    assert not [ln for ln in lines if "btd6_tower_stats" in ln]
