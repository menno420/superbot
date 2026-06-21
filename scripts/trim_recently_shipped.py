#!/usr/bin/env python3.10
"""Recently-shipped trim actuator — move overflow bullets to the archive, fix the floor pointer.

Every Q-0107 reconciliation pass ends with the same mechanical, drift-prone chore: the
``current-state.md`` § Recently shipped list is soft-ratcheted at 20 (``check_docs.py``), so
after adding the band's new entries the pass must **trim the oldest bullets into
``current-state-archive.md``** and **hand-update the "Older merges (#X … #535)" floor pointer**.
Doing it by hand means counting bullets, picking the oldest N, cutting them from one file,
pasting into another, and re-deriving a prose pointer — the pointer being the fragile part,
because the ledger's grouped band bullets are **non-monotonic** (a band like ``#1101 · #1121``
carries a recent PR even though its base number is old), so the floor can silently misstate the
boundary. ``check_current_state_ledger.py`` catches a *missing* PR; nothing catches a *wrong
floor pointer* — it is prose.

This is the **actuator** complement to that **detector**: given the two files, it
1. counts the live Recently-shipped bullets; if over ``--budget`` (default 20), moves the
   **oldest (bottom) N** bullets *verbatim* from ``current-state.md`` into the archive's
   ``## Recently shipped — archived`` section (prepended — they are newest in the archive now);
2. recomputes the **"Older merges (#HIGH … #LOW)"** floor pointer from the **actual** PR-number
   span of the archive's **bullet headers** after the move, so the pointer can't drift from
   reality (BUG-0020: it reads only each bullet's leading ``#A · #B …`` cluster, never a stray
   ``#N`` in prose);
3. runs **idempotently** and prints a unified-diff dry-run first (``--check``), so a pass previews
   the move before committing it (``--apply``).

It **never deletes** a bullet — only moves — and the pass still runs
``check_current_state_ledger.py --strict`` afterward as the real guard.

Reliability (Q-0105): **unverified — added 2026-06-20.** The non-monotonic grouped band bullets
are the known hazard; review the ``--check`` diff every time before ``--apply``. If it mishandles
a band even once, **delete it** and keep trimming by hand — it is a convenience actuator, not
load-bearing. Default action is the dry-run; ``--apply`` is the only mutating mode.

Usage:
    python3.10 scripts/trim_recently_shipped.py            # dry-run diff (default)
    python3.10 scripts/trim_recently_shipped.py --apply    # write the trim
    python3.10 scripts/trim_recently_shipped.py --budget 25
"""

from __future__ import annotations

import argparse
import difflib
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CURRENT_STATE = REPO_ROOT / "docs" / "current-state.md"
ARCHIVE = REPO_ROOT / "docs" / "current-state-archive.md"

DEFAULT_BUDGET = 20  # mirrors check_docs.py `_RECENTLY_SHIPPED_BUDGET`

_LIVE_HEADER = "## Recently shipped"
_ARCHIVE_HEADER = "## Recently shipped — archived"
_FLOOR_PREFIX = "- **Older merges"

# A bullet that records merged PR(s): "- **#1156 · #1158 …". The floor pointer
# ("- **Older merges …") is deliberately excluded by the more specific check below.
_PR_BULLET_RE = re.compile(r"^- \*\*#")
# The "(#HIGH … #LOW)" span inside the floor pointer line (ellipsis char or "...").
_FLOOR_SPAN_RE = re.compile(r"\(#\d+\s*(?:…|\.\.\.)\s*#\d+\)")
# Any PR reference / range, to derive the true archive span.
_REF_RE = re.compile(r"#(\d+)")
_RANGE_RE = re.compile(r"#(\d+)\s*[–-]\s*#?(\d+)")


