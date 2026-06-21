"""Tests for ``scripts/check_permission_overlap.py``.

Exercises the pure shadow-detection core: an ``allow`` rule whose matched command set
is fully contained in a broader ``ask``/``deny`` rule is flagged; the normal carve-out
direction (broad allow, narrow ask) is not.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "check_permission_overlap.py"


@pytest.fixture(scope="module")
def po():
    spec = importlib.util.spec_from_file_location("check_permission_overlap_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _shadows(po, perms):
    return [(s.allow_rule, s.blocker_rule, s.blocker_list) for s in po.find_shadows(perms)]


def test_parse_rule_glob_and_exact(po):
    g = po.parse_rule("Bash(git push --force*)")
    assert g is not None and g.is_glob and g.prefix == "git push --force"
    e = po.parse_rule("Bash(git push --force )")
    assert e is not None and not e.is_glob and e.prefix == "git push --force "


def test_parse_rule_skips_non_bash(po):
    assert po.parse_rule("Read") is None
    assert po.parse_rule("mcp__github__pull_request_read") is None
    assert po.parse_rule("Bash()") is None


def test_the_real_bug_is_flagged(po):
    """The exact #1211 residual: narrow allow shadowed by broad ask."""
    perms = {
        "allow": ["Bash(git push --force-with-lease*)"],
        "ask": ["Bash(git push --force*)"],
    }
    shadows = _shadows(po, perms)
    assert shadows == [
        ("Bash(git push --force-with-lease*)", "Bash(git push --force*)", "ask")
    ]


def test_precise_ask_rule_is_clean(po):
    """The semantics-independent fix: trailing-space ask no longer covers lease form."""
    perms = {
        "allow": ["Bash(git push --force-with-lease*)"],
        "ask": ["Bash(git push --force )", "Bash(git push --force *)"],
    }
    assert _shadows(po, perms) == []


def test_normal_carveout_not_flagged(po):
    """Broad allow + narrow ask is the intended exception pattern, not a shadow."""
    perms = {
        "allow": ["Bash(git push*)"],
        "ask": ["Bash(git push --force*)"],
    }
    assert _shadows(po, perms) == []


def test_deny_shadowing_allow_is_flagged(po):
    perms = {
        "allow": ["Bash(rm -rf /tmp/x*)"],
        "deny": ["Bash(rm -rf*)"],
    }
    shadows = _shadows(po, perms)
    assert shadows == [("Bash(rm -rf /tmp/x*)", "Bash(rm -rf*)", "deny")]


def test_exact_allow_under_glob_ask_is_flagged(po):
    perms = {
        "allow": ["Bash(git push --force-with-lease)"],
        "ask": ["Bash(git push --force*)"],
    }
    shadows = _shadows(po, perms)
    assert shadows and shadows[0][2] == "ask"


def test_unrelated_tools_do_not_overlap(po):
    perms = {
        "allow": ["Bash(ls*)", "Read", "Glob"],
        "ask": ["Bash(rm -rf*)"],
    }
    assert _shadows(po, perms) == []


def test_live_settings_is_clean(po):
    """The committed .claude/settings.json must have no shadowed allow rules."""
    import json

    settings = json.loads((_REPO_ROOT / ".claude" / "settings.json").read_text())
    assert _shadows(po, settings.get("permissions", {})) == []
