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
import re
import subprocess
from fnmatch import fnmatch
from pathlib import Path
from typing import cast

_RS = "\x1e"  # record separator between commits
_US = "\x1f"  # unit separator between hash and subject

# The claim ledger (Q-0126) — the *earliest* duplicate-work signal: a claim line
# exists before any PR or commit does, so it catches overlap the merged-commit
# scan structurally cannot (the #1221 duplicate-reaction-roles-PR2 lesson).
_ACTIVE_WORK = Path(__file__).resolve().parents[1] / "docs" / "owner" / "active-work.md"

# A backtick token is a *path* (not a branch/component name) when it contains a
# "/" or ends in a source extension — and is not a branch ref.
_PATH_EXTS = (".py", ".sql", ".md", ".yml", ".yaml", ".json", ".ts", ".tsx", ".js")
_BRANCH_PREFIXES = ("claude/", "bot/", "origin/")
_BACKTICK = re.compile(r"`([^`]+)`")


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


# ---------------------------------------------------------------------------
# Claim-ledger scan (active-work.md)
# ---------------------------------------------------------------------------


def _norm_path(p: str) -> str:
    """Normalize for cross-comparison: drop a leading ``disbot/``, trailing ``/``.

    Claim lines write repo-relative paths inconsistently (``services/x.py`` vs
    ``disbot/services/x.py``); stripping the package prefix aligns both forms.
    """
    p = p.strip().rstrip("/")
    return p[len("disbot/") :] if p.startswith("disbot/") else p


def _is_path_token(tok: str) -> bool:
    if tok.startswith(_BRANCH_PREFIXES):
        return False
    return "/" in tok or tok.endswith(_PATH_EXTS)


def _paths_overlap(a: str, b: str) -> bool:
    """True when normalized paths ``a`` and ``b`` are the same or nest either way."""
    a, b = _norm_path(a), _norm_path(b)
    if not a or not b:
        return False
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def parse_claims(text: str) -> list[dict[str, object]]:
    """Parse the ``## Active claims`` block into ``{branch, summary, paths}`` entries.

    Pure (text in, structured out) so it is unit-testable without the real file.
    """
    lines = text.splitlines()
    try:
        start = next(
            i for i, ln in enumerate(lines) if ln.strip().lower() == "## active claims"
        )
    except StopIteration:
        return []
    block: list[str] = []
    for ln in lines[start + 1 :]:
        if ln.startswith("## "):  # next section ends the block
            break
        block.append(ln)

    claims: list[dict[str, object]] = []
    current: list[str] = []

    def _flush() -> None:
        if not current:
            return
        entry_text = " ".join(s.strip() for s in current).strip()
        tokens = _BACKTICK.findall(entry_text)
        branch = next((t for t in tokens if t.startswith(_BRANCH_PREFIXES)), "?")
        paths = [t for t in tokens if _is_path_token(t)]
        # The human-readable scope is the bold **...** title, when present.
        m = re.search(r"\*\*(.+?)\*\*", entry_text)
        summary = m.group(1) if m else entry_text[:80]
        claims.append({"branch": branch, "summary": summary, "paths": paths})

    for ln in block:
        if ln.lstrip().startswith("- "):  # new claim entry
            _flush()
            current = [ln]
        elif current:  # continuation line of the current claim
            current.append(ln)
    _flush()
    return claims


def scan_claims(
    scopes: list[str],
    claims: list[dict[str, object]],
) -> dict[str, list[dict[str, object]]]:
    """Map each scope -> the active claims whose declared paths overlap it."""
    hits: dict[str, list[dict[str, object]]] = {}
    for scope in scopes:
        matched: list[dict[str, object]] = []
        for claim in claims:
            paths = cast("list[str]", claim["paths"])
            overlap = [p for p in paths if _paths_overlap(p, scope)]
            if overlap:
                matched.append({**claim, "matched": overlap})
        if matched:
            hits[scope] = matched
    return hits


def _load_claims() -> list[dict[str, object]]:
    try:
        return parse_claims(_ACTIVE_WORK.read_text(encoding="utf-8"))
    except OSError:
        return []


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
    "\n  NOTE: this covers the recently-MERGED commits (local git) + the active-work.md "
    "claim ledger. The OPEN-PR half (a concurrent unmerged PR with no claim line) still "
    "needs GitHub — ALSO run `list_pull_requests`."
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
    claim_hits = scan_claims(args.scopes, _load_claims())

    if not hits and not claim_hits:
        print(
            f"check_lane_overlap: no recently-merged commit (last {args.limit}) and no "
            f"active-work.md claim touch {', '.join(args.scopes)} ✓" + _FOOTER,
        )
        return 0

    if claim_hits:
        print(
            "check_lane_overlap: ⚠ CLAIMED — this scope is claimed by a parallel session "
            "in active-work.md. Coordinate or pick another lane before building:\n",
        )
        for scope, claims in claim_hits.items():
            print(f"  scope `{scope}`:")
            for claim in claims:
                shown = ", ".join(cast("list[str]", claim["matched"])[:4])
                print(f"    {claim['branch']}  {claim['summary']}")
                print(f"             ↳ {shown}")
        print()

    if hits:
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
    return 1 if (args.strict and (hits or claim_hits)) else 0


if __name__ == "__main__":
    raise SystemExit(main())
