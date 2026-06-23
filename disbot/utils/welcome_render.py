"""Welcome greeting-card renderer — the welcome phase-2 image (Q-0110).

The production home for the join greeting card promoted from the UX-lab
prototype (``utils/ux_patterns/image_builders.render_welcome_card``, which now
delegates here so the gallery preview and the live feature share one source of
truth).

Same contract as :mod:`utils.mining_render` / :mod:`utils.character_render`:
**lazy PIL import**, ``bytes | None`` return (``None`` = Pillow unavailable →
the welcome service keeps its embed-only fallback), pure inputs in / bytes out
— **no network**.  The avatar is a generated initials disc (the
fallback-silhouette path, per the platform-limits doc §4): rendering never
fetches the member's real avatar, so the card is content-free and cannot block
or fail on a CDN round-trip.  The real avatar still rides the embed thumbnail.
"""

from __future__ import annotations

import io

# Shared card palette (dark-theme friendly) — mirrors the Discord blurple set.
_BG = (24, 25, 31)
_PANEL = (32, 34, 42)
_ACCENT = (88, 101, 242)  # blurple
_TEXT = (235, 236, 240)
_SUBTLE = (148, 155, 164)
_GOLD = (240, 178, 50)

# Card geometry.
_WIDTH = 960
_HEIGHT = 360


def _fonts(size_big: int, size_small: int):  # noqa: ANN202 — PIL lazy types
    """Best-effort (bold-big, regular-small) DejaVu pair.

    Delegates to the shared card engine so the font loader lives in exactly one
    place (was triplicated across the renderers).
    """
    from utils.card_render import dejavu_fonts

    return dejavu_fonts(size_big, size_small)


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


def _initials(name: str) -> str:
    """First two alphanumerics of the display name, upper-cased (``?`` if none)."""
    letters = [c for c in name if c.isalnum()]
    return ("".join(letters[:2]) or "?").upper()


def _fit(draw, text: str, font, max_width: int) -> str:  # noqa: ANN001
    """Truncate ``text`` with an ellipsis until it fits within ``max_width`` px.

    Discord names and server names are unbounded, so a long one would run off
    the right edge of the fixed-width card.  This clamps any string to the
    drawable area, ellipsising the overflow.
    """
    if draw.textlength(text, font=font) <= max_width:
        return text
    ellipsis = "…"
    while text and draw.textlength(text + ellipsis, font=font) > max_width:
        text = text[:-1]
    return (text + ellipsis) if text else ellipsis


def render_welcome_card(
    member_name: str = "AstroFox",
    server_name: str = "Demo Server",
    member_number: int = 1235,
) -> bytes | None:
    """Render the join greeting card: avatar disc + greeting + member number.

    Pure / no-network; returns JPEG bytes, or ``None`` when Pillow is absent so
    callers fall back to the embed-only greeting.  The defaults make it a
    self-contained gallery sample (the UX-lab preview calls it bare).
    """
    try:
        from PIL import Image, ImageDraw  # lazy: degrade gracefully
    except Exception:  # noqa: BLE001
        return None
    img = Image.new("RGB", (_WIDTH, _HEIGHT), _BG)
    draw = ImageDraw.Draw(img)
    big, small = _fonts(56, 30)
    _initials_disc(
        draw,
        cx=180,
        cy=180,
        r=96,
        initials=_initials(member_name),
        font=big,
    )
    # Text column: x=340 to the right margin — clamp both lines so an unbounded
    # member/server name can never run off the card edge.
    text_x = 340
    text_max = _WIDTH - text_x - 60
    greeting = _fit(draw, f"Welcome, {member_name}!", big, text_max)
    subtitle = _fit(
        draw,
        f"You are member #{member_number:,} of {server_name}",
        small,
        text_max,
    )
    draw.text((text_x, 110), greeting, font=big, fill=_TEXT)
    draw.text((text_x + 2, 196), subtitle, font=small, fill=_SUBTLE)
    draw.line((text_x, 260, _WIDTH - 60, 260), fill=_ACCENT, width=3)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


__all__ = ["render_welcome_card"]
