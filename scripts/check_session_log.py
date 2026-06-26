#!/usr/bin/env python3.10
"""Session-log completeness checker — the Q-0089 / Q-0102 session-enders, enforced.

[session-close-gate] Invoked from ``/session-close`` Step 4 (``check_session_close_gate.py`` enforces that this stays wired in).

The session workflow requires every session to end with a `.sessions/<date>-<slug>.md`
log that carries:

  1. a Status badge (`> **Status:** `<token>``) — `.sessions/` is *not* under `docs/`,
     so `check_docs.py` does not validate these files; this checker is their gate;
  2. a `💡 Session idea` flag (owner directive Q-0089 — one new idea per session);
  3. a `⟲ Previous-session review` note (owner directive Q-0102 — review the previous
     session + surface one system/workflow improvement).

These are *conventions an agent can silently skip* — the maintainer's stated pain
("not always being properly done"). This script turns them into a checkable signal,
wired non-blocking into the post-edit and Stop hooks and run `--strict` by the
`/session-close` skill.

**Target selection.** The "current session's log" is identified via git — the
`.sessions/*.md` file added or modified versus `origin/main` (or, failing git, the
newest by mtime). Filename date-sort cannot disambiguate same-day logs and would risk
flagging another session's already-merged log.

Pure stdlib so the unit test runs in CI without extra deps (same discipline as
`check_docs.py`).

Reliability (Q-0105, added 2026-06-12): **unverified** — if this nags spuriously or misses
incomplete logs over multiple sessions, **delete it**; it is a convenience guard for the
Q-0089/Q-0102 enders, not load-bearing.

Usage:
    python3.10 scripts/check_session_log.py              # report (exit 0)
    python3.10 scripts/check_session_log.py --strict     # exit 1 if incomplete/missing
    python3.10 scripts/check_session_log.py --file PATH  # check one specific log
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SESSIONS_DIR = REPO_ROOT / ".sessions"

# (key, human label, predicate-substring test). Kept as plain membership tests so the
# convention is obvious and lenient about surrounding wording.
_REQUIRED: list[tuple[str, str, str]] = [
    ("badge", "Status badge (`> **Status:** `<token>``)", "**Status:**"),
    ("idea", "`💡 Session idea` flag (Q-0089)", "💡"),
    ("review", "`⟲ Previous-session review` note (Q-0102)", "previous-session review"),
]


def missing_sections(text: str) -> list[str]:
    """Return human labels for required elements absent from a log's text."""
    lower = text.lower()
    missing: list[str] = []
    for _key, label, needle in _REQUIRED:
        if needle.lower() not in lower:
            missing.append(label)
    return missing


def _git_changed_session_logs() -> list[Path]:
    """`.sessions/*.md` added/modified vs origin/main or in the working tree."""
    found: set[str] = set()
    cmds = (
        ["git", "diff", "--name-only", "origin/main...HEAD"],
        ["git", "diff", "--name-only", "HEAD"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    )
    for cmd in cmds:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
        except OSError:
            continue
        if result.returncode != 0:
            continue
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith(".sessions/") and line.endswith(".md"):
                if Path(line).name != "README.md":
                    found.add(line)
    return [REPO_ROOT / p for p in found if (REPO_ROOT / p).exists()]


def current_session_log() -> Path | None:
    """Best guess at *this* session's log: newest git-touched `.sessions/*.md`.

    Falls back to the newest file by mtime if git reports nothing (e.g. the log was
    written but not yet staged in a detached check).
    """
    candidates = _git_changed_session_logs()
    if not candidates and SESSIONS_DIR.is_dir():
        candidates = [p for p in SESSIONS_DIR.glob("*.md") if p.name != "README.md"]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def check(path: Path) -> list[str]:
    """Return the missing-element labels for one log file."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return [label for _k, label, _n in _REQUIRED]
    return missing_sections(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SuperBot session-log checker.")
    parser.add_argument("--strict", action="store_true", help="exit 1 if incomplete")
    parser.add_argument(
        "--file",
        help="check this specific log instead of auto-detecting",
    )
    args = parser.parse_args(argv)

    if args.file:
        target: Path | None = Path(args.file)
        if not target.is_absolute():
            target = REPO_ROOT / target
    else:
        target = current_session_log()

    if target is None or not target.exists():
        print(
            "check_session_log: no session log found for this session yet — "
            "add `.sessions/<date>-<slug>.md` with a Status badge, a `💡 Session idea` "
            "(Q-0089), and a `⟲ Previous-session review` (Q-0102).",
        )
        return 1 if args.strict else 0

    rel = target.relative_to(REPO_ROOT) if target.is_relative_to(REPO_ROOT) else target
    missing = check(target)
    if not missing:
        print(f"check_session_log: {rel} complete ✓")
        return 0

    print(f"check_session_log: {rel} is missing:")
    for label in missing:
        print(f"  - {label}")
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
