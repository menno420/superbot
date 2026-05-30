"""Anthropic (Claude) provider adapter tests.

Mirrors the OpenAI tool-calling tests against the Anthropic Messages-API
shape, and pins the provider-neutral wiring:

* The adapter runs a bounded tool_use/tool_result loop and returns text.
* ``dispatch=None`` → no tools offered (single-shot), identical behaviour.
* The loop is bounded by ``_TOOL_HOP_LIMIT``.
* ``max_tokens`` is always sent (Anthropic requires it).
* The system prompt is sent as a cache-marked block (prompt caching).
* JSON mode unwraps the schema into ``output_config.format``.
* The gateway registers ``anthropic`` and routes tasks to Claude models
  (Sonnet for reasoning, Haiku for light explains).
"""

from __future__ import annotations

from types import SimpleNamespace

from core.runtime.ai.contracts import (
    AIRequest,
    AIRequestContext,
    AIResponseMode,
    AIScope,
    AITask,
    AIToolSpec,
)
from core.runtime.ai.gateway import AIGateway
from core.runtime.ai.providers.anthropic_provider import (
    _TOOL_HOP_LIMIT,
    AnthropicProvider,
)
from core.runtime.ai.routing import clear_overrides, default_model_for, resolve

# --- fakes -------------------------------------------------------------


def _text_block(text):
    return SimpleNamespace(type="text", text=text)


def _tool_use_block(block_id, name, tool_input):
    return SimpleNamespace(type="tool_use", id=block_id, name=name, input=tool_input)


def _response(blocks, *, stop_reason="end_turn"):
    return SimpleNamespace(content=blocks, stop_reason=stop_reason)


class _FakeMessages:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls: list[dict] = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        return self._responses.pop(0)


class _FakeAnthropic:
    def __init__(self, responses):
        self.messages = _FakeMessages(responses)


def _request(*names: str, mode=AIResponseMode.TEXT, response_schema=None) -> AIRequest:
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
        mode=mode,
        response_schema=response_schema,
        timeout_seconds=5.0,
        tools=specs,
    )


# --- provider-level loop ----------------------------------------------


async def test_provider_runs_tool_loop_and_returns_final_text():
    client = _FakeAnthropic(
        [
            _response(
                [_tool_use_block("tu1", "get_server_time", {})],
                stop_reason="tool_use",
            ),
            _response([_text_block("It is noon.")]),
        ],
    )
    provider = AnthropicProvider(client=client)
    calls: list[tuple[str, dict]] = []

    async def dispatch(name, args):
        calls.append((name, args))
        return '{"utc": "2026-05-29T12:00:00+00:00"}'

    text = await provider.execute(
        _request("get_server_time"),
        model="claude-haiku-4-5",
        dispatch=dispatch,
    )

    assert text == "It is noon."
    assert calls == [("get_server_time", {})]
    first = client.messages.calls[0]
    # Anthropic tool shape: flat name/description/input_schema (no "function").
    assert first["tools"][0]["input_schema"] == {"type": "object", "properties": {}}
    assert "max_tokens" in first  # required by the Messages API
    # The follow-up call carried the tool_result back as a user turn.
    second = client.messages.calls[1]["messages"]
    assert any(
        isinstance(m["content"], list)
        and any(
            isinstance(b, dict) and b.get("tool_use_id") == "tu1" for b in m["content"]
        )
        for m in second
        if isinstance(m.get("content"), list)
    )


async def test_provider_without_dispatch_never_offers_tools():
    client = _FakeAnthropic([_response([_text_block("plain answer")])])
    provider = AnthropicProvider(client=client)

    text = await provider.execute(
        _request("get_server_time"),
        model="claude-sonnet-4-6",
        dispatch=None,
    )

    assert text == "plain answer"
    assert len(client.messages.calls) == 1
    assert "tools" not in client.messages.calls[0]


async def test_provider_tool_loop_is_bounded():
    responses = [
        _response([_tool_use_block(f"tu{i}", "t", {})], stop_reason="tool_use")
        for i in range(_TOOL_HOP_LIMIT)
    ]
    responses.append(_response([_text_block("forced final")]))
    client = _FakeAnthropic(responses)
    provider = AnthropicProvider(client=client)

    hops = 0

    async def dispatch(name, args):
        nonlocal hops
        hops += 1
        return "{}"

    text = await provider.execute(
        _request("t"),
        model="claude-sonnet-4-6",
        dispatch=dispatch,
    )

    assert text == "forced final"
    assert hops == _TOOL_HOP_LIMIT
    assert "tools" not in client.messages.calls[-1]


