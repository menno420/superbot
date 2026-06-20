#!/usr/bin/env python3.10
"""Deterministic git merge-state for the PR CI guards (no GitHub async mergeability).

Single source of truth for the merge-state decision shared by
``.github/workflows/pr-conflict-guard.yml`` and ``.github/workflows/pr-auto-update.yml``. Both used
to read GitHub's *asynchronously-computed* ``mergeStateStatus``, which is ``UNKNOWN`` for seconds
after a push (the query is what triggers recomputation) and caused a recurring flake — the conflict
guard skipped freshly-DIRTY PRs (fixed PR #1187) and auto-update skipped freshly-BEHIND PRs (fixed
PR #1188). This computes the answer **locally with git** instead, so it is decided the instant it
runs, with no async window and no race.

Because the logic kept getting re-broken (each fix reached back for the async field), it lives here
as one importable/CLI unit pinned by ``tests/unit/scripts/test_git_merge_state.py`` — a future edit
that regresses it fails CI instead of silently shipping.

Usage (operates on the CURRENT git repo; ``base``/``head`` are any revisions already present
locally — the workflows fetch them before calling)::

    python3 scripts/git_merge_state.py conflict <base> <head>   # -> CLEAN | DIRTY | UNKNOWN
    python3 scripts/git_merge_state.py behind   <base> <head>   # -> BEHIND | CURRENT | UNKNOWN

``conflict`` — does merging ``head`` with ``base`` conflict? ``git merge-tree --write-tree`` exits
0 = clean, 1 = conflict. Both revisions are verified to exist first: a *missing* object also exits
1, which would otherwise false-flag a conflict, so that case returns ``UNKNOWN``.

``behind`` — is ``head`` missing commits that are on ``base``? ``BEHIND`` iff ``base`` is **not** an
ancestor of ``head`` (``git merge-base --is-ancestor``). If ``base`` is an ancestor, ``head`` already
contains it (``CURRENT``).

Provenance + reliability (Q-0105): added 2026-06-20, owner-directed (continuing the #1187/#1188
fixes). Verified by the temp-repo tests cited above. stdlib-only. Delete only if both guards are
retired.
"""

from __future__ import annotations

import subprocess
import sys


def _git(*args: str) -> int:
    """Run a git command in the current repo, return its exit code (output discarded)."""
    return subprocess.run(
        ["git", *args],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode


def _exists(rev: str) -> bool:
    """True if ``rev`` resolves to a commit object in the current repo."""
    return _git("cat-file", "-e", f"{rev}^{{commit}}") == 0


def conflict_state(base: str, head: str) -> str:
    """CLEAN / DIRTY / UNKNOWN — does merging ``head`` into ``base`` conflict?"""
    if not (_exists(base) and _exists(head)):
        return "UNKNOWN"
    rc = _git("merge-tree", "--write-tree", base, head)
    if rc == 0:
        return "CLEAN"
    if rc == 1:
        return "DIRTY"
    return "UNKNOWN"  # merge-tree error (rc > 1) — don't false-flag


def behind_state(base: str, head: str) -> str:
    """BEHIND / CURRENT / UNKNOWN — is ``head`` missing commits that are on ``base``?"""
    if not (_exists(base) and _exists(head)):
        return "UNKNOWN"
    rc = _git("merge-base", "--is-ancestor", base, head)
    if rc == 0:
        return "CURRENT"  # base is an ancestor of head -> head already contains base
    if rc == 1:
        return "BEHIND"
    return "UNKNOWN"  # is-ancestor error (rc > 1)


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[0] not in ("conflict", "behind"):
        print(
            "usage: git_merge_state.py {conflict|behind} <base> <head>",
            file=sys.stderr,
        )
        return 2
    mode, base, head = argv
    state = (
        conflict_state(base, head) if mode == "conflict" else behind_state(base, head)
    )
    print(state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
