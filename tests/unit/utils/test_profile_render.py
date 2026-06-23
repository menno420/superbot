"""Unit tests for the profile hero-card renderer (utils.profile_render)."""

from __future__ import annotations

import pytest

from utils import profile_render


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


def _render(**overrides):
    kwargs = dict(
        display_name="AstroFox",
        subtitle="Your server profile",
        stats=[("Features", "5"), ("Opted in", "3/5")],
        progress=("Profile engagement", 0.6),
    )
    kwargs.update(overrides)
    return profile_render.render_profile_card(**kwargs)


def test_render_returns_png_bytes():
    out = _render()
    assert isinstance(out, bytes) and out[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_without_progress():
    out = _render(progress=None)
    assert isinstance(out, bytes) and out


def test_render_with_no_stats_still_renders_identity():
    # Empty state (no participation-aware features) must still produce a card.
    out = _render(stats=[], progress=None)
    assert isinstance(out, bytes) and out


def test_render_caps_stats_at_four_panels():
    # More than four stats must not overflow / crash — they are clamped.
    out = _render(stats=[(f"S{i}", str(i)) for i in range(7)])
    assert isinstance(out, bytes) and out


def test_render_tolerates_overlong_and_symbolic_names():
    out = _render(display_name="🎉" + "Z" * 200)
    assert isinstance(out, bytes) and out


def test_unknown_theme_falls_back_not_crashes():
    out = _render(theme="no-such-theme")
    assert isinstance(out, bytes) and out


def test_each_theme_renders():
    from utils.card_render import THEMES

    for name in THEMES:
        assert isinstance(_render(theme=name), bytes)


def test_render_returns_none_without_pillow(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def _fail_pil(name, *args, **kwargs):
        if name.startswith("PIL"):
            raise ImportError("no pillow")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _fail_pil)
    assert _render() is None
