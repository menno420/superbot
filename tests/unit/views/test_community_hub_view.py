"""Unit tests for the Community hub view (S9).

Pins the v1 behaviour:

- Five cross-link buttons routing to xp / role / counting / chain /
  leaderboard via each cog's existing ``build_help_menu_view`` hook.
- Buttons follow the hub-ui-standard layout: progression on row 0,
  community activities on row 1.
- Stable custom_ids in ``community:open:<subsystem>`` form.
- Failure paths surface as ephemerals; the message is never left
  half-edited.

The hub is nav-only — no DB writes, no game logic, no governance
resolution.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from views.community.hub import (
    CommunityHubView,
    _CommunityChildButton,
    build_community_hub_embed,
)


def _author(id_: int = 1) -> MagicMock:
    author = MagicMock(spec=discord.Member)
    author.id = id_
    return author


def _interaction() -> MagicMock:
    interaction = MagicMock(spec=discord.Interaction)
    interaction.client = MagicMock()
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    return interaction


# ---------------------------------------------------------------------------
# Embed
# ---------------------------------------------------------------------------


def test_embed_lists_all_five_children():
    embed = build_community_hub_embed()
    description = embed.description or ""
    for token in ("XP", "Roles", "Counting", "Chain", "Leaderboard"):
        assert token in description, token


def test_embed_title_and_color():
    embed = build_community_hub_embed()
    assert "Community" in (embed.title or "")
    assert embed.color is not None


# ---------------------------------------------------------------------------
# View shape — five buttons routing to the five child subsystems
# ---------------------------------------------------------------------------


def test_view_has_five_child_buttons():
    view = CommunityHubView(_author())
    buttons = [c for c in view.children if isinstance(c, _CommunityChildButton)]
    assert len(buttons) == 5


def test_buttons_cover_each_target_subsystem():
    view = CommunityHubView(_author())
    subsystems = {btn._subsystem for btn in view.children if isinstance(btn, _CommunityChildButton)}  # type: ignore[attr-defined]
    assert subsystems == {"xp", "role", "counting", "chain", "leaderboard"}


def test_button_custom_ids_are_stable_and_namespaced():
    view = CommunityHubView(_author())
    ids = {
        c.custom_id
        for c in view.children
        if isinstance(c, _CommunityChildButton)
    }
    assert ids == {
        "community:open:xp",
        "community:open:role",
        "community:open:counting",
        "community:open:chain",
        "community:open:leaderboard",
    }


def test_buttons_split_across_two_rows():
    """Progression (XP/Roles) sit on row 0; community activities
    (Counting/Chain/Leaderboard) sit on row 1 — pinning the layout
    keeps the hub-ui-standard preset stable across edits.
    """
    view = CommunityHubView(_author())
    row0 = {
        btn._subsystem  # type: ignore[attr-defined]
        for btn in view.children
        if isinstance(btn, _CommunityChildButton) and btn.row == 0
    }
    row1 = {
        btn._subsystem  # type: ignore[attr-defined]
        for btn in view.children
        if isinstance(btn, _CommunityChildButton) and btn.row == 1
    }
    assert row0 == {"xp", "role"}
    assert row1 == {"counting", "chain", "leaderboard"}


# ---------------------------------------------------------------------------
# Button callback routing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_button_opens_host_cog_panel_in_place():
    button = _CommunityChildButton(
        subsystem="xp",
        label="🏆 XP",
        style=discord.ButtonStyle.primary,
        row=0,
    )
    fake_cog = MagicMock()
    fake_embed = discord.Embed(title="XP")
    fake_view = discord.ui.View()
    fake_cog.build_help_menu_view = AsyncMock(return_value=(fake_embed, fake_view))

    interaction = _interaction()
    with patch("cogs.help_cog._cog_for_subsystem", return_value=fake_cog):
        await button.callback(interaction)

    fake_cog.build_help_menu_view.assert_awaited_once_with(interaction)
    interaction.response.edit_message.assert_awaited_once()
    _args, kwargs = interaction.response.edit_message.call_args
    assert kwargs["embed"] is fake_embed
    assert kwargs["view"] is fake_view


@pytest.mark.asyncio
async def test_button_missing_cog_sends_ephemeral():
    button = _CommunityChildButton(
        subsystem="xp",
        label="🏆 XP",
        style=discord.ButtonStyle.primary,
        row=0,
    )
    interaction = _interaction()
    with patch("cogs.help_cog._cog_for_subsystem", return_value=None):
        await button.callback(interaction)
    interaction.response.send_message.assert_awaited_once()
    interaction.response.edit_message.assert_not_called()


@pytest.mark.asyncio
async def test_button_cog_without_hook_sends_ephemeral():
    button = _CommunityChildButton(
        subsystem="xp",
        label="🏆 XP",
        style=discord.ButtonStyle.primary,
        row=0,
    )
    fake_cog = MagicMock(spec=[])  # no build_help_menu_view attr
    interaction = _interaction()
    with patch("cogs.help_cog._cog_for_subsystem", return_value=fake_cog):
        await button.callback(interaction)
    interaction.response.send_message.assert_awaited_once()
    interaction.response.edit_message.assert_not_called()


@pytest.mark.asyncio
async def test_button_hook_exception_sends_ephemeral():
    button = _CommunityChildButton(
        subsystem="xp",
        label="🏆 XP",
        style=discord.ButtonStyle.primary,
        row=0,
    )
    fake_cog = MagicMock()
    fake_cog.build_help_menu_view = AsyncMock(side_effect=RuntimeError("boom"))
    interaction = _interaction()
    with patch("cogs.help_cog._cog_for_subsystem", return_value=fake_cog):
        await button.callback(interaction)
    interaction.response.send_message.assert_awaited_once()
    interaction.response.edit_message.assert_not_called()


# ---------------------------------------------------------------------------
# Doctrine: hub is nav-only
# ---------------------------------------------------------------------------


def test_view_contains_no_select_components():
    """The Community hub uses buttons exclusively — five children fit
    under the hub-ui-standard ≤8-button threshold.
    """
    view = CommunityHubView(_author())
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    assert selects == []
