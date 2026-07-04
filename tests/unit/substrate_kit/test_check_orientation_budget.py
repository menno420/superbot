"""Tests for the orientation-budget gate (Lane B6, the K0 word cap)."""

from pathlib import Path

from engine.checks.check_orientation_budget import (
    check_orientation_budget,
    orientation_word_count,
)
from engine.lib.config import Config


def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _config(**orientation) -> Config:
    base = {"budget_words": 7000, "boot_docs": []}
    base.update(orientation)
    return Config(orientation=base)


# ---------------------------------------------------------------------------
# orientation_word_count
# ---------------------------------------------------------------------------


def test_word_count_per_doc_and_total(tmp_path):
    a = tmp_path / "docs" / "a.md"
    b = tmp_path / "docs" / "b.md"
    _write(a, "one two three\n")
    _write(b, "four five\n")
    counts = orientation_word_count(tmp_path, [a, b])
    assert counts == {"docs/a.md": 3, "docs/b.md": 2, "_total": 5}


def test_word_count_missing_file_counts_zero(tmp_path):
    counts = orientation_word_count(tmp_path, [tmp_path / "gone.md"])
    assert counts == {"gone.md": 0, "_total": 0}


# ---------------------------------------------------------------------------
# check_orientation_budget — budget over/under
# ---------------------------------------------------------------------------


def test_under_budget_is_clean(tmp_path):
    _write(tmp_path / "docs" / "boot.md", "a few words only\n")
    config = _config(budget_words=100, boot_docs=["boot.md"])
    assert check_orientation_budget(tmp_path, config) == []


def test_over_budget_fires_naming_total_and_budget(tmp_path):
    _write(tmp_path / "docs" / "boot.md", "w " * 30)
    config = _config(budget_words=10, boot_docs=["boot.md"])
    findings = check_orientation_budget(tmp_path, config)
    assert len(findings) == 1
    f = findings[0]
    assert f.kind == "orientation-budget"
    assert "30 words" in f.message and "10-word" in f.message


def test_missing_boot_doc_reported(tmp_path):
    config = _config(budget_words=100, boot_docs=["ghost.md"])
    findings = check_orientation_budget(tmp_path, config)
    assert len(findings) == 1
    assert findings[0].kind == "orientation-missing"
    assert findings[0].path == "docs/ghost.md"


def test_empty_boot_docs_falls_back_to_readpath_docs(tmp_path):
    _write(tmp_path / "docs" / "AGENT_ORIENTATION.md", "short\n")
    _write(tmp_path / "docs" / "current-state.md", "short\n")
    config = Config(orientation={"budget_words": 100, "boot_docs": []})
    assert config.readpath_docs == ["AGENT_ORIENTATION.md", "current-state.md"]
    assert check_orientation_budget(tmp_path, config) == []


def test_entry_with_slash_resolves_from_project_root(tmp_path):
    _write(tmp_path / ".session-journal.md", "root level doc\n")
    config = _config(budget_words=100, boot_docs=[".session-journal.md"])
    # Bare name -> docs_root -> missing; with a slash -> project root -> found.
    assert len(check_orientation_budget(tmp_path, config)) == 1
    config = _config(budget_words=100, boot_docs=["./.session-journal.md"])
    assert check_orientation_budget(tmp_path, config) == []


# ---------------------------------------------------------------------------
# Per-doc self-caps
# ---------------------------------------------------------------------------


def test_self_cap_over_fires(tmp_path):
    body = "<!-- substrate-budget: 5 words -->\n" + "word " * 20
    _write(tmp_path / "docs" / "capped.md", body)
    config = _config(budget_words=1000, boot_docs=["capped.md"])
    findings = check_orientation_budget(tmp_path, config)
    assert len(findings) == 1
    f = findings[0]
    assert f.kind == "orientation-doc-cap" and f.path == "docs/capped.md"
    assert "5-word self-cap" in f.message


def test_self_cap_under_is_clean(tmp_path):
    body = "<!-- substrate-budget: 50 words -->\njust a few words\n"
    _write(tmp_path / "docs" / "capped.md", body)
    config = _config(budget_words=1000, boot_docs=["capped.md"])
    assert check_orientation_budget(tmp_path, config) == []


def test_self_cap_only_read_from_first_12_lines(tmp_path):
    body = "\n" * 15 + "substrate-budget: 1 words\n" + "word " * 10
    _write(tmp_path / "docs" / "late.md", body)
    config = _config(budget_words=1000, boot_docs=["late.md"])
    assert check_orientation_budget(tmp_path, config) == []
