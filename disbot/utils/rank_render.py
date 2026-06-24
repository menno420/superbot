"""Rank-card renderer — the single-user ``!rank`` card on the themeable engine.

Renders a member's rank standing (``!rank``) as a designed image — avatar
initials disc + name/subtitle, a grid of stat panels (rank position, level,
totals, coins…), and the level progress bar — instead of a plain text embed.
The sibling of :mod:`utils.profile_render`: same engine, a different feature
card.  Where the profile card is a fixed four-panel hero strip, the rank card
lays its panels out in a **grid** (up to six) so the "both" view's
XP-rank / level / total-XP / messages / coin-rank / coins all show at once.

Contract (identical to every other renderer): pure presentation inputs in,
``bytes | None`` out (``None`` = Pillow unavailable → the caller keeps its text
embed).  No Discord, no DB, no network — the caller resolves data and passes
plain values.  Layering: ``utils`` may import stdlib + discord only; this module
imports neither services/core/cogs nor Discord — it is pure rendering.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from utils.card_render import get_theme, initials, new_canvas

# Card geometry.  Fixed width; the height grows with the number of stat rows so
# a two-row ("both") card and a one-row ("coins") card both read cleanly.
_WIDTH = 900
_HEADER_H = 150
_MARGIN = 28
_COLS = 3
_COL_GAP = 18
_ROW_GAP = 16
_PANEL_H = 100
_GRID_TOP_PAD = 24
_PROG_H = 70
_FOOTER_H = 44


def render_rank_card(
    *,
    display_name: str,
    subtitle: str,
    stats: Sequence[tuple[str, str]],
    progress: tuple[str, float] | None = None,
    theme: str | None = None,
    footer: str = "SuperBot",
) -> bytes | None:
    """Render the single-user rank card.

    Parameters
    ----------
    display_name:
        The member's display name (header, ellipsised to fit).
    subtitle:
        A one-line context string under the name (e.g. ``"Demo Server · rank"``).
    stats:
        ``(label, value)`` headline panels, laid out in a 3-column grid (up to
        six are drawn; extras are ignored).
    progress:
        Optional ``(label, fraction)`` level-progress bar; ``fraction`` is
        clamped to ``[0, 1]`` by the engine.
    theme:
        A :data:`utils.card_render.THEMES` key; unknown/None → default skin.
    footer:
        Subtle bottom-left caption.

    Returns PNG bytes, or ``None`` when Pillow is unavailable.
    """
    panels = list(stats)[:6]
    cols = min(len(panels), _COLS) or 1
    rows = math.ceil(len(panels) / cols) if panels else 0

    grid_top = _HEADER_H + _GRID_TOP_PAD
    grid_h = rows * _PANEL_H + max(0, rows - 1) * _ROW_GAP
    prog_h = _PROG_H if progress is not None else 0
    height = grid_top + grid_h + prog_h + _FOOTER_H

    t = get_theme(theme)
    canvas = new_canvas(_WIDTH, height, t)
    if canvas is None:
        return None

    # Header band + identity (mirrors the profile hero card so the two single-
    # user cards share a visual language).
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

    # Stat-panel grid — left-aligned; the last row may hold fewer than `cols`.
    if panels:
        avail = _WIDTH - 2 * _MARGIN
        pw = (avail - _COL_GAP * (cols - 1)) // cols
        for i, (label, value) in enumerate(panels):
            col = i % cols
            row = i // cols
            px0 = _MARGIN + col * (pw + _COL_GAP)
            py0 = grid_top + row * (_PANEL_H + _ROW_GAP)
            canvas.panel((px0, py0, px0 + pw, py0 + _PANEL_H), radius=16)
            canvas.text(
                (px0 + 18, py0 + 16),
                label.upper(),
                size=18,
                color=t.subtle,
                max_width=pw - 36,
            )
            canvas.text(
                (px0 + 18, py0 + 44),
                value,
                size=38,
                bold=True,
                color=t.text,
                max_width=pw - 36,
            )

    # Level progress bar (when present).
    if progress is not None:
        label, fraction = progress
        by = height - _FOOTER_H - 30
        canvas.text((_MARGIN, by - 28), label, size=20, color=t.subtle)
        canvas.progress_bar(
            (_MARGIN, by, _WIDTH - _MARGIN, by + 22),
            fraction,
            fill=t.accent_alt,
        )

    # Footer.
    canvas.text(
        (_MARGIN, height - 32),
        footer,
        size=18,
        color=t.subtle,
    )

    return canvas.to_png()


__all__ = ["render_rank_card"]
