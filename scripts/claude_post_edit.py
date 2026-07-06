#!/usr/bin/env python3
"""PostToolUse hook: auto-format Python files; check docs on Markdown edits.

Called by Claude Code after every Edit or Write tool use.
The file path is read from CLAUDE_TOOL_INPUT_FILE_PATH.

For .py files: runs ruff format → ruff check --fix on the single edited file.
Auto-fixes formatting silently in the happy path. When a fix was applied OR
a tool reported an error, prints a loud, multi-line warning so the change is
visible in the chat transcript — the previous "always quiet" behaviour hid
real issues (see PR #338 post-mortem).

For .md files: runs check_docs.py --strict against the whole docs/ tree and
prints a loud warning if any issue is found (missing badge, orphan doc, broken
link). This catches CI failures at edit-time rather than at PR push.

Always exits 0 — auto-fixes and doc warnings never block Claude. The Stop hook
runs check-only versions for hard failures (architecture, mypy).
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# CI runs Python 3.10 — match it so formatter/lint behaviour is identical
# (see CLAUDE.md "Match CI exactly" section and PR #338 post-mortem).
PY = "python3.10" if shutil.which("python3.10") else sys.executable


def _digest(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return ""


def _check_docs(path: Path) -> int:
    """Run check_docs --strict after any .md edit and warn loudly on failure."""
    # Only care about files inside docs/ or the session journal — skip everything else
    try:
        rel = path.relative_to(REPO_ROOT)
    except ValueError:
        return 0
    parts = rel.parts
    if not (
        parts[0] == "docs"
        or str(rel) in (".session-journal.md", "CLAUDE.md")
        or parts[:2] == (".claude",)
    ):
        return 0

    check_script = REPO_ROOT / "scripts" / "check_docs.py"
    if not check_script.exists():
        return 0

    result = subprocess.run(
        [PY, str(check_script), "--strict"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        output = (result.stdout + result.stderr).strip()
        print(
            "\n━━━ check_docs warning ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            file=sys.stderr,
        )
        print(f"  triggered by edit to: {rel}", file=sys.stderr)
        print(
            "  ⚠ DOCS ISSUE — fix before pushing (will fail CI):",
            file=sys.stderr,
        )
        for line in output.splitlines():
            print(f"    {line}", file=sys.stderr)
        print(
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n",
            file=sys.stderr,
        )
    return 0  # always non-blocking


def _check_session_log(path: Path) -> int:
    """On a `.sessions/*.md` edit, warn if the log is missing required sections.

    Enforces the Q-0089 (session idea) / Q-0102 (previous-session review) enders at
    write-time — `.sessions/` is not under `docs/`, so `check_docs` never sees it.
    Non-blocking and defensive: any failure here is swallowed so the hook never breaks.
    """
    try:
        rel = path.relative_to(REPO_ROOT)
    except ValueError:
        return 0
    if rel.parts[:1] != (".sessions",) or path.name == "README.md":
        return 0

    checker = REPO_ROOT / "scripts" / "check_session_log.py"
    if not checker.exists():
        return 0
    try:
        result = subprocess.run(
            [PY, str(checker), "--file", str(path)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
    except OSError:
        return 0
    if result.returncode != 0 or "is missing:" in result.stdout:
        print(
            "\n━━━ session-log reminder ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            file=sys.stderr,
        )
        for line in result.stdout.strip().splitlines():
            print(f"  {line}", file=sys.stderr)
        print(
            "  (Q-0089 idea + Q-0102 previous-session review are required enders)",
            file=sys.stderr,
        )
        print(
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n",
            file=sys.stderr,
        )
    return 0  # always non-blocking


def main() -> int:
    file_path = os.environ.get("CLAUDE_TOOL_INPUT_FILE_PATH", "").strip()
    if not file_path:
        return 0

    path = Path(file_path)
    if not path.exists():
        return 0

    if path.suffix == ".md":
        _check_docs(path)
        _check_session_log(path)
        return 0

    if path.suffix != ".py":
        return 0

    try:
        rel = path.relative_to(REPO_ROOT)
    except ValueError:
        rel = path

    before = _digest(path)
    changed_by: list[str] = []
    errors: list[tuple[str, str]] = []

    # ruff replaced black + isort (A3, 2026-07-06): `ruff format` owns formatting,
    # `ruff check --fix` owns import sorting (the `I` rule) + lint autofix.
    for cmd in (
        [PY, "-m", "ruff", "format", "--quiet", str(path)],
        [PY, "-m", "ruff", "check", "--fix", "--quiet", str(path)],
    ):
        tool = f"{cmd[2]} {cmd[3]}"  # "ruff format" / "ruff check"
        try:
            result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
        except FileNotFoundError:
            errors.append((tool, f"{PY} not found — hooks require Python 3.10"))
            continue
        after = _digest(path)
        if after != before:
            changed_by.append(tool)
            before = after
        # ruff exits 1 when it applies fixes (not an error); anything > 1 is a problem
        # ruff exits 1 for "module not found" too (tool not installed in python3.10 env)
        if result.returncode > 1 or (
            result.returncode == 1
            and "No module named" in (result.stderr + result.stdout)
        ):
            msg = (result.stderr.strip() or result.stdout.strip())[:300]
            errors.append((tool, msg))

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
