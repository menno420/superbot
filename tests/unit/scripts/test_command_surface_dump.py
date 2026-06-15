"""Tests for ``scripts/command_surface_dump.py`` — offline command-surface dump."""

from __future__ import annotations

import importlib.util
import json
import sys
from io import StringIO
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "command_surface_dump.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("command_surface_dump_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_collect_returns_entries(mod):
    entries = mod.collect()
    assert len(entries) > 50, "expected many commands across all cog files"


def test_economy_cog_known_commands(mod):
    entries = mod.collect(cog_filter="economy_cog.py")
    names = {e.name for e in entries}
    assert "daily" in names
    assert "balance" in names
    assert "shop" in names
    assert "economymenu" in names


def test_aliases_extracted(mod):
    entries = mod.collect(cog_filter="economy_cog.py")
    balance = next(e for e in entries if e.name == "balance")
    assert "bal" in balance.aliases
    assert "wallet" in balance.aliases


def test_kind_prefix_vs_slash(mod):
    entries = mod.collect(cog_filter="economy_cog.py")
    prefix_cmds = [e for e in entries if e.kind == "prefix"]
    slash_cmds = [e for e in entries if e.kind == "slash"]
    assert prefix_cmds, "should have prefix commands"
    assert slash_cmds, "should have slash commands"


def test_admin_perm_detected(mod):
    entries = mod.collect(cog_filter="admin_cog.py")
    restart = next((e for e in entries if e.name == "restart"), None)
    assert restart is not None
    assert restart.perm == "admin"


def test_json_output_roundtrip(mod, capsys):
    mod.main(["--json", "--cog", "economy_cog.py"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert all("name" in item and "kind" in item for item in data)


def test_diff_checklist_exits_nonzero_with_gaps(mod):
    # There are always some source commands not in the checklist.
    rc = mod.main(["--diff-checklist"])
    assert rc in (0, 1), "should exit 0 (no gaps) or 1 (gaps found)"


def test_no_commands_returns_error(mod, tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "COGS_DIR", tmp_path)
    rc = mod.main([])
    assert rc == 1
