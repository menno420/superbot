#!/usr/bin/env python3
"""Quality check runner for SuperBot.

Runs ruff, black, and isort with auto-fix by default.
Optionally runs mypy and pytest.

Usage:
    python scripts/check_quality.py               # auto-fix formatting, report remaining
    python scripts/check_quality.py --check-only  # no auto-fix, exit 1 if anything fails
    python scripts/check_quality.py --full        # also run mypy + pytest (no auto-fix)
    python scripts/check_quality.py --fix-only    # only run formatters (no lint/type/test)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DISBOT_ROOT = REPO_ROOT / "disbot"


def _run(label: str, cmd: list[str], *, check: bool = False) -> int:
    """Run a command, print its output, and return the exit code."""
    print(f"\n── {label} {'─' * max(0, 60 - len(label))}")
    result = subprocess.run(cmd, cwd=REPO_ROOT)
    if result.returncode != 0:
        print(f"  ✗ {label} failed (exit {result.returncode})")
    else:
        print(f"  ✓ {label} passed")
    return result.returncode


def run_formatters(*, check_only: bool) -> list[tuple[str, int]]:
    results = []
    flag = ["--check"] if check_only else []

    results.append(("black", _run(
        "black" + (" --check" if check_only else " --fix"),
        ["black", *flag, "disbot/", "scripts/", "tests/"],
    )))
    results.append(("isort", _run(
        "isort" + (" --check-only" if check_only else ""),
        ["isort", *(["--check-only"] if check_only else []), "disbot/", "scripts/", "tests/"],
    )))
    results.append(("ruff", _run(
        "ruff" + (" --no-fix" if check_only else " --fix"),
        ["ruff", "check", *(["--no-fix"] if check_only else ["--fix"]), "disbot/", "scripts/"],
    )))
    return results


def run_mypy() -> int:
    return _run("mypy", ["mypy", "disbot/"])


def run_pytest() -> int:
    return _run("pytest", ["pytest", "tests/", "-q", "--tb=short"])


def main() -> int:
    parser = argparse.ArgumentParser(description="SuperBot quality checker")
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="No auto-fix; exit 1 if any formatter or linter fails",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Also run mypy and pytest (implies --check-only for formatters)",
    )
    parser.add_argument(
        "--fix-only",
        action="store_true",
        help="Only run formatters (black + isort + ruff --fix), skip lint/type/test",
    )
    args = parser.parse_args()

    check_only = args.check_only or args.full
    failed: list[str] = []

    print("SuperBot quality checks")
    print("=" * 64)

    formatter_results = run_formatters(check_only=check_only)
    for name, code in formatter_results:
        if code != 0:
            failed.append(name)

    if not args.fix_only:
        if args.full:
            if run_mypy() != 0:
                failed.append("mypy")
            if run_pytest() != 0:
                failed.append("pytest")

    print("\n" + "=" * 64)
    if failed:
        print(f"FAILED: {', '.join(failed)}")
        if check_only:
            return 1
    else:
        print("All checks passed ✓")

    return 0


if __name__ == "__main__":
    sys.exit(main())
