# 2026-06-08 — buff stack cap parser-reproducible (cutover fidelity)

**Branch:** `claude/inspiring-cray-tywlxl` · **PR:** #597

## Task
"Continue with the BTD6 data-mapping plan." The plan's living ledger is
`docs/btd6/btd6-gamedata-decode-status.md`. Its ordered "Do next" list is almost
entirely **cutover-gated or maintainer-gated** (new buff/zone numbers can't be
confirmed pre-cutover; income multiplier + MK magnitudes + map removable costs are
maintainer calls). The one clean, ungated, confirmable item the ledger explicitly
flagged was the buff **stack-cap** gap.

## What I did
Closed the flagged gap. The game-native parser path (`map_tower → _map_tier →
`_buffs`) emitted `isGlobal` but **not** the stack cap, even though the renderer
(`btd6_upgrade_detail_service._stack_cap`) reads it. So a future tower cutover
would silently lose the "(stacks up to N)" clause.

- `scripts/parse_gamedata.py` `_buffs()`: pass both dump field names
  (`maxStacks` / `maxStackSize`) through verbatim — faithful structural copy like
  `isGlobal`, `0` preserved, emitted after the nested-tag drop check.
- Tests: fixed the Shinobi test (it asserted the cap *dropped* — encoded the bug) +
  2 new (`both_field_names`, `zero_preserved`).
- Ledger: marked the "known small gap" FIXED + a session-log entry.

## Key facts learned (for next session)
- **`--overlay` only refreshes `{range, footprintRadius}`** — it does **not** rewrite
  `buffs[]`. The committed `buffs[]` are a *fuller, earlier* extraction; the lean
  `_buffs()` is the **cutover** path. So committed buffs carry many fields `_buffs()`
  drops (`customRadius`, `appliesToOwningTower`, `filterInBaseTowerId`,
  `cashPerRound*`, …). They diverge by design; the "--overlay --dry-run is a no-op"
  claim is about `{range, footprintRadius}`, not buffs.
- Therefore "fix `_buffs()` to reproduce committed" is a **cutover-prep** activity,
  not a live-bug fix. Only render-relevant dropped fields are worth emitting; the
  only one the renderer consumes is the stack cap (now done). The rest are inert.
- The remaining data-mapping frontier is genuinely gated — see the ledger's
  "Do next" 1–6. To unblock more: maintainer call on the tower **cutover** (steps
  4–5), the **income multiplier** (needs economy towers to get minimal tiers), and
  **MK magnitudes / map removable costs** (not dump-sourced — curate or skip).

## Verification
`python3.10 scripts/check_quality.py --full` → 8157 passed.
`check_architecture --mode strict` → no new errors (only pre-existing `[known]` xp warns).
