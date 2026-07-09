# S4 — Documentation system (the content) · live state

> **Status:** `living-ledger` — per-sector live snapshot (Q-0195).

> Per-sector snapshot (Q-0195). Hub: [`../current-state.md`](../current-state.md) ·
> Forward queue: [`../roadmap.md`](../roadmap.md) § S4.
>
> *The memory/folios/contracts/ledger the engine produces. Its trigger/checker **machinery** is
> S3; the docs it produces are S4.*

**Recently shipped (this sector):**
- **Fortieth Q-0107 reconciliation pass** (band-#1890, issue #1891 —
  [pass record](../planning/reconciliation-pass-2026-07-09-band1890.md)): reconciled the ledger
  (band #1863–#1890 — seven grouped entries, **entirely docs/tooling**, zero `disbot/` runtime:
  the **EAP Anthropic-feedback email assembled + sent** #1864/#1866/#1867/#1868; the **EAP Project
  fleet founding → independent cross-repo review** #1873…#1877/#1887/#1889/#1890 (the fleet grew to
  four repos — `superbot`, `superbot-next`, `substrate-kit`, `websites` — plus the manager-Project
  brief; headline finding: the substrate-kit's **render/engage half strands in every fresh adoption**,
  an upstream-kit fix); the **substrate-kit graduation to its own repo**
  #1878/#1879/#1881/#1882/#1883/#1884 (v1.0.0 pinned via `substrate.config.json`; the in-tree copy
  removed — 101 files; provenance riders + exporter telemetry + `console.json` contract as kit-lab
  companions); the **Dependabot PR policy Q-0256** #1886 (+ the #1761–#1766 backlog merge); the
  39th-pass docs PR #1863; and 8 dashboard refreshes), trimmed Recently-shipped to 20
  (`trim_recently_shipped.py --apply`, moved the 7 oldest bullets, floor recomputed), disposed
  **0 open PRs** (**zero open at pass start** — the dependabot backlog cleared under Q-0256; no
  stale session PR), confirmed **ROUTINE_PAT set / loop self-fires** (issue #1891 authored by
  `menno420`), carried the forward queue intact (still deep, no THIN flag — the rebuild Phase-B
  canonical plan + the live SuperBot Project program/fleet dominate), refreshed the dashboard export
  (Q-0167), reset the marker #1861 → #1890.
- **Thirty-eighth Q-0107 reconciliation pass** (band-#1830, issue #1832 —
  [pass record](../planning/reconciliation-pass-2026-07-08-band1830.md)): reconciled the ledger
  (band #1801–#1830 — five grouped entries, headlined by the **entirely docs-only SuperBot Project
  coordinator arc**: the Projects-EAP coordinator going live → kickoff/calibration rewrite #1811…#1823,
  the evaluation guidebook #1820, and the EAP findings for the owner's Friday Anthropic feedback
  #1821…#1830 (headline: the auto-mode first-publish push wall is likely **un-self-clearable in cloud
  Projects** — 11-test probe #1830) — plus the **Q-0254 understand-and-reflect kit-doctrine graduation**
  #1806/#1809, the **website-design + kit-lab program briefs** #1802/#1804, the 37th-pass docs PRs
  #1801/#1803, and 3 dashboard refreshes), trimmed Recently-shipped to 20
  (`trim_recently_shipped.py --apply`, floor recomputed), disposed the open-PR set (6 dependabot bumps
  #1761–#1766 left in flight — runtime, not docs; no stale session PR), confirmed **ROUTINE_PAT set /
  loop self-fires** (issue #1832 authored by `menno420`), carried the forward queue intact (still deep,
  no THIN flag — the rebuild Phase-B canonical plan + the live SuperBot Project program dominate),
  refreshed the dashboard export (Q-0167), reset the marker #1800 → #1830.
- **Thirty-seventh Q-0107 reconciliation pass** (band-#1800, issue #1801 —
  [pass record](../planning/reconciliation-pass-2026-07-07-band1800.md)): reconciled the ledger
  (band #1771–#1800 — seven grouped entries, headlined by the **S3 rebuild final-review → plan-review →
  idea-consolidation → multi-repo program founding** arc: the FINAL review #1778/#1783 (verdict *plan ready*
  → the §6.3 runtime fixes #1781/#1782), Phase-2.5 A/B run #1775, **Projects-EAP-as-coordinator + Q-0241
  never-wait autonomy** #1776/#1777, the plan-review + owner-idea capture session #1784…#1790 (incl. the S1
  **automod** spam-evasion/duplicate-content runtime fix #1789), and the consolidation → program-founding
  session #1791…#1798 (owner rulings Q-0243…Q-0252 + the three-program-sessions launch index) — plus the
  36th-pass docs PR #1772 and 5 dashboard refreshes), trimmed Recently-shipped to 20
  (`trim_recently_shipped.py --apply`, moved 7 oldest bullets, floor recomputed), **disposed 11 open PRs** —
  **closed the 5 Codex Gate-V evidence PRs** #1752–#1755/#1758 (evidence-consumed into the merged synthesis
  #1767; two prior passes left them open — this pass acted per Q-0125 + the disposition-guard idea, flagged
  for owner veto), left the 6 dependabot bumps in flight (runtime, not docs), confirmed **ROUTINE_PAT set /
  loop self-fires** (issue #1801 authored by `menno420`), carried the forward queue intact (still deep, no
  THIN flag — the rebuild Phase-B canonical plan + the four program sessions dominate), refreshed the
  dashboard export (Q-0167), reset the marker #1770 → #1800.
- **Thirty-sixth Q-0107 reconciliation pass** (band-#1770, issue #1771 —
  [pass record](../planning/reconciliation-pass-2026-07-06-band1770.md)): reconciled the ledger
  (band #1741–#1770 — four grouped entries, headlined by the **S3 rebuild foundational consolidation →
  ONE canonical plan (Fable 5)** #1768/#1769/#1770 (the Q-0240 decide-and-flag decision model +
  `rebuild-canonical-plan-2026-07-06.md` with the corrected K-layer taxonomy) — plus the **Gate V
  verification-fleet pass A–D + synthesis** #1750/#1751/#1756/#1757/#1759/#1767 (verdict *Gate V
  COMPLETE → Phase-B under Sequence C*), the **CI-followups arc** #1743/#1744/#1745/#1747/#1748 (CodeQL
  watchdog · `check_audit_seam` + `check_deferred_recovery` AST guards · ruff replaces black+isort), and
  3 dashboard refreshes), trimmed Recently-shipped to 20 (`trim_recently_shipped.py --apply`, moved 4
  oldest bullets, floor recomputed), disposed **11 open PRs** (none a stale session PR — 6 dependabot
  bumps runtime-not-docs; 5 codex Gate V evidence reports #1752–#1755/#1758 evidence-complete, flagged
  for the owner to merge-or-close), confirmed **ROUTINE_PAT set / loop self-fires** (issue #1771 authored
  by `menno420`), carried the forward queue intact (still deep, no THIN flag — the rebuild Phase-B
  canonical plan dominates), refreshed the dashboard export (Q-0167), reset the marker #1740 → #1770.
