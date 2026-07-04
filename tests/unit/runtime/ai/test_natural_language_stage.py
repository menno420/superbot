"""Regression tests for the central natural-language stage (Issue A fix).

Pinned behaviours after the post-PR-#310 hardening:

* ``_invoke_gateway`` calls ``services.ai_gateway.execute`` (not the
  old non-existent ``run``).
* Provider failure surfaces as ``decision='degraded'`` /
  ``PROVIDER_UNAVAILABLE`` — never as a misleading
  ``skipped / NO_ROUTE_MATCHED`` row.
* Genuine empty-text from a healthy provider still records
  ``skipped / NO_ROUTE_MATCHED``.
* Success rows carry ``provider`` and ``model`` populated from the
  ``AIResponse`` so the audit table is debug-actionable.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from core.runtime.ai.contracts import (
    AIRequest,
    AIRequestContext,
    AIResponse,
    AIResponseMode,
    AIScope,
    AITask,
    PolicyDenialReason,
)
from core.runtime.ai.natural_language_stage import (
    AINaturalLanguageStage,
    _invoke_gateway,
    _is_direct_bot_mention,
)
from core.runtime.message_pipeline import MessagePipelineContext

# Capture the real implementations at import time so the new PR-1
# tests can restore them after ``stub_services`` swaps them out for
# mocks. Importing inside a fixture would re-read the (already
# mocked) module attribute and produce a no-op.
from services.ai_conversation_service import (  # noqa: E402
    _reset_for_tests as _real_reset_buffers,
)
from services.ai_conversation_service import append as _real_conversation_append
from services.ai_conversation_service import recent_turns as _real_recent_turns
from services.ai_instruction_service import assemble as _real_assemble  # noqa: E402
from services.ai_natural_language_policy import PolicyDecision
from services.ai_task_router import classify as _real_router_classify  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_message(*, guild_id: int = 99, channel_id: int = 1, user_id: int = 42):
    msg = MagicMock()
    msg.content = "hello bot"
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
    # A real discord Message always exposes ``mentions`` as a list and
    # ``mention_everyone`` as a bool. Default: nobody pinged. Tests that
    # need a direct bot mention set these explicitly.
    msg.mentions = []
    msg.mention_everyone = False
    return msg


def _make_ctx(message):
    bot = MagicMock()
    bot.user = SimpleNamespace(mentioned_in=lambda _msg: True)
    return MessagePipelineContext(bot=bot, message=message)


def _make_allowed_decision() -> PolicyDecision:
    return PolicyDecision(
        allowed=True,
        reason_code=PolicyDenialReason.NONE,
        effective_min_level=0,
        effective_cooldown=0,
        instruction_profile_ids=(),
        policy_snapshot_hash="hash",
    )


def _make_response(
    *,
    text: str | None,
    degraded: bool = False,
    provider: str = "openai",
    model: str = "gpt-4o-mini",
    fallback_reason: str | None = None,
) -> AIResponse:
    return AIResponse(
        task=AITask.GENERAL_NL_ANSWER,
        provider=provider,
        model=model,
        text=text,
        data=None,
        suggestions=(),
        latency_ms=12.3,
        degraded=degraded,
        fallback_reason=fallback_reason,
    )


@pytest.fixture
def stub_services(monkeypatch):
    """Stub every service used by the stage so the test owns its inputs."""
    from core.runtime.ai import natural_language_stage as mod

    monkeypatch.setattr(
        mod.ai_permission_service,
        "snapshot",
        AsyncMock(
            return_value=SimpleNamespace(level=10, is_fresh_user=False),
        ),
    )
    monkeypatch.setattr(
        mod.ai_permission_service,
        "is_on_cooldown",
        lambda *a, **kw: False,
    )
    monkeypatch.setattr(
        mod.ai_permission_service,
        "mark_reply_sent",
        lambda *a, **kw: None,
    )
    monkeypatch.setattr(
        mod.ai_natural_language_policy,
        "resolve",
        AsyncMock(return_value=_make_allowed_decision()),
    )
    monkeypatch.setattr(
        mod.ai_task_router,
        "classify",
        lambda _text, **_kw: SimpleNamespace(
            task=AITask.GENERAL_NL_ANSWER,
            route="general.nl_answer",
        ),
    )
    monkeypatch.setattr(
        mod.ai_instruction_service,
        "assemble",
        AsyncMock(
            return_value=SimpleNamespace(
                render_system_prompt=lambda: "sys",
                render_payload_text=lambda: "user text",
                instruction_profile_ids=(),
            ),
        ),
    )
    monkeypatch.setattr(
        mod.ai_context_service,
        "build",
        lambda **kw: SimpleNamespace(
            request_context=AIRequestContext(
                task=kw["task"],
                scope=AIScope.USER,
                guild_id=kw["guild_id"],
                actor_id=kw["actor_id"],
                channel_id=kw["channel_id"],
                correlation_id=kw["correlation_id"],
                source="test",
            ),
            correlation_id=kw["correlation_id"],
        ),
    )
    monkeypatch.setattr(
        mod.ai_conversation_service,
        "append",
        lambda *a, **kw: None,
    )

    audit_calls: list[dict] = []

    async def _capture(**kwargs):
        audit_calls.append(kwargs)
        return len(audit_calls)

    monkeypatch.setattr(mod.ai_decision_audit_service, "record", _capture)

    from core.runtime.ai import response_renderer_registry

    monkeypatch.setattr(
        response_renderer_registry, "render", AsyncMock(return_value=None)
    )

    return audit_calls


# ---------------------------------------------------------------------------
# _invoke_gateway — the actual one-word-name regression pin
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_invoke_gateway_calls_execute_not_run(monkeypatch):
    """The stage must call ``ai_gateway.execute`` (the old ``run`` name
    raised AttributeError silently and was misattributed as
    ``skipped / NO_ROUTE_MATCHED`` in the audit table)."""
    from services import ai_gateway

    captured: dict[str, AIRequest] = {}

    async def fake_execute(request: AIRequest) -> AIResponse:
        captured["request"] = request
        return _make_response(text="ok")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    stack = SimpleNamespace(
        render_system_prompt=lambda: "sys",
        render_payload_text=lambda: "payload",
    )
    built = SimpleNamespace(
        request_context=AIRequestContext(
            task=AITask.GENERAL_NL_ANSWER,
            scope=AIScope.USER,
            source="test",
        ),
    )
    ctx = _make_ctx(_make_message())

    response = await _invoke_gateway(stack, built, ctx)

    assert "request" in captured, "execute() was never called"
    assert isinstance(captured["request"], AIRequest)
    assert captured["request"].mode is AIResponseMode.TEXT
    assert response.text == "ok"


# ---------------------------------------------------------------------------
# Audit semantics — degraded vs skipped vs replied vs errored
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_replied_audit_carries_provider_and_model(
    monkeypatch,
    stub_services,
):
    """Success audit must populate ``provider`` and ``model`` from the
    gateway response so operators can debug routing decisions."""
    from services import ai_gateway

    async def fake_execute(_request):
        return _make_response(
            text="here is my reply",
            provider="openai",
            model="gpt-4o-mini",
        )

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    stage = AINaturalLanguageStage()
    msg = _make_message()
    await stage.process(_make_ctx(msg))

    assert len(stub_services) == 1
    row = stub_services[0]
    assert row["decision"] == "replied"
    assert row["reason_code"] is PolicyDenialReason.NONE
    assert row["provider"] == "openai"
    assert row["model"] == "gpt-4o-mini"
    msg.channel.send.assert_awaited_once()
    call_args, call_kwargs = msg.channel.send.call_args
    assert call_args == ("here is my reply",)
    am = call_kwargs.get("allowed_mentions")
    assert am is not None
    assert am.everyone is False


@pytest.mark.asyncio
async def test_preset_short_circuits_before_gateway(monkeypatch, stub_services):
    """An operator-authored vetted preset is served verbatim with NO model call.

    The whole point of the preset layer: an exact normalized-question match
    short-circuits before feature-facts + the gateway, so the provider is never
    invoked and the reply is the operator's exact text.
    """
    from services import ai_gateway, ai_preset_service

    async def _preset(_guild_id, _question):
        return "The vetted answer."

    monkeypatch.setattr(ai_preset_service, "lookup", _preset)
    execute = AsyncMock()
    monkeypatch.setattr(ai_gateway, "execute", execute)

    stage = AINaturalLanguageStage()
    msg = _make_message()
    result = await stage.process(_make_ctx(msg))

    # The gateway/provider was never called — zero-API answer.
    execute.assert_not_called()
    # The exact vetted text was sent.
    msg.channel.send.assert_awaited_once()
    call_args, _ = msg.channel.send.call_args
    assert call_args == ("The vetted answer.",)
    # Audited as a normal reply, and the pipeline short-circuited.
    assert len(stub_services) == 1
    assert stub_services[0]["decision"] == "replied"
    assert result.short_circuit is True


@pytest.mark.asyncio
async def test_no_preset_runs_the_normal_model_path(monkeypatch, stub_services):
    """With no matching preset (lookup → None) the gateway path runs unchanged —
    the preset layer is byte-identical when the table is empty."""
    from services import ai_gateway, ai_preset_service

    async def _no_preset(_guild_id, _question):
        return None

    monkeypatch.setattr(ai_preset_service, "lookup", _no_preset)

    async def fake_execute(_request):
        return _make_response(text="model reply", provider="openai", model="gpt-4o-mini")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    stage = AINaturalLanguageStage()
    msg = _make_message()
    await stage.process(_make_ctx(msg))

    msg.channel.send.assert_awaited_once()
    call_args, _ = msg.channel.send.call_args
    assert call_args == ("model reply",)
    assert stub_services[0]["decision"] == "replied"
    assert stub_services[0]["provider"] == "openai"


@pytest.mark.asyncio
async def test_degraded_response_audits_as_degraded(monkeypatch, stub_services):
    """A degraded response (gateway/provider failure) must audit as
    ``decision='degraded'``, NOT the misleading ``skipped /
    NO_ROUTE_MATCHED`` that the old swallow-and-empty-string path
    produced."""
    from services import ai_gateway

    async def fake_execute(_request):
        return _make_response(
            text=None,
            degraded=True,
            provider="openai",
            model="",
            fallback_reason="timeout:20s",
        )

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    stage = AINaturalLanguageStage()
    msg = _make_message()
    await stage.process(_make_ctx(msg))

    assert len(stub_services) == 1
    row = stub_services[0]
    assert row["decision"] == "degraded"
    assert row["reason_code"] is PolicyDenialReason.PROVIDER_UNAVAILABLE
    assert row["provider"] == "openai"
    # No reply was sent.
    msg.channel.send.assert_not_called()


@pytest.mark.asyncio
async def test_healthy_empty_response_audits_as_skipped(monkeypatch, stub_services):
    """A non-degraded response with empty text (model genuinely chose
    not to answer) keeps the ``skipped / NO_ROUTE_MATCHED`` semantics."""
    from services import ai_gateway

    async def fake_execute(_request):
        return _make_response(
            text="",
            degraded=False,
            provider="deterministic",
            model="",
        )

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    stage = AINaturalLanguageStage()
    msg = _make_message()
    await stage.process(_make_ctx(msg))

    assert len(stub_services) == 1
    row = stub_services[0]
    assert row["decision"] == "skipped"
    assert row["reason_code"] is PolicyDenialReason.NO_ROUTE_MATCHED
    msg.channel.send.assert_not_called()


@pytest.mark.asyncio
async def test_gateway_raises_audits_as_errored(monkeypatch, stub_services):
    """If the gateway violates its own no-raise contract, the outer
    handler audits the failure as ``errored / PROVIDER_UNAVAILABLE``
    — never the misleading ``skipped`` row the old local swallow
    produced."""
    from services import ai_gateway

    async def fake_execute(_request):
        raise RuntimeError("contract violation")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    stage = AINaturalLanguageStage()
    msg = _make_message()
    await stage.process(_make_ctx(msg))

    assert len(stub_services) == 1
    row = stub_services[0]
    assert row["decision"] == "errored"
    assert row["reason_code"] is PolicyDenialReason.PROVIDER_UNAVAILABLE
    msg.channel.send.assert_not_called()


# ---------------------------------------------------------------------------
# Renderer seam — PR 6
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_renderer_seam_uses_embed_when_renderer_returns_response(
    monkeypatch,
    stub_services,
):
    """When the registry returns a RenderedResponse, the stage sends the embed."""
    from core.runtime.ai import response_renderer_registry
    from core.runtime.ai.response_renderer_registry import RenderedResponse
    from services import ai_gateway

    async def fake_execute(_request):
        return _make_response(text="summary text")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    fake_embed = MagicMock()
    rendered = RenderedResponse(content=None, embed=fake_embed, allowed_mentions=None)
    monkeypatch.setattr(
        response_renderer_registry,
        "render",
        AsyncMock(return_value=rendered),
    )

    stage = AINaturalLanguageStage()
    msg = _make_message()
    await stage.process(_make_ctx(msg))

    msg.channel.send.assert_awaited_once()
    call_kwargs = msg.channel.send.call_args
    assert call_kwargs.kwargs.get("embed") is fake_embed
    assert call_kwargs.kwargs.get("allowed_mentions") is not None

    assert len(stub_services) == 1
    assert stub_services[0]["decision"] == "replied"


@pytest.mark.asyncio
async def test_renderer_seam_plain_text_when_renderer_returns_none(
    monkeypatch,
    stub_services,
):
    """When the registry returns None, the stage sends plain text with AllowedMentions.none()."""
    from services import ai_gateway

    async def fake_execute(_request):
        return _make_response(text="plain text reply")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    stage = AINaturalLanguageStage()
    msg = _make_message()
    await stage.process(_make_ctx(msg))

    msg.channel.send.assert_awaited_once()
    call_args, call_kwargs = msg.channel.send.call_args
    assert call_args == ("plain text reply",)
    am = call_kwargs.get("allowed_mentions")
    assert am is not None
    assert am.everyone is False


@pytest.mark.asyncio
async def test_send_failure_video_task_writes_video_send_failed(
    monkeypatch,
    stub_services,
):
    """Send failure on a VIDEO task writes reason_code='video_response_send_failed'."""
    from core.runtime.ai import natural_language_stage as mod
    from core.runtime.ai.feature_facts import FeatureFactsResult
    from services import ai_gateway

    monkeypatch.setattr(
        mod.ai_task_router,
        "classify",
        lambda _t, **_kw: SimpleNamespace(
            task=AITask.VIDEO_DESCRIBE, route="video.describe"
        ),
    )
    monkeypatch.setattr(
        mod,
        "_gather_feature_facts",
        AsyncMock(
            return_value=FeatureFactsResult(
                facts=("title: Test Video",), render_context=None
            )
        ),
    )

    async def fake_execute(_request):
        return _make_response(text="video summary")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    stage = AINaturalLanguageStage()
    msg = _make_message()
    msg.channel.send = AsyncMock(
        side_effect=discord.HTTPException(MagicMock(), "send failed")
    )
    await stage.process(_make_ctx(msg))

    assert len(stub_services) == 1
    row = stub_services[0]
    assert row["decision"] == "errored"
    assert row["reason_code"] == "video_response_send_failed"


@pytest.mark.asyncio
async def test_send_failure_non_video_task_writes_response_send_failed(
    monkeypatch,
    stub_services,
):
    """Send failure on a non-video task writes reason_code='response_send_failed'."""
    from services import ai_gateway

    async def fake_execute(_request):
        return _make_response(text="some reply")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    stage = AINaturalLanguageStage()
    msg = _make_message()
    msg.channel.send = AsyncMock(
        side_effect=discord.HTTPException(MagicMock(), "send failed")
    )
    await stage.process(_make_ctx(msg))

    assert len(stub_services) == 1
    row = stub_services[0]
    assert row["decision"] == "errored"
    assert row["reason_code"] == "response_send_failed"


# ---------------------------------------------------------------------------
# BUG-0009 — "Monkey Knowledge related to <tower>" pre-emptive deterministic floor
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mk_reference_question_floored_before_model(monkeypatch, stub_services):
    """A clear "which MK relate to the farm?" question is answered by the
    deterministic builder and the model gateway is NEVER called — the model's
    own grouping is the BUG-0009 mislabel, and it passes the value guard."""
    from core.runtime.ai import natural_language_stage as mod
    from core.runtime.ai.feature_facts import FeatureFactsResult
    from services import ai_gateway

    monkeypatch.setattr(
        mod.ai_task_router,
        "classify",
        lambda _t, **_kw: SimpleNamespace(task=AITask.BTD6_ANSWER, route="btd6.answer"),
    )
    monkeypatch.setattr(
        mod,
        "_gather_feature_facts",
        AsyncMock(return_value=FeatureFactsResult(facts=(), render_context=None)),
    )

    gateway_called = False

    async def fake_execute(_request):
        nonlocal gateway_called
        gateway_called = True
        return _make_response(text="should not be used")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    stage = AINaturalLanguageStage()
    msg = _make_message()
    msg.content = "what are all the monkey knowledges related to the farm"
    await stage.process(_make_ctx(msg))

    assert gateway_called is False, "model was invoked for a deterministic case"
    sent = "\n".join(c.args[0] for c in msg.channel.send.call_args_list)
    assert "Banana Farm" in sent
    assert "Farm Subsidy" in sent
    assert "Big Traps" not in sent  # the model's wrong grouping
    assert stub_services and stub_services[-1]["decision"] == "replied"


@pytest.mark.asyncio
async def test_non_mk_btd6_question_still_reaches_model(monkeypatch, stub_services):
    """The floor is narrow: an ordinary BTD6 question is untouched (the model
    still runs), so only the mislabel-prone list class is intercepted."""
    from core.runtime.ai import natural_language_stage as mod
    from core.runtime.ai.feature_facts import FeatureFactsResult
    from services import ai_gateway

    monkeypatch.setattr(
        mod.ai_task_router,
        "classify",
        lambda _t, **_kw: SimpleNamespace(task=AITask.BTD6_ANSWER, route="btd6.answer"),
    )
    monkeypatch.setattr(
        mod,
        "_gather_feature_facts",
        AsyncMock(
            return_value=FeatureFactsResult(
                facts=("Dart Monkey base cost: $200",), render_context=None
            )
        ),
    )

    gateway_called = False

    async def fake_execute(_request):
        nonlocal gateway_called
        gateway_called = True
        return _make_response(text="A Dart Monkey costs $200.")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    stage = AINaturalLanguageStage()
    msg = _make_message()
    msg.content = "how much does a dart monkey cost"
    await stage.process(_make_ctx(msg))

    assert gateway_called is True, "the model floor leaked onto a normal question"


@pytest.mark.asyncio
async def test_geraldo_per_level_question_floored_before_model(
    monkeypatch, stub_services
):
    """A "what does Geraldo unlock per level?" question is answered by the
    deterministic builder and the model gateway is NEVER called (BUG-0009 slice
    2 — the model's own per-level grouping is the mislabel that passes the value
    guard). Confirms the unified dispatcher routes the Geraldo family too."""
    from core.runtime.ai import natural_language_stage as mod
    from core.runtime.ai.feature_facts import FeatureFactsResult
    from services import ai_gateway

    monkeypatch.setattr(
        mod.ai_task_router,
        "classify",
        lambda _t, **_kw: SimpleNamespace(task=AITask.BTD6_ANSWER, route="btd6.answer"),
    )
    monkeypatch.setattr(
        mod,
        "_gather_feature_facts",
        AsyncMock(return_value=FeatureFactsResult(facts=(), render_context=None)),
    )

    gateway_called = False

    async def fake_execute(_request):
        nonlocal gateway_called
        gateway_called = True
        return _make_response(text="should not be used")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    stage = AINaturalLanguageStage()
    msg = _make_message()
    msg.content = "what items does geraldo unlock at each level"
    await stage.process(_make_ctx(msg))

    assert gateway_called is False, "model was invoked for a deterministic case"
    sent = "\n".join(c.args[0] for c in msg.channel.send.call_args_list)
    assert "Geraldo" in sent
    assert "Paragon Power Totem" in sent
    assert stub_services and stub_services[-1]["decision"] == "replied"


# ---------------------------------------------------------------------------
# PR 1 — AI mention-reply bug fixes:
#   * task contract framing (T1, T2)
#   * outbound snowflake redaction (T4b, T4c)
#   * triggering message not duplicated in payload (T5)
#   * triggering mention recorded exactly once for future context (T6, T7)
#   * multiple bot mentions stripped (T11)
#   * bare-mention messages do not call the provider (T12)
# ---------------------------------------------------------------------------


_BOT_ID = 555000000000000111


def _make_message_with_mention(content: str, *, user_id: int = 42):
    """Discord message whose content is exactly ``content`` and which
    directly, personally pings the bot (the bot's id is in ``mentions``)."""
    msg = _make_message(user_id=user_id)
    msg.content = content
    msg.mentions = [SimpleNamespace(id=_BOT_ID)]
    return msg


def _make_ctx_with_bot_id(message):
    """Pipeline context whose ``bot.user`` has both ``mentioned_in`` and ``id``.

    The default ``_make_ctx`` does not give ``bot.user`` an ``id``, so
    mention-stripping is a no-op there. These tests need the real
    bot-id plumbing to verify the strip behaviour.
    """
    bot = MagicMock()
    bot.user = SimpleNamespace(
        id=_BOT_ID,
        mentioned_in=lambda _msg: True,
    )
    return MessagePipelineContext(bot=bot, message=message)


def _use_real_assemble(monkeypatch):
    """Override ``stub_services``'s SimpleNamespace stub of ``assemble`` so
    the real instruction-service builder runs and the captured request
    reflects the new task contract + speaker pseudonymization."""
    from core.runtime.ai import natural_language_stage as mod
    from utils.db import ai as ai_db

    async def _no_profile(_pid):
        return None

    monkeypatch.setattr(ai_db, "get_instruction_profile", _no_profile)
    monkeypatch.setattr(mod.ai_instruction_service, "assemble", _real_assemble)


def _use_real_conversation_buffer(monkeypatch):
    """Re-enable the in-process conversation buffer (``stub_services`` no-ops it)."""
    from core.runtime.ai import natural_language_stage as mod

    _real_reset_buffers()
    monkeypatch.setattr(
        mod.ai_conversation_service, "append", _real_conversation_append
    )


def _gather_recent_turns_returns(monkeypatch, turns):
    """Force ``ai_memory_service.gather_recent_turns`` to return ``turns``."""
    from services import ai_memory_service

    async def _gather(**_kw):
        return list(turns)

    monkeypatch.setattr(ai_memory_service, "gather_recent_turns", _gather)


@pytest.mark.asyncio
async def test_payload_frames_current_user_message_directly(
    monkeypatch,
    stub_services,
):
    """T1: payload contains the task contract and the triggering
    message in the ``current_user_message`` span. Recent turns are
    background-only and precede the current message."""
    from services import ai_gateway

    _use_real_assemble(monkeypatch)
    _gather_recent_turns_returns(
        monkeypatch,
        [
            SimpleNamespace(user_id=11, role="user", text="bystander one"),
            SimpleNamespace(user_id=22, role="user", text="bot-dev chatter"),
            SimpleNamespace(user_id=33, role="user", text="another aside"),
        ],
    )

    captured: dict = {}

    async def fake_execute(request):
        captured["request"] = request
        return _make_response(text="ok")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    stage = AINaturalLanguageStage()
    msg = _make_message_with_mention(f"<@{_BOT_ID}> are you there")
    await stage.process(_make_ctx_with_bot_id(msg))

    assert "request" in captured
    system_prompt = captured["request"].system_prompt
    payload = captured["request"].payload["text"]

    # Task contract is present and names the new spans.
    assert "Task contract" in system_prompt
    assert "current_user_message" in system_prompt
    assert "recent_channel_turns" in system_prompt

    # Triggering message is wrapped as current_user_message and contains
    # the user's actual question, with the bot mention stripped.
    assert "UNTRUSTED_DATA__current_user_message__BEGIN" in payload
    assert "are you there" in payload
    assert f"<@{_BOT_ID}>" not in payload
    assert "@SuperBot" not in payload  # no display-form leak either

    # Recent turns precede the current message in the payload.
    assert payload.index("recent_channel_turns") < payload.index("current_user_message")


@pytest.mark.asyncio
async def test_summarizable_context_does_not_select_summary(
    monkeypatch,
    stub_services,
):
    """T2: even with a verbose summarizable context, a normal question
    routes to GENERAL_NL_ANSWER (no summary task exists) and the
    contract instructs the model not to summarize unless asked."""
    from services import ai_gateway

    _use_real_assemble(monkeypatch)
    _gather_recent_turns_returns(
        monkeypatch,
        [
            SimpleNamespace(user_id=i, role="user", text=f"discussion item {i}")
            for i in range(11, 20)
        ],
    )

    captured: dict = {}

    async def fake_execute(request):
        captured["request"] = request
        return _make_response(text="response")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    # Drop the SimpleNamespace router stub so the real router runs.
    from core.runtime.ai import natural_language_stage as mod

    monkeypatch.setattr(mod.ai_task_router, "classify", _real_router_classify)

    stage = AINaturalLanguageStage()
    msg = _make_message_with_mention(f"<@{_BOT_ID}> what is the weather")
    await stage.process(_make_ctx_with_bot_id(msg))

    assert "request" in captured
    system_prompt = captured["request"].system_prompt
    # PR1: contract relaxes the no-summarize default; routing still
    # picks GENERAL_NL_ANSWER for a plain question regardless of the
    # surrounding context size.
    assert "Task contract" in system_prompt

    # The route the audit row carries reflects the real router's pick.
    assert stub_services[0]["task"] == AITask.GENERAL_NL_ANSWER.value


@pytest.mark.asyncio
async def test_outbound_reply_redacts_raw_snowflakes(
    monkeypatch,
    stub_services,
):
    """T4b: snowflakes in the model's reply are scrubbed before the
    text is sent to Discord."""
    from services import ai_gateway

    async def fake_execute(_request):
        return _make_response(
            text="Hi <@987654321098765432> see 123456789012345678",
        )

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    stage = AINaturalLanguageStage()
    msg = _make_message()
    await stage.process(_make_ctx(msg))

    msg.channel.send.assert_awaited_once()
    sent_text = msg.channel.send.call_args.args[0]
    assert "987654321098765432" not in sent_text
    assert "123456789012345678" not in sent_text


@pytest.mark.asyncio
async def test_outbound_redacted_text_is_what_lands_in_memory(
    monkeypatch, stub_services
):
    """T4c: the assistant reply written to conversation memory is the
    sanitized form, not the raw provider output."""
    from services import ai_gateway

    _use_real_conversation_buffer(monkeypatch)

    async def fake_execute(_request):
        return _make_response(text="ack <@987654321098765432>")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    stage = AINaturalLanguageStage()
    msg = _make_message()
    await stage.process(_make_ctx(msg))

    turns = _real_recent_turns(msg.guild.id, msg.channel.id)
    assistant_turns = [t for t in turns if t.role == "assistant"]
    assert len(assistant_turns) == 1
    assert "987654321098765432" not in assistant_turns[0].text


@pytest.mark.asyncio
async def test_triggering_message_appears_only_once_in_payload(
    monkeypatch,
    stub_services,
):
    """T5: a unique sentinel in the triggering message appears exactly
    once in the rendered payload (no duplication via recent_turns)."""
    from services import ai_gateway

    _use_real_assemble(monkeypatch)
    _use_real_conversation_buffer(monkeypatch)
    # Pre-seed unrelated bystander chatter so recent_turns is non-empty.
    _real_conversation_append(99, 1, user_id=11, role="user", text="prior unrelated 1")
    _real_conversation_append(99, 1, user_id=22, role="user", text="prior unrelated 2")

    captured: dict = {}

    async def fake_execute(request):
        captured["request"] = request
        return _make_response(text="ok")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    stage = AINaturalLanguageStage()
    msg = _make_message_with_mention(f"<@{_BOT_ID}> unique-sentinel-XYZ")
    await stage.process(_make_ctx_with_bot_id(msg))

    payload = captured["request"].payload["text"]
    assert payload.count("unique-sentinel-XYZ") == 1


@pytest.mark.asyncio
async def test_triggering_mention_recorded_exactly_once_after_success(
    monkeypatch,
    stub_services,
):
    """T6: after a successful reply, the triggering mention is in
    conversation memory exactly once, in its raw form."""
    from services import ai_gateway

    _use_real_conversation_buffer(monkeypatch)

    async def fake_execute(_request):
        return _make_response(text="ok")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    stage = AINaturalLanguageStage()
    msg_content = f"<@{_BOT_ID}> unique-sentinel-XYZ"
    msg = _make_message_with_mention(msg_content)
    await stage.process(_make_ctx_with_bot_id(msg))

    turns = _real_recent_turns(msg.guild.id, msg.channel.id)
    user_turns = [t for t in turns if t.role == "user"]
    matching = [t for t in user_turns if "unique-sentinel-XYZ" in t.text]
    assert len(matching) == 1
    # Memory stores the raw (unstripped) content.
    assert matching[0].text == msg_content


@pytest.mark.asyncio
async def test_triggering_mention_recorded_exactly_once_after_denied(monkeypatch):
    """T7: when the policy denies, the triggering mention is still
    captured in memory exactly once."""
    from core.runtime.ai import natural_language_stage as mod

    _real_reset_buffers()

    monkeypatch.setattr(
        mod.ai_permission_service,
        "snapshot",
        AsyncMock(return_value=SimpleNamespace(level=0, is_fresh_user=False)),
    )
    monkeypatch.setattr(
        mod.ai_natural_language_policy,
        "resolve",
        AsyncMock(
            return_value=PolicyDecision(
                allowed=False,
                reason_code=PolicyDenialReason.BELOW_MIN_LEVEL,
                effective_min_level=5,
                effective_cooldown=0,
                policy_snapshot_hash="h",
            ),
        ),
    )
    monkeypatch.setattr(
        mod.ai_decision_audit_service,
        "record",
        AsyncMock(return_value=1),
    )

    stage = AINaturalLanguageStage()
    msg_content = f"<@{_BOT_ID}> blocked-sentinel"
    msg = _make_message_with_mention(msg_content)
    await stage.process(_make_ctx_with_bot_id(msg))

    turns = _real_recent_turns(msg.guild.id, msg.channel.id)
    matching = [t for t in turns if "blocked-sentinel" in t.text]
    assert len(matching) == 1
    assert matching[0].text == msg_content


@pytest.mark.asyncio
async def test_multiple_bot_mentions_are_removed_from_current_user_message(
    monkeypatch,
    stub_services,
):
    """T11: every occurrence of the bot mention is stripped from the
    text the model sees, not just the first."""
    from services import ai_gateway

    _use_real_assemble(monkeypatch)

    captured: dict = {}

    async def fake_execute(request):
        captured["request"] = request
        return _make_response(text="ok")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    stage = AINaturalLanguageStage()
    msg = _make_message_with_mention(f"<@{_BOT_ID}> are you there <@{_BOT_ID}>")
    await stage.process(_make_ctx_with_bot_id(msg))

    payload = captured["request"].payload["text"]
    assert "are you there" in payload
    assert f"<@{_BOT_ID}>" not in payload


@pytest.mark.asyncio
async def test_empty_message_after_bot_mention_strip_does_not_call_provider(
    monkeypatch,
    stub_services,
):
    """T12: a bare-mention message ('<@BOT>' alone) is recorded to
    memory but never reaches the provider. Audit row is
    skipped/EMPTY_MESSAGE."""
    from services import ai_gateway

    _use_real_conversation_buffer(monkeypatch)
    called = {"v": False}

    async def fake_execute(_request):
        called["v"] = True
        return _make_response(text="should not be sent")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    stage = AINaturalLanguageStage()
    msg_content = f"<@{_BOT_ID}>"
    msg = _make_message_with_mention(msg_content)
    await stage.process(_make_ctx_with_bot_id(msg))

    assert called["v"] is False
    # Audit row is a clean skip.
    assert len(stub_services) == 1
    row = stub_services[0]
    assert row["decision"] == "skipped"
    assert row["reason_code"] is PolicyDenialReason.EMPTY_MESSAGE

    # Raw mention is still in memory for future context.
    turns = _real_recent_turns(msg.guild.id, msg.channel.id)
    matching = [t for t in turns if t.text == msg_content]
    assert len(matching) == 1


@pytest.mark.asyncio
async def test_cooldown_active_records_one_row_and_skips_gateway(
    monkeypatch,
    stub_services,
):
    """RC-11 guard: when the user is on cooldown, the stage records
    exactly one ``COOLDOWN_ACTIVE`` denial row and never calls the
    gateway.

    Pins the cooldown-ordering guarantee that the AI-guard coverage map
    left covered only indirectly — the other denied-path test denies via
    ``BELOW_MIN_LEVEL``, so "records exactly one ``COOLDOWN_ACTIVE`` row
    and never calls the provider" was previously unpinned."""
    from core.runtime.ai import natural_language_stage as mod
    from services import ai_gateway

    # Policy ALLOWS (stub_services default) so the flow reaches the
    # cooldown check; force the user to be on cooldown.
    monkeypatch.setattr(
        mod.ai_permission_service,
        "is_on_cooldown",
        lambda *a, **kw: True,
    )

    called = {"v": False}

    async def fake_execute(_request):
        called["v"] = True
        return _make_response(text="should not be sent")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    stage = AINaturalLanguageStage()
    msg = _make_message_with_mention(f"<@{_BOT_ID}> are you on cooldown")
    await stage.process(_make_ctx_with_bot_id(msg))

    # The gateway must never be reached on a cooldown denial.
    assert called["v"] is False
    # Exactly one audit row, and it is the cooldown denial.
    assert len(stub_services) == 1
    row = stub_services[0]
    assert row["decision"] == "denied"
    assert row["reason_code"] is PolicyDenialReason.COOLDOWN_ACTIVE


# ---------------------------------------------------------------------------
# PR1 — bot self-knowledge: gather call + accessible-channel gating
# ---------------------------------------------------------------------------


from services.ai_instruction_service import BotKnowledgeBlock  # noqa: E402


@pytest.mark.asyncio
async def test_stage_passes_bot_knowledge_to_assemble(monkeypatch, stub_services):
    """The stage hands ``bot_knowledge_blocks`` through to assemble()."""
    from core.runtime.ai import natural_language_stage as mod
    from services import ai_gateway, bot_knowledge_service

    captured: dict = {}

    async def fake_assemble(**kwargs):
        captured["kwargs"] = kwargs
        return SimpleNamespace(
            render_system_prompt=lambda: "sys",
            render_payload_text=lambda: "p",
            instruction_profile_ids=(),
        )

    monkeypatch.setattr(mod.ai_instruction_service, "assemble", fake_assemble)

    expected_block = BotKnowledgeBlock(kind="bot_command_catalog", text="X")
    monkeypatch.setattr(
        bot_knowledge_service,
        "gather",
        AsyncMock(return_value=(expected_block,)),
    )

    async def fake_execute(_request):
        return _make_response(text="ok")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    stage = AINaturalLanguageStage()
    msg = _make_message()
    await stage.process(_make_ctx(msg))

    assert captured["kwargs"]["bot_knowledge_blocks"] == (expected_block,)


@pytest.mark.asyncio
async def test_stage_continues_when_bot_knowledge_raises(monkeypatch, stub_services):
    """A raise inside the bot-knowledge gather must NOT poison the reply
    path — the stage assembles with empty blocks and audits ``replied``."""
    from core.runtime.ai import natural_language_stage as mod
    from services import ai_gateway, bot_knowledge_service

    captured: dict = {}

    async def fake_assemble(**kwargs):
        captured["kwargs"] = kwargs
        return SimpleNamespace(
            render_system_prompt=lambda: "sys",
            render_payload_text=lambda: "p",
            instruction_profile_ids=(),
        )

    monkeypatch.setattr(mod.ai_instruction_service, "assemble", fake_assemble)

    async def boom(**_kw):
        raise RuntimeError("gather broke")

    monkeypatch.setattr(bot_knowledge_service, "gather", boom)

    async def fake_execute(_request):
        return _make_response(text="ok")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    stage = AINaturalLanguageStage()
    msg = _make_message()
    await stage.process(_make_ctx(msg))

    assert captured["kwargs"]["bot_knowledge_blocks"] == ()
    assert len(stub_services) == 1
    assert stub_services[0]["decision"] == "replied"


@pytest.mark.asyncio
async def test_stage_skips_accessible_channels_for_non_audit_intent(
    monkeypatch,
    stub_services,
):
    """For a non-audit question, the stage must NOT call
    ``_accessible_channel_ids_for`` — large guilds otherwise pay a
    per-channel ``permissions_for`` cost on every AI mention."""
    from core.runtime.ai import natural_language_stage as mod
    from services import ai_gateway, bot_knowledge_service

    accessible_calls: list[object] = []

    def fake_accessible(member, guild):
        accessible_calls.append((member, guild))
        return frozenset({999})

    monkeypatch.setattr(mod, "_accessible_channel_ids_for", fake_accessible)

    gather_calls: list[dict] = []

    async def fake_gather(**kwargs):
        gather_calls.append(kwargs)
        return ()

    monkeypatch.setattr(bot_knowledge_service, "gather", fake_gather)

    async def fake_execute(_request):
        return _make_response(text="ok")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    stage = AINaturalLanguageStage()
    msg = _make_message()
    msg.content = "hello there"
    await stage.process(_make_ctx(msg))

    assert accessible_calls == []
    assert gather_calls[0]["accessible_channel_ids"] == frozenset()


@pytest.mark.asyncio
async def test_stage_computes_accessible_channels_for_audit_intent(
    monkeypatch,
    stub_services,
):
    """An audit-intent question DOES trigger the accessible-channel walk."""
    from core.runtime.ai import natural_language_stage as mod
    from services import ai_gateway, bot_knowledge_service

    accessible_calls: list[object] = []

    def fake_accessible(member, guild):
        accessible_calls.append((member, guild))
        return frozenset({777})

    monkeypatch.setattr(mod, "_accessible_channel_ids_for", fake_accessible)

    gather_calls: list[dict] = []

    async def fake_gather(**kwargs):
        gather_calls.append(kwargs)
        return ()

    monkeypatch.setattr(bot_knowledge_service, "gather", fake_gather)

    async def fake_execute(_request):
        return _make_response(text="ok")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    stage = AINaturalLanguageStage()
    msg = _make_message()
    msg.content = "why didn't you reply to me"
    await stage.process(_make_ctx(msg))

    assert len(accessible_calls) == 1
    assert gather_calls[0]["accessible_channel_ids"] == frozenset({777})


@pytest.mark.asyncio
async def test_accessible_channel_ids_for_filters_by_view_channel(monkeypatch):
    """The helper returns only channel ids the member can ``view_channel``."""
    from core.runtime.ai.natural_language_stage import _accessible_channel_ids_for

    member = MagicMock()
    visible = MagicMock()
    visible.id = 1
    hidden = MagicMock()
    hidden.id = 2

    def perms_for(m):
        # Visible channel grants view_channel=True; hidden does not.
        nonlocal_obj = SimpleNamespace
        # Member is the same for both — perms_for() differentiates by channel.
        return (
            nonlocal_obj(view_channel=True)
            if m is member
            else nonlocal_obj(view_channel=False)
        )

    visible.permissions_for = lambda m: SimpleNamespace(view_channel=True)
    hidden.permissions_for = lambda m: SimpleNamespace(view_channel=False)

    guild = SimpleNamespace(text_channels=[visible, hidden])
    assert _accessible_channel_ids_for(member, guild) == frozenset({1})


@pytest.mark.asyncio
async def test_accessible_channel_ids_for_dm_returns_empty(monkeypatch):
    """No guild → no channels → empty frozenset."""
    from core.runtime.ai.natural_language_stage import _accessible_channel_ids_for

    assert _accessible_channel_ids_for(MagicMock(), None) == frozenset()


# ---------------------------------------------------------------------------
# BTD6 live-state knowledge block wiring (PR-2 of the AI-data-access plan)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stage_appends_btd6_live_state_block_for_btd6_answer(
    monkeypatch, stub_services
):
    """When the task router returns BTD6_ANSWER and the text triggers
    the BTD6-anchor + state heuristic, the new gatherer's block must
    be present in `bot_knowledge_blocks` passed to `assemble()`."""
    from core.runtime.ai import natural_language_stage as mod
    from services import (
        ai_gateway,
        bot_knowledge_service,
        btd6_ai_knowledge_block_service,
    )

    captured: dict = {}

    async def fake_assemble(**kwargs):
        captured["kwargs"] = kwargs
        return SimpleNamespace(
            render_system_prompt=lambda: "sys",
            render_payload_text=lambda: "p",
            instruction_profile_ids=(),
        )

    monkeypatch.setattr(mod.ai_instruction_service, "assemble", fake_assemble)

    # Default fixture routes everything to GENERAL_NL_ANSWER — override.
    monkeypatch.setattr(
        mod.ai_task_router,
        "classify",
        lambda _text, **_kw: SimpleNamespace(
            task=AITask.BTD6_ANSWER,
            route="btd6.answer",
        ),
    )

    # Bot-knowledge gather still returns its own command-catalog block.
    monkeypatch.setattr(
        bot_knowledge_service,
        "gather",
        AsyncMock(
            return_value=(BotKnowledgeBlock(kind="bot_command_catalog", text="cmds"),)
        ),
    )

    btd6_block = BotKnowledgeBlock(kind="bot_btd6_live_state", text="boss event: X")
    monkeypatch.setattr(
        btd6_ai_knowledge_block_service,
        "gather_btd6_bot_knowledge_blocks",
        AsyncMock(return_value=(btd6_block,)),
    )

    async def fake_execute(_request):
        return _make_response(text="ok")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    stage = AINaturalLanguageStage()
    msg = _make_message()
    msg.content = "<@bot> what boss event is on right now?"
    await stage.process(_make_ctx(msg))

    blocks = captured["kwargs"]["bot_knowledge_blocks"]
    kinds = {b.kind for b in blocks}
    assert "bot_btd6_live_state" in kinds
    assert "bot_command_catalog" in kinds


