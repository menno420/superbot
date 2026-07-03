# 2026-07-03 — Unified layout-success simulator (owner-directed capture)

> **Status:** `complete` — PR #1687. Owner-directed capture. Docs-only; no `disbot/` code.

## What shipped (PR #1687)

1. **[`docs/ideas/rebuild-layout-success-simulator-2026-07-03.md`](../docs/ideas/rebuild-layout-success-simulator-2026-07-03.md)**
   — one instruction-driven layout-success simulator (deterministic + AI user models) scoring any
   generated hub/menu by **task success rate** ("create roles" → does a user model reach the right
   node?), unifying the **5 existing bespoke UX-layout sims** (`claim_layout_sim`,
   `help_menu_grouping_sim`, `role_menu_layout_sim`, `settings_order_sim`, `setup_wizard_sim`).
   Quantifies the "self-explanatory" half of the Q-0234 oracle; mechanism behind Q-0230's "sim
   optimizes arrangement". **Pipeline:** sim defines the proper settings/layout bot-wide → **live
   co-test is the final review**. Instruction corpus reused by the NL router.
2. **Router Q-0235** with verbatim-quote provenance; ledger #1687; ideas index.

## 💡 Session idea (Q-0089)

The layout-success simulator itself is this capture's genuine idea (already indexed). No second
idea manufactured — per Q-0089's anti-filler bar; the session produced five real ideas today.

## ⟲ Previous-session review (Q-0102)

Previous card: **#1686 (oracle + verification strategy).** It cleanly closed the last open rubric
item and recorded the phase gates. **Good pattern it set, continued here:** applying the rubric to
my *own* response — before answering "use simulations," I grepped and found five existing sims
rather than describing a greenfield tool. That's the #1685→#1686 lesson (grep first) now habitual.
**Improvement:** the five layout sims are themselves un-unified prior art — a small current-repo
grooming task (a pointer doc cross-linking them, or a note in `simulation-driven-design`) would make
the fragmentation visible to the next agent without waiting for the rebuild; worth a future groom.

## Docs audit (Q-0104)

- `check_docs --strict` + `check_plan_homing` + `check_session_gate` at close (below)
- Owner decision → Q-0235; ideas index updated; ledger #1687
- Chat-only residue: none — the simulator idea + the sim-defines-settings / live-cotest-final-review
  pipeline are durable in the idea file + Q-0235.

## ⚑ Self-initiated

None — Q-0235 is owner-directed (the simulation idea + the "centralize quickly / define settings /
final review in live testing" framing were the owner's words).

## Session arc (seven PRs — Stage 1, conventions & review-system complete)

#1679 Stage-1 review · #1680 conventions freeze · #1683 permissions + endorsement · #1684
hub/navigation/presets · #1685 critical-review rubric · #1686 oracle + verification strategy ·
#1687 layout-success simulator.

## For the next session

- **Run the rubric over today's decision logs** (self-check).
- **Resolve** the last open sub-decision: preset hide-vs-disable (Q-0232).
- **Stage 2 — the subsystem walk** (rubric-driven, 10 probes × 43) → Gate V (verification fleet) →
  Phase B → migration.
- Grooming candidates: the class-4 `check_plan_staleness.py` extension; a pointer unifying the 5
  layout sims.