def _section_bounds(lines: list[str], header_prefix: str) -> tuple[int, int]:
    """``(header_index, end_index)`` for the first ``## <header_prefix>`` section.

    ``end_index`` is the line index of the next top-level ``## `` header (exclusive), or
    ``len(lines)``. Raises ``ValueError`` if the header is absent.
    """
    hdr = next(
        (i for i, ln in enumerate(lines) if ln.startswith(header_prefix)),
        None,
    )
    if hdr is None:
        raise ValueError(f"header not found: {header_prefix!r}")
    end = next(
        (i for i in range(hdr + 1, len(lines)) if lines[i].startswith("## ")),
        len(lines),
    )
    return hdr, end


def _bullet_blocks(lines: list[str], start: int, end: int) -> list[tuple[int, int]]:
    """``(block_start, block_stop)`` for each top-level ``- `` bullet in ``lines[start:end]``.

    A block runs from its ``- `` line up to the next ``- `` line (continuation lines are
    indented, so they fall inside the block). Trailing non-bullet lines after the last bullet
    (a ``>`` trailer, blanks) are left out of every block.
    """
    starts = [i for i in range(start, end) if lines[i].startswith("- ")]
    blocks: list[tuple[int, int]] = []
    for idx, s in enumerate(starts):
        stop = starts[idx + 1] if idx + 1 < len(starts) else end
        blocks.append((s, stop))
    return blocks


def _pr_numbers(text: str) -> set[int]:
    """Every PR number in ``text``, expanding ``#A–#B`` ranges (guarded against huge spans)."""
    nums: set[int] = set()
    for lo, hi in _RANGE_RE.findall(text):
        a, b = int(lo), int(hi)
        if a <= b and b - a < 100:
            nums.update(range(a, b + 1))
    nums.update(int(n) for n in _REF_RE.findall(text))
    return nums


def live_entry_count(cs_text: str) -> int:
    """Number of merged-PR bullets in § Recently shipped (excludes the floor pointer)."""
    lines = cs_text.splitlines()
    hdr, end = _section_bounds(lines, _LIVE_HEADER)
    return sum(
        1
        for s, _ in _bullet_blocks(lines, hdr + 1, end)
        if _PR_BULLET_RE.match(lines[s])
    )


def _archive_span_numbers(archive_text: str) -> set[int]:
    """PR numbers from archived **bullet headers only** — never free-floating ``#N`` in prose.

    The floor pointer ``(#HIGH … #LOW)`` must reflect the highest/lowest archived *PR bullet*,
    not a stray reference elsewhere in the archive prose (BUG-0020): the original recompute
    scanned the whole archive and so picked up a ``band-#1170`` parenthetical note and ``#1``
    rank notation, writing a wrong span.

    For each bullet header line (``- **#…``) we read only its **leading PR-reference cluster**
    — the ``#A · #B …`` run before the first ``" ("`` (the date/context paren) or ``"**"`` (the
    bold close). A grouped non-monotonic band bullet (``#690 · #721``) still contributes its
    newest member; a ``#1`` rank token or a ``band-#1170`` note in prose does not.
    """
    nums: set[int] = set()
    for ln in archive_text.splitlines():
        if not _PR_BULLET_RE.match(ln):
            continue
        cluster = ln[len("- **") :]  # strip the bullet prefix; now starts at "#…"
        cut = len(cluster)
        for marker in (" (", "**"):
            idx = cluster.find(marker)
            if idx != -1:
                cut = min(cut, idx)
        nums.update(_pr_numbers(cluster[:cut]))
    return nums


def _rewrite_floor(lines: list[str], archive_text: str) -> None:
    """Rewrite the floor pointer's ``(#HIGH … #LOW)`` from the archive's true PR span (in place)."""
    nums = _archive_span_numbers(archive_text)
    if not nums:
        return
    span = f"(#{max(nums)} … #{min(nums)})"
    for i, ln in enumerate(lines):
        if ln.startswith(_FLOOR_PREFIX):
            lines[i] = _FLOOR_SPAN_RE.sub(span, ln, count=1)
            return