@pytest.mark.asyncio
async def test_stage_skips_btd6_block_for_non_btd6_task(monkeypatch, stub_services):
    """For GENERAL_NL_ANSWER (the default) the BTD6 gatherer must NOT
    run — general-channel chatter shouldn't pay the lookup cost."""
    from core.runtime.ai import natural_language_stage as mod
    from services import (
        ai_gateway,
        bot_knowledge_service,
        btd6_ai_knowledge_block_service,
    )

    captured: dict = {}

    async def fake_assemble(**kwargs):
        captured["kwargs"] = kwargs
        return SimpleNamespace(
            render_system_prompt=lambda: "sys",
            render_payload_text=lambda: "p",
            instruction_profile_ids=(),
        )

    monkeypatch.setattr(mod.ai_instruction_service, "assemble", fake_assemble)
    monkeypatch.setattr(
        bot_knowledge_service,
        "gather",
        AsyncMock(return_value=()),
    )

    btd6_gather_mock = AsyncMock(return_value=())
    monkeypatch.setattr(
        btd6_ai_knowledge_block_service,
        "gather_btd6_bot_knowledge_blocks",
        btd6_gather_mock,
    )

    async def fake_execute(_request):
        return _make_response(text="ok")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    stage = AINaturalLanguageStage()
    msg = _make_message()
    msg.content = "<@bot> what's the weather like?"
    await stage.process(_make_ctx(msg))

    btd6_gather_mock.assert_not_awaited()
    assert captured["kwargs"]["bot_knowledge_blocks"] == ()


