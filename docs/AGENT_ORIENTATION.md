# SuperBot — Agent Orientation (Read This First)

> **Status:** binding (reference material, not implementation approval).
> Future Claude / Codex / human contributors should read this page
> before proposing or implementing changes. It is the only file in
> `docs/` that exists to orient a brand-new session; everything else
> is consumed on-demand once you know where to look.
>
> **Scope:** orientation only. This document does not define
> architecture, ownership, or runtime contracts — it tells you which
> existing documents do.

---

## Why this file exists

SuperBot has 23 markdown files in `docs/` plus three ADRs plus seven
sub-roadmap docs plus `.claude/CLAUDE.md`. A new agent that opens the
folder and starts reading top-to-bottom will hit roadmap and audit
material before reaching the binding contracts. This file fixes that
by stating, up front:

1. Which docs are **binding** (treat as authoritative).
2. Which docs are **reference inventories** (consult per-task).
3. Which docs are **historical plans** (read for context only — do
   not treat as the current end-state).
4. Which docs are **how-to-work-in-this-repo** material.

If you only read three files before touching code, read:

1. **`docs/architecture.md`** — layering, invariants, decomposition rules.
2. **`docs/ownership.md`** — who owns which tables, services, events.
3. **`docs/runtime_contracts.md`** — lifecycle guarantees + failure modes.

If you are about to add, move, or extract a helper function, also
read **`docs/helper-policy.md`** first.

---

## Reading order by task

### Any task

| Order | Doc | Why |
|---|---|---|
| 1 | `.claude/CLAUDE.md` | CodeGraph rules — what the static index can and cannot tell you about this codebase. Auto-loaded. |
| 2 | `docs/codegraph-usage.md` | Full trust matrix behind the short CLAUDE.md rules. Skim once, refer back when CodeGraph surprises you. |
| 3 | `docs/AGENT_ORIENTATION.md` (this file) | What to read next, based on what you are doing. |
| 4 | `docs/repo-navigation-map.md` | Where things live in the tree. Use as a folder-to-purpose lookup. |

### Adding a new subsystem / cog

1. `docs/architecture.md` § "Where to add a new subsystem" + § "Subsystem decomposition" + § "PersistentView placement".
2. `docs/ownership.md` § "Subsystem ownership" + § "Dependency direction".
3. `docs/runtime_contracts.md` § 1 ("Subsystem identity contract") + § 3 ("PersistentView contract") + § 7 ("Managed task lifecycle").
4. `docs/building-roadmap/command-integration-standard.md` — required panel / Help / settings wiring.
5. `docs/building-roadmap/mother-hub-map.md` — where the new subsystem fits in the hub tree.
6. `docs/helper-policy.md` — where to put any new helpers you write along the way.

### Editing an existing cog

1. `docs/repo-navigation-map.md` — find the cog's package, view package, service, DB module.
2. `docs/ownership.md` — confirm which service/pipeline mutations must go through.
3. `docs/help-command-surface-map.md` — confirm the cog's Help route and hub.
4. `docs/runtime_contracts.md` § 6 (interaction lifecycle) + § 7 (managed tasks).
5. Source files (always authoritative when in doubt).

### Touching shared runtime / `core/runtime/*`

1. `docs/architecture.md` § "Ownership boundary" + § "Single-process assumption" + § "State classification".
2. `docs/runtime_contracts.md` (all sections).
3. `docs/platform-consistency-ledger.md` § 1 (domain contract ledger).
4. `docs/decisions/001-no-redis-backed-state.md` — before adding any "we should cache this in Redis" plan.

### Touching governance / mutation pipelines

1. `docs/ownership.md` § "Service ownership" + § "Direct DB writes — explicit blocklist".
2. `docs/architecture.md` § "Runtime invariants (CI-enforced)" — INV-E, INV-F, INV-G are AST-checked.
3. `docs/runtime_contracts.md` § 9 (mutation contract checklist).

### Touching settings / bindings / resource provisioning

1. `docs/settings-customization-roadmap.md` — the three lanes (settings / binding / provisioning) and which pipeline owns which.
2. `docs/resource-provisioning-overview.md` — the RPM lane.
3. `docs/platform-consistency-ledger.md` § 1 — current state of each domain.
4. `docs/building-roadmap/config-input-standard.md` — UI rules for setting widgets.

### Touching tests / docs / smoke

1. `docs/smoke-test-checklist.md` — what must be smoked before a runtime-relevant PR ships. Pinned to `ReadinessSnapshot` by `tests/unit/docs/test_smoke_test_checklist.py`.
2. `tests/unit/docs/` — every doc-pinning test. Adding or removing a doc that has a pinning test means the test changes too.

### Touching command access (prefix + slash admission)

1. `disbot/core/runtime/command_access.py` — the resolver
   (`resolve_command_access`), adapters (`from_prefix_ctx` /
   `from_interaction`), and the bootstrap allowlist.  Both the
   prefix global check and `bot.tree.interaction_check` delegate
   here.
2. `disbot/services/command_access_service.py` — the canonical write
   path (`set_mode`, `replace_allowed_channels`, the `set_policy`
   composite).  Every operator-facing mutation must route through
   this module so cache invalidation + audit emission stay in step.
3. `disbot/cogs/bootstrap_access_cog.py` — installs both gates
   (prefix `_channel_guard` and `tree.interaction_check`).  Loads
   first in `config.INITIAL_EXTENSIONS`.
4. `disbot/views/settings/edit_command_access.py` + the
   `Command access` button on `views/settings/hub.py` — the
   operator UI surface.
