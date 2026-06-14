# 2026-06-14 — hardening P1-2: health findings lifecycle + operational retention (#843)

> **Status:** `complete` — PR **#843 MERGED** (auto-merged on green, Q-0123); this
> session-close docs slice lands as a small follow-up PR (see "Ledger hygiene / the
> auto-merge race" below).

**PR:** **#843** (merged) — code + Slice-A/B/C doc updates. Closes the two **code** gaps in
the health/diagnostics production-readiness map; the remaining gap to production-ready is the
owner-led live walk only.

## Context

Picked from the band-#820 reconciliation decade queue (slot 8). The P0 spine (P0-1…P0-4) is
complete and P0-2 PR 1 shipped (#829), so P1-2 was the next fully-completable, owner-unblocked
track: **Q-0097 was already answered (operator-managed lifecycle)**, and the live-verification
half is owner-led (no sandbox AI key), leaving a clean, contained code slice.

The two gaps: (1) findings could be *filtered* as resolved/ignored but **nothing transitioned
them** — so in normal operation every finding stayed `open` forever and the retention roll-up
was unreachable; (2) retention ran **only at startup**, so a long-lived replica never re-swept.

## What shipped

1. **Lifecycle transitions through the sole writer (Q-0097):**
   - `utils/db/health_findings.set_finding_status` — a CTE `UPDATE … RETURNING` the prior
     status. Added to the sole-writer AST guard's `_FORBIDDEN_NAMES`.
   - `health_findings_service.set_status` — the one transition path (`open`↔`resolved`/
     `ignored`), validates status (above the migration-057 CHECK), returns a typed
     `TransitionResult`, and emits `audit.action_recorded` **only on a genuine change** (system
     recording stays audit-free, as the module always documented).
   - `!platform finding resolve/ignore/reopen <fingerprint>` — admin command, kept **out** of
     the read-only platform hub by design.
2. **Operational retention:** new `HealthMaintenanceCog` reruns `run_retention()` on a daily
   `tasks.loop` (mirrors `MediaMaintenanceCog` from #829); registered in `config`. Startup sweep stays.
3. **Invariant + docs:** pinned the platform-hub typed-only exclusion of
   `startup`/`findings`/`finding`; updated `ownership.md`, the health map (rows → Done, verdict),
   the hardening roadmap (P1-2 **SHIPPED**), the folio, the smoke checklist, and the two
   cog-count doc-tests for the new extension.

## Verification

- `check_quality --full` green (**9551 passed**, 3 skipped); `check_architecture --mode strict`
  **0 errors**; `check_docs --strict` + `check_current_state_ledger --strict` green.
- **Brought up local Postgres** and ran `test_health_findings_integration.py` (12 passed incl.
  3 new `set_finding_status` tests) — the new CTE SQL is verified against a real DB, not just mocked.
- +15 tests total (service unit, DB integration, cog command, maintenance-cog loop, hub exclusion).

## Context delta (reflection)

- **What worked:** the readiness map was a near-turn-key spec — its "Required before
  production-ready" items 2+3 and the simplification notes ("keep transitions in
  `health_findings_service`", "reuse the managed task supervisor") pointed straight at the
  shape. `MediaMaintenanceCog` (#829, last week's P0-2) was a perfect template for the retention
  cog — copying a *just-shipped* sanctioned pattern beats inventing one.
- **Decisions made alone:** (a) emit audit only on a real change (not on `unchanged`/`not_found`)
  so a no-op operator command doesn't spam the audit channel; (b) a *deliberate* operator
  transition can reopen an `ignored` finding, distinct from the upsert's recurrence rule which
  keeps `ignored` rows ignored — the explicit DB-layer docstring records the difference;
  (c) typed command, not a hub mutation surface — keeps the four hub Selects read-only and the
  slice bounded (an interactive findings-manager panel is a clean future follow-up).
- **Weak point of what shipped:** the `!platform finding` command takes a raw fingerprint string
  — fine for the colon-delimited fingerprints in use (`diagnostics.provider_failed:ai`), but an
  operator must copy it from the `!platform findings` list, which doesn't number its rows. A
  short index or an interactive picker would be friendlier (the follow-up above).

## Ledger hygiene / the auto-merge race (process note)

The session pushed in two batches: commit 1 (code + Slice-A/B/C docs) then commit 2 (this
session-close set — the #843 ledger entry, this log, grooming, claim clear). **Auto-merge (Q-0123)
fired on commit 1 the instant `code-quality` went green — *before* commit 2 was pushed** — so
#843 merged with the code but **without its ledger entry**, and commit 2 was stranded on the
(now-closed) branch. Meanwhile a band-#840 reconciliation pass had advanced `main` independently,
so the stranded commit couldn't be reused (its `current-state.md` was based on pre-band-840 main
and would have reverted that pass). Recovery: a clean follow-up branch from current `main`
re-applies only the genuinely-needed session-close docs (this log + the #843 ledger entry +
ratchet archive of #764 + claim clear + the idea grooming) on top of the band-#840 state. The
takeaway is in the previous-session review's system-improvement below.

## 💡 Session idea (Q-0089)

**A periodic-task heartbeat + a health adapter that flags a managed `tasks.loop` that has stopped
firing.** This session added the *third* domain retention loop (`HealthMaintenanceCog` after
`MediaMaintenanceCog` and `counters_cog`), all hand-rolled `@tasks.loop` cogs with the same
shape. Two gaps follow: (1) no single place lists "these are the scheduled maintenance loops and
their cadences" (the existing `docs/ideas/scheduled-maintenance-registry-2026-06-14.md` covers the
registry half); (2) the health `_tasks_subsystem` adapter is **shallow** — the readiness map flags
it reports healthy from *active count* alone and "cannot report recent task failure," so a loop
that silently stops would never surface. Idea: each registered maintenance loop records a
`last_ran_at` heartbeat; the tasks adapter degrades the subsystem when a loop hasn't fired within
~2× its cadence. This makes "retention runs daily" a *verifiable* claim on a long-lived replica —
exactly the gap P1-2 was about, but for tasks. **Folded into the existing registry idea this
session (grooming below)** rather than minting a near-duplicate file.

## ⟲ Previous-session review (Q-0102) — #829 (P0-2 PR 1, media retention)

- **Did well:** #829 is the reason this session was fast. It established `MediaMaintenanceCog`
  as the canonical "glue cog owning a content-free retention `tasks.loop`" — I copied that shape
  almost verbatim for `HealthMaintenanceCog`. A shipped pattern became a template; the system
  working.
- **Missed / could've done better:** #829 wired a new periodic loop without touching the health
  `_tasks_subsystem` adapter — so neither the media purge loop nor (now) the health retention loop
  is actually *observable* if it stops. Both sessions left "the loop runs on a cadence" as an
  untested live claim. That's the same class of gap P1-2 closed for *findings* but reproduced for
  *tasks*.
- **System improvement it surfaces:** *two*, both from this session's lived experience. (1) The
  loop-observability gap above (folded into the registry idea). (2) **The auto-merge / push-batching
  ordering trap** (the race above): with native auto-merge (Q-0123) arming on the first green
  `code-quality`, a session that pushes code first and session-close docs second will routinely
  merge *without* its ledger entry — the #843 case. The push-batching rule (Q-0126) says "push when
  meaningfully complete," which should mean **one push containing code *and* the ledger entry**, or
  the ledger entry committed before the first push. Worth a CLAUDE.md clarification (router round):
  *when auto-merge is armed, the ledger/session-close docs must be in the same push as the code, not
  a follow-up* — otherwise every session pays this stranded-commit + follow-up-PR tax.

## Grooming (Q-0015)

Advanced `docs/ideas/scheduled-maintenance-registry-2026-06-14.md`: strengthened its case (P1-2
minted a fourth single-loop cog with the identical shape) and **sharpened its observability half**
from a vague "silently-dead loop is invisible" into the concrete heartbeat → `_tasks_subsystem`
degradation mechanism, connecting it to the readiness map's Partial-rated shallow-tasks adapter.
This is also where the Q-0089 idea above lands (dedup, not a near-duplicate file).
