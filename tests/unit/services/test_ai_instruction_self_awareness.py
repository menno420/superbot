"""The task contract must route self-awareness questions to the Phase 3 tools.

Answerability Phase 3 (Q-0047) registered three read-only self-awareness tools
over the #616 introspection read model: ``get_ai_tool_catalog`` ("what can you
do here?"), ``get_ai_policy_explanation`` ("why didn't you reply?"), and
``btd6_answerability`` ("what BTD6 data do you know?"). Without an instruction
clause the model answers those meta-questions from guesswork — exactly the
failure class the data-self-knowledge clause was added for. These tests pin
the advertising clause so it can't silently drop, and pin that it advertises
only tools that actually exist in the registry.
"""

from __future__ import annotations

from services import ai_instruction_service as instr
from services import ai_tools

_SELF_AWARENESS_TOOLS = (
    "get_ai_tool_catalog",
    "get_ai_policy_explanation",
    "btd6_answerability",
)


def test_task_contract_advertises_the_three_self_awareness_tools():
    tc = instr._TASK_CONTRACT
    for name in _SELF_AWARENESS_TOOLS:
        assert f"'{name}'" in tc, name


def test_task_contract_routes_the_three_meta_questions():
    tc = instr._TASK_CONTRACT.lower()
    assert "what can you do (here)?" in tc
    assert "why didn't you reply?" in tc
    assert "what btd6 data do you know?" in tc


def test_task_contract_keeps_tier_filtering_honest():
    """The clause must tell the model the catalog is pre-filtered — never to
    name tools beyond the returned list (audience tiering is construction-time,
    not prompt-enforced, but the prose must not invite leakage either)."""
    tc = instr._TASK_CONTRACT
    assert "already filtered to the asker's permission tier" in tc
    assert "never name a tool it does not return" in tc


def test_advertised_tools_exist_in_the_registry():
    """Advertising a tool that isn't registered teaches the model to call a
    ghost; the clause and the registry must not drift apart."""
    specs = ai_tools.all_tool_specs()
    for name in _SELF_AWARENESS_TOOLS:
        assert name in specs, name
