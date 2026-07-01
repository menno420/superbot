"""Unit tests for the themeable card-rendering engine (utils.card_render)."""

from __future__ import annotations

import pytest

from utils import card_render


def _pillow_available() -> bool:
    try:
        import PIL  # noqa: F401
    except Exception:  # noqa: BLE001
        return False
    return True


# --- Pure helpers (no Pillow needed) -------------------------------------


def test_initials_takes_first_two_alphanumerics():
    assert card_render.initials("AstroFox") == "AS"
    assert card_render.initials("banana mage") == "BA"


def test_initials_falls_back_to_question_mark():
    # Emoji/symbol-only names have no alphanumerics → "?" (never an empty slice).
    assert card_render.initials("🎉🎉") == "?"
    assert card_render.initials("") == "?"


def test_mix_blends_and_clamps():
    black, white = (0, 0, 0), (255, 255, 255)
    # Endpoints are exact; the midpoint rounds per channel.
    assert card_render.mix(black, white, 0.0) == black
    assert card_render.mix(black, white, 1.0) == white
    assert card_render.mix(black, white, 0.5) == (128, 128, 128)
    # Out-of-range fractions clamp to [0, 1] — never an invalid channel value.
    assert card_render.mix(black, white, -3.0) == black
    assert card_render.mix(black, white, 9.0) == white
    # Asymmetric channels blend independently.
    assert card_render.mix((10, 20, 30), (30, 60, 90), 0.5) == (20, 40, 60)


def test_image_safe_strips_emoji_but_keeps_renderable_punctuation():
    # Emoji the bundled font can't draw are removed and the leftover spacing is
    # tidied, so a card never shows a tofu box.
    assert card_render.image_safe("🏆 XP Leaderboard") == "XP Leaderboard"
    assert card_render.image_safe("8,473 🪙") == "8,473"
    assert card_render.image_safe("🎉Name") == "Name"
    # Punctuation the cards actually draw ("→", "·", "…") is preserved.
    kept = "Level 13 → 14 · 44/1595 XP…"
    assert card_render.image_safe(kept) == kept
    # Emoji-free text is returned verbatim (intentional spacing preserved).
    assert card_render.image_safe("plain  text") == "plain  text"


def test_image_safe_all_emoji_collapses_to_empty():
    assert card_render.image_safe("🎉🏆🪙") == ""


def test_get_theme_resolves_known_and_falls_back():
    assert card_render.get_theme("ember").name == "ember"
    # Unknown / None never raises — it returns the default skin.
    assert card_render.get_theme("does-not-exist").name == card_render.DEFAULT_THEME
    assert card_render.get_theme(None).name == card_render.DEFAULT_THEME


def test_default_theme_is_registered():
    assert card_render.DEFAULT_THEME in card_render.THEMES


def test_themes_are_frozen_and_hashable():
    # Frozen Theme → usable as an lru_cache key for cached renders.
    t = card_render.get_theme("midnight")
    assert hash(t) is not None
    with pytest.raises(Exception):
        t.bg = (0, 0, 0)  # type: ignore[misc]


# --- Pillow-backed rendering --------------------------------------------

pillow = pytest.mark.skipif(
    not _pillow_available(),
    reason="Pillow not installed — engine degrades to None (covered separately)",
)


@pillow
def test_new_canvas_returns_canvas_and_exports_png():
    canvas = card_render.new_canvas(200, 120, card_render.get_theme("midnight"))
    assert canvas is not None
    assert canvas.width == 200 and canvas.height == 120
    canvas.text((10, 10), "hi", size=20)
    out = canvas.to_png()
    assert isinstance(out, bytes) and out[:8] == b"\x89PNG\r\n\x1a\n"


@pillow
def test_fit_truncates_to_width():
    canvas = card_render.new_canvas(10, 10, card_render.get_theme("midnight"))
    assert canvas is not None
    font = canvas.font(40, bold=True)
    long = "Z" * 200
    fitted = canvas.fit(long, font, 120)
    assert fitted.endswith("…")
    assert canvas.draw.textlength(fitted, font=font) <= 120
    assert canvas.fit("Hi", font, 400) == "Hi"  # short string unchanged


@pillow
def test_progress_bar_clamps_fraction_without_error():
    theme = card_render.get_theme("midnight")
    for frac in (-1.0, 0.0, 0.5, 1.0, 2.0):
        canvas = card_render.new_canvas(200, 40, theme)
        assert canvas is not None
        canvas.progress_bar((10, 10, 190, 30), frac)
        assert isinstance(canvas.to_png(), bytes)


@pillow
def test_initials_disc_renders_centered_label():
    canvas = card_render.new_canvas(120, 120, card_render.get_theme("ember"))
    assert canvas is not None
    canvas.initials_disc((60, 60), 40, "AS")
    assert isinstance(canvas.to_png(), bytes)


def _sample_png_bytes(color=(200, 120, 60), size=64) -> bytes:
    import io

    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (size, size), color).save(buf, format="PNG")
    return buf.getvalue()


@pillow
def test_avatar_disc_composites_real_avatar_bytes():
    # A decodable avatar composites (returns True) — the real-avatar look.
    canvas = card_render.new_canvas(160, 160, card_render.get_theme("midnight"))
    assert canvas is not None
    assert canvas.avatar_disc((80, 80), 50, _sample_png_bytes()) is True
    assert isinstance(canvas.to_png(), bytes)


@pillow
def test_avatar_disc_returns_false_on_undecodable_bytes():
    # Garbage bytes → False, so the caller falls back to the initials disc and
    # never ships a broken card.
    canvas = card_render.new_canvas(160, 160, card_render.get_theme("midnight"))
    assert canvas is not None
    assert canvas.avatar_disc((80, 80), 50, b"not-an-image") is False


@pillow
def test_every_theme_renders():
    # A new skin must be config-only: each registered theme drives the same
    # draw calls to a valid card.
    for name in card_render.THEMES:
        canvas = card_render.new_canvas(160, 80, card_render.get_theme(name))
        assert canvas is not None
        canvas.header_band(30)
        canvas.panel((8, 36, 152, 72))
        assert isinstance(canvas.to_png(), bytes)


def test_new_canvas_returns_none_without_pillow(monkeypatch):
    """When the lazy PIL import fails, the engine degrades to None."""
    import builtins

    real_import = builtins.__import__

    def _fail_pil(name, *args, **kwargs):
        if name.startswith("PIL"):
            raise ImportError("no pillow")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _fail_pil)
    assert card_render.new_canvas(10, 10, card_render.get_theme(None)) is None
