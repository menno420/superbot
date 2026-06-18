#!/usr/bin/env python3
"""Emit the autonomous-loop **phase signal**: fix-phase vs. invent-phase.

> **ADVISORY-ONLY as of owner directive Q-0172 (2026-06-17).** The maintainer **opened the
> idea→plan gate**: any agent may now promote an idea → plan → implementation at any time
> *without approval*, flagging it on the `⚑ Self-initiated:` run-report line for review (the
> work is reversible). So this script **no longer blocks** feature origination — it is a
> *"bugs-first season" readout* that informs **priority** (correctness work still comes first
> when bugs/Not-Done rows exist), not **permission**. `--require-invent` still reports the same
> phase/exit code for anyone who wants the signal, but the dispatch routine no longer treats
> exit 1 as "refuse to build." Bugs-first is still binding via the Working agreement
> ("Bugs first, durably"); this gate just stopped being a hard fence around self-invented work.

The maintainer's autonomous-improvement loop is explicitly *ordered* (vision:
``docs/ideas/autonomous-improvement-loop-vision-2026-06-12.md`` §2): bugs first,
then UX, then "everything works," and **only then** agent-originated features.
An ungated loop would invent features while bugs remain. This script is the
machine-readable gate that says which season we are in, so an autonomous routine
can refuse to *originate a new feature* until correctness work is done.

It is the implementation of owner decision **Q-0114** (the human approve/deny
gate applies to agent-originated *features*; bug/UX/docs/correctness work flows
freely) — the phase signal is what tells a routine whether feature-origination
is even in-season.

**Scope (Q-0114 clarification, owner-stated 2026-06-15):** this gate is for
**agent-SELF-originated** features — ones an agent invents mid-session. A
**dispatched** work order (fired at a routine via the ``/fire`` endpoint, even
when tagged ``CLASS: feature``) is **owner-directed** and flows freely like a bug
fix — do NOT gate it. So a routine resolving a ``feature`` work order splits on
*origin*: dispatched ⇒ build; self-invented ⇒ guard with ``--require-invent`` and,
in fix-phase, capture-and-stop. (Background: the router Q-0114 entry +
``docs/ideas/dispatch-phase-gate-precheck-2026-06-15.md``.)

## The signal

Two hard conditions must both hold to be in **invent-phase**:

1. **Zero OPEN bugs** in the bug book (``docs/health/bug-book.md``) — "bugs first".
2. **Zero ``Not Done`` rows** across the production-readiness maps — "everything
   works" (parsed via ``readiness_scoreboard.collect()``; no duplication).

Otherwise the loop is in **fix-phase**: only bug fixes, UX polish, docs, and
correctness work are in-season; agent-*originated* features stay gated.

``Done %`` is reported for context but is **not** a gate condition — a subsystem
can be 100% Not-Done-free while still carrying Partial rows (refinements that are
not blockers). The two hard conditions above are the bar the maintainer stated.

## Usage

    python3.10 scripts/check_phase_gate.py            # human-readable report
    python3.10 scripts/check_phase_gate.py --phase    # prints `fix` or `invent`
    python3.10 scripts/check_phase_gate.py --json      # machine-readable JSON
    python3.10 scripts/check_phase_gate.py --require-invent
        # exit 0 only in invent-phase; exit 1 (with reasons) in fix-phase.
        # This is the line an "originate a feature" routine guards itself with.

> **Provenance (Q-0105 reliability header):** added 2026-06-12 for the autonomous
> loop (Q-0113/Q-0114). **Unverified** — confirm its phase call against the real
> bug book + readiness maps a few times across sessions before a routine trusts it
> to gate work. **Delete this if it proves unreliable over multiple sessions** —
> it is a convenience gate, not load-bearing runtime code.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BUG_BOOK = REPO_ROOT / "docs" / "health" / "bug-book.md"

# Reuse the readiness tally rather than re-parsing the maps (helper-policy: one
# source of truth for the readiness count). scripts/ is not a package, so add it
# to the path and import the sibling module.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import readiness_scoreboard  # noqa: E402  (path-dependent import)

# A bug-book entry's status line, e.g. `- **Status:** OPEN — ...`.
_OPEN_BUG_RE = re.compile(r"^\s*-\s*\*\*Status:\*\*\s*OPEN\b", re.MULTILINE)


def count_open_bugs(path: Path = BUG_BOOK) -> int:
    """Count bug-book entries whose status line is OPEN."""
    if not path.exists():
        return 0
    return len(_OPEN_BUG_RE.findall(path.read_text(encoding="utf-8")))


def readiness_not_done() -> tuple[int, int]:
    """Return ``(not_done_total, done_pct)`` across the readiness maps."""
    tallies = readiness_scoreboard.collect()
    not_done = sum(t.not_done for t in tallies.values())
    done = sum(t.done for t in tallies.values())
    total = sum(t.total for t in tallies.values())
    pct = round(100 * done / total) if total else 0
    return not_done, pct


def evaluate() -> dict[str, object]:
    """Compute the phase signal and the evidence behind it."""
    open_bugs = count_open_bugs()
    not_done, done_pct = readiness_not_done()

    reasons: list[str] = []
    if open_bugs:
        reasons.append(f"{open_bugs} OPEN bug(s) in the bug book")
    if not_done:
        reasons.append(f"{not_done} 'Not Done' row(s) in the readiness maps")

    phase = "invent" if not reasons else "fix"
    return {
        "phase": phase,
        "open_bugs": open_bugs,
        "readiness_not_done": not_done,
        "readiness_done_pct": done_pct,
        "blocking_reasons": reasons,
    }


def _render(result: dict[str, object]) -> str:
    phase = result["phase"]
    banner = (
        "INVENT-PHASE — correctness is done; this is a clean season to originate "
        "features (ADVISORY since Q-0172: feature origination is no longer gated; "
        "flag self-initiated work on the run-report `⚑ Self-initiated:` line)."
        if phase == "invent"
        else "FIX-PHASE (ADVISORY since Q-0172) — bugs/Not-Done rows remain, so "
        "correctness work still comes FIRST in priority. This is a readout, NOT a "
        "block: an agent may still originate a feature here (idea→plan→ship is open, "
        "Q-0172) — just flag it on the run-report `⚑ Self-initiated:` line and don't "
        "let it crowd out the bugs below. (Read-only Q-0105 dev tooling/checks were "
        "never gated.)"
    )
    lines = [
        "# Autonomous-loop phase gate",
        "",
        f"Phase: **{str(phase).upper()}**",
        "",
        banner,
        "",
        f"- OPEN bugs (bug-book):        {result['open_bugs']}",
        f"- 'Not Done' readiness rows:   {result['readiness_not_done']}",
        f"- Readiness Done %:            {result['readiness_done_pct']}% (informational)",
    ]
    reasons = result["blocking_reasons"]
    if isinstance(reasons, list) and reasons:
        lines.append("")
        lines.append("Blocking invent-phase:")
        lines.extend(f"  - {r}" for r in reasons)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Autonomous-loop phase gate.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--phase",
        action="store_true",
        help="print just `fix` or `invent` and exit 0.",
    )
    group.add_argument(
        "--json",
        action="store_true",
        help="print the signal + evidence as JSON.",
    )
    group.add_argument(
        "--require-invent",
        action="store_true",
        help="exit 0 only in invent-phase; exit 1 (with reasons) in fix-phase.",
    )
    args = parser.parse_args(argv)

    result = evaluate()

    if args.phase:
        print(result["phase"])
        return 0
    if args.json:
        print(json.dumps(result, indent=2))
        return 0
    if args.require_invent:
        print(_render(result), file=sys.stderr)
        return 0 if result["phase"] == "invent" else 1

    print(_render(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
