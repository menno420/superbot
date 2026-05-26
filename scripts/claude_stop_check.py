#!/usr/bin/env python3
"""Stop hook: verify architecture on changed files when Claude finishes a turn.

Called by Claude Code on the Stop event (end of each assistant turn).
Only checks files changed vs origin/main so it stays fast.

Exit behaviour:
  0 — no errors (warnings are shown but do not block)
  1 — architecture errors found in changed files; Claude should fix before committing
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"


def _changed_py_files() -> bool:
    """Return True if any Python files under disbot/ changed vs origin/main."""
    for cmd in (
        ["git", "diff", "--name-only", "origin/main...HEAD"],
        ["git", "diff", "--name-only", "HEAD"],
    ):
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
        if result.returncode == 0 and result.stdout.strip():
            return any(
                line.strip().endswith(".py") and line.strip().startswith("disbot/")
                for line in result.stdout.splitlines()
            )
    return False


def main() -> int:
    if not _changed_py_files():
        return 0

    print("\n── stop-check ──────────────────────────────────────────────")

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "check_architecture.py"),
            "--changed-only",
            "--mode",
            "strict",
        ],
        cwd=REPO_ROOT,
    )

    if result.returncode != 0:
        print(
            "\n[stop-check] ✗ Architecture errors in changed files — "
            "fix before committing.\n",
            file=sys.stderr,
        )
        return 1

    print("[stop-check] ✓ Architecture check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
