#!/usr/bin/env python3.10
"""Render the live per-sector dispatch menu from the roadmap.

Provenance / reliability header (per CLAUDE.md Q-0105 adopt-with-kill-switch):
- Why: the #880 dispatch test showed that "what would a worker dispatched to sector SX
  actually pick up?" is answerable by hand in 2-3 hops, but only by reading prose. This is
  the machine version (the #880 Q-0089 idea): parse the ``roadmap.md`` per-sector dispatch
  index and print, per sector, the first **▶ startable** item, its executor, and a flag for
  a "starving" sector whose ``Now`` is entirely blocked (⛔/👤). A dispatcher (or Hermes)
  picks from this generated, always-fresh menu instead of re-reading the roadmap.
- Added: 2026-06-14 (Q-0143 follow-on). **Unverified** — confirm its output against the
  roadmap a few times before trusting it. **Delete this script if it proves unreliable**;
  it is a disposable convenience reporter, read-only, not load-bearing.

The parsing helpers here intentionally mirror ``check_sector_map.py`` (each script stays a
self-contained single file — the repo's standalone-script convention; ``isort src_paths``
makes cross-script imports brittle). If a third consumer appears, factor a shared module.

Usage::

    python3.10 scripts/dispatch_menu.py            # all sectors
    python3.10 scripts/dispatch_menu.py S2          # one sector
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ROADMAP = REPO_ROOT / "docs" / "roadmap.md"

_SECTOR_HEADING = re.compile(r"^###\s+(S\d)\s+—\s+(.+?)\s+·")
_BULLET_HEAD = re.compile(r"^- \*\*([^:*]+):\*\*")
_EXECUTOR = re.compile(r"executor \*\*([^*]+)\*\*")
_ITEM_SEP = re.compile(r" · | — | \(")


def _read(path: Path) -> str:
    """Return file text, or empty string if unreadable."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def by_sector_section(text: str) -> str:
    """Return the roadmap text between '## By sector' and the next '## ' heading."""
    start = text.find("## By sector")
    if start == -1:
        return ""
    rest = text[start + len("## By sector") :]
    nxt = rest.find("\n## ")
    return rest if nxt == -1 else rest[:nxt]


def sector_blocks(section: str) -> list[tuple[str, str, str]]:
    """Return ordered ``(id, name, block_text)`` tuples for each ``### S<n>`` block."""
    blocks: list[tuple[str, str, str]] = []
    cur_id: str | None = None
    cur_name = ""
    buf: list[str] = []
    for line in section.splitlines():
        m = _SECTOR_HEADING.match(line)
        if m:
            if cur_id:
                blocks.append((cur_id, cur_name, "\n".join(buf)))
            cur_id, cur_name = m.group(1), m.group(2).strip()
            buf = [line]
        elif cur_id:
            buf.append(line)
    if cur_id:
        blocks.append((cur_id, cur_name, "\n".join(buf)))
    return blocks


def bullet_text(block: str, label: str) -> str:
    """Return the text of the ``- **<label>...:**`` bullet (incl. continuation lines)."""
    out: list[str] = []
    grabbing = False
    for line in block.splitlines():
        m = _BULLET_HEAD.match(line)
        if m:
            if grabbing:
                break
            if m.group(1).strip().startswith(label):
                grabbing = True
                out.append(line)
        elif grabbing:
            out.append(line)
    return "\n".join(out)


def first_startable(bullet: str) -> str | None:
    """Return the first ▶-tagged item's short label in a bullet, or None.

    Tolerates the markup variants (``**▶ X**``, ``**▶** the … **X**``): collapse
    whitespace, drop markdown link targets and emphasis/bracket punctuation, then take
    the text up to the first item separator (·, em-dash, or an opening paren).
    """
    if "▶" not in bullet:
        return None
    after = " ".join(bullet.split("▶", 1)[1].split())
    after = re.sub(r"\]\([^)]*\)", "]", after)  # drop link targets
    after = after.replace("**", "").replace("[", "").replace("]", "")
    after = _ITEM_SEP.split(after, maxsplit=1)[0]
    after = after.strip(" *:-")
    return after[:60].strip() or None


def resolve(block: str) -> tuple[str, str]:
    """Return ``(executor, dispatch_line)`` for a sector block."""
    dispatch = bullet_text(block, "Dispatch")
    m = _EXECUTOR.search(dispatch)
    executor = m.group(1).strip() if m else "?"
    return executor, dispatch


def menu_line(block: str) -> str:
    """Return the one-line 'what's dispatchable' summary for a sector block."""
    now = bullet_text(block, "Now")
    now_item = first_startable(now)
    if now_item:
        return f"▶ Now: {now_item}"
    nxt_item = first_startable(bullet_text(block, "Next"))
    if "⛔" in now or "👤" in now:
        if nxt_item:
            return f"⛔/👤 Now blocked → ▶ Next: {nxt_item}"
        return (
            "⛔/👤 Now blocked — no ▶ startable item (route to executor / surface one)"
        )
    if nxt_item:
        return f"▶ Next: {nxt_item}"
    return "(no ▶ startable item found — check the roadmap)"


def build_menu(text: str, only: str | None = None) -> list[str]:
    """Return the rendered menu lines for all sectors (or one, if ``only`` given)."""
    blocks = sector_blocks(by_sector_section(text))
    if not blocks:
        return ["(no '## By sector' dispatch index found in roadmap.md)"]
    lines: list[str] = []
    for sid, name, block in blocks:
        if only and sid != only:
            continue
        executor, _ = resolve(block)
        lines.append(f"{sid}  {name:<22}  exec: {executor}")
        lines.append(f"      {menu_line(block)}")
    if only and not any(line.startswith(only) for line in lines):
        return [f"(sector {only} not found — valid: S1..S5)"]
    return lines


def main() -> int:
    """CLI entry point: print the dispatch menu."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "sector",
        nargs="?",
        help="optional single sector id (e.g. S2) to show only that sector",
    )
    args = parser.parse_args()

    text = _read(ROADMAP)
    if not text:
        print(f"dispatch_menu: cannot read {ROADMAP}")
        return 1

    only = args.sector.upper() if args.sector else None
    print("SuperBot — sector dispatch menu  (live, from docs/roadmap.md § By sector)")
    print("=" * 72)
    for line in build_menu(text, only):
        print(line)
    print("=" * 72)
    print(
        "tags: ▶ startable · ⛔ gated · 👤 maintainer   |   contract: repo-sector-map.md",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
