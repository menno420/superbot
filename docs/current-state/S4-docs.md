# S4 — Documentation system (the content) · live state

> **Status:** `living-ledger` — per-sector live snapshot (Q-0195).

> Per-sector snapshot (Q-0195). Hub: [`../current-state.md`](../current-state.md) ·
> Forward queue: [`../roadmap.md`](../roadmap.md) § S4.
>
> *The memory/folios/contracts/ledger the engine produces. Its trigger/checker **machinery** is
> S3; the docs it produces are S4.*

**Recently shipped (this sector):**
- **Nineteenth Q-0107 reconciliation pass** (band-#1260, issue #1264 —
  [pass record](../planning/reconciliation-pass-2026-06-21-band1260.md)): reconciled the ledger,
  trimmed Recently-shipped to 20, planned the next band.
- **Ledger / docs in sync** — `check_current_state_ledger.py` and `check_docs.py` green.

**▶ Next:**
- **Next reconciliation pass due once merged PRs cross #1290** (every multiple of 30, Q-0134) —
  auto-triggered by `reconciliation-trigger.yml`; run by the docs-reconciliation routine, **not** a
  manual session (Q-0124).
- Plan-band depth is healthy — **no `PLAN-BACKLOG-THIN` flag** (buildable depth well over cadence).

**Cadence note:** a manually-started session does **not** run the reconciliation pass; pursue the
work it was started for. The recon marker + Recently-shipped ledger live in
[`../current-state.md`](../current-state.md).
