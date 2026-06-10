# 2026-06-10 — Verification, docs cleanup, #646/#647 reconciliation, plan consolidation

PR **#648**. The owner asked for a broad verification + repo-memory cleanup: verify
the two open Codex untapped-mapping PRs, fix stale routing, archive/mark completed
plans, and leave **one** up-to-date executable plan.

## Arc

1. **Verified live state** — only #646/#647 open (both Codex, docs-only, base
   `ed62697`, disjoint files); #584 (PR14 hub) merged 2026-06-08; #638–#645 all
   merged 2026-06-09/10. Source-verified the maps' claims with parallel Explore
   agents: **essentially all confirmed** (RS01–RS18, DT01–DT15; count nits only).
2. **Merged #646 then #647.** Direct merge was blocked (required `code-quality`
   check red — each PR's single violation was its own new map being a
   `check_docs --strict` reachability **orphan**). Fix: one link commit per PR
   branch (646's map ← roadmap; 647's map ← standard §7.1 — different files, so no
   cross-PR conflict), CI green in seconds, merged both. No red-main window.
3. **Queue-truth fixes** (17 files): tracker header (PR14 "queued" → shipped #584),
   roadmap (PR14/campaign/hedges/adaptive-horizon conflict), current-state
   (▶ rewrite, stale Next-candidates bullet, missing Recently-shipped bullets
   #638/#641/#643–#647), orientation + implementation-plan "PR1–PR9 shipped" tails,
   PR14-plan Decision-1 reversal note, adaptive plan P1B→complete(#632), A/B report
   + untapped-map mapping-time annotations, standard §2.4 update + §7.1 extension
   (campaign complete, merge-gate record, Q-A/Q-B routing), help/settings audits +
   settings-customization-roadmap "queued as Lane 7/8" → shipped #640/#642.
4. **One live queue:** new `docs/planning/consolidated-implementation-plan-2026-06-10.md`
   (Batches 1–10 with files/tests/risks/rollback/stop conditions; §6 carries the
   06-09 §5 gated tail item-by-item). Re-badged `historical`: the completed
   multi-lane scoreboard (all 8 lanes shipped) + the 06-09 consolidated plan.
5. **Router §31:** Q-0071 (cross-domain transaction owner — blocks Batch 7),
   Q-0072 (mining next slice), Q-0073 (`setlogchannel` ownership), Q-0074 (Admin
   tier vs routes). Q-A02/Q-A03/Q-B02 held at map defaults (recorded in §7.1 +
   plan §7) — kept the router decision-grade rather than routing all five.

## Open-PR reconciliation notes

- #646/#647 were complementary, non-conflicting, and **accurate**: 26/28 spot-verified
  claims exact; corrections worth recording: help render tests = **23** (map said 28),
  invariants dir = **38** files (map said 39), `DOMAIN_CONFIG_SUBSYSTEMS` is not
  literally labeled "temporary" (its comment does say Phase 2 replaces it).
- **FIND-DT01 split verdict:** the server-management tracker's *header* was stale but
  its *body* already recorded PR14 shipped — the Codex map over-claimed "tracker
  queues PR14"; current-state/roadmap were genuinely stale. Lesson: check a tracker's
  body before trusting a staleness claim about it.
- The maps' "zero open PRs at mapping time" lines were mapping-time facts (the open
  set was the two PRs themselves) — annotated, not rewritten.
- The 06-09 consolidated plan's SRV-2 row ("then PR14 hub") was stale **at write
  time** (#584 had merged the day before) — the drift propagated from the roadmap
  into a fresh plan. One-fact-one-home matters.

## Docs cleanup summary

Kept-active / updated / annotated / re-badged ledger:
`consolidated-implementation-plan-2026-06-10.md` **§4** (one home; not restated here).

## Verification run

- `python3.10 scripts/check_docs.py --strict` — ✓ (156 docs; ratchet 16/16; ran
  green at every step: each PR branch, post-merge main, and this branch).
- `python3.10 scripts/check_quality.py --full` + `check_architecture.py --mode strict`
  — run at session end (docs-only change set); results in the PR body.
- Stale-language sweep: `grep -rn "remain queued\|queued as scoreboard\|PR14 remain" docs/`
  → only historical/evidence contexts remain (router decision records, annotated
  audit bodies, the tracker's own correction note).

## Context delta

- **Needed but not pointed to:** nothing major — the orientation route held. What the
  route *can't* give: live CI/check-run state on open PRs decided the whole merge
  strategy (required-check red on both Codex PRs); "verify open PRs live" should be
  read as "including their check runs", which no doc says explicitly.
- **Pointed to but didn't need:** the BTD6 decode-tail docs (the maps' BTD6 findings
  were routing-only); most of the adaptive plan's body (only the three status lines
  mattered).
- **Discovered by hand:** (1) GitHub blocks MCP merges on the required `code-quality`
  check — the fix is a green-making commit *on the PR branch itself*, and putting the
  two PRs' link commits in **different files** avoids any cross-PR conflict without
  update-branch; (2) the check_docs reachability BFS traverses `historical` docs'
  outbound links, so re-badging strands nothing; (3) badge must sit in the first 12
  lines — preamble notes go *below* the badge line.
- **Decisions made alone:** merge-vs-absorb for #646/#647 (merged — owner had
  pre-sanctioned determining it; provenance preserved); routing only 4 of the maps'
  7+ question candidates to the router (the rest held at defaults with recorded
  dispositions); recommending C (workshop-workflow boundary) for Q-0072; Batch 5
  (P1C) ordered *before* the Help seam (three docs pin Help-consumes-projection to
  the P1C lane — the prompt's draft order had it reversed).
- **Flagged for maintainer:** Q-0071/Q-0072 genuinely block Batch 7 — one
  structured-choices round closes them; the #633 refresh workflow still awaits its
  **first real dispatch** (Actions tab); HLT-2 production live-tests remain owed;
  both AI model loops (#634/#639) still await the prod check.
- **One change that would have helped:** a scout-verdict spot-check rule — one
  Explore agent called the stale tracker header "ALREADY-CORRECT" (it had read the
  correct body and glossed the header); the Codex map made the inverse error.
  Cross-checking the two against each other + the file settled it. Already covered
  by the journal's "verify cross-agent output" rule — this session adds: *when two
  agents disagree, read the disputed lines yourself; when they agree, still spot-check
  one load-bearing claim.*
