#!/usr/bin/env python3.10
"""Reconciliation-cadence guard — flag when a docs-only review/planning pass is due.

Owner directive Q-0107: PR numbers crossing a **multiple of 20** (#20, #40, #60, …) are
reserved for a **docs-only repo review + planning-reconciliation** pass — review the state
of the repo (ledger, active lanes, open Q-blocks, idea backlog, roadmap), prune stale docs,
and refocus the next priorities. This guard tracks the cadence against the
``Last reconciliation pass:** PR #N`` marker in ``docs/current-state.md``: a pass is **due**
once merged PRs have crossed into a new multiple-of-20 band since the last marked pass.
(Cadence raised 10 → 20 on 2026-06-12, owner-directed: small PRs inflate the count, so every
10 fired too often; the band size is the ``STEP`` constant below — retune there.)

The marker is read from **origin/main as well as the working tree** (max of the two), so a
reconciliation the autonomous routine already merged on main is not re-flagged as "due" when
a continuation session starts on a branch that predates it (the 2026-06-13 stale-branch
false-positive). Always ``git fetch origin main`` at session start before trusting the local
ledger — a routine may have moved the world on.

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

STEP = 20  # the cadence: a pass per multiple-of-20 PR band (raised from 10, 2026-06-12)

_MARKER_RE = re.compile(r"Last reconciliation pass:\*\*\s*PR #(\d+)")
# Match all three merge-subject styles in this repo's history:
# "Merge pull request #N" (GitHub web), "Merge PR #N: …" (MCP merges with a
# custom title — the dominant style since 2026-06), and "title (#N)" suffixes.
# The missing "PR #" alternative made the checker under-report the latest PR
# (stuck at #751 while #762 was merged — caught by the 2026-06-12 night pass).
_MERGE_SUBJECT_RE = re.compile(r"(?:pull request #|PR #|\(#)(\d+)")


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
        int(m.group(1))
        for line in result.stdout.splitlines()
        if (m := _MERGE_SUBJECT_RE.search(line))
    ]
    return max(numbers) if numbers else None


def _marker_in(text: str) -> int | None:
    """Extract the reconciliation-marker PR number from current-state text."""
    match = _MARKER_RE.search(text)
    return int(match.group(1)) if match else None


def _marker_local() -> int | None:
    """The reconciliation marker in the working-tree current-state.md."""
    try:
        return _marker_in(CURRENT_STATE.read_text(encoding="utf-8"))
    except OSError:
        return None


def _marker_on_ref(ref: str) -> int | None:
    """The reconciliation marker in ``<ref>:docs/current-state.md`` (or None)."""
    try:
        result = subprocess.run(
            ["git", "show", f"{ref}:docs/current-state.md"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return _marker_in(result.stdout)


def _last_reconcile_pr() -> int | None:
    """Highest reconciliation marker across the working tree AND origin/main.

    Read from BOTH the local file and ``origin/main``, taking the max. Rationale
    (2026-06-13): the autonomous reconciliation routine resets the marker in a PR
    that merges to main; a continuation session whose branch predates that merge
    would otherwise read only its **stale local** marker and report a FALSE 'due'
    — the routine already did the pass. Reading origin/main too (the same source
    ``_latest_merged_pr`` already trusts and fetches) makes a routine-completed
    pass visible before the local branch syncs; local is still considered so an
    in-progress reconciliation (marker bumped, not yet merged) also counts.
    """
    markers = [
        m for m in (_marker_local(), _marker_on_ref("origin/main")) if m is not None
    ]
    return max(markers) if markers else None


def is_due(
    latest: int | None = None,
    marker: int | None = None,
) -> tuple[bool, int | None, int | None]:
    """Return (due, latest_pr, marker_pr). Due once we cross a new multiple-of-10 band."""
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
    args = parser.parse_args(argv)

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
            f"(last pass #{marker}, latest #{latest}). The next session should be a "
            "docs-only repo review + planning reconciliation; reset the marker after.",
        )
        return 1 if args.strict else 0
    print(
        f"check_reconciliation_due: not due (last pass #{marker}, latest #{latest}; "
        f"next pass at #{next_band}).",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
