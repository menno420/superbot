"""Tests for the shared ``PaginatedSelectView`` windowed-select primitive.

Pins the #1040 regression at the root: a long option list is *windowed* into
≤25-option pages with Prev/Next nav, never front-truncated, so every option
stays reachable.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import discord
import pytest

from views.paginated_select import (
    MAX_OPTIONS,
    PaginatedSelectView,
    _PageButton,
    _WindowSelect,
)


def _author():
    return SimpleNamespace(id=42)


def _opts(n: int) -> list[discord.SelectOption]:
    return [discord.SelectOption(label=f"opt {i}", value=str(i)) for i in range(n)]


async def _noop(interaction, values):  # noqa: ANN001
    return None


def _selects(view):
    return [c for c in view.children if isinstance(c, _WindowSelect)]


def _buttons(view):
    return [c for c in view.children if isinstance(c, _PageButton)]


# ---------------------------------------------------------------------------
# Single page
# ---------------------------------------------------------------------------


def test_single_page_has_no_nav():
    view = PaginatedSelectView(_author(), _opts(10), _noop)
    assert view.page_count == 1
    selects = _selects(view)
    assert len(selects) == 1
    assert len(selects[0].options) == 10
    assert _buttons(view) == []


def test_exactly_25_is_one_page():
    view = PaginatedSelectView(_author(), _opts(25), _noop)
    assert view.page_count == 1
    assert _buttons(view) == []
    assert len(_selects(view)[0].options) == 25


# ---------------------------------------------------------------------------
# Multi page — the truncation regression
# ---------------------------------------------------------------------------


def test_long_list_pages_without_dropping_any_option():
    """53 options (the live select_option_truncation candidate count) must all
    be reachable across pages — none truncated.
    """
    view = PaginatedSelectView(_author(), _opts(53), _noop)
    assert view.page_count == 3  # ceil(53 / 25)

    seen: set[str] = set()
    for page in range(view.page_count):
        view._page = page
        view._render()
        select = _selects(view)[0]
        assert len(select.options) <= MAX_OPTIONS
        seen.update(o.value for o in select.options)

    assert seen == {str(i) for i in range(53)}


def test_nav_disabled_state_at_edges():
    view = PaginatedSelectView(_author(), _opts(53), _noop)
    buttons = _buttons(view)
    assert len(buttons) == 2
    prev = next(b for b in buttons if "Prev" in (b.label or ""))
    nxt = next(b for b in buttons if "Next" in (b.label or ""))
    # First page: Prev disabled, Next enabled.
    assert prev.disabled is True
    assert nxt.disabled is False

    # Last page: Prev enabled, Next disabled.
    view._page = view.page_count - 1
    view._render()
    buttons = _buttons(view)
    prev = next(b for b in buttons if "Prev" in (b.label or ""))
    nxt = next(b for b in buttons if "Next" in (b.label or ""))
    assert prev.disabled is False
    assert nxt.disabled is True


def test_placeholder_shows_page_marker_when_multi_page():
    view = PaginatedSelectView(_author(), _opts(53), _noop, placeholder="Pick…")
    assert "page 1/3" in _selects(view)[0].placeholder


def test_custom_page_size_clamped_to_25():
    view = PaginatedSelectView(_author(), _opts(40), _noop, page_size=99)
    assert view._page_size == MAX_OPTIONS
    assert view.page_count == 2


def test_smaller_page_size_respected():
    view = PaginatedSelectView(_author(), _opts(25), _noop, page_size=10)
    assert view.page_count == 3
    assert len(_selects(view)[0].options) == 10


# ---------------------------------------------------------------------------
# Empty state
# ---------------------------------------------------------------------------


def test_empty_options_renders_disabled_sentinel():
    view = PaginatedSelectView(_author(), [], _noop)
    assert view.page_count == 1
    select = _selects(view)[0]
    assert select.disabled is True
    assert len(select.options) == 1
    assert _buttons(view) == []


# ---------------------------------------------------------------------------
# extra_items survive paging
# ---------------------------------------------------------------------------


def test_extra_items_preserved_across_render():
    extra = discord.ui.Button(label="◀ Back")
    view = PaginatedSelectView(_author(), _opts(53), _noop, extra_items=[extra])
    assert extra in view.children
    # After a page flip the extra item is re-added.
    view._page = 1
    view._render()
    assert extra in view.children


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dispatch_forwards_selected_values():
    captured: list[list[str]] = []

    async def on_select(interaction, values):  # noqa: ANN001
        captured.append(values)

    view = PaginatedSelectView(_author(), _opts(10), on_select)
    interaction = SimpleNamespace()
    await view._dispatch(interaction, ["3", "7"])
    assert captured == [["3", "7"]]


@pytest.mark.asyncio
async def test_dispatch_filters_empty_sentinel():
    from views.paginated_select import _EMPTY_VALUE

    captured: list[list[str]] = []

    async def on_select(interaction, values):  # noqa: ANN001
        captured.append(values)

    view = PaginatedSelectView(_author(), [], on_select)
    interaction = SimpleNamespace()
    await view._dispatch(interaction, [_EMPTY_VALUE])
    assert captured == [[]]


@pytest.mark.asyncio
async def test_change_page_edits_message_in_place():
    view = PaginatedSelectView(_author(), _opts(53), _noop)
    edit = AsyncMock()
    interaction = SimpleNamespace(response=SimpleNamespace(edit_message=edit))
    assert view._page == 0
    await view._change_page(interaction, 1)
    assert view._page == 1
    edit.assert_awaited_once()
    # The view re-rendered in place (passed as the view= kwarg).
    assert edit.await_args.kwargs["view"] is view


@pytest.mark.asyncio
async def test_change_page_clamps_at_edges():
    view = PaginatedSelectView(_author(), _opts(53), _noop)
    interaction = SimpleNamespace(response=SimpleNamespace(edit_message=AsyncMock()))
    await view._change_page(interaction, -1)  # below 0
    assert view._page == 0
    view._page = view.page_count - 1
    await view._change_page(interaction, 1)  # past last
    assert view._page == view.page_count - 1