async def test_system_prompt_is_sent_as_cache_marked_block():
    client = _FakeAnthropic([_response([_text_block("ok")])])
    provider = AnthropicProvider(client=client)

    await provider.execute(_request(), model="claude-sonnet-4-6")

    system = client.messages.calls[0]["system"]
    assert isinstance(system, list)
    assert system[0]["cache_control"] == {"type": "ephemeral"}
    assert system[0]["text"] == "system"


async def test_max_tokens_is_forwarded_from_request():
    client = _FakeAnthropic([_response([_text_block("ok")])])
    provider = AnthropicProvider(client=client)
    request = AIRequest(
        context=AIRequestContext(
            task=AITask.GENERAL_NL_ANSWER,
            scope=AIScope.USER,
            source="test",
        ),
        system_prompt="system",
        payload={"text": "hi"},
        mode=AIResponseMode.TEXT,
        max_output_tokens=1234,
    )

    await provider.execute(request, model="claude-sonnet-4-6")

    assert client.messages.calls[0]["max_tokens"] == 1234


async def test_json_mode_unwraps_schema_into_output_config():
    inner = {
        "type": "object",
        "properties": {"ok": {"type": "boolean"}},
        "additionalProperties": False,
    }
    client = _FakeAnthropic([_response([_text_block('{"ok": true}')])])
    provider = AnthropicProvider(client=client)

    request = _request(
        mode=AIResponseMode.JSON,
        # The neutral contract carries the OpenAI json_schema wrapper.
        response_schema={"name": "r", "schema": inner, "strict": True},
    )
    text = await provider.execute(request, model="claude-sonnet-4-6")

    assert text == '{"ok": true}'
    output_config = client.messages.calls[0]["output_config"]
    assert output_config["format"]["type"] == "json_schema"
    assert output_config["format"]["schema"] == inner  # wrapper unwrapped


# --- gateway registration + routing -----------------------------------


def test_gateway_registers_anthropic_by_default():
    gateway = AIGateway()
    provider = gateway.get_provider("anthropic")
    assert provider is not None
    assert provider.name == "anthropic"


def test_routing_picks_claude_models_for_anthropic(monkeypatch):
    clear_overrides()
    monkeypatch.setenv("AI_DEFAULT_PROVIDER", "anthropic")

    nl = resolve(AITask.GENERAL_NL_ANSWER)
    assert nl.provider == "anthropic"
    assert nl.model == "claude-haiku-4-5"  # live chat → fast tier

    proposed = resolve(AITask.SETTINGS_PROPOSE)
    assert proposed.model == "claude-sonnet-4-6"  # non-real-time → reasoning tier

    helped = resolve(AITask.HELP_ANSWER)
    assert helped.model == "claude-haiku-4-5"  # light tier

    # The helper is also usable directly.
    assert (
        default_model_for("anthropic", AITask.SETTINGS_PROPOSE) == "claude-sonnet-4-6"
    )
    assert default_model_for("openai", AITask.HELP_ANSWER) == "gpt-4o-mini"


async def test_gateway_end_to_end_tool_loop_via_anthropic(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "1")
    monkeypatch.setenv("AI_TOOLS_ENABLED", "1")
    monkeypatch.setenv("AI_DEFAULT_PROVIDER", "anthropic")
    clear_overrides()
    client = _FakeAnthropic(
        [
            _response(
                [_tool_use_block("tu1", "get_server_time", {})],
                stop_reason="tool_use",
            ),
            _response([_text_block("Done at noon.")]),
        ],
    )
    gateway = AIGateway(providers={"anthropic": AnthropicProvider(client=client)})
    seen: dict = {}

    async def time_handler(_args):
        seen["called"] = True
        return {"utc": "2026-05-29T12:00:00+00:00"}

    response = await gateway.execute(
        _request("get_server_time"),
        tool_handlers={"get_server_time": time_handler},
    )

    assert response.degraded is False
    assert response.provider == "anthropic"
    assert response.model == "claude-haiku-4-5"  # GENERAL_NL_ANSWER → fast tier
    assert response.text == "Done at noon."
    assert seen.get("called") is True
