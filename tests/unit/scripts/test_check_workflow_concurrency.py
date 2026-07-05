"""Tests for scripts/check_workflow_concurrency.py — the cancellation-race guard (PR #1737, G4).

Cover the pure logic: a merge-relevant workflow with `cancel-in-progress: false` (or absent) is
safe; `true` or a `${{ ... }}` expression is a finding; a non-merge-relevant workflow is never
flagged regardless of its concurrency config.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "check_workflow_concurrency",
    Path(__file__).resolve().parents[3] / "scripts" / "check_workflow_concurrency.py",
)
assert _SPEC and _SPEC.loader
wc = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(wc)


def _wf(cancel: str | None) -> str:
    body = "name: X\non:\n  pull_request:\njobs:\n  a:\n    runs-on: ubuntu-latest\n"
    if cancel is None:
        return body
    return (
        "name: X\non:\n  pull_request:\n"
        f"concurrency:\n  group: g-${{{{ github.ref }}}}\n  cancel-in-progress: {cancel}\n"
        "jobs:\n  a:\n    runs-on: ubuntu-latest\n"
    )


def test_is_safe_literal_false():
    assert wc._is_safe("false") is True
    assert wc._is_safe(" false ") is True
    assert wc._is_safe("'false'") is True
    assert wc._is_safe("False") is True  # YAML is case-insensitive for booleans


def test_is_unsafe_true_and_expressions():
    assert wc._is_safe("true") is False
    assert wc._is_safe("${{ github.ref != 'refs/heads/main' }}") is False


def test_merge_relevant_false_passes():
    assert wc.check({"code-quality.yml": _wf("false")}) == []


def test_merge_relevant_absent_passes():
    # No cancel-in-progress key → GitHub defaults to false → safe.
    assert wc.check({"code-quality.yml": _wf(None)}) == []


def test_merge_relevant_true_flagged():
    problems = wc.check({"ci.yml": _wf("true")})
    assert len(problems) == 1
    assert "ci.yml" in problems[0]
    assert "cancel-in-progress" in problems[0]


def test_merge_relevant_expression_flagged():
    # This is codeql.yml's real value today — the A1 tell.
    problems = wc.check({"codeql.yml": _wf("${{ github.ref != 'refs/heads/main' }}")})
    assert len(problems) == 1
    assert "codeql.yml" in problems[0]


def test_non_merge_relevant_never_flagged():
    # A routine workflow that cancels is fine — it feeds no required check.
    assert wc.check({"dashboard-data-refresh.yml": _wf("true")}) == []


def test_real_repo_all_merge_relevant_safe():
    # Ground truth against the live workflows dir: after PR #1739 flipped codeql.yml to
    # cancel-in-progress: false, EVERY merge-relevant workflow is safe → no findings. This test is
    # also the guard's own gate (it runs as a required step in code-quality.yml), so if a future edit
    # reintroduces a cancelling merge-relevant workflow, both this test AND the CI step go red.
    problems = wc.check(wc.load_workflows(wc.WORKFLOWS_DIR))
    assert problems == [], f"merge-relevant workflow(s) can cancel a head run: {problems}"
