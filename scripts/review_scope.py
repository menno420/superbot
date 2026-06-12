#!/usr/bin/env python3
"""Report the **review scope** of a file or a changed-file set.

Operationalizes ``docs/repo-review-map.md`` — instead of remembering the partition,
ask the tool:

    # one file -> its review unit
    python3.10 scripts/review_scope.py disbot/cogs/economy_cog.py

    # a whole change -> single-slice / multi-slice / platform / non-runtime
    python3.10 scripts/review_scope.py --diff                 # vs origin/main
    python3.10 scripts/review_scope.py --diff main
    git diff --name-only | python3.10 scripts/review_scope.py --stdin

Read-only and heuristic; it points at the binding docs when a call is ambiguous
(services don't map 1:1 to slices). The doc + ``ownership.md`` win over its guess.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from _review_units import ReviewUnit, classify_changeset, classify_path  # noqa: E402

REPO_ROOT = _SCRIPTS_DIR.parent


def _changed_paths(base: str) -> list[str]:
    """Files changed vs ``base`` (merge-base diff), best-effort."""
    try:
        out = subprocess.run(
            ["git", "diff", "--name-only", f"{base}...HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"review_scope: could not run git diff vs {base}: {exc}", file=sys.stderr)
        return []
    return [line for line in out.splitlines() if line.strip()]


def _print_file(path: str) -> int:
    unit: ReviewUnit = classify_path(path)
    print(f"{path}")
    print(f"  review unit : {unit.label()}")
    print(f"  domain      : {unit.domain}")
    if unit.detail:
        print(f"  note        : {unit.detail}")
    return 0


def _print_changeset(paths: list[str], show_files: bool) -> int:
    verdict = classify_changeset(paths)
    if verdict.verdict == "empty":
        print("review_scope: no changed paths.")
        return 0

    print(f"Review scope: {verdict.verdict.upper()}")
    if verdict.slices:
        print(f"  slices         : {', '.join(sorted(verdict.slices))}")
    if verdict.platform_layers:
        print(
            f"  platform layers: {', '.join(sorted(p for p in verdict.platform_layers if p))}",
        )
    print(f"  → {verdict.advice}")

    if show_files:
        print("\nFiles:")
        for path, unit in verdict.units:
            print(f"  {unit.label():<28} {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report a file's or change's review scope.",
    )
    parser.add_argument("path", nargs="?", help="A single file to classify.")
    parser.add_argument(
        "--diff",
        nargs="?",
        const="origin/main",
        metavar="BASE",
        help="Classify files changed vs BASE (default origin/main).",
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Classify newline-separated paths read from stdin.",
    )
    parser.add_argument(
        "--files",
        action="store_true",
        help="With --diff/--stdin, also list each file's unit.",
    )
    args = parser.parse_args(argv)

    if args.stdin:
        paths = [line for line in sys.stdin.read().splitlines() if line.strip()]
        return _print_changeset(paths, args.files)
    if args.diff is not None:
        return _print_changeset(_changed_paths(args.diff), args.files)
    if args.path:
        return _print_file(args.path)

    parser.error("give a PATH, or --diff [BASE], or --stdin")
    return 2  # pragma: no cover


if __name__ == "__main__":
    sys.exit(main())
