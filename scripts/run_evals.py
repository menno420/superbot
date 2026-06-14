#!/usr/bin/env python3
r"""Run the AI capability evals against live providers and print a scorecard.

Opt-in and paid: set ``RUN_EVALS=1`` and provide ``OPENAI_API_KEY`` and/or
``ANTHROPIC_API_KEY``. Example::

    RUN_EVALS=1 OPENAI_API_KEY=sk-... ANTHROPIC_API_KEY=sk-ant-... \\
        python3.10 scripts/run_evals.py --provider both

The harness machinery is covered by ``tests/evals/test_evals_harness.py`` in CI
(with a fake provider, no API); this script is the real run and is never part
of per-PR CI.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
# Mirror tests/conftest.py: a token must exist before disbot imports validate
# config, and both the repo root (for ``tests.evals``) and ``disbot/`` must be
# importable.
os.environ.setdefault("DISCORD_BOT_TOKEN_PRODUCTION", "EVAL_TOKEN_PLACEHOLDER")
for _path in (str(_ROOT), str(_ROOT / "disbot")):
    if _path not in sys.path:
        sys.path.insert(0, _path)


def _build_providers(selected: str) -> dict:
    from core.runtime.ai.providers import AnthropicProvider, OpenAIProvider

    providers: dict = {}
    if selected in ("openai", "both") and os.getenv("OPENAI_API_KEY"):
        providers["openai"] = OpenAIProvider()
    if selected in ("anthropic", "both") and os.getenv("ANTHROPIC_API_KEY"):
        providers["anthropic"] = AnthropicProvider()
    return providers


def _run_smoke() -> int:
    """Run the offline deterministic smoke matrix — no creds, no budget.

    This is the CI-runnable half of the versioned eval/smoke record: it proves
    the gateway's deterministic contract (gates, fallback, tool dispatch, audit,
    safety, redaction, config) with scripted providers. The faults the matrix
    injects are logged by the gateway by design, so quiet that logger for a
    clean scorecard.
    """
    import asyncio
    import logging

    logging.getLogger("bot.runtime.ai.gateway").setLevel(logging.CRITICAL)

    from tests.evals.smoke import render_report, run_matrix

    graded = asyncio.run(run_matrix())
    print(render_report(graded))
    failures = [case.id for case, grade in graded if not grade.passed]
    if failures:
        print(f"\nFAIL — {len(failures)} smoke case(s): {', '.join(failures)}")
        return 1
    print("\nPASS — offline smoke matrix all green")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run AI capability evals.")
    parser.add_argument(
        "--provider",
        choices=["openai", "anthropic", "both"],
        default="both",
    )
    parser.add_argument("--threshold", type=float, default=0.8)
    parser.add_argument(
        "--category",
        default=None,
        help="run only one category (e.g. tool_use)",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="run the offline deterministic smoke matrix (no API keys / budget)",
    )
    args = parser.parse_args(argv)

    if args.smoke:
        return _run_smoke()

    if os.getenv("RUN_EVALS") != "1":
        print(
            "Refusing to run: set RUN_EVALS=1 — this makes real, paid API calls.\n"
            "Also provide OPENAI_API_KEY and/or ANTHROPIC_API_KEY.",
        )
        return 2

    # Tool cases need the gateway to actually offer tools to the model.
    os.environ.setdefault("AI_ENABLED", "1")
    os.environ.setdefault("AI_TOOLS_ENABLED", "1")

    providers = _build_providers(args.provider)
    if not providers:
        print(
            "No usable providers — set OPENAI_API_KEY and/or ANTHROPIC_API_KEY "
            "for the providers you selected.",
        )
        return 2

    from tests.evals.cases import CASES, GOLDEN_SET_VERSION
    from tests.evals.harness import run_suite
    from tests.evals.smoke import SMOKE_MATRIX_VERSION

    cases = [c for c in CASES if args.category in (None, c.category)]
    if not cases:
        print(f"No cases match category {args.category!r}.")
        return 2

    print(
        f"Eval record — golden set v{GOLDEN_SET_VERSION} "
        f"(live) · smoke matrix v{SMOKE_MATRIX_VERSION} (offline, run --smoke)",
    )
    card = asyncio.run(run_suite(cases, providers=providers))
    print(card.render())
    ok = card.pass_rate >= args.threshold
    print(
        f"\n{'PASS' if ok else 'FAIL'} — overall {card.pass_rate:.0%} "
        f"(threshold {args.threshold:.0%})",
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
