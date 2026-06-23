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


def _channel(name: str) -> MagicMock:
    ch = MagicMock()
    ch.name = name
    return ch


def _cog(
    words: list[str] | None = None,
    channels: list[int] | None = None,
    guild_channels: dict[int, str] | None = None,
) -> MagicMock:
    """A fake Cleanup cog.

    ``channels`` is the *global* static whitelist (``CLEANUP_WHITELIST_CHANNELS``);
    ``guild_channels`` maps the ids that actually exist in guild 42 to their name,
    so the panel can resolve + filter to the current server.
    """
    cog = MagicMock()
    cog._word_cache = {42: list(words or [])}
    cog._load_guild = AsyncMock()
    cog.whitelisted_channels = list(channels or [])

    resolved = {cid: _channel(name) for cid, name in (guild_channels or {}).items()}
    guild = MagicMock()
    guild.get_channel = lambda cid: resolved.get(cid)
    cog.bot = MagicMock()
    cog.bot.get_guild = lambda gid: guild if gid == 42 else None
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


def test_overview_embed_lists_whitelist_channels_by_name():
    cog = _cog(
        words=[],
        channels=[111, 222],
        guild_channels={111: "general", 222: "memes"},
    )
    embed = build_cleanup_overview_embed(cog, guild_id=42)
    whitelist_field = next(f for f in embed.fields if "Whitelist" in f.name)
    # Channel names, not raw ids / mentions.
    assert "#general" in whitelist_field.value
    assert "#memes" in whitelist_field.value
    assert "<#" not in whitelist_field.value


def test_overview_embed_filters_whitelist_to_current_guild():
    # 111 is in this guild; 999 belongs to another server → must be omitted.
    cog = _cog(words=[], channels=[111, 999], guild_channels={111: "general"})
    embed = build_cleanup_overview_embed(cog, guild_id=42)
    whitelist_field = next(f for f in embed.fields if "Whitelist" in f.name)
    assert "#general" in whitelist_field.value
    assert "999" not in whitelist_field.value


def test_overview_embed_whitelist_none_in_this_server():
    # The whitelist has ids, but none resolve in this guild.
    cog = _cog(words=[], channels=[111, 222], guild_channels={})
    embed = build_cleanup_overview_embed(cog, guild_id=42)
    whitelist_field = next(f for f in embed.fields if "Whitelist" in f.name)
    assert "None in this server" in whitelist_field.value


def test_overview_embed_when_guild_unloaded():
    cog = _cog(words=[])
    # guild_id=None mimics a DM context or a fresh guild not yet warmed.
    embed = build_cleanup_overview_embed(cog, guild_id=None)
    word_field = next(f for f in embed.fields if "Words" in f.name)
    assert "None" in word_field.value


# ---------------------------------------------------------------------------
# View shape
# ---------------------------------------------------------------------------


def test_view_has_expected_button_custom_ids():
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
        "cleanup:policies",
        "cleanup:refresh",
    }


def test_view_buttons_use_two_rows():
    view = CleanupPanelView(_author(), _cog(), guild_id=42)
    rows = {
        c.row  # type: ignore[attr-defined]
        for c in view.children
        if isinstance(c, discord.ui.Button)
    }
    # Top-row routing buttons + the refresh button on a second row.
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
async def test_policies_button_opens_policy_panel_with_diagnostics():
    cog = _cog()
    view = CleanupPanelView(_author(), cog, guild_id=42)
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = view._author
    interaction.client = MagicMock()
    interaction.guild = MagicMock()
    interaction.guild.id = 42
    interaction.response = MagicMock()
    interaction.response.edit_message = AsyncMock()
    interaction.response.send_message = AsyncMock()

    fake_embed = discord.Embed(title="Cleanup Policies — Diagnostics")
    with patch(
        "views.cleanup.policy_panel.build_cleanup_diagnostics_embed",
        AsyncMock(return_value=fake_embed),
    ):
        btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button) and c.custom_id == "cleanup:policies"
        )
        await btn.callback(interaction)  # type: ignore[union-attr,misc]

    from views.cleanup.policy_panel import CleanupPolicyPanelView

    interaction.response.edit_message.assert_awaited_once()
    _args, kwargs = interaction.response.edit_message.call_args
    assert isinstance(kwargs["view"], CleanupPolicyPanelView)
    assert kwargs["embed"] is fake_embed
    back = _back_button(kwargs["view"])
    assert back is not None, "Policy panel must have a cleanup:back button"


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


# ---------------------------------------------------------------------------
# Back-to-Cleanup attachment on every routed sub-view (PR AB1)
# ---------------------------------------------------------------------------


def _back_button(view: discord.ui.View) -> discord.ui.Button | None:
    for child in view.children:
        if isinstance(child, discord.ui.Button) and child.custom_id == "cleanup:back":
            return child
    return None


