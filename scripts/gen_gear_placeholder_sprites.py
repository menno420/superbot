"""Generate the placeholder gear sprite set + manifest (V-16 / Q-0092).

Provenance (2026-06-11): these sprites are CODE RECREATIONS of the owner's
base-item images shared in chat (flat single-color shapes: stick-figure base
character, sword, helmet, chestplate, leggings, boots, shield) — the original
PNG pack lives on the owner's PythonAnywhere and swaps in file-for-file when
uploaded (same names, same manifest). Until then these are the working set:
design-identical placeholders, byte-new.

Output: ``disbot/assets/gear/`` — base_character.png, six family bases
(owner-cyan), 6 families x 5 tiers = 30 tiered sprites (palette recolors),
and ``manifest.json`` (slots per Q-0092 set-piece model, per-slot anchors on
the reference doll, tier palettes). Deterministic — rerun any time.

Usage:  python3.10 scripts/gen_gear_placeholder_sprites.py
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

OUT_DIR = Path(__file__).resolve().parents[1] / "disbot" / "assets" / "gear"

BASE_CYAN = (0, 191, 255, 255)
TIER_PALETTES: dict[str, tuple[int, int, int, int]] = {
    "bronze": (184, 115, 51, 255),
    "silver": (192, 192, 200, 255),
    "gold": (255, 210, 74, 255),
    "iron": (138, 143, 152, 255),
    "diamond": (95, 227, 220, 255),
}

# Reference doll canvas the manifest anchors refer to.
DOLL_SIZE = (200, 300)


def _canvas(
    size: tuple[int, int] = (256, 256)
) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def draw_base_character() -> Image.Image:
    """The owner's stick figure: gray head, black stick body."""
    img, d = _canvas(DOLL_SIZE)
    head = (62, 17, 138, 93)  # circle bbox, center (100, 55)
    d.ellipse(head, fill=(205, 205, 205, 255))
    line = (20, 20, 24, 255)
    w = 7
    d.line((100, 93, 100, 210), fill=line, width=w)  # torso
    d.line((100, 120, 45, 170), fill=line, width=w)  # left arm
    d.line((100, 120, 155, 170), fill=line, width=w)  # right arm
    d.line((100, 210, 60, 285), fill=line, width=w)  # left leg
    d.line((100, 210, 140, 285), fill=line, width=w)  # right leg
    return img


def draw_helmet(color: tuple[int, int, int, int]) -> Image.Image:
    """Owner shape: full circle with a short rectangular neck below."""
    img, d = _canvas()
    d.ellipse((48, 28, 208, 188), fill=color)
    d.rectangle((98, 180, 158, 228), fill=color)
    return img


def draw_chestplate(color: tuple[int, int, int, int]) -> Image.Image:
    """Owner shape: the blocky t-shirt."""
    img, d = _canvas()
    d.polygon(
        [
            (58, 48),  # left shoulder top
            (108, 48),
            (108, 86),  # neck notch
            (148, 86),
            (148, 48),
            (198, 48),  # right shoulder top
            (198, 120),
            (168, 120),  # right sleeve end
            (168, 208),
            (88, 208),  # hem
            (88, 120),
            (58, 120),  # left sleeve end
        ],
        fill=color,
    )
    return img


def draw_leggings(color: tuple[int, int, int, int]) -> Image.Image:
    """Owner shape: the wide low rectangle."""
    img, d = _canvas()
    d.rectangle((58, 150, 198, 215), fill=color)
    return img


def draw_boots(color: tuple[int, int, int, int]) -> Image.Image:
    """Owner shape: the square."""
    img, d = _canvas()
    d.rectangle((73, 73, 183, 183), fill=color)
    return img


def draw_shield(color: tuple[int, int, int, int]) -> Image.Image:
    """Owner shape: the pentagon, apex up."""
    img, d = _canvas()
    d.polygon(
        [(128, 38), (213, 103), (181, 208), (75, 208), (43, 103)],
        fill=color,
    )
    return img


def draw_sword(color: tuple[int, int, int, int]) -> Image.Image:
    """Owner shape: thin vertical blade with the block guard/grip at the bottom."""
    img, d = _canvas()
    d.rectangle((121, 28, 135, 178), fill=color)  # blade
    d.rectangle((93, 178, 163, 198), fill=color)  # crossguard block
    d.rectangle((121, 198, 135, 228), fill=color)  # grip
    return img


FAMILIES = {
    "helmet": (draw_helmet, "helmet", (100, 42), 0.40),
    "chestplate": (draw_chestplate, "chestplate", (100, 150), 0.55),
    "leggings": (draw_leggings, "leggings", (100, 222), 0.55),
    "boots": (draw_boots, "boots", (100, 278), 0.35),
    "shield": (draw_shield, "shield", (42, 168), 0.38),
    "sword": (draw_sword, "weapon", (158, 165), 0.45),
}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    draw_base_character().save(OUT_DIR / "base_character.png")
    count = 1
    manifest: dict[str, object] = {
        "provenance": (
            "Placeholder sprites recreated as code from the owner's base-item "
            "images (2026-06-11). The original PNG pack replaces these "
            "file-for-file when uploaded; the manifest stays."
        ),
        "reference_canvas": list(DOLL_SIZE),
        "base_character": "base_character.png",
        "tier_palettes": {tier: list(rgba[:3]) for tier, rgba in TIER_PALETTES.items()},
        "families": {},
    }
    for family, (draw, slot, anchor, scale) in FAMILIES.items():
        draw(BASE_CYAN).save(OUT_DIR / f"{family}.png")
        count += 1
        tiers: dict[str, str] = {}
        for tier, rgba in TIER_PALETTES.items():
            name = f"{family}_{tier}.png"
            draw(rgba).save(OUT_DIR / name)
            tiers[tier] = name
            count += 1
        manifest["families"][family] = {  # type: ignore[index]
            "slot": slot,
            "base": f"{family}.png",
            "tiers": tiers,
            "anchor": list(anchor),
            "scale": scale,
        }
    (OUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {count} sprites + manifest.json -> {OUT_DIR}")


if __name__ == "__main__":
    main()
