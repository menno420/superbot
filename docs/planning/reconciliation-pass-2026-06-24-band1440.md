# Reconciliation pass — 2026-06-24 · the band-#1440 Q-0107 cadence pass

> **Status:** `plan` — the docs-only review + planning pass for the band that crossed **#1440**
> (cadence = every **30th** merged PR per Q-0134; `#1440 = 30 × 48`; previous cadence pass
> [the band-#1410 pass](reconciliation-pass-2026-06-24-band1410.md), now `historical`).
> Triggered by the auto-opened `reconcile` issue **#1442**
> (`.github/workflows/reconciliation-trigger.yml`) — the **twenty-third** consecutive real cadence
> fire and live proof the loop self-fires: #1442 was authored by **`menno420`** (the `ROUTINE_PAT`
> owner), not `github-actions[bot]`.
> Sections: §1 verified state + open-PR disposition · §2 band scorecard · §3 pruned/fixed +
> control-plane · §4 the next band · §5 the idea + previous-pass review + the system improvement.
> Reset target: marker #1410 → **#1441**.

---

## 1. Verified state at this pass (against git log + live GitHub)

**A full, substantial band** — the opposite of the band-#1410 micro-band (4 merges, fired ~50 min
behind its predecessor). Merged since the marker #1410: **#1413–#1441** (29 PRs; #1411 = the prior
band's trigger issue, #1412 = the prior pass's own PR). The headline is the **Essential Setup wizard
restructure** — a 13-PR S1 arc that took the setup flow from jargon-heavy panels to a linear,
direct-apply, plain-language wizard and **cut it over to the primary `!setup` / `/setup`**.

**Open PRs at pass time (Q-0125 disposition):**
- **#1440** — `Essential Setup survives restart: revive the wizard message in place`. An
  **owner-directed** (`claude/friendly-keller-e8ofhk`) follow-up to #1439 fixing a real restart bug
  (the in-channel wizard held state in memory, so its buttons died after a restart; the launcher
  already survived via `_resume_launchers`, the in-channel flow never adopted that pattern). Non-draft,
  born-red (Q-0133), **minutes old** at pass time (created ~14 min before this trigger). **Active
  in-flight — left to its own auto-merge.** Not stale, not redundant.

No stale or redundant open PRs to close this pass (the one open is minutes old and actively in flight).

## 2. Band scorecard (#1413–#1441)

