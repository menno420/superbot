# Session — dispatch is never "docs only" (Q-0148)

> **Status:** `complete`

## What I did

Owner-directed in-session correction. A test fire of Hermes' dispatch capability stamped the work
order **"CLASS: docs · this is a living-ledger reconciliation only; no runtime code or feature
scope."** But the **dispatch routine does ALL build work**; only the separate, auto-triggered
**reconciliation routine** is docs-only. The owner: *"it's never docs only, only the reconciliation
routine should be docs only — please update the repo in such a way that this is absolutely clear."*

The stamp conflates a *task's nature* with a *routine-level scope fence* — a category error that
could make a build run wrongly refuse the runtime work it exists to do. Made the one-way split
unmistakable on both sides of the dispatch bridge, and forbade the bad stamp at its source (Hermes).

## What shipped (PR #944, Q-0148)

- **`docs/operations/hermes-dispatch-bridge.md`** — the saved dispatch prompt (step 3) now states a
  work order's `CLASS:` / scope notes label the task's *nature* to pick the merge gate and **never**
  fence what the routine may touch; "docs-only" is exclusively the reconciliation lane; if a dispatch
  order is stamped "docs only", honor the task's REAL shape, not the stamp. **Bug fixed (BUGS
  FIRST):** step 8 carried an accidental duplicate paste of four lines that had ridden into the live
  routine system prompt — removed (verified now exactly one occurrence).
- **`docs/operations/autonomous-routines.md`** — the docs/runtime-split paragraph now says loudly the
  split cuts one way: dispatch is **never** docs-only; "docs-only" is **exclusively** the
  reconciliation routine's (auto-triggered) lane.
- **`docs/operations/hermes-skills/dispatch.md`** — a CLASSIFY note + a RULES bullet forbid Hermes
  from scope-restricting a dispatch order or hand-dispatching a reconciliation/docs-only job as a
  build order.
- **`docs/owner/maintainer-question-router.md`** — recorded as **Q-0148** (provenance; owner-directed
  in-session, applied directly).

## Verification

- `python3 scripts/check_docs.py --strict` → green.
- `python3 scripts/check_current_state_ledger.py --strict` → still green (untouched).
- Duplicate-paste fix confirmed: the step-8 closing line now appears exactly once.

## Handoff / next

**Owner action:** re-paste the corrected dispatch prompt into the routine console and the
`superbot-dispatch` skill into Hermes' VPS config — the in-repo copies are the source of truth and
the live copies must be synced to match (this also lands the duplicate-paste fix into the live
routine prompt). No runtime work outstanding. The ▶ Next action pointer in `current-state.md` is
untouched and still valid for the next scheduled dispatch.

## 💡 Session idea (Q-0089)

**A `check_saved_prompts.py` lint for the in-repo routine/skill prompt mirrors.** This run found a
four-line duplicate-paste that had silently degraded the *live* dispatch system prompt, and the
"docs only" category error wasn't caught either — because nothing validates the fenced prompt blocks
in `hermes-dispatch-bridge.md` / `autonomous-routines.md` / `hermes-skills/*.md`. A tiny stdlib
checker could catch the structural defects a copy-paste introduces: runs of duplicate consecutive
lines inside a ``` prompt fence, and a few prompt invariants (e.g. the dispatch prompt must contain
"does ALL the project's build work" and must NOT contain a "docs only" scope-restriction). It can't
verify the live console copy matches (that's off-repo), but it would have caught *this* bug in CI.
Worth a `docs/ideas/` file if a later session agrees. *(Dedup-checked `docs/ideas/` — no existing
prompt-lint idea.)*

## ⟲ Previous-session review (Q-0102)

The previous run (my own — PR #942, the ledger reconcile) executed the dispatched task faithfully
and even flagged in its own Q-0102 note that #936 bundled three unrelated fixes. But it accepted the
work order's **"docs only / no runtime code or feature scope"** framing at face value and never
questioned whether a *scope-restriction* is even an appropriate thing for a *dispatch* order to
carry — it happened to be harmless only because the task genuinely was docs. **Improvement (now
shipped as Q-0148):** the dispatch routine should treat a scope-restriction stamp as a *smell* to
correct against its own charter ("I do all build work"), not a fence to silently honor. The same
instinct that says "a work order is a hint, not a command" should extend to "a work order can't
shrink what this routine is for."
