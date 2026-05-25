"""PR-5 — natural-language stage threads effective_source/mode and memory
metadata into the ai_decision_audit row.

Pins:

* Every ``record(...)`` call from the stage (denied / errored /
  skipped / degraded / replied) passes ``effective_source`` and
  ``effective_mode`` derived from the resolver's ``PolicyDecision``.
* The ``replied`` branch additionally passes
  ``memory_turns_used``, ``memory_window_minutes``,
  ``memory_scan_attempted``, ``memory_scan_added_turns`` from the
  metadata-aware memory helper.
* Other branches (denied / errored / skipped / degraded) leave the
  memory_* kwargs unset (None) — they did not produce a reply.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from core.runtime.ai.contracts import AIResponse, AITask, PolicyDenialReason
from core.runtime.ai.natural_language_stage import AINaturalLanguageStage
from core.runtime.message_pipeline import MessagePipelineContext
from services import ai_conversation_service, ai_memory_service
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
    msg.author.bot = False
    msg.author.roles = []
    return msg


def _make_ctx(message):
    bot = MagicMock()
    bot.user = SimpleNamespace(mentioned_in=lambda _msg: False)
    return MessagePipelineContext(bot=bot, message=message)


def _patch_common(monkeypatch):
    """Stub the snapshot and permission helpers that always run."""
    from core.runtime.ai import natural_language_stage as mod

    monkeypatch.setattr(
        mod.ai_permission_service,
        "snapshot",
        AsyncMock(return_value=SimpleNamespace(level=10, is_fresh_user=False)),
    )
    monkeypatch.setattr(
        mod.ai_permission_service,
        "is_on_cooldown",
        lambda *_a, **_kw: False,
    )
    monkeypatch.setattr(
        mod.ai_permission_service,
        "mark_reply_sent",
        lambda *_a, **_kw: None,
    )


def _capture_record(monkeypatch) -> list[dict]:
    """Replace ai_decision_audit_service.record with a kwargs capturer."""
    from core.runtime.ai import natural_language_stage as mod

    captured: list[dict] = []

    async def _capture(**kwargs):
        captured.append(kwargs)
        return len(captured)

    monkeypatch.setattr(mod.ai_decision_audit_service, "record", _capture)
    return captured


# ---------------------------------------------------------------------------
# Denied branch — effective fields populated, memory fields absent.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_denied_branch_carries_effective_source_and_mode(monkeypatch):
    from core.runtime.ai import natural_language_stage as mod

    _patch_common(monkeypatch)
    captured = _capture_record(monkeypatch)
    monkeypatch.setattr(
        mod.ai_natural_language_policy,
        "resolve",
        AsyncMock(
            return_value=PolicyDecision(
                allowed=False,
                reason_code=PolicyDenialReason.CHANNEL_DISABLED,
                effective_min_level=2,
                effective_cooldown=30,
                effective_mode="disabled",
                effective_source="channel",
                policy_snapshot_hash="h",
            ),
        ),
    )

    stage = AINaturalLanguageStage()
    msg = _make_message(content="hello world")
    await stage.process(_make_ctx(msg))

    row = captured[0]
    assert row["decision"] == "denied"
    assert row["effective_source"] == "channel"
    assert row["effective_mode"] == "disabled"
    # Memory fields are not threaded on the denied branch — they
    # remain unset (the helper defaults them to None at the DB layer).
    assert "memory_turns_used" not in row
    assert "memory_window_minutes" not in row


# ---------------------------------------------------------------------------
# Replied branch — full memory + effective metadata.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_replied_branch_carries_memory_and_effective_metadata(monkeypatch):
    from core.runtime.ai import natural_language_stage as mod

    _patch_common(monkeypatch)
    captured = _capture_record(monkeypatch)

    monkeypatch.setattr(
        mod.ai_natural_language_policy,
        "resolve",
        AsyncMock(
            return_value=PolicyDecision(
                allowed=True,
                reason_code=PolicyDenialReason.NONE,
                effective_min_level=2,
                effective_cooldown=30,
                effective_mode="always_reply",
                effective_source="guild",
                policy_snapshot_hash="h",
            ),
        ),
    )

    # Memory helper returns metadata with a populated turn list.
    fake_result = ai_memory_service.MemoryGatherResult(
        turns=[
            ai_conversation_service.ConversationTurn(
                user_id=1, role="user", text="prior", ts=1.0,
            ),
            ai_conversation_service.ConversationTurn(
                user_id=1, role="user", text="more prior", ts=2.0,
            ),
            ai_conversation_service.ConversationTurn(
                user_id=1, role="user", text="hello world", ts=3.0,
            ),
        ],
        window_minutes=30,
        scan_attempted=True,
        scan_added_turns=1,
    )
    monkeypatch.setattr(
        mod.ai_memory_service if hasattr(mod, "ai_memory_service") else ai_memory_service,
        "gather_recent_turns_with_metadata",
        AsyncMock(return_value=fake_result),
    )
    # The stage imports ai_memory_service inside the function body, so
    # also patch at the source.
    monkeypatch.setattr(
        ai_memory_service,
        "gather_recent_turns_with_metadata",
        AsyncMock(return_value=fake_result),
    )

    # Stub the instruction stack assembly and context build to return
    # minimal valid objects.
    monkeypatch.setattr(
        mod.ai_instruction_service,
        "assemble",
        AsyncMock(
            return_value=SimpleNamespace(
                instruction_profile_ids=(),
                system_instructions="",
                feature_instructions="",
                user_message="hello world",
            ),
        ),
    )
    monkeypatch.setattr(
        mod.ai_context_service,
        "build",
        lambda **_kw: SimpleNamespace(),
    )
    # Gateway returns a non-empty reply.
    monkeypatch.setattr(
        mod,
        "_invoke_gateway",
        AsyncMock(
            return_value=AIResponse(
                task=AITask.GENERAL_NL_ANSWER,
                provider="openai",
                model="gpt-4o-mini",
                text="hi there",
                degraded=False,
            ),
        ),
    )

    stage = AINaturalLanguageStage()
    msg = _make_message(content="hello world")
    await stage.process(_make_ctx(msg))

    # The last record() call is the `replied` row.
    row = captured[-1]
    assert row["decision"] == "replied"
    assert row["effective_source"] == "guild"
    assert row["effective_mode"] == "always_reply"
    assert row["memory_turns_used"] == 3
    assert row["memory_window_minutes"] == 30
    assert row["memory_scan_attempted"] is True
    assert row["memory_scan_added_turns"] == 1
    assert row["provider"] == "openai"
    assert row["model"] == "gpt-4o-mini"
