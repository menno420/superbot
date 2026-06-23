"""PIL prototype builders for the UX Lab image wing.

Two *candidate* card renderers that don't exist as features yet — a
leaderboard image and an event poster — rendered entirely from sample data
with **no network**.  The welcome card is **no longer a prototype**: it
shipped as welcome phase 2 (Q-0110) and now lives in
:mod:`utils.welcome_render`; the gallery re-exports it from there so the
preview and the live feature share one renderer (one source of truth).

Same contract as ``utils/mining_render.py``: lazy PIL import, ``bytes |
None`` return (``None`` = Pillow unavailable → callers keep an embed
fallback), pure inputs in / bytes out.
"""

from __future__ import annotations

import io

# The welcome card graduated to a real feature; re-export the production
# renderer so the UX-lab gallery previews the exact card members receive.
from utils.welcome_render import render_welcome_card

# Shared sample palette (dark-theme friendly).
_BG = (24, 25, 31)
_PANEL = (32, 34, 42)
_ACCENT = (88, 101, 242)  # blurple
_TEXT = (235, 236, 240)
_SUBTLE = (148, 155, 164)
_GOLD = (240, 178, 50)


def _fonts(size_big: int, size_small: int):  # noqa: ANN202 — PIL lazy types
    """Best-effort (bold-big, regular-small) DejaVu pair.

    Delegates to the shared card engine — one font loader, not three.
    """
    from utils.card_render import dejavu_fonts

    return dejavu_fonts(size_big, size_small)


def render_leaderboard_image(
    rows: tuple[tuple[str, int], ...] = (
        ("AstroFox", 13_370),
        ("BananaMage", 11_204),
        ("CinderWolf", 9_876),
        ("DuskRunner", 8_545),
        ("EmberLynx", 7_002),
    ),
) -> bytes | None:
    """Top-N horizontal bars — the image alternative to the embed board."""
    try:
        from PIL import Image, ImageDraw  # lazy: degrade gracefully
    except Exception:  # noqa: BLE001
        return None
    img = Image.new("RGB", (720, 96 + 64 * len(rows)), _BG)
    draw = ImageDraw.Draw(img)
    big, small = _fonts(36, 24)
    draw.text((32, 24), "🏆 Top members", font=big, fill=_GOLD)
    top = rows[0][1] if rows else 1
    for i, (name, score) in enumerate(rows):
        y = 96 + i * 64
        width = int(420 * score / top)
        draw.rounded_rectangle(
            (200, y, 200 + width, y + 40),
            radius=8,
            fill=_ACCENT if i else _GOLD,
        )
        draw.text((32, y + 6), f"{i + 1}. {name}", font=small, fill=_TEXT)
        draw.text((210 + width, y + 6), f"{score:,}", font=small, fill=_SUBTLE)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def render_event_poster(
    title: str = "Movie Night 🎬",
    when: str = "Friday · 20:00 CET",
    host: str = "AstroFox",
) -> bytes | None:
    """Event-poster candidate (the Q-0112 scheduler's visual upgrade)."""
    try:
        from PIL import Image, ImageDraw  # lazy: degrade gracefully
    except Exception:  # noqa: BLE001
        return None
    img = Image.new("RGB", (800, 420), _PANEL)
    draw = ImageDraw.Draw(img)
    big, small = _fonts(52, 28)
    draw.rectangle((0, 0, 800, 12), fill=_ACCENT)
    draw.rectangle((0, 408, 800, 420), fill=_ACCENT)
    draw.text((48, 96), title, font=big, fill=_TEXT)
    draw.text((50, 190), when, font=small, fill=_GOLD)
    draw.text((50, 240), f"Hosted by {host}", font=small, fill=_SUBTLE)
    draw.text(
        (50, 320),
        "RSVP with the buttons below ✅ ❔ ❌",
        font=small,
        fill=_TEXT,
    )
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


__all__ = [
    "render_event_poster",
    "render_leaderboard_image",
    "render_welcome_card",  # re-exported from utils.welcome_render (feature home)
]
