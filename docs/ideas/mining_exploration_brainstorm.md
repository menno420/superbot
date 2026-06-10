# Mining & Exploration — Brainstorm & Roadmap

> **Status:** `ideas`

> Status: **brainstorm / design notes**, not a binding contract. The
> binding docs (`architecture.md`, `ownership.md`, `runtime_contracts.md`)
> win on any conflict. This document captures ideas for growing the
> mining/exploration subsystem and records the safe, additive foundation
> shipped alongside it.

## 1. Where the subsystem is today

| Layer | File | Role |
|---|---|---|
| Cog | `cogs/mining_cog.py` (283 LOC) | Commands: `minemenu`, `mine`, `chop`, `mineinv`, `minestats`, `build`, `buildlist`, `buildable`, `explore`, `use`, `reset_inventory`, `give`. Most are `hidden=True`. |
| Domain | `cogs/mining/rewards.py` | Pure loot math: `ORE_WEIGHTS`, `roll_mine_loot(has_pickaxe)`, `roll_harvest_amount(has_axe)`, `EXPLORE_OUTCOMES` (5 flat entries), `roll_explore_outcome()`. |
| Domain | `cogs/mining/recipes.py` | JSON-loaded structure recipes with hard-coded fallback. |
| DB | `utils/db/games/mining.py` | `mining_inventory` CRUD, guild-scoped (PR M3). `user_id` is legacy `TEXT`. |
| DB | `utils/db/inventory.py` | A *separate* unified `inventory` table (`user_id` is `BIGINT`). |
| Views | `views/mining/main_panel.py` | `MiningHubView` persistent panel (Mine/Harvest/Explore/Inventory/Stats/Build). |
| Views | `views/mining/mine_view.py` | `MineView` ephemeral 3-button session + `_MineResultsView`. |

### What works well
- Clean pure/impure split: loot math is already testable without a Discord harness.
- Guild-scoped storage (the cross-guild wipe bomb was fixed in PR M3).
- Button-first UX via the hub panel — consistent with "the whole bot is reachable in 3 taps".

### Honest limitations (the brainstorm fuel)
1. **`explore` is flat.** Five outcomes, uniform `random.choice`, zero awareness of what gear you carry or how deep you are. Owning a pickaxe only ever "doubles" `mine`; the explore path ignores gear entirely.
2. **Gear is binary.** "Owns pickaxe → ×2", "owns axe → ×2". No tiers, no durability, no loadout, no trade-offs.
3. **Consumables are cosmetic.** `!use torch` / `!use dynamite` print flavour text and decrement the item, but change *no* outcome. They are mechanically inert.
4. **Items are untyped strings.** Ore, wood, tools, built structures, and consumables are all undifferentiated keys in `mining_inventory`. No layer can ask "is this a tool?" or "what tier is this?" without re-hard-coding name lists.
5. **Two inventory tables** (`mining_inventory` TEXT vs `inventory` BIGINT) — latent fragmentation; unifying is its own migration and explicitly out of scope here.
6. **No session/state.** Each explore is independent; there is no depth, no run, no risk/return arc.
7. **Rendering is embed-only.** No images; no way to give an explore a visual identity.
8. **The AI layer is a spectator.** `services/ai_tools.py` is strictly read-only and scope-gated ("Adding a write-capable tool is deliberately out of scope: mutations must go through services"). The `response_renderer_registry` (see `views/youtube_renderers.py`) is the seam for AI-driven *presentation*, but nothing exploration-related is wired to it.

## 2. Feature brainstorm

Naming things makes them discussable. None of these exist yet; this is the menu.

### 2.1 Depth & biomes — "the Descent"
Exploration becomes *banded by depth*: **Surface → Cavern → Deep → Magma**. Deeper bands carry rarer ore, bigger payoffs, and nastier hazards. Depth is the natural pacing mechanism and the hook for everything below.
- *Implemented as foundation:* `cogs/mining/exploration.Biome` + `min_biome` gating in the catalog.

