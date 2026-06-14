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

Range-scope (band-#800 false-green, structurally fixed 2026-06-14): this check used to
expand every ``#AAA-#BBB`` range it found *anywhere* in ``current-state.md`` into "present"
coverage, so a **forward-looking planning range** in the ``▶ Next action`` pointer — e.g.
naming the band the queue plans — masked that whole band the moment it merged, and the guard
reported green while the ledger was short (~14 substrate-kit / auto-merge PRs were hidden this
way). ``known_ledger_numbers`` now expands ranges **only** inside ``## Recently shipped`` (and
the whole archive); above that header only individual ``#N`` refs count. The convention
(reference the pass *by name*, never an inline range) stays good practice but is no longer
load-bearing. (Idea: ``docs/ideas/ledger-checker-range-scope-2026-06-13.md``.)

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

# Range-expansion is scoped to the ledger proper (this header onward) + the archive, so a
# forward-looking planning range in the ``▶ Next action`` pointer can't mask a merged band.
RECENTLY_SHIPPED_HEADER = "## Recently shipped"

# A PR reference in a commit subject: "Merge pull request #734" (GitHub web),
# "Merge PR #734: ..." (MCP merges with a custom title — the dominant style
# since 2026-06), or "title (#734)". The missing "PR #" alternative let five
# merged PRs (#753-#761) go invisible to this check while it reported green
# (caught by the 2026-06-12 night reconciliation pass).
_MERGE_SUBJECT_RE = re.compile(r"(?:pull request #|PR #|\(#)(\d+)")
# A standalone ledger reference: "#734", "PR #734", "**#734".
_LEDGER_REF_RE = re.compile(r"#(\d+)")
# A ledger range: "#715–#723" / "#715-#723" / "#715–723" (en-dash or hyphen).
_LEDGER_RANGE_RE = re.compile(r"#(\d+)\s*[–-]\s*#?(\d+)")


def ledger_pr_numbers(text: str, *, expand_ranges: bool = True) -> set[int]:
    """Every PR number a ledger references.

    With ``expand_ranges`` (default), ``#AAA–#BBB`` spans expand into every member.
    With ``expand_ranges=False`` only individual ``#N`` refs count (a range's two
    endpoints still match as individual refs, but its interior does not) — used for the
    portion of ``current-state.md`` *above* ``## Recently shipped`` so a forward-looking
    planning range in the ``▶ Next action`` pointer cannot mask a just-merged band.
    """
    numbers: set[int] = set()
    if expand_ranges:
        for lo, hi in _LEDGER_RANGE_RE.findall(text):
            a, b = int(lo), int(hi)
            if a <= b and b - a < 100:  # guard against a stray huge "range"
                numbers.update(range(a, b + 1))
    numbers.update(int(n) for n in _LEDGER_REF_RE.findall(text))
    return numbers


def _git_merged_pr_map(limit: int) -> dict[int, str]:
    """Recent merged PRs from origin/main as an ordered ``{number: merge-subject}`` map.

    Newest-first, de-duped (the first/newest subject wins for a repeated number).
    ``dict`` preserves insertion order, so ``list(map)`` recovers the newest-first
    number sequence ``_git_merged_pr_numbers`` returns. The subject is the merge-commit
    ``%s`` already in hand at extraction time — kept so callers can show *what* each
    missing PR did, not just its number (the manual ``git log --grep`` step every
    reconciliation pass otherwise runs by hand).
    """
    try:
        result = subprocess.run(
            ["git", "log", "origin/main", "--pretty=format:%s", "-n", str(limit * 4)],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
    except OSError:
        return {}
    if result.returncode != 0:
        return {}
    mapping: dict[int, str] = {}
    for subject in result.stdout.splitlines():
        match = _MERGE_SUBJECT_RE.search(subject)
        if match:
            pr = int(match.group(1))
            if pr not in mapping:
                mapping[pr] = subject.strip()
    return mapping


def _git_merged_pr_numbers(limit: int) -> list[int]:
    """Recent merged PR numbers from origin/main history, newest-first, de-duped."""
    return list(_git_merged_pr_map(limit))


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def known_ledger_numbers(
    current_state_text: str | None = None,
    archive_text: str | None = None,
) -> set[int]:
    """PR numbers the ledger covers, with range-expansion scoped to the ledger proper.

    Ranges expand **only** inside ``## Recently shipped`` (and the whole archive); above
    that header — the ``▶ Next action`` pointer and the status preamble — only individual
    ``#N`` refs count. This closes the band-#800 false-green: a forward-looking planning
    range written into the ``▶ Next action`` pointer (e.g. ``(band #781–#800)``) used to
    mark that whole band "present" the instant it merged, so the guard reported green while
    the ledger was ~14 entries short. The convention mitigation (reference the pass by name,
    never an inline range) stays good practice; this makes it structural.
    """
    cs = _read(CURRENT_STATE) if current_state_text is None else current_state_text
    archive = _read(ARCHIVE) if archive_text is None else archive_text
    head, sep, tail = cs.partition(RECENTLY_SHIPPED_HEADER)
    numbers = ledger_pr_numbers(head, expand_ranges=False)
    numbers |= ledger_pr_numbers(sep + tail, expand_ranges=True)
    numbers |= ledger_pr_numbers(archive, expand_ranges=True)
    return numbers


def find_missing(window: int = DEFAULT_WINDOW) -> list[int]:
    """Merged PRs in the recent window absent from current-state + archive."""
    recent = _git_merged_pr_numbers(window)[:window]
    known = known_ledger_numbers()
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

    # Show each missing PR's merge-commit subject so the reconciler can write an honest
    # ledger entry without the manual `git log --grep "#N"` loop (Q-0089 grooming idea).
    subjects = _git_merged_pr_map(args.window)
    print(
        f"check_current_state_ledger: {len(missing)} recent merged PR(s) not in "
        "current-state.md / current-state-archive.md:",
    )
    for pr in missing:
        subject = subjects.get(pr, "(no merge commit found — closed/unmerged?)")
        print(f"  - #{pr}  {subject}")
    print(
        "\nThis is the living-ledger drift class. Add each to docs/current-state.md "
        "§ Recently shipped (or archive) before closing the session "
        "(verify the #number against live GitHub first).",
    )
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
