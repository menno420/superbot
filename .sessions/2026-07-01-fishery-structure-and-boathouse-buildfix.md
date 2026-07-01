# 2026-07-01 — Fishery (4th fishing structure) + Boathouse build-crash root fix

> **Status:** `in-progress`

**Run type:** routine · dispatch

## What I'm about to do

Scheduled dispatch fire, no work order → advance the next S1 offline plan slice (the ▶-next
"fourth fishing structure"), plus a bugs-first root fix discovered during orientation.

1. **BUG-0031 (bugs-first, root):** `mining_workflow.build_structure` indexes a hand-maintained
   `_STRUCTURE_BUILD_REASON` map with `[structure]`; `boathouse` was never added (shipped #1605),
   so **`!boathouse` build raises `KeyError: 'boathouse'`** in production. Root fix kills the
   drift class: derive the audit reason generically (`market.structure_build_reason`) instead of a
   map that must be kept in sync, + a regression test over **every** registered structure.

2. **Feature — the Fishery (4th fishing structure, S1 ▶-next offline successor):** the three coral
   axes so far are quality (Tide Pool), throughput (Dock), endurance (Boathouse). The Fishery is the
   fresh **yield/abundance** lever — it raises the lucky-double-catch chance (`roll_bonus_catch`),
   folded into `commit_catch`. Byte-identical when unbuilt (level 0 ⇒ +0.0 ⇒ base 0.10 chance).
   Coral + wood sink, same registry/audited-`build_structure`/panel/`!fishery`/Structures-hub pattern.

CI mirror green + arch strict before each ship. Self-merge on green (contained, test-covered).
