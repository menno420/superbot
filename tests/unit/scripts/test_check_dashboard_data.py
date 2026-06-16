"""Tests for ``scripts/check_dashboard_data.py`` — the dashboard export guard.

Loaded via ``importlib`` (the repo convention for ``scripts/`` modules). Pure
stdlib, so it runs in CI with no extra dependencies — including the live guard
that validates the freshly-built export.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "check_dashboard_data.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("check_dashboard_data_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# cog -> subsystem resolution
# ---------------------------------------------------------------------------


def test_cog_subsystem_resolution_flags_unregistered_real_cog(mod):
    data = {
        "catalogue": [{"key": "economy"}],
        "cogs": [
            {"cog": "EconomyCog", "is_cog": True, "subsystem": "economy", "file": "a"},
            {"cog": "MysteryCog", "is_cog": True, "subsystem": "mystery", "file": "b"},
        ],
    }
    issues = mod.check_cog_subsystem_resolution(data)
    assert [i.code for i in issues] == ["cog_subsystem_unresolved"]
    assert "MysteryCog" in issues[0].message
    assert issues[0].severity == "error"


def test_cog_subsystem_resolution_allows_allowlist_and_modules(mod):
    data = {
        "catalogue": [{"key": "economy"}],
        # HermesCog is allow-listed (no own registry entry); the module is is_cog=False.
        "cogs": [
            {"cog": "HermesCog", "is_cog": True, "subsystem": "hermes", "file": "h"},
            {"cog": "(bot1.py)", "is_cog": False, "subsystem": "", "file": "b"},
        ],
    }
    assert mod.check_cog_subsystem_resolution(data) == []


# ---------------------------------------------------------------------------
# count integrity
# ---------------------------------------------------------------------------


def _count_consistent_data():
    return {
        "meta": {
            "counts": {
                "cogs": 1,
                "commands": 2,
                "synonyms": 1,
                "ideas": 0,
                "bugs": 0,
                "env_vars": 0,
                "setting_domains": 0,
                "setting_keys": 0,
                "visible_subsystems": 1,
            },
        },
        "cogs": [{"is_cog": True, "commands": [{}, {}]}],
        "synonyms": [{"synonyms": ["a"]}],
        "ideas": [],
        "bugs": [],
        "env_usage": [],
        "settings": [],
        "access": {"total_visible": 1},
    }


def test_count_integrity_passes_when_consistent(mod):
    assert mod.check_count_integrity(_count_consistent_data()) == []


def test_count_integrity_flags_mismatch_and_missing(mod):
    data = _count_consistent_data()
    data["meta"]["counts"]["commands"] = 99  # wrong
    del data["meta"]["counts"]["synonyms"]  # missing
    issues = mod.check_count_integrity(data)
    codes = {i.code for i in issues}
    assert "count_mismatch" in codes
    assert "count_missing" in codes
    mismatch = next(i for i in issues if i.code == "count_mismatch")
    assert mismatch.severity == "error"


# ---------------------------------------------------------------------------
# required fields
# ---------------------------------------------------------------------------


def test_required_fields_flags_each_class(mod):
    data = {
        "cogs": [
            {
                "cog": "X",
                "file": "",  # missing file
                "commands": [
                    {"name": "ok", "type": "prefix"},
                    {"name": "", "type": "weird"},  # missing name + bad type
                ],
            },
        ],
        "catalogue": [{"key": ""}],  # missing key
    }
    codes = {i.code for i in mod.check_required_fields(data)}
    assert codes == {
        "cog_missing_file",
        "command_missing_name",
        "command_bad_type",
        "catalogue_missing_key",
    }


# ---------------------------------------------------------------------------
# live guard — the in-CI value: a freshly-built export must be clean
# ---------------------------------------------------------------------------


def test_live_export_has_no_integrity_errors(mod):
    data = mod._build_fresh()
    errors = [i for i in mod.validate(data) if i.severity == "error"]
    assert errors == [], f"dashboard export has integrity errors: {errors}"


def test_main_fresh_exits_zero(mod):
    assert mod.main(["--fresh"]) == 0
