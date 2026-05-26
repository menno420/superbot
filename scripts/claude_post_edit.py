#!/usr/bin/env python3
"""PostToolUse hook: auto-format the just-edited Python file.

Called by Claude Code after every Edit or Write tool use.
The file path is read from CLAUDE_TOOL_INPUT_FILE_PATH.

Runs black → isort → ruff --fix in sequence.
Always exits 0 — formatting failures are logged but never block
Claude from continuing. Architecture violations are intentionally
NOT fixed here; those require human judgment.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


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

    print(f"[post-edit] {rel}")

    for cmd in (
        ["black", "--quiet", str(path)],
        ["isort", "--quiet", str(path)],
        ["ruff", "check", "--fix", "--quiet", str(path)],
    ):
        result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
        # ruff exits 1 when it applies fixes (not an error); anything else is a problem
        if result.returncode > 1:
            msg = result.stderr.strip() or result.stdout.strip()
            print(f"[post-edit] {cmd[0]} warning: {msg}", file=sys.stderr)

    return 0  # never block Claude


if __name__ == "__main__":
    sys.exit(main())
