# 2026-06-14 — P0-3 arc PR 3: delegated-Setup apply authority (Q-0098)

**PR:** [#817](https://github.com/menno420/superbot/pull/817) (ready, native auto-merge armed) ·
**Plan:** [settings pointer-lane convergence](../docs/planning/settings-pointer-lane-convergence-plan-2026-06-13.md) §4 ·
**Queue:** [band-#800 decade queue](../docs/planning/reconciliation-pass-2026-06-13-band800.md) §4 slot 2 ·
**Authoritative state:** `docs/current-state.md` (stamp + Recently-shipped #817).

## Arc

Continued the production-hardening P0 spine (the standing priority). Executed the
documented next slot — **P0-3 arc PR 3**, the delegated-Setup apply authority contract
(Q-0098). Closes the "you may apply, then every per-op write fails" gap: Final Review's
`_gate_apply` authorizes the owner OR a delegated admin (a possibly **non-administrator**
member added via `/setup-delegate`), but each staged op then hit the administrator floor
in `governance.capability` and silently failed.

## Shipped

- **`governance/capability.py`** — a bounded `actor_type="setup_delegate"` is authorized at
  the floor like `system`/`backfill`, but **deliberately not the step-1 short-circuit**:
  still requires target-guild membership (step 2) and stays subject to the revoke overlay
  (step 4). Audited as `setup_delegate` (distinct from an admin write).
- **`services/setup_operations.apply_operations`** is the **sole minter**. New
  `_resolve_apply_actor_type` re-verifies the live delegation (`setup_access.can_apply_setup`)
  against a **fresh `SetupSession`** before minting — never trusts the view gate. Owner/admin
  keep `"user"` (and short-circuit before any DB read); delegation-lost falls back to `"user"`
  so the floor denies. The resolved type is threaded to all three capability pipelines —
  `binding_mutation` was the one NOT already forwarding `actor_type`; now it does.
- **DB**: `setup_delegate` added to the three pipelines' `_ALLOWED_ACTOR_TYPES` + the
  settings/resource audit `CHECK` constraints (**migration 069**; bindings has no DB CHECK).
  The migration finds each *auto-named, table-level* constraint by definition (`pg_constraint`
  introspection) and re-adds a **named, widened, idempotent** version.
- **Four non-escalation guards:** AST fence (`test_setup_delegate_actor_boundary.py`) — (1)
  no literal-kwarg mint outside the seam + (2) the `"setup_delegate"` token confined to the 5
  contract files; setup-lane only; revoke overlay applies; live re-verification.
- **Tests:** extended `test_capability.py` (3 delegate cases), new `test_setup_delegate_apply.py`
  (resolver partition + threading), the new AST fence, updated 4 alignment/allowlist tests to
  read migration 069 for the actor_type set (the 059→op_kind precedent).
- **Docs:** `capability-authority.md` §1/§6, convergence-plan §4/§7 (arc PR 3 DONE), roadmap
  Now horizon, current-state (stamp + Recently-shipped #817), archived #738–#740 to hold the
  ratchet, active-work claim cleared.

## Verification

- `check_quality.py --full` → **9442 passed, 34 skipped** (lint + mypy clean).
- `check_architecture --mode strict` → **0 errors**. `check_docs --strict` ✓.
- **Real Postgres + clean boot** (Galaxy Bot): migration 069 applies in-sequence; both
  constraints widened (renamed `*_actor_type_check`); a `setup_delegate` row is **accepted**, a
  bogus actor_type **rejected**; migration **idempotent** (re-run → no duplicate constraints).

## Context delta

- **Needed but not pointed to:** (1) the binding dispatcher (`_apply_binding`/`_apply_clear_binding`)
  was the *only* capability pipeline not already forwarding `actor_type` — settings/resource
  already did; found by reading the dispatcher arms. (2) Adding an actor_type literal couples to
  **two** test families the context maps did **not** flag (they said "Relevant tests: none" for
  the settings/resource pipelines): the migration-029/030 **alignment** tests AND the
  `test_*_pipeline.py::test_actor_type_allowlist_matches_documented_set` **hardcoded-set** tests.
  (3) The 029/030 CHECKs are *table-level auto-named* (not column-named like 059's), so a later
  ALTER can't guess the name — needs `pg_constraint` introspection.
- **Pointed to but didn't need:** the context maps' recommended importer reads (the
  `views/settings/edit_*.py` callers, economy/xp cogs) — the change lived entirely at the
  pipeline + dispatcher seam, not the call sites.
- **Discovered by hand:** the **"widen a CHECK in a later migration + keep its alignment test
  green by repointing to the new migration"** recipe — it lives only in migration 059's comment
  + `test_setup_draft_op_kind_parity.py`. It's the canonical pattern for this whole class and
  deserves a documented home (→ session idea).
- **Decided alone (ratify):** (a) Forwarded the resolved actor_type to `create_managed_role`
  too (not just the 3 capability pipelines): `RoleLifecycleService` has **no** actor-authority
  gate (only a bot-permission gate) and uses `actor_type` purely as an event-payload audit
  label, so a delegate can also create role-template roles, honestly audited — strictly more
  complete, zero new escalation. (b) Added a **second** AST-fence check (token confined to 5
  files) stronger than the design's literal-kwarg-only fence, because the resolver returns the
  literal as a *variable* so the kwarg-only fence alone is weak. (c) Migration 069 uses
  `pg_constraint` introspection rather than guessing the auto-generated name.
- **Flagged for maintainer:** the bypass covers settings/binding/resource (+ create_managed_role
  as a label). A delegate draft containing `set_role_threshold` / `set_cleanup_policy` /
  `set_cog_routing` ops routes through *other* authority models (actor_id / `GovernanceContext`)
  I did **not** extend — per the design's three-pipeline scope this is intended, but a non-admin
  delegate's apply isn't 100% uniform across every op kind. Confirm if delegates commonly stage
  those (rare in practice — recommendations only produce bind ops).

## Gates / handoff for the next session

- **#817 will self-merge** on green `code-quality` (auto-merge armed; subscribed for CI). No
  manual merge needed. **Next P0 = P0-4** (server-mgmt channel-ownership convergence, Q-0100),
  then P0-2 (media/YouTube retention, Q-0099) — band-#800 decade queue §4 slots 3–4.
- **Pre-existing ledger drift (NOT this PR):** `check_current_state_ledger --strict` flags
  **#802–#814** (other sessions' band merges) absent from the ledger — this is the normal
  band-accumulation reconciled at the **#820** Q-0107 pass (a manual session does not run it,
  Q-0124). It is **not** a CI gate (CI runs `check_docs --strict`, which is green). Left for the
  #820 reconciliation routine.
- **Pre-existing flaky test (NOT this PR, confirmed on clean HEAD):**
  `test_platform_consistency.py::test_build_readiness_snapshot_after_collect_includes_status`
  fails when `invariants/` runs before it in the same process (its `_reset_pc_state` fixture
  doesn't reset the `pc` global snapshot a prior invariants test leaves at `warning`). Latent in
  the full suite (an intervening service test resets it → CI green). This is the same cross-test
  state pollution the Q-0126 session named. → session idea / promote to tracked debt.

## ⟲ Previous-session review

Previous: the **Q-0126 CI-cost reduction** session (#814). **Did well:** strong empirical
discipline — it backed `pytest -n auto` out of CI the moment CI (not local) caught the suite's
non-determinism, and it shipped the `active-work.md` claim ledger I used at the *start* of this
session (it works). **Missed / could improve:** it correctly diagnosed the suite's cross-test
state pollution but parked the fix as a follow-up *idea*, leaving the pollution latent — and
this session walked straight into it (the `test_platform_consistency` flake), spending real time
proving it pre-existing on clean HEAD. **System improvement:** that pollution is now a *named,
reproducible* blocker for both a 3× CI speedup (parallel suite) **and** per-session red-herring
cost — it deserves promotion from "idea" to a tracked debt item carrying the concrete reproducer
(`invariants/` → `test_platform_consistency` global-snapshot leak), so the next agent recognizes
it instantly instead of re-deriving "is this mine?".

## 💡 Session idea

**A shared `effective_check_constraint(table, column)` test helper that derives the *current*
CHECK literal-set by scanning all migrations in order** (last inline/ADD definition wins),
replacing the bespoke, per-table alignment tests that must be *manually repointed* every time a
constraint moves to a new migration (059→op_kind, now 069→actor_type — each hand-rolled a
regex + a `_MIGRATION`/`_ACTOR_TYPE_MIGRATION` pointer). It's the constraint-alignment twin of
the "scope range-expansion to the Recently-shipped section" fix the band-#800 pass deferred for
the ledger checker — same class (a drift-guard that goes stale when the thing it guards evolves).
Genuinely believe in it: I re-implemented the bespoke extraction twice this session and the
repointing is exactly the kind of silent-staleness the alignment tests exist to prevent. Filed
intent here; dedup-grep of `docs/ideas/` showed no existing entry. Small/safe → a grooming-lane
candidate (build the helper + migrate the 3 existing alignment tests onto it).

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs opened | 1 (#817, ready, auto-merge armed) |
| Source files changed | 5 (capability, 3 pipelines, setup_operations) |
| Migration added | 1 (069, idempotent, real-PG proven) |
| Tests added/changed | 6 (2 new, 4 updated); net new test cases ~17 |
| `check_quality --full` | 9442 passed / 34 skipped ✓ |
| `check_architecture` | 0 errors ✓ |
| Live verification | real Postgres + clean boot ✓ |
| Owner decisions used | Q-0098 (delegated apply); design pinned in convergence-plan §4 |
| New owner decisions | 0 (none needed — design was decided) |
| Session idea | 1 (effective-CHECK-constraint test helper) |
| Pre-existing issues surfaced | 2 (ledger drift #802–#814; `test_platform_consistency` flake) |
