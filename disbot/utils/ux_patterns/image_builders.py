"""PIL prototype builders for the UX Lab image wing.

Three *candidate* card renderers that don't exist as features yet — the
welcome card (the Q-0110 phase-2 preview), a leaderboard image, and an
event poster — rendered entirely from sample data with **no network**: the
avatar is a generated initials disc (the fallback-silhouette path every
real implementation needs anyway, per the platform-limits doc §4).

Same contract as ``utils/mining_render.py``: lazy PIL import, ``bytes |
None`` return (``None`` = Pillow unavailable → callers keep an embed
fallback), pure inputs in / bytes out.
"""

from __future__ import annotations

import io

# Shared sample palette (dark-theme friendly).
_BG = (24, 25, 31)
_PANEL = (32, 34, 42)
_ACCENT = (88, 101, 242)  # blurple
_TEXT = (235, 236, 240)
_SUBTLE = (148, 155, 164)
_GOLD = (240, 178, 50)


def _fonts(size_big: int, size_small: int):  # noqa: ANN202 — PIL lazy types
    """Best-effort font pair; Pillow's default bitmap font as the fallback."""
    from PIL import ImageFont  # lazy: optional at import time

    big: ImageFont.FreeTypeFont | ImageFont.ImageFont
    small: ImageFont.FreeTypeFont | ImageFont.ImageFont
    try:
        big = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            size_big,
        )
        small = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            size_small,
        )
    except Exception:  # noqa: BLE001 — font availability is environmental
        big = ImageFont.load_default()
        small = ImageFont.load_default()
    return big, small


def _initials_disc(
    draw,
    *,
    cx: int,
    cy: int,
    r: int,
    initials: str,
    font,
) -> None:  # noqa: ANN001
    """The no-network avatar: accent ring + initials disc."""
    draw.ellipse(
        (cx - r - 6, cy - r - 6, cx + r + 6, cy + r + 6),
        outline=_ACCENT,
        width=6,
    )
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=_PANEL)
    box = draw.textbbox((0, 0), initials, font=font)
    tw, th = box[2] - box[0], box[3] - box[1]
    draw.text((cx - tw / 2, cy - th / 2 - box[1]), initials, font=font, fill=_TEXT)


def render_welcome_card(
    member_name: str = "AstroFox",
    server_name: str = "Demo Server",
    member_number: int = 1235,
) -> bytes | None:
    """The Q-0110 phase-2 candidate: avatar disc + greeting + member count."""
    try:
        from PIL import Image, ImageDraw  # lazy: degrade gracefully
    except Exception:  # noqa: BLE001
        return None
    img = Image.new("RGB", (960, 360), _BG)
    draw = ImageDraw.Draw(img)
    big, small = _fonts(56, 30)
    _initials_disc(
        draw,
        cx=180,
        cy=180,
        r=96,
        initials=member_name[:2].upper(),
        font=big,
    )
    draw.text((340, 110), f"Welcome, {member_name}!", font=big, fill=_TEXT)
    draw.text(
        (342, 196),
        f"You are member #{member_number} of {server_name}",
        font=small,
        fill=_SUBTLE,
    )
    draw.line((340, 260, 900, 260), fill=_ACCENT, width=3)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


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
