"""Unit tests for the interactive cog manager (PR C).

Pins:

* The "📋 Cog List" button opens a :class:`_CogManagerView` instead of
  the previous read-only embed.
* The view exposes Select + Load / Unload / Reload / Refresh +
  back-to-admin (the back button is added by ``coglist_btn`` via
  ``attach_back_to_admin_button``).
* Owner check: non-owners trigger an ephemeral "Owner only." denial
  on mutation buttons and ``bot.{load,unload,reload}_extension`` is
  NOT called.
* Critical-cog protection: panel Unload on a member of
  ``_PROTECTED_COGS`` refuses with an ephemeral citing the prefix
  escape hatch; ``bot.unload_extension`` is NOT called. Reload of a
  protected cog IS allowed.
* The prefix ``!cog`` command remains unprotected (it is the
  escape hatch).
* Load / Unload / Reload paths share their bodies with the prefix
  command via :func:`_do_load` / :func:`_do_unload` / :func:`_do_reload`.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from cogs.admin.cog_manager import (
    _CogManagerView,
    _PROTECTED_COGS,
    _do_load,
    _do_reload,
    _do_unload,
)
from cogs.admin_cog import AdminCog, _AdminPanelView


def _author(id_: int = 1) -> MagicMock:
    author = MagicMock(spec=discord.Member)
    author.id = id_
    return author


def _admin_cog(extensions: dict[str, object] | None = None) -> AdminCog:
    bot = MagicMock()
    bot.extensions = extensions or {"cogs.admin_cog": object()}
    bot.load_extension = AsyncMock()
    bot.unload_extension = AsyncMock()
    bot.reload_extension = AsyncMock()
    return AdminCog(bot=bot)


# ---------------------------------------------------------------------------
# _AdminPanelView.coglist_btn opens the interactive manager
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_coglist_button_opens_cog_manager_view():
    cog = _admin_cog()
    ctx = MagicMock()
    ctx.author = _author()
    panel = _AdminPanelView(ctx, cog)

    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = panel._author
    interaction.client = MagicMock()
    interaction.response = MagicMock()
    interaction.response.edit_message = AsyncMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.is_done = MagicMock(return_value=False)

    btn = next(
        c
        for c in panel.children
        if isinstance(c, discord.ui.Button)
        and "Cog List" in (c.label or "")
    )
    await btn.callback(interaction)  # type: ignore[union-attr,misc]

    interaction.response.edit_message.assert_awaited_once()
    _args, kwargs = interaction.response.edit_message.call_args
    assert isinstance(kwargs["view"], _CogManagerView)


# ---------------------------------------------------------------------------
# View shape — Select + 4 action buttons
# ---------------------------------------------------------------------------


def test_cog_manager_view_has_select_and_four_buttons():
    view = _CogManagerView(_admin_cog(), _author())
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    assert len(selects) == 1
    assert {b.label for b in buttons} == {"Load", "Unload", "Reload", "🔄 Refresh"}


def test_cog_manager_view_select_options_label_loaded_state():
    cog = _admin_cog(extensions={"cogs.admin_cog": object()})
    view = _CogManagerView(cog, _author())
    select = next(c for c in view.children if isinstance(c, discord.ui.Select))
    # Every option's label encodes the load state (✅ or ❌).
    for opt in select.options:
        assert "✅" in opt.label or "❌" in opt.label


def test_cog_manager_view_protected_options_carry_shield_glyph():
    view = _CogManagerView(_admin_cog(), _author())
    select = next(c for c in view.children if isinstance(c, discord.ui.Select))
    for opt in select.options:
        if opt.value in _PROTECTED_COGS:
            assert "🛡" in opt.label
            assert opt.description and "Protected" in opt.description


# ---------------------------------------------------------------------------
# Owner gate — non-owner mutation buttons deny
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_non_owner_load_button_denies_and_does_not_load():
    cog = _admin_cog()
    view = _CogManagerView(cog, _author())
    view.selected_module = "cogs.general_cog"

    interaction = MagicMock(spec=discord.Interaction)
    interaction.client = MagicMock()
    interaction.client.is_owner = AsyncMock(return_value=False)
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()

    load_btn = next(
        c for c in view.children if isinstance(c, discord.ui.Button) and c.label == "Load"
    )
    await load_btn.callback(interaction)  # type: ignore[union-attr,misc]

    interaction.response.send_message.assert_awaited_once()
    args, kwargs = interaction.response.send_message.call_args
    assert "Owner only" in (args[0] if args else kwargs.get("content", ""))
    assert kwargs.get("ephemeral") is True
    cog.bot.load_extension.assert_not_called()


@pytest.mark.asyncio
async def test_non_owner_unload_button_denies_and_does_not_unload():
    cog = _admin_cog()
    view = _CogManagerView(cog, _author())
    view.selected_module = "cogs.general_cog"

    interaction = MagicMock(spec=discord.Interaction)
    interaction.client = MagicMock()
    interaction.client.is_owner = AsyncMock(return_value=False)
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()

    unload_btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.label == "Unload"
    )
    await unload_btn.callback(interaction)  # type: ignore[union-attr,misc]

    interaction.response.send_message.assert_awaited_once()
    cog.bot.unload_extension.assert_not_called()


@pytest.mark.asyncio
async def test_non_owner_reload_button_denies_and_does_not_reload():
    cog = _admin_cog()
    view = _CogManagerView(cog, _author())
    view.selected_module = "cogs.general_cog"

    interaction = MagicMock(spec=discord.Interaction)
    interaction.client = MagicMock()
    interaction.client.is_owner = AsyncMock(return_value=False)
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()

    reload_btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.label == "Reload"
    )
    await reload_btn.callback(interaction)  # type: ignore[union-attr,misc]

    interaction.response.send_message.assert_awaited_once()
    cog.bot.reload_extension.assert_not_called()


# ---------------------------------------------------------------------------
# Owner mutation paths
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_owner_load_button_calls_bot_load_extension():
    cog = _admin_cog()
    view = _CogManagerView(cog, _author())
    view.selected_module = "cogs.general_cog"

    interaction = MagicMock(spec=discord.Interaction)
    interaction.client = MagicMock()
    interaction.client.is_owner = AsyncMock(return_value=True)
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()

    load_btn = next(
        c for c in view.children if isinstance(c, discord.ui.Button) and c.label == "Load"
    )
    await load_btn.callback(interaction)  # type: ignore[union-attr,misc]

    cog.bot.load_extension.assert_awaited_once_with("cogs.general_cog")
    interaction.response.edit_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_owner_unload_button_calls_bot_unload_extension():
    cog = _admin_cog(extensions={"cogs.general_cog": object()})
    view = _CogManagerView(cog, _author())
    view.selected_module = "cogs.general_cog"

    interaction = MagicMock(spec=discord.Interaction)
    interaction.client = MagicMock()
    interaction.client.is_owner = AsyncMock(return_value=True)
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()

    unload_btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.label == "Unload"
    )
    await unload_btn.callback(interaction)  # type: ignore[union-attr,misc]

    cog.bot.unload_extension.assert_awaited_once_with("cogs.general_cog")


@pytest.mark.asyncio
async def test_owner_reload_button_calls_bot_reload_extension():
    cog = _admin_cog(extensions={"cogs.general_cog": object()})
    view = _CogManagerView(cog, _author())
    view.selected_module = "cogs.general_cog"

    interaction = MagicMock(spec=discord.Interaction)
    interaction.client = MagicMock()
    interaction.client.is_owner = AsyncMock(return_value=True)
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()

    reload_btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.label == "Reload"
    )
    await reload_btn.callback(interaction)  # type: ignore[union-attr,misc]

    cog.bot.reload_extension.assert_awaited_once_with("cogs.general_cog")


@pytest.mark.asyncio
async def test_owner_load_button_with_no_selection_asks_to_pick_first():
    cog = _admin_cog()
    view = _CogManagerView(cog, _author())
    # No selected_module set.

    interaction = MagicMock(spec=discord.Interaction)
    interaction.client = MagicMock()
    interaction.client.is_owner = AsyncMock(return_value=True)
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()

    load_btn = next(
        c for c in view.children if isinstance(c, discord.ui.Button) and c.label == "Load"
    )
    await load_btn.callback(interaction)  # type: ignore[union-attr,misc]

    interaction.response.send_message.assert_awaited_once()
    args, kwargs = interaction.response.send_message.call_args
    assert "Pick a cog" in (args[0] if args else kwargs.get("content", ""))
    cog.bot.load_extension.assert_not_called()


# ---------------------------------------------------------------------------
# Critical-cog protection
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_owner_panel_unload_of_protected_cog_is_refused():
    cog = _admin_cog(extensions={"cogs.admin_cog": object()})
    view = _CogManagerView(cog, _author())
    # admin_cog is in _PROTECTED_COGS by design.
    view.selected_module = "cogs.admin_cog"

    interaction = MagicMock(spec=discord.Interaction)
    interaction.client = MagicMock()
    interaction.client.is_owner = AsyncMock(return_value=True)
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()

    unload_btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.label == "Unload"
    )
    await unload_btn.callback(interaction)  # type: ignore[union-attr,misc]

    interaction.response.send_message.assert_awaited_once()
    args, kwargs = interaction.response.send_message.call_args
    msg = args[0] if args else kwargs.get("content", "")
    assert "protected core cog" in msg
    assert "!cog unload" in msg  # escape-hatch reference
    assert kwargs.get("ephemeral") is True
    # The protected cog must NOT have been touched.
    cog.bot.unload_extension.assert_not_called()


@pytest.mark.asyncio
async def test_owner_panel_reload_of_protected_cog_is_allowed():
    """Reload is reversible — protected cogs may still be reloaded
    from the panel, since reload doesn't risk losing the cog.
    """
    cog = _admin_cog(extensions={"cogs.admin_cog": object()})
    view = _CogManagerView(cog, _author())
    view.selected_module = "cogs.admin_cog"

    interaction = MagicMock(spec=discord.Interaction)
    interaction.client = MagicMock()
    interaction.client.is_owner = AsyncMock(return_value=True)
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()

    reload_btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.label == "Reload"
    )
    await reload_btn.callback(interaction)  # type: ignore[union-attr,misc]

    cog.bot.reload_extension.assert_awaited_once_with("cogs.admin_cog")


# ---------------------------------------------------------------------------
# Prefix `!cog` retains no protection (escape hatch)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_prefix_cog_unload_of_protected_cog_is_not_blocked():
    """``!cog unload admin`` is the operator's escape hatch when the
    panel won't open. The prefix command intentionally has no
    protected-cog check — only the panel does. Pin that.
    """
    cog = _admin_cog(extensions={"cogs.admin_cog": object()})
    ctx = MagicMock()
    ctx.send = AsyncMock()

    await cog.manage_cog.callback(cog, ctx, "unload", "admin")

    # The prefix command DID call the underlying unload (regardless
    # of whether ``cogs.admin_cog`` is protected).
    cog.bot.unload_extension.assert_awaited_once_with("cogs.admin_cog")


# ---------------------------------------------------------------------------
# Helper bodies are shared between prefix command and panel
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_do_load_calls_bot_load_extension():
    bot = MagicMock()
    bot.load_extension = AsyncMock()
    status = await _do_load(bot, "cogs.general_cog")
    bot.load_extension.assert_awaited_once_with("cogs.general_cog")
    assert "loaded" in status


@pytest.mark.asyncio
async def test_do_load_returns_error_on_exception():
    bot = MagicMock()
    bot.load_extension = AsyncMock(side_effect=RuntimeError("boom"))
    status = await _do_load(bot, "cogs.general_cog")
    assert "Error loading" in status
    assert "boom" in status


@pytest.mark.asyncio
async def test_do_unload_calls_bot_unload_extension():
    bot = MagicMock()
    bot.unload_extension = AsyncMock()
    status = await _do_unload(bot, "cogs.general_cog")
    bot.unload_extension.assert_awaited_once_with("cogs.general_cog")
    assert "unloaded" in status


@pytest.mark.asyncio
async def test_do_reload_calls_bot_reload_extension():
    bot = MagicMock()
    bot.reload_extension = AsyncMock()
    status = await _do_reload(bot, "cogs.general_cog")
    bot.reload_extension.assert_awaited_once_with("cogs.general_cog")
    assert "reloaded" in status
