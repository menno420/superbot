"""Parity harness CLI.

Usage (from the repo root, python3.10, DATABASE_URL pointing at Postgres):

    python3.10 -m parity.run capture            # curated + sweep → goldens/
    python3.10 -m parity.run capture --curated  # curated only (fast)
    python3.10 -m parity.run check              # replay against goldens (red on drift)
    python3.10 -m parity.run coverage           # (re)compute COVERAGE.md

``check`` is the current-bot regression net today and the red-until-parity
oracle for the rebuild tomorrow.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

GOLDENS_ROOT = _REPO_ROOT / "parity" / "goldens"
SWEEP_SKIPS_PATH = GOLDENS_ROOT / "_sweep_skips.json"


async def _all_cases(harness, include_sweep: bool):  # type: ignore[no-untyped-def]
    from parity.cases import CURATED_CASES
    from parity.cases.sweep import build_sweep_cases

    cases = list(CURATED_CASES)
    skipped: dict[str, str] = {}
    if include_sweep:
        sweep_cases, skipped = build_sweep_cases(harness.bot)
        curated_ids = {c.id for c in cases}
        cases.extend(c for c in sweep_cases if c.id not in curated_ids)
    return cases, skipped


async def _capture(args: argparse.Namespace) -> int:
    from parity.harness.boot import Harness
    from parity.harness.runner import capture_case, golden_path

    harness = await Harness.start()
    if harness.extension_failures:
        print("EXTENSION FAILURES:", harness.extension_failures)
        return 2
    cases, skipped = await _all_cases(harness, include_sweep=not args.curated)
    if args.only:
        cases = [c for c in cases if args.only in c.id]
    print(f"capturing {len(cases)} case(s)…")
    failures: dict[str, str] = {}
    for i, case in enumerate(cases, 1):
        try:
            document = await capture_case(harness, case)
        except Exception as exc:  # noqa: BLE001 - a failed case must not kill the run
            failures[case.id] = f"{type(exc).__name__}: {exc}"
            continue
        path = golden_path(GOLDENS_ROOT, case)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(document, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
        )
        if i % 25 == 0:
            print(f"  {i}/{len(cases)}")
    if not args.curated:
        SWEEP_SKIPS_PATH.parent.mkdir(parents=True, exist_ok=True)
        SWEEP_SKIPS_PATH.write_text(
            json.dumps(skipped, indent=1, sort_keys=True) + "\n",
        )
    await harness.close()
    print(f"captured {len(cases) - len(failures)}/{len(cases)} cases")
    if failures:
        print("CAPTURE FAILURES (harness gaps, not bot bugs):")
        for cid, err in sorted(failures.items()):
            print(f"  {cid}: {err}")
    return 0 if not failures else 1


async def _check(args: argparse.Namespace) -> int:
    from parity.harness.boot import Harness
    from parity.harness.runner import replay_case

    harness = await Harness.start()
    cases, _ = await _all_cases(harness, include_sweep=not args.curated)
    if args.only:
        cases = [c for c in cases if args.only in c.id]
    from parity.cases.sweep import FLAKY_ADVISORY

    ok = 0
    advisory: dict[str, int] = {}
    failed: dict[str, list[str]] = {}
    gating_total = 0
    for case in cases:
        match, problems = await replay_case(harness, case, GOLDENS_ROOT)
        if case.id in FLAKY_ADVISORY:
            if not match:
                advisory[case.id] = len(problems)
            continue
        gating_total += 1
        if match:
            ok += 1
        else:
            failed[case.id] = problems
    await harness.close()
    print(
        f"parity: {ok}/{gating_total} gating green"
        f" (+{len(advisory)} advisory diffs"
        f" of {len(FLAKY_ADVISORY)} advisory cases)",
    )
    for cid, n in sorted(advisory.items()):
        print(f"ADVISORY {cid}: {n} diff(s) — {FLAKY_ADVISORY[cid]}")
    for cid, problems in sorted(failed.items()):
        print(f"RED {cid}")
        for problem in problems[:8]:
            print(f"    {problem}")
        if len(problems) > 8:
            print(f"    … {len(problems) - 8} more")
    return 0 if not failed else 1


async def _coverage(args: argparse.Namespace) -> int:  # noqa: ARG001
    from parity.coverage import build_coverage_report

    report = await build_coverage_report(GOLDENS_ROOT)
    out = _REPO_ROOT / "parity" / "COVERAGE.md"
    out.write_text(report)
    print(f"wrote {out}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="parity")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, needs_flags in (("capture", True), ("check", True), ("coverage", False)):
        p = sub.add_parser(name)
        if needs_flags:
            p.add_argument("--curated", action="store_true", help="curated cases only")
            p.add_argument("--only", default="", help="substring filter on case id")
    args = parser.parse_args()
    handler = {"capture": _capture, "check": _check, "coverage": _coverage}[
        args.command
    ]
    return asyncio.run(handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
