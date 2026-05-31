"""Tests for the ChainStage migration (§3.2).

Stage wrapper contract + _process_chain_message routing through
moderation_service.auto_delete on rule violations.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cogs.chain_cog import (
    CHAIN_STAGE_NAME,
    CHAIN_STAGE_ORDER,
    ChainCog,
    ChainStage,
)
from core.runtime.message_pipeline import MessagePipelineContext


def _make_cog():
    bot = MagicMock()
    # Default: not a command — chain validation should proceed.
    fake_ctx = MagicMock()
    fake_ctx.valid = False
    bot.get_context = AsyncMock(return_value=fake_ctx)
    return ChainCog(bot=bot)


def _make_message(*, content="hello", channel_id=1, author_id=42, guild_id=99):
    msg = MagicMock()
    msg.content = content
    msg.id = 555
    msg.guild = MagicMock()
    msg.guild.id = guild_id
    msg.guild.name = "test-guild"
    msg.channel = MagicMock()
    msg.channel.id = channel_id
    msg.channel.send = AsyncMock()
    msg.author = MagicMock()
    msg.author.id = author_id
    msg.author.bot = False
    msg.author.mention = f"<@{author_id}>"
    return msg


class TestChainStageContract:
    def test_metadata(self):
        stage = ChainStage(_make_cog())
        assert stage.name == CHAIN_STAGE_NAME == "chain"
        assert stage.order == CHAIN_STAGE_ORDER == 20

    @pytest.mark.asyncio
    async def test_delete_short_circuits(self):
        cog = _make_cog()
        cog._process_chain_message = AsyncMock(return_value=True)
        stage = ChainStage(cog)
        ctx = MessagePipelineContext(bot=MagicMock(), message=MagicMock())
        result = await stage.process(ctx)
        assert result.deleted is True
        assert result.short_circuit is True

    @pytest.mark.asyncio
    async def test_no_delete_passes_through(self):
        cog = _make_cog()
        cog._process_chain_message = AsyncMock(return_value=False)
        stage = ChainStage(cog)
        ctx = MessagePipelineContext(bot=MagicMock(), message=MagicMock())
        result = await stage.process(ctx)
        assert result.deleted is False
        assert result.short_circuit is False


class TestProcessChainMessage:
    @pytest.mark.asyncio
    async def test_command_messages_pass_through(self):
        """ctx.valid → True means it's a command; chain rules don't apply."""
        cog = _make_cog()
        cog.bot.get_context.return_value = MagicMock(valid=True)
        msg = _make_message()

        with (
            patch(
                "cogs.chain_cog.db.get_chain_channel",
                new_callable=AsyncMock,
            ) as get_chain,
            patch(
                "cogs.chain_cog.moderation_service.auto_delete",
                new_callable=AsyncMock,
            ) as auto_delete,
        ):
            handled = await cog._process_chain_message(msg)

        assert handled is False
        get_chain.assert_not_awaited()
        auto_delete.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_unchained_channel_passes_through(self):
        cog = _make_cog()
        msg = _make_message()

        with (
            patch(
                "cogs.chain_cog.db.get_chain_channel",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch(
                "cogs.chain_cog.moderation_service.auto_delete",
                new_callable=AsyncMock,
            ) as auto_delete,
        ):
            handled = await cog._process_chain_message(msg)

        assert handled is False
        auto_delete.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_disallowed_word_routes_through_auto_delete(self):
        cog = _make_cog()
        msg = _make_message(content="bad")

        with (
            patch(
                "cogs.chain_cog.db.get_chain_channel",
                new_callable=AsyncMock,
                return_value={"word": "good", "word_limit": 0},
            ),
            patch(
                "cogs.chain_cog.moderation_service.auto_delete",
                new_callable=AsyncMock,
                return_value=True,
            ) as auto_delete,
        ):
            handled = await cog._process_chain_message(msg)

        assert handled is True
        auto_delete.assert_awaited_once()
        assert auto_delete.call_args.kwargs["rule"] == "chain.violation"
        assert "good" in auto_delete.call_args.kwargs["reason"]

    @pytest.mark.asyncio
    async def test_word_limit_exceeded_routes_through_auto_delete(self):
        cog = _make_cog()
        msg = _make_message(content="one two three four")

        with (
            patch(
                "cogs.chain_cog.db.get_chain_channel",
                new_callable=AsyncMock,
                return_value={"word": "", "word_limit": 2},
            ),
            patch(
                "cogs.chain_cog.moderation_service.auto_delete",
                new_callable=AsyncMock,
                return_value=True,
            ) as auto_delete,
        ):
            handled = await cog._process_chain_message(msg)

        assert handled is True
        auto_delete.assert_awaited_once()
        assert auto_delete.call_args.kwargs["rule"] == "chain.violation"
        assert "2 words" in auto_delete.call_args.kwargs["reason"]

    @pytest.mark.asyncio
    async def test_allowed_word_match_increments_count(self):
        cog = _make_cog()
        msg = _make_message(content="good")

        with (
            patch(
                "cogs.chain_cog.db.get_chain_channel",
                new_callable=AsyncMock,
                return_value={"word": "good", "word_limit": 0},
            ),
            patch(
                "cogs.chain_cog.db.increment_chain_count",
                new_callable=AsyncMock,
            ) as inc,
            patch(
                "cogs.chain_cog.moderation_service.auto_delete",
                new_callable=AsyncMock,
            ) as auto_delete,
        ):
            handled = await cog._process_chain_message(msg)

        assert handled is False
        inc.assert_awaited_once_with(msg.channel.id)
        auto_delete.assert_not_awaited()
