#!/usr/bin/env python3.10
"""PreToolUse hook: show a file's context map before the agent edits it.

Wired to the ``Edit|Write`` matcher in ``.claude/settings.json``. For the
**first** edit of a ``disbot/*.py`` file in a session, it runs
``scripts/context_map.py`` on that file and injects the result as
``additionalContext`` — so the agent sees the file's importers, blast
radius, CodeGraph-invisible lazy imports, related docs, the recommended
read set, and the post-edit checks *before* touching it. That is the
file-level navigation step the agent would otherwise have to remember to
run by hand (the gap noted in the 2026-06-07 workflow review: the tool
existed and was good, but nothing surfaced it at edit time).

Discipline:

* fires **at most once per file per session** (a temp marker — the
  sandbox container is per-session, so the marker is too);
* only for existing ``disbot/*.py`` files (new-file ``Write`` is skipped —
  there is no context yet);
* **never blocks**: any failure / timeout exits 0 with no output. The map
  is a convenience, not a gate.

Uses the same ``additionalContext`` injection mechanism as
``claude_pr_subscribe_reminder.py``.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
_SEEN_DIR = Path(tempfile.gettempdir()) / "claude_ctxmap_seen"
_CONTEXT_MAP = REPO_ROOT / "scripts" / "context_map.py"


def _target_path() -> Path | None:
    """Resolve the edited file path from the hook env var, then stdin."""
    raw = os.environ.get("CLAUDE_TOOL_INPUT_FILE_PATH", "").strip()
    if not raw:
        # Fallback: parse the hook payload on stdin for tool_input.file_path.
        try:
            payload = json.loads(sys.stdin.read() or "{}")
            raw = ((payload.get("tool_input") or {}).get("file_path") or "").strip()
        except (ValueError, AttributeError, TypeError):
            raw = ""
    return Path(raw) if raw else None


def main() -> int:
    path = _target_path()
    if path is None:
        return 0
    try:
        rel = path.resolve().relative_to(REPO_ROOT)
    except (ValueError, OSError):
        return 0

    # Only existing disbot/*.py files. New-file Writes have no context yet.
    if rel.parts[:1] != ("disbot",) or rel.suffix != ".py" or not path.exists():
        return 0

    # Once per file per session (temp dir is per-session in the sandbox).
    marker = _SEEN_DIR / hashlib.sha256(str(rel).encode()).hexdigest()
    if marker.exists():
        return 0

    try:
        out = subprocess.run(
            [
                "python3.10",
                str(_CONTEXT_MAP),
                str(rel),
                "--max-importers",
                "8",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return 0  # never block on the convenience path

    # Best-effort marker so the map shows once, not on every edit of the file.
    try:
        _SEEN_DIR.mkdir(parents=True, exist_ok=True)
        marker.touch()
    except OSError:
        pass

    body = (out.stdout or "").strip()
    if not body:
        return 0

    message = (
        f"Context map for {rel} — auto-shown once before your first edit (the "
        "file-level navigation step from CLAUDE.md). Skim importers / blast radius "
        "/ related docs / recommended read set before changing it:\n\n" + body
    )
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "additionalContext": message,
                },
            },
        ),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
