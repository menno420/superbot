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
)
from core.runtime.message_pipeline import MessagePipelineContext
from services.ai_natural_language_policy import PolicyDecision

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
        lambda _text: SimpleNamespace(
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
    monkeypatch.setattr(response_renderer_registry, "render", AsyncMock(return_value=None))

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
        lambda _t: SimpleNamespace(task=AITask.VIDEO_DESCRIBE, route="video.describe"),
    )
    monkeypatch.setattr(
        mod,
        "_gather_feature_facts",
        AsyncMock(return_value=FeatureFactsResult(facts=("title: Test Video",), render_context=None)),
    )

    async def fake_execute(_request):
        return _make_response(text="video summary")

    monkeypatch.setattr(ai_gateway, "execute", fake_execute)

    stage = AINaturalLanguageStage()
    msg = _make_message()
    msg.channel.send = AsyncMock(side_effect=discord.HTTPException(MagicMock(), "send failed"))
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
    msg.channel.send = AsyncMock(side_effect=discord.HTTPException(MagicMock(), "send failed"))
    await stage.process(_make_ctx(msg))

    assert len(stub_services) == 1
    row = stub_services[0]
    assert row["decision"] == "errored"
    assert row["reason_code"] == "response_send_failed"
