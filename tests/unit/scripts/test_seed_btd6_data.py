"""Tests for ``scripts/seed_btd6_data.py`` (offline paths only).

The actual seed needs a database; here we exercise the pure row builder and
``--dry-run`` against the real data tree — no DB connection.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "seed_btd6_data.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("seed_btd6_data", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mod = _load_module()


def test_build_rows_parses_and_hashes(tmp_path):
    (tmp_path / "a.json").write_text('{"x": 1}', encoding="utf-8")
    sub = tmp_path / "stats"
    sub.mkdir()
    (sub / "b.json").write_text('{"y": 2}', encoding="utf-8")

    rows = mod.build_rows(tmp_path)
    by_name = {name: (body, sha) for name, body, sha in rows}
    assert set(by_name) == {"a.json", "stats/b.json"}
    assert by_name["a.json"][0] == {"x": 1}  # parsed body
    assert len(by_name["a.json"][1]) == 64  # sha256 hex


def test_build_rows_excludes_manifest(tmp_path):
    (tmp_path / "a.json").write_text("{}", encoding="utf-8")
    (tmp_path / "manifest.json").write_text("{}", encoding="utf-8")
    assert {name for name, _b, _s in mod.build_rows(tmp_path)} == {"a.json"}


def test_dry_run_on_real_data():
    assert mod.main(["--dry-run"]) == 0


def test_rows_on_real_data_include_fixtures():
    rows = mod.build_rows(mod.DEFAULT_ROOT)
    names = {name for name, _b, _s in rows}
    assert "towers.json" in names
    assert len(rows) >= 7
