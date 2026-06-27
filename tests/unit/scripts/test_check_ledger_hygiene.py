"""Tests for ``scripts/check_ledger_hygiene.py`` — the B2 ledger-hygiene linter.

Covers the duplicate detectors (per-file claim-branch collisions, idea index
entries, any-link cross-refs), the entry-vs-advisory split, and ``main`` exit
codes in both report-only and ``--strict`` modes — including the real-repo
invariant that the linter exits 0 against the live ledgers so its PR can land
(it never modifies the ledgers it can only read).

De-staled 2026-06-27 for the Q-0195 per-claim-file restructure: the claim half
now scans ``docs/owner/claims/*.md`` for a branch claimed by more than one file
(the single shared ``active-work.md`` claim ledger was retired to a pointer stub).
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


def _claims(tmp_path: Path, files: dict[str, str]) -> Path:
    """Build a per-file claim directory and return it. ``files`` is {filename: body}."""
    claims = tmp_path / "claims"
    claims.mkdir()
    for name, body in files.items():
        (claims / name).write_text(body, encoding="utf-8")
    return claims


# --- duplicate_claim_branches (per-file, Q-0195) ----------------------------


def test_duplicate_claim_branches_flags_branch_in_two_files(tmp_path: Path) -> None:
    claims = _claims(
        tmp_path,
        {
            "a.md": "- `claude/dup` · scope one · 2026-06-27\n",
            "b.md": "- `claude/dup` · scope two (accidental re-claim) · 2026-06-27\n",
            "c.md": "- `claude/solo` · scope · 2026-06-27\n",
        },
    )
    assert clh.duplicate_claim_branches(claims) == [("claude/dup", 2)]


def test_duplicate_claim_branches_same_branch_repeated_in_one_file_is_not_a_dupe(
    tmp_path: Path,
) -> None:
    """A single claim file naming its own branch twice counts once (per-file)."""
    claims = _claims(
        tmp_path,
        {"a.md": "- `claude/x` · scope\n- see `claude/x` again in this same file\n"},
    )
    assert clh.duplicate_claim_branches(claims) == []


def test_duplicate_claim_branches_skips_readme(tmp_path: Path) -> None:
    claims = _claims(
        tmp_path,
        {
            "README.md": "convention doc mentioning `claude/foo` as an example\n",
            "foo.md": "- `claude/foo` · real claim\n",
        },
    )
    # README's example mention must not collide with the real claim.
    assert clh.duplicate_claim_branches(claims) == []


def test_duplicate_claim_branches_clean(tmp_path: Path) -> None:
    claims = _claims(
        tmp_path,
        {"a.md": "- `claude/a`\n", "b.md": "- `claude/b`\n"},
    )
    assert clh.duplicate_claim_branches(claims) == []


def test_duplicate_claim_branches_sorted_and_counts(tmp_path: Path) -> None:
    claims = _claims(
        tmp_path,
        {
            "1.md": "- `claude/zeta`\n",
            "2.md": "- `claude/zeta`\n",
            "3.md": "- `claude/zeta`\n",
            "4.md": "- `claude/alpha`\n",
            "5.md": "- `claude/alpha`\n",
        },
    )
    assert clh.duplicate_claim_branches(claims) == [
        ("claude/alpha", 2),
        ("claude/zeta", 3),
    ]


def test_duplicate_claim_branches_missing_dir_is_empty(tmp_path: Path) -> None:
    assert clh.duplicate_claim_branches(tmp_path / "nope") == []


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
    claims = _claims(tmp_path, {"a.md": "- `claude/a`\n"})
    rm = tmp_path / "README.md"
    rm.write_text("- [`a.md`](./a.md) — one\n", encoding="utf-8")
    rc = clh.main(["--claims-dir", str(claims), "--ideas-readme", str(rm)])
    assert rc == 0
    assert "clean" in capsys.readouterr().out


def test_main_hard_dupe_report_only_exits_zero(tmp_path, capsys) -> None:
    claims = _claims(
        tmp_path,
        {"a.md": "- `claude/dup`\n", "b.md": "- `claude/dup`\n"},
    )
    rm = tmp_path / "README.md"
    rm.write_text("- [`a.md`](./a.md)\n", encoding="utf-8")
    # Report-only default: surfaces the dupe but exits 0 (non-blocking advisory).
    rc = clh.main(["--claims-dir", str(claims), "--ideas-readme", str(rm)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "claude/dup" in out and "report-only" in out


def test_main_advisory_crossref_never_fails_strict(tmp_path, capsys) -> None:
    """A cross-reference-only duplicate is advisory: exits 0 even under --strict."""
    claims = _claims(tmp_path, {"a.md": "- `claude/a`\n"})
    rm = tmp_path / "README.md"
    rm.write_text(
        "- [`foo.md`](./foo.md) — entry\n"
        "- [`bar.md`](./bar.md) — see [`foo.md`](./foo.md)\n",
        encoding="utf-8",
    )
    rc = clh.main(["--strict", "--claims-dir", str(claims), "--ideas-readme", str(rm)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Advisory" in out


# --- main: --strict (exit 1 on a hard dupe) ---------------------------------


def test_main_strict_fails_on_duplicate_claim(tmp_path, capsys) -> None:
    claims = _claims(
        tmp_path,
        {"a.md": "- `claude/dup`\n", "b.md": "- `claude/dup`\n"},
    )
    rm = tmp_path / "README.md"
    rm.write_text("- [`a.md`](./a.md)\n", encoding="utf-8")
    rc = clh.main(["--strict", "--claims-dir", str(claims), "--ideas-readme", str(rm)])
    out = capsys.readouterr().out
    assert rc == 1
    assert "FAIL" in out and "claude/dup" in out


def test_main_strict_fails_on_duplicate_idea_entry(tmp_path, capsys) -> None:
    claims = _claims(tmp_path, {"a.md": "- `claude/a`\n"})
    rm = tmp_path / "README.md"
    rm.write_text(
        "- [`foo.md`](./foo.md) — entry one\n- [`foo.md`](./foo.md) — entry two\n",
        encoding="utf-8",
    )
    rc = clh.main(["--strict", "--claims-dir", str(claims), "--ideas-readme", str(rm)])
    out = capsys.readouterr().out
    assert rc == 1
    assert "FAIL" in out and "./foo.md" in out


def test_main_missing_files_exit_zero(tmp_path, capsys) -> None:
    """Absent claim dir / idea file read as empty → clean, never crash."""
    rc = clh.main(
        [
            "--claims-dir",
            str(tmp_path / "nope"),
            "--ideas-readme",
            str(tmp_path / "nope2.md"),
        ]
    )
    assert rc == 0
    assert "clean" in capsys.readouterr().out


# --- live-repo invariant ----------------------------------------------------


def test_live_ledgers_exit_zero_report_only() -> None:
    """Against the real ledgers, the default report-only run must exit 0."""
    assert clh.main([]) == 0


def test_module_carries_kill_switch_header() -> None:
    """Q-0105 disposability: the docstring must say to delete it if unreliable."""
    assert clh.__doc__ is not None
    doc = clh.__doc__.lower()
    assert "unverified" in doc
    assert "delete this script" in doc