### 2.2 Loadout-aware outcomes
The tools you carry change *which* outcomes are reachable and *how generous* they are:
- **Torch / Lantern** → unlocks deep finds that are dark-gated (`hidden_diamond_vein`, `molten_geode`).
- **Dynamite** → unlocks high-payoff "blasted vein" outcomes (consumed on use).
- **Lucky Charm** → +1 to positive yields.
- **Pickaxe** → doubles ore gains (mirrors the existing `!mine` bonus, now applied to explore too).
- *Implemented as foundation:* `Loadout`, `requires`/`consumes` on outcomes, `_scale_amount`.

### 2.3 Item taxonomy & tool tiers — "the Forge ladder"
Give items *kinds* (`RESOURCE / TOOL / CONSUMABLE / STRUCTURE / TREASURE`), *tiers*, and *values*. Then a crafting progression falls out naturally: `pickaxe → iron pickaxe`, `torch → lantern`. Tiering also powers sensible inventory sorting and an inventory "net worth" stat.
- *Implemented as foundation:* `cogs/mining/items.py` (`classify`, `tool_tier`, `total_value`, `next_tool_upgrade`, `sort_inventory`, `TOOL_LADDERS`).

### 2.4 Crafting cog — "the Workshop"
A dedicated, additive **crafting subsystem** sitting on top of recipes + the tool ladder:
- Upgrade tools by spending lower-tier materials (`iron pickaxe` from `iron + wood`, already a recipe).
- Tool **durability**: tools wear and need repair/recraft — gives resources a sink.
- A `WorkshopView` panel parallel to the mining hub.
- Owns its own writes through a `crafting_mutation.py` service; emits audit actions; never writes the DB directly from the view/cog.

### 2.5 Consumables that actually do something
Wire `!use` into the exploration engine: a torch consumed *this run* temporarily grants the torch loadout; dynamite spends on a blast outcome. The engine already models `consumes`; only the wiring + a mutation call are missing.

### 2.6 AI-active exploration — "the Guide"
The architecturally interesting one, and the one to do **last and carefully**. The AI layer is read-only by contract, so the clean shape is:
- The exploration **service** owns the catalog and all state/mutations.
- The AI's role is to **pick from and narrate** a catalog of outcomes the service defines — it returns a *structured choice + flavour text*, never a write.
- A registered **renderer** (`response_renderer_registry`) turns that choice into an embed / buttons / an image.
- Result: AI-driven custom buttons, themed narration, even per-run art — all while mutations stay deterministic and auditable. This respects the zero-tolerance `services/ → views/` rule and the read-only AI-tools contract.

> ⚠️ Trade-off to decide explicitly: letting the AI emit UI or write state directly would create new `services/ → views/` violations and unaudited mutations. The "narrate a service-owned catalog" approach is the one that passes `check_architecture.py`.

### 2.7 Image cards — "the Postcard"
Render an inventory or explore result as a PNG card (depth-themed background, kind-coloured rows, a "net worth" footer). Optional dependency, graceful fallback to embed.
- *Implemented as foundation:* `utils/mining_render.py` (pure `build_card_spec` + lazy/optional `render_inventory_card`).

### 2.8 Smaller ideas worth a line
- **Expeditions**: a multi-step explore "run" with escalating depth and a bank-or-push-your-luck choice.
- **Daily vein**: a once-per-day rich node, ties into existing cooldown/economy patterns.
- **Hazard mitigation**: a hazard outcome is reduced/negated if the right tool is equipped (lantern vs cave-in).
- **Leaderboard by net worth** instead of raw item count (reuses `items.total_value`).
- **Shared guild dig site**: a server-wide vein everyone contributes to (collaborative, fits the social bot).

## 3. Architecture fit (how these land without breaking rules)

```
cogs/mining/exploration.py   (pure)   ← outcome catalog + selection math   [shipped]
cogs/mining/items.py         (pure)   ← taxonomy, tiers, values            [shipped]
utils/mining_render.py       (pure+lazy PIL) ← image card spec + render    [shipped]
        │
        ▼  (future, separate approved PRs)
services/exploration_service.py        ← owns state, applies outcomes (writes)
services/crafting_mutation.py          ← tool upgrades/durability (writes + audit)
core/runtime/ai/...  + a renderer      ← AI narrates a service-owned catalog
views/mining/explore_view.py           ← buttons/embed/image surface
```

