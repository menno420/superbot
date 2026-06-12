# Games wager money-safety plan — P0-1 (2026-06-12)

> **Status:** `plan` — the design for hardening track **P0-1** ([hardening
> roadmap](production-readiness/hardening-roadmap-2026-06-12.md)). **Owner-picked as the
> next implementation session** (2026-06-12, question panel — the same round that answered
> Q-0097/Q-0082-interim/Q-0115). Evidence: the [games readiness
> map](production-readiness/games-production-readiness-map-2026-06-12.md); claims below
> re-verified against source 2026-06-12. One risky-runtime PR; ADR-002 (game state not
> restart-safe) stays accepted — this plan fixes **money**, not game-state restartability.

## The defect class (source-verified)

| Path | Today | Risk |
|---|---|---|
| RPS PvP settle — `views/rps/pvp_play.py` (~L156–173) | `economy_service.credit(winner)` **then** `debit(loser, allow_overdraft=True)` | Crash between calls **mints coins**; loser can spend down pre-settle and only ever pays floor-zero |
| Blackjack PvP settle — `views/blackjack/pvp_view.py` (~L209–215) | Same sequential credit→overdraft-debit | Same mint/short-pay class |
| RPS tournament entry — `cogs/rps_tournament/_persistence.py` | Entry fee debited at registration; checkpoint row written separately | Crash between debit and row ⇒ fee lost with nothing to refund |
| Blackjack tournament entry/payout — `cogs/blackjack_cog.py` + `cogs/blackjack/` | Paid-entry debit→checkpoint and multi-winner payouts are multi-call | Same loss class; repeated settle calls have **no idempotency key** |

**The good news (verified):** `services/economy_service.py` already exposes the atomic
primitives — `transfer()`, `debit_in_txn()` / `credit_in_txn()`, `bet_and_settle()`,
`refund()` — the wager flows simply don't compose them. P0-1 is therefore a
**composition + idempotency + checkpoint-ordering** job on the existing seam, not new
plumbing. (Mining's `services/mining_workflow.py` — one transaction per op, AST-fenced —
is the shipped precedent to mirror.)

## Design — `services/game_wager_workflow.py`

One audited workflow service owning every two-party / paid-entry money movement in games.
All ops compose `*_in_txn` primitives inside **one transaction**, call
`emit_audit_action`, and are **idempotent by a wager/entry key** (replays return the
recorded outcome instead of re-paying).

| Op | Transactionally |
|---|---|
| `open_pvp_wager(match_id, a, b, stake)` | Escrow-debit both players + write the stake into the existing `game_state` checkpoint row — one txn (D1 below) |
| `settle_pvp(match_id, winner)` | Pay the pot from escrow to the winner + mark the checkpoint settled — one txn, idempotent by `match_id` |
| `refund_pvp(match_id)` | Return both stakes + clear — one txn, idempotent (decline/timeout/abort path) |
| `enter_tournament(tid, player, fee)` | Fee debit **+ entry row in the same txn** (kills the lost-fee window) |
| `payout_tournament(tid, placements)` | All winner credits in one txn, idempotent by `(tid)` — a re-run can never double-pay |
| `refund_tournament(tid)` | Recovery refund, idempotent (the existing recovery paths route here) |

**D1 — escrow-at-accept (recommended, the one product-visible change).** PvP stakes leave
both wallets when the challenge is **accepted** (escrowed into the checkpoint row), not at
resolve. This deletes the overdraft semantics outright — the loser *cannot* be short at
settle. Fallback if the owner dislikes the timing: keep resolve-time exchange but as one
`transfer()` txn (still atomic; overdraft floor preserved as today's documented behavior).
Default to escrow unless the owner objects on the PR.

**Scope:** blackjack PvP + tournament, RPS PvP + tournament. Solo flows are single-sided
(`bet_and_settle` already exists) — touch only if a free ride-along. Duels/deathmatch have
no coin wager (map-verified) — out of scope.

## Tests + the "stays fixed" layer

1. **Failure injection at every boundary** — monkeypatch the txn connection to raise
   between compose steps; assert **no partial money movement** (balances + audit rows).
2. **Terminal-state matrix** — win/lose/draw/decline/timeout/abort/recovery ×
   {balances, checkpoint state, audit emission}, per game.
3. **Idempotency probes** — double-call `settle_pvp` / `payout_tournament`; second call is
   a no-op returning the recorded outcome.
4. **AST fence (P1-3 slice)** — extend the `test_mining_write_boundary.py` pattern: no raw
   `economy_service.credit/debit` calls from `views/rps/`, `views/blackjack/`,
   `cogs/rps_tournament/`, `cogs/blackjack*` — wagered money moves only through the
   workflow (allowlist for solo `bet_and_settle`).
5. **Live round-trip** on the test bot: one PvP wager + one tournament entry/payout against
   real Postgres.

## Session shape

One PR: the workflow service + the four call-site migrations + tests (+ the fence). No
schema migration expected (escrow rides the existing `game_state` checkpoint rows — verify
field shape first; if a column is genuinely needed, it ships in the same PR per migration
conventions). Read `.claude/rules/mutation-and-db.md` + `docs/ownership.md` § games rows
before editing; run `context_map.py` on each touched file.
