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

from utils.card_render import RGB, CardCanvas, get_theme, mix, new_canvas

# Card geometry — a wide banner that sits above the menu embed.
_WIDTH = 960
_HEIGHT = 240

# The styles the renderer knows how to draw. The presentation catalogue must not
# offer a card whose ``style`` is not in here (guarded by a test).
KNOWN_STYLES = ("banner", "gradient", "minimal", "spotlight")


def _draw_background(canvas: CardCanvas, style: str, accent: RGB) -> None:
    """Paint the card background for the chosen preset style (in place).

    Drawn through the engine's :class:`~utils.card_render.CardCanvas` (the
    ``midnight`` skin = the dark-blurple palette this card always used) plus
    the shared :func:`~utils.card_render.mix` blend, so the role-menu and
    welcome cards read as one visual system off one code path.
    """
    draw = canvas.draw
    t = canvas.theme
    if style == "gradient":
        # Vertical accent → dark gradient (one horizontal line per row).
        top = mix(accent, t.bg, 0.35)
        for y in range(_HEIGHT):
            draw.line(((0, y), (_WIDTH, y)), fill=mix(top, t.bg, y / max(1, _HEIGHT - 1)))
    elif style == "spotlight":
        # Dark panel with a bold accent block down the left third.
        draw.rectangle((0, 0, _WIDTH, _HEIGHT), fill=t.panel)
        draw.rectangle((0, 0, 18, _HEIGHT), fill=accent)
        draw.rectangle((_WIDTH - 280, 0, _WIDTH, _HEIGHT), fill=mix(accent, t.panel, 0.78))
    elif style == "minimal":
        # Flat channel-blending dark; the accent shows only as a thin underline.
        draw.rectangle((0, 0, _WIDTH, _HEIGHT), fill=t.bg)
    else:  # "banner" (default) — dark panel + a left accent bar.
        draw.rectangle((0, 0, _WIDTH, _HEIGHT), fill=t.panel)
        draw.rectangle((0, 0, 14, _HEIGHT), fill=accent)


def render_role_menu_card(
    *,
    style: str = "banner",
    title: str = "Pick your roles",
    overlay: str | None = None,
    accent: RGB | None = None,
) -> bytes | None:
    """Render a role-menu banner card → PNG bytes, or ``None`` without Pillow.

    ``style`` selects a preset background treatment (see :data:`KNOWN_STYLES`; an
    unknown value falls back to ``banner``). ``title`` is the headline; ``overlay``
    an optional second line. ``accent`` (the menu theme's colour) tints the chrome,
    defaulting to blurple. Pure / no-network — callers fall back to embed-only when
    this returns ``None``.
    """
    canvas = new_canvas(_WIDTH, _HEIGHT, get_theme("midnight"))
    if canvas is None:  # Pillow unavailable → caller keeps the embed fallback.
        return None

    style = style if style in KNOWN_STYLES else "banner"
    rgb = accent or canvas.theme.accent
    _draw_background(canvas, style, rgb)

    # Text column: leave room for the left accent bar / block on the side styles.
    text_x = 60 if style in ("banner", "gradient") else 70
    text_max = _WIDTH - text_x - 80
    heading = title or "Pick your roles"

    if overlay:
        canvas.text((text_x, 78), heading, size=58, bold=True, max_width=text_max)
        canvas.text(
            (text_x + 2, 158),
            overlay,
            size=30,
            color=canvas.theme.subtle,
            max_width=text_max,
        )
    else:
        # Centre the single line vertically when there is no overlay.
        canvas.text((text_x, 96), heading, size=58, bold=True, max_width=text_max)

    if style == "minimal":
        # The accent is a thin underline beneath the heading rather than a panel.
        canvas.draw.line((text_x, 170, _WIDTH - 80, 170), fill=rgb, width=4)

    return canvas.to_png()


__all__ = ["KNOWN_STYLES", "render_role_menu_card"]
