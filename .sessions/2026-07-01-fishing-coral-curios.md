# 2026-07-01 — Fishing: coral 🪸 deepwater rare-material drop → cosmetic curio collectibles

> **Status:** `complete`

**Run type:** `routine · dispatch`

## What I'm about to do

Scheduled dispatch fire, no work order. Both FIX-backlog bugs are gated (BUG-0019 #1 = owner
design fork; BUG-0009 remainder = data-gated on release-order source), so I take the next real
plan slice under S1's completion-first posture: the **fishing rare-material successor** — the
explicit `[offline]` "▶ Next offline successor" in `docs/current-state/S1-bot.md`.

Mirror the pearl pattern (#1518) with a **second** rare reel-drop material feeding a **new,
non-bait craft target** (the roadmap's "a dedicated craft material that feeds a *new* craft
target rather than the premium bait — e.g. a cosmetic or a structure"):

- **coral 🪸** — a rare reel-drop material, **deepwater-venue-gated** (thematic reef find; also
  gives the boat venue #1340 a unique payoff — deepens an existing feature). Mirrors the pearl:
  stored in the generic `mining_inventory` (no migration), never a dex/trophy row, byte-identical
  economics when it doesn't drop.
- **Curios** (`utils/fishing/curios.py`) — cosmetic **carving collectibles** crafted from coral
  (`ItemKind.TREASURE` → non-sellable, no crafting use), a completionist collection like the
  Fishdex/trophies. Shown by the **existing** inventory browser (no new panel) + a `!curios`
  list + `!craftcurio`. Also catalogues coral + the pre-existing (uncatalogued) pearl for clean
  display — fix-on-sight drift.

No migration, no minigame-view mechanic wiring, pure + sim-pinnable, self-mergeable. Deepens two
completion units (fishing + inventory).

Aim: 2–3 slices — this material→collection slice first; then a second plan slice if budget allows.

## What shipped (PR #1596)

- **`utils/fishing/rewards.py`** — `CORAL_ITEM` + `CORAL_DROP_CHANCE` (0.06) + `coral_drop_chance(venue)`
  / `roll_coral_drop(venue, rng)`: a flat, **deepwater-only** reel-drop (shore short-circuits to
  `False` without consuming rng, so shore casts stay byte-identical). Mirrors the pearl roll but
  venue-gated instead of size-scaled.
- **`utils/fishing/curios.py`** (new, pure) — the cosmetic curio catalog (Carved Coral Shell 🐚 /
  Coral Seahorse 🌊 / Coral Idol 🗿, ascending coral cost 2/4/8) + `curio_by_key` / `craftable_key_for`
  / `cost_text` / `collection_progress` (mirrors the bait recipe helpers).
- **`services/fishing_workflow.py`** — `commit_catch` rolls + grants coral (deepwater only) in the
  same atomic transaction (order bonus→pearl→coral), sets `FishResult.coral_found`; new `craft_curio`
  (debit coral, grant the `TREASURE` curio, one transaction — no coins, never sold) + `CurioCraftResult`.
- **`utils/mining/items.py`** — the three curios catalogued as `ItemKind.TREASURE` (→ `market.sell_price`
  returns `None`: non-sellable, no coin faucet). Coral left uncatalogued as a material (mirrors the
  pearl → unknown → not sellable).
- **`cogs/fishing_cog.py`** — `!curios` (collection + coral + per-curio ✅/🔨/🔒 progress) and
  `!craftcurio <name>` (aliases `carve`/`curiocraft`).
- **`cogs/inventory_cog.py`** — `ITEM_CATALOGUE` gains a **Fishing** category (coral + the
  previously-uncatalogued **pearl** — fix-on-sight) and a **Collectibles** category (the curios), with
  category order + meta; so the existing browser shows them cleanly instead of the "Other" catch-all.
- **`views/fishing/cast_view.py`** — renders the "🪸 A piece of coral!" line on a coral reel.
- **Tests (+~20):** `test_fishing_rewards.py` (coral roll: deepwater-only, deterministic, ≈rate) ·
  `test_fishing_curios.py` (catalog/recipes pinned, TREASURE-non-sellable contract, collection tally) ·
  `test_fishing_workflow_curio.py` (craft debits coral/grants curio/rejects unknown+insufficient) ·
  `test_fishing_workflow.py` (commit grants coral only in deepwater, never on shore, byte-identical
  when unlucky).
- **Docs:** `docs/planning/fishing-coral-numbers-2026-07-01.md` (sim-pinned) + de-staled the S1
  fishing bullet (marked the successor shipped, linked the numbers doc, pointed at the next successor).
  Regenerated dashboard/site artifacts (2 new commands → 476 total).

CI mirror green (`check_quality.py --full`: 13,414 passed; arch 0 errors).

## 📤 Run report

- **Did:** shipped the S1 completion-first `[offline]` "▶ next offline successor" — the fishing
  rare-material variant (coral 🪸 deepwater drop → cosmetic curio collectibles), deepening the fishing
  + inventory units and giving the boat venue a unique payoff · **Outcome:** shipped (CI green,
  auto-merge armed).
- **Shipped:** #1596.
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** none.
- **⚑ Owner manual steps:** none (pure logic + additive content; no migration, live on next
  auto-deploy). To try it: `!sail` to deepwater, `!fish` until coral drops, then `!curios` / `!craftcurio`.
- **⚑ Self-initiated:** yes — no work order this fire; I took the next plan slice under S1's
  completion-first posture (the roadmap-named next offline successor). Contained, reversible,
  test-covered; flagged here per Q-0172 for owner review.
- **↪ Next:** a *second* curio tier or a **structure**-target variant (a deepwater material that
  builds a fishing structure rather than a collectible) — pure + sim-pinnable, self-mergeable (see the
  de-staled S1 bullet). Both FIX-backlog bugs (BUG-0019 #1 owner design fork; BUG-0009 newest-towers
  data-gated on release-order source) remain owner/data-gated.

## 💡 Session idea (Q-0089)

**A "dead capability declaration" guard.** While scoping Inventory punch #3 I found the
`@capability(...)` decorator (`core/runtime/subsystem_capabilities.py`) has **zero real usages** in the
whole codebase (the only match is the docstring example) — so the reverse-map diagnostic
(`!platform capability-map`) is always empty, and the registry's `capabilities` lists are governance
declarations enforced elsewhere (ui_permissions / GovernanceMutationPipeline), not via this decorator.
A tiny checker (or a `!platform` note) that flags a **declared** capability with **no** enforcing use
would turn "aspirational placeholder vs. real capability" from tribal knowledge into a visible signal —
exactly the ambiguity that makes Inventory punch #3 an owner call today. Genuine (it directly shaped
this session's pick), not filler. Captured only here (it needs an owner decision on enforce-vs-remove
before it becomes a plan — router-worthy, not self-buildable).

## ⟲ Previous-session review (Q-0102)

The previous run (#1595, Inventory item-detail per-rarity-tier fields) was a clean, well-tested
completion-first punch (#4 closed) — no complaint. What it (and the whole recent Inventory cert thread)
**left implicit** is that the unit's remaining `◐ → ✔` blockers (#1–#3) are *all* owner-gated, which
isn't obvious until you trace the `@capability` decorator and find it dead (above). **System
improvement:** a completion cert's punch-list should mark each item's **gate** (`[offline]` /
`[owner]` / `[needs-live-bot]`) inline, the same tags S1's ▶ Next uses — so a dispatch run can tell at
a glance which punches are self-buildable vs. which need the owner, without re-deriving it (I spent
real budget confirming Inventory's punches were all owner-gated before pivoting). The Inventory cert
does this in prose ("owner, minor") but not with the machine-readable tag.

## Doc audit (Q-0104)

- No owner *decision* to route (self-initiated build under the existing completion-first posture; the
  standing Q-0172 idea-gate covers it, flagged on the run report).
- Ledger: this session's PR is the newest merge; the living-ledger reconciliation is the recon
  routine's job (not due until #1620) — no drift to fix on sight.
- New doc (`fishing-coral-numbers-2026-07-01.md`) is reachable (linked from S1-bot.md) and badged
  `living-ledger` (matching the sibling pearl numbers doc; `numbers-pin` is not an allowed badge — a
  small trap I hit and corrected).
- Generated artifacts re-exported (dashboard/site) so the new commands aren't stale; `check_quality
  --full` green confirms `check_docs` / `check_artifacts_fresh` clean.

## 🛠 Friction → guard (Q-0194)

- **Friction:** I badged the new numbers doc `numbers-pin` (it *is* a numbers pin), but that token
  isn't in `check_docs`'s allowed set → red. **Guard (shipped):** none needed beyond the fix — the
  `check_docs` badge check already *is* the enforcing guard; it caught the invalid token immediately.
  The durable lesson (recorded here): copy an existing sibling doc's `Status:` badge rather than
  inventing a descriptive one.
- **Friction:** running `isort` over `disbot/ tests/ scripts/` flagged a `tests/` file from an
  unrelated merged PR — a false alarm, since CI/`check_quality` **exclude `tests/`** from formatters.
  **Guard (habit):** trust `check_quality.py` (pinned scope) over ad-hoc bare-tool invocations — the
  exact trap CLAUDE.md §CI-parity already warns about; reconfirmed here.

## Context delta

- **Needed but not pointed to:** that curios/coral are *cosmetic collectibles reusing `mining_inventory`
  with no migration* is the design insight that made this a tight slice — it's implicit in how the
  pearl works but nowhere stated. The pearl/coral pattern ("rare reel-drop material → a craft sink,
  stored in the generic mining inventory, never a dex/trophy row") is now a clear two-instance template
  for the next successor.
- **Pointed to but didn't need:** the mining structures panel machinery — I scoped a structure-target
  variant first, then chose the lighter collectible target (no new panel/effect wiring), which is why
  the slice stayed tight. The structure variant remains the named next successor for a later run.
