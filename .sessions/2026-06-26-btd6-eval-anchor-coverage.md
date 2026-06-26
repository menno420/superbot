# Session — 2026-06-26 · BTD6 eval-anchor coverage + distractor negative-anchor guard

> **Status:** `complete` — ready to merge (Q-0133). Run type: routine · dispatch.

## What this run did

Empty-fire dispatch → advanced the **S2 BTD6 ▶ "Anchor-tooling follow-ons (offline, self-mergeable)"**
lane the #1458/#1460 anchor runs explicitly teed up. Both follow-ons shipped as additive, offline,
test-layer slices on `tests/evals/test_btd6_grounding_anchors.py` (no runtime / `disbot/` change, no DB,
no AI hot-path).

**PR #1466 — anchor coverage guard + distractor negative-anchor guard.**

1. **Eval-anchor coverage guard.** Inventories every **significant (≥ $1,000)** numeric token across each
   BTD6 case's rubrics + fixtures and asserts each is either **anchored** (an `Anchor`/`FixtureAnchor`
   re-derives it) or on a curated `_UNANCHORED_ALLOWLIST` of **distractors + user-inputs** (each with a
   one-line reason). A future rubric/fixture edit that introduces a new dollar/HP *truth* without an
   anchor now fails CI instead of leaving an un-guarded "truth" the golden set grades against. The
   ≥ $1,000 significance threshold drops structural noise (round numbers, boss tiers, crosspath digits,
   the "6" in BTD6) so the report isn't noisy — the #1458 "allowlisting distractors + user-inputs"
   requirement. BTD6 case scope is derived from the case-id convention (a new BTD6 case is auto-in-scope).
   Includes a no-dead-entries guard (every allowlisted number must still be a present, *unanchored*
   significant number) + a non-empty-scope guard.
2. **Distractor negative-anchor guard.** `DISTRACTOR_NEGATIVE_ANCHORS` pins each documented distractor
   ($71,315.20 BUG-0004, $107,164.60 BUG-0010, the five standard-Lych-as-elite HP values) **distinct
   from the truth(s) its case asserts** — so a data re-seed can't silently collapse a case's
   discrimination (the rejected "wrong" answer coinciding with the right one). For the one distractor
   that IS a derivable wrong computation ($107,164.60 = the standard-set range given as the ABR answer),
   a `derive_alias` pins it to `round_cash(25,83,'default')` so the cross-roundset confusion stays
   exactly reproducible. Plus a rubric-presence guard (the distractor must still be rejected by the
   rubric) and a real-case guard.

Curation note: $71,315.20 is **not** cleanly derivable (the true from-round-1 cumulative is $70,665.20) —
a genuine hallucination, so it carries no alias and is guarded only by distinctness from both case
truths; only $107,164.60 (right calc, wrong roundset) earns an alias.

## Verification
- New tests: +23 (file 62 → 85 anchor tests). `check_quality.py --full` GREEN (**12566 passed**, 48
  skipped, 2 xfailed). `check_architecture --mode strict` exit 0 (pre-existing baseview WARNs only,
  unrelated). `--check-only` all green (black/isort/ruff/check_docs/check_consistency).
- **Non-vacuity proven:** emptying the allowlist makes the coverage guard flag the Lych distractors;
  forcing a truth == distractor makes the distinctness guard fire — both verified to fail against the
  drift they exist to catch (the guard-the-guard discipline already in this file).

## 💡 Session idea (Q-0089)
*A negative-anchor for the **un-anchored user-input** figures too.* Today the coverage allowlist marks
user-supplied numbers (20000 / 26932 / 5443) as "input, not a data-derived truth" — but nothing pins that
a future dataset change can't make one of those *accidentally* become a derivable figure that then reads
as a truth (the mirror of the distractor risk). A tiny extension — assert each allowlisted *user-input*
stays NOT reproducible from any standard accessor for its case's rounds — would close the symmetric gap.
Low value today (inputs are arbitrary), but it generalises the "a re-seed can't silently change what a
number *means*" invariant the negative anchors started. Genuinely tied to today's allowlist edit, not
filler; recorded here, not promoted (the distractor side was the higher-value half and is done).

## ⟲ Previous-session review (Q-0102)
The previous run (2026-06-25 Project Moon Sinner literary origins) did its best work in **honest
scoping**: it built only the cleanly-offline Slice A and explicitly deferred the gated AI-grounding PR 2
rather than half-forcing it — and its Q-0102 note nailed a real, recurring cost: an autonomous run burns
orient-time discovering which ▶ Next startables are offline vs. needs-live-bot, because the per-sector
files don't tag them. **This run is more evidence for that note:** I again spelunked S1 (setup PR 3b,
Project Moon PR 2, botsite cutover all needs-live-bot/owner-gated) before finding S2's *explicitly
tagged* "(offline, self-mergeable)" lane — which is exactly why I could move fast on it. **System
improvement it confirms:** S2 already uses the `(offline, self-mergeable)` tag on its ▶ items and it
worked perfectly as a dispatch signal; the cheap, high-leverage move is to **propagate that same tag to
every ▶ Next startable in the S1/S3/S5 sector files** (and have `dispatch_menu.py --unattended` read it
directly). The prior run flagged it; this run is the second occurrence — per its own "worth a router
DISCUSS block if it recurs once more" bar, that threshold is now met. Left as a routed observation here
(not a unilateral CLAUDE.md/router edit in an unattended run).

## Doc audit (Q-0104)
S2 sector ▶ anchor-tooling-follow-ons bullet de-staled to "both shipped 2026-06-26 (PR #1466)". Ledger:
`check_current_state_ledger --strict` reports 22 merges newer than the #1441 marker — **benign
newest-merge lag** (Q-0166; recon due at #1470, the docs-reconciliation routine's lane, not a manual
dispatch's — Q-0124), no older-than-marker drift. `check_docs --strict` + `check_consistency` green. No
owner decision this run (executes the S2 P1-1 lane the prior anchor runs queued). Claim file deleted at
close.

## 📤 Run report
- **Run type:** routine · dispatch
- **What shipped:** **PR #1466** — BTD6 eval-anchor **coverage guard** (every ≥ $1,000 rubric/fixture
  number anchored-or-allowlisted, distractors + user-inputs documented) + **distractor negative-anchor
  guard** (each documented distractor pinned distinct from its case's truths; the one derivable
  distractor aliased to its wrong-roundset computation); +23 tests; S2 sector de-staled.
- **⚑ Self-initiated:** none — this is the S2 BTD6 ▶ "Anchor-tooling follow-ons" lane the #1458/#1460
  anchor runs explicitly queued; advanced via an empty-fire dispatch.
- **⚑ Owner-decisions:** none.
- **⚑ Owner-manual-steps:** none (test-only; no data/seed step; merge auto-deploys nothing runtime).
- **Bug-book:** none fixed (BUG-0009 newest-towers data-gated, BUG-0011 needs VPS repro, BUG-0019 #1
  awaits an owner behavior decision — all stay OPEN).
