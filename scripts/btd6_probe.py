#!/usr/bin/env python3
"""BTD6 grounding probe — print the facts a message would ground.

Replays a user's message through ``btd6_context_service.build()`` (the same
call the AI mention path and the deterministic Ask path use) and prints the
grounding facts, source summary, and resolver confidence. **Read-only** — it
touches no Discord and writes nothing; with Postgres down the DB passes
degrade exactly as they do in production (fixture grounding still runs).

Why this exists: diagnosing a wrong BTD6 answer starts by replaying the
user's EXACT text — not a cleaned-up version — and reading what the model was
actually given. The 2026-06-10 Navarch session ("does the navarch of seas
paragon make coins" → confidently wrong "no") wrote this same probe inline
four times; the 0-facts result was the single highest-information measurement
of the whole diagnosis (missing routing, not missing data — PR #662).

Provenance: built 2026-06-10 (Navarch routing session follow-up). Unverified
beyond its own tests: confirm its output against a live wrong-answer report
once or twice before trusting it as the first triage step.

Usage:
    python3.10 scripts/btd6_probe.py "does the navarch of seas paragon make coins"
    python3.10 scripts/btd6_probe.py --grep income "navarch of the seas"
    python3.10 scripts/btd6_probe.py --route "what is the hp of elite lych per tier"

``--route`` prepends the task-router + round-cash-workflow legs: a routing
miss is invisible in the facts view (the facts are built by *this* script
calling build() directly — the live pipeline only does that when the router
classifies the message ``btd6.answer``).
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DISBOT = _REPO_ROOT / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))


async def probe(text: str):
    """Build and return the grounding context for ``text`` (test seam)."""
    from services import btd6_context_service

    return await btd6_context_service.build(text)


def route_report(text: str) -> list[str]:
    """The routing/workflow legs the grounding facts can't show (test seam).

    Added 2026-06-11 (BUG-0002/0003 session): the probe printed 5 healthy
    facts for "elite lych hp per tier" while the live pipeline never reached
    grounding at all — the router had sent the message to the GENERAL path.
    A routing bug is invisible to the facts view by construction, so triage
    needs both legs in one place.
    """
    from services import (
        ai_orchestration_presets,
        ai_round_cash_workflow,
        ai_task_router,
    )

    lines: list[str] = []
    routed = ai_task_router.classify(text)
    lines.append(f"task: {routed.task.value}  (route={routed.route})")
    if routed.task.value != "btd6.answer":
        lines.append(
            "⚠ NOT routed to btd6.answer — BTD6 grounding/guards never run; "
            "the model answers this from memory (the BUG-0002/0003 class).",
        )
    plan = ai_round_cash_workflow.plan_question(text)
    if plan is None:
        lines.append("round-cash workflow: no match (conservative planner stays out)")
    else:
        lines.append(f"round-cash workflow: MATCH → {plan}")
        engaged = sorted(
            p.key
            for p in ai_orchestration_presets.all_presets()
            if p.workflow == ai_round_cash_workflow.WORKFLOW_KEY
        )
        lines.append(f"  engages under profiles: {', '.join(engaged)}")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Print the BTD6 grounding facts a message would produce.",
    )
    parser.add_argument("message", help="the user's message, verbatim")
    parser.add_argument(
        "--grep",
        metavar="SUBSTR",
        help="only print facts containing this substring (case-insensitive)",
    )
    parser.add_argument(
        "--route",
        action="store_true",
        help="also print the task-router / round-cash-workflow legs "
        "(a routing miss is invisible in the facts view)",
    )
    args = parser.parse_args(argv)

    if args.route:
        for line in route_report(args.message):
            print(line)
        print()

    ctx = asyncio.run(probe(args.message))
    facts = list(ctx.facts)
    shown = [f for f in facts if args.grep.lower() in f.lower()] if args.grep else facts
    for fact in shown:
        print(f"- {fact}")
    suffix = f" ({len(shown)} shown)" if args.grep else ""
    print()
    print(f"facts: {len(facts)}{suffix}")
    print(f"source_summary: {ctx.source_summary}")
    print(f"confidence: {ctx.confidence}")
    # 0 facts on a question that names an entity is the classic routing-miss
    # signature (see the Navarch case) — make it unmissable.
    if not facts:
        print("⚠ ZERO grounding facts — the model would answer from memory.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
