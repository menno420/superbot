"""Tests for scripts/check_ci_coverage.py — the dropped-synchronize watchdog (Q-0195 idea;
self-silencing fix PR #1737 §C.3 Mode 2).

Cover the pure classification logic (no gh): a head with a PR-event run of the required workflow is
COVERED (whatever its conclusion); a head with no run past grace is REKICK; a head where a dispatched
re-kick already completed without producing a PR-event run is ESCALATE; a fresh head or an in-flight
dispatch is WAIT.
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

NOW = datetime(2026, 7, 5, 12, 0, 0, tzinfo=timezone.utc)
OLD = NOW - timedelta(minutes=30)  # well past grace
FRESH = NOW - timedelta(minutes=2)  # inside grace

WF = cc.REQUIRED_WORKFLOW_PATH


def _run(event: str, status: str = "completed", conclusion: str | None = "success", path: str = WF):
    return {"path": path, "event": event, "status": status, "conclusion": conclusion}


def test_past_grace():
    assert cc.past_grace(OLD, NOW) is True
    assert cc.past_grace(FRESH, NOW) is False


def test_pr_event_success_is_covered():
    assert cc.classify_head([_run("pull_request")], OLD, NOW) == cc.COVERED


def test_pr_event_failure_is_covered_not_rekicked():
    # A real CI failure is NOT the watchdog's job — auto-merge correctly won't fire; never re-kick it.
    assert cc.classify_head([_run("pull_request", conclusion="failure")], OLD, NOW) == cc.COVERED


def test_pr_event_in_progress_is_covered():
    assert (
        cc.classify_head([_run("pull_request", status="in_progress", conclusion=None)], OLD, NOW)
        == cc.COVERED
    )


def test_push_event_counts_as_pr_coverage():
    assert cc.classify_head([_run("push")], OLD, NOW) == cc.COVERED


def test_no_run_past_grace_is_rekick():
    assert cc.classify_head([], OLD, NOW) == cc.REKICK


def test_no_run_fresh_is_wait():
    assert cc.classify_head([], FRESH, NOW) == cc.WAIT


def test_dispatch_in_flight_is_wait():
    assert (
        cc.classify_head([_run("workflow_dispatch", status="in_progress", conclusion=None)], OLD, NOW)
        == cc.WAIT
    )


def test_completed_dispatch_without_pr_run_is_escalate():
    # The self-silencing case: our own re-kick ran and finished, but there is still no PR-event run.
    # Old code called this "covered" (name present) and stalled; now it escalates to a human.
    assert cc.classify_head([_run("workflow_dispatch")], OLD, NOW) == cc.ESCALATE


def test_dispatch_plus_later_pr_run_is_covered():
    # If a real PR-event run shows up alongside the dispatch, the head is covered.
    runs = [_run("workflow_dispatch"), _run("pull_request")]
    assert cc.classify_head(runs, OLD, NOW) == cc.COVERED


def test_unrelated_workflow_runs_ignored():
    # A run of some OTHER workflow on the head does not count as coverage of the required one.
    other = _run("pull_request", path=".github/workflows/codeql.yml")
    assert cc.classify_head([other], OLD, NOW) == cc.REKICK


def test_find_actionable_filters_and_labels():
    prs = [
        {"number": 1, "branch": "claude/a", "sha": "aaa"},  # no run + old -> REKICK
        {"number": 2, "branch": "claude/b", "sha": "bbb"},  # pr run -> COVERED (dropped)
        {"number": 3, "branch": "claude/c", "sha": "ccc"},  # no run + fresh -> WAIT (dropped)
        {"number": 4, "branch": "claude/d", "sha": "ddd"},  # completed dispatch, no pr run -> ESCALATE
    ]
    head = {
        "aaa": ([], OLD),
        "bbb": ([_run("pull_request")], OLD),
        "ccc": ([], FRESH),
        "ddd": ([_run("workflow_dispatch")], OLD),
    }
    actionable = cc.find_actionable(prs, lambda sha: head[sha], NOW)
    assert [(pr["number"], v) for pr, v in actionable] == [(1, cc.REKICK), (4, cc.ESCALATE)]


def test_find_actionable_empty_when_all_covered():
    prs = [{"number": 9, "branch": "claude/x", "sha": "x"}]
    assert cc.find_actionable(prs, lambda sha: ([_run("pull_request")], OLD), NOW) == []
