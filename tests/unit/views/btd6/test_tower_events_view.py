"""Event-restriction drill-down: separate from the (now uncluttered) overview."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import discord

from services import btd6_knowledge_service
from services.btd6_live_query_service import TowerRestrictionContext
from services.btd6_view_model_service import TowerDetailViewModel
from views.btd6.tower_browser_view import build_tower_detail_embed
from views.btd6.tower_events_view import attach_event_status_button, build_event_embed


def _banned_ctx() -> TowerRestrictionContext:
    return TowerRestrictionContext(
        event_kind="btd6_race",
        event_id="abc",
        event_name="Reversed Loop",
        end_ms=None,
        fetched_at=datetime.now(tz=timezone.utc),
        stance="banned",
        max_count=0,
        path1_blocked=0,
        path2_blocked=0,
        path3_blocked=0,
        is_hero=False,
        sentinel_all_heroes_banned=False,
    )


def _vm(restrictions: tuple) -> TowerDetailViewModel:
    return TowerDetailViewModel(
        tower_id="bomb_shooter",
        canonical="Bomb Shooter",
        fact=btd6_knowledge_service.tower_fact("bomb_shooter"),
        restrictions=restrictions,
        context=MagicMock(),
    )


def test_event_button_added_only_when_restrictions_exist():
    view = discord.ui.View()
    attach_event_status_button(view, "Bomb Shooter", (_banned_ctx(),), detail_rebuilder=None)  # type: ignore[arg-type]
    assert any(isinstance(c, discord.ui.Button) for c in view.children)

    empty = discord.ui.View()
    attach_event_status_button(empty, "Bomb Shooter", (), detail_rebuilder=None)  # type: ignore[arg-type]
    assert empty.children == []


def test_event_embed_lists_restriction():
    embed = build_event_embed("Bomb Shooter", (_banned_ctx(),))
    assert "Bomb Shooter" in embed.title
    assert "BANNED" in (embed.description or "")


def test_overview_no_longer_shows_live_data_field():
    embed = build_tower_detail_embed(_vm((_banned_ctx(),)))
    assert not any(f.name == "Live data" for f in embed.fields)
    # base stats are still there
    assert any("Base stats" in f.name for f in embed.fields)
