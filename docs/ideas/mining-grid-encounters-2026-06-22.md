# Mining grid encounters — depth-gated sparse events (2026-06-22)

> **✅ OWNER DECISION (Q-0198, 2026-06-28, question panel):** **build the encounters, loot/flavour-only
> first** — combat is a fast-follow that reuses the creature/deathmatch engine (never a third bespoke
> combat model). Depth/chance/cooldown, a live roll (not per-cell-deterministic), and navigator-button
> resolution ride this doc's recommended defaults, sim-tunable at build time. Canonical: router Q-0198.

> **Status:** `ideas`. **Not a plan, not approval.** Capture doc. Source + binding contracts +
> `docs/current-state.md` win. **Subsystem:** games, mining.
>
> Origin: the owner's grid-Mine design (Q-0173). The grid Mine (hub-redesign PR 3) shipped
> **encounter-free** by explicit owner decision — *"v1 = free movement, NO encounters … encounters
> ARE wanted, as a separate later session."* This captures that deferred follow-up so it isn't lost.

## The idea

Layer **sparse, depth-gated random encounters** onto the shipped grid-Mine navigator
(`views/mining/grid_mine_view.py`). The owner's stated shape: *"after a certain depth you can get
random encounters, but not too many."* So an encounter is a low-probability event that can fire on a
`move` / `Mine here` action once the player is deep enough — surfaced in the navigator embed with a
small set of resolution buttons (fight / flee / loot), resolved through the audited
`mining_workflow` seam (RS02), never a direct write.

Deliberately small and additive (the same discipline the grid v1 followed):

- **Gated** — no encounters above a depth threshold; the surface bands stay calm so casual play is
  unchanged (the Q-0087 "never mandatory-feeling" rule).
- **Sparse** — a low per-action chance with a cooldown, so roaming isn't interrupt-spam.
- **Seam-reuse** — rewards/penalties route through `economy_service` / `update_mining_item` /
  `game_xp_service` exactly like `mine_here`; combat (if any) reuses the deathmatch/creature engine
  rather than inventing a third combat model.

## Why it's worth having

- It is the **one owner-named** grid follow-up — already scoped by Q-0173, just deferred.
- The grid already persists position + a seed-deterministic world, so an encounter table keyed on
  `(seed, x, y, z)` would be **deterministic and shareable** for free (the same property that makes
  the grid itself shareable).
- Gives depth a *reason* beyond richer ore — a light risk/reward curve as you descend.

## Relationship to the existing "wild encounters" idea

Distinct from [`wild-encounters-activity-spawning-2026-06-20.md`](./wild-encounters-activity-spawning-2026-06-20.md):
that one is **chat-activity-triggered** channel spawns (passive, message-driven, claim-button). This
one is **exploration-triggered** while actively roaming the mine grid (depth-gated, per-action). They
could **share one encounter-resolution engine** (a pure `utils/.../encounter.py` table + an audited
workflow op) with two different *triggers* — worth designing the engine once if both are built.

## Open design questions — ROUTED to the owner as router **Q-0198** (DISCUSS, 2026-06-22)

The four decisions below are now posed to the owner with recommended defaults in
[`docs/owner/maintainer-question-router.md` § Q-0198](../owner/maintainer-question-router.md) — once
he answers, a runtime session builds it (small PRs, runtime-verified). Do **not** build ahead of that.

1. **Depth threshold + per-action chance + cooldown** (config-driven; the "not too many" tuning).
2. **Encounter content** — pure flavour/loot events vs. light combat (and if combat, which engine).
3. **Determinism** — fully seed-deterministic per cell, or a live roll (the grid is deterministic;
   encounters may want a live element so two players' runs differ).
4. **Resolution UI** — extra buttons on the navigator vs. a swapped sub-view.

## Anti-patterns

- ❌ Frequent/blocking encounters that turn roaming into a slog (sparse + gated, always).
- ❌ A third bespoke combat model — reuse deathmatch/creature battle if combat is in scope.
- ❌ A direct write from the view — every mutation goes through `mining_workflow` (RS02/Q-0071).

→ relates [`planning/mining-hub-redesign-2026-06-15.md`](../planning/mining-hub-redesign-2026-06-15.md)
(PR 3 shipped, this is its "Later — encounters") · Q-0173 · Q-0087 (never mandatory) ·
Q-0071 (atomic workflow) · [`wild-encounters-activity-spawning-2026-06-20.md`](./wild-encounters-activity-spawning-2026-06-20.md).
