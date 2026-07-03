# 2026-07-03 — New-bot capability-audit CAPSTONE (final review + unified build plan)

> **Status:** `in-progress`
> **Branch:** `claude/bot-capability-audit-capstone-scy0zx` · **PR:** #1674
> **Session type:** capstone synthesis (Fable 5, ultracode) — the go/no-go gate between
> planning/discovery and creating the new repo, per `FINAL-REVIEW-HANDOFF.md`.

## What happened

Delivered both capstone artifacts into
`docs/analysis/rebuild-discovery/new-bot-capability-audit/findings/`:

1. **`FINAL-REVIEW.md` — verdict: GO-with-amendments.** Measured all-43 tier-1/2 fit:
   **1,635 units · 63.8% as-written → 85.1% with amendments** (median 88.9%; 36/43 ≥ 80%);
   the consolidated amendment list canonically renumbered (G-1…G-24 + 15 riders + P-1…P-4
   provisional + a 10-item adversarially-refuted do-not-re-propose set); all five structural
   danger zones answered (stateful games = declared lifecycle + priced-in engine hatch;
   gateway = G-1 + new G-11 pipeline stages; `wait_for` wizards = pattern nearly extinct in
   source, 1 call left; scheduled loops = ManagedTaskSpec + G-9 one-shot; voice = verified
   absent, deliberate omission). Six live runtime bugs surfaced by the audit routed as
   immediate current-bot work (2 money bugs: deathmatch PvP double-settle, blackjack
   free-tournament double-pay).
2. **`NEW-BOT-BUILD-PLAN.md` — the single dependency-ordered plan.** Gates 0–1 (spec-amendment
   pass + owner ratification) → L0 kernel (K0–K10 / Lane G) → L1 core management (platform
   proves itself → operator spine → presentation foundation) → L2 economy/social → L3
   games/world (mining ports LAST as the acceptance test) → L4 knowledge/AI → L5 control
   plane; every capability with disposition, dependencies, done-definition index, and
   resolved outperform targets.

**Method:** verified lane claims against source before trusting them (Q-0120) — own re-checks
(G-9/G-10 consumers, the one remaining `bot.wait_for`, role `unique` mode, merged-spec coverage
of G-1…G-6 + facets, all lane fit arithmetic re-summed) + two workflow fleets: a 4-agent
extraction/verification pass over lanes A/B/C + Lane F's gap list (7 CONFIRMED · 1 REFUTED ·
2 PARTIAL), and — **owner-requested mid-session** — a 5-agent independent review of all 143
`docs/planning/` + 177 `docs/ideas/` files plus a rebuild doc-set consistency check
(~1.3M subagent tokens across both fleets, 0 errors).

**The independent plans review materially changed the record:** Lane E had missed the shipped
manifest spine (production-tested prior art for the rebuild's core bet), inherited ≥17 stale
`plan` badges (citing shipped fishing/mining/reaction-roles mechanics as forward builds), buried
the owner's Q-0186 Pokétwo build order, missed owner-decided Q-0184/Q-0091/Q-0213 items, and
parked Project Moon behind a foundation that already shipped. All corrections are recorded in
BUILD-PLAN §4 (binding over the raw Lane E rows they touch); doc-set freshness findings
(the design spec doesn't yet know about Gate-0; phantom "handoff §F"; stale handoff §C) are the
Gate-0 session's first edits.

## ⚑ Self-initiated

- **`scripts/check_plan_staleness.py`** (warn-first, stdlib, Q-0105 provenance + delete-clause):
  the Q-0194 friction→guard conversion for the stale-badge drift class that misled Lane E —
  3 mechanical rules (plan-with-shipped-markers, recon-band-behind-marker, idea-with-shipped-
  markers); 26 findings on first run, matching the review agents' independent lists.
- **Fixed on sight (Q-0166):** the two unambiguous recon-band mislabels
  (`reconciliation-pass-…band1530/band1560` → `historical`); made the two new findings docs
  link-reachable from `findings/README.md`.
- The owner requested the plans review mid-session; the checker + badge fixes + the P-2…P-4
  future-family candidates in FINAL-REVIEW §3.3 are the self-initiated conversions of its output.

## 💡 Session idea

**Rebuild amendment registry** —
[`docs/ideas/rebuild-amendment-registry-2026-07-03.md`](../docs/ideas/rebuild-amendment-registry-2026-07-03.md):
one committed file as the sole minting authority for G-/R-/P-/refuted amendment IDs. Genuine
belief, empirically motivated: Lanes B, C, and D **independently minted colliding G-numbers**
(three different "G-7"s) and Lane B's sub-agents reused "G-14…G-20" for different refuted
proposals each — this capstone reconciled it by hand once; the registry makes that a
never-again class (the rebuild's namespace discipline applied to its own meta-artifacts).
Surfaced independently by the doc-set reviewer; endorsed, shaped, filed, indexed.

## ⟲ Previous-session review

The 2026-07-02 review session (#1653/#1673, reviewing the #1649 kit finalize) was a model of the
review-then-fix pattern: it verified every headline claim independently, fixed 10 of 12 confirmed
defects **at root with regression tests**, and its "fixture-adversary" insight (happy-path
fixtures masked the misses) is durable methodology. One concrete system improvement it surfaces
in hindsight: **a deferred defect should be *placed*, not just captured.** It deferred the kit's
transaction-atomicity fix into an ideas file — correct scope discipline — but nothing attached it
to the gate it blocks; this session's ideas sweep independently found that same fix is a hard
prerequisite for the Phase-2.5 cold-start A/B (BUILD-PLAN I-13). When a review defers a defect,
the capture should name the queue/gate item it blocks so the dependency is visible where the
gate is read, not two hops away in an ideas file.

## 📊 Telemetry

- PR #1674 · 2 capstone deliverables + 1 checker + 1 idea file + 2 drift fixes + this log
- Fleets: 9 agents across 2 workflows (~1.3M subagent tokens, 0 errors); all 4 lane extracts
  adversarially self-corrected by their source lanes before consumption
- Verdict inputs: 43 subsystems · 1,635 units · 4 lane files (10.4k lines) read/extracted in full
- CI: born-red gate held as designed through the session (verified via job logs: only
  `check_session_gate` red); flip-to-complete is this PR's final commit

## Doc audit (Q-0104)

`check_docs --strict` green · `check_current_state_ledger --strict` green (this PR is unmerged —
its ledger entry is next session's benign newest-merge lag, per Q-0166 carve-out) ·
new idea file indexed in `docs/ideas/README.md` · both deliverables linked from
`findings/README.md` (reachability) · no new owner decisions taken (the verdict routes decisions
*to* the owner: Gate-0 approval checklist in FINAL-REVIEW §7, G-22/R-12/P-1 embedded decisions,
I-10 voice router-Q) · claim file deleted at close.
