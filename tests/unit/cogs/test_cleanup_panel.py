"""Unit tests for :class:`CleanupPanelView` (Phase 5).

Covers:

* The overview embed renders the prohibited-word count and
  whitelist-channel summary read-only.
* The view exposes Prohibited Words / Logging Status / Settings /
  Refresh buttons in the expected layout.
* The Prohibited Words button opens the existing ``_WordMenuView``
  in-place (no new view class is invented).
* The Logging Status button delegates to the logging cog's
  ``build_help_menu_view`` hook when available, and falls back to a
  defensive ephemeral when the cog is missing.
* The Settings button routes to ``SubsystemSettingsView("cleanup")``.
* The Refresh button rebuilds the embed without mutation.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from cogs.cleanup.panel import (
    CleanupPanelView,
    build_cleanup_overview_embed,
)


def _author(id_: int = 1) -> MagicMock:
    author = MagicMock(spec=discord.Member)
    author.id = id_
    return author


def _cog(words: list[str] | None = None, channels: list[int] | None = None) -> MagicMock:
    cog = MagicMock()
    cog._word_cache = {42: list(words or [])}
    cog._load_guild = AsyncMock()
    cog.whitelisted_channels = list(channels or [])
    return cog


# ---------------------------------------------------------------------------
# Overview embed
# ---------------------------------------------------------------------------


def test_overview_embed_shows_word_count():
    cog = _cog(words=["badword", "another"])
    embed = build_cleanup_overview_embed(cog, guild_id=42)
    word_field = next(f for f in embed.fields if "Words" in f.name)
    assert "2" in word_field.value


def test_overview_embed_shows_empty_word_list_gracefully():
    cog = _cog(words=[])
    embed = build_cleanup_overview_embed(cog, guild_id=42)
    word_field = next(f for f in embed.fields if "Words" in f.name)
    assert "None" in word_field.value


def test_overview_embed_lists_whitelist_channels():
    cog = _cog(words=[], channels=[111, 222])
    embed = build_cleanup_overview_embed(cog, guild_id=42)
    whitelist_field = next(f for f in embed.fields if "Whitelist" in f.name)
    assert "<#111>" in whitelist_field.value
    assert "<#222>" in whitelist_field.value


def test_overview_embed_when_guild_unloaded():
    cog = _cog(words=[])
    # guild_id=None mimics a DM context or a fresh guild not yet warmed.
    embed = build_cleanup_overview_embed(cog, guild_id=None)
    word_field = next(f for f in embed.fields if "Words" in f.name)
    assert "None" in word_field.value


# ---------------------------------------------------------------------------
# View shape
# ---------------------------------------------------------------------------


def test_view_has_four_buttons_with_expected_custom_ids():
    view = CleanupPanelView(_author(), _cog(), guild_id=42)
    custom_ids = {
        c.custom_id  # type: ignore[attr-defined]
        for c in view.children
        if isinstance(c, discord.ui.Button)
    }
    assert custom_ids == {
        "cleanup:words",
        "cleanup:logging",
        "cleanup:settings",
        "cleanup:refresh",
    }


def test_view_buttons_use_two_rows():
    view = CleanupPanelView(_author(), _cog(), guild_id=42)
    rows = {
        c.row  # type: ignore[attr-defined]
        for c in view.children
        if isinstance(c, discord.ui.Button)
    }
    # Three top-row routing buttons + the refresh button on a second row.
    assert rows == {0, 1}


# ---------------------------------------------------------------------------
# Routing buttons
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_words_button_renders_word_menu_view_in_place():
    cog = _cog(words=["badword"])
    view = CleanupPanelView(_author(), cog, guild_id=42)
    interaction = MagicMock(spec=discord.Interaction)
    interaction.client = MagicMock()
    interaction.user = view._author
    interaction.guild = MagicMock()
    interaction.channel = MagicMock()
    interaction.response = MagicMock()
    interaction.response.edit_message = AsyncMock()

    btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == "cleanup:words"
    )
    await btn.callback(interaction)  # type: ignore[union-attr,misc]

    interaction.response.edit_message.assert_awaited_once()
    _args, kwargs = interaction.response.edit_message.call_args
    # The new view must be the existing _WordMenuView, not a fresh
    # cleanup-specific re-implementation.
    from cogs.cleanup_cog import _WordMenuView

    assert isinstance(kwargs["view"], _WordMenuView)


@pytest.mark.asyncio
async def test_words_button_loads_guild_when_missing():
    cog = _cog(words=[])
    cog._word_cache = {}  # guild 42 not loaded
    view = CleanupPanelView(_author(), cog, guild_id=42)
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = view._author
    interaction.guild = MagicMock()
    interaction.channel = MagicMock()
    interaction.client = MagicMock()
    interaction.response = MagicMock()
    interaction.response.edit_message = AsyncMock()

    btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == "cleanup:words"
    )
    await btn.callback(interaction)  # type: ignore[union-attr,misc]

    cog._load_guild.assert_awaited_once_with(42)


@pytest.mark.asyncio
async def test_logging_button_routes_via_cog_build_hook():
    cog = _cog()
    view = CleanupPanelView(_author(), cog, guild_id=42)

    logging_cog = MagicMock()
    expected_embed = discord.Embed(title="Logging")
    expected_view = discord.ui.View()
    logging_cog.build_help_menu_view = AsyncMock(
        return_value=(expected_embed, expected_view),
    )

    interaction = MagicMock(spec=discord.Interaction)
    interaction.client = MagicMock()
    interaction.client.get_cog = MagicMock(return_value=logging_cog)
    interaction.response = MagicMock()
    interaction.response.edit_message = AsyncMock()
    interaction.response.send_message = AsyncMock()

    btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == "cleanup:logging"
    )
    await btn.callback(interaction)  # type: ignore[union-attr,misc]

    interaction.client.get_cog.assert_called_with("LoggingCog")
    logging_cog.build_help_menu_view.assert_awaited_once_with(interaction)
    interaction.response.edit_message.assert_awaited_once()
    _args, kwargs = interaction.response.edit_message.call_args
    assert kwargs["embed"] is expected_embed
    assert kwargs["view"] is expected_view


@pytest.mark.asyncio
async def test_logging_button_handles_missing_logging_cog():
    view = CleanupPanelView(_author(), _cog(), guild_id=42)
    interaction = MagicMock(spec=discord.Interaction)
    interaction.client = MagicMock()
    interaction.client.get_cog = MagicMock(return_value=None)
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()

    btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == "cleanup:logging"
    )
    await btn.callback(interaction)  # type: ignore[union-attr,misc]

    interaction.response.send_message.assert_awaited_once()
    interaction.response.edit_message.assert_not_called()


@pytest.mark.asyncio
async def test_settings_button_routes_to_subsystem_settings_view():
    view = CleanupPanelView(_author(), _cog(), guild_id=42)
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = view._author
    interaction.client = MagicMock()
    interaction.guild = MagicMock()
    interaction.channel = MagicMock()
    interaction.response = MagicMock()
    interaction.response.edit_message = AsyncMock()

    fake_embed = discord.Embed(title="Cleanup settings")
    with patch(
        "views.settings.subsystem_view.build_subsystem_embed",
        AsyncMock(return_value=fake_embed),
    ):
        btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button) and c.custom_id == "cleanup:settings"
        )
        await btn.callback(interaction)  # type: ignore[union-attr,misc]

    from views.settings.subsystem_view import SubsystemSettingsView

    interaction.response.edit_message.assert_awaited_once()
    _args, kwargs = interaction.response.edit_message.call_args
    assert kwargs["embed"] is fake_embed
    assert isinstance(kwargs["view"], SubsystemSettingsView)
    assert kwargs["view"].subsystem == "cleanup"


@pytest.mark.asyncio
async def test_refresh_button_rebuilds_embed_without_mutation():
    cog = _cog(words=["alpha"])
    view = CleanupPanelView(_author(), cog, guild_id=42)
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = view._author
    interaction.response = MagicMock()
    interaction.response.edit_message = AsyncMock()

    btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == "cleanup:refresh"
    )
    await btn.callback(interaction)  # type: ignore[union-attr,misc]

    cog._load_guild.assert_awaited_once_with(42)
    interaction.response.edit_message.assert_awaited_once()
    _args, kwargs = interaction.response.edit_message.call_args
    assert kwargs["view"] is view
    assert isinstance(kwargs["embed"], discord.Embed)
