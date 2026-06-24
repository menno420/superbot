# Reconciliation pass — 2026-06-23 · the band-#1350 Q-0107 cadence pass

> **Status:** `historical` — the docs-only review + planning pass for the band that crossed **#1350**
> (cadence = every **30th** merged PR per Q-0134; `#1350 = 30 × 45`; previous cadence pass
> [the band-#1320 pass](reconciliation-pass-2026-06-22-band1320.md), now `historical`).
> Triggered by the auto-opened `reconcile` issue **#1353**
> (`.github/workflows/reconciliation-trigger.yml`) — the **twentieth** consecutive real cadence fire
> and live proof the loop self-fires: #1353 was authored by **`menno420`** (the `ROUTINE_PAT` owner),
> not `github-actions[bot]`.
> Sections: §1 verified state + open-PR disposition · §2 band scorecard · §3 pruned/fixed + control-plane
> · §4 the next band · §5 the idea + previous-pass review + the system improvement.
> Reset target: marker → **#1352**.

---

## 1. Verified state at this pass (against git log + live GitHub)

**Merged since the band-#1320 pass (band #1322–#1352; #1321 = that pass's trigger issue, #1323 = the pass
PR itself).** The headline is a **wave of brand-new economy/game subsystems** — an idle egg/chicken **farm**,
a **Karma** reputation system, a **Casino** (table framework + Texas Hold'em poker), and a server-owned
**Treasury** coin pool — alongside a deep **fishing-minigame expansion** (bait economy knobs, bait-crafting,
a deepwater boat venue, daily weather), **BTD6 round-economy** answers (round XP + unified RBE/cash/XP
reply), a **themeable card-render engine** (the out-visual-Dank-Memer foundation), **cleanup-surface**
simplification, and a batch of **tooling/CI guards**. As in nearly every prior band, the planned band-#1320
queue (A1–E3) mostly carried forward untouched — the buffer became the band (the farm/karma/casino/treasury
arc and the fishing expansion were not in the queue). **Fishing follow-ups (D1)** is the one queue slice
that landed.

**Open PRs at pass time (Q-0125 disposition):**
- **#1351** — `Fishing: trophy records (per-species biggest-caught)`. A fresh (created ~7 min before this
  pass) `claude/*` game PR; born-red (Q-0133), `conflict-guard` green, `code-quality` still running.
  **Active in-flight — left to its own auto-merge.** Not stale, not redundant.

No stale or redundant open PRs to close this pass (the one open is minutes old and actively in flight).

## 2. Band scorecard (#1322–#1352)

| Theme | PRs | Source |
|---|---|---|
| **NEW economy/game subsystems** — idle farm (+fresh-coop fix) · Karma reputation · Casino table-framework + Texas Hold'em · Treasury server coin-pool (+Economy panel link) | #1328 · #1331 · #1332 · #1333 · #1334 · #1344 | unplanned (buffer-became-band) |
| **Fishing minigame expansion** — Bait knob · bait speed knob · bait-crafting · deepwater boat venue · daily weather · test-helper consolidation | #1329 · #1337 · #1338 · #1340 · #1341 · #1342 | **planned (D1 fishing follow-ups)** |
| **BTD6 round economy** — round XP surface · unified RBE/cash/XP reply · validated round_xp.json | #1324 · #1326 · #1325 (#1318) | partial (BTD6 lineage) |
| **Themeable card-render engine** — engine + first profile card (out-visual Dank Memer PR 1) | #1349 | unplanned (owner-directed visual arc) |
| **Cleanup channel surface** — panel UX (readable whitelist, fixable warnings, custom levels) → removed legacy whitelist | #1345 · #1350 | unplanned (drift-on-sight / owner-adjacent) |
| **Tooling / CI guards** — migration-collision guard · isort scope fix · `new_subsystem.py` checker extension | #1322 · #1343 · #1346 | unplanned (drift-on-sight) |
| **Hermes ops** — one-command auto-redeploy (no terminal) | #1327 | unplanned (ops) |
| **Docs / plans / dashboard** — prev recon pass · Karma plan · hub child-rendering plan · giveaway plan · competitive-positioning north-star · 3 dashboard refreshes | #1323 · #1330 · #1347 · #1348 · #1352 · #1335 · #1336 · #1339 | routine + planning |

**Roughly 1/11 planned slices executed (D1 fishing follow-ups)** — the recurring "buffer becomes the band"
shape, this time dominated by the unplanned new-subsystem wave and the owner-directed card engine. (This is
exactly the pattern the band-#1320 §5 idea — the band-queue hit-rate metric — proposes to *measure*.)

## 3. Reconciled / fixed + control-plane

- **Ledger:** added the band #1322–#1352 work as **eight grouped entries**, trimmed Recently-shipped back
  to 20 (moved #1276-band · #1235-band · #1234-band · #1238-band · #1244-band · #1247-band · #1236-band ·
  #1215-band to [`current-state-archive.md`](../current-state-archive.md), newest-first via
  `trim_recently_shipped.py --apply`), reset the marker **#1320 → #1352**, and bumped the `Last updated:`
  stamp + the S4-sector snapshot + the top-of-file sector table.
- **Docs:** `check_docs.py --strict` and `check_current_state_ledger.py --strict` green at pass open
  (only the benign 27-merge newest lag, which this pass records); re-ran after edits.
- **Control-plane (Q-0135):** `check_loop_health.py` **SKIP** in this container (no `gh`/token). Manual
  fallback per the routine: the trigger issue **#1353 author is `menno420`** (a real-user login) ⇒
  **`ROUTINE_PAT` is set and the loop self-fires** — matches the canonical Control-plane state table; no
  drift to correct (the bullet is a pure pointer by design).
- **Dashboard export:** regenerated `dashboard/data/dashboard.json` (Q-0167 cadence half).

## 4. The next band (depth to #1380)

**Depth check: well over the 30-slice cadence threshold, so NO `⚠️ PLAN-BACKLOG-THIN` flag.** Most of the
band-#1320 queue carries forward intact (only D1 fishing follow-ups executed), and the band *added*
buildable lanes: four new subsystems (farm/karma/casino/treasury) each with obvious follow-ups, the
**card-render engine** with a clear card roadmap, and the **giveaway** + **hub child-rendering** plans now
written and ready to build. **Honest caveat (carried, unchanged):** the *cleanly-ungated self-merge* subset
is thinner than the headline — Project Moon's runtime build and the AI-nav / procedures→skills batches are
runtime/review-gated, so an empty *autonomous* fire should prefer a substantial review-gated lane or promote
a fresh idea → plan → build (Q-0172) over a marginal guard.

| Slice | Lane | Gate | Notes |
|---|---|---|---|
| A1 | **Project Moon runtime PR 1 — extract the `KnowledgeDomain` seam** | review-gated | Generalise the BTD6 stack's seam (data/fact-store/resolver/grounding) without behaviour change, byte-identical for BTD6. [plan](project-moon-knowledge-domain-plan-2026-06-21.md) §3–4. |
| A2 | **Project Moon — first domain ingest (one game)** | `plan-first` | After the seam: a first Project Moon domain's data + vocabulary + grounding, the first usable increment. |
| B1 | **Native giveaway system PR 1** | `plan-first` | The plan landed (#1348); build the giveaway create/enter/draw loop on the audited service+migration pattern. [plan](giveaway-system-plan-2026-06-23.md). |
| B2 | **Hub child-rendering consistency PR 1** | `plan-first` | The plan landed (#1347); normalise child-panel rendering + placement coherence across hubs. [plan](hub-child-rendering-and-placement-2026-06-23.md). |
| C1 | **Card-render engine PR 2+** | `plan-first` | The engine + profile card landed (#1349); roll the themeable card out to the next surfaces (economy/level/fishdex cards). [vision](../ideas/visual-card-engine-vision-2026-06-23.md). |
| C2 | **botsite React-SPA migration PR 2+** | `plan-first` | PR 1 landed (#1305); continue migrating the live bot-site onto the React app. [plan](botsite-react-spa-migration-plan-2026-06-20.md). |
| C3 | **Consistency-linter AI-nav PR 1** | `plan-first` | [plan](ai-panel-inplace-navigation-plan-2026-06-19.md); clears the `views/ai/` `edit_in_place` findings, then graduates the rule. Runtime/Q-0086. |
| D1 | **New-subsystem follow-ups** (farm / karma / casino / treasury) | `plan-first` | Each landed subsystem (#1328/#1332/#1333/#1334) has obvious depth — more games at the casino table, karma leaderboards, treasury sinks/payouts, farm upgrades. |
| D2 | **Fishing minigame further slices** | `plan-first` | Bait/boat/weather shipped (#1329–#1342); the design doc has more (fishdex depth, events). [plan](fishing-minigame-design-2026-06-22.md). |
| D3 | **Reconcile open-PR staleness classifier** (build the band-#1290 Q-0089 idea) | `ready` | Add machine help to the Q-0125 disposition step. [idea](../ideas/reconcile-open-pr-staleness-classifier-2026-06-22.md). |
| E1 | **procedures→skills Batch 2** | `plan-first` | [plan](procedures-to-skills-conversion-plan-2026-06-17.md); session enders → `/session-close`. Edits CLAUDE.md → review-gated. |
| E2 | **Role-management / reaction-roles continuation** | owner-paced | Reaction-roles web builder (Surface A) stays gated; Carl-bot-parity arc is otherwise mature. |

Gated/owner-paced (not in the buildable count): reaction-roles web builder (Surface A, control-API write +
security review) · creature-game PvP balance + art (Q-0187) · website rollout (provision `botsite/` +
submissions DB, domain cutover) · feedback-board PR 1 (owner dashboard auth) · AI-ticket build (Q-0183, own
session) · dashboard writes / control-API (security review) · Project Moon later phases (per-game
data-sourcing, owner-paced) · Discord 2026 gambling-headwind review on casino-heavy surfaces (#1333).

## 5. The idea + the previous-pass review + the system improvement

**💡 New idea (Q-0089):** *new-subsystem follow-up backlog auto-tracker* — see
[`docs/ideas/new-subsystem-followup-tracker-2026-06-23.md`](../ideas/new-subsystem-followup-tracker-2026-06-23.md).
This band stood up **four** brand-new subsystems in a single arc (farm, karma, casino, treasury), each with
obvious follow-up depth — but those follow-ups live only in scattered session-card prose and this pass's §4
queue, so they are easy to lose between bands. A tiny `scripts/new_subsystem.py`-adjacent convention (a
`## Follow-ups` stub written into each new subsystem's folio at creation, surfaced by a checker) would turn
"new subsystem shipped" into a self-maintaining follow-up backlog the dispatch routine can pull from — so a
new game's depth gets built, not orphaned.

**⟲ Previous-pass review (Q-0102):** the band-#1320 pass was clean — correct open-PR disposition (both opens
minutes-old and left to auto-merge), accurate scorecard, and it *introduced* the band-queue hit-rate metric
idea to measure the very "buffer-became-band" gap it kept observing. That was the right instinct. The thing
it (and this pass) still can't escape: the §4 forward queue keeps over-indexing on long-horizon review-gated
runtime lanes (Project Moon, AI-nav) while the *actual* bands are dominated by unplanned, owner-directed,
or buffer work. The band-#1320 idea names the fix (measure it); this pass's idea complements it (capture the
*buildable* follow-ups the bands actually produce, so the queue is fed from real shipped depth rather than
aspirational runtime initiatives).

**🔧 System improvement:** the trim half of this ritual is now fully mechanical (`trim_recently_shipped.py
--apply` moved the oldest 8 bullets and recomputed the floor pointer in one call, verified green) — the
band-#1320 pass had to reason about which bullets to move; this pass did not. The remaining manual edges are
the *grouping* of new merges into themed entries and the *prose* of the §4 queue. The new-subsystem
follow-up tracker idea above chips at the second: if each shipped subsystem auto-declares its follow-ups,
the §4 queue stops being hand-authored aspiration and becomes an aggregation of real, shipped-from depth.
