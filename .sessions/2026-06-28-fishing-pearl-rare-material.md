# 2026-06-28 — Fishing: the "pearl" rare-material drop + a premium-bait pearl craft

> **Status:** `complete`

**Run type:** routine · dispatch

## What I'm about to do

Empty-fire dispatch. S1's first ▶ Next-startable item names the offline successor explicitly:

> ▶ **Next offline successor:** extend the same caught-fish craft pattern to … a **fish-loot
> rare-material drop** (a dedicated craft material, not just a double fish). Pure + sim-pinnable,
> self-mergeable.

(The rod-ladder craft path the same bullet offers as the alternative already shipped in #1515.)

**The slice — the "pearl" 🦪, a rare fishing material with a real, repeatable sink:**

1. **Drop** — a successful reel can also yield a **pearl** (a dedicated inventory item, *not* a
   fish / dex row), at a chance that scales with the caught fish's `size_rank` (bigger fish → better
   odds). Pure roll in `utils/fishing/rewards.py`, sim-pinned, byte-identical when it doesn't fire.
2. **Sink (repeatable, no dead-item)** — a **pearl-only recipe** crafts the premium **Royal Feast**
   bait, the one bait deliberately left with *no* fish-craft path (a pure coin sink today). Pearls
   give it a gameplay-native, repeatable earn path (bait is consumed, so pearls never go dead);
   coins stay the fast alternative. Mirrors `craft_bait` exactly.
3. **Surface** — the catch message announces a pearl, the bait shop shows the pearl recipe + your
   pearl count, and `!craftpearl` / a bait-shop select crafts the feast.

No DB migration (pearls reuse the generic `mining_inventory` item store). Offline + sim-pinned;
self-mergeable on green.

## What shipped (PR #1518)

The **pearl** 🦪 — a fish-loot rare-material drop with a real, repeatable sink:

- **`utils/fishing/rewards.py`** — `PEARL_ITEM`, `pearl_drop_chance(size_rank)` (size-scaled:
  2% at rank 1 → ~10% at trophy tier, capped 15%), and `roll_pearl_drop` (drawn after the
  bonus-catch roll on the shared rng). Pure, byte-identical when it doesn't fire.
- **`services/fishing_workflow.py`** — `commit_catch` grants the pearl in the same atomic catch
  transaction (the fish grant stays the *last* `update_mining_item` call — a stable seam); a new
  `pearl_found` flag on `FishResult`; and `craft_pearl_bait` — the pearl→Royal-Feast conversion.
- **`utils/fishing/bait.py`** — `PEARL_BAIT_RECIPES` (`feast` = 4 pearls), `pearl_recipe`,
  `pearl_recipe_text`, `pearl_craftable_key_for`, with a tested *disjointness* invariant (a bait is
  fish-craftable XOR pearl-craftable, never both).
- **Surface** — the catch message announces a pearl, the bait shop shows a "Craft from pearls" field
  (with your pearl count) + a `_PearlCraftSelect`, and `!craftpearl` (aliases `pearlcraft`).
- **Numbers** sim-pinned in [`../planning/fishing-pearl-numbers-2026-06-28.md`](../planning/fishing-pearl-numbers-2026-06-28.md);
  no DB migration (pearls reuse the generic `mining_inventory` store).
- **Tests** — +24 (rewards drop math/rate/monotonicity; commit-catch grant ordering byte-identical
  when no pearl; `craft_pearl_bait` debit/stack/reject; bait recipe helpers + disjointness).
- Regenerated the dashboard/site artifacts (`dashboard/data/dashboard.json`, `botsite/data/site.json`,
  `botsite/site/data.js`) — the new command bumped the committed counts (Q-0167 freshness guard).

CI mirror green: `check_quality --full` (ruff/black/isort/mypy + 12,950 tests), `check_architecture
--mode strict` 0 errors. Self-merged on green (small, contained, additive — `CLASS: feature`,
self-initiated Q-0172).

## 📤 Run report

- **Did:** built the fish-loot rare-material drop (the pearl) + its repeatable premium-bait craft
  sink, the named S1 ▶ Next offline successor · **Outcome:** shipped
- **Shipped:** #1518 — pearl drop (`rewards`), `craft_pearl_bait` (`fishing_workflow`), pearl recipes
  (`bait`), bait-shop + cast-view + `!craftpearl` surface, +24 tests, sim-pinned numbers doc.
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none (merge auto-deploys; pearls use the existing inventory table — no
  seed/migration step)
- **⚑ Self-initiated:** yes — empty-fire dispatch; promoted the S1-named offline successor (a captured
  ▶ Next item, grounded in the live queue) → built + shipped without a dispatch/owner ask (Q-0172).
- **↪ Next:** S1 ▶ now names the next offline successor — a rare *material* feeding a **new** craft
  target (cosmetic/structure), or the rod-ladder recipe-browser UI. Both pure + sim-pinnable.

## ⟲ Previous-session review (Q-0102)

The previous run (#1500, "sharpen S1 ▶ Next with an offline item") did the right *meta* thing — it
recognised that an empty-fire dispatch needs an offline-startable S1 lane and added one — but it
pointed at an idea (`fishing-gear-stats`) that had **already shipped that same run** (#1504), so the
handoff it left was already stale when written. The deeper lesson: a ▶ Next pointer should name the
*not-yet-built* successor, not the just-shipped feature. This run honoured that — the fishing craft
bullet already carried a concrete "▶ Next offline successor" naming the rare-material drop, which made
*this* dispatch's "decide what to do" step a single read. **System improvement:** the freshness guard
`check_drift`/▶-Next checker (#1476) catches a *stale* ▶ Next, but not a ▶ Next that points at
already-merged work; a cheap extension would flag a ▶ Next bullet whose linked idea/plan doc is marked
`historical`/`built` (idea below).

## 💡 Session idea (Q-0089)

**A "▶-Next points at unbuilt work" lint.** Extend the ▶-Next freshness guard (#1476): when a sector
`▶ Next startable` item links an idea/plan doc, fail (warn-first) if that doc's `Status:` is
`historical`/`built`/`shipped` — i.e. the pointer names work that's already done. This catches exactly
the #1500 stale-handoff class at the root, cheaply, offline. (Dedup-checked `docs/ideas/` — the
existing handoff-hygiene/freshness ideas cover *staleness of prose*, not *points-at-shipped-doc*; this
is the distinct sub-case.) Worth having because the dispatch loop's whole speed depends on the ▶ Next
line being a trustworthy "build this next."

## Doc audit (Q-0104)

- New planning doc `fishing-pearl-numbers-2026-06-28.md` reachable from S1-bot.md ▶ Next + this card;
  `check_docs --strict` green (no orphans, Status token present).
- S1-bot.md ▶ Next de-staled to mark the pearl drop shipped + name the next successor.
- Ledger: PR #1518 is *in-flight at write time* — `check_current_state_ledger --strict` tracks merged
  PRs; benign newest-merge lag, the next reconciliation pass folds it in (marker #1500, next #1530).
- No owner decisions/contracts to route (self-initiated additive feature, no new Q).
