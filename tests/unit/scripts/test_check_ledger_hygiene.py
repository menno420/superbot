"""Tests for ``scripts/check_ledger_hygiene.py`` — the B2 ledger-hygiene linter.

Covers section scoping, the three duplicate detectors (active-claim branches,
idea index entries, any-link cross-refs), the entry-vs-advisory split, and
``main`` exit codes in both report-only and ``--strict`` modes — including the
real-repo invariant that the linter exits 0 against the live ledgers so its PR
can land (it never modifies the ledgers it can only read).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_MOD = _REPO_ROOT / "scripts" / "check_ledger_hygiene.py"

_spec = importlib.util.spec_from_file_location("check_ledger_hygiene", _MOD)
assert _spec and _spec.loader
clh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(clh)


# --- section_body -----------------------------------------------------------


def test_section_body_extracts_named_section() -> None:
    text = (
        "# Title\n\n"
        "## Active claims\n"
        "- `claude/a` · scope\n"
        "- `claude/b` · scope\n\n"
        "## Recently cleared\n"
        "- `claude/a` · 2026 · PR #1\n"
    )
    body = clh.section_body(text, "Active claims")
    assert "`claude/a`" in body and "`claude/b`" in body
    # The Recently-cleared line must NOT bleed into the Active-claims body.
    assert "PR #1" not in body


def test_section_body_missing_returns_empty() -> None:
    assert clh.section_body("## Other\n- x\n", "Active claims") == ""


def test_section_body_exact_heading_match_not_prefix() -> None:
    text = "## Active claims extended\n- `claude/x`\n"
    # The heading "Active claims" must not match "Active claims extended".
    assert clh.section_body(text, "Active claims") == ""


# --- duplicate_active_claims ------------------------------------------------


def test_duplicate_active_claims_flags_repeat_in_section() -> None:
    text = (
        "## Active claims\n"
        "- `claude/dup` · scope one\n"
        "- `claude/solo` · scope\n"
        "- `claude/dup` · scope two (accidental re-add)\n"
    )
    assert clh.duplicate_active_claims(text) == [("claude/dup", 2)]


def test_duplicate_active_claims_ignores_recently_cleared() -> None:
    """A branch in BOTH Active claims and Recently cleared is NOT a duplicate."""
    text = (
        "## Active claims\n"
        "- `claude/live` · current work\n"
        "## Recently cleared\n"
        "- `claude/live` · 2026 · PR #9 (different older run, same generated slug)\n"
    )
    assert clh.duplicate_active_claims(text) == []


def test_duplicate_active_claims_clean_section() -> None:
    text = "## Active claims\n- `claude/a`\n- `claude/b`\n"
    assert clh.duplicate_active_claims(text) == []


def test_duplicate_active_claims_sorted_and_counts() -> None:
    text = (
        "## Active claims\n"
        "- `claude/zeta`\n- `claude/zeta`\n- `claude/zeta`\n"
        "- `claude/alpha`\n- `claude/alpha`\n"
    )
    assert clh.duplicate_active_claims(text) == [
        ("claude/alpha", 2),
        ("claude/zeta", 3),
    ]


# --- duplicate_idea_entries -------------------------------------------------


def test_duplicate_idea_entries_flags_double_index_row() -> None:
    text = (
        "- [`foo-2026-06-16.md`](./foo-2026-06-16.md) — first index entry\n"
        "- [`bar-2026-06-16.md`](./bar-2026-06-16.md) — other\n"
        "- [`foo-2026-06-16.md`](./foo-2026-06-16.md) — accidental second entry\n"
    )
    assert clh.duplicate_idea_entries(text) == [("./foo-2026-06-16.md", 2)]


def test_duplicate_idea_entries_inline_crossref_not_an_entry() -> None:
    """A cross-ref inside another idea's prose is NOT a duplicate index entry."""
    text = (
        "- [`foo-2026-06-16.md`](./foo-2026-06-16.md) — the one index entry\n"
        "- [`bar-2026-06-16.md`](./bar-2026-06-16.md) — references\n"
        "  [`foo-2026-06-16.md`](./foo-2026-06-16.md) for context\n"
    )
    # Only one *index entry* for foo (the indented prose ref does not open a list item).
    assert clh.duplicate_idea_entries(text) == []


def test_duplicate_idea_entries_clean() -> None:
    text = "- [`a.md`](./a.md) — one\n- [`b.md`](./b.md) — two\n"
    assert clh.duplicate_idea_entries(text) == []


# --- duplicate_idea_links (any link, advisory superset) ---------------------


