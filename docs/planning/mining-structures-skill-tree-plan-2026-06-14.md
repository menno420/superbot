# Mining — structures (§7.5) + capped skill tree (§7.4): turn-key build plan

> **Status:** `plan` — promotes the mining brainstorm's §7.4 (skill tree) and §7.5 (Forge / Vault /
> Home structures) from `ideas` into **executable, PR-sized slices**. Source-verified 2026-06-14
> against live code. **Folio:** [`subsystems/games.md`](../subsystems/games.md) · **Vision:**
> [`ideas/mining_exploration_brainstorm.md`](../ideas/mining_exploration_brainstorm.md) §7. Source +
> merged PRs win over this doc.

## ▶ For the autonomous / night executor (read this first)

This plan exists so a session with **little steering can build mining end-to-end**. The owner's
standing steer (2026-06-14): *bot-side product work, mining cog + related, is welcome unattended —
**you can work as long as you want, executing any documented slice below**.*

- The slices are **independent and additive** — pick any **▶ startable** one, ship it, pick the next.
  Recommended order is **D (skill tree) → A (vault cap) → B (forge) → E (respec) → F (titles) → C
  (home)**, but they don't hard-depend on each other except where noted.
- **One PR per slice**, born-red per Q-0133 (open the `.sessions/` card `in-progress`, flip to
  `complete` last). Keep runtime PRs small and focused (CLAUDE.md).
- **Verify every slice** before flipping the card: `python3.10 scripts/check_quality.py --full`
  (green) + `python3.10 scripts/check_architecture.py --mode strict` (0 errors) + boot the test bot
  on real Postgres and exercise the new path (the Vault slice #884 did exactly this — see its session
  log for the recipe; Postgres bring-up is in `.session-journal.md` → Runbook).
- Numbers below are **concrete recommended defaults** (so you can just build), but **tunable** —
  pin them in a small `docs/planning/*-numbers-*.md` record + a test, the way
  [`gear-set-numbers-2026-06-11.md`](gear-set-numbers-2026-06-11.md) does, if you change them.

## What is already shipped (don't rebuild)

