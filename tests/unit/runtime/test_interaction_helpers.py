"""Regression tests for core.runtime.interaction_helpers.

Covers CRIT-2 (interaction handlers without defer) from the
platform-hardening plan.  Verifies:

- safe_defer is idempotent when response.is_done()
- safe_defer swallows NotFound (token expired) returning False
- safe_followup uses followup.send when response is done
- safe_followup uses response.send_message + original_response when not done
- safe_edit uses response.edit_message when not done
- safe_edit uses followup.edit_message when deferred
- all three helpers swallow recoverable exceptions and return falsy
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from core.runtime import interaction_helpers as ih


def _make_interaction(*, responded: bool = False) -> MagicMock:
    interaction = MagicMock()
    interaction.user = MagicMock()
    interaction.user.id = 12345
    interaction.response = MagicMock()
    interaction.response.is_done = MagicMock(return_value=responded)
    interaction.response.defer = AsyncMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock(return_value=MagicMock(spec=discord.Message))
    interaction.followup.edit_message = AsyncMock()
    interaction.original_response = AsyncMock(return_value=MagicMock(spec=discord.Message))
    interaction.message = MagicMock()
    interaction.message.id = 99999
    return interaction


class TestSafeDefer:
    @pytest.mark.asyncio
    async def test_defers_when_not_responded(self):
        i = _make_interaction(responded=False)
        ok = await ih.safe_defer(i)
        assert ok is True
        i.response.defer.assert_awaited_once_with(ephemeral=False, thinking=False)

    @pytest.mark.asyncio
    async def test_noop_when_already_responded(self):
        i = _make_interaction(responded=True)
        ok = await ih.safe_defer(i)
        assert ok is True
        i.response.defer.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_swallows_token_expired_returns_false(self):
        i = _make_interaction(responded=False)
        i.response.defer.side_effect = discord.NotFound(MagicMock(), "expired")
        ok = await ih.safe_defer(i)
        assert ok is False

    @pytest.mark.asyncio
    async def test_passes_ephemeral_and_thinking(self):
        i = _make_interaction(responded=False)
        await ih.safe_defer(i, ephemeral=True, thinking=True)
        i.response.defer.assert_awaited_once_with(ephemeral=True, thinking=True)


class TestSafeFollowup:
    @pytest.mark.asyncio
    async def test_uses_followup_when_responded(self):
        i = _make_interaction(responded=True)
        msg = await ih.safe_followup(i, content="hi")
        assert msg is not None
        i.followup.send.assert_awaited_once()
        i.response.send_message.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_uses_send_message_when_not_responded(self):
        i = _make_interaction(responded=False)
        msg = await ih.safe_followup(i, content="hi")
        i.response.send_message.assert_awaited_once()
        i.followup.send.assert_not_awaited()
        i.original_response.assert_awaited_once()
        assert msg is not None

    @pytest.mark.asyncio
    async def test_returns_none_on_token_expired(self):
        i = _make_interaction(responded=True)
        i.followup.send.side_effect = discord.NotFound(MagicMock(), "expired")
        msg = await ih.safe_followup(i, content="hi")
        assert msg is None

    @pytest.mark.asyncio
    async def test_passes_embed_view_ephemeral(self):
        i = _make_interaction(responded=True)
        embed = MagicMock()
        view = MagicMock()
        await ih.safe_followup(i, content="x", embed=embed, view=view, ephemeral=True)
        call_kwargs = i.followup.send.call_args.kwargs
        assert call_kwargs.get("content") == "x"
        assert call_kwargs.get("embed") is embed
        assert call_kwargs.get("view") is view
        assert call_kwargs.get("ephemeral") is True


class TestSafeEdit:
    @pytest.mark.asyncio
    async def test_uses_response_edit_when_not_responded(self):
        i = _make_interaction(responded=False)
        ok = await ih.safe_edit(i, content="updated")
        assert ok is True
        i.response.edit_message.assert_awaited_once()
        i.followup.edit_message.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_uses_followup_edit_when_deferred(self):
        i = _make_interaction(responded=True)
        ok = await ih.safe_edit(i, content="updated")
        assert ok is True
        i.followup.edit_message.assert_awaited_once()
        i.response.edit_message.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_swallows_not_found_returns_false(self):
        i = _make_interaction(responded=False)
        i.response.edit_message.side_effect = discord.NotFound(MagicMock(), "gone")
        ok = await ih.safe_edit(i, content="updated")
        assert ok is False
