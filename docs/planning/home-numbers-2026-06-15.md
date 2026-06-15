# Mining Home structure — pinned numbers (Slice C)

> **Status:** `reference` — the tuned defaults for the §7.5 **Home** structure
> (mining Slice C), mirrored by `tests/unit/utils/test_mining_structures.py`. The
> code in `utils/mining/structures.py` (build ladder/level names) and
> `utils/character_render.py` (backdrop palette) is the source of truth; this doc
> records *why* the numbers are what they are. Change both together.

## What Home is

A **built**, purely cosmetic structure: each level gives the player's Character
card a richer **backdrop colour**. It is a coin + material **sink** with a visible
reward — never a gameplay gate (contrast the Forge, which gates gold/diamond gear).
Reuses #905's generic `mining_structures` table + `build_structure`.

**Additive guarantee:** Home level 0 (unbuilt) maps to `backdrop=None` → the
default `_BG`, so the Character card renders **byte-identical** to before Slice C.

## Levels (`_HOME_LEVEL_NAMES` + `_HOME_BUILD_LADDER`)

| Level | Name | Build cost (from prev level) | Backdrop (`HOME_BACKDROPS`) |
|---|---|---|---|
| 0 | (not built) | — | none → default `_BG` `(24, 26, 32)` |
| 1 | Cozy Cabin | 2,000 🪙 + 30 wood + 20 stone | warm brown `(43, 34, 28)` |
| 2 | Stone Keep | 5,000 🪙 + 50 stone + 15 iron | cool slate `(40, 46, 54)` |
| 3 | Grand Hall | 12,000 🪙 + 15 gold + 3 diamond | regal indigo `(34, 30, 58)` |

`MAX_HOME_LEVEL = 3` (= the ladder length).

## Why these numbers

- **Rising cost, mixed materials.** Each tier pulls a different material band
  (wood/stone → stone/iron → gold/diamond), so building the Home draws on the
  whole mining ladder rather than one resource — a broad sink.
- **Cheaper than the Forge at tier 1** (2,000 vs 3,000 🪙) because Home is a
  cosmetic want, not a power gate — an early, satisfying first build.
- **Grand Hall (tier 3) costs diamond** so the top backdrop is a genuine
  end-game flex, matching the diamond-tier gear it visually frames.
- **Backdrop colours** are deliberately low-saturation and dark so the
  paper-doll sprite + tier-coloured gear stay readable on top (the card composites
  the doll over the backdrop). All three are darker than mid-grey.

## Verification

`tests/unit/utils/test_mining_structures.py` pins the ladder length, the
level-name mapping, the build-cost lookup (incl. the maxed `None`), and the
`home_backdrop` palette (incl. level 0 → `None`, the byte-identical property).
