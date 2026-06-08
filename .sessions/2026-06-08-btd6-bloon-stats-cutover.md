# 2026-06-08 — BTD6 bloon-stats cutover (health/speed/fortified → game data)

**Branch:** `claude/btd6-bloon-stats-cutover` · follows the not-in-dump re-audit + boss PRs.

## Task
Owner picked (AskUserQuestion) **bloon-stats cutover** as the next build, and **"Everything"**
as the completeness target (map every domain incl. cosmetic — captured in the roadmap).

## What shipped
Extended `overlay_bloons` (the existing children+immunity overlay) to also source
`health`, `speed`, and `health_fortified` from the dump:
- `health` ← `maxHealth`, `speed` ← `speed` (the dump speed is **already in the curated
  units** — Red 25, Ceramic 62.5, BFB 6.25 — so no normalization).
- `health_fortified` ← the bloon's **Fortified variant** model's `maxHealth`, via a new
  `_select_bloon_variant_model(bloon, index, extra={"fortified"})` helper.
- **Verified 23/23 byte-identical** (0 corrections) — pure provenance + reproducibility,
  exactly like the immunity cutover. The curated combat numbers were already right.
- `rbe`/`rbe_fortified` stay **derived** (health+children), pinned by `test_btd6_rbe.py`
  — that test is the tripwire if a future dump health moves without an rbe reconcile.
- Provenance marker broadened: `children_immunity_source` → `game_sourced_fields` (list)
  + `game_sourced_fields_source`. Nothing reads it (pure provenance), safe to rename.
- Coverage map regenerated (Bloons note updated).

## Key facts (for next session)
- **Curated bloon `speed` == dump `speed` units** (no relative normalization needed).
- **Fortified variants** live alongside the base in `Bloons/<Family>/` (`CeramicFortified`
  maxHealth 20, `MoabFortified` 400, `LeadFortified` 4, `BfbFortified` 1400) and match
  curated `health_fortified` exactly.
- `overlay_bloons` reads `_DATA_ROOT/bloons.json` directly → unit-test it by
  `monkeypatch.setattr(mod, "_DATA_ROOT", tmp)` with a tiny bloons.json + tmp dump.

## Remaining "map everything" backlog (owner wants ALL domains; see roadmap)
- **Cutovers/verify:** tower stats (the big gated one), **mode-rules** (`Mods/` — teed up).
- **New gameplay:** boss skull mechanics (decodable: `HealthPercentTrigger` +
  `SpawnBloonsAction`), alternate round sets (ABR 140, Endurance 205).
- **Niche:** Rogue Legends (`Artifacts/` 568 + `rogueData.json`), Frontier
  (`frontierData.json`), Achievements (156).
- **Cosmetic (owner said include):** Skins (51), TrophyStoreItems (424), BloonOverlays
  (46), `resources.json` (asset GUIDs), `Buffs/` (UI icons). Low Q&A value but in scope.

## Verification
`check_quality.py --full` green (8167 passed); `check_architecture --mode strict` 0 errors.
Bloon overlay run: "0 corrections — provenance recorded."