@pytest.mark.asyncio
async def test_stage_continues_when_btd6_gather_raises(monkeypatch, stub_services):
    """A raise inside the BTD6 gatherer must NOT poison the reply path."""
    from core.runtime.ai import natural_language_stage as mod
    from services import (
        ai_gateway,
        bot_knowledge_service,
        btd6_ai_knowledge_block_service,
    )

    captured: dict = {}

    async def fake_assemble(**kwargs):
        captured["kwargs"] = kwargs
        return SimpleNamespace(
            render_system_prompt=lambda: "sys",
            render_payload_text=lambda: "p",
            instruction_profile_ids=(),
        )

    monkeypatch.setattr(mod.ai_instruction_service, "assemble", fake_assemble)
    monkeypatch.setattr(
        mod.ai_task_router,
        "classify",
        lambda _text, **_kw: SimpleNamespace(
            task=AITask.BTD6_ANSWER, route="btd6.answer"
        ),
    )
    monkeypatch.setattr(
        bot_knowledge_service,
        "gather",
        AsyncMock(return_value=()),
    )

    async def boom(**_kw):
        raise RuntimeError("gather broke")

    monkeypatch.setattr(
        btd6_ai_knowledge_block_service,
        "gather_btd6_bot_knowledge_blocks",
        boom,
    )

    async def fake_execute(_request):
        return _make_response(text="ok")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    stage = AINaturalLanguageStage()
    msg = _make_message()
    msg.content = "<@bot> any current boss?"
    await stage.process(_make_ctx(msg))

    # Stage still finishes; blocks stay as whatever bot_knowledge_service produced.
    assert captured["kwargs"]["bot_knowledge_blocks"] == ()
    assert len(stub_services) == 1
    assert stub_services[0]["decision"] == "replied"


