"""check_sector_map validates the live 5-sector partition and catches drift."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO = Path(__file__).parents[3]


def _load():
    spec = importlib.util.spec_from_file_location(
        "check_sector_map", _REPO / "scripts" / "check_sector_map.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


csm = _load()

_MAP = "<!-- BEGIN sector-folio-map -->\n{body}\n<!-- END sector-folio-map -->"


def test_live_partition_is_clean():
    """The real repo passes every sector check (ground-truth verification, Q-0105)."""
    assert csm.run() == []


def test_main_exits_zero_and_reports_ok(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["check_sector_map.py"])
    assert csm.main() == 0
    assert "OK" in capsys.readouterr().out


def test_parse_folio_map_detects_double_home():
    text = _MAP.format(body="S1: ai, games\nS2: ai")
    mapping, errors = csm.parse_folio_map(text)
    assert mapping["games"] == "S1"
    assert any("double-homed" in e for e in errors)


def test_parse_folio_map_missing_block_is_an_error():
    _, errors = csm.parse_folio_map("no block here")
    assert any("missing" in e for e in errors)


def test_check_folio_homing_flags_orphan(monkeypatch):
    monkeypatch.setattr(csm, "folios_on_disk", lambda: {"ai", "btd6", "newthing"})
    errors = csm.check_folio_homing(_MAP.format(body="S1: ai\nS2: btd6"))
    assert any("newthing" in e and "not homed" in e for e in errors)


def test_check_folio_homing_flags_phantom(monkeypatch):
    monkeypatch.setattr(csm, "folios_on_disk", lambda: {"ai"})
    errors = csm.check_folio_homing(_MAP.format(body="S1: ai, ghost"))
    assert any("ghost" in e and "phantom" in e for e in errors)


def test_check_folio_homing_clean(monkeypatch):
    monkeypatch.setattr(csm, "folios_on_disk", lambda: {"ai", "btd6"})
    assert csm.check_folio_homing(_MAP.format(body="S1: ai\nS2: btd6")) == []


_FIT = ", unattended-fit **🟢 auto**"


def _roadmap(
    executor_s1: str = "(executor **Claude-in-repo**" + _FIT + ")",
) -> str:
    blocks = []
    for sid in ("S1", "S2", "S3", "S4", "S5"):
        ex = executor_s1 if sid == "S1" else "(executor **Claude-in-repo**" + _FIT + ")"
        blocks.append(
            f"### {sid} — Name · *x*\n"
            f"- **Now:** **▶** do a thing\n"
            f"- **Dispatch:** `{sid}` {ex} · plan = x\n"
        )
    return "## By sector\n" + "\n".join(blocks) + "\n## Cross-horizon snapshot\n"


def test_roadmap_convention_clean():
    assert csm.check_roadmap_convention(_roadmap()) == []


def test_roadmap_convention_flags_missing_executor():
    errors = csm.check_roadmap_convention(_roadmap(executor_s1="· plan only"))
    assert any("S1" in e and "executor" in e for e in errors)


def test_roadmap_convention_flags_untagged_now():
    road = _roadmap().replace("- **Now:** **▶** do a thing", "- **Now:** plain text", 1)
    errors = csm.check_roadmap_convention(road)
    assert any("startability tag" in e for e in errors)


def test_roadmap_convention_flags_missing_unattended_fit():
    # An executor but no unattended-fit tag on the Dispatch line (#1285).
    road = _roadmap(executor_s1="(executor **Claude-in-repo**)")
    errors = csm.check_roadmap_convention(road)
    assert any("S1" in e and "unattended-fit" in e for e in errors)


def test_sector_presence_flags_missing_sector():
    road = _roadmap().replace("### S5 — Name · *x*", "### Sx — Name · *x*")
    errors = csm.check_sector_presence(_MAP.format(body="S1: ai"), road)
    assert any("S5" in e for e in errors)
