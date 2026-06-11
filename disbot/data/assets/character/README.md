# Character sprite pack — drop zone

The paper-doll compositor (`disbot/utils/character_render.py`, V-16) reads
sprites from this directory **by naming convention** — drop PNGs here and the
next render uses them; no code change, no restart of anything but the bot.

| File | Used for |
|---|---|
| `base_character.png` | The base figure every item is drawn onto |
| `{family}_{tier}.png` | One set item, e.g. `sword_diamond.png`, `boots_gold.png`, `chestplate_iron.png` |
| `{item_name}.png` (spaces → `_`) | Any other gear, e.g. `iron_pickaxe.png`, `lucky_charm.png`, `torch.png` |

Families: `sword`, `shield`, `helmet`, `chestplate`, `leggings`, `boots`.
Tiers: `bronze`, `iron`, `silver`, `gold`, `diamond` (= `utils/equipment.py`
`TIER_ORDER`). This matches the owner's existing PythonAnywhere pack naming
(`temp/`, 2025-08-10) 1:1 — the pack can be committed here as-is.

Any sprite that is missing falls back to a procedural placeholder shape in
the tier's palette colour, so partial packs are fine. Transparent-background
PNGs look best; images are scaled to fit each slot's anchor box
(`SLOT_ANCHORS`).
