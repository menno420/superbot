#!/usr/bin/env python3.10
"""Ledger drift guard — flag merged PRs absent from ``current-state.md``.

`docs/current-state.md` § "Recently shipped" is the living ledger of merged work, and
its recurring failure mode is **drift**: a session merges a PR and the ledger is never
updated (or a PR number is mislabeled). This happened on 2026-06-12 — #730/#733 were
missing and the untested-surface entry was mislabeled #730 (it was #731).

The session-log gate (`check_session_log.py`) made the *session log* self-checking for
the Q-0089/Q-0102 enders; this does the same for the *living ledger*: it reads the merged
PR numbers from git history and warns about recent ones that appear in neither
`current-state.md` nor `current-state-archive.md`.

Advisory by default (exit 0) like `check_doc_freshness.py` — a brand-new merge legitimately
lags the ledger by a session, so this must never hard-fail CI. Run `--strict` to gate
explicitly (e.g. from `/session-close`). Pure stdlib, like `check_docs.py`.

Reliability (Q-0105, added 2026-06-12): **unverified** — confirm its flags against live
GitHub across a few sessions before trusting it. If it proves unreliable (false positives
from an unusual commit-subject format, or a missed real drift) over multiple sessions,
**delete it** — it is a convenience guard, not load-bearing.

Usage:
    python3.10 scripts/check_current_state_ledger.py            # advisory report (exit 0)
    python3.10 scripts/check_current_state_ledger.py --strict   # exit 1 if drift found
    python3.10 scripts/check_current_state_ledger.py --window N # check the last N merges
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CURRENT_STATE = REPO_ROOT / "docs" / "current-state.md"
ARCHIVE = REPO_ROOT / "docs" / "current-state-archive.md"

DEFAULT_WINDOW = 15

# A PR reference in a commit subject: "Merge pull request #734" or "title (#734)".
_MERGE_SUBJECT_RE = re.compile(r"(?:pull request #|\(#)(\d+)")
# A standalone ledger reference: "#734", "PR #734", "**#734".
_LEDGER_REF_RE = re.compile(r"#(\d+)")
# A ledger range: "#715–#723" / "#715-#723" / "#715–723" (en-dash or hyphen).
_LEDGER_RANGE_RE = re.compile(r"#(\d+)\s*[–-]\s*#?(\d+)")


def ledger_pr_numbers(text: str) -> set[int]:
    """Every PR number a ledger references, expanding ``#AAA–#BBB`` ranges."""
    numbers: set[int] = set()
    for lo, hi in _LEDGER_RANGE_RE.findall(text):
        a, b = int(lo), int(hi)
        if a <= b and b - a < 100:  # guard against a stray huge "range"
            numbers.update(range(a, b + 1))
    numbers.update(int(n) for n in _LEDGER_REF_RE.findall(text))
    return numbers


def _git_merged_pr_numbers(limit: int) -> list[int]:
    """Recent merged PR numbers from origin/main history, newest-first, de-duped."""
    try:
        result = subprocess.run(
            ["git", "log", "origin/main", "--pretty=format:%s", "-n", str(limit * 4)],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
    except OSError:
        return []
    if result.returncode != 0:
        return []
    seen: list[int] = []
    for subject in result.stdout.splitlines():
        match = _MERGE_SUBJECT_RE.search(subject)
        if match:
            pr = int(match.group(1))
            if pr not in seen:
                seen.append(pr)
    return seen


def _ledger_text() -> str:
    parts: list[str] = []
    for f in (CURRENT_STATE, ARCHIVE):
        try:
            parts.append(f.read_text(encoding="utf-8"))
        except OSError:
            continue
    return "\n".join(parts)


def find_missing(window: int = DEFAULT_WINDOW) -> list[int]:
    """Merged PRs in the recent window absent from current-state + archive."""
    recent = _git_merged_pr_numbers(window)[:window]
    known = ledger_pr_numbers(_ledger_text())
    return [pr for pr in recent if pr not in known]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="current-state ledger drift guard.")
    parser.add_argument("--strict", action="store_true", help="exit 1 if drift found")
    parser.add_argument(
        "--window",
        type=int,
        default=DEFAULT_WINDOW,
        help=f"check the last N merged PRs (default {DEFAULT_WINDOW})",
    )
    args = parser.parse_args(argv)

    missing = find_missing(args.window)
    if not missing:
        print(
            f"check_current_state_ledger: last {args.window} merged PRs all present ✓",
        )
        return 0

    print(
        f"check_current_state_ledger: {len(missing)} recent merged PR(s) not in "
        "current-state.md / current-state-archive.md:",
    )
    for pr in missing:
        print(
            f"  - #{pr} (add to docs/current-state.md § Recently shipped, or archive)",
        )
    print(
        "\nThis is the living-ledger drift class. Reconcile before closing the session "
        "(verify the #number against live GitHub first).",
    )
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
