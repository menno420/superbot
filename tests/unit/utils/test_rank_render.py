"""Unit tests for the rank-card renderer (utils.rank_render)."""

from __future__ import annotations

import pytest

from utils import rank_render


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
        subtitle="Demo Server · rank",
        stats=[
            ("XP Rank", "#3"),
            ("Level", "12"),
            ("Total XP", "8421"),
            ("Messages", "1337"),
            ("Coin Rank", "#5"),
            ("Coins", "910"),
        ],
        progress=("Level 12 → 13 · 21/100 XP", 0.21),
    )
    kwargs.update(overrides)
    return rank_render.render_rank_card(**kwargs)


def test_render_returns_png_bytes():
    out = _render()
    assert isinstance(out, bytes) and out[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_two_stats_one_row():
    # The "coins" view: two panels, no progress bar — must render cleanly.
    out = _render(stats=[("Coin Rank", "#5"), ("Coins", "910")], progress=None)
    assert isinstance(out, bytes) and out


def test_render_four_stats_xp_view():
    out = _render(
        stats=[
            ("XP Rank", "#3"),
            ("Level", "12"),
            ("Total XP", "8421"),
            ("Messages", "1337"),
        ]
    )
    assert isinstance(out, bytes) and out


def test_render_without_progress():
    out = _render(progress=None)
    assert isinstance(out, bytes) and out


def test_render_with_no_stats_still_renders_identity():
    out = _render(stats=[], progress=None)
    assert isinstance(out, bytes) and out


def test_render_caps_stats_at_six_panels():
    # More than six stats must not overflow / crash — they are clamped to six.
    out = _render(stats=[(f"S{i}", str(i)) for i in range(10)])
    assert isinstance(out, bytes) and out


def test_render_tolerates_overlong_and_symbolic_names():
    out = _render(display_name="🎉" + "Z" * 200)
    assert isinstance(out, bytes) and out


def _sample_avatar_png() -> bytes:
    import io

    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (64, 64), (200, 120, 60)).save(buf, format="PNG")
    return buf.getvalue()


def test_render_with_real_avatar_bytes():
    out = _render(avatar_png=_sample_avatar_png())
    assert isinstance(out, bytes) and out[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_with_undecodable_avatar_falls_back_to_initials():
    # A bad/failed avatar fetch must never break the card.
    out = _render(avatar_png=b"garbage-not-an-image")
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
