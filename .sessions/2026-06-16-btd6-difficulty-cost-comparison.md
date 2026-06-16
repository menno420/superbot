# Session — BTD6 difficulty cost-comparison floor (AI §7.5)

> **Status:** `complete`

**Branch:** `claude/magical-rubin-swi7wp` · **Date:** 2026-06-16 · scheduled dispatch (no work order → advance the next plan slice)

## What I'm about to do

The live ▶ NEXT buildable plan-first lane is **the AI §7 next workflow family**. The §7.5
multi-entity comparison floor shipped its first member in #946 — *tower-vs-tower* cost comparison
(`compare_crosspath_costs` + `deterministic_cost_comparison_reply`). The §7.5 plan explicitly lists
**difficulty cost comparisons** as the next member, still unbuilt: "is a 0-4-1 desperado cheaper on
medium or impoppable?" ranks the **same** upgrade state across difficulties — a single tower, so the
#946 multi-tower builder returns `None` and the question falls through to the model, which can
mis-state which difficulty is cheaper (the BUG-0009 "grounded values, wrong assembly" class the
floor exists to own).

Plan (mirrors the #946 shape exactly, contained + test-covered):
- `btd6_data_service.compare_difficulty_costs(tower, code, difficulties)` — the §7.5 difficulty
  rank/diff primitive; prices the one upgrade state once (`crosspath_cost` already returns every
  difficulty), ranks the named difficulties ascending, fails closed (<2 distinct valid difficulties).
- `btd6_context_service.deterministic_difficulty_cost_comparison_reply` — high-precision floor:
  cost-compare cue + **exactly one** resolvable `(tower, crosspath)` (≥2 is the multi-tower builder)
  + **≥2** named difficulties; `None` otherwise. Appended to the `deterministic_btd6_list_reply`
  dispatcher (auto-wires the pre-emptive BTD6 floor).
- Tests covering the firing case, base/crosspath, 3-difficulty ranking + spread, and the negatives
  (single difficulty, two towers → multi-tower builder, no cost cue, strategy).

## ✅ Done

Shipped (PR #950, self-merge candidate on green):
- `btd6_data_service.compare_difficulty_costs(tower, code, difficulties)` — the §7.5 difficulty
  rank/diff primitive; prices the one upgrade state once, ranks named difficulties ascending,
  fails closed (<2 distinct valid). Dedups (`hard`==`chimps`), skips unknowns, never guesses.
- `btd6_context_service.deterministic_difficulty_cost_comparison_reply` + `_format_…` — the floor:
  cost-compare cue + **exactly 1** `(tower, crosspath)` candidate + **≥2** difficulties. Mutually
  exclusive with the #946 multi-tower builder on candidate count, so both ride the
  `deterministic_btd6_list_reply` dispatcher without overlap.
- 14 tests (`tests/unit/services/test_btd6_difficulty_cost_comparison.py`). `check_quality --full`
  green (9972, +14); `check_architecture --mode strict` 0 errors; `check_docs --strict` green.
- De-staled docs: AI orchestration plan §7.5 (tower ✅#946 / difficulty ✅#950 / paragon + round-range
  unbuilt) + current-state ▶ ledger entry; archived #897 to hold the recently-shipped ratchet at 20.

**§7.5 cost-comparison family (tower + difficulty) is now complete.**

## ▶ Handoff — next dispatch

The buildable `ready` queue stays thin (image-mod #941 + security tiers #929 in flight under
`needs-hermes-review`; BUG-0009 slice 3 data-gated; absence-guard Layer B creds-gated). The
remaining **AI §7.5** members are both unbuilt and the cleanest plan-first AI slices:
- **paragon degree/resource comparison** — needs a paragon-cost/resource primitive; check
  `btd6_data_service` for paragon data depth first.
- **round-range cash comparison** ("which earns more, rounds 20-40 or 40-60") — distinct from the
  single-range projection the round-cash workflow owns; keep non-overlapping by requiring **two**
  ranges. Touches the delicate, heavily-bug-fixed round-cash path — scope it carefully.
Otherwise: next AI §7 workflow family beyond §7.5, or the Hermes bug-triage `gh issue create`
write (Q-0121, plan-first).

## 💡 Session idea (Q-0089)

**A floor-builder coverage/conflict invariant for `deterministic_btd6_list_reply`.** The dispatcher
now fans out to 5 narrow builders (MK · Geraldo · modes · cost-compare · difficulty-compare), each
a regex/heuristic matcher over the same message. Today their non-overlap is argued in prose (e.g.
"the two cost builders are mutually exclusive on candidate count") and pinned only by per-builder
tests. As the floor grows, two builders silently claiming the same phrasing — or a new builder
shadowing an older one by dispatcher order — is a real regression class the value-only faithfulness
guard can't see. Idea: a CI invariant that runs **every** dispatcher builder (not just the
dispatcher) against a curated corpus of "should-fire-here" / "should-defer" phrasings and asserts
**exactly one** builder fires per should-fire case (and zero on defers) — making the
mutual-exclusion contract executable instead of prose. Worth having: it turns "I reasoned the
builders don't overlap" into a guard that fails when a sixth builder breaks that reasoning. (Dedup:
grepped `docs/ideas/` — no existing floor-conflict invariant idea.)

## ⟲ Previous-session review (Q-0102)

Previous run = **#949 (BUG-0014, the `!coglist` infinite "assumed from" loop)**. Did well:
root-caused a genuine runaway (channel-spam/rate-limit) loop to a *structural* amplifier — the
not-found handler re-dispatched an AUTO correction without checking the target exists or differs —
and fixed it at two levels: the loop-breaker (only re-dispatch a *registered, different* command)
**plus** a CI invariant (`test_command_synonyms_resolve_to_real_commands`) so an orphaned synonym
canonical can't ship again. Defense-in-depth, root over symptom — exactly the bug-book bar.

**System improvement it surfaces:** #949 closed with "**Merge ≠ deploy** — needs a Railway prod
deploy to clear it live", same as #933 (BUG-0013). Multiple recent bug-book entries are
FIXED-in-main but **not yet known-deployed**, and nothing tracks that gap — the owner has to
remember which merged fixes are actually live. Concrete improvement: add a lightweight **`Deployed:`
field** (or a "fixed-not-deployed" roll-up at the top) to the bug-book convention, so a glance shows
which user-visible fixes are still waiting on a prod restart. Small, durable, and it directly serves
the "merge ≠ deploy" reality the routine keeps re-noting. (Captured here as the review's improvement;
a future docs/process session could formalize it — it's a bug-book convention tweak, owner-facing.)

## 📋 Doc audit (Q-0104)

- `check_current_state_ledger --strict`: 5 recent merges (#944/#945/#947/#948/#949) not yet entered
  — **left for the reconciliation routine** (full-ledger catch-up is its lane per Q-0124, not the
  dispatch routine's; the next cadence pass fires at #960). My own #950 entry is in; ratchet held at
  20 by archiving #897.
- New owner decisions: none this run (no router Q raised).
- Docs reachable: `check_docs --strict` green; the §7.5 plan + ledger entry cross-reference #946/#950.

