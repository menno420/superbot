# 2026-06-27 — Mining/character gear loadout presets (V-14 / Q-0175 Phase-1 unified-loadout model)

> **Status:** `complete`

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

## What shipped (PR #1499)

**Named gear loadout presets** — the unified-loadout half of the fishing/open-world plan's Phase 1
(the fish-set + 7-level half was already shipped). You save your equipped gear as a named set
(`mining`/`combat`/`fishing`, cap 10) and swap your whole loadout with one click.

- **Migration 101** `mining_loadout_presets` — one row per `(user_id, guild_id, name, slot)`,
  mirroring `mining_equipment`'s direct-lane column types (RC-8A — same lane as equip, no audited
  service; gear swaps aren't money writes).
- **`utils/db/games/mining_loadout.py`** — `save_loadout` / `get_loadout` / `list_loadouts` /
  `delete_loadout` CRUD; re-exported from `utils.db`.
- **`services/mining_workflow.py`** — `save_loadout` (snapshot current equipment, name-normalised,
  cap-guarded), `apply_loadout` (equip every still-owned saved item, **clear any other filled slot**
  so a preset restores exactly, report anything no longer owned — all in one transaction),
  `list_loadouts`, `delete_loadout`. Additive: a player with no preset is byte-identical.
- **`views/mining/gear_panel.py`** — a `💾 Loadouts` gear-panel button → a `MiningLoadoutView`
  (apply-select · delete-select · 💾 Save-current modal · ↩ Gear back).
- **`cogs/mining_cog.py`** — `!loadout` (`!loadouts`): `save <name>` · `<name>`/`apply <name>` ·
  `list` · `delete <name>`.
- **Tests** — `tests/unit/db/test_mining_loadout_db.py` (5) + `tests/unit/services/test_mining_loadout.py`
  (12): CRUD, snapshot, cap, ownership-filtering + clear-others + missing-report, no-op when nothing owned.

**Bug-first cleanup folded in (root cause, one source of truth):** adding `!loadout` pushed
`mining_cog.py` over the 800-LOC decomposition fail-threshold. Rather than suppress, I removed the
real bloat — the `!gear` command **reimplemented** the gear embed + paper-doll render that already
exist in the view layer. Extracted `build_gear_command_embed` into `gear_panel.py` (where embed
builders belong) and made `!gear` reuse it + `render_gear_doll`. `!gear` output is unchanged; the cog
dropped 842 → 787 LOC and a duplicate embed builder is gone.

CI mirror green end-to-end (`check_quality.py --full`: 12828 passed; black/isort/ruff/mypy clean) ·
`check_architecture --mode strict` 0 errors · `check_consistency --mode strict` clean · dashboard
artifacts regenerated (the new command). Born-red gate held the merge until this card flipped
`complete`.

## 💡 Session idea (Q-0089)

**Fishing-specific gear stats — close the "matching gear → better fishing" half of Q-0175.** The plan
says matching gear should *increase the activity's bonus* ("fishing gear → better fishing"). This run
shipped the *swap* mechanism; the *bonus* half has nothing to bias yet because `EffectiveStats` only
models mining + combat stats. Idea: add a `fishing_power` (and/or `bite_luck`) field to
`utils/equipment.EffectiveStats`, a small set of fishing-flavoured gear items, and have
`fishing_workflow.begin_cast` read it as a 4th how-well knob (rod × bait × weather × gear) — turning
loadout presets from cosmetic convenience into a real optimisation. Genuinely believe in this: it's
the natural next slice that makes the just-shipped preset feature *matter*, and it reuses the existing
stat seam rather than inventing one. (Will file to `docs/ideas/` if not already captured.)

## ⟲ Previous-session review (Q-0102)

Reviewing `2026-06-27-btd6-qa-accuracy...` (BTD6 damage-type/status interaction grounding): **did well**
— it treated a background research agent's 164-Q corpus as *input to verify, not truth* (Q-0120), and
caught real errors by checking the game dump (Sniper is Sharp/no-lead, not Normal), then cross-checked
the curated `damage_types.json` against game-sourced `immune_to` so a future re-seed can't silently rot
it. That cross-check-against-ground-truth pattern is exactly the discipline the workflow wants. **Could
improve / system note:** that run shipped a brand-new committed data file (`damage_types.json`) whose
correctness rests on the cross-check guard — but the guard only covers `blocked_by_properties` vs
`immune_to`; the status-effect rows (glue/ice/knockback/stun behaviour) and the pop-guide prose have
**no** anchor, so they can drift unnoticed. **System improvement surfaced:** the BTD6 anchor-coverage
guard (#1466) inventories rubric/fixture *numbers*; there's a parallel gap for **curated-fact prose**
in these new knowledge JSONs — a future S2/S3 slice could extend the anchor idea to "every curated
interaction claim is either cross-checked against game data or on a documented `[wiki]` allowlist,"
generalising #1466's dollar/HP coverage to qualitative facts.

## 📤 Run report

- **Did:** shipped named gear loadout presets (save/swap/delete) + removed a `!gear` embed-builder
  duplication that the feature exposed · **Outcome:** shipped
- **Shipped:** #1499 — loadout presets (migration 101 + db CRUD + workflow + `💾 Loadouts` panel +
  `!loadout`); `!gear` embed builder moved to the view layer (cog 842→787 LOC, DRY)
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none (migration 101 applies automatically on the next boot/auto-deploy)
- **⚑ Self-initiated:** gear loadout presets — promoted the Phase-1 unified-loadout slice of
  [`fishing-open-world-expansion-plan-2026-06-18.md`](../docs/planning/fishing-open-world-expansion-plan-2026-06-18.md)
  (Q-0175 / V-14) with no dispatch/owner ask (Q-0172); empty-fire dispatch run
- **↪ Next:** S1 sector ▶ stays as before (Essential Setup PR 3b · botsite React · giveaway PR 1 —
  all `[needs-live-bot]`/owner). The natural follow-on to *this* feature is the Q-0089 idea above
  (fishing-specific gear stats → make loadout presets a real optimisation).

## Doc audit (Q-0104)

`check_current_state_ledger --strict` (green; 26 newer merges = benign post-#1470-marker lag, the
reconciliation routine records them — Q-0124/Q-0166) · `check_docs --strict` green · de-staled the
fishing-open-world plan (loadout piece ✅), the S1 sector file (Recently-shipped), and the games folio
(loadout shipped, Phase 2 still gated). No owner decision this run → router untouched.
