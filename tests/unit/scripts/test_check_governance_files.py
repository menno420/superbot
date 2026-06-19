"""Tests for ``scripts/check_governance_files.py`` — the Fleet B1 governance guard.

Covers presence (missing / empty file), path-freshness (a stale backtick repo-path
in a root governance doc), CFF validity (missing required key), the ``--strict``
exit contract, and that the live repo's governance files actually pass.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
_MOD = REPO_ROOT / "scripts" / "check_governance_files.py"

_spec = importlib.util.spec_from_file_location("check_governance_files", _MOD)
assert _spec and _spec.loader
cgf = importlib.util.module_from_spec(_spec)
sys.modules["check_governance_files"] = cgf
_spec.loader.exec_module(cgf)


def _seed_clean_repo(root: Path) -> None:
    """Write a minimal, fully-valid governance file set into ``root``."""
    (root / "LICENSE").write_text("MIT License\n\nCopyright (c) 2026\n", encoding="utf-8")
    (root / "SECURITY.md").write_text(
        "# Security Policy\n\nReport via `disbot/control_api.py`.\n",
        encoding="utf-8",
    )
    # A referenced path that exists on disk.
    (root / "disbot").mkdir(exist_ok=True)
    (root / "disbot" / "control_api.py").write_text("x = 1\n", encoding="utf-8")
    (root / "CONTRIBUTING.md").write_text(
        "# Contributing\n\nRun `scripts/check_quality.py`. See `docs/`.\n",
        encoding="utf-8",
    )
    (root / "scripts").mkdir(exist_ok=True)
    (root / "scripts" / "check_quality.py").write_text("y = 2\n", encoding="utf-8")
    (root / "docs").mkdir(exist_ok=True)
    (root / "CITATION.cff").write_text(
        "cff-version: 1.2.0\ntitle: Test\nauthors:\n  - given-names: A\n",
        encoding="utf-8",
    )


def _patch_root(monkeypatch, root: Path) -> None:
    monkeypatch.setattr(cgf, "REPO_ROOT", root)


# --- presence ---------------------------------------------------------------


def test_clean_seeded_repo_passes(tmp_path, monkeypatch) -> None:
    _seed_clean_repo(tmp_path)
    _patch_root(monkeypatch, tmp_path)
    assert cgf.collect_violations() == []
    assert cgf.main([]) == 0
    assert cgf.main(["--strict"]) == 0


def test_missing_file_is_a_violation(tmp_path, monkeypatch) -> None:
    _seed_clean_repo(tmp_path)
    (tmp_path / "LICENSE").unlink()
    _patch_root(monkeypatch, tmp_path)
    violations = cgf.check_presence()
    assert ("LICENSE", "missing — required governance file does not exist") in violations
    assert cgf.main(["--strict"]) == 1


def test_empty_file_is_a_violation(tmp_path, monkeypatch) -> None:
    _seed_clean_repo(tmp_path)
    (tmp_path / "SECURITY.md").write_text("   \n\n", encoding="utf-8")
    _patch_root(monkeypatch, tmp_path)
    problems = [p for where, p in cgf.check_presence() if where == "SECURITY.md"]
    assert any("empty" in p for p in problems)
    assert cgf.main(["--strict"]) == 1


def test_all_required_files_checked(tmp_path, monkeypatch) -> None:
    # Wipe everything: every required file should be reported missing.
    _patch_root(monkeypatch, tmp_path)
    reported = {where for where, _ in cgf.check_presence()}
    assert reported == set(cgf.REQUIRED_FILES)


# --- freshness --------------------------------------------------------------


def test_stale_path_reference_is_a_violation(tmp_path, monkeypatch) -> None:
    _seed_clean_repo(tmp_path)
    # CONTRIBUTING cites a script that does not exist on disk.
    (tmp_path / "CONTRIBUTING.md").write_text(
        "# Contributing\n\nRun `scripts/totally_gone.py`.\n",
        encoding="utf-8",
    )
    _patch_root(monkeypatch, tmp_path)
    violations = cgf.check_freshness()
    assert (
        "CONTRIBUTING.md",
        "references missing path `scripts/totally_gone.py`",
    ) in violations
    assert cgf.main(["--strict"]) == 1


def test_stale_directory_reference_is_a_violation(tmp_path, monkeypatch) -> None:
    _seed_clean_repo(tmp_path)
    (tmp_path / "SECURITY.md").write_text(
        "# Security\n\nSee `disbot/nonexistent_dir/`.\n",
        encoding="utf-8",
    )
    _patch_root(monkeypatch, tmp_path)
    violations = cgf.check_freshness()
    assert any("disbot/nonexistent_dir/" in p for _, p in violations)


def test_fresh_paths_pass(tmp_path, monkeypatch) -> None:
    _seed_clean_repo(tmp_path)
    _patch_root(monkeypatch, tmp_path)
    assert cgf.check_freshness() == []


def test_referenced_paths_skips_placeholders(tmp_path, monkeypatch) -> None:
    # A glob/placeholder path is not treated as a concrete reference.
    refs = cgf._referenced_paths("see `scripts/*.py` and `docs/<name>.md`")
    assert refs == set()


def test_referenced_paths_finds_files_and_dirs() -> None:
    text = "Run `scripts/check_quality.py` in `disbot/`, read `docs/architecture.md`."
    refs = cgf._referenced_paths(text)
    assert "scripts/check_quality.py" in refs
    assert "docs/architecture.md" in refs
    assert "disbot/" in refs


# --- citation ---------------------------------------------------------------


def test_missing_cff_key_is_a_violation(tmp_path, monkeypatch) -> None:
    _seed_clean_repo(tmp_path)
    # Drop the `authors` key.
    (tmp_path / "CITATION.cff").write_text(
        "cff-version: 1.2.0\ntitle: Test\n",
        encoding="utf-8",
    )
    _patch_root(monkeypatch, tmp_path)
    violations = cgf.check_citation()
    assert ("CITATION.cff", "missing required CFF key `authors`") in violations
    assert cgf.main(["--strict"]) == 1


def test_valid_cff_passes(tmp_path, monkeypatch) -> None:
    _seed_clean_repo(tmp_path)
    _patch_root(monkeypatch, tmp_path)
    assert cgf.check_citation() == []


def test_absent_cff_not_double_reported_by_citation(tmp_path, monkeypatch) -> None:
    # check_citation must not crash / report when the file is absent (presence owns that).
    _patch_root(monkeypatch, tmp_path)
    assert cgf.check_citation() == []


# --- strict / advisory exit contract ----------------------------------------


def test_advisory_never_fails(tmp_path, monkeypatch) -> None:
    # Even with everything missing, the advisory (non-strict) run exits 0.
    _patch_root(monkeypatch, tmp_path)
    assert cgf.main([]) == 0


def test_strict_fails_when_violations(tmp_path, monkeypatch) -> None:
    _patch_root(monkeypatch, tmp_path)
    assert cgf.main(["--strict"]) == 1


# --- live repo --------------------------------------------------------------


def test_live_repo_governance_files_pass() -> None:
    """The real repo's governance files must be present, fresh, and CFF-valid."""
    assert cgf.collect_violations() == []
