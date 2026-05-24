"""Passive BTD6 message stage tests — Module 6 of the AI/BTD6 plan.

Each skip condition gets its own test so a regression that
accidentally enables passive behaviour by default shows up
exactly where the gate broke.
"""

from __future__ import annotations

import time
from types import SimpleNamespace
from unittest.mock import AsyncMock

import discord
import pytest

from cogs.btd6.stage import (
    REASON_ALREADY_HANDLED,
    REASON_BOT_AUTHOR,
    REASON_CHANNEL_NOT_CONFIGURED,
    REASON_COMMAND_PREFIX,
    REASON_COOLDOWN,
    REASON_DISABLED,
    REASON_EMPTY,
    REASON_LOW_CONFIDENCE,
    REASON_SYSTEM_MESSAGE,
    REASON_WEBHOOK,
    STAGE_NAME,
    STAGE_ORDER,
    BTD6AssistantMessageStage,
)
from core.runtime.message_pipeline import MessagePipelineContext


def _make_message(
    *,
    content: str = "Dart Monkey on round 63?",
    author_bot: bool = False,
    webhook_id: int | None = None,
    channel_id: int = 1234,
    guild_id: int | None = 9999,
    msg_type: discord.MessageType = discord.MessageType.default,
):
    author = SimpleNamespace(id=42, bot=author_bot, name="alice")
    channel = SimpleNamespace(id=channel_id)
    guild = SimpleNamespace(id=guild_id) if guild_id is not None else None
    message = SimpleNamespace(
        id=99,
        content=content,
        author=author,
        channel=channel,
        guild=guild,
        webhook_id=webhook_id,
        type=msg_type,
    )
    message.reply = AsyncMock()
    return message


def _make_ctx(message, *, command_prefix: str = "!", metadata: dict | None = None):
    bot = SimpleNamespace(command_prefix=command_prefix)
    ctx = MessagePipelineContext(bot=bot, message=message)
    if metadata:
        ctx.metadata.update(metadata)
    return ctx


@pytest.fixture
def stage(monkeypatch):
    monkeypatch.delenv("BTD6_PASSIVE_ENABLED", raising=False)
    monkeypatch.delenv("BTD6_PASSIVE_CHANNELS", raising=False)
    monkeypatch.delenv("BTD6_CONFIDENCE_THRESHOLD", raising=False)
    monkeypatch.delenv("BTD6_COOLDOWN_SECONDS", raising=False)
    monkeypatch.delenv("BTD6_AI_ENABLED", raising=False)
    monkeypatch.delenv("AI_ENABLED", raising=False)
    yield BTD6AssistantMessageStage()


def test_stage_has_correct_name_and_order(stage):
    assert stage.name == STAGE_NAME
    assert stage.order == STAGE_ORDER


@pytest.mark.asyncio
async def test_default_config_does_not_respond(stage):
    """`BTD6_PASSIVE_ENABLED` unset means we never reply."""
    message = _make_message()
    ctx = _make_ctx(message)
    result = await stage.process(ctx)
    assert not message.reply.await_count
    assert result.deleted is False
    assert result.short_circuit is False
    skips = stage.latest_skips(message.channel.id)
    assert skips and skips[-1].reason == REASON_DISABLED


@pytest.mark.asyncio
async def test_bot_author_skipped(stage):
    message = _make_message(author_bot=True)
    await stage.process(_make_ctx(message))
    assert stage.latest_skips(message.channel.id)[-1].reason == REASON_BOT_AUTHOR


@pytest.mark.asyncio
async def test_webhook_message_skipped(stage):
    message = _make_message(webhook_id=12345)
    await stage.process(_make_ctx(message))
    assert stage.latest_skips(message.channel.id)[-1].reason == REASON_WEBHOOK


@pytest.mark.asyncio
async def test_system_message_skipped(stage):
    message = _make_message(msg_type=discord.MessageType.pins_add)
    await stage.process(_make_ctx(message))
    assert (
        stage.latest_skips(message.channel.id)[-1].reason == REASON_SYSTEM_MESSAGE
    )


