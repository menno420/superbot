"""Render a Contested Territory hex map to a PNG.

Pillow is an **optional** dependency: this module lazy-imports it and
:func:`render_ct_map` returns ``None`` when it is absent, so importing the
module never breaks the bot and callers fall back to a text browser. The
layout math (axial hex → pixel, image bounds) is pure and runs regardless
of whether Pillow is installed; only the final pixel-pushing needs it.

Pure ``utils`` module — no service/data imports. The caller (a view) is
responsible for turning live tile rows into :class:`MapTile` records,
including each tile's colour bucket and short label, so this module never
needs the BTD6 data layer.
"""

from __future__ import annotations

import io
import math
from dataclasses import dataclass

# Colour buckets by tile kind. RGB tuples ready for Pillow.
KIND_COLORS: dict[str, tuple[int, int, int]] = {
    "relic": (245, 200, 70),
    "banner": (95, 145, 225),
    "team": (110, 200, 135),
    "regular": (85, 90, 105),
    "unknown": (70, 72, 84),
}
_DEFAULT_COLOR = (70, 72, 84)
_BG = (22, 24, 30)
_OUTLINE = (28, 30, 38)
_TITLE_COLOR = (235, 235, 240)
_LABEL_COLOR = (20, 20, 26)
_CENTER_RING = (240, 240, 245)

_HEX_SIZE = 26  # circumradius of one tile, px
_PADDING = 22
_HEADER = 34
_LEGEND_H = 26


@dataclass(frozen=True)
class MapTile:
    """One CT tile positioned in axial hex coordinates.

    ``kind`` keys into :data:`KIND_COLORS`; ``label`` is a short string
    (relic abbreviation, ≤4 chars) drawn centred on relic tiles.
    """

    q: int
    r: int
    kind: str
    label: str = ""
    is_center: bool = False


def _axial_to_pixel(q: int, r: int, size: int) -> tuple[float, float]:
    """Pointy-top axial → pixel centre (relative to the grid origin)."""
    x = size * math.sqrt(3) * (q + r / 2)
    y = size * 1.5 * r
    return x, y


def _hex_corners(cx: float, cy: float, size: int) -> list[tuple[float, float]]:
    """Six pointy-top corners around ``(cx, cy)``."""
    pts: list[tuple[float, float]] = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        pts.append((cx + size * math.cos(angle), cy + size * math.sin(angle)))
    return pts


def _layout(
    tiles: list[MapTile],
    size: int,
) -> tuple[dict[int, tuple[float, float]], int, int]:
    """Map tile index → pixel centre (already offset into the image) + canvas size."""
    raw = [_axial_to_pixel(t.q, t.r, size) for t in tiles]
    if not raw:
        return {}, _PADDING * 2, _HEADER + _PADDING * 2 + _LEGEND_H
    min_x = min(x for x, _ in raw) - size
    max_x = max(x for x, _ in raw) + size
    min_y = min(y for _, y in raw) - size
    max_y = max(y for _, y in raw) + size
    grid_w = max_x - min_x
    grid_h = max_y - min_y
    width = int(grid_w + _PADDING * 2)
    height = int(grid_h + _HEADER + _LEGEND_H + _PADDING * 2)
    off_x = _PADDING - min_x
    off_y = _HEADER + _PADDING - min_y
    centres = {i: (x + off_x, y + off_y) for i, (x, y) in enumerate(raw)}
    return centres, width, height


def render_ct_map(
    tiles: list[MapTile],
    *,
    title: str,
    size: int = _HEX_SIZE,
) -> bytes | None:
    """Render ``tiles`` to PNG bytes, or ``None`` when Pillow is unavailable."""
    if not tiles:
        return None
    try:
        from PIL import Image, ImageDraw  # lazy: optional dependency
    except Exception:  # noqa: BLE001 — any import failure → graceful no-op
        return None

    centres, width, height = _layout(tiles, size)
    img = Image.new("RGB", (width, height), _BG)
    draw = ImageDraw.Draw(img)

    draw.text((_PADDING, _PADDING // 2), title, fill=_TITLE_COLOR)

    for i, tile in enumerate(tiles):
        cx, cy = centres[i]
        color = KIND_COLORS.get(tile.kind, _DEFAULT_COLOR)
        draw.polygon(_hex_corners(cx, cy, size), fill=color, outline=_OUTLINE)
        if tile.is_center:
            draw.ellipse(
                (cx - size * 0.4, cy - size * 0.4, cx + size * 0.4, cy + size * 0.4),
                outline=_CENTER_RING,
                width=2,
            )
        if tile.label:
            _draw_centered(draw, cx, cy, tile.label)

    _draw_legend(draw, width, height)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def _draw_centered(draw, cx: float, cy: float, text: str) -> None:
    try:
        bbox = draw.textbbox((0, 0), text)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except Exception:  # noqa: BLE001 — very old Pillow without textbbox
        tw, th = len(text) * 6, 11
    draw.text((cx - tw / 2, cy - th / 2), text, fill=_LABEL_COLOR)


def _draw_legend(draw, width: int, height: int) -> None:
    items = [
        ("Relic", "relic"),
        ("Banner", "banner"),
        ("Team", "team"),
        ("Regular", "regular"),
    ]
    x = _PADDING
    y = height - _LEGEND_H + 4
    for label, kind in items:
        draw.rectangle((x, y, x + 14, y + 14), fill=KIND_COLORS[kind], outline=_OUTLINE)
        draw.text((x + 18, y + 2), label, fill=_TITLE_COLOR)
        x += 18 + 8 * len(label) + 22


def pillow_available() -> bool:
    """True when Pillow can be imported (image rendering is live)."""
    try:
        import PIL  # noqa: F401

        return True
    except Exception:  # noqa: BLE001
        return False


__all__ = ["KIND_COLORS", "MapTile", "render_ct_map", "pillow_available"]
