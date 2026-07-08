#!/usr/bin/env python3.10
"""Plan-homing guard — no live `plan` doc goes unrouted (stdlib, read-only).

WHY (idea `plan-homing-guard-2026-06-19`, Q-0089): the planning-map cleanup found the project's
**dominant active thread** (the dashboard / control-API / website initiative, ~8 `plan`-badged
docs) was reachable only by directory listing — not linked from `roadmap.md`, any folio, or
`current-state.md`. ``check_docs.py --strict`` did **not** catch it: its reachability check needs
only *one* inbound link from *anywhere* under ``docs/``, so a plan cross-linked solely by a sibling
planning doc counts as "reachable" while being invisible to every agent route. A live plan can rot
off the map while CI stays green — the "green check that contradicts visible evidence" trap
(CLAUDE.md § CI-parity, Q-0120).

This guard is the **routing** complement to ``check_docs``'s **reachability** check:

* reachability asks "is it linked from *anywhere*?"
* homing asks "is it on an agent's *map*?"

It asserts: every **live `plan`-badged** doc under ``docs/planning/`` has **≥1 inbound link from a
*routing* doc** — ``roadmap.md``, a ``docs/subsystems/*.md`` folio, ``docs/current-state.md``, or the
``docs/planning/README.md`` plan index. A plan that ships is rebadged ``historical`` in place (per the
plan-index ship convention) and drops out of scope automatically; only `plan` badges are homed.

Run::

    python3.10 scripts/check_plan_homing.py            # report-only (always exit 0)
    python3.10 scripts/check_plan_homing.py --strict   # exit 1 when a live plan is unhomed
    python3.10 scripts/check_plan_homing.py --json      # machine-readable summary

**Report-only by default; ``--strict`` is a per-PR merge gate since 2026-07-08.** The default
exit is 0 (a routing readout for a planning session), while ``--strict`` runs as an always-on
pre-setup step in the required ``code-quality`` job — **including the docs-only fast path**. That
promotion (PR #1855, Q-0194 friction→guard) closes the #1843 "green-by-skip" gap: the fast path
skips pytest, so the live-tree test ``test_live_repo_plans_are_all_homed`` never ran on exactly
the PR class (docs-only) that can introduce an unhomed plan; #1843 merged green in 12s and
reddened every subsequent full-CI branch until the plan was homed by hand. It reasons over docs
only — never touches runtime code, never runs a bot.

Reliability (Q-0105): added 2026-06-20; CI-gating since 2026-07-08 (PR #1855). Verified against
ground truth twice (the 2026-06-19 planning-map orphan set; the #1843 unhomed plan, which it
flags and the homed fix clears). The "routing doc" allow-list and the basename link-match are
still heuristics; **demote the CI step back to advisory (or delete this script) if it proves
noisy** (e.g. flags deliberately-parked Someday drafts) over multiple sessions rather than
working around it.

→ relates ``scripts/check_docs.py`` (reachability) · ``scripts/check_sector_map.py`` (folio homing) ·
``scripts/check_plan_backlog.py`` (depth) · ``docs/planning/README.md`` · ``docs/roadmap.md``.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
PLANNING_DIR = DOCS_DIR / "planning"
SUBSYSTEMS_DIR = DOCS_DIR / "subsystems"

# The Status badge line: `> **Status:** `plan` — …`. Hyphen allowed (`living-ledger`).
_STATUS_RE = re.compile(r">\s*\*\*Status:\*\*\s*`([a-z-]+)`")

# Only this badge is a live, buildable plan that must be homed. Everything else
# (`historical`/`reference`/`audit`/`living-ledger`/`ideas`) is out of scope by design — a shipped
# plan is rebadged `historical` in place, so it leaves scope the moment its work lands.
LIVE_PLAN_BADGE = "plan"

# The plan index itself is a `living-ledger`, not a `plan`, so it is never in scope; named here only
# for clarity / to exclude defensively if its badge ever changes.
_PLAN_INDEX = PLANNING_DIR / "README.md"


def _badge(text: str) -> str | None:
    """The first Status-badge token in a doc, or None if it carries no badge."""
    match = _STATUS_RE.search(text)
    return match.group(1) if match else None


def routing_docs() -> list[Path]:
    """The docs that count as an agent's *map*: roadmap, current-state, the plan index, folios.

    A plan linked from any of these is "homed" — reachable on a route an agent actually reads,
    not merely cross-linked by a sibling plan.
    """
    docs: list[Path] = []
    for name in ("roadmap.md", "current-state.md"):
        path = DOCS_DIR / name
        if path.exists():
            docs.append(path)
    # The per-sector live-state files (Q-0195) are part of the current-state routing
    # surface — a session dispatched to a sector reads its file — so a plan linked from
    # one is genuinely homed.
    current_state_dir = DOCS_DIR / "current-state"
    if current_state_dir.is_dir():
        docs.extend(sorted(current_state_dir.glob("*.md")))
    if _PLAN_INDEX.exists():
        docs.append(_PLAN_INDEX)
    if SUBSYSTEMS_DIR.is_dir():
        docs.extend(sorted(SUBSYSTEMS_DIR.glob("*.md")))
    return docs


def live_plans(planning_dir: Path | None = None) -> list[Path]:
    """Every `plan`-badged doc directly under ``docs/planning/`` (the live, buildable set)."""
    if planning_dir is None:
        planning_dir = PLANNING_DIR  # read at call time so tests can repoint it
    plans: list[Path] = []
    for path in sorted(planning_dir.glob("*.md")):
        if path == _PLAN_INDEX:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if _badge(text) == LIVE_PLAN_BADGE:
            plans.append(path)
    return plans


def _linked_basenames(routing: list[Path]) -> set[str]:
    """The set of ``foo.md`` basenames referenced by any routing doc's markdown links.

    Match on basename inside a markdown link target — ``](…/foo.md)`` or ``](foo.md)`` — so the
    relative-path prefix (``planning/`` from roadmap, ``../planning/`` from a folio, bare from the
    plan index) is irrelevant. A bare basename mention outside a link does not count; the link
    syntax is required so prose name-drops are not mistaken for a route.
    """
    linked: set[str] = set()
    link_re = re.compile(r"\]\(([^)]+\.md)(?:#[^)]*)?\)")
    for path in routing:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for target in link_re.findall(text):
            linked.add(Path(target).name)
    return linked


@dataclass(frozen=True)
class HomingReport:
    plan_count: int
    homed: tuple[str, ...]
    # relative paths of live plans with no routing-doc inbound link
    unhomed: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.unhomed


def build_report(planning_dir: Path | None = None) -> HomingReport:
    """Compute which live plans are homed to a routing doc and which are orphaned."""
    plans = live_plans(planning_dir)
    linked = _linked_basenames(routing_docs())
    homed: list[str] = []
    unhomed: list[str] = []
    for plan in plans:
        rel = str(plan.relative_to(REPO_ROOT))
        (homed if plan.name in linked else unhomed).append(rel)
    return HomingReport(
        plan_count=len(plans),
        homed=tuple(sorted(homed)),
        unhomed=tuple(sorted(unhomed)),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Plan-homing guard: every live `plan` doc is on an agent's map.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 when any live plan is unhomed (the reconciliation cadence gate)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print a machine-readable summary instead of prose",
    )
    args = parser.parse_args(argv)

    report = build_report()

    if args.json:
        print(
            json.dumps(
                {
                    "plan_count": report.plan_count,
                    "homed": list(report.homed),
                    "unhomed": list(report.unhomed),
                    "ok": report.ok,
                },
                indent=2,
            ),
        )
        return 1 if (args.strict and not report.ok) else 0

    if report.ok:
        print(
            f"check_plan_homing: OK — all {report.plan_count} live `plan` docs under "
            "docs/planning/ are linked from a routing doc (roadmap / current-state / plan index "
            "/ a folio).",
        )
        return 0

    print(
        f"check_plan_homing: ⚠️ {len(report.unhomed)} of {report.plan_count} live `plan` docs "
        "are UNHOMED — reachable only by directory listing, not on any agent route:",
    )
    for rel in report.unhomed:
        print(f"  - {rel}")
    print(
        "\nHome each: add a row to docs/planning/README.md (Active plans), and link it from "
        "docs/roadmap.md and/or its subsystem folio. (Report-only unless --strict.)",
    )
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
