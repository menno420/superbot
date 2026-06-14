# Session: eval-coverage drift guard (Q-0089 idea → build)

> **Status:** `complete`

**Branch:** `claude/wizardly-edison-xw34kb` · **PR:** (opening) · **Date:** 2026-06-14 · **Type:** AI hardening / invariant (follow-up to #878)

## What I'm about to do (born-red declaration)
Implement the session idea the owner approved from #878: a **CI eval-coverage drift guard**. A tiny
invariant that fails when a canonical AI tool (`services.ai_tools.all_tool_specs`) or an `AITask`
enters the surface but **no** golden/smoke eval case references it — so the now-versioned eval
matrix can't silently fall behind the surface it's meant to prove ("enforce, don't exhort", the same
principle as the doc-freshness gates).

**Design:** a self-cleaning **ratchet**, not an absolute mandate (only 8/34 tools, 2/16 tasks are
covered today). Partition: `catalogue == referenced ∪ acknowledged`. The acknowledged set is the
explicit, reviewable **pick-list of the current gap**; the guard fails on (a) a new
unreferenced+unacknowledged tool/task, (b) a stale ack whose tool/task no longer exists, and (c) an
ack entry that is now *also* referenced (forces the ledger to shrink as coverage grows).

## Coordination
Bot tests only (`tests/evals/`). No `disbot/` runtime change. Follow-up to the just-merged #878.

## Shipped
- **`tests/evals/test_eval_coverage.py`** — the drift guard. Partition ratchet over the canonical
  tool surface (`services.ai_tools.all_tool_specs`, 34 tools) and `AITask` (16): `referenced ∪
  acknowledged == surface`, disjoint, with a **coverage floor** (8 tools / 2 tasks) so coverage can
  only ratchet up. Three actionable failure directions (new-unacked · stale-ack · ack-now-covered)
  + **2 meta-tests** proving the guard actually *fires* on synthetic drift (a guard that can't fail
  is worse than none — the journal's dead-safety-check lesson). The two acknowledged sets are the
  explicit, grouped **pick-list of the current gap** (BTD6 data · server-introspection · AI
  self-awareness · diagnostics — 26 tools; 14 tasks).

## Verified
`check_quality --full` green (**9645 passed** — +12 guard tests) · `check_architecture --mode strict`
**0 errors** · the guard's firing is itself tested (`test_guard_fires_on_a_synthetic_new_tool`).
PR **#879** (born-red → flipped complete last).

## 💡 Session idea (Q-0089)
**Surface the coverage gap as a scorecard line:** have `run_evals.py --smoke` (and the live record)
print `tools: 8/34 covered · tasks: 2/16` sourced from the same guard logic — so the acknowledged
pick-list becomes a *visible dashboard number* that nudges each session to pick one off, not just a
silent allowlist. Small; turns the ratchet into a progress signal. Dedup-checked: no existing
eval-dashboard idea.

## ⟲ Previous-session review (Q-0102)
Reviewing **#878 (the eval/smoke matrix, this conversation's prior session):** solid — it shipped a
genuinely missing artifact (CI-gated deterministic AI contract) and left Layer B correctly gated.
**What it missed:** it *added* a versioned matrix but nothing stopped that matrix from decaying — the
idea that became this PR. It also surfaced (but didn't fix) that **P1-1 is really 3–4 sub-slices**
under one roadmap line. **System improvement:** this two-session arc (build the matrix → immediately
guard it from decay) is a good *pattern* — **"ship the enforcement with the artifact, not a session
later."** A new CI artifact (matrix, ledger, registry) should land with its anti-drift guard in the
same or the very next PR, while the gap is fresh; the doc-freshness gates already embody this, and
the eval matrix now does too.

## Doc audit (Q-0104)
`check_docs --strict` ✓ · `check_quality --full` ✓ · no owner decision this session (the idea was
owner-approved in chat; the design — ratchet vs. mandate — was derived from current 8/34 reality, no
router entry needed). Ledger: folded #879 into the existing #878 Recently-shipped entry (one eval
thread → ratchet stays at 20); added a one-line note to the AI readiness map. The #872–#876 drift
noted in #878's log remains for the reconciliation routine (Q-0124).
**Grooming (Q-0015):** hardened the #878 artifact against the most likely way it would have rotted —
exactly the "enforce, don't exhort" maturation the agent-workflow prizes.
