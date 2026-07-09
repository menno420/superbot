# Fortieth Q-0107 reconciliation pass — band-#1890

> **Status:** `historical` — pass record (dated snapshot). Live state: [`../current-state.md`](../current-state.md).
> Trigger issue: **#1891** (`reconcile`). Marker: **#1861 → #1890**.

## What this pass did

Docs-only Q-0107 reconciliation + planning pass over **band #1863–#1890**. No `disbot/` runtime,
migrations, or tests touched by this pass (Q-0107 rule). **The entire band is docs/tooling** —
verified `git diff --name-only e9988b3b..72053d26 -- 'disbot/'` returns nothing (the band's larger
diffs are the substrate-kit in-tree copy *deletion* (#1882) and the exporter-telemetry / dashboard
tooling, all outside `disbot/`).

### Ledger reconciled (band #1863–#1890 → seven grouped Recently-shipped entries)

- **#1864 · #1866 · #1867 · #1868** — the **EAP Anthropic-feedback email assembled + sent, close-out**:
  #1864 assembled the full two-part email (landed Menno's Part 1, made the agent Part 2 complementary),
  #1866 signed Part 2 as Claude (two-author sign-off), #1867 closed out the projects-testing feedback
  thread, #1868 shipped the rebuild-direction handoff + marked the EAP email sent.
- **#1873 · #1874 · #1875 · #1876 · #1877 · #1887 · #1889 · #1890** — the **EAP Project fleet founding →
  independent cross-repo review**: the fleet grew to **four repos** (`superbot`, `superbot-next`,
  `substrate-kit`, `websites`). #1877 = the EAP Project fleet plan (7 domain projects + 3-model
  comparison + kit-lab); #1874 = a second Project (rebuild status site + Railway test); #1876 = the
  websites Project kickoff (superseding the draft); #1873 = the rebuild-Project audit checklist (+ a
  planning/README homing fix, Q-0166); #1875 = the settings-ledger update (rulesets now on `superbot-next`
  + `substrate-kit`). #1887/#1889/#1890 = the **independent cross-repo fleet review**
  ([`../eap/fleet-review-2026-07-09.md`](../eap/fleet-review-2026-07-09.md) — honest verdict + first-party
  clone-and-run verification: `superbot-next` 998 pass / 1 skip under **Python 3.11**) + the
  **manager-Project brief**. Headline finding: the substrate-kit's **render/engage half strands in every
  fresh adoption** (`adopt` plants-but-doesn't-render/wire) — an **upstream-kit** fix, captured for kit-lab.
- **#1878 · #1879 · #1881 · #1882 · #1883 · #1884** — the **substrate-kit graduation to its own repo**
  ([menno420/substrate-kit](https://github.com/menno420/substrate-kit), v1.0.0), superbot as first consumer:
  #1878 substrate-kit planning; #1879 pinned the kit via a root **`substrate.config.json`** (kit-lab
  founding-plan §4.2 consumer half); #1882 **removed the in-tree `substrate-kit/` + `tests/unit/substrate_kit/`
  copy** (101 files — the kit lives upstream now); #1881 added **program-law provenance riders**
  (PL-001…PL-009) to the eight origin Q-blocks in the router (KL-2 companion); #1883 shipped the exporter
  **`telemetry` family** in `export_dashboard_data.py` (KL-6 companion — reads `telemetry/model-usage.jsonl`,
  field-whitelisted, fail-open, capped to 200 rows); #1884 pinned the **`console.json` cross-repo shape
  contract**.
- **#1886** — the **Dependabot PR policy** (owner decision **Q-0256**, durable home
  [`../operations/repo-settings-state.md`](../operations/repo-settings-state.md) § Dependabot PR policy;
  the not-shipped auto-arm alternative is Q-0257) + the **backlog review/merge of #1761–#1766**.
- **#1863** — the 39th Q-0107 pass docs PR (band-#1860).
- **#1865 · #1869 · #1870 · #1871 · #1872 · #1880 · #1885 · #1888** — 8 dashboard-data refreshes (Q-0167).

Trimmed Recently-shipped 27 → **20** (`trim_recently_shipped.py --apply`, moved the 7 oldest bullets —
the #1778/#1783 FINAL-review, #1776/#1777 coordinator+Q-0241, #1775 Phase-2.5 A/B, the #1773-dashboard
band, #1772 36th-pass, #1781/#1782 §6.3 live-bot fixes, #1768/#1769/#1770 canonical-plan — to the archive,
floor pointer recomputed). `check_current_state_ledger --strict` and `check_docs --strict` both green.

### Runtime note (captured, not fixed — Q-0107 docs-only)

**No new runtime bug noticed this pass**, and the band shipped **zero** `disbot/` runtime changes, so the
bug-book (step 3) was untouched. Open bugs BUG-0009 / BUG-0011 remain OPEN as recorded in the bug-book.

The fleet-review's one reproducible weakness — the substrate-kit **`adopt` render/engage gap** — is a
*cross-repo kit* defect, **not** a superbot `disbot/` bug; it is already homed in
[`../eap/fleet-review-2026-07-09.md`](../eap/fleet-review-2026-07-09.md) and belongs upstream in kit-lab,
so no superbot bug-book entry is warranted.

### Open-PR disposition (Q-0125 — 0 open at pass start)

**Zero open PRs at pass start** (`list_pull_requests` state=open → empty). The 6 dependabot dep-bumps that
sat in flight through passes 30–39 were **cleared this band** under the new Q-0256 review-on-sight policy
(#1886: #1762/#1763/#1764/#1765/#1766 merged, #1761 closed as a subset). This is the cleanest open-PR
disposition the snapshot has logged since band-#870.

### Control-plane (Q-0135)

`check_loop_health.py` **SKIP** (no `gh`/token in the sandbox). MCP fallback: the newest `reconcile`
trigger issue **#1891 is authored by `menno420`** (a real-user login) ⇒ **ROUTINE_PAT set, loop
self-fires**. The canonical Control-plane state table (rows 1/2/6 verified live) is unchanged; row 1's
verdict stays ✅ (this pass is one more live re-confirmation).

### Planning — next full band (Q-0144 + Q-0164)

**No `PLAN-BACKLOG-THIN` flag.** Forward buildable depth is well over the 30-PR cadence:

- the frozen **rebuild Phase-B canonical plan**
  ([`rebuild-canonical-plan-2026-07-06.md`](rebuild-canonical-plan-2026-07-06.md), 16-step S0–S15
  build-order) remains the spine; and
- the **live SuperBot Project fleet** — now four repos with a dedicated **manager-Project brief**
  ([`eap-manager-project-brief-2026-07-09.md`](eap-manager-project-brief-2026-07-09.md)), the
  **EAP Project fleet plan** (7 domain projects + kit-lab), the **kit-lab founding plan** (KL bands
  — KL-2/KL-6 companions landed this band, more queued), and the **websites Project**
  ([`websites-project-kickoff-2026-07-09.md`](websites-project-kickoff-2026-07-09.md)) — dominates the
  active execution queue.

Freshly-planned buildable work landed **this** band (no idea→plan promotion was needed to fill it): the
EAP fleet plan (#1877), the manager-Project brief (#1887), the websites Project kickoff (#1876), and the
per-repo settings-ledger continuation (#1875). The one genuine finding to feed forward — the kit
`adopt` **render/engage gap** — is a concrete, buildable kit-lab slice (fix `adopt` to render `${...}`
and wire `.claude/` on fresh adoption), homed in the fleet review for the kit-lab Project.

### Freshness

Regenerated `dashboard/data/dashboard.json` (+ botsite mirrors) via `export_dashboard_data.py` (Q-0167).

### Q-0089 idea + Q-0102 review

See the session log [`.sessions/2026-07-09-reconcile-band1890.md`](../../.sessions/2026-07-09-reconcile-band1890.md).
