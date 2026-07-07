"""Tests for tools/check_amendments.py — the amendment-registry enforcer (P-9)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
_spec = importlib.util.spec_from_file_location(
    "check_amendments",
    REPO_ROOT / "tools" / "check_amendments.py",
)
ca = importlib.util.module_from_spec(_spec)
sys.modules["check_amendments"] = ca
_spec.loader.exec_module(ca)

_CORPUS = "spec_corpus:\n  - docs/planning/rebuild-design-spec-2026-07-02.md\n"


def _registry(amendments: str = "", refuted: str = "") -> str:
    return (
        "version: 1\n" + _CORPUS + "amendments:\n" + amendments + "refuted:\n" + refuted
    )


def test_live_registry_is_clean():
    problems = ca.check(ca.REGISTRY.read_text(encoding="utf-8"))
    assert problems == []


def test_gap_in_family_numbering_is_flagged():
    text = _registry(
        "  G-1: {name: A, status: pending-gate-0, spec_ref: null}\n"
        "  G-3: {name: B, status: pending-gate-0, spec_ref: null}\n",
    )
    problems = ca.check(text)
    assert any("not contiguous" in p and "G-2" in p for p in problems)


def test_duplicate_id_is_flagged():
    text = _registry(
        "  G-1: {name: A, status: pending-gate-0, spec_ref: null}\n"
        "  G-1: {name: B, status: pending-gate-0, spec_ref: null}\n",
    )
    assert any("duplicate id G-1" in p for p in ca.check(text))


def test_refuted_name_reuse_is_flagged():
    text = _registry(
        "  G-1: {name: LootTableSpec, status: pending-gate-0, spec_ref: null}\n",
        '  LootTableSpec: {reason: "not one family", source: "Lane B"}\n',
    )
    assert any("REFUTED name 'LootTableSpec'" in p for p in ca.check(text))


def test_in_spec_requires_resolvable_ref():
    text = _registry(
        '  G-1: {name: A, status: in-spec, spec_ref: "no-such-file.md"}\n',
    )
    assert any("not in the spec_corpus" in p for p in ca.check(text))


def test_in_spec_bad_section_ref_is_flagged():
    text = _registry(
        '  G-1: {name: A, status: in-spec, spec_ref: "§99.99"}\n',
    )
    assert any("§99.99 matches no numbered heading" in p for p in ca.check(text))


def test_in_spec_good_section_ref_passes():
    text = _registry(
        '  G-1: {name: A, status: in-spec, spec_ref: "§2.8"}\n',
    )
    assert ca.check(text) == []


def test_pending_with_spec_ref_is_flagged():
    text = _registry(
        '  G-1: {name: A, status: pending-gate-0, spec_ref: "§2.8"}\n',
    )
    assert any("must be null until its fold ships" in p for p in ca.check(text))


def test_unknown_status_is_flagged():
    text = _registry(
        "  G-1: {name: A, status: frozen, spec_ref: null}\n",
    )
    assert any("unknown status 'frozen'" in p for p in ca.check(text))
