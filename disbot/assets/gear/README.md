# Gear sprite pack — drop zone

The paper-doll compositor (`disbot/utils/character_render.py`, V-16) renders
from this directory. The current PNGs are **generated placeholders**
(`scripts/gen_gear_placeholder_sprites.py` — deterministic, rerunnable; the
owner's shapes recreated as code, PR #701). **The owner's original PNG pack
replaces them file-for-file** — same names, drop them in, next render uses
them; no code change.

| File | Used for |
|---|---|
| `base_character.png` | The 200×300 base doll every item is drawn onto |
| `{family}_{tier}.png` | One set item, e.g. `sword_diamond.png`, `boots_gold.png` |
| `{family}.png` | The untiered starter of a set family (`sword.png`, `shield.png`) |
| `{item_name}.png` (spaces → `_`) | Any other gear, e.g. `iron_pickaxe.png`, `torch.png` |
| `manifest.json` | The layout authority — anchors/scales/palettes. Stays when sprites are replaced |

Families: `sword`, `shield`, `helmet`, `chestplate`, `leggings`, `boots`.
Tiers: `bronze`, `iron`, `silver`, `gold`, `diamond` (= `utils/equipment.py`
`TIER_ORDER`).

**Manifest semantics (the compositor's contract):** each family's `anchor`
is the sprite's centre on the 200×300 reference doll; `scale × 256` is the
square box (reference px) the sprite is thumbnail-fitted into. Tune layout
by editing `FAMILIES` in the generator and re-running it (it rewrites the
manifest + placeholder sprites together), or by editing `manifest.json`
directly once the real pack is in. Any sprite that is missing or unreadable
falls back to a procedural placeholder shape in the tier's palette colour —
partial packs are fine.
