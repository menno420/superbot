"""Optional image rendering for mining cards (foundation).

Renders an inventory / exploration "card" as a PNG.  Pillow is an
**optional** dependency: this module lazy-imports it and degrades
gracefully (``render_inventory_card`` returns ``None``) when it is not
installed, so importing this module never breaks the bot and the project
gains no hard dependency.

> To activate image rendering in production, add ``Pillow`` to
> ``requirements.txt``.  That one-line dependency decision is deliberately
> left to the maintainer — until then the helper is dormant and any
> caller should fall back to an embed when it returns ``None``.

The layout math (:func:`build_card_spec`) is pure and fully unit-tested
regardless of whether Pillow is present; only the final pixel-pushing in
:func:`render_inventory_card` needs the library.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field

# Quantity-coloured rows give the card an at-a-glance rarity feel without
# needing per-item art.  RGB tuples so the renderer can pass them straight
# to Pillow.
_KIND_COLOR: dict[str, tuple[int, int, int]] = {
    "resource": (210, 210, 210),
    "tool": (130, 200, 255),
    "consumable": (255, 200, 120),
    "structure": (180, 160, 255),
    "treasure": (255, 215, 90),
}
_DEFAULT_COLOR = (210, 210, 210)
_BG = (24, 26, 32)
_TITLE_COLOR = (240, 240, 240)


@dataclass(frozen=True)
class CardRow:
    label: str
    quantity: int
    color: tuple[int, int, int]


@dataclass(frozen=True)
class CardSpec:
    """A resolution-independent description of the card to draw."""

    title: str
    rows: tuple[CardRow, ...]
    footer: str = ""
    width: int = 420
    row_height: int = 34
    padding: int = 18
    header_height: int = 48
    meta: dict[str, str] = field(default_factory=dict)

    @property
    def height(self) -> int:
        body = max(len(self.rows), 1) * self.row_height
        footer_h = self.row_height if self.footer else 0
        return self.header_height + body + footer_h + self.padding * 2


def build_card_spec(
    title: str,
    inventory_rows: list[tuple[str, int]],
    *,
    classify_kind=None,
    footer: str = "",
) -> CardSpec:
    """Build a :class:`CardSpec` from ordered ``(item_name, qty)`` rows.

    *classify_kind* is an optional ``name -> kind_string`` callable (e.g.
    ``lambda n: utils.mining.items.classify(n).value``) used to colour
    rows.  Kept as an injected callable so this ``utils`` module never
    imports the ``cogs`` layer (respecting the layer boundary) and stays
    trivially testable.
    """
    rows: list[CardRow] = []
    for name, qty in inventory_rows:
        kind = classify_kind(name) if classify_kind else "resource"
        color = _KIND_COLOR.get(kind, _DEFAULT_COLOR)
        rows.append(CardRow(label=name.title(), quantity=qty, color=color))
    return CardSpec(title=title, rows=tuple(rows), footer=footer)


def render_inventory_card(spec: CardSpec) -> bytes | None:
    """Render *spec* to PNG bytes, or ``None`` if Pillow is unavailable.

    Callers MUST treat ``None`` as "rendering unavailable" and fall back
    to a text/embed representation.
    """
    try:
        from PIL import Image, ImageDraw  # lazy: optional dependency
    except Exception:  # noqa: BLE001 — any import failure → graceful no-op
        return None

    img = Image.new("RGB", (spec.width, spec.height), _BG)
    draw = ImageDraw.Draw(img)
    pad = spec.padding

    # Title.
    draw.text((pad, pad), spec.title, fill=_TITLE_COLOR)

    # Rows.
    y = spec.header_height + pad
    for row in spec.rows:
        draw.text((pad, y), row.label, fill=row.color)
        qty_text = f"x{row.quantity}"
        # Right-align the quantity within the card width.
        draw.text((spec.width - pad - 8 * len(qty_text), y), qty_text, fill=row.color)
        y += spec.row_height

    if spec.footer:
        draw.text((pad, y), spec.footer, fill=(150, 150, 150))

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def pillow_available() -> bool:
    """Return True when Pillow can be imported (image rendering is live)."""
    try:
        import PIL  # noqa: F401

        return True
    except Exception:  # noqa: BLE001
        return False


__all__ = [
    "CardRow",
    "CardSpec",
    "build_card_spec",
    "render_inventory_card",
    "pillow_available",
]
