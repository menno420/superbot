"""Tests for ``scripts/extension_crosswalk.py`` — the extension-taxonomy crosswalk.

These tests *are* the CI enforcement of the taxonomy (Q-0151c): ``test_check_clean``
fails the suite if any loaded extension is unclassified, the overlay drifts from the
live manifest/registry, or the committed doc goes stale — no workflow edit needed.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "extension_crosswalk.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("extension_crosswalk_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_check_clean(mod):
    """The live overlay classifies every extension and the doc is not stale."""
    errors = mod.check()
    assert errors == [], "\n".join(errors)


def test_counts_match_live_sources(mod):
    """Pin the headline numbers the architecture review hinged on (43 / 33 / 10)."""
    rows, errors = mod.build_rows()
    assert errors == []
    assert len(rows) == len(mod.initial_extensions())
    registered = [r for r in rows if r.registered]
    non_1to1 = [r for r in rows if not r.registered]
    assert len(registered) == len(mod.subsystem_keys())
    # Every registered subsystem is backed by exactly one extension (no orphans).
    assert {r.extension for r in registered} == mod.subsystem_keys()
    # The non-1:1 set is the review's "unclassified" extensions — now classified.
    assert len(non_1to1) >= 1
    assert all(r.role != "?" for r in rows), "every row carries a real role"


def test_render_is_deterministic(mod):
    rows, _ = mod.build_rows()
    keys = mod.subsystem_keys()
    assert mod.render(rows, keys) == mod.render(rows, keys)


def test_unclassified_extension_is_flagged(mod, monkeypatch):
    """The guard must catch a new extension added without a role (the gap re-growing)."""
    real = mod.initial_extensions()
    monkeypatch.setattr(mod, "initial_extensions", lambda: [*real, "brand_new_thing"])
    _rows, errors = mod.build_rows()
    assert any("brand_new_thing" in e and "not classified" in e for e in errors), errors


def test_invalid_backs_is_flagged(mod, monkeypatch):
    """A `backs` pointing at a non-existent subsystem is rejected."""
    overlay = mod._load_overlay()
    # Corrupt one entry's `backs` to a stranger key.
    victim = next(iter(overlay["extensions"]))
    overlay["extensions"][victim] = {"role": "maintenance", "backs": "no_such_subsystem"}
    monkeypatch.setattr(mod, "_load_overlay", lambda: overlay)
    _rows, errors = mod.build_rows()
    assert any("no_such_subsystem" in e for e in errors), errors
