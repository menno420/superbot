# S4 — Documentation system (the content) · live state

> **Status:** `living-ledger` — per-sector live snapshot (Q-0195).

> Per-sector snapshot (Q-0195). Hub: [`../current-state.md`](../current-state.md) ·
> Forward queue: [`../roadmap.md`](../roadmap.md) § S4.
>
> *The memory/folios/contracts/ledger the engine produces. Its trigger/checker **machinery** is
> S3; the docs it produces are S4.*

**Recently shipped (this sector):**
- **Fifty-sixth Q-0107 reconciliation pass** (band-#2393, issues #2394 + #2371 —
  record in [`.sessions/2026-08-10-reconcile.md`](../../.sessions/2026-08-10-reconcile.md)): reconciled
  the ledger (band #2342–#2393 — **entirely docs/CI/tooling + generated artifact + botsite deps, zero
  `disbot/` runtime**, matching oracle-freeze: the **55th-pass reconcile PR** #2344, one **Dependabot bump**
  #2339 (fastapi/botsite), one **botsite dep PR** #2345 (uvicorn remainder), and **47 dashboard refreshes**
  #2346…#2370/#2372…#2393), trimmed Recently-shipped to 20, **disposed the open-PR set** — **zero open PRs**:
  the long-standing Dependabot dep-bump backlog is now **fully drained** (#2340 + #2343 closed **unmerged**
  as superseded by #2345/#2339; the rest merged), no external drive-by and no stale session PR to dispose
  this band, confirmed **ROUTINE_PAT set / loop self-fires** (issues #2394 + #2371 authored by `menno420`),
  **⚠️ carried PLAN BACKLOG THIN** (the in-repo product backlog is intentionally frozen — no 30-PR feature
  band to plan; forward queue is `NEXT-TASKS.md`: superbot-next rebuild cutover + docs curation + owner-gated
  calls), refreshed the dashboard export (Q-0167), reset the marker #2341 → #2393. Supersede-banner soft
  warnings unchanged at 9 (honest cross-repo phantom successors in fleet-manager the in-repo checker can't
  resolve).
- **Fifty-fifth Q-0107 reconciliation pass** (band-#2340, issue #2342 —
  record in [`.sessions/2026-08-05-reconcile.md`](../../.sessions/2026-08-05-reconcile.md)): reconciled
  the ledger (band #2311–#2341 — **entirely docs/CI/tooling + generated artifact, zero `disbot/` runtime**,
  matching oracle-freeze: the **54th-pass reconcile PR** #2312 + its **Codex follow-up** #2313, four
  **deps/CI PRs** #2334/#2335/#2337/#2338, and **19 dashboard refreshes** #2314/#2315/#2318…#2333/#2341),
  trimmed Recently-shipped to 20, **disposed the open-PR set** — **3 open Dependabot dep-bump PRs**
  (#2339/#2340/#2343 — the runtime dep lane, Q-0256, left in flight; not this docs-only pass), no external
  drive-by and no stale session PR to dispose this band, confirmed **ROUTINE_PAT set / loop self-fires**
  (issue #2342 authored by `menno420`), **⚠️ carried PLAN BACKLOG THIN** (the in-repo product backlog is
  intentionally frozen — no 30-PR feature band to plan; forward queue is `NEXT-TASKS.md`: superbot-next
  rebuild cutover + docs curation + owner-gated calls), refreshed the dashboard export (Q-0167), reset the
  marker #2310 → #2341. Supersede-banner soft warnings unchanged at 9 (honest cross-repo phantom
  successors in fleet-manager the in-repo checker can't resolve).
- **Fifty-fourth Q-0107 reconciliation pass** (band-#2310, issue #2311 —
  record in [`.sessions/2026-08-03-reconcile.md`](../../.sessions/2026-08-03-reconcile.md)): reconciled
  the ledger (band #2281–#2310, 29 PRs — **entirely docs + generated artifact, zero `disbot/` runtime**,
  matching oracle-freeze: the **53rd-pass reconcile PR** #2282 and **28 dashboard refreshes**
  #2283…#2310), trimmed Recently-shipped to 20, **disposed the open-PR set** — **9 open Dependabot
  dep-bump PRs** (#2171/#2172/#2173/#2175/#2176/#2178/#2185/#2247/#2248 — the runtime dep lane, Q-0256,
  left in flight; not this docs-only pass), no external drive-by and no stale session PR to dispose this
  band, confirmed **ROUTINE_PAT set / loop self-fires** (issue #2311 authored by `menno420`), **⚠️ carried
  PLAN BACKLOG THIN** (the in-repo product backlog is intentionally frozen — no 30-PR feature band to
  plan; forward queue is `NEXT-TASKS.md`: superbot-next rebuild cutover + docs curation + owner-gated
  calls), refreshed the dashboard export (Q-0167), reset the marker #2280 → #2310. Supersede-banner soft
  warnings unchanged at 9 (honest cross-repo phantom successors in fleet-manager the in-repo checker
  can't resolve).
- **Fifty-third Q-0107 reconciliation pass** (band-#2280, issue #2281 —
  record in [`.sessions/2026-07-31-reconcile.md`](../../.sessions/2026-07-31-reconcile.md)): reconciled
  the ledger (band #2251–#2280, 29 PRs — **entirely docs + generated artifact, zero `disbot/` runtime**,
  matching oracle-freeze: the **52nd-pass reconcile PR** #2252 and **28 dashboard refreshes**
  #2253…#2280), trimmed Recently-shipped to 20, **disposed the open-PR set** — **9 open Dependabot
  dep-bump PRs** (#2171/#2172/#2173/#2175/#2176/#2178/#2185/#2247/#2248 — the runtime dep lane, Q-0256,
  left in flight; not this docs-only pass), no external drive-by and no stale session PR to dispose this
  band, confirmed **ROUTINE_PAT set / loop self-fires** (issue #2281 authored by `menno420`), **⚠️ carried
  PLAN BACKLOG THIN** (the in-repo product backlog is intentionally frozen — no 30-PR feature band to
  plan; forward queue is `NEXT-TASKS.md`: superbot-next rebuild cutover + docs curation + owner-gated
  calls), refreshed the dashboard export (Q-0167), reset the marker #2250 → #2280. Supersede-banner soft
  warnings unchanged at 9 (honest cross-repo phantom successors in fleet-manager the in-repo checker
  can't resolve).
- **Fifty-second Q-0107 reconciliation pass** (band-#2250, issue #2251 —
  record in [`.sessions/2026-07-27-reconcile.md`](../../.sessions/2026-07-27-reconcile.md)): reconciled
  the ledger (band #2221–#2250, 27 PRs — **entirely docs + generated artifact, zero `disbot/` runtime**,
  matching oracle-freeze: the **51st-pass reconcile PR** #2222 + its **Codex follow-up** #2223 and
  **25 dashboard refreshes** #2224…#2246/#2249/#2250), trimmed Recently-shipped to 20, **disposed the
  open-PR set** — **9 open Dependabot dep-bump PRs** (#2171/#2172/#2173/#2175/#2176/#2178/#2185 + the
  two new #2247/#2248 — the runtime dep lane, Q-0256, left in flight; not this docs-only pass), no
  external drive-by and no stale session PR to dispose this band, confirmed **ROUTINE_PAT set / loop
  self-fires** (issue #2251 authored by `menno420`), **⚠️ carried PLAN BACKLOG THIN** (the in-repo
  product backlog is intentionally frozen — no 30-PR feature band to plan; forward queue is
  `NEXT-TASKS.md`: superbot-next rebuild cutover + docs curation + owner-gated calls), refreshed the
  dashboard export (Q-0167), reset the marker #2220 → #2250. Supersede-banner soft warnings unchanged
  at 9 (honest cross-repo phantom successors in fleet-manager the in-repo checker can't resolve).
- **Fifty-first Q-0107 reconciliation pass** (band-#2220, issue #2221 —
  record in [`.sessions/2026-07-25-reconcile.md`](../../.sessions/2026-07-25-reconcile.md)): reconciled
  the ledger (band #2191–#2220, 28 PRs — **entirely docs + generated artifact, zero `disbot/` runtime**,
  matching oracle-freeze: the **50th-pass reconcile PR** #2192 and **27 dashboard refreshes**
  #2193…#2216/#2218/#2219/#2220), trimmed Recently-shipped to 20, **disposed the open-PR set** —
  **8 open Dependabot dep-bump PRs** (#2171/#2172/#2173/#2175/#2176/#2178/#2184/#2185 — the runtime dep
  lane, Q-0256, left in flight; not this docs-only pass) and **closed #2217** (an external drive-by
  adding a redundant generic `python-app.yml` CI workflow duplicating the pinned `code-quality.yml`),
  no stale session PR, confirmed **ROUTINE_PAT set / loop self-fires** (issue #2221 authored by
  `menno420`), **⚠️ carried PLAN BACKLOG THIN** (the in-repo product backlog is intentionally frozen —
  no 30-PR feature band to plan; forward queue is `NEXT-TASKS.md`: superbot-next rebuild cutover
  + docs curation + owner-gated calls), refreshed the dashboard export (Q-0167), reset the marker
  #2190 → #2220. Supersede-banner soft warnings unchanged at 9 (honest cross-repo phantom successors in
  fleet-manager the in-repo checker can't resolve).
- **Fiftieth … twenty-fifth Q-0107 passes (band-#2190 … band-#1440)** — collapsed to keep this sector list lean; the newest six passes are above, and every older pass is preserved in full in its own `planning/reconciliation-pass-*.md` record + `.sessions/*-reconcile.md` log (and the hub [`../current-state-archive.md`](../current-state-archive.md) Recently-shipped archive). Each was a docs-only ledger reconcile (marker bump + Recently-shipped trim to 20 + open-PR disposition + control-plane ROUTINE_PAT confirm); the band-#2160-and-later passes carried **PLAN BACKLOG THIN** under the oracle-freeze.
- **Help-reachability CI guard (#1297)** — `check_docs`/the help tree now fails CI when a subsystem
  isn't homed, and a **tool-pin CI guard (#1320)** closes the three-places-pin-drift class at the root.
- **Ledger / docs in sync** — `check_current_state_ledger.py` and `check_docs.py` green.

**▶ Next:**
- **▶ Rebuild — (historical) the review-then-plan phase (owner-directed 2026-07-03; capstone #1674 merged):** the
  new-bot capability audit is complete — verdict **GO-with-amendments** (measured all-43 fit 85.1%),
  and [`NEW-BOT-BUILD-PLAN.md`](../analysis/rebuild-discovery/new-bot-capability-audit/findings/NEW-BOT-BUILD-PLAN.md)
  is the **frozen reference**. *(Superseded 2026-07-07 by Q-0241/#1776 — see the LIVE tail below;
  kept for the record:)* Next: (A) one more owner-led **content review pass** over the whole
  surface (commands / functions / methods), then (B) **one 100%-complete design plan per step**
  before any code. Process + gates + start sequence now canonical in
  [`planning/rebuild-canonical-plan-2026-07-06.md`](../planning/rebuild-canonical-plan-2026-07-06.md)
  (PR #1770). The gates were retired by Q-0241/#1776 (2026-07-07); the rebuild is LIVE in
  menno420/superbot-next (50/51 parity rows ported per parity/parity.yml@33d3073 — only
  _unmapped pending; deep-game goldens owner-gated on D-0043).
- **▶ SuperBot retention application — startable (owner-directed brainstorm, PR #1643; Q-0214):** the
  **kit-native** context-economy engine already shipped in **#1649** (`src/engine/economy/` — now in the graduated
  [menno420/substrate-kit](https://github.com/menno420/substrate-kit) repo; the in-tree copy was removed in #1882, pin = `substrate.config.json`);
  what remains here is applying retention to SuperBot's *own* docs via a `check_retention.py`
  checker/actuator (which consumes that engine) —
  [`planning/memory-retention-and-context-economy-plan-2026-07-02.md`](../planning/memory-retention-and-context-economy-plan-2026-07-02.md)
  — per-class delete/archive windows + hard caps, sim-derived numbers
  (`tools/sim/retention_policy_sim.py`). 3 PRs; PR 1 (checker, no real deletions) is the
  startable slice. Companion: the still-unexecuted
  [orientation-cost-reduction plan](../planning/orientation-cost-reduction-plan-2026-06-30.md)
  (Q-0210 router archive now 3+ passes overdue — B0–B3 should run soon regardless).
- **Next reconciliation pass due once merged PRs cross #2400** (every multiple of 30, Q-0134) —
  auto-triggered by `reconciliation-trigger.yml`; run by the docs-reconciliation routine, **not** a
  manual session (Q-0124).
- **⚠️ `PLAN BACKLOG THIN` (raised band-#2160, 2026-07-19)** — the in-repo product backlog is
  **intentionally frozen** (superbot is the behavioral oracle for the `superbot-next` rebuild), so there
  is no 30-PR in-repo feature band to plan. This is the Q-0164 *signal*, not a failure: the honest
  forward queue is [`NEXT-TASKS.md`](../NEXT-TASKS.md) — superbot-next rebuild cutover + backlog
  curation + the autonomy-apparatus wind-down + owner-gated product/deploy calls. The flag clears if
  the owner re-opens in-repo product work (NEXT-TASKS item 6).
- **(Historical owner steer, 2026-06-30 — superseded):** the fresh-rebuild vision re-elevates the **AI-memory substrate-kit**
  to top focus — S3's forward queue leads with PR 2 remainder + PR 3; the full rebuild stays
  idea-stage (gated on Fable 5 + owner keep/change spec) — the rebuild has since shipped its
  design spec, canonical plan, and the live superbot-next repo (50/51 parity rows ported).

**Cadence note:** a manually-started session does **not** run the reconciliation pass; pursue the
work it was started for. The recon marker + Recently-shipped ledger live in
[`../current-state.md`](../current-state.md).