# ---------------------------------------------------------------------------
# BTD6 faithfulness guard (PR1)
# ---------------------------------------------------------------------------


def _route_btd6(monkeypatch):
    from core.runtime.ai import natural_language_stage as mod

    monkeypatch.setattr(
        mod.ai_task_router,
        "classify",
        lambda _t, **_kw: SimpleNamespace(task=AITask.BTD6_ANSWER, route="btd6.answer"),
    )


def _stub_facts(monkeypatch, facts: tuple[str, ...]):
    from core.runtime.ai import natural_language_stage as mod
    from core.runtime.ai.feature_facts import FeatureFactsResult

    monkeypatch.setattr(
        mod,
        "_gather_feature_facts",
        AsyncMock(return_value=FeatureFactsResult(facts=facts, render_context=None)),
    )


def _sent_text(msg) -> str:
    assert msg.channel.send.call_args is not None, "nothing was sent"
    args, _ = msg.channel.send.call_args
    return args[0] if args else ""


@pytest.mark.asyncio
async def test_btd6_roster_question_serves_deterministic_list(
    monkeypatch, stub_services
):
    """The five-heroes repro: the ungrounded roster never reaches the user, but a
    roster-LIST question is answered with the deterministic, COMPLETE roster (the
    model can't restate 17 costs verbatim, so the code-built list is the floor) —
    audited as replied, not refused."""
    from services import ai_gateway

    _route_btd6(monkeypatch)
    _stub_facts(monkeypatch, ())

    calls: list[int] = []

    async def fake_execute(_request):
        calls.append(1)
        return _make_response(
            text="BTD6 has five heroes: Quincy, Gwen, Obyn, Geraldo, Adora."
        )

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    msg = _make_message()
    msg.content = "<@bot> which heroes are in the game?"
    await AINaturalLanguageStage().process(_make_ctx(msg))

    sent = _sent_text(msg)
    assert "five heroes" not in sent  # the hallucination is NOT served
    assert "verified BTD6 data" not in sent  # NOT the refusal floor
    # The complete deterministic roster is served — including heroes the
    # hallucination omitted.
    assert "17" in sent
    assert "Benjamin" in sent and "Sauda" in sent and "Silas" in sent
    assert len(calls) == 2  # regenerate-once is still attempted first
    assert stub_services[-1]["decision"] == "replied"
    assert stub_services[-1]["reason_code"] is PolicyDenialReason.NONE


