# Mining — wire `!explore` to the depth/loadout engine

> **Status:** `plan` — a small, ready-to-execute slice promoted from the mining brainstorm
> via the **idea lifecycle** (`docs/ideas/README.md`; owner decision Q-0015 grooming pass,
> 2026-06-08). **Not yet approved to build** — it is a behaviour change to a user-facing
> command, so it needs the maintainer's go. Source and merged PRs win over this plan.

## What & why

`!explore` today is flat: `mining_cog.py:225` does
`text, item, amount = roll_explore_outcome()` over five uniform outcomes that ignore the
gear you carry. The depth/loadout-aware replacement engine is **already shipped and tested**
as pure scaffolding (`cogs/mining/exploration.py`), wired into nothing. This slice swaps
`!explore` onto it — making outcomes gear/depth-aware — while keeping the existing inventory
write path. It is the brainstorm's own §5 step 1.

## Promotion gates — verified against source (2026-06-08)

| Gate | Finding |
|---|---|
| **Ownership** | `cogs/mining_cog.py` (`explore` command) + the existing `update_inventory` → `utils/db/games/mining.py` write path. **No new service** needed for this slice. |
| **Reuse** | The already-shipped, unit-tested pure engine `cogs/mining/exploration.py` (`resolve()` + `resolve_to_legacy_tuple()` @ L299) and `cogs/mining/items.py` (build a `Loadout` from inventory). `resolve_to_legacy_tuple()` returns the **exact** `(text, item, amount)` tuple `!explore` already unpacks — a near one-line swap, not a rewrite. |
| **Risk** | Low / contained. Behaviour change = explore outcomes become loadout/depth-aware (a game feature; low stakes). ADR-002 (game state not restart-safe) still holds — this slice adds **no** persistent run state. No new dependency (image cards / Pillow are a separate later step). No layer violation: the engine is pure; writes stay on the existing mutation path. |
| **Mechanics** | Touches `mining_cog.py` (behaviour change → its own PR). Build a `Loadout` from the user's inventory (pickaxe / torch / lantern / dynamite / lucky charm), start depth at **Surface** (torch/lantern/depth items push deeper), call `exploration.resolve(loadout, depth)`, apply the result through `update_inventory`. **No migration.** Engine unit tests already exist (`tests/unit/cogs/test_mining_exploration.py`); add **one integration test** for the cog wiring. **Rollback** = revert the cog swap; the engine returns to dormant (its state today). |
| **Promotion** | Routed onto `docs/roadmap.md` (Games — a concrete, ungated, ready slice) + this plan. Awaiting maintainer go. |

## Scope

**In:** swap `!explore` to construct a `Loadout` from inventory + a Surface-start depth notion
and call `exploration.resolve(...).resolve_to_legacy_tuple()`; apply via the existing
`update_inventory` path; one integration test; update the games folio + `current-state` on ship.

**Out (later brainstorm steps, each its own approved PR):** the Workshop / crafting mutation
service (§2.4 / §5 step 2); AI-active "Guide" narration + image cards (§2.6 / §5 step 3 —
**AI-gated**, waits on the AI orchestration foundation); unifying the two inventory tables
(explicitly out of scope in the brainstorm).

## Suggested PR shape

One focused PR on `cogs/mining_cog.py` + `tests/unit/cogs/` (the integration test). Behaviour
change to one user-facing command → small, risk-isolated, easy to review and revert.

## Provenance

Promoted from [`../ideas/mining_exploration_brainstorm.md`](../ideas/mining_exploration_brainstorm.md)
§5 step 1 on 2026-06-08 as a live demo of the idea-backlog grooming loop
([`../ideas/README.md`](../ideas/README.md)). The brainstorm remains the home for the
not-yet-promoted mining ideas (depth/biomes, crafting, AI guide, image cards).
