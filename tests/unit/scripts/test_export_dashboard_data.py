"""Tests for ``scripts/export_dashboard_data.py`` — the dashboard data exporter.

Loaded via ``importlib`` (the repo convention for ``scripts/`` modules, which are
not a package) so the test does not depend on ``sys.path`` layout. The exporter is
pure stdlib, so this runs in CI with no extra dependencies.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "export_dashboard_data.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("export_dashboard_data_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SAMPLE_REGISTRY = '''
from utils.ui_constants import ADMIN_COLOR

SUBSYSTEMS: dict[str, dict] = {
    "admin": {
        "display_name": "Administration",
        "description": "Cog management",
        "emoji": "X",
        "color": ADMIN_COLOR.value,
        "category": "admin",
        "visibility_tier": "administrator",
        "tags": ["admin", "cogs"],
        "entry_points": ["adminmenu"],
        "capabilities": ["admin.cog.load"],
    },
}
'''

SAMPLE_BUGS = """# Bug book

## BUG-0014 — `!coglist` infinite loop — FIXED

- **Symptom (owner-reported):** typing `!coglist`
  spammed the channel endlessly until restart.
- **Root cause:** something.

## BUG-0010 — something still broken — OPEN

- **Symptom:** it breaks.
"""


def test_parse_catalogue_extracts_literals_and_skips_color(mod):
    entries = mod.parse_catalogue(SAMPLE_REGISTRY)
    assert len(entries) == 1
    entry = entries[0]
    assert entry["key"] == "admin"
    assert entry["display_name"] == "Administration"
    assert entry["tags"] == ["admin", "cogs"]
    assert entry["entry_points"] == ["adminmenu"]
    # The non-literal ``color`` field is skipped, not crashed on.
    assert "color" not in entry


def test_parse_catalogue_handles_source_without_registry(mod):
    assert mod.parse_catalogue("x = 1\n") == []


def test_parse_bugs_extracts_id_title_status_summary(mod):
    bugs = mod.parse_bugs(SAMPLE_BUGS)
    assert [b["id"] for b in bugs] == ["BUG-0014", "BUG-0010"]
    assert bugs[0]["status"] == "FIXED"
    assert bugs[1]["status"] == "OPEN"
    assert "infinite loop" in bugs[0]["title"]
    # Multi-line symptom is joined.
    assert "spammed the channel endlessly" in bugs[0]["summary"]


def test_parse_ideas_reads_title_status_date(mod, tmp_path):
    ideas_dir = tmp_path / "ideas"
    ideas_dir.mkdir()
    (ideas_dir / "README.md").write_text("# index\n", encoding="utf-8")
    (ideas_dir / "cool-thing-2026-06-16.md").write_text(
        "# Cool thing\n\n> **Status:** `ideas`\n\nThis is the idea body.\n",
        encoding="utf-8",
    )
    ideas = mod.parse_ideas(ideas_dir)
    assert len(ideas) == 1
    assert ideas[0]["title"] == "Cool thing"
    assert ideas[0]["date"] == "2026-06-16"
    assert ideas[0]["summary"] == "This is the idea body."


def test_build_data_against_real_repo_is_well_formed(mod):
    data = mod.build_data()
    assert set(data) >= {"meta", "catalogue", "ideas", "bugs", "updates", "env_usage"}
    assert data["meta"]["counts"]["functions"] == len(data["catalogue"])
    assert len(data["catalogue"]) >= 10
    keys = {e["key"] for e in data["catalogue"]}
    assert "admin" in keys
    for entry in data["catalogue"]:
        assert isinstance(entry["key"], str)


def test_build_data_includes_env_usage_section(mod):
    data = mod.build_data()
    env_usage = data["env_usage"]
    assert data["meta"]["counts"]["env_vars"] == len(env_usage)
    assert len(env_usage) >= 20
    names = {r["name"] for r in env_usage}
    assert "DATABASE_URL" in names
    # The section is the scanner's shape (names + locations only, no values).
    for record in env_usage:
        assert set(record) == {"name", "required", "usage_count", "layers", "usages"}
