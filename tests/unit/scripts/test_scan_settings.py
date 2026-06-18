"""Tests for ``scripts/scan_settings.py`` — the settings-key catalogue scanner.

Loaded via ``importlib`` (the repo convention for ``scripts/`` modules). Pure
stdlib, so it runs in CI with no extra dependencies.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "scan_settings.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("scan_settings_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SAMPLE_DOMAIN = '''"""Settings keys owned by the Sample subsystem (cogs.sample_cog)."""

SAMPLE_ENABLED = "sample_enabled"
SAMPLE_THRESHOLD = "sample_threshold"
# Not a settings key (non-string) — must be skipped.
SAMPLE_LIMIT = 5
'''

SAMPLE_INIT = '''"""Re-export surface — must be skipped by the scanner."""

from utils.settings_keys.sample import SAMPLE_ENABLED

__all__ = ["SAMPLE_ENABLED"]
'''


def _write_keys_dir(tmp_path: Path) -> Path:
    keys_dir = tmp_path / "settings_keys"
    keys_dir.mkdir()
    (keys_dir / "sample.py").write_text(SAMPLE_DOMAIN, encoding="utf-8")
    (keys_dir / "__init__.py").write_text(SAMPLE_INIT, encoding="utf-8")
    return keys_dir


def test_scan_settings_extracts_keys_and_purpose(mod, tmp_path):
    records = mod.scan_settings(_write_keys_dir(tmp_path))
    assert len(records) == 1  # __init__ skipped
    sample = records[0]
    assert sample["domain"] == "sample"
    assert "Sample subsystem" in sample["purpose"]
    by_const = {k["constant"]: k["key"] for k in sample["keys"]}
    assert by_const == {
        "SAMPLE_ENABLED": "sample_enabled",
        "SAMPLE_THRESHOLD": "sample_threshold",
    }
    # the non-string constant is not a settings key
    assert "SAMPLE_LIMIT" not in by_const


def test_scan_settings_real_repo(mod):
    records = mod.scan_settings()
    by_domain = {r["domain"] for r in records}
    assert {"xp", "automod", "moderation"} <= by_domain
    assert "__init__" not in by_domain
    xp = next(r for r in records if r["domain"] == "xp")
    assert ("XP_MIN", "xp_min") in {(k["constant"], k["key"]) for k in xp["keys"]}
    total = sum(len(r["keys"]) for r in records)
    assert total >= 50