- **Thirty-fifth Q-0107 reconciliation pass** (band-#1740, issue #1741 —
  [pass record](../planning/reconciliation-pass-2026-07-06-band1740.md)): reconciled the ledger
  (band #1711–#1740 — five grouped entries, headlined by the **S3 rebuild Gate-0 grammar-freeze →
  Phase-B L0 build-order + Stage-2 subsystem walk** #1713/#1716/#1725/#1735 — the frozen L0
  manifest-grammar + amendment registry + 16-step build-order (S0–S15) and the 52-row owner-disposition
  subsystem walk — plus the Stage-2 **save-fixes** 8-bug runtime backport + CodeQL hardening #1728/#1730
  (the band's only `disbot/` change), the **CI-setup redesign → Phase-A hard merge gates**
  #1736/#1737/#1739, the 34th-pass + open-PR sweep #1712/#1719, and 16 dashboard refreshes), trimmed
  Recently-shipped to 20 (`trim_recently_shipped.py --apply`, moved 7 oldest bullets, floor recomputed),
  disposed **0 open PRs** (none open at pass start), confirmed **ROUTINE_PAT set / loop self-fires**
  (issue #1741 authored by `menno420`), carried the forward queue intact (still deep, no THIN flag —
  the rebuild Phase-B build phase dominates), refreshed the dashboard export (Q-0167), reset the marker
  #1710 → #1740.
- **Thirty-fourth Q-0107 reconciliation pass** (band-#1710, issue #1711 —
  [pass record](../planning/reconciliation-pass-2026-07-04-band1710.md)): reconciled the ledger
  (band #1681–#1710 — three grouped entries, headlined by the **S3 rebuild foundations audit →
  Fable-5 judgment → design-prep arc** #1689/#1690/#1691/#1693/#1700/#1701/#1703/#1704/#1705 — the
  engine-room (PROMPT A) + surface/proving (PROMPT B) foundations audits, the **two confirmed prod
  loss-path fixes** #1693, and the Fable-5 capstone judgment's **7 Tier-1 owner decisions** (Q-0237)
  — plus the 33rd-pass docs PR #1682 and the per-merge dashboard refreshes
  #1692/#1694/#1702/#1706/#1707/#1709/#1710), trimmed Recently-shipped to 20
  (`trim_recently_shipped.py --apply`, floor recomputed), disposed 13 open PRs (**none a stale
  session PR** — #1708 is the active in-flight foundational-design session; #1509 + five codex review
  docs #1695–#1699 left for the owner; six dependabot bumps runtime-not-docs), confirmed **ROUTINE_PAT
  set / loop self-fires** (issue #1711 authored by `menno420`), carried the forward queue intact
  (still deep, no THIN flag — the rebuild Stage-2/design phase dominates), refreshed the dashboard
  export (Q-0167), reset the marker #1680 → #1710.
- **Thirty-third Q-0107 reconciliation pass** (band-#1680, issue #1681 —
  [pass record](../planning/reconciliation-pass-2026-07-03-band1680.md)): reconciled the ledger
  (band #1651–#1680 — four grouped entries, headlined by the **S3 rebuild new-bot capability audit →
  frozen BUILD-PLAN** #1662…#1668/#1674/#1677 (verdict **GO-with-amendments**, measured all-43 fit
  **85.1%**) and the owner-live **Phase-A conventions freeze** #1679/#1680 — plus the 32nd-pass +
  Q-0102 review/brainstorm routine sessions #1652/#1653/#1657/#1658/#1659/#1661/#1669/#1672/#1673 and
  the per-merge dashboard refreshes #1656/#1660/#1670/#1671/#1675/#1676/#1678), trimmed Recently-shipped
  to 20 (`trim_recently_shipped.py --apply`, moved 5 oldest bullets, floor recomputed), disposed 7 open
  PRs (none a stale session PR: #1509 owner audit + six dependabot bumps), confirmed **ROUTINE_PAT set /
  loop self-fires** (issue #1681 authored by `menno420`), carried the forward queue intact (still deep,
  no THIN flag — the rebuild planning phase dominates), refreshed the dashboard export (Q-0167), reset
  the marker #1650 → #1680.
- **Thirty-second Q-0107 reconciliation pass** (band-#1650, issue #1651 —
  [pass record](../planning/reconciliation-pass-2026-07-02-band1650.md)): reconciled the ledger
  (band #1621–#1650 — six grouped entries, headlined by the **S3 fresh-rebuild arc** — the Fable 5
  Phase-2 design spec, fresh-rebuild strategy + Codex map fold #1634/#1642, parallel-execution schedule
  #1644/#1645, the memory-retention/context-economy plan #1643/#1647/#1648 (Q-0214) and the linchpin
  validation #1639 — plus **server-logging v2 audit-log** #1624, **fishing Fishery** #1626, **BTD6
  Layout B** #1621, and the 31st-pass+dashboard docs band), trimmed Recently-shipped to 20
  (`trim_recently_shipped.py --apply`, floor recomputed — moved 7 oldest bullets), disposed 8 open PRs
  (none a stale session PR: #1649 memory-substrate in flight, #1509 left for owner, six dependabot
  bumps), confirmed **ROUTINE_PAT set / loop self-fires** (issue #1651 authored by `menno420`), carried
  the forward queue intact (still deep, no THIN flag), refreshed the dashboard export (Q-0167), reset
  the marker #1620 → #1650.
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
- **▶ Rebuild — the review-then-plan phase (owner-directed 2026-07-03; capstone #1674 merged):** the
  new-bot capability audit is complete — verdict **GO-with-amendments** (measured all-43 fit 85.1%),
  and [`NEW-BOT-BUILD-PLAN.md`](../analysis/rebuild-discovery/new-bot-capability-audit/findings/NEW-BOT-BUILD-PLAN.md)
  is the **frozen reference**. Next: (A) one more owner-led **content review pass** over the whole
  surface (commands / functions / methods), then (B) **one 100%-complete design plan per step**
  before any code. Process + gates + start sequence now canonical in
  [`planning/rebuild-canonical-plan-2026-07-06.md`](../planning/rebuild-canonical-plan-2026-07-06.md)
  (PR #1770). Still behind the G1 owner gate; no new-repo code yet.
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
- **Next reconciliation pass due once merged PRs cross #1920** (every multiple of 30, Q-0134) —
  auto-triggered by `reconciliation-trigger.yml`; run by the docs-reconciliation routine, **not** a
  manual session (Q-0124).
- Plan-band depth is healthy — **no `PLAN-BACKLOG-THIN` flag** (buildable depth well over cadence).
- **Owner steer (2026-06-30):** the fresh-rebuild vision re-elevates the **AI-memory substrate-kit**
  to top focus — S3's forward queue leads with PR 2 remainder + PR 3; the full rebuild stays
  idea-stage (gated on Fable 5 + owner keep/change spec).

**Cadence note:** a manually-started session does **not** run the reconciliation pass; pursue the
work it was started for. The recon marker + Recently-shipped ledger live in
[`../current-state.md`](../current-state.md).
