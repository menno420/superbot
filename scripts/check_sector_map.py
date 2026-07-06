#!/usr/bin/env python3.10
"""Validate the 5-sector planning partition is complete and self-consistent.

Provenance / reliability header (per CLAUDE.md Q-0105 adopt-with-kill-switch):
- Why: the sector dispatch structure (``docs/repo-sector-map.md`` + the ``roadmap.md``
  per-sector dispatch index, owner decisions Q-0137/Q-0143) encodes its homing, executor,
  and startability conventions in **prose**. A live dogfooding test (#880) flagged that as
  the weak point: a new folio could go un-homed, or a ``Now`` item ship untagged, with
  nothing to catch it until a human noticed. This checker makes the convention
  machine-checked instead of prose-asserted.
- Added: 2026-06-14 (Q-0143 follow-on). **Unverified** — confirm its output against ground
  truth over a few sessions before trusting it. **Delete this script if it proves
  noisy/unreliable over multiple sessions**; it is a disposable convenience guard, not
  load-bearing. It is intentionally NOT wired into CI (that is ask-first per the autonomy
  boundary) — run it by hand or from the docs-reconciliation routine.

What it checks (read-only; exits 1 on any violation, 0 when clean):
1. Folio homing — every ``docs/subsystems/*.md`` folio (minus README) is homed to exactly
   one sector in the machine-readable ``sector-folio-map`` block of ``repo-sector-map.md``
   (no orphan, no phantom, no double-home).
2. Sector presence — sectors S1..S5 each appear as a ``### S<n>`` block in BOTH
   ``repo-sector-map.md`` and the ``roadmap.md`` "By sector" dispatch index.
3. Dispatch convention — every roadmap sector's ``Dispatch`` bullet names an executor, and
   every sector's ``Now`` bullet carries at least one startability tag (▶/⛔/👤) or a done
   marker (✅).

Usage::

    python3.10 scripts/check_sector_map.py            # report + exit code
    python3.10 scripts/check_sector_map.py --quiet     # exit code only
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SECTOR_MAP = REPO_ROOT / "docs" / "repo-sector-map.md"
ROADMAP = REPO_ROOT / "docs" / "roadmap.md"
FOLIO_DIR = REPO_ROOT / "docs" / "subsystems"

EXPECTED_SECTORS = ["S1", "S2", "S3", "S4", "S5"]
STARTABILITY_GLYPHS = ("▶", "⛔", "👤", "✅")
# The orthogonal unattended-fit tag (#1285): can a scheduled empty-fire run *finish & merge* it?
_UNATTENDED_FIT = re.compile(r"unattended-fit \*\*[^*]+\*\*")

_FOLIO_MAP_BLOCK = re.compile(
    r"<!--\s*BEGIN sector-folio-map.*?-->(.*?)<!--\s*END sector-folio-map",
    re.DOTALL,
)
_FOLIO_MAP_LINE = re.compile(r"^\s*(S\d):\s*(.+?)\s*$")
_SECTOR_HEADING = re.compile(r"^###\s+(S\d)\b")


def _read(path: Path) -> str:
    """Return the file text, or an empty string if it does not exist."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def folios_on_disk() -> set[str]:
    """Return the set of subsystem folio stems (excluding the README index)."""
    return {p.stem for p in FOLIO_DIR.glob("*.md") if p.stem != "README"}


def parse_folio_map(text: str) -> tuple[dict[str, str], list[str]]:
    """Parse the machine-readable folio→sector block.

    Returns ``(folio_to_sector, errors)``. A folio listed under two sectors is an error.
    """
    errors: list[str] = []
    block = _FOLIO_MAP_BLOCK.search(text)
    if not block:
        errors.append(
            "repo-sector-map.md: missing the <!-- BEGIN sector-folio-map --> block.",
        )
        return {}, errors

    mapping: dict[str, str] = {}
    for line in block.group(1).splitlines():
        m = _FOLIO_MAP_LINE.match(line)
        if not m:
            continue
        sector, folios = m.group(1), m.group(2)
        for folio in (f.strip() for f in folios.split(",")):
            if not folio:
                continue
            if folio in mapping:
                errors.append(
                    f"folio '{folio}' is double-homed ({mapping[folio]} and {sector}).",
                )
            mapping[folio] = sector
    return mapping, errors


def check_folio_homing(text: str) -> list[str]:
    """Every folio on disk is homed exactly once; nothing phantom is listed."""
    mapping, errors = parse_folio_map(text)
    disk = folios_on_disk()
    listed = set(mapping)
    for folio in sorted(disk - listed):
        errors.append(
            f"folio '{folio}' exists in docs/subsystems/ but is not homed to a sector "
            f"(add it to the sector-folio-map block).",
        )
    for folio in sorted(listed - disk):
        errors.append(
            f"folio '{folio}' is listed in the sector-folio-map but has no "
            f"docs/subsystems/{folio}.md (phantom — remove or rename it).",
        )
    for folio, sector in sorted(mapping.items()):
        if sector not in EXPECTED_SECTORS:
            errors.append(f"folio '{folio}' homed to unknown sector '{sector}'.")
    return errors


