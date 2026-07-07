# Founding brief — the trading research repo (dedicated Fable session)

> **Status:** `plan` — the launch brief + paste-ready prompt for **program session 3 of 3**
> (Q-0252): a dedicated **Claude Fable 5, `/effort ultracode`** research-and-plan session whose
> deliverable is the **executable founding plan** for the stock-market research + trading repo.
> Launch index:
> [`program-three-sessions-launch-index-2026-07-07.md`](program-three-sessions-launch-index-2026-07-07.md).
> Design inputs are already owner-ruled — **Q-0250** (stocks-first, US large-cap tech;
> point-in-time universe; API-broker paper lane later; DEGIRO = read-only manual benchmark) and
> **Q-0251** (decision-ledger mock trades; sniper bucket; the 3-way hybrid allocator) — do not
> re-litigate them; build on them. Governance: **Q-0241/Q-0240** · **Q-0249** (no budget caps —
> telemetry) · execution sequencing per **Q-0247** (trading is repo #3; this session only PLANS).

## 1. Reading route (in order)

1. `.claude/CLAUDE.md` → `docs/collaboration-model.md` → `docs/current-state.md` S3 row.
2. **The program frame:** [`../ideas/multi-repo-program-kit-lab-trading-2026-07-07.md`](../ideas/multi-repo-program-kit-lab-trading-2026-07-07.md)
   Part 3 in full — the discipline-mapping table, the rigor list, the operating-model subsection.
3. **The two rulings verbatim:** router **Q-0250 + Q-0251** (`docs/owner/maintainer-question-router.md`).
4. **The pattern precedents in this repo:** the sim-decides-design fleet (`tools/sim/`,
   `tools/game_sim/`) and the drift-pin discipline · the parity/golden reproducibility model
   (`parity/README.md`) · the promotion-gate idiom (the canonical plan §4/§5) · botsite/dashboard
   export (`scripts/export_dashboard_data.py`, `botsite/`) as the tracker-website precedent.
5. The [kit-lab founding brief](kit-lab-repo-founding-brief-2026-07-07.md) §2 lanes 5–6 (the
   governance home + friction protocol this repo will instantiate as kit consumer #3).

## 2. The mandate — research deeply, then produce ONE executable founding plan

Research lanes (fan out; verify external facts with real sources — WebSearch/WebFetch are in
scope for vendor/API research; cite what you adopt):

1. **Data foundation** — point-in-time US large-cap equities data: candidate sources (free tiers
   vs paid; e.g. what daily+intraday history, split/dividend adjustment quality, and
   point-in-time index/universe membership each actually offers), the snapshot-pinning design
   (data versions committed/hashed so every backtest replays byte-identically), and the
   corporate-actions handling contract. Recommend one starting stack with costs; flag ⚑.
2. **The decision ledger** — schema + mechanics of Q-0251's core: a mock-trade record
   (instrument, direction, size, thesis, entry, exit rules, horizon, strategy id) committed
   **before** its outcome window (git timestamp = tamper evidence), plus the verification job
   that grades closed windows against market data and writes results back. Include the
   standing-entry form (Q-0251's "entry at a decided level") and the sniper-alert path.
3. **The backtest engine** — architecture choice (event-driven vs vectorized; build-vs-adopt an
   existing open-source engine with the Q-0105 adopt-freely + kill-switch discipline),
   deterministic replay, pessimistic cost model (commission/spread/slippage), and the
   walk-forward harness. The engine is the repo's `sim/` — same role, same rigor.
4. **The statistics layer** — multiple-testing correction for an autonomous strategy search
   (holdout embargo, deflated Sharpe or equivalent), the leaderboard metrics (owner's gain-%-per-
   time and per-trade-count + drawdown/sample/exposure honesty columns), and the **sniper-bucket
   small-N evaluation** (uncertainty-aware; forward-test-weighted).
5. **The promotion ladder as CI** — in-sample → out-of-sample → walk-forward → forward
   (decision-ledger) → paper-API → capped-live, each gate machine-checked; define each gate's
   pass criteria and its checker. The ladder is this repo's golden-parity: born-red until earned.
6. **The allocator** — the 3-way hybrid (active / swing / reserve) as a first-class backtestable
   strategy: declared weight/rebalance/profit-routing/reserve-refill rules; **pre-declared
   reserve-deployment triggers** (drawdown/crash thresholds, standing entries, sniper signals).
7. **The tracker website** — strategy registry, leaderboards, decision-ledger browser, the
   owner's DEGIRO transaction-export ingestion (his real portfolio as a benchmark lane beside
   the strategies), notification transport for sniper alerts. Botsite-pattern: generated from
   repo data, agent-deployable.
8. **Repo skeleton** — kit adoption (consumer #3), governance instantiation (local router,
   claims, session logs, CI mirror), the Q-0248/Q-0249 telemetry from session one, and the
   first build band (what ships in the repo's first 2–3 PRs — recommended: ledger + verifier +
   one deliberately-simple reference strategy end-to-end, so the whole pipe is proven before any
   clever strategy exists).

**Output artifacts:** (1) `docs/planning/trading-repo-founding-plan-<date>.md` — the executable
plan (architecture, the chosen data stack ⚑, the ladder spec, the first build band, provisioning
checklist with owner-input items — e.g. data-vendor signup if paid, broker paper account when
that later gate nears); (2) a decisions log (⚑ everything); (3) router Q-blocks only for genuine
product forks (e.g. if the recommended data stack has a real monthly cost — Q-0249 says
observe-first, but a *new recurring* cost is an owner-visible flag).

## 3. What NOT to do

- No execution machinery toward real money — the real-money brake and its caps are a distant,
  owner-gated tier; v1 is the decision ledger (Q-0251), not a broker integration.
- Don't re-open Q-0250/Q-0251 (market scope, mock-trade model, hybrid shape — ruled).
- Don't build in this session — this is research-and-plan; the repo doesn't exist yet (Q-0247:
  trading is #3, after the kickoff and the kit lab).
- Don't promise returns anywhere in the plan — the measurable goal is strategies that survive
  falsification and beat costs out-of-sample; the platform is the product.

## 4. Paste-ready prompt

> You are a **Claude Fable 5** session at **`/effort ultracode`** on the SuperBot repo. Read
> `docs/planning/trading-repo-founding-brief-2026-07-07.md` — it is your full brief and reading
> route; Q-0250 and Q-0251 in the question router are binding design inputs. Research deeply
> (real sources for data vendors/APIs), then produce the executable founding plan for the trading
> research repo (`docs/planning/trading-repo-founding-plan-<date>.md`): the point-in-time data
> stack ⚑, the git-timestamped decision ledger + verification job, the backtest engine
> (build-vs-adopt ⚑), the statistics layer with multiple-testing correction and the sniper-bucket
> small-N treatment, the promotion ladder as machine-checked gates, the 3-way hybrid allocator
> with pre-declared reserve triggers, the tracker website with DEGIRO export ingestion, and the
> repo's first build band (ledger + verifier + one reference strategy end-to-end).
> Decide-and-flag everything reversible; never wait for me; silence = consent.
