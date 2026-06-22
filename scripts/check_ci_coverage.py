#!/usr/bin/env python3.10
"""check_ci_coverage.py — find open claude/* PR heads missing their `code-quality` run.

PROVENANCE / RELIABILITY (2026-06-22, owner-endorsed Q-0195 idea
``ci-dropped-synchronize-auto-retrigger-2026-06-22``):
    Why: GitHub sometimes **drops the `pull_request: synchronize` event**, so a PR head gets no
    ``code-quality`` run at all. That is the *silent* CI stall — no run means no failure webhook
    ever fires, so native auto-merge waits forever with nothing red to notice (observed on PR
    #1283). The cancellation race was already fixed (#1275, ``cancel-in-progress: false``); this is
    the distinct dropped-*delivery* mode. The manual remedy was an empty commit; this automates it.

    HOW IT RE-KICKS: ``--rekick`` dispatches ``code-quality.yml`` (its ``workflow_dispatch`` trigger)
    on the PR branch via ``gh``. A dispatched run reports a ``code-quality`` check on the branch
    head, which is the PR head for a same-repo PR, so it satisfies the required check. The presence
    check is a natural cap: once a run exists (even queued), the next cycle sees it and does NOT
    re-dispatch, so there is no loop. A grace window avoids racing the seconds-long gap between a
    push and its run being registered.

    UNVERIFIED — heuristic, mirrors ``pr-auto-update.yml`` scoping (claude/* non-draft, non-carved).
    Needs ``gh`` + a token (always present in Actions); SKIP-degrades locally without them. Confirm
    its verdicts across a few cycles before trusting the ``--rekick`` path; **delete this script +
    its workflow if they misfire** — a missing run is always re-kickable by hand (empty commit /
    "Re-run" / `gh workflow run code-quality.yml --ref <branch>`).

Usage:
    check_ci_coverage.py [--rekick] [--required NAME] [--grace-min N] [--max-rekicks N]
"""

from __future__ import annotations

import argparse
import json
import subprocess
from collections.abc import Callable
from datetime import datetime, timezone

REQUIRED_CHECK = "code-quality"
GRACE_MIN = 8  # don't re-kick a head younger than this (run may not be registered yet)
MAX_REKICKS = 5  # per invocation, defensive cap
CARVE_OUT_LABELS = ("needs-hermes-review", "do-not-automerge")


# --------------------------------------------------------------------------- #
# Pure logic (unit-tested without gh)
# --------------------------------------------------------------------------- #


def missing_required_check(
    check_run_names: list[str],
    required: str = REQUIRED_CHECK,
) -> bool:
    """True when no check run named *required* exists for the head (queued counts as present)."""
    return required not in check_run_names


def past_grace(
    head_committed_at: datetime,
    now: datetime,
    grace_min: int = GRACE_MIN,
) -> bool:
    """True when the head commit is old enough that a normal run would already be registered."""
    return (now - head_committed_at).total_seconds() >= grace_min * 60


def should_rekick(
    check_run_names: list[str],
    head_committed_at: datetime,
    now: datetime,
    *,
    required: str = REQUIRED_CHECK,
    grace_min: int = GRACE_MIN,
) -> bool:
    """A head needs a re-kick iff its required run is missing AND it is past the grace window."""
    return missing_required_check(check_run_names, required) and past_grace(
        head_committed_at,
        now,
        grace_min,
    )


def find_uncovered(
    prs: list[dict],
    fetch_head: Callable[[str], tuple[list[str], datetime]],
    now: datetime,
    *,
    required: str = REQUIRED_CHECK,
    grace_min: int = GRACE_MIN,
) -> list[dict]:
    """Pure: return the PRs whose head is missing *required* and past grace.

    ``fetch_head(sha) -> (check_run_names, head_committed_at)`` is injected so this is testable
    without gh. ``prs`` items carry ``number``, ``branch``, ``sha``.
    """
    uncovered: list[dict] = []
    for pr in prs:
        names, committed_at = fetch_head(pr["sha"])
        if should_rekick(
            names,
            committed_at,
            now,
            required=required,
            grace_min=grace_min,
        ):
            uncovered.append(pr)
    return uncovered


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


def fetch_head_via_gh(repo: str) -> Callable[[str], tuple[list[str], datetime]]:
    def _fetch(sha: str) -> tuple[list[str], datetime]:
        runs = _gh_json(
            [
                "api",
                f"repos/{repo}/commits/{sha}/check-runs",
                "--jq",
                "[.check_runs[].name]",
            ],
        )
        names = list(runs) if isinstance(runs, list) else []
        commit = _gh_json(
            ["api", f"repos/{repo}/commits/{sha}", "--jq", ".commit.committer.date"],
        )
        when = _iso(commit) if isinstance(commit, str) else datetime.now(timezone.utc)
        return names, when

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


def main() -> int:
    import os

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--rekick",
        action="store_true",
        help="dispatch code-quality for uncovered heads",
    )
    ap.add_argument("--required", default=REQUIRED_CHECK)
    ap.add_argument("--grace-min", type=int, default=GRACE_MIN)
    ap.add_argument("--max-rekicks", type=int, default=MAX_REKICKS)
    args = ap.parse_args()

    repo = os.environ.get("GITHUB_REPOSITORY", "menno420/superbot")
    prs = list_open_claude_prs(repo)
    if prs is None:
        print(
            "check_ci_coverage: SKIP — gh/token unavailable (run inside Actions or set GH_TOKEN).",
        )
        return 0

    now = datetime.now(timezone.utc)
    uncovered = find_uncovered(
        prs,
        fetch_head_via_gh(repo),
        now,
        required=args.required,
        grace_min=args.grace_min,
    )

    if not uncovered:
        print(
            f"check_ci_coverage: {len(prs)} open claude/* PR(s), all have a `{args.required}` run ✓",
        )
        return 0

    print(
        f"check_ci_coverage: {len(uncovered)} PR head(s) missing `{args.required}` (dropped event):",
    )
    kicked = 0
    for pr in uncovered:
        line = f"  #{pr['number']} ({pr['branch']} @ {pr['sha'][:8]})"
        if args.rekick and kicked < args.max_rekicks:
            ok = rekick(repo, pr["branch"])
            kicked += 1
            print(
                (
                    f"{line} -> re-kicked code-quality"
                    if ok
                    else f"{line} -> re-kick FAILED"
                ),
            )
        else:
            print(line)
    if args.rekick:
        print(f"Re-kicked {kicked} (cap {args.max_rekicks}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
