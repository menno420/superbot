"""Workflow↔script flag parity guard.

Provenance / reliability header (per CLAUDE.md Q-0105 adopt-with-kill-switch):
- Why: PR #1770 caught `code-quality.yml` invoking ``check_session_slug_unique.py --strict``
  when the script defines no ``--strict`` flag — argparse exited 2, so the (advisory) checker
  never ran at all. A checker that can't parse its own CI invocation is silently dead
  (the Q-0120 "green/red that lies" class). This test enforces, per Q-0194 friction→guard,
  that every ``scripts/*.py`` invocation in ``code-quality.yml`` only passes long options the
  script's ``--help`` actually advertises.
- Added: 2026-07-06 (session `claude/superbot-rebuild-phase-2.5-qk07s7`). **Unverified** —
  confirm its output against ground truth a few times across sessions before trusting it.
  **Delete this test if it proves unreliable over multiple sessions** (e.g. a script whose
  ``--help`` is dynamic); it is a disposable convenience guard, not load-bearing.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "code-quality.yml"

# python3 scripts/foo.py --a --b value  (run: lines, incl. line-continuation multi-line runs)
_INVOCATION_RE = re.compile(r"python3?(?:\.\d+)?\s+(scripts/[\w./-]+\.py)((?:\s+\S+)*)")
_LONG_OPT_RE = re.compile(r"^--[\w-]+$")


def _invocations() -> list[tuple[str, list[str]]]:
    """(script, [long options]) for each scripts/*.py invocation in code-quality.yml."""
    text = WORKFLOW.read_text(encoding="utf-8")
    # Join backslash line-continuations so multi-line `run: |` commands parse as one.
    text = re.sub(r"\\\n\s*", " ", text)
    found: list[tuple[str, list[str]]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue  # commented-out or explanatory lines are not invocations
        m = _INVOCATION_RE.search(stripped)
        if not m:
            continue
        script, tail = m.group(1), m.group(2)
        opts = [tok for tok in tail.split() if _LONG_OPT_RE.match(tok)]
        found.append((script, opts))
    return found


def test_workflow_only_passes_flags_the_scripts_define() -> None:
    invocations = _invocations()
    assert invocations, "no scripts/*.py invocations found — regex or workflow moved?"
    failures: list[str] = []
    for script, opts in invocations:
        if not opts:
            continue
        path = REPO_ROOT / script
        if not path.exists():
            failures.append(f"{script}: invoked in code-quality.yml but missing on disk")
            continue
        result = subprocess.run(
            [sys.executable, str(path), "--help"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            timeout=60,
        )
        if result.returncode != 0:
            failures.append(f"{script}: --help exited {result.returncode}")
            continue
        for opt in opts:
            if opt not in result.stdout:
                failures.append(
                    f"{script}: workflow passes {opt} but --help does not list it "
                    "(argparse would exit 2 and the step never really runs)"
                )
    assert not failures, "\n".join(failures)


def test_regex_catches_the_pr_1770_shape() -> None:
    """Self-check: the parser sees a flagged invocation like the one that broke."""
    line = "        run: python3 scripts/check_session_slug_unique.py --strict"
    m = _INVOCATION_RE.search(line.strip())
    assert m is not None
    assert m.group(1) == "scripts/check_session_slug_unique.py"
    assert "--strict" in m.group(2)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
