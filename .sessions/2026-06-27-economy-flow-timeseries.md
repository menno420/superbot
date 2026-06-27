# 2026-06-27 — Games-economy observability: faucet/sink timeseries (+ inflation finding)

> **Status:** `in-progress`

**Run type:** routine · dispatch

## What this run is doing

Empty-fire dispatch. The clean offline lanes are thin (BTD6 anchors complete; procedures→skills
Batch 2 needs a CLAUDE.md self-edit — autonomous-blocked by Q-0106; botsite PR 2 flips the live
homepage — owner-paced; BUG-0009 newest-towers is data-gated; Project Moon Slice A/B need a network
datamine or runtime verification; fishing Phase 2 is owner-design-gated). The cleanest genuinely-
useful offline slice is the **§6 follow-up tail** of the shipped games-economy faucet/sink diagnostic
([plan](../planning/games-economy-faucet-sink-diagnostic-plan-2026-06-15.md), shipped #1044): the
all-time + windowed *aggregate* view + verdict shipped, but the per-day **trend** and the **inflation
health-finding** were explicitly "capture, don't build here". Both are read-only / content-free,
extend shipped work, and serve the owner's stated need (watch whether the mining economy is inflating
*over time*, not from a single window aggregate).

**Slice 1 (PR) — economy-flow timeseries (per-day trend).** A pure DB read fn
(`economy_flow_daily`, GROUP BY day over `economy_audit_log.occurred_at`) → a typed
`EconomyFlowTimeseries` service read model → a `!platform economytrend [days]` admin view (per-day
minted/drained/net table + a dependency-free net-flow sparkline + an overall trend read). Read-only,
content-free, no migration (rides the existing `occurred_at` column), no new reason.

**Slice 2 (assessed after Slice 1) — inflation health-finding.** Wire the existing `verdict` into the
P1-2 health-findings lifecycle (#843) so a sustained "inflating ⚠" surfaces as a persistent operator
finding manageable via `!platform finding`.

Also fixing on sight (Q-0166 drift): the roadmap §Games "Now" line still lists **P0-1 wager
money-safety** as the next implementation session, but its plan is `historical` — EXECUTED in #748.

## Verification
*(filled at close)*
