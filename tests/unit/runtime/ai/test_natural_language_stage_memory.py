"""Chat-memory recording tests for the natural-language stage.

The stage records every human guild message in
``ai_conversation_service`` (whether or not it ends up replying) so
the in-process cache feeds the chat-memory feature. The pipeline is
the only on_message-equivalent that the cog can install (the
boundary tests in ``test_no_duplicate_passive_listeners`` forbid the
AI cog from registering its own listener), so the recording lives
inside ``AINaturalLanguageStage.process()``.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from core.runtime.ai.contracts import PolicyDenialReason
from core.runtime.ai.natural_language_stage import AINaturalLanguageStage
from core.runtime.message_pipeline import MessagePipelineContext
from services import ai_conversation_service
from services.ai_natural_language_policy import PolicyDecision


@pytest.fixture(autouse=True)
def _reset_buffers():
    ai_conversation_service._reset_for_tests()
    yield
    ai_conversation_service._reset_for_tests()


def _make_message(
    *,
    content: str = "hello",
    guild_id: int = 99,
    channel_id: int = 1,
    user_id: int = 42,
    is_bot: bool = False,
):
    msg = MagicMock()
    msg.content = content
    msg.id = 555
    msg.guild = MagicMock()
    msg.guild.id = guild_id
    msg.channel = MagicMock()
    msg.channel.id = channel_id
    msg.channel.category_id = None
    msg.channel.send = AsyncMock()
    msg.author = MagicMock()
    msg.author.id = user_id
    msg.author.bot = is_bot
    msg.author.roles = []
    return msg


def _make_ctx(message):
    bot = MagicMock()
    bot.user = SimpleNamespace(mentioned_in=lambda _msg: False)
    return MessagePipelineContext(bot=bot, message=message)


def _patch_denied(monkeypatch):
    """Patch services so the stage immediately denies (we only want to
    test that the cache append happens BEFORE the decision)."""
    from core.runtime.ai import natural_language_stage as mod

    monkeypatch.setattr(
        mod.ai_permission_service,
        "snapshot",
        AsyncMock(
            return_value=SimpleNamespace(level=0, is_fresh_user=False),
        ),
    )
    monkeypatch.setattr(
        mod.ai_natural_language_policy,
        "resolve",
        AsyncMock(
            return_value=PolicyDecision(
                allowed=False,
                reason_code=PolicyDenialReason.BELOW_MIN_LEVEL,
                effective_min_level=5,
                effective_cooldown=30,
                policy_snapshot_hash="h",
            ),
        ),
    )
    monkeypatch.setattr(
        mod.ai_decision_audit_service,
        "record",
        AsyncMock(return_value=1),
    )


@pytest.mark.asyncio
async def test_stage_records_user_message_even_when_denied(monkeypatch):
    """Cache must capture bystander/denied messages so memory works
    in channels where the bot rarely replies."""
    _patch_denied(monkeypatch)
    stage = AINaturalLanguageStage()
    msg = _make_message(content="ambient channel chatter")
    await stage.process(_make_ctx(msg))

    turns = ai_conversation_service.recent_turns(99, 1)
    assert any(t.text == "ambient channel chatter" for t in turns)


@pytest.mark.asyncio
async def test_stage_skips_command_prefixed_messages(monkeypatch):
    _patch_denied(monkeypatch)
    stage = AINaturalLanguageStage()
    for content in ("!ai diagnostics", "/btd6 status"):
        msg = _make_message(content=content)
        await stage.process(_make_ctx(msg))

    assert ai_conversation_service.recent_turns(99, 1) == []


@pytest.mark.asyncio
async def test_stage_skips_bot_messages(monkeypatch):
    _patch_denied(monkeypatch)
    stage = AINaturalLanguageStage()
    msg = _make_message(content="i am a bot", is_bot=True)
    await stage.process(_make_ctx(msg))

    assert ai_conversation_service.recent_turns(99, 1) == []


@pytest.mark.asyncio
async def test_stage_skips_empty_text(monkeypatch):
    _patch_denied(monkeypatch)
    stage = AINaturalLanguageStage()
    msg = _make_message(content="   ")
    await stage.process(_make_ctx(msg))

    assert ai_conversation_service.recent_turns(99, 1) == []
