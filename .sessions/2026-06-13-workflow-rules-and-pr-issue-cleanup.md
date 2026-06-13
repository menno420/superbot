# 2026-06-13 — Course-correction: workflow rules (Q-0124/Q-0125) + PR/issue cleanup

> **Status:** `complete`

**PRs (all merged):** #806 (workflow rules Q-0124/Q-0125) · #808 (preserve issue specs) ·
#766 (fixed red CI + merged). **Closed:** PR #771 (redundant) · issues #229, #232, #773.
**Branch of this log:** `claude/session-close-2026-06-13-workflow-cleanup`.

## Context

Started on "continue where PR #800 ended." I mis-read it: PR #800 was the tail of the **P0-3
arc PR 2** session (its log names the next step as **arc PR 3 — delegated-apply, Q-0098**), but
I let the SessionStart `Recon: DUE` banner + `current-state` steer me into running a **docs
reconciliation pass** instead. Worse, I didn't `git fetch` first — so I built a near-complete
duplicate of a pass a routine had **already merged concurrently as #804**. The owner caught both:
the wrong-task substitution, and that several stale open PRs/issues (one red) had been ignored by
sessions *and* two prior reconciliation passes.

## What shipped (this session)

1. **Discarded the duplicate recon pass**, reset to `origin/main` (#804's pass is canonical).
2. **Q-0124** (PR #806) — the Q-0107 reconciliation pass is the *routines'* job; a manually-started
   session doesn't run it unless explicitly asked. CLAUDE.md Q-0107 bullet + the misleading
   `check_reconciliation_due` banner reworded + router + journal.
3. **Q-0125** (PR #806) — sessions check open-PR/issue *health* (not just title collisions); the
   reconciliation pass + the autonomous routine *disposition* stale items (close/fix), not just note
   them. CLAUDE.md reconcile scope + autonomous-routines prompt + router + journal.
4. **PR cleanup:** #766 (red CI) root-caused as `check_docs` reachability orphans → rebased onto
   main, linked from the README index, **merged**; #771 (redundant + conflicted) **closed**.
5. **Issue cleanup (PR #808):** preserved the genuinely-uncaptured specs from #229 (RPS
   tournament refactor) and #232 (setup-wizard onboarding planner) into `docs/ideas/` before
   closing; #773 (backup alert) closed — its gate (`DATABASE_PUBLIC_URL`) was already tracked.
6. **arc PR 3** (the real PR #800 continuation) — deferred to a **fresh focused session** (owner's
   call, per Q-0088); teed up turn-key against convergence plan §4.

## Verification

All docs-only / config; `check_docs --strict` green on every branch; `check_quality --check-only`
green; `check_reconciliation_due` parses + reports correctly. No `disbot/` runtime code touched.

## Context delta (reflection)

- **Route miss:** the SessionStart banner is the single most-read line at session start and it is
  written for the *routine* ("the next session should be a docs-only reconciliation pass"). For a
  *human-prompted* session it actively mis-steers. The orientation route never says "a manual
  session ignores the recon banner" — now fixed (Q-0124), but the banner itself was the trap.
- **Discovered by hand (the expensive one):** that `origin/main` had advanced #800→#804+ with my
  exact task already merged. The journal *had* a "check what merged to main" rule; I didn't run it
  at orientation. Reinforced it to a literal first-action Quick-ref row + the collision rule.
- **Route excess:** re-read the full prior pass doc top-to-bottom when the header grep + §2/§4 would
  have sufficed.
- **Decisions made alone:** discarded my own (substantial, complete) duplicate rather than ship a
  competing pass — the clean call (don't create a 2nd live decade-queue doc / conflict-edit the same
  files). Rebased #766 onto main + hand-merged it (a `docs/*` branch auto-merge won't arm; Q-0123
  residual hand-merge, CI-green-on-final-head verified).
- **Weak point of what shipped:** nothing runtime; the risk is purely that I added several
  CLAUDE.md/router rules in one session — kept each tightly scoped + provenance-stamped (Q-0124/0125)
  to avoid rule-sprawl.
- **One change that would have helped most:** an audience-aware SessionStart banner (below).

## 💡 Session idea (Q-0089)

**Make the SessionStart context audience-aware (routine vs human-prompted).** The root cause of
this whole session's wrong turn was that routine-oriented signals (`Recon: DUE`, "the next session
should be a reconciliation pass," `current-state` ▶ written for the autonomous loop) are shown
identically to a human-prompted session, where they mislead. Idea: the SessionStart hook detects
whether a human prompt is present and, if so, **demotes the routine-only nudges** (recon-due,
continue-issue banners) to a one-line "(routine signal — ignore unless you were asked)" footer
instead of a headline. The generalization of the Q-0124 banner reword, applied at the hook level.
*Config change (the hook) → propose-first per Q-0106; capturing here for a router round, not
self-applying.* Genuinely new (distinct from Q-0124's docs fix); directly prevents the failure that
cost this session its first hour.

## ⟲ Previous-session review (Q-0102) — the #804 band-#800 reconciliation pass

- **Did well:** a clean, correct Q-0107 pass — scored band #781–#800 (2/10 planned slots), found
  *and fixed by convention* the same ledger range-masking false-green I independently hit, planned
  #801–#820, reset the marker, re-badged the third pass. Solid, and its concurrent fire is proof the
  `reconcile`-issue trigger works.
- **Missed:** it **noted** open PRs (e.g. "#771 — recommend close") but didn't *act* — left #771
  open and never swept #766's red CI. That "note, don't disposition" habit is exactly the gap the
  owner flagged and **Q-0125** (this session) closes: a pass must disposition, not annotate.
- **New collision type for Q-0060:** #804 (routine) vs my manual session both ran the same
  routine-triggered task — a *routine-vs-human* duplicate, not the manual-vs-manual #678 class. A
  stronger data point for the deferred "active-sessions ledger" (Q-0060 option b) than any so far:
  the trigger is shared (the issue), but nothing claims it.