- **Vault v1 (#884, this plan's first slice — DONE):** a per-player *safe stash* — `mining_vault`
  table (migration 070), `vault_deposit` / `vault_withdraw` / `vault_deposit_all_resources` on the
  workflow, `🏦 Vault` hub button + `!vault`/`!stash`/`!unstash`. **No cap yet** — that's Slice A.
- **Gear + sets (V-16 phase 1, #702):** `utils/equipment.py` `EffectiveStats` (the shared stat block),
  9 slots, 5 tiers, same-tier set bonus, paper-doll compositor with placeholder sprites.
- **Workshop + durability (#665):** craft / repair / quick-craft, wear keyed by item name.
- **Market (#661…#665):** sell-ore faucet + buy-gear sink through `economy_service`.
- **Shared game-XP (#665, migration 065):** `services/game_xp_service.py` — guild-scoped track, daily
  soft cap, **shared derived level** from `SUM(xp)`; `gamexp`/`crafting` leaderboards. **This is the
  skill-point currency.**

## The seams you build on (all confirmed in source 2026-06-14)

| Need | Use | Where |
|---|---|---|
| Atomic mining writes | `services/mining_workflow.py` (one `db.transaction()` per op) | RS02/Q-0071 — the AST ratchet `tests/unit/invariants/test_mining_write_boundary.py` forbids direct mining writes in cogs/views; **add each new write-primitive name to its `_FORBIDDEN_ANY_RECEIVER` set** |
| New per-game table | `utils/db/games/<name>.py` (conn-aware primitives) + re-export in `utils/db/__init__.py` | mirror `mining_vault.py` / `game_xp.py` |
| Player power read-model | `utils/equipment.py` `EffectiveStats` (+ `compute_stats`) | the §7.4 merge point — *"computed from equipped gear (and, later, skills)"* is literally in its docstring |
| Game level / XP total | `game_xp_service.level_info(guild, user)` → `(level, into, needed)`; `db.get_total_xp` | skill points derive from level |
| Coin sink (respec, builds) | `economy_service.debit_in_txn(conn, …)` inside the workflow txn | the `mining_workflow.repair` precedent |
| New child panel | `HubView` subclass + lazy back-link to `MiningHubView` | mirror `views/mining/market_panel.py` / the new `vault_panel.py` |

---

## Slice D — Capped skill tree (§7.4) · **▶ startable · the marquee · recommended first**

The brainstorm's headline platform feature, and its prerequisites (`game_xp_service` + the
`EffectiveStats` merge point) are **both in place**. Four branches, **capped so you can't max all** →
forced specialization (digger / duelist / tycoon / smith), which is what lights up solo/PvP/leaderboards/co-op (§7.3).

**Build:**
1. **Table** `migration 071_player_skills.sql` + `utils/db/games/player_skills.py`:
   `player_skills(user_id BIGINT, guild_id BIGINT, branch TEXT, points INT NOT NULL DEFAULT 0,
   PRIMARY KEY(user_id, guild_id, branch))`. Conn-aware `get_skills(user,guild)` →
   `{branch: points}` and `set_skill_points(user,guild,branch,points,*,conn)` (the write primitive →
   add to the boundary ratchet). Re-export both in `utils/db/__init__.py`.
2. **Pure model** `utils/mining/skills.py` (stdlib-only, like `equipment.py`):
   `BRANCHES = ("mining","combat","fortune","crafting")`; `PER_BRANCH_CAP = 10`;
   `skill_stats(alloc: dict[str,int]) -> EffectiveStats` — recommended v1 mapping (1 pt each):
   mining→`mining_power+1`; combat→`damage+1` every 2 pts & `max_health+2`; fortune→`luck+1` &
   `loot_bonus` every 2 pts; crafting→`loot_bonus+1` (crafting-cost perks are a non-`EffectiveStats`
   read — keep v1 simple). Pure + table-driven so it's trivially unit-testable.
3. **Service** `services/skill_service.py`:
   `available_points(guild,user)` = `min(level, SOFT_TOTAL_CAP=20) − sum(spent)` (20 < 4×10=40 ⇒
   **can't max all** — the cap); `allocate(guild,user,branch,n)` (validates branch, `n>0`, available,
   per-branch cap; one txn); `respec(guild,user)` (coin sink via `economy_service.debit_in_txn`,
   clears all allocations in one txn; price e.g. `200 + 50·level`). Emit `audit.action_recorded` on
   respec (real coin move) — allocate is self-service, no audit (the craft precedent).
4. **Merge** — add `character_stats(equipped, alloc) -> EffectiveStats` (in `utils/equipment.py` or a
   thin `utils/mining/character.py`): `compute_stats(equipped) + skill_stats(alloc)`. Adopt at the
   mining read sites that gate on stats: `mining_workflow.descend` (uses `equipment.compute_stats`),
   the gear/character panels. **Empty allocations ⇒ byte-identical** to today (the safety property —
   assert it in a test). Deathmatch adoption is an optional follow-up.
5. **UI** — `views/mining/skills_panel.py` (`HubView` child): show branches, points, available, stat
   preview; a select/buttons to spend a point per branch; a Respec button (confirm + cost). `🌳 Skills`
   hub button + `!skills` / `!skill <branch>` commands.

**Tests:** pure `skill_stats` table; `available_points` cap math; allocate guards (over-spend,
over-cap, unknown branch); respec debits + clears; **the byte-identical-when-empty invariant**.
**Gate:** none — fully buildable now. **Size:** one focused PR (the table+service+merge), UI can be a
second PR if it runs long.

## Slice A — Vault v2: inventory soft-cap + the sink · **▶ startable** (builds on #884)

Turns the shipped Vault from a convenience into a **real sink** (the §7.5 intent: *"inventory cap +
safe stash"*). The active pack gets a **soft cap**; the vault is uncapped-but-built.

**Build:** a configurable `PACK_SOFT_CAP` (recommend **distinct item-types**, not total quantity, so
hoarders aren't punished for stacking — e.g. 40 types). When the pack is at cap, mining still works but
the hub nudges *"pack full — stash at the 🏦 Vault."* Optionally gate vault **capacity** behind a
**built** upgrade (coin + material sink): `mining_structures` table (see Slice B's shared table) row
`vault_level`, each level +N vault slots for a rising cost. **Keep enforcement gentle** (warn, don't
hard-block mining) so it's additive, not a nerf — the owner hasn't ok'd a hard cap.
**Tests:** cap math + the "stash all clears the warning" path. **Gate:** none. **Size:** small.

## Slice B — Forge structure · **▶ startable**

A **built** structure (coin + material sink) that gates higher-tier gear crafting — ties structures
into the gear ladder. Recommended: shared `migration 072_mining_structures.sql`
(`mining_structures(user_id, guild_id, structure TEXT, level INT, PK(user,guild,structure))`) +
`utils/db/games/mining_structures.py`; `mining_workflow.build_structure` (debits coins/materials
atomically, raises the level); **Forge tier N unlocks tier-N gear recipes** in the recipe browser /
`craft` (a forge-level check in `_resolve_recipe`). `🏗️ Build`-area UI or a `🔥 Forge` panel.
**Tests:** build debits + level-up; recipe gating. **Gate:** none (pick simple gating). **Size:** medium.

## Slice E — Respec polish · **▶ startable** (after D)

If Slice D shipped respec minimally, this adds the **UX** (confirm modal, cost preview, "are you sure"
+ partial respec of one branch). **Gate:** Slice D. **Size:** small.

## Slice F — Titles from skill mastery + milestones · **▶ startable** (after D)

The cheapest identity feature (text). Earned, equippable titles from **skill mastery** ("the Deep",
"Ironclad", "Lucky", "Master Smith") + **milestones** ("depth 50", "first diamond"). Pure trigger
table → a `player_titles` store + an equipped-title field surfaced on the Character card. **Gate:**
Slice D (mastery triggers) for the skill titles; milestone titles need only existing depth/XP data.
**Size:** small–medium.

## Slice C — Home structure / profile backdrop · **▶ startable (art-light)**

The §7.5 "Home (hub + profile backdrop)". v1 with **zero custom art**: a built Home structure that
adds a personalized header/backdrop to the Character card (PIL `character_render` already composites;
Home just selects a backdrop colour/frame). **Gate:** none for v1 (cosmetic frames, not sprites).
**Size:** small.

## ⛔ Owner-blocked (do NOT attempt unattended)

- **V-16 phase 2 — paper-doll real sprites:** waits on the **owner's PNG pack** dropping into
  `disbot/assets/gear/` (`utils/character_render.py` hot-swaps placeholders → real art automatically;
  nothing to build until the art lands). The compositor + manifest are already shipped.

## Routing

When a slice ships: tick it here, update the [games folio](../subsystems/games.md) mining bullet +
`docs/current-state.md` Recently-shipped, and re-badge this plan `historical` once the startable slices
are all done. This plan is the authority for scope; the folio owns per-area detail.
