"""Tests for scripts/check_codeql_coverage.py — the CodeQL stuck-scan watchdog (design §C.2 / A10).

Cover the pure classification (no gh): a clean PR-event scan is HEALTHY; a scan in-progress within
the hang window is WAIT; a hung or errored scan under the retry budget is RERUN and at/over it is
ESCALATE; a live scan is left alone even beside an earlier failure; no scan past grace is RERUN; a
fresh head or a mere workflow_dispatch scan does not count as coverage.
"""

from __future__ import annotations

import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "check_codeql_coverage",
    Path(__file__).resolve().parents[3] / "scripts" / "check_codeql_coverage.py",
)
assert _SPEC and _SPEC.loader
cq = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(cq)

NOW = datetime(2026, 7, 6, 12, 0, 0, tzinfo=timezone.utc)
OLD = NOW - timedelta(minutes=60)  # well past grace
FRESH = NOW - timedelta(minutes=2)  # inside grace
WF = cq.CODEQL_WORKFLOW_PATH


def _run(
    event: str = "pull_request",
    status: str = "completed",
    conclusion: str | None = "success",
    path: str = WF,
    started_min_ago: int = 5,
):
    return {
        "path": path,
        "event": event,
        "status": status,
        "conclusion": conclusion,
        "started_at": NOW - timedelta(minutes=started_min_ago),
    }


def test_success_scan_is_healthy():
    assert cq.classify_codeql_head([_run()], OLD, NOW) == cq.HEALTHY


def test_in_progress_within_window_is_wait():
    r = _run(status="in_progress", conclusion=None, started_min_ago=5)
    assert cq.classify_codeql_head([r], OLD, NOW) == cq.WAIT


def test_hung_in_progress_scan_reruns():
    r = _run(
        status="in_progress", conclusion=None, started_min_ago=90
    )  # past hang_min (45)
    assert cq.classify_codeql_head([r], OLD, NOW) == cq.RERUN


def test_single_errored_scan_reruns():
    assert cq.classify_codeql_head([_run(conclusion="failure")], OLD, NOW) == cq.RERUN


def test_startup_failure_counts_as_stuck():
    assert (
        cq.classify_codeql_head([_run(conclusion="startup_failure")], OLD, NOW)
        == cq.RERUN
    )


def test_repeated_errors_escalate():
    # two stuck attempts >= max_retries (2) -> a human is needed
    runs = [_run(conclusion="failure"), _run(conclusion="startup_failure")]
    assert cq.classify_codeql_head(runs, OLD, NOW) == cq.ESCALATE


def test_live_scan_wins_over_prior_error():
    # a fresh scan is running alongside an earlier failure -> never touch the live one
    runs = [
        _run(conclusion="failure"),
        _run(status="in_progress", conclusion=None, started_min_ago=3),
    ]
    assert cq.classify_codeql_head(runs, OLD, NOW) == cq.WAIT


def test_no_scan_past_grace_reruns():
    assert cq.classify_codeql_head([], OLD, NOW) == cq.RERUN


def test_no_scan_fresh_is_wait():
    assert cq.classify_codeql_head([], FRESH, NOW) == cq.WAIT


def test_dispatch_scan_is_not_coverage():
    # only pull_request/push scans count; a manual dispatch success must not mask a stuck PR scan
    assert (
        cq.classify_codeql_head([_run(event="workflow_dispatch")], OLD, NOW) == cq.RERUN
    )


def test_non_codeql_workflow_ignored():
    other = _run(path=".github/workflows/code-quality.yml")
    assert cq.classify_codeql_head([other], OLD, NOW) == cq.RERUN


def test_find_stuck_filters_and_labels():
    prs = [
        {"number": 1, "branch": "claude/a", "sha": "aaa"},  # clean -> HEALTHY
        {"number": 2, "branch": "claude/b", "sha": "bbb"},  # one error -> RERUN
        {"number": 3, "branch": "claude/c", "sha": "ccc"},  # two errors -> ESCALATE
        {"number": 4, "branch": "claude/d", "sha": "ddd"},  # fresh, no run -> WAIT
    ]
    head = {
        "aaa": ([_run()], OLD),
        "bbb": ([_run(conclusion="failure")], OLD),
        "ccc": ([_run(conclusion="failure"), _run(conclusion="failure")], OLD),
        "ddd": ([], FRESH),
    }
    stuck = cq.find_stuck(prs, lambda sha: head[sha], NOW)
    assert [(pr["number"], v) for pr, v in stuck] == [(2, cq.RERUN), (3, cq.ESCALATE)]
