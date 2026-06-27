# S4 — Documentation system (the content) · live state

> **Status:** `living-ledger` — per-sector live snapshot (Q-0195).

> Per-sector snapshot (Q-0195). Hub: [`../current-state.md`](../current-state.md) ·
> Forward queue: [`../roadmap.md`](../roadmap.md) § S4.
>
> *The memory/folios/contracts/ledger the engine produces. Its trigger/checker **machinery** is
> S3; the docs it produces are S4.*

**Recently shipped (this sector):**
- **Twenty-seventh Q-0107 reconciliation pass** (band-#1500, issue #1501 —
  [pass record](../planning/reconciliation-pass-2026-06-27-band1500.md)): reconciled the ledger
  (band #1472–#1500 — five grouped entries, headlined by the owner-directed **BTD6 QA-accuracy arc**
  #1487…#1498 and the **self-improving-workflow guard lane** #1476/#1477/#1479/#1482/#1495), trimmed
  Recently-shipped to 20 (`trim_recently_shipped.py --apply`, floor recomputed), carried the band-#1470
  forward queue intact (no §4 queue slice executed this band → `mixed` archetype; still deep, no THIN
  flag), reset the marker #1470 → #1500.
- **Twenty-sixth Q-0107 reconciliation pass** (band-#1470, issue #1471 —
  [pass record](../planning/reconciliation-pass-2026-06-26-band1470.md)): reconciled the ledger
  (band #1442–#1470 — six grouped entries, headlined by the **NEW Project Moon (Limbus) knowledge
  domain** arc #1453…#1470), trimmed Recently-shipped to 20 (`trim_recently_shipped.py --apply`, floor
  recomputed), **fixed S3 drift** (the retired `needs-hermes-review` label, Q-0197), carried the
  band-#1440 forward queue (still deep, no THIN flag), reset the marker #1441 → #1470.
- **Twenty-fifth Q-0107 reconciliation pass** (band-#1440, issue #1442 —
  [pass record](../planning/reconciliation-pass-2026-06-24-band1440.md)): reconciled the ledger
  (band #1413–#1441 — six grouped entries, headlined by the **Essential Setup wizard restructure** arc),
  trimmed Recently-shipped to 20 (`trim_recently_shipped.py --apply`, floor recomputed), carried the
  band-#1410 forward queue (still deep, no THIN flag), reset the marker #1410 → #1441.
- **Twenty-fourth Q-0107 reconciliation pass** (band-#1410, issue #1411 —
  [pass record](../planning/reconciliation-pass-2026-06-24-band1410.md)): reconciled the ledger
  (band #1405–#1410 — three grouped entries: ticket subsystem #1405/#1410 · BTD6 floor coverage #1408 ·
  prev recon #1407), trimmed Recently-shipped to 20 (`trim_recently_shipped.py --apply`, floor
  #1320 … #535), affirmed the band-#1380 forward queue (still deep, no THIN flag), reset the marker
  #1404 → #1410.
- **Help-reachability CI guard (#1297)** — `check_docs`/the help tree now fails CI when a subsystem
  isn't homed, and a **tool-pin CI guard (#1320)** closes the three-places-pin-drift class at the root.
- **Ledger / docs in sync** — `check_current_state_ledger.py` and `check_docs.py` green.

**▶ Next:**
- **Next reconciliation pass due once merged PRs cross #1530** (every multiple of 30, Q-0134) —
  auto-triggered by `reconciliation-trigger.yml`; run by the docs-reconciliation routine, **not** a
  manual session (Q-0124).
- Plan-band depth is healthy — **no `PLAN-BACKLOG-THIN` flag** (buildable depth well over cadence).

**Cadence note:** a manually-started session does **not** run the reconciliation pass; pursue the
work it was started for. The recon marker + Recently-shipped ledger live in
[`../current-state.md`](../current-state.md).
