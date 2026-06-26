#!/usr/bin/env python3.10
"""Flag per-sector ``▶ Next`` items that point at already-shipped plans.

Provenance / reliability header (per CLAUDE.md Q-0105 adopt-with-kill-switch):
- Why: ``docs/current-state/S*.md`` are the *freshness* layer — the dispatch routine
  reads a sector's ``▶ Next startable`` to pick the next slice. When a ``▶ Next`` item
  links a plan that has already shipped (its ``Status:`` is ``historical``), the routine
  is steered to rebuild finished work. This is exactly the mis-step the 2026-06-26
  dispatch run nearly made: S3's ▶ Next listed "Consistency-linter AI-nav PR 1" linking
  ``ai-panel-inplace-navigation-plan-2026-06-19.md``, which had been SHIPPED in #1376.
  The reconciliation routine reconciles ``current-state.md`` every 30 PRs, but the
  *per-sector* ▶ Next pointers had no machine guard against this drift class.
- Added: 2026-06-26 (autonomous dispatch run, S3 mechanism). **Unverified** — confirm its
  output against ground truth over a few sessions before trusting it. **Delete this script
  if it proves noisy/unreliable over multiple sessions**; it is a disposable convenience
  guard, not load-bearing. It is intentionally NOT wired into CI (ask-first per the
  autonomy boundary) — run it by hand or from the docs-reconciliation routine.

What it checks (read-only; exits 1 on any finding, 0 when clean):
- For each ``docs/current-state/S*.md`` sector file, isolate the ``▶ Next`` section(s)
  (a bold heading line beginning ``**▶ Next`` up to the next sibling ``**...**`` heading).
- Extract every ``../planning/<file>.md`` link inside that section.
- Read the linked plan's ``Status:`` marker; flag any whose status is ``historical``
  (the convention's "initiative complete / shipped" state) — a ▶ Next must point at
  *buildable* work, never a finished plan.

The scoping to the ▶ Next section is deliberate: a sector's *Recently shipped* list and a
docs sector's pass-record links are legitimately ``historical`` and must not false-positive.

Usage::

    python3.10 scripts/check_sector_next_freshness.py            # report + exit code
    python3.10 scripts/check_sector_next_freshness.py --quiet     # exit code only
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SECTOR_DIR = REPO_ROOT / "docs" / "current-state"
PLANNING_DIR = REPO_ROOT / "docs" / "planning"

# Statuses that mean "this plan is done — do not dispatch against it as new work".
SHIPPED_STATUSES = frozenset({"historical"})

# A bold section heading line (``**Label...**``) — NOT a ``- **bullet:**`` list item,
# which starts with ``- ``. Used to find the ▶ Next section and its end boundary.
_SECTION_HEADING = re.compile(r"^\*\*(.+?)\*\*")
_NEXT_HEADING = re.compile(r"^\*\*▶\s*Next")
# A relative link to a planning doc, from a current-state/ file (``../planning/<file>``).
_PLAN_LINK = re.compile(r"\]\(\.\./planning/([A-Za-z0-9._-]+\.md)")
# The plan's status marker, e.g. ``> **Status:** `historical` — ...``.
_STATUS = re.compile(r"Status:\*\*\s*`([a-z-]+)`")


def _read(path: Path) -> str:
    """Return the file text, or an empty string if it does not exist."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def next_sections(text: str) -> list[str]:
    """Return the text of every ``▶ Next`` section in a sector file.

    A section starts at a line matching ``**▶ Next...**`` and ends at the next
    sibling bold heading (another ``**...**`` line that is not a ``- **`` bullet),
    a ``## `` heading, or end-of-file.
    """
    lines = text.splitlines()
    sections: list[str] = []
    buf: list[str] | None = None
    for line in lines:
        if _NEXT_HEADING.match(line):
            if buf is not None:
                sections.append("\n".join(buf))
            buf = [line]
            continue
        if buf is not None:
            # End the section at the next sibling heading.
            if line.startswith("## ") or (
                _SECTION_HEADING.match(line) and not _NEXT_HEADING.match(line)
            ):
                sections.append("\n".join(buf))
                buf = None
                continue
            buf.append(line)
    if buf is not None:
        sections.append("\n".join(buf))
    return sections


def plan_status(plan_file: str) -> str | None:
    """Return the lowercase status of a planning doc, or ``None`` if unreadable."""
    text = _read(PLANNING_DIR / plan_file)
    if not text:
        return None
    m = _STATUS.search(text)
    return m.group(1) if m else None


def check_sector_file(path: Path) -> list[str]:
    """Return the list of stale-pointer findings for one sector file."""
    findings: list[str] = []
    text = _read(path)
    if not text:
        return findings
    seen: set[str] = set()
    for section in next_sections(text):
        for plan_file in _PLAN_LINK.findall(section):
            if plan_file in seen:
                continue
            seen.add(plan_file)
            status = plan_status(plan_file)
            if status in SHIPPED_STATUSES:
                findings.append(
                    f"{path.name}: ▶ Next links '{plan_file}' whose plan Status is "
                    f"`{status}` (shipped/complete) — re-point ▶ Next at buildable work "
                    f"(Q-0166 fix-on-sight).",
                )
    return findings


def run() -> list[str]:
    """Run the check over every sector file and return the combined findings."""
    if not SECTOR_DIR.is_dir():
        return [f"cannot read sector dir {SECTOR_DIR}"]
    findings: list[str] = []
    for path in sorted(SECTOR_DIR.glob("S*.md")):
        findings += check_sector_file(path)
    return findings


def main() -> int:
    """CLI entry point: print findings and return an exit code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="suppress output; return exit code only",
    )
    args = parser.parse_args()

    findings = run()
    if findings:
        if not args.quiet:
            print("check_sector_next_freshness: FAIL — ▶ Next points at shipped work:")
            for f in findings:
                print(f"  - {f}")
        return 1
    if not args.quiet:
        n = len(sorted(SECTOR_DIR.glob("S*.md")))
        print(
            f"check_sector_next_freshness: OK — {n} sector files, "
            f"no ▶ Next item points at a shipped (`historical`) plan ✓",
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
