# Reconciliation pass — 2026-06-24 · the band-#1410 Q-0107 cadence pass

> **Status:** `plan` — the docs-only review + planning pass for the band that crossed **#1410**
> (cadence = every **30th** merged PR per Q-0134; `#1410 = 30 × 47`; previous cadence pass
> [the band-#1380 pass](reconciliation-pass-2026-06-24-band1380.md), now `historical`).
> Triggered by the auto-opened `reconcile` issue **#1411**
> (`.github/workflows/reconciliation-trigger.yml`) — the **twenty-second** consecutive real cadence
> fire and live proof the loop self-fires: #1411 was authored by **`menno420`** (the `ROUTINE_PAT`
> owner), not `github-actions[bot]`.
> Sections: §1 verified state + open-PR disposition · §2 band scorecard · §3 pruned/fixed +
> control-plane · §4 the next band · §5 the idea + previous-pass review + the system improvement.
> Reset target: marker #1404 → **#1410**.

---

## 1. Verified state at this pass (against git log + live GitHub)

**A short band.** The previous (band-#1380) pass reset the marker to **#1404** only hours earlier
(its trigger issue was #1406, ~50 min before this one), so the cadence boundary at #1410 came around
fast. Merged since #1404: **#1405, #1407, #1408, #1410** (#1406 = the band-#1380 trigger issue,
#1409 = an open in-flight PR, #1411 = this trigger issue). Four merges, one of which (#1407) is the
previous reconciliation pass itself.

The product headline of this micro-band is the **NEW support-ticket subsystem** (#1405): a complete
`ticket` subsystem (migration 098, audited `ticket_mutation` seam, persistent launcher + control
panel + staff hub + describe modal, `!ticket`/`!ticketpanel`/`!ticketsetup`/`!ticketblacklist`)
modeled on the best ticket bots, **and the first write-capable AI *action* tool**
(`open_support_ticket`). Its same-day follow-up (#1410) re-postured that tool: the AI opens a ticket
via a **one-click confirm, not autonomously** — recorded as router **Q-0201**, superseding #1405's
direct-open draft. Alongside: **BTD6 AI floor coverage** (#1408 — range RBE + the paragon elite-boss
damage multiplier, extending the #1402/#1404 lineage).

**Open PRs at pass time (Q-0125 disposition):**
- **#1409** — `btd6/admin: fix duplicate slash-command sync + /btd6ref round range`. A fresh
  (~27 min before this trigger) `claude/*` PR fixing two owner-reported Discord-thread issues
  (a `!syncslash clear` scope for the global+guild double-render, plus a `/btd6ref round` range).
  Non-draft, born-red (Q-0133), `conflict-guard` green, `code-quality` **in_progress** at pass time
  (other checks green). **Active in-flight — left to its own auto-merge.** Not stale, not redundant.
  *(Update: #1409 merged during this pass's PR conflict-resync, while #1413 + the rank-card H3 stack also
  landed on `main`; #1409 ≤ marker #1410 so it was folded into the BTD6 ledger entry on the resync. The
  rebase took `main`'s generated dashboard artifacts and regenerated them from the merged docs.)*

No stale or redundant open PRs to close this pass (the one open is minutes old and actively in flight).

## 2. Band scorecard (#1405–#1410)

| Theme | PRs | Source |
|---|---|---|
| **NEW support-ticket subsystem** — command + AI natural language; migration 098 + audited `ticket_mutation` + views + cog; the **first write-capable AI action tool** `open_support_ticket`, re-postured to a one-click confirm (router Q-0201) | #1405 · #1410 | unplanned (owner-directed) |
| **BTD6 AI floor coverage + admin slash-command fix** — range RBE + paragon elite-boss multiplier (#1408); `!syncslash clear` dupe-fix + `/btd6ref round` range (#1409, merged during resync) | #1408 · #1409 | partial (BTD6 lineage) |
| **Docs** — the twenty-third Q-0107 reconciliation pass (band-#1380) | #1407 | routine |

**0/12 of the band-#1380 forward queue executed this band** — expected: only 3 product merges
landed before the next cadence boundary, and both were unplanned owner-directed work (the ticket
subsystem). The recurring "buffer becomes the band" shape holds in miniature; the queue carries
forward essentially intact (see §4).

## 3. Reconciled / fixed + control-plane

- **Ledger:** added the band #1405–#1410 work as **three grouped entries** (ticket subsystem
  #1405/#1410 · BTD6 floor coverage #1408 · prev recon #1407), trimmed Recently-shipped back to 20
  (moved #1294-band · #1295-band · #1305 to [`current-state-archive.md`](../current-state-archive.md),
  newest-first via `trim_recently_shipped.py --apply`; floor pointer recomputed to **#1320 … #535**),
  reset the marker **#1404 → #1410**, and bumped the `Last updated:` stamp + the top-of-file sector
  table (S4 cell) + the S4 sector file + the next-due boundary (#1410 → **#1440**).
- **Docs:** `check_docs.py --strict` and `check_current_state_ledger.py --strict` green at pass open
  (only the benign newest-merge lag, which this pass records); re-ran after edits.
- **Router (Q-0104 audit):** the band's new owner decisions are already recorded — **Q-0199**
  (AI may apply setup changes after confirmation), **Q-0200** (DISCUSS — grep-before-define dedup
  step), **Q-0201** (AI opens tickets via one-click confirm, not autonomously). No router drift.
- **Control-plane (Q-0135):** `check_loop_health.py` **SKIP** in this container (no `gh`/token).
  Manual fallback per the routine: the trigger issue **#1411 author is `menno420`** (a real-user
  OWNER login) ⇒ **`ROUTINE_PAT` is set and the loop self-fires** — matches the canonical
  Control-plane state table; no drift to correct (the bullet is a pure pointer by design).
- **Dashboard export:** regenerated `dashboard/data/dashboard.json` (Q-0167 cadence half).
- **Fixed plan-homing drift (`check_plan_homing` / `test_check_plan_homing`):** the band-#1350 pass
  record was still `plan`-badged and unhomed — the band-#1380 pass *claimed* in its prose to "re-badge
  the band-#1350 pass historical" but never edited the file's `Status` line, so it stayed in plan-homing
  scope and reddened CI on this PR. Re-badged **band-#1350 → `historical`** (the actual fix) **and
  band-#1380 → `historical`** (now superseded by this band-#1410 pass — making my own header's "now
  historical" claim true rather than repeating the same missed-edit bug). A superseded reconciliation
  pass record is `historical` by the plan-index ship convention, which removes it from homing scope.
- **Runtime bugs (STEP 3):** none noticed this pass (docs-only review of a 4-PR band).

## 4. The next band (depth to #1440)

**Depth check: well over the 30-slice cadence threshold, so NO `⚠️ PLAN-BACKLOG-THIN` flag.** This
band consumed essentially none of the band-#1380 forward queue — that queue was planned only hours
earlier and remains intact — and the band *added* fresh buildable depth (the new ticket subsystem
has obvious follow-ups). The band-#1380 §4 table is therefore **carried forward**, lightly refreshed
below to reflect the now-merged ticket subsystem.

| Slice | Lane | Gate | Notes |
|---|---|---|---|
| A1 | **Project Moon runtime PR 1 — extract the `KnowledgeDomain` seam** | review-gated | Generalise the BTD6 stack's seam (data/fact-store/resolver/grounding) without behaviour change, byte-identical for BTD6. [plan](project-moon-knowledge-domain-plan-2026-06-21.md) §3–4. |
| A2 | **Project Moon — first domain ingest (one game)** | `plan-first` | After the seam: a first Project Moon domain's data + vocabulary + grounding, the first usable increment. |
| B1 | **Native giveaway system PR 1** | `plan-first` | The plan landed (#1348); build the giveaway create/enter/draw loop on the audited service+migration pattern. [plan](giveaway-system-plan-2026-06-23.md). |
| B2 | **Hub child-rendering consistency PR 1** | `plan-first` | The plan landed (#1347); normalise child-panel rendering + placement coherence across hubs, building on the shipped `HubChildButton` (#1373). [plan](hub-child-rendering-and-placement-2026-06-23.md). |
| C1 | **Card-render engine — next surfaces** | `plan-first` | Profile (#1349), leaderboard + rank cards (#1398/#1399/#1401) shipped; roll the themeable card onto economy/level/fishdex cards. [vision](../ideas/visual-card-engine-vision-2026-06-23.md). |
| C2 | **botsite React-SPA migration PR 2+** | `plan-first` | PR 1 landed (#1305); continue migrating the live bot-site onto the React app. [plan](botsite-react-spa-migration-plan-2026-06-20.md). |
| C3 | **Consistency-linter AI-nav PR 1** | `plan-first` | The U1 in-place AI nav landed (#1376); finish clearing the `views/ai/` `edit_in_place` findings, then graduate the rule. Runtime/Q-0086. [plan](ai-panel-inplace-navigation-plan-2026-06-19.md). |
| D1 | **Support-ticket subsystem follow-ups** | `plan-first` | The subsystem shipped (#1405/#1410). Obvious depth: transcript polish, category templates, staff-routing rules, the AI-action-tool audit walk now that Q-0201 (one-click confirm) is settled. |
| D2 | **New-subsystem follow-ups** (farm / karma / casino / treasury / fishing) | `plan-first` | Each landed subsystem has depth — more casino games, karma leaderboards, treasury sinks/payouts, farm upgrades, fishdex events. [fishing plan](fishing-minigame-design-2026-06-22.md). |
| D3 | **Reconcile open-PR staleness classifier** (build the band-#1290 Q-0089 idea) | `ready` | Add machine help to the Q-0125 disposition step. [idea](../ideas/reconcile-open-pr-staleness-classifier-2026-06-22.md). |
| E1 | **procedures→skills Batch 2** | `plan-first` | [plan](procedures-to-skills-conversion-plan-2026-06-17.md); session enders → `/session-close`. Edits CLAUDE.md → review-gated. |
| E2 | **New-subsystem follow-up auto-tracker** (build the band-#1350 Q-0089 idea) | `ready` | A `## Follow-ups` stub in each new subsystem's folio at creation + a checker, so shipped depth feeds the dispatch queue. [idea](../ideas/new-subsystem-followup-tracker-2026-06-23.md). |
| E3 | **Planned-slice hit-rate tracker** (build the band-#1380 Q-0089 idea) | `ready` | Measure which named §4 slices actually ship instead of hand-counting each pass. [idea](../ideas/planned-slice-hit-rate-tracker-2026-06-24.md). |

Gated/owner-paced (not in the buildable count): reaction-roles web builder (Surface A, control-API
write + security review) · creature-game PvP balance + art (Q-0187) · website rollout (provision
`botsite/` + submissions DB, domain cutover) · feedback-board PR 1 (owner dashboard auth) · dashboard
writes / control-API (security review) · Project Moon later phases (per-game data-sourcing,
owner-paced) · Discord 2026 gambling-headwind review on casino-heavy surfaces (#1333).

## 5. The idea + the previous-pass review + the system improvement

**💡 New idea (Q-0089):** *cadence-boundary jitter guard* — see
[`docs/ideas/recon-cadence-boundary-jitter-2026-06-24.md`](../ideas/recon-cadence-boundary-jitter-2026-06-24.md).
This pass fired only ~50 minutes after the previous one, on a band of just **4 merges** (one of which
was the previous pass itself) — because the previous pass reset its marker to **#1404** while
#1405–#1410 were already merged or in flight, so the very next merge crossed the #1410 boundary
immediately. The cadence is doing its job, but at burst velocity a strict "every 30th PR" can fire a
near-empty pass right behind a full one. The idea: have `check_reconciliation_due.py` (or the trigger
workflow) suppress a new `reconcile` issue when the *previous* pass merged within the last N PRs / M
hours **and** fewer than K product PRs have merged since — folding the tiny band into the next real
one instead of spending a full pass ritual on it. (Records the boundary it skipped so nothing is lost.)

**⟲ Previous-pass review (Q-0102):** the band-#1380 pass was thorough and correct — accurate
seven-entry scorecard, a genuinely deep §4 queue, a well-aimed §5 idea (planned-slice hit-rate
tracker), and clean open-PR disposition (#1405 left to auto-merge, which is exactly where it landed).
Its one avoidable cost is the one this pass's idea targets: it reset the marker to **#1404** even
though #1405 was already merged-or-imminent, which guaranteed the cadence would re-fire almost
immediately on a 4-PR band. Resetting the marker to the *latest merged PR at pass time* (or noting
the imminent crossing) would have let this near-empty pass be absorbed. Not wrong — the marker rule
is "reset to the latest PR" and #1404 *was* the latest *merged* at that instant — but it shows the
strict-boundary rule needs the jitter guard above.

**🔧 System improvement:** the mechanical half held up cleanly again — `trim_recently_shipped.py
--apply` moved the oldest 3 bullets and recomputed the floor pointer (#1320 … #535) in one verified
call, and `check_current_state_ledger.py --strict` confirmed all live PRs present with zero
hand-counting. The improvement this pass *proposes* (the jitter guard) is the natural next step: the
detectors and actuators for ledger drift are solid; the remaining inefficiency is in the *trigger
cadence* firing a full ritual on a band too small to warrant one. That is the cheapest remaining win
in the reconciliation loop.

A **second, concrete drift class surfaced this pass** (and was fixed in §3): a pass record's prose says
"re-badged the previous pass `historical`" while the previous pass *file* is left `plan`-badged — so it
silently stays in `check_plan_homing` scope and reddens the *next* pass's CI (exactly what happened to
band-#1350 here). The recurring shape is "claim in prose, forget the file edit." The cheap guard that
would catch it at the root: assert **exactly one `plan`-badged `reconciliation-pass-*` doc exists** (the
current pass), so a forgotten re-badge fails fast and locally instead of surfacing two bands later. Not
built this pass (it needs a test, which is out of scope for a docs-only routine) — captured here as the
next reconciliation-tooling slice.
