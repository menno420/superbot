# Reconciliation pass — 2026-06-27 · the band-#1500 Q-0107 cadence pass

> **Status:** `plan` — the docs-only review + planning pass for the band that crossed **#1500**
> (cadence = every **30th** merged PR per Q-0134; `#1500 = 30 × 50`; previous cadence pass
> [the band-#1470 pass](reconciliation-pass-2026-06-26-band1470.md), now `historical`).
> Triggered by the auto-opened `reconcile` issue **#1501**
> (`.github/workflows/reconciliation-trigger.yml`) — live proof the loop self-fires: #1501 was
> authored by **`menno420`** (the `ROUTINE_PAT` owner), not `github-actions[bot]`.
> Sections: §1 verified state + open-PR disposition · §2 band scorecard · §3 reconciled/fixed +
> control-plane · §4 the next band · §5 the idea + previous-pass review + the system improvement.
> Reset target: marker #1470 → **#1500**.
>
> **Band archetype:** `mixed` (owner-directed marquee + autonomous workflow/hardening) — the BTD6
> QA-accuracy arc was owner-directed from live screenshots and dominated the band, while the rest was
> the self-improving-workflow guard lane + autonomous test coverage + small S1 feature depth. No
> forward *queue* lane (Project Moon seam, giveaway, etc.) was executed this band.

---

## 1. Verified state at this pass (against git log + live GitHub)

Merged since the marker #1470: **#1472–#1500** (29 PRs; #1471 = this band's trigger issue, #1472 =
the prior band-#1470 pass's own docs PR, #1501 = this pass's trigger issue). The headline is the
**BTD6 QA-accuracy arc** (#1487…#1498) — owner-directed from live Discord screenshots, it grounded
damage-type/status interactions against a VERIFIED corpus, built an honest semantic-grading eval
harness, and — when the owner live-tested the DDT counter-tower list and found it wrong — **reverted
the unsound auto-derived list at the root** (#1498) rather than ground misinformation.

**Open PRs at pass time (Q-0125 disposition):** **none** — `list_pull_requests` (state=open) returned
zero before this pass opened its own PR (#1502). The cleanest disposition the snapshot can log; no
stale or redundant PRs to close.

## 2. Band scorecard (#1472–#1500)

| Theme | PRs | Source |
|---|---|---|
| **BTD6 QA-accuracy arc (S2)** — damage-type/status interaction grounding + VERIFIED corpus (#1487), corpus wired into evals (#1488), faithful "exactly live" answer-path replay (#1490), semantic grading / grader false-negative fix (#1491), AI answer review-log (#1494), VERIFIED DDT counter grounding (#1492) → **root-cause revert of the unsound auto-derived list** (#1498), arc-consolidation docs + live-verify checklist (#1493) | #1487 · #1488 · #1490 · #1491 · #1492 · #1493 · #1494 · #1498 | **owner-directed (live-test driven) — marquee** |
| **Self-improving-workflow guards (S3/S4)** — ▶ Next freshness guard (#1476) + `/session-close` wiring (#1477), session-close-gate meta-check (#1479), per-sector offline-fit startability tags (#1482, Q-0207), reconcile-marker band-consistency guard + #1472→#1470 fix (#1495), offline-startable S1 ▶ Next handoff (#1500) | #1476 · #1477 · #1479 · #1482 · #1495 · #1500 | self-improving loop (executes prior passes' ideas) |
| **S1 feature depth** — games-economy per-day faucet/sink trend view (#1483), Essential Setup "Where can people use commands?" command-channels step (#1496), mining gear loadout presets (V-14/Q-0175 Phase-1, migration 101, #1499) | #1483 · #1496 · #1499 | autonomous + owner-directed (setup) |
| **Autonomous test coverage** — YouTube fetch/renderer/embed tests (#1485), YouTube cache DB-primitive tests (#1486) | #1485 · #1486 | autonomous hardening |
| **Docs / dashboard** — the twenty-sixth Q-0107 pass (band-#1470, #1472), nine dashboard refreshes (#1473/#1474/#1475/#1478/#1480/#1481/#1484/#1489/#1497) | #1472 · 9 refreshes | routine |

**Queue execution this band:** **none of the §4 forward-queue lanes** (Project Moon seam, giveaway,
hub-rendering, card-engine next surfaces, botsite React PR 2, etc.) were executed — the band was
**owner-directed BTD6 accuracy work** (the live-test loop ran hard for a full day) plus the
**self-improving-workflow guard lane** (S3/S4 mechanisms, several executing earlier passes' own Q-0089
ideas) and **autonomous test/feature depth**. That's the `mixed` archetype: the maintainer steered the
band toward a real correctness problem (BTD6 over-refusal / wrong recommendations) rather than the
buildable queue — exactly the lane the workflow exists to support. The §4 queue is **carried forward
essentially intact** and stays deep (no THIN flag).

**Honesty highlight:** the DDT-counter sub-thread (#1492 → owner live-test → #1498 revert) is the
band's best self-correction story — the bot grounded a plausible-but-unsound list, the owner caught it
in live play, and the next session removed it at the root with a written root-cause (the committed
stats encode neither MOAB-class targeting nor config quality) instead of patching the symptom. That is
the bugs-first / root-cause-over-symptom rule working end-to-end.

## 3. Reconciled / fixed + control-plane

- **Ledger:** added the band #1472–#1500 work as **five grouped entries** (BTD6 QA-accuracy arc ·
  self-improving-workflow guards · S1 feature depth · autonomous test coverage · docs/dashboard),
  trimmed Recently-shipped back to 20 via `trim_recently_shipped.py --apply` (moved the oldest 5
  bullets #1355-band · #1364-band · #1384-band · #1351-band + the prior overflow to
  [`current-state-archive.md`](../current-state-archive.md), floor pointer recomputed), reset the
  marker **#1470 → #1500**, and bumped the `Last updated:` stamp + the top-of-file sector table +
  the S4 sector file + the next-due boundary (#1500 → **#1530**).
- **Docs:** `check_docs.py --strict` and `check_current_state_ledger.py --strict` green after edits.
- **Router (Q-0104 audit):** the band's new owner decision **Q-0207** (offline-fit startability tag
  convention, DISCUSS lane) is captured via #1482's session log. No router drift.
- **Control-plane (Q-0135):** `check_loop_health.py` **SKIP** in this container (no `gh`/token). Manual
  fallback per the routine: the trigger issue **#1501 author is `menno420`** (a real-user OWNER login) ⇒
  **`ROUTINE_PAT` is set and the loop self-fires** — matches the canonical Control-plane state table; no
  drift to correct (the bullet is a pure pointer by design).
- **Dashboard export:** regenerated `dashboard/data/dashboard.json` (Q-0167 cadence half).
- **Re-badged the band-#1470 pass record `historical`** — so **exactly one `plan`-badged
  `reconciliation-pass-*` doc exists** (this one).
- **Runtime bugs (STEP 3):** none noticed this pass (docs-only review of the band; the band's own
  BTD6 over-refusal / wrong-recommendation issue was already fixed at root in-band by #1492/#1498, and
  the still-open golden-set over-refusals are tracked in the BTD6 corpus doc, owner-paced).

## 4. The next band (depth to #1530)

**Depth check: well over the 30-slice cadence threshold, so NO `⚠️ PLAN-BACKLOG-THIN` flag.** This band
executed **no §4 queue lane** (it ran the owner-directed BTD6 accuracy arc + the workflow-guard lane
instead), so the band-#1470 §4 queue is **carried forward essentially intact**, refreshed below.

| Slice | Lane | Gate | Notes |
|---|---|---|---|
| A1 | **Project Moon — shared `KnowledgeDomain` seam extraction (Slice B)** | `plan-first` | The detector/disjointness groundwork landed (#1470). Extract the shared seam (data/fact-store/resolver/grounding/guard) from BTD6 + Limbus without behaviour change, byte-identical for BTD6. [plan](project-moon-knowledge-domain-plan-2026-06-21.md) §5. |
| A2 | **Project Moon — Slice A item 1 (StaticData exact-number ingest) + a second game (LoR / LobCorp)** | `plan-first` | After the seam: exact-number facts + the next domain as a one-line registration (the #1470 recipe). |
| A3 | **BTD6 counter-recommendation — curated/verified tower lists** | `ready` | The #1498 open question: how to do tower recommendations after reverting the auto-derived list — a hand-curated wiki-verified list, an owner-supplied list, or leave the rules-based guidance. Plus the still-open golden-set over-refusals + stale golden rubrics flagged in the BTD6 corpus doc. |
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

Gated/owner-paced (not in the buildable count): Project Moon Q-0086 live runtime walk · BTD6 live
re-test (re-run *AI Evals → suite: btd6* after deploy + live Discord spot-check) · reaction-roles web
builder (control-API write + security review) · creature-game PvP balance + art (Q-0187) · website
rollout (provision `botsite/` + submissions DB, domain cutover) · feedback-board PR 1 (owner dashboard
auth) · dashboard writes / control-API (security review) · Discord 2026 gambling-headwind review on
casino-heavy surfaces (#1333).

## 5. The idea + the previous-pass review + the system improvement

**💡 New idea (Q-0089):** *a per-band "queue-execution rate" line in each pass record* — see
[`docs/ideas/band-queue-execution-rate-2026-06-27.md`](../ideas/band-queue-execution-rate-2026-06-27.md).
Three of the last four bands executed **zero** named §4 forward-queue slices (the work was owner-directed
or autonomous-hardening instead). That's not a problem in itself — the owner steering the band toward a
real bug is exactly the point — but it *is* an invisible signal: the §4 queue keeps getting re-planned
and carried forward without anyone tracking how often a named slice actually ships. A single computed
line per pass ("queue slices executed this band: 0 of N named") would make the planning-vs-reality gap
legible across bands, and is the natural precursor to E3 (the planned-slice hit-rate tracker) — it's the
manual version that proves the metric is worth automating.

**⟲ Previous-pass review (Q-0102):** the band-#1470 pass was a clean, honest pass — it reconciled a
28-PR band into six grouped entries with zero hand-count drift, correctly fixed a real S3 drift (the
retired `needs-hermes-review` label still sitting in the S3 sector file), and **introduced the band
archetype label** (`mixed`), which proved its worth immediately: this band reused it. Its one real miss
is that it **proposed** the reconcile-marker band-consistency guard as its Q-0089 idea but the *next*
session (#1495) had to both build the guard **and** fix the very marker conflation the previous pass had
just re-introduced in its own marker text (`PR #1470 (… twenty-sixth … pass …)` again conflating reset
target with pass identity). The lesson held: ideas the loop generates get built fast (good), but the
marker text is still hand-written, so this pass deliberately wrote the marker as the clean "latest
merged PR #1500" without claiming that PR *is* the pass.

**🔧 System improvement:** the mechanical half (trim actuator + `--strict` ledger check + the #1495
`check_reconcile_marker.py` guard now live) held up with zero hand-counting — and the marker guard
shipped this band is the concrete proof the self-improving loop closes its own drift classes: the
band-#1470 pass *named* the marker-conflation problem, its idea became a real checker one session later,
and this pass is the first to run with that guard in place. The `mixed` archetype this pass labels
itself with surfaces the real readout the loop exists to produce — **the autonomous fleet did not touch
the forward queue this band**; it ran the owner's BTD6 accuracy arc and its own workflow-guard lane.
That's healthy (owner-steered correctness work + self-improvement), but it's why the §4 idea above —
make queue-execution rate a computed line — is worth having: so "the queue keeps being carried forward
un-executed" is a number the owner sees, not a thing a careful reader infers.