@pytest.mark.asyncio
async def test_btd6_regenerate_once_rescues(monkeypatch, stub_services):
    """First reply ungrounded, the constrained retry grounded → the grounded
    reply is served and the gateway was called twice."""
    from services import ai_gateway

    _route_btd6(monkeypatch)
    _stub_facts(monkeypatch, ("Quincy is a hero available from the start.",))

    texts = iter(["The Glaive Dominus is the best hero.", "Quincy is a starter hero."])

    async def fake_execute(_request):
        return _make_response(text=next(texts))

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    msg = _make_message()
    msg.content = "<@bot> tell me about Quincy"
    await AINaturalLanguageStage().process(_make_ctx(msg))

    assert _sent_text(msg) == "Quincy is a starter hero."
    assert stub_services[-1]["decision"] == "replied"


@pytest.mark.asyncio
async def test_btd6_grounded_answer_is_served(monkeypatch, stub_services):
    from services import ai_gateway

    _route_btd6(monkeypatch)
    _stub_facts(monkeypatch, ("Quincy is a hero available from the start.",))

    async def fake_execute(_request):
        return _make_response(text="Quincy is a starter hero.")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    msg = _make_message()
    msg.content = "<@bot> tell me about Quincy"
    await AINaturalLanguageStage().process(_make_ctx(msg))

    assert _sent_text(msg) == "Quincy is a starter hero."
    assert stub_services[-1]["decision"] == "replied"