| Theme | PRs | Source |
|---|---|---|
| **Essential Setup wizard restructure** — plan + simulator (#1418), banned-jargon CI guard / 207-string baseline (#1420), plain-language sweep guild→server 207→154 (#1422), the linear direct-apply **spine** (#1425) + steps 3–4 (#1427), log-channel step → two-channel mod+activity multi-select (#1429/#1432), "Reward active members" (#1434), polish + custom naming (#1435), step-0 server-type preset (#1437), **cutover to primary `!setup` / `/setup`** (#1438), plan/state reconcile (#1436), defer-before-slow-work fix (#1439) | #1418 · #1420 · #1422 · #1425 · #1427 · #1429 · #1432 · #1434 · #1435 · #1436 · #1437 · #1438 · #1439 | owner-directed (Q-0202–Q-0205) |
| **Support tickets — discoverability + full button setup** — `!setup` + welcome wiring (#1417), readiness-scan grading (#1421), fully button/dropdown setup + auto-create log channel (#1423) | #1417 · #1421 · #1423 | follow-up (#1405 subsystem) |
| **Visual card-engine H3** — rank image card in the `xpmenu` hub (#1413), help-nav attachment seam (#1430) + forward-path pins (#1431) | #1413 · #1430 · #1431 | partial (C1 card-render lineage) |
| **BTD6 unification + slash-sync runtime** — five command groups under one `/btd6` (#1419), diff-gated startup command-tree auto-sync (#1424), `!syncslash global` gated through the diff-aware helper (#1426) | #1419 · #1424 · #1426 | unplanned (owner-reported) |
| **Bot-migration assistant** — captured owner idea (#1415) + structured plan (#1416): detect → map → replicate → retire other bots | #1415 · #1416 | new idea→plan |
| **Docs** — the twenty-fourth Q-0107 reconciliation pass (band-#1410, #1412) + four dashboard refreshes (#1414/#1428/#1433/#1441) | #1412 · #1414 · #1428 · #1433 · #1441 | routine |

**~1/13 of the band-#1410 forward queue executed this band** (C1 card-render advanced via the H3
help-nav stack #1413/#1430/#1431). The rest of the band was **owner-directed off-queue work** — the
Essential Setup restructure was the maintainer's live focus all day, with the BTD6 unification and the
bot-migration plan dropped alongside. The recurring "buffer becomes the band" shape holds at full
scale here: the planned queue carries forward essentially intact (§4) while the owner's live priority
filled the band with real, shipped product.

## 3. Reconciled / fixed + control-plane

- **Ledger:** added the band #1413–#1441 work as **six grouped entries** (Essential Setup arc · ticket
  discoverability · card-engine H3 · BTD6+slash-sync · bot-migration idea→plan · docs+dashboard),
  trimmed Recently-shipped back to 20 via `trim_recently_shipped.py --apply` (moved the oldest 6 bullets
  #1349 · #1322-band · #1327 · #1323-band · #1296-band · #1300-band to
  [`current-state-archive.md`](../current-state-archive.md), floor pointer recomputed), reset the marker
  **#1410 → #1441**, and bumped the `Last updated:` stamp + the top-of-file sector table (S1 + S4 cells)
  + the S4 sector file + the next-due boundary (#1440 → **#1470**).
- **Docs:** `check_docs.py --strict` and `check_current_state_ledger.py --strict` green after edits.
- **Router (Q-0104 audit):** the band's new owner decisions are already recorded — **Q-0202** (Essential
  Setup log-channel scope + naming + step-0 preset), **Q-0203** (the log step is two-channel + multi-select,
  superseding Q-0202's moderation-only), **Q-0204** ("Reward active members" step shape), **Q-0205** (spine
  polish + "optional typing everywhere sensible"). No router drift.
- **Control-plane (Q-0135):** `check_loop_health.py` **SKIP** in this container (no `gh`/token). Manual
  fallback per the routine: the trigger issue **#1442 author is `menno420`** (a real-user OWNER login) ⇒
  **`ROUTINE_PAT` is set and the loop self-fires** — matches the canonical Control-plane state table; no
  drift to correct (the bullet is a pure pointer by design).
- **Dashboard export:** regenerated `dashboard/data/dashboard.json` (Q-0167 cadence half).
- **Re-badged the band-#1410 pass record `historical`** — the recurring "claim in prose, forget the file
  edit" drift class the band-#1410 pass itself flagged in its §5. This pass made the actual file edit, so
  **exactly one `plan`-badged `reconciliation-pass-*` doc exists** (this one).
- **Runtime bugs (STEP 3):** none noticed this pass (docs-only review of the band).

## 4. The next band (depth to #1470)

**Depth check: well over the 30-slice cadence threshold, so NO `⚠️ PLAN-BACKLOG-THIN` flag.** This
band consumed only one slice of the band-#1410 forward queue (C1 advanced via H3) and *added* fresh
depth — the **Essential Setup wizard is now complete** (so its restructure plan retires) and the
**bot-migration assistant** plan (#1416) is a new buildable initiative. The band-#1410 §4 table is
**carried forward**, refreshed below.

| Slice | Lane | Gate | Notes |
|---|---|---|---|
| A1 | **Project Moon runtime PR 1 — extract the `KnowledgeDomain` seam** | review-gated | Generalise the BTD6 stack's seam (data/fact-store/resolver/grounding) without behaviour change, byte-identical for BTD6. [plan](project-moon-knowledge-domain-plan-2026-06-21.md) §3–4. |
| A2 | **Project Moon — first domain ingest (one game)** | `plan-first` | After the seam: a first Project Moon domain's data + vocabulary + grounding, the first usable increment. |
| B0 | **Bot-migration assistant PR 1** | `plan-first` | Plan landed (#1416): detect → map → replicate → retire other bots. Build the detect/map foundation against the shipped Essential Setup spine. [plan](bot-migration-assistant-plan-2026-06-24.md). |
| B1 | **Native giveaway system PR 1** | `plan-first` | Plan landed (#1348); build the giveaway create/enter/draw loop on the audited service+migration pattern. [plan](giveaway-system-plan-2026-06-23.md). |
| B2 | **Hub child-rendering consistency PR 1** | `plan-first` | Plan landed (#1347); normalise child-panel rendering + placement coherence across hubs, building on the shipped `HubChildButton` (#1373). [plan](hub-child-rendering-and-placement-2026-06-23.md). |
| C1 | **Card-render engine — next surfaces** | `plan-first` | Profile (#1349), leaderboard + rank cards (#1398/#1399/#1401), rank-through-Help H3 (#1413/#1430/#1431) shipped; roll the themeable card onto economy/level/fishdex cards. [vision](../ideas/visual-card-engine-vision-2026-06-23.md). |
| C2 | **botsite React-SPA migration PR 2+** | `plan-first` | PR 1 landed (#1305); continue migrating the live bot-site onto the React app. [plan](botsite-react-spa-migration-plan-2026-06-20.md). |
| C3 | **Consistency-linter AI-nav PR 1** | `plan-first` | The U1 in-place AI nav landed (#1376); finish clearing the `views/ai/` `edit_in_place` findings, then graduate the rule. Runtime/Q-0086. [plan](ai-panel-inplace-navigation-plan-2026-06-19.md). |
| D1 | **Support-ticket subsystem follow-ups** | `plan-first` | Subsystem (#1405/#1410) + discoverability (#1417/#1421/#1423) shipped. Remaining depth: transcript polish, category templates, staff-routing rules, the AI-action-tool audit walk now that Q-0201 (one-click confirm) is settled. |
| D2 | **New-subsystem follow-ups** (farm / karma / casino / treasury / fishing) | `plan-first` | Each landed subsystem has depth — more casino games, karma leaderboards, treasury sinks/payouts, farm upgrades, fishdex events. [fishing plan](fishing-minigame-design-2026-06-22.md). |
| D3 | **Reconcile open-PR staleness classifier** (build the band-#1290 Q-0089 idea) | `ready` | Add machine help to the Q-0125 disposition step. [idea](../ideas/reconcile-open-pr-staleness-classifier-2026-06-22.md). |
| E1 | **procedures→skills Batch 2** | `plan-first` | [plan](procedures-to-skills-conversion-plan-2026-06-17.md); session enders → `/session-close`. Edits CLAUDE.md → review-gated. |
| E2 | **New-subsystem follow-up auto-tracker** (build the band-#1350 Q-0089 idea) | `ready` | A `## Follow-ups` stub in each new subsystem's folio at creation + a checker, so shipped depth feeds the dispatch queue. [idea](../ideas/new-subsystem-followup-tracker-2026-06-23.md). |
| E3 | **Planned-slice hit-rate tracker** (build the band-#1380 Q-0089 idea) | `ready` | Measure which named §4 slices actually ship instead of hand-counting each pass. [idea](../ideas/planned-slice-hit-rate-tracker-2026-06-24.md). |
| E4 | **One-plan-badged-pass guard** (build the band-#1410 Q-0102 idea) | `ready` | Assert exactly one `plan`-badged `reconciliation-pass-*` doc exists, so a forgotten re-badge fails fast and locally instead of reddening the next pass's CI. (This pass re-badged band-#1410 by hand — the guard would have caught the original miss.) |

Gated/owner-paced (not in the buildable count): reaction-roles web builder (Surface A, control-API
write + security review) · creature-game PvP balance + art (Q-0187) · website rollout (provision
`botsite/` + submissions DB, domain cutover) · feedback-board PR 1 (owner dashboard auth) · dashboard
writes / control-API (security review) · Project Moon later phases (per-game data-sourcing,
owner-paced) · Discord 2026 gambling-headwind review on casino-heavy surfaces (#1333).

## 5. The idea + the previous-pass review + the system improvement

**💡 New idea (Q-0089):** *band-archetype classifier in the pass record* — see
[`docs/ideas/band-archetype-classifier-2026-06-24.md`](../ideas/band-archetype-classifier-2026-06-24.md).
Three of the last four passes scored "~0–1/N of the forward queue executed; the band was owner-directed
off-queue work" — the band-#1410 micro-band, this band-#1440 Essential Setup arc, and the band-#1380
fishing/card arc. This is not a failure (the §4 queue is a *menu*, not a *schedule*, and owner-directed
work is the highest-priority lane), but the scorecard re-derives the same observation by hand every pass.
The idea: have the pass record open with a one-line **band archetype** tag — `owner-directed` /
`queue-executing` / `mixed` / `micro` — computed from (a) how many named §4 slices shipped vs. (b) how
many merges were owner-directed. Over time this gives the owner a cheap, honest readout of *how much of
the roadmap the autonomous fleet actually drives vs. how much he steers live* — which is exactly the
"is the workflow self-improving?" signal the loop exists to surface.

**⟲ Previous-pass review (Q-0102):** the band-#1410 pass was correct and unusually self-aware — it
named its own *cause* (it fired ~50 min behind its predecessor on a 4-merge band because it reset the
marker to #1404 while #1405–#1410 were already merged-or-imminent) and proposed the right fix (the
cadence-boundary jitter guard). Its one concrete miss it *also* flagged but could only fix going
forward: the "claim in prose, forget the file edit" re-badge drift. It re-badged band-#1350 and band-#1380
correctly, so this pass inherited a clean homing scope — and this pass closed the loop by actually
re-badging band-#1410 (its own §3) and queuing the **one-plan-badged-pass guard** (E4) so the class
fails fast at the root. Good pass; nothing avoidable left undone.

**🔧 System improvement:** the mechanical half held up cleanly at *full band scale* this time — a
29-PR band with a 13-PR sub-arc reconciled into six grouped bullets, `trim_recently_shipped.py --apply`
moved the oldest 6 and recomputed the floor in one verified call, and `check_current_state_ledger.py
--strict` confirmed all 29 present with zero hand-counting. The remaining inefficiency is the one §5
keeps surfacing: the **scorecard's "queue vs. owner-directed" judgement is re-made by hand every pass**
(the band-archetype idea above is the cheapest fix), and the **jitter guard** the previous pass proposed
is still unbuilt — both are S3-tooling slices, both `ready`, and both would remove a recurring manual
step from this routine. The detectors/actuators for *ledger* drift are solid; the next reconciliation-loop
wins are in **automating the pass record's prose judgements**, not the ledger mechanics.
