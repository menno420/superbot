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
- **Website two-site split rollout** — v1 is code-complete + reviewed; what remains is the
  owner-paced rollout (provision `botsite/` + submissions DB, domain cutover)
  ([handoff](../operations/website-split-next-steps-2026-06-19.md)).
- Two **security-review-gated** slices: control-panel migration · live status aggregator.

**Control-plane truth:** see [`../current-state.md`](../current-state.md) § Gates / blocked work —
that section is a pure pointer to the canonical control-plane table (copying its verdict drifted
twice).
