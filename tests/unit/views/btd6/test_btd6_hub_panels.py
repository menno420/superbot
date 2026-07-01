"""BTD6 hub sub-panels (menu Layout B) — structure + wiring.

The persistent panel's category buttons delegate to
``hub_panels.open_category``; these pin that the category registry is
well-formed, aligns with the panel's category buttons, and that the
round-lookup modal parses input the way the builders expect.
"""

from __future__ import annotations

import discord
import pytest

from views.btd6 import hub_panels
from views.btd6.hub_panels import BTD6CategoryView, _CATEGORIES, _parse_round
from views.btd6.panel import BTD6PanelView


# --- _parse_round -------------------------------------------------------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("63", 63),
        ("1", 1),
        ("140", 140),
        ("r29", 29),  # r-shorthand
        ("  R100 ", 100),  # whitespace + capital R
        ("", None),  # blank → single-round / no-range
        (None, None),
        ("0", None),  # below range
        ("141", None),  # above range
        ("abc", None),  # non-numeric
        ("12.5", None),  # not an int
    ],
)
def test_parse_round(raw, expected):
    assert _parse_round(raw) == expected


# --- category registry --------------------------------------------------------


def test_category_registry_is_well_formed():
    for cat_id, (emoji, label, blurb, entries) in _CATEGORIES.items():
        assert isinstance(cat_id, str) and cat_id
        assert emoji and label and blurb
        assert entries, f"category {cat_id!r} has no entries"
        for entry in entries:
            e_emoji, e_label, style, handler = entry
            assert e_emoji and e_label
            assert isinstance(style, discord.ButtonStyle)
            assert callable(handler)


def test_panel_category_buttons_align_with_registry():
    # Every non-{ask, admin, nav} panel button opens a category that exists, and
    # every registered category has a panel button — no orphans either way.
    panel_ids = {
        c.custom_id
        for c in BTD6PanelView().children
        if getattr(c, "custom_id", None)
    }
    category_button_ids = panel_ids - {"btd6:ask", "btd6:admin", "nav:help"}
    expected = {f"btd6:{cat}" for cat in _CATEGORIES}
    assert category_button_ids == expected


def test_units_category_wires_the_three_unit_browsers():
    handlers = [entry[3] for entry in _CATEGORIES["units"][3]]
    assert hub_panels._open_towers in handlers
    assert hub_panels._open_heroes in handlers
    assert hub_panels._open_paragon in handlers


def test_rounds_category_covers_round_rbe_income_bloon():
    labels = [entry[1] for entry in _CATEGORIES["rounds"][3]]
    assert labels == ["Round / range", "RBE", "Income", "Bloon lookup"]


# --- BTD6CategoryView ---------------------------------------------------------


class _FakeUser:
    id = 42


def test_category_view_has_one_button_per_entry():
    entries = _CATEGORIES["units"][3]
    view = BTD6CategoryView(_FakeUser(), entries)
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    # No standard nav is attached (SUBSYSTEM unset), so it's exactly the entries.
    assert len(buttons) == len(entries)
    assert [b.label for b in buttons] == [e[1] for e in entries]


def test_category_view_is_invoker_locked():
    view = BTD6CategoryView(_FakeUser(), _CATEGORIES["maps"][3])
    # BaseView default public=False → only the invoker may interact.
    assert view._public is False
