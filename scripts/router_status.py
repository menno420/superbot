#!/usr/bin/env python3.10
"""Digest the maintainer question router — next free Q-number + the open queue.

Reads ``docs/owner/maintainer-question-router.md`` (the append-only owner-decision
log, ~180+ ``### Q-NNNN`` blocks) and reports:

* the **highest** ``Q-NNNN`` and the **next free** number — so a session appending a
  new block (the append-only convention) gets the right number without grepping a
  6,500-line file by hand; and
* the blocks still **OPEN** (awaiting an owner decision) vs **DECIDED**, plus an
  honest **UNCLASSIFIED** bucket for blocks whose leading status marker does not
  match a known token.

Classification reads each block's first ``> **<MARKER>`` line (the house
convention): ``DECISION`` / ``DECIDED`` / ``ANSWERED`` / ``DIRECTED`` / ``APPLIED``
… = decided; ``OPEN`` / ``PROPOSED`` / ``PARTLY DECIDED`` / ``DISCUSS`` = open.

Pure stdlib, read-only — never writes the router. Useful with the website
owner-zone "open decisions" surface (it could feed ``export_dashboard_data.py``).

Reliability (Q-0105): **UNVERIFIED.** The next-number output is exact (a header
parse). The OPEN/DECIDED split is a **heuristic** over the leading-marker
convention and is reported alongside an ``UNCLASSIFIED`` list precisely so a human
can confirm what the tool was unsure about (the Q-0120 "verify the tool against
the evidence" discipline). Confirm the classification against the file a few times
across sessions before trusting it; **delete this script if it proves unreliable**
— it is a convenience digest, not load-bearing.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ROUTER_FILE = REPO_ROOT / "docs" / "owner" / "maintainer-question-router.md"

# ``### Q-0179 — <title> (<date>)`` — number is the load-bearing capture; the title
# and trailing (YYYY-MM-DD) are best-effort.
_HEAD_RE = re.compile(r"^###\s+(Q-(\d{4}))\b\s*(?:[—–-]\s*(.*?))?\s*$")
# A block's first ``> **<bold>**`` quote line carries its status marker.
_MARKER_RE = re.compile(r"^>\s*\*\*(.+?)\*\*")
_DATE_RE = re.compile(r"\((\d{4}-\d{2}-\d{2})\)\s*$")

# Leading marker tokens (matched against the uppercased bold text via startswith).
# OPEN is checked first so "PARTLY DECIDED" classifies as open, not decided.
_OPEN_TOKENS = (
    "OPEN",
    "PROPOSED",
    "PARTLY",
    "DISCUSS",
    "UNDECIDED",
    "AWAITING",
    "PENDING",
)
_DECIDED_TOKENS = (
    "DECISION",
    "DECIDED",
    "ANSWERED",
    "DIRECTED",
    "APPLIED",
    "RESOLVED",
    "APPROVED",
    "NOW LIVE",
    "ROLLED OUT",
    "CLOSED",
    "CAPTURED",
)


@dataclass
class QBlock:
    """One ``### Q-NNNN`` router block."""

    number: int
    qid: str
    title: str
    date: str
    marker: str
    status: str  # "open" | "decided" | "unclassified"


def classify(marker: str) -> str:
    """Classify a block by its leading bold marker text."""
    upper = marker.strip().upper()
    if upper.startswith(_OPEN_TOKENS):
        return "open"
    if upper.startswith(_DECIDED_TOKENS):
        return "decided"
    return "unclassified"


def parse_blocks(text: str) -> list[QBlock]:
    """Parse the router markdown into a list of :class:`QBlock` (in file order)."""
    lines = text.splitlines()
    blocks: list[QBlock] = []
    current: dict[str, str | int] | None = None
    marker_found = False

    def _flush() -> None:
        if current is not None:
            marker = str(current["marker"])
            blocks.append(
                QBlock(
                    number=int(current["number"]),
                    qid=str(current["qid"]),
                    title=str(current["title"]),
                    date=str(current["date"]),
                    marker=marker,
                    status=classify(marker),
                ),
            )

    for line in lines:
        head = _HEAD_RE.match(line)
        if head:
            _flush()
            rest = (head.group(3) or "").strip()
            date_match = _DATE_RE.search(rest)
            date = date_match.group(1) if date_match else ""
            title = _DATE_RE.sub("", rest).strip() if date else rest
            current = {
                "number": int(head.group(2)),
                "qid": head.group(1),
                "title": title,
                "date": date,
                "marker": "",
            }
            marker_found = False
            continue
        if current is not None and not marker_found:
            marker = _MARKER_RE.match(line)
            if marker:
                current["marker"] = marker.group(1).strip()
                marker_found = True
    _flush()
    return blocks


def next_number(blocks: list[QBlock]) -> str:
    """The next free ``Q-NNNN`` for an append (highest + 1; ``Q-0001`` if empty)."""
    highest = max((b.number for b in blocks), default=0)
    return f"Q-{highest + 1:04d}"


def _print_block_lines(blocks: list[QBlock]) -> None:
    for b in blocks:
        print(f"  {b.qid} — {b.title or '(untitled)'}  [{b.marker or 'no marker'}]")


def _print_digest(blocks: list[QBlock]) -> None:
    open_blocks = [b for b in blocks if b.status == "open"]
    decided = sum(1 for b in blocks if b.status == "decided")
    unclassified = [b for b in blocks if b.status == "unclassified"]
    print("question-router status")
    print(
        f"  blocks: {len(blocks)}  ·  decided: {decided}  ·  "
        f"open: {len(open_blocks)}  ·  unclassified: {len(unclassified)}",
    )
    print(f"  next free number: {next_number(blocks)}")
    print()
    print(f"OPEN — awaiting an owner decision ({len(open_blocks)}):")
    if open_blocks:
        _print_block_lines(open_blocks)
    else:
        print("  (none)")
    if unclassified:
        # Mostly older blocks with no leading `> **MARKER**` line — summarise, don't
        # dump; the actionable signal is the OPEN list above. `--unclassified` lists them.
        print()
        print(
            f"unclassified: {len(unclassified)} block(s) with an unrecognised/absent "
            "marker (mostly older formats) — run --unclassified to list, --json for all.",
        )


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Digest the maintainer question router.",
    )
    parser.add_argument(
        "--router",
        default=str(ROUTER_FILE),
        help="router markdown path",
    )
    parser.add_argument(
        "--next",
        action="store_true",
        help="print only the next free Q-number",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="print only the OPEN blocks",
    )
    parser.add_argument(
        "--unclassified",
        action="store_true",
        help="print the blocks with an unrecognised/absent marker",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit the parsed blocks as JSON",
    )
    args = parser.parse_args(argv)

    path = Path(args.router)
    if not path.exists():
        parser.error(f"router file not found: {path}")
    blocks = parse_blocks(path.read_text(encoding="utf-8"))

    if args.next:
        print(next_number(blocks))
    elif args.json:
        print(json.dumps([asdict(b) for b in blocks], indent=2, ensure_ascii=False))
    elif args.open:
        _print_block_lines([b for b in blocks if b.status == "open"])
    elif args.unclassified:
        _print_block_lines([b for b in blocks if b.status == "unclassified"])
    else:
        _print_digest(blocks)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
