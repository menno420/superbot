# Session — 2026-06-24 · settle-once guard for blackjack PvP (slice 2)

> **Status:** `complete` — blackjack PvP adoption + relocation of `SettleOnceMixin` to `utils/`.
> Continues the same dispatch run that shipped PR #1444. PR #1445.

**Trigger:** continuation of this run's own handoff. PR #1444 closed the cross-game terminal contract for
RPS PvP + deathmatch bot-duel; the documented remaining adopter was **blackjack PvP settlement** — the
third money-handling terminal path.

## What shipped

- **Relocated `SettleOnceMixin` → `disbot/utils/terminal_guard.py`** (from `views/`). Blackjack's terminal
  state is `_PvPState`, which lives in `services/`, and **`services/` may not import `views/`**
  (zero-tolerance arch rule). The mixin is pure logic with no view dependency and is now needed by both
  layers → per `docs/helper-policy.md` its correct home is `utils/`. Pure move: the two existing adopters
  (RPS PvP, deathmatch bot-duel) re-point their import; the unit test moves to `tests/unit/utils/`. No
  behaviour change for them.
- **Blackjack PvP** (`views/blackjack/pvp_view.py`): `_PvPState(SettleOnceMixin)`; `_resolve_pvp` claims
  the terminal transition at the top, so a second settlement (a per-player `BlackjackView` firing
  `on_finish` twice, or a late duplicate) short-circuits — no duplicate result embed, no redundant
  (idempotent) wager settle. The pre-existing `_pvp.pop(key, None)` stays (drops the live-match registry
  entry) but is no longer load-bearing as the double-settle guard.
- **Tests:** relocated primitive test + 2 blackjack regression tests (win settles once / tie refunds once,
  each with a racing second `_resolve_pvp` proven a no-op).
- **Games-readiness map:** the terminal-contract row flipped **Not Done → Done** (all three money/terminal
  paths now guarded); doc path reference updated to `utils/`.

## ✅ Verification

`check_quality.py --full` → **12525 passed, 48 skipped, 2 xfailed** (mypy + black/isort/ruff green).
`check_architecture --mode strict` → **0 errors** (49 pre-existing warnings, none new) — confirms the
relocation removed the would-be `services → views` edge cleanly. `check_quality --check-only` green
(isort auto-fixed the two re-pointed imports pre-push). No stale `views.terminal_guard` references remain.

## Note for a future session

Blackjack **tournament** settlement (`tournament_views.py`) is a separate multi-round flow, not a
single-shot PvP settle — I did not force the mixin onto it. If a double-settle vector is found in the
per-round tournament payout, the same `SettleOnceMixin` (now in `utils/`) is the ready primitive. Flagged
in the games-map row, not left as silent debt.

## 💡 Session idea (Q-0089)

**Promote last session's `AskUserQuestion` per-option `preview` idea into `docs/ideas/`.** (Carried from
this run's slice-1 review: a strong session idea — render a mockup of each option's resulting UX for setup
/design forks — currently lives only in the `2026-06-24-setup-log-channel-rework.md` log, where it isn't
groomable.) My *own* new idea this session: **a `check_architecture` rule "a `discord.ui.View` (or game
state object) that calls a wager-settle helper in a method also reachable from `on_timeout`/a finish
callback must adopt `SettleOnceMixin`"** — the CI ratchet form of the manual double-settle hunt this run
did across four views by hand. Same shape as the slice-1 idea but now sharper (the mixin exists and has
proven itself across three adopters, so the guard has a concrete target). Dedup-checked `docs/ideas/` — no
settle-once/terminal-guard idea present. Captured, not built (the guard should earn a couple more
sessions of trust first, per its own Q-0105 kill-switch posture).

## ⟲ Previous-session review (Q-0102)

Previous: **this run's slice 1** (`2026-06-24-game-settle-once-guard.md`, PR #1444). **Did well:** scoped
slice 1 to two views as a focused PR and explicitly *named the residual* (blackjack, different shape) in
both the games-map and the handoff — which is exactly what let slice 2 start cleanly. **Missed:** it put
the new `SettleOnceMixin` in `views/` without checking whether a *non-view* adopter would soon need it —
which it did, one slice later, forcing this session's relocation to `utils/`. **System improvement:** when
introducing a shared primitive, ask "which layers will adopt this?" *before* choosing its home —
`docs/helper-policy.md` already says cross-layer helpers go in `utils/`, but slice 1 placed by the *first*
adopter's layer, not the *eventual* set. A cheap habit: a primitive with an obvious second adopter in
another layer should start in `utils/`. (No CLAUDE.md edit — helper-policy already covers it; this is a
recall failure, not a missing rule.)

## 📋 Doc audit (Q-0104)

Games-readiness map updated (row → Done, path → `utils/`). No `current-state.md` ledger entry until #1445
merges (ledger checker keys off merged PRs; the next reconciliation pass picks up #1444 + #1445). No owner
*decision* made (self-initiated correctness slice). The new primitive's home + rationale are documented in
its own module docstring. `check_docs --strict` green.

## 📤 Run report

- **Run type:** routine · dispatch
- **What shipped this slice:** PR #1445 — `SettleOnceMixin` relocated to `utils/` + blackjack PvP adoption
  + the cross-game terminal-contract row closed (Not Done → Done). (This run also shipped PR #1444, the
  primitive + RPS/deathmatch adoption.)
- **⚑ Self-initiated:** yes — completed a production-readiness "Not Done" → Done correctness/safety row
  (no dispatch/owner ask). Contained, reversible, test-covered.
- **⚑ Owner-decisions:** none
- **⚑ Owner-manual-steps:** none
- **Bug-book:** no entry flipped (this generalizes the BUG-0013 class, already FIXED). BUG-0019 #1 and
  BUG-0009 newest-towers remain OPEN/gated.
- **Remarks:** CodeGraph rebuilt clean on resume (52428 nodes). Two slices shipped this run (#1444, #1445)
  — well under the ~700K ceiling; stopping here at a clean boundary (the terminal-contract row is now
  fully Done across all three money paths).
