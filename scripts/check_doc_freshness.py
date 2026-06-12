#!/usr/bin/env python3
"""Advisory staleness check for dated snapshot docs (``audit`` / ``plan`` badges).

A dated review (readiness map, audit, point-in-time plan) silently rots as the source
it describes moves. This walks those docs, reads their as-of date, and warns when a
source path they cite has been changed in git **since** that date — "this doc may be
stale; re-verify before trusting it".

    python3.10 scripts/check_doc_freshness.py            # summary
    python3.10 scripts/check_doc_freshness.py --list     # + which paths changed

**Always exits 0** — this is a signal, never a gate (a stale snapshot is expected, not a
build failure). Heuristic: it only flags docs that (a) carry a date and an ``audit``/``plan``
badge and (b) cite source paths under disbot/ · scripts/ · tools/ that exist today.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_ROOT = REPO_ROOT / "docs"

_DATE_RE = re.compile(r"(20\d{2}-\d{2}-\d{2})")
_BADGE_RE = re.compile(r">\s*\*\*Status:\*\*\s*`([a-z-]+)`")
_PATH_RE = re.compile(r"`((?:disbot|scripts|tools)/[A-Za-z0-9_./-]+)`")
_BADGES = {"audit", "plan"}


@dataclass
class Stale:
    doc: Path
    as_of: str
    changed: list[str]
    cited: int


def _doc_meta(path: Path) -> tuple[str | None, str | None]:
    """Return ``(badge, as_of_date)`` for a doc, reading filename then header."""
    head = path.read_text(encoding="utf-8")[:2000]
    badge_m = _BADGE_RE.search(head)
    badge = badge_m.group(1) if badge_m else None
    name_date = _DATE_RE.search(path.name)
    header_date = _DATE_RE.search(head)
    as_of = (
        name_date.group(1)
        if name_date
        else (header_date.group(1) if header_date else None)
    )
    return badge, as_of


def _cited_paths(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    seen: list[str] = []
    for m in _PATH_RE.findall(text):
        clean = m.split("#")[0].rstrip(".")
        if clean not in seen and (REPO_ROOT / clean).exists():
            seen.append(clean)
    return seen


def _changed_since(rel: str, date: str) -> bool:
    """True if ``rel`` has a commit strictly after ``date``."""
    try:
        out = subprocess.run(
            ["git", "log", "-1", f"--since={date} 23:59:59", "--format=%h", "--", rel],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
    return bool(out)


def scan() -> list[Stale]:
    results: list[Stale] = []
    for path in sorted(DOCS_ROOT.rglob("*.md")):
        badge, as_of = _doc_meta(path)
        if badge not in _BADGES or not as_of:
            continue
        cited = _cited_paths(path)
        if not cited:
            continue
        changed = [p for p in cited if _changed_since(p, as_of)]
        if changed:
            results.append(Stale(path, as_of, changed, len(cited)))
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Advisory staleness check for dated docs.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List the changed source paths per doc.",
    )
    args = parser.parse_args(argv)

    stale = scan()
    if not stale:
        print(
            "doc-freshness: no dated audit/plan docs have cited source changed since their date.",
        )
        return 0

    print(
        f"doc-freshness: {len(stale)} dated doc(s) MAY be stale (advisory — not a failure):\n",
    )
    for s in sorted(stale, key=lambda x: len(x.changed), reverse=True):
        rel = s.doc.relative_to(REPO_ROOT)
        print(
            f"  • {rel}  (as of {s.as_of}) — {len(s.changed)}/{s.cited} cited paths changed since",
        )
        if args.list:
            for p in s.changed[:12]:
                print(f"      - {p}")
    print(
        "\n  Re-verify these against current source before trusting them as execution queues.",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
