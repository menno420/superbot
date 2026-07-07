"""Adopt-time slot derivation — "adopt renders what it knows" (the Phase-2.5 G2 fix).

The cold-start A/B (``phase-2.5-cold-start-report-2026-07-07.md``) failed
because ``adopt`` planted raw ``${...}`` templates: a task-focused cold
session paid the reading cost and (correctly) ignored them. The fix has two
halves; this module is the first — derive every slot the kit can know
**deterministically** from the target tree (project name, primary language,
verify command, docs root) and record each as a *provisional* interview
answer before the adopt render, so the planted docs open readable instead of
inert. Provisional answers never count toward graduation until confirmed
(the interview contract is unchanged) and ``bootstrap ask`` still asks —
derivation seeds the interview, it does not replace it. Detection is
file-presence based, never a guess: a slot with no confident signal stays
unfilled (and the adopt banner marks it — the second half, in ``adopt.py``).
Pure stdlib.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from engine.interview.interview import record_answer
from engine.interview.question_bank import QUESTIONS

_REQUIRES_PYTHON_RE = re.compile(r'requires-python\s*=\s*"([^"]+)"')
_MAKEFILE_TEST_RE = re.compile(r"^test\s*:", re.MULTILINE)

# Marker files that make a tree confidently Python before any other check.
_PYTHON_MARKERS = ("pyproject.toml", "setup.py", "setup.cfg", "requirements.txt")


def _read_if_exists(path: Path) -> str:
    """Return the file's text, or empty for a missing/unreadable file."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def detect_language(root: Path) -> str | None:
    """Return the project's primary language from marker files, or None.

    Python wins ties deliberately (the kit's own tooling is Python-first and a
    mixed tree with a ``pyproject.toml`` is Python-led for verification
    purposes). The version qualifier comes only from an explicit
    ``requires-python`` — never inferred.
    """
    if any((root / marker).is_file() for marker in _PYTHON_MARKERS):
        match = _REQUIRES_PYTHON_RE.search(_read_if_exists(root / "pyproject.toml"))
        return f"Python {match.group(1)}" if match else "Python"
    if (root / "package.json").is_file():
        return "TypeScript" if (root / "tsconfig.json").is_file() else "JavaScript"
    if (root / "Cargo.toml").is_file():
        return "Rust"
    if (root / "go.mod").is_file():
        return "Go"
    return None


def _python_has_tests(root: Path) -> bool:
    """True when the tree carries a recognizable pytest surface."""
    if (root / "tests").is_dir() or (root / "pytest.ini").is_file():
        return True
    pyproject = _read_if_exists(root / "pyproject.toml")
    return "[tool.pytest" in pyproject


def _npm_has_real_test_script(root: Path) -> bool:
    """True when package.json declares a test script that isn't npm's stub."""
    text = _read_if_exists(root / "package.json")
    if '"test"' not in text:
        return False
    return "no test specified" not in text


def detect_verify_command(root: Path) -> str | None:
    """Return the one-command verification entry point, or None.

    Order mirrors :func:`detect_language`; each candidate requires a positive
    marker (a test tree, a real test script, a ``test:`` target) so the
    derived command is runnable, not aspirational.
    """
    if any((root / marker).is_file() for marker in _PYTHON_MARKERS):
        if _python_has_tests(root):
            return "python3 -m pytest"
        return None
    if (root / "package.json").is_file() and _npm_has_real_test_script(root):
        return "npm test"
    if (root / "Cargo.toml").is_file():
        return "cargo test"
    if (root / "go.mod").is_file():
        return "go test ./..."
    if _MAKEFILE_TEST_RE.search(_read_if_exists(root / "Makefile")):
        return "make test"
    return None


def derive_slots(root: Path, docs_root: str) -> dict[str, str]:
    """Return every slot value derivable from the target tree.

    Keys match the question bank's slot names. Only confidently-derived
    entries appear — absent key means "leave the slot to the interview".
    """
    derived: dict[str, str] = {"project_name": root.resolve().name}
    language = detect_language(root)
    if language:
        derived["primary_language"] = language
    verify = detect_verify_command(root)
    if verify:
        derived["verify_command"] = verify
    if docs_root:
        derived["doc_roots"] = docs_root
    return derived


def record_derived_slots(backend: Any, derived: dict[str, str]) -> list[str]:
    """Record derived values as provisional answers for still-empty slots.

    Existing answers of any status (filled / partial / provisional) are never
    overwritten — derivation only seeds blanks. Returns report lines in the
    adopt-report format.
    """
    by_slot = {question["slot"]: question for question in QUESTIONS}
    slots = backend.get("slots", {})
    lines: list[str] = []
    for slot, value in derived.items():
        question = by_slot.get(slot)
        if question is None or slots.get(slot):
            continue
        record_answer(backend, question, value, source="derived")
        lines.append(
            f"derived: {slot} = {value!r} (provisional — confirm or correct "
            f"via `bootstrap answer {slot} ...`)",
        )
    return lines
