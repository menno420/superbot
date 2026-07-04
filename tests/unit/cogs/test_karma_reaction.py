"""Tests for the karma react-to-thank listener (cogs.karma_cog).

Reacting with the guild's configured trigger emoji grants karma to the
reacted message's author through the audited ``karma_service.give`` seam.
These tests pin the listener's gating: it only fires when react-to-thank is
enabled *and* the emoji matches, never for bots or self-reactions, and it
swallows a blocked grant (cooldown / cap / self / disabled) silently.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from cogs.karma_cog import KarmaCog
from services.karma_config import KarmaPolicy
from services.karma_service import KarmaCooldownError


def _policy(*, enabled: bool = True, emoji: str = "✨") -> KarmaPolicy:
    return KarmaPolicy(
        enabled=enabled,
        cooldown_seconds=3600,
        daily_cap=10,
        reaction_emoji=emoji,
    )


def _cog(*, author_id: int = 20, author_bot: bool = False) -> KarmaCog:
    """Build a KarmaCog whose bot resolves a fake channel + message."""
    author = SimpleNamespace(id=author_id, bot=author_bot)
    message = SimpleNamespace(author=author)
    channel = MagicMock(spec=discord.TextChannel)  # passes isinstance(Messageable)
    channel.fetch_message = AsyncMock(return_value=message)
    bot = MagicMock()
    bot.get_channel.return_value = channel
    return KarmaCog(bot)


def _payload(
    *,
    guild_id: int | None = 1,
    reactor_id: int = 10,
    reactor_bot: bool = False,
    emoji: str = "✨",
) -> SimpleNamespace:
    member = None if reactor_bot is None else SimpleNamespace(bot=reactor_bot)
    return SimpleNamespace(
        guild_id=guild_id,
        user_id=reactor_id,
        member=member,
        emoji=emoji,
        channel_id=100,
        message_id=200,
    )


class TestReactionToThank:
    @pytest.mark.asyncio
    async def test_matching_emoji_grants_karma(self):
        cog = _cog(author_id=20)
        with (
            patch(
                "services.karma_config.load_policy",
                new_callable=AsyncMock,
                return_value=_policy(emoji="✨"),
            ),
            patch(
                "services.karma_service.give",
                new_callable=AsyncMock,
            ) as give,
        ):
            await cog.on_raw_reaction_add(_payload(emoji="✨", reactor_id=10))
        give.assert_awaited_once()
        kwargs = give.await_args.kwargs
        assert kwargs["from_user"] == 10
        assert kwargs["to_user"] == 20
        assert kwargs["source"] == "reaction"

    @pytest.mark.asyncio
    async def test_feature_off_when_emoji_unset(self):
        cog = _cog()
        with (
            patch(
                "services.karma_config.load_policy",
                new_callable=AsyncMock,
                return_value=_policy(emoji=""),
            ),
            patch(
                "services.karma_service.give",
                new_callable=AsyncMock,
            ) as give,
        ):
            await cog.on_raw_reaction_add(_payload(emoji="✨"))
        give.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_disabled_policy_skips(self):
        cog = _cog()
        with (
            patch(
                "services.karma_config.load_policy",
                new_callable=AsyncMock,
                return_value=_policy(enabled=False),
            ),
            patch(
                "services.karma_service.give",
                new_callable=AsyncMock,
            ) as give,
        ):
            await cog.on_raw_reaction_add(_payload(emoji="✨"))
        give.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_non_matching_emoji_skips(self):
        cog = _cog()
        with (
            patch(
                "services.karma_config.load_policy",
                new_callable=AsyncMock,
                return_value=_policy(emoji="✨"),
            ),
            patch(
                "services.karma_service.give",
                new_callable=AsyncMock,
            ) as give,
        ):
            await cog.on_raw_reaction_add(_payload(emoji="👍"))
        give.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_bot_reactor_skips_before_policy_read(self):
        cog = _cog()
        with (
            patch(
                "services.karma_config.load_policy",
                new_callable=AsyncMock,
            ) as load,
            patch(
                "services.karma_service.give",
                new_callable=AsyncMock,
            ) as give,
        ):
            await cog.on_raw_reaction_add(_payload(reactor_bot=True))
        load.assert_not_awaited()  # bot pre-filter runs before any DB read
        give.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_dm_reaction_skips(self):
        cog = _cog()
        with patch(
            "services.karma_service.give",
            new_callable=AsyncMock,
        ) as give:
            await cog.on_raw_reaction_add(_payload(guild_id=None))
        give.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_bot_author_not_thanked(self):
        cog = _cog(author_bot=True)
        with (
            patch(
                "services.karma_config.load_policy",
                new_callable=AsyncMock,
                return_value=_policy(emoji="✨"),
            ),
            patch(
                "services.karma_service.give",
                new_callable=AsyncMock,
            ) as give,
        ):
            await cog.on_raw_reaction_add(_payload(emoji="✨"))
        give.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_self_reaction_is_noop(self):
        cog = _cog(author_id=10)  # author == reactor
        with (
            patch(
                "services.karma_config.load_policy",
                new_callable=AsyncMock,
                return_value=_policy(emoji="✨"),
            ),
            patch(
                "services.karma_service.give",
                new_callable=AsyncMock,
            ) as give,
        ):
            await cog.on_raw_reaction_add(_payload(emoji="✨", reactor_id=10))
        give.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_blocked_grant_is_swallowed(self):
        cog = _cog(author_id=20)
        with (
            patch(
                "services.karma_config.load_policy",
                new_callable=AsyncMock,
                return_value=_policy(emoji="✨"),
            ),
            patch(
                "services.karma_service.give",
                new_callable=AsyncMock,
                side_effect=KarmaCooldownError(60),
            ),
        ):
            # must not raise — a reaction never spams the channel with an error
            await cog.on_raw_reaction_add(_payload(emoji="✨", reactor_id=10))
