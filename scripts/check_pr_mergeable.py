#!/usr/bin/env python3.10
"""Git-based mergeability check for the *current branch* vs ``origin/main`` (stdlib, no GitHub).

WHY: in this remote-exec environment, GitHub's ``mergeable_state`` is **not trustworthy**. A push to
an existing PR branch intermittently fails to register, which leaves GitHub's *asynchronously*
computed mergeability stale — it can report ``dirty`` (conflict) for a branch that ``git`` merges
perfectly cleanly. Chasing that phantom ``dirty`` burned several sessions (the #1256 investigation:
``git merge-tree`` said CLEAN, GitHub said ``dirty``; the deterministic ``conflict-guard`` correctly
posted green). The lesson lives in ``.session-journal.md``: **trust the git computation, not
GitHub's signal.**

This is the agent-side companion to ``.github/workflows/pr-conflict-guard.yml``: the workflow posts
the ``conflict-guard`` commit status on GitHub (when it fires); this script answers the *same*
question locally, in one command, with no dependence on GitHub firing anything — so a session can
verify its own branch's true mergeability before opening a PR or after a push that may not have
registered. It reuses ``scripts/git_merge_state.py`` (the one deterministic source of truth shared
with the guards) so all three agree by construction.

Usage::

    python3.10 scripts/check_pr_mergeable.py                 # report current branch vs origin/main
    python3.10 scripts/check_pr_mergeable.py --strict        # exit 1 on a real conflict (DIRTY)
    python3.10 scripts/check_pr_mergeable.py --base origin/dev --no-fetch
    python3.10 scripts/check_pr_mergeable.py --head HEAD --base origin/main

Exit codes: report mode always 0. ``--strict`` exits 1 only on ``DIRTY`` (a true merge conflict);
``BEHIND`` is informational (out-of-date is not a conflict) and ``UNKNOWN`` never fails (don't
false-flag on a fetch/object hiccup) — the same conservative posture as the guards.

Provenance + reliability (Q-0105): added 2026-06-21, owner-directed (the #1256 false-``dirty``
finding). stdlib-only; verified by ``tests/unit/scripts/test_check_pr_mergeable.py``. Delete if it
ever disagrees with ``git`` ground truth across sessions.
"""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
from pathlib import Path
from types import ModuleType

_SCRIPT_DIR = Path(__file__).resolve().parent


def _load_merge_state() -> ModuleType:
    """Import the shared ``git_merge_state`` helper by path (scripts/ is not a package)."""
    path = _SCRIPT_DIR / "git_merge_state.py"
    spec = importlib.util.spec_from_file_location("git_merge_state", path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git_out(*args: str) -> str:
    """Run a git command, return stripped stdout ('' on failure)."""
    proc = subprocess.run(
        ["git", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    return proc.stdout.strip() if proc.returncode == 0 else ""


def _fetch(base: str) -> None:
    """Best-effort fetch of the base ref so the comparison is against live origin."""
    # `origin/main` -> remote `origin`, ref `main`. Bare ref -> fetch from origin.
    remote, _, ref = base.partition("/")
    if not ref:  # base was just a ref name, no remote prefix
        remote, ref = "origin", base
    subprocess.run(
        ["git", "fetch", "--quiet", "--no-tags", remote, ref],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def evaluate(base: str, head: str) -> tuple[str, str]:
    """Return ``(conflict_state, behind_state)`` for merging ``head`` into ``base``."""
    ms = _load_merge_state()
    return ms.conflict_state(base, head), ms.behind_state(base, head)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Git-based mergeability of the current branch vs origin/main "
        "(does NOT trust GitHub's async mergeable_state).",
    )
    parser.add_argument(
        "--base",
        default="origin/main",
        help="base revision (default origin/main)",
    )
    parser.add_argument("--head", default="HEAD", help="head revision (default HEAD)")
    parser.add_argument(
        "--no-fetch",
        action="store_true",
        help="skip fetching the base ref (use the local ref as-is)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 on a real conflict (DIRTY); report-only otherwise",
    )
    args = parser.parse_args(argv)

    if not args.no_fetch:
        _fetch(args.base)

    branch = _git_out("rev-parse", "--abbrev-ref", args.head) or args.head
    conflict, behind = evaluate(args.base, args.head)

    print(f"check_pr_mergeable: {branch} vs {args.base}")
    print(f"  conflict: {conflict}   (CLEAN = merges cleanly, DIRTY = real conflict)")
    print(f"  behind:   {behind}     (BEHIND = origin has commits you lack)")
    if conflict == "DIRTY":
        print(
            "  ⚠ real merge conflict — resolve with: "
            "git fetch origin main && git merge origin/main",
        )
    elif behind == "BEHIND":
        print("  • up-to-date check: merge origin/main to refresh (no conflict).")
    else:
        print(
            "  ✓ no conflict with the base branch (trust this over GitHub's mergeable_state).",
        )

    return 1 if (args.strict and conflict == "DIRTY") else 0


if __name__ == "__main__":
    raise SystemExit(main())
