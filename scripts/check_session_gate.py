#!/usr/bin/env python3.10
"""Session merge-gate — hold a PR red until its session card says it's done.

The merge race this closes (owner directive Q-0133, 2026-06-14)
--------------------------------------------------------------
Native auto-merge (Q-0123) merges a `claude/*` PR the instant the required
`Code Quality` check goes green. A session that pushes its code first and its
session-close docs (the ledger entry, the `.sessions/` log) second can therefore
merge **before** those docs are pushed — the #843 case: the PR merged without its
ledger entry, leaving a stranded follow-up.

The fix is the owner's: every session declares itself up-front in a single
per-session file that is *both* the start-declaration ("what is about to happen",
visible to parallel/next sessions on the open PR) **and** the end-record ("what
has happened"). That file is the existing `.sessions/<date>-<slug>.md` log, and
its `> **Status:**` badge gates the merge:

* Created in the **first** commit with a HOLD status (`in-progress`) → the PR is
  **born red**, so auto-merge arms but cannot fire (no race window — the gate is
  red from commit 1, not added later).
* Flipped to a READY status (`complete`) as the deliberate **final** step →
  `Code Quality` goes green → auto-merge fires.

Engage-when-present (the safe default Q-0133 chose over airtight): the gate fails
**only** when the PR *adds* a session card whose status is a hold/unknown token. A
PR that adds **no** new session card behaves exactly as before (merges on green),
so workflow-authored PRs (btd6-data-refresh) and any routine that hasn't created a
card are never deadlocked. Creating the card is mandatory **by CLAUDE.md rule** +
the Stop-hook / `/session-close` reminder, not by hard CI enforcement.

Only **newly-added** cards (`git diff --diff-filter=A`) are inspected — a
reconciliation PR that re-badges an *old* log to `historical` is never held.

Pure stdlib (runs in CI's `code-quality` job before any setup) and unit-tested.

Usage:
    python3.10 scripts/check_session_gate.py                 # auto (vs origin/main)
    python3.10 scripts/check_session_gate.py --base SHA --head SHA   # CI
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# READY = the PR may merge. Anything else on a newly-added card holds it red, so a
# typo'd or still-in-progress status fails safe (held) rather than merging early.
_READY_STATUSES = {"complete", "done", "ready", "final", "merged", "shipped"}

# Terminator is an em/en-dash or pipe or end-of-line — NOT a plain hyphen, which is
# part of word-tokens like `in-progress`.
_STATUS_RE = re.compile(r"\*\*Status:\*\*\s*`?\s*([A-Za-z0-9 _-]+?)\s*`?\s*(?:[—–|]|$)")


def parse_status(text: str) -> str | None:
    """Return the lowercased `> **Status:** `<token>`` badge token, or None."""
    for line in text.splitlines():
        if "**Status:**" in line:
            m = _STATUS_RE.search(line)
            if m:
                return m.group(1).strip().lower()
    return None


def added_session_cards(base: str | None, head: str | None) -> list[Path]:
    """`.sessions/*.md` files ADDED between base and head (README excluded).

    CI passes the PR base/head SHAs; locally we diff against ``origin/main`` (the
    merge base of this branch). Returns [] on any git failure — a gate that cannot
    read git must not block (fail-open here; the rule + reminder are the backstop).
    """
    if base and head:
        # CI: the card is committed in the PR — the committed diff is authoritative.
        cmds = [
            [
                "git",
                "diff",
                "--name-only",
                "--diff-filter=A",
                base,
                head,
                "--",
                ".sessions/",
            ],
        ]
    else:
        # Local: include not-yet-committed cards (staged or untracked) so a pre-push
        # run reflects what the PR will contain.
        cmds = [
            [
                "git",
                "diff",
                "--name-only",
                "--diff-filter=A",
                "origin/main...HEAD",
                "--",
                ".sessions/",
            ],
            ["git", "ls-files", "--others", "--exclude-standard", "--", ".sessions/"],
        ]
    found: set[str] = set()
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
    return [REPO_ROOT / p for p in sorted(found)]


def held_cards(cards: list[Path]) -> list[tuple[Path, str]]:
    """Return (card, status) for each card NOT in a READY status."""
    held: list[tuple[Path, str]] = []
    for card in cards:
        try:
            text = card.read_text(encoding="utf-8")
        except OSError:
            continue
        status = parse_status(text) or "(no Status badge)"
        if status not in _READY_STATUSES:
            held.append((card, status))
    return held


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SuperBot session merge-gate.")
    parser.add_argument("--base", help="base commit SHA (CI: PR base)")
    parser.add_argument("--head", help="head commit SHA (CI: PR head)")
    args = parser.parse_args(argv)

    cards = added_session_cards(args.base, args.head)
    if not cards:
        print("check_session_gate: no new session card in this PR — not gated. ✓")
        return 0

    held = held_cards(cards)
    if not held:
        names = ", ".join(c.name for c in cards)
        print(
            f"check_session_gate: session card(s) ready — merge unblocked ✓ ({names})",
        )
        return 0

    print("check_session_gate: MERGE HELD — session card not marked ready.")
    for card, status in held:
        rel = card.relative_to(REPO_ROOT) if card.is_relative_to(REPO_ROOT) else card
        print(f"  - {rel}: Status `{status}` (held)")
    ready = ", ".join(sorted(_READY_STATUSES))
    print(
        "\nThis is the born-red session gate (Q-0133): flip the card's "
        "`> **Status:**` badge to a ready token to merge.\n"
        f"  Ready tokens: {ready}\n"
        "  (Do this as the deliberate final step, after the session-close docs "
        "are written — so auto-merge fires on a complete PR, not a partial one.)",
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
