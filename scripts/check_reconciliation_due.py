#!/usr/bin/env python3.10
"""Reconciliation-cadence guard — flag when a docs-only review/planning pass is due.

[session-close-gate] Invoked from ``/session-close`` Step 4 (``check_session_close_gate.py`` enforces that this stays wired in).

Owner directive Q-0107: PR numbers crossing a **multiple of 30** (#30, #60, #90, …) are
reserved for a **docs-only repo review + planning-reconciliation** pass — review the state
of the repo (ledger, active lanes, open Q-blocks, idea backlog, roadmap), prune stale docs,
and refocus the next priorities. This guard tracks the cadence against the
``Last reconciliation pass:** PR #N`` marker in ``docs/current-state.md``: a pass is **due**
once merged PRs have crossed into a new multiple-of-30 band since the last marked pass.
(Cadence raised 10 → 20 on 2026-06-12, then 20 → 30 on 2026-06-14 (Q-0134) — at burst
velocity a 20-band crossed in under a day and fired the docs pass several times daily; the
band size is the ``STEP`` constant below — retune there.)

Advisory by default (exit 0); ``--strict`` for an explicit gate (e.g. ``/session-close``).
After completing a pass, reset the marker to the latest PR. Pure stdlib, like ``check_docs.py``.

Reliability (Q-0105, added 2026-06-12): **unverified** — if the cadence misfires (PR-number
gaps from other repos' activity, a wrong marker) over multiple sessions, **delete it**; it is
a convenience nudge for the Q-0107 cadence, not load-bearing.

Usage:
    python3.10 scripts/check_reconciliation_due.py            # advisory (exit 0)
    python3.10 scripts/check_reconciliation_due.py --strict   # exit 1 if a pass is due
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CURRENT_STATE = REPO_ROOT / "docs" / "current-state.md"

STEP = 30  # the cadence: a pass per multiple-of-30 PR band (10→20 2026-06-12; 20→30 2026-06-14, Q-0134)

_MARKER_RE = re.compile(r"Last reconciliation pass:\*\*\s*PR #(\d+)")
# Match all three merge-subject styles in this repo's history:
# "Merge pull request #N" (GitHub web), "Merge PR #N: …" (MCP merges with a
# custom title — the dominant style since 2026-06), and "title (#N)" suffixes.
# The missing "PR #" alternative made the checker under-report the latest PR
# (stuck at #751 while #762 was merged — caught by the 2026-06-12 night pass).
# Anchored to real PR-landing forms ONLY (2026-07-10, the "#104" false-red): a
# merge commit head ("Merge pull request #N ..." / "Merge PR #N: ...") or a squash
# suffix ("title (#N)" at end-of-subject). An UN-anchored "PR #N" also matched
# cross-repo references inside ordinary branch-commit subjects that reach main via
# a true merge (e.g. "... (superbot-next ORDER 010, PR #104); ..." -> phantom #104).
_MERGE_SUBJECT_RE = re.compile(r"^Merge (?:pull request|PR) #(\d+)|\(#(\d+)\)\s*$")


def issue_body() -> str:
    """The canonical `reconcile`-issue body — the single source the workflow echoes.

    Built from ``STEP`` so the human-readable cadence copy can never drift away from the
    live firing cadence again. BUG-0016 was exactly that drift: the workflow carried its own
    hardcoded body string that still said "multiple-of-20" / "next ~9 PRs" long after the
    cadence became 30 (Q-0134) and the planning horizon became the full band (Q-0164). The
    workflow now calls ``check_reconciliation_due.py --issue-body`` instead of holding a copy.
    """
    return (
        f"A {STEP}-PR band was crossed — a docs-only reconciliation + planning pass is due "
        f"(Q-0107, cadence {STEP} per Q-0134).\n\n"
        "This issue triggers the **superbot docs reconciliation** routine, which reconciles "
        "the ledger, de-stales docs, plans the next full band (depth >= the cadence, Q-0164), "
        "adds one idea, resets the `Last reconciliation pass` marker, and closes this issue.\n\n"
        "Auto-opened by `.github/workflows/reconciliation-trigger.yml`. You can also open a "
        "`reconcile`-labeled issue by hand whenever you spot docs drift."
    )


def _latest_merged_pr() -> int | None:
    """Highest merged PR number from recent origin/main history.

    Best-effort fetch first: fresh containers clone with a stale ``origin/main``
    ref, and reading it unfetched under-reports the latest PR (observed
    2026-06-12: reported #687 while live main was at #740). Offline or slow
    remotes degrade gracefully to the local ref.
    """
    try:
        subprocess.run(
            ["git", "fetch", "origin", "main", "--quiet"],
            capture_output=True,
            cwd=REPO_ROOT,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        pass
    try:
        result = subprocess.run(
            ["git", "log", "origin/main", "--pretty=format:%s", "-n", "60"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    numbers = [
        int(m.group(1) or m.group(2))
        for line in result.stdout.splitlines()
        if (m := _MERGE_SUBJECT_RE.search(line))
    ]
    return max(numbers) if numbers else None


def _last_reconcile_pr() -> int | None:
    """The PR number recorded in the current-state.md reconciliation marker."""
    try:
        text = CURRENT_STATE.read_text(encoding="utf-8")
    except OSError:
        return None
    match = _MARKER_RE.search(text)
    return int(match.group(1) or match.group(2)) if match else None


def is_due(
    latest: int | None = None,
    marker: int | None = None,
) -> tuple[bool, int | None, int | None]:
    """Return (due, latest_pr, marker_pr). Due once we cross a new multiple-of-STEP band."""
    if latest is None:
        latest = _latest_merged_pr()
    if marker is None:
        marker = _last_reconcile_pr()
    if latest is None or marker is None:
        return (False, latest, marker)
    return (latest // STEP > marker // STEP, latest, marker)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="reconciliation-cadence guard (Q-0107).",
    )
    parser.add_argument("--strict", action="store_true", help="exit 1 if a pass is due")
    parser.add_argument(
        "--issue-body",
        action="store_true",
        help="print the canonical `reconcile`-issue body and exit (the workflow echoes this)",
    )
    args = parser.parse_args(argv)

    if args.issue_body:
        print(issue_body())
        return 0

    due, latest, marker = is_due()
    if marker is None:
        print(
            "check_reconciliation_due: no `Last reconciliation pass:** PR #N` marker in "
            "current-state.md — add one to start the Q-0107 cadence.",
        )
        return 0
    next_band = (marker // STEP + 1) * STEP
    if due:
        print(
            f"check_reconciliation_due: DUE — merged PRs crossed #{next_band} "
            f"(last pass #{marker}, latest #{latest}). The docs-only reconciliation pass "
            "is run automatically by the routines (the `reconcile`-issue trigger); a "
            "manually-started session should NOT run it unless explicitly asked (Q-0124) "
            "— pursue the work you were started for. Reset the marker after a pass.",
        )
        return 1 if args.strict else 0
    print(
        f"check_reconciliation_due: not due (last pass #{marker}, latest #{latest}; "
        f"next pass at #{next_band}).",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
