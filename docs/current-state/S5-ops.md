# S5 — Operations / control-plane · live state

> **Status:** `living-ledger` — per-sector live snapshot (Q-0195).

> Per-sector snapshot (Q-0195). Hub: [`../current-state.md`](../current-state.md) ·
> Forward queue: [`../roadmap.md`](../roadmap.md) § S5 · Runbooks:
> [autonomous-routines](../operations/autonomous-routines.md) ·
> [production-deployment](../operations/production-deployment.md).
>
> *The operational health that isn't a file — deploy · secrets · the autonomous loop. The executor
> outlier: most S5 work is **Hermes-VPS / maintainer**, not Claude-in-repo (only in-repo `check_*` /
> workflow guards are Claude's).*

**Recently shipped (this sector):**
- **CI dropped-`synchronize` watchdog** (PR #1288) — `ci-rerun-watchdog.yml` + `check_ci_coverage.py`
  re-kick `code-quality` when a `claude/*` PR head has no run (the silent-stall fix; complements the
  #1275 cancellation fix). [idea](../ideas/ci-dropped-synchronize-auto-retrigger-2026-06-22.md).
- **Q-0193 merge = deploy clarity** (#1247) — Railway auto-redeploys `worker` on every merge to
  `main`; never tell the owner to "restart/deploy" a merge. Canonical:
  [production-deployment](../operations/production-deployment.md).
- **Autonomous loop** self-fires (control-plane verified) — canonical state is the
  [Control-plane state table](../operations/autonomous-routines.md) (do not restate its verdict
  elsewhere).

**▶ Next (owner / Hermes-executed):**
*(offline-fit tags — `[offline]` self-mergeable now · `[needs-live-bot]` needs a running bot / runtime
creds · `[owner]` needs an owner decision/action; see [`../repo-sector-map.md`](../repo-sector-map.md)
§ "the offline-fit startability tag". S5 is the executor outlier — most items are owner/Hermes-run.)*
- **✅ CI-setup redesign DELIVERED (PR #1737, 2026-07-05)** — the target-state design + phased,
  reversible migration:
  [`../planning/ci-setup-redesign-2026-07-05.md`](../planning/ci-setup-redesign-2026-07-05.md) +
  the authoritative [`../operations/ci-what-runs-where.md`](../operations/ci-what-runs-where.md) map.
  Headline: **one required `ci-gate` context** (fan-in, `cancelled`=hard-fail) + a **CodeQL
  merge-protection ruleset** (closes the Q-0238 race) + **ruff replaces black/isort** + 17→14
  workflows + `check_ci_coverage` self-silencing fix + `check_workflow_concurrency.py` (shipped,
  advisory). Corrected the brief: repo is PUBLIC → minutes free (cost = latency/clutter/contention);
  all app-CI already path-filtered; no push+PR double-fire; merge-queue unavailable (personal account).
  **Executed so far:** the **CodeQL merge-protection ruleset is LIVE** (owner-enabled, closes the Q-0238
  race); `check_architecture`/`check_tool_pins`/`check_workflow_concurrency` are now **hard merge gates**
  (#1739); the dropped-`synchronize` watchdog is **de-self-silenced** (#1743). **▶ next = the turn-key
  backlog** in [`../planning/ci-followups-handoff-2026-07-05.md`](../planning/ci-followups-handoff-2026-07-05.md)
  (`[offline]` ruff consolidation · the `ci.yml`/`web-ci.yml` restructure · the CodeQL stuck-scan watchdog ·
  the two AST guards) + `[owner]` the Phase-B config tail (router Q-0239 G2–G8: the required-context swap,
  workflow deletions, settings.json rewires). Fresh-repo divergence answered (design §D: converge on the
  contract + `parity/`; diverge on the grammar-integrity stack; build at kernel K10).
- `[owner]` **Website two-site split rollout** — v1 is code-complete + reviewed; what remains is the
  owner-paced rollout (provision `botsite/` + submissions DB, domain cutover)
  ([handoff](../operations/website-split-next-steps-2026-06-19.md)).
- `[owner]` Two **security-review-gated** slices: control-panel migration · live status aggregator.

**Control-plane truth:** see [`../current-state.md`](../current-state.md) § Gates / blocked work —
that section is a pure pointer to the canonical control-plane table (copying its verdict drifted
twice).
