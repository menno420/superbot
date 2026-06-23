"""Unit tests for the shared hub child-discovery primitive + HubChildButton."""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from governance.models import VisibilityResult
from utils.subsystem_registry import SUBSYSTEMS
from views.hub_children import HubChildButton, discover_hub_children


def test_utility_children_are_general_and_four_twenty():
    """The Utility hub's registry children (the general-cog fix relies on this)."""
    keys = [name for name, _ in discover_hub_children("utility")]
    assert "general" in keys
    assert "four_twenty" in keys


def test_unknown_hub_has_no_children():
    assert discover_hub_children("nope-not-a-hub") == []


def test_default_sort_is_ui_priority_then_key(monkeypatch):
    fake = {
        "b_low": {"parent_hub": "h", "ui_priority": 5},
        "a_high": {"parent_hub": "h", "ui_priority": 1},
        "c_mid": {"parent_hub": "h", "ui_priority": 1},  # tie → key order
        "other": {"parent_hub": "elsewhere", "ui_priority": 0},
    }
    monkeypatch.setattr("views.hub_children.SUBSYSTEMS", fake)
    assert [n for n, _ in discover_hub_children("h")] == ["a_high", "c_mid", "b_low"]


def test_group_order_sorts_groups_first(monkeypatch):
    fake = {
        "act": {"parent_hub": "g", "hub_group": "activities", "ui_priority": 0},
        "comp": {"parent_hub": "g", "hub_group": "competitive", "ui_priority": 9},
    }
    monkeypatch.setattr("views.hub_children.SUBSYSTEMS", fake)
    order = {"competitive": 0, "activities": 1}
    # competitive ranks first despite higher ui_priority — group beats priority.
    assert [n for n, _ in discover_hub_children("g", group_order=order)] == [
        "comp",
        "act",
    ]


def test_meta_is_copied(monkeypatch):
    fake = {"x": {"parent_hub": "h", "ui_priority": 0}}
    monkeypatch.setattr("views.hub_children.SUBSYSTEMS", fake)
    _, meta = discover_hub_children("h")[0]
    meta["mutated"] = True
    assert "mutated" not in fake["x"]  # caller mutation must not leak into the registry


def test_delegation_matches_games_and_community():
    """The 3 hubs delegate to this primitive — pin the equivalence."""
    from views.community.hub import discover_community_children
    from views.games.hub import _GROUP_ORDER, discover_game_children

    assert discover_game_children() == discover_hub_children(
        "games", group_order=_GROUP_ORDER
    )
    primary, _cross = discover_community_children()
    assert primary == discover_hub_children("community")


# ---------------------------------------------------------------------------
# HubChildButton — the shared child-forwarding button (the "first consolidation")
# ---------------------------------------------------------------------------


def _interaction() -> MagicMock:
    i = MagicMock(spec=discord.Interaction)
    i.client = MagicMock()
    i.user = MagicMock(spec=discord.Member)
    i.user.id = 1
    i.response = MagicMock()
    i.response.send_message = AsyncMock()
    i.response.edit_message = AsyncMock()
    return i


@contextmanager
def _all_visible():
    vr = VisibilityResult(
        visible_subsystems=set(SUBSYSTEMS),
        member_tier="user",
        resolved_from={},
        traces={},
    )
    with patch(
        "services.governance_service.resolve_visibility",
        new_callable=AsyncMock,
        return_value=vr,
    ):
        yield


def _button(*, fallback_builder=None, back_attacher=None) -> HubChildButton:
    return HubChildButton(
        hub_key="testhub",
        subsystem="general",
        label="X",
        style=discord.ButtonStyle.primary,
        row=0,
        back_attacher=back_attacher or MagicMock(return_value=True),
        fallback_builder=fallback_builder,
    )


def test_custom_id_is_hub_scoped():
    assert _button().custom_id == "testhub:open:general"


async def test_forwards_to_hook_and_attaches_back():
    back = MagicMock(return_value=True)
    button = _button(back_attacher=back)
    interaction = _interaction()
    embed = discord.Embed(title="G")
    sub_view = discord.ui.View()
    cog = MagicMock()
    cog.build_help_menu_view = AsyncMock(return_value=(embed, sub_view))

    with _all_visible(), patch("cogs.help_cog._cog_for_subsystem", return_value=cog):
        await button.callback(interaction)

    cog.build_help_menu_view.assert_awaited_once_with(interaction)
    interaction.response.edit_message.assert_awaited_once()
    assert interaction.response.edit_message.await_args.kwargs["embed"] is embed
    back.assert_called_once()  # the hub's Back attacher ran on the child view


async def test_invisible_child_fails_closed():
    button = _button()
    interaction = _interaction()
    vr = VisibilityResult(
        visible_subsystems=set(),
        member_tier="user",
        resolved_from={},
        traces={},
    )
    with patch(
        "services.governance_service.resolve_visibility",
        new_callable=AsyncMock,
        return_value=vr,
    ):
        await button.callback(interaction)
    interaction.response.send_message.assert_awaited_once()
    assert interaction.response.send_message.await_args.kwargs.get("ephemeral") is True
    interaction.response.edit_message.assert_not_called()


async def test_missing_cog_without_fallback_sends_ephemeral():
    """Community / Utility behaviour — no fallback_builder → fail closed."""
    button = _button(fallback_builder=None)
    interaction = _interaction()
    with _all_visible(), patch("cogs.help_cog._cog_for_subsystem", return_value=None):
        await button.callback(interaction)
    interaction.response.send_message.assert_awaited_once()
    interaction.response.edit_message.assert_not_called()


async def test_missing_cog_with_fallback_edits_in_place():
    """Games-ready behaviour — a fallback_builder edits a graceful embed in place."""
    fallback_embed = discord.Embed(title="no panel")
    fb = MagicMock(return_value=fallback_embed)
    button = _button(fallback_builder=fb)
    interaction = _interaction()
    with _all_visible(), patch("cogs.help_cog._cog_for_subsystem", return_value=None):
        await button.callback(interaction)
    fb.assert_called_once()
    interaction.response.edit_message.assert_awaited_once()
    assert (
        interaction.response.edit_message.await_args.kwargs["embed"] is fallback_embed
    )
    interaction.response.send_message.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
