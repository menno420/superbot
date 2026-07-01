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


def _is_open_category_call(expr: ast.expr) -> bool:
    """A delegation to ``hub_panels.open_category`` — a safe first await.

    The Layout-B category buttons are thin delegates: their whole body is
    ``await open_category(interaction, "<id>")``. ``open_category`` calls
    ``safe_defer`` before any follow-up work (pinned by
    :func:`test_open_category_defers_before_followup`), so a button that delegates
    to it satisfies the same defer-before-service-work contract.
    """
    return isinstance(expr, ast.Call) and (
        (isinstance(expr.func, ast.Name) and expr.func.id == "open_category")
        or (isinstance(expr.func, ast.Attribute) and expr.func.attr == "open_category")
    )


def _collect_awaits_in_source_order(node: ast.AST) -> list[ast.Await]:
    out: list[ast.Await] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Await):
            out.append(child)
    out.sort(key=lambda a: (a.lineno, a.col_offset))
    return out


# Modal-triggering callbacks are exempt: they MUST NOT call safe_defer
# before send_modal (the modal needs the initial response slot). The
# Ask button is the canonical example.
_MODAL_EXEMPT = frozenset(
    {
        ("BTD6PanelView", "ask_btn"),
    },
)


@pytest.mark.parametrize(
    "class_name,method_name",
    [
        ("BTD6AskModal", "on_submit"),
        # Category buttons — thin delegates to open_category (defers internally).
        ("BTD6PanelView", "events_btn"),
        ("BTD6PanelView", "units_btn"),
        ("BTD6PanelView", "rounds_btn"),
        ("BTD6PanelView", "maps_btn"),
        ("BTD6PanelView", "strategy_btn"),
        ("BTD6PanelView", "status_btn"),
        # Admin does its own safe_defer before the admin-panel build.
        ("BTD6PanelView", "admin_btn"),
    ],
)
def test_handler_defers_before_service_work(class_name, method_name):
    if (class_name, method_name) in _MODAL_EXEMPT:
        pytest.skip("modal-triggering callback — must not call safe_defer")

    node = _load_method(class_name, method_name)
    awaits = _collect_awaits_in_source_order(node)
    assert awaits, f"{class_name}.{method_name}: no awaits found"

    for await_node in awaits:
        if _is_interaction_response_send(await_node.value):
            continue
        assert _is_safe_defer_call(await_node.value) or _is_open_category_call(
            await_node.value
        ), (
            f"{class_name}.{method_name}: first DB/service await at line "
            f"{await_node.lineno} is not safe_defer() or open_category()."
        )
        return


_HUB_PATH = (
    Path(__file__).resolve().parents[3]
    / "disbot"
    / "views"
    / "btd6"
    / "hub_panels.py"
)


def test_open_category_defers_before_followup() -> None:
    """``open_category`` — the delegate every category button routes through —
    must ``safe_defer`` before its ``safe_followup`` (the guarantee the button
    delegates inherit)."""
    tree = ast.parse(_HUB_PATH.read_text())
    node = next(
        (
            n
            for n in ast.walk(tree)
            if isinstance(n, ast.AsyncFunctionDef) and n.name == "open_category"
        ),
        None,
    )
    assert node is not None, "open_category not found in hub_panels.py"
    awaits = _collect_awaits_in_source_order(node)
    defer_lines = [a.lineno for a in awaits if _is_safe_defer_call(a.value)]
    followup_lines = [
        a.lineno
        for a in awaits
        if isinstance(a.value, ast.Call)
        and isinstance(a.value.func, ast.Name)
        and a.value.func.id == "safe_followup"
    ]
    assert defer_lines, "open_category must call safe_defer"
    assert followup_lines, "open_category must call safe_followup"
    assert min(defer_lines) < min(
        followup_lines
    ), "open_category must safe_defer before its first safe_followup"


def test_ask_button_calls_send_modal_directly() -> None:
    """The Ask button must call ``send_modal`` as the initial response.

    Pin the modal exception so a future refactor doesn't accidentally
    insert a ``safe_defer`` before ``send_modal`` (which would break
    the modal).
    """
    import ast

    node = _load_method("BTD6PanelView", "ask_btn")
    # First await statement should be on send_modal, NOT on safe_defer.
    awaits = _collect_awaits_in_source_order(node)
    assert awaits, "ask_btn must await something"
    first = awaits[0]
    assert isinstance(first.value, ast.Call)
    func = first.value.func
    assert isinstance(func, ast.Attribute) and func.attr == "send_modal", (
        "ask_btn must call interaction.response.send_modal as the initial "
        "await; do not insert safe_defer ahead of it."
    )
