"""Live wiring: the orchestration policy reaches build_registry + AIRequest.

Pins that ``natural_language_stage._invoke_gateway`` resolves the orchestration
profile and threads it onto the tool registry (toolset narrowing) and the
request (tool_choice / tool_budget) — with the default decision reproducing the
historical behaviour (no narrowing, AUTO, default budget).
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from core.runtime.ai import natural_language_stage as nls  # noqa: E402
from core.runtime.ai.contracts import (  # noqa: E402
    AIResponse,
    AIScope,
    AITask,
    AIToolBudget,
    AIToolChoice,
    ToolRequirementMode,
)
from services import ai_context_service  # noqa: E402
from services import ai_orchestration_policy as orch  # noqa: E402


def _fake_stack(user_message: str = "hi"):
    return SimpleNamespace(
        render_system_prompt=lambda: "system",
        render_payload_text=lambda: "hi",
        user_message=user_message,
    )


def _built():
    return ai_context_service.build(
        task=AITask.GENERAL_NL_ANSWER,
        guild_id=1,
        actor_id=2,
        channel_id=3,
        correlation_id="c",
        scope=AIScope.ADMIN,
    )


def _wire(monkeypatch, decision):
    """Stub resolve + build_registry + execute; return the capture dict."""
    captured: dict = {}

    async def fake_resolve(ctx, *, dry_run=False):
        captured["ctx"] = ctx
        return decision

    def fake_build_registry(**kwargs):
        captured["build_kwargs"] = kwargs
        # Mimic select_tools narrowing: an empty enabled set offers nothing.
        if kwargs.get("enabled_toolsets") == ():
            specs: tuple = ()
        else:
            specs = (SimpleNamespace(name="btd6_lookup"),)
        handlers = {s.name: (lambda a: None) for s in specs}
        return SimpleNamespace(specs=specs, handlers=handlers)

    async def fake_execute(request, *, tool_handlers=None):
        captured["request"] = request
        captured["handlers"] = tool_handlers
        return AIResponse(task=request.context.task, provider="x", model="m", text="ok")

    monkeypatch.setenv("AI_ENABLED", "1")
    monkeypatch.setenv("AI_TOOLS_ENABLED", "1")
    monkeypatch.setattr(orch, "resolve", fake_resolve)
    monkeypatch.setattr("services.ai_tools.build_registry", fake_build_registry)
    monkeypatch.setattr("services.ai_gateway.execute", fake_execute)
    return captured


_DEFAULT = orch.OrchestrationDecision(
    profile_key="compatible_default",
    source="default",
    enabled_toolsets=None,
    disabled_tools=(),
    tool_choice=AIToolChoice(),
    tool_budget=AIToolBudget(),
    workflow="direct_or_tool",
    answer_contract="concise_fact",
)


async def test_default_decision_is_byte_identical(monkeypatch) -> None:
    captured = _wire(monkeypatch, _DEFAULT)
    await nls._invoke_gateway(_fake_stack(), _built(), object())

    # build_registry got the compatibility defaults (no narrowing).
    assert captured["build_kwargs"]["enabled_toolsets"] is None
    assert captured["build_kwargs"]["disabled_tools"] == ()
    # Request carries the default AUTO choice + default budget.
    assert captured["request"].tool_choice.mode is ToolRequirementMode.AUTO
    assert captured["request"].tool_budget == AIToolBudget()
    assert {s.name for s in captured["request"].tools} == {"btd6_lookup"}


async def test_narrowing_decision_threads_through(monkeypatch) -> None:
    decision = orch.OrchestrationDecision(
        profile_key="btd6_grounded",
        source="channel",
        enabled_toolsets=("btd6_reference", "btd6_rounds"),
        disabled_tools=("recent_audit",),
        tool_choice=AIToolChoice(mode=ToolRequirementMode.REQUIRED_ANY),
        tool_budget=AIToolBudget(max_hops=3, max_calls=4),
        workflow="analyze_execute_verify",
        answer_contract="concise_fact",
    )
    captured = _wire(monkeypatch, decision)
    await nls._invoke_gateway(_fake_stack(), _built(), object())

    assert captured["build_kwargs"]["enabled_toolsets"] == (
        "btd6_reference",
        "btd6_rounds",
    )
    assert captured["build_kwargs"]["disabled_tools"] == ("recent_audit",)
    assert captured["request"].tool_choice.mode is ToolRequirementMode.REQUIRED_ANY
    assert captured["request"].tool_budget.max_calls == 4


async def test_no_tools_decision_takes_single_shot_path(monkeypatch) -> None:
    decision = orch.OrchestrationDecision(
        profile_key="no_tools",
        source="channel",
        enabled_toolsets=(),
        disabled_tools=(),
        tool_choice=AIToolChoice(mode=ToolRequirementMode.NONE),
        tool_budget=AIToolBudget(),
        workflow="direct_answer",
        answer_contract="concise_fact",
    )
    captured = _wire(monkeypatch, decision)
    await nls._invoke_gateway(_fake_stack(), _built(), object())

    # No tools offered → identical legacy single-shot path (handlers None).
    assert captured["request"].tools == ()
    assert captured["handlers"] is None
    assert captured["request"].tool_choice.mode is ToolRequirementMode.NONE


# ---------------------------------------------------------------------------
# Phase 4 MVP — the round-cash workflow is profile-gated (Q-0046)
# ---------------------------------------------------------------------------

_ROUND_CASH_QUESTION = "how much cash from round 50 to 60?"

_AEV = orch.OrchestrationDecision(
    profile_key="btd6_grounded",
    source="channel",
    enabled_toolsets=("btd6_reference", "btd6_rounds"),
    disabled_tools=(),
    tool_choice=AIToolChoice(),
    tool_budget=AIToolBudget(max_hops=3, max_calls=4),
    workflow="analyze_execute_verify",
    answer_contract="concise_fact",
)


async def test_direct_or_tool_decision_never_runs_workflow(
    monkeypatch,
) -> None:
    """A round-cash question under a ``direct_or_tool`` decision must produce
    the exact historical request — the workflow is gated on the resolved
    decision's ``workflow`` label, not on the question text. (The *default
    preset* declares ``analyze_execute_verify`` since the 2026-06-11 BUG-0001
    recurrence — this pin now covers the label mechanism itself, e.g. a
    decision resolved from an older persisted profile.)"""
    captured = _wire(monkeypatch, _DEFAULT)
    ledger: list[str] = []
    await nls._invoke_gateway(
        _fake_stack(_ROUND_CASH_QUESTION), _built(), object(), ledger=ledger
    )

    assert captured["request"].system_prompt == "system"
    assert ledger == []


async def test_workflow_engages_under_analyze_execute_verify(monkeypatch) -> None:
    captured = _wire(monkeypatch, _AEV)
    ledger: list[str] = []
    await nls._invoke_gateway(
        _fake_stack(_ROUND_CASH_QUESTION), _built(), object(), ledger=ledger
    )

    prompt = captured["request"].system_prompt
    assert prompt.startswith("system\n\n")
    assert "Deterministic round-cash workflow result" in prompt
    assert "19,840.00" in prompt  # the Q-0043 inclusive anchor
    # The evidence also grounds the faithfulness ledger.
    assert len(ledger) == 1 and "19840" in ledger[0].replace(",", "")


async def test_workflow_silent_for_non_matching_text(monkeypatch) -> None:
    """Under the workflow-selecting profile, a non-round-cash question leaves
    the request byte-identical (the conservative planner stays out)."""
    captured = _wire(monkeypatch, _AEV)
    ledger: list[str] = []
    await nls._invoke_gateway(
        _fake_stack("which heroes are best?"), _built(), object(), ledger=ledger
    )

    assert captured["request"].system_prompt == "system"
    assert ledger == []


async def test_workflow_ledger_entry_not_duplicated_on_retry(monkeypatch) -> None:
    """The regenerate-once grounding retry reuses the same ledger — the
    deterministic evidence entry must appear exactly once."""
    captured = _wire(monkeypatch, _AEV)
    ledger: list[str] = []
    stack = _fake_stack(_ROUND_CASH_QUESTION)
    await nls._invoke_gateway(stack, _built(), object(), ledger=ledger)
    await nls._invoke_gateway(
        stack, _built(), object(), ledger=ledger, grounding_constraint="no"
    )

    assert len(ledger) == 1
    # The retry still carries the workflow block + the constraint.
    assert (
        "Deterministic round-cash workflow result" in captured["request"].system_prompt
    )
    assert captured["request"].system_prompt.endswith("no")


async def test_workflow_fault_degrades_to_unchanged_request(monkeypatch) -> None:
    """A workflow crash must never break the reply — the request degrades to
    the exact no-workflow shape."""
    captured = _wire(monkeypatch, _AEV)

    def boom(_text):
        raise RuntimeError("workflow exploded")

    monkeypatch.setattr("services.ai_round_cash_workflow.run", boom)
    ledger: list[str] = []
    await nls._invoke_gateway(
        _fake_stack(_ROUND_CASH_QUESTION), _built(), object(), ledger=ledger
    )

    assert captured["request"].system_prompt == "system"
    assert ledger == []
