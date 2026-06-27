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


def test_sector_record_startable_now_run_by_claude():
    block = (
        "### S2 — BTD6 · exec\n"
        "- **Dispatch:** executor **Claude-in-repo**\n"
        "- **Now:** **▶ go now** (foo)\n"
        "- **Next:** y\n"
    )
    rec = dm.sector_record("S2", "BTD6", block)
    assert rec["state"] == "startable"
    assert rec["startable_item"] == "go now"
    assert rec["source"] == "Now"
    assert rec["executor"] == "Claude-in-repo"


def test_sector_record_falls_through_to_next():
    block = (
        "### S1 — Bot · exec\n"
        "- **Dispatch:** executor **Claude-in-repo**\n"
        "- **Now:** **⛔ a** · **👤 b**\n"
        "- **Next:** the **▶ real thing** (foo)\n"
    )
    rec = dm.sector_record("S1", "Bot", block)
    assert rec["state"] == "now_blocked_fallthrough"
    assert rec["source"] == "Next"
    assert "real thing" in rec["startable_item"]


def test_sector_record_non_claude_executor_is_routed_away():
    block = (
        "### S5 — Operations · exec\n"
        "- **Dispatch:** executor **Hermes-VPS**\n"
        "- **Now:** **▶ tail the logs** (foo)\n"
    )
    rec = dm.sector_record("S5", "Operations", block)
    assert rec["state"] == "maintainer_or_hermes"
    assert rec["executor"] == "Hermes-VPS"


def test_sector_record_starving_when_no_startable():
    block = (
        "### S3 — AI · exec\n"
        "- **Dispatch:** executor **Claude-in-repo**\n"
        "- **Now:** **⛔ a**\n"
        "- **Next:** also ⛔ blocked\n"
    )
    rec = dm.sector_record("S3", "AI", block)
    assert rec["state"] == "starving"
    assert rec["startable_item"] is None


def test_build_records_covers_live_roadmap_sectors():
    text = (_REPO / "docs" / "roadmap.md").read_text(encoding="utf-8")
    records = dm.build_records(text)
    sectors = {r["sector"] for r in records}
    assert {"S1", "S2", "S3", "S4", "S5"} <= sectors
    for r in records:
        assert r["state"] in {
            "startable",
            "now_blocked_fallthrough",
            "maintainer_or_hermes",
            "starving",
        }


# --- unattended-fit dimension (#1285) -------------------------------------------------


def test_unattended_fit_parses_keyword_from_dispatch_line():
    block = (
        "### S1 — Bot · exec\n"
        "- **Dispatch:** `S1` (executor **Claude-in-repo**, unattended-fit **🟡 review**) · plan\n"
        "- **Now:** **▶ go** (foo)\n"
    )
    assert dm.unattended_fit(block) == "review"


def test_unattended_fit_none_when_tag_absent():
    block = (
        "### S2 — BTD6 · exec\n"
        "- **Dispatch:** executor **Claude-in-repo**\n"
        "- **Now:** **▶ go** (foo)\n"
    )
    assert dm.unattended_fit(block) is None


def test_unattended_fit_on_every_live_sector():
    text = (_REPO / "docs" / "roadmap.md").read_text(encoding="utf-8")
    for rec in dm.build_records(text):
        assert rec["unattended_fit"] in dm._FIT_KEYWORDS, rec["sector"]


def test_unattended_summary_ranks_auto_before_review():
    text = (_REPO / "docs" / "roadmap.md").read_text(encoding="utf-8")
    lines = dm.build_unattended_summary(text)
    joined = "\n".join(lines)
    # The live roadmap currently resolves at least one 🟢 auto lane (S2/S3/S4).
    assert "SELF-MERGEABLE now" in joined
    auto_idx = next(i for i, ln in enumerate(lines) if "SELF-MERGEABLE" in ln)
    review_idx = next(
        (i for i, ln in enumerate(lines) if "🟡 build PR" in ln), len(lines)
    )
    assert auto_idx < review_idx  # auto lanes are listed first


def test_unattended_summary_falls_back_when_no_auto_lane():
    # A roadmap where every buildable sector is 🟡 review → the nudge points at review/promote.
    text = (
        "## By sector\n"
        "### S1 — Bot · x\n"
        "- **Dispatch:** (executor **Claude-in-repo**, unattended-fit **🟡 review**) · y\n"
        "- **Now:** **▶ runtime thing** (foo)\n"
        "## End\n"
    )
    lines = dm.build_unattended_summary(text)
    joined = "\n".join(lines)
    assert "🟢 auto: none" in joined
    assert "promote an idea" in joined


# --- per-item offline-fit picks (read from the per-sector live-state files) -----------


def test_offline_item_label_strips_markup_and_links():
    line = "- `[offline]` **Fishing follow-ups** (turn-key) — remaining: x"
    assert dm._offline_item_label(line) == "Fishing follow-ups"
    line2 = "- `[offline]` **[botsite PR 2](../planning/x.md)** — serve the app"
    assert "botsite PR 2" in dm._offline_item_label(line2)


def test_sector_offline_pick_reads_live_files():
    """The real S1/S2/S3 sector files each surface a concrete [offline] item; S5 has none."""
    assert dm.sector_offline_pick("S1") is not None
    assert dm.sector_offline_pick("S2") is not None
    assert dm.sector_offline_pick("S3") is not None
    # S5 is the executor outlier — its ▶ Next items are all [owner], so no offline pick.
    assert dm.sector_offline_pick("S5") is None


def test_sector_offline_pick_none_for_unknown_sector():
    assert dm.sector_offline_pick("S9") is None


def test_next_block_stops_at_next_bold_heading():
    text = (
        "**▶ Next startable:**\n"
        "- `[offline]` an item.\n\n"
        "**In flight:**\n"
        "- `[offline]` an unrelated item.\n"
    )
    block = dm._next_block(text)
    assert "an item." in block and "unrelated" not in block


def test_unattended_summary_lists_concrete_offline_items():
    text = (_REPO / "docs" / "roadmap.md").read_text(encoding="utf-8")
    joined = "\n".join(dm.build_unattended_summary(text))
    assert "Concrete [offline] items" in joined
    # At least one real sector pick is surfaced.
    assert "S1:" in joined or "S2:" in joined or "S3:" in joined
