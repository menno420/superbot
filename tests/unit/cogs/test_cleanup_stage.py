"""Tests for the CleanupStage migration (§3.2).

Covers the stage wrapper contract:
  - delete returns short-circuit + deleted flags
  - no-delete returns empty result
  - underlying remove_unwanted_message routes through moderation_service.auto_delete
    for the three rule paths (command policy, whitelist fallback, prohibited words)
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cogs.cleanup_cog import (
    CLEANUP_STAGE_NAME,
    CLEANUP_STAGE_ORDER,
    Cleanup,
    CleanupStage,
)
from core.runtime.message_pipeline import MessagePipelineContext


def _make_cog():
    """Construct a Cleanup cog with isolated caches and a stub command pattern."""
    cog = Cleanup(bot=MagicMock())
    # Fresh per-test caches — avoid cross-test bleed.
    cog._word_cache = {}
    cog._pattern_cache = {}
    return cog


def _make_message(
    *, content: str, guild_id: int = 99, channel_id: int = 1, author_id: int = 42
):
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


class TestStageContract:
    def test_metadata(self):
        cog = _make_cog()
        stage = CleanupStage(cog)
        assert stage.name == CLEANUP_STAGE_NAME == "cleanup"
        assert stage.order == CLEANUP_STAGE_ORDER == 10

    @pytest.mark.asyncio
    async def test_delete_short_circuits(self):
        cog = _make_cog()
        cog.remove_unwanted_message = AsyncMock(return_value=True)
        stage = CleanupStage(cog)
        ctx = MessagePipelineContext(bot=MagicMock(), message=MagicMock())
        result = await stage.process(ctx)
        assert result.deleted is True
        assert result.short_circuit is True
        assert result.moderation_action is None

    @pytest.mark.asyncio
    async def test_no_delete_passes_through(self):
        cog = _make_cog()
        cog.remove_unwanted_message = AsyncMock(return_value=False)
        stage = CleanupStage(cog)
        ctx = MessagePipelineContext(bot=MagicMock(), message=MagicMock())
        result = await stage.process(ctx)
        assert result.deleted is False
        assert result.short_circuit is False


class TestRemoveUnwantedMessageRoutesToModerationService:
    @pytest.mark.asyncio
    async def test_prohibited_word_routes_through_auto_delete(self):
        cog = _make_cog()
        import re

        cog._pattern_cache[99] = [re.compile(r"\bbadword\b", re.IGNORECASE)]
        msg = _make_message(content="this has a badword in it")

        with patch(
            "cogs.cleanup_cog.moderation_service.auto_delete",
            new_callable=AsyncMock,
        ) as auto_delete:
            handled = await cog.remove_unwanted_message(msg)

        assert handled is True
        auto_delete.assert_awaited_once()
        assert auto_delete.call_args.args == (msg,)
        assert auto_delete.call_args.kwargs["rule"] == "cleanup.prohibited_words"

    @pytest.mark.asyncio
    async def test_blocked_command_routes_through_auto_delete(self):
        cog = _make_cog()
        msg = _make_message(content="!banned_cmd")

        # Stub governance to disallow the command and request a delete.
        fake_policy = SimpleNamespace(
            allowed=False,
            feedback="",
            cleanup=SimpleNamespace(
                delete_message=True,
                delete_after_seconds=5,
            ),
        )

        with (
            patch(
                "cogs.cleanup_cog.governance_service.resolve_command_policy",
                new_callable=AsyncMock,
                return_value=fake_policy,
            ),
            patch(
                "cogs.cleanup_cog.moderation_service.auto_delete",
                new_callable=AsyncMock,
            ) as auto_delete,
        ):
            handled = await cog.remove_unwanted_message(msg)

        assert handled is True
        auto_delete.assert_awaited_once()
        assert auto_delete.call_args.kwargs["rule"] == "cleanup.command_policy"
        assert "banned_cmd" in auto_delete.call_args.kwargs["reason"]

    @pytest.mark.asyncio
    async def test_whitelist_fallback_routes_through_auto_delete(self):
        """The whitelist branch fires when command_pattern matches but the
        governance path is skipped (guild None or command_name None).  Using
        guild=None to force the fallthrough — equivalent in the unit-test
        boundary, since the in-pipeline path doesn't reach DMs anyway.
        """
        cog = _make_cog()
        cog.whitelisted_channels = set()  # empty → not whitelisted
        msg = _make_message(content="!hello")
        msg.guild = None  # forces the if-guild-and-command-name fallthrough

        with patch(
            "cogs.cleanup_cog.moderation_service.auto_delete",
            new_callable=AsyncMock,
        ) as auto_delete:
            handled = await cog.remove_unwanted_message(msg)

        assert handled is True
        auto_delete.assert_awaited_once()
        assert auto_delete.call_args.kwargs["rule"] == "cleanup.whitelist"

    @pytest.mark.asyncio
    async def test_clean_message_returns_false_no_delete(self):
        cog = _make_cog()
        cog._pattern_cache[99] = []  # no prohibited words
        msg = _make_message(content="just chatting")

        with patch(
            "cogs.cleanup_cog.moderation_service.auto_delete",
            new_callable=AsyncMock,
        ) as auto_delete:
            handled = await cog.remove_unwanted_message(msg)

        assert handled is False
        auto_delete.assert_not_awaited()
