"""Tests for the 420 easter-egg subsystem (PR #420).

Pins the two surfaces:

* ``FourTwentyStage`` — the passive message hook: matches 420/4:20/blaze
  it, ignores look-alikes (1420, 4200), is observe-only (never deletes /
  short-circuits), and self-rate-limits per channel.
* ``_FourTwentyPanelView`` — the ``!420`` panel: wisdom + fact buttons
  edit in place, overview returns.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from cogs.four_twenty_cog import (
    FOUR_TWENTY_STAGE_NAME,
    FOUR_TWENTY_STAGE_ORDER,
    FourTwentyStage,
    _FourTwentyPanelView,
)
from core.runtime.message_pipeline import MessagePipelineContext

# ---------------------------------------------------------------------------
# Trigger matching
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "420",
        "it's 4:20 somewhere",
        "4-20 baby",
        "blaze it",
        "BLAZE IT",
        "four twenty",
        "four-twenty",
        "lol 420 dude",
    ],
)
def test_trigger_matches(text):
    from cogs.four_twenty_cog import _TRIGGER_RE

    assert _TRIGGER_RE.search(text) is not None


@pytest.mark.parametrize(
    "text",
    [
        "1420",
        "4200",
        "the year 2042",
        "channel 14200",
        "hello world",
        "score is 42",
        "",
    ],
)
def test_trigger_rejects_lookalikes(text):
    from cogs.four_twenty_cog import _TRIGGER_RE

    assert _TRIGGER_RE.search(text) is None


# ---------------------------------------------------------------------------
# Stage behaviour
# ---------------------------------------------------------------------------


def _ctx(content: str, channel_id: int = 1):
    message = MagicMock()
    message.content = content
    message.add_reaction = AsyncMock()
    channel = MagicMock()
    channel.id = channel_id
    channel.send = AsyncMock()
    message.channel = channel
    return MessagePipelineContext(bot=MagicMock(), message=message), message


def test_stage_identity():
    stage = FourTwentyStage()
    assert stage.name == FOUR_TWENTY_STAGE_NAME
    # Observe-only stage runs late, behind game/mod/xp stages.
    assert stage.order == FOUR_TWENTY_STAGE_ORDER >= 90


@pytest.mark.asyncio
async def test_stage_reacts_on_match_and_is_observe_only():
    stage = FourTwentyStage()
    ctx, message = _ctx("420 friends")
    # Force the one-liner branch on so we can assert it routes to channel.send.
    with patch("cogs.four_twenty_cog.random.random", return_value=0.0):
        result = await stage.process(ctx)
    message.add_reaction.assert_awaited_once_with("🍃")
    message.channel.send.assert_awaited_once()
    # Never destructive, never short-circuits the pipeline.
    assert result.deleted is False
    assert result.short_circuit is False


@pytest.mark.asyncio
async def test_stage_reaction_only_when_random_high():
    stage = FourTwentyStage()
    ctx, message = _ctx("blaze it")
    with patch("cogs.four_twenty_cog.random.random", return_value=0.99):
        await stage.process(ctx)
    message.add_reaction.assert_awaited_once_with("🍃")
    message.channel.send.assert_not_awaited()  # quiet react, no one-liner


@pytest.mark.asyncio
async def test_stage_ignores_non_match():
    stage = FourTwentyStage()
    ctx, message = _ctx("just a normal message")
    result = await stage.process(ctx)
    message.add_reaction.assert_not_awaited()
    assert result.deleted is False and result.short_circuit is False


@pytest.mark.asyncio
async def test_stage_per_channel_cooldown():
    stage = FourTwentyStage()
    ctx1, m1 = _ctx("420", channel_id=7)
    ctx2, m2 = _ctx("420 again", channel_id=7)
    with patch("cogs.four_twenty_cog.random.random", return_value=0.99):
        await stage.process(ctx1)
        await stage.process(ctx2)  # same channel, within cooldown
    m1.add_reaction.assert_awaited_once()
    m2.add_reaction.assert_not_awaited()  # suppressed by cooldown


@pytest.mark.asyncio
async def test_stage_swallows_reaction_failure():
    stage = FourTwentyStage()
    ctx, message = _ctx("420")
    message.add_reaction = AsyncMock(
        side_effect=discord.HTTPException(MagicMock(), "boom")
    )
    # Must not raise — the egg can never break message handling.
    result = await stage.process(ctx)
    assert result.deleted is False and result.short_circuit is False


# ---------------------------------------------------------------------------
# Panel
# ---------------------------------------------------------------------------


def _panel():
    cog = MagicMock()
    cog._wisdom = ["stay leafy"]
    cog._facts = ["420 is the sum of four primes"]
    author = MagicMock()
    author.id = 1
    return _FourTwentyPanelView(author, cog)


async def _click(view, label: str, interaction) -> None:
    """Invoke a decorator-defined button callback the way discord.py does."""
    btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.label == label
    )
    btn._view = view  # discord.py binds the parent view via Item._view
    await btn.callback(interaction)


@pytest.mark.asyncio
async def test_wisdom_button_edits_in_place():
    view = _panel()
    interaction = MagicMock()
    interaction.response.edit_message = AsyncMock()
    await _click(view, "🍃 Wisdom", interaction)
    interaction.response.edit_message.assert_awaited_once()
    embed = interaction.response.edit_message.await_args.kwargs["embed"]
    assert "stay leafy" in embed.description


@pytest.mark.asyncio
async def test_fact_button_edits_in_place():
    view = _panel()
    interaction = MagicMock()
    interaction.response.edit_message = AsyncMock()
    await _click(view, "🔢 420 Fact", interaction)
    interaction.response.edit_message.assert_awaited_once()
    embed = interaction.response.edit_message.await_args.kwargs["embed"]
    assert "four primes" in embed.description


@pytest.mark.asyncio
async def test_panel_handles_empty_pools_gracefully():
    cog = MagicMock()
    cog._wisdom = []
    cog._facts = []
    author = MagicMock()
    author.id = 1
    view = _FourTwentyPanelView(author, cog)
    interaction = MagicMock()
    interaction.response.edit_message = AsyncMock()
    await _click(view, "🍃 Wisdom", interaction)
    embed = interaction.response.edit_message.await_args.kwargs["embed"]
    assert "No wisdom available" in embed.description