- **Pure foundation in `cogs/mining/` and `utils/`** — imports only stdlib (and lazy PIL). No layer violations; no new production dependency.
- **All future writes** flow through a `*_mutation.py` service and call `emit_audit_action()` — never a direct DB write from cog/view (per `CLAUDE.md`).
- **Naming caution:** do **not** name an exploration module/cog `explorer` — it collides with `views/access/explorer.py` (governance). Use `exploration`.

## 4. Shipped in this PR (additive only — zero behaviour change)

New files only; no existing file modified; nothing wired into a command yet:

- `cogs/mining/exploration.py` — depth/loadout-aware outcome engine. `resolve_to_legacy_tuple()` returns the exact `(text, item, amount)` shape `!explore` already consumes, so future adoption is a one-line swap, not a rewrite.
- `cogs/mining/items.py` — item taxonomy, tool tiers, value + sorting helpers.
- `utils/mining_render.py` — pure card-spec builder + optional Pillow renderer (returns `None` when Pillow is absent; callers fall back to an embed).
- Tests for all three (`tests/unit/cogs/test_mining_exploration.py`, `tests/unit/cogs/test_mining_items.py`, `tests/unit/utils/test_mining_render.py`).

## 5. Suggested sequencing (future, each its own approved PR)

1. **Wire exploration** — swap `!explore` to build a `Loadout` from inventory and call `exploration.resolve(...)`, applying results through the existing inventory mutation path. Add a depth notion (start at Surface; torch/lantern/depth items push deeper). *Touches `mining_cog.py` — behaviour change, so it's its own PR.*
   > **→ Routed 2026-06-08 (idea lifecycle / Q-0015 grooming):** promoted to a structured plan,
   > [`../planning/mining-wire-exploration-plan.md`](../planning/mining-wire-exploration-plan.md),
   > and onto `docs/roadmap.md` (Games, ready/ungated). Awaiting maintainer go to build. Steps 2–3
   > below stay captured here.
2. **Workshop / crafting** — `services/crafting_mutation.py` + `WorkshopView` + tool durability, built on `items.TOOL_LADDERS`.
3. **AI-active "Guide" + image cards** — renderer + read-only AI tool that narrates the service-owned catalog; opt-in Pillow for art.

### Image rendering is already unblocked
`Pillow>=10.0,<12` is in `requirements.txt`, so `utils/mining_render.render_inventory_card`
returns PNG bytes today (it still returns `None` and falls back to an embed if Pillow ever
fails to import — fallback-by-design is preserved). No dependency step remains; image cards
are purely a content + wiring task.

---

## 6. Refined design — foundation-first build (decisions locked 2026-06-08)