@pytest.mark.asyncio
async def test_btd6_healthy_empty_reply_is_refused(monkeypatch, stub_services):
    """A healthy empty reply to a BTD6 question serves the refusal (denied /
    GROUNDING_FAILED), not silence."""
    from services import ai_gateway

    _route_btd6(monkeypatch)
    _stub_facts(monkeypatch, ())

    async def fake_execute(_request):
        return _make_response(text="", degraded=False, provider="deterministic")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    msg = _make_message()
    msg.content = "<@bot> what's the best tower?"
    await AINaturalLanguageStage().process(_make_ctx(msg))

    assert "verified BTD6 data" in _sent_text(msg)
    assert stub_services[-1]["decision"] == "denied"
    assert stub_services[-1]["reason_code"] is PolicyDenialReason.GROUNDING_FAILED


@pytest.mark.asyncio
async def test_btd6_degraded_reply_is_not_a_grounding_failure(
    monkeypatch, stub_services
):
    """A provider outage on a BTD6 question stays PROVIDER_UNAVAILABLE — it must
    never be misclassified as a grounding failure (C2)."""
    from services import ai_gateway

    _route_btd6(monkeypatch)
    _stub_facts(monkeypatch, ())

    async def fake_execute(_request):
        return _make_response(text=None, degraded=True, model="")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    msg = _make_message()
    msg.content = "<@bot> what's the best tower?"
    await AINaturalLanguageStage().process(_make_ctx(msg))

    assert stub_services[-1]["decision"] == "degraded"
    assert stub_services[-1]["reason_code"] is PolicyDenialReason.PROVIDER_UNAVAILABLE
    msg.channel.send.assert_not_called()


