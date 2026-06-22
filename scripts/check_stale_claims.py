#!/usr/bin/env python3.10
"""check_stale_claims.py — flag (or prune) per-claim files whose work already landed.

PROVENANCE / RELIABILITY (2026-06-22, owner decision Q-0195 — the GC half of the
one-file-per-claim claim ledger):
    Why: claims now live as one file per claim under ``docs/owner/claims/`` (the single
    shared ``active-work.md`` produced a ~98% merge-conflict rate — see
    ``tools/sim/claim_layout_sim.py``). A session is expected to DELETE its own claim file
    at close, so day-to-day the directory stays tiny. This script is the *failsafe*: the
    docs-reconciliation pass (Q-0107, every 30th PR) runs it to GC any orphan a session
    forgot to delete, so the directory can never accumulate.

    UNVERIFIED — heuristic. "Stale" = the claim's branch is **gone from origin** OR **fully
    merged into origin/main**. The merged/gone probes need a reasonably fresh clone (the
    routine fetches first). Confirm its verdicts across a few passes before wiring it to
    auto-prune anything; **delete this script if it proves unreliable.** Default is
    report-only (exit 0); ``--strict`` exits 1 when stale files exist; ``--prune`` deletes
    them (reconciliation routine, after eyeballing the list).

Usage:
    check_stale_claims.py [--strict] [--prune]
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

_CLAIMS_DIR = Path(__file__).resolve().parents[1] / "docs" / "owner" / "claims"
_BACKTICK_BRANCH = "claude/"


def claim_files() -> list[Path]:
    """Every live claim file (``README.md`` excluded)."""
    if not _CLAIMS_DIR.is_dir():
        return []
    return [
        p for p in sorted(_CLAIMS_DIR.glob("*.md")) if p.name.lower() != "readme.md"
    ]


def branch_of(text: str) -> str | None:
    """Extract the first ``claude/…`` branch token from a claim file's body."""
    for chunk in text.split("`"):
        if chunk.startswith(_BACKTICK_BRANCH):
            return chunk.strip()
    return None


def _git_ok(*args: str) -> bool:
    """Run a git command; True on exit 0 (errors are treated as 'no')."""
    return (
        subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
        ).returncode
        == 0
    )


def _branch_gone(branch: str) -> bool:
    """The remote head no longer exists (PR merged + branch deleted)."""
    return not _git_ok("ls-remote", "--exit-code", "--heads", "origin", branch)


def _branch_merged(branch: str) -> bool:
    """Every commit on the remote branch is already in origin/main."""
    return _git_ok("merge-base", "--is-ancestor", f"origin/{branch}", "origin/main")


def default_state_fn(branch: str) -> str:
    """Real-git classifier: ``gone`` / ``merged`` / ``active``."""
    if _branch_gone(branch):
        return "gone"
    if _branch_merged(branch):
        return "merged"
    return "active"


def find_stale(files, state_fn):
    """Pure: map each claim file -> reason, for files whose branch is gone/merged.

    ``state_fn(branch) -> 'gone'|'merged'|'active'`` is injected so this is testable
    without git. A file with no parseable branch is left alone (never auto-pruned).
    """
    stale: list[tuple[Path, str, str]] = []
    for path in files:
        try:
            branch = branch_of(path.read_text(encoding="utf-8"))
        except OSError:
            continue
        if not branch:
            continue
        state = state_fn(branch)
        if state in ("gone", "merged"):
            stale.append((path, branch, state))
    return stale


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--strict", action="store_true", help="exit 1 if any stale claim")
    ap.add_argument("--prune", action="store_true", help="delete stale claim files")
    args = ap.parse_args()

    files = claim_files()
    stale = find_stale(files, default_state_fn)

    if not stale:
        print(f"check_stale_claims: {len(files)} claim file(s), none stale ✓")
        return 0

    print(f"check_stale_claims: {len(stale)} stale claim file(s):")
    for path, branch, state in stale:
        print(f"  {path.relative_to(_CLAIMS_DIR.parents[2])}  ({branch} — {state})")
        if args.prune:
            path.unlink()
            print("    ↳ pruned")

    if args.prune:
        print("Pruned. Commit the deletions with the reconciliation pass.")
        return 0
    return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
