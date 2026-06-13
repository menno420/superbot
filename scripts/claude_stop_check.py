#!/usr/bin/env python3
"""Stop hook: hard-fail gate before Claude returns control to the user.

Called by Claude Code on the Stop event (end of each assistant turn).
Runs check-only verification on Python files changed vs origin/main:

  1. Architecture (strict)  — layer boundaries, SQL location, etc.
  2. Black --check          — formatting
  3. isort --check-only     — import ordering
  4. Ruff check (no --fix)  — lint
  5. Mypy (changed files)   — types

All are hard failures — exit 1 surfaces in chat and Claude must fix
before committing. The post-edit hook auto-fixes black/isort/ruff on
write, so a Stop-time failure here means either (a) a fix could not be
auto-applied or (b) something was edited outside the hook path.

Pytest is NOT run here — it is too slow per turn. The hook prints the
exact command to run the full pre-PR suite manually before pushing.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"

# CI runs Python 3.10 — match it locally to avoid version-drift
# false negatives (see PR #338: mypy passed under 3.11 because a
# transitively missing package was treated as Any).
PY = "python3.10" if shutil.which("python3.10") else sys.executable


# CI's exclude list for formatters/lint — must match
# .github/workflows/code-quality.yml exactly.
_EXCLUDED_PREFIXES = (".github/", "tests/", "venv/", "env/", "build/", "dist/")


def _changed_py_files() -> list[str]:
    """Return Python files changed vs origin/main (plus dirty WC).

    Excludes the same prefixes CI excludes from black/isort/ruff. The
    formatter/lint scope is *not* limited to disbot/ — scripts/ and any
    other top-level .py files are also checked. Mypy is narrowed further
    in main() to match CI's `mypy disbot/` invocation.
    """
    seen: set[str] = set()
    for cmd in (
        ["git", "diff", "--name-only", "origin/main...HEAD"],
        ["git", "diff", "--name-only", "HEAD"],
    ):
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
        if result.returncode != 0:
            continue
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line.endswith(".py"):
                continue
            if any(line.startswith(p) for p in _EXCLUDED_PREFIXES):
                continue
            seen.add(line)
    return sorted(seen)


def _run(label: str, cmd: list[str]) -> tuple[bool, str]:
    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    ok = result.returncode == 0
    output = (result.stdout + result.stderr).strip()
    return ok, output


def _commits_ahead_of_main() -> int:
    """How many commits HEAD is ahead of origin/main (0 if unknown)."""
    try:
        result = subprocess.run(
            ["git", "rev-list", "--count", "origin/main..HEAD"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
    except OSError:
        return 0
    if result.returncode != 0:
        return 0
    try:
        return int(result.stdout.strip() or "0")
    except ValueError:
        return 0


def _end_of_session_advisory() -> None:
    """Non-blocking end-of-session reminders, printed when HEAD is ahead of
    origin/main (i.e. this session produced real work).

    Covers the session-ender obligations easy to forget because nothing else
    checks them — but the Stop hook runs locally with **no GitHub access**, so the
    PR-lifecycle line is a reminder to *confirm*, not true enforcement:

      * Q-0052  — open the session PR early (right after the first push).
      * Q-0103/Q-0084 — the PR must reach a terminal state (merge on green CI or
        close); never leave it abandoned open (the parallel-agent conflict window).
      * Q-0015  — grooming: move one ``docs/ideas/`` idea down its lifecycle.
      * Q-0089/Q-0102 — the ``.sessions/`` log carries a new idea + a previous-
        session review (delegated to ``check_session_log.py`` when present).

    Advisory only — never changes the exit code. Fully defensive: any failure is
    swallowed (provenance: owner-directed in-session, router Q-0122 / Q-0106).
    """
    try:
        if _commits_ahead_of_main() < 1:
            return
        print(
            "\n── end-of-session reminders (advisory, non-blocking) ───────",
            file=sys.stderr,
        )
        checker = SCRIPTS / "check_session_log.py"
        if checker.exists():
            result = subprocess.run(
                [PY, str(checker)],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )
            out = result.stdout.strip()
            if out and "complete ✓" not in out:
                for line in out.splitlines():
                    print(f"  {line}", file=sys.stderr)
            else:
                print("  · session log: complete ✓", file=sys.stderr)
        print(
            "  · PR lifecycle (Q-0052/Q-0103/Q-0084): the session PR should be OPEN "
            "and reach a terminal state — merge on green CI or close it. Don't leave "
            "it abandoned open. (Hook has no GitHub access — confirm this yourself.)",
            file=sys.stderr,
        )
        print(
            "  · grooming (Q-0015): once the main task + PR are done, move one "
            "docs/ideas/ idea one step down its lifecycle.",
            file=sys.stderr,
        )
    except Exception:  # noqa: BLE001 — advisory must never break the Stop hook
        return


def main() -> int:
    _end_of_session_advisory()
    changed = _changed_py_files()
    if not changed:
        return 0
    # mypy in CI runs only against disbot/ — narrow the type-check set
    # so we don't add false positives from scripts/ etc.
    disbot_changed = [p for p in changed if p.startswith("disbot/")]
    arch_changed = disbot_changed  # architecture rules only apply under disbot/

    print(
        "\n── stop-check ──────────────────────────────────────────────",
        file=sys.stderr,
    )

    checks: list[tuple[str, list[str], bool]] = [
        # (label, command, skip-if-empty-target)
        (
            "architecture",
            [
                PY,
                str(SCRIPTS / "check_architecture.py"),
                "--changed-only",
                "--mode",
                "strict",
            ],
            not arch_changed,
        ),
        (
            "black --check",
            [PY, "-m", "black", "--check", "--quiet", *changed],
            False,
        ),
        (
            "isort --check",
            [PY, "-m", "isort", "--check-only", "--quiet", *changed],
            False,
        ),
        (
            "ruff check",
            [PY, "-m", "ruff", "check", *changed],
            False,
        ),
        (
            "mypy",
            [PY, "-m", "mypy", *disbot_changed],
            not disbot_changed,
        ),
    ]

    failures: list[tuple[str, str]] = []
    for label, cmd, skip in checks:
        if skip:
            print(f"  · {label} (skipped — no matching files)", file=sys.stderr)
            continue
        ok, output = _run(label, cmd)
        if ok:
            print(f"  ✓ {label}", file=sys.stderr)
        else:
            print(f"  ✗ {label}", file=sys.stderr)
            failures.append((label, output[:1500]))

    if failures:
        print(
            "\n[stop-check] HARD FAILURE — fix before pushing:\n",
            file=sys.stderr,
        )
        for label, output in failures:
            print(f"── {label} ─────────────────────────────────────", file=sys.stderr)
            print(output, file=sys.stderr)
            print("", file=sys.stderr)
        print(
            "Run the full pre-PR suite to mirror CI before pushing:\n"
            f"  {PY} scripts/check_quality.py --check-only\n"
            f"  {PY} -m pytest tests/ -q\n",
            file=sys.stderr,
        )
        return 1

    print(
        "\n[stop-check] ✓ all changed-file checks passed. Run the full "
        f"suite before pushing:\n  {PY} scripts/check_quality.py --check-only "
        f"&& {PY} -m pytest tests/ -q\n",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
