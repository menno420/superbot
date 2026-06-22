#!/usr/bin/env python3.10
"""Guard: a branch's new migrations must not collide with ``origin/main``'s numbers.

Migrations are ``NNN_name.sql`` numbered off a **single shared append point** (the
next free integer above the highest on ``main``). Under the fast multi-session fleet,
several in-flight PRs pick the *same* next number; whichever merges first wins and the
rest now carry a **duplicate** number against ``main``. CI tests the *merge result*
(``refs/pull/N/merge``) so it goes red — but a branch-only local ``check_quality.py
--full`` passes (it never merges with ``main``), so the author gets green-local /
red-CI with no obvious cause. #1279's migration was renumbered **four times** this way.

This guard closes that gap: run it before pushing a migration-bearing branch and it
compares the branch's *new* migration numbers against ``origin/main``, printing the
next free number + the exact ``git mv`` to renumber — one local one-liner instead of a
4-round CI treadmill.

Stdlib-only, read-only (it never fetches or writes). If ``origin/main`` isn't present
locally it says so and exits 0 (can't determine the base — run ``git fetch origin main``).
Exit 0 = no collision / undetermined; exit 1 = a collision (prints the fix).

Run:  python3.10 scripts/check_migration_collision.py

UNVERIFIED (Q-0105, 2026-06-22): confirm its output against a real collision a few times
before trusting it; delete this script if it proves unreliable over multiple sessions —
it is a convenience guard, the migration runner is the source of truth.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Directories whose ``NNN_*.sql`` files share one numbering space each.
MIGRATION_DIRS = ("disbot/migrations", "botsite/migrations")

_NUM = re.compile(r"^(\d+)_")


def parse_number(filename: str) -> int | None:
    """``089_role_menu_card.sql`` → ``89`` (``None`` if it isn't an ``NNN_`` migration)."""
    m = _NUM.match(filename)
    return int(m.group(1)) if m else None


@dataclass
class Collision:
    filename: str
    number: int
    suggested: int


@dataclass
class Report:
    directory: str
    collisions: list[Collision] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.collisions


def analyze(directory: str, base_files: set[str], head_files: set[str]) -> Report:
    """Pure core: which of the branch's *added* migrations collide with the base set?

    A collision is a file the branch **adds** (present on HEAD, absent on the base)
    whose number already exists in the base. The suggestion is the next free number
    above everything seen, advancing past numbers already taken or already suggested.
    """
    base_numbers = {n for f in base_files if (n := parse_number(f)) is not None}
    head_numbers = {n for f in head_files if (n := parse_number(f)) is not None}
    added = head_files - base_files

    taken = base_numbers | head_numbers
    cursor = (max(taken) + 1) if taken else 1
    report = Report(directory=directory)
    for filename in sorted(added):
        number = parse_number(filename)
        if number is None or number not in base_numbers:
            continue
        while cursor in taken:
            cursor += 1
        report.collisions.append(Collision(filename, number, cursor))
        taken.add(cursor)
        cursor += 1
    return report


def _git_basenames(ref: str, directory: str) -> set[str] | None:
    """``.sql`` basenames under ``directory`` at a git ``ref`` (``None`` if ref absent)."""
    try:
        out = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", ref, "--", directory],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return {
        Path(line).name
        for line in out.stdout.splitlines()
        if line.strip().endswith(".sql")
    }


def _worktree_basenames(directory: str) -> set[str]:
    path = REPO_ROOT / directory
    if not path.is_dir():
        return set()
    return {p.name for p in path.glob("*.sql")}


def _suggest(collision: Collision, directory: str) -> str:
    old = f"{directory}/{collision.filename}"
    new = f"{directory}/{collision.filename.replace(str(collision.number).zfill(3), str(collision.suggested).zfill(3), 1)}"
    return f"  git mv {old} {new}"


def main(base_ref: str = "origin/main") -> int:
    any_base = False
    reports: list[Report] = []
    for directory in MIGRATION_DIRS:
        base = _git_basenames(base_ref, directory)
        if base is None:
            continue
        any_base = True
        reports.append(analyze(directory, base, _worktree_basenames(directory)))

    if not any_base:
        print(
            f"check_migration_collision: base ref {base_ref!r} not found — "
            "run `git fetch origin main` to enable the check (skipping, exit 0).",
        )
        return 0

    collided = [r for r in reports if not r.ok]
    if not collided:
        print(f"✓ no migration-number collisions vs {base_ref}")
        return 0

    print(f"Migration-number collision vs {base_ref} — renumber before pushing:")
    for report in collided:
        for c in report.collisions:
            print(
                f"  ✗ {report.directory}/{c.filename}: {c.number:03d} already on "
                f"{base_ref} — use {c.suggested:03d}",
            )
            print(_suggest(c, report.directory))
    print(
        "\nWhy: CI tests the branch *merged with* main, so a duplicate number reddens "
        "the migration tests even though a branch-only local run passes.",
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
