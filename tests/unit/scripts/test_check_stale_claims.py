"""Tests for scripts/check_stale_claims.py — the per-claim GC sweep (Q-0195).

Cover the pure parse + classification logic (no git, no real directory): a claim file
whose branch is gone/merged is stale; an active one (or one with no branch) is kept.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "check_stale_claims",
    Path(__file__).resolve().parents[3] / "scripts" / "check_stale_claims.py",
)
assert _SPEC and _SPEC.loader
csc = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(csc)


def test_branch_of_extracts_branch_token():
    assert csc.branch_of("- `claude/foo-bar` · **x** · `a.py` · 2026") == "claude/foo-bar"


def test_branch_of_none_when_absent():
    assert csc.branch_of("- some claim with no branch token") is None


def _write(dir_, name, body):
    (dir_ / name).write_text(body)
    return dir_ / name


def test_find_stale_flags_gone_and_merged_keeps_active(tmp_path):
    a = _write(tmp_path, "a.md", "- `claude/a` · merged lane\n")
    b = _write(tmp_path, "b.md", "- `claude/b` · gone lane\n")
    c = _write(tmp_path, "c.md", "- `claude/c` · active lane\n")
    state = {"claude/a": "merged", "claude/b": "gone", "claude/c": "active"}
    stale = csc.find_stale([a, b, c], lambda br: state[br])
    stale_paths = {p.name for p, _, _ in stale}
    assert stale_paths == {"a.md", "b.md"}  # active 'c' kept


def test_find_stale_ignores_files_with_no_branch(tmp_path):
    p = _write(tmp_path, "weird.md", "- a claim with no branch token at all\n")
    assert csc.find_stale([p], lambda br: "gone") == []


def test_claim_files_excludes_readme(tmp_path, monkeypatch):
    _write(tmp_path, "README.md", "readme")
    _write(tmp_path, "claude__x.md", "- `claude/x` · lane\n")
    monkeypatch.setattr(csc, "_CLAIMS_DIR", tmp_path)
    names = {p.name for p in csc.claim_files()}
    assert names == {"claude__x.md"}
