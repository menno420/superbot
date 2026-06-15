"""Tests for the LiveEventsBrowserView ephemeral drill-down."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import discord

from services.btd6_view_model_service import (
    ContextHandle,
    DataFreshness,
    EventListItem,
    EventListViewModel,
)
from utils.btd6.event_window import format_window
from views.btd6.live_events_view import (
    EventDetailView,
    LiveEventsBrowserView,
    build_event_list_embed,
    build_kind_picker_embed,
)


def _stub_user() -> discord.User:
    user = MagicMock(spec=discord.User)
    user.id = 12345
    return user


def _item(entity_key: str, kind: str = "race") -> EventListItem:
    return EventListItem(
        entity_kind=f"btd6_{kind}",
        entity_key=entity_key,
        name=f"{kind.title()} {entity_key}",
        window=format_window(None, None),
        context=ContextHandle(
            context_id=f"btd6_{kind}:{entity_key}",
            context_type=kind,
        ),
    )


def _vm(
    kind: str, items: list[EventListItem], total: int | None = None,
) -> EventListViewModel:
    return EventListViewModel(
        kind=kind,
        entity_kind=f"btd6_{kind}",
        items=tuple(items),
        total_count=total if total is not None else len(items),
        freshness=DataFreshness(
            state="fresh",
            last_success_at=datetime.now(tz=timezone.utc),
            last_attempt_at=datetime.now(tz=timezone.utc),
            source_key=f"nk_btd6_{kind}s",
        ),
        context=ContextHandle(context_id=f"btd6_{kind}:list", context_type=kind),
    )


def test_kind_picker_starts_with_only_kind_select() -> None:
    view = LiveEventsBrowserView(_stub_user())
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    assert len(selects) == 1
    assert selects[0].options[0].value in {"race", "boss", "ct", "odyssey", "event"}


def test_set_kind_adds_event_select() -> None:
    view = LiveEventsBrowserView(_stub_user())
    view.set_kind("race", _vm("race", [_item("R1"), _item("R2")]))
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    # Should now have BOTH the kind picker and the event select.
    assert len(selects) == 2


def test_event_select_caps_at_25() -> None:
    items = [_item(f"R{i}") for i in range(40)]
    view = LiveEventsBrowserView(_stub_user())
    view.set_kind("race", _vm("race", items, total=40))
    event_selects = [
        c
        for c in view.children
        if isinstance(c, discord.ui.Select)
        and c.placeholder
        and "event to view" in c.placeholder
    ]
    assert event_selects, "expected event select after set_kind"
    assert len(event_selects[0].options) <= 25


def test_kind_picker_embed_title() -> None:
    embed = build_kind_picker_embed()
    assert embed.title == "🐵 BTD6 — Live Events"


def test_list_embed_renders_warning_when_stale() -> None:
    items = [_item("R1")]
    vm = EventListViewModel(
        kind="race",
        entity_kind="btd6_race",
        items=tuple(items),
        total_count=1,
        freshness=DataFreshness(
            state="stale",
            last_success_at=None,
            last_attempt_at=None,
            source_key="nk_btd6_races",
        ),
        context=ContextHandle(context_id="btd6_race:list", context_type="race"),
    )
    embed = build_event_list_embed(vm)
    field = next(
        (f for f in embed.fields if "Data freshness" in (f.name or "")),
        None,
    )
    assert field is not None
    assert "outdated" in (field.value or "")


def test_list_embed_renders_empty_state_when_no_items() -> None:
    vm = _vm("race", [])
    embed = build_event_list_embed(vm)
    no_events_field = next(
        (f for f in embed.fields if f.name == "No events"),
        None,
    )
    assert no_events_field is not None


def test_views_are_hubview_subclasses() -> None:
    from views.base import HubView

    assert issubclass(LiveEventsBrowserView, HubView)
    assert issubclass(EventDetailView, HubView)
