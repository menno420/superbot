#!/usr/bin/env python3.10
"""check_lane_overlap.py — before starting work on a scope, flag whether that scope was
already touched by *recently-merged* work (the #1133/#1128 duplicate-work lesson).

PROVENANCE / RELIABILITY (2026-06-19, mechanizes ultracode-fleet-plan rule #7 / the #1137
fleet-dispatch overlap-check rule):
    Why: lane B4 (PR #1133) rebuilt the consistency-linter cog-scope work that #1128 had
    merged ~8 minutes earlier, because the orchestrator trusted a stale claim ledger instead
    of scanning what had actually shipped. The fleet's fix was a *procedural* "MUST scan
    recent PRs" rule — but the incident happened *because* a manual step got skipped. This
    gives that rule teeth: a script the orchestrator runs so overlap-detection doesn't depend
    on memory.

    UNVERIFIED — heuristic, and **partial by construction**: it sees only the *recently-merged*
    half (local git history). The *open-PR* half (a concurrent unmerged PR touching the same
    files) needs GitHub and CANNOT be checked locally — always ALSO run `list_pull_requests`.
    Confirm its hits across a few sessions; **delete it if it proves noisy/unreliable.**

Usage:
    check_lane_overlap.py <scope> [<scope> ...] [--limit N] [--strict]

    <scope>  — files / directories / globs the lane will touch
               (e.g. `scripts/check_consistency.py`, `disbot/views/mining/`, `disbot/**/fish*`).
    --limit  — how many recent commits to scan (default 80 — ~2 burst bands).
    --strict — exit 1 if any overlap is found (for a dispatch gate once trusted).
"""

from __future__ import annotations

import argparse
import subprocess
from fnmatch import fnmatch

_RS = "\x1e"  # record separator between commits
_US = "\x1f"  # unit separator between hash and subject


def _recent_commits(limit: int) -> list[tuple[str, str, list[str]]]:
    """Return [(short_hash, subject, [changed_files])] for the last *limit* commits."""
    out = subprocess.run(
        ["git", "log", f"-n{limit}", "--name-only", f"--format={_RS}%h{_US}%s"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    commits: list[tuple[str, str, list[str]]] = []
    for record in out.split(_RS):
        if not record.strip():
            continue
        lines = record.split("\n")
        short_hash, _, subject = lines[0].partition(_US)
        files = [ln for ln in lines[1:] if ln.strip()]
        commits.append((short_hash, subject, files))
    return commits


def _matches(path: str, scope: str) -> bool:
    """A changed *path* belongs to *scope* (an exact file, a dir prefix, or a glob)."""
    scope = scope.rstrip("/")
    if path == scope or path.startswith(scope + "/"):
        return True
    return any(ch in scope for ch in "*?[") and fnmatch(path, scope)


def scan(scopes: list[str], limit: int) -> dict[str, list[tuple[str, str, list[str]]]]:
    """Map each scope -> the recent commits whose files overlap it."""
    commits = _recent_commits(limit)
    hits: dict[str, list[tuple[str, str, list[str]]]] = {}
    for scope in scopes:
        overlaps = []
        for short_hash, subject, files in commits:
            matched = [f for f in files if _matches(f, scope)]
            if matched:
                overlaps.append((short_hash, subject, matched))
        if overlaps:
            hits[scope] = overlaps
    return hits


_FOOTER = (
    "\n  NOTE: this covers the recently-MERGED half only (local git). The OPEN-PR half "
    "(a concurrent unmerged PR on the same files) needs GitHub — ALSO run `list_pull_requests`."
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "scopes",
        nargs="+",
        help="files / dirs / globs the lane will touch",
    )
    ap.add_argument(
        "--limit",
        type=int,
        default=80,
        help="recent commits to scan (default 80)",
    )
    ap.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 if any overlap is found (dispatch gate)",
    )
    args = ap.parse_args()

    hits = scan(args.scopes, args.limit)
    if not hits:
        print(
            f"check_lane_overlap: no recently-merged commit (last {args.limit}) touched "
            f"{', '.join(args.scopes)} ✓" + _FOOTER,
        )
        return 0

    print(
        "check_lane_overlap: ⚠ OVERLAP — this scope was touched by recently-merged work. "
        "Verify it didn't already ship your lane (drop/re-scope before dispatch):\n",
    )
    for scope, overlaps in hits.items():
        print(f"  scope `{scope}`:")
        for short_hash, subject, matched in overlaps:
            shown = ", ".join(matched[:4])
            more = "" if len(matched) <= 4 else f" (+{len(matched) - 4})"
            print(f"    {short_hash}  {subject[:72]}")
            print(f"             ↳ {shown}{more}")
    print(_FOOTER)
    return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
