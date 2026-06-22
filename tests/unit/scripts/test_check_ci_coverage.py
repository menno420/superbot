"""Tests for scripts/check_ci_coverage.py — the dropped-synchronize watchdog (Q-0195 idea).

Cover the pure detection logic (no gh): a head with no `code-quality` run AND past the grace
window needs a re-kick; a head with the run (even queued), or one still inside grace, does not.
"""

from __future__ import annotations

import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "check_ci_coverage",
    Path(__file__).resolve().parents[3] / "scripts" / "check_ci_coverage.py",
)
assert _SPEC and _SPEC.loader
cc = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(cc)

NOW = datetime(2026, 6, 22, 12, 0, 0, tzinfo=timezone.utc)
OLD = NOW - timedelta(minutes=30)  # well past grace
FRESH = NOW - timedelta(minutes=2)  # inside grace


def test_missing_required_check():
    assert cc.missing_required_check(["CodeQL", "flag-conflicts"]) is True
    assert cc.missing_required_check(["CodeQL", "code-quality"]) is False


def test_past_grace():
    assert cc.past_grace(OLD, NOW) is True
    assert cc.past_grace(FRESH, NOW) is False


def test_should_rekick_only_when_missing_and_old():
    # missing + old -> rekick
    assert cc.should_rekick([], OLD, NOW) is True
    # present (even just queued) -> never
    assert cc.should_rekick(["code-quality"], OLD, NOW) is False
    # missing but fresh -> wait (run may not be registered yet)
    assert cc.should_rekick([], FRESH, NOW) is False


def test_find_uncovered_filters_correctly():
    prs = [
        {"number": 1, "branch": "claude/a", "sha": "aaa"},  # missing + old -> uncovered
        {"number": 2, "branch": "claude/b", "sha": "bbb"},  # has run -> covered
        {"number": 3, "branch": "claude/c", "sha": "ccc"},  # missing but fresh -> not yet
    ]
    head = {
        "aaa": ([], OLD),
        "bbb": (["code-quality"], OLD),
        "ccc": ([], FRESH),
    }
    uncovered = cc.find_uncovered(prs, lambda sha: head[sha], NOW)
    assert [pr["number"] for pr in uncovered] == [1]


def test_find_uncovered_empty_when_all_covered():
    prs = [{"number": 9, "branch": "claude/x", "sha": "x"}]
    assert cc.find_uncovered(prs, lambda sha: (["code-quality"], OLD), NOW) == []
