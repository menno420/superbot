# Session: Mining Slice B — the Forge structure (gear-tier crafting gate)

> **Status:** `complete` — born-red card (Q-0133) flipped as the deliberate final step.

**Branch:** `claude/peaceful-pascal-1jmb8m` · **Date:** 2026-06-15 · **Type:** runtime feature (S1 bot, mining lane) · **Trigger:** Hermes dispatch work order (mining lane)

## What I'm about to do

Dispatched work order asked for **Slice D (capped skill tree, §7.4)** — but that **already shipped
as #891** (and the "retire `docs/plans/…` duplicate doc" precondition is moot: that file/dir does
not exist on main). Per the routine's already-shipped rule, I'm taking the **genuine next plan
slice** instead: **Slice B — the Forge structure** (current-state ▶ Next action names exactly this;
the plan's recommended order is D→A→B→…, and D #891 + A #897 are done).

**Slice B — Forge** (`docs/planning/mining-structures-skill-tree-plan-2026-06-14.md`):
a built structure (coin + material sink) that gates higher-tier gear crafting, tying structures into
the existing 5-tier gear ladder.

- **Generic `mining_structures` table** (migration 073) + `utils/db/games/mining_structures.py`
  (`get_structures` read · `set_structure_level` write primitive → boundary ratchet) — reusable for
  Home (Slice C).
- **Pure `utils/mining/structures.py`**: the Forge build-cost ladder (coins + materials, rising) +
  the recipe→required-forge-level map derived from `equipment.gear_tier` (bronze/iron/silver free;
  **gold → forge L1, diamond → forge L2**; tools/structures free). Additive: most progression
  untouched; only the top two gear tiers gate behind a cheap, immediately-buildable forge.
- **`mining_workflow.build_structure`**: audited coin-debit + material-consume + level-raise in ONE
  transaction (the `vault_upgrade` precedent). Gate `craft`/`quick_craft` on the forge requirement
  (zero extra I/O for forge-free recipes — existing craft paths unchanged).
- **UI**: `🔥 Forge` HubView panel + hub button + `!forge` command; recipe browser shows the gate.
- Numbers pinned in `docs/planning/forge-numbers-2026-06-15.md` + tests.

**Verify:** `check_quality --full` green + `check_architecture --mode strict` 0.

**Note for the owner / next run:** the dispatch fired a **stale/already-shipped slice** (asked for D
= #891). This is the Q-0142 dispatch-by-prediction class recurring — flagged in the handoff.

## What shipped

Slice B — the **Forge** — end-to-end, all in PR #905:

- **migration 073** `mining_structures` (generic `(user,guild,structure,level)` — reused by Slice C
  Home) + `utils/db/games/mining_structures.py` (`get_structures` read · `set_structure_level` write
  primitive → added to the RS02 boundary ratchet).
- **pure `utils/mining/structures.py`** — the forge build-cost ladder (Forge I: 3 000🪙 + 25 iron +
  15 stone; Forge II: 8 000🪙 + 20 gold + 10 iron; `MAX_FORGE_LEVEL=2`) + the recipe→required-forge
  map derived from `equipment.gear_tier`: **gold → L1, diamond → L2; bronze/iron/silver gear, tools,
  structures stay free** (`forge_level = max(0, tier_index − 3)`).
- **`mining_workflow.build_structure`** — coin debit + material consume + level raise in ONE
  transaction (the `vault_upgrade` precedent extended with a material leg); `_forge_gate` on
  `craft`/`quick_craft` that does **zero extra DB I/O** for forge-free recipes (so the
  characterization net stays byte-identical and existing craft paths are unchanged).
- **UI** — `views/mining/forge_panel.py` (`🔥 Forge` HubView child) + hub button (row 4) + `!forge`;
  the recipe browser now shows a 🔒 lock + the forge requirement on gated recipes.
- Numbers pinned in `docs/planning/forge-numbers-2026-06-15.md`; tests:
  `tests/unit/utils/test_mining_structures.py` (pure) + `tests/unit/services/test_mining_forge.py`
  (gate + build). `check_quality --full` green (9754); `check_architecture --mode strict` 0 errors.

**Deliberate behavior change (documented, reversible):** gold/diamond gear now needs a built forge.
Additive for everything else; the forge is cheap and buildable immediately, and the requirement map
is one pure function (set every tier to 0 to fully revert). Sibling mining slices (#891/#897) set the
self-merge precedent; this one carries the same risk profile + full test coverage → self-merged.

## 💡 Session idea (Q-0089)

**A `dispatch_ledger_precheck` step for the Hermes dispatch skill** — this run was dispatched a
**stale slice** (Slice D, already #891), the third time the Q-0142 "dispatch by predicted slice, not
verified-against-ledger" class has bitten (see #868). The existing fix tells Hermes to *pick* the
next slice by description-vs-ledger; the missing half is a **guard the dispatcher runs before firing**:
grep the slice's marker (PR #, plan `✅ SHIPPED` tag, or current-state Recently-shipped) and, if the
named slice is already shipped, **auto-advance to the next ▶ startable one** (or refuse + re-pick)
rather than firing a no-op order the executor has to detect and recover from. A tiny stdlib
`scripts/check_dispatch_freshness.py` (work-order slice-id → "shipped?/startable?") wired into
`routine_fire.py` would close the loop at the source. Dedup-checked `docs/ideas/` — the closest is
`dispatch-phase-gate-precheck` (#898, gates *feature class* at the dispatcher); this is its sibling
for *slice freshness*. Worth having: the executor recovering gracefully (as here) is the safety net,
not the fix — the dispatcher firing fresh orders is.

## ⟲ Previous-session review (Q-0102)

Previous run = **#900-ish, "merge dispatch + night-executor into one routine prompt" (Q-0145)**. Did
well: it correctly consolidated the fleet to 2 routine prompts and, crucially, folded the executor's
**bug-book orient + bounded-continuation handoff** into the single dispatch prompt — which is exactly
the scaffolding that let *this* run recover cleanly from a bad dispatch (sync-first caught the stale
clone; work-order-is-a-hint let me ignore the already-shipped order and build the real next slice).
What it (and the whole chain) still misses: the consolidation hardened the **executor** side of the
loop but left the **dispatcher** side firing predicted slice-ids — this run is the third stale-slice
dispatch. The system improvement is the Q-0089 idea above: a freshness precheck at the dispatcher, so
the foolproofing isn't only "the executor recovers" but "the order is correct when fired." The
routine prompt is genuinely strong now; the remaining weak link is upstream of it, in Hermes' fire path.

## 🔎 Doc audit (Q-0104)

`current-state.md`: ▶ Next action re-pointed (Forge → E/F/C), mining lane bullet + #905
Recently-shipped entry added; the plan doc's Slice B flipped to ✅ SHIPPED + the recommended-order
line updated; numbers doc reachable (linked from the plan). `check_current_state_ledger --strict`
and `check_docs --strict` both run below. No owner decision was made this run (dispatched build, no
new Q) — nothing for the router. Bug-book: no OPEN entry matches this work; none to flip FIXED.

