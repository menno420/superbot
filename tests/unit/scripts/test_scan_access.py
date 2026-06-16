"""Tests for ``scripts/scan_access.py`` — the tier→visibility access-map scanner.

Loaded via ``importlib`` (the repo convention for ``scripts/`` modules). Pure
stdlib, so it runs in CI with no extra dependencies. The scanner is a static
mirror of ``disbot/utils/visibility_rules.get_subsystems_for_tier``; these
tests pin the mirrored rule (tier bucketing + internal/hidden exclusion).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "scan_access.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("scan_access_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SAMPLE_REGISTRY = '''
SUBSYSTEMS = {
    "games": {"display_name": "Games", "category": "games", "emoji": "🎮",
              "visibility_tier": "user"},
    "moderation": {"display_name": "Moderation", "category": "mod", "emoji": "🔨",
                   "visibility_tier": "moderator"},
    "diagnostics": {"display_name": "Diagnostics", "category": "admin", "emoji": "🩺",
                    "visibility_tier": "administrator"},
    "plumbing": {"display_name": "Plumbing", "category": "core",
                 "visibility_mode": "internal"},
    "secret": {"display_name": "Secret", "category": "core", "hidden": True},
    "weird": {"display_name": "Weird", "category": "x", "visibility_tier": "nonsense"},
}
'''


def _write_registry(tmp_path: Path) -> Path:
    path = tmp_path / "subsystem_registry.py"
    path.write_text(SAMPLE_REGISTRY, encoding="utf-8")
    return path


def test_scan_access_buckets_by_tier_and_excludes_internal(mod, tmp_path):
    access = mod.scan_access(_write_registry(tmp_path))
    by_tier = {t["tier"]: t for t in access["tiers"]}

    # internal + hidden are excluded; the unknown tier floors to "user".
    assert access["total_visible"] == 4
    assert access["internal_count"] == 2
    assert {s["key"] for s in by_tier["user"]["subsystems"]} == {"games", "weird"}
    assert {s["key"] for s in by_tier["moderator"]["subsystems"]} == {"moderation"}
    assert {s["key"] for s in by_tier["administrator"]["subsystems"]} == {"diagnostics"}

    # the ladder + its Discord-permission gates are present and ordered.
    assert [t["tier"] for t in access["tiers"]] == [
        "user", "trusted", "staff", "moderator", "administrator", "owner",
    ]
    assert by_tier["administrator"]["discord_permission"] == "administrator"
    assert by_tier["user"]["discord_permission"] is None


def test_scan_access_real_repo_matches_visibility_rule(mod):
    """The mirror must agree with the live rule it copies (verified mirror)."""
    sys.path.insert(0, str(_REPO_ROOT / "disbot"))
    try:
        from utils.visibility_rules import get_subsystems_for_tier
    finally:
        sys.path.pop(0)

    access = mod.scan_access()
    by_tier = {t["tier"]: t for t in access["tiers"]}

    # Everything visible at "user" must be exactly the rule's "user" set, and the
    # cumulative admin set must match the rule's admin set (the page's core claim).
    cumulative: set[str] = set()
    for tier in ("user", "trusted", "staff", "moderator", "administrator", "owner"):
        cumulative |= {s["key"] for s in by_tier[tier]["subsystems"]}
        assert cumulative == set(get_subsystems_for_tier(tier)), tier
