#!/usr/bin/env python3.10
"""Resolve merge conflicts on committed *generated* artifacts (stdlib only, tooling only).

The 2-hourly ``dashboard-data-refresh.yml`` workflow lands
``chore(dashboard): refresh generated data`` merges on ``main``, so any open branch
that also regenerated ``dashboard/data/dashboard.json`` (+ the botsite exports —
routine guard collateral) re-conflicts on those files at **every** refresh merge.
PR #2061 hit this three times overnight 2026-07-12→13. The files are pure generator
output (``scripts/export_dashboard_data.py`` is the single producer; nobody
hand-edits them), so a text-level merge of them is *meaningless* — the only correct
resolution is: clear the conflict, then **regenerate from the merged sources**.

This script codifies that known-working recipe so every agent resolves identically::

    python3.10 scripts/resolve_generated_conflicts.py            # do it
    python3.10 scripts/resolve_generated_conflicts.py --dry-run  # show what it would do

Steps (merge in progress, conflicts present):

1. Find conflicted paths (``git diff --name-only --diff-filter=U``) and intersect
   with the generated-artifact registry below.
2. ``git checkout --theirs -- <those paths>`` — take the incoming side wholesale
   (valid JSON baseline; no markers). During a **rebase** the meaning of
   theirs/ours inverts, so there ``--ours`` is the incoming/upstream side and is
   used instead.
3. Re-run the producer (``scripts/export_dashboard_data.py``) so the artifacts are
   rebuilt from the *merged* working tree — the sources (``.sessions/``, ``docs/``,
   ``disbot/``) at merge time already contain both sides, so the regenerated output
   is the true post-merge artifact.
4. ``git add`` the resolved paths and report any *remaining* (non-generated)
   conflicts, which you resolve normally.

Deliberately **not** solved with git attributes — both were tested empirically
(2026-07-13, real ``dashboard.json`` versions from commits ``df5ee69`` /
``cce250f`` / ``a1c95fb~1``):

* ``merge=union`` exits 0 but **corrupts the JSON** (both sides' lines kept →
  duplicate ``meta.generated_at`` / ``build`` keys, unbalanced braces;
  ``json.load`` fails). Never apply union to these files.
* A custom merge driver needs per-clone ``git config merge.<name>.driver`` —
  which fresh agent clones never have (git then silently falls back to the normal
  conflicting merge; verified) — and GitHub's server-side merges never run custom
  drivers at all.

Full recipe + evidence: ``docs/operations/generated-data-merge-recipe.md``.

**Never imported by bot runtime** — pure dev tooling; zero runtime behavior change.

Reliability (Q-0105): added 2026-07-13 (session ``claude/dashboard-conflict-recipe``).
**Unverified** — confirm its resolutions against a by-hand take-theirs+regen a few
times across sessions before trusting it, and **delete this script if it proves
unreliable** over multiple sessions rather than working around it; the manual recipe
in the doc above always works.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# The committed artifacts produced by scripts/export_dashboard_data.py (the single
# producer for both web tiers). Keep in sync with that script's *_OUTPUT_FILE
# constants. The *contract* JSONs (dashboard_data_contract.json /
# site_data_contract.json / console_data_contract.json) are deliberately EXCLUDED:
# they are hand-versioned, so a conflict there is a real semantic conflict that
# must be merged by a human/agent, never auto-taken.
GENERATED_PATHS: tuple[str, ...] = (
    "dashboard/data/dashboard.json",
    "botsite/data/site.json",
    "botsite/data/console.json",
    "botsite/site/data.js",
)

EXPORTER = REPO_ROOT / "scripts" / "export_dashboard_data.py"


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _git_dir() -> Path:
    proc = _git("rev-parse", "--git-dir")
    return (REPO_ROOT / proc.stdout.strip()).resolve()


def _conflicted_paths() -> list[str]:
    proc = _git("diff", "--name-only", "--diff-filter=U")
    return [line for line in proc.stdout.splitlines() if line.strip()]


def _python() -> str:
    """CI parity prefers python3.10; the exporter is stdlib-only so any 3.10+ works."""
    return shutil.which("python3.10") or sys.executable


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report what would be resolved/regenerated without changing anything",
    )
    args = parser.parse_args(argv)

    git_dir = _git_dir()
    merging = (git_dir / "MERGE_HEAD").exists()
    rebasing = (git_dir / "rebase-merge").exists() or (
        git_dir / "rebase-apply"
    ).exists()
    if not merging and not rebasing:
        print("No merge or rebase in progress — nothing to resolve.")
        print("(Run this while a `git merge origin/main` sits in conflict.)")
        return 0

    conflicted = _conflicted_paths()
    targets = [p for p in conflicted if p in GENERATED_PATHS]
    others = [p for p in conflicted if p not in GENERATED_PATHS]

    if not targets:
        print("No generated-artifact conflicts found.")
        if others:
            print("Remaining conflicts (resolve normally):")
            for path in others:
                print(f"  {path}")
        return 0

    # In a merge, --theirs is the incoming side (e.g. origin/main's refresh).
    # In a rebase, sides invert: --ours is the upstream/incoming side.
    side = "--theirs" if merging else "--ours"
    print(f"Generated-artifact conflicts ({'merge' if merging else 'rebase'}):")
    for path in targets:
        print(f"  {path}")

    if args.dry_run:
        print(f"[dry-run] would: git checkout {side} -- <paths above>;")
        print(
            f"[dry-run] then: {_python()} {EXPORTER.relative_to(REPO_ROOT)}; git add."
        )
        return 0

    checkout = _git("checkout", side, "--", *targets)
    if checkout.returncode != 0:
        print(f"git checkout {side} failed:\n{checkout.stderr}", file=sys.stderr)
        print("(A delete/modify conflict needs manual resolution.)", file=sys.stderr)
        return 1

    regen = subprocess.run(
        [_python(), str(EXPORTER)],
        cwd=REPO_ROOT,
        check=False,
    )
    if regen.returncode != 0:
        print(
            "export_dashboard_data.py failed — the taken side is still staged-able "
            "valid JSON, but regenerate before landing.",
            file=sys.stderr,
        )
        return 1

    add = _git("add", "--", *targets)
    if add.returncode != 0:
        print(f"git add failed:\n{add.stderr}", file=sys.stderr)
        return 1

    print("Resolved + regenerated + staged:")
    for path in targets:
        print(f"  {path}")
    if others:
        print("Remaining conflicts (resolve normally):")
        for path in others:
            print(f"  {path}")
    else:
        print(
            "No other conflicts — continue the merge (git commit / git merge --continue)."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