@pytest.mark.asyncio
async def test_btd6_verifier_crash_fails_closed(monkeypatch, stub_services):
    """If the verifier index raises, the guard fails CLOSED to the refusal."""
    from services import ai_gateway, btd6_grounding_service

    _route_btd6(monkeypatch)
    _stub_facts(monkeypatch, ())

    def _boom():
        raise RuntimeError("index broke")

    monkeypatch.setattr(btd6_grounding_service, "_name_index", _boom)

    async def fake_execute(_request):
        return _make_response(text="some otherwise-harmless reply")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    msg = _make_message()
    msg.content = "<@bot> tell me about towers"
    await AINaturalLanguageStage().process(_make_ctx(msg))

    assert "verified BTD6 data" in _sent_text(msg)
    assert stub_services[-1]["decision"] == "denied"


@pytest.mark.asyncio
async def test_general_ordinary_name_is_not_refused(monkeypatch, stub_services):
    """An ordinary general reply that shares a word with a hero name
    ("Benjamin") must be served unchanged — the general-path guard only fires on
    BTD6 context or a distinctive multi-word name."""
    from services import ai_gateway

    _stub_facts(monkeypatch, ())  # router stub already returns GENERAL_NL_ANSWER

    async def fake_execute(_request):
        return _make_response(
            text="Benjamin Franklin (1706-1790) was an American polymath."
        )

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    msg = _make_message()
    msg.content = "Who was Benjamin Franklin?"
    await AINaturalLanguageStage().process(_make_ctx(msg))

    assert "Benjamin Franklin" in _sent_text(msg)
    assert stub_services[-1]["decision"] == "replied"


@pytest.mark.asyncio
async def test_general_numeric_answer_is_not_refused(monkeypatch, stub_services):
    """Ordinary general numbers are never grounded (no BTD6 payload to ground
    against)."""
    from services import ai_gateway

    _stub_facts(monkeypatch, ())

    async def fake_execute(_request):
        return _make_response(text="There are 7 continents.")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    msg = _make_message()
    msg.content = "How many continents are there?"
    await AINaturalLanguageStage().process(_make_ctx(msg))

    assert _sent_text(msg) == "There are 7 continents."
    assert stub_services[-1]["decision"] == "replied"


@pytest.mark.asyncio
async def test_general_path_btd6_leak_is_refused(monkeypatch, stub_services):
    """A general reply that names a distinctive multi-word BTD6 entity it cannot
    ground is refused even though the router missed it. The prompt here is NOT
    itself BTD6-themed, so the floor is the generic guard copy — the
    version-stamped BTD6 refusal read as a non-sequitur on such questions
    (live miss 2026-06-11, "what is the last message you can see")."""
    from services import ai_gateway

    _stub_facts(monkeypatch, ())

    async def fake_execute(_request):
        return _make_response(text="The Apex Plasma Master costs 5000000.")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    msg = _make_message()
    msg.content = "tell me something cool"
    await AINaturalLanguageStage().process(_make_ctx(msg))

    assert "game details I can't verify" in _sent_text(msg)
    assert stub_services[-1]["decision"] == "denied"


@pytest.mark.asyncio
async def test_general_path_reply_may_quote_recent_conversation(
    monkeypatch,
    stub_services,
):
    """A general reply may name BTD6 entities the recent conversation already
    contains — the conversation floor is part of the guard's trusted haystack
    on the general path (live miss 2026-06-11: "what is the last message you
    can see" floored to the BTD6 refusal for quoting the prior Desperado
    turns). Entities the conversation never named still floor."""
    from services import ai_gateway

    _stub_facts(monkeypatch, ())
    _gather_recent_turns_returns(
        monkeypatch,
        [
            SimpleNamespace(
                user_id=11,
                role="assistant",
                text="A 0-4-1 Desperado costs $12,025 on Impoppable.",
            ),
        ],
    )

    async def fake_execute(_request):
        return _make_response(
            text="Your last message asked about the Desperado tower's cost.",
        )

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    msg = _make_message()
    msg.content = "what is the last message you can see"
    await AINaturalLanguageStage().process(_make_ctx(msg))

    assert "Desperado" in _sent_text(msg)
    assert stub_services[-1]["decision"] == "replied"


@pytest.mark.asyncio
async def test_general_path_btd6_themed_leak_keeps_version_refusal(
    monkeypatch,
    stub_services,
):
    """A BTD6-themed question whose general-path reply cannot be grounded
    still gets the version-stamped refusal (the strict copy is correct when
    the user actually asked about the game)."""
    from services import ai_gateway

    _stub_facts(monkeypatch, ())

    async def fake_execute(_request):
        return _make_response(text="The Apex Plasma Master costs 5000000.")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    msg = _make_message()
    # "banana" is a curated BTD6 context keyword — themed, but routed general
    # in this stub setup.
    msg.content = "tell me something cool about banana farming strategies"
    await AINaturalLanguageStage().process(_make_ctx(msg))

    assert "verified BTD6 data" in _sent_text(msg)
    assert stub_services[-1]["decision"] == "denied"


@pytest.mark.asyncio
async def test_ledger_captures_only_btd6_tool_results():
    """The faithfulness ledger captures approved BTD6 tool outputs (redacted)
    and never an unrelated server/user tool's numbers (C1)."""
    from core.runtime.ai.natural_language_stage import _wrap_handlers_for_ledger

    async def btd6_handler(_args):
        return {"cost": 48210, "name": "Dart Monkey"}

    async def server_handler(_args):
        return {"members": 235}

    ledger: list[str] = []
    wrapped = _wrap_handlers_for_ledger(
        {"btd6_lookup": btd6_handler, "get_server_overview": server_handler},
        frozenset({"btd6_lookup"}),
        ledger,
    )

    await wrapped["btd6_lookup"]({})
    await wrapped["get_server_overview"]({})

    assert len(ledger) == 1
    assert "48210" in ledger[0]
    assert "235" not in " ".join(ledger)
    # The non-BTD6 handler is returned untouched (not wrapped).
    assert wrapped["get_server_overview"] is server_handler


@pytest.mark.asyncio
async def test_btd6_roster_answer_is_served_when_grounded(monkeypatch, stub_services):
    """Regression: a roster question grounded by the hero-roster facts must be
    SERVED, not refused. In production it refused because heroes/towers had no
    roster auto-grounding, so the model's correct list read as ungrounded."""
    from services import ai_gateway

    _route_btd6(monkeypatch)
    _stub_facts(
        monkeypatch,
        (
            "[btd6_hero_roster] BTD6 has 17 heroes — the complete list: Quincy, "
            "Gwendolin, Striker Jones, Obyn Greenfoot, Captain Churchill, "
            "Benjamin, Ezili, Pat Fusty, Adora, Admiral Brickell, Etienne, "
            "Sauda, Psi, Geraldo, Corvus, Rosalia, Silas.",
        ),
    )

    async def fake_execute(_request):
        return _make_response(
            text=(
                "BTD6 has 17 heroes: Quincy, Gwendolin, Striker Jones, Obyn "
                "Greenfoot, Captain Churchill, Benjamin, Ezili, Pat Fusty, Adora, "
                "Admiral Brickell, Etienne, Sauda, Psi, Geraldo, Corvus, Rosalia, "
                "Silas."
            )
        )

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    msg = _make_message()
    msg.content = "<@bot> which heroes are in the game?"
    await AINaturalLanguageStage().process(_make_ctx(msg))

    sent = _sent_text(msg)
    assert "verified BTD6 data" not in sent  # NOT the refusal floor
    assert "Quincy" in sent and "Silas" in sent  # the real roster is served
    assert stub_services[-1]["decision"] == "replied"


