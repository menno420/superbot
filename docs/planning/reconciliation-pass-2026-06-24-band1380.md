# Reconciliation pass — 2026-06-24 · the band-#1380 Q-0107 cadence pass

> **Status:** `historical` — the docs-only review + planning pass for the band that crossed **#1380**
> (cadence = every **30th** merged PR per Q-0134; `#1380 = 30 × 46`; previous cadence pass
> [the band-#1350 pass](reconciliation-pass-2026-06-23-band1350.md), now `historical`).
> Triggered by the auto-opened `reconcile` issue **#1406**
> (`.github/workflows/reconciliation-trigger.yml`) — the **twenty-first** consecutive real cadence
> fire and live proof the loop self-fires: #1406 was authored by **`menno420`** (the `ROUTINE_PAT`
> owner), not `github-actions[bot]`.
> Sections: §1 verified state + open-PR disposition · §2 band scorecard · §3 pruned/fixed +
> control-plane · §4 the next band · §5 the idea + previous-pass review + the system improvement.
> Reset target: marker → **#1404**.

---

## 1. Verified state at this pass (against git log + live GitHub)

**Merged since the band-#1350 pass (band #1351–#1404; #1353 = that pass's trigger issue, #1354 = the
pass PR itself; #1351 was the open PR left to auto-merge at that pass and landed into this band).** The
headline is the **consolidation & discoverability audit going from brief → executed** as a multi-session
**ultracode fleet**: a help-findability foundation + per-command reachability guard, the extracted shared
`HubChildButton`, in-place navigation across AI/roles/games panels, and the **never-stranded** pair
(universal Help + Back-to-hub on every leaf panel; game-result continuation buttons). Alongside it: the
**AI natural-language setup wedge** maturing into the first AI surface that *applies* setup changes after
confirmation (`/setup-describe` → create+bind → Accept·Deny·Edit advisor, Q-0048 write-lift / Q-0199), the
**themeable card-render engine** rolling onto real features (leaderboard + rank image cards, the planned
band-#1350 C1 slice), **BTD6 mechanics/round-economy depth** (round-scaled bloon health, freeplay curve
fix, paragon elite-boss ×2, per-round economy slash commands), **fishing follow-ups** (the band-#1350 D2
slice), and a standalone **obfuscation-resistant moderation word filter**. As in nearly every prior band,
much of the band-#1350 forward queue (Project Moon, hub child-rendering, giveaway) carried forward
untouched — the buffer (the discoverability audit + card-engine rollout) *was* the band — but this band is
unusual in that **two planned slices (C1 card-engine rollout, D2 fishing) did land**.

**Open PRs at pass time (Q-0125 disposition):**
- **#1405** — `tickets: support-ticket subsystem (command + AI natural language)`. A fresh (created
  ~4 min before the trigger issue) `claude/*` subsystem PR; non-draft, born-red (Q-0133), auto-merge
  armed. Carries an owner-directed feature (research the best ticket bots → build by command + AI NL) and
  a ratification Q (the first write-capable AI *action* tool — `open_support_ticket` through the audited
  mutation seam). **Active in-flight — left to its own auto-merge.** Not stale, not redundant.

No stale or redundant open PRs to close this pass (the one open is minutes old and actively in flight).

## 2. Band scorecard (#1351–#1404)

| Theme | PRs | Source |
|---|---|---|
| **Consolidation & discoverability audit — execution** (ultracode fleet): help-findability foundation + reachability guard · Phase-0 shared hub-child primitive + settings-orphan guard + fleet plan · extracted `HubChildButton` + dependency/ownership map + coordinator · in-place nav (AI/roles/games) · `!btd6strat` Strategy-panel button · universal Help + Back-to-hub on every leaf · game-result continuation buttons · settings-reachability guard · cleanup-policy panel tips · delete-blocked-commands · Final-Review create-count guard · audit briefs | #1359 · #1360 · #1361 · #1363 · #1366 · #1367 · #1369 · #1370 · #1371 · #1372 · #1373 · #1374 · #1375 · #1376 · #1377 · #1378 · #1382 · #1383 · #1385 | unplanned (owner-directed audit) |
| **AI natural-language setup wedge — Q-0048 write-lift / Q-0199**: `/setup-describe` · create+bind · Accept·Deny·Edit advisor · edit-rebind | #1355 · #1357 · #1386 · #1390 | unplanned (owner-directed) |
| **Themeable card-render engine — H2/H3 rollout**: golden tests · renderers onto `CardCanvas` + guards · leaderboard image card + themes · rank image card | #1364 · #1396 · #1397 · #1398 · #1399 · #1401 · #1403 | **planned (C1 card-engine rollout)** |
| **BTD6 mechanics + round-economy depth**: round-scaled bloon health · freeplay curve fix + RBE · paragon elite-boss ×2 · per-round economy slash commands | #1384 · #1387 · #1402 · #1404 | partial (BTD6 lineage) |
| **Fishing minigame follow-ups**: trophy records · soft-fail clue + heaviest-catch leaderboard · `premature_grace` rod knob | #1351 · #1356 · #1365 | **planned (D2 fishing slices)** |
| **Moderation**: obfuscation-resistant word filter (out-filters Sapphire) | #1394 | unplanned (competitive-positioning) |
| **Docs / ideas / router / dashboard**: prev recon pass · promote loose ideas · router Q-0199 · BTD6 runtime-mechanics + cash-model ideas · reconcile consolidation-audit docs · 6 dashboard refreshes | #1354 · #1362 · #1389 · #1391 · #1392 · #1393 · #1358 · #1368 · #1380 · #1388 · #1395 · #1400 | routine + planning |

