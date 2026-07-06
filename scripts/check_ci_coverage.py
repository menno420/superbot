#!/usr/bin/env python3.10
"""check_ci_coverage.py — recover a claude/* PR head that got NO code-quality run (dropped event).

PROVENANCE / RELIABILITY (2026-06-22 idea ``ci-dropped-synchronize-auto-retrigger-2026-06-22``;
self-silencing fix 2026-07-05, CI-setup redesign PR #1737 §C.3 Mode 2 / decision A2):
    Why: GitHub sometimes **drops the `pull_request: synchronize` event**, so a PR head gets no
    ``code-quality`` run at all. That is the *silent* CI stall — no run means no failure webhook, so
    native auto-merge waits forever with nothing red to notice (observed on PR #1283).

    THE SELF-SILENCING BUG THIS FIXES (was line 53, ``required not in check_run_names``): the old
    check treated the *presence of a check-run name* as "covered." A ``--rekick`` dispatches
    ``code-quality.yml`` via ``workflow_dispatch``; that produces a ``code-quality`` run whose NAME is
    present — so the next cycle believed the head was covered and stopped, **even if that dispatched
    run never satisfied the PR's required status check** (the PR stayed blocked forever). Presence is
    not satisfaction.

    THE FIX — classify by the *triggering event*, robust to the one thing we could not verify offline
    (whether a ``workflow_dispatch`` run satisfies the required check):
      * A ``pull_request``/``push`` run of the required workflow (success, failure, OR in-progress)
        means CI actually ran for the PR event → **COVERED**; the watchdog leaves it alone (auto-merge
        handles success/failure; re-kicking a real *failure* would be wrong).
      * No PR/push run at all, past a grace window → the dropped-event case → **REKICK** (dispatch).
      * No PR/push run, but a ``workflow_dispatch`` re-kick already **completed** and still produced no
        PR-event coverage → **ESCALATE**: open one owner-alert issue instead of re-dispatching forever.
      This is correct either way the unknown resolves: if a dispatched run *does* satisfy the gate, the
      PR merges and leaves the open list before we escalate; if it *doesn't*, a human is alerted rather
      than the PR stalling silently.

    UNVERIFIED (Q-0105) — heuristic; mirrors ``pr-auto-update.yml`` scoping (claude/* non-draft,
    non-carved). Needs ``gh`` + a token (present in Actions); SKIP-degrades locally without them.
    The ESCALATE→issue path and the event-classification want a live dropped-synchronize confirmation
    (see the handoff in docs/planning/ci-followups-handoff-2026-07-05.md). **Delete this script + its
    workflow if they misfire** — a missing run is always re-kickable by hand (empty commit / "Re-run" /
    ``gh workflow run code-quality.yml --ref <branch>``).

Usage:
    check_ci_coverage.py [--rekick] [--required NAME] [--grace-min N]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

# scripts/ is not a package; add it to the path so the shared lib.owner_alert helper imports whether
# this runs as `python3 scripts/check_ci_coverage.py` (Actions) or is loaded by file path (tests).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.owner_alert import alert_marker, ensure_issue  # noqa: E402

REQUIRED_CHECK = (
    "code-quality"  # the required status-check name (for messaging / --required)
)
# The workflow whose PR/push run satisfies the required `code-quality` check. Matching on the workflow
# file path is stable across a rename of the display name.
REQUIRED_WORKFLOW_PATH = ".github/workflows/code-quality.yml"
GRACE_MIN = 8  # don't re-kick a head younger than this (run may not be registered yet)
CARVE_OUT_LABELS = ("do-not-automerge",)

# Classifications
COVERED = "covered"
REKICK = "rekick"
ESCALATE = "escalate"
WAIT = "wait"

# Event names that count as "CI ran for the PR" (i.e. the required check will reflect this head).
_PR_EVENTS = ("pull_request", "push")


# --------------------------------------------------------------------------- #
# Pure logic (unit-tested without gh)
#
# A "run" is a dict: {"path": str, "event": str, "status": str, "conclusion": str | None}
# mirroring the GitHub Actions `workflow_runs` shape (status is queued|in_progress|completed).
# --------------------------------------------------------------------------- #


def past_grace(
    head_committed_at: datetime,
    now: datetime,
    grace_min: int = GRACE_MIN,
) -> bool:
    """True when the head commit is old enough that a normal run would already be registered."""
    return (now - head_committed_at).total_seconds() >= grace_min * 60


def classify_head(
    runs: list[dict],
    head_committed_at: datetime,
    now: datetime,
    *,
    workflow_path: str = REQUIRED_WORKFLOW_PATH,
    grace_min: int = GRACE_MIN,
) -> str:
    """Classify a PR head into COVERED / REKICK / ESCALATE / WAIT.

    Satisfaction, not mere presence: only a ``pull_request``/``push`` run of the required workflow
    counts as covered. A completed ``workflow_dispatch`` run that produced no PR-event coverage means
    our own re-kick did not unblock the PR → escalate to a human rather than self-silencing.
    """
    req = [r for r in runs if r.get("path") == workflow_path]
    pr_runs = [r for r in req if r.get("event") in _PR_EVENTS]
    if pr_runs:
        # CI ran for the PR event (any status/conclusion) — NOT a dropped event; leave it to auto-merge.
        return COVERED
    dispatch_runs = [r for r in req if r.get("event") == "workflow_dispatch"]
    if any(r.get("status") == "completed" for r in dispatch_runs):
        # We already re-kicked; it finished but there is still no PR-event run → human needed.
        return ESCALATE
    if dispatch_runs:
        return WAIT  # a dispatched re-kick is still in flight
    if past_grace(head_committed_at, now, grace_min):
        return REKICK  # no run at all, past grace → the dropped-synchronize case
    return WAIT  # too fresh; a normal run may not be registered yet


def find_actionable(
    prs: list[dict],
    fetch_head: Callable[[str], tuple[list[dict], datetime]],
    now: datetime,
    *,
    workflow_path: str = REQUIRED_WORKFLOW_PATH,
    grace_min: int = GRACE_MIN,
) -> list[tuple[dict, str]]:
    """Pure: return ``(pr, verdict)`` for every PR needing REKICK or ESCALATE.

    ``fetch_head(sha) -> (runs, head_committed_at)`` is injected so this is testable without gh.
    ``prs`` items carry ``number``, ``branch``, ``sha``.
    """
    actionable: list[tuple[dict, str]] = []
    for pr in prs:
        runs, committed_at = fetch_head(pr["sha"])
        verdict = classify_head(
            runs,
            committed_at,
            now,
            workflow_path=workflow_path,
            grace_min=grace_min,
        )
        if verdict in (REKICK, ESCALATE):
            actionable.append((pr, verdict))
    return actionable


# --------------------------------------------------------------------------- #
# gh-backed I/O (skipped cleanly when gh/token absent)
# --------------------------------------------------------------------------- #


def _gh_json(args: list[str]) -> object | None:
    try:
        out = subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return None


def _iso(dt: str) -> datetime:
    return datetime.fromisoformat(dt.replace("Z", "+00:00"))


def list_open_claude_prs(repo: str) -> list[dict] | None:
    """Open, non-draft, non-carved claude/* PRs (mirrors pr-auto-update.yml scoping)."""
    data = _gh_json(
        [
            "pr",
            "list",
            "--repo",
            repo,
            "--state",
            "open",
            "--base",
            "main",
            "--json",
            "number,headRefName,headRefOid,isDraft,labels",
        ],
    )
    if data is None:
        return None
    prs: list[dict] = []
    for pr in data:  # type: ignore[union-attr]
        if not str(pr["headRefName"]).startswith("claude/"):
            continue
        if pr.get("isDraft"):
            continue
        labels = {label["name"] for label in pr.get("labels", [])}
        if labels & set(CARVE_OUT_LABELS):
            continue
        prs.append(
            {
                "number": pr["number"],
                "branch": pr["headRefName"],
                "sha": pr["headRefOid"],
            },
        )
    return prs


def fetch_head_via_gh(repo: str) -> Callable[[str], tuple[list[dict], datetime]]:
    """Return a fetcher: sha -> (workflow runs for that head, head commit datetime).

    Uses the Actions ``workflow_runs`` endpoint (not ``check-runs``) because only it carries the
    triggering ``event`` — the field the self-silencing fix classifies on.
    """

    def _fetch(sha: str) -> tuple[list[dict], datetime]:
        runs = _gh_json(
            [
                "api",
                f"repos/{repo}/actions/runs?head_sha={sha}&per_page=50",
                "--jq",
                "[.workflow_runs[] | {path: .path, event: .event, "
                "status: .status, conclusion: .conclusion}]",
            ],
        )
        run_list = list(runs) if isinstance(runs, list) else []
        commit = _gh_json(
            ["api", f"repos/{repo}/commits/{sha}", "--jq", ".commit.committer.date"],
        )
        when = _iso(commit) if isinstance(commit, str) else datetime.now(timezone.utc)
        return run_list, when

    return _fetch


def rekick(repo: str, branch: str) -> bool:
    """Dispatch code-quality.yml on *branch* (gh workflow run). True on success."""
    try:
        subprocess.run(
            [
                "gh",
                "workflow",
                "run",
                "code-quality.yml",
                "--repo",
                repo,
                "--ref",
                branch,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


def open_alert_issue(repo: str, pr: dict) -> bool:
    """Idempotently open an owner-alert issue for a stuck head (dispatched re-kick didn't help).

    Delegates the marker-based dedupe + create to the shared ``lib.owner_alert.ensure_issue`` (Q-0089)
    so every watchdog escalates the same, deduped, tested-in-one-place way — the 12-min cron never
    spams duplicate issues. Best-effort: returns False (and the caller just logs) if gh is absent.
    """
    marker = alert_marker("ci-coverage", pr["number"])
    body = (
        f"The head of PR #{pr['number']} (`{pr['branch']}` @ `{pr['sha'][:8]}`) has **no "
        f"`pull_request`/`push` run** of `{REQUIRED_WORKFLOW_PATH}`, and a `workflow_dispatch` "
        f"re-kick already completed without producing one — so native auto-merge is stuck with "
        f"nothing to wait on.\n\nLikely a dropped `pull_request: synchronize` event that a dispatched "
        f"run does not satisfy for branch protection. **Manual remedy:** push an empty commit, or "
        f"close+reopen the PR (re-arms `auto-merge-enabler`), or investigate a real block.\n\n"
        f"{marker}"
    )
    title = f"CI watchdog: PR #{pr['number']} head has no PR-event code-quality run"
    return ensure_issue(repo, marker, title, body)


def main() -> int:
    import os

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--rekick",
        action="store_true",
        help="act on uncovered heads (dispatch / alert)",
    )
    ap.add_argument("--required", default=REQUIRED_CHECK)
    ap.add_argument("--grace-min", type=int, default=GRACE_MIN)
    args = ap.parse_args()

    repo = os.environ.get("GITHUB_REPOSITORY", "menno420/superbot")
    prs = list_open_claude_prs(repo)
    if prs is None:
        print(
            "check_ci_coverage: SKIP — gh/token unavailable (run inside Actions or set GH_TOKEN).",
        )
        return 0

    now = datetime.now(timezone.utc)
    actionable = find_actionable(
        prs,
        fetch_head_via_gh(repo),
        now,
        grace_min=args.grace_min,
    )

    if not actionable:
        print(
            f"check_ci_coverage: {len(prs)} open claude/* PR(s), all have a PR-event "
            f"`{args.required}` run (or are within grace) ✓",
        )
        return 0

    rekicks = [pr for pr, v in actionable if v == REKICK]
    escalations = [pr for pr, v in actionable if v == ESCALATE]
    print(
        f"check_ci_coverage: {len(rekicks)} head(s) missing a PR-event `{args.required}` run "
        f"(dropped event); {len(escalations)} stuck after a re-kick:",
    )
    for pr in rekicks:
        line = f"  #{pr['number']} ({pr['branch']} @ {pr['sha'][:8]}) -> MISSING"
        if args.rekick:
            ok = rekick(repo, pr["branch"])
            line += " -> re-kicked code-quality" if ok else " -> re-kick FAILED"
        print(line)
    for pr in escalations:
        line = f"  #{pr['number']} ({pr['branch']} @ {pr['sha'][:8]}) -> STUCK (re-kick did not help)"
        if args.rekick:
            ok = open_alert_issue(repo, pr)
            line += (
                " -> owner-alert issue open" if ok else " -> alert FAILED (logged only)"
            )
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
