"""Tests for ``scripts/scan_setting_specs.py`` — the SettingSpec scanner.

Loaded via ``importlib`` (the repo convention for ``scripts/`` modules). Pure
stdlib, so it runs in CI with no extra dependencies.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "scan_setting_specs.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("scan_setting_specs_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SAMPLE_SCHEMA = '''
from core.runtime.subsystem_schema import SettingSpec
from utils.settings_keys import MY_FLAG

LOCAL_DEFAULT = True

SAMPLE_SETTINGS = (
    SettingSpec(
        name="flag",
        value_type=bool,
        default=LOCAL_DEFAULT,
        settings_key=MY_FLAG,
        hint="A sample flag.",
        capability_required="sample.configure",
    ),
    SettingSpec(
        name="mode",
        value_type=str,
        default="normal",
        settings_key="sample_mode",
        allowed_values=("off", "normal", "strict"),
    ),
)
'''


def _write_repo(tmp_path: Path) -> tuple[Path, Path]:
    cogs = tmp_path / "cogs" / "sample"
    cogs.mkdir(parents=True)
    (cogs / "schemas.py").write_text(SAMPLE_SCHEMA, encoding="utf-8")
    keys = tmp_path / "settings_keys"
    keys.mkdir()
    (keys / "sample.py").write_text('MY_FLAG = "my_flag"\n', encoding="utf-8")
    return tmp_path / "cogs", keys


def test_scan_setting_specs_extracts_typed_metadata(mod, tmp_path):
    cogs_dir, keys_dir = _write_repo(tmp_path)
    records = mod.scan_setting_specs(cogs_dir=cogs_dir, keys_dir=keys_dir)
    by_name = {r["name"]: r for r in records}

    flag = by_name["flag"]
    assert flag["subsystem"] == "sample"
    assert flag["value_type"] == "bool"
    assert flag["settings_key"] == "my_flag"  # resolved from the constant
    assert flag["default"] is True and flag["default_known"] is True  # local const
    assert flag["hint"] == "A sample flag."

    mode = by_name["mode"]
    assert mode["settings_key"] == "sample_mode"  # string-literal key
    assert mode["allowed_values"] == ["off", "normal", "strict"]


def test_scan_setting_specs_real_repo(mod):
    records = mod.scan_setting_specs()
    assert len(records) >= 50
    by_key = {r["settings_key"]: r for r in records if r["settings_key"]}

    # An enum-shaped setting surfaces its choices.
    provider = by_key.get("ai_default_provider")
    assert provider is not None
    assert "openai" in provider["allowed_values"]

    # An imported (cross-module) default resolves rather than showing None.
    enabled = by_key.get("automod_enabled")
    assert enabled is not None
    assert enabled["default_known"] is True
    assert enabled["value_type"] == "bool"
