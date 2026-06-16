#!/usr/bin/env python3
"""SessionStart hook: print a codebase health summary at the start of every session.

Gives Claude immediate context about the repo state so it never starts
work from an unknown baseline. Kept fast — no test runs, no full lint.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"

SEP = "─" * 60


def _run(cmd: list[str], default: str = "?", timeout: int = 10) -> str:
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            timeout=timeout,
        )
        return r.stdout.strip() if r.returncode == 0 else default
    except Exception:
        return default


def main() -> int:
    print(SEP)
    print("SuperBot — session start")
    print(SEP)

    # Branch + recent commit
    branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    commit = _run(["git", "log", "-1", "--oneline"])
    print(f"Branch : {branch}")
    print(f"Commit : {commit}")

    # Dirty / staged files
    dirty = _run(["git", "status", "--short"])
    if dirty:
        lines = dirty.splitlines()
        preview = ", ".join(ln.split()[-1] for ln in lines[:4])
        suffix = f", +{len(lines) - 4} more" if len(lines) > 4 else ""
        print(f"Changed: {len(lines)} file(s) — {preview}{suffix}")
    else:
        print("Changed: (clean working tree)")

    # Architecture check on changed files (fast path)
    print()
    print("Architecture (changed files):")
    arch = subprocess.run(
        [sys.executable, str(SCRIPTS / "check_architecture.py"), "--changed-only"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=30,
    )
    first_line = (
        arch.stdout.splitlines()[0] if arch.stdout.strip() else "no changes to check"
    )
    print(f"  {first_line}")
    if arch.returncode != 0:
        print("  ⚠  errors found — run check_architecture.py for details")

    # Reconciliation-due advisory (Q-0107 cadence guard — printed early so the
    # session knows before doing feature work whether it should be a planning pass)
    recon = subprocess.run(
        [sys.executable, str(SCRIPTS / "check_reconciliation_due.py")],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=10,
    )
    recon_line = recon.stdout.strip().splitlines()[0] if recon.stdout.strip() else ""
    if recon.returncode != 0:
        print()
        print(
            "⚠  RECONCILIATION PASS DUE (Q-0107) — make this a docs-only planning pass.",
        )
        print(f"   {recon_line}")
    else:
        print()
        recon_short = recon_line.replace("check_reconciliation_due: ", "")
        print(f"Recon  : {recon_short}")

    # Living-ledger drift advisory (Q-0152) — printed at START so a session sees drift
    # *growing* rather than discovering the whole pile at /session-close. Fail-silent: a
    # drift advisory must never break session start. (Self-referential reconciliation PRs
    # are already exempt inside the checker.)
    ledger = subprocess.run(
        [sys.executable, str(SCRIPTS / "check_current_state_ledger.py"), "--strict"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=15,
    )
    if ledger.returncode == 0:
        print("Ledger : in sync ✓")
    elif "not in" in ledger.stdout:
        match = re.search(r":\s*(\d+)\s+recent", ledger.stdout)
        count = match.group(1) if match else "some"
        print(
            f"Ledger : ⚠ {count} merged PR(s) not yet in current-state — reconcile before close",
        )

    # Quick commands
    print()
    print("Quick commands:")
    print(
        "  python3.10 scripts/check_architecture.py --mode strict   # full arch check",
    )
    print("  python3.10 scripts/check_quality.py --check-only         # lint only")
    print(
        "  python3.10 scripts/check_quality.py --full               # lint + mypy + tests",
    )
    print(SEP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
