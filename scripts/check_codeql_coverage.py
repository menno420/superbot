#!/usr/bin/env python3.10
"""check_codeql_coverage.py — bound a CodeQL scan that STARTS THEN ERRORS/HANGS.

PROVENANCE / RELIABILITY (design ci-setup-redesign-2026-07-05.md §C.2 / plan A10; handoff item #2;
built 2026-07-06):
    Why: the owner's ``codeql-merge-protection`` ruleset (2026-07-05) makes CodeQL a merge gate — it
    **holds** the merge while a scan is in-progress and **blocks** when CodeQL is unconfigured. But it
    does **not** bound a scan that *starts then errors or hangs* (autobuild failure, ``codeql-action``
    outage): that state holds an auto-merge PR forever with nothing red to notice — the same
    "waits-forever" shape ``check_ci_coverage`` fixes for the dropped ``synchronize`` event, on a new
    axis (design §C.2 "Residual hole the ruleset does NOT close").

    THE WATCHDOG — a stuck-scan leg for ``ci-rerun-watchdog.yml``. On the ``*/12`` cadence, for each
    open ``claude/*`` PR head, classify the head's ``codeql.yml`` runs:
      * a completed **success** scan → **HEALTHY** (the ruleset evaluates its alerts; not our job).
      * a scan still progressing **within the hang window** → **WAIT** (leave the live scan alone).
      * errored/hung attempts **under** the retry budget → **RERUN** (re-dispatch codeql).
      * errored/hung attempts **at/over** the budget → **ESCALATE** (one idempotent owner-alert issue).
      * **no** scan of the PR event at all past grace → **RERUN** (a dropped codeql event — bound it too).

    ALERTING-ONLY FIRST (plan A10): the workflow runs this **without** ``--rerun`` until the re-dispatch
    path is live-confirmed, so it *reports + opens one owner-alert issue* on any stuck head but does not
    auto re-dispatch. ``--rerun`` (future, once confirmed) re-runs RERUN heads and alerts only on
    ESCALATE.

    UNVERIFIED (Q-0105) — the exact GitHub Actions run shape for CodeQL (its ``.path``, and whether a
    re-run surfaces as a fresh ``workflow_runs`` row vs. a new attempt on the same run) is offline-built
    and wants **one** live errored/dropped-scan confirmation before ``--rerun`` is switched on. Needs
    ``gh`` + a token (present in Actions); SKIP-degrades locally without them. **Delete this script +
    its watchdog leg if they misfire** — a stuck scan is always re-runnable by hand ("Re-run all jobs"
    / ``gh workflow run codeql.yml --ref <branch>``).

Usage:
    check_codeql_coverage.py [--rerun] [--grace-min N] [--hang-min N] [--max-retries K]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

# scripts/ is not a package; add it to the path so the sibling watchdog's proven gh helpers and the
# shared lib.owner_alert import whether this runs as `python3 scripts/check_codeql_coverage.py`
# (Actions) or is loaded by file path (tests).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_ci_coverage import (  # noqa: E402
    _PR_EVENTS,
    _gh_json,
    _iso,
    list_open_claude_prs,
)
from lib.owner_alert import alert_marker, ensure_issue  # noqa: E402

CODEQL_WORKFLOW_PATH = ".github/workflows/codeql.yml"
GRACE_MIN = 8  # a normal codeql run should be registered within this
HANG_MIN = 45  # an in-progress scan older than this is treated as hung (autobuild/action outage)
MAX_RETRIES = 2  # re-run at most this many times before escalating to a human

# Classifications
HEALTHY = "healthy"
RERUN = "rerun"
ESCALATE = "escalate"
WAIT = "wait"

# codeql conclusions meaning "the scan started but did not produce a clean result".
_ERROR_CONCLUSIONS = (
    "failure",
    "cancelled",
    "timed_out",
    "startup_failure",
    "stale",
    "action_required",
)
# non-terminal statuses — a scan still in flight.
_INCOMPLETE_STATUSES = ("queued", "in_progress", "requested", "waiting", "pending")


# --------------------------------------------------------------------------- #
# Pure logic (unit-tested without gh)
#
# A "run" is a dict: {"path": str, "event": str, "status": str, "conclusion": str | None,
# "started_at": datetime | None} — the GitHub Actions `workflow_runs` shape plus `run_started_at`
# (needed to tell a normal in-progress scan from a hung one).
# --------------------------------------------------------------------------- #


def _older_than(ref: datetime, now: datetime, minutes: int) -> bool:
    """True when ``ref`` is at least ``minutes`` old relative to ``now``."""
    return (now - ref).total_seconds() >= minutes * 60


def _is_hung(run: dict, now: datetime, hang_min: int) -> bool:
    """True when an in-flight scan has been running longer than the hang window."""
    started = run.get("started_at")
    return isinstance(started, datetime) and _older_than(started, now, hang_min)


def classify_codeql_head(
    runs: list[dict],
    head_committed_at: datetime,
    now: datetime,
    *,
    workflow_path: str = CODEQL_WORKFLOW_PATH,
    grace_min: int = GRACE_MIN,
    hang_min: int = HANG_MIN,
    max_retries: int = MAX_RETRIES,
) -> str:
    """Classify a PR head's CodeQL state into HEALTHY / RERUN / ESCALATE / WAIT.

    Only a ``pull_request``/``push`` run of ``codeql.yml`` counts (a manual ``workflow_dispatch`` scan
    does not mask a stuck PR scan). A live scan within the hang window is always left alone — the
    ruleset holds on it — even when an earlier attempt errored.
    """
    req = [
        r
        for r in runs
        if r.get("path") == workflow_path and r.get("event") in _PR_EVENTS
    ]
    # A clean completed scan → the ruleset evaluates its alerts. Not the watchdog's concern.
    if any(
        r.get("status") == "completed" and r.get("conclusion") == "success" for r in req
    ):
        return HEALTHY
    incomplete = [r for r in req if r.get("status") in _INCOMPLETE_STATUSES]
    # A scan progressing within the hang window → leave the live scan alone (the ruleset holds).
    if any(not _is_hung(r, now, hang_min) for r in incomplete):
        return WAIT
    hung = [r for r in incomplete if _is_hung(r, now, hang_min)]
    errored = [
        r
        for r in req
        if r.get("status") == "completed" and r.get("conclusion") in _ERROR_CONCLUSIONS
    ]
    stuck_attempts = len(hung) + len(errored)
    if stuck_attempts:
        return ESCALATE if stuck_attempts >= max_retries else RERUN
    # No codeql run of the PR event at all → a dropped codeql event; bound it like the synchronize case.
    if _older_than(head_committed_at, now, grace_min):
        return RERUN
    return WAIT  # too fresh; a normal scan may not be registered yet


def find_stuck(
    prs: list[dict],
    fetch_head: Callable[[str], tuple[list[dict], datetime]],
    now: datetime,
    *,
    workflow_path: str = CODEQL_WORKFLOW_PATH,
    grace_min: int = GRACE_MIN,
    hang_min: int = HANG_MIN,
    max_retries: int = MAX_RETRIES,
) -> list[tuple[dict, str]]:
    """Pure: return ``(pr, verdict)`` for every PR whose CodeQL scan needs RERUN or ESCALATE.

    ``fetch_head(sha) -> (runs, head_committed_at)`` is injected so this is testable without gh.
    """
    actionable: list[tuple[dict, str]] = []
    for pr in prs:
        runs, committed_at = fetch_head(pr["sha"])
        verdict = classify_codeql_head(
            runs,
            committed_at,
            now,
            workflow_path=workflow_path,
            grace_min=grace_min,
            hang_min=hang_min,
            max_retries=max_retries,
        )
        if verdict in (RERUN, ESCALATE):
            actionable.append((pr, verdict))
    return actionable


# --------------------------------------------------------------------------- #
# gh-backed I/O (skipped cleanly when gh/token absent) — reuses check_ci_coverage's helpers
# --------------------------------------------------------------------------- #


def fetch_codeql_head_via_gh(
    repo: str,
) -> Callable[[str], tuple[list[dict], datetime]]:
    """Return a fetcher: sha -> (codeql-relevant workflow runs for that head, head commit datetime).

    Uses the Actions ``workflow_runs`` endpoint (like check_ci_coverage) but also carries
    ``run_started_at`` so a hung in-progress scan is distinguishable from a normal one.
    """

    def _fetch(sha: str) -> tuple[list[dict], datetime]:
        raw = _gh_json(
            [
                "api",
                f"repos/{repo}/actions/runs?head_sha={sha}&per_page=50",
                "--jq",
                "[.workflow_runs[] | {path: .path, event: .event, status: .status, "
                "conclusion: .conclusion, started_at: .run_started_at}]",
            ],
        )
        run_list: list[dict] = []
        if isinstance(raw, list):
            for r in raw:
                started = r.get("started_at")
                run_list.append(
                    {
                        "path": r.get("path"),
                        "event": r.get("event"),
                        "status": r.get("status"),
                        "conclusion": r.get("conclusion"),
                        "started_at": (
                            _iso(started) if isinstance(started, str) else None
                        ),
                    },
                )
        commit = _gh_json(
            ["api", f"repos/{repo}/commits/{sha}", "--jq", ".commit.committer.date"],
        )
        when = _iso(commit) if isinstance(commit, str) else datetime.now(timezone.utc)
        return run_list, when

    return _fetch


def rerun_codeql(repo: str, branch: str) -> bool:
    """Dispatch codeql.yml on *branch* (gh workflow run). True on success."""
    try:
        subprocess.run(
            ["gh", "workflow", "run", "codeql.yml", "--repo", repo, "--ref", branch],
            capture_output=True,
            text=True,
            check=True,
        )
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


def open_alert_issue(repo: str, pr: dict) -> bool:
    """Idempotently open an owner-alert issue for a head whose CodeQL scan is stuck.

    Reuses the shared ``lib.owner_alert.ensure_issue`` dedupe (Q-0089) — one issue per head, no spam.
    """
    marker = alert_marker("codeql-coverage", pr["number"])
    body = (
        f"The head of PR #{pr['number']} (`{pr['branch']}` @ `{pr['sha'][:8]}`) has **no clean "
        f"`pull_request`/`push` scan** of `{CODEQL_WORKFLOW_PATH}` — the CodeQL run errored or hung "
        f"past the grace window and did not recover. The `codeql-merge-protection` ruleset holds on "
        f"*in-progress* and blocks on *unconfigured*, but does **not** bound a scan that starts then "
        f"errors/hangs, so native auto-merge is stuck with nothing to release it.\n\n**Manual "
        f"remedy:** the PR's Checks tab → CodeQL → *Re-run all jobs*, or "
        f"`gh workflow run codeql.yml --ref {pr['branch']}`, or investigate a real autobuild / "
        f"`codeql-action` failure.\n\n{marker}"
    )
    title = (
        f"CodeQL watchdog: PR #{pr['number']} scan errored/hung with no clean result"
    )
    return ensure_issue(repo, marker, title, body)


def main() -> int:
    import os

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--rerun",
        action="store_true",
        help="re-dispatch codeql for RERUN heads (default: alerting-only — report + owner-alert issue)",
    )
    ap.add_argument("--grace-min", type=int, default=GRACE_MIN)
    ap.add_argument("--hang-min", type=int, default=HANG_MIN)
    ap.add_argument("--max-retries", type=int, default=MAX_RETRIES)
    args = ap.parse_args()

    repo = os.environ.get("GITHUB_REPOSITORY", "menno420/superbot")
    prs = list_open_claude_prs(repo)
    if prs is None:
        print(
            "check_codeql_coverage: SKIP — gh/token unavailable (run inside Actions or set GH_TOKEN).",
        )
        return 0

    now = datetime.now(timezone.utc)
    actionable = find_stuck(
        prs,
        fetch_codeql_head_via_gh(repo),
        now,
        grace_min=args.grace_min,
        hang_min=args.hang_min,
        max_retries=args.max_retries,
    )

    if not actionable:
        print(
            f"check_codeql_coverage: {len(prs)} open claude/* PR(s), all CodeQL scans healthy "
            f"or within grace ✓",
        )
        return 0

    mode = "re-run + alert" if args.rerun else "alerting-only"
    print(
        f"check_codeql_coverage: {len(actionable)} head(s) with a stuck CodeQL scan ({mode}):",
    )
    for pr, verdict in actionable:
        if args.rerun and verdict == RERUN:
            ok = rerun_codeql(repo, pr["branch"])
            action = "re-ran codeql" if ok else "re-run FAILED"
        else:
            ok = open_alert_issue(repo, pr)
            action = "owner-alert issue open" if ok else "alert FAILED (logged only)"
        print(
            f"  #{pr['number']} ({pr['branch']} @ {pr['sha'][:8]}) [{verdict}] -> {action}",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
