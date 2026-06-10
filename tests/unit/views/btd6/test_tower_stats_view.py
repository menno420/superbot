"""Tests for the Pro stats drill-down view + detail base-stats integration."""

from __future__ import annotations

from unittest.mock import MagicMock

import discord

from services import btd6_knowledge_service, btd6_stats_service
from services.btd6_view_model_service import TowerDetailViewModel
from utils.btd6 import tier_codes
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


def test_tier_picker_lists_only_single_path_tiers():
    # First step must stay within Discord's 25-option cap — so it shows only the
    # base + 16 single-path tiers, never the ~48 crosspaths.
    stats = btd6_stats_service.get_tower_stats("bomb_shooter")
    view = TowerStatsView(_user(), stats)
    select = next(c for c in view.children if isinstance(c, discord.ui.Select))
    values = [o.value for o in select.options]
    assert len(values) <= 25
    assert all(v in tier_codes.SINGLE_PATH_CODES for v in values)


def test_picking_tier_reveals_crosspath_subpicker_within_cap():
    stats = btd6_stats_service.get_tower_stats("bomb_shooter")
    view = TowerStatsView(_user(), stats)
    view.show_crosspaths_for("200")
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    assert len(selects) == 2  # tier select + crosspath sub-picker
    assert all(0 < len(s.options) <= 25 for s in selects)
    assert "220" in [o.value for o in selects[1].options]
    # A tier with no crosspaths (base) clears the sub-picker again.
    view.show_crosspaths_for("000")
    assert len([c for c in view.children if isinstance(c, discord.ui.Select)]) == 1


def test_pro_button_added_for_combat_tower():
    view = discord.ui.View()
    attach_pro_stats_button(view, "bomb_shooter", detail_rebuilder=None)  # type: ignore[arg-type]
    assert any(isinstance(c, discord.ui.Button) for c in view.children)


def test_pro_button_added_for_economy_tower_since_cutover():
    # The Farm has full game-native tiers since the Q-0067 cutover (abilities,
    # buffs, income — attacks suppressed), so the Pro view is real data now.
    view = discord.ui.View()
    attach_pro_stats_button(view, "banana_farm", detail_rebuilder=None)  # type: ignore[arg-type]
    assert any(isinstance(c, discord.ui.Button) for c in view.children)


def test_pro_button_skipped_for_tower_without_stats_file(monkeypatch):
    from services import btd6_stats_service

    monkeypatch.setattr(btd6_stats_service, "get_tower_stats", lambda _tid: None)
    view = discord.ui.View()
    attach_pro_stats_button(view, "banana_farm", detail_rebuilder=None)  # type: ignore[arg-type]
    assert [c for c in view.children if isinstance(c, discord.ui.Button)] == []


def test_detail_embed_includes_base_stats_field():
    embed = build_tower_detail_embed(_detail_vm("bomb_shooter"))
    field = next((f for f in embed.fields if "Base stats" in f.name), None)
    assert field is not None
    assert "Explosion" in field.value
    assert "pierce" in field.value.lower()
