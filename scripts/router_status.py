#!/usr/bin/env python3.10
"""Digest the maintainer question router — next free Q-number + the open queue.

Reads ``docs/owner/maintainer-question-router.md`` (the append-only owner-decision
log, ~180+ ``### Q-NNNN`` blocks) and reports:

* the **highest** ``Q-NNNN`` and the **next free** number — so a session appending a
  new block (the append-only convention) gets the right number without grepping a
  6,500-line file by hand;
* the blocks still **OPEN** (awaiting an owner decision) vs **DECIDED**, plus an
  honest **UNCLASSIFIED** bucket for blocks whose leading status marker does not
  match a known token; and
* **PARTIAL** blocks — decided at the top but still carrying an unresolved
  ``Still open`` / ``Open (owner deciding …)`` **sub-part** (the case a
  leading-marker-only scan misses: Q-0173 / Q-0175 shipped *decided* yet parked
  named sub-questions for the owner — invisible to a marker scan, found only by
  reading the block).

Classification reads each block's first ``> **<MARKER>`` line (the house
convention): ``DECISION`` / ``DECIDED`` / ``ANSWERED`` / ``DIRECTED`` / ``APPLIED``
… = decided; ``OPEN`` / ``PROPOSED`` / ``PARTLY DECIDED`` / ``DISCUSS`` = open.
Sub-part detection is independent of the leading marker: a bolded line that
*starts* with ``Still open`` or ``Open (owner deciding`` flags the block **unless**
its span (down to the next blank line) carries a resolution token (``RESOLVED`` /
``DECIDED`` / ``ANSWERED``) or its items are struck through (``~~…~~``) — so a
fully-resolved sub-list stops flagging.

Pure stdlib, read-only — never writes the router. Useful with the website
owner-zone "open decisions" surface (it could feed ``export_dashboard_data.py``).

Reliability (Q-0105): **UNVERIFIED.** The next-number output is exact (a header
parse). The OPEN/DECIDED split is a **heuristic** over the leading-marker
convention and is reported alongside an ``UNCLASSIFIED`` list precisely so a human
can confirm what the tool was unsure about (the Q-0120 "verify the tool against
the evidence" discipline). The **PARTIAL sub-part** detector is a deliberately
conservative heuristic (the header must *start* a line; any resolution token or
struck-through items clear it) — tuned to report **zero false positives on the
committed router** as of 2026-06-19, and surfaced as a "verify" bucket, not an
assertion (it errs toward under-flagging, like the rest of this digest). Confirm
both against the file a few times across sessions before trusting them; **delete
this script if it proves unreliable** — it is a convenience digest, not
load-bearing.
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

# A bolded sub-part header *inside* an otherwise-decided block: a line that *starts*
# with "Still open" / "Open (owner deciding" (after optional ``**`` and quote ``>``).
# Starting the line is what distinguishes a declared sub-part header from a
# mid-sentence prose mention of "still open".
_SUBPART_HEAD_RE = re.compile(
    r"^\*{0,2}\s*(?:still open|open \(owner deciding)",
    re.IGNORECASE,
)
# If any of these appears anywhere in the header's span, the sub-parts are resolved.
_SUBPART_RESOLVED = ("RESOLVED", "DECIDED", "ANSWERED")
# Struck-through item, e.g. ``~~one shared grid vs. per-depth-level~~``.
_STRUCK_RE = re.compile(r"~~.*?~~")

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
    open_subpart: str = ""  # text of an unresolved sub-part (decided block), else ""


def classify(marker: str) -> str:
    """Classify a block by its leading bold marker text."""
    upper = marker.strip().upper()
    if upper.startswith(_OPEN_TOKENS):
        return "open"
    if upper.startswith(_DECIDED_TOKENS):
        return "decided"
    return "unclassified"


def detect_open_subparts(body_lines: list[str]) -> str | None:
    """Return an unresolved 'still open' sub-part's text, or ``None``.

    The router parks sub-questions the owner still owns *inside* an otherwise-decided
    block with a bolded header that **starts** a line — ``**Still open (owner
    deciding …):**`` or ``**Open (owner deciding …):**``. When those sub-parts are
    later resolved, the header's span (down to the next blank line) gains a
    ``RESOLVED`` / ``DECIDED`` / ``ANSWERED`` continuation, or the items are struck
    through (``~~…~~``). So a header counts as *still open* only when its span carries
    no resolution token and still has a non-struck item — the conservative rule that
    reports zero false positives on the committed router (2026-06-19).
    """
    for idx, raw in enumerate(body_lines):
        probe = raw.strip().lstrip(">").strip()
        if not _SUBPART_HEAD_RE.match(probe):
            continue
        # The span is the header line through the next blank line (resolutions are
        # appended as following ``→ RESOLVED …`` lines, so they belong to the span).
        span = [probe]
        for nxt in body_lines[idx + 1 :]:
            if not nxt.strip():
                break
            span.append(nxt.strip())
        span_text = " ".join(span)
        if any(tok in span_text.upper() for tok in _SUBPART_RESOLVED):
            continue  # the sub-parts were resolved in place
        # Drop struck items, then the header prefix up to its first colon; whatever
        # substantive text remains is the unresolved sub-question(s).
        remaining = _STRUCK_RE.sub("", span_text)
        _, sep, after = remaining.partition(":")
        candidate = (after if sep else remaining).strip(" *·—–-")
        if candidate:
            return candidate
    return None


def parse_blocks(text: str) -> list[QBlock]:
    """Parse the router markdown into a list of :class:`QBlock` (in file order)."""
    lines = text.splitlines()
    blocks: list[QBlock] = []
    current: dict[str, str | int] | None = None
    body: list[str] = []
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
                    open_subpart=detect_open_subparts(body) or "",
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
            body = []
            marker_found = False
            continue
        if current is not None:
            body.append(line)
            if not marker_found:
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


def partial_blocks(blocks: list[QBlock]) -> list[QBlock]:
    """Decided blocks that still carry an unresolved sub-part.

    Excludes blocks that are already OPEN at the top — those surface in the OPEN
    list, so this avoids double-counting them.
    """
    return [b for b in blocks if b.status != "open" and b.open_subpart]


def _print_block_lines(blocks: list[QBlock]) -> None:
    for b in blocks:
        print(f"  {b.qid} — {b.title or '(untitled)'}  [{b.marker or 'no marker'}]")


def _print_partial_lines(blocks: list[QBlock]) -> None:
    for b in blocks:
        print(f"  {b.qid} — {b.title or '(untitled)'}")
        print(f"      ↳ open sub-part: {b.open_subpart}")


def _print_digest(blocks: list[QBlock]) -> None:
    open_blocks = [b for b in blocks if b.status == "open"]
    decided = sum(1 for b in blocks if b.status == "decided")
    unclassified = [b for b in blocks if b.status == "unclassified"]
    partial = partial_blocks(blocks)
    print("question-router status")
    print(
        f"  blocks: {len(blocks)}  ·  decided: {decided}  ·  "
        f"open: {len(open_blocks)}  ·  partial: {len(partial)}  ·  "
        f"unclassified: {len(unclassified)}",
    )
    print(f"  next free number: {next_number(blocks)}")
    print()
    print(f"OPEN — awaiting an owner decision ({len(open_blocks)}):")
    if open_blocks:
        _print_block_lines(open_blocks)
    else:
        print("  (none)")
    print()
    print(
        f"PARTIAL — decided, but an open sub-part remains to verify ({len(partial)}):",
    )
    if partial:
        _print_partial_lines(partial)
    else:
        print("  (none)")
    if unclassified:
        # Mostly older blocks with no leading `> **MARKER**` line — summarise, don't
        # dump; the actionable signal is the OPEN/PARTIAL lists above. `--unclassified`
        # lists them.
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
        "--subparts",
        action="store_true",
        help="print only the PARTIAL blocks (decided, with an open sub-part)",
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
    elif args.subparts:
        _print_partial_lines(partial_blocks(blocks))
    elif args.unclassified:
        _print_block_lines([b for b in blocks if b.status == "unclassified"])
    else:
        _print_digest(blocks)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
