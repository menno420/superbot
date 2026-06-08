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

### To activate image rendering
Add `Pillow` to `requirements.txt`. Until then `utils/mining_render.render_inventory_card` returns `None` by design and the dependency footprint is unchanged.


## Routing update — 2026-06-08

The shipped-engine wiring remains owned by [`../planning/mining-wire-exploration-plan.md`](../planning/mining-wire-exploration-plan.md); deeper floors, bosses, events, co-op, idle extension, and crafting handoff are routed to [`../planning/games-mining-idle-roadmap-2026-06-08.md`](../planning/games-mining-idle-roadmap-2026-06-08.md). This brainstorm remains preserved and unapproved.
