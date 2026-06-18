"""Tests for the shared windowed-select primitives.

Pins the #1040 regression at the root: a long option list is *windowed* into
≤25-option pages with Prev/Next nav, never front-truncated, so every option
stays reachable.  Covers both the standalone :class:`PaginatedSelectView` and
the embedded :func:`attach_windowed_select` path (a window dropped into a host
view that already carries other controls).
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import discord
import pytest

from views.base import BaseView
from views.paginated_select import (
    MAX_OPTIONS,
    PaginatedSelectView,
    SelectWindow,
    _PageButton,
    _WindowSelect,
    attach_windowed_select,
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


def _window(view) -> SelectWindow:
    return view._window


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
    win = _window(view)
    assert view.page_count == 3  # ceil(53 / 25)

    seen: set[str] = set()
    for page in range(view.page_count):
        win.page = page
        win.render()
        select = _selects(view)[0]
        assert len(select.options) <= MAX_OPTIONS
        seen.update(o.value for o in select.options)

    assert seen == {str(i) for i in range(53)}


def test_nav_disabled_state_at_edges():
    view = PaginatedSelectView(_author(), _opts(53), _noop)
    win = _window(view)
    buttons = _buttons(view)
    assert len(buttons) == 2
    prev = next(b for b in buttons if "Prev" in (b.label or ""))
    nxt = next(b for b in buttons if "Next" in (b.label or ""))
    # First page: Prev disabled, Next enabled.
    assert prev.disabled is True
    assert nxt.disabled is False

    # Last page: Prev enabled, Next disabled.
    win.page = view.page_count - 1
    win.render()
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
    assert _window(view)._page_size == MAX_OPTIONS
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
    _window(view).page = 1
    _window(view).render()
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
    await _window(view)._dispatch(interaction, ["3", "7"])
    assert captured == [["3", "7"]]


@pytest.mark.asyncio
async def test_dispatch_filters_empty_sentinel():
    from views.paginated_select import _EMPTY_VALUE

    captured: list[list[str]] = []

    async def on_select(interaction, values):  # noqa: ANN001
        captured.append(values)

    view = PaginatedSelectView(_author(), [], on_select)
    interaction = SimpleNamespace()
    await _window(view)._dispatch(interaction, [_EMPTY_VALUE])
    assert captured == [[]]


@pytest.mark.asyncio
async def test_change_page_edits_message_in_place():
    view = PaginatedSelectView(_author(), _opts(53), _noop)
    win = _window(view)
    edit = AsyncMock()
    interaction = SimpleNamespace(response=SimpleNamespace(edit_message=edit))
    assert win.page == 0
    await win._change_page(interaction, 1)
    assert win.page == 1
    edit.assert_awaited_once()
    # The view re-rendered in place (passed as the view= kwarg).
    assert edit.await_args.kwargs["view"] is view


@pytest.mark.asyncio
async def test_change_page_clamps_at_edges():
    view = PaginatedSelectView(_author(), _opts(53), _noop)
    win = _window(view)
    interaction = SimpleNamespace(response=SimpleNamespace(edit_message=AsyncMock()))
    await win._change_page(interaction, -1)  # below 0
    assert win.page == 0
    win.page = view.page_count - 1
    await win._change_page(interaction, 1)  # past last
    assert win.page == view.page_count - 1


# ---------------------------------------------------------------------------
# Embedded path — attach_windowed_select into a host with other controls
# ---------------------------------------------------------------------------


class _HostPanel(BaseView):
    """A panel with its own button, plus an embedded windowed select."""

    def __init__(self, options, on_select):  # noqa: ANN001
        super().__init__(_author())
        self.add_item(discord.ui.Button(label="Sibling", row=4))
        self.window = attach_windowed_select(
            self,
            options,
            on_select,
            placeholder="Pick…",
            select_row=0,
            nav_row=4,
        )


def _sibling_buttons(view):
    return [
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and not isinstance(c, _PageButton)
    ]


def test_embedded_window_coexists_with_host_controls():
    view = _HostPanel(_opts(53), _noop)
    # The window's band + the host's own button are all present.
    assert len(_selects(view)) == 1
    assert len(_buttons(view)) == 2  # Prev/Next (multi-page)
    assert len(_sibling_buttons(view)) == 1  # the host's "Sibling" button
    # The select sits on its requested row, nav on the shared row.
    assert _selects(view)[0].row == 0
    assert all(b.row == 4 for b in _buttons(view))


def test_embedded_page_flip_preserves_host_controls():
    view = _HostPanel(_opts(53), _noop)
    sibling = _sibling_buttons(view)[0]
    win = view.window
    win.page = 1
    win.render()
    # The host's sibling button survives the window re-render untouched.
    assert sibling in view.children
    assert len(_sibling_buttons(view)) == 1
    # And the window swapped to page 2's options (no duplicates left behind).
    assert len(_selects(view)) == 1
    assert _selects(view)[0].options[0].value == str(MAX_OPTIONS)


def test_embedded_single_page_adds_no_nav_buttons():
    view = _HostPanel(_opts(5), _noop)
    assert _buttons(view) == []
    assert len(_sibling_buttons(view)) == 1


@pytest.mark.asyncio
async def test_embedded_change_page_edits_host_view_in_place():
    view = _HostPanel(_opts(53), _noop)
    win = view.window
    edit = AsyncMock()
    interaction = SimpleNamespace(response=SimpleNamespace(edit_message=edit))
    await win._change_page(interaction, 1)
    assert win.page == 1
    edit.assert_awaited_once()
    assert edit.await_args.kwargs["view"] is view


@pytest.mark.asyncio
async def test_embedded_dispatch_forwards_values():
    captured: list[list[str]] = []

    async def on_select(interaction, values):  # noqa: ANN001
        captured.append(values)

    view = _HostPanel(_opts(40), on_select)
    interaction = SimpleNamespace()
    await view.window._dispatch(interaction, ["7"])
    assert captured == [["7"]]
