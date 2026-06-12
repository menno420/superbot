"""Tests for ``scripts/_review_units.py`` — the review-map path classifier."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "_review_units.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("review_units_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("path", "axis", "kind", "name"),
    [
        ("disbot/cogs/economy_cog.py", "A1", "slice", "economy"),
        ("disbot/cogs/economy/_helpers.py", "A1", "slice", "economy"),
        ("disbot/views/economy/hub.py", "A1", "slice", "economy"),
        ("disbot/views/base.py", "A1", "platform", "view-primitives"),
        ("disbot/views/navigation.py", "A1", "platform", "view-primitives"),
        ("disbot/core/runtime/event_bus.py", "A1", "platform", "runtime-core"),
        ("disbot/core/resources/discovery.py", "A1", "platform", "resources-core"),
        ("disbot/governance/writes.py", "A1", "platform", "governance"),
        ("disbot/utils/db/economy.py", "A1", "platform", "utils"),
        ("disbot/bot1.py", "A1", "platform", "entry-lifecycle"),
        ("disbot/migrations/070_x.sql", "A1", "platform", "entry-lifecycle"),
        ("disbot/services/economy_service.py", "A1", "service", "economy"),
        ("disbot/data/json/general_content.json", "A1", "runtime-data", ""),
        ("scripts/parse_gamedata.py", "A2", "data-pipeline", ""),
        ("data/btd6/towers.csv", "A2", "data-pipeline", ""),
        ("scripts/check_docs.py", "A3", "tooling", ""),
        ("tools/agent_context/build_pack.py", "A3", "tooling", ""),
        ("pyproject.toml", "A3", "config", ""),
        ("docs/roadmap.md", "A4", "docs", ""),
        ("tests/unit/cogs/test_economy_cog.py", "A5", "tests", ""),
    ],
)
def test_classify_path(mod, path, axis, kind, name):
    unit = mod.classify_path(path)
    assert unit.axis == axis
    assert unit.kind == kind
    assert unit.name == name


def test_classify_path_is_filesystem_free(mod):
    # A deleted/renamed path from a diff must still classify.
    unit = mod.classify_path("disbot/cogs/nonexistent_cog.py")
    assert unit.axis == "A1" and unit.kind == "slice" and unit.name == "nonexistent"


def test_changeset_single_slice(mod):
    v = mod.classify_changeset(
        [
            "disbot/cogs/economy_cog.py",
            "disbot/views/economy/hub.py",
            "tests/unit/cogs/test_economy_cog.py",
        ],
    )
    assert v.verdict == "single-slice"
    assert v.slices == {"economy"}


def test_changeset_multi_slice(mod):
    v = mod.classify_changeset(
        ["disbot/cogs/economy_cog.py", "disbot/cogs/mining_cog.py"],
    )
    assert v.verdict == "multi-slice"
    assert v.slices == {"economy", "mining"}


def test_changeset_platform_dominates(mod):
    v = mod.classify_changeset(
        ["disbot/core/runtime/event_bus.py", "disbot/cogs/economy_cog.py"],
    )
    assert v.verdict == "platform"
    assert "runtime-core" in v.platform_layers


def test_changeset_non_runtime(mod):
    v = mod.classify_changeset(["docs/roadmap.md", "scripts/check_docs.py"])
    assert v.verdict == "non-runtime"


def test_changeset_empty(mod):
    assert mod.classify_changeset([]).verdict == "empty"