def trim(
    cs_text: str,
    archive_text: str,
    budget: int = DEFAULT_BUDGET,
) -> tuple[str, str, list[str]]:
    """Return ``(new_current_state, new_archive, moved_descriptions)``.

    Moves the oldest ``count - budget`` merged-PR bullets (those just above the floor pointer)
    out of § Recently shipped and into the archive's ``## Recently shipped — archived`` section,
    then recomputes the floor pointer's span. A no-op (inputs returned unchanged, empty move
    list) when at/under budget. Never deletes a bullet.
    """
    cs_lines = cs_text.splitlines()
    hdr, end = _section_bounds(cs_lines, _LIVE_HEADER)
    blocks = _bullet_blocks(cs_lines, hdr + 1, end)
    pr_blocks = [(s, e) for s, e in blocks if _PR_BULLET_RE.match(cs_lines[s])]

    overflow = len(pr_blocks) - budget
    if overflow <= 0:
        return cs_text, archive_text, []

    # The oldest N are the bottom N pr-blocks (the list is newest-first in the file).
    moving = pr_blocks[-overflow:]
    move_lo = moving[0][0]
    move_hi = moving[-1][1]
    moved_lines = cs_lines[move_lo:move_hi]
    moved_descriptions = [cs_lines[s].lstrip("- ").strip() for s, _ in moving]

    new_cs_lines = cs_lines[:move_lo] + cs_lines[move_hi:]

    # Insert the moved block into the archive right after its header (+ a following blank line),
    # preserving the moved bullets' order (newest-first), since they are newer than all existing
    # archived entries.
    arch_lines = archive_text.splitlines()
    a_hdr, _ = _section_bounds(arch_lines, _ARCHIVE_HEADER)
    insert_at = a_hdr + 1
    while insert_at < len(arch_lines) and arch_lines[insert_at].strip() == "":
        insert_at += 1
    new_arch_lines = arch_lines[:insert_at] + moved_lines + arch_lines[insert_at:]

    # Recompute the live floor pointer from the *new* archive span.
    new_archive_text = "\n".join(new_arch_lines) + (
        "\n" if archive_text.endswith("\n") else ""
    )
    _rewrite_floor(new_cs_lines, new_archive_text)
    new_cs_text = "\n".join(new_cs_lines) + ("\n" if cs_text.endswith("\n") else "")

    return new_cs_text, new_archive_text, moved_descriptions


def _diff(old: str, new: str, path: str) -> str:
    return "".join(
        difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
        ),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write the trim (default is a dry-run diff)",
    )
    parser.add_argument(
        "--budget",
        type=int,
        default=DEFAULT_BUDGET,
        help=f"keep this many live bullets (default {DEFAULT_BUDGET})",
    )
    args = parser.parse_args(argv)

    cs_text = CURRENT_STATE.read_text(encoding="utf-8")
    archive_text = ARCHIVE.read_text(encoding="utf-8")

    count = live_entry_count(cs_text)
    new_cs, new_archive, moved = trim(cs_text, archive_text, args.budget)

    if not moved:
        print(
            f"trim_recently_shipped: {count} live bullet(s) ≤ budget {args.budget} — "
            "nothing to trim ✓",
        )
        return 0

    print(
        f"trim_recently_shipped: {count} live bullet(s) > budget {args.budget} — "
        f"moving the oldest {len(moved)} to the archive:",
    )
    for desc in moved:
        print(f"  → {desc[:90]}")

    if not args.apply:
        print("\n--- dry-run diff (re-run with --apply to write) ---\n")
        print(_diff(cs_text, new_cs, "docs/current-state.md"))
        print(_diff(archive_text, new_archive, "docs/current-state-archive.md"))
        print(
            "Review the moved bullets above (the grouped band bullets are non-monotonic — "
            "Q-0105 hazard), then re-run with --apply. Run "
            "check_current_state_ledger.py --strict afterward.",
        )
        return 0

    CURRENT_STATE.write_text(new_cs, encoding="utf-8")
    ARCHIVE.write_text(new_archive, encoding="utf-8")
    print(
        f"\n✓ applied — moved {len(moved)} bullet(s) to the archive and recomputed the floor "
        "pointer. Now run: python3.10 scripts/check_current_state_ledger.py --strict",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
