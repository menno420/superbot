"""Paper-doll character compositor (V-16 phase 1) — manifest-driven, pure.

Renders the player's character as a PNG: the base figure with every equipped
item drawn at its slot's anchor.  This is the restoration of minebot's
``/gear`` render (April 2025) and the seed of the cross-ecosystem character
identity (V-13: the same doll later holds the fishing rod).

The art pipeline is **hot-swappable**, anchored on :data:`ASSET_DIR`
(``disbot/assets/gear/`` — seeded by PR #701 with 37 generated placeholder
sprites recreated from the owner's shapes):

* ``manifest.json`` is the layout authority: per-family sprite filenames,
  anchor centres + scales on the 200×300 reference doll, and tier palettes.
  The owner's original PNG pack replaces the sprite files **file-for-file**
  (same names); the manifest stays.
* Anything *not* covered by a sprite file — mining gear (tool/light/charm),
  a missing/corrupt file — falls back to a **procedural placeholder shape**
  in the item's tier colour, so the doll always renders complete.

Layout (:func:`build_character_spec`) is pure and unit-tested without
Pillow; only :func:`render_character` needs the library, and it degrades to
``None`` exactly like :mod:`utils.mining_render` — callers always keep
their embed fallback.
"""

from __future__ import annotations

import io
import json
import os
from dataclasses import dataclass
from functools import lru_cache

from utils import equipment

# The sprite pack + manifest home (PR #701).  Files are optional one by one —
# any present sprite is used, any absent one falls back to its placeholder.
ASSET_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets",
    "gear",
)
MANIFEST_FILE = "manifest.json"
BASE_SPRITE = "base_character.png"

# The manifest's reference doll canvas (base_character.png is exactly this),
# and the output upscale factor for a crisper Discord attachment.
_REF_W, _REF_H = 200, 300
_RENDER_SCALE = 2
_BG = (24, 26, 32)

# Built-in layout defaults, in reference-canvas coordinates:
# slot -> (anchor_cx, anchor_cy, scale).  The six set families mirror the
# seeded manifest (which overrides these when readable); tool/light/charm are
# compositor-local — they have no manifest entry yet.
DEFAULT_LAYOUT: dict[str, tuple[int, int, float]] = {
    equipment.HELMET: (100, 42, 0.4),
    equipment.CHARM: (100, 95, 0.12),
    equipment.CHESTPLATE: (100, 150, 0.55),
    equipment.LEGGINGS: (100, 222, 0.55),
    equipment.BOOTS: (100, 278, 0.35),
    equipment.WEAPON: (158, 165, 0.45),
    equipment.SHIELD: (42, 168, 0.38),
    equipment.TOOL: (32, 230, 0.28),
    equipment.LIGHT: (168, 235, 0.22),
}

# Tier palette fallback (the manifest's tier_palettes win when readable).
TIER_COLORS: dict[str, tuple[int, int, int]] = {
    "bronze": (184, 115, 51),
    "iron": (138, 143, 152),
    "silver": (192, 192, 200),
    "gold": (255, 210, 74),
    "diamond": (95, 227, 220),
}
_UNTIERED_COLOR = (150, 120, 90)
_FIGURE_COLOR = (90, 96, 110)
_OUTLINE = (16, 17, 21)

_SLOT_TO_FAMILY: dict[str, str] = {
    equipment.WEAPON: "sword",
    equipment.SHIELD: "shield",
    equipment.HELMET: "helmet",
    equipment.CHESTPLATE: "chestplate",
    equipment.LEGGINGS: "leggings",
    equipment.BOOTS: "boots",
}


