"""Tests for the hero Pro stats drill-down view + detail base-stats integration."""

from __future__ import annotations

from unittest.mock import MagicMock

import discord

from services import btd6_stats_service
from services.btd6_view_model_service import HeroDetailViewModel
from views.btd6.hero_browser_view import build_hero_detail_embed
from views.btd6.hero_stats_view import HeroStatsView, attach_hero_pro_stats_button


def _user() -> discord.User:
    user = MagicMock(spec=discord.User)
    user.id = 1
    return user


def _detail_vm(hero_id: str) -> HeroDetailViewModel:
    return HeroDetailViewModel(
        hero_id=hero_id,
        canonical=hero_id.replace("_", " ").title(),
        restrictions=(),
        context=MagicMock(),
    )


def test_stats_view_has_level_picker():
    stats = btd6_stats_service.get_hero_stats("quincy")
    view = HeroStatsView(_user(), stats)
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    assert len(selects) == 1
    assert 0 < len(selects[0].options) <= 25
    assert selects[0].options[0].value == "1"  # starts at level 1


def test_pro_button_added_for_hero_with_module():
    view = discord.ui.View()
    attach_hero_pro_stats_button(view, "quincy", detail_rebuilder=None)  # type: ignore[arg-type]
    assert any(isinstance(c, discord.ui.Button) for c in view.children)


def test_pro_button_skipped_for_hero_without_stats():
    # A hero with no committed stats file (unknown id) gets no Pro button.
    view = discord.ui.View()
    attach_hero_pro_stats_button(view, "does_not_exist", detail_rebuilder=None)  # type: ignore[arg-type]
    assert [c for c in view.children if isinstance(c, discord.ui.Button)] == []


def test_pro_button_added_for_game_data_hero():
    # Obyn had no bloonswiki module; the game-data export gives him one, so the
    # Pro button now attaches just like any module hero.
    view = discord.ui.View()
    attach_hero_pro_stats_button(view, "obyn_greenfoot", detail_rebuilder=None)  # type: ignore[arg-type]
    assert any(isinstance(c, discord.ui.Button) for c in view.children)


def test_detail_embed_includes_level1_stats_for_module_hero():
    embed = build_hero_detail_embed(_detail_vm("quincy"))
    field = next((f for f in embed.fields if "Level 1 stats" in f.name), None)
    assert field is not None
    assert "pierce" in field.value.lower()


def test_detail_embed_omits_stats_field_for_hero_without_stats():
    embed = build_hero_detail_embed(_detail_vm("does_not_exist"))
    assert not [f for f in embed.fields if "Level 1 stats" in f.name]
