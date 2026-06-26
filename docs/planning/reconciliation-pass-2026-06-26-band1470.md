# Reconciliation pass — 2026-06-26 · the band-#1470 Q-0107 cadence pass

> **Status:** `plan` — the docs-only review + planning pass for the band that crossed **#1470**
> (cadence = every **30th** merged PR per Q-0134; `#1470 = 30 × 49`; previous cadence pass
> [the band-#1440 pass](reconciliation-pass-2026-06-24-band1440.md), now `historical`).
> Triggered by the auto-opened `reconcile` issue **#1471**
> (`.github/workflows/reconciliation-trigger.yml`) — live proof the loop self-fires: #1471 was
> authored by **`menno420`** (the `ROUTINE_PAT` owner), not `github-actions[bot]`.
> Sections: §1 verified state + open-PR disposition · §2 band scorecard · §3 reconciled/fixed +
> control-plane · §4 the next band · §5 the idea + previous-pass review + the system improvement.
> Reset target: marker #1441 → **#1470**.
>
> **Band archetype:** `mixed` — Project Moon advanced from one shipped PR to a complete data→grounding→
> guard arc (the marquee), while the rest of the band was small autonomous hardening (eval anchors,
> settle-once guards, two bug fixes) rather than forward-queue execution.

---

## 1. Verified state at this pass (against git log + live GitHub)

Merged since the marker #1441: **#1442–#1470** (28 PRs; #1442 = the prior band's trigger issue,
#1443 = the prior pass's own docs PR, #1471 = this pass's trigger issue). The headline is the **NEW
Project Moon (Limbus) knowledge domain** — it crossed the whole BTD6-style stack this band: a
read-only data + browse surface (PR 1, #1453), lore depth (#1456), the AI grounding path (PR 2,
#1467), a faithfulness guard (#1469), and the cross-domain over-route guard that preps the shared
seam (#1470).

**Open PRs at pass time (Q-0125 disposition):** **none** — `list_pull_requests` (state=open) returned
zero before this pass opened its own PR. The cleanest disposition the snapshot can log; no stale or
redundant PRs to close.

**Marker-labeling note (fixed this pass):** the band-#1440 marker text read
`Last reconciliation pass: PR #1441 (… twenty-fifth … pass …)`, conflating the *reset target* (#1441,
the latest merged PR at pass time — correct per the "reset to the latest PR" convention) with the
*pass identity* (the 25th pass shipped as PR **#1443**, branch `claude/reconcile-1440`). Restated this
pass so the marker names the latest PR cleanly without claiming that PR *is* the pass.

## 2. Band scorecard (#1442–#1470)

| Theme | PRs | Source |
|---|---|---|
| **NEW Project Moon (Limbus) knowledge domain** — data + browse `!pm`/`/pm` surface + Project Moon Help hub (PR 1, #1453), Sinner `literary_origin` + Origins cross-ref (lore Slice A, #1456), AI grounding path `AITask.PROJMOON_ANSWER` (PR 2, #1467), faithfulness guard (#1469), cross-domain over-route guard / detector-curation recipe (Slice B prep, #1470) | #1453 · #1456 · #1467 · #1469 · #1470 | **queue (A1/A2) — major advance** |
| **BTD6 eval-anchor hardening (S2 P1-1)** — fixture-drift anchor guard (#1458), projected-total figures + starting-cash convention (#1460), #855 MOAB-class bonuses +15/+30/+99 (#1461), eval-anchor coverage report + distractor negative-anchor guard (#1466) | #1458 · #1460 · #1461 · #1466 | autonomous hardening |
| **Settle-once money-safety (games)** — terminal guard for game-state views (#1444), blackjack-PvP guard + mixin → `utils/` (#1445), `check_consistency` Rule 6 warn-first adoption guard (#1454) | #1444 · #1445 · #1454 | autonomous hardening |
| **Essential Setup wizard follow-ons** — PR 2 extras menu + "Check my setup" (#1449), claim-GC automation Q-0206 + status badges (#1450), PR 3a retire dead/legacy sections (#1451) | #1449 · #1450 · #1451 | follow-up (shipped spine) |
| **BUG-0025 image-card navigation fix** — `/myprofile` hero-card preserved across editor nav (#1463), stranded rank card cleared on XP Configure (#1464) | #1463 · #1464 | bug fix (root) |
| **Docs / grooming / dashboard** — the twenty-fifth Q-0107 pass (band-#1440, #1443), grooming promote two ideas (#1447), nine dashboard refreshes (#1446/#1448/#1452/#1455/#1457/#1459/#1462/#1465/#1468) | #1443 · #1447 · 9 refreshes | routine |

**Queue execution this band:** the **A1/A2 Project Moon lane was the band** — it went from "PR 1
shipped" (band-#1440) to a complete data→grounding→faithfulness-guard arc plus the Slice-B-prep
disjointness guard, the single biggest forward-queue advance in several bands. The rest was
**autonomous hardening** (eval anchors, settle-once guards, two bug fixes) — small, real, root-cause
work that isn't on the §4 menu but is exactly the "bugs-first, leave it better" lane. No owner-directed
off-queue arc this band (unlike the last three), hence the `mixed` archetype.

## 3. Reconciled / fixed + control-plane

- **Ledger:** added the band #1442–#1470 work as **six grouped entries** (Project Moon · BTD6
  eval-anchors · settle-once · Essential Setup follow-ons · BUG-0025 · docs/grooming/dashboard),
  trimmed Recently-shipped back to 20 via `trim_recently_shipped.py --apply` (moved the oldest 6 bullets
  #1394 · #1354-band · #1328-band · #1329-band · #1324-band · #1345-band to
  [`current-state-archive.md`](../current-state-archive.md), floor pointer recomputed), reset the marker
  **#1441 → #1470**, and bumped the `Last updated:` stamp + the top-of-file sector table (S1/S2/S3/S4
  cells) + the S4 sector file + the next-due boundary (#1470 → **#1500**).
- **Docs:** `check_docs.py --strict` and `check_current_state_ledger.py --strict` green after edits.
- **S3 drift fixed:** the S3 sector file still tagged "Consistency-linter AI-nav PR 1" and its note with
  the **retired** `needs-hermes-review` label (Q-0197 retired it — every PR auto-merges on green CI).
  Removed both, and added the band's two S3 mechanisms (the settle-once Rule 6 guard #1454, the
  cross-domain routing-disjointness guard #1470) to S3 Recently-shipped.
- **Router (Q-0104 audit):** the band's new owner decision **Q-0206** (claim-GC automation) is recorded
  via #1450. No router drift.
- **Control-plane (Q-0135):** `check_loop_health.py` **SKIP** in this container (no `gh`/token). Manual
  fallback per the routine: the trigger issue **#1471 author is `menno420`** (a real-user OWNER login) ⇒
  **`ROUTINE_PAT` is set and the loop self-fires** — matches the canonical Control-plane state table; no
  drift to correct (the bullet is a pure pointer by design).
- **Dashboard export:** regenerated `dashboard/data/dashboard.json` (Q-0167 cadence half).
- **Re-badged the band-#1440 pass record `historical`** — so **exactly one `plan`-badged
  `reconciliation-pass-*` doc exists** (this one).
- **Runtime bugs (STEP 3):** none noticed this pass (docs-only review of the band; BUG-0025 was already
  fixed at root in-band by #1463/#1464).

## 4. The next band (depth to #1500)

**Depth check: well over the 30-slice cadence threshold, so NO `⚠️ PLAN-BACKLOG-THIN` flag.** This band
*advanced* the A1/A2 Project Moon lane substantially but left the rest of the band-#1440 forward queue
essentially intact, and Project Moon itself still has a full sub-roadmap (the live Q-0086 walk, the
shared `KnowledgeDomain` seam extraction, a first non-BTD6/non-Limbus domain). The band-#1440 §4 table is
**carried forward**, refreshed below.

| Slice | Lane | Gate | Notes |
|---|---|---|---|
| A1 | **Project Moon — shared `KnowledgeDomain` seam extraction (Slice B)** | `plan-first` | The detector/disjointness groundwork landed (#1470). Extract the shared seam (data/fact-store/resolver/grounding/guard) from BTD6 + Limbus without behaviour change, byte-identical for BTD6. [plan](project-moon-knowledge-domain-plan-2026-06-21.md) §5. |
| A2 | **Project Moon — Slice A item 1 (StaticData exact-number ingest) + a second game (LoR / LobCorp)** | `plan-first` | After the seam: exact-number facts + the next domain as a one-line registration (the #1470 recipe). |
| B0 | **Bot-migration assistant PR 1** | `plan-first` | Plan landed (#1416): detect → map → replicate → retire other bots. Build the detect/map foundation against the shipped Essential Setup spine. [plan](bot-migration-assistant-plan-2026-06-24.md). |
| B1 | **Native giveaway system PR 1** | `plan-first` | Plan landed (#1348); build the giveaway create/enter/draw loop on the audited service+migration pattern. [plan](giveaway-system-plan-2026-06-23.md). |
| B2 | **Hub child-rendering consistency PR 1** | `plan-first` | Plan landed (#1347); normalise child-panel rendering + placement across hubs on the shipped `HubChildButton` (#1373). [plan](hub-child-rendering-and-placement-2026-06-23.md). |
| C1 | **Card-render engine — next surfaces** | `plan-first` | Profile/leaderboard/rank/rank-through-Help shipped; roll the themeable card onto economy/level/fishdex cards + finish H2 `mining_render` rebase. [vision](../ideas/visual-card-engine-vision-2026-06-23.md). |
| C2 | **botsite React-SPA migration PR 2+** | `plan-first` | PR 1 landed (#1305); continue migrating the live bot-site onto the React app. [plan](botsite-react-spa-migration-plan-2026-06-20.md). |
| C3 | **Consistency-linter AI-nav PR 1** | `plan-first` | The U1 in-place AI nav landed (#1376); finish clearing the `views/ai/` `edit_in_place` findings, then graduate the rule. [plan](ai-panel-inplace-navigation-plan-2026-06-19.md). |
| D1 | **Support-ticket subsystem follow-ups** | `plan-first` | Subsystem (#1405/#1410) + discoverability (#1417/#1421/#1423) shipped. Remaining: transcript polish, category templates, staff-routing rules, the AI-action-tool audit walk (Q-0201 settled). |
| D2 | **Essential Setup PR 3b + new-subsystem follow-ups** | `plan-first` | PR 3b = rework the Advanced draft→Final-Review editor (Q-E) + delete dead service code (**needs live-bot verification**). Plus depth in farm / karma / casino / treasury / fishing. [setup plan](setup-wizard-restructure-plan-2026-06-24.md) · [fishing plan](fishing-minigame-design-2026-06-22.md). |
| D3 | **Reconcile open-PR staleness classifier** (band-#1290 idea) | `ready` | Machine help for the Q-0125 disposition step. [idea](../ideas/reconcile-open-pr-staleness-classifier-2026-06-22.md). |
| E1 | **procedures→skills Batch 2** | `plan-first` | [plan](procedures-to-skills-conversion-plan-2026-06-17.md); session enders → `/session-close`. Edits CLAUDE.md → owner-directed only. |
| E2 | **New-subsystem follow-up auto-tracker** (band-#1350 idea) | `ready` | A `## Follow-ups` stub per new subsystem folio + a checker, so shipped depth feeds the dispatch queue. [idea](../ideas/new-subsystem-followup-tracker-2026-06-23.md). |
| E3 | **Planned-slice hit-rate tracker** (band-#1380 idea) | `ready` | Measure which named §4 slices actually ship instead of hand-counting each pass. [idea](../ideas/planned-slice-hit-rate-tracker-2026-06-24.md). |
| E4 | **Band-archetype + one-plan-badged-pass guards** (band-#1410/#1440 ideas) | `ready` | Assert exactly one `plan`-badged `reconciliation-pass-*` doc; auto-tag each pass record with a band archetype. [archetype idea](../ideas/band-archetype-classifier-2026-06-24.md). |

Gated/owner-paced (not in the buildable count): Project Moon Q-0086 live runtime walk (owner — confirm a
real Limbus Q&A grounds on both providers) · reaction-roles web builder (Surface A, control-API write +
security review) · creature-game PvP balance + art (Q-0187) · website rollout (provision `botsite/` +
submissions DB, domain cutover) · feedback-board PR 1 (owner dashboard auth) · dashboard writes /
control-API (security review) · Discord 2026 gambling-headwind review on casino-heavy surfaces (#1333).

## 5. The idea + the previous-pass review + the system improvement

**💡 New idea (Q-0089):** *a `reconcile`-issue → trigger-band consistency guard* — see
[`docs/ideas/reconcile-trigger-band-consistency-guard-2026-06-26.md`](../ideas/reconcile-trigger-band-consistency-guard-2026-06-26.md).
This pass spent real time disentangling a marker mislabel (#1441 the *reset target* vs. #1443 the
*25th pass PR*) — a class of confusion that recurs because the marker text is hand-written and conflates
two different numbers. A tiny checker that, given the current marker `#N` and the latest open `reconcile`
issue, asserts the marker is the latest *merged* PR and the issue's band boundary lines up, would catch
the "marker labeled as the pass" drift at the root rather than each pass re-explaining it in prose.

**⟲ Previous-pass review (Q-0102):** the band-#1440 pass was a strong, honest pass — it reconciled a
full 29-PR band (13-PR sub-arc → six bullets) with zero hand-count drift and correctly re-badged its
predecessor. Its one avoidable miss is the marker-labeling conflation this pass had to fix (it wrote
`PR #1441 (… twenty-fifth … pass …)` when #1441 was a *dashboard refresh* and the pass itself was #1443);
the convention "reset to the latest PR" is right, but the parenthetical claimed that PR *was* the pass.
Small, cosmetic, but it cost this pass a few minutes to verify — exactly the kind of thing the §5 idea
above would catch.

**🔧 System improvement:** the mechanical half (trim + `--strict` ledger check) again held up with zero
hand-counting, and the **`mixed` band archetype this pass labels itself with is the band-#1440 §5 idea in
action** — the previous pass proposed tagging each record with `owner-directed` / `queue-executing` /
`mixed` / `micro`, and applying it here immediately surfaced the real signal: this is the first band in
four where the autonomous fleet *executed a marquee queue lane* (Project Moon A1/A2) rather than riding an
owner-directed off-queue arc. That's the "is the workflow self-improving?" readout the loop exists to
produce — worth building the archetype auto-tagger (E4) so it's computed, not judged by hand.
