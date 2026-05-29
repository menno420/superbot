"""Read-only tool-calling tests — PR-1 foundation.

Pins the behaviour the tool-calling plan requires:

* The OpenAI adapter runs a bounded model<->tool loop when handed a
  dispatch callback and tool specs, and returns the final text.
* With ``dispatch=None`` the adapter never offers tools — identical to
  the legacy single-shot path (the inertness guarantee).
* The loop is bounded by ``_TOOL_HOP_LIMIT`` and forces a final,
  tool-free answer.
* The gateway only builds a dispatch when ``AI_TOOLS_ENABLED`` is on.
* The gateway's dispatch enforces the offered-tool allowlist, redacts
  tool output before it re-enters context, and converts tool faults
  into a JSON error string (never raising).
"""

from __future__ import annotations

import json
from types import SimpleNamespace

from core.runtime.ai import natural_language_stage as nls
from core.runtime.ai.contracts import (
    AIRequest,
    AIRequestContext,
    AIResponse,
    AIResponseMode,
    AIScope,
    AITask,
    AIToolSpec,
)
from core.runtime.ai.gateway import AIGateway
from core.runtime.ai.providers.openai_provider import _TOOL_HOP_LIMIT, OpenAIProvider
from services import ai_context_service

# --- fakes -------------------------------------------------------------


def _msg(*, content=None, tool_calls=None):
    return SimpleNamespace(content=content, tool_calls=tool_calls)


def _response(message):
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def _tool_call(call_id, name, arguments):
    return SimpleNamespace(
        id=call_id,
        type="function",
        function=SimpleNamespace(name=name, arguments=arguments),
    )


class _FakeCompletions:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls: list[dict] = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        return self._responses.pop(0)


class _FakeClient:
    def __init__(self, responses):
        self.chat = SimpleNamespace(completions=_FakeCompletions(responses))


class _CapturingProvider:
    """Records the ``dispatch`` it was handed; returns fixed text."""

    name = "openai"

    def __init__(self):
        self.dispatch = "unset"

    async def execute(self, request, *, model, dispatch=None):
        self.dispatch = dispatch
        return "ok"


def _tool_request(*names: str) -> AIRequest:
    specs = tuple(
        AIToolSpec(
            name=name,
            description=f"{name} description",
            parameters={"type": "object", "properties": {}},
        )
        for name in names
    )
    return AIRequest(
        context=AIRequestContext(
            task=AITask.GENERAL_NL_ANSWER,
            scope=AIScope.USER,
            source="test",
        ),
        system_prompt="system",
        payload={"text": "hi"},
        mode=AIResponseMode.TEXT,
        timeout_seconds=5.0,
        tools=specs,
    )


# --- provider-level loop ----------------------------------------------


async def test_provider_runs_tool_loop_and_returns_final_text():
    client = _FakeClient(
        [
            _response(_msg(tool_calls=[_tool_call("c1", "get_server_time", "{}")])),
            _response(_msg(content="It is noon.")),
        ],
    )
    provider = OpenAIProvider(client=client)
    calls: list[tuple[str, dict]] = []

    async def dispatch(name, args):
        calls.append((name, args))
        return '{"utc": "2026-05-29T12:00:00+00:00"}'

    text = await provider.execute(
        _tool_request("get_server_time"),
        model="m",
        dispatch=dispatch,
    )

    assert text == "It is noon."
    assert calls == [("get_server_time", {})]
    # First call offered tools; second call carried the tool result back.
    assert "tools" in client.chat.completions.calls[0]
    second = client.chat.completions.calls[1]["messages"]
    assert any(
        m.get("role") == "tool" and m.get("tool_call_id") == "c1" for m in second
    )


async def test_provider_without_dispatch_never_offers_tools():
    client = _FakeClient([_response(_msg(content="plain answer"))])
    provider = OpenAIProvider(client=client)

    text = await provider.execute(
        _tool_request("get_server_time"),
        model="m",
        dispatch=None,
    )

    assert text == "plain answer"
    assert len(client.chat.completions.calls) == 1
    assert "tools" not in client.chat.completions.calls[0]


async def test_provider_tool_loop_is_bounded():
    # Model keeps asking for a tool; after _TOOL_HOP_LIMIT hops the
    # adapter forces a tool-free final completion.
    responses = [
        _response(_msg(tool_calls=[_tool_call(f"c{i}", "t", "{}")]))
        for i in range(_TOOL_HOP_LIMIT)
    ]
    responses.append(_response(_msg(content="forced final")))
    client = _FakeClient(responses)
    provider = OpenAIProvider(client=client)

    hops = 0

    async def dispatch(name, args):
        nonlocal hops
        hops += 1
        return "{}"

    text = await provider.execute(_tool_request("t"), model="m", dispatch=dispatch)

    assert text == "forced final"
    assert hops == _TOOL_HOP_LIMIT
    assert "tools" not in client.chat.completions.calls[-1]


async def test_provider_forwards_max_output_tokens():
    # Regression: the adapter previously dropped request.max_output_tokens.
    client = _FakeClient([_response(_msg(content="ok"))])
    provider = OpenAIProvider(client=client)

    await provider.execute(_tool_request(), model="m", dispatch=None)

    assert client.chat.completions.calls[0]["max_tokens"] == 800


