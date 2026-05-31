"""Invariant tests for the platform consistency typed readiness contract.

Pins two structural constraints introduced in PR-01a:

1. ``_LABEL_TO_KIND`` covers every label used by the
   ``collect_report`` orchestrator.  Adding a new collector requires
   adding its label/kind pair here at the same time.

2. ``READINESS_KINDS`` is exhaustive over ``ReadinessKind`` and
   matches the orchestrator's collector tuple order.  A missing kind
   would silently lose its identity at runtime.

The runtime stamping behaviour (every section in a collected report
carries a typed kind) is pinned by
``tests/unit/services/test_platform_consistency.py``.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from services import platform_consistency as pc

_REPO_ROOT = Path(__file__).resolve().parents[3]
_MODULE_PATH = _REPO_ROOT / "disbot" / "services" / "platform_consistency.py"


def _extract_collector_labels() -> tuple[str, ...]:
    """Parse the labels used in the ``collect_report`` collector tuple.

    Handles both ``collectors = (...)`` and the annotated form
    ``collectors: ... = (...)``.  Returns the string label of each
    entry in declaration order.
    """
    tree = ast.parse(_MODULE_PATH.read_text())
    for node in ast.walk(tree):
        if not isinstance(node, ast.AsyncFunctionDef) or node.name != "collect_report":
            continue
        for sub in ast.walk(node):
            value: ast.AST | None = None
            if isinstance(sub, ast.Assign):
                target = sub.targets[0] if sub.targets else None
                if isinstance(target, ast.Name) and target.id == "collectors":
                    value = sub.value
            elif isinstance(sub, ast.AnnAssign):
                target = sub.target
                if isinstance(target, ast.Name) and target.id == "collectors":
                    value = sub.value
            if value is None or not isinstance(value, ast.Tuple):
                continue
            labels: list[str] = []
            for entry in value.elts:
                if (
                    isinstance(entry, ast.Tuple)
                    and entry.elts
                    and isinstance(entry.elts[0], ast.Constant)
                    and isinstance(entry.elts[0].value, str)
                ):
                    labels.append(entry.elts[0].value)
            return tuple(labels)
    pytest.fail("Could not locate the `collectors` tuple inside collect_report")


def test_label_to_kind_covers_every_collector_label():
    labels = _extract_collector_labels()
    assert len(labels) == 12, f"Expected 12 collectors; found {len(labels)}"
    missing = [label for label in labels if label not in pc._LABEL_TO_KIND]
    assert not missing, (
        f"_LABEL_TO_KIND missing entries for: {missing}.  "
        "Adding a new collector requires updating _LABEL_TO_KIND."
    )


def test_label_to_kind_has_no_orphan_entries():
    labels = set(_extract_collector_labels())
    orphan = [label for label in pc._LABEL_TO_KIND if label not in labels]
    assert (
        not orphan
    ), f"_LABEL_TO_KIND has orphan entries (no matching collector): {orphan}"


def test_readiness_kinds_matches_label_to_kind_values():
    """Every kind referenced by ``_LABEL_TO_KIND`` is in
    ``READINESS_KINDS``, and vice versa."""
    via_labels = set(pc._LABEL_TO_KIND.values())
    via_tuple = set(pc.READINESS_KINDS)
    assert via_labels == via_tuple, (
        f"READINESS_KINDS / _LABEL_TO_KIND drift: "
        f"only-in-tuple={via_tuple - via_labels}; "
        f"only-in-labels={via_labels - via_tuple}"
    )


def test_readiness_kinds_exhausts_enum():
    """Every ``ReadinessKind`` enum member appears in
    ``READINESS_KINDS``.  Adding a new enum member requires updating
    the canonical tuple."""
    assert set(pc.READINESS_KINDS) == set(pc.ReadinessKind)


def test_readiness_kinds_order_matches_collector_order():
    """The order of ``READINESS_KINDS`` matches the order of labels in
    the orchestrator's collector tuple.  Diagnostic embeds and the
    readiness snapshot rely on this ordering."""
    labels = _extract_collector_labels()
    expected = tuple(pc._LABEL_TO_KIND[label] for label in labels)
    assert pc.READINESS_KINDS == expected
