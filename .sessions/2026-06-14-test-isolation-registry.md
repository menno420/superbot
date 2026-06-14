# 2026-06-14 — Central test-isolation registry (Q-0089 guardrail)

> **Status:** `complete`

**PR:** central test-isolation registry — `tests/_isolation.py` + conftest refactor + a
guardrail invariant test. **Branch:** `claude/trusting-goldberg-po4p7s`.
**Owner-directed** (AskUserQuestion: "Harden test suite (guardrail)") — promoted the Q-0089
idea I generated last session from idea → active work.

## Context

Last session re-enabled `pytest -n auto` (#815) but the fix only reset the **3 observed**
leaking singletons; I flagged the weak point in that session's log — *31* disbot modules
ship a `_reset_for_tests` hook, each wired ad-hoc in only some test files, so any of them
could leak across tests and reintroduce non-deterministic parallel failures. The owner chose
to harden this into a guardrail.

## What shipped

1. **`tests/_isolation.py`** — the single source of truth classifying all 31 reset hooks:
   - **GLOBAL (12)** — reset before/after every test by the conftest autouse fixture
     (`apply_global_resets`): the 3 proven (`lifecycle`, `startup_outcome`, `feature_flags`)
     plus 9 baseline-safe `core.runtime` caches (`command_descriptions`, `settings_registry`,
     `command_surface_ledger`, `guild_config`, `user_config`, `scope_locks`, `slow_path_log`,
     `participation_capabilities`, `subsystem_capabilities`). `feature_flags` is
     snapshot/restored (its hook wipes import-populated defaults — the #815 trap).
   - **PER_FILE (19)** — deliberately not global, each with a reason: 4 import-populated
     registries (`subsystem_schema`, `participation_schema`, `cleanup_registry`,
     `response_renderer_registry` — a global wipe would drop import-time registrations) + 13
     service singletons + `governance.role_templates` + the diagnostic `_log_buffer`.
2. **`tests/conftest.py`** — the autouse fixture now drives off the registry
   (`apply_global_resets`) instead of an inline 3-module list.
3. **`tests/unit/invariants/test_global_state_isolation.py`** — the guardrail: scans `disbot/`
   for every `_reset_for_tests`/`reset_for_tests` hook and **fails** if one is unclassified
   (or if a classification is stale), plus pins feature_flags' baseline-restore behavior. A
   new global-state module now *cannot* silently go unwired — the #815 root class is closed.
4. **Journal** — fixed a stale note (#815 made "pytest runs serial" wrong) + added the
   real-DB parallel caveat + the registry rule under CI & quality gates.

## Verification

- Guardrail test: 5 passed (all 31 hooks classified; no stale entries; baseline restore pinned).
- Full suite green across **6 parallel runs** (1 initial + 3× `--dist loadscope` + 2× `-n auto`),
  **9472 passed, 0 failed**, ~32–34s each. The 9 newly-global modules broke nothing.
- `check_quality --check-only` (black/isort/ruff/check_docs) green; `check_architecture
  --mode strict` 0 errors. (`tests/` is mypy/lint-excluded in CI; the new files are test-only.)

## Context delta (reflection)

- **What worked:** classifying by *reading the reset bodies* (one grep with `-A 10`) rather
  than trial-and-error — it cleanly separated baseline-safe caches (`_CACHED=None`, empty maps)
  from import-populated registries (`_REGISTRY.clear()`), which is the whole correctness axis.
- **Decision made alone:** did **not** force all 31 global. Import-populated registries +
  heavy service singletons stay PER_FILE; the lint makes that an *acknowledged* choice, not a
  silent gap. Auto-applying all 31 would have risked wiping import-time registrations and added
  suite-wide import weight for localized state.
- **Weak point of what shipped:** the guardrail only catches modules that *have* a reset hook.
  A future module with module-level mutable state and **no** hook at all would still leak and
  isn't detected by the lint — only by actually running parallel. That gap is the session idea.
- **Low-churn choice:** left the existing per-file reset fixtures in place (now harmlessly
  redundant for GLOBAL modules) rather than ripping ~24 of them out — that cleanup is a
  separate, riskier change with no correctness benefit.

## 💡 Session idea (Q-0089)

**Add a parallel-safety *audit* (the detection half) to complement this prevention.** The
registry/lint prevents the "hook exists but unwired" class, but not "new global state with no
reset hook" or pollution via a non-hook path — those only surface by running parallel. Idea: a
`scripts/check_quality.py --parallel-audit` mode that runs the suite under `--dist loadscope`
N times and diffs the failure sets (deterministic repro, the way I reproduced #815), **plus** a
periodic routine (nightly/weekly) that runs it and opens an issue on any non-determinism — so a
leak is caught by automation, not by a human debugging a flaky CI run weeks later. Cheap
on-demand tool (free-rein) + a routine (propose-first per the routine conventions). Genuinely
new (distinct from the registry shipped here); it's the detection complement that closes the
weak point above.

## ⟲ Previous-session review (Q-0102) — the #814/#815/#816 CI session (same day, earlier)

- **Did well:** root-caused 3 distinct global-state leaks and verified the fix across 8 parallel
  runs before flipping `-n auto` — disciplined, no "green locally, ship it." And it *generated
  the idea this session executed* and honestly flagged its own weak point (only 3 of 31 hooks
  handled), which is exactly the self-auditing loop the workflow wants.
- **Missed / could've done better:** it changed a **cross-cutting fact** (testing went
  serial → parallel) but didn't grep for stale statements of the old fact — leaving the
  journal's "pytest runs serial here, so a shared module prefix is safe" note wrong (and now a
  latent real-DB parallel hazard). I caught + fixed it this session.
- **System improvement it surfaces:** when a change flips a global invariant (serial→parallel,
  a renamed contract, a retired flag), the same PR should `grep` the docs/journal for the *old*
  statement and update it — stale "it works like X" notes are higher-risk than missing docs
  because they actively mislead. Worth a Q-0102-style habit, maybe a `/session-close` prompt:
  "did you change a cross-cutting fact? grep for stale references to its prior state."
