"""Tests for the reusable views.selectors primitives (D1).

The selectors are now ``attach_*`` helpers that attach a *windowed* select to
a host view (``views.paginated_select.attach_windowed_select``): any-length
collections are paginated past Discord's 25-option cap instead of
front-truncated (the #1040 class).  These tests verify:

- a long list is windowed (page 1 caps at 25; ``page_count`` > 1) — never dropped
- RoleSelector applies the default filter (skips @everyone)
- ScopeSelector renders the right options for each context (still a plain Select)
- SubsystemSelector pulls from the live registry and omits internal mode
- every helper invokes its on_select awaitable with parsed args
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from views.selectors import (
    ScopeSelector,
    attach_channel_select,
    attach_multi_channel_select,
    attach_multi_role_select,
    attach_multi_select,
    attach_role_select,
    attach_subsystem_select,
)


def _host() -> discord.ui.View:
    """A bare host view the windowed select attaches into."""
    return discord.ui.View()


def _select(view: discord.ui.View) -> discord.ui.Select:
    """The windowed ``Select`` item the helper added to ``view``."""
    return next(c for c in view.children if isinstance(c, discord.ui.Select))


# ---------------------------------------------------------------------------
# attach_channel_select
# ---------------------------------------------------------------------------


def _channel(cid: int, name: str = "general") -> MagicMock:
    ch = MagicMock()
    ch.id = cid
    ch.name = name
    return ch


def test_channel_select_windows_long_list_without_dropping():
    channels = [_channel(i, f"c{i}") for i in range(40)]
    view = _host()
    window = attach_channel_select(view, channels, on_select=AsyncMock())
    # 40 options across 2 pages — none silently dropped.
    assert window.page_count == 2
    assert len(_select(view).options) == 25


@pytest.mark.asyncio
async def test_channel_select_invokes_callback_with_int_id():
    cb = AsyncMock()
    view = _host()
    attach_channel_select(view, [_channel(123, "general")], on_select=cb)
    sel = _select(view)
    sel._values = ["123"]  # discord.ui.Select stores selection here
    interaction = MagicMock()
    await sel.callback(interaction)
    cb.assert_awaited_once_with(interaction, 123)


# ---------------------------------------------------------------------------
# attach_role_select
# ---------------------------------------------------------------------------


def _role(rid: int, name: str = "Member", default: bool = False) -> MagicMock:
    r = MagicMock()
    r.id = rid
    r.name = name
    r.is_default = MagicMock(return_value=default)
    return r


def test_role_select_filters_out_everyone_by_default():
    roles = [_role(1, "@everyone", default=True), _role(2, "Member")]
    view = _host()
    attach_role_select(view, roles, on_select=AsyncMock())
    opts = _select(view).options
    assert len(opts) == 1
    assert opts[0].label == "Member"


def test_role_select_windows_long_list_without_dropping():
    roles = [_role(i, f"r{i}") for i in range(30)]
    view = _host()
    window = attach_role_select(view, roles, on_select=AsyncMock())
    assert window.page_count == 2
    assert len(_select(view).options) == 25


def test_role_select_custom_filter():
    roles = [_role(1, "Admin"), _role(2, "Moderator"), _role(3, "User")]
    view = _host()
    attach_role_select(
        view,
        roles,
        on_select=AsyncMock(),
        role_filter=lambda r: r.name in ("Admin", "Moderator"),
    )
    labels = {o.label for o in _select(view).options}
    assert labels == {"Admin", "Moderator"}


@pytest.mark.asyncio
async def test_role_select_invokes_callback():
    cb = AsyncMock()
    view = _host()
    attach_role_select(view, [_role(42)], on_select=cb)
    sel = _select(view)
    sel._values = ["42"]
    interaction = MagicMock()
    await sel.callback(interaction)
    cb.assert_awaited_once_with(interaction, 42)


# ---------------------------------------------------------------------------
# ScopeSelector (unchanged — at most 3 fixed options, never windowed)
# ---------------------------------------------------------------------------


def test_scope_selector_offers_channel_category_guild_when_all_present():
    sel = ScopeSelector(
        guild_id=10,
        category_id=20,
        channel_id=30,
        on_select=AsyncMock(),
    )
    values = [o.value for o in sel.options]
    assert "channel:30" in values
    assert "category:20" in values
    assert "guild:10" in values


def test_scope_selector_omits_missing_levels():
    sel = ScopeSelector(
        guild_id=10,
        category_id=None,
        channel_id=None,
        on_select=AsyncMock(),
    )
    values = [o.value for o in sel.options]
    assert values == ["guild:10"]


@pytest.mark.asyncio
async def test_scope_selector_parses_value():
    cb = AsyncMock()
    sel = ScopeSelector(
        guild_id=10,
        category_id=20,
        channel_id=30,
        on_select=cb,
    )
    sel._values = ["category:20"]
    interaction = MagicMock()
    await sel.callback(interaction)
    cb.assert_awaited_once_with(interaction, "category", 20)


# ---------------------------------------------------------------------------
# attach_subsystem_select
# ---------------------------------------------------------------------------


def test_subsystem_select_excludes_internal_when_visible_only():
    view = _host()
    attach_subsystem_select(view, on_select=AsyncMock(), visible_only=True)
    from utils.subsystem_registry import SUBSYSTEMS

    expected_visible = {
        name
        for name, meta in SUBSYSTEMS.items()
        if meta.get("visibility_mode") != "internal"
    }
    rendered = {o.value for o in _select(view).options}
    # Page 1 caps at 25, but every option must be in the visible set.
    assert rendered.issubset(expected_visible)


@pytest.mark.asyncio
async def test_subsystem_select_invokes_callback_with_name():
    cb = AsyncMock()
    view = _host()
    attach_subsystem_select(view, on_select=cb)
    sel = _select(view)
    sel._values = ["role"]
    interaction = MagicMock()
    await sel.callback(interaction)
    cb.assert_awaited_once_with(interaction, "role")


# ---------------------------------------------------------------------------
# attach_multi_select (P1-10)
# ---------------------------------------------------------------------------


def _opt(value: str, label: str | None = None) -> discord.SelectOption:
    return discord.SelectOption(label=label or value, value=value)


def test_multi_select_defaults_max_to_all_options_on_page():
    view = _host()
    attach_multi_select(view, [_opt("a"), _opt("b"), _opt("c")], on_select=AsyncMock())
    sel = _select(view)
    assert sel.max_values == 3
    assert sel.min_values == 0


def test_multi_select_windows_long_list_and_clamps_max_per_page():
    view = _host()
    window = attach_multi_select(
        view,
        [_opt(str(i)) for i in range(40)],
        on_select=AsyncMock(),
    )
    sel = _select(view)
    assert window.page_count == 2
    assert len(sel.options) == 25
    # max_values can never exceed the option count Discord sees on the page.
    assert sel.max_values == 25


def test_multi_select_explicit_max_is_clamped_to_option_count():
    view = _host()
    attach_multi_select(view, [_opt("a"), _opt("b")], on_select=AsyncMock(), max_values=10)
    assert _select(view).max_values == 2


def test_multi_select_empty_options_fall_back_to_placeholder():
    # Must not raise on an empty collection.
    view = _host()
    attach_multi_select(view, [], on_select=AsyncMock())
    sel = _select(view)
    assert len(sel.options) == 1
    assert sel.max_values == 1


@pytest.mark.asyncio
async def test_multi_select_invokes_callback_with_selected_values():
    cb = AsyncMock()
    view = _host()
    attach_multi_select(view, [_opt("a"), _opt("b"), _opt("c")], on_select=cb)
    sel = _select(view)
    sel._values = ["a", "c"]
    interaction = MagicMock()
    await sel.callback(interaction)
    cb.assert_awaited_once_with(interaction, ["a", "c"])


@pytest.mark.asyncio
async def test_multi_select_filters_empty_guard_sentinel():
    cb = AsyncMock()
    view = _host()
    attach_multi_select(view, [], on_select=cb)  # only the sentinel option exists
    sel = _select(view)
    # The sentinel value the windowing layer uses for an empty list.
    sel._values = [sel.options[0].value]
    interaction = MagicMock()
    await sel.callback(interaction)
    cb.assert_awaited_once_with(interaction, [])


# ---------------------------------------------------------------------------
# attach_multi_channel_select
# ---------------------------------------------------------------------------


def test_multi_channel_select_windows_long_list_without_dropping():
    channels = [_channel(i, f"c{i}") for i in range(40)]
    view = _host()
    window = attach_multi_channel_select(view, channels, on_select=AsyncMock())
    assert window.page_count == 2
    assert len(_select(view).options) == 25


@pytest.mark.asyncio
async def test_multi_channel_select_invokes_callback_with_int_ids():
    channels = [_channel(11, "a"), _channel(22, "b"), _channel(33, "c")]
    cb = AsyncMock()
    view = _host()
    attach_multi_channel_select(view, channels, on_select=cb)
    sel = _select(view)
    sel._values = ["11", "33"]
    interaction = MagicMock()
    await sel.callback(interaction)
    cb.assert_awaited_once_with(interaction, [11, 33])


@pytest.mark.asyncio
async def test_multi_channel_select_skips_unparseable_values():
    cb = AsyncMock()
    view = _host()
    attach_multi_channel_select(view, [_channel(11, "a")], on_select=cb)
    sel = _select(view)
    sel._values = ["11", "not-an-int"]
    interaction = MagicMock()
    await sel.callback(interaction)
    cb.assert_awaited_once_with(interaction, [11])


# ---------------------------------------------------------------------------
# attach_multi_role_select (PR2)
# ---------------------------------------------------------------------------


def test_multi_role_select_filters_everyone_by_default():
    roles = [_role(1, "@everyone", default=True), _role(2, "Member"), _role(3, "Admin")]
    view = _host()
    attach_multi_role_select(view, roles, on_select=AsyncMock())
    assert {o.label for o in _select(view).options} == {"Member", "Admin"}


def test_multi_role_select_windows_long_list_without_dropping():
    roles = [_role(i, f"r{i}") for i in range(40)]
    view = _host()
    window = attach_multi_role_select(view, roles, on_select=AsyncMock())
    assert window.page_count == 2
    assert len(_select(view).options) == 25


def test_multi_role_select_custom_filter():
    roles = [_role(1, "Admin"), _role(2, "Mod"), _role(3, "User")]
    view = _host()
    attach_multi_role_select(
        view,
        roles,
        on_select=AsyncMock(),
        role_filter=lambda r: r.name in ("Admin", "Mod"),
    )
    assert {o.label for o in _select(view).options} == {"Admin", "Mod"}


@pytest.mark.asyncio
async def test_multi_role_select_invokes_callback_with_int_ids():
    roles = [_role(11, "a"), _role(22, "b"), _role(33, "c")]
    cb = AsyncMock()
    view = _host()
    attach_multi_role_select(view, roles, on_select=cb)
    sel = _select(view)
    sel._values = ["11", "33"]
    interaction = MagicMock()
    await sel.callback(interaction)
    cb.assert_awaited_once_with(interaction, [11, 33])


@pytest.mark.asyncio
async def test_multi_role_select_skips_unparseable_values():
    cb = AsyncMock()
    view = _host()
    attach_multi_role_select(view, [_role(11, "a")], on_select=cb)
    sel = _select(view)
    sel._values = ["11", "nope"]
    interaction = MagicMock()
    await sel.callback(interaction)
    cb.assert_awaited_once_with(interaction, [11])