# --- gateway dispatch wiring ------------------------------------------


async def test_gateway_no_dispatch_when_tools_flag_off(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "1")
    monkeypatch.delenv("AI_TOOLS_ENABLED", raising=False)
    provider = _CapturingProvider()
    gateway = AIGateway(providers={"openai": provider})

    async def handler(_args):
        return {"ok": True}

    await gateway.execute(
        _tool_request("get_server_time"),
        provider_override=provider,
        tool_handlers={"get_server_time": handler},
    )

    assert provider.dispatch is None


async def test_gateway_dispatch_routes_redacts_and_isolates(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "1")
    monkeypatch.setenv("AI_TOOLS_ENABLED", "1")
    provider = _CapturingProvider()
    gateway = AIGateway(providers={"openai": provider})
    seen: dict = {}

    async def standing(args):
        seen["args"] = args
        return {"level": 7}

    async def leaky(_args):
        # A Discord-snowflake-like value must be scrubbed before the
        # result re-enters the model context.
        return {"trace_id": 123456789012345678}

    async def boom(_args):
        raise ValueError("kaboom")

    await gateway.execute(
        _tool_request("get_user_standing", "leaky", "boom"),
        provider_override=provider,
        tool_handlers={"get_user_standing": standing, "leaky": leaky, "boom": boom},
    )

    dispatch = provider.dispatch
    assert dispatch is not None

    # A clean result round-trips as JSON; arguments reach the handler.
    out = await dispatch("get_user_standing", {"x": 1})
    assert json.loads(out)["level"] == 7
    assert seen["args"] == {"x": 1}

    # A secret-looking value is redacted (the raw value never appears).
    leaked = await dispatch("leaky", {})
    assert "123456789012345678" not in leaked
    assert "redacted" in leaked

    # A tool not on the offered allowlist is refused.
    refused = await dispatch("not_offered", {})
    assert json.loads(refused)["error"] == "tool_not_available"

    # A handler that raises is isolated into an error string.
    failed = await dispatch("boom", {})
    assert json.loads(failed)["error"] == "tool_failed"


async def test_gateway_end_to_end_tool_loop(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "1")
    monkeypatch.setenv("AI_TOOLS_ENABLED", "1")
    monkeypatch.setenv("AI_DEFAULT_PROVIDER", "openai")
    client = _FakeClient(
        [
            _response(_msg(tool_calls=[_tool_call("c1", "get_server_time", "{}")])),
            _response(_msg(content="Done at noon.")),
        ],
    )
    gateway = AIGateway(providers={"openai": OpenAIProvider(client=client)})
    seen: dict = {}

    async def time_handler(_args):
        seen["called"] = True
        return {"utc": "2026-05-29T12:00:00+00:00"}

    response = await gateway.execute(
        _tool_request("get_server_time"),
        tool_handlers={"get_server_time": time_handler},
    )

    assert response.degraded is False
    assert response.text == "Done at noon."
    assert seen.get("called") is True


# --- live natural-language-stage wiring -------------------------------


def _fake_stack():
    return SimpleNamespace(
        render_system_prompt=lambda: "system",
        render_payload_text=lambda: "hi",
    )


async def test_stage_invoke_gateway_attaches_scoped_tools(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "1")
    monkeypatch.setenv("AI_TOOLS_ENABLED", "1")
    captured: dict = {}

    async def fake_execute(request, *, tool_handlers=None):
        captured["tools"] = request.tools
        captured["handlers"] = tool_handlers
        return AIResponse(
            task=request.context.task,
            provider="x",
            model="m",
            text="ok",
        )

    monkeypatch.setattr("services.ai_gateway.execute", fake_execute)
    built = ai_context_service.build(
        task=AITask.GENERAL_NL_ANSWER,
        guild_id=1,
        actor_id=2,
        channel_id=3,
        correlation_id="c",
        scope=AIScope.ADMIN,
    )

    response = await nls._invoke_gateway(_fake_stack(), built, object())

    assert response.text == "ok"
    names = {spec.name for spec in captured["tools"]}
    # Admin scope is offered the admin tools too.
    assert "get_user_standing" in names
    assert "get_guild_ai_config" in names
    assert captured["handlers"] is not None
    assert set(captured["handlers"]) == names


async def test_stage_invoke_gateway_no_tools_when_flag_off(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "1")
    monkeypatch.delenv("AI_TOOLS_ENABLED", raising=False)
    captured: dict = {}

    async def fake_execute(request, *, tool_handlers=None):
        captured["tools"] = request.tools
        captured["handlers"] = tool_handlers
        return AIResponse(
            task=request.context.task,
            provider="x",
            model="m",
            text="ok",
        )

    monkeypatch.setattr("services.ai_gateway.execute", fake_execute)
    built = ai_context_service.build(
        task=AITask.GENERAL_NL_ANSWER,
        guild_id=1,
        actor_id=2,
        channel_id=3,
        correlation_id="c",
        scope=AIScope.ADMIN,
    )

    await nls._invoke_gateway(_fake_stack(), built, object())

    assert captured["tools"] == ()
    assert captured["handlers"] is None
