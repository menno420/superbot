"""Unit tests for the welcome greeting-card renderer (utils.welcome_render)."""

from __future__ import annotations

import importlib

import pytest

from utils import welcome_render


def _pillow_available() -> bool:
    try:
        import PIL  # noqa: F401
    except Exception:  # noqa: BLE001
        return False
    return True


pytestmark = pytest.mark.skipif(
    not _pillow_available(),
    reason="Pillow not installed — renderer degrades to None (covered separately)",
)


def test_render_returns_jpeg_bytes():
    out = welcome_render.render_welcome_card("AstroFox", "Demo Server", 1235)
    assert isinstance(out, bytes) and out
    assert out[:3] == b"\xff\xd8\xff"  # JPEG SOI marker


def test_render_tolerates_empty_and_symbolic_names():
    # An emoji-only / symbol display name must still produce a card (no crash
    # on the initials slice) — the disc falls back to "?".
    out = welcome_render.render_welcome_card("🎉🎉", "S", 0)
    assert isinstance(out, bytes) and out


def test_render_returns_none_without_pillow(monkeypatch):
    """When the lazy PIL import fails the renderer degrades to None."""
    import builtins

    real_import = builtins.__import__

    def _fail_pil(name, *args, **kwargs):
        if name.startswith("PIL"):
            raise ImportError("no pillow")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _fail_pil)
    assert welcome_render.render_welcome_card("X", "Y", 1) is None


def test_render_handles_overlong_names_without_error():
    """An unbounded member/server name must render (truncated), not crash."""
    out = welcome_render.render_welcome_card("X" * 200, "Y" * 200, 9_999_999)
    assert isinstance(out, bytes) and out


def test_fit_truncates_to_width():
    """The migrated renderer ellipsises overflow via the shared engine's
    ``CardCanvas.fit`` (the private ``_fit`` copy is gone)."""
    from utils.card_render import get_theme, new_canvas

    canvas = new_canvas(10, 10, get_theme("midnight"))
    assert canvas is not None
    font = canvas.font(56, bold=True)
    long = "Welcome, " + "Z" * 100 + "!"
    fitted = canvas.fit(long, font, 400)
    assert fitted.endswith("…")
    assert canvas.draw.textlength(fitted, font=font) <= 400
    # A short string is returned unchanged (no needless ellipsis).
    assert canvas.fit("Hi!", font, 400) == "Hi!"


def test_gallery_reexports_the_production_renderer():
    """The UX-lab gallery preview is the same function as the live feature."""
    mod = importlib.import_module("utils.ux_patterns.image_builders")
    assert mod.render_welcome_card is welcome_render.render_welcome_card
