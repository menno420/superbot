"""Paper-doll character compositor (V-16 phase 1) — manifest-driven, pure.

Renders the player's character as a PNG: a base figure with every equipped
item drawn at its slot's anchor position.  This is the restoration of
minebot's ``/gear`` render (April 2025) and the seed of the cross-ecosystem
character identity (V-13: the same doll later holds the fishing rod).

The render pipeline is **hot-swappable art**:

* The sprite manifest is a *naming convention over a directory*
  (:data:`ASSET_DIR`): the owner's PNG pack drops in as
  ``{family}_{tier}.png`` (``sword_diamond.png``, ``boots_gold.png`` — the
  pack's own naming) plus ``base_character.png``, and the compositor picks
  the files up on the next render — no code change.
* Until a sprite exists, the renderer draws a **procedural placeholder**
  (a per-family shape in the tier's palette colour), so the doll works for
  all 30 set items + mining gear from day one.

Layout (:func:`build_character_spec`) is pure and unit-tested without
Pillow; only :func:`render_character` needs the library, and it degrades to
``None`` exactly like :mod:`utils.mining_render` — callers always keep
their embed fallback.
"""

from __future__ import annotations

import io
import os
from dataclasses import dataclass
from functools import lru_cache

from utils import equipment

# Where the owner's sprite pack lives.  Files are optional one by one — any
# present sprite is used, any absent one falls back to its placeholder.
ASSET_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "assets",
    "character",
)
BASE_SPRITE = "base_character.png"

_CANVAS_W = 360
_CANVAS_H = 440
_BG = (24, 26, 32)

# Per-slot anchor boxes (x, y, w, h) on the canvas — where each equipped
# item is drawn.  The base figure is centred at x=180: head ≈ (180, 88),
# torso 130–250, legs 250–380, feet 380–416.
SLOT_ANCHORS: dict[str, tuple[int, int, int, int]] = {
    equipment.HELMET: (142, 42, 76, 46),
    equipment.CHARM: (166, 122, 28, 24),
    equipment.CHESTPLATE: (142, 136, 76, 96),
    equipment.LEGGINGS: (148, 240, 64, 110),
    equipment.BOOTS: (138, 376, 84, 40),
    equipment.WEAPON: (264, 140, 76, 150),
    equipment.SHIELD: (22, 156, 72, 104),
    equipment.TOOL: (52, 286, 60, 60),
    equipment.LIGHT: (252, 296, 52, 56),
}

# Tier palette for placeholder sprites (and any future tint pass).  Untiered
# gear (starters, mining tools) renders in a neutral wood/leather brown.
TIER_COLORS: dict[str, tuple[int, int, int]] = {
    "bronze": (176, 108, 56),
    "iron": (130, 130, 140),
    "silver": (200, 200, 210),
    "gold": (235, 190, 60),
    "diamond": (120, 225, 230),
}
_UNTIERED_COLOR = (150, 120, 90)
_FIGURE_COLOR = (90, 96, 110)
_OUTLINE = (16, 17, 21)


def sprite_filename(item_name: str) -> str:
    """The manifest filename for *item_name*.

    Tiered set gear uses the owner pack's ``{family}_{tier}.png`` convention
    (``"diamond sword"`` → ``sword_diamond.png``); everything else maps
    spaces to underscores (``"iron pickaxe"`` → ``iron_pickaxe.png``).
    """
    name = item_name.lower()
    tier = equipment.gear_tier(name)
    if tier is not None:
        family = name.split(None, 1)[1]
        return f"{family.replace(' ', '_')}_{tier}.png"
    return f"{name.replace(' ', '_')}.png"


@dataclass(frozen=True)
class CharacterLayer:
    """One equipped item to draw: resolved sprite path or placeholder data."""

    slot: str
    item: str
    anchor: tuple[int, int, int, int]
    sprite_path: str | None  # None → draw the procedural placeholder
    color: tuple[int, int, int]


@dataclass(frozen=True)
class CharacterSpec:
    """A resolution-independent description of the doll to draw."""

    base_sprite_path: str | None  # None → draw the procedural figure
    layers: tuple[CharacterLayer, ...]
    width: int = _CANVAS_W
    height: int = _CANVAS_H


def _existing(path: str) -> str | None:
    return path if os.path.isfile(path) else None


def build_character_spec(
    equipped: dict[str, str],
    *,
    asset_dir: str | None = None,
) -> CharacterSpec:
    """Compose the render spec for an ``{slot: item}`` loadout (pure layout).

    Sprite resolution is the only filesystem touch: a sprite file that exists
    under *asset_dir* is referenced, anything else renders as a placeholder.
    Slots draw in :data:`SLOT_ANCHORS` order (armor first, held items on
    top), each at its anchor.
    """
    directory = ASSET_DIR if asset_dir is None else asset_dir
    layers: list[CharacterLayer] = []
    for slot, anchor in SLOT_ANCHORS.items():
        item = equipped.get(slot)
        if not item:
            continue
        tier = equipment.gear_tier(item)
        layers.append(
            CharacterLayer(
                slot=slot,
                item=item.lower(),
                anchor=anchor,
                sprite_path=_existing(
                    os.path.join(directory, sprite_filename(item)),
                ),
                color=TIER_COLORS.get(tier or "", _UNTIERED_COLOR),
            ),
        )
    return CharacterSpec(
        base_sprite_path=_existing(os.path.join(directory, BASE_SPRITE)),
        layers=tuple(layers),
    )


