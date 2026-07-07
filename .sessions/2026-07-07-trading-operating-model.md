# 2026-07-07 — Trading operating model (Q-0251: decision ledger + sniper bucket + 3-way hybrid)

> **Status:** `complete`
> **Branch:** `claude/rebuild-plan-consolidation-c34c0b` (restarted from main after #1796) · **PR:** #1797
> **Continues:** the 2026-07-07 consolidation conversation (PRs #1791–#1796)

## What happened

Recorded **Q-0251** — the owner's trading operating model, strengthened:

1. **Decision-ledger mock trades = the v1 product** (no broker execution): signals recorded
   before their outcome window, verified after; **git commits as tamper-evident timestamps** —
   forward testing nothing can retro-fake. The Q-0250 API-broker paper lane demotes to a later
   realism upgrade.
2. **Leaderboard** per the owner's asks (gain % per time and per trade count) + honesty columns
   (drawdown, sample size, exposure).
3. **Sniper bucket** for rare-but-precise strategies: uncertainty-aware stats (5-for-5 proves the
   pattern class, not the edge), forward-test emphasis, notification wiring on live triggers,
   and named as a reserve-deployment trigger.
4. **3-way hybrid = a backtestable allocator** (active / swing / reserve) with pre-declared
   reserve-deployment rules — lucky moments defined in advance, never hindsight.
5. **Crypto** re-scoped: backtest robustness data eventually, never a venue.

Capture doc Part 3 gained the operating-model subsection; the founding brief now has two recorded
design inputs (Q-0250 + Q-0251). Checks: `check_docs --strict` ✓.

## Session enders

Same conversation as the main consolidation session — enders live in
`.sessions/2026-07-07-rebuild-idea-consolidation.md`.
