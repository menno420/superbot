"""Provider-neutral tool-choice + budgets (orchestration plan §8, §11) — Phase 2.

Pins the compatibility-preserving contract: the default ``AIToolChoice``/``AIToolBudget``
reproduce the historical behaviour (AUTO choice, hop-bounded loop, no call/wall/result caps),
while a policy can force a tool, require a group, disable tools, or cap the loop — mapped
correctly onto BOTH the OpenAI and Anthropic adapters. The neutral fields also survive the
gateway's redaction seam.
"""

from __future__ import annotations

from types import SimpleNamespace

from core.runtime.ai.contracts import (
    AIRequest,
    AIRequestContext,
    AIResponseMode,
    AIScope,
    AITask,
    AIToolBudget,
    AIToolChoice,
    AIToolSpec,
    ToolRequirementMode,
)
from core.runtime.ai.gateway import AIGateway
from core.runtime.ai.providers import base
from core.runtime.ai.providers.anthropic_provider import (
    _TOOL_HOP_LIMIT as _ANTHROPIC_HOP_LIMIT,
)
from core.runtime.ai.providers.anthropic_provider import (
    AnthropicProvider,
    _anthropic_tool_choice,
)
from core.runtime.ai.providers.openai_provider import (
    _TOOL_HOP_LIMIT as _OPENAI_HOP_LIMIT,
)
from core.runtime.ai.providers.openai_provider import (
    OpenAIProvider,
    _openai_tool_choice,
)


def _request(*names: str, choice=None, budget=None) -> AIRequest:
    specs = tuple(
        AIToolSpec(name=n, description=f"{n} desc", parameters={"type": "object"})
        for n in names
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
        tool_choice=choice or AIToolChoice(),
        tool_budget=budget or AIToolBudget(),
    )


# ---------------------------------------------------------------------------
# Contract defaults — compatibility
# ---------------------------------------------------------------------------


def test_defaults_reproduce_historical_behaviour():
    assert AIToolChoice().mode is ToolRequirementMode.AUTO
    budget = AIToolBudget()
    assert budget.max_hops == 4
    assert budget.max_calls is None
    assert budget.max_wall_seconds is None
    assert budget.max_result_chars is None
    # The default hop budget must equal each adapter's historical constant, or the
    # "default == legacy" promise silently breaks.
    assert budget.max_hops == _OPENAI_HOP_LIMIT == _ANTHROPIC_HOP_LIMIT


# ---------------------------------------------------------------------------
# base.py shared helpers
# ---------------------------------------------------------------------------


def test_cap_tool_result_is_noop_without_a_cap():
    assert base.cap_tool_result("x" * 100, None) == "x" * 100


def test_cap_tool_result_truncates_over_cap():
    out = base.cap_tool_result("abcdefghij", 4)
    assert out.startswith("abcd")
    assert "truncated" in out
    assert len(out) > 4  # carries the marker


def test_tool_loop_state_default_is_hop_only():
    state = base.ToolLoopState(AIToolBudget())
    assert all(state.may_offer_tools(h) for h in range(4))
    assert state.may_offer_tools(4) is False  # the forced final hop


def test_tool_loop_state_enforces_call_cap():
    state = base.ToolLoopState(AIToolBudget(max_calls=2))
    assert state.may_offer_tools(0) is True
    state.record_call()
    state.record_call()
    assert state.may_offer_tools(1) is False  # 2 calls spent


def test_tool_loop_state_enforces_wall_cap():
    state = base.ToolLoopState(AIToolBudget(max_wall_seconds=1.0))
    assert state.may_offer_tools(0) is True
    state.started_monotonic -= 100.0  # pretend 100s elapsed
    assert state.may_offer_tools(0) is False


# ---------------------------------------------------------------------------
# Tool-choice mapping (covers all five modes incl. REQUIRED_GROUP, both adapters)
# ---------------------------------------------------------------------------


def test_openai_tool_choice_mapping_covers_every_mode():
    auto = AIToolChoice(ToolRequirementMode.AUTO)
    any_ = AIToolChoice(ToolRequirementMode.REQUIRED_ANY)
    group = AIToolChoice(
        ToolRequirementMode.REQUIRED_GROUP, group_name="btd6_grounding"
    )
    one = AIToolChoice(ToolRequirementMode.REQUIRED_TOOL, tool_name="btd6_round_cash")

    assert _openai_tool_choice(auto, 0) == "auto"
    assert _openai_tool_choice(any_, 0) == "required"
    assert _openai_tool_choice(group, 0) == "required"  # group narrowed by resolver
    assert _openai_tool_choice(one, 0) == {
        "type": "function",
        "function": {"name": "btd6_round_cash"},
    }
    # Every mode relaxes to auto after the first tool-offering hop.
    for choice in (any_, group, one):
        assert _openai_tool_choice(choice, 1) == "auto"


