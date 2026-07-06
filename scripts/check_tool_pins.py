#!/usr/bin/env python3.10
"""Guard: the lint/format/type tool pins must match across CI and the dev install.

CLAUDE.md rule #3 (and the header of ``requirements-dev.txt``) requires the
``ruff`` / ``mypy`` versions to be **identical** in (ruff replaced black + isort, A3):

* ``.github/workflows/code-quality.yml`` — what CI installs (the authority),
* ``requirements-dev.txt``              — what local / Claude-Code-web sessions install, and
* ``.pre-commit-config.yaml``           — what the pre-commit hooks run.

When they drift, ``scripts/check_quality.py`` silently stops being a true CI
mirror: a newer local ruff flags rules the pinned CI ruff doesn't (and vice
versa) — "passes/fails locally, opposite in CI" churn. This is **not** a
hypothetical: dependabot PR #1074 bumped ``requirements-dev.txt``'s ruff to
0.15.18 while CI stayed at 0.15.14, so local runs flagged an ``ERA001`` that CI
never enforced (BUG-0022); it recurred in #1315 (fixed #1317). Dependabot bumps
the requirements file but not the workflow / pre-commit pins, so this trap
recurs — hence a guard (now also a CI trigger via ``.github/workflows/tool-pins.yml``).

Stdlib-only. Exit 0 = aligned; exit 1 = a mismatch (prints the offenders).

Run:  python3.10 scripts/check_tool_pins.py
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "code-quality.yml"
REQUIREMENTS_DEV = REPO_ROOT / "requirements-dev.txt"
PRE_COMMIT = REPO_ROOT / ".pre-commit-config.yaml"

# The tools whose output changes between releases, so a drift breaks the mirror.
_TOOLS = ("ruff", "mypy")
_PIN = re.compile(r"\b(ruff|mypy)==([0-9][0-9A-Za-z.\-]*)")

# Pre-commit identifies a tool by its hook repo, and pins via ``rev:`` (both ruff and
# mypy carry a leading ``v``), so it needs its own parser rather than the
# ``tool==version`` regex above. (The single ruff-pre-commit repo hosts both the
# ruff-format and ruff hooks under one ``rev:`` — one pin for both.)
_PRECOMMIT_REPO_TO_TOOL = {
    "ruff-pre-commit": "ruff",
    "mirrors-mypy": "mypy",
}
_PRECOMMIT_REV = re.compile(r"rev:\s*v?([0-9][0-9A-Za-z.\-]*)")

# Human-readable source labels, in authority order (CI first).
_SOURCES = (
    ("code-quality.yml", CI_WORKFLOW),
    ("requirements-dev.txt", REQUIREMENTS_DEV),
    (".pre-commit-config.yaml", PRE_COMMIT),
)


def _pins(text: str) -> dict[str, set[str]]:
    """All ``tool==version`` pins found in ``text`` (a set per tool, to catch dupes)."""
    found: dict[str, set[str]] = {t: set() for t in _TOOLS}
    for tool, version in _PIN.findall(text):
        found[tool].add(version)
    return found


def _precommit_pins(text: str) -> dict[str, set[str]]:
    """Tool → ``rev`` versions in a ``.pre-commit-config.yaml`` (``v`` prefix stripped)."""
    found: dict[str, set[str]] = {t: set() for t in _TOOLS}
    current: str | None = None
    for line in text.splitlines():
        repo = re.search(r"repo:\s*(\S+)", line)
        if repo:
            current = next(
                (
                    tool
                    for key, tool in _PRECOMMIT_REPO_TO_TOOL.items()
                    if key in repo.group(1)
                ),
                None,
            )
            continue
        if current:
            rev = _PRECOMMIT_REV.search(line)
            if rev:
                found[current].add(rev.group(1))
                current = None  # consumed this repo's rev
    return found


def _pins_for(label: str, path: Path) -> dict[str, set[str]]:
    text = path.read_text(encoding="utf-8")
    return _precommit_pins(text) if label == ".pre-commit-config.yaml" else _pins(text)


def check(sources: tuple[tuple[str, Path], ...] = _SOURCES) -> list[str]:
    """Return a list of human-readable mismatch messages (empty == all aligned)."""
    problems: list[str] = []
    for _label, path in sources:
        if not path.exists():
            problems.append(f"missing pin source: {path}")
    if problems:
        return problems

    pins = {label: _pins_for(label, path) for label, path in sources}

    for tool in _TOOLS:
        by_source = {label: pins[label][tool] for label, _ in sources}
        present = {label: v for label, v in by_source.items() if v}
        if not present:
            continue
        missing = [label for label, _ in sources if not by_source[label]]
        all_versions = set().union(*present.values())
        if len(all_versions) > 1 or missing:
            detail = ", ".join(
                f"{label}={sorted(by_source[label]) or '—'}" for label, _ in sources
            )
            problems.append(
                f"{tool}: pins disagree ({detail}) "
                f"— align all three (CLAUDE.md rule #3) so check_quality.py mirrors CI",
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
    print(
        "✓ tool pins aligned — code-quality.yml == requirements-dev.txt "
        "== .pre-commit-config.yaml",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
