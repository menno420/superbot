#!/usr/bin/env python3
"""PostToolUse hook: auto-format the just-edited Python file.

Called by Claude Code after every Edit or Write tool use.
The file path is read from CLAUDE_TOOL_INPUT_FILE_PATH.

Runs black → isort → ruff --fix on the single edited file. Auto-fixes
formatting silently in the happy path. When a fix was applied OR a tool
reported an error, prints a loud, multi-line warning so the change is
visible in the chat transcript — the previous "always quiet" behaviour
hid real issues (see PR #338 post-mortem).

Always exits 0 — formatting auto-fixes never block Claude. The Stop hook
runs check-only versions for hard failures (architecture, mypy).
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _digest(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return ""


def main() -> int:
    file_path = os.environ.get("CLAUDE_TOOL_INPUT_FILE_PATH", "").strip()
    if not file_path:
        return 0

    path = Path(file_path)
    if not path.exists() or path.suffix != ".py":
        return 0

    try:
        rel = path.relative_to(REPO_ROOT)
    except ValueError:
        rel = path

    before = _digest(path)
    changed_by: list[str] = []
    errors: list[tuple[str, str]] = []

    for cmd in (
        ["black", "--quiet", str(path)],
        ["isort", "--quiet", str(path)],
        ["ruff", "check", "--fix", "--quiet", str(path)],
    ):
        result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
        after = _digest(path)
        if after != before:
            changed_by.append(cmd[0])
            before = after
        # ruff exits 1 when it applies fixes (not an error); anything > 1 is a problem
        if result.returncode > 1:
            msg = (result.stderr.strip() or result.stdout.strip())[:300]
            errors.append((cmd[0], msg))

    if changed_by or errors:
        print(
            "\n━━━ post-edit auto-fix ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            file=sys.stderr,
        )
        print(f"  file: {rel}", file=sys.stderr)
        if changed_by:
            print(
                f"  ⚠ AUTO-FIXED by: {', '.join(changed_by)} — review the diff "
                "before committing.",
                file=sys.stderr,
            )
        for tool, msg in errors:
            print(f"  ✗ {tool}: {msg}", file=sys.stderr)
        print(
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n",
            file=sys.stderr,
        )

    return 0  # formatting auto-fixes never block


if __name__ == "__main__":
    sys.exit(main())
