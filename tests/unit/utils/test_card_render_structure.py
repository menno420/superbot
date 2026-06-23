"""Render-structure ("golden") tests for the themeable card engine.

The byte-level tests in ``test_card_render.py`` / ``test_profile_render.py`` only
assert "returns PNG bytes / doesn't crash" — a **layout** regression (a panel
shifting, a bar overflowing, a theme colour swapped) passes them silently. These
tests close that gap.

Rather than commit reference PNGs (notoriously fragile across font/Pillow
versions and anti-aliasing), they sample **solid-fill regions** of the rendered
image — the header band, panels, the progress bar's filled vs. empty halves, and
the background — at coordinates known to be away from text, and assert the pixel
equals the theme's declared colour. That is environment-independent (solid fills
don't depend on glyph rendering) yet still catches real regressions: move the
header band or change a theme colour and a sample fails. Promoted from the
card-engine vision's H2 follow-up idea
(``docs/ideas/session-followups-visual-ai-setup-2026-06-23.md`` §1).
"""

from __future__ import annotations

import io

import pytest

from utils.card_render import THEMES, get_theme, new_canvas
from utils.profile_render import render_profile_card


def _pillow_available() -> bool:
    try:
        import PIL  # noqa: F401
    except Exception:  # noqa: BLE001
        return False
    return True


pytestmark = pytest.mark.skipif(
    not _pillow_available(),
    reason="Pillow not installed — renderers degrade to None (covered separately)",
)


def _open(png: bytes | None):  # noqa: ANN202 — PIL lazy type
    from PIL import Image

    assert isinstance(png, bytes) and png
    return Image.open(io.BytesIO(png)).convert("RGB")


# ---------------------------------------------------------------------------
# CardCanvas primitives — each fills a solid region with a known colour
# ---------------------------------------------------------------------------


def test_new_canvas_background_is_theme_bg_for_every_theme():
    for name in THEMES:
        theme = get_theme(name)
        canvas = new_canvas(50, 50, theme)
        assert canvas is not None
        img = _open(canvas.to_png())
        assert img.getpixel((25, 25)) == theme.bg, name


def test_header_band_fills_panel_colour():
    theme = get_theme("midnight")
    canvas = new_canvas(120, 80, theme)
    assert canvas is not None
    canvas.header_band(40)
    img = _open(canvas.to_png())
    assert img.getpixel((60, 20)) == theme.panel  # inside the band
    assert img.getpixel((60, 70)) == theme.bg  # below the band (untouched)


def test_panel_fills_with_given_colour():
    theme = get_theme("midnight")
    canvas = new_canvas(120, 120, theme)
    assert canvas is not None
    canvas.panel((20, 30, 100, 90), fill=theme.accent, radius=8)
    img = _open(canvas.to_png())
    assert img.getpixel((60, 60)) == theme.accent  # solid centre


def test_progress_bar_fill_vs_track_split():
    theme = get_theme("midnight")
    canvas = new_canvas(140, 40, theme)
    assert canvas is not None
    # span = 120, fraction 0.5 → fill ends at x = 10 + 60 = 70.
    canvas.progress_bar((10, 10, 130, 30), 0.5, fill=theme.accent, track=theme.outline)
    img = _open(canvas.to_png())
    assert img.getpixel((30, 20)) == theme.accent  # filled (left of split)
    assert img.getpixel((110, 20)) == theme.outline  # empty track (right of split)


def test_progress_bar_clamps_full_and_empty():
    theme = get_theme("midnight")
    full = new_canvas(140, 40, theme)
    empty = new_canvas(140, 40, theme)
    assert full is not None and empty is not None
    full.progress_bar((10, 10, 130, 30), 5.0, fill=theme.accent)  # clamps to 1.0
    empty.progress_bar((10, 10, 130, 30), -1.0, fill=theme.accent)  # clamps to 0.0
    assert _open(full.to_png()).getpixel((110, 20)) == theme.accent  # all filled
    assert _open(empty.to_png()).getpixel((70, 20)) == theme.outline  # all track


# ---------------------------------------------------------------------------
# Profile hero card — structural layout + per-theme palette
# ---------------------------------------------------------------------------


def _profile(theme: str, *, progress=("Engagement", 0.6)):
    return render_profile_card(
        display_name="Wanderer",
        subtitle="Demo Server profile",
        stats=[("Features", "11"), ("Opted in", "7/11")],
        progress=progress,
        theme=theme,
    )


def test_profile_card_fixed_dimensions():
    img = _open(_profile("midnight"))
    assert img.size == (900, 400)


def test_profile_card_header_accent_and_background():
    theme = get_theme("midnight")
    img = _open(_profile("midnight"))
    # Header band (panel), away from the avatar disc + name text.
    assert img.getpixel((850, 20)) == theme.panel
    # The 4px accent underline at y = _HEADER_H - 2.
    assert img.getpixel((450, 148)) == theme.accent
    # Body background, bottom-right corner (below every element).
    assert img.getpixel((890, 395)) == theme.bg


def test_profile_card_progress_bar_position():
    theme = get_theme("midnight")
    img = _open(_profile("midnight"))
    # Bar spans x 28..872 at y 322..344; fraction 0.6 → fill ends at x ≈ 534.
    assert img.getpixel((120, 333)) == theme.accent_alt  # filled portion
    assert img.getpixel((820, 333)) == theme.outline  # empty track


def test_profile_card_each_theme_paints_its_palette():
    # A new skin must actually change the pixels — the re-skin property.
    for name in ("midnight", "ember", "verdant", "abyss"):
        theme = get_theme(name)
        img = _open(_profile(name, progress=None))
        assert img.getpixel((890, 395)) == theme.bg, name
        assert img.getpixel((850, 20)) == theme.panel, name
        assert img.getpixel((450, 148)) == theme.accent, name


def test_profile_card_without_progress_has_no_bar():
    theme = get_theme("midnight")
    img = _open(_profile("midnight", progress=None))
    # With no progress bar, the band region is plain background.
    assert img.getpixel((120, 333)) == theme.bg
