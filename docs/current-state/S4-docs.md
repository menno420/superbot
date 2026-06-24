# S4 — Documentation system (the content) · live state

> **Status:** `living-ledger` — per-sector live snapshot (Q-0195).

> Per-sector snapshot (Q-0195). Hub: [`../current-state.md`](../current-state.md) ·
> Forward queue: [`../roadmap.md`](../roadmap.md) § S4.
>
> *The memory/folios/contracts/ledger the engine produces. Its trigger/checker **machinery** is
> S3; the docs it produces are S4.*

**Recently shipped (this sector):**
- **Twenty-third Q-0107 reconciliation pass** (band-#1380, issue #1406 —
  [pass record](../planning/reconciliation-pass-2026-06-24-band1380.md)): reconciled the ledger
  (band #1351–#1404 as seven grouped entries), trimmed Recently-shipped to 20
  (`trim_recently_shipped.py --apply`, floor #1320 … #535), planned the next band, reset the marker
  #1352 → #1404.
- **Twenty-second Q-0107 reconciliation pass** (band-#1350, issue #1353 —
  [pass record](../planning/reconciliation-pass-2026-06-23-band1350.md)): reconciled the ledger
  (band #1322–#1352 as eight grouped entries), trimmed Recently-shipped to 20
  (`trim_recently_shipped.py --apply`), planned the next band, reset the marker #1320 → #1352.
- **Help-reachability CI guard (#1297)** — `check_docs`/the help tree now fails CI when a subsystem
  isn't homed, and a **tool-pin CI guard (#1320)** closes the three-places-pin-drift class at the root.
- **Ledger / docs in sync** — `check_current_state_ledger.py` and `check_docs.py` green.

**▶ Next:**
- **Next reconciliation pass due once merged PRs cross #1410** (every multiple of 30, Q-0134) —
  auto-triggered by `reconciliation-trigger.yml`; run by the docs-reconciliation routine, **not** a
  manual session (Q-0124).
- Plan-band depth is healthy — **no `PLAN-BACKLOG-THIN` flag** (buildable depth well over cadence).

**Cadence note:** a manually-started session does **not** run the reconciliation pass; pursue the
work it was started for. The recon marker + Recently-shipped ledger live in
[`../current-state.md`](../current-state.md).
