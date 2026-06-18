# Fishing — ecosystem #2 (the second character-platform activity)

> **Status:** `plan` — promoted from idea → plan under the open
> idea→plan gate (Q-0172, 2026-06-17). Fishing is the **owner-ratified
> ecosystem #2** (V-13/Q-0090, the 2026-06-10 teardown verdict). This plan
> synthesizes the three source threads that named fishing but never gave it a
> build plan:
>
> - `docs/planning/rpg-survival-difficulty-design-2026-06-10.md` **P3**
>   ("Fishing + campfire/cooking") + its "Open" note: *"Fishing may be promoted
>   from P3 activity to ecosystem #2 … keep its seams ecosystem-ready (own loot
>   ladder, local-currency hook, collection-log hook)."*
> - `docs/planning/mining-hub-redesign-2026-06-15.md` — the open-world **Explore**
>   hub leads with `🎣 Fishing`, a separate explorer not tied to mine depth.
> - `docs/ideas/mining_exploration_brainstorm.md` §7 — the character platform:
>   shared **game-XP**, gathering verbs (mine/chop/**fish**/explore).
>
> **Provenance:** self-initiated dispatch promotion (no work order this run);
> flagged on the run-report `⚑ Self-initiated` line.

## Why fishing (and why now)

The buildable `ready` queue is consumed (current-state ▶ Next action): the BTD6
deterministic-floor lane is exhausted, the dashboard write lanes are owner-paced,
and the two open product PRs (#929 security, #941 image-mod) are `needs-hermes-review`
carve-outs. Q-0172 opened the idea→plan gate precisely for this shortage, and
named **fishing** the canonical first candidate. Fishing is the lowest-risk large
build available: it is a **pure additive minigame** (a new cog + new tables; no
existing behaviour changes), it has a **proven architectural template** (mining),
and it is the owner's already-ratified next ecosystem.

## Architecture — fishing mirrors mining exactly

Mining is the decomposition template (`docs/architecture.md` §"Subsystem
decomposition"). Fishing reuses every seam:

| Layer | Mining | Fishing |
|---|---|---|
| Pure domain | `utils/mining/` | `utils/fishing/` (catalog + roll) |
| Audited write boundary | `services/mining_workflow.py` | `services/fishing_workflow.py` |
| Shared progression | `services/game_xp_service.py` `GAME_MINING` | same service, `GAME_FISHING` |
| Currency | `economy_service.credit_in_txn` (the audited coin seam) | same |
| DB CRUD | `utils/db/games/mining*.py` | `utils/db/games/fishing.py` |
| Cog (plumbing only) | `cogs/mining_cog.py` | `cogs/fishing_cog.py` |
| Registry | `subsystem_registry.SUBSYSTEMS["mining"]` | `["fishing"]` |

Invariants honoured: no raw SQL outside `utils/db/`; every write through the
workflow service inside ONE `db.transaction()`; coin credit through the audited
`economy_service` seam; game-XP awarded with the owning `conn` and events emitted
**after** commit.

## The ecosystem-ready seams (the survival-plan requirement)

P3's "Open" note requires fishing's seams to be ecosystem-ready so a later
promotion *extends* rather than *rewrites* it. This plan bakes all three in from
PR 1:

1. **Own loot ladder** — `utils/fishing/fish.py` is a self-contained species
   catalog with rarity weights, never a reskin of ore weights.
2. **Local-currency hook** — each catch pays coins (the shared economy) through
   the audited seam; a fish-specific currency can later be layered without
   touching the loop.
3. **Collection-log hook** — `fishing_catch_log` records per-species count +
   best weight + first/last caught: the "collection log" the ecosystem vision
   wants, available from day one.

## Build slices

### PR 1 — the core loop (this session)

A complete, rewarding minigame on its own:

- **Domain** `utils/fishing/`:
  - `fish.py` — the `FishSpecies` catalog (name, emoji, rarity tier, coin value
    band, weight band) + lookups. Pure, stdlib-only, fully tested.
  - `rewards.py` — `roll_catch(rng, *, rod_bonus=0)` → a `Catch` (species,
    weight, coin value). Rarity-weighted; seed-deterministic for tests.
- **Migration** `075_fishing_catch_log.sql` — the per-(user, guild, species)
  collection log (`BIGINT` user/guild to match player-progression identity, the
  `mining_structures`/`game_xp` precedent, not `mining_inventory`'s legacy TEXT).
- **DB** `utils/db/games/fishing.py` — `get_fishing_log`, `record_catch`
  (conn-aware, upsert: bump count + total value, keep best weight, stamp times),
  `top_fishers`; wired into `utils/db/__init__.py`.
- **Service** `services/fishing_workflow.py` — `fish(user_id, guild_id)`: roll a
  catch, then in ONE transaction record it + credit coins
  (`economy_service.credit_in_txn`) + award `GAME_FISHING` XP; emit balance +
  XP events post-commit. Returns a frozen `FishResult`.
- **Game-XP** — add `GAME_FISHING = "fishing"` + a `"fish"` award row to
  `game_xp_service`.
- **Cog** `cogs/fishing_cog.py` — `!fish` (cast), `!fishlog` (your collection),
  `!fishtop` (server's top anglers); a Help-menu hook; guild-only.
- **Registration** — `subsystem_registry` entry (hub-less, Help-hooked, like
  `welcome`/`counters`/`security`), `config.INITIAL_EXTENSIONS`, and the doc
  surface maps (`help-command-surface-map.md`,
  `setup-platform/settings-customization-command-map.md`, `repo-navigation-map.md`,
  `ownership.md`).
- **Tests** — domain (catalog integrity, roll distribution/determinism),
  workflow (a fake-pool harness pins the atomic legs), and the enumeration
  touch-point tests stay green.

### PR 2+ (later, not this session)

- **Rods & bait** — a small gear ladder (better rod → `rod_bonus`), bought with
  coins; mirrors the mining tool ladder.
- **Water biomes** — gate fishing locations (pond → lake → ocean) with their own
  species pools; the survival plan's "fishing gated to water-bearing biomes".
- **Cooking** — raw fish → cooked food (the survival P3 campfire loop), once the
  survival hunger/energy layer (P1/P2) lands.
- **The Explore hub** — fold `!fish` into the `🎣 Fishing` button of the
  open-world Explore panel (`mining-hub-redesign`), with a persistent view.
- **Leaderboard polish** — biggest-catch records, rarity-completion titles
  (the titles seam, like mining).

## Risks / non-goals

- **Balance:** coin payouts are deliberately modest in PR 1 (a fish is worth less
  than a mined gem) and live in one pure table for easy retune; the daily soft
  cap on game-XP (`game_xp_service.DAILY_SOFT_CAP`) already throttles grind.
- **No survival coupling yet:** PR 1 does **not** touch hunger/energy — that
  layer (survival P1/P2) is not built. Fishing stands alone until then.
- **Additive safety:** an empty `fishing_catch_log` + a never-loaded cog is
  byte-identical to today; the only behaviour is the new commands.
