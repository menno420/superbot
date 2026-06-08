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
> go before building (§5 step 1's plan is the template).

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

`user_id` stays `TEXT` to match legacy `mining_inventory`. No `discovered_cells` table in v1 —
that arrives with the P6 grid.

### 6.5 New service seams (mirror `economy_service`: write → audit → event)

- **`services/mining/world_service.py`** — owns position: `get_state`, `descend`/`ascend`
  (depth ± light/depth-item gating), biome selection. Writes player-state; emits audit.
- **`services/equipment_service.py`** — `get_equipment`, `equip`/`unequip`, `apply_durability`,
  broken-item tracking. Exposes an **`EffectiveStats`** read model; emits `equipment.item_equipped`
  / `equipment.item_broken`. The one seam every game reads.
- **`services/crafting_mutation.py`** — `craft`/`repair`/`upgrade` through an **audited** path,
  closing today's gap (current `!build` mutates the bag straight from the modal with no audit
  seam). Powers quick-craft-last-broken via `mining_player_state.last_broken_item`.
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

- **P2:** exactly how do torch/lantern/depth-items "push deeper" — own one tool per band, or
  consume a light per descent?
- **P5:** durability harshness — a resource sink, not an annoyance (the brainstorm's own caution).
- **P6:** resource depletion semantics once cells exist (permanent / regenerating / per-player),
  and personal-vs-shared dig sites. The `world_seed` stored back in P2 already makes generation
  deterministic when this lands.