def _draw_figure(draw) -> None:
    """The procedural base character (used until base_character.png exists)."""
    # Head, torso, arms, legs — a friendly blocky figure, centred at x=180.
    draw.ellipse((150, 58, 210, 118), fill=_FIGURE_COLOR, outline=_OUTLINE)
    draw.rectangle((152, 126, 208, 252), fill=_FIGURE_COLOR, outline=_OUTLINE)
    draw.rectangle((118, 136, 150, 244), fill=_FIGURE_COLOR, outline=_OUTLINE)
    draw.rectangle((210, 136, 242, 244), fill=_FIGURE_COLOR, outline=_OUTLINE)
    draw.rectangle((154, 252, 178, 384), fill=_FIGURE_COLOR, outline=_OUTLINE)
    draw.rectangle((182, 252, 206, 384), fill=_FIGURE_COLOR, outline=_OUTLINE)


def _draw_placeholder(draw, layer: CharacterLayer) -> None:
    """A per-family placeholder shape in the item's tier colour."""
    x, y, w, h = layer.anchor
    c, o = layer.color, _OUTLINE
    slot = layer.slot
    if slot == equipment.HELMET:
        draw.pieslice((x, y, x + w, y + 2 * h), 180, 360, fill=c, outline=o)
    elif slot == equipment.CHESTPLATE:
        draw.rounded_rectangle((x, y, x + w, y + h), radius=8, fill=c, outline=o)
    elif slot == equipment.LEGGINGS:
        mid = x + w // 2
        draw.rectangle((x, y, mid - 3, y + h), fill=c, outline=o)
        draw.rectangle((mid + 3, y, x + w, y + h), fill=c, outline=o)
    elif slot == equipment.BOOTS:
        mid = x + w // 2
        draw.rectangle((x, y, mid - 4, y + h), fill=c, outline=o)
        draw.rectangle((mid + 4, y, x + w, y + h), fill=c, outline=o)
    elif slot == equipment.WEAPON:
        # Blade with a small crossguard.
        bx = x + w // 2
        draw.polygon(
            ((bx - 7, y + h - 30), (bx + 7, y + h - 30), (bx, y)),
            fill=c,
            outline=o,
        )
        draw.rectangle((bx - 16, y + h - 30, bx + 16, y + h - 22), fill=c, outline=o)
        draw.rectangle((bx - 4, y + h - 22, bx + 4, y + h), fill=c, outline=o)
    elif slot == equipment.SHIELD:
        draw.ellipse((x, y, x + w, y + h), fill=c, outline=o)
    elif slot == equipment.TOOL:
        # Pick head + handle.
        draw.arc((x, y, x + w, y + h), 200, 340, fill=c, width=6)
        draw.line(
            (x + w // 2, y + h // 4, x + w // 2, y + h),
            fill=c,
            width=5,
        )
    elif slot == equipment.LIGHT:
        draw.ellipse((x + 8, y, x + w - 8, y + h - 16), fill=(255, 222, 120), outline=o)
        draw.rectangle((x + w // 2 - 5, y + h - 16, x + w // 2 + 5, y + h), fill=c)
    elif slot == equipment.CHARM:
        bx, by = x + w // 2, y + h // 2
        draw.polygon(
            ((bx, y), (x + w, by), (bx, y + h), (x, by)),
            fill=c,
            outline=o,
        )


@lru_cache(maxsize=64)
def _render_cached(spec: CharacterSpec) -> bytes | None:
    try:
        from PIL import Image, ImageDraw  # lazy: degrade gracefully
    except Exception:  # noqa: BLE001 — any import failure → graceful no-op
        return None

    img = Image.new("RGB", (spec.width, spec.height), _BG)
    draw = ImageDraw.Draw(img)

    base = None
    if spec.base_sprite_path:
        try:
            base = Image.open(spec.base_sprite_path).convert("RGBA")
        except Exception:  # noqa: BLE001 — a corrupt sprite must not kill the panel
            base = None
    if base is not None:
        base.thumbnail((spec.width - 40, spec.height - 40))
        img.paste(
            base,
            ((spec.width - base.width) // 2, (spec.height - base.height) // 2),
            base,
        )
    else:
        _draw_figure(draw)

    for layer in spec.layers:
        sprite = None
        if layer.sprite_path:
            try:
                sprite = Image.open(layer.sprite_path).convert("RGBA")
            except Exception:  # noqa: BLE001 — fall back to the placeholder
                sprite = None
        x, y, w, h = layer.anchor
        if sprite is not None:
            sprite.thumbnail((w, h))
            img.paste(
                sprite,
                (x + (w - sprite.width) // 2, y + (h - sprite.height) // 2),
                sprite,
            )
        else:
            _draw_placeholder(draw, layer)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def render_character(spec: CharacterSpec) -> bytes | None:
    """Render *spec* to PNG bytes, or ``None`` if Pillow is unavailable.

    Cached per spec (loadout + resolved sprites), so re-opening a panel with
    an unchanged loadout never re-draws.  Callers MUST treat ``None`` as
    "rendering unavailable" and keep their embed fallback.
    """
    return _render_cached(spec)


def render_character_for(
    equipped: dict[str, str],
    *,
    asset_dir: str | None = None,
) -> bytes | None:
    """One-call convenience: spec + render for an ``{slot: item}`` loadout."""
    return render_character(build_character_spec(equipped, asset_dir=asset_dir))


__all__ = [
    "ASSET_DIR",
    "BASE_SPRITE",
    "SLOT_ANCHORS",
    "TIER_COLORS",
    "sprite_filename",
    "CharacterLayer",
    "CharacterSpec",
    "build_character_spec",
    "render_character",
    "render_character_for",
]
