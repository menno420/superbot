#!/usr/bin/env python3.10
"""Guard: the lint/format/type tool pins must match across CI and the dev install.

CLAUDE.md rule #3 (and the header of ``requirements-dev.txt``) requires the
``black`` / ``isort`` / ``ruff`` / ``mypy`` versions to be **identical** in:

* ``.github/workflows/code-quality.yml`` — what CI installs (the authority), and
* ``requirements-dev.txt``              — what local / Claude-Code-web sessions install.

When they drift, ``scripts/check_quality.py`` silently stops being a true CI
mirror: a newer local ruff flags rules the pinned CI ruff doesn't (and vice
versa) — "passes/fails locally, opposite in CI" churn. This is **not** a
hypothetical: dependabot PR #1074 bumped ``requirements-dev.txt``'s ruff to
0.15.18 while CI stayed at 0.15.14, so local runs flagged an ``ERA001`` that CI
never enforced (BUG-0022). Dependabot bumps the requirements file but not the
workflow pin, so this trap recurs — hence a guard.

Stdlib-only. Exit 0 = aligned; exit 1 = a mismatch (prints the offenders).

Run:  python3.10 scripts/check_tool_pins.py
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "code-quality.yml"
REQUIREMENTS_DEV = REPO_ROOT / "requirements-dev.txt"

# The tools whose output changes between releases, so a drift breaks the mirror.
_TOOLS = ("black", "isort", "ruff", "mypy")
_PIN = re.compile(r"\b(black|isort|ruff|mypy)==([0-9][0-9A-Za-z.\-]*)")


def _pins(text: str) -> dict[str, set[str]]:
    """All ``tool==version`` pins found in ``text`` (a set per tool, to catch dupes)."""
    found: dict[str, set[str]] = {t: set() for t in _TOOLS}
    for tool, version in _PIN.findall(text):
        found[tool].add(version)
    return found


def check() -> list[str]:
    """Return a list of human-readable mismatch messages (empty == all aligned)."""
    problems: list[str] = []
    for path in (CI_WORKFLOW, REQUIREMENTS_DEV):
        if not path.exists():
            problems.append(f"missing pin source: {path.relative_to(REPO_ROOT)}")
    if problems:
        return problems

    ci = _pins(CI_WORKFLOW.read_text(encoding="utf-8"))
    dev = _pins(REQUIREMENTS_DEV.read_text(encoding="utf-8"))

    for tool in _TOOLS:
        ci_v, dev_v = ci[tool], dev[tool]
        if not ci_v or not dev_v:
            # A tool not pinned in one place is its own (softer) problem; report it.
            if ci_v or dev_v:
                problems.append(
                    f"{tool}: pinned in only one place "
                    f"(code-quality.yml={sorted(ci_v) or '—'}, requirements-dev.txt={sorted(dev_v) or '—'})",
                )
            continue
        if ci_v != dev_v:
            problems.append(
                f"{tool}: CI pins {sorted(ci_v)} but requirements-dev.txt pins {sorted(dev_v)} "
                f"— align them (CLAUDE.md rule #3) so check_quality.py mirrors CI",
            )
    return problems


def main() -> int:
    problems = check()
    if problems:
        print("Tool-pin drift — local checks will not match CI:")
        for p in problems:
            print(f"  ✗ {p}")
        print(
            "\nFix: set the same version in code-quality.yml, requirements-dev.txt, "
            "and .pre-commit-config.yaml (the three-places rule).",
        )
        return 1
    print("✓ tool pins aligned — code-quality.yml == requirements-dev.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
