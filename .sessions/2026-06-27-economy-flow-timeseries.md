# 2026-06-27 — Games-economy observability: per-day faucet/sink trend view

> **Status:** `complete`

**Run type:** routine · dispatch

## What this run did

Empty-fire dispatch. The clean offline lanes were thin — every other concrete candidate was gated
for an autonomous run: BTD6 anchors are complete; procedures→skills **Batch 2 needs a `.claude/CLAUDE.md`
self-edit** (Q-0106 — proposals only in an autonomous run); botsite React **PR 2 flips the live
homepage** (owner-paced website rollout); **BUG-0009** newest-towers is **data-gated**; Project Moon
Slice A item 1 needs a **network datamine + runtime verification**, Slice B is a **runtime-verification-
needing BTD6 refactor**; fishing Phase 2 is **owner-design-gated**. The cleanest genuinely-useful
offline slice was the **§6 follow-up tail** of the shipped games-economy faucet/sink diagnostic
([plan](../planning/games-economy-faucet-sink-diagnostic-plan-2026-06-15.md), shipped #1044): the
all-time + windowed *aggregate* view + verdict shipped, but the per-day **trend** was explicitly
"capture, don't build here". Read-only, content-free, extends shipped work, serves the owner's stated
need (watch whether the mining economy is inflating *over time*).

**PR #1483 — games-economy per-day faucet/sink trend view.**

**Slice 1 (shipped) — the timeseries / trend view.**
1. `utils/db/economy.economy_flow_daily(guild_id, *, since)` — a pure
   `GROUP BY (occurred_at AT TIME ZONE 'UTC')::date` read over `economy_audit_log` returning per-day
   `(day, minted, drained, net, movements)`, oldest-first (deterministic UTC day boundary). The
   time-series sibling of the shipped `economy_flow_by_reason`; no migration (rides `occurred_at`).
2. `services/economy_flow_service.build_flow_timeseries` → `EconomyFlowTimeseries` (a `DayFlow` series +
   totals/ratio + the reused aggregate `verdict` classifier + a first-half-vs-second-half
   **rising/falling/steady** `_trend` read, noise-tolerant via `_TREND_EPS`). Pure aggregation, no
   Discord types.
3. `!platform economytrend [days]` (alias `coinflowtrend`) — a dependency-free unicode net-flow
   **sparkline** + a recent-days table + a summary line (minted/drained/net/ratio/verdict/trend).
   Read-only, content-free, admin-gated, beside `!platform economy`.

**Slice 2 — NOT built (deliberately).** The §6 health-finding (a persistent finding when a guild
sustains the `inflating ⚠` verdict) is genuinely **design-for-review**: the economy verdict is
**per-guild** but the `operational_health_findings` store + `record_findings(HealthSnapshot)` seam is
**guild-agnostic** (no `guild_id` column; fingerprint excludes unbounded identifiers). I sharpened it
into a turn-key design-for-review handoff in the plan §6 (the three decisions it needs: guild_id in the
fingerprint vs. a roll-up · the sustained rule · which loop emits it) rather than build it blind in an
autonomous run.

**Drift fixed on sight (Q-0166):** the roadmap §Games "Now" line listed **P0-1 wager money-safety** as
the next implementation session, but its plan is `historical` — EXECUTED in #748. Marked shipped (+ the
settle-once lineage #1444/#1445/#1454).

## Verification
- New tests: `tests/unit/db/test_economy_db_txn.py` (+2: `economy_flow_daily` all-time grouping &
  windowed filter, query-shape asserted), `tests/unit/services/test_economy_flow_service.py` (+6:
  timeseries assembly/totals/verdict, empty path, `_trend` rising/falling/steady/n-a + noise-tolerance,
  `build_flow_timeseries` since/label), `tests/unit/services/test_diagnostic_economy_trend_embed.py`
  (new, 6: sparkline empty/flat/min-max, day-rows newest-first+cap, embed render + no-activity path).
- `python3.10 scripts/check_quality.py --full` GREEN (12669 passed; the initial run flagged the
  expected derived-artifact drift — my new command bumped the live count 448→449, so I re-exported
  `botsite/data/site.json` + `site/data.js` via `scripts/export_dashboard_data.py`; data.js diff is
  exactly the new command entry, no sha churn).
- `python3.10 scripts/check_architecture.py --mode strict` — 0 errors (49 pre-existing warnings, none
  from this change; the new code is `utils/db` + `services` + `cogs`, layering-clean).

## 💡 Session idea (Q-0089)
*Give the per-day economy-flow read model a single shared "window → (since, label)" helper.* Right now
`build_flow_report` (aggregate) and `build_flow_timeseries` (trend) each contain the identical
`days → since/window_label` block (`datetime.now(utc) - timedelta(days=N)` + the `last N day(s)` label).
It's only ~6 lines duplicated, but the two are guaranteed to be asked for *together* (an operator who
looks at the aggregate verdict will want the trend), and a future windowing tweak (e.g. "this calendar
month") would have to land in both. A tiny private `_resolve_window(days) -> (since, label)` removes
the duplication and is the obvious extraction point if a third window-based reader appears. Low urgency
(the two don't conflict today), genuinely tied to this run's edit — captured, not built, to keep the
shipped slice focused.

## ⟲ Previous-session review (Q-0102)
The previous run (2026-06-27 offline-fit startability tags) did its best work by **closing the loop it
identified** — it didn't just tag the sector files, it wired the tags into `dispatch_menu --unattended`
so the *next* empty-fire run gets a concrete pick without re-deriving it. That paid off **this run**: I
ran `dispatch_menu --unattended` first and it surfaced the candidate sectors immediately. Its one miss:
the `Concrete [offline] items` it surfaces are **stale relative to what's actually buildable** — it
listed "S2: Anchor-tooling follow-ons" as offline, but S2's own file says that tail is "none cleanly
offline", and it didn't catch that S1's headline offline lanes are mostly shipped/gated. The tags are a
*presence* signal, not a *freshness* one. **System improvement this surfaces:** the dispatch tool reads
the tag but not the prose qualifier next to it ("none cleanly offline" / "shipped"); a cheap upgrade is
for `check_startability_tags.py` to also flag a `[offline]` item whose bullet contains a
shipped/exhausted marker ("✅", "SHIPPED", "none cleanly offline") as a **stale tag** — so an
`[offline]` tag can't outlive the work it points at. Routed as an observation here, not a rule edit.

## Doc audit (Q-0104)
Durable homes updated: the **plan §6** (follow-up #1 SHIPPED + #2 sharpened), the **games folio**
(`!platform economytrend` documented), and the **roadmap** drift fix. `check_docs --strict` +
`check_consistency` green (via `check_quality --check-only`). **Recently-shipped NOT edited** — #1483
isn't merged at write time and the ledger convention is merged-PRs-only; the lag is benign (the next
session / the #1500 reconciliation records it). `check_current_state_ledger --strict` lag is the same
benign newest-merge lag (recon is the docs-reconciliation routine's lane, Q-0124). Claim file deleted
at close.

## 📤 Run report
- **Did:** built the per-day games-economy faucet/sink **trend** view (db read fn + service timeseries
  read model + `!platform economytrend` with a sparkline) — the §6 follow-up tail of the shipped #1044
  diagnostic; fixed the roadmap P0-1 drift on sight; sharpened the §6 health-finding into a turn-key
  design-for-review handoff. · **Outcome:** shipped (auto-merges on green).
- **Shipped:** #1483 — `economy_flow_daily` + `build_flow_timeseries`/`EconomyFlowTimeseries` +
  `!platform economytrend [days]`; +14 tests; roadmap/plan/games-folio de-staled; artifacts re-exported.
- **Run type:** routine · dispatch
- **⚑ Owner decisions needed:** none (the §6 health-finding stays design-for-review — captured, not a
  blocking decision; agent rec when picked up: guild_id in the fingerprint + a sustained ≥N-of-M-days
  rule, emitted from the daily `HealthMaintenanceCog`).
- **⚑ Owner manual steps:** none.
- **⚑ Self-initiated:** yes — this lane was self-picked from the shipped plan's explicitly-captured §6
  follow-ups (no dispatch payload, no owner ask); it's a read-only observability extension of shipped
  work, flagged here per Q-0172.
- **↪ Next:** the BTD6 grounding-eval offline tail is complete and procedures→skills Batch 2 /
  botsite PR 2 / Project Moon Slice A·B remain gated for an autonomous run (CLAUDE.md-edit /
  production-web / network-datamine / runtime-verification respectively). The cleanest *next* offline
  pick is the **§6 economy-flow health-finding** once its three design questions (above) are decided, or
  promoting a fresh `docs/ideas/` entry → plan → build (Q-0172). Bug-book: BUG-0009 newest-towers
  data-gated, BUG-0011 needs a VPS repro, BUG-0019 #1 awaits an owner behavior decision — all stay OPEN.
