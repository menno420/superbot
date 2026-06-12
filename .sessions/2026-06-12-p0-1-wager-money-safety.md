# 2026-06-12 — P0-1 games wager money-safety (game_wager_workflow)

> **Status:** `audit`

**PR:** #748 (ready, open)
**Branch:** `claude/jolly-keller-plunlc`

## Context

Owner-approved (PR #745) implementation session: execute
[`games-wager-money-safety-plan-2026-06-12.md`](../docs/planning/games-wager-money-safety-plan-2026-06-12.md)
— hardening track **P0-1**. D1 escrow-at-accept the approved default. One risky-runtime PR.

## What shipped (PR #748)

- **`services/game_wager_workflow.py`** — the audited money boundary for every two-party /
  paid-entry game coin move, composing `economy_service.*_in_txn` inside one
  `db.transaction()` (the `mining_workflow` precedent). Ops: `open_pvp_wager`
  (D1 escrow-at-accept), `settle_pvp`, `refund_pvp`, `enter_tournament`,
  `payout_tournament`, `recover_escrow`. PvP settle/refund + tournament payout are
  **idempotent** by `FOR UPDATE` row-consumption (replay = no-op, never double-pays).
- **D1 escrow-at-accept** deletes the credit-then-`allow_overdraft`-debit **mint window**:
  stakes leave both wallets atomically with per-player `*_escrow` `game_state` rows at
  challenge accept; the loser can't be short at settle. If either player can't afford the
  stake the match aborts before dealing (the one product-visible change).
- **All four call sites migrated** (RPS + blackjack PvP escrow/settle; RPS + blackjack
  tournament entry/payout). Removed the dead un-escrowed `deduct_fees` batch debit.
- **`game_state_service`**: `save`/`clear` gain `conn=`; new `fetch_rows_for_update`
  locks escrow rows for an atomic settle. Escrow rows carry the `bet` key, so the 24h GC +
  `recover_escrow` (cog_load / on_guild_remove) refund stranded stakes. **No schema migration.**
- **AST fence** `test_game_wager_write_boundary`: no `economy_service.credit/.debit` in the
  wager files; `allow_overdraft=True` solo-only.
- **Tests**: real-Postgres integration (failure injection at every boundary, terminal-state
  matrix, idempotency — 12 tests) + mock-based CI coverage (10 tests).

## Verification

- `check_quality.py --full` ✓ (black/isort/ruff/mypy + **9144 passed, 3 skipped**)
- `check_architecture.py --mode strict` ✓ (0 errors)
- 12 real-Postgres integration tests ✓ · live boot ✓ (both modified cogs load; escrow
  recovery cog_load tasks run clean)
- `check_docs --strict` ✓ · `check_current_state_ledger --strict` ✓

## Context delta (reflection interview)

- **Needed but not pointed to:** the four call sites span **6 files across 3 layers**
  (challenge-accept *and* resolve for each PvP game live in different view files), and the
  tournament fee debit hides in `utils/tournaments.deduct_fees` — none of these adjacencies
  are in the games folio. The folio now lists the `game_wager_workflow` seam; a "wager money
  flow map" (accept→escrow→settle, per game) would have saved the manual trace.
- **Pointed to but didn't need:** CodeGraph — a known set of files + grep + the plan's
  turn-key op table carried the whole session (the documented "contained change" path).
- **Discovered by hand:** that the generic 24h GC refunds by a single `row["user_id"]`, so
  a two-party escrow must be **per-player rows** (not one canonical-id row) for recovery to
  pay both — this drove the whole escrow row shape and isn't written anywhere.
- **Decisions made alone:** per-player escrow rows in new `*_escrow` subsystems (vs.
  stuffing escrow into the gameplay checkpoint, which the gameplay saves would clobber);
  free-tournament reward left non-row-guarded (zero money-at-risk, single-call); fence
  scoped to explicit wager files + a repo-wide `allow_overdraft` ban.
- **Weak point of what shipped:** prompt escrow recovery (`recover_escrow`) reuses the
  un-transactional refund-then-clear loop; correctness rests on the GC backstop, not a
  second transaction. Acceptable (money is provably safe), but not as tight as the settle path.
- **One change that would have helped:** a lint/hook catch for the
  "bare `black`/`isort`/`ruff` over `tests/`" trap — I hit it (reformatted 269 unrelated
  files; CLAUDE.md warns about exactly this) and had to selectively `git checkout` the
  spurious churn. `check_quality.py` is the only correct path; nothing *stops* the bare run.

## ⟲ Previous-session review (Q-0102)

Reviewing `2026-06-12-reconciliation-cadence-rule.md` (the Q-0107 cadence session): **did
well** — shipped the rule *with* its enforcement (`check_reconciliation_due.py` + 9 tests +
`/session-close` wiring + the marker), so the cadence can't silently rot; the kill-switch
header is exactly the Q-0105 discipline. **Could improve:** it set `Last reconciliation pass:
PR #737` and said "next due at #740", but #741 (the actual first pass) then re-set it — a
one-session window where two markers disagreed. **System improvement it surfaces:** the
reconciliation marker and the "next implementation session" pointer both live as prose in
`current-state.md` and are edited by hand every session — the same drift class the per-lane
bullets fixed. A tiny `scripts/` helper that *reads* the marker + open-PR state and prints
the single authoritative "what's next / is a pass due" line (instead of each session
re-asserting it in prose) would remove the last hand-maintained status sentence.

## 💡 Session idea (Q-0089)

**A `wager-money-flow` doc (or `scripts/wager_flow_map.py`)** that traces every game's
money path accept→escrow→settle/refund and entry→payout across its view/cog files. This
session's single biggest cost was hand-tracing that PvP money touches *four* files per game
(challenge-accept, play-resolve, plus the tournament entry/payout split) with the fee debit
hidden in `utils/tournaments`. A generated map (grep the `game_wager_workflow` call sites +
the `*_escrow`/entry subsystems) would make the next "touch a wager path" session a lookup,
not an archaeology dig — and would double as the fence's human-readable companion. Dedup-checked
`docs/ideas/`: the mining brainstorm and games folio cover *features*, not a money-flow map.

## Notes for next session

- Next hardening track: **P0-2** (Media/YouTube data-minimization, Q-0099 answered) —
  see the [decade queue](../docs/planning/reconciliation-pass-2026-06-12.md).
- Next reconciliation pass is due at **PR #750** (Q-0107).
- `deduct_fees` is gone; `_save_tournament_entry` / `_clear_tournament_entry` remain as
  row primitives (still unit-tested) but are no longer on the production path — the money
  atomicity is in `enter_tournament`. Candidates to retire in a later cleanup.
