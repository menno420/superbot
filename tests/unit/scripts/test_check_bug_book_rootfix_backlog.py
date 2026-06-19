"""Tests for ``scripts/check_bug_book_rootfix_backlog.py`` — the root-fix backlog guard.

Loaded via ``importlib`` (the repo convention for ``scripts/`` modules, which are not a
package). Pure stdlib, so it runs in CI with no extra dependencies. Classification is
verified against an inline fixture, never the live bug book, so the test is deterministic
as real entries open and close.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "check_bug_book_rootfix_backlog.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location(
        "check_bug_book_rootfix_backlog_ut", _SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SAMPLE = """# Bug book

## BUG-0099 — symptom patched, root deferred — FIXED (immediate) / root-fix RECOMMENDED

- **Symptom:** something reddened CI.
- **Root-fix RECOMMENDED (not done):** do the durable thing later.
- **Status:** FIXED 2026-06-19 — immediate regen landed; root cause documented for later.

## BUG-0098 — half done — PARTIALLY FIXED

- **Symptom:** a family of mislabels.
- **Status:** PARTIALLY FIXED — slices 1+2 done, slice 3 OPEN.

## BUG-0097 — interim only

- **Symptom:** a thing.
- **Status:** FIXED (immediate) — interim, no durable fix yet.

## BUG-0096 — fully closed — FIXED (root)

- **Symptom:** a thing.
- **Root-fix DONE (recommendation (a)):** the durable fix landed.
- **Status:** FIXED (root) 2026-06-19 — closed at the root.

## BUG-0095 — ordinary closed — FIXED

- **Symptom:** a thing.
- **Status:** FIXED — this PR.

## BUG-0094 — still open — OPEN

- **Symptom:** infra crash-loop.
- **Status:** OPEN — captured during a setup session.
"""


def test_flags_recommended_partial_and_immediate_only(mod):
    backlog = mod.find_rootfix_backlog(SAMPLE)
    flagged = {item.bug_id for item in backlog}
    # The three "looks done but owes a root fix" classes are flagged.
    assert flagged == {"BUG-0099", "BUG-0098", "BUG-0097"}


def test_does_not_flag_terminal_or_open(mod):
    backlog = mod.find_rootfix_backlog(SAMPLE)
    flagged = {item.bug_id for item in backlog}
    # FIXED (root) and plain FIXED are terminal; OPEN is honestly-labelled, not the trap.
    assert "BUG-0096" not in flagged
    assert "BUG-0095" not in flagged
    assert "BUG-0094" not in flagged


def test_fixed_root_short_circuits_a_recommendation_mention(mod):
    # An entry closed at the root whose body still says "recommendation (a)" must
    # NOT re-flag — the FIXED (root) terminal wins (the BUG-0018 self-fix shape).
    text = (
        "## BUG-0100 — closed but mentions recommendation — FIXED (root)\n\n"
        "- **Root-fix DONE (recommendation (a)):** durable fix landed.\n"
        "- **Status:** FIXED (root) — recommendation (a) implemented.\n"
    )
    assert mod.find_rootfix_backlog(text) == []


def test_reason_strings_are_specific(mod):
    by_id = {item.bug_id: item.reason for item in mod.find_rootfix_backlog(SAMPLE)}
    assert "partially" in by_id["BUG-0098"].lower()
    assert "recommended" in by_id["BUG-0099"].lower()
    assert "immediate" in by_id["BUG-0097"].lower()


def test_empty_book_is_clean(mod):
    assert mod.find_rootfix_backlog("# Bug book\n\nNo entries yet.\n") == []


# ---------------------------------------------------------------------------
# #1144 review hardening — precise matching, scoped to the status label not the title
# ---------------------------------------------------------------------------


def test_title_mentioning_partially_is_not_flagged(mod):
    # A title like "partially ignores X" with a terminal FIXED status must NOT flag —
    # the bare word "partially" in the title is not the "PARTIALLY FIXED" status phrase.
    text = (
        "## BUG-0200 — counting partially ignores role hierarchy — FIXED\n\n"
        "- **Symptom:** a thing.\n"
        "- **Status:** FIXED — this PR.\n"
    )
    assert mod.find_rootfix_backlog(text) == []


def test_immediate_with_root_cause_prose_is_still_flagged(mod):
    # "FIXED (immediate)" whose deferral text says "root cause deferred" must still
    # flag — keying on the "(root)" marker, not any occurrence of the word "root".
    text = (
        "## BUG-0201 — interim patch — FIXED (immediate)\n\n"
        "- **Status:** FIXED (immediate) — root cause deferred, no durable fix yet.\n"
    )
    flagged = {item.bug_id for item in mod.find_rootfix_backlog(text)}
    assert flagged == {"BUG-0201"}


def test_terminal_fixed_mentioning_recommendation_is_not_flagged(mod):
    # A closed entry whose status says "recommendation (a) implemented" must NOT flag —
    # "recommendation" is not the deferred-root word "RECOMMENDED".
    text = (
        "## BUG-0202 — closed — FIXED (root)\n\n"
        "- **Status:** FIXED (root) — recommendation (a) implemented.\n"
    )
    assert mod.find_rootfix_backlog(text) == []


def test_title_with_root_word_and_partially_does_not_false_positive(mod):
    # Belt-and-braces: a title carrying both "root" and "partially" with a plain FIXED
    # status is terminal — the title is never scanned for status signals.
    text = (
        "## BUG-0203 — root partially restored after partial outage — FIXED\n\n"
        "- **Status:** FIXED — root-caused and fixed.\n"
    )
    assert mod.find_rootfix_backlog(text) == []


def test_main_advisory_exit_zero_even_with_backlog(mod, tmp_path):
    book = tmp_path / "bug-book.md"
    book.write_text(SAMPLE, encoding="utf-8")
    assert mod.main(["--path", str(book)]) == 0  # advisory default


def test_main_strict_exits_one_on_backlog(mod, tmp_path):
    book = tmp_path / "bug-book.md"
    book.write_text(SAMPLE, encoding="utf-8")
    assert mod.main(["--strict", "--path", str(book)]) == 1


def test_main_strict_exits_zero_when_clean(mod, tmp_path):
    book = tmp_path / "bug-book.md"
    book.write_text(
        "# Bug book\n\n## BUG-1 — done — FIXED\n\n- **Status:** FIXED\n",
        encoding="utf-8",
    )
    assert mod.main(["--strict", "--path", str(book)]) == 0


def test_main_missing_file_is_advisory(mod, tmp_path):
    assert mod.main(["--path", str(tmp_path / "nope.md")]) == 0
