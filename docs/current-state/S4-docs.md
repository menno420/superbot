# S4 — Documentation system (the content) · live state

> **Status:** `living-ledger` — per-sector live snapshot (Q-0195).

> Per-sector snapshot (Q-0195). Hub: [`../current-state.md`](../current-state.md) ·
> Forward queue: [`../roadmap.md`](../roadmap.md) § S4.
>
> *The memory/folios/contracts/ledger the engine produces. Its trigger/checker **machinery** is
> S3; the docs it produces are S4.*

**Recently shipped (this sector):**
- **Thirty-first Q-0107 reconciliation pass** (band-#1620, issue #1622 —
  [pass record](../planning/reconciliation-pass-2026-07-01-band1620.md)): reconciled the ledger
  (band #1591–#1620 — seven grouped entries, headlined by the **S1 completion-deepening lane** —
  fishing coral structures #1596…#1605, reaction-roles slim builder #1608…#1615, XP import #1607/#1610,
  server-logging depth #1594/#1618/#1619 — plus the **bot-owner permission-gate bypass** #1602 and a
  **boot smoke-test CI guard** #1601), trimmed Recently-shipped to 20
  (`trim_recently_shipped.py --apply`, floor recomputed), disposed 8 open PRs (none a stale session PR:
  #1621 in flight, #1509 left for owner per the prior pass, six dependabot bumps), confirmed
  **ROUTINE_PAT set / loop self-fires** (issue #1622 authored by `menno420`), carried the forward queue
  intact (still deep, no THIN flag), refreshed the dashboard export (Q-0167), reset the marker
  #1590 → #1620.
- **Thirtieth Q-0107 reconciliation pass** (band-#1590, issue #1591 —
  [pass record](../planning/reconciliation-pass-2026-06-30-band1590.md)): reconciled the ledger
  (band #1561–#1590 — seven grouped entries, headlined by the **bot-owner platform-admin override**
  #1573/#1577/#1582, the **S1 certification deepening** #1565/#1566/#1568/#1575/#1588, and the
  **owner fresh-rebuild vision capture** #1589/#1590), trimmed Recently-shipped to 20
  (`trim_recently_shipped.py --apply`, floor recomputed), reflected the **owner re-elevation of the
  AI-memory substrate-kit** to top focus (S3), confirmed **ROUTINE_PAT set / loop self-fires** (issue
  #1591 authored by `menno420`), carried the forward queue intact (still deep, no THIN flag), reset
  the marker #1560 → #1590.
- **Twenty-ninth Q-0107 reconciliation pass** (band-#1560, issue #1563 —
  [pass record](../planning/reconciliation-pass-2026-06-29-band1560.md)): reconciled the ledger
  (band #1531–#1560), trimmed Recently-shipped to 20, carried the forward queue intact, reset the
  marker #1530 → #1560.
- **Twenty-eighth Q-0107 reconciliation pass** (band-#1530, issue #1531 —
  [pass record](../planning/reconciliation-pass-2026-06-28-band1530.md)): reconciled the ledger
  (band #1502–#1530 — six grouped entries, headlined by the **fishing acquisition-depth + gear arc**
  #1504…#1521 and the **S1 feature-completion certification framework** #1513/#1519/#1523/#1530), trimmed
  Recently-shipped to 20 (`trim_recently_shipped.py --apply`, floor recomputed), carried the band-#1500
  forward queue intact (no §4 queue slice executed this band → `mixed` archetype; still deep, no THIN
  flag), reset the marker #1500 → #1530.
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
- **Help-reachability CI guard (#1297)** — `check_docs`/the help tree now fails CI when a subsystem
  isn't homed, and a **tool-pin CI guard (#1320)** closes the three-places-pin-drift class at the root.
- **Ledger / docs in sync** — `check_current_state_ledger.py` and `check_docs.py` green.

**▶ Next:**
- **Next reconciliation pass due once merged PRs cross #1620** (every multiple of 30, Q-0134) —
  auto-triggered by `reconciliation-trigger.yml`; run by the docs-reconciliation routine, **not** a
  manual session (Q-0124).
- Plan-band depth is healthy — **no `PLAN-BACKLOG-THIN` flag** (buildable depth well over cadence).
- **Owner steer (2026-06-30):** the fresh-rebuild vision re-elevates the **AI-memory substrate-kit**
  to top focus — S3's forward queue leads with PR 2 remainder + PR 3; the full rebuild stays
  idea-stage (gated on Fable 5 + owner keep/change spec).

**Cadence note:** a manually-started session does **not** run the reconciliation pass; pursue the
work it was started for. The recon marker + Recently-shipped ledger live in
[`../current-state.md`](../current-state.md).
