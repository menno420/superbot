"""check_startability_tags asserts each sector ▶ Next block carries an offline-fit tag."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO = Path(__file__).parents[3]


def _load():
    spec = importlib.util.spec_from_file_location(
        "check_startability_tags",
        _REPO / "scripts" / "check_startability_tags.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cst = _load()


def test_live_sector_files_are_clean():
    """The real repo passes (ground-truth verification, Q-0105)."""
    assert cst.run() == []


def test_main_exits_zero_and_reports_ok(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["check_startability_tags.py"])
    assert cst.main() == 0
    assert "OK" in capsys.readouterr().out


def _block(body: str) -> str:
    return f"# S9 — test\n\n{body}\n"


def test_recognized_tag_passes(tmp_path):
    path = tmp_path / "S9-test.md"
    path.write_text(
        _block("**▶ Next startable:**\n- `[offline]` do a thing.\n"),
        encoding="utf-8",
    )
    assert cst.check_file(path) == []


def test_missing_tag_fails(tmp_path):
    """A ▶ Next block with no offline-fit tag is flagged — the drift the guard exists for."""
    path = tmp_path / "S9-test.md"
    path.write_text(
        _block("**▶ Next startable:**\n- do an untagged thing.\n"),
        encoding="utf-8",
    )
    errors = cst.check_file(path)
    assert errors and "no offline-fit tag" in errors[0]


def test_missing_next_heading_fails(tmp_path):
    path = tmp_path / "S9-test.md"
    path.write_text(
        _block("**Recently shipped:**\n- shipped a thing.\n"), encoding="utf-8"
    )
    errors = cst.check_file(path)
    assert errors and "no '**▶ Next" in errors[0]


def test_each_recognized_tag_is_accepted(tmp_path):
    for tag in cst.RECOGNIZED_TAGS:
        path = tmp_path / "S9-test.md"
        path.write_text(
            _block(f"**▶ Next startable:**\n- `{tag}` an item.\n"),
            encoding="utf-8",
        )
        assert cst.check_file(path) == [], tag


def test_block_ends_at_next_section_heading(tmp_path):
    """A tag in a *sibling* section after ▶ Next does not satisfy the ▶ Next block."""
    path = tmp_path / "S9-test.md"
    path.write_text(
        _block(
            "**▶ Next startable:**\n- an untagged item.\n\n"
            "**In flight:**\n- `[offline]` an unrelated tagged item.\n",
        ),
        encoding="utf-8",
    )
    errors = cst.check_file(path)
    assert errors and "no offline-fit tag" in errors[0]


def test_legend_line_does_not_terminate_the_block(tmp_path):
    """The italic ``*(legend…)*`` line under the heading stays inside the block."""
    path = tmp_path / "S9-test.md"
    path.write_text(
        _block(
            "**▶ Next startable:**\n*(offline-fit tags — see the map.)*\n"
            "- `[needs-live-bot]` an item.\n",
        ),
        encoding="utf-8",
    )
    assert cst.check_file(path) == []


def test_s4_is_exempt(tmp_path):
    """S4 (docs/reconciliation sector) is exempt — its ▶ Next is a cadence-gated pass."""
    path = tmp_path / "S4-docs.md"
    path.write_text(
        _block("**▶ Next:**\n- next reconciliation pass at the next 30-PR band.\n"),
        encoding="utf-8",
    )
    assert cst.sector_id(path) == "S4"
    assert cst.check_file(path) == []


def test_sector_id_extracts_the_id():
    assert cst.sector_id(Path("S2-btd6.md")) == "S2"
    assert cst.sector_id(Path("S5-ops.md")) == "S5"


def test_live_real_sector_files_are_all_tagged():
    """Every non-exempt live sector file individually carries a tag (not just run() aggregate)."""
    for path in cst.sector_files():
        if cst.sector_id(path) in cst.EXEMPT_SECTORS:
            continue
        assert cst.check_file(path) == [], path.name
