"""Welcome-card compositor (welcome phase 2, Q-0110) — pure, lazy-PIL.

The phase-2 image upgrade for the member greeting.  welcome v1 posts an embed;
when an operator opts the card in (``welcome_card_enabled``), the join handler
attaches a rendered banner alongside it.

Same contract as :mod:`utils.mining_render` / :mod:`utils.character_render`:

* **Pure inputs in, bytes out.**  No network, no I/O beyond the optional system
  font load — the avatar is a generated **initials disc** (the no-network
  fallback-silhouette path the platform-limits doc §4 says every real card
  needs anyway), so the card never blocks the join handler on an avatar fetch.
* **Lazy PIL import, ``bytes | None`` return.**  ``None`` means Pillow is
  unavailable; the caller keeps its embed fallback and posts no attachment.

This is the production home for the candidate that lived as a sample in
``utils/ux_patterns/image_builders.py`` (the UX-Lab gallery); that prototype
stays put for the lab, this is the feature renderer with real, parameterised
inputs.
"""

from __future__ import annotations

import io

# Card geometry (16:6 banner — comfortably within Discord's embed-image width).
_W, _H = 960, 360

# Palette (dark-theme friendly; mirrors the UX-Lab prototype so the gallery
# preview matches what actually posts).
_BG = (24, 25, 31)
_PANEL = (32, 34, 42)
_DEFAULT_ACCENT = (88, 101, 242)  # blurple
_TEXT = (235, 236, 240)
_SUBTLE = (148, 155, 164)

# The card filename callers attach the bytes under.
CARD_FILENAME = "welcome.png"


def _initials(name: str) -> str:
    """Up to two uppercase initials from a display name, never empty.

    Splits on whitespace so "Astro Fox" -> "AF"; a single token uses its first
    two letters ("AstroFox" -> "AS").  A blank/symbol-only name degrades to
    "?" so the disc always has a glyph.
    """
    parts = [p for p in name.split() if p]
    if len(parts) >= 2:
        letters = parts[0][:1] + parts[1][:1]
    elif parts:
        letters = parts[0][:2]
    else:
        letters = ""
    letters = "".join(ch for ch in letters if ch.isalnum()).upper()
    return letters or "?"


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


def _ellipsize(draw, text: str, font, max_width: int) -> str:  # noqa: ANN001
    """Trim ``text`` (appending an ellipsis) until it fits ``max_width`` px."""
    if draw.textlength(text, font=font) <= max_width:
        return text
    ellipsis = "…"
    trimmed = text
    while trimmed and draw.textlength(trimmed + ellipsis, font=font) > max_width:
        trimmed = trimmed[:-1]
    return (trimmed + ellipsis) if trimmed else ellipsis


def render_welcome_card(
    *,
    member_name: str = "AstroFox",
    server_name: str = "Demo Server",
    member_number: int = 1235,
    accent: tuple[int, int, int] | None = None,
) -> bytes | None:
    """Render the welcome banner: accent-ringed initials disc + greeting line.

    ``accent`` overrides the ring/divider colour (e.g. a member's top-role
    colour); ``None`` uses the blurple default.  Returns the JPEG/PNG bytes, or
    ``None`` when Pillow is unavailable so the caller keeps its embed fallback.
    """
    try:
        from PIL import Image, ImageDraw  # lazy: degrade gracefully
    except Exception:  # noqa: BLE001
        return None

    ring = accent or _DEFAULT_ACCENT
    img = Image.new("RGB", (_W, _H), _BG)
    draw = ImageDraw.Draw(img)
    big, small = _fonts(56, 30)

    # Avatar: accent ring + panel disc + initials (no-network silhouette path).
    cx, cy, r = 180, 180, 96
    draw.ellipse(
        (cx - r - 6, cy - r - 6, cx + r + 6, cy + r + 6),
        outline=ring,
        width=6,
    )
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=_PANEL)
    initials = _initials(member_name)
    box = draw.textbbox((0, 0), initials, font=big)
    tw, th = box[2] - box[0], box[3] - box[1]
    draw.text((cx - tw / 2, cy - th / 2 - box[1]), initials, font=big, fill=_TEXT)

    # Greeting block (right of the avatar), with both text lines width-clamped
    # so a long name/server never overruns the canvas edge.
    text_x, right_margin = 340, 920
    avail = right_margin - text_x
    greeting = _ellipsize(draw, f"Welcome, {member_name}!", big, avail)
    draw.text((text_x, 110), greeting, font=big, fill=_TEXT)
    sub = _ellipsize(
        draw,
        f"You are member #{member_number:,} of {server_name}",
        small,
        avail,
    )
    draw.text((text_x + 2, 196), sub, font=small, fill=_SUBTLE)
    draw.line((text_x, 260, right_margin - 20, 260), fill=ring, width=3)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


__all__ = ["CARD_FILENAME", "render_welcome_card"]
