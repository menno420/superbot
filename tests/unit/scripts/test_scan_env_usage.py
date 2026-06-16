"""Tests for ``scripts/scan_env_usage.py`` — the read-only env-var usage scanner.

Loaded via ``importlib`` (the repo convention for ``scripts/`` modules, which are
not a package). Pure stdlib, so it runs in CI with no extra dependencies.

The scanner's contract: it surfaces variable **names and code locations only** —
never a value. The ``no_value`` test pins that guarantee.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "scan_env_usage.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("scan_env_usage_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SAMPLE = '''
import os
from os import getenv, environ

TOKEN = os.getenv("DISCORD_TOKEN")               # required (no default)
PREFIX = os.getenv("BOT_PREFIX", "!")            # optional (default)
LEVEL = os.environ.get("LOG_LEVEL")              # required (no default)
HOST = os.environ.get("HOST", "localhost")       # optional (default)
DSN = os.environ["DATABASE_URL"]                 # required (subscript)
BARE = getenv("BARE_VAR", "x")                   # optional via bare import
BARE_REQ = environ["BARE_REQ"]                   # required via bare environ
'''


def test_scan_source_detects_every_access_shape(mod):
    reads = mod.scan_source(SAMPLE)
    names = {name for name, _line, _default in reads}
    assert names == {
        "DISCORD_TOKEN",
        "BOT_PREFIX",
        "LOG_LEVEL",
        "HOST",
        "DATABASE_URL",
        "BARE_VAR",
        "BARE_REQ",
    }


def test_required_vs_optional_classification(mod):
    by_name = {name: default for name, _line, default in mod.scan_source(SAMPLE)}
    # has_default True == optional.
    assert by_name["BOT_PREFIX"] is True
    assert by_name["HOST"] is True
    assert by_name["BARE_VAR"] is True
    # has_default False == required.
    assert by_name["DISCORD_TOKEN"] is False
    assert by_name["LOG_LEVEL"] is False
    assert by_name["DATABASE_URL"] is False
    assert by_name["BARE_REQ"] is False


def test_keyword_default_counts_as_optional(mod):
    # A keyword default (rare, but valid) must read as having a default.
    reads = mod.scan_source('import os\nX = os.getenv("KW", default="z")\n')
    assert reads == [("KW", 2, True)]


def test_non_string_name_is_skipped(mod):
    # Dynamic names (a variable, not a literal) cannot be mapped — skip, no crash.
    reads = mod.scan_source('import os\nkey = "X"\nv = os.getenv(key)\n')
    assert reads == []


def test_unrelated_get_is_not_an_env_read(mod):
    # ``some_dict.get("X")`` / ``cfg.getenv`` must not be mistaken for os.environ.
    src = 'd = {}\nv = d.get("X", 1)\nw = cfg.getenv("Y")\n'
    assert mod.scan_source(src) == []


def test_scan_source_tolerates_syntax_error(mod):
    assert mod.scan_source("def (:\n") == []


def test_scan_env_usage_aggregates_and_sorts(mod, tmp_path):
    root = tmp_path / "disbot"
    (root / "services").mkdir(parents=True)
    (root / "config.py").write_text(
        'import os\nT = os.getenv("APP_TOKEN")\n', encoding="utf-8"
    )
    (root / "services" / "svc.py").write_text(
        'import os\nA = os.getenv("APP_TOKEN", "")\nB = os.getenv("OPTIONAL_FLAG", "0")\n',
        encoding="utf-8",
    )
    records = mod.scan_env_usage(scan_root=root, repo_root=tmp_path)

    by_name = {r["name"]: r for r in records}
    # APP_TOKEN read once without a default (config) => required, two usages, two layers.
    token = by_name["APP_TOKEN"]
    assert token["required"] is True
    assert token["usage_count"] == 2
    assert token["layers"] == ["config", "services"]
    # OPTIONAL_FLAG only ever read with a default => optional.
    assert by_name["OPTIONAL_FLAG"]["required"] is False
    # Required-first ordering: APP_TOKEN (required) precedes OPTIONAL_FLAG.
    assert [r["name"] for r in records] == ["APP_TOKEN", "OPTIONAL_FLAG"]
    # Usage records carry the repo-relative path + line, never a value.
    usage = token["usages"][0]
    assert usage["file"].startswith("disbot/")
    assert isinstance(usage["line"], int)


def test_records_carry_no_values_only_names_and_locations(mod, tmp_path):
    """The safety guarantee: a record exposes name + location keys, no value."""
    root = tmp_path / "disbot"
    root.mkdir()
    (root / "x.py").write_text('import os\nv = os.getenv("SECRET_KEY", "shh")\n', "utf-8")
    records = mod.scan_env_usage(scan_root=root, repo_root=tmp_path)
    assert records, "expected at least one record"
    record = records[0]
    assert set(record) == {"name", "required", "usage_count", "layers", "usages"}
    assert set(record["usages"][0]) == {"file", "line", "layer", "has_default"}
    # The default literal ("shh") must never appear anywhere in the serialised map.
    import json

    assert "shh" not in json.dumps(records)


def test_render_doc_is_a_badged_table_without_values(mod):
    records = [
        {
            "name": "APP_TOKEN",
            "required": True,
            "usage_count": 1,
            "layers": ["config"],
            "usages": [
                {"file": "disbot/config.py", "line": 9, "layer": "config",
                 "has_default": False},
            ],
        },
        {
            "name": "OPTIONAL_FLAG",
            "required": False,
            "usage_count": 1,
            "layers": ["services"],
            "usages": [
                {"file": "disbot/services/x.py", "line": 3, "layer": "services",
                 "has_default": True},
            ],
        },
    ]
    doc = mod.render_doc(records)
    # Badged so check_docs accepts it; generated-file marker present.
    assert "> **Status:** `living-ledger`" in doc.splitlines()[2]
    assert "GENERATED FILE" in doc
    # Required and optional both tabled; counts surfaced.
    assert "**2 variables** — 1 required · 1 optional." in doc
    assert "## Required" in doc and "## Optional" in doc
    assert "`APP_TOKEN`" in doc and "`disbot/config.py:9`" in doc
    assert "*(default)*" in doc  # the optional usage is marked


def test_committed_env_vars_doc_is_in_sync_with_the_scanner(mod):
    """The committed doc must match a fresh render (it is a generated artifact)."""
    doc_path = _REPO_ROOT / "docs" / "operations" / "env-vars.md"
    if not doc_path.exists():
        pytest.skip("env-vars.md not generated in this tree")
    expected = mod.render_doc(mod.scan_env_usage())
    actual = doc_path.read_text(encoding="utf-8")
    assert actual == expected, (
        "docs/operations/env-vars.md is stale — refresh with "
        "`python3.10 scripts/scan_env_usage.py --write-doc`"
    )


def test_scan_against_real_disbot_is_well_formed(mod):
    records = mod.scan_env_usage()
    assert len(records) >= 20  # the plan estimates ~36 vars
    names = {r["name"] for r in records}
    assert "DATABASE_URL" in names
    assert "OPENAI_API_KEY" in names
    for record in records:
        assert isinstance(record["name"], str)
        assert isinstance(record["required"], bool)
        assert record["usage_count"] == len(record["usages"])
    # DATABASE_URL is read without a default (utils/db/pool raises if absent).
    db = next(r for r in records if r["name"] == "DATABASE_URL")
    assert db["required"] is True
