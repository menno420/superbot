"""Tests for ``scripts/check_phase_gate.py`` — the autonomous-loop phase gate.

Guards the fix-phase/invent-phase signal: the OPEN-bug counter, the
readiness-not-done wiring, and the gate logic (both hard conditions must clear
to reach invent-phase). The maps/bug-book are the source of truth; these tests
pin the *derivation*, not the live numbers.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
_MODULE = REPO_ROOT / "scripts" / "check_phase_gate.py"

_spec = importlib.util.spec_from_file_location("check_phase_gate", _MODULE)
assert _spec and _spec.loader
phase_gate = importlib.util.module_from_spec(_spec)
sys.modules["check_phase_gate"] = phase_gate
_spec.loader.exec_module(phase_gate)


def test_count_open_bugs_parses_status_lines(tmp_path: Path) -> None:
    book = tmp_path / "bug-book.md"
    book.write_text(
        "## BUG-0001 — foo — OPEN\n"
        "- **Status:** OPEN — captured this session\n\n"
        "## BUG-0002 — bar\n"
        "- **Status:** FIXED — this PR\n\n"
        "## BUG-0003 — baz\n"
        "- **Status:** OPEN — needs a repro\n",
        encoding="utf-8",
    )
    assert phase_gate.count_open_bugs(book) == 2


def test_count_open_bugs_missing_file_is_zero(tmp_path: Path) -> None:
    assert phase_gate.count_open_bugs(tmp_path / "nope.md") == 0


def test_evaluate_shape_and_keys() -> None:
    result = phase_gate.evaluate()
    assert result["phase"] in ("fix", "invent")
    for key in (
        "open_bugs",
        "readiness_not_done",
        "readiness_done_pct",
        "blocking_reasons",
    ):
        assert key in result
    assert isinstance(result["blocking_reasons"], list)


def test_phase_is_fix_iff_blocking_reasons() -> None:
    result = phase_gate.evaluate()
    has_reasons = bool(result["blocking_reasons"])
    assert (result["phase"] == "fix") == has_reasons
    # The two hard conditions are exactly the reason sources.
    if result["open_bugs"] or result["readiness_not_done"]:
        assert result["phase"] == "fix"


def test_phase_flag_prints_token(capsys: pytest.CaptureFixture[str]) -> None:
    rc = phase_gate.main(["--phase"])
    assert rc == 0
    out = capsys.readouterr().out.strip()
    assert out in ("fix", "invent")


def test_require_invent_exit_code_matches_phase() -> None:
    rc = phase_gate.main(["--require-invent"])
    phase = phase_gate.evaluate()["phase"]
    assert rc == (0 if phase == "invent" else 1)
