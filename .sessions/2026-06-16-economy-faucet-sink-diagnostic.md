# Session — games-economy faucet/sink diagnostic (`!platform economy`)

> **Status:** `in-progress`

## Why

The live ▶ Next action (current-state, band-#930 decade queue §4): build the read-only
faucet/sink economy diagnostic so the owner can *observe* whether the games economy inflates
instead of guessing from static balance sims. Gate cleared — respec (#912) + structures sinks
(#905 Forge / #910 Home) now emit real sink reasons. Turn-key plan:
`docs/planning/games-economy-faucet-sink-diagnostic-plan-2026-06-15.md`.

## What I'm shipping (this PR)

A read-only operator read model that sums the **economy audit ledger** (`economy_audit_log`,
already written on every coin movement) into a per-guild **faucet vs. sink** view — coins
minted, drained, net flow, mint:drain ratio + verdict, and the per-reason breakdown over a
time window — surfaced as `!platform economy [days]` beside `media` / `event_bus`. No new
writes, no new reasons, content-free (counts + coin totals only, no per-user rows).

- `utils/db/economy.py` — `economy_flow_by_reason(guild_id, *, since=None)` pure read
  (`SELECT reason, SUM(delta), COUNT(*) ... GROUP BY reason`), windowed by `occurred_at`.
- `services/economy_flow_service.py` (new) — `EconomyFlowReport`/`ReasonFlow` + `build_flow_report`;
  classifies each reason by the **sign** of its summed delta (self-cleaning — new reasons sort
  automatically), computes totals/ratio/verdict (inflating ⚠ / draining / balanced / no activity).
- `cogs/diagnostic/_platform_embeds.py` — `build_economy_flow_embed`; `diagnostic_cog.py` —
  `!platform economy [days]` (alias `coinflow`).
- Tests: `tests/unit/services/test_economy_flow_service.py` (split/sort/ratio/edge cases) +
  `tests/unit/db/test_economy_db_txn.py` (SQL-shape: group-by, windowed `occurred_at`).

## Verification

`check_quality.py --full` green (9905 passed) · `check_architecture.py --mode strict` 0 errors.
