#!/usr/bin/env python3.10
"""Session-slug uniqueness guard — fail when a PR reuses an existing `.sessions/` slug.

[session-close-gate] Invoked from ``/session-close`` Step 4 (``check_session_close_gate.py``
enforces that this stays wired in).

Provenance / reliability header (per CLAUDE.md Q-0105 adopt-with-kill-switch):
- Why: this closes the *residual* harm BUG-0027 (PR #1523/#1524) left behind. That bug had two
  stacked faults: (1) a slug collision (a new dispatch run reused an existing ``.sessions/`` slug)
  caused ``git add`` to record the born-red card as a **modification**, not an addition, so the
  merge-gate's added-only scan failed open and a partial PR auto-merged; and (2) the collision
  **silently clobbered** the prior session's complete log in ``main``. #1524 fixed fault (1) at the
  root (the gate now scans added-OR-modified cards). Fault (2) — the silent clobber — still happens
  *before* the gate ever engages: by the time CI runs, the prior log has already been overwritten in
  the working tree and committed. The only way to stop the clobber is to catch the collision **at
  author time**, which is what this checker does: a session card path that already exists in
  ``origin/main`` is a reused slug → rename it to a unique slug *before* it overwrites the old log.
- The fix is the previous dispatch run's own Q-0089 idea (#1524 session log): a guard that fails when
  a PR's new ``.sessions/`` card path already exists in ``origin/main``. "Enforce, don't exhort"
  (Q-0132 / the Q-0194 friction→guard rule): the recurring-task slug-collision class is structural
  (date+topic slugs for a task type that fires repeatedly), so a checker beats a journal note.
- Distinguishing a collision from a *legitimate* re-badge: a normal session card never exists in
  ``main`` when the session opens it, so across ``origin/main...HEAD`` it is an **addition**, never a
  modification — it can't trip this guard. The one legitimate reason to *modify* an existing
  ``.sessions/`` card is a reconciliation pass re-badging an **old** log to a terminal status
  (``historical``/``archived``/…); those are carved out via ``check_session_gate._TERMINAL_OK_STATUSES``
  (the single source of truth for session-card status semantics, imported here so the two guards can
  never disagree). So: a card that exists in ``main`` AND is touched by this PR AND is **not** a
  terminal re-badge == a reused active-session slug == a collision.
- Added: 2026-06-29 (autonomous dispatch run, S3/S4 mechanism — the previous run's Q-0089 idea).
  **Unverified** — confirm its output against ground truth over a few sessions before trusting it.
  **Delete this script if it proves noisy/unreliable over multiple sessions**; it is a disposable
  convenience guard, not load-bearing. Run from ``/session-close`` Step 4 (author time), not CI —
  the whole point is to catch the collision *before* the clobber commit, which CI is too late for.

What it checks (read-only; exits 1 on a collision, 0 when clean):
- Find the ``.sessions/*.md`` cards this PR touches (added or modified vs ``origin/main``, plus
  not-yet-committed staged/untracked cards so a pre-push run reflects what the PR will contain).
- For each, ask git whether that exact path **already exists in ``origin/main``** (``git cat-file -e``).
- A card that exists in ``main`` is a reused slug. If its (HEAD) status is a terminal re-badge token
  it is an allowed reconciliation modification; otherwise it is a collision → FAIL with a rename hint.

Usage::

    python3.10 scripts/check_session_slug_unique.py            # auto (vs origin/main)
    python3.10 scripts/check_session_slug_unique.py --base SHA --head SHA   # explicit range
    python3.10 scripts/check_session_slug_unique.py --quiet     # exit code only
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# One source of truth for session-card status parsing + the terminal re-badge carve-out:
# import them from the merge-gate so the two guards can never drift apart.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_session_gate import (  # noqa: E402
    _TERMINAL_OK_STATUSES,
    REPO_ROOT,
    gate_session_cards,
    parse_status,
)

# A session-card slug that is the *base* against which a collision is measured: a card already in
# ``main``. The single legitimate modify-an-existing-card case is a reconciliation re-badge to a
# terminal status — every other touch of an in-main card is a reused slug. Re-exported for tests.
_REBADGE_OK_STATUSES = _TERMINAL_OK_STATUSES


def _exists_in_main(rel_path: str) -> bool:
    """True if ``rel_path`` already exists in ``origin/main`` (a reused slug).

    Uses ``git cat-file -e origin/main:<path>`` — the cheap object-existence probe the original
    Q-0089 idea named. Returns ``False`` on any git failure (no ref, detached env): a guard that
    cannot read git must not block (the merge-gate + the rule are the backstop).
    """
    try:
        result = subprocess.run(
            ["git", "cat-file", "-e", f"origin/main:{rel_path}"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
    except OSError:
        return False
    return result.returncode == 0


def collisions(base: str | None, head: str | None) -> list[tuple[Path, str]]:
    """Return (card, status) for each touched session card that reuses an in-``main`` slug.

    A card collides when its path already exists in ``origin/main`` AND its current status is not a
    terminal re-badge token (those are legitimate reconciliation modifications, carved out). The
    candidate set is the merge-gate's added-OR-modified card list, so this and the gate agree on
    *which* cards a PR touches.
    """
    found: list[tuple[Path, str]] = []
    for card in gate_session_cards(base, head):
        try:
            rel = card.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = card.as_posix()
        if not _exists_in_main(rel):
            continue  # net-new slug — the normal case, never a collision.
        try:
            status = (
                parse_status(card.read_text(encoding="utf-8")) or "(no Status badge)"
            )
        except OSError:
            status = "(unreadable)"
        if status in _REBADGE_OK_STATUSES:
            continue  # a reconciliation re-badge of an old log — allowed.
        found.append((card, status))
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="SuperBot session-slug uniqueness guard.",
    )
    parser.add_argument("--base", help="base commit SHA (explicit range)")
    parser.add_argument("--head", help="head commit SHA (explicit range)")
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="suppress output; return exit code only",
    )
    args = parser.parse_args(argv)

    hits = collisions(args.base, args.head)
    if not hits:
        if not args.quiet:
            print(
                "check_session_slug_unique: OK — no session card reuses an existing "
                "origin/main slug ✓",
            )
        return 0

    if not args.quiet:
        print(
            "check_session_slug_unique: COLLISION — a session card path already exists in "
            "origin/main:",
        )
        for card, status in hits:
            rel = (
                card.relative_to(REPO_ROOT) if card.is_relative_to(REPO_ROOT) else card
            )
            print(f"  - {rel}: Status `{status}` — this slug is already taken in main.")
        ok = ", ".join(sorted(_REBADGE_OK_STATUSES))
        print(
            "\nReusing an existing .sessions/ slug for a new session SILENTLY CLOBBERS the prior "
            "session's log (BUG-0027 / the #1523 collision). Rename your card to a unique slug "
            "(e.g. add a disambiguating word) before it overwrites the old one.\n"
            f"  (A reconciliation pass re-badging an *old* log to a terminal status — {ok} — is "
            "exempt; that is a legitimate modify-in-place.)",
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
