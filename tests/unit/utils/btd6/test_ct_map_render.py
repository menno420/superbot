"""CT hex-map renderer (utils.btd6.ct_map_render).

Layout math is pure and always runs; the PNG path is exercised only when
Pillow is installed (it ships in requirements, so CI covers it), and the
no-Pillow path degrades to None.
"""

from __future__ import annotations

import sys
from pathlib import Path

_DISBOT = Path(__file__).parents[4] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from utils.btd6.ct_map_render import (  # noqa: E402
    KIND_COLORS,
    MapTile,
    _layout,
    pillow_available,
    render_ct_map,
)

_PNG_MAGIC = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])


def _sample_tiles() -> list[MapTile]:
    return [
        MapTile(0, 0, "relic", "ABI", is_center=True),
        MapTile(-7, 7, "banner"),
        MapTile(1, -3, "relic", "CT"),
        MapTile(3, 0, "team"),
        MapTile(-2, 2, "regular"),
    ]


def test_kind_colors_cover_buckets():
    for kind in ("relic", "banner", "team", "regular", "unknown"):
        assert kind in KIND_COLORS


def test_layout_is_deterministic_and_bounded():
    tiles = _sample_tiles()
    centres, w, h = _layout(tiles, 26)
    assert len(centres) == len(tiles)
    # Every centre sits inside the canvas.
    for cx, cy in centres.values():
        assert 0 <= cx <= w
        assert 0 <= cy <= h


def test_empty_returns_none():
    assert render_ct_map([], title="x") is None


def test_render_png_when_pillow_present():
    out = render_ct_map(_sample_tiles(), title="Contested Territory - test")
    if pillow_available():
        assert isinstance(out, bytes)
        assert out[:8] == _PNG_MAGIC
    else:  # pragma: no cover - depends on env
        assert out is None
