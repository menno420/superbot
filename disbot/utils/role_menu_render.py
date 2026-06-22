"""Role-menu banner-card renderer — the optional PR-6 header image (plan §4.6d).

A role menu can carry an optional **banner/header image** attached above its
embed. This is the sibling of :mod:`utils.welcome_render`: same contract —
**lazy PIL import**, ``bytes | None`` return (``None`` = Pillow unavailable →
the menu degrades to embed-only), pure inputs in / bytes out, **no network**.

The card is decorative chrome rendered entirely from the menu's own config (a
preset *style*, the menu title, an optional overlay line, and the theme's accent
colour) — it never fetches anything, so it cannot block or fail on a round-trip.
The preset *catalogue* (which styles exist + their labels) lives in
:mod:`utils.role_menu_presentation` (pure data); this module owns the drawing.
"""

from __future__ import annotations

import io

# Shared card palette (dark-theme friendly) — mirrors welcome_render so the two
# card families read as one visual system.
_BG = (24, 25, 31)
_PANEL = (32, 34, 42)
_TEXT = (235, 236, 240)
_SUBTLE = (148, 155, 164)
_DEFAULT_ACCENT = (88, 101, 242)  # blurple

# Card geometry — a wide banner that sits above the menu embed.
_WIDTH = 960
_HEIGHT = 240

# The styles the renderer knows how to draw. The presentation catalogue must not
# offer a card whose ``style`` is not in here (guarded by a test).
KNOWN_STYLES = ("banner", "gradient", "minimal", "spotlight")


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


def _fit(draw, text: str, font, max_width: int) -> str:  # noqa: ANN001
    """Ellipsise ``text`` until it fits within ``max_width`` px (welcome_render rule)."""
    if draw.textlength(text, font=font) <= max_width:
        return text
    ellipsis = "…"
    while text and draw.textlength(text + ellipsis, font=font) > max_width:
        text = text[:-1]
    return (text + ellipsis) if text else ellipsis


def _mix(
    a: tuple[int, int, int],
    b: tuple[int, int, int],
    t: float,
) -> tuple[int, int, int]:
    """Linear blend of two RGB colours at fraction ``t`` (0 → a, 1 → b)."""
    return (
        round(a[0] + (b[0] - a[0]) * t),
        round(a[1] + (b[1] - a[1]) * t),
        round(a[2] + (b[2] - a[2]) * t),
    )


def _draw_background(
    img,
    draw,
    style: str,
    accent: tuple[int, int, int],
) -> None:  # noqa: ANN001
    """Paint the card background for the chosen preset style (in place)."""
    if style == "gradient":
        # Vertical accent → dark gradient (one horizontal line per row).
        top = _mix(accent, _BG, 0.35)
        for y in range(_HEIGHT):
            draw.line(
                ((0, y), (_WIDTH, y)),
                fill=_mix(top, _BG, y / max(1, _HEIGHT - 1)),
            )
    elif style == "spotlight":
        # Dark panel with a bold accent block down the left third.
        draw.rectangle((0, 0, _WIDTH, _HEIGHT), fill=_PANEL)
        draw.rectangle((0, 0, 18, _HEIGHT), fill=accent)
        draw.rectangle(
            (_WIDTH - 280, 0, _WIDTH, _HEIGHT),
            fill=_mix(accent, _PANEL, 0.78),
        )
    elif style == "minimal":
        # Flat channel-blending dark; the accent shows only as a thin underline.
        draw.rectangle((0, 0, _WIDTH, _HEIGHT), fill=_BG)
    else:  # "banner" (default) — dark panel + a left accent bar.
        draw.rectangle((0, 0, _WIDTH, _HEIGHT), fill=_PANEL)
        draw.rectangle((0, 0, 14, _HEIGHT), fill=accent)


def render_role_menu_card(
    *,
    style: str = "banner",
    title: str = "Pick your roles",
    overlay: str | None = None,
    accent: tuple[int, int, int] | None = None,
) -> bytes | None:
    """Render a role-menu banner card → PNG bytes, or ``None`` without Pillow.

    ``style`` selects a preset background treatment (see :data:`KNOWN_STYLES`; an
    unknown value falls back to ``banner``). ``title`` is the headline; ``overlay``
    an optional second line. ``accent`` (the menu theme's colour) tints the chrome,
    defaulting to blurple. Pure / no-network — callers fall back to embed-only when
    this returns ``None``.
    """
    try:
        from PIL import Image, ImageDraw  # lazy: degrade gracefully
    except Exception:  # noqa: BLE001
        return None

    style = style if style in KNOWN_STYLES else "banner"
    rgb = accent or _DEFAULT_ACCENT
    img = Image.new("RGB", (_WIDTH, _HEIGHT), _BG)
    draw = ImageDraw.Draw(img)
    _draw_background(img, draw, style, rgb)

    big, small = _fonts(58, 30)
    # Text column: leave room for the left accent bar / block on the side styles.
    text_x = 60 if style in ("banner", "gradient") else 70
    text_max = _WIDTH - text_x - 80
    heading = _fit(draw, title or "Pick your roles", big, text_max)

    if overlay:
        sub = _fit(draw, overlay, small, text_max)
        draw.text((text_x, 78), heading, font=big, fill=_TEXT)
        draw.text((text_x + 2, 158), sub, font=small, fill=_SUBTLE)
    else:
        # Centre the single line vertically when there is no overlay.
        draw.text((text_x, 96), heading, font=big, fill=_TEXT)

    if style == "minimal":
        # The accent is a thin underline beneath the heading rather than a panel.
        draw.line((text_x, 170, _WIDTH - 80, 170), fill=rgb, width=4)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


__all__ = ["KNOWN_STYLES", "render_role_menu_card"]
