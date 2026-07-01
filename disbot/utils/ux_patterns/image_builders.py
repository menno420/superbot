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

import math
import re

from utils.card_render import RGB, get_theme, new_canvas

# The welcome card graduated to a real feature; re-export the production
# renderer so the UX-lab gallery previews the exact card members receive.
from utils.welcome_render import render_welcome_card

# Both candidate cards draw on the shared engine's "midnight" skin — the
# dark-blurple palette these prototypes always used — so they share the one
# palette + font loader rather than re-declaring their own.
_THEME = "midnight"


_DEFAULT_LEADERBOARD_ROWS: tuple[tuple[str, float], ...] = (
    ("AstroFox", 13_370),
    ("BananaMage", 11_204),
    ("CinderWolf", 9_876),
    ("DuskRunner", 8_545),
    ("EmberLynx", 7_002),
)

# Podium tints for the top three ranks.  Gold rides the theme (a re-skin
# recolours it); silver/bronze are fixed metallics that read on every skin.
_SILVER: RGB = (198, 203, 209)
_BRONZE: RGB = (206, 140, 84)

# Row + column geometry.  A right-hand value column is *reserved* so the #1
# row's value can never overrun the canvas edge (the clipping bug in the
# screenshot), and the bar span lives between the name and value columns.
_LB_W = 760
_LB_PAD = 32
_LB_ROW_H = 64
_LB_TOP = 100
_LB_BAR_X0 = 220
_LB_VALUE_W = 160
_LB_BAR_X1 = _LB_W - _LB_PAD - _LB_VALUE_W
_LB_BAR_MAXW = _LB_BAR_X1 - _LB_BAR_X0
_LB_NAME_X = _LB_PAD + 46
_LB_NAME_MAX = _LB_BAR_X0 - _LB_NAME_X - 12

_MENTION_RE = re.compile(r"^<@!?\d+>$")


def _clean_name(name: str) -> str:
    """Neutralise a raw ``<@id>`` mention before it is baked into the image.

    ``member_display`` falls back to ``<@id>`` for a member who left the server
    or isn't cached; rendered as literal pixels that is unreadable (the
    ``<@1118…>`` rows in the screenshot).  Resolved names pass through
    untouched; an unresolved one becomes a neutral placeholder so the card
    stays clean.
    """
    return "unknown" if _MENTION_RE.match(name.strip()) else name


def _bar_fraction(score: float, top: float) -> float:
    """Outlier-safe bar length in ``[floor, 1]``.

    A linear ``score / top`` collapses the whole field under a single runaway
    leader — one 118k-XP member squashes nine sub-10k bars into invisible stubs
    (the motivating screenshot).  A square root compresses that lead so the rest
    of the board stays legible, and a floor guarantees even last place keeps a
    real bar.  The exact figure still rides in the value column, so the bar only
    has to convey rough standing, not precise magnitude.
    """
    if top <= 0 or score <= 0:
        return 0.0
    floor = 0.12
    return floor + (1.0 - floor) * math.sqrt(score / top)


