"""Tests for the HeroBrowserView ephemeral drill-down."""

from __future__ import annotations

from unittest.mock import MagicMock

import discord

from services.btd6_view_model_service import (
    ContextHandle,
    HeroListItem,
    HeroListViewModel,
)
from views.btd6.hero_browser_view import (
    HeroBrowserView,
    HeroDetailView,
    build_hero_list_embed,
)


def _stub_user() -> discord.User:
    user = MagicMock(spec=discord.User)
    user.id = 12345
    return user


def _item(hero_id: str) -> HeroListItem:
    return HeroListItem(
        hero_id=hero_id,
        canonical=hero_id.title(),
        base_cost=900,
        description=f"{hero_id} description.",
        context=ContextHandle(
            context_id=f"btd6_hero:{hero_id}",
            context_type="hero",
        ),
    )


def _vm(
    items: list[HeroListItem],
    total: int | None = None,
    page: int = 0,
    total_pages: int = 1,
) -> HeroListViewModel:
    return HeroListViewModel(
        items=tuple(items),
        total_count=total if total is not None else len(items),
        context=ContextHandle(context_id="btd6_hero:list", context_type="hero"),
        page=page,
        total_pages=total_pages,
    )


def test_view_starts_empty_then_set_vm_adds_select() -> None:
    view = HeroBrowserView(_stub_user())
    assert len(view.children) == 0
    view.set_vm(_vm([_item("quincy"), _item("sauda")]))
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    assert len(selects) == 1


def test_set_vm_adds_nav_buttons() -> None:
    vm = _vm([_item("quincy")], total=17, total_pages=3, page=1)
    view = HeroBrowserView(_stub_user())
    view.set_vm(vm)
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    assert len(buttons) == 2


def test_select_caps_at_25_options() -> None:
    items = [_item(f"h{i}") for i in range(40)]
    view = HeroBrowserView(_stub_user())
    view.set_vm(_vm(items, total=40))
    sel = next(c for c in view.children if isinstance(c, discord.ui.Select))
    assert len(sel.options) <= 25


def test_list_embed_title() -> None:
    embed = build_hero_list_embed(_vm([_item("quincy")]))
    assert embed.title == "🐵 BTD6 — Heroes"


def test_list_embed_shows_page_info() -> None:
    items = [_item(f"h{i}") for i in range(8)]
    vm = _vm(items, total=17, page=1, total_pages=3)
    embed = build_hero_list_embed(vm)
    assert "Page 2/3" in (embed.description or "")


def test_views_are_hubview_subclasses() -> None:
    from views.base import HubView

    assert issubclass(HeroBrowserView, HubView)
    assert issubclass(HeroDetailView, HubView)
