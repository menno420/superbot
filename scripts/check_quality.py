#!/usr/bin/env python3
"""Quality check runner for SuperBot.

Runs ruff format + ruff check (lint + import sort) with auto-fix by default.
Optionally runs mypy and pytest.

Usage:
    python scripts/check_quality.py               # auto-fix formatting, report remaining
    python scripts/check_quality.py --check-only  # no auto-fix, exit 1 if anything fails
    python scripts/check_quality.py --full        # also run mypy + pytest (no auto-fix)
    python scripts/check_quality.py --fix-only    # only run formatters (no lint/type/test)
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DISBOT_ROOT = REPO_ROOT / "disbot"

# Always invoke tools as `python3.10 -m <tool>`, never as the bare
# executable. CI runs Python 3.10, and a bare `ruff` / `pytest` / etc. on
# PATH can resolve to a DIFFERENT interpreter (e.g. a uv-installed
# standalone pytest on its own isolated env that lacks the project's
# dependencies — which produces thousands of bogus import-error
# "failures"). Routing through python3.10 -m guarantees the same
# interpreter + installed packages CI and the Claude Code hooks use.
# See .claude/CLAUDE.md "Match CI exactly" and the PR #338 post-mortem.
_PY = "python3.10" if shutil.which("python3.10") else sys.executable


def _tool(name: str, *args: str) -> list[str]:
    """Build a ``python3.10 -m <name> ...`` command (never the bare exe)."""
    return [_PY, "-m", name, *args]


# CI parity (see .github/workflows/code-quality.yml). This MUST match the
# workflow's invocations exactly, or this script reports failures CI will
# never see (or misses ones it will). The canonical traps this prevents:
#   * CI excludes tests/ from ruff — checking tests/ here too surfaced ~196
#     pre-existing test-file reformats that CI ignores, which turned the
#     prescribed pre-push check permanently red for no real reason.
#   * CI runs mypy only against disbot/.
# ruff replaced black + isort (A3, 2026-07-06): `ruff format` owns formatting and
# `ruff check` (with the `I` rule) owns import sorting + lint. Both take the same
# comma-list --exclude. Kept aligned with the workflow;
# tests/unit/scripts/test_check_quality_ci_parity.py guards against re-drift.
_RUFF_EXCLUDE = ".github,tests,venv,env,build,dist"


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
    """Run ``ruff format`` + ``ruff check`` (lint + import sort) over CI's exact scope.

    ruff replaced black + isort (A3): ``ruff format`` owns formatting (Black-compatible)
    and ``ruff check`` (with the ``I`` rule) owns import sorting + lint. Scope and exclude
    flags mirror ``.github/workflows/code-quality.yml`` so a pass here means a pass in CI
    (and vice versa). In ``--check-only`` mode the invocations are byte-for-byte the
    workflow's; in fix mode the only difference is the auto-fix flag.
    """
    results = []

    results.append(
        (
            "ruff format",
            _run(
                "ruff format" + (" --check" if check_only else ""),
                _tool(
                    "ruff",
                    "format",
                    *(["--check"] if check_only else []),
                    ".",
                    "--exclude",
                    _RUFF_EXCLUDE,
                ),
            ),
        ),
    )
    results.append(
        (
            "ruff",
            _run(
                "ruff check" + (" --no-fix" if check_only else " --fix"),
                _tool(
                    "ruff",
                    "check",
                    *(["--no-fix"] if check_only else ["--fix"]),
                    ".",
                    "--exclude",
                    _RUFF_EXCLUDE,
                ),
            ),
        ),
    )
    return results


def run_mypy() -> int:
    # CI runs `mypy disbot/` — match the target exactly.
    return _run("mypy", _tool("mypy", "disbot/"))


def run_pytest() -> int:
    # `-n auto` (pytest-xdist) parallelizes the ~9.4k-test suite across cores for a
    # ~3x speedup, mirroring code-quality.yml exactly. Parallel-safe since the Q-0126
    # test-isolation follow-up: autouse singleton resets in tests/conftest.py + the
    # server_logging bus-subscription teardown. Keep this flag in lockstep with CI's
    # pytest step (flip both together if the suite ever regresses to serial).
    return _run("pytest", _tool("pytest", "tests/", "-q", "-n", "auto", "--tb=short"))


def run_check_docs() -> int:
    # CI runs `python3 scripts/check_docs.py --strict` on every PR (incl. docs-only).
    return _run(
        "check_docs",
        [_PY, str(REPO_ROOT / "scripts" / "check_docs.py"), "--strict"],
    )


def run_check_consistency() -> int:
    # CI runs `python scripts/check_consistency.py --mode strict` (in the deps block).
    # Only GRADUATED rules fail strict (error severity); warn-only rules just print.
    return _run(
        "check_consistency",
        [_PY, str(REPO_ROOT / "scripts" / "check_consistency.py"), "--mode", "strict"],
    )


def run_check_artifacts_fresh() -> int:
    """Verify the committed generated artifacts (dashboard.json / site.json / …)
    match a fresh build.

    Fast (a fresh export is ~1-2s) so it runs on every invocation — a new
    command / cog / settings key that drifts the dashboard or bot-site data is
    then caught in the pre-push pass instead of only in the 3-min full pytest
    suite (where ``test_committed_artifacts_are_currently_fresh`` is the CI gate).
    Re-run ``scripts/export_dashboard_data.py`` to refresh on a hit.
    """
    return _run(
        "check_artifacts_fresh",
        [
            _PY,
            str(REPO_ROOT / "scripts" / "check_generated_artifacts_fresh.py"),
            "--strict",
        ],
    )


def run_check_tool_pins() -> int:
    """Verify the lint/format/type tool versions match between CI and the dev install.

    A drift here means this script is no longer a true CI mirror (a newer local ruff
    flags rules the pinned CI ruff doesn't, and vice versa — BUG-0022). Cheap, so it
    runs on every invocation, not just --full.
    """
    return _run(
        "check_tool_pins",
        [_PY, str(REPO_ROOT / "scripts" / "check_tool_pins.py")],
    )


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
        help="Only run formatters (ruff format + ruff check --fix), skip lint/type/test",
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
        if run_check_tool_pins() != 0:
            failed.append("check_tool_pins")
        if run_check_docs() != 0:
            failed.append("check_docs")
        if run_check_consistency() != 0:
            failed.append("check_consistency")
        if run_check_artifacts_fresh() != 0:
            failed.append("check_artifacts_fresh")
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
