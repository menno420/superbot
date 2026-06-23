# 2026-06-23 — Discoverability U4: surface `!btd6strat` (BTD6 Strategy button)

> **Status:** `complete` — fleet unit U4 of the discoverability audit shipped (PR #1372). Full CI mirror
> green (12114 passed); arch strict 0; check_docs strict ✓. Continuation of Session 1 (#1370) + the
> Phase-0 fleet rails (#1371). Self-merge on green (no active fleet coordinator).

> **Run type:** `manual · continuation` (next startable item after the merged foundation)

## What I did

Fixed one of the two recorded reachability gaps as **fleet unit U4**
([fleet plan](../docs/planning/consolidation-fleet-plan-2026-06-23.md)):

1. **Surfaced `!btd6strat`** — added a **"📋 Strategy" child button to `BTD6PanelView`** (row 2, next to
   Maps), mirroring the existing Live-Events/Towers buttons: it defers ephemerally and opens the strategy
   browse embed (`views.btd6.strategy_browse.build_browse_embed(limit=10)` — the same surface as
   `!btd6strat browse`). So the member-facing strategy memory is now reachable by clicking through the
   BTD6 hub.
2. **Closed the guard gap** — allowlisted `btd6strat` as reachable-via-panel (source-cited) and dropped it
   from `test_command_reachability._BASELINE`. Guard: **214 commands → 75 reachable · 138 exempt · 1 gap**
   (was 2). The remaining gap (`!temproles`) is routed to fleet unit U2 (roles).
3. **Pinned the new button** — added `btd6:strategy` to the panel's custom-id regression set
   (`test_btd6_panel_legacy_custom_ids._NEW_CUSTOM_IDS`), which doubles as the button-present guard.

Also **GC'd the stale merged claim** `claude__phase0-completion.md` (#1371) and **corrected a factual
error in the fleet plan**: its Phase-0.5 settings-orphan guard was specced to read
`subsystem_schema.all_schemas()` "(offline)", but that returns `{}` offline (schemas register at
`cog_load`) — I verified it and routed the static alternative (`utils/settings_keys/<x>.py` +
`register_schemas` AST sites) into the plan so Phase 0.5 isn't built on an empty source.

**Acceptance met:** Strategy button surfaces the browse embed; `btd6strat` no longer a gap; full CI mirror
+ arch strict + check_docs strict all green. Contained to btd6 files + the guard allowlist/baseline/doc.

> **⚑ Self-initiated:** picking up U4 (the btd6strat gap) was the next startable item after the merged
> foundation, routed by the fleet plan — not invented. The fleet-plan Phase-0.5 correction + the stale-claim
> GC are drift-on-sight (Q-0166). All reversible, test-covered. No new owner decision.

## 💡 Session idea (Q-0089)

**Let a panel button *declare* the command it surfaces, so the reachability guard can verify panel-button
reachability statically.** The guard's one real limitation (documented) is that it can't see hand-wired
hub-panel buttons — so each panel-reachable command (btd6events/btd6ref/paragon/cbattle…/now btd6strat)
is verified by hand and allowlisted. If a panel button carried a tiny machine-readable marker linking its
`custom_id` to the command(s) it surfaces (e.g. `extras={"surfaces": ["btd6strat"]}` on the button, or a
module-level `SURFACES = {"btd6:strategy": "btd6strat"}` map the guard reads via AST), the guard could
**auto-confirm** those commands instead of relying on a hand-maintained allowlist — closing the gap
between "the guard flags it" and "but it's actually reachable via a button." Cheap, high-leverage, and it
makes the whole allowlist self-verifying. Captured for grooming → `docs/ideas/`.

## ⟲ Previous-session review (Q-0102)

The immediately-prior session (#1371, the Phase-0 fleet rails) did genuinely excellent leverage work: it
**extracted the shared `hub_children` discovery primitive** (the exact Q-0089 idea Session 1 had captured
— the self-improving loop visibly working) and wrote a well-structured fleet plan (held-set + file-disjoint
units + born-red→coordinator protocol) that made *this* session's pickup trivial — I read it and knew
exactly which unit (U4) to take and which files I owned. **What it missed:** the fleet plan specced
Phase-0.5 as "turn-key" using `subsystem_schema.all_schemas()` "(offline)" — but that source is empty
offline (the same bot-walk blindness the guard was meant to avoid), so a worker would have built on a
0-row source. **System improvement it surfaces:** a plan that labels a step "turn-key" should *run* its
proposed data source first — the one-line check (`all_schemas()` → `{}`) would have caught it. I corrected
the plan in place; the broader lesson is "verify the offline data source actually has data before writing
'reuse X (offline)' in a CI-guard spec." Same discipline as this session's guard, which *emits* its
counts rather than asserting them in prose.

## 📋 Doc audit (Q-0104)

Anything not in a durable home? **No.** The fix + its disposition are in the gap ledger
(`docs/audits/command-reachability-gaps-2026-06-23.md`, btd6strat moved to reachable-via-panel + the
baseline now 1), the fleet-plan Phase-0.5 correction is recorded, the allowlist carries the source-cited
reason, and the button is pinned by the custom-id regression test. `check_docs --strict` ✓,
`check_quality --full` ✓, arch strict 0. No new owner decision → no router entry owed. Reconciliation
marker untouched (next pass at #1380 records #1370–#1372).

## 📤 Run report

- **Run type:** `manual · continuation` (fleet unit U4).
- **Slices shipped this run:** 1 PR (#1372) — the BTD6 Strategy button + guard baseline 2→1 + the
  fleet-plan Phase-0.5 correction.
- **⚑ Self-initiated:** U4 pickup (routed by the fleet plan) + the Phase-0.5 plan correction + stale-claim
  GC (drift-on-sight). No invented features.
- **⚑ Owner-decisions:** none.
- **⚑ Owner-manual-steps:** none — no migration/data step; the merge auto-deploys. The new button appears
  on **newly-posted** BTD6 panel anchors; existing production anchors keep their historical button row
  (Discord doesn't re-render persistent messages) — re-post the panel to get the Strategy button on an
  existing anchor, if desired.
- **Bug-book:** no entries opened/closed.
