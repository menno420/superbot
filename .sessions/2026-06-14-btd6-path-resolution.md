# 2026-06-14 — P1-1 Layer A: BTD6 path/line-aware resolution (absence-claim trigger removal)

> **Status:** `complete` — PR **#855** ready; born-red card flipped as the deliberate final step
> (Q-0133) once code + tests + close-out docs were all in.

**PR:** **#855** — the first concrete, fully-completable slice of **P1-1** (the standing #1
priority): the BTD6 absence-claim guard's **Layer A** (the design's Recommendation #1, "ship
Layer A first"). Retrieval root-cause fix; no guard, no AI keys, deterministically verifiable.

## Context

Autonomous session ("start"). Oriented (`git fetch` first per the journal's hardest rule — clone
was current at #853; no concurrent `claude/*` PR open, no duplication risk). The P0 spine is
complete and P1-2 shipped (#843), so the band-#840 queue's slot 2 — **P1-1** — was the standing
priority. P1-1 has a creds-gated half (the live eval matrix) and a contained, non-gated half: the
**absence-claim guard's Layer A**, which the design doc explicitly recommends shipping first and
separately, "verifiable live the same way the round/map/mode tools were."

Re-verified the design's diagnosis was still current (it insists "run, don't assume"):
`resolve_upgrade("bomb shooter middle path")` → `none`. So path/line phrasing grounded **nothing**
and the model could confabulate "that path has no MOAB bonus" — a *retrieval* gap (the
+15/+30/+99 vs MOAB-Class data is committed and reachable, just unqueried), not extraction.

## What shipped

1. `btd6_upgrade_service.resolve_path_reference(query) -> PathReference | None` — detects a
   `<tower> <top|middle|bottom> path` reference (direction synonyms top/upper · middle/mid/center/
   centre/central · bottom/bot/lower) and returns that path's five tier identities in order.
   **Conservative (design §5):** requires a resolvable tower **and** the literal `path` token
   adjacent to the direction, so "top tier" / "bottom line" / a bare "middle path" never fire.
2. `btd6_upgrade_detail_service.path_grounding_for_query(query)` — a header line naming **every
   tier on the path** ("these are every tier; do not claim the path lacks a tier/effect listed
   here" — the direct absence antidote) + each tier's full grounding; tiers the user named outright
   are skipped (Pass 3c grounds those).
3. `btd6_context_service.build` **Pass 3f** wires it in, isolated like its siblings (Pass 3d, the
   parent-tower enrichment, was the §4.1 *mechanism 2*; this is the §4.1 path/line bullet).
4. `tests/unit/services/test_btd6_path_resolution.py` — 22 cases: resolution, direction synonyms,
   the tower/keyword requirements, the conservatism negatives, the MOAB grounding (numeric +15/+99
   verbatim), and the async `build()` integration (+ a plain-tower negative).

## Verification

- Deterministic + offline (no Postgres, no AI keys — the design verified Layer A this exact way).
- `check_quality --full` green (**9579 passed**, 37 skipped); `check_architecture --mode strict`
  **0 errors**; `check_docs --strict` + `check_current_state_ledger --strict` green.
- The related BTD6 suites (upgrade service/detail, context grounding, paragon income) stay green
  (158 passed) — no regression.

## Context delta (reflection)

- **Needed but not pointed to:** the design doc `docs/btd6/btd6-absence-claim-guard-design.md` is
  *not* on the standard orientation route (current-state → AGENT_ORIENTATION) — I reached it by
  grepping "absence-claim" off the btd6 readiness map's row reference. It's in the agent-context
  index (`docs/agent/index.yml` btd6 pack) but a P1-1 session keying off current-state/roadmap
  wouldn't be routed to it. Worth a one-line pointer from the hardening roadmap §P1-1 (done this
  session — §P1-1 now links the design doc by name).
- **Pointed to but didn't need:** the CodeGraph symbol tools — this was a contained change in 3
  known files, so the PreToolUse `context_map` + grep + targeted Read carried it, exactly as
  CLAUDE.md says ("contained change → context_map + grep is usually faster than the graph"). The
  graph would have been overhead.
- **Discovered by hand:** that Pass 3d **already cites this design doc §4.1 as "Layer A /
  mechanism 2"** (so half of Layer A shipped earlier and the doc's status banner hadn't said so) —
  found only by reading `build()`. Also the `_PATH_LABEL` / `_cap` helpers in the detail service,
  and that the registry is towers-only (heroes have no `upgrade_paths`), which bounds path
  references to towers naturally.

## Decisions made alone

- **Layer A only, not Layer B.** Scoped to the deterministic, verifiable, non-gated retrieval half
  (the design's Rec #1). Layer B (the negative-existential *gate*, §4.3 crux) needs the review the
  doc asks for **and** the prod-creds live half — shipping it half-tested would be the "implement
  blind" the design warns against.
- **Ground the *whole* path (all five tiers), not just a named/queried tier.** The design §7 left
  this open; I chose completeness because the absence antidote *wants* the full path visible (so no
  tier can be claimed missing), and it's bounded (~18 facts, in line with the PMFC parent-tower
  enrichment's volume).
- **Precision over recall in detection** (tower + literal `path`). A reviewer might later want
  "line" added or `path`-less direction phrases ("bomb shooter top" → top path); I deliberately
  did not, to keep false fires at zero. Easy to widen if live use shows missed phrasings.
- **Reconciled a cross-lane drift:** `roadmap.md` still listed P1-2 as *future* though #843 shipped
  it — fixed it to `✅ #843` in the same edit as my P1-1 marker (no parallel `claude/*` PR open, so
  no conflict risk).

## Flagged for maintainer (weak point / unverified half)

- **The live end-to-end is unverified here** (no AI keys). Layer A is deterministic and tested —
  the path now *grounds* — but whether the model, given that grounding, actually stops confabulating
  the false "no" is the prod-check item. It should, by the identical mechanism as the round/map/mode
  reachability fixes that the owner verified live; the new grounding is correct and bounded. A
  one-line Discord check ("bomb shooter middle path — does it bonus MOABs?") would confirm.
- **Grounding volume:** a path query adds ~18 facts. Bounded and all relevant, but on the heavier
  side; if context budget ever bites, trimming to the header + the modifier lines (dropping the
  per-tier attack/ability detail) is the lever.

## 💡 Session idea (Q-0089)

**A reusable "completeness-claim" grounding primitive** —
[`docs/ideas/grounding-completeness-claim-primitive-2026-06-14.md`](../docs/ideas/grounding-completeness-claim-primitive-2026-06-14.md).
#855's path header asserts *completeness* ("these are **every** tier") deterministically; promote
that ad-hoc sentence (also used by rosters + the capabilities reply) into a primitive that emits a
**parseable completeness marker**, so the faithfulness guard can gain a completeness check beside
its value check and catch the **BUG-0009** long-list drop/add class ("which maps have water" → 64
vs 69 truth). The emit side is cheap retrieval; the guard check rides with Layer B. A genuine,
new, believed-in extension of this session's work toward the open BUG-0009 — dedup-grepped
`docs/ideas/` first (no list-answer/absence idea existed).

## ⟲ Previous-session review (Q-0102) — #849 (the born-red merge-gate, Q-0133)

I am the **first real adopter** of #849's born-red gate, so this is lived feedback, not a read.

- **Did well:** it worked exactly as designed. Creating the `in-progress` card as commit 1 opened
  PR #855 born-red, so I could push code (commit 2) and get an early CI signal **without any risk
  of a premature partial merge** — the #843 race the gate exists to kill. Flipping to `complete` as
  the final step is a clean, single, deliberate action. The mechanism is genuinely low-friction;
  dogfooding it on its own PR (#849) clearly de-risked it.
- **Missed / could've done better:** very little. The one residual is the **soft engage-when-present**
  posture — a session that simply *forgets* to add a card isn't gated at all, so protection still
  rests on the CLAUDE.md rule + Stop-hook reminder, not hard CI. #849's own entry already flags
  "tighten to airtight once routine adoption is proven," so it's a known, deliberate choice, not an
  oversight. There is no concrete improvement I'd add yet beyond gathering adoption evidence — per
  Q-0102, I'd rather say that honestly than invent filler. **System note:** the genuinely useful
  next data point is *N successful adoptions* (this is N=1, clean) — when a few more land, the
  airtight tightening (require a card on every `claude/*` PR) becomes evidence-backed.

## Grooming (Q-0015)

Advanced [`docs/ideas/ledger-checker-print-pr-subjects-2026-06-14.md`](../docs/ideas/ledger-checker-print-pr-subjects-2026-06-14.md)
from "idea" to **turn-key**: verified and recorded the exact seam — `_git_merged_pr_numbers`
already holds each PR's merge `subject` at the moment it extracts the number and discards it, so
the change is ~10 lines (memoize `{pr: subject}`, print it for missing numbers; reuse
`_MERGE_SUBJECT_RE`, no new `git` call) + one test. Indexed both the sharpened idea and the new
Q-0089 idea in the ideas README.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 (#855, on green via auto-merge once the card flipped) |
| CI-red rounds | 0 (full CI mirror green locally before the first code push; born-red gate held the merge by design, not by failure) |
| Repo-rule trips | 0 (arch 0 errors; no new known-violation entries) |
| New ideas contributed | 1 (Q-0089 — the completeness-claim primitive) |
| Ideas groomed | 1 (ledger-checker idea → turn-key) |