def render_leaderboard_image(
    rows: tuple[tuple[str, float], ...] = _DEFAULT_LEADERBOARD_ROWS,
    *,
    title: str = "🏆 Top members",
    value_texts: tuple[str, ...] | None = None,
    theme: str | None = None,
) -> bytes | None:
    """Top-N ranked bars — the image alternative to the embed board.

    ``rows`` are ``(name, score)`` pairs (highest first); ``score`` drives the
    bar length via an outlier-safe scale (:func:`_bar_fraction`).  ``title``
    lets the live feature stamp the category ("🏆 XP Leaderboard"); emoji it
    can't draw are stripped by the engine.  ``value_texts``, when given,
    supplies the per-row figure drawn right-aligned in the reserved value column
    (e.g. ``"5W / 2L"``); when omitted the score is shown with thousands
    separators.  ``theme`` names the card skin (one of :data:`card_render.THEMES`);
    it defaults to this wing's dark-blurple ``midnight`` and falls back to the
    engine default on an unknown key, so the call can never break a render.
    Returns ``None`` when Pillow is unavailable so the caller keeps its embed
    fallback.
    """
    if not rows:  # empty board → let the caller post its embed-only empty state.
        return None
    canvas = new_canvas(
        _LB_W,
        _LB_TOP + _LB_ROW_H * len(rows),
        get_theme(theme or _THEME),
    )
    if canvas is None:  # Pillow unavailable → caller keeps the embed fallback.
        return None
    t = canvas.theme

    # Title band + accent underline (the card's header strip).
    canvas.text(
        (_LB_PAD, 30),
        title,
        size=36,
        bold=True,
        color=t.gold,
        max_width=_LB_W - 2 * _LB_PAD,
    )
    canvas.draw.rectangle((_LB_PAD, 84, _LB_W - _LB_PAD, 87), fill=t.accent)

    top = max((s for _, s in rows), default=0.0) or 1.0
    for i, (name, score) in enumerate(rows):
        cy = _LB_TOP + i * _LB_ROW_H + _LB_ROW_H // 2
        rank_color = (t.gold, _SILVER, _BRONZE)[i] if i < 3 else t.subtle
        bar_color = (t.gold, _SILVER, _BRONZE)[i] if i < 3 else t.accent

        # Rank number (podium-tinted for the top three) + display name.
        canvas.text(
            (_LB_PAD, cy),
            f"{i + 1}",
            size=28,
            bold=True,
            color=rank_color,
            anchor="lm",
        )
        canvas.text(
            (_LB_NAME_X, cy),
            _clean_name(name),
            size=24,
            color=t.text,
            max_width=_LB_NAME_MAX,
            anchor="lm",
        )

        # Bar — outlier-safe length; podium colour for the top three.
        width = int(_LB_BAR_MAXW * _bar_fraction(score, top))
        if width >= 6:
            canvas.draw.rounded_rectangle(
                (_LB_BAR_X0, cy - 15, _LB_BAR_X0 + width, cy + 15),
                radius=10,
                fill=bar_color,
            )

        # Value — right-aligned in its reserved column, so it never clips.
        value = (
            value_texts[i]
            if value_texts is not None and i < len(value_texts)
            else f"{score:,.0f}"
        )
        canvas.text(
            (_LB_W - _LB_PAD, cy),
            value,
            size=23,
            bold=i < 3,
            color=t.text,
            anchor="rm",
        )
    return canvas.to_jpeg(quality=88)


def render_event_poster(
    title: str = "Movie Night 🎬",
    when: str = "Friday · 20:00 CET",
    host: str = "AstroFox",
) -> bytes | None:
    """Event-poster candidate (the Q-0112 scheduler's visual upgrade)."""
    canvas = new_canvas(800, 420, get_theme(_THEME))
    if canvas is None:  # Pillow unavailable → caller keeps the embed fallback.
        return None
    t = canvas.theme
    # Panel-fill body (not the theme bg) with accent rails top and bottom.
    canvas.draw.rectangle((0, 0, 800, 420), fill=t.panel)
    canvas.draw.rectangle((0, 0, 800, 12), fill=t.accent)
    canvas.draw.rectangle((0, 408, 800, 420), fill=t.accent)
    canvas.text((48, 96), title, size=52, bold=True)
    canvas.text((50, 190), when, size=28, color=t.gold)
    canvas.text((50, 240), f"Hosted by {host}", size=28, color=t.subtle)
    canvas.text((50, 320), "RSVP with the buttons below ✅ ❔ ❌", size=28)
    return canvas.to_jpeg(quality=85)


__all__ = [
    "render_event_poster",
    "render_leaderboard_image",
    "render_welcome_card",  # re-exported from utils.welcome_render (feature home)
]
