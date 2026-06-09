# Mining → character-platform foundation

**Branch:** `claude/eloquent-ptolemy-cmusuj` · **Date:** 2026-06-08

A long brainstorm-then-build session. Refined the maintainer's mining idea into a
whole-bot **character platform** vision, then laid the first foundation slices for it.

## What shipped (commits, newest-first)
- `6c5c800` — **exploration reads equipped gear's `EffectiveStats`** (scaling: mining_power
  2→×2 / 4→×3 ore, loot_bonus flat; gating from *equipped* gear, which fixed a latent bug —
  a lantern in the LIGHT slot now satisfies the torch-gated deep finds). `explore_from_state`
  replaced `explore_from_inventory`.
- `dbf7524` — **equipment seam**: migration 060 `mining_equipment` + `utils/db/games/mining_equipment.py`
  + pure `cogs/mining/equipment.py` (slots tool/light/charm; `EffectiveStats` read model; `compute_stats`)
  + `!equip`/`!unequip`/`!gear`.
- `6f5d4ad` — **correction** (see Learnings).
- `9344a6c` — typed **Inventory** panel + net worth (wired the dormant `items.py`).
- `50a5a46` — **Wave 0**: `!explore` made loadout/depth-aware (wired the dormant `exploration.py`).
- `6e5a605` — brainstorm doc §6/§7: the character-platform vision (decisions, roadmap).

All green through `python3.10 scripts/check_quality.py --full` before each push.

## Learnings / gotchas (read before extending mining)
- **Mining is an *intentional direct-lane domain* — NOT an audit-service gap.** I was about to
  build an "audited mining mutation service" (my own framing + a wrong §7.5 note said `!build`
  was an un-audited gap). Reading the binding contracts *first* (the mutation-and-db rule) caught
  it: `ownership.md` routes `mining_inventory` **"direct via `utils/db/games/mining.py`"**, and the
  RC-8A ledger (`docs/audits/direct-db-exception-ledger.md`) catalogues it as **`accepted-direct-write`**
  ("a mutation service is a *future option, not a current violation*"). Lightweight game state
  (mining/chain/counting/deathmatch/rps) is direct-lane by design; audited services are for
  value/config/governance (economy, xp, moderation, governance). **A mining service is only
  warranted when crafting goes cross-domain (spends coins → `economy_service`) or grows durability
  state.** Don't repeat the mistake.
- **`views/ → cogs/` is a layer error.** The pure mining engines (`exploration`, `items`,
  `equipment`) live in `cogs/mining/`, so views import them **lazily inside the handler** (module-level
  would be a *new* arch-fix-13 violation). The real fix — relocating the pure engines to a shared
  layer so `services/` can build on them too — is deferred (brainstorm §7.4).
- **`EffectiveStats` is the platform's "one stat block."** Gear feeds it now (`compute_stats`);
  skills + combat gear (`damage`/`defense`/`max_health`, reserved) feed it later. Every game reads
  the subset it cares about — no game imports the item catalog.
- DB tests **mock the pool** (`patch("...pool.fetchall")` + assert SQL/params); migrations are
  production-only, not applied under test. CI **excludes `tests/`** from black/isort/ruff — ignore
  ruff "errors" from running it on a test file directly.

## Next steps (per brainstorm §7.7 roadmap)
The character spine + Wave-1 inventory/equipment are in. Remaining, each its own slice:
- **Persistent depth** (Wave 1): `mining_player_state` + a thin owner; explore/mine use the real
  biome instead of always SURFACE. Needs one owner call: how torch/lantern gate descent (§6.8).
- **Combat gear + deathmatch reads stats** (Wave 1): add sword/armor items → `damage`/`defense`,
  make deathmatch read `EffectiveStats` instead of hardcoded HP/dmg. (Fills the reserved combat slots.)
- **Sell-ore / buy-gear market** (Wave 1): coins integration — *this* leg routes through
  `economy_service` (genuine cross-domain service).
- **Game-XP service** (Wave 2): the shared cross-game XP track (mirrors the audited `xp_service`),
  + the capped 4-branch skill tree feeding `EffectiveStats`.
- **Profile card / paper-doll** (Wave 3): `utils/mining_render` already exists; Pillow is in
  `requirements.txt`.
