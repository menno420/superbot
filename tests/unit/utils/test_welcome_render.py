"""Unit tests for the welcome-card compositor (utils.welcome_render).

PIL-dependent assertions are guarded by ``importorskip`` so the suite stays
green whether or not Pillow is installed; the pure helpers (``_initials``) and
the graceful-degradation contract are tested unconditionally.
"""

from __future__ import annotations

import pytest

from utils import welcome_render

# ---------------------------------------------------------------------------
# _initials — pure, no PIL
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Astro Fox", "AF"),  # two tokens -> first letter of each
        ("AstroFox", "AS"),  # one token -> first two letters
        ("a", "A"),  # single char, upper-cased
        ("", "?"),  # empty -> placeholder glyph
        ("   ", "?"),  # whitespace-only -> placeholder
        ("🦊", "?"),  # symbol-only -> placeholder (no alnum)
        ("Émile Zola", "ÉZ"),  # non-ASCII alnum kept
    ],
)
def test_initials(name: str, expected: str) -> None:
    assert welcome_render._initials(name) == expected


# ---------------------------------------------------------------------------
# render_welcome_card — graceful degradation + real render
# ---------------------------------------------------------------------------


def test_render_returns_none_without_pillow(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pillow unavailable -> None (the caller keeps its embed fallback)."""
    import builtins

    real_import = builtins.__import__

    def _no_pil(name, *args, **kwargs):  # noqa: ANN001, ANN002, ANN003
        if name == "PIL" or name.startswith("PIL."):
            raise ImportError("Pillow not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _no_pil)
    assert welcome_render.render_welcome_card() is None


def test_render_produces_png_bytes() -> None:
    pytest.importorskip("PIL")
    png = welcome_render.render_welcome_card(
        member_name="Astro Fox",
        server_name="Demo Server",
        member_number=1235,
    )
    assert isinstance(png, bytes)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"  # PNG magic


def test_render_accent_override_changes_bytes() -> None:
    """A non-default accent yields a visibly different image."""
    pytest.importorskip("PIL")
    default = welcome_render.render_welcome_card(member_name="Astro")
    tinted = welcome_render.render_welcome_card(
        member_name="Astro",
        accent=(240, 50, 50),
    )
    assert default != tinted


def test_render_long_name_still_renders() -> None:
    """An overlong name/server is ellipsized, not raised on."""
    pytest.importorskip("PIL")
    png = welcome_render.render_welcome_card(
        member_name="X" * 200,
        server_name="Y" * 200,
        member_number=10_000_000,
    )
    assert isinstance(png, bytes)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
