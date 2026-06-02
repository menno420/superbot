"""Interaction safety regression: BTD6 slash handlers defer before
async work.

Each handler must call ``safe_defer`` before any other ``await``
that hits DB / service work. Early-return guards that only do
``await interaction.response.send_message(...)`` are fine — they
respond within the 3-second window without deferring.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_DISBOT_COGS = Path(__file__).resolve().parents[3] / "disbot" / "cogs"

# The BTD6 slash surface is split across the mother cog + sibling cogs; a
# handler may live in any of them, so the AST scan sweeps all four.
_COG_PATHS = (
    _DISBOT_COGS / "btd6_cog.py",
    _DISBOT_COGS / "btd6_reference_cog.py",
    _DISBOT_COGS / "btd6_events_cog.py",
    _DISBOT_COGS / "btd6_strategy_cog.py",
)

# Handlers that previously did async DB/service work before the first
# response. ``btd6_diagnostics_slash`` and ``btd6_test_intent_slash``
# build their embeds synchronously and stay on ``interaction.response.
# send_message`` directly — confirmed sync-only path.
_HANDLERS_REQUIRING_SAFE_DEFER = (
    "btd6_ask_slash",
    "btd6_hero_slash",
    "btd6_strategy_audit_slash",
    "btd6_grounding_slash",
    "btd6menu_slash",
    "btd6_strategies_slash",
    "btd6_sources_slash",
)


def _load_function_node(name: str) -> ast.AsyncFunctionDef:
    for path in _COG_PATHS:
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == name:
                return node
    raise AssertionError(
        f"handler {name} not found in {[p.name for p in _COG_PATHS]}",
    )


def _is_safe_defer_call(expr: ast.expr) -> bool:
    if isinstance(expr, ast.Call):
        func = expr.func
        if isinstance(func, ast.Name) and func.id == "safe_defer":
            return True
        if isinstance(func, ast.Attribute) and func.attr == "safe_defer":
            return True
    return False


def _is_interaction_response_send(expr: ast.expr) -> bool:
    """``interaction.response.send_message(...)`` — safe early-return guard."""
    if not isinstance(expr, ast.Call):
        return False
    func = expr.func
    if not isinstance(func, ast.Attribute):
        return False
    return func.attr == "send_message"


def _is_interaction_response_send_modal(expr: ast.expr) -> bool:
    """``interaction.response.send_modal(...)`` — synchronous response."""
    if not isinstance(expr, ast.Call):
        return False
    func = expr.func
    return isinstance(func, ast.Attribute) and func.attr == "send_modal"


def _collect_awaits_in_source_order(node: ast.AST) -> list[ast.Await]:
    """Return awaits in source-line order (ast.walk is BFS, not source order)."""
    out: list[ast.Await] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Await):
            out.append(child)
    out.sort(key=lambda a: (a.lineno, a.col_offset))
    return out


@pytest.mark.parametrize("handler_name", _HANDLERS_REQUIRING_SAFE_DEFER)
def test_handler_defers_before_service_work(handler_name):
    node = _load_function_node(handler_name)
    awaits = _collect_awaits_in_source_order(node)
    assert awaits, f"{handler_name}: no awaits found"

    # Skip early-return guards (interaction.response.send_message /
    # send_modal) — those respond in the 3-second window without a defer.
    for await_node in awaits:
        if _is_interaction_response_send(await_node.value):
            continue
        if _is_interaction_response_send_modal(await_node.value):
            continue
        # First non-guard await — must be safe_defer.
        assert _is_safe_defer_call(await_node.value), (
            f"{handler_name}: first DB/service await at line {await_node.lineno} "
            f"is not safe_defer(). Add `if not await safe_defer(...): return` "
            f"before any builder/service call."
        )
        return
    # All awaits were early-return guards — safe by construction.


def test_handler_list_covers_known_unsafe_set():
    assert len(_HANDLERS_REQUIRING_SAFE_DEFER) == 7