def test_anthropic_tool_choice_mapping_covers_every_mode():
    auto = AIToolChoice(ToolRequirementMode.AUTO)
    any_ = AIToolChoice(ToolRequirementMode.REQUIRED_ANY)
    group = AIToolChoice(ToolRequirementMode.REQUIRED_GROUP)
    one = AIToolChoice(ToolRequirementMode.REQUIRED_TOOL, tool_name="btd6_round_cash")

    assert _anthropic_tool_choice(auto, 0) == {"type": "auto"}
    assert _anthropic_tool_choice(any_, 0) == {"type": "any"}
    assert _anthropic_tool_choice(group, 0) == {"type": "any"}
    assert _anthropic_tool_choice(one, 0) == {"type": "tool", "name": "btd6_round_cash"}
    for choice in (any_, group, one):
        assert _anthropic_tool_choice(choice, 1) == {"type": "auto"}


# ---------------------------------------------------------------------------
# OpenAI adapter — end-to-end loop behaviour
# ---------------------------------------------------------------------------


def _oa_msg(*, content=None, tool_calls=None):
    return SimpleNamespace(content=content, tool_calls=tool_calls)


def _oa_response(message):
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def _oa_tool_call(call_id, name, arguments="{}"):
    return SimpleNamespace(
        id=call_id,
        type="function",
        function=SimpleNamespace(name=name, arguments=arguments),
    )


class _FakeOpenAI:
    def __init__(self, responses):
        completions = SimpleNamespace(create=self._create)
        self.chat = SimpleNamespace(completions=completions)
        self._responses = list(responses)
        self.calls: list[dict] = []

    async def _create(self, **kwargs):
        self.calls.append(kwargs)
        return self._responses.pop(0)


async def _noop_dispatch(_name, _args):
    return "{}"


async def test_openai_none_offers_no_tools():
    client = _FakeOpenAI([_oa_response(_oa_msg(content="plain"))])
    provider = OpenAIProvider(client=client)
    req = _request("get_server_time", choice=AIToolChoice(ToolRequirementMode.NONE))

    text = await provider.execute(req, model="m", dispatch=_noop_dispatch)

    assert text == "plain"
    assert "tools" not in client.calls[0]
    assert "tool_choice" not in client.calls[0]


async def test_openai_required_any_forces_then_relaxes():
    client = _FakeOpenAI(
        [
            _oa_response(_oa_msg(tool_calls=[_oa_tool_call("c1", "t")])),
            _oa_response(_oa_msg(content="final")),
        ],
    )
    provider = OpenAIProvider(client=client)
    req = _request("t", choice=AIToolChoice(ToolRequirementMode.REQUIRED_ANY))

    text = await provider.execute(req, model="m", dispatch=_noop_dispatch)

    assert text == "final"
    assert client.calls[0]["tool_choice"] == "required"  # hop 0 forces a tool
    assert client.calls[1]["tool_choice"] == "auto"  # hop 1 relaxes


async def test_openai_required_tool_forces_named_function():
    client = _FakeOpenAI(
        [
            _oa_response(_oa_msg(tool_calls=[_oa_tool_call("c1", "t")])),
            _oa_response(_oa_msg(content="final")),
        ],
    )
    provider = OpenAIProvider(client=client)
    req = _request(
        "t", choice=AIToolChoice(ToolRequirementMode.REQUIRED_TOOL, tool_name="t")
    )

    await provider.execute(req, model="m", dispatch=_noop_dispatch)
    assert client.calls[0]["tool_choice"] == {
        "type": "function",
        "function": {"name": "t"},
    }


async def test_openai_call_budget_stops_offering_tools():
    # Model would loop forever; max_calls=2 stops it after two dispatches.
    client = _FakeOpenAI(
        [
            _oa_response(_oa_msg(tool_calls=[_oa_tool_call("c1", "t")])),
            _oa_response(_oa_msg(tool_calls=[_oa_tool_call("c2", "t")])),
            _oa_response(_oa_msg(content="forced final")),
        ],
    )
    provider = OpenAIProvider(client=client)
    calls = 0

    async def dispatch(_n, _a):
        nonlocal calls
        calls += 1
        return "{}"

    req = _request("t", budget=AIToolBudget(max_calls=2))
    text = await provider.execute(req, model="m", dispatch=dispatch)

    assert text == "forced final"
    assert calls == 2
    assert "tools" not in client.calls[-1]  # the budget-exhausted hop offered none


