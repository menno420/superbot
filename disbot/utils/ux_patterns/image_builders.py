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

from utils.card_render import get_theme, new_canvas

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


def render_leaderboard_image(
    rows: tuple[tuple[str, float], ...] = _DEFAULT_LEADERBOARD_ROWS,
    *,
    title: str = "🏆 Top members",
    value_texts: tuple[str, ...] | None = None,
) -> bytes | None:
    """Top-N horizontal bars — the image alternative to the embed board.

    ``rows`` are ``(name, score)`` pairs (highest first); ``score`` only
    drives the bar width.  ``title`` lets the live feature stamp the
    category ("🏆 XP Leaderboard").  ``value_texts``, when given, supplies
    the per-row label drawn at each bar's end (e.g. ``"5W / 2L"``) so a
    category whose statistic isn't a bare count still reads correctly;
    when omitted the score is shown formatted with thousands separators.
    Returns ``None`` when Pillow is unavailable so the caller keeps its
    embed fallback.
    """
    if not rows:  # empty board → let the caller post its embed-only empty state.
        return None
    canvas = new_canvas(720, 96 + 64 * len(rows), get_theme(_THEME))
    if canvas is None:  # Pillow unavailable → caller keeps the embed fallback.
        return None
    t = canvas.theme
    canvas.text((32, 24), title, size=36, bold=True, color=t.gold, max_width=656)
    top = rows[0][1] or 1
    for i, (name, score) in enumerate(rows):
        y = 96 + i * 64
        width = int(420 * score / top) if top else 0
        if width > 0:
            canvas.draw.rounded_rectangle(
                (200, y, 200 + width, y + 40),
                radius=8,
                fill=t.accent if i else t.gold,
            )
        canvas.text((32, y + 6), f"{i + 1}. {name}", size=24, max_width=160)
        value = (
            value_texts[i]
            if value_texts is not None and i < len(value_texts)
            else f"{score:,.0f}"
        )
        canvas.text((210 + width, y + 6), value, size=24, color=t.subtle)
    return canvas.to_jpeg(quality=85)


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
