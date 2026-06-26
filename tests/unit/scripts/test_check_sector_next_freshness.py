"""check_sector_next_freshness flags ▶ Next pointers at shipped (historical) plans."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO = Path(__file__).parents[3]


def _load():
    spec = importlib.util.spec_from_file_location(
        "check_sector_next_freshness",
        _REPO / "scripts" / "check_sector_next_freshness.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


csf = _load()


# --------------------------------------------------------------------------- live
def test_live_sectors_have_no_shipped_next_pointer():
    """Ground truth (Q-0105): the real sector files pass after the S3 fix."""
    assert csf.run() == []


def test_main_exits_zero_and_reports_ok(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["check_sector_next_freshness.py"])
    assert csf.main() == 0
    assert "OK" in capsys.readouterr().out


# ------------------------------------------------------------------- section scope
_SECTOR = """\
# S9 — fixture

**Recently shipped (this sector):**
- A thing ([plan](../planning/done-plan.md)).

**▶ Next startable:**
- Build the live thing ([plan](../planning/live-plan.md)).

**Note:**
- trailing ([plan](../planning/note-plan.md)).
"""


def test_next_sections_isolates_only_the_next_block():
    sections = csf.next_sections(_SECTOR)
    assert len(sections) == 1
    body = sections[0]
    assert "live-plan.md" in body
    # Recently-shipped and the trailing Note must be outside the ▶ Next section.
    assert "done-plan.md" not in body
    assert "note-plan.md" not in body


def test_plan_link_extraction():
    assert csf._PLAN_LINK.findall("see ](../planning/foo-bar_2026.md) end") == [
        "foo-bar_2026.md",
    ]


# ----------------------------------------------------------------- finding logic
def _write_fixture(tmp_path, monkeypatch, sector_body: str, plans: dict[str, str]):
    sector_dir = tmp_path / "current-state"
    planning_dir = tmp_path / "planning"
    sector_dir.mkdir()
    planning_dir.mkdir()
    (sector_dir / "S9-fix.md").write_text(sector_body, encoding="utf-8")
    for name, status in plans.items():
        (planning_dir / name).write_text(
            f"# Plan\n\n> **Status:** `{status}` — fixture.\n", encoding="utf-8"
        )
    monkeypatch.setattr(csf, "SECTOR_DIR", sector_dir)
    monkeypatch.setattr(csf, "PLANNING_DIR", planning_dir)


def test_flags_next_pointer_to_historical_plan(tmp_path, monkeypatch):
    _write_fixture(
        tmp_path,
        monkeypatch,
        _SECTOR,
        {"live-plan.md": "historical", "done-plan.md": "historical"},
    )
    findings = csf.run()
    assert len(findings) == 1
    assert "live-plan.md" in findings[0]
    # The Recently-shipped historical link is NOT flagged (scope correctness).
    assert all("done-plan.md" not in f for f in findings)


def test_does_not_flag_buildable_plan(tmp_path, monkeypatch):
    _write_fixture(tmp_path, monkeypatch, _SECTOR, {"live-plan.md": "plan"})
    assert csf.run() == []


def test_missing_plan_file_is_not_flagged(tmp_path, monkeypatch):
    """An unreadable/absent plan yields status None — no false positive."""
    _write_fixture(tmp_path, monkeypatch, _SECTOR, {})
    assert csf.run() == []
