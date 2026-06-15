# Session: Mining Slice B — the Forge structure (gear-tier crafting gate)

> **Status:** `in-progress` — born-red card (Q-0133); flips to `complete` as the final step.

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