> **Status:** still `ideas` — this section is *design intent + recommended phasing*, **not** a
> build approval. It consolidates the §2 feature menu and a broader "mother panel + child panels
> + reusable gear" expansion (maintainer brainstorm, 2026-06-08) into one decided, sequenced
> shape. Each phase still promotes to its own `docs/planning/` slice and needs the maintainer's
> go before building (§5 step 1's plan is the template). **Update (2026-06-08):** §7 below
> expands this into the full **character-platform** vision and a revised roadmap — read §7 for
> the current shape; §6 remains the detailed **mining-mechanics** reference.

The brainstorm widened from "make `!explore` smarter" to a **Mining / Exploration / Crafting /
Gear platform**: one *mother panel* routing four–five child panels, a reusable equipment system
other game cogs (deathmatch, future modes) can read, and a persistent player world. Eight owner
decisions this session pin the v1 cut to "foundation-first, clean seams, defer the heavy and the
risky."

### 6.1 Decisions locked (2026-06-08)

| # | Decision | Choice | Why it matters |
|---|---|---|---|
| 1 | Spatial fidelity of v1 | **Depth-bands first** (x/y grid is a later phase) | The shipped `exploration.py` already models depth bands; real coordinates are the biggest net-new build, so they sequence last among the core work. |
| 2 | World scope | **Personal position, per-guild seed** | No griefing, easy reset/balance; a stored `world_seed` makes the later grid deterministic. Shared dig-sites stay a separate future feature. |
| 3 | Run model | **Persistent position** | Leave at depth 3, return to depth 3. Position is DB state (allowed by ADR-002); only panels are ephemeral. |
| 4 | Inventory storage | **Keep two bags, overlay types** | No migration now; `items.py` classifies the existing bag; gear is a new table referencing bag item-names. Unifying the bags stays deferred. |
| 5 | Survival stats | **None in v1** (health/stamina later) | Prove the loop before balancing danger/recovery. |
| 6 | Character scope | **Guild-scoped** | Consistent with inventory/XP/economy; gear is built from guild-scoped resources. |
| 7 | Gear ↔ other games | **Generic stats read model** | Deathmatch/future games read computed stats, never the item catalog — the `economy_service` decoupling pattern. |
| 8 | Crafting depth | **Flat + quick-craft-last-broken**; stations later | Ship the craft→break→recraft loop first; stations are a later progression gate. |

### 6.2 What v1 is (and isn't)

**In v1:** persistent depth/biome position per player · mother panel + child panels · typed
inventory overlay · equip/unequip with generic stats · durability + "quick-craft the last item
that broke" · loadout/depth-aware mining & exploration outcomes (the already-shipped engine) ·
deathmatch reading gear stats.

**Explicitly deferred (each revisits at its phase):** x/y coordinates + N/S/E/W movement +
per-cell worldgen (→ P6) · health/stamina + hazards (→ post-loop) · crafting stations (→ after
flat crafting) · inventory-table unification (own migration) · shared guild dig-site · expeditions
/ push-your-luck · global character · AI "Guide" (AI-gated) · combat that references specific items.

### 6.3 Panel structure (mother + children)

`MiningHubView` (already a `PersistentView`) becomes the **mother panel** — an overview embed
(location · depth · biome · equipped main tool · net worth) that mostly *routes*:

```
Mining Mother Panel (persistent)
├── 🌍 World / Exploration   (surface actions ↔ underground; dynamic by state)
├── ⛏️ Mine                  (mine current biome; gear/durability aware)
├── 🔨 Craft (Workshop)      (quick-craft last broken · craftable-now · all recipes)
├── 🎒 Inventory             (typed, grouped, net worth)
└── 🧍 Gear                  (equip/unequip · generic stat summary · [later] character card)
```

Children are **ephemeral** `BaseView`/`HubView` panels (timeout) with a *Back to hub* button;
the mother panel persists across restarts. **Dynamic buttons come from state, not the view:**

- Surface: `🌲 Chop` · `🪨 Gather` · `⬇️ Mine Down`
- Underground (v1): `⛏️ Mine Here` · `⬆️ Go Up` · `⬇️ Go Deeper` (gated by light/depth items)
- **N/S/E/W movement is deferred to P6** (the grid) — v1 underground movement is vertical only.

### 6.4 New persistent state (follows the `utils/db/games/` + guild-scoping conventions)

```
mining_worlds          (guild_id PK, seed, worldgen_version, created_at)
  └ per-guild deterministic seed; stored in P2, first *used* by the P6 grid.

mining_player_state    (guild_id, user_id, depth, current_biome, last_broken_item,
                        last_action_at, updated_at)        PK (guild_id, user_id)
  └ reserved-for-later columns: health, stamina (added when survival lands).

mining_equipment       (guild_id, user_id, slot, item_name, durability, equipped_at)
                        PK (guild_id, user_id, slot)
  └ references item-names in mining_inventory; durability ticks down per use.
```

> **Correction (2026-06-09, as built):** durability did **not** land as a column on
> `mining_equipment` — a slot-keyed value resets on unequip/re-equip, a free-repair
> exploit. It lives in its own **`mining_gear_wear`** table keyed by *(user, guild,
> item_name)* (migration 063); a row exists only while the item is worn.
> `last_broken_item` landed on `mining_player_state` as sketched.

`user_id` stays `TEXT` to match legacy `mining_inventory`. No `discovered_cells` table in v1 —
that arrives with the P6 grid.

### 6.5 New service seams (mirror `economy_service`: write → audit → event)

- **`services/mining/world_service.py`** — owns position: `get_state`, `descend`/`ascend`
  (depth ± light/depth-item gating), biome selection. Writes player-state; emits audit.
- **`services/equipment_service.py`** — `get_equipment`, `equip`/`unequip`, `apply_durability`,
  broken-item tracking. Exposes an **`EffectiveStats`** read model; emits `equipment.item_equipped`
  / `equipment.item_broken`. The one seam every game reads.
- **`services/mining/crafting_mutation.py`** — *optional future seam, not a current fix.*
  **Correction (2026-06-08, verified against binding docs):** mining is an **intentional
  direct-lane domain** — `ownership.md` routes `mining_inventory` *direct via
  `utils/db/games/mining.py`*, and the RC-8A direct-DB ledger
  (`docs/audits/direct-db-exception-ledger.md`) catalogues `!build`'s write as
  **`accepted-direct-write`**: "a mutation service is a *future option, not a current
  violation*." So today's `!build` is **correct, not an audit gap** (an earlier draft of this
  doc wrongly called it one). An audited crafting service becomes warranted only when crafting
  turns **cross-domain** (e.g. it spends coins — that leg *must* route through `economy_service`)
  or grows durability / quick-craft state. Until then, crafting writes stay on the db helper;
  the only robustness nit worth fixing there is making the multi-item build **atomic** (one
  transaction in `utils/db/games/mining.py`). **Lightweight game state ≠ audited service.**