def test_duplicate_idea_links_includes_crossrefs() -> None:
    text = (
        "- [`foo.md`](./foo.md) — entry\n"
        "- [`bar.md`](./bar.md) — see [`foo.md`](./foo.md)\n"
    )
    assert clh.duplicate_idea_links(text) == [("./foo.md", 2)]


# --- main: report-only (always exit 0) --------------------------------------


def test_main_clean_exits_zero(tmp_path, capsys) -> None:
    aw = tmp_path / "active-work.md"
    aw.write_text("## Active claims\n- `claude/a`\n", encoding="utf-8")
    rm = tmp_path / "README.md"
    rm.write_text("- [`a.md`](./a.md) — one\n", encoding="utf-8")
    rc = clh.main(["--active-work", str(aw), "--ideas-readme", str(rm)])
    assert rc == 0
    assert "clean" in capsys.readouterr().out


def test_main_hard_dupe_report_only_exits_zero(tmp_path, capsys) -> None:
    aw = tmp_path / "active-work.md"
    aw.write_text(
        "## Active claims\n- `claude/dup`\n- `claude/dup`\n", encoding="utf-8"
    )
    rm = tmp_path / "README.md"
    rm.write_text("- [`a.md`](./a.md)\n", encoding="utf-8")
    # Report-only default: surfaces the dupe but exits 0 (non-blocking advisory).
    rc = clh.main(["--active-work", str(aw), "--ideas-readme", str(rm)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "claude/dup" in out and "report-only" in out


def test_main_advisory_crossref_never_fails_strict(tmp_path, capsys) -> None:
    """A cross-reference-only duplicate is advisory: exits 0 even under --strict.

    This is the live-repo case (`live-decade-queue-pointer-invariant` linked
    twice) — the linter must NOT redden a PR for an intentional cross-ref.
    """
    aw = tmp_path / "active-work.md"
    aw.write_text("## Active claims\n- `claude/a`\n", encoding="utf-8")
    rm = tmp_path / "README.md"
    rm.write_text(
        "- [`foo.md`](./foo.md) — entry\n"
        "- [`bar.md`](./bar.md) — see [`foo.md`](./foo.md)\n",
        encoding="utf-8",
    )
    rc = clh.main(["--strict", "--active-work", str(aw), "--ideas-readme", str(rm)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Advisory" in out


# --- main: --strict (exit 1 on a hard dupe) ---------------------------------


def test_main_strict_fails_on_duplicate_claim(tmp_path, capsys) -> None:
    aw = tmp_path / "active-work.md"
    aw.write_text(
        "## Active claims\n- `claude/dup`\n- `claude/dup`\n", encoding="utf-8"
    )
    rm = tmp_path / "README.md"
    rm.write_text("- [`a.md`](./a.md)\n", encoding="utf-8")
    rc = clh.main(["--strict", "--active-work", str(aw), "--ideas-readme", str(rm)])
    out = capsys.readouterr().out
    assert rc == 1
    assert "FAIL" in out and "claude/dup" in out


def test_main_strict_fails_on_duplicate_idea_entry(tmp_path, capsys) -> None:
    aw = tmp_path / "active-work.md"
    aw.write_text("## Active claims\n- `claude/a`\n", encoding="utf-8")
    rm = tmp_path / "README.md"
    rm.write_text(
        "- [`foo.md`](./foo.md) — entry one\n- [`foo.md`](./foo.md) — entry two\n",
        encoding="utf-8",
    )
    rc = clh.main(["--strict", "--active-work", str(aw), "--ideas-readme", str(rm)])
    out = capsys.readouterr().out
    assert rc == 1
    assert "FAIL" in out and "./foo.md" in out


def test_main_missing_files_exit_zero(tmp_path, capsys) -> None:
    """Absent ledger files read as empty → clean, never crash."""
    rc = clh.main(
        [
            "--active-work",
            str(tmp_path / "nope.md"),
            "--ideas-readme",
            str(tmp_path / "nope2.md"),
        ]
    )
    assert rc == 0
    assert "clean" in capsys.readouterr().out


# --- live-repo invariant ----------------------------------------------------


def test_live_ledgers_exit_zero_report_only() -> None:
    """Against the real ledgers, the default report-only run must exit 0.

    Guards the brief's landing requirement: even if the live README has a real
    cross-ref duplicate, the linter exits cleanly so its own PR can merge.
    """
    assert clh.main([]) == 0


def test_module_carries_kill_switch_header() -> None:
    """Q-0105 disposability: the docstring must say to delete it if unreliable."""
    assert clh.__doc__ is not None
    doc = clh.__doc__.lower()
    assert "unverified" in doc
    assert "delete this script" in doc
