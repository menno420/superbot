"""CI gate for the offline AI eval **smoke matrix** (P1-1).

Unlike the golden set (``cases.py``, live/paid only), this deterministic matrix
runs in normal CI: it drives the real gateway pipeline with scripted providers
(no API) and proves the contract — gates, fallback, tool dispatch, audit
visibility, safety, redaction, config — holds. A red here means a regression in
the AI path's deterministic behaviour, not a flaky model.
"""

from __future__ import annotations

import pytest
from tests.evals.smoke import (
    SMOKE_CASES,
    SMOKE_MATRIX_VERSION,
    render_report,
    run_matrix,
    run_smoke_case,
)

# Every dimension the hardening roadmap's P1-1 names for the offline half.
_REQUIRED_CATEGORIES = {
    "gate",
    "fallback",
    "tool_dispatch",
    "audit",
    "safety",
    "redaction",
    "config",
}


@pytest.mark.parametrize("case", SMOKE_CASES, ids=[c.id for c in SMOKE_CASES])
async def test_smoke_case_passes(case):
    """Each deterministic contract probe holds through the real gateway."""
    result, grade = await run_smoke_case(case)
    assert grade.passed, f"{case.id}: {grade.detail}  (description: {case.description})"
    # Sanity: the run produced a typed response object, never None.
    assert result.response is not None


def test_matrix_is_well_formed():
    ids = [c.id for c in SMOKE_CASES]
    assert len(ids) == len(set(ids)), "duplicate smoke case ids"
    assert len(SMOKE_CASES) >= 12, "smoke matrix unexpectedly small"
    categories = {c.category for c in SMOKE_CASES}
    missing = _REQUIRED_CATEGORIES - categories
    assert not missing, f"smoke matrix is missing required categories: {missing}"
    for case in SMOKE_CASES:
        assert case.id and case.category and case.description
        assert callable(case.expect)
        assert callable(case.providers)


def test_version_is_stamped():
    assert SMOKE_MATRIX_VERSION
    # The version is a date-stamped revision, e.g. "2026-06-14.1".
    assert SMOKE_MATRIX_VERSION[:4].isdigit()


async def test_full_matrix_is_green_and_renders():
    """The whole matrix passes and the versioned scorecard renders."""
    graded = await run_matrix()
    failures = [(case.id, grade.detail) for case, grade in graded if not grade.passed]
    assert not failures, f"smoke matrix failures: {failures}"

    report = render_report(graded)
    assert f"v{SMOKE_MATRIX_VERSION}" in report
    assert "AI Smoke Matrix" in report
    assert f"{len(graded)}/{len(graded)}" in report  # TOTAL N/N


async def test_env_isolation_restores_managed_keys(monkeypatch):
    """The runner must leave the AI-env namespace exactly as it found it."""
    import os

    monkeypatch.setenv("AI_ENABLED", "sentinel-value")
    monkeypatch.delenv("AI_FALLBACK_PROVIDER", raising=False)

    # Run a case that sets both keys internally.
    case = next(c for c in SMOKE_CASES if c.id == "fallback.primary_fault_recovers")
    await run_smoke_case(case)

    assert os.environ.get("AI_ENABLED") == "sentinel-value"
    assert "AI_FALLBACK_PROVIDER" not in os.environ
