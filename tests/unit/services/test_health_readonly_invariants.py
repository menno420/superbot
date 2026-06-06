"""Pin: services.health_snapshot_service never mutates state.

The health aggregator is a read model — it composes existing
observability seams and must not call any registry-mutating, lifecycle-
mutating, task-spawning, recorder-writing, or DB-writing seam.

Enforced by AST scan (no runtime import of the module under test), so it
runs without DB / Discord setup.  Mirrors
``tests/unit/services/test_ai_readonly_invariants.py``.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SUBJECT = _REPO_ROOT / "disbot" / "services" / "health_snapshot_service.py"

# (receiver, attribute) call pairs that would mean the aggregator is
# writing state.  Keyed on the receiver identifier as it appears in the
# module (matching this codebase's ``from x import y; y.foo()`` style and
# the aliases the service uses: ``so`` for startup_outcome, etc.).
_FORBIDDEN_CALLS: frozenset[tuple[str, str]] = frozenset(
    {
        ("diagnostics_service", "register"),
        ("diagnostics_service", "unregister"),
        ("diagnostics_service", "_reset_for_tests"),
        ("lifecycle", "set_phase"),
        ("lifecycle", "request_shutdown"),
        ("lifecycle", "request_restart"),
        ("tasks", "spawn"),
        ("tasks", "cancel_all"),
        ("tasks", "cancel_by_prefix"),
        ("so", "record_success"),
        ("so", "record_failure"),
        ("so", "record_phase"),
        ("so", "reset_for_tests"),
        ("startup_outcome", "record_success"),
        ("startup_outcome", "record_failure"),
        ("pool", "execute"),
        ("db", "execute"),
        ("db", "set_setting"),
        ("db_health", "execute"),
    },
)


def _walk_qualified_calls(tree: ast.AST) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            pairs.append((func.value.id, func.attr))
    return pairs


def test_no_forbidden_mutation_calls() -> None:
    tree = ast.parse(_SUBJECT.read_text(encoding="utf-8"))
    called = set(_walk_qualified_calls(tree))
    offenders = called & _FORBIDDEN_CALLS
    assert not offenders, (
        f"health_snapshot_service invokes forbidden mutation calls: "
        f"{sorted(offenders)}. The aggregator is read-only."
    )


def test_subject_exists() -> None:
    assert _SUBJECT.exists(), (
        "health_snapshot_service.py moved — update "
        "tests/unit/services/test_health_readonly_invariants.py."
    )
