"""Tests for ``scripts/upload_btd6_data.py`` (offline paths only).

The upload itself needs boto3 + credentials; here we exercise the pure
manifest builder, the local manifest write, and ``--check`` against the real
data tree — no network, no boto3.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "upload_btd6_data.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("upload_btd6_data", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mod = _load_module()


def test_build_manifest_hashes_files(tmp_path):
    (tmp_path / "a.json").write_text('{"x": 1}', encoding="utf-8")
    sub = tmp_path / "stats"
    sub.mkdir()
    (sub / "b.json").write_text('{"y": 2}', encoding="utf-8")

    manifest = mod.build_manifest(tmp_path)
    assert manifest["count"] == 2
    assert set(manifest["files"]) == {"a.json", "stats/b.json"}
    assert all(len(f["sha256"]) == 64 for f in manifest["files"].values())
    assert manifest["files"]["a.json"]["size"] == len('{"x": 1}')


def test_build_manifest_excludes_manifest_itself(tmp_path):
    (tmp_path / "a.json").write_text("{}", encoding="utf-8")
    (tmp_path / "manifest.json").write_text("{}", encoding="utf-8")
    manifest = mod.build_manifest(tmp_path)
    assert set(manifest["files"]) == {"a.json"}


def test_write_manifest_roundtrip(tmp_path):
    (tmp_path / "a.json").write_text("{}", encoding="utf-8")
    manifest = mod.build_manifest(tmp_path)
    target = mod.write_manifest(tmp_path, manifest)
    assert target.exists()
    assert json.loads(target.read_text(encoding="utf-8"))["count"] == 1


def test_check_mode_runs_on_real_data():
    assert mod.main(["--check"]) == 0


def test_manifest_on_real_data_includes_fixtures():
    manifest = mod.build_manifest(mod.DEFAULT_ROOT)
    assert manifest["count"] >= 7  # 7 committed fixtures + the stats tree
    assert "towers.json" in manifest["files"]
