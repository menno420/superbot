"""Themeable card-rendering engine — the shared substrate for image cards.

Every image renderer in the bot (``mining_render``, ``welcome_render``,
``character_render``, ``ux_patterns.image_builders``) re-declared its *own*
``_fonts()`` helper and its own copy of the dark-blurple palette.  That is
exactly the duplication Dank Memer avoids: their seasonal cards are one
templated engine *re-skinned* per season, so a new look is a config drop, not
new code.  This module is that engine for us.

What it provides
----------------
* :class:`Theme` — a frozen palette + font value object, and a named
  :data:`THEMES` registry so a new skin ("ember", "verdant", …) is **config,
  not code**.  :func:`get_theme` resolves by name with a safe default.
* :class:`CardCanvas` — a thin, themed wrapper over a Pillow image+draw with
  the primitives every card needs: themed text with width-fit truncation,
  rounded panels, progress bars, an avatar initials disc, a header band, and
  PNG/JPEG export.

Contract (identical to the other renderers): **lazy PIL import**, graceful
degradation — :func:`new_canvas` returns ``None`` when Pillow is unavailable,
so callers always keep their embed fallback.  Layout helpers that don't touch
pixels (:func:`initials`) are pure and importable without Pillow.

Layering: ``utils`` may import stdlib + discord only.  This module imports
neither ``services``/``core``/``cogs`` nor Discord — it is pure rendering.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from functools import lru_cache

RGB = tuple[int, int, int]

# Candidate font files.  We ship no custom fonts yet, so every theme points at
# the system DejaVu pair; a theme may name its own font file first and fall
# back to these (the engine tries each path in order, then Pillow's bitmap
# default).  Dropping a branded .ttf in and naming it in a Theme is the whole
# "custom font per skin" story.
_DEJAVU_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_DEJAVU = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


@dataclass(frozen=True)
class Theme:
    """A card skin: palette + font candidates.  Frozen so it is hashable and
    safe to cache renders against.

    Colours are RGB tuples (Pillow-native).  ``font_bold`` / ``font_regular``
    are ordered candidate paths — the first that loads wins, else the bitmap
    default.  A new season/world is a new :class:`Theme`, registered in
    :data:`THEMES`; the layout code never changes.
    """

    name: str
    bg: RGB
    panel: RGB
    accent: RGB
    accent_alt: RGB
    text: RGB
    subtle: RGB
    gold: RGB
    outline: RGB
    font_bold: tuple[str, ...] = (_DEJAVU_BOLD,)
    font_regular: tuple[str, ...] = (_DEJAVU,)


# The named skin registry.  "midnight" mirrors the existing dark-blurple
# palette so migrated renderers look identical; the others demonstrate that a
# whole new look is a few RGB tuples (the Dank-Memer "new season = art drop"
# property, in code).
THEMES: dict[str, Theme] = {
    "midnight": Theme(
        name="midnight",
        bg=(24, 25, 31),
        panel=(32, 34, 42),
        accent=(88, 101, 242),  # blurple
        accent_alt=(120, 200, 255),
        text=(235, 236, 240),
        subtle=(148, 155, 164),
        gold=(240, 178, 50),
        outline=(16, 17, 21),
    ),
    "ember": Theme(
        name="ember",
        bg=(28, 18, 18),
        panel=(44, 26, 24),
        accent=(232, 96, 56),
        accent_alt=(255, 168, 92),
        text=(244, 234, 228),
        subtle=(176, 142, 130),
        gold=(245, 196, 96),
        outline=(18, 11, 10),
    ),
    "verdant": Theme(
        name="verdant",
        bg=(18, 26, 22),
        panel=(26, 38, 30),
        accent=(76, 184, 110),
        accent_alt=(150, 224, 150),
        text=(232, 240, 232),
        subtle=(140, 166, 146),
        gold=(226, 200, 96),
        outline=(11, 16, 13),
    ),
    "abyss": Theme(
        name="abyss",
        bg=(16, 22, 32),
        panel=(22, 32, 46),
        accent=(64, 156, 214),
        accent_alt=(120, 214, 232),
        text=(228, 238, 246),
        subtle=(132, 156, 178),
        gold=(228, 196, 110),
        outline=(9, 13, 20),
    ),
}

DEFAULT_THEME = "midnight"


def get_theme(name: str | None) -> Theme:
    """Resolve a theme by name, falling back to :data:`DEFAULT_THEME`.

    Never raises on an unknown name — a bad theme key must never take a card
    down; it just renders in the default skin.
    """
    if name is None:
        return THEMES[DEFAULT_THEME]
    return THEMES.get(name, THEMES[DEFAULT_THEME])


@lru_cache(maxsize=128)
def _load_font_path(path: str, size: int):  # noqa: ANN202 — PIL lazy types
    """Cached truetype load for one (path, size); raises on a missing file."""
    from PIL import ImageFont  # lazy: optional at import time

    return ImageFont.truetype(path, size)


def load_font(candidates: tuple[str, ...], size: int):  # noqa: ANN201
    """First loadable font among *candidates* at *size*, else the bitmap default.

    Font availability is environmental, so this never raises — a stripped image
    with no DejaVu still renders, just with Pillow's built-in font.
    """
    from PIL import ImageFont  # lazy

    for path in candidates:
        try:
            return _load_font_path(path, size)
        except Exception:  # noqa: BLE001, S112 — just try the next candidate
            continue
    return ImageFont.load_default()


def dejavu_fonts(size_big: int, size_small: int):  # noqa: ANN201
    """A (bold-big, regular-small) DejaVu pair — the legacy ``_fonts()`` shape.

    The single home for the helper that ``welcome_render`` and
    ``ux_patterns.image_builders`` each used to define privately; they now
    import this so there is one font loader, not three.
    """
    return load_font((_DEJAVU_BOLD,), size_big), load_font((_DEJAVU,), size_small)


def mix(a: RGB, b: RGB, t: float) -> RGB:
    """Linear blend of two RGB colours at fraction *t* (0 → *a*, 1 → *b*).

    Pure colour math — the one home for the per-channel lerp that gradient
    backgrounds need (``role_menu_render`` grew it privately as ``_mix``).  *t*
    is clamped to ``[0, 1]`` so an out-of-range fraction can never produce an
    invalid channel value.
    """
    if t < 0:
        t = 0.0
    elif t > 1:
        t = 1.0
    return (
        round(a[0] + (b[0] - a[0]) * t),
        round(a[1] + (b[1] - a[1]) * t),
        round(a[2] + (b[2] - a[2]) * t),
    )


def initials(name: str) -> str:
    """First two alphanumerics of *name*, upper-cased (``?`` if none).

    Pure — the no-network avatar label, shared by every card with an initials
    disc.  (Mirrors the helper ``welcome_render`` grew privately.)
    """
    letters = [c for c in name if c.isalnum()]
    return ("".join(letters[:2]) or "?").upper()


class CardCanvas:
    """A themed Pillow surface with the card primitives.

    Build one with :func:`new_canvas` (which returns ``None`` when Pillow is
    missing).  All colour defaults pull from the bound :class:`Theme`, so a
    renderer written against the canvas is automatically re-skinnable: pass a
    different theme and the same draw calls produce a different look.
    """

    def __init__(self, img, draw, theme: Theme) -> None:  # noqa: ANN001 — PIL types
        self._img = img
        self._draw = draw
        self.theme = theme

    @property
    def width(self) -> int:
        return self._img.width

    @property
    def height(self) -> int:
        return self._img.height

    @property
    def draw(self):  # noqa: ANN201 — escape hatch for bespoke art
        return self._draw

    def font(self, size: int, *, bold: bool = False):  # noqa: ANN201
        cands = self.theme.font_bold if bold else self.theme.font_regular
        return load_font(cands, size)

    def fit(self, text: str, font, max_width: int) -> str:  # noqa: ANN001
        """Truncate *text* with an ellipsis until it fits ``max_width`` px.

        Display/server names are unbounded; this clamps any string to the
        drawable area so it can never run off the card edge.
        """
        if self._draw.textlength(text, font=font) <= max_width:
            return text
        ell = "…"
        while text and self._draw.textlength(text + ell, font=font) > max_width:
            text = text[:-1]
        return (text + ell) if text else ell

    def text(
        self,
        xy: tuple[int, int],
        text: str,
        *,
        size: int = 24,
        bold: bool = False,
        color: RGB | None = None,
        max_width: int | None = None,
        anchor: str | None = None,
    ) -> None:
        """Themed text.  ``max_width`` ellipsises overflow; ``color`` defaults
        to the theme's body text colour.
        """
        font = self.font(size, bold=bold)
        if max_width is not None:
            text = self.fit(text, font, max_width)
        self._draw.text(
            xy,
            text,
            font=font,
            fill=color or self.theme.text,
            anchor=anchor,
        )

    def panel(
        self,
        box: tuple[int, int, int, int],
        *,
        radius: int = 14,
        fill: RGB | None = None,
        outline: RGB | None = None,
        width: int = 1,
    ) -> None:
        """A rounded panel; defaults to the theme's panel fill."""
        self._draw.rounded_rectangle(
            box,
            radius=radius,
            fill=fill if fill is not None else self.theme.panel,
            outline=outline,
            width=width,
        )

    def header_band(self, height: int, *, fill: RGB | None = None) -> None:
        """A full-width band across the top (the card's title strip)."""
        self._draw.rectangle(
            (0, 0, self.width, height),
            fill=fill if fill is not None else self.theme.panel,
        )

    def progress_bar(
        self,
        box: tuple[int, int, int, int],
        fraction: float,
        *,
        radius: int | None = None,
        track: RGB | None = None,
        fill: RGB | None = None,
    ) -> None:
        """A rounded progress bar; *fraction* is clamped to ``[0, 1]``.

        Guards a zero/near-zero fill so a tiny fraction still shows a cap-width
        sliver rather than an invalid (x0 > x1) rectangle.
        """
        x0, y0, x1, y1 = box
        r = radius if radius is not None else (y1 - y0) // 2
        self._draw.rounded_rectangle(
            box,
            radius=r,
            fill=track if track is not None else self.theme.outline,
        )
        frac = 0.0 if fraction < 0 else 1.0 if fraction > 1 else fraction
        span = x1 - x0
        end = x0 + int(span * frac)
        min_w = 2 * r  # never narrower than the rounded caps want
        if frac > 0 and end - x0 < min_w:
            end = min(x0 + min_w, x1)
        if end > x0:
            self._draw.rounded_rectangle(
                (x0, y0, end, y1),
                radius=r,
                fill=fill if fill is not None else self.theme.accent,
            )

    def initials_disc(
        self,
        center: tuple[int, int],
        radius: int,
        text: str,
        *,
        ring: RGB | None = None,
        size: int | None = None,
    ) -> None:
        """The no-network avatar: accent ring + filled disc + centred initials.

        Real member avatars require a CDN fetch (can block/fail), so cards use
        this content-free disc; the live avatar rides the embed thumbnail.
        """
        cx, cy = center
        ring_c = ring if ring is not None else self.theme.accent
        self._draw.ellipse(
            (cx - radius - 6, cy - radius - 6, cx + radius + 6, cy + radius + 6),
            outline=ring_c,
            width=6,
        )
        self._draw.ellipse(
            (cx - radius, cy - radius, cx + radius, cy + radius),
            fill=self.theme.panel,
        )
        font = self.font(size or int(radius * 0.9), bold=True)
        self._draw.text(
            (cx, cy),
            text,
            font=font,
            fill=self.theme.text,
            anchor="mm",
        )

    def to_png(self) -> bytes:
        buf = io.BytesIO()
        self._img.convert("RGB").save(buf, format="PNG")
        return buf.getvalue()

    def to_jpeg(self, quality: int = 88) -> bytes:
        buf = io.BytesIO()
        self._img.convert("RGB").save(buf, format="JPEG", quality=quality)
        return buf.getvalue()


def new_canvas(
    width: int,
    height: int,
    theme: Theme,
    *,
    mode: str = "RGB",
) -> CardCanvas | None:
    """A themed :class:`CardCanvas`, or ``None`` if Pillow is unavailable.

    The single lazy-PIL gate for the engine: callers that get ``None`` keep
    their embed/text fallback.
    """
    try:
        from PIL import Image, ImageDraw  # lazy: degrade gracefully
    except Exception:  # noqa: BLE001 — any import failure → graceful no-op
        return None
    img = Image.new(mode, (width, height), theme.bg)
    return CardCanvas(img, ImageDraw.Draw(img), theme)


def pillow_available() -> bool:
    """True when Pillow can be imported (image rendering is live)."""
    try:
        import PIL  # noqa: F401

        return True
    except Exception:  # noqa: BLE001
        return False


__all__ = [
    "RGB",
    "Theme",
    "THEMES",
    "DEFAULT_THEME",
    "get_theme",
    "load_font",
    "dejavu_fonts",
    "mix",
    "initials",
    "CardCanvas",
    "new_canvas",
    "pillow_available",
]
