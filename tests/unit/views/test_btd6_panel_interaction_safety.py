"""Interaction safety regression for BTD6 panel handlers.

The modal + status_btn + admin_btn handlers previously did async
DB/service work before the first interaction response. Each must
now call ``safe_defer`` before any DB/service await — early-return
``interaction.response.send_message`` guards are allowed.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_PANEL_PATH = (
    Path(__file__).resolve().parents[3] / "disbot" / "views" / "btd6" / "panel.py"
)


def _load_method(class_name: str, method_name: str) -> ast.AsyncFunctionDef:
    tree = ast.parse(_PANEL_PATH.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, ast.AsyncFunctionDef) and item.name == method_name:
                    return item
    raise AssertionError(f"{class_name}.{method_name} not found in {_PANEL_PATH}")


def _is_safe_defer_call(expr: ast.expr) -> bool:
    if isinstance(expr, ast.Call):
        func = expr.func
        if isinstance(func, ast.Name) and func.id == "safe_defer":
            return True
        if isinstance(func, ast.Attribute) and func.attr == "safe_defer":
            return True
    return False


def _is_interaction_response_send(expr: ast.expr) -> bool:
    if not isinstance(expr, ast.Call):
        return False
    func = expr.func
    return isinstance(func, ast.Attribute) and func.attr == "send_message"


def _collect_awaits_in_source_order(node: ast.AST) -> list[ast.Await]:
    out: list[ast.Await] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Await):
            out.append(child)
    out.sort(key=lambda a: (a.lineno, a.col_offset))
    return out


@pytest.mark.parametrize(
    "class_name,method_name",
    [
        ("BTD6AskModal", "on_submit"),
        ("BTD6PanelView", "status_btn"),
        ("BTD6PanelView", "admin_btn"),
    ],
)
def test_handler_defers_before_service_work(class_name, method_name):
    node = _load_method(class_name, method_name)
    awaits = _collect_awaits_in_source_order(node)
    assert awaits, f"{class_name}.{method_name}: no awaits found"

    for await_node in awaits:
        if _is_interaction_response_send(await_node.value):
            continue
        assert _is_safe_defer_call(await_node.value), (
            f"{class_name}.{method_name}: first DB/service await at line "
            f"{await_node.lineno} is not safe_defer()."
        )
        return
