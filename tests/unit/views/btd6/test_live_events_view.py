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
    LiveOverviewItem,
    LiveOverviewKind,
    LiveOverviewViewModel,
)
from utils.btd6.event_window import format_window
from views.btd6.live_events_view import (
    EventDetailView,
    LiveEventsBrowserView,
    LiveOverviewView,
    _LiveOverviewSelect,
    build_event_list_embed,
    build_kind_picker_embed,
    build_live_overview_embed,
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
    # The kind picker is now the *history* (past-events) step; the live
    # overview owns the "Live Events" title.
    embed = build_kind_picker_embed()
    assert embed.title == "🐵 BTD6 — Past events"


# ---------------------------------------------------------------------------
# Live overview (current-event-first landing)
# ---------------------------------------------------------------------------


def _overview_item(short: str, key: str, name: str, end_ms: int) -> LiveOverviewItem:
    emoji = {"race": "🏁", "boss": "👑", "ct": "🗺️", "odyssey": "🌊", "event": "🎪"}[short]
    return LiveOverviewItem(
        entity_kind=f"btd6_{short}",
        short_kind=short,
        emoji=emoji,
        label=short.title(),
        entity_key=key,
        name=name,
        end_ms=end_ms,
        window=format_window(end_ms - 3_600_000, end_ms),
        context=ContextHandle(context_id=f"btd6_{short}:{key}", context_type=short),
    )


def _overview_vm(live_items: list[LiveOverviewItem]) -> LiveOverviewViewModel:
    by_kind: dict[str, list[LiveOverviewItem]] = {}
    for it in live_items:
        by_kind.setdefault(it.short_kind, []).append(it)
    kinds = tuple(
        LiveOverviewKind(
            entity_kind=f"btd6_{short}",
            short_kind=short,
            emoji=emoji,
            label=short.title(),
            live=tuple(by_kind.get(short, [])),
            freshness=DataFreshness(
                state="fresh",
                last_success_at=datetime.now(tz=timezone.utc),
                last_attempt_at=datetime.now(tz=timezone.utc),
                source_key=f"nk_btd6_{short}s",
            ),
        )
        for short, emoji in (
            ("race", "🏁"),
            ("boss", "👑"),
            ("ct", "🗺️"),
            ("odyssey", "🌊"),
            ("event", "🎪"),
        )
    )
    return LiveOverviewViewModel(
        kinds=kinds,
        context=ContextHandle(context_id="btd6_hub:live", context_type="hub"),
    )


def test_overview_embed_lists_live_event_and_title() -> None:
    now_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
    vm = _overview_vm([_overview_item("ct", "ct1", "Contested Territory", now_ms + 36_000_000)])
    embed = build_live_overview_embed(vm)
    assert embed.title == "🐵 BTD6 — Live Events"
    # The live event's name appears in a field value.
    joined = "\n".join(f.value or "" for f in embed.fields)
    assert "Contested Territory" in joined
    # And kinds with nothing live are clearly marked.
    assert "nothing live" in joined


def test_overview_embed_empty_state() -> None:
    vm = _overview_vm([])
    embed = build_live_overview_embed(vm)
    assert "Nothing is running right now" in (embed.description or "")


def test_overview_select_lists_only_live_events() -> None:
    now_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
    vm = _overview_vm(
        [
            _overview_item("ct", "ct1", "Contested Territory", now_ms + 36_000_000),
            _overview_item("event", "ev1", "Collab Event", now_ms + 72_000_000),
        ],
    )
    sel = _LiveOverviewSelect(vm)
    assert sel.disabled is False
    # value = "<short>:<entity_key>" so the callback can route to detail.
    assert {o.value for o in sel.options} == {"ct:ct1", "event:ev1"}


def test_overview_select_disabled_when_nothing_live() -> None:
    sel = _LiveOverviewSelect(_overview_vm([]))
    assert sel.disabled is True
    assert [o.value for o in sel.options] == ["__none__"]


def test_overview_view_has_select_and_past_events_button() -> None:
    vm = _overview_vm([])
    view = LiveOverviewView(_stub_user(), vm)
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    assert len(selects) == 1
    assert any("Past events" in (b.label or "") for b in buttons)


def test_history_browser_has_back_to_live_button() -> None:
    view = LiveEventsBrowserView(_stub_user())
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    assert any("Live now" in (b.label or "") for b in buttons)
    # set_kind must preserve the back button (it re-renders all children).
    view.set_kind("race", _vm("race", [_item("R1")]))
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    assert any("Live now" in (b.label or "") for b in buttons)


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
