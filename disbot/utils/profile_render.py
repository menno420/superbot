"""Profile hero-card renderer — the first feature card on the themeable engine.

Renders ``/myprofile`` as a designed image (avatar disc + name/subtitle, a row
of stat panels, an optional engagement progress bar, themed frame) instead of a
plain text embed.  This is the proof that :mod:`utils.card_render` is a real
template engine: the whole card is theme-driven, so a different skin is one
argument away.

Contract: pure presentation inputs in, ``bytes | None`` out (``None`` = Pillow
unavailable → the view keeps its text embed).  No Discord, no DB, no network —
the caller resolves data and passes plain values, exactly like
:mod:`utils.welcome_render`.
"""

from __future__ import annotations

from collections.abc import Sequence

from utils.card_render import get_theme, initials, new_canvas

# Fixed card geometry — a 16:7-ish banner that reads well as a Discord embed
# image on both desktop and mobile.
_WIDTH = 900
_HEIGHT = 400
_HEADER_H = 150
_MARGIN = 28


def render_profile_card(
    *,
    display_name: str,
    subtitle: str,
    stats: Sequence[tuple[str, str]],
    progress: tuple[str, float] | None = None,
    theme: str | None = None,
    footer: str = "SuperBot",
) -> bytes | None:
    """Render the profile hero card.

    Parameters
    ----------
    display_name:
        The member's display name (drawn in the header, ellipsised to fit).
    subtitle:
        A one-line context string under the name (e.g. ``"Demo Server · profile"``).
    stats:
        Up to four ``(label, value)`` headline panels, laid out evenly.
    progress:
        Optional ``(label, fraction)`` engagement bar; ``fraction`` is clamped.
    theme:
        A :data:`utils.card_render.THEMES` key; unknown/None → default skin.
    footer:
        Subtle bottom-left caption.

    Returns PNG bytes, or ``None`` when Pillow is unavailable.
    """
    t = get_theme(theme)
    canvas = new_canvas(_WIDTH, _HEIGHT, t)
    if canvas is None:
        return None

    # Header band + identity.
    canvas.header_band(_HEADER_H)
    canvas.draw.rectangle((0, _HEADER_H - 4, _WIDTH, _HEADER_H), fill=t.accent)

    disc_cx, disc_cy, disc_r = 92, _HEADER_H // 2, 52
    canvas.initials_disc(
        (disc_cx, disc_cy),
        disc_r,
        initials(display_name),
        size=42,
    )

    text_x = disc_cx + disc_r + 32
    text_max = _WIDTH - text_x - _MARGIN
    canvas.text(
        (text_x, 42),
        display_name,
        size=46,
        bold=True,
        max_width=text_max,
    )
    canvas.text(
        (text_x, 98),
        subtitle,
        size=24,
        color=t.subtle,
        max_width=text_max,
    )

    # Stat panels — evenly split across the content width (max four).
    panels = list(stats)[:4]
    if panels:
        gap = 18
        avail = _WIDTH - 2 * _MARGIN
        pw = (avail - gap * (len(panels) - 1)) // len(panels)
        py0 = _HEADER_H + 26
        ph = 108
        for i, (label, value) in enumerate(panels):
            px0 = _MARGIN + i * (pw + gap)
            canvas.panel((px0, py0, px0 + pw, py0 + ph), radius=16)
            canvas.text(
                (px0 + 18, py0 + 18),
                label.upper(),
                size=18,
                color=t.subtle,
                max_width=pw - 36,
            )
            canvas.text(
                (px0 + 18, py0 + 46),
                value,
                size=40,
                bold=True,
                color=t.text,
                max_width=pw - 36,
            )

    # Engagement progress bar.
    if progress is not None:
        label, fraction = progress
        by = _HEIGHT - 78
        canvas.text((_MARGIN, by - 30), label, size=20, color=t.subtle)
        canvas.progress_bar(
            (_MARGIN, by, _WIDTH - _MARGIN, by + 22),
            fraction,
            fill=t.accent_alt,
        )

    # Footer.
    canvas.text(
        (_MARGIN, _HEIGHT - 32),
        footer,
        size=18,
        color=t.subtle,
    )

    return canvas.to_png()


__all__ = ["render_profile_card"]
