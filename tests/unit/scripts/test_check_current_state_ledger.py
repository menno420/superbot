"""Tests for ``scripts/check_current_state_ledger.py`` — the ledger drift guard."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
_MOD = REPO_ROOT / "scripts" / "check_current_state_ledger.py"

_spec = importlib.util.spec_from_file_location("check_current_state_ledger", _MOD)
assert _spec and _spec.loader
csl = importlib.util.module_from_spec(_spec)
sys.modules["check_current_state_ledger"] = csl
_spec.loader.exec_module(csl)


def test_standalone_refs() -> None:
    nums = csl.ledger_pr_numbers("shipped **#730** and PR #733, also (#729)")
    assert {729, 730, 733} <= nums


def test_range_expansion_en_dash() -> None:
    nums = csl.ledger_pr_numbers("- **#715–#723** the map set")
    assert {715, 716, 717, 718, 719, 720, 721, 722, 723} <= nums
    assert 724 not in nums


def test_range_expansion_hyphen_and_bare_hi() -> None:
    assert {685, 686, 698} <= csl.ledger_pr_numbers("#685-#698")
    assert {700, 701, 702} <= csl.ledger_pr_numbers("#700–702")


def test_absurd_range_is_ignored() -> None:
    # A stray "#1–#9999" must not balloon into thousands of entries.
    nums = csl.ledger_pr_numbers("#1–#9999")
    assert 5000 not in nums


def test_merge_subject_extraction(monkeypatch) -> None:
    subjects = "\n".join(
        [
            "Merge pull request #734 from menno420/branch",
            "fix: something (#733)",
            "chore: no pr number here",
            "Merge pull request #730 from menno420/other",
        ]
    )

    class _R:
        returncode = 0
        stdout = subjects

    monkeypatch.setattr(csl.subprocess, "run", lambda *a, **k: _R())
    nums = csl._git_merged_pr_numbers(10)
    assert nums == [734, 733, 730]  # order preserved, de-duped, non-PR skipped


def test_find_missing_flags_unlisted(monkeypatch) -> None:
    monkeypatch.setattr(csl, "_git_merged_pr_numbers", lambda limit: [734, 733, 730])
    monkeypatch.setattr(csl, "_ledger_text", lambda: "shipped **#733** and **#730**")
    assert csl.find_missing(window=15) == [734]


def test_find_missing_empty_when_all_present(monkeypatch) -> None:
    monkeypatch.setattr(csl, "_git_merged_pr_numbers", lambda limit: [733, 730])
    monkeypatch.setattr(csl, "_ledger_text", lambda: "#730 #733")
    assert csl.find_missing() == []


def test_range_in_ledger_covers_member(monkeypatch) -> None:
    monkeypatch.setattr(csl, "_git_merged_pr_numbers", lambda limit: [719])
    monkeypatch.setattr(csl, "_ledger_text", lambda: "- **#715–#723** the set")
    assert csl.find_missing() == []


def test_strict_exit_code(monkeypatch) -> None:
    monkeypatch.setattr(csl, "find_missing", lambda window: [999])
    assert csl.main(["--strict"]) == 1
    assert csl.main([]) == 0  # advisory default never fails
