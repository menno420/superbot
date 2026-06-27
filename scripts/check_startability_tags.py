#!/usr/bin/env python3.10
"""Assert every per-sector live-state file tags its ▶ Next startables with an offline-fit tag.

Provenance / reliability header (per CLAUDE.md Q-0105 adopt-with-kill-switch):
- Why: the per-sector live-state files (``docs/current-state/S*.md``) list each sector's
  ``▶ Next startable`` items. **S2** annotated those items with an offline-fit phrase
  ("(offline, self-mergeable)") and two consecutive dispatch runs' Q-0102 reviews (the
  2026-06-25 and 2026-06-26 session logs) found that tag worked as a fast dispatch signal —
  while S1/S3/S5 lacked it, so each empty-fire run burned orient-time rediscovering which
  startables are offline-verifiable vs. needs-live-bot vs. owner-gated. This checker makes the
  now-standardized per-item offline-fit tag (``[offline]`` / ``[needs-live-bot]`` / ``[owner]``)
  a machine-checked convention so it can't silently drift back out.
- Added: 2026-06-27 (dispatch run, self-initiated per Q-0172). **Unverified** — confirm its
  output against the sector files over a few sessions before trusting it. **Delete this script
  if it proves noisy/unreliable over multiple sessions**; it is a disposable convenience guard,
  read-only, not load-bearing. It is intentionally **NOT wired into CI** (that is ask-first per
  the autonomy boundary) — run it by hand or from the docs-reconciliation routine.

The check (read-only; exits 1 on any violation, 0 when clean): each non-exempt
``docs/current-state/S<n>.md`` file's ``▶ Next`` startable bullet block contains at least one
recognized offline-fit tag. It is deliberately a **presence** check, not a rigid per-bullet
parse — the sector files are rich prose and a per-bullet parser would be brittle; presence
catches the real failure (a sector file that gives a dispatch run no offline-fit guidance at all).

Usage::

    python3.10 scripts/check_startability_tags.py            # report + exit code
    python3.10 scripts/check_startability_tags.py --quiet     # exit code only
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = REPO_ROOT / "docs" / "current-state"

# The per-item offline-fit tag vocabulary (documented in repo-sector-map.md §
# "the offline-fit startability tag"). Orthogonal to the ▶/⛔/👤 startability glyph
# (may-begin) and to dispatch_menu's sector-level unattended-fit (can-finish-and-merge);
# this one answers, per ▶ item, "what does verifying it require?".
RECOGNIZED_TAGS = ("[offline]", "[needs-live-bot]", "[owner]")

# S4 is the documentation/reconciliation sector: its ▶ Next is a cadence-gated docs pass
# (auto-triggered by the reconciliation routine), not a menu of buildable startables, so it
# carries no per-item offline-fit tag by design.
EXEMPT_SECTORS = {"S4"}

_SECTOR_FILE = re.compile(r"^S(\d)\b")
_NEXT_HEADING = re.compile(r"^\*\*▶ Next\b")
_BOLD_HEADING = re.compile(r"^\*\*[^*].*:\*\*")


def _read(path: Path) -> str:
    """Return the file text, or an empty string if it does not exist."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def sector_files() -> list[Path]:
    """Return the per-sector live-state files (``S<n>.md``), excluding the README."""
    return sorted(
        p for p in STATE_DIR.glob("S*.md") if _SECTOR_FILE.match(p.stem) is not None
    )


def next_block(text: str) -> str | None:
    """Return the ``▶ Next`` startable bullet block, or ``None`` if there is no heading.

    The block runs from the ``**▶ Next…:**`` heading line up to (but not including) the next
    bold section heading line (``**Something:**`` at line start) or end of file. Bullets start
    with ``-`` and the italic legend line starts with ``*(`` — neither terminates the block, so
    only a sibling section heading ends it.
    """
    lines = text.splitlines()
    start = next(
        (i for i, line in enumerate(lines) if _NEXT_HEADING.match(line)),
        None,
    )
    if start is None:
        return None
    out = [lines[start]]
    for line in lines[start + 1 :]:
        if _BOLD_HEADING.match(line):
            break
        out.append(line)
    return "\n".join(out)


def sector_id(path: Path) -> str:
    """Return the ``S<n>`` id from a sector file stem (``S4-docs`` → ``S4``)."""
    m = _SECTOR_FILE.match(path.stem)
    return f"S{m.group(1)}" if m else path.stem


def check_file(path: Path) -> list[str]:
    """Return violation strings for one sector file (empty when clean)."""
    if sector_id(path) in EXEMPT_SECTORS:
        return []
    text = _read(path)
    if not text:
        return [f"{path.name}: unreadable or empty."]
    block = next_block(text)
    if block is None:
        return [
            f"{path.name}: no '**▶ Next…:**' startable heading found "
            f"(every active sector lists its next startables).",
        ]
    if not any(tag in block for tag in RECOGNIZED_TAGS):
        return [
            f"{path.name}: the ▶ Next block carries no offline-fit tag "
            f"(tag each item with one of {', '.join(RECOGNIZED_TAGS)} — see "
            f"repo-sector-map.md § 'the offline-fit startability tag').",
        ]
    return []


def run() -> list[str]:
    """Run the check over every sector file and return combined violation strings."""
    files = sector_files()
    if not files:
        return [f"no S<n>.md files found in {STATE_DIR}"]
    errors: list[str] = []
    for path in files:
        errors += check_file(path)
    return errors


def main() -> int:
    """CLI entry point: print violations and return an exit code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="suppress output; return exit code only",
    )
    args = parser.parse_args()

    errors = run()
    if errors:
        if not args.quiet:
            print("check_startability_tags: FAIL — sector ▶ Next tagging drift:")
            for err in errors:
                print(f"  - {err}")
        return 1
    if not args.quiet:
        checked = [
            sector_id(p) for p in sector_files() if sector_id(p) not in EXEMPT_SECTORS
        ]
        print(
            "check_startability_tags: OK — "
            f"{len(checked)} sectors tagged ({', '.join(checked)}); "
            f"{', '.join(sorted(EXEMPT_SECTORS))} exempt ✓",
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
