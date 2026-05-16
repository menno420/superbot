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

import pytest

from views.selectors import (
    ChannelSelector,
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
        guild_id=10, category_id=20, channel_id=30, on_select=AsyncMock(),
    )
    values = [o.value for o in sel.options]
    assert "channel:30" in values
    assert "category:20" in values
    assert "guild:10" in values


def test_scope_selector_omits_missing_levels():
    sel = ScopeSelector(
        guild_id=10, category_id=None, channel_id=None, on_select=AsyncMock(),
    )
    values = [o.value for o in sel.options]
    assert values == ["guild:10"]


@pytest.mark.asyncio
async def test_scope_selector_parses_value():
    cb = AsyncMock()
    sel = ScopeSelector(
        guild_id=10, category_id=20, channel_id=30, on_select=cb,
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
