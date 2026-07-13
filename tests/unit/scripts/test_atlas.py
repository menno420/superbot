"""Tests for ``scripts/atlas.py`` — the thin repo-wide architecture-atlas composer.

``test_coherent`` is the CI enforcement seam (Q-0151a): it fails the suite if the
composite index can't be built, a loaded extension lacks a source file, or the
delegated crosswalk guard drifts — no workflow edit needed. The rest pin the
composition (role enrichment, review-unit coverage, do-not-duplicate reuse).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "atlas.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("atlas_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def index(mod):
    return mod.build_index()


def test_coherent(mod, index):
    """The live repo composes cleanly: no hard coherence errors."""
    errors = mod.coherence_errors(index)
    assert errors == [], "\n".join(errors)


def test_no_orphans(mod, index):
    """Every source file classifies into a layer or is a known top-level module."""
    assert mod.orphans(index) == []


def test_index_is_substantial_and_classified(index):
    """Sanity: the roster covers the repo and every record carries a review unit."""
    assert len(index) > 400
    assert all(r.review_unit for r in index)
    # The known top-level modules are the only layer-less files.
    layerless = {r.module for r in index if r.layer is None}
    assert layerless <= {
        "bot1",
        "config",
        "control_api",
        "guild_lifecycle",
        "healthserver",
        "mining_write_api",
    }


def test_role_enrichment_from_crosswalk(index):
    """Role/backs/registered are joined from the extension crosswalk (PR #958)."""
    by_rel = {r.rel: r for r in index}
    maint = by_rel["disbot/cogs/health_maintenance_cog.py"]
    assert maint.role == "maintenance" and maint.backs == "diagnostic"
    mining = by_rel["disbot/cogs/mining_cog.py"]
    assert mining.role == "product_subsystem" and mining.registered is True
    paragon = by_rel["disbot/cogs/paragon_cog.py"]
    assert paragon.role == "specialized_surface" and paragon.backs == "btd6"


def test_missing_extension_file_is_flagged(mod, monkeypatch):
    """The guard catches an extension declared in the manifest with no source file."""
    real = mod.xwalk.initial_extensions()
    monkeypatch.setattr(mod.xwalk, "initial_extensions", lambda: [*real, "ghost_thing"])
    errors = mod._missing_extension_files()
    assert any("ghost_thing" in e for e in errors), errors


def test_full_render_carries_provenance(mod, index):
    rendered = mod.render_full(index)
    assert "GENERATED — NOT SOURCE OF TRUTH" in rendered
    assert "disbot/cogs/mining_cog.py" in rendered
    assert "_commit:_" in rendered


def test_is_a_composer_not_a_reimplementation(mod):
    """Do-not-duplicate: the atlas must source its facts from the sibling tools."""
    assert (
        hasattr(mod, "cmap") and hasattr(mod, "xwalk") and hasattr(mod, "_review_units")
    )
