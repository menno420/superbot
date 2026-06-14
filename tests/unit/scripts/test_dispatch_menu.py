"""dispatch_menu resolves the live roadmap into a per-sector dispatch menu."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_REPO = Path(__file__).parents[3]


def _load():
    spec = importlib.util.spec_from_file_location(
        "dispatch_menu", _REPO / "scripts" / "dispatch_menu.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


dm = _load()


def test_live_menu_has_all_sectors_and_executors():
    text = (_REPO / "docs" / "roadmap.md").read_text(encoding="utf-8")
    joined = "\n".join(dm.build_menu(text))
    for sid in ("S1", "S2", "S3", "S4", "S5"):
        assert sid in joined
    assert "Claude-in-repo" in joined
    assert "Hermes-VPS" in joined  # S5 is the executor outlier


def test_first_startable_handles_inline_bold_tag():
    assert dm.first_startable("**▶ Layer B** (the absence-guard gate)") == "Layer B"


def test_first_startable_handles_separated_tag_and_link():
    got = dm.first_startable(
        "**▶** the owner's **[portable substrate-kit](x.md)** OSS arc — resume"
    )
    assert got is not None and "portable substrate-kit" in got


def test_first_startable_none_when_no_glyph():
    assert dm.first_startable("no startable tag here, just ⛔ and 👤") is None


def test_menu_line_startable_now():
    block = "head\n- **Now:** **▶ go now** (foo)\n- **Next:** y\n"
    assert dm.menu_line(block) == "▶ Now: go now"


def test_menu_line_blocked_now_falls_through_to_next():
    block = (
        "head\n"
        "- **Now:** **⛔ a** · **👤 b**\n"
        "- **Next:** the **▶ real thing** (foo)\n"
    )
    line = dm.menu_line(block)
    assert "Now blocked" in line and "real thing" in line


def test_menu_line_blocked_now_no_startable_anywhere():
    block = "head\n- **Now:** **⛔ a** · **👤 b**\n- **Next:** also ⛔ blocked\n"
    assert "no ▶ startable item" in dm.menu_line(block)


def test_build_menu_single_sector_filter():
    text = (_REPO / "docs" / "roadmap.md").read_text(encoding="utf-8")
    lines = dm.build_menu(text, only="S2")
    joined = "\n".join(lines)
    assert "S2" in joined
    assert "S1  Bot product" not in joined
