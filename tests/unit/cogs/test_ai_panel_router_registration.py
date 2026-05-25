"""Tests for the AI interaction-router handler registered by ``AICog`` (PR1).

Before PR1, button clicks on the AI panel produced a WARNING
("Unhandled interaction prefix 'ai'") on every process restart because
no cog claimed the ``ai`` prefix. PR1 adds an idempotent registration
in ``AICog.cog_load`` and a thin ``handle_ai_interaction`` dispatcher
in ``views.ai.panel`` that bails when the PersistentView has already
handled the interaction.
"""

from __future__ import annotations

import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from cogs.ai_cog import AICog
from core.runtime import interaction_router
from views.ai.panel import (
    AI_ROUTER_PREFIX,
    handle_ai_interaction,
)


@pytest.fixture(autouse=True)
def _clear_router_handler():
    """Each test starts with a clean ``ai`` prefix in the router."""
    interaction_router._handlers.pop(AI_ROUTER_PREFIX, None)
    yield
    interaction_router._handlers.pop(AI_ROUTER_PREFIX, None)


def _make_interaction(*, admin: bool, is_done: bool = False) -> MagicMock:
    """Build a minimal discord.Interaction stub for handler tests."""
    interaction = MagicMock(spec=discord.Interaction)
    interaction.guild_id = 1
    interaction.user = MagicMock()
    interaction.user.guild_permissions = SimpleNamespace(administrator=admin)
    interaction.response = MagicMock()
    interaction.response.is_done = MagicMock(return_value=is_done)
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    return interaction


# ---------------------------------------------------------------------------
# Registration lifecycle
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ai_prefix_registered_after_cog_load():
    bot = MagicMock()
    cog = AICog(bot)
    # cog_load also touches message_pipeline; that path is fine to exercise
    # against the real registry — it dedupes by name.
    await cog.cog_load()
    assert interaction_router._handlers.get(AI_ROUTER_PREFIX) is handle_ai_interaction


@pytest.mark.asyncio
async def test_ai_prefix_registration_is_idempotent_on_repeated_cog_load(caplog):
    """Reloading the cog must not produce an overwrite WARNING."""
    bot = MagicMock()
    cog = AICog(bot)
    await cog.cog_load()
    caplog.set_level(logging.WARNING, logger="bot.runtime.router")
    caplog.set_level(logging.WARNING, logger="bot")
    caplog.clear()
    await cog.cog_load()
    # Handler must remain handle_ai_interaction.
    assert interaction_router._handlers.get(AI_ROUTER_PREFIX) is handle_ai_interaction
    # No overwrite-related WARNING should have fired on the second load.
    assert not any(
        "Overwriting existing handler" in r.message
        or "replacing unexpected handler" in r.message
        for r in caplog.records
    )


@pytest.mark.asyncio
async def test_ai_prefix_registration_replaces_foreign_handler(caplog):
    """A handler set by some other path is replaced with a WARNING."""

    async def foreign(*_args, **_kwargs):
        return None

    interaction_router._handlers[AI_ROUTER_PREFIX] = foreign
    bot = MagicMock()
    cog = AICog(bot)
    caplog.set_level(logging.WARNING)
    await cog.cog_load()
    assert interaction_router._handlers.get(AI_ROUTER_PREFIX) is handle_ai_interaction
    assert any("replacing unexpected handler" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# handle_ai_interaction behaviour
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_handler_returns_early_when_response_is_done():
    """If the PersistentView already handled it, the router bails."""
    interaction = _make_interaction(admin=True, is_done=True)
    await handle_ai_interaction(interaction, "diagnostics", None, "req-1")
    # No send / edit happened.
    interaction.response.send_message.assert_not_called()
    interaction.response.edit_message.assert_not_called()


@pytest.mark.asyncio
async def test_handler_admin_only_gate():
    """Non-admins see an ephemeral denial — no edit_message."""
    interaction = _make_interaction(admin=False, is_done=False)
    await handle_ai_interaction(interaction, "diagnostics", None, "req-1")
    interaction.response.send_message.assert_awaited_once()
    args, kwargs = interaction.response.send_message.call_args
    assert kwargs.get("ephemeral") is True
    interaction.response.edit_message.assert_not_called()


@pytest.mark.asyncio
async def test_handler_dispatches_diagnostics_action():
    """Admin + sync action: edit_message with an Embed."""
    interaction = _make_interaction(admin=True, is_done=False)
    await handle_ai_interaction(interaction, "diagnostics", None, "req-1")
    interaction.response.edit_message.assert_awaited_once()
    args, kwargs = interaction.response.edit_message.call_args
    embed = kwargs["embed"]
    assert isinstance(embed, discord.Embed)
    assert "Diagnostics" in (embed.title or "")


@pytest.mark.asyncio
async def test_handler_dispatches_refresh_action():
    interaction = _make_interaction(admin=True, is_done=False)
    await handle_ai_interaction(interaction, "refresh", None, "req-1")
    interaction.response.edit_message.assert_awaited_once()
    embed = interaction.response.edit_message.call_args.kwargs["embed"]
    assert "AI Platform" in (embed.title or "")


@pytest.mark.asyncio
async def test_handler_dispatches_providers_and_routing():
    for action, expected_in_title in (
        ("providers", "Providers"),
        ("routing", "Routing"),
    ):
        interaction = _make_interaction(admin=True, is_done=False)
        await handle_ai_interaction(interaction, action, None, "req-1")
        interaction.response.edit_message.assert_awaited_once()
        embed = interaction.response.edit_message.call_args.kwargs["embed"]
        assert expected_in_title in (embed.title or "")


@pytest.mark.asyncio
async def test_handler_settings_action_uses_async_builder():
    """The "settings" branch must await _build_ai_settings_panel."""
    interaction = _make_interaction(admin=True, is_done=False)
    fake_embed = discord.Embed(title="AI Settings")
    fake_view = MagicMock()
    with patch(
        "cogs.ai_cog._build_ai_settings_panel",
        new_callable=AsyncMock,
        return_value=(fake_embed, fake_view),
    ) as builder:
        await handle_ai_interaction(interaction, "settings", None, "req-1")
    builder.assert_awaited_once_with(interaction.user, interaction.guild_id)
    interaction.response.edit_message.assert_awaited_once_with(
        embed=fake_embed,
        view=fake_view,
    )


@pytest.mark.asyncio
async def test_handler_unknown_action_replies_gracefully():
    """An unrecognised action returns an ephemeral error, not a crash."""
    interaction = _make_interaction(admin=True, is_done=False)
    await handle_ai_interaction(interaction, "explode", None, "req-1")
    interaction.response.send_message.assert_awaited_once()
    args, kwargs = interaction.response.send_message.call_args
    assert kwargs.get("ephemeral") is True
    assert "Unknown" in args[0] or "Unknown" in kwargs.get("content", "")
    interaction.response.edit_message.assert_not_called()
