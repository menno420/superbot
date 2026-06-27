# 2026-06-27 — Mining/character gear loadout presets (V-14 / Q-0175 Phase-1 unified-loadout model)

> **Status:** `in-progress`

**Run type:** routine · dispatch

## What I'm about to do

Empty-fire dispatch (no work order). No open PRs; bug-book root-fix backlog is gated (BUG-0009
data-gated, BUG-0019 owner design-fork). Offline self-mergeable lanes were the pick.

**Self-initiated (Q-0172):** promoting the **named gear loadout presets** slice — the remaining
Phase-1 piece of the fishing/open-world unified-character plan
([`docs/planning/fishing-open-world-expansion-plan-2026-06-18.md`](../docs/planning/fishing-open-world-expansion-plan-2026-06-18.md)
§ "One character, swappable gear types", Q-0175 / V-14). The fish-set + 7-level half is shipped;
the unified-loadout half ("*put on fishing gear*" → swap your equipped items to a saved loadout)
was not built. This run builds it.

Scope (additive, reuses the existing **direct-lane** `mining_equipment` seam — no audit needed,
RC-8A): a `mining_loadout_presets` table (migration 101) + `utils/db/games/mining_loadout.py` CRUD +
`mining_workflow` save/apply/list/delete (ownership-validated, equips only items you still own) +
a `💾 Loadouts` Gear-panel surface + `!loadout` command + tests. Byte-identical when no preset
exists (the additive-safety property).

(close-out filled at the end — what shipped, idea, prev-session review, doc audit, run report.)