async def test_openai_result_budget_caps_tool_output():
    client = _FakeOpenAI(
        [
            _oa_response(_oa_msg(tool_calls=[_oa_tool_call("c1", "t")])),
            _oa_response(_oa_msg(content="done")),
        ],
    )
    provider = OpenAIProvider(client=client)

    async def big(_n, _a):
        return "y" * 500

    req = _request("t", budget=AIToolBudget(max_result_chars=10))
    await provider.execute(req, model="m", dispatch=big)

    tool_msg = next(m for m in client.calls[1]["messages"] if m.get("role") == "tool")
    assert tool_msg["content"].startswith("y" * 10)
    assert "truncated" in tool_msg["content"]
    assert len(tool_msg["content"]) < 500


# ---------------------------------------------------------------------------
# Anthropic adapter — end-to-end loop behaviour
# ---------------------------------------------------------------------------


def _an_text(text):
    return SimpleNamespace(type="text", text=text)


def _an_tool_use(use_id, name, tool_input=None):
    return SimpleNamespace(
        type="tool_use", id=use_id, name=name, input=tool_input or {}
    )


def _an_response(*blocks):
    return SimpleNamespace(content=list(blocks))


class _FakeAnthropic:
    def __init__(self, responses):
        self.messages = SimpleNamespace(create=self._create)
        self._responses = list(responses)
        self.calls: list[dict] = []

    async def _create(self, **kwargs):
        self.calls.append(kwargs)
        return self._responses.pop(0)


async def test_anthropic_none_offers_no_tools():
    client = _FakeAnthropic([_an_response(_an_text("plain"))])
    provider = AnthropicProvider(client=client)
    req = _request("t", choice=AIToolChoice(ToolRequirementMode.NONE))

    text = await provider.execute(req, model="m", dispatch=_noop_dispatch)
    assert text == "plain"
    assert "tools" not in client.calls[0]


async def test_anthropic_required_any_forces_then_relaxes():
    client = _FakeAnthropic(
        [
            _an_response(_an_tool_use("u1", "t")),
            _an_response(_an_text("final")),
        ],
    )
    provider = AnthropicProvider(client=client)
    req = _request("t", choice=AIToolChoice(ToolRequirementMode.REQUIRED_ANY))

    text = await provider.execute(req, model="m", dispatch=_noop_dispatch)
    assert text == "final"
    assert client.calls[0]["tool_choice"] == {"type": "any"}
    assert client.calls[1]["tool_choice"] == {"type": "auto"}


async def test_anthropic_required_tool_forces_named():
    client = _FakeAnthropic(
        [
            _an_response(_an_tool_use("u1", "t")),
            _an_response(_an_text("final")),
        ],
    )
    provider = AnthropicProvider(client=client)
    req = _request(
        "t", choice=AIToolChoice(ToolRequirementMode.REQUIRED_TOOL, tool_name="t")
    )

    await provider.execute(req, model="m", dispatch=_noop_dispatch)
    assert client.calls[0]["tool_choice"] == {"type": "tool", "name": "t"}


async def test_anthropic_call_budget_stops_offering_tools():
    client = _FakeAnthropic(
        [
            _an_response(_an_tool_use("u1", "t")),
            _an_response(_an_tool_use("u2", "t")),
            _an_response(_an_text("forced final")),
        ],
    )
    provider = AnthropicProvider(client=client)
    calls = 0

    async def dispatch(_n, _a):
        nonlocal calls
        calls += 1
        return "{}"

    req = _request("t", budget=AIToolBudget(max_calls=2))
    text = await provider.execute(req, model="m", dispatch=dispatch)

    assert text == "forced final"
    assert calls == 2
    assert "tools" not in client.calls[-1]


# ---------------------------------------------------------------------------
# Gateway — the neutral fields survive the redaction seam
# ---------------------------------------------------------------------------


class _CaptureProvider:
    name = "openai"

    def __init__(self):
        self.request = None

    async def execute(self, request, *, model, dispatch=None):
        self.request = request
        return "ok"


async def test_gateway_redaction_preserves_tool_choice_and_budget(monkeypatch):
    monkeypatch.setenv("AI_ENABLED", "1")
    monkeypatch.setenv("AI_TOOLS_ENABLED", "1")
    provider = _CaptureProvider()
    gateway = AIGateway(providers={"openai": provider})
    req = _request(
        "get_server_time",
        choice=AIToolChoice(ToolRequirementMode.REQUIRED_ANY, group_name="g"),
        budget=AIToolBudget(max_calls=3, max_result_chars=99),
    )

    async def handler(_args):
        return {"ok": True}

    await gateway.execute(
        req,
        provider_override=provider,
        tool_handlers={"get_server_time": handler},
    )

    # The redacted request handed to the provider must still carry the policy
    # (regression guard for the field-by-field reconstruction that used to drop new fields).
    seen = provider.request
    assert seen is not None
    assert seen.tool_choice.mode is ToolRequirementMode.REQUIRED_ANY
    assert seen.tool_choice.group_name == "g"
    assert seen.tool_budget.max_calls == 3
    assert seen.tool_budget.max_result_chars == 99
