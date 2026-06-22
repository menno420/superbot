# Reconciliation pass — 2026-06-22 · the band-#1320 Q-0107 cadence pass

> **Status:** `plan` — the docs-only review + planning pass for the band that crossed **#1320**
> (cadence = every **30th** merged PR per Q-0134; `#1320 = 30 × 44`; previous cadence pass
> [the band-#1290 pass](reconciliation-pass-2026-06-22-band1290.md), now `historical`).
> Triggered by the auto-opened `reconcile` issue **#1321**
> (`.github/workflows/reconciliation-trigger.yml`) — the **nineteenth** consecutive real cadence fire
> and live proof the loop self-fires: #1321 was authored by **`menno420`** (the `ROUTINE_PAT` owner),
> not `github-actions[bot]`.
> Sections: §1 verified state + open-PR disposition · §2 band scorecard · §3 pruned/fixed + control-plane
> · §4 the next band · §5 the idea + previous-pass review + the system improvement.
> Reset target: marker → **#1320**.

---

## 1. Verified state at this pass (against git log + live GitHub)

**Merged since the band-#1290 pass (band #1294–#1320; #1292 = that pass's trigger, #1293 = the pass PR
itself).** The headline is a **brand-new fishing minigame** stood up end-to-end in one arc (design sim →
4 build PRs → menu), alongside **role-management enhancements**, a **botsite React-SPA migration
foundation**, **help-surface slimming + a reachability CI guard**, **BTD6 answerability** work, a
**dependency-bump wave**, and **CI/ledger/tool-pin hygiene**. As in nearly every prior band, the planned
band-#1290 queue (A1–E3) mostly carried forward untouched — the buffer became the band (the fishing arc
was not in the queue at all). Only the **botsite React PR 1** (C1, #1305) and part of **E2 Help-menu
regrouping** (#1294/#1297) came from the plan.

**Open PRs at pass time (Q-0125 disposition):**
- **#1318** — `feat(btd6): add validated XP-per-round data (round_xp.json)`. A fresh (created ~10 min
  before this pass) `claude/*` data PR; verified-against-source formula + tests. **Active in-flight —
  left to its own auto-merge.** Not stale, not redundant.
- **#1319** — `Retire the needs-hermes-review label + merge gate (Q-0197)`. An owner-authored, substantial
  policy PR (created minutes before this pass) that retires the `needs-hermes-review` carve-out across the
  workflows + docs and updates the very references this pass touches. **Active in-flight, owner-directed —
  left to its own auto-merge.** *Reconciliation note:* this pass reconciles against current `main`, where
  `needs-hermes-review` still exists, so its references in `current-state.md`/`S3` are **intentionally left
  as-is**; #1319 updates them itself, and the next pass reconciles whichever lands.

No stale or redundant open PRs to close this pass (both opens are minutes old and actively in flight).

## 2. Band scorecard (#1294–#1320)

| Theme | PRs | Source |
|---|---|---|
| **NEW fishing minigame** (design sim → cast/reel loop → trophy fight → rod ladder → menu → energy/sell rebalance) | #1296 · #1298 · #1299 · #1301 · #1303 · #1304 | unplanned (buffer-became-band) |
| **Role management** — bulk creation via preset packs + enhancements + per-role colours | #1300 · #1302 · #1306 | unplanned / owner-adjacent (E3-ish) |
| **Help surface** — remove redundant "All Commands/Advanced" + help-reachability CI guard | #1294 · #1297 | **planned (E2 Help-menu regrouping)** |
| **BTD6 answerability** — grounding-anchor eval guard (#704) + whole-catalog roster | #1295 · #1316 | partial (P1-1 lineage) |
| **botsite React-SPA migration PR 1** — buildable data-fed React foundation | #1305 | **planned (C1)** |
| **CI / ledger / tool-pin hygiene** — #1279 ledger drift, design-system CI paths, ruff pin revert, stale-claim GC, tool-pin CI guard | #1308 · #1317 · #1320 | unplanned (drift-on-sight) |
| **Dependency bumps + dashboard refresh** | #1307 · #1309 · #1311 · #1312 · #1313 · #1314 · #1315 | routine (Dependabot + Q-0167) |

**Roughly 2/11 planned slices executed (C1 + the E2 help leg)** — the recurring "buffer becomes the band"
shape, this time dominated by the unplanned fishing arc. (This is exactly the pattern the §5 Q-0089 idea
proposes to *measure*.)

## 3. Reconciled / fixed + control-plane

- **Ledger:** added the band #1294–#1320 work as **seven grouped entries**, trimmed Recently-shipped back
  to 20 (moved #1208-band · #1226-band · #1211-band · #1210 · #1203-band · #1209-band · #1183-band to
  [`current-state-archive.md`](../current-state-archive.md), newest-first), reset the marker **#1291 →
  #1320**, and bumped the `Last updated:` stamp + the S4-sector snapshot + the top-of-file sector table.
- **Docs:** `check_docs.py --strict` and `check_current_state_ledger.py --strict` green at pass open
  (only the benign 23-merge newest lag, which this pass records); re-ran after edits.
- **Control-plane (Q-0135):** `check_loop_health.py` **SKIP** in this container (no `gh`/token). Manual
  fallback per the routine: the trigger issue **#1321 author is `menno420`** (a real-user login) ⇒
  **`ROUTINE_PAT` is set and the loop self-fires** — matches the canonical Control-plane state table; no
  drift to correct (the bullet is a pure pointer by design).
- **Dashboard export:** regenerated `dashboard/data/dashboard.json` (Q-0167 cadence half).

## 4. The next band (depth to #1350)

**Depth check: well over the 30-slice cadence threshold, so NO `⚠️ PLAN-BACKLOG-THIN` flag.** Most of the
band-#1290 queue carries forward intact (only C1 + the E2 help leg executed), and the band *added*
buildable lanes: a now-shipped **fishing minigame** with obvious follow-ups, **role-management**
continuation, and the **botsite React migration** with PR 1 landed (PR 2+ open). **Honest caveat
(carried, unchanged):** the *cleanly-ungated self-merge* subset is thinner than the headline — Project
Moon's runtime build and the AI-nav / procedures→skills batches are runtime, so an empty *autonomous* fire
should prefer a substantial review-gated lane or promote a fresh idea → plan → build (Q-0172) over a
marginal guard. *(If #1319 lands, the `needs-hermes-review` carve-out is retired — Q-0197 — and that gate
language collapses to the plain `do-not-automerge` hold; re-read the live policy before relying on it.)*

| Slice | Lane | Gate | Notes |
|---|---|---|---|
| A1 | **Project Moon runtime PR 1 — extract the `KnowledgeDomain` seam** | review-gated | Generalise the BTD6 stack's seam (data/fact-store/resolver/grounding) without behaviour change, byte-identical for BTD6. [plan](project-moon-knowledge-domain-plan-2026-06-21.md) §3–4. |
| A2 | **Project Moon — first domain ingest (one game)** | `plan-first` | After the seam: a first Project Moon domain's data + vocabulary + grounding, the first usable increment. |
| B1 | **Creature-game — leaderboards UI + ranked** | `plan-first` | The #1244 provider exists; surface it (Explore-hub panel) + a ranked tier. Runtime. |
| C1 | **botsite React-SPA migration PR 2+** | `plan-first` | PR 1 landed (#1305); continue migrating the live bot-site onto the React app. [plan](botsite-react-spa-migration-plan-2026-06-20.md). |
| C2 | **Consistency-linter AI-nav PR 1** | `plan-first` | [plan](ai-panel-inplace-navigation-plan-2026-06-19.md); clears the `views/ai/` `edit_in_place` findings, then graduates the rule. Runtime/Q-0086. |
| C3 | **procedures→skills Batch 2** | `plan-first` | [plan](procedures-to-skills-conversion-plan-2026-06-17.md); session enders → `/session-close`. Edits CLAUDE.md → review-gated. |
| D1 | **Fishing minigame follow-ups** | `plan-first` | The minigame shipped (#1296–#1304); the design doc has further slices (bait, boat, fishdex depth). [plan](fishing-minigame-design-2026-06-22.md). |
| D2 | **Reconcile open-PR staleness classifier** (build the band-#1290 Q-0089 idea) | `ready` | Add machine help to the Q-0125 disposition step. [idea](../ideas/reconcile-open-pr-staleness-classifier-2026-06-22.md). |
| E1 | **Mining grid-redesign follow-ups** | `plan-first` | The grid world (#1281/#1282) opened the hub-redesign plan's remaining slices. [plan](mining-hub-redesign-2026-06-15.md). |
| E2 | **Role-management continuation** | owner-paced | Bulk creation + colours shipped (#1300/#1302/#1306); reaction-roles web builder (Surface A) stays gated. |
| E3 | **Pokétwo/MusicBot mapped features** | `plan-first` | From the #1180 feature-mapping plan, as the owner greenlights rows (music respects the #1185 legal findings). |

Gated/owner-paced (not in the buildable count): reaction-roles web builder (Surface A, control-API write +
security review) · creature-game PvP balance + art (Q-0187) · website rollout (provision `botsite/` +
submissions DB, domain cutover) · feedback-board PR 1 (owner dashboard auth) · AI-ticket build (Q-0183, own
session) · dashboard writes / control-API (security review) · Project Moon later phases (per-game
data-sourcing, owner-paced).

## 5. The idea + the previous-pass review + the system improvement

**💡 New idea (Q-0089):** *band-queue hit-rate metric* — see
[`docs/ideas/band-queue-hit-rate-metric-2026-06-22.md`](../ideas/band-queue-hit-rate-metric-2026-06-22.md).
Every pass plans a ~30-slice next band, and almost every subsequent pass records "the buffer became the
band" in prose only — no number. Extend `band_pr_status.py` with a `--queue-hit-rate` mode (planned slices
shipped ÷ planned, + count of unplanned PRs) and track that one line per pass, so the owner gets
*data-driven* evidence of whether deep forward-planning predicts reality or should go lighter/reactive.

**⟲ Previous-pass review (Q-0102):** the band-#1290 pass was clean and its open-PR disposition was correct
for its moment (zero stale opens). Its §4 queue, though, again over-indexed on long-horizon review-gated
lanes (Project Moon, AI-nav) — and the band that followed ignored almost all of it in favour of an
unplanned fishing minigame. That's not a *fault* of the pass (owner-steered work rightly outranks the
queue, Q-0124), but it is the same prediction gap every recent pass quietly logs. The honest improvement is
to **stop treating low queue-hit-rate as a surprise and start measuring it** — which is exactly the §5
idea, born from noticing the band-#1290 pass make the same observation the band-#1260 pass made.

**🔧 System improvement:** the reconciliation routine now has machine help for *ledger* reconciliation
(`band_pr_status.py --themes`, `trim_recently_shipped.py --apply`) and a *proposed* detector for *open-PR*
reconciliation (the staleness-classifier idea), but **nothing measures the planning half** — whether the
next-band queue it produces is worth the effort. The queue-hit-rate metric closes that gap: it makes the
loop self-audit its own most expensive ritual (the ~30-slice forward plan) with one cheap, disposable line.
