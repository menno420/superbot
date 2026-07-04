# 2026-06-30 — Diagnostics + Counters completion-deepening

> **Status:** `complete`
<!-- born-red flow (Q-0133): `in-progress` while open; flipped to `complete` as the final close step. -->

**PR:** [#1575](https://github.com/menno420/superbot/pull/1575) — diagnostics hub completeness + counters loop backoff.
**Branch:** `claude/funny-franklin-d1m4wk`
**Run type:** `routine · dispatch`

## What this run did

Empty-fire dispatch (no work order) → advanced the standing S1 completion-first ▶ Next (clear
assessed certs' offline punch-lists, Q-0209). No contained OPEN bug to jump the queue (BUG-0009
plan-level, BUG-0011 VPS-repro, BUG-0019 #1 owner-gated). Shipped two contained, offline,
self-merge-on-green slices in one PR.

### PR 1 — Diagnostics punch #1 (hub completeness)

The `!platform` hub's docstring + completion cert flagged `startup`/`findings` as typed-only by
design — an honest but incomplete gap. Closed it by **making the claim true** (the goal-serving
fix over a docstring edit): `startup` + `findings` (both read-only health reports) are now grouped
into the hub's **Runtime/status** category select with audience-preserving `_dispatch` branches
mirroring the typed commands (`startup` prefers the stored settled snapshot re-projected to the
caller's audience; `findings` shows the default `open` status, the typed `!platform findings
<status>` keeps the filter). The `finding` *lifecycle mutation* stays excluded from the read-only
Selects — the segregated Mutations row is the only write surface. Updated the panel docstring + the
lockstep hub-view test together (the test file itself mandated this) + 2 new dispatch tests.
Confirmed the smoke-checklist `!platform diagnostics` clause was already fixed (P2 sweep).

### PR 2 — Counters punch #3 (loop backoff)

The rename loop attempted every guild every tick with no backoff → a persistently-failing guild
(permission/cache fault, deleted bound channel) was re-attempted every 10 min forever (log spam +
wasted API calls + rate-limit re-hammering). Added `services.counter_service.GuildSyncBackoff` —
a pure, discord-free, tick-based exponential backoff (skip 1 → 2 → 4 … capped at 6 ticks) — wired
into `CountersCog._counter_sync_loop`. A repeatedly-failing guild is skipped for a growing number of
loop ticks but **never dropped forever** (the cap guarantees an ≥hourly retry at the 10-min cadence),
and one clean sync resets it. Per-process/ephemeral state (ADR-002 — a restart re-attempts every
guild once). The fail-safe per-guild try/except is preserved (now `logger.warning` with `exc_info`
+ the failure-streak/backoff context).

## Verification

- `python3.10 scripts/check_quality.py --full` → **13,289 passed**, 48 skipped, 2 xfailed.
- `python3.10 scripts/check_architecture.py --mode strict` → **0 errors** (49 pre-existing warnings).
- `check_current_state_ledger --strict` → benign newest-merge lag only (Q-0166 exception).
  `check_docs --strict` → all checks passed.
- +12 tests this PR (4 hub-view: 2 dispatch + the updated coverage/exclusion pair; 6 pure backoff +
  2 loop-wiring).

## Session enders

**💡 Session idea (Q-0089):** *"Audience-aware hub `_dispatch` lift — a `_dispatch_health(name, …)`
helper."* Three platform-hub surfaces now (`health`, `startup`, `findings`) re-resolve the caller's
health audience inside `_dispatch` with near-identical `resolve_audience` + project/gate boilerplate.
A tiny shared helper that resolves the audience once and hands it to the per-surface builders would
de-duplicate that and make the next health surface a one-liner. Small, genuine, not forced — logged
here, not yet an idea file (below the file-worthy bar).

**⟲ Previous-session review (Q-0102):** the previous run (#1572, AI review-log triage round 1) did
the *honest* thing well — it reverted/curated rather than shipping a confabulated DDT counter-list,
and flagged that the prod Postgres backlog isn't readable from the code env instead of pretending.
What it (and the broader completion arc) could improve: the completion certs' offline punch-lists
are scattered across 36 unit files, so "what's the next turn-key pick?" requires reading several
certs by hand. **System improvement surfaced:** a `scripts/check_completion_punchlist.py` (or a
`--punchlist` mode on the existing parity checker) that greps every `units/*.md` for un-`✅`'d
punch-list items tagged `(offline…)` and prints them ranked — turning the dispatch "next pick"
decision from a manual multi-file read into one command. (Logged as a candidate, not built this run.)

**📋 Doc audit (Q-0104):** cert files updated (diagnostic #1, counters #3); S1 ▶ Next sharpened;
ledger/docs checkers green. Nothing from this run is captured only in chat. #1575 is intentionally
**not** added to current-state Recently-shipped (merged-PRs-only; the next session reconciles).

## 📤 Run report

- **Did:** diagnostics hub-completeness (startup/findings grouped) + counters per-guild loop backoff · **Outcome:** shipped
- **Shipped:** #1575 — diagnostic cert punch #1 + counters cert punch #3 (2 offline completion-deepening slices)
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** none (dispatched standing ▶ Next — S1 completion-deepening, Q-0209)
- **↪ Next:** Diagnostics punch #2 (apply `_PaginatorView` to long findings/consistency output) + #5 (health-metrics reconcile) · Cleanup #4 (spam-window setting with a Settings widget)

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 (auto-merge on green) |
| CI-red rounds | 0 (born-red gate only; no real-failure rounds) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (Q-0089) |
