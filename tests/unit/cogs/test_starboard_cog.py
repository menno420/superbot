"""Tests for cogs.starboard_cog helpers (idea B1 / PR 2).

The self-star discount needs the cog to know whether the message author is among
the ⭐ reactors. ``_author_starred`` answers that from a message's reaction list;
these tests pin its behaviour (found / not-found / wrong-emoji / API-failure →
fail-open) without a live Discord connection.
"""

from __future__ import annotations

from types import SimpleNamespace

import discord
import pytest

from cogs.starboard_cog import _author_starred, _count_emoji


class _Reaction:
    """Minimal stand-in for ``discord.Reaction`` with an async ``users()``."""

    def __init__(self, emoji: str, user_ids: list[int], *, raises=False, count=None):
        self.emoji = emoji
        self.count = count if count is not None else len(user_ids)
        self._user_ids = user_ids
        self._raises = raises

    def users(self):
        raises = self._raises
        user_ids = self._user_ids

        async def _gen():
            if raises:
                raise discord.HTTPException(
                    SimpleNamespace(status=500, reason="Server Error"),
                    "boom",
                )
            for uid in user_ids:
                yield SimpleNamespace(id=uid)

        return _gen()


def _message(author_id: int, reactions: list[_Reaction]) -> SimpleNamespace:
    return SimpleNamespace(author=SimpleNamespace(id=author_id), reactions=reactions)


def test_count_emoji_reads_the_matching_reaction():
    msg = _message(10, [_Reaction("⭐", [1, 2, 3], count=3), _Reaction("🔥", [9])])
    assert _count_emoji(msg, "⭐") == 3
    assert _count_emoji(msg, "💎") == 0


@pytest.mark.asyncio
async def test_author_starred_true_when_author_reacted():
    msg = _message(10, [_Reaction("⭐", [1, 10, 2])])
    assert await _author_starred(msg, "⭐") is True


@pytest.mark.asyncio
async def test_author_starred_false_when_author_absent():
    msg = _message(10, [_Reaction("⭐", [1, 2, 3])])
    assert await _author_starred(msg, "⭐") is False


@pytest.mark.asyncio
async def test_author_starred_ignores_other_emoji():
    msg = _message(10, [_Reaction("🔥", [10])])
    assert await _author_starred(msg, "⭐") is False


@pytest.mark.asyncio
async def test_author_starred_fails_open_on_api_error():
    msg = _message(10, [_Reaction("⭐", [10], raises=True)])
    assert await _author_starred(msg, "⭐") is False
