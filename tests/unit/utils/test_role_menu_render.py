"""Unit tests for the role-menu banner-card renderer (utils.role_menu_render).

Sibling of ``test_welcome_render`` — same contract (lazy PIL, ``bytes | None``
fallback, pure / no-network). Pins that every preset style renders valid PNG
bytes, long titles/overlays don't crash, and a missing Pillow degrades to None.
"""

from __future__ import annotations

import pytest

from utils import role_menu_render


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

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


@pytest.mark.parametrize("style", role_menu_render.KNOWN_STYLES)
def test_every_known_style_renders_png_bytes(style):
    out = role_menu_render.render_role_menu_card(
        style=style,
        title="Pick your roles",
        overlay="Choose below",
        accent=(255, 0, 200),
    )
    assert isinstance(out, bytes) and out
    assert out[:8] == _PNG_MAGIC


def test_unknown_style_falls_back_to_banner_not_crash():
    out = role_menu_render.render_role_menu_card(style="nope", title="T")
    assert isinstance(out, bytes) and out[:8] == _PNG_MAGIC


def test_renders_without_overlay():
    out = role_menu_render.render_role_menu_card(style="banner", title="Solo line")
    assert isinstance(out, bytes) and out[:8] == _PNG_MAGIC


def test_overlong_title_and_overlay_do_not_crash():
    out = role_menu_render.render_role_menu_card(
        style="gradient",
        title="X" * 300,
        overlay="Y" * 300,
    )
    assert isinstance(out, bytes) and out[:8] == _PNG_MAGIC


def test_default_accent_when_none_given():
    out = role_menu_render.render_role_menu_card(
        style="minimal",
        title="T",
        accent=None,
    )
    assert isinstance(out, bytes) and out[:8] == _PNG_MAGIC


def test_render_returns_none_without_pillow(monkeypatch):
    """The lazy PIL import failing degrades the renderer to None (embed-only)."""
    import builtins

    real_import = builtins.__import__

    def _fail_pil(name, *args, **kwargs):
        if name.startswith("PIL"):
            raise ImportError("no pillow")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _fail_pil)
    assert role_menu_render.render_role_menu_card(style="banner", title="T") is None


def test_fit_truncates_to_width():
    """The migrated renderer clamps overflow via the shared engine's
    ``CardCanvas.fit`` (the private ``_fit`` copy is gone)."""
    from utils.card_render import get_theme, new_canvas

    canvas = new_canvas(10, 10, get_theme("midnight"))
    assert canvas is not None
    font = canvas.font(58, bold=True)
    fitted = canvas.fit("Z" * 200, font, 400)
    assert fitted.endswith("…")
    assert canvas.draw.textlength(fitted, font=font) <= 400
    assert canvas.fit("Hi", font, 400) == "Hi"
