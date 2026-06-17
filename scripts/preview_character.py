#!/usr/bin/env python3
"""Preview the mining paper-doll character render locally — no Discord needed.

Renders the V-16 character compositor (``disbot/utils/character_render.py``) to a
PNG you can open, so iterating on the **sprite pack + positioning** takes seconds
instead of the upload-to-Discord-and-eyeball loop. Render one tier, a custom
loadout, or a contact sheet of every tier; point it at the live assets dir or a
candidate pack you are trying out.

Examples:
    # contact sheet of all five tiers -> /tmp/character_preview.png
    python3 scripts/preview_character.py

    # one full set
    python3 scripts/preview_character.py --tier diamond

    # a tier set plus the mining tools (pickaxe / lantern / charm)
    python3 scripts/preview_character.py --tier gold --mining

    # a hand-picked loadout (slot=item, comma-separated)
    python3 scripts/preview_character.py --loadout "weapon=diamond sword,helmet=gold helmet"

    # preview a candidate pack in another folder (its manifest.json + PNGs)
    python3 scripts/preview_character.py --asset-dir /tmp/my_new_pack --out /tmp/new_pack.png

Tuning positioning: edit ``disbot/assets/gear/manifest.json`` (a family's
``anchor`` = its centre on the 200x300 doll; ``scale`` x 256 = its box) and
re-run — the render reflects the change immediately, no code edit.

Provenance (Q-0105 dev tooling): added 2026-06-17 to kill the manual
sprite-positioning loop (owner reported ~100+ upload/retest rounds). Pure dev
convenience — stdlib + Pillow (already the render dependency) + the live
compositor, so the preview is the exact image the bot ships. Not CI-wired.
Delete if it stops earning its keep.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

# The bot's source root is ``disbot/`` (its modules import as ``from utils import
# ...``); put it on the path so we reuse the *live* compositor — the preview is
# then the exact render the bot produces, not a reimplementation.
_DISBOT = Path(__file__).resolve().parents[1] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from utils import character_render, equipment  # noqa: E402  (path-dependent import)

# Default output lives in the OS temp dir (portable; avoids a hardcoded /tmp).
_DEFAULT_OUT = str(Path(tempfile.gettempdir()) / "character_preview.png")


def _full_set(tier: str, *, mining: bool) -> dict[str, str]:
    """A complete same-tier combat set, optionally plus the mining tools."""
    loadout = {
        equipment.WEAPON: f"{tier} sword",
        equipment.SHIELD: f"{tier} shield",
        equipment.HELMET: f"{tier} helmet",
        equipment.CHESTPLATE: f"{tier} chestplate",
        equipment.LEGGINGS: f"{tier} leggings",
        equipment.BOOTS: f"{tier} boots",
    }
    if mining:
        loadout.update(
            {
                equipment.TOOL: "diamond pickaxe",
                equipment.LIGHT: "diamond lantern",
                equipment.CHARM: "lucky charm",
            },
        )
    return loadout


def _parse_loadout(spec: str) -> dict[str, str]:
    """Parse ``slot=item,slot=item`` into an ``{slot: item}`` loadout."""
    loadout: dict[str, str] = {}
    for raw in spec.split(","):
        pair = raw.strip()
        if not pair:
            continue
        if "=" not in pair:
            raise SystemExit(f"bad --loadout segment {pair!r} (want slot=item)")
        slot, item = (p.strip() for p in pair.split("=", 1))
        if slot not in equipment.SLOTS:
            raise SystemExit(
                f"unknown slot {slot!r}; valid: {', '.join(equipment.SLOTS)}",
            )
        loadout[slot] = item
    return loadout


def _render_one(loadout: dict[str, str], asset_dir: str | None) -> bytes:
    png = character_render.render_character_for(loadout, asset_dir=asset_dir)
    if png is None:
        raise SystemExit(
            "render returned None — Pillow is not installed (pip install Pillow) "
            "or the assets are unreadable.",
        )
    return png


def _contact_sheet(asset_dir: str | None, *, mining: bool) -> bytes:
    """Render every tier side by side with a label — the whole pack at a glance."""
    from io import BytesIO

    from PIL import Image, ImageDraw

    pad, label_h = 12, 22
    tiles = [
        (
            tier,
            Image.open(BytesIO(_render_one(_full_set(tier, mining=mining), asset_dir))),
        )
        for tier in equipment.TIER_ORDER
    ]
    tile_w = max(t.width for _, t in tiles)
    tile_h = max(t.height for _, t in tiles)
    sheet = Image.new(
        "RGB",
        (len(tiles) * tile_w + (len(tiles) + 1) * pad, tile_h + label_h + 2 * pad),
        (18, 19, 23),
    )
    draw = ImageDraw.Draw(sheet)
    for i, (tier, tile) in enumerate(tiles):
        x = pad + i * (tile_w + pad)
        sheet.paste(
            tile.convert("RGB"),
            (x + (tile_w - tile.width) // 2, label_h + pad),
        )
        draw.text((x + 4, pad // 2), tier.upper(), fill=(220, 220, 230))
    out = BytesIO()
    sheet.save(out, format="PNG")
    return out.getvalue()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Preview the character render locally.",
    )
    parser.add_argument(
        "--tier",
        choices=equipment.TIER_ORDER,
        help="render one full same-tier set",
    )
    parser.add_argument("--loadout", help="custom 'slot=item,slot=item' loadout")
    parser.add_argument(
        "--mining",
        action="store_true",
        help="also equip the mining tools (pickaxe / lantern / charm)",
    )
    parser.add_argument(
        "--asset-dir",
        help="render from this pack dir (manifest + PNGs) instead of the live one",
    )
    parser.add_argument(
        "--out",
        default=_DEFAULT_OUT,
        help=f"output PNG path (default: {_DEFAULT_OUT})",
    )
    args = parser.parse_args(argv)

    if args.loadout:
        png, what = (
            _render_one(_parse_loadout(args.loadout), args.asset_dir),
            "custom loadout",
        )
    elif args.tier:
        png = _render_one(_full_set(args.tier, mining=args.mining), args.asset_dir)
        what = f"{args.tier} full set"
    else:
        png, what = (
            _contact_sheet(args.asset_dir, mining=args.mining),
            "contact sheet (all tiers)",
        )

    out = Path(args.out)
    out.write_bytes(png)
    print(f"wrote {what} -> {out}  ({len(png)} bytes)")
    print(f"assets: {args.asset_dir or character_render.ASSET_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