@lru_cache(maxsize=8)
def _load_manifest(asset_dir: str) -> dict | None:
    """Parse ``manifest.json`` under *asset_dir* (None on any problem)."""
    try:
        with open(os.path.join(asset_dir, MANIFEST_FILE), encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def sprite_filename(item_name: str, manifest: dict | None = None) -> str:
    """The sprite filename for *item_name*.

    The manifest's family tables win; the fallback convention matches them
    exactly — tiered set gear is ``{family}_{tier}.png`` (the owner pack's
    own naming), set starters are the family base (``sword.png``), and
    everything else maps spaces to underscores (``iron_pickaxe.png``).
    """
    name = item_name.lower()
    tier = equipment.gear_tier(name)
    slot = equipment.slot_for(name)
    family = _SLOT_TO_FAMILY.get(slot or "")
    if family is not None and manifest is not None:
        entry = (manifest.get("families") or {}).get(family) or {}
        if tier is not None and isinstance(entry.get("tiers"), dict):
            filename = entry["tiers"].get(tier)
            if isinstance(filename, str):
                return filename
        elif tier is None and isinstance(entry.get("base"), str):
            return entry["base"]
    if family is not None:
        return f"{family}_{tier}.png" if tier is not None else f"{family}.png"
    return f"{name.replace(' ', '_')}.png"


def _layout_for(slot: str, manifest: dict | None) -> tuple[int, int, float]:
    """(anchor_cx, anchor_cy, scale) for *slot* — manifest first, defaults after."""
    family = _SLOT_TO_FAMILY.get(slot)
    if family is not None and manifest is not None:
        entry = (manifest.get("families") or {}).get(family) or {}
        anchor = entry.get("anchor")
        scale = entry.get("scale")
        if (
            isinstance(anchor, list)
            and len(anchor) == 2
            and isinstance(scale, (int, float))
        ):
            return int(anchor[0]), int(anchor[1]), float(scale)
    return DEFAULT_LAYOUT[slot]


def _tier_color(tier: str | None, manifest: dict | None) -> tuple[int, int, int]:
    if tier is None:
        return _UNTIERED_COLOR
    if manifest is not None:
        palette = (manifest.get("tier_palettes") or {}).get(tier)
        if isinstance(palette, list) and len(palette) == 3:
            return tuple(int(c) for c in palette)  # type: ignore[return-value]
    return TIER_COLORS.get(tier, _UNTIERED_COLOR)


@dataclass(frozen=True)
class CharacterLayer:
    """One equipped item to draw: resolved sprite path or placeholder data."""

    slot: str
    item: str
    # Pixel box (x, y, w, h) on the OUTPUT canvas, centred on the anchor.
    box: tuple[int, int, int, int]
    sprite_path: str | None  # None → draw the procedural placeholder
    color: tuple[int, int, int]


@dataclass(frozen=True)
class CharacterSpec:
    """A resolution-independent description of the doll to draw."""

    base_sprite_path: str | None  # None → draw the procedural figure
    layers: tuple[CharacterLayer, ...]
    width: int = _REF_W * _RENDER_SCALE
    height: int = _REF_H * _RENDER_SCALE


def _existing(path: str) -> str | None:
    return path if os.path.isfile(path) else None


def build_character_spec(
    equipped: dict[str, str],
    *,
    asset_dir: str | None = None,
) -> CharacterSpec:
    """Compose the render spec for an ``{slot: item}`` loadout (pure layout).

    Sprite resolution is the only filesystem touch.  Manifest ``scale`` is
    the factor applied to a sprite's intrinsic size (the seeded sprites are
    uniform 256×256), expressed here as a box centred on the anchor; the
    placeholder shapes draw inside the same box.  Slots render in
    body-first order (armor under the held items).
    """
    directory = ASSET_DIR if asset_dir is None else asset_dir
    manifest = _load_manifest(directory)
    layers: list[CharacterLayer] = []
    order = (
        equipment.CHESTPLATE,
        equipment.LEGGINGS,
        equipment.BOOTS,
        equipment.HELMET,
        equipment.CHARM,
        equipment.SHIELD,
        equipment.WEAPON,
        equipment.TOOL,
        equipment.LIGHT,
    )
    for slot in order:
        item = equipped.get(slot)
        if not item:
            continue
        cx, cy, scale = _layout_for(slot, manifest)
        side = int(256 * scale * _RENDER_SCALE)
        box = (
            cx * _RENDER_SCALE - side // 2,
            cy * _RENDER_SCALE - side // 2,
            side,
            side,
        )
        tier = equipment.gear_tier(item)
        layers.append(
            CharacterLayer(
                slot=slot,
                item=item.lower(),
                box=box,
                sprite_path=_existing(
                    os.path.join(directory, sprite_filename(item, manifest)),
                ),
                color=_tier_color(tier, manifest),
            ),
        )
    base_name = BASE_SPRITE
    if manifest is not None and isinstance(manifest.get("base_character"), str):
        base_name = manifest["base_character"]
    return CharacterSpec(
        base_sprite_path=_existing(os.path.join(directory, base_name)),
        layers=tuple(layers),
    )


def _draw_figure(draw, w: int, h: int) -> None:
    """The procedural base character (only if base_character.png is gone)."""
    cx = w // 2
    head_r = w // 9
    head_cy = int(h * 0.18)
    draw.ellipse(
        (cx - head_r, head_cy - head_r, cx + head_r, head_cy + head_r),
        fill=_FIGURE_COLOR,
        outline=_OUTLINE,
    )
    torso_w, torso_top, torso_bot = int(w * 0.16), int(h * 0.27), int(h * 0.55)
    draw.rectangle(
        (cx - torso_w, torso_top, cx + torso_w, torso_bot),
        fill=_FIGURE_COLOR,
        outline=_OUTLINE,
    )
    arm_w = int(w * 0.09)
    draw.rectangle(
        (cx - torso_w - arm_w, torso_top, cx - torso_w, int(h * 0.52)),
        fill=_FIGURE_COLOR,
        outline=_OUTLINE,
    )
    draw.rectangle(
        (cx + torso_w, torso_top, cx + torso_w + arm_w, int(h * 0.52)),
        fill=_FIGURE_COLOR,
        outline=_OUTLINE,
    )
    leg_w = int(w * 0.07)
    draw.rectangle(
        (cx - leg_w * 2, torso_bot, cx - 2, int(h * 0.9)),
        fill=_FIGURE_COLOR,
        outline=_OUTLINE,
    )
    draw.rectangle(
        (cx + 2, torso_bot, cx + leg_w * 2, int(h * 0.9)),
        fill=_FIGURE_COLOR,
        outline=_OUTLINE,
    )


def _draw_placeholder(draw, layer: CharacterLayer) -> None:
    """A per-family placeholder shape in the item's tier colour."""
    x, y, w, h = layer.box
    c, o = layer.color, _OUTLINE
    slot = layer.slot
    if slot == equipment.HELMET:
        draw.pieslice(
            (x, y + h // 4, x + w, y + h + h // 4),
            180,
            360,
            fill=c,
            outline=o,
        )
    elif slot == equipment.CHESTPLATE:
        pad = w // 5
        draw.rounded_rectangle(
            (x + pad, y + pad, x + w - pad, y + h - pad),
            radius=max(4, w // 12),
            fill=c,
            outline=o,
        )
    elif slot in (equipment.LEGGINGS, equipment.BOOTS):
        pad = w // 4
        mid = x + w // 2
        gap = max(3, w // 20)
        draw.rectangle((x + pad, y + pad, mid - gap, y + h - pad), fill=c, outline=o)
        draw.rectangle(
            (mid + gap, y + pad, x + w - pad, y + h - pad),
            fill=c,
            outline=o,
        )
    elif slot == equipment.WEAPON:
        bx = x + w // 2
        guard_y = y + h - h // 4
        draw.polygon(
            ((bx - w // 14, guard_y), (bx + w // 14, guard_y), (bx, y)),
            fill=c,
            outline=o,
        )
        draw.rectangle(
            (bx - w // 6, guard_y, bx + w // 6, guard_y + h // 16),
            fill=c,
            outline=o,
        )
        draw.rectangle(
            (bx - w // 24, guard_y + h // 16, bx + w // 24, y + h),
            fill=c,
            outline=o,
        )
    elif slot == equipment.SHIELD:
        pad = w // 6
        draw.ellipse((x + pad, y, x + w - pad, y + h), fill=c, outline=o)
    elif slot == equipment.TOOL:
        draw.arc((x, y, x + w, y + h), 200, 340, fill=c, width=max(3, w // 10))
        draw.line(
            (x + w // 2, y + h // 4, x + w // 2, y + h),
            fill=c,
            width=max(2, w // 12),
        )
    elif slot == equipment.LIGHT:
        draw.ellipse(
            (x + w // 6, y, x + w - w // 6, y + h - h // 4),
            fill=(255, 222, 120),
            outline=o,
        )
        draw.rectangle(
            (x + w // 2 - w // 10, y + h - h // 4, x + w // 2 + w // 10, y + h),
            fill=c,
        )
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

    img = Image.new("RGBA", (spec.width, spec.height), _BG)
    draw = ImageDraw.Draw(img)

    base = None
    if spec.base_sprite_path:
        try:
            base = Image.open(spec.base_sprite_path).convert("RGBA")
        except Exception:  # noqa: BLE001 — a corrupt sprite must not kill the panel
            base = None
    if base is not None:
        # NEAREST keeps the pixel-art placeholders crisp at 2× output.
        base = base.resize((spec.width, spec.height), Image.Resampling.NEAREST)
        img.alpha_composite(base)
    else:
        _draw_figure(draw, spec.width, spec.height)

    for layer in spec.layers:
        sprite = None
        if layer.sprite_path:
            try:
                sprite = Image.open(layer.sprite_path).convert("RGBA")
            except Exception:  # noqa: BLE001 — fall back to the placeholder
                sprite = None
        x, y, w, h = layer.box
        if sprite is not None:
            sprite.thumbnail((w, h))
            img.alpha_composite(
                sprite,
                (x + (w - sprite.width) // 2, y + (h - sprite.height) // 2),
            )
        else:
            _draw_placeholder(draw, layer)

    buffer = io.BytesIO()
    img.convert("RGB").save(buffer, format="PNG")
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
    "MANIFEST_FILE",
    "BASE_SPRITE",
    "DEFAULT_LAYOUT",
    "TIER_COLORS",
    "sprite_filename",
    "CharacterLayer",
    "CharacterSpec",
    "build_character_spec",
    "render_character",
    "render_character_for",
]
