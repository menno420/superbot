# 2026-06-08 — Server-management PR13 (deterministic role templates) + a latent PR11 fix

**Arc:** Continue the server-management plan. Task said "finish PRs 13–15"; the plan
actually ends at **PR14** (the tracker is authoritative — PR13 templates, PR14 hub). Built
**PR13's deterministic slice** end-to-end and fixed a root-cause bug it surfaced. Deferred
the PR13 **AI** layer (high-sensitivity, not live-testable without provider keys; the roadmap
sequences deterministic first). PR14 (hub) left for next session.

**Shipped (one PR):**
- `services/setup_role_templates.py` — built-in, **permission-free** role bundles
  (`RoleSuggestion`/`RoleTemplate`, 6 templates) + `validate_*` + pure `plan_template`
  (create-vs-exists partition, no I/O). Named `setup_role_templates` to avoid colliding with
  the pre-existing **`governance.role_templates`** (permission-tier governance roles — a
  different concern; documented in the docstring).
- New audited **`create_managed_role`** op-kind (`services/setup_operations.py`) → routes
  through `RoleLifecycleService` (the allowlisted manual-role owner, *not* provisioning) +
  best-effort time/XP tier companion using the new role id. Preflight + label arms.
- `views/setup/sections/role_templates.py` (order 56, std+adv) — pick → preview → "Stage new
  roles". `recommended_ops_builder=None`; Final Review is the only apply gate.
- **Root-cause fixes found mid-build** (see tracker PR13 subsection): (1) **PR11 regression** —
  `set_role_threshold` was wired into the dispatcher but never the DB op-kind gate or migration
  CHECK, so the shipped roles section couldn't stage (ValueError, masked by mocked tests);
  **migration 059** + `_KNOWN_OP_KINDS` fix it. (2) **Threshold slot-collision** — the draft
  slot key omits `target_id`, so two roles' tiers overwrote each other; both sections now carry
  a per-row `binding_name` discriminator. (3) **Drift guard** —
  `test_setup_draft_op_kind_parity.py` pins dispatcher ↔ DB-gate ↔ migration CHECK in lockstep
  (the missing dispatcher↔gate check that would have caught the PR11 gap).

**Verification:** full CI mirror green (`check_quality --full`: 8009 passed, 16 skipped);
`check_architecture --mode strict`: 0 errors; **live boot clean** — migration 059 applied,
SetupCog/section register, DB CHECK verified live to accept both new kinds, 0 ERROR/CRITICAL.

**Gates / next:** PR13 **AI generation layer** (reuses the deterministic validation as its
safety filter + the `create_managed_role` staging path), then **PR14** (Server Management Hub).
Authoritative queue: `docs/planning/server-management-status-2026-06-05.md`.

**Second deliverable — PR14 implementation plan.** Rather than rush the capstone hub
(persistent views + restoration aren't cleanly live-testable in the sandbox), researched the
existing hub infra (Explore agent) and wrote a source-grounded, executable
**[PR14 hub plan](../docs/planning/server-management-pr14-hub-plan.md)**: reuse each manager's
`build_help_menu_view()` factory, compose read-only health badges from
`resource_health`/`setup_diagnostics`/`setup_readiness`/feasibility, mirror `views/games/hub.py`
+ `ModPanelView` for the persistent nav + ADR-005 re-checks. Wired into the roadmap, folio, and
tracker. PR #582 now carries PR13 (code) + this plan (docs) — review as "PR13 shipped + the
runway for PR14."

**Idea-backlog grooming (standing secondary task, Q-0015):** browsed `docs/ideas/`. The
mining brainstorm is already routed (open PR #581); `ai-extra-tool-capability-ideas` is correctly
parked behind the AI-orchestration gate; `future-product-direction-2026-06-07` is an explicit
**capture-only** doc ("do not promote until a candidate is actually promoted") whose items are
nearly all gated *after* server-management — so no unilateral promotion was appropriate this
session. The PR14 plan **is** the "research → plan for next session" move the maintainer invited.
No idea left orphaned.

## Context delta
- **Needed but not pointed to:** the **setup-draft op-kind machinery** is a *three-place*
  contract — the dispatcher `_KNOWN_KINDS` (`services/setup_operations.py`), the DB gate
  `_KNOWN_OP_KINDS` (`utils/db/setup_draft.py`), **and** the migration-035 CHECK — and the
  draft's **replace-on-conflict slot key** `(op_kind, subsystem, setting_name, binding_name)`
  (no `target_id`). Nothing in the folio/orientation names either; both bit me (the PR11 bug +
  the slot-collision). A pointer in the server-management folio's debug-router would save the
  next agent the same spelunking. (Now partly self-documenting via the new parity test.)
- **Pointed to but didn't need:** the CodeGraph trust-tier sections of CLAUDE.md — CodeGraph
  was unavailable this session ("Package unavailable — skipping index build"), so grep +
  `context_map.py` carried the whole investigation. The PreToolUse context-map hook (Grimp
  importers/blast-radius) was the genuinely useful orientation tool, not CodeGraph.
- **Discovered by hand:** the existing **`governance.role_templates`** module — found only via
  a `[known]` arch-warning line, not any doc. Two `RoleTemplate` concepts now coexist; the
  naming-collision risk is exactly what CLAUDE.md warns about. Resolved by the `setup_`-prefixed
  module name + a cross-reference docstring.
