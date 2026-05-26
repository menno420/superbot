#!/usr/bin/env python3
"""Stop hook: hard-fail gate before Claude returns control to the user.

Called by Claude Code on the Stop event (end of each assistant turn).
Runs check-only verification on Python files changed vs origin/main:

  1. Architecture (strict)  — layer boundaries, SQL location, etc.
  2. Black --check          — formatting
  3. isort --check-only     — import ordering
  4. Ruff check (no --fix)  — lint
  5. Mypy (changed files)   — types

All are hard failures — exit 1 surfaces in chat and Claude must fix
before committing. The post-edit hook auto-fixes black/isort/ruff on
write, so a Stop-time failure here means either (a) a fix could not be
auto-applied or (b) something was edited outside the hook path.

Pytest is NOT run here — it is too slow per turn. The hook prints the
exact command to run the full pre-PR suite manually before pushing.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"

# CI runs Python 3.10 — match it locally to avoid version-drift
# false negatives (see PR #338: mypy passed under 3.11 because a
# transitively missing package was treated as Any).
PY = "python3.10" if shutil.which("python3.10") else sys.executable


def _changed_disbot_files() -> list[str]:
    """Return Python files under disbot/ changed vs origin/main (plus dirty WC)."""
    seen: set[str] = set()
    for cmd in (
        ["git", "diff", "--name-only", "origin/main...HEAD"],
        ["git", "diff", "--name-only", "HEAD"],
    ):
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
        if result.returncode != 0:
            continue
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.endswith(".py") and line.startswith("disbot/"):
                seen.add(line)
    return sorted(seen)


def _run(label: str, cmd: list[str]) -> tuple[bool, str]:
    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    ok = result.returncode == 0
    output = (result.stdout + result.stderr).strip()
    return ok, output


def main() -> int:
    changed = _changed_disbot_files()
    if not changed:
        return 0

    print("\n── stop-check ──────────────────────────────────────────────", file=sys.stderr)

    checks: list[tuple[str, list[str]]] = [
        (
            "architecture",
            [
                PY,
                str(SCRIPTS / "check_architecture.py"),
                "--changed-only",
                "--mode",
                "strict",
            ],
        ),
        (
            "black --check",
            [PY, "-m", "black", "--check", "--quiet", *changed],
        ),
        (
            "isort --check",
            [PY, "-m", "isort", "--check-only", "--quiet", *changed],
        ),
        (
            "ruff check",
            [PY, "-m", "ruff", "check", *changed],
        ),
        (
            "mypy",
            [PY, "-m", "mypy", *changed],
        ),
    ]

    failures: list[tuple[str, str]] = []
    for label, cmd in checks:
        ok, output = _run(label, cmd)
        if ok:
            print(f"  ✓ {label}", file=sys.stderr)
        else:
            print(f"  ✗ {label}", file=sys.stderr)
            failures.append((label, output[:1500]))

    if failures:
        print(
            "\n[stop-check] HARD FAILURE — fix before pushing:\n",
            file=sys.stderr,
        )
        for label, output in failures:
            print(f"── {label} ─────────────────────────────────────", file=sys.stderr)
            print(output, file=sys.stderr)
            print("", file=sys.stderr)
        print(
            "Run the full pre-PR suite to mirror CI before pushing:\n"
            f"  {PY} scripts/check_quality.py --check-only\n"
            f"  {PY} -m pytest tests/ -q\n",
            file=sys.stderr,
        )
        return 1

    print(
        "\n[stop-check] ✓ all changed-file checks passed. Run the full "
        f"suite before pushing:\n  {PY} scripts/check_quality.py --check-only "
        f"&& {PY} -m pytest tests/ -q\n",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
