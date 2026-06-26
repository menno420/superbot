#!/usr/bin/env python3.10
"""check_plan_code_drift.py — flag planning docs still badged ``plan`` whose
implementation already exists in ``disbot/`` (the "shipped-but-not-rebadged" drift class).

[session-close-gate] Invoked from ``/session-close`` Step 4 (``check_session_close_gate.py`` enforces that this stays wired in).

PROVENANCE / RELIABILITY (owner-directed 2026-06-19, router Q-0181):
    Why: a ``plan``-badged doc whose code already shipped silently misleads the next
    agent into rebuilding it or mis-prioritising — the exact A3/A4 miss the 2026-06-19
    review surfaced. The "rebadge-on-ship" convention relies on a human remembering;
    this re-derives badge truth from the *code* instead (ground truth > a hand-kept badge).

    UNVERIFIED — heuristic. Its hits are *candidates for human review*, not proof: a plan
    may legitimately reference existing code it intends to *extend*. Confirm its output
    against ground truth across a few sessions before trusting it, and **delete this script
    if it proves noisy/unreliable over multiple sessions** rather than working around it.

How: for each ``plan``-badged planning doc, extract the implementation artifacts it *names*
— ``disbot/.../*.py`` paths and back-ticked symbols that are real ``def``/``class`` names in
``disbot/`` — and report which already exist. A plan that names implementation which now
exists is a **rebadge candidate** (likely shipped → should be ``historical``).

Advisory by default (exit 0). ``--strict`` exits 1 when candidates are found, so it can be
wired into CI once it has earned trust.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLANNING = ROOT / "docs" / "planning"
DISBOT = ROOT / "disbot"

# A doc is in scope only if its front-matter Status badge is `plan` (buildable spec).
_PLAN_BADGE = re.compile(r"Status:\*\*\s*`plan`")
# Implementation file paths a plan names (in or out of back-ticks).
_DISBOT_PATH = re.compile(r"disbot/[A-Za-z0-9_/]+\.py")
# Back-ticked tokens — plans cite code symbols in back-ticks; we only keep ones that are
# real disbot symbols (below), so prose in back-ticks never counts.
_BACKTICKED = re.compile(r"`([^`]+)`")
_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]+$")
# def / class definitions in disbot source.
_DEF_CLASS = re.compile(
    r"^[ \t]*(?:async[ \t]+)?def[ \t]+([a-z_][A-Za-z0-9_]+)"
    r"|^[ \t]*class[ \t]+([A-Za-z_][A-Za-z0-9_]+)",
    re.MULTILINE,
)
# Symbols too generic to be evidence (would match across unrelated code).
_GENERIC = frozenset(
    {
        "run",
        "main",
        "build",
        "setup",
        "handle",
        "process",
        "execute",
        "start",
        "stop",
        "snapshot",
        "reset",
        "render",
        "update",
        "create",
        "get",
        "load",
    },
)


def _disbot_symbols() -> set[str]:
    syms: set[str] = set()
    for p in DISBOT.rglob("*.py"):
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in _DEF_CLASS.finditer(text):
            syms.add(m.group(1) or m.group(2))
    return syms - _GENERIC


def _disbot_files() -> set[str]:
    return {str(p.relative_to(ROOT)) for p in DISBOT.rglob("*.py")}


def _plan_docs() -> list[Path]:
    out = []
    for p in sorted(PLANNING.glob("*.md")):
        head = p.read_text(encoding="utf-8", errors="ignore")[:1500]
        if _PLAN_BADGE.search(head):
            out.append(p)
    return out


class Candidate:
    def __init__(self, path: Path, exist_paths: set[str], exist_syms: set[str]) -> None:
        self.path = path
        self.exist_paths = exist_paths
        self.exist_syms = exist_syms

    @property
    def strong(self) -> bool:
        # Strong = the plan named a file that now exists AND ≥1 of its named symbols
        # is a real disbot def/class. Weak = only one kind of evidence.
        return bool(self.exist_paths) and bool(self.exist_syms)


# A symbol cited by this many *or more* distinct plans is shared infrastructure
# (BaseView, SettingSpec, HubView, debit, …), not any single plan's deliverable — so it
# is not evidence that a *particular* plan shipped. Keep only plan-specific symbols.
_SHARED_PLAN_THRESHOLD = 3


def scan() -> list[Candidate]:
    disbot_syms = _disbot_symbols()
    disbot_files = _disbot_files()

    # Pass 1: gather each plan's named (and real) paths + symbols, and count how many
    # distinct plans cite each symbol (the specificity signal).
    raw: list[tuple[Path, set[str], set[str]]] = []
    sym_plan_count: dict[str, int] = {}
    for doc in _plan_docs():
        text = doc.read_text(encoding="utf-8", errors="ignore")
        paths = {p for p in _DISBOT_PATH.findall(text) if p in disbot_files}
        syms = {
            t for t in _BACKTICKED.findall(text) if _IDENT.match(t) and t in disbot_syms
        }
        for s in syms:
            sym_plan_count[s] = sym_plan_count.get(s, 0) + 1
        raw.append((doc, paths, syms))

    # Pass 2: drop shared-infrastructure symbols, then keep plans that still name real
    # implementation — a real file path, or ≥2 plan-specific symbols.
    candidates: list[Candidate] = []
    for doc, paths, syms in raw:
        specific = {s for s in syms if sym_plan_count[s] < _SHARED_PLAN_THRESHOLD}
        if paths or len(specific) >= 2:
            candidates.append(Candidate(doc, paths, specific))
    return candidates


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 if any rebadge candidate is found (for CI once trusted)",
    )
    args = ap.parse_args()

    candidates = scan()
    if not candidates:
        print("check_plan_code_drift: no `plan`-badged docs reference shipped code ✓")
        return 0

    strong = [c for c in candidates if c.strong]
    print(
        f"check_plan_code_drift: {len(candidates)} `plan`-badged doc(s) reference code that "
        f"already exists — REBADGE CANDIDATES (verify completion, then rebadge `historical`):\n",
    )
    for c in sorted(candidates, key=lambda c: (not c.strong, c.path.name)):
        tag = "STRONG" if c.strong else "weak  "
        print(f"  [{tag}] docs/planning/{c.path.name}")
        if c.exist_paths:
            print(f"           files present : {', '.join(sorted(c.exist_paths))}")
        if c.exist_syms:
            shown = ", ".join(sorted(c.exist_syms)[:6])
            more = "" if len(c.exist_syms) <= 6 else f" (+{len(c.exist_syms) - 6})"
            print(f"           symbols present: {shown}{more}")
    print(
        "\n  NOTE: heuristic — a plan may *extend* existing code rather than have shipped. "
        "Verify each against the code before rebadging. (STRONG = named file + symbol both exist.)",
    )
    return 1 if (args.strict and strong) else 0


if __name__ == "__main__":
    raise SystemExit(main())