@pytest.mark.asyncio
async def test_btd6_meta_question_serves_answerability_summary(
    monkeypatch, stub_services
):
    """ "What kind of things do you know about btd6" (live miss 2026-06-10):
    the model's capability description carries counts the ledger can't ground,
    so the guard blocks it — the floor must serve the deterministic
    answerability summary, never the version-stamped refusal (which answers
    the wrong question)."""
    from services import ai_gateway

    _route_btd6(monkeypatch)
    _stub_facts(monkeypatch, ())

    async def fake_execute(_request):
        return _make_response(
            text="I know about 99 towers, 88 heroes and 77 maps in BTD6."
        )

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    msg = _make_message()
    msg.content = "<@bot> what kind of things do you know about btd6"
    await AINaturalLanguageStage().process(_make_ctx(msg))

    sent = _sent_text(msg)
    assert "99 towers" not in sent  # the hallucinated counts never ship
    assert "verified BTD6 data" not in sent  # NOT the no-data refusal
    assert "What I know about BTD6" in sent  # the code-built summary is served
    assert "towers (25)" in sent
    assert stub_services[-1]["decision"] == "replied"
    assert stub_services[-1]["reason_code"] is PolicyDenialReason.NONE


# ---------------------------------------------------------------------------
# Project Moon (Limbus) faithfulness guard (Slice A follow-up b)
# ---------------------------------------------------------------------------


def _route_projmoon(monkeypatch):
    from core.runtime.ai import natural_language_stage as mod

    monkeypatch.setattr(
        mod.ai_task_router,
        "classify",
        lambda _t, **_kw: SimpleNamespace(
            task=AITask.PROJMOON_ANSWER, route="projmoon.answer"
        ),
    )


@pytest.mark.asyncio
async def test_projmoon_grounded_answer_is_served(monkeypatch, stub_services):
    """A Limbus reply that names only grounded Sinners is served unchanged."""
    from services import ai_gateway

    _route_projmoon(monkeypatch)
    _stub_facts(monkeypatch, ("Faust: a steady, cerebral Sinner.",))

    async def fake_execute(_request):
        return _make_response(text="Faust is one of the twelve Sinners.")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    msg = _make_message()
    msg.content = "<@bot> tell me about Faust in limbus"
    await AINaturalLanguageStage().process(_make_ctx(msg))

    assert _sent_text(msg) == "Faust is one of the twelve Sinners."
    assert stub_services[-1]["decision"] == "replied"


@pytest.mark.asyncio
async def test_projmoon_unsupported_name_is_refused(monkeypatch, stub_services):
    """A reply that drifts to an ungrounded Sinner is floored to the deterministic
    Limbus refusal after the constrained retry still misses."""
    from services import ai_gateway

    _route_projmoon(monkeypatch)
    _stub_facts(monkeypatch, ("Faust: a steady, cerebral Sinner.",))

    # Both the first reply and the retry name Heathcliff (never grounded).
    async def fake_execute(_request):
        return _make_response(text="Actually Heathcliff is the strongest Sinner.")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    msg = _make_message()
    msg.content = "<@bot> who is the best limbus sinner"
    await AINaturalLanguageStage().process(_make_ctx(msg))

    sent = _sent_text(msg)
    assert "Heathcliff" not in sent  # the ungrounded reply is NOT served
    assert "Project Moon" in sent  # the deterministic refusal floor
    assert stub_services[-1]["decision"] == "denied"
    assert stub_services[-1]["reason_code"] is PolicyDenialReason.GROUNDING_FAILED


@pytest.mark.asyncio
async def test_projmoon_regenerate_once_rescues(monkeypatch, stub_services):
    """First reply ungrounded, the constrained retry grounded → served."""
    from services import ai_gateway

    _route_projmoon(monkeypatch)
    _stub_facts(monkeypatch, ("Faust: a steady, cerebral Sinner.",))

    texts = iter(
        ["Heathcliff is the answer.", "Faust is a cerebral, steady Sinner."]
    )

    async def fake_execute(_request):
        return _make_response(text=next(texts))

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    msg = _make_message()
    msg.content = "<@bot> tell me about Faust"
    await AINaturalLanguageStage().process(_make_ctx(msg))

    assert _sent_text(msg) == "Faust is a cerebral, steady Sinner."
    assert stub_services[-1]["decision"] == "replied"


@pytest.mark.asyncio
async def test_projmoon_degraded_retry_stays_provider_unavailable(
    monkeypatch, stub_services
):
    """An ungrounded first reply whose retry degrades stays PROVIDER_UNAVAILABLE —
    a provider outage on retry must never be misclassified as a grounding miss."""
    from services import ai_gateway

    _route_projmoon(monkeypatch)
    _stub_facts(monkeypatch, ("Faust: a steady, cerebral Sinner.",))

    responses = iter(
        [
            _make_response(text="Heathcliff is the best.", degraded=False),
            _make_response(text=None, degraded=True, model=""),
        ]
    )

    async def fake_execute(_request):
        return next(responses)

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    msg = _make_message()
    msg.content = "<@bot> who is the best limbus sinner"
    await AINaturalLanguageStage().process(_make_ctx(msg))

    assert stub_services[-1]["decision"] == "degraded"
    assert stub_services[-1]["reason_code"] is PolicyDenialReason.PROVIDER_UNAVAILABLE


# ---------------------------------------------------------------------------
# BUG-0019 #2 — @everyone / @here must NOT read as a direct personal ping.
#
# discord.py's ``ClientUser.mentioned_in`` returns True on
# ``message.mention_everyone``, so a server-wide blast used to flip the
# ``mention_only`` policy gate open ("false personal ping" class). The fix
# computes ``is_mention`` as membership of the bot's own id in
# ``message.mentions`` only. These guards fail against the old behaviour.
# ---------------------------------------------------------------------------


def _mention_msg(*, mentions, mention_everyone=False):
    return SimpleNamespace(mentions=list(mentions), mention_everyone=mention_everyone)


def test_direct_bot_mention_is_a_personal_ping():
    bot = SimpleNamespace(id=_BOT_ID)
    msg = _mention_msg(mentions=[SimpleNamespace(id=_BOT_ID)])
    assert _is_direct_bot_mention(msg, bot) is True


def test_everyone_blast_is_not_a_personal_ping():
    """The regression: @everyone/@here (mention_everyone=True, empty
    ``mentions``) must NOT register as a direct mention even though
    discord.py's ``mentioned_in`` would have returned True."""
    bot = SimpleNamespace(id=_BOT_ID)
    msg = _mention_msg(mentions=[], mention_everyone=True)
    assert _is_direct_bot_mention(msg, bot) is False


def test_mention_of_another_user_or_bot_is_not_a_personal_ping():
    """A message pinging only some other user/bot does not ping us."""
    bot = SimpleNamespace(id=_BOT_ID)
    msg = _mention_msg(mentions=[SimpleNamespace(id=_BOT_ID + 999)])
    assert _is_direct_bot_mention(msg, bot) is False


def test_direct_mention_alongside_everyone_still_counts():
    """If we are genuinely in ``mentions`` it is a real ping, regardless
    of an accompanying @everyone."""
    bot = SimpleNamespace(id=_BOT_ID)
    msg = _mention_msg(
        mentions=[SimpleNamespace(id=_BOT_ID + 1), SimpleNamespace(id=_BOT_ID)],
        mention_everyone=True,
    )
    assert _is_direct_bot_mention(msg, bot) is True


def test_missing_bot_id_or_uniterable_mentions_is_false():
    """Defensive: no bot id, or a non-iterable ``mentions`` double, never
    raises — it yields False."""
    assert _is_direct_bot_mention(_mention_msg(mentions=[]), None) is False
    assert _is_direct_bot_mention(_mention_msg(mentions=[]), SimpleNamespace()) is False
    weird = SimpleNamespace(mentions=object(), mention_everyone=False)
    assert _is_direct_bot_mention(weird, SimpleNamespace(id=_BOT_ID)) is False
