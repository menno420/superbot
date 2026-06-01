"""Tests for utils.mining_render.

The layout math is tested unconditionally; the actual PNG rendering is
guarded by ``importorskip`` so the suite stays green whether or not the
optional Pillow dependency is installed.
"""

from __future__ import annotations

import pytest

from utils import mining_render as mr


def test_build_card_spec_colours_by_kind():
    rows = [("gold", 3), ("pickaxe", 1)]
    spec = mr.build_card_spec(
        "Inventory",
        rows,
        classify_kind=lambda n: "tool" if n == "pickaxe" else "resource",
    )
    assert spec.title == "Inventory"
    assert len(spec.rows) == 2
    by_label = {r.label: r for r in spec.rows}
    # Title-cased labels.
    assert "Gold" in by_label
    assert by_label["Pickaxe"].color == mr._KIND_COLOR["tool"]
    assert by_label["Gold"].color == mr._KIND_COLOR["resource"]


def test_build_card_spec_defaults_to_resource_colour_without_classifier():
    spec = mr.build_card_spec("Inv", [("widget", 1)])
    assert spec.rows[0].color == mr._KIND_COLOR["resource"]


def test_card_height_grows_with_rows():
    small = mr.build_card_spec("t", [("a", 1)])
    big = mr.build_card_spec("t", [("a", 1), ("b", 2), ("c", 3)])
    assert big.height > small.height


def test_card_height_handles_empty_rows():
    spec = mr.build_card_spec("empty", [])
    assert spec.height > 0  # must not divide-by-zero / go negative


def test_render_returns_bytes_or_none():
    spec = mr.build_card_spec("Inv", [("gold", 2)])
    result = mr.render_inventory_card(spec)
    # Contract: bytes when Pillow is present, None when it is not.
    assert result is None or isinstance(result, bytes)


def test_render_produces_png_when_pillow_present():
    pytest.importorskip("PIL")
    spec = mr.build_card_spec("Inv", [("gold", 2), ("diamond", 1)], footer="value: 24")
    data = mr.render_inventory_card(spec)
    assert isinstance(data, bytes)
    assert data[:8] == b"\x89PNG\r\n\x1a\n"  # PNG magic number
