# Session — BUG-0009 slice 2: deterministic Geraldo per-level item lists

> **Status:** `complete`

**Dispatch:** empty/generic work order → took the live ▶ Next action = **BUG-0009
slice 2: per-level item lists (Geraldo per-level groupings)**, the same proven
shape as slice 1 (#924, MK-related family). PR **#926**.

## What shipped
- **`btd6_data_service.geraldo_items_by_unlock_level()`** — deterministic
  ascending `(level, (item, …))` grouping; the relation the model mis-assembled.
- **`btd6_context_service.deterministic_geraldo_per_level_reply()`** — fires on
  the per-level / by-level / "level N" shape (Geraldo cue + level/list cue);
  formats the full grouping, a single level's unlocks, or an honest "nothing
  unlocks at level N". `None` for single-item lookups / strategy → reach model.
- **`btd6_context_service.deterministic_btd6_list_reply()`** — one dispatcher
  fronting both BUG-0009 builders (MK first, then Geraldo). `natural_language_stage`
  now calls this single seam; slice 3 (newest-towers) appends its builder here.
- **Slice 2b (same PR) — game mode groupings**, the owner's third named
  BUG-0009 mislabel. `btd6_data_service.modes_by_kind()` owns the
  difficulty→mode→modifier grouping (BTD6's own `ModeEntry.kind` split);
  `btd6_context_service.deterministic_modes_reply()` fires on a clear modes
  enumeration, guarded against the qualifier over-route (a message naming
  another roster entity — "which towers work on impoppable mode" — defers to the
  model). Appended to the dispatcher after MK + Geraldo. CHIMPS is now always a
  mode, Easy/Medium/Hard difficulties.
- Tests: `tests/unit/services/test_btd6_geraldo_per_level.py` (13) +
  `test_btd6_modes_grouping.py` (12) +
  `test_geraldo_per_level_question_floored_before_model` in the stage suite.
- Bug-book BUG-0009 marked slices 2 + 2b fixed; current-state ▶ re-pointed.

**Verification:** `python3.10 scripts/check_quality.py --full` green (9889, +29
new tests pass) · `check_architecture --mode strict` 0 errors · ledger + docs
strict green.

## Handoff (next routine reads current-state ▶)
- **Next ▶ startable = security service tiers 1+2** (band-#900 queue slot 9,
  plan-first — raid detection + account-age filter, Q-0111; cite
  `ux/pattern-library.md` `mock_security_*` pattern_ids).
- **BUG-0009 slice 3 (newest-towers ordering) is data-gated** — `towers.json`
  has no release-order field. It needs sourced release-order data first
  (ADR-006 / `!btd6ops seed-data` provenance lane); once present, the builder is
  trivial: a new `deterministic_*` reply appended to `deterministic_btd6_list_reply`.
- The BUG-0009 floor is now a clean extension point (`deterministic_btd6_list_reply`)
  — any future "grounded-but-mis-grouped" list family is one builder + one tuple entry.

## 💡 Session idea (Q-0089)
**A "list-shape" answerability probe for the deterministic BTD6 floor.** BUG-0009
keeps surfacing because we discover mis-grouped list families *reactively* (the
owner reports one, we add a builder). A small dev-only script
(`scripts/btd6_list_shapes.py`) could enumerate, from the dataset itself, every
"grouped enumeration" the data supports (MK-by-tower, Geraldo-by-level,
towers-by-class, bloons-by-property, bosses-by-immunity…) and report which have a
deterministic builder vs. which are still model-assembled — turning BUG-0009 from
a reactive bug into a *covered surface* the way the 34/34 tool-eval ratchet did
for tools. Genuinely believe in it: it's the same "own the labelled answer"
discipline, made systematic. Captured here, not built (out of this slice's scope).

## ⟲ Previous-session review (Q-0102)
The previous run (#924, BUG-0009 slice 1) did the hard design work well — it
established the exact proven shape (deterministic relation in `btd6_data_service`
+ a narrow reply in `btd6_context_service` + a pre-emptive floor before the
model, because the value-only guard can't catch a mis-grouping) and documented it
crisply in the bug book. That made *this* slice fast. One thing it left on the
floor: it wired `deterministic_mk_reference_reply` **directly** into the stage,
so a second family (this one) would have meant a second near-identical send/audit
block — copy-paste drift waiting to happen. **System improvement made this
session:** I introduced the `deterministic_btd6_list_reply` dispatcher so the
stage has *one* BUG-0009 seam and new families are append-only. The general
lesson worth carrying: when a fix is explicitly "slice 1 of N", the first slice
should land the *extension point*, not just the first instance — the second
slice shouldn't have to refactor the first.

## Doc audit (Q-0104)
- `check_docs.py --strict` exit 0; `check_quality --full` exit 0; arch 0; session
  gate green.
- New code reachable from existing folios (btd6 subsystem); no new doc file needed
  (builders live in already-documented services).
- **Mid-session, PR #925 merged on main** (the docs-hygiene scannable-pointer +
  stamp-wall archive). I re-synced origin/main into the branch and resolved the
  `current-state.md` conflict by hand: **kept #925's scannable `▶ NEXT` lead line
  but updated it** (slices 2/2b shipped → next = security tiers) and kept my
  updated `▶ Next action` paragraph. No markers left; full mirror re-run green.
- **Known ledger drift (NOT this session's):** `check_current_state_ledger.py
  --strict` exits 1 on **8 PRs from other parallel sessions** (#913/#914/#915/
  #916/#919/#921/#923/#925) that aren't yet in the ledger/archive. This is the
  expected reconcile-lag class — they're from sessions I have no context on, so I
  deliberately did **not** guess entries for them (that risks wrong/fabricated
  ledger lines + more conflicts). **The band-#930 reconciliation pass (due very
  soon) should reconcile these.** This check is advisory-only (not in
  `code-quality.yml`), so it does not gate #926's merge.
- Recently-shipped ratchet is over its soft cap (pre-existing from #924; #925
  already did a stamp-wall trim) — left for the reconciliation pass, not groomed
  here (soft warning, no CI impact).

## ⚠ Parallel-work note for the next agent / reconciliation
Two BUG-0009 doc PRs ran concurrently this evening: **#925** (docs-only:
scannable pointer + stamp archive) and **#926** (this — slices 2/2b code). They
collided on `current-state.md`'s ▶ pointer. Resolved cleanly, but it's a concrete
instance of the parallel-session conflict the claim ledger / born-red gate exist
to reduce. The system-improvement angle is in the Q-0102 note above.
