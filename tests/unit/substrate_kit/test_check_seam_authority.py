"""Tests for the config-driven seam-authority fences (Lane B6)."""

from pathlib import Path

from engine.checks.check_seam_authority import check_seam_authority

_DB_SEAM = {
    "name": "db-seam",
    "paths": ["src/**/*.py"],
    "forbidden": r"pool\.execute",
    "allowed": ["src/db/*"],
    "message": "call db helpers, never the pool directly",
}


def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def test_forbidden_hit_fires_with_name_message_and_lineno(tmp_path):
    _write(tmp_path / "src" / "cog.py", "x = 1\nawait pool.execute(q)\n")
    findings = check_seam_authority(tmp_path, [_DB_SEAM])
    assert len(findings) == 1
    f = findings[0]
    assert f.path == "src/cog.py" and f.kind == "seam"
    assert "L2:" in f.message
    assert "db-seam" in f.message
    assert "call db helpers" in f.message


def test_allowed_glob_exempts_the_seams_own_home(tmp_path):
    _write(tmp_path / "src" / "db" / "core.py", "await pool.execute(q)\n")
    assert check_seam_authority(tmp_path, [_DB_SEAM]) == []


def test_clean_files_and_unmatched_paths_are_silent(tmp_path):
    _write(tmp_path / "src" / "ok.py", "from db import helpers\n")
    _write(tmp_path / "README.md", "pool.execute mentioned outside scanned globs\n")
    assert check_seam_authority(tmp_path, [_DB_SEAM]) == []


def test_multiple_hits_and_multiple_seams(tmp_path):
    _write(tmp_path / "src" / "a.py", "pool.execute(q)\npool.execute(r)\n")
    _write(tmp_path / "views" / "v.py", "import cogs.thing\n")
    view_seam = {
        "name": "view-fence",
        "paths": ["views/*.py"],
        "forbidden": r"import cogs",
        "allowed": [],
        "message": "views must not import cogs",
    }
    findings = check_seam_authority(tmp_path, [_DB_SEAM, view_seam])
    assert len(findings) == 3
    kinds = {f.kind for f in findings}
    assert kinds == {"seam"}
    assert any("view-fence" in f.message for f in findings)


def test_invalid_regex_reported_not_raised(tmp_path):
    seam = {
        "name": "broken",
        "paths": ["*.py"],
        "forbidden": "(unclosed",
        "allowed": [],
        "message": "n/a",
    }
    findings = check_seam_authority(tmp_path, [seam])
    assert len(findings) == 1
    assert findings[0].kind == "seam"
    assert "invalid forbidden regex" in findings[0].message


def test_overlapping_globs_do_not_double_report(tmp_path):
    _write(tmp_path / "src" / "a.py", "pool.execute(q)\n")
    seam = dict(_DB_SEAM, paths=["src/**/*.py", "src/a.py"])
    assert len(check_seam_authority(tmp_path, [seam])) == 1


def test_no_seams_is_a_noop(tmp_path):
    assert check_seam_authority(tmp_path, []) == []