- **Reuse, don't replace:** the pure `cogs/mining/exploration.py` (catalog + selection) and
  `cogs/mining/items.py` (taxonomy) stay pure; the new services *apply* their results.

### 6.6 The cross-cog stat contract (the "platform" seam)

`equipment_service` computes a **neutral** stat block from equipped items; each game reads only
the subset it cares about — no game imports mining's items.

```
EffectiveStats (generic, read-only):
  mining_power · light_radius · depth_access · hazard_resistance · luck · loot_bonus
  damage · defense · max_health · durability
```

Deathmatch reads `damage` / `defense` / `max_health` (replacing today's hardcoded HP 100 /
dmg 15); mining reads `mining_power` / `light_radius` / `loot_bonus`; future cogs plug in for free.

### 6.7 Phasing (each = its own approved slice → `docs/planning/`)

| Phase | Deliverable | New tables | Risk |
|---|---|---|---|
| **P0** | Wire `!explore` to the loadout/depth engine (**plan already written & ready**) | none | low |
| **P1** | Mother-panel refactor (route 5 children + overview embed) | none | low |
| **P2** | Persistent depth/biome position + World view (Go Deeper/Up/Mine Here) | `mining_worlds`, `mining_player_state` | med |
| **P3** | Typed inventory overlay + grouped Inventory view + net worth | none | low |
| **P4** | Equipment service + Gear view + generic stats; **deathmatch reads stats** | `mining_equipment` | med |
| **P5** | Audited Workshop: craft/repair/upgrade + durability + quick-craft-last-broken | none (uses P2/P4) | med |
| **P6** | x/y grid + deterministic cell gen + N/S/E/W + discovered cells (**the big arc**) | `mining_discovered_cells` | high |
| **P7** | PIL cards (character + local map), embed-first | none | low |
| **P8** | AI "Guide" narration (**AI-orchestration-gated**) | none | gated |

