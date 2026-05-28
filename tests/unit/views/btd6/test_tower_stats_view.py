"""Tests for the Pro stats drill-down view + detail base-stats integration."""

from __future__ import annotations

from unittest.mock import MagicMock

import discord

from services import btd6_knowledge_service, btd6_stats_service
from services.btd6_view_model_service import TowerDetailViewModel
from views.btd6.tower_browser_view import build_tower_detail_embed
from views.btd6.tower_stats_view import TowerStatsView, attach_pro_stats_button


def _user() -> discord.User:
    user = MagicMock(spec=discord.User)
    user.id = 1
    return user


def _detail_vm(tower_id: str) -> TowerDetailViewModel:
    return TowerDetailViewModel(
        tower_id=tower_id,
        canonical=tower_id.replace("_", " ").title(),
        fact=btd6_knowledge_service.tower_fact(tower_id),
        restrictions=(),
        context=MagicMock(),
    )


def test_stats_view_has_tier_picker():
    stats = btd6_stats_service.get_tower_stats("bomb_shooter")
    view = TowerStatsView(_user(), stats)
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    assert len(selects) == 1
    assert 0 < len(selects[0].options) <= 25
    assert selects[0].options[0].value == "000"


def test_pro_button_added_for_combat_tower():
    view = discord.ui.View()
    attach_pro_stats_button(view, "bomb_shooter", detail_rebuilder=None)  # type: ignore[arg-type]
    assert any(isinstance(c, discord.ui.Button) for c in view.children)


def test_pro_button_skipped_for_economy_tower():
    view = discord.ui.View()
    attach_pro_stats_button(view, "banana_farm", detail_rebuilder=None)  # type: ignore[arg-type]
    assert [c for c in view.children if isinstance(c, discord.ui.Button)] == []


def test_detail_embed_includes_base_stats_field():
    embed = build_tower_detail_embed(_detail_vm("bomb_shooter"))
    field = next((f for f in embed.fields if "Base stats" in f.name), None)
    assert field is not None
    assert "Explosion" in field.value
    assert "pierce" in field.value.lower()
