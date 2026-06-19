#!/usr/bin/env python3.10
"""Bug-book root-fix backlog guard — surface entries that are symptom-fixed but still owe a root fix.

The bug book (``docs/health/bug-book.md``) follows the CLAUDE.md "bugs first,
durably" rule: root cause over symptom-patch. But a dispatch run under time
pressure can land an *immediate* fix (regenerate the artifact, patch the symptom)
and defer the durable root fix to "the owner / a later session" — and that deferral
then sits un-promoted with no signal that work is still owed. BUG-0018 was exactly
this: logged ``FIXED (immediate) / root-fix RECOMMENDED`` and left, until a later
run noticed it by hand. This guard turns that latent backlog into an explicit list
the next empty-fire dispatch run can pick up (the same role ``check_plan_backlog``
plays for thin plans).

What it flags (the "looks done but isn't fully" class — matched on the header's
**status label** (the segment after the last em-dash) + the entry's ``- **Status:**``
line, never the title or body prose, so a title containing "partially"/"root" or a
"recommendation" mention in a paragraph can't false-positive):

* ``PARTIALLY FIXED``                — a fix landed for some sub-cases, others open.
* ``root-fix RECOMMENDED`` / ``RECOMMENDED`` — symptom fixed, durable fix deferred.
* ``FIXED (immediate)`` without ``(root)`` — an explicitly-interim fix.

What it does NOT flag: ``FIXED`` / ``FIXED (root)`` (terminal) and ``OPEN``
(an honestly-labelled active bug, already visible as such — not the deferred-root trap).

Advisory by default (exit 0); ``--strict`` makes a non-empty backlog exit 1 (e.g. for
a cadence/close-out gate). Pure stdlib, like ``check_reconciliation_due.py``.

Reliability (Q-0105, added 2026-06-19): **unverified** — confirm its output against the
bug book a few times across sessions before trusting it. If it misfires (a status phrasing
it can't classify, a false positive) over multiple sessions, **delete it**; it is a
convenience backlog nudge, not load-bearing.

Usage:
    python3.10 scripts/check_bug_book_rootfix_backlog.py            # advisory (exit 0)
    python3.10 scripts/check_bug_book_rootfix_backlog.py --strict   # exit 1 if backlog non-empty
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BUG_BOOK = REPO_ROOT / "docs" / "health" / "bug-book.md"

# A bug entry opens at a "## BUG-NNNN — <title ...>" header (em-dash separated).
_ENTRY_HEADER_RE = re.compile(r"^##\s+(BUG-\d+)\b(.*)$")
# The per-entry status line: "- **Status:** <text>".
_STATUS_LINE_RE = re.compile(r"^\s*-\s*\*\*Status:\*\*\s*(.*)$")


@dataclass(frozen=True)
class RootFixOwed:
    """One bug-book entry that is symptom-fixed but still owes a durable root fix."""

    bug_id: str
    reason: str  # which signal matched (partial / recommended / immediate-only)
    status_text: str  # the header status label + status line, for the report


def _header_status_label(header_tail: str) -> str:
    """The status label from a ``## BUG-NNNN — <title> — <STATUS>`` header.

    Returns the segment after the **last** em-dash — i.e. the status label, never the
    title. Scoping to this (rather than the whole header tail) keeps a *title* that
    merely contains words like "partially" or "root" from being misread as a status
    (the false-positive class flagged in #1144 review). An entry that carries no header
    status segment (status only on the ``- **Status:**`` line) yields its last segment,
    which is harmless: the precise phrase/paren matching below won't fire on prose.
    """
    parts = header_tail.split("—")
    return parts[-1].strip() if len(parts) > 1 else ""


def _classify(status_text: str) -> str | None:
    """Return the backlog reason for a status string, or None if it owes no root fix.

    Matches **precise phrases / parenthesized markers**, not loose substrings, and
    classifies the terminal ``FIXED (root)`` label first (#1144 / #1146 review hardening):

    * the terminal ``FIXED (root)`` *label* short-circuits — a closed-at-root entry whose
      text still *mentions* a recommendation can't re-flag. Keyed on the full ``FIXED (root)``
      phrase, **not** any ``(root)`` occurrence, so prose like "add (root) after the durable
      fix" in a *still-deferred* status doesn't wrongly clear it (the bug-book contract is that
      a deferred entry *lacks* the terminal label);
    * ``PARTIALLY FIXED`` (the status phrase, not any "partially …") → partial;
    * ``RECOMMENDED`` (the deferred-root word; "recommendation" does not match) → deferred;
    * ``(immediate)`` (the parenthesized label, not bare "immediate") → an explicitly-interim
      fix. The terminal ``FIXED (root)`` short-circuit above already excludes a since-rooted
      entry, so "root cause deferred" prose no longer suppresses a genuine immediate-only one.
    """
    upper = status_text.upper()
    if "FIXED (ROOT)" in upper:
        return None
    if "PARTIALLY FIXED" in upper:
        return "partially fixed — open sub-cases remain"
    if "RECOMMENDED" in upper:
        return "root-fix RECOMMENDED but not done"
    if "(IMMEDIATE)" in upper:
        return "FIXED (immediate) only — no root fix"
    return None


def find_rootfix_backlog(text: str) -> list[RootFixOwed]:
    """Parse the bug book and return entries that owe a durable root fix."""
    backlog: list[RootFixOwed] = []
    lines = text.splitlines()
    i = 0
    n = len(lines)
    while i < n:
        header = _ENTRY_HEADER_RE.match(lines[i])
        if not header:
            i += 1
            continue
        bug_id = header.group(1)
        # The status signal lives in the header's status label + the Status: line —
        # never the free-text title (which would cause false positives).
        status_text = _header_status_label(header.group(2))
        j = i + 1
        while j < n and not lines[j].startswith("## "):
            status_match = _STATUS_LINE_RE.match(lines[j])
            if status_match:
                status_text += " " + status_match.group(1)
            j += 1
        reason = _classify(status_text)
        if reason is not None:
            backlog.append(
                RootFixOwed(
                    bug_id=bug_id,
                    reason=reason,
                    status_text=status_text.strip(),
                ),
            )
        i = j
    return backlog


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 if the root-fix backlog is non-empty (default: advisory, exit 0)",
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=BUG_BOOK,
        help="path to the bug book (default: docs/health/bug-book.md)",
    )
    args = parser.parse_args(argv)

    if not args.path.exists():
        print(f"check_bug_book_rootfix_backlog: {args.path} not found", file=sys.stderr)
        return 0  # advisory tool: a missing file is not a failure

    backlog = find_rootfix_backlog(args.path.read_text(encoding="utf-8"))
    if not backlog:
        print("check_bug_book_rootfix_backlog: OK ✓ (no deferred root fixes owed)")
        return 0

    print(
        f"check_bug_book_rootfix_backlog: {len(backlog)} entr{'y' if len(backlog) == 1 else 'ies'} owe a root fix",
    )
    for item in backlog:
        print(f"  • {item.bug_id} — {item.reason}")
    print(
        "\nThese are symptom-fixed but still owe a durable root fix — a standing "
        "dispatch backlog an empty-fire run can pick up (CLAUDE.md 'bugs first, durably').",
    )
    return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