P0–P1 are immediate, low-risk, noticeable. P2–P5 are the real foundation ("build the whole
foundation first"). P6 is where the original grid/coordinate vision lands, on top of a proven loop.

### 6.8 Questions to settle at their phase (captured, not blocking v1)

- **P2 — DECIDED 2026-06-09; OWNER-CONFIRMED 2026-06-09 (Q-0050, gate-lifting interview):
  lights stay permanent** — durability (P5/§7.5 Workshop) carries the recurring-sink role
  instead; one sink, clearly owned. Descent is
  gated by the equipped light's already-shipped `depth_access` stat and is **persistent, not
  consumed**: a torch (`depth_access` 1) unlocks the Cavern, a lantern (`depth_access` 2) the
  Deep; the Magma core needs `depth_access` 3, which no current gear grants (aspirational
  headroom for a future deeper light). Ascent is always free; position persists in
  `mining_player_state.depth`. *Why this over "consume a light per descent":* it reuses the
  stat gear already feeds, matches decision 6.1 #3 (persistent position), and leaves the
  consumption/sink mechanic to the durability slice (P5) instead of overloading descent now.
  The whole gate is one pure function (`cogs/mining/world.max_accessible_depth`) — trivially
  swappable to a consumption model if the owner prefers it.
- **P5 — DECIDED 2026-06-09; OWNER-CONFIRMED 2026-06-09 (Q-0054): numbers + the
  lights-wear-underground model stay as shipped.**
  Durability shipped generous-side per this caution: pickaxe 60 uses / iron 150 / torch 40 /
  lantern 100 / charm 80 (data in `utils/equipment.MAX_DURABILITY`); repair = `REPAIR_RATE`
  (0.5) × shop price, scaled by missing durability; lights wear only **underground**; descent
  itself stays free (the P2 persistent-gating decision is unchanged — wear-on-use replaced
  the deferred "consume a light per descent" idea). All knobs are single-table data.
- **P6:** resource depletion semantics once cells exist (permanent / regenerating / per-player),
  and personal-vs-shared dig sites. The `world_seed` stored back in P2 already makes generation
  deterministic when this lands.

---

## 7. The character platform — expanded vision (brainstorm 2026-06-08)

> **Status:** still `ideas`. This section **expands §6**: where §6 designs "mining as a real
> game," this round reframed the whole thing — *mining is **activity #1** of a shared **character
> platform** the entire bot plugs into.* Captured from a multi-round brainstorm with the
> maintainer (owner taste decisions inline). It **supersedes §6's P0–P8 *ordering*** (see §7.7);
> §6 stays the detailed reference for **mining mechanics** specifically. Locks nothing; slices
> still promote to `docs/planning/` individually.

### 7.1 The reframe

The gear system was meant to be referenced by mining, exploration, deathmatch, and future cogs.
Taken seriously, the artifact isn't a mining game — it's a **persistent character + gear + stats +
progression layer for the whole bot**. You are a *character on the server*; mining is the first
(flagship) activity that feeds that character, and deathmatch / blackjack / future games read from
and contribute to the same character.

**The spine:** `shared character (gear + skills + game-level + coins) → one stat block → many
activities → social layers on top.` The **Character/Profile** is likely the *mother panel itself*,
with Mining / Deathmatch / etc. as activities hanging off it.

### 7.2 Owner taste decisions (this brainstorm)

| Topic | Decision |
|---|---|
| Pacing | **Active sessions** (click-through now). Idle/passive **parked**. |
| Social scope | **All four**, sequenced *after* the solo core: solo & cozy · head-to-head (PvP) · co-op & trading · server-wide goals. |
| XP model | **Two separate tracks bot-wide:** existing **chat XP** (drives auto-roles — keep clean) **+ NEW game XP**, shared across *all* game cogs. |
| Coins | Mining **sells ore (faucet)** + **buys gear (sink)** — integrated with the existing economy. |
| Repeat hooks | **Gear progression · leaderboards · build-your-base.** (Not collection/completion.) |
| Game-XP function | **Prestige + leaderboard** *and* a **capped skill tree**. **Not** content-unlocks (avoids cross-game gating weirdness). |
| Skill tree | **Four branches:** Mining/gathering · Combat · Fortune/luck · Crafting/utility. **Capped** (can't max all). Respec = coin sink. |
| Structures | **Forge** (recipes/tiers) · **Vault** (inventory cap + safe stash) · **Home** (hub + profile backdrop). Elevator/fast-travel **parked**. |
| Profile visual | Ship **composited stat card** (zero art) → grow toward **character with visible gear (paper-doll)** as the dream. Full base-scene **not** the target. |
| Titles | Earned from **skill mastery + milestones** (permanent, personal). Not rank/seasonal, not hidden. Ship early. |

### 7.3 The three shared layers (what makes it a *platform*)

1. **Gear / equipment** — *horizontal, swappable* power (equip per activity). [§6.5 equipment service]
2. **Skills** — *vertical, permanent* power; spend capped game-XP points across the 4 branches.
3. **Coins** — existing currency; mining is faucet **and** sink.

…plus **game XP / level** (the shared progression track) and **identity** (titles, avatar, rank).

**The convergence insight — one stat block.** Gear (swappable) **and** skills (permanent) both add
modifiers to a single neutral **`EffectiveStats`** read model (§6.6). Every game reads *one number*.
Adding skills costs almost no new seam — it's another input to a read model gear already feeds. Your
power = gear + skills (+ later: consumables / structures).

**Build identity — the engine that lights up every social pillar.** Because skill points are
**capped**, players *specialize* (digger / duelist / tycoon / smith). That single fact makes **solo**
a real choice, **PvP** varied, **leaderboards** plural (different builds top different boards), and
**co-op** complementary (an expedition wants a digger *and* a fighter *and* a looter). One mechanic
powers all four social pillars.

### 7.4 New shared systems (for the next agent — architecture)

- **Game-XP service** — sibling to the existing chat-XP `xp_service`; **own table**, guild-scoped.
  **Central award policy** so no single game is the optimal XP farm (XP ≈ effort/risk; consider a
  soft daily cap per game). Other game cogs call it to award XP. *Separate from chat XP on purpose —
  chat XP already drives the auto-role tiers.*
- **Skill service** — per-player allocations across 4 branches; computes perk modifiers into
  `EffectiveStats`; **respec** through an audited path (coin sink).
- **Equipment service** (§6.5) — gear → `EffectiveStats`; now **merged with** skill modifiers.
  *(Partly shipped 2026-06-09: the pure model was relocated to **`utils/equipment.py`** — a
  shared, stdlib-only seam — the moment a second game needed it, and combat gear
  (weapon/armor → `damage`/`defense`/`max_health`) was added so **deathmatch reads
  `EffectiveStats`**. A stateful service + skill-modifier merge remain later steps.)*
- **Profile read-model + renderer** — composes level, skills, gear→stats, coins, rank, titles;
  **owns no data**. `utils/mining_render` is the seed but generalizes to a **cross-game character
  renderer** (no longer mining-specific). Stat-card first; paper-doll later.
- **Titles / achievements** — skill-mastery + milestone triggers grant equippable titles (text — the
  cheapest identity feature). Badges = small-art follow-on.

### 7.5 The economic loop (closed, self-balancing)

> mine ore → **sell** some / **craft + repair** gear → go **deeper** → better ore → repeat

**Durability is the keystone** — the recurring ore+coin sink that keeps ore valuable. The sell-ore
**faucet** is balanced by **sinks**: gear purchases, repairs, structure builds, skill **respec**.
Design it as *one* loop, not separate features.

**Shipped 2026-06-09:** the **sell-ore / buy-gear market** (`cogs/mining/market.py`) — the
faucet + first sink. Coins move only through the audited `services.economy_service`; sell
prices reuse `items.item_value`; the gear shop is a tunable coin catalogue.

**Shipped 2026-06-09 (second slice): the keystone — Workshop + durability**
(`cogs/mining/workshop.py` + migration 063 + `views/mining/workshop_panel.py`): gear wears
1 durability per use (mine wears tool + light-underground; explore wears light-underground
+ charm), breaks at 0 (**consumed from inventory** — the ore sink), and comes back via
**repair** (coin sink, audited through economy_service `mining:repair_gear`; price derived
from the gear shop at `REPAIR_RATE`) or **re-craft** (`!craft`/quick-craft-last-broken,
auto-equip; materials+product move in one transaction). Wear is keyed by item *name*
(`mining_gear_wear`), not slot, so unequip/re-equip can't reset it (the §6.4 sketch of a
durability column on `mining_equipment` was a free-repair exploit — corrected). The hub
also gained the §6.3 **live overview** embed (location · tool+durability · light · net
worth · broken-gear hint). The remaining sinks (**structures** Forge/Vault/Home, **respec**)
are next. **Duels-wear shipped 2026-06-10** (Q-0054 closed): a finished PvP deathmatch
ticks each human fighter's weapon + armor once (`ACTION_DUEL`), so combat gear is fully
in the craft→break→repair loop.

### 7.6 Profile & identity (the spine, in detail)

> **Shipped 2026-06-09 (seed):** a read-only **Character overview** (`!character`/`!profile`
> + a hub Character button, `views/mining/character_panel.py`) aggregating position +
> gear/`EffectiveStats` + coins + net worth — the stat-card-first step as an embed. The PIL
> card and paper-doll remain the later visual-roadmap steps; game-level/skills/titles slot in
> as those systems land.

- **What it is:** a read-only card aggregating the whole character — avatar, game level + XP bar,
  skill spec, equipped gear, coins / net-worth, equipped **title**, leaderboard rank.
- **Visual roadmap:** **stat card** (avatar + PIL panel, *zero custom art*, ships first) →
  **paper-doll character** wearing the actual loadout (base character + layered gear sprites,
  PIL-composited). The character is the **cross-game avatar** — it appears in duels, boards, and
  future games, which is *why* paper-doll beat the mining-only base-scene.
- **Titles:** from **skill mastery** ("the Deep", "Ironclad", "Lucky", "Master Smith") and
  **milestones** ("depth 50", "first diamond"). Permanent, equippable, and depend only on systems
  we're already building → **ship early**.
- **Cosmetics** (card themes/frames): optional later **coin sink**; pure expression, never balance.

### 7.7 Revised unified roadmap (supersedes §6's ordering)

Grouped into waves; slices promote to `docs/planning/` individually. **Principle:** build the first
activity (mining) into a real solo game, *then* extract the shared platform from it — don't build the
abstraction before its first concrete use.

| Wave | Theme | Contents |
|---|---|---|
| **0** | Instant win | Wire `!explore` to the loadout/depth engine (plan ready; no new tables). |
| **1** | Mining as a real solo game | Hub/mother panel · persistent position + World view · typed inventory · equipment + Gear view (**deathmatch reads stats**) · audited Workshop + durability + functional structures (Forge/Vault/Home) · sell-ore / buy-gear market. |
| **2** | The platform layers | **Game-XP service** + leaderboards (retrofit other games to award it) · **skill tree** (4 branches, capped) folding into `EffectiveStats` + respec · **Profile** read-model + **stat-card** render + **titles**. |
| **3** | Visual identity | **Paper-doll** character (layered gear art) · badges · cosmetic card themes. |
| **4** | The world arc | x/y grid + coordinates + N/S/E/W movement + discovered cells + map render (§6 P6). |
| **5** | Social systems | Leaderboard depth · **PvP** (arena / coin-wager duels) · **trading / market** (+ anti-alt guardrails) · **server-wide goals** · seasons. |
| **6** | AI Guide | AI narration layer (AI-orchestration-gated). |

### 7.8 Still-open threads (next brainstorm — not yet decided)

> **2026-06-10 update:** the owner's new vision statement
> ([`superbot-vision-2026-06-10.md`](superbot-vision-2026-06-10.md)) answers several
> of these threads in owner-voice and opens the deferred survival layer: difficulty
> modes (V-05), energy (V-06), fishing/cooking (V-07), PvP XP-both-sides (V-08),
> story pets (V-09, tension T-1 vs. the pets plan), and the AI quest/story layer
> (V-10). Read it before re-opening any thread below.

- **PvP shape** — matchmade arena vs. challenge-a-friend **coin-wager duels** vs. gear straight into
  the existing deathmatch. *(Weapons — sword/bow/dagger — get their purpose here, or from PvE.)*
  **Update 2026-06-09:** the "gear into the existing deathmatch" leg **shipped** — equipped
  weapon/armor now tilts duels (a small, fair edge). The broader arena-vs-wager-vs-existing
  *shape*, and whether gear should swing PvP harder, stay open for a product call.
- **Server-wide goals** — a shared **dig-bar** toward "the Core" (active contribution) vs. a communal
  **boss** vs. rotating **events** / seasons.
- **Trading & market** — player trade / gift / market **and the anti-alt-account guardrails**
  (level / cooldown gates, audit) so coins / gear / XP can't be laundered through alts.
- **Smaller open calls:** weapons PvE-vs-PvP purpose · prestige loop at level cap · game-XP
  normalization / daily-cap specifics. *(Descent gating — §6.8 P2 — decided 2026-06-09:
  persistent, light-`depth_access`-gated; **owner-confirmed** same day (Q-0050); see §6.8.)*


## Routing update — 2026-06-08

The shipped-engine wiring remains owned by [`../planning/mining-wire-exploration-plan.md`](../planning/mining-wire-exploration-plan.md); deeper floors, bosses, events, co-op, idle extension, and crafting handoff are routed to [`../planning/games-mining-idle-roadmap-2026-06-08.md`](../planning/games-mining-idle-roadmap-2026-06-08.md). This brainstorm remains preserved and unapproved.
