"""Tests for ``scripts/check_plan_homing.py`` — the plan-homing guard.

The guard reasons over docs only; these tests feed it synthetic plan/routing files in a tmp
tree (no live docs, no network) and assert the homed-vs-unhomed split and the helpers.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "check_plan_homing.py"


@pytest.fixture(scope="module")
def ph():
    spec = importlib.util.spec_from_file_location("check_plan_homing_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write(path: Path, badge: str | None) -> Path:
    body = f"# {path.stem}\n\n"
    if badge is not None:
        body += f"> **Status:** `{badge}` — synthetic\n"
    path.write_text(body, encoding="utf-8")
    return path


def test_badge_extracts_token(ph):
    assert ph._badge("> **Status:** `plan` — buildable spec") == "plan"
    assert ph._badge("> **Status:** `living-ledger`") == "living-ledger"
    assert ph._badge("no badge here") is None


def test_live_plans_only_returns_plan_badge(ph, tmp_path):
    planning = tmp_path / "planning"
    planning.mkdir()
    _write(planning / "alpha-plan.md", "plan")
    _write(planning / "beta-plan.md", "historical")
    _write(planning / "gamma-plan.md", "reference")
    _write(planning / "delta-plan.md", None)
    _write(planning / "README.md", "living-ledger")  # the index is never in scope

    names = {p.name for p in ph.live_plans(planning)}
    assert names == {"alpha-plan.md"}


def test_linked_basenames_matches_any_relative_prefix(ph, tmp_path):
    routing = tmp_path / "roadmap.md"
    routing.write_text(
        "See [A](planning/a-plan.md) and [B](../planning/b-plan.md) and [C](c-plan.md#sec).\n"
        "Bare prose mention of d-plan.md is NOT a link. [doc](notes.txt) is not markdown.\n",
        encoding="utf-8",
    )
    linked = ph._linked_basenames([routing])
    assert linked == {"a-plan.md", "b-plan.md", "c-plan.md"}
    assert "d-plan.md" not in linked  # prose name-drop without link syntax


def test_build_report_splits_homed_and_unhomed(ph, tmp_path, monkeypatch):
    planning = tmp_path / "planning"
    planning.mkdir()
    homed = _write(planning / "homed-plan.md", "plan")
    _write(planning / "orphan-plan.md", "plan")  # linked from nowhere

    roadmap = tmp_path / "roadmap.md"
    roadmap.write_text("Active: [homed](planning/homed-plan.md)\n", encoding="utf-8")

    monkeypatch.setattr(ph, "routing_docs", lambda: [roadmap])
    monkeypatch.setattr(ph, "REPO_ROOT", tmp_path)

    report = ph.build_report(planning)
    assert report.plan_count == 2
    assert report.homed == ("planning/homed-plan.md",)
    assert report.unhomed == ("planning/orphan-plan.md",)
    assert report.ok is False
    assert homed.name in {Path(h).name for h in report.homed}


def test_build_report_ok_when_all_homed(ph, tmp_path, monkeypatch):
    planning = tmp_path / "planning"
    planning.mkdir()
    _write(planning / "only-plan.md", "plan")
    roadmap = tmp_path / "roadmap.md"
    roadmap.write_text("[x](planning/only-plan.md)\n", encoding="utf-8")

    monkeypatch.setattr(ph, "routing_docs", lambda: [roadmap])
    monkeypatch.setattr(ph, "REPO_ROOT", tmp_path)

    report = ph.build_report(planning)
    assert report.ok is True
    assert report.unhomed == ()


def test_strict_exit_code_on_unhomed(ph, tmp_path, monkeypatch):
    planning = tmp_path / "planning"
    planning.mkdir()
    _write(planning / "orphan-plan.md", "plan")
    monkeypatch.setattr(ph, "routing_docs", lambda: [])
    monkeypatch.setattr(ph, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(ph, "PLANNING_DIR", planning)

    assert ph.main(["--strict"]) == 1
    assert ph.main([]) == 0  # report-only default never blocks


def test_live_repo_plans_are_all_homed(ph):
    """Guard the real tree: every live `plan` doc in this repo is currently homed.

    This is the regression value — if a future plan lands unrouted, this fails. If it ever
    fails legitimately (a deliberately-parked draft), home it or adjust the routing allow-list.
    """
    report = ph.build_report()
    assert report.unhomed == (), f"unhomed live plans: {report.unhomed}"