@pytest.mark.asyncio
async def test_words_button_attaches_back_to_cleanup_on_child():
    """Prohibited Words view must carry a Back-to-Cleanup button so the
    user is not trapped — issue #1 of the post-#152 stabilization sweep.
    """
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

    _args, kwargs = interaction.response.edit_message.call_args
    child_view = kwargs["view"]
    back = _back_button(child_view)
    assert back is not None, "Words view must have a cleanup:back button"
    assert back.label == "↩ Back to Cleanup"


@pytest.mark.asyncio
async def test_logging_button_attaches_back_to_cleanup_on_child():
    cog = _cog()
    view = CleanupPanelView(_author(), cog, guild_id=42)

    logging_cog = MagicMock()
    returned_view = discord.ui.View()
    logging_cog.build_help_menu_view = AsyncMock(
        return_value=(discord.Embed(title="Logging"), returned_view),
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

    back = _back_button(returned_view)
    assert back is not None, "Logging view must have a cleanup:back button"
    assert back.label == "↩ Back to Cleanup"


@pytest.mark.asyncio
async def test_logging_button_failure_path_includes_exception_class_name():
    """If the logging cog's build hook raises, the ephemeral should name
    the exception class so operators can triage from the user's report.
    """
    cog = _cog()
    view = CleanupPanelView(_author(), cog, guild_id=42)

    logging_cog = MagicMock()
    logging_cog.build_help_menu_view = AsyncMock(
        side_effect=RuntimeError("boom"),
    )

    interaction = MagicMock(spec=discord.Interaction)
    interaction.client = MagicMock()
    interaction.client.get_cog = MagicMock(return_value=logging_cog)
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
    args, kwargs = interaction.response.send_message.call_args
    message = args[0] if args else kwargs.get("content", "")
    assert "RuntimeError" in message
    assert kwargs.get("ephemeral") is True
    interaction.response.edit_message.assert_not_called()


@pytest.mark.asyncio
async def test_settings_button_attaches_back_to_cleanup_on_child():
    view = CleanupPanelView(_author(), _cog(), guild_id=42)
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = view._author
    interaction.client = MagicMock()
    interaction.guild = MagicMock()
    interaction.channel = MagicMock()
    interaction.response = MagicMock()
    interaction.response.edit_message = AsyncMock()

    with patch(
        "views.settings.subsystem_view.build_subsystem_embed",
        AsyncMock(return_value=discord.Embed(title="Cleanup settings")),
    ):
        btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button) and c.custom_id == "cleanup:settings"
        )
        await btn.callback(interaction)  # type: ignore[union-attr,misc]

    _args, kwargs = interaction.response.edit_message.call_args
    child_view = kwargs["view"]
    back = _back_button(child_view)
    assert back is not None, "Settings view must have a cleanup:back button"
    assert back.label == "↩ Back to Cleanup"


@pytest.mark.asyncio
async def test_back_button_returns_to_same_cleanup_panel_instance():
    """The back button's parent_builder must return the SAME live
    CleanupPanelView instance (identity), not a fresh rebuild. This is
    how AB1 preserves any back-to-Help / back-to-Admin attached by the
    opener — a rebuild would lose those.
    """
    cog = _cog(words=["badword"])
    view = CleanupPanelView(_author(), cog, guild_id=42)

    # Mimic an opener attaching its own back button (e.g. back-to-Help)
    # on the live CleanupPanelView before any subroute is opened.
    synthetic_origin_btn = discord.ui.Button(
        label="↩ Back to Help",
        custom_id="help:back",
        style=discord.ButtonStyle.secondary,
        row=4,
    )
    view.add_item(synthetic_origin_btn)

    interaction = MagicMock(spec=discord.Interaction)
    interaction.client = MagicMock()
    interaction.user = view._author
    interaction.guild = MagicMock()
    interaction.channel = MagicMock()
    interaction.response = MagicMock()
    interaction.response.edit_message = AsyncMock()
    interaction.response.is_done = MagicMock(return_value=False)

    btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == "cleanup:words"
    )
    await btn.callback(interaction)  # type: ignore[union-attr,misc]

    _args, kwargs = interaction.response.edit_message.call_args
    child_view = kwargs["view"]
    back = _back_button(child_view)
    assert back is not None

    # Invoke the back button's callback directly and verify it edits
    # the message with the original CleanupPanelView instance — the one
    # that still carries the synthetic back-to-Help button.
    next_interaction = MagicMock(spec=discord.Interaction)
    next_interaction.client = MagicMock()
    next_interaction.response = MagicMock()
    next_interaction.response.is_done = MagicMock(return_value=False)
    next_interaction.response.defer = AsyncMock()
    next_interaction.response.edit_message = AsyncMock()
    next_interaction.response.send_message = AsyncMock()
    next_interaction.edit_original_response = AsyncMock()

    await back.callback(next_interaction)  # type: ignore[union-attr,misc]

    next_interaction.response.edit_message.assert_awaited_once()
    _args, edit_kwargs = next_interaction.response.edit_message.call_args
    assert (
        edit_kwargs["view"] is view
    ), "Back button must return the live CleanupPanelView instance"
    # The synthetic origin button (e.g. back-to-Help) must still be on
    # the returned view — that's the whole point of preserving identity.
    assert synthetic_origin_btn in view.children
