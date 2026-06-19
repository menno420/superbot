"""Tests for ``scripts/check_autospec_fidelity.py`` — the signature-blind-mock guard.

Loaded via ``importlib`` (the repo convention for ``scripts/`` modules, which are not a
package). Pure stdlib, so it runs in CI with no extra dependencies.

The guard's contract: flag a ``monkeypatch.setattr`` / ``patch.object`` that replaces a
``disbot.*`` callable with a *bare* ``Mock``/``MagicMock``/``AsyncMock`` (no
``spec=``/``autospec=``/``wraps=``) — the BTD6 ``search_facts(entity_key=…)`` crash class —
while leaving signature-faithful doubles and third-party targets alone. It is **warn-only
by default** (report mode exits 0) so it never reddens CI over existing tests.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "check_autospec_fidelity.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("check_autospec_fidelity_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# The canonical bad pattern: a real disbot DB facade replaced by a bare AsyncMock.
BAD = '''
from unittest.mock import AsyncMock
from disbot.utils.db import btd6_db

def test_x(monkeypatch):
    monkeypatch.setattr(btd6_db, "search_facts", AsyncMock(return_value=[]))
'''

# The good pattern: the same replacement, but signature-faithful via spec=.
GOOD_SPEC = '''
from unittest.mock import AsyncMock
from disbot.utils.db import btd6_db

def test_x(monkeypatch):
    monkeypatch.setattr(btd6_db, "search_facts", AsyncMock(spec=btd6_db.search_facts))
'''


# ---------------------------------------------------------------------------
# Core: flags the bad pattern, passes the good one.
# ---------------------------------------------------------------------------


def test_flags_bare_asyncmock_on_disbot_target(mod):
    findings = mod.scan_source(BAD, "tests/test_x.py")
    assert len(findings) == 1
    f = findings[0]
    assert f.target == "btd6_db"
    assert f.attr == "search_facts"
    assert f.mock == "AsyncMock"
    assert f.line == 6


def test_specced_mock_is_not_flagged(mod):
    assert mod.scan_source(GOOD_SPEC, "tests/test_x.py") == []


@pytest.mark.parametrize("kwarg", ["spec", "spec_set", "autospec", "wraps"])
def test_each_faithfulness_kwarg_suppresses_flag(mod, kwarg):
    src = (
        "from unittest.mock import MagicMock\n"
        "from disbot.utils.db import btd6_db\n"
        "def test_x(monkeypatch):\n"
        f'    monkeypatch.setattr(btd6_db, "search_facts", MagicMock({kwarg}=object))\n'
    )
    assert mod.scan_source(src, "tests/test_x.py") == []


@pytest.mark.parametrize("klass", ["Mock", "MagicMock", "AsyncMock", "NonCallableMock"])
def test_every_bare_mock_class_is_flagged(mod, klass):
    src = (
        f"from unittest.mock import {klass}\n"
        "from disbot.utils.db import btd6_db\n"
        "def test_x(monkeypatch):\n"
        f'    monkeypatch.setattr(btd6_db, "fn", {klass}())\n'
    )
    findings = mod.scan_source(src, "tests/test_x.py")
    assert len(findings) == 1
    assert findings[0].mock == klass


# ---------------------------------------------------------------------------
# Scope: only disbot.* targets, only the two setattr shapes.
# ---------------------------------------------------------------------------


def test_third_party_target_is_not_flagged(mod):
    # discord (not disbot) — a bare mock here is out of scope, no false positive.
    src = (
        "import discord\n"
        "from unittest.mock import AsyncMock\n"
        "def test_x(monkeypatch):\n"
        '    monkeypatch.setattr(discord, "utils", AsyncMock())\n'
    )
    assert mod.scan_source(src, "tests/test_x.py") == []


def test_unresolved_target_is_not_flagged(mod):
    # A target never imported (a local/fixture) cannot be proven to be disbot.* — skip.
    src = (
        "from unittest.mock import AsyncMock\n"
        "def test_x(monkeypatch, some_obj):\n"
        '    monkeypatch.setattr(some_obj, "fn", AsyncMock())\n'
    )
    assert mod.scan_source(src, "tests/test_x.py") == []


def test_bare_mock_as_plain_argument_is_not_flagged(mod):
    # An AsyncMock passed as a function arg (not a setattr replacement) is fine.
    src = (
        "from unittest.mock import AsyncMock\n"
        "from disbot.utils.db import btd6_db\n"
        "def test_x():\n"
        "    btd6_db.search_facts(AsyncMock())\n"
    )
    assert mod.scan_source(src, "tests/test_x.py") == []


def test_dotted_target_resolves_via_leading_local(mod):
    # ``counting_cog.db`` — leading local ``counting_cog`` imported from disbot => flag.
    src = (
        "from unittest.mock import AsyncMock\n"
        "from disbot.cogs import counting_cog\n"
        "def test_x(monkeypatch):\n"
        '    monkeypatch.setattr(counting_cog.db, "set_state", AsyncMock())\n'
    )
    findings = mod.scan_source(src, "tests/test_x.py")
    assert len(findings) == 1
    assert findings[0].target == "counting_cog.db"
    assert findings[0].attr == "set_state"


# ---------------------------------------------------------------------------
# patch.object shape.
# ---------------------------------------------------------------------------


def test_patch_object_with_bare_mock_is_flagged(mod):
    src = (
        "from unittest.mock import patch, AsyncMock\n"
        "from disbot.utils.db import btd6_db\n"
        "def test_x():\n"
        '    with patch.object(btd6_db, "search_facts", AsyncMock()):\n'
        "        pass\n"
    )
    findings = mod.scan_source(src, "tests/test_x.py")
    assert len(findings) == 1
    assert findings[0].target == "btd6_db"
    assert findings[0].attr == "search_facts"


def test_patch_object_with_autospec_kwarg_is_not_flagged(mod):
    src = (
        "from unittest.mock import patch, AsyncMock\n"
        "from disbot.utils.db import btd6_db\n"
        "def test_x():\n"
        '    with patch.object(btd6_db, "search_facts", AsyncMock(), autospec=True):\n'
        "        pass\n"
    )
    assert mod.scan_source(src, "tests/test_x.py") == []


# ---------------------------------------------------------------------------
# AST-mechanics edge cases (no crash, precise non-flags).
# ---------------------------------------------------------------------------


def test_qualified_mock_construction_is_flagged(mod):
    # ``mock.AsyncMock()`` (attribute form) is the same permissive double.
    src = (
        "import unittest.mock as mock\n"
        "from disbot.utils.db import btd6_db\n"
        "def test_x(monkeypatch):\n"
        '    monkeypatch.setattr(btd6_db, "fn", mock.AsyncMock())\n'
    )
    findings = mod.scan_source(src, "tests/test_x.py")
    assert len(findings) == 1
    assert findings[0].mock == "AsyncMock"


def test_double_star_kwargs_is_treated_as_possibly_faithful(mod):
    # ``AsyncMock(**opts)`` is opaque — could carry spec — so do not flag (stay quiet).
    src = (
        "from unittest.mock import AsyncMock\n"
        "from disbot.utils.db import btd6_db\n"
        "def test_x(monkeypatch, opts):\n"
        '    monkeypatch.setattr(btd6_db, "fn", AsyncMock(**opts))\n'
    )
    assert mod.scan_source(src, "tests/test_x.py") == []


def test_non_string_attr_is_skipped(mod):
    # A dynamic attr name (not a literal) cannot be reported — skip, no crash.
    src = (
        "from unittest.mock import AsyncMock\n"
        "from disbot.utils.db import btd6_db\n"
        "def test_x(monkeypatch, name):\n"
        "    monkeypatch.setattr(btd6_db, name, AsyncMock())\n"
    )
    assert mod.scan_source(src, "tests/test_x.py") == []


def test_two_arg_setattr_is_skipped(mod):
    # ``setattr(obj, value)`` (no attr string) has nothing to report — skip cleanly.
    src = (
        "from unittest.mock import AsyncMock\n"
        "from disbot.utils.db import btd6_db\n"
        "def test_x(monkeypatch):\n"
        "    monkeypatch.setattr(btd6_db, AsyncMock())\n"
    )
    assert mod.scan_source(src, "tests/test_x.py") == []


def test_import_alias_target_resolves(mod):
    # ``from disbot.x import y as z`` then setattr on ``z`` => resolves to disbot.
    src = (
        "from unittest.mock import AsyncMock\n"
        "from disbot.utils.db import btd6_db as db\n"
        "def test_x(monkeypatch):\n"
        '    monkeypatch.setattr(db, "search_facts", AsyncMock())\n'
    )
    findings = mod.scan_source(src, "tests/test_x.py")
    assert len(findings) == 1
    assert findings[0].target == "db"


def test_scan_source_tolerates_syntax_error(mod):
    assert mod.scan_source("def (:\n", "tests/bad.py") == []


# ---------------------------------------------------------------------------
# Tree scan + CLI contract.
# ---------------------------------------------------------------------------


def test_scan_tree_aggregates_and_sorts(mod, tmp_path):
    root = tmp_path / "tests"
    (root / "a").mkdir(parents=True)
    (root / "a" / "test_one.py").write_text(BAD, encoding="utf-8")
    (root / "a" / "test_two.py").write_text(GOOD_SPEC, encoding="utf-8")
    findings = mod.scan_tree(scan_root=root, repo_root=tmp_path)
    # Only the bad file contributes a finding; paths are repo-relative.
    assert len(findings) == 1
    assert findings[0].file == "tests/a/test_one.py"


def test_finding_serialisation_round_trips(mod):
    f = mod.scan_source(BAD, "tests/test_x.py")[0]
    d = f.as_dict()
    assert d == {
        "file": "tests/test_x.py",
        "line": 6,
        "target": "btd6_db",
        "attr": "search_facts",
        "mock": "AsyncMock",
    }
    assert "WARN" in f.display()


def test_main_report_mode_always_exits_zero(mod, tmp_path, capsys, monkeypatch):
    # Even with a known-bad file in scope, report mode is warn-only (exit 0).
    bad = tmp_path / "test_bad.py"
    bad.write_text(BAD, encoding="utf-8")
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    rc = mod.main(["--file", "test_bad.py"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "search_facts" in out
    assert "warn-only" in out


def test_main_strict_mode_fails_on_finding(mod, tmp_path, monkeypatch):
    bad = tmp_path / "test_bad.py"
    bad.write_text(BAD, encoding="utf-8")
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    assert mod.main(["--mode", "strict", "--file", "test_bad.py"]) == 1


def test_main_strict_mode_passes_when_clean(mod, tmp_path, monkeypatch):
    good = tmp_path / "test_good.py"
    good.write_text(GOOD_SPEC, encoding="utf-8")
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    assert mod.main(["--mode", "strict", "--file", "test_good.py"]) == 0


def test_main_json_mode_emits_findings_array(mod, tmp_path, capsys, monkeypatch):
    import json

    bad = tmp_path / "test_bad.py"
    bad.write_text(BAD, encoding="utf-8")
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    rc = mod.main(["--json", "--file", "test_bad.py"])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload[0]["attr"] == "search_facts"


def test_main_no_findings_message(mod, tmp_path, capsys, monkeypatch):
    good = tmp_path / "test_good.py"
    good.write_text(GOOD_SPEC, encoding="utf-8")
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    rc = mod.main(["--file", "test_good.py"])
    assert rc == 0
    assert "no signature-blind" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Live-tree smoke: the guard must run clean (exit 0) against the real tests/ tree,
# proving warn-only lands green without touching any existing test.
# ---------------------------------------------------------------------------


def test_runs_against_real_tests_tree_in_report_mode(mod):
    # scan_tree over the real tests/ must not raise; report-mode CLI exits 0.
    findings = mod.scan_tree()
    assert isinstance(findings, list)
    for f in findings:
        assert f.target and f.attr and f.mock
        assert f.line > 0
    # Warn-only default never reddens CI, regardless of how many it finds.
    assert mod.main([]) == 0