@pytest.mark.asyncio
async def test_command_prefix_message_skipped(stage):
    message = _make_message(content="!btd6 status")
    await stage.process(_make_ctx(message, command_prefix="!"))
    assert (
        stage.latest_skips(message.channel.id)[-1].reason == REASON_COMMAND_PREFIX
    )


@pytest.mark.asyncio
async def test_empty_message_skipped(stage):
    message = _make_message(content="   ")
    await stage.process(_make_ctx(message))
    assert stage.latest_skips(message.channel.id)[-1].reason == REASON_EMPTY


@pytest.mark.asyncio
async def test_unconfigured_channel_skipped(stage, monkeypatch):
    monkeypatch.setenv("BTD6_PASSIVE_ENABLED", "1")
    monkeypatch.setenv("BTD6_PASSIVE_CHANNELS", "111,222")
    message = _make_message(channel_id=999)  # not in the configured list
    await stage.process(_make_ctx(message))
    assert (
        stage.latest_skips(message.channel.id)[-1].reason
        == REASON_CHANNEL_NOT_CONFIGURED
    )


@pytest.mark.asyncio
async def test_already_handled_metadata_skipped(stage, monkeypatch):
    monkeypatch.setenv("BTD6_PASSIVE_ENABLED", "1")
    message = _make_message()
    ctx = _make_ctx(message, metadata={"handled_by": "some_other_stage"})
    await stage.process(ctx)
    assert (
        stage.latest_skips(message.channel.id)[-1].reason == REASON_ALREADY_HANDLED
    )


@pytest.mark.asyncio
async def test_low_confidence_skipped(stage, monkeypatch):
    monkeypatch.setenv("BTD6_PASSIVE_ENABLED", "1")
    message = _make_message(content="hello everyone how are we doing today")
    await stage.process(_make_ctx(message))
    last = stage.latest_skips(message.channel.id)[-1]
    assert last.reason == REASON_LOW_CONFIDENCE
    assert last.confidence < 0.34


@pytest.mark.asyncio
async def test_cooldown_skipped_after_handled(stage, monkeypatch):
    """After handling once, the same user gets a cooldown skip."""
    monkeypatch.setenv("BTD6_PASSIVE_ENABLED", "1")
    monkeypatch.setenv("BTD6_COOLDOWN_SECONDS", "60")

    message1 = _make_message()
    await stage.process(_make_ctx(message1))
    assert message1.reply.await_count == 1  # the first message was answered

    message2 = _make_message()
    await stage.process(_make_ctx(message2))
    assert message2.reply.await_count == 0  # cooldown blocked it
    assert stage.latest_skips(message2.channel.id)[-1].reason == REASON_COOLDOWN


@pytest.mark.asyncio
async def test_configured_channel_high_confidence_replies(stage, monkeypatch):
    """All gates pass → the stage replies and marks ctx.metadata."""
    monkeypatch.setenv("BTD6_PASSIVE_ENABLED", "1")
    monkeypatch.setenv("BTD6_PASSIVE_CHANNELS", "1234")
    monkeypatch.setenv("BTD6_COOLDOWN_SECONDS", "0")

    message = _make_message(content="Dart Monkey on round 63 in CHIMPS")
    ctx = _make_ctx(message)
    await stage.process(ctx)

    assert message.reply.await_count == 1
    embed = message.reply.await_args.kwargs.get("embed")
    assert embed is not None
    assert ctx.metadata.get("handled_by") == STAGE_NAME


def test_skip_buffer_never_includes_message_content(stage):
    """`why-no-response` must not leak user content. The buffer is reason-only."""
    msg = _make_message(content="my secret strategy goes here")
    import asyncio

    asyncio.run(stage.process(_make_ctx(msg)))
    skips = stage.latest_skips(msg.channel.id)
    for record in skips:
        assert "secret" not in record.reason.lower()


def test_skip_buffer_is_bounded(stage):
    """The per-channel buffer caps at the configured size."""
    # Spam many empty messages to fill the buffer.
    import asyncio

    for _ in range(20):
        msg = _make_message(content="")
        asyncio.run(stage.process(_make_ctx(msg)))
    skips = stage.latest_skips(1234)
    assert len(skips) <= 8  # _SKIP_BUFFER_PER_CHANNEL
