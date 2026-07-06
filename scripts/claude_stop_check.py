#!/usr/bin/env python3
"""Stop hook: hard-fail gate before Claude returns control to the user.

Called by Claude Code on the Stop event (end of each assistant turn).
Runs check-only verification on Python files changed vs origin/main:

  0. Merge-conflict guard   — hard-fails if the branch conflicts with
                              origin/main (a conflict silently parks the PR:
                              auto-merge won't run and no webhook warns).
  1. Architecture (strict)  — layer boundaries, SQL location, etc.
  2. Ruff format --check    — formatting (replaced black, A3)
  3. Ruff check (no --fix)  — lint + import ordering (the `I` rule; replaced isort)
  4. Mypy (changed files)   — types

All are hard failures — exit 1 surfaces in chat and Claude must fix
before committing. The post-edit hook auto-fixes ruff format + ruff check on
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

    Excludes the same prefixes CI excludes from ruff. The
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


def _merge_conflicts_with_main() -> list[str] | None:
    """Paths that would conflict if ``origin/main`` were merged into HEAD.

    Returns ``[]`` (clean), a non-empty list of conflicted paths, or ``None``
    (undeterminable — git < 2.38 without ``merge-tree --write-tree``, no
    ``origin/main``, or offline). Writes only to the object store — it never
    touches the working tree or the index.

    Owner-directed, in-session 2026-06-15 (Q-0106 carve-out): a conflict with
    ``origin/main`` silently parks a PR — native auto-merge will not run, and PR
    webhooks do not deliver merge-conflict transitions — so "auto-merge on green"
    can be declared on a branch that can never merge. This is the missing guard.
    """
    # Best-effort refresh so we check against the *latest* main (a stale local
    # ref is exactly how the conflict was missed). Offline / slow → fall back to
    # whatever origin/main is already fetched.
    try:
        subprocess.run(
            ["git", "fetch", "--quiet", "origin", "main"],
            cwd=REPO_ROOT,
            capture_output=True,
            timeout=20,
        )
    except Exception:  # noqa: BLE001 — best-effort; never break the hook
        pass
    try:
        proc = subprocess.run(
            ["git", "merge-tree", "--write-tree", "--name-only", "origin/main", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except Exception:  # noqa: BLE001
        return None
    if proc.returncode == 0:
        return []  # clean merge
    if proc.returncode == 1:
        # Conflict. With --write-tree the first stdout line is the tree oid;
        # --name-only makes the remaining lines the conflicted paths.
        lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
        return lines[1:] or ["(merge conflict — run: git merge origin/main)"]
    return None  # unknown option (old git) / other error → never false-alarm


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

    # Merge-conflict guard (owner-directed in-session 2026-06-15, Q-0106 carve-out).
    # A real conflict with origin/main means the PR cannot merge — fail the Stop so
    # it is resolved, not silently parked behind a green "auto-merge on green" (the
    # exact gap that let a conflicting PR be declared done). Only a *genuine*
    # conflict fails; mere divergence merges clean. Kill-switch (Q-0105): if this
    # proves noisy in high-parallelism work, downgrade `return 1` to an advisory
    # print — the detection is reliable, only the severity is a judgement call.
    if _commits_ahead_of_main() >= 1:
        conflicts = _merge_conflicts_with_main()
        if conflicts:
            print(
                "\n── stop-check ──────────────────────────────────────────────",
                file=sys.stderr,
            )
            print("  ✗ merge conflict with origin/main", file=sys.stderr)
            print(
                "\n[stop-check] HARD FAILURE — this branch conflicts with "
                "origin/main, so the PR cannot merge until you resolve it. "
                "Auto-merge will NOT run and no webhook will warn you.\n\n"
                "  Conflicted paths:",
                file=sys.stderr,
            )
            for path in conflicts[:25]:
                print(f"    • {path}", file=sys.stderr)
            print(
                "\n  Resolve before treating the PR as done:\n"
                "    git fetch origin main && git merge origin/main\n"
                "    # fix conflicts, then "
                f"{PY} scripts/check_quality.py --full, commit, push\n",
                file=sys.stderr,
            )
            return 1

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
            "ruff format --check",
            [PY, "-m", "ruff", "format", "--check", "--quiet", *changed],
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
