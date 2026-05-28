"""Tests for the TowerBrowserView ephemeral drill-down."""

from __future__ import annotations

from unittest.mock import MagicMock

import discord

from services.btd6_view_model_service import (
    ContextHandle,
    TowerListItem,
    TowerListViewModel,
)
from views.btd6.tower_browser_view import (
    TowerBrowserView,
    TowerDetailView,
    build_tower_list_embed,
)


def _stub_user() -> discord.User:
    user = MagicMock(spec=discord.User)
    user.id = 12345
    return user


def _vm(items: list[TowerListItem], total: int | None = None) -> TowerListViewModel:
    return TowerListViewModel(
        items=tuple(items),
        total_count=total if total is not None else len(items),
        context=ContextHandle(context_id="btd6_tower:list", context_type="tower"),
    )


def _item(tower_id: str) -> TowerListItem:
    return TowerListItem(
        tower_id=tower_id,
        canonical=tower_id.replace("_", " ").title(),
        base_cost=100,
        category="primary",
        context=ContextHandle(
            context_id=f"btd6_tower:{tower_id}",
            context_type="tower",
        ),
    )


def test_view_starts_empty_then_set_vm_adds_select() -> None:
    view = TowerBrowserView(_stub_user())
    assert len(view.children) == 0
    vm = _vm([_item("dart_monkey"), _item("sniper_monkey")])
    view.set_vm(vm)
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    assert len(selects) == 1


def test_select_caps_at_25_options() -> None:
    items = [_item(f"t{i}") for i in range(40)]
    vm = _vm(items, total=40)
    view = TowerBrowserView(_stub_user())
    view.set_vm(vm)
    sel = next(c for c in view.children if isinstance(c, discord.ui.Select))
    assert len(sel.options) <= 25


def test_empty_vm_renders_disabled_placeholder() -> None:
    vm = _vm([], total=0)
    view = TowerBrowserView(_stub_user())
    view.set_vm(vm)
    sel = next(c for c in view.children if isinstance(c, discord.ui.Select))
    assert len(sel.options) >= 1
    assert sel.options[0].value == "__none__"


def test_list_embed_title() -> None:
    vm = _vm([_item("dart_monkey")])
    embed = build_tower_list_embed(vm)
    assert embed.title == "🐵 BTD6 — Towers"
    assert "1 of 1 towers" in (embed.description or "")


def test_list_embed_pagination_hint_when_truncated() -> None:
    items = [_item(f"t{i}") for i in range(25)]
    vm = _vm(items, total=40)
    embed = build_tower_list_embed(vm)
    pagination_field = next(
        (f for f in embed.fields if "Pagination" in (f.name or "")),
        None,
    )
    assert pagination_field is not None
    assert "25 options" in (pagination_field.value or "")


def test_detail_view_has_no_children_at_init() -> None:
    # Children are added by the select callback (attach_back_button).
    view = TowerDetailView(_stub_user())
    assert len(view.children) == 0


def test_views_are_hubview_subclasses() -> None:
    from views.base import HubView

    assert issubclass(TowerBrowserView, HubView)
    assert issubclass(TowerDetailView, HubView)