**2/12 planned slices executed (C1 card-engine rollout, D2 fishing) — better than the usual ~1/11** —
but the band's volume was still dominated by the unplanned owner-directed discoverability audit and the
AI-setup wedge. The recurring "buffer becomes the band" shape holds; the difference this band is that the
card-engine vision (#1349, last band) produced a *concrete, plan-first* C1 slice that a session actually
pulled — evidence for the band-#1350 §5 thesis (feed the queue from real shipped depth, not aspirational
runtime initiatives).

## 3. Reconciled / fixed + control-plane

- **Ledger:** added the band #1351–#1404 work as **seven grouped entries**, trimmed Recently-shipped back
  to 20 (moved #1308-band · #1307-band · #1281-band · #1270-band · #1275-band · #1283-band · #1267-band to
  [`current-state-archive.md`](../current-state-archive.md), newest-first via
  `trim_recently_shipped.py --apply`; floor pointer recomputed to **#1320 … #535**), reset the marker
  **#1352 → #1404**, and bumped the `Last updated:` stamp + the top-of-file sector table (S4 cell) + the
  next-due boundary (#1380 → **#1410**).
- **Docs:** `check_docs.py --strict` and `check_current_state_ledger.py --strict` green at pass open
  (only the benign 45-merge newest lag, which this pass records); re-ran after edits.
- **Control-plane (Q-0135):** `check_loop_health.py` **SKIP** in this container (no `gh`/token). Manual
  fallback per the routine: the trigger issue **#1406 author is `menno420`** (a real-user OWNER login) ⇒
  **`ROUTINE_PAT` is set and the loop self-fires** — matches the canonical Control-plane state table; no
  drift to correct (the bullet is a pure pointer by design).
- **Dashboard export:** regenerated `dashboard/data/dashboard.json` (Q-0167 cadence half).

## 4. The next band (depth to #1410)

**Depth check: well over the 30-slice cadence threshold, so NO `⚠️ PLAN-BACKLOG-THIN` flag.** Two slices
of the band-#1350 queue executed (C1, D2) and the rest carries forward intact; the band *added* buildable
lanes (the support-ticket subsystem #1405 in flight with obvious follow-ups, the AI-setup wedge with a
next surface, more card-engine surfaces). **Honest caveat (carried, unchanged):** the *cleanly-ungated
self-merge* subset is thinner than the headline — Project Moon's runtime build and the AI-nav /
procedures→skills batches are runtime/review-gated, so an empty *autonomous* fire should prefer a
substantial review-gated lane or promote a fresh idea → plan → build (Q-0172) over a marginal guard.

| Slice | Lane | Gate | Notes |
|---|---|---|---|
| A1 | **Project Moon runtime PR 1 — extract the `KnowledgeDomain` seam** | review-gated | Generalise the BTD6 stack's seam (data/fact-store/resolver/grounding) without behaviour change, byte-identical for BTD6. [plan](project-moon-knowledge-domain-plan-2026-06-21.md) §3–4. |
| A2 | **Project Moon — first domain ingest (one game)** | `plan-first` | After the seam: a first Project Moon domain's data + vocabulary + grounding, the first usable increment. |
| B1 | **Native giveaway system PR 1** | `plan-first` | The plan landed (#1348); build the giveaway create/enter/draw loop on the audited service+migration pattern. [plan](giveaway-system-plan-2026-06-23.md). |
| B2 | **Hub child-rendering consistency PR 1** | `plan-first` | The plan landed (#1347); normalise child-panel rendering + placement coherence across hubs. Now *complemented* by the shipped `HubChildButton` (#1373) — build on it. [plan](hub-child-rendering-and-placement-2026-06-23.md). |
| C1 | **Card-render engine PR 4+** | `plan-first` | Profile (#1349), leaderboard + rank cards (#1398/#1399/#1401) shipped; roll the themeable card onto the next surfaces (economy/level/fishdex cards). [vision](../ideas/visual-card-engine-vision-2026-06-23.md). |
| C2 | **botsite React-SPA migration PR 2+** | `plan-first` | PR 1 landed (#1305); continue migrating the live bot-site onto the React app. [plan](botsite-react-spa-migration-plan-2026-06-20.md). |
| C3 | **Consistency-linter AI-nav PR 1** | `plan-first` | [plan](ai-panel-inplace-navigation-plan-2026-06-19.md). The U1 in-place AI nav landed (#1376); finish clearing the `views/ai/` `edit_in_place` findings, then graduate the rule. Runtime/Q-0086. |
| D1 | **Support-ticket subsystem follow-ups** | `plan-first` | The subsystem is in flight (#1405); obvious depth — ticket transcripts polish, category templates, staff-routing rules, the AI-action-tool audit walk. Gate on the #1405 ratification Q landing. |
| D2 | **New-subsystem follow-ups** (farm / karma / casino / treasury / fishing) | `plan-first` | Each landed subsystem has depth — more casino games, karma leaderboards, treasury sinks/payouts, farm upgrades, fishdex events. [fishing plan](fishing-minigame-design-2026-06-22.md). |
| D3 | **Reconcile open-PR staleness classifier** (build the band-#1290 Q-0089 idea) | `ready` | Add machine help to the Q-0125 disposition step. [idea](../ideas/reconcile-open-pr-staleness-classifier-2026-06-22.md). |
| E1 | **procedures→skills Batch 2** | `plan-first` | [plan](procedures-to-skills-conversion-plan-2026-06-17.md); session enders → `/session-close`. Edits CLAUDE.md → review-gated. |
| E2 | **New-subsystem follow-up auto-tracker** (build the band-#1350 Q-0089 idea) | `ready` | A `## Follow-ups` stub in each new subsystem's folio at creation + a checker, so shipped depth feeds the dispatch queue. [idea](../ideas/new-subsystem-followup-tracker-2026-06-23.md). |

Gated/owner-paced (not in the buildable count): reaction-roles web builder (Surface A, control-API write +
security review) · creature-game PvP balance + art (Q-0187) · website rollout (provision `botsite/` +
submissions DB, domain cutover) · feedback-board PR 1 (owner dashboard auth) · dashboard writes /
control-API (security review) · Project Moon later phases (per-game data-sourcing, owner-paced) · Discord
2026 gambling-headwind review on casino-heavy surfaces (#1333).

## 5. The idea + the previous-pass review + the system improvement

**💡 New idea (Q-0089):** *planned-slice hit-rate tracker* — see
[`docs/ideas/planned-slice-hit-rate-tracker-2026-06-24.md`](../ideas/planned-slice-hit-rate-tracker-2026-06-24.md).
The band-#1320 pass *proposed* measuring the buffer-becomes-band gap and every pass since has hand-counted
"~1/11 planned slices executed" in prose — this pass counted 2/12 by hand again. A tiny script that, given
a pass's §4 queue table (slice → PR-lineage) and the next band's merged PRs, reports the **hit rate**
(which planned slices actually shipped) would turn that recurring manual scorecard line into a measured,
trend-able number — and make the "is the forward queue predictive or aspirational?" question answerable
across passes instead of re-litigated each one.

**⟲ Previous-pass review (Q-0102):** the band-#1350 pass was strong — correct open-PR disposition (#1351
left to auto-merge, which is exactly where it landed in this band), an accurate eight-entry scorecard, and
its §5 idea (new-subsystem follow-up auto-tracker) was well-aimed at the "shipped depth gets orphaned"
problem. What it *slightly* under-called: its §4 forward queue listed C1 (card-engine rollout) and D2
(fishing) as plan-first lanes, and **both actually shipped this band** — yet the queue framing still
treated the long-horizon review-gated lanes (Project Moon, AI-nav) as the headline. The lesson the
hit-rate idea (this pass) encodes: the queue *is* becoming predictive for the plan-first product lanes;
the passes should lead with those and stop over-indexing on the gated runtime initiatives that never move.

**🔧 System improvement:** the mechanical half of this ritual held up cleanly again —
`trim_recently_shipped.py --apply` moved the oldest 7 bullets and recomputed the floor pointer
(#1320 … #535) in one verified call, and `check_current_state_ledger.py --strict` confirmed all 49 live
PRs present with zero hand-counting. The remaining manual edges are unchanged: the *grouping* of merges
into themed entries and the *prose* of the §4 queue. The hit-rate idea above attacks the queue's
*accountability* (did the slices we named ship?); combined with the still-pending new-subsystem
follow-up tracker (band-#1350), the two close the loop between "what we planned" and "what the bands
actually produce."
