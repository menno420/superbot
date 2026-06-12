"""Tests for ``scripts/check_session_log.py`` — the Q-0089/Q-0102 session-log gate."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
_MOD = REPO_ROOT / "scripts" / "check_session_log.py"

_spec = importlib.util.spec_from_file_location("check_session_log", _MOD)
assert _spec and _spec.loader
csl = importlib.util.module_from_spec(_spec)
sys.modules["check_session_log"] = csl
_spec.loader.exec_module(csl)


_COMPLETE = """# Session log

> **Status:** `audit`

## What was done
stuff

## 💡 Session idea
an idea

## ⟲ Previous-session review
a review
"""


def test_complete_log_has_no_missing() -> None:
    assert csl.missing_sections(_COMPLETE) == []


def test_missing_idea_and_review_detected() -> None:
    text = "> **Status:** `audit`\n\nbody only"
    missing = csl.missing_sections(text)
    assert any("Q-0089" in m for m in missing)
    assert any("Q-0102" in m for m in missing)
    assert not any("Status badge" in m for m in missing)


def test_missing_badge_detected() -> None:
    text = "# log\n\n## 💡 Session idea\nx\n\n## ⟲ Previous-session review\ny"
    missing = csl.missing_sections(text)
    assert any("Status badge" in m for m in missing)
    assert len(missing) == 1


def test_review_match_is_case_insensitive() -> None:
    text = "> **Status:** `audit`\n💡\n## PREVIOUS-SESSION REVIEW\nx"
    assert csl.missing_sections(text) == []


def test_check_reads_file(tmp_path: Path) -> None:
    log = tmp_path / "2099-01-01-example.md"
    log.write_text(_COMPLETE, encoding="utf-8")
    assert csl.check(log) == []


def test_check_missing_file_reports_all(tmp_path: Path) -> None:
    missing = csl.check(tmp_path / "does-not-exist.md")
    assert len(missing) == 3


def test_strict_exit_on_incomplete(tmp_path: Path) -> None:
    log = tmp_path / "2099-01-01-bad.md"
    log.write_text("no markers here", encoding="utf-8")
    rc = csl.main(["--file", str(log), "--strict"])
    assert rc == 1


def test_nonstrict_exit_zero_on_incomplete(tmp_path: Path) -> None:
    log = tmp_path / "2099-01-01-bad.md"
    log.write_text("no markers here", encoding="utf-8")
    rc = csl.main(["--file", str(log)])
    assert rc == 0


def test_complete_log_passes_via_cli(tmp_path: Path) -> None:
    log = tmp_path / "2099-01-01-ok.md"
    log.write_text(_COMPLETE, encoding="utf-8")
    assert csl.main(["--file", str(log), "--strict"]) == 0