def sectors_in(text: str) -> list[str]:
    """Return the ordered S<n> ids that appear as ``### S<n>`` headings."""
    return [
        m.group(1) for line in text.splitlines() if (m := _SECTOR_HEADING.match(line))
    ]


def by_sector_section(text: str) -> str:
    """Return the roadmap text between '## By sector' and the next '## ' heading."""
    start = text.find("## By sector")
    if start == -1:
        return ""
    rest = text[start + len("## By sector") :]
    nxt = rest.find("\n## ")
    return rest if nxt == -1 else rest[:nxt]


def sector_blocks(section: str) -> dict[str, str]:
    """Split a By-sector section into {S<n>: block_text} by ``### S<n>`` headings."""
    blocks: dict[str, str] = {}
    current: str | None = None
    buf: list[str] = []
    for line in section.splitlines():
        m = _SECTOR_HEADING.match(line)
        if m:
            if current:
                blocks[current] = "\n".join(buf)
            current = m.group(1)
            buf = [line]
        elif current:
            buf.append(line)
    if current:
        blocks[current] = "\n".join(buf)
    return blocks


def bullet_text(block: str, label: str) -> str | None:
    """Return the text of the ``- **<label>...:**`` bullet (incl. continuation lines)."""
    lines = block.splitlines()
    out: list[str] = []
    grabbing = False
    head = re.compile(r"^- \*\*([^:*]+):\*\*")
    for line in lines:
        m = head.match(line)
        if m:
            if grabbing:
                break
            if m.group(1).strip().startswith(label):
                grabbing = True
                out.append(line)
        elif grabbing:
            out.append(line)
    return "\n".join(out) if out else None


def check_roadmap_convention(text: str) -> list[str]:
    """Each roadmap sector names an executor and tags its Now item."""
    errors: list[str] = []
    section = by_sector_section(text)
    if not section:
        errors.append("roadmap.md: missing the '## By sector' dispatch index.")
        return errors
    blocks = sector_blocks(section)
    for sector in EXPECTED_SECTORS:
        block = blocks.get(sector)
        if block is None:
            errors.append(f"roadmap.md: sector {sector} has no '### {sector}' block.")
            continue
        dispatch = bullet_text(block, "Dispatch")
        if dispatch is None or "executor" not in dispatch:
            errors.append(
                f"roadmap.md {sector}: Dispatch bullet is missing an 'executor' label.",
            )
        if dispatch is not None and not _UNATTENDED_FIT.search(dispatch):
            errors.append(
                f"roadmap.md {sector}: Dispatch bullet is missing an 'unattended-fit "
                f"**<glyph> <auto|review|live|ext-data>**' tag (the #1285 dimension — "
                f"see repo-sector-map.md § 'the unattended-fit tag').",
            )
        now = bullet_text(block, "Now")
        if now is None:
            errors.append(f"roadmap.md {sector}: missing a 'Now' bullet.")
        elif not any(g in now for g in STARTABILITY_GLYPHS):
            errors.append(
                f"roadmap.md {sector}: Now bullet has no startability tag "
                f"(one of ▶/⛔/👤/✅).",
            )
    return errors


def check_sector_presence(map_text: str, road_text: str) -> list[str]:
    """S1..S5 each appear in both maps."""
    errors: list[str] = []
    in_map = sectors_in(map_text)
    in_road = sectors_in(by_sector_section(road_text))
    for sector in EXPECTED_SECTORS:
        if sector not in in_map:
            errors.append(f"repo-sector-map.md: sector {sector} block is missing.")
        if sector not in in_road:
            errors.append(f"roadmap.md By-sector: sector {sector} block is missing.")
    return errors


def run() -> list[str]:
    """Run every check and return the combined list of violation strings."""
    map_text = _read(SECTOR_MAP)
    road_text = _read(ROADMAP)
    errors: list[str] = []
    if not map_text:
        return [f"cannot read {SECTOR_MAP}"]
    if not road_text:
        return [f"cannot read {ROADMAP}"]
    errors += check_folio_homing(map_text)
    errors += check_sector_presence(map_text, road_text)
    errors += check_roadmap_convention(road_text)
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
            print("check_sector_map: FAIL — sector partition has drift:")
            for err in errors:
                print(f"  - {err}")
        return 1
    if not args.quiet:
        n_folios = len(folios_on_disk())
        print(
            f"check_sector_map: OK — {n_folios} folios homed, "
            f"5 sectors present in both maps, dispatch convention satisfied ✓",
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
