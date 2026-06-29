"""Tests for ``scripts/check_completion_ledger_parity.py`` — the registry↔ledger parity guard.

Two layers:

* the **pure core** (``analyze``) is driven with synthetic ``(reg, declared, links)`` inputs to
  exercise every violation class (A registry↔certs · B ledger↔files · C exclusion/allowlist) plus
  the clean baseline, with no disk access;
* one **live regression test** asserts the committed repo state (registry · ledger · certs) passes,
  so any real future parity break (a new registry subsystem with no cert, a renamed key, an orphan
  cert) fails this test in CI.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "check_completion_ledger_parity.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location(
        "check_completion_ledger_parity_ut",
        _SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# --- a minimal, internally-consistent synthetic world (mirrors the real shapes) ---
_REG = {
    "alpha",
    "beta",
    "gamma",
    "hub",
    "btd6",
}  # hub + btd6 stand in for excluded keys


def _clean(mod):
    """A consistent synthetic world: alpha/beta/gamma certifiable + the non-registry 'wiz'."""
    reg = set(_REG)
    declared = {"alpha": "alpha", "beta": "beta", "gamma": "gamma", "wiz": None}
    links = ["alpha", "beta", "gamma", "wiz"]
    return reg, declared, links


@pytest.fixture
def patched(mod, monkeypatch):
    """Point the guard's EXCLUDED/NON_REGISTRY_UNITS at the synthetic world."""
    monkeypatch.setattr(mod, "EXCLUDED", frozenset({"hub", "btd6"}))
    monkeypatch.setattr(mod, "NON_REGISTRY_UNITS", frozenset({"wiz"}))
    return mod


def test_clean_world_has_no_problems(patched):
    reg, declared, links = _clean(patched)
    assert patched.analyze(reg, declared, links) == []


def test_A_missing_cert_for_certifiable_key(patched):
    reg, declared, links = _clean(patched)
    del declared[
        "gamma"
    ]  # gamma is still a certifiable registry key but loses its cert
    links = [s for s in links if s != "gamma"]
    problems = patched.analyze(reg, declared, links)
    assert any(p.startswith("[A]") and "'gamma'" in p for p in problems)


def test_A_orphan_cert_declares_unknown_key(patched):
    reg, declared, links = _clean(patched)
    declared["ghost"] = "ghost"  # cert declares a key that is not in the registry
    links.append("ghost")
    problems = patched.analyze(reg, declared, links)
    assert any(
        p.startswith("[A]") and "ghost" in p and "not a registry key" in p
        for p in problems
    )


def test_A_orphan_cert_declares_excluded_key(patched):
    reg, declared, links = _clean(patched)
    declared["hub"] = "hub"  # a cert for an EXCLUDED routing-only hub
    links.append("hub")
    problems = patched.analyze(reg, declared, links)
    # surfaces under [A] (declares an excluded key) and/or [C] (excluded key carries a cert)
    assert any("hub" in p and "EXCLUDED" in p for p in problems)


def test_B_ledger_links_missing_file(patched):
    reg, declared, links = _clean(patched)
    links.append("phantom")  # a ledger row links a cert that is not on disk
    problems = patched.analyze(reg, declared, links)
    assert any(
        p.startswith("[B]") and "phantom" in p and "does not exist" in p
        for p in problems
    )


def test_B_duplicate_ledger_row(patched):
    reg, declared, links = _clean(patched)
    links.append("alpha")  # alpha linked twice
    problems = patched.analyze(reg, declared, links)
    assert any(
        p.startswith("[B]") and "alpha" in p and "2 times" in p for p in problems
    )


def test_B_unlinked_cert(patched):
    reg, declared, links = _clean(patched)
    links = [
        s for s in links if s != "beta"
    ]  # beta cert exists but no ledger row links it
    problems = patched.analyze(reg, declared, links)
    assert any(
        p.startswith("[B]") and "beta" in p and "no ledger row" in p for p in problems
    )


def test_C_typo_in_excluded_set(mod, monkeypatch):
    monkeypatch.setattr(mod, "EXCLUDED", frozenset({"hub", "btd6", "notakey"}))
    monkeypatch.setattr(mod, "NON_REGISTRY_UNITS", frozenset({"wiz"}))
    reg, declared, links = _clean(mod)
    problems = mod.analyze(reg, declared, links)
    assert any(
        p.startswith("[C]") and "notakey" in p and "not a live registry key" in p
        for p in problems
    )


def test_C_non_registry_cert_not_allowlisted(patched):
    reg, declared, links = _clean(patched)
    declared["sneaky"] = None  # a non-backticked cert that is not on NON_REGISTRY_UNITS
    links.append("sneaky")
    problems = patched.analyze(reg, declared, links)
    assert any(
        p.startswith("[C]") and "sneaky" in p and "NON_REGISTRY_UNITS" in p
        for p in problems
    )


def test_C_allowlisted_unit_missing_cert(patched):
    reg, declared, links = _clean(patched)
    del declared["wiz"]  # the documented non-registry unit loses its cert
    links = [s for s in links if s != "wiz"]
    problems = patched.analyze(reg, declared, links)
    assert any(p.startswith("[C]") and "wiz" in p and "no cert" in p for p in problems)


# --- live regression: the committed repo state must be parity-clean ---


def test_committed_repo_state_is_consistent(mod):
    problems = mod.check()
    assert problems == [], "completion ledger parity broke:\n" + "\n".join(problems)


def test_excluded_and_allowlist_are_disjoint(mod):
    """An EXCLUDED routing-only key and a NON_REGISTRY_UNITS allowlist key can't be the same name."""
    assert mod.EXCLUDED.isdisjoint(mod.NON_REGISTRY_UNITS)
