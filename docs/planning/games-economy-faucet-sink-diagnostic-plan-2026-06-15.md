# Plan — games-economy faucet/sink diagnostic (observe the loop's balance)

> **Status:** `historical` — **▶ SHIPPED in #1044** (verified present + wired + tested 2026-06-19:
> `economy_flow_by_reason` in `utils/db/economy.py` · the `economy_flow_service` read model
> (`build_flow_report` / `EconomyFlowReport`) · the `!platform economy` subcommand in
> `cogs/diagnostic/platform_group.py` · `tests/unit/services/test_economy_flow_service.py`). The §6
> follow-ups (windowed/timeseries view, inflation health-finding) remain captured, not part of this slice.
> Original plan retained below for provenance. Promoted from the
> [idea capture](../ideas/games-economy-faucet-sink-diagnostic-2026-06-14.md) (now `historical`)
> by the band-#930 reconciliation pass (2026-06-15). Routing: **S1 Bot / games + observability**.
> Approved-to-build basis: the idea's gate ("promote once a sink-heavy slice lands") is **cleared**
> — respec (#912) and the structures sinks (#905 Forge / #910 Home) now emit real sink reasons. The
> slice is read-only, content-free, no per-exposure AI lift (Q-0048 read-only-deterministic posture).
> One executable PR.

---

## 1. What this ships (one sentence)

A read-only operator read model that sums the **economy audit ledger** already written on every
coin movement into a per-guild **faucet vs. sink** view (coins minted, coins drained, net flow,
and the per-reason breakdown over a time window), surfaced through the existing `!platform`
diagnostics admin surface — so the owner can watch whether the mining economy is inflating instead
of guessing from static balance sims.

## 2. Why it's buildable cold (the data already exists)

Every coin movement is already audited. `utils/db/economy.py::insert_economy_audit` appends one row
to **`economy_audit_log` `(guild_id, user_id, actor_id, delta, new_balance, reason)`** on every
`economy_service.credit`/`debit`/`transfer`. The mining loop already emits a clean reason taxonomy
(verified in source 2026-06-15):

- **Faucet (mint, `delta > 0`):** `mining:sell_ore` (the only first-class faucet today; game/daily
  rewards add others).
- **Sinks (drain, `delta < 0`):** `mining:buy_gear`, `mining:repair_gear`, `mining:skill_respec`,
  `mining:skill_respec_branch`, `mining:forge_build`, `mining:home_build`, `mining:vault_upgrade`.

This slice **adds no new writes and no new reasons** — it only *reads and aggregates* what the
audited service seam already records. Classification is by the **sign of the summed delta per
reason**, not a hardcoded faucet/sink list, so a future reason is classified automatically and the
view never goes stale (the same self-cleaning principle as the eval drift guard #879).

## 3. House-style placement (the one boundary to get right)

**Do NOT register this in `services/diagnostics_service.py`.** That module's own docstring fences it
to the **sync, I/O-free, process-local** provider registry and explicitly says a DB read model
"lives with the domain owner and is invoked from the admin command directly" (the
`setup_diagnostics` / `resource_health` precedent). A coin-flow query is async DB I/O, so it follows
that pattern, not the sync registry. Layering (per `docs/architecture.md`):

| Layer | File | Responsibility |
|---|---|---|
| `utils/db/` | `utils/db/economy.py` (extend) | one new **pure read** function `economy_flow_by_reason(guild_id, *, since)` — a single `SELECT reason, SUM(delta) ... GROUP BY reason` over `economy_audit_log`. No writes. The only layer that touches `pool`/SQL (the hard DB-access rule). |
| `services/` | `services/economy_flow_service.py` (new) | the read model: call the db fn, split rows into faucet (`net > 0`) / sink (`net < 0`), compute totals + the faucet:sink ratio + net, return a typed `EconomyFlowReport` (dataclass / NamedTuple). Pure aggregation, no Discord types, no views import. |
| `cogs/` | the existing `!platform` admin cog (where `media` / `event_bus` / `health` already live) | add a `!platform economy [days]` subcommand (owner-tier) that awaits the service and renders the report as an embed/table. |

No new hub, no new top-level command name (mirrors `media` / `event_bus` — a `!platform`
subcommand). Content-free: **counts and coin totals only, no user IDs, no per-user rows** (the
read model aggregates away `user_id`).

## 4. Concrete build steps (turn-key)

1. **DB read fn** — `utils/db/economy.py`:
   ```python
   async def economy_flow_by_reason(
       guild_id: int, *, since: datetime | None = None,
       conn: asyncpg.Connection | None = None,
   ) -> list[tuple[str, int, int]]:
       """Per-reason (reason, net_delta, movement_count) over economy_audit_log.

       Pure read. `since` filters by the audit row timestamp (omit = all-time).
       """
   ```
   `SELECT reason, SUM(delta) AS net, COUNT(*) AS n FROM economy_audit_log WHERE guild_id=$1 [AND created_at >= $2] GROUP BY reason ORDER BY net DESC`.
   *(Check the live `economy_audit_log` schema first for the timestamp column name — `context_map.py`
   on `economy.py` + a quick `\d economy_audit_log`; if there is no timestamp column, ship the
   all-time view and note the windowed view as a one-line follow-up rather than adding a migration in
   this read-only slice.)*

2. **Service read model** — `services/economy_flow_service.py`:
   - `EconomyFlowReport` (NamedTuple): `faucets: list[ReasonFlow]`, `sinks: list[ReasonFlow]`,
     `total_minted: int`, `total_drained: int`, `net: int`, `ratio: float | None` (minted/drained;
     `None` when no sinks), `window_label: str`.
   - `async def build_flow_report(guild_id, *, days: int | None) -> EconomyFlowReport` — calls the
     db fn, classifies each row by `net > 0` (faucet) / `net < 0` (sink), sums, computes the ratio.
   - No `views/` import (services→views is the zero-tolerance rule); no Discord types.

3. **Admin surface** — add `!platform economy [days]` to the cog that owns `!platform media` /
   `!platform event_bus`:
   - owner/staff capability check at callback time (re-check authority, per the views rule — even
     though this is a cog command, follow the same posture used by the sibling `!platform`
     subcommands).
   - render: a header line (window · minted · drained · **net** · faucet:sink ratio with an
     "inflating ⚠ / draining / balanced" verdict), then the per-reason faucet table and sink table.

4. **Tests** (`tests/unit/`):
   - `tests/unit/services/test_economy_flow_service.py` — feed the service a stubbed db-fn result
     and assert the faucet/sink split, totals, net, ratio, and the empty-ledger and sinks-only-zero
     edge cases (ratio `None`, no divide-by-zero).
   - extend the economy db tests with a `economy_flow_by_reason` round-trip (insert a few audit
     rows across reasons, assert the grouped sums) if the suite has a Postgres-backed economy test;
     otherwise unit-test the service against a fake.

5. **Run the gates:** `python3.10 scripts/context_map.py disbot/services/economy_flow_service.py`
   (blast radius) · `python3.10 scripts/check_architecture.py --mode strict` (0 new violations —
   the new service imports only `utils.db` + stdlib) · `python3.10 scripts/check_quality.py --full`.

## 5. Scope fence (what this slice is NOT)

- **Not** a new write, migration, or reason — read-only over existing audit rows (so it is a
  direct, reversible, single-domain change — the FIX/observability lane, not a feature build; the
  phase gate doesn't apply to a read-only diagnostic).
- **Not** a static balance sim — those *predict* balance offline (the `gear-set-numbers` record, the
  Q-0087 survival harness); this *observes* it live. Complementary, not a replacement.
- **Not** per-user analytics — aggregated, content-free (counts + coin totals only).
- **Not** a new hub or command name — a `!platform` subcommand beside `media`/`event_bus`.

## 6. Follow-ups (capture, don't build here)

- **✅ A windowed/timeseries view (coin flow per day) — SHIPPED (2026-06-27 dispatch run).** The
  audit table carries `occurred_at`, so this landed as the per-day **trend** sibling of the aggregate
  view: `utils.db.economy.economy_flow_daily` (a pure `GROUP BY (occurred_at AT TIME ZONE 'UTC')::date`
  read), the `economy_flow_service.build_flow_timeseries` → `EconomyFlowTimeseries` read model (per-day
  `DayFlow` series + totals + a first-half-vs-second-half **rising/falling/steady** trend read), and
  `!platform economytrend [days]` (a net-flow unicode sparkline + a recent-days table + the verdict).
  Read-only, content-free, no migration, no new reason.
- **A health-finding when the faucet:sink ratio sustains an inflation verdict (ties into the P1-2
  health-findings lifecycle, #843) — STILL design-for-review.** The deliberate open design question
  (why it wasn't built with the timeseries): the economy verdict is **per-guild**, but the
  `operational_health_findings` store + `record_findings(HealthSnapshot)` seam is **guild-agnostic**
  (the fingerprint excludes unbounded identifiers; the store has no `guild_id` column). A turn-key
  next slice must decide: (a) carry the `guild_id` in the finding's fingerprint + message (so each
  guild gets a distinct, dedupable finding) vs. a process-wide "some guild is inflating" roll-up; (b)
  the **sustained** rule (don't fire on one noisy day — e.g. verdict `inflating ⚠` on ≥ N of the last
  M days, computed off `build_flow_timeseries`); (c) which loop emits it (the daily
  `HealthMaintenanceCog` is the precedent, but it would need to iterate guilds). Once decided it is a
  small producer + a wiring into the daily loop; the read model already computes the verdict + trend.
- Extend faucet coverage when game/daily reward reasons are folded in (the classifier already
  handles them by sign; this is just documentation of the taxonomy).
