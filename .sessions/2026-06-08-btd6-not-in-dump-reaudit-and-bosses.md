# 2026-06-08 — BTD6 "not in the dump" re-audit + Boss Bloons ingest

Four PRs this session, all on the BTD6 data-mapping plan. Theme that emerged:
**prior "not in the dump / hardcoded" verdicts were repeatedly wrong because a
session read the top-level model and never opened the nested `mutatorMods[]` /
`behaviors[]` array.** The maintainer's "it has to be there" instinct was right
three times.

## PRs
- **#597 — buff stack cap parser-reproducible** (MERGED). `_buffs()` dropped the
  stack cap; cutover path would lose "(stacks up to N)". Forward-looking fidelity fix.
- **#598 — Monkey Knowledge effect magnitudes** (MERGED). The headline correction.
  Magnitudes live in `mod.mutatorMods[]` (More Cash `StartingCash{addition 200}`,
  Bonus Monkey `FreeTower{baseTowerID DartMonkey}`, …). `_mk_effect` faithful
  passthrough → `effect.factors[]` on `btd6_monkey_knowledge_lookup`. 119/134 carry one.
- **#599 — dump re-audit docs** (open). Swept all 18 domains, re-verified every
  "not in dump" claim. Corrected: **mode rules** (Mods/ has the full set —
  CHIMPS = `Clicks.json`!) and **per-pop cash** (`DistributeCashModel{cash:1.0}`).
  Held: map removables, opaque theme enums, DDT cap. Recorded the missing-data backlog.
- **#600 — Boss Bloons** (open). The biggest real gap. All 7 bosses (Bloonarius…
  Diamondback) → `bosses.json` + `BossEntry` + `btd6_boss_lookup`. Per-tier
  health/speed, derived immunities, game-authored mechanic descriptions.

## Durable facts learned (for next session)
- **`--overlay` only refreshes `{range, footprintRadius}`** — never `buffs[]`. Committed
  buffs are a fuller/older extraction; the lean `_buffs()` is the *cutover* path.
- **Dump nests effects one level down.** Knowledge: `mod.mutatorMods[]`. Game modes:
  `Mods/<mode>.json` top-level `mutatorMods[]` (file IS the ModModel). Bloons: `behaviors[]`
  (DistributeCashModel). Bosses: `Bloons/<Boss>/<Boss>{1..5}.json`. Always descend +
  run `explore_gamedata.py --search <Model> --struct` before declaring data absent.
- **Bloons/ is dir-per-family** (`Bloons/Bad/Bad.json`, variants alongside), NOT flat.
  A `glob('Bloons/*.json')` matches nothing — use `Bloons/*/*.json`.
- **Boss roster = `Bosses/` folder** (7, incl. Diamondback). `BossData.LocsKey` → textTable
  name/`<key>InfoPanelDescription`/`<key>TagLine{,2}`. Phayze `isCamo` is **False**
  (camo is a runtime Reality-Shield) — don't derive a camo flag from it.
- **Still-missing backlog** (in dump, not fetched): mode-rules cutover (Mods/),
  alternate round sets (Rounds/ has many sets, we use default 140), Achievements (156),
  Rogue Legends / Frontier (Artifacts/, rogueData.json, frontierData.json — niche).
  `frontierData.json` is the **Wild-West Frontier** Legends mode (coverage map mislabels
  it "Boss/Legends scaling").

## Process notes
- The git stash/branch-off-main dance worked cleanly for splitting independent batches
  into separate PRs (MK off main, re-audit off main, bosses off main). Verify
  `git diff origin/main --stat` is the expected file set before pushing.
- `send_later` is NOT available this env; can't arm the hour-out PR check-in. A Monitor
  can't reach GitHub (no `gh` CLI). Rely on the webhook subscription for CI-failure/review.
- Bare `black .` includes `tests/` (out of CI scope) — trust `check_quality.py`. The
  black↔ruff trailing-comma interaction on a wrapped call: extract a local var instead.
