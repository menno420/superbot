"""Tests for the LeaderboardBrowserView three-step drill-down."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import discord

from services.btd6_view_model_service import (
    ContextHandle,
    DataFreshness,
    LeaderboardDetailViewModel,
    LeaderboardListItem,
    LeaderboardListViewModel,
)
from utils.btd6.event_window import format_window
from views.btd6.leaderboard_browser_view import (
    LeaderboardBrowserView,
    LeaderboardDetailView,
    LeaderboardKindListView,
    build_event_list_embed,
    build_kind_picker_embed,
    build_leaderboard_detail_embed,
)


def _stub_user() -> discord.User:
    user = MagicMock(spec=discord.User)
    user.id = 12345
    return user


def _item(event_id: str, kind: str = "race") -> LeaderboardListItem:
    return LeaderboardListItem(
        event_kind=kind,
        event_id=event_id,
        event_name=f"{kind.title()} {event_id}",
        window=format_window(None, None),
        context=ContextHandle(
            context_id=f"btd6_leaderboard:{kind}_{event_id}",
            context_type="leaderboard",
        ),
    )


def _list_vm(
    items: list[LeaderboardListItem], total: int | None = None,
) -> LeaderboardListViewModel:
    return LeaderboardListViewModel(
        event_kind="race",
        items=tuple(items),
        total_count=total if total is not None else len(items),
        freshness=DataFreshness(
            state="fresh",
            last_success_at=datetime.now(tz=timezone.utc),
            last_attempt_at=datetime.now(tz=timezone.utc),
            source_key="nk_btd6_races",
        ),
        context=ContextHandle(
            context_id="btd6_leaderboard:race_list",
            context_type="leaderboard",
        ),
    )


def test_browser_view_has_kind_select() -> None:
    view = LeaderboardBrowserView(_stub_user())
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    assert len(selects) == 1
    values = {opt.value for opt in selects[0].options}
    assert values == {"race", "boss"}


def test_kind_list_view_after_set_vm_has_two_selects() -> None:
    view = LeaderboardKindListView(_stub_user())
    view.set_vm("race", _list_vm([_item("R1"), _item("R2")]))
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    assert len(selects) == 2


def test_kind_list_select_caps_at_25() -> None:
    items = [_item(f"R{i}") for i in range(40)]
    view = LeaderboardKindListView(_stub_user())
    view.set_vm("race", _list_vm(items, total=40))
    event_selects = [
        c
        for c in view.children
        if isinstance(c, discord.ui.Select)
        and c.placeholder
        and "leaderboard" in c.placeholder
    ]
    assert event_selects
    assert len(event_selects[0].options) <= 25


def test_kind_picker_embed_title() -> None:
    embed = build_kind_picker_embed()
    assert "Leaderboards" in (embed.title or "")


def test_list_embed_renders_freshness_warning() -> None:
    items = [_item("R1")]
    vm = LeaderboardListViewModel(
        event_kind="race",
        items=tuple(items),
        total_count=1,
        freshness=DataFreshness(
            state="stale",
            last_success_at=None,
            last_attempt_at=None,
            source_key="nk_btd6_races",
        ),
        context=ContextHandle(
            context_id="btd6_leaderboard:race_list",
            context_type="leaderboard",
        ),
    )
    embed = build_event_list_embed(vm)
    field = next(
        (f for f in embed.fields if "Data freshness" in (f.name or "")),
        None,
    )
    assert field is not None


def test_detail_embed_handles_empty_rows() -> None:
    vm = LeaderboardDetailViewModel(
        event_kind="race",
        event_id="R1",
        event_name="Race R1",
        rows=(),
        freshness=DataFreshness(
            state="fresh",
            last_success_at=datetime.now(tz=timezone.utc),
            last_attempt_at=datetime.now(tz=timezone.utc),
            source_key="nk_btd6_races",
        ),
        context=ContextHandle(
            context_id="btd6_leaderboard:race_R1",
            context_type="leaderboard",
        ),
    )
    embed = build_leaderboard_detail_embed(vm)
    assert "No leaderboard rows stored" in (embed.description or "")


def test_views_are_hubview_subclasses() -> None:
    from views.base import HubView

    assert issubclass(LeaderboardBrowserView, HubView)
    assert issubclass(LeaderboardKindListView, HubView)
    assert issubclass(LeaderboardDetailView, HubView)
