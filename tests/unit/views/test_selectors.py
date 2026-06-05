"""Tests for the reusable views.selectors primitives (D1).

The selectors are thin wrappers over ``discord.ui.Select`` that
enforce the 25-option Discord cap and dispatch to an async callback
with parsed identifiers.  These tests verify:

- ChannelSelector truncates lists > 25 entries
- RoleSelector applies the default filter (skips @everyone)
- ScopeSelector renders the right options for each context
- SubsystemSelector pulls from the live registry and omits internal mode
- All four selectors invoke their on_select awaitable with parsed args
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from views.selectors import (
    ChannelSelector,
    MultiChannelSelector,
    MultiRoleSelector,
    MultiSelect,
    RoleSelector,
    ScopeSelector,
    SubsystemSelector,
)

# ---------------------------------------------------------------------------
# ChannelSelector
# ---------------------------------------------------------------------------


def _channel(cid: int, name: str = "general") -> MagicMock:
    ch = MagicMock()
    ch.id = cid
    ch.name = name
    return ch


@pytest.mark.asyncio
async def test_channel_selector_truncates_to_25():
    channels = [_channel(i, f"c{i}") for i in range(40)]
    sel = ChannelSelector(channels, on_select=AsyncMock())
    assert len(sel.options) == 25


@pytest.mark.asyncio
async def test_channel_selector_invokes_callback_with_int_id():
    channels = [_channel(123, "general")]
    cb = AsyncMock()
    sel = ChannelSelector(channels, on_select=cb)
    sel._values = ["123"]  # discord.ui.Select stores selection here
    interaction = MagicMock()
    await sel.callback(interaction)
    cb.assert_awaited_once_with(interaction, 123)


# ---------------------------------------------------------------------------
# RoleSelector
# ---------------------------------------------------------------------------


def _role(rid: int, name: str = "Member", default: bool = False) -> MagicMock:
    r = MagicMock()
    r.id = rid
    r.name = name
    r.is_default = MagicMock(return_value=default)
    return r


@pytest.mark.asyncio
async def test_role_selector_filters_out_everyone_by_default():
    roles = [_role(1, "@everyone", default=True), _role(2, "Member")]
    sel = RoleSelector(roles, on_select=AsyncMock())
    # @everyone is filtered out; one real option remains.
    assert len(sel.options) == 1
    assert sel.options[0].label == "Member"


@pytest.mark.asyncio
async def test_role_selector_truncates_to_25():
    roles = [_role(i, f"r{i}") for i in range(30)]
    sel = RoleSelector(roles, on_select=AsyncMock())
    assert len(sel.options) == 25


@pytest.mark.asyncio
async def test_role_selector_custom_filter():
    roles = [_role(1, "Admin"), _role(2, "Moderator"), _role(3, "User")]
    sel = RoleSelector(
        roles,
        on_select=AsyncMock(),
        role_filter=lambda r: r.name in ("Admin", "Moderator"),
    )
    labels = {o.label for o in sel.options}
    assert labels == {"Admin", "Moderator"}


@pytest.mark.asyncio
async def test_role_selector_invokes_callback():
    cb = AsyncMock()
    sel = RoleSelector([_role(42)], on_select=cb)
    sel._values = ["42"]
    interaction = MagicMock()
    await sel.callback(interaction)
    cb.assert_awaited_once_with(interaction, 42)


# ---------------------------------------------------------------------------
# ScopeSelector
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
# SubsystemSelector
# ---------------------------------------------------------------------------


def test_subsystem_selector_excludes_internal_when_visible_only():
    sel = SubsystemSelector(on_select=AsyncMock(), visible_only=True)
    from utils.subsystem_registry import SUBSYSTEMS

    expected_visible = {
        name
        for name, meta in SUBSYSTEMS.items()
        if meta.get("visibility_mode") != "internal"
    }
    rendered = {o.value for o in sel.options}
    # The selector caps at 25, but every option must be in the visible set.
    assert rendered.issubset(expected_visible)


@pytest.mark.asyncio
async def test_subsystem_selector_invokes_callback_with_name():
    cb = AsyncMock()
    sel = SubsystemSelector(on_select=cb)
    sel._values = ["role"]
    interaction = MagicMock()
    await sel.callback(interaction)
    cb.assert_awaited_once_with(interaction, "role")


# ---------------------------------------------------------------------------
# MultiSelect (P1-10)
# ---------------------------------------------------------------------------


def _opt(value: str, label: str | None = None) -> discord.SelectOption:
    return discord.SelectOption(label=label or value, value=value)


def test_multiselect_defaults_max_to_all_options():
    sel = MultiSelect([_opt("a"), _opt("b"), _opt("c")], on_select=AsyncMock())
    assert sel.max_values == 3
    assert sel.min_values == 0


def test_multiselect_truncates_options_and_clamps_max():
    sel = MultiSelect([_opt(str(i)) for i in range(40)], on_select=AsyncMock())
    assert len(sel.options) == 25
    # max_values can never exceed the option count Discord sees.
    assert sel.max_values == 25


def test_multiselect_explicit_max_is_clamped_to_option_count():
    sel = MultiSelect([_opt("a"), _opt("b")], on_select=AsyncMock(), max_values=10)
    assert sel.max_values == 2


def test_multiselect_empty_options_fall_back_to_placeholder():
    # Must not raise on an empty collection (the gap ChannelSelector has).
    sel = MultiSelect([], on_select=AsyncMock())
    assert len(sel.options) == 1
    assert sel.max_values == 1


@pytest.mark.asyncio
async def test_multiselect_invokes_callback_with_selected_values():
    cb = AsyncMock()
    sel = MultiSelect([_opt("a"), _opt("b"), _opt("c")], on_select=cb)
    sel._values = ["a", "c"]
    interaction = MagicMock()
    await sel.callback(interaction)
    cb.assert_awaited_once_with(interaction, ["a", "c"])


@pytest.mark.asyncio
async def test_multiselect_filters_empty_guard_sentinel():
    cb = AsyncMock()
    sel = MultiSelect([], on_select=cb)  # only the sentinel option exists
    sel._values = [""]  # user somehow "picked" the placeholder
    interaction = MagicMock()
    await sel.callback(interaction)
    cb.assert_awaited_once_with(interaction, [])


# ---------------------------------------------------------------------------
# MultiChannelSelector
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_multi_channel_selector_truncates_to_25():
    channels = [_channel(i, f"c{i}") for i in range(40)]
    sel = MultiChannelSelector(channels, on_select=AsyncMock())
    assert len(sel.options) == 25


@pytest.mark.asyncio
async def test_multi_channel_selector_invokes_callback_with_int_ids():
    channels = [_channel(11, "a"), _channel(22, "b"), _channel(33, "c")]
    cb = AsyncMock()
    sel = MultiChannelSelector(channels, on_select=cb)
    sel._values = ["11", "33"]
    interaction = MagicMock()
    await sel.callback(interaction)
    cb.assert_awaited_once_with(interaction, [11, 33])


@pytest.mark.asyncio
async def test_multi_channel_selector_skips_unparseable_values():
    channels = [_channel(11, "a")]
    cb = AsyncMock()
    sel = MultiChannelSelector(channels, on_select=cb)
    sel._values = ["11", "not-an-int"]
    interaction = MagicMock()
    await sel.callback(interaction)
    cb.assert_awaited_once_with(interaction, [11])


# ---------------------------------------------------------------------------
# MultiRoleSelector (PR2)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_multi_role_selector_filters_everyone_by_default():
    roles = [_role(1, "@everyone", default=True), _role(2, "Member"), _role(3, "Admin")]
    sel = MultiRoleSelector(roles, on_select=AsyncMock())
    assert {o.label for o in sel.options} == {"Member", "Admin"}


@pytest.mark.asyncio
async def test_multi_role_selector_truncates_to_25():
    roles = [_role(i, f"r{i}") for i in range(40)]
    sel = MultiRoleSelector(roles, on_select=AsyncMock())
    assert len(sel.options) == 25


@pytest.mark.asyncio
async def test_multi_role_selector_custom_filter():
    roles = [_role(1, "Admin"), _role(2, "Mod"), _role(3, "User")]
    sel = MultiRoleSelector(
        roles,
        on_select=AsyncMock(),
        role_filter=lambda r: r.name in ("Admin", "Mod"),
    )
    assert {o.label for o in sel.options} == {"Admin", "Mod"}


@pytest.mark.asyncio
async def test_multi_role_selector_invokes_callback_with_int_ids():
    roles = [_role(11, "a"), _role(22, "b"), _role(33, "c")]
    cb = AsyncMock()
    sel = MultiRoleSelector(roles, on_select=cb)
    sel._values = ["11", "33"]
    interaction = MagicMock()
    await sel.callback(interaction)
    cb.assert_awaited_once_with(interaction, [11, 33])


@pytest.mark.asyncio
async def test_multi_role_selector_skips_unparseable_values():
    roles = [_role(11, "a")]
    cb = AsyncMock()
    sel = MultiRoleSelector(roles, on_select=cb)
    sel._values = ["11", "nope"]
    interaction = MagicMock()
    await sel.callback(interaction)
    cb.assert_awaited_once_with(interaction, [11])
