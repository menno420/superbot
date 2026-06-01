"""Tests for the paragon stats drill-down view + its two entry points."""

from __future__ import annotations

from unittest.mock import MagicMock

import discord
import pytest

from services import btd6_stats_service
from views.btd6.paragon_stats_view import (
    ParagonStatsView,
    attach_paragon_stats_button,
)


@pytest.fixture(autouse=True)
def _fresh():
    btd6_stats_service.reset_cache()
    yield
    btd6_stats_service.reset_cache()


def _user() -> discord.User:
    user = MagicMock(spec=discord.User)
    user.id = 1
    return user


def test_stats_view_has_degree_picker_and_toggles():
    stats = btd6_stats_service.get_paragon_stats("glaive_dominus")
    view = ParagonStatsView(_user(), stats)
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    assert len(selects) == 1
    assert 0 < len(selects[0].options) <= 25
    assert selects[0].options[0].value == "1"  # starts at degree 1
    # Base-stats toggle + enter-degree button.
    assert len(buttons) >= 2


def test_paragon_button_added_for_tower_with_paragon_module():
    view = discord.ui.View()
    attach_paragon_stats_button(view, "boomerang_monkey", detail_rebuilder=None)  # type: ignore[arg-type]
    assert any(isinstance(c, discord.ui.Button) for c in view.children)


def test_paragon_button_skipped_for_tower_without_paragon():
    # Super Monkey has no paragon at all — no button.
    view = discord.ui.View()
    attach_paragon_stats_button(view, "super_monkey", detail_rebuilder=None)  # type: ignore[arg-type]
    assert [c for c in view.children if isinstance(c, discord.ui.Button)] == []


def test_paragon_button_skipped_for_module_less_paragon():
    # Druid's paragon (Root of all Nature) has no stats module — no button.
    view = discord.ui.View()
    attach_paragon_stats_button(view, "druid", detail_rebuilder=None)  # type: ignore[arg-type]
    assert [c for c in view.children if isinstance(c, discord.ui.Button)] == []
