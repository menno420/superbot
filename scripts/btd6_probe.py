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
    args = parser.parse_args(argv)

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