5. `disbot/migrations/050_guild_command_access.sql` (schema) +
   `051_command_access_main_server_backfill.sql` (data) — the
   policy storage and the main-server backfill.  Add to
   migration 050's CHECK constraint before adding a new
   `AccessMode` literal.

### Touching AI / setup advisor

1. `docs/ai-config-ownership.md` — binding contract for the AI cog's
   read model, projection rules, mutation seam, and UI surface
   pinning. Read this before any AI-cog change.
2. `docs/ai-readiness-plan.md` — the inert scaffold + planned layer.
3. `docs/ai-service-integration-map.md` — current setup advisor integration shape.
4. `disbot/core/runtime/ai/README.md` — package-level intent.

---

## Document classification

The taxonomy below is the only reliable way to tell "what does the
project still care about?" from "what was the plan a year ago?". When
in doubt, treat the source files as authoritative over any doc.

### Binding (treat as authoritative)

These define the platform contract. Changing them is an architecture
change — open an issue or a separate doc-only PR before implementing
something that conflicts with them.

- `.claude/CLAUDE.md`
- `docs/architecture.md`
- `docs/ownership.md`
- `docs/runtime_contracts.md`
- `docs/codegraph-usage.md`
- `docs/AGENT_ORIENTATION.md` (this file)
- `docs/repo-navigation-map.md`
- `docs/helper-policy.md`
- `docs/decisions/*.md` (ADRs — immutable once landed)
- `docs/server-logging.md` (shipped feature reference)
- `docs/smoke-test-checklist.md` (pinned to code by doc-test)
- `docs/help-command-surface-map.md` (pinned to code by doc-test)
- `docs/ai-config-ownership.md` (pinned to code by doc-test)

### Living inventories / status ledgers

Updated as work lands. Always check the date / referenced PRs at the
top before trusting the contents.

- `docs/platform-consistency-ledger.md`
- `docs/phase-2-completion-readiness.md`
- `docs/settings-customization-command-map.md`
- `docs/operator-settings-presets.md`
- `docs/games-actionability-roadmap.md` (status: complete — historical now)
- `docs/helper-debt-inventory.md` (snapshot — companion to `helper-policy.md`)
- `docs/ui-view-adoption-audit.md` (snapshot — companion to `helper-debt-inventory.md`)
- `docs/audits/mutation_boundary_audit.md` — mutation boundary audit results.
  Run against the codebase post-hardening session (2026-05-24).

### Standards / reference guides

Read once when relevant. They describe how to do something, not what
has already been done.

- `docs/building-roadmap/command-integration-standard.md`
- `docs/building-roadmap/hub-ui-standard.md`
- `docs/building-roadmap/config-input-standard.md`
- `docs/building-roadmap/mother-hub-map.md`
- `docs/settings-customization-roadmap.md`
- `docs/resource-provisioning-overview.md`
- `docs/architecture/service_ownership.md` — enriched "at a glance" ownership lookup.
  Quick-reference companion to `docs/ownership.md`; `ownership.md` is authoritative
  when the two disagree.

### Plans / roadmaps (read for context only)

These describe **planned** end-states. They do **not** describe what
exists today. Do not implement against them as if they were specs —
cross-check the source and the consistency ledger first.

- `docs/roadmap_setup_platform.md`
- `docs/loose-ends-audit-roadmap.md`
- `docs/phase_2b_bindings_plan.md`
- `docs/building-roadmap/interface-completion-roadmap.md`
- `docs/building-roadmap/command-expansion-backlog.md`
- `docs/building-roadmap/admin-powers-config-coverage.md`
- `docs/ai-readiness-plan.md`
- `docs/ai-readiness-pr-notes.md`
- `docs/ai-service-integration-map.md`

### Subsystem-specific scaffold notes

- `disbot/core/runtime/ai/README.md`

---

## "Read first" mandate for agents

Before proposing or implementing any non-trivial change:

1. Open this file (`docs/AGENT_ORIENTATION.md`) and follow the
   "Reading order by task" section that matches your work.
2. Open the relevant binding doc(s) before editing the corresponding
   code. Do not synthesize the contract from memory or from a roadmap.
3. If you are about to put a function somewhere "general" (in
   `utils/`, in `services/`, in `views/base.py`), open
   `docs/helper-policy.md` first.
4. If CodeGraph and a source file disagree, the **source file wins**
   (`.claude/CLAUDE.md` § "Source files win"). Re-read the actual file
   you are about to edit.

This is not a courtesy — repeated rediscovery is the main reason
SuperBot accumulates duplicate helpers and orphan plans. The minutes
spent reading these docs pay back at PR review.

---

## What this document does **not** cover

- Architecture. That is `docs/architecture.md`.
- Ownership. That is `docs/ownership.md`.
- Runtime guarantees. That is `docs/runtime_contracts.md`.
- Helper rules. That is `docs/helper-policy.md`.
- Where things live. That is `docs/repo-navigation-map.md`.
- CodeGraph caveats. That is `.claude/CLAUDE.md` and
  `docs/codegraph-usage.md`.

If you have to choose between this file and any of the above for a
given question, the specific doc wins.

---

## Updating this file

This file is **orientation**, not architecture. Update it when:

- A new binding doc lands → add it to the classification list.
- An existing doc graduates from "plan" to "binding" → move it.
- A binding doc is renamed or split → fix the path.
- A new common task pattern emerges that needs its own reading order
  → add a row to "Reading order by task".

Do **not** update it for:

- Phase progress (use `docs/phase-2-completion-readiness.md` or
  the consistency ledger).
- Specific PR notes (those belong in the PR description).
- Long-form architecture rationale (those belong in
  `docs/architecture.md` or an ADR).

Keep this file short. If it grows past ~250 lines it has become a
duplicate architecture doc and the additions belong elsewhere.
