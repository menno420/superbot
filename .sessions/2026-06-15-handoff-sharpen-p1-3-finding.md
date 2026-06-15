# Session — 2026-06-15 · handoff sharpen + P1-3 coverage finding (follow-up to #906)

> **Status:** `complete`

## What this is

A small docs-only follow-up to PR #906 (the Railway log-triage analyzer, merged), sharpening
the handoff per the dispatch routine's step 8. While scoping a second slice I investigated the
**P1-3 invariants** track (the band-#900 queue's next `ready` slot) and found a real result worth
recording so the next run doesn't redo it:

**All four P1-3-named tracks already carry an invariant.** P1-3's roadmap framing ("add AST/registry
parity tests, one per track") reads as open work, but each named track is already covered:

| Track | Existing invariant |
|---|---|
| settings (declared→consumer · no dual pointer+binding · backfill parity) | `test_backfill_target_declaration_parity` · `test_pointer_lane_ledger` · `test_no_direct_settings_keys_writes` · `test_guild_config_typed_accessors` |
| games cross-game terminal-state | `tests/unit/services/test_game_wager_workflow_integration.py` + the `test_game_wager_write_boundary` P0-1 fence |
| AI declared-vs-consumed tools | `test_catalogue_covers_exactly_the_registered_tools` + `test_all_tool_specs_match_the_catalogue` (`all_tool_specs()` == CATALOGUE == the maximal dispatchable `build_registry` set) + the `tests/evals/test_eval_coverage.py` drift guard |
| BTD6 derived-value provenance | `tests/unit/services/test_btd6_source_registry_m3b.py` (migration-042 source-provenance parity) |

So **P1-3 is "find a *specific* uncovered contract, or close the track as substantially-covered"**,
not "land one invariant per track from scratch." Recorded in `current-state.md` ▶ Next action so the
next dispatch starts from this, not from a redundant build.

## Changes

- `docs/current-state.md` ▶ Next action: dropped the **log-triage** slice (shipped #906), noted
  **Home (Slice C) unblocked** by #905, and folded in the **P1-3 coverage finding** (twice — the
  startable-slices line + the "remaining P1" parenthetical).
- `docs/owner/active-work.md`: moved my `claude/hopeful-allen-r7qsg8` claim to Recently cleared (#906 merged).

## Handoff / next

Next ▶ startable, independent of any open parallel work: **mining Home (Slice C)** — now unblocked,
reuses #905's generic `mining_structures` table + `build_structure`; v1 is art-light (a Home-level
backdrop/frame on the PIL character card, byte-identical when unbuilt). It IS a medium build
(generalize #905's forge-specific `build_structure` cost/naming by structure + a `character_render.py`
backdrop hook + a render call-site + UI) — give it a full session. Then respec-polish/titles (E/F).
P1-3: see the finding above — scope a *specific* uncovered contract before treating it as open.

## ⟲ Note (continuity)

Q-0089 new idea, Q-0102 prev-session review, and the Q-0104 doc audit for this run are recorded in
the **#906 session card** (`.sessions/2026-06-15-railway-log-triage-analyzer.md`) — this card is a
thin same-session docs follow-up, not a separate session, so it points there rather than duplicating
the enders. Known inter-cadence ledger drift: #902/#904 (routine PRs) are not yet in Recently-shipped;
they fall in the **#930 reconciliation window** (marker is #900) and are that pass's to fold in —
left deliberately, per the Q-0107 cadence (a dispatch session doesn't run the reconciliation pass).
