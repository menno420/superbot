# Server Management Implementation Plan

> Converts `docs/planning/server-management-roadmap-2026-06-05.md` into a
> dependency-ordered, repo-grounded, highest-value-first implementation sequence.
>
> ---
>
> **📦 PR1–PR6 shipped (2026-06-05).** This document is the live **scope reference**
> for the PR sequence; for *what has actually landed and what is next*, read the
> status tracker: **`docs/planning/server-management-status-2026-06-05.md`**.
> Shipped: **PR1** moderation convergence (#521), **PR2** role feasibility +
> `MultiRoleSelector` (#522, selectors-only slice), **PR3 + PR4** lifecycle contract +
> `ChannelLifecycleService` channel rename/move/delete (#523, the `.delete`/`.edit`
> slice), **PR5** `RoleLifecycleService` (role create/edit/delete) + non-destructive
> field-specific time/XP threshold deletes (#525), and **PR6** selector-driven
> time/XP role config + the `role_thresholds` `role_id`/`display_name` migration
> (056) + id-first dual-read resolution. The remaining queue starts at **PR7**.
>
> **Rev 2 (external review incorporated):** PR1's moderation audit is stated as **three distinct
> signals** — `mod_logs` (authoritative history) · `moderation.action_taken` (domain event) ·
> `audit.action_recorded` (best-effort audit-routing companion, *not* a second history store). The
> companion is explicitly best-effort/non-invalidating, and `mod_logs` carries no `mutation_id` column
> (no migration).
>
> **Rev 3 (post-ship correction):** the clear-warnings label was **not** handled by display
> normalization as Rev 2 anticipated. The shipped service standardized the stored/emitted token on
> **`clearwarnings`** (one word) to match every historical `mod_logs` row, so no normalization was
> needed. Wherever this plan says new rows log `clear_warnings` and the modlogs display normalizes
> both (the Rev-2 header above, Risk (a) in PR1, and Open Question #1), read **`clearwarnings`,
> no normalization** — source wins.

## Context

SuperBot is converging into a button-first, service-owned "Guild OS." The
`Server Management Roadmap` (merged via PR #520) established the *direction* and settled
the maintainer decisions, but it is a planning artifact — it changes no behavior. This
plan turns that roadmap into an executable PR sequence, grounded in the actual current
source, and front-loads the work that gives the strongest architectural foundation with
the least avoidable rework.

The central finding from source inspection: **the problem is convergence and ownership,
not missing features.** Most primitives already exist (provisioning pipeline, moderation
service, cleanup inheritance, setup section registry, shared selectors, audit publisher).
The work is to (1) route existing surfaces through their canonical owners, (2) harden and
extend shared primitives, and (3) add lifecycle services for the mutations no pipeline
owns yet — *before* building new UI (move/reorder, hub, AI templates).

**Confirmed lead (user decision):** the first PR is **Moderation Service Convergence** — a
contained, low-risk, high-certainty win that closes a real P0 audit gap and establishes the
cog/view → service convergence pattern that every later lifecycle PR mirrors.

---

## Audit Base

- **Branch:** `claude/busy-darwin-zyPD2` (develop here; created from current HEAD).
- **Commit:** `771321e` — *Merge #520 "add server management roadmap"*. Working tree clean.
- **Recent merge context:** #512–#520 landed governance/ADR foundations the plan builds on —
  ADR-005 capability-native authority (`governance/capability.actor_holds_capability`) + F1
  operator kill-switches (`core/runtime/feature_flags`), per-surface fail-open posture
  (ADR-004), cleanup-registry ownership (RC-7), thread cleanup-scope rejection (RC-5),
  visibility cache keyed by thread (RC-2).
- **Roadmap source:** `docs/planning/server-management-roadmap-2026-06-05.md` (741 lines).
  *(The roadmap's own header says path `docs/roadmaps/…`; the file actually lives under
  `docs/planning/…`. Minor doc-path drift, not a content issue.)*
- **Repo-state notes:**
  - Roadmap's stated audit base is `23b0f36` (branch `work`); current HEAD `771321e` is only
    the merge that landed the roadmap doc itself — **the roadmap is current, not stale.**
  - CI is **Python 3.10**. Gates: `python3.10 scripts/check_architecture.py --mode strict`
    and `python3.10 scripts/check_quality.py --full` must both exit 0 before any push.
  - Hard layering rule with **zero tolerance for new violations: `services/` must not import
    `views/`.** `views/ → services/` is allowed (so modals calling `moderation_service` is clean).

### Roadmap vs. current source — reconciliations the plan adopts

| Roadmap claim | Source reality (verified) | Plan adjustment |
|---|---|---|
| "moderation cog bypasses the service" (`moderation_cog.py:126-226`) | **Confirmed, and broader:** *both* `cogs/moderation_cog.py` (typed cmds, lines 48/126/134/139/155/172/189/210/224) **and** `views/moderation/modals.py` (7 modals) bypass it. The auto-mod path (`auto_delete`) is *already* converged in counting/chain/cleanup/message_pipeline. | PR1 routes **both** manual surfaces; auto_delete callers are the reference pattern, untouched. |
| Cleanup "inherited but not expressive" | **4-level inheritance already shipped** (`governance/cleanup.py` channel→category→guild→default); thread scope rejected pre-DB (RC-5 invariant `tests/unit/governance/test_cleanup_scope.py`). | Cleanup work is **vocabulary + versioning**, NOT a model change. Preserve the RC-5 thread-rejection invariant. |
| Time/XP "row deletion can interfere" | **Confirmed:** `remove_role_threshold` does a full-row `DELETE` (wipes XP cols); `set_role_xp_threshold` preserves `days_required`. | PR5 makes deletes field-specific. |
| Role automation is name-based | **Confirmed:** `role_thresholds` keyed by `role_name`; resolved by normalized name. **But `role_automation_exemptions` is already ID-keyed (migration 052)** — a ready precedent. | PR5/PR6 migrate thresholds to ID-keyed using the exemptions pattern. |
| Selectors "fragmented, cap at 25" | **Confirmed + better than implied:** a real `views/selectors/` package exists (`ChannelSelector`, `RoleSelector`, `MultiSelect`, `MultiChannelSelector`, `ScopeSelector`, `SubsystemSelector`). Gaps: no `MultiRoleSelector`, no feasibility filter, no paging/stale-revalidation. | Phase 1 is **harden + extend + adopt**, not greenfield. |
| Need a mutation plan/preview/result primitive | **`ResourceProvisioningPipeline` is a complete, shipped template** for exactly this contract. | New lifecycle services + the shared primitive **mirror** it rather than invent. |

---

## Executive Recommendation

1. **Lead with Moderation Convergence (PR1).** The service exists and already works
   (auto_delete proves it); routing the manual surfaces through it is a pure, behavior-
   preserving refactor that closes a P0 audit gap, needs no migration/event, and sets the
   convergence pattern + invariant template for every later phase.
2. **Foundations before UI, always.** Ship shared selectors+feasibility (PR2) and the shared
   mutation/preview/result/audit contract (PR3) before any lifecycle service, move/reorder
   panel, hub, or AI template. The first phases must make *selection, safety evaluation,
   preview/apply, audit, and partial-failure behavior* reusable.
3. **Mirror, don't reinvent.** `ResourceProvisioningPipeline` (`services/resource_provisioning.py`)
   is the canonical contract: typed `Request`→side-effect-free `Preview`→`confirmed=True`
   gate→ordered apply→append-only audit (`_write_audit` + `emit_audit_action`)→best-effort
   catalogued event→typed `Result`, with function-local imports and outcome literal sets that
   mirror migration CHECK constraints. New `ChannelLifecycleService` / `RoleLifecycleService`
   and the shared primitive copy this shape.
4. **Compose canonical owners; never replace them.** Lifecycle services *coordinate* declared
   creation through `ResourceProvisioningPipeline` and bindings through
   `BindingMutationPipeline`; cleanup writes stay in `GovernanceMutationPipeline`; settings in
   `SettingsMutationPipeline`. Lifecycle services own only the mutations no pipeline owns:
   rename/move/reorder/overwrite/delete/clone (channels) and create/edit/delete/reorder/assign
   (roles).
5. **Extract the shared primitive with a real consumer (PR3 + PR4 land adjacent).** Honor
   `docs/helper-policy.md`'s "2+ callers" rule — the mutation/preview/result contract ships
   *with* the channel lifecycle service as its first consumer, role lifecycle as the second.
   No speculative standalone primitive.
6. **Honesty about rollback.** No transactional rollback for Discord mutations. Snapshot prior
   state, classify reversibility (reversible / compensatable / irreversible), audit every step,
   report partial failure, and offer a confirmed "Revert Safe Changes" plan. Never describe
   recreating a deleted channel/role as rollback.
7. **Setup orchestrates, never owns mutations.** New setup sections (role/moderation/governance/
   diagnostics) stage `SetupOperation`s and route through `apply_operations`; the AST invariant
   `tests/unit/invariants/test_setup_operations_invariants.py` forbids setup views importing
   pipelines directly.
8. **AI proposes only.** AI role templates emit *structured suggestions* that are validated,
   reviewed, edited, and converted into ordinary staged lifecycle operations. AI never calls
   Discord, writes config, grants permissions, or bypasses review.
9. **One persistent-decision gate everywhere.** Every persistent/ephemeral hub callback rechecks
   capability + target guild at interaction time (ADR-005), never trusting render-time authority.
10. **Sequence to avoid rework:** moderation convergence → selectors/diagnostics → mutation
    primitive+channel lifecycle → role lifecycle+automation safety → high-value capabilities
    (dynamic time/XP, move/reorder) → policy depth (cleanup, mod config) → setup convergence →
    templates/AI → hub last.

---

## Priority Ranking

**P0 — Foundation / must happen first**
- Moderation service convergence (PR1) — closes audit P0; establishes convergence+invariant pattern.
- Shared dynamic selectors + feasibility/exclusion diagnostics (PR2).
- Shared mutation plan/preview/result/reversibility/audit contract (PR3, lands with PR4's consumer).

**P1 — High-value user-facing capability**
- Channel/category lifecycle service + route existing surfaces (PR4).
- Role lifecycle service + non-destructive time/XP semantics + role-ID groundwork (PR5).
- Dynamic time/XP role configuration (replace free-text names) (PR6).
- Channel/category move & reorder manager (PR7).

**P2 — Platform depth & setup convergence**
- Cleanup policy schema/versioning preserving current behavior (PR8).
- Cleanup builder + dry-run + diagnostics (PR9).
- Moderation first-class configuration (roles/destinations/escalation/DMs) (PR10).
- Setup role/moderation/governance sections (PR11) + diagnostics/repair (PR12).

**P3 — Optional expansion**
- Deterministic role templates, then AI-generated templates through review/staging/apply (PR13).
- Persistent + ephemeral Server Management Hub over one shared builder (PR14).

---

## Dependency Graph

```text
PR1 Moderation convergence ──(independent; uses existing emit_audit_action)──► [audit pattern + invariant template]
        │ (pattern reused by every lifecycle PR's invariant + audit wiring)
        ▼
PR2 Shared selectors + feasibility diagnostics
        │                                   │
        ▼                                   ▼
PR3 Mutation/preview/result/audit ───► PR4 Channel/category lifecycle service
   contract (lands w/ PR4 consumer)          │ (route create/delete/restrict/move/rename)
        │                                     ▼
        └──────────────► PR5 Role lifecycle service + non-destructive time/XP + role-ID groundwork
                                  │                         │
                                  ▼                         ▼
                       PR6 Dynamic time/XP config   PR7 Channel move/reorder manager
                       (needs PR2 selectors+PR5)     (needs PR2 selectors + PR3 plan + PR4)
                                  
PR8 Cleanup schema/versioning ──► PR9 Cleanup builder/dry-run (needs PR2 scope selectors)
PR10 Moderation config (needs PR1 convergence + settings/governance pipelines)

PR11 Setup role/mod/governance sections (needs PR2 selectors, PR5 role lifecycle, PR10 mod config, PR8/9 cleanup)
PR12 Setup diagnostics/repair (needs PR2 diagnostics model + lifecycle services for repair staging)
PR13 Role templates → AI templates (needs PR5 role lifecycle + PR3 staged ops; AI through existing gateway)
PR14 Server Management Hub (needs all specialized managers + PR2 health badges; LAST)
```

Critical-path spine: **PR2 → PR3/PR4 → PR5** unblocks the most downstream work. PR1 is off the
critical path (intentionally parallelizable / safe to lead with). Cleanup (PR8/9) and mod-config
(PR10) are independent tracks that can interleave once PR2 lands.

---

## Proposed PR Sequence

> Format per PR: Objective · Scope · Out of scope · Files · New abstractions · Migration/data ·
> UI · Tests · Risks · Definition of done. Detail is front-loaded (PR1–PR5); later PRs are
> lighter and will be re-planned when reached (per `.claude/CLAUDE.md` "2–3 PRs per session").

### PR1 — Moderation service convergence  ·  Risk: Low  ·  **(Recommended first)**
- **Objective:** Route every *manual* moderation action through `services/moderation_service.py`
  and add the generic audit-routing companion event — **without** disturbing `mod_logs` as the
  authoritative moderation history (see *Audit contract* below).
- **Scope:** Rewrite the 7 modals (`views/moderation/modals.py`) and the typed commands
  (`cogs/moderation_cog.py`) to call `moderation_service.{warn,timeout,kick,ban,unban,clear_warnings}`
  instead of inline `member.*`/`guild.*`/`db.*`. Add `emit_audit_action(...)` + a per-action
  `mutation_id` inside the service. Add an AST invariant forbidding direct moderation writes in
  `cogs/moderation*` and `views/moderation*`.
- **Out of scope:** Numbered cases, evidence, appeals, staff notes, escalation policy config,
  new mod-log columns, new UI, mod-log channel routing (all → PR10 / future case system).
- **Files:** `views/moderation/modals.py`, `cogs/moderation_cog.py`, `services/moderation_service.py`,
  `cogs/moderation/_helpers.py` (keep `_can_act_on_interaction` at the view/cog layer),
  new `tests/unit/invariants/test_no_direct_moderation_writes.py`, extend
  `tests/unit/services/test_moderation_service.py`.
- **New abstractions:** None structural — adds a `mutation_id` + a **best-effort** `emit_audit_action`
  companion to existing service functions (optionally a private `_emit_mod_audit(...)` helper).
- **Audit contract (three signals; mirror `resource_provisioning.py:571-613`):** per successful manual
  action — (1) **`mod_logs` row** via `db.log_mod_action` = *authoritative moderation history*
  (unchanged; the schema has **no `mutation_id` column** and PR1 adds none); (2) **`moderation.action_taken`**
  (`EVT_MOD_ACTION`) = domain event (existing); (3) **`audit.action_recorded`** via `emit_audit_action`
  = *generic audit-routing companion for server-logging/audit dashboards — NOT a second moderation
  history*. Signals (2) and (3) are **best-effort** (the helper returns `False` on bus failure): a
  failure there must never invalidate the Discord action or its `mod_logs` row. The two events share
  the `mutation_id` (thread it into the `EVT_MOD_ACTION` payload, additive, for correlation).
- **Migration/data:** **None.** `mod_logs` schema unchanged; `EVT_MOD_ACTION` already catalogued
  (`core/events_catalogue.py:59`). `audit.action_recorded` already exists.
- **UI:** No visible change (behavior-preserving). Same ephemeral messages, same hierarchy checks.
- **Tests:** Each action calls the service exactly once; writes one `mod_logs` row; emits
  `moderation.action_taken` once; emits a best-effort `audit.action_recorded` companion once (sharing
  the `mutation_id`); a simulated companion/event-bus failure does NOT raise or block the `mod_logs`
  write; Discord `Forbidden` still surfaces the same ephemeral error; warn→auto-timeout escalation
  preserved; invariant test catches any direct `member.ban/kick/timeout`, `guild.ban/unban`, or
  `db.add_warning/clear_warnings/log_mod_action` in the two surfaces.
- **Risks:** (a) **action-string drift** — modal/prefix log `"clearwarnings"`, service logs
  `"clear_warnings"`; standardize *new* rows on `"clear_warnings"`, leave historical rows untouched,
  and **normalize the modlogs display** so both `"clearwarnings"` and `"clear_warnings"` render as one
  friendly label (`_ModLogsModal` shows `action.upper()` today). (b) **warn escalation** — `_WarnModal` does warn→
  (if ≥threshold) timeout+clear; orchestrate as sequential service calls, keep the threshold read
  (`services.settings_resolution.resolve_value`) at the view layer. (c) **timeout duration in
  reason** — modal logs `"30m: reason"`; preserve by passing the composite reason, or move duration
  to a structured field (defer to PR10). (d) double-logging if a call-site is missed — the invariant
  prevents regressions.
- **Definition of done:** Both manual surfaces route 100% through the service; `check_architecture
  --mode strict` + `check_quality --full` green; invariant test present and passing; no behavior
  change visible to operators; per action exactly one `mod_logs` row (authoritative), one
  `moderation.action_taken` event, and one best-effort `audit.action_recorded` companion, the two
  events sharing a `mutation_id`.

### PR2 — Shared dynamic selectors + feasibility/exclusion diagnostics  ·  Risk: Medium
- **Objective:** One configurable selector family (channels/categories/roles/threads/members/mixed)
  with single+multi modes, paging/search beyond 25, feasibility filters, structured exclusion
  reasons, and stale-selection revalidation; plus a structured diagnostics/findings model.
- **Scope:** Extend `views/selectors/` (add `MultiRoleSelector` mirroring `MultiChannelSelector`;
  add feasibility/exclusion filtering: `@everyone`, managed/integration/system roles, roles above
  bot top role, channels the bot lacks Manage on); add paging/search wrapper; add a
  `views/selectors/feasibility.py` (or `services/resource_feasibility.py`) producing structured
  `Finding(severity, code, kind, resource_id, name, explanation, remediation, repairable)`; adopt
  in **one** low-risk surface (role exemptions or channel restrict).
- **Out of scope:** Lifecycle mutations, the hub, full adoption across all surfaces (incremental).
- **Files:** `views/selectors/*` (new `multi_role.py`, `paging.py`/`search.py`, `feasibility.py`),
  `views/selectors/__init__.py`, one consumer view, `services/resource_health.py` (consume findings),
  `tests/unit/views/selectors/*`.
- **New abstractions:** `Finding`/`FeasibilityReport` dataclasses (frozen); `ResourceFilter`
  predicate set; paging/search selector wrapper. Owner of the *findings model* is shared (used by
  resource_health, setup readiness, hub badges) → place data model in `utils/` or
  `services/resource_feasibility.py` per `docs/helper-policy.md` (needed by both services and views).
- **Migration/data:** None.
- **UI:** Selected surface gains search/paging + "why excluded" affordances; multi-select where it
  was single. Behavior elsewhere unchanged until adopted.
- **Tests:** >25 resources; search/paging; multi-select bounds; each filter; exclusion reasons +
  counts; stale-selection revalidation; empty-guild guard (existing sentinel pattern).
- **Risks:** speculative breadth — mitigate by shipping only the filters the first 1–2 consumers
  need (helper-policy evidence rule); Discord 25-cap interaction with paging.
- **DoD:** `MultiRoleSelector` + feasibility filtering shipped and adopted in one surface; findings
  model consumed by `resource_health`; tests green; no regressions in existing selector consumers.

### PR3 — Shared mutation plan / preview / result / audit contract  ·  Risk: Medium  ·  *(lands with PR4)*
- **Objective:** Typed request → side-effect-free preview → `confirmed=True` gate → ordered apply
  steps → per-step result + failure classification → `mutation_id` + audit + catalogued event →
  reversibility classification — reusable across lifecycle services.
- **Scope:** Define `services/lifecycle/contracts.py` (or similar): `LifecycleRequest`,
  `LifecyclePreview`, `LifecycleResult`, `StepResult`, `Reversibility{reversible,compensatable,
  irreversible}`, `Outcome{success,partial,blocked,declined,discord_failed,audit_failed}`. Add a
  shared `_emit_lifecycle_audit` wrapper over `emit_audit_action`. Add event-catalogue entries.
  Add the generic AST invariant forbidding new direct lifecycle Discord mutations in cogs/views
  for migrated domains. **Land together with PR4** (channel lifecycle) so it has a real consumer.
- **Out of scope:** Any domain logic (lives in PR4/PR5), true rollback.
- **Files:** new `services/lifecycle/contracts.py`, `core/events_catalogue.py`,
  `tests/unit/invariants/test_no_direct_lifecycle_mutations.py`, `tests/unit/services/lifecycle/*`.
- **New abstractions:** the contract dataclasses above — **mirror `ResourceProvisioningPipeline`'s
  `ProvisioningRequest/Preview/Result` exactly** (frozen dataclasses, literal outcome sets pinned to
  any CHECK constraints, `_now_utc()` per INV-N, function-local cross-package imports).
- **Migration/data:** new append-only `*_lifecycle_audit` table iff PR4 needs one (model on
  migration 030 `resource_provisioning_audit`); otherwise reuse `emit_audit_action` only.
- **UI:** none.
- **Tests:** preview purity (no writes — AST + behavioral); deterministic step ordering; outcome
  classification; audit row + event shape; reversibility classification table.
- **Risks:** over-design — keep the contract minimal and consumer-driven.
- **DoD:** contracts + invariants land *with* PR4's channel service consuming them; tests green.

### PR4 — Channel/category lifecycle service  ·  Risk: Medium-High
- **Objective:** `ChannelLifecycleService` owns rename/edit/overwrite/delete/clone/move/reorder/
  category-sync; existing channel commands+panels route through it; declared creation composes
  `ResourceProvisioningPipeline` (no duplication).
- **Scope:** New service implementing PR3 contracts; route `cogs/channel_cog.py` (lines ~173–462)
  and `views/channels/{create,delete,restrict}_panel.py` through it; snapshot positions/overwrites
  before preview; revalidate before apply; partial-failure reporting.
- **Out of scope:** The move/reorder *panel UI* (PR7); first-class category management surface (PR7).
- **Files:** new `services/channel_lifecycle_service.py` (+ `services/lifecycle/` helpers),
  `cogs/channel_cog.py`, `views/channels/**`, `core/runtime/guild_resources.py` (dispatch via
  `ensure_*`/`resolve_*`), `core/resources/channel_service.py`, tests.
- **New abstractions:** `ChannelLifecycleService` (mirrors provisioning pipeline). Dispatches Discord
  calls only through `core/runtime/guild_resources` helpers (per the no-direct-`create_*` invariant).
- **Migration/data:** optional `channel_lifecycle_audit` table (model on migration 030).
- **UI:** none yet (routing only; behavior preserved).
- **Tests:** route coverage for create/delete/restrict/move/rename; snapshot+revalidate;
  partial-failure; invariant: no direct channel mutations remain in channel cog/views.
- **Risks:** Discord hierarchy/permission races; category-sync side effects; behavior drift during
  routing — mitigate with golden-output tests on existing panels.
- **DoD:** all channel mutations flow through the service; panels unchanged visibly; invariant green.

### PR5 — Role lifecycle service + automation safety + role-ID groundwork  ·  Risk: Medium-High
- **Objective:** `RoleLifecycleService` owns create/edit/delete/reorder/assign/remove with
  centralized hierarchy+manageability checks; make time/XP threshold mutations **field-specific**;
  lay role-ID migration groundwork (dual-read + display-name snapshot).
- **Scope:** New service; route `views/roles/{creation,management}_panel.py` + `cogs/role_cog.py`
  role mutations + `services/role_automation.py` member mutations through it; split
  `utils/db/roles.py` deletes so removing time config clears only time fields and vice-versa
  (delete the row only when no automation fields remain); add ID-keyed read path modeled on
  `role_automation_exemptions` (migration 052).
- **Out of scope:** The dynamic time/XP *selector UI* (PR6); templates (PR13).
- **Files:** new `services/role_lifecycle_service.py`, `views/roles/**`, `cogs/role_cog.py`,
  `services/role_automation.py`, `utils/db/roles.py`, new migration (add `role_id` +
  `display_name` columns to `role_thresholds`, nullable, backfilled lazily), tests.
- **New abstractions:** `RoleLifecycleService` (mirrors provisioning pipeline).
- **Migration/data:** **the trickiest migration** — `role_thresholds` gains nullable `role_id`/
  `display_name`; dual-read (ID first, fall back to normalized name); no destructive name→ID flip
  in this PR. Field-specific delete replaces the full-row `DELETE`.
- **UI:** none yet (routing + persistence safety only).
- **Tests:** time-delete preserves XP fields and vice-versa; row deleted only when empty;
  hierarchy/managed/default exclusion; dual-read resolution; rename/delete diagnostics; invariant:
  no direct role mutations remain in role cog/views.
- **Risks:** name→ID ambiguity (duplicate/renamed roles) — ambiguous matches become diagnostic
  findings, never silent guesses; cache invalidation (`invalidate_xp_threshold_roles`).
- **DoD:** field-specific mutations proven non-destructive; role mutations flow through the service;
  ID groundwork present with dual-read; invariant green.

### PR6 — Dynamic time/XP role configuration (replace free-text names)  ·  Risk: Medium
- **Objective / Scope:** Replace the free-text role-name modal (`views/roles/time_roles_panel.py`,
  `_helpers.py` hardcoded `Neu/Iron/Beacon`) with the PR2 `RoleSelector`/`MultiRoleSelector`;
  persist role IDs (+ display-name snapshot); diagnose stale roles; make hardcoded defaults optional
  templates. Keep one combined Role Automation section. **Out of scope:** templates/AI (PR13).
- **Files:** `views/roles/time_roles_panel.py`, `views/roles/xp_roles_panel.py`, `_helpers.py`,
  `utils/db/roles.py`, tests. **Migration:** flip reads to ID-first (groundwork from PR5).
  **UI:** dropdown selection replaces typed names; "stale role" findings shown.
  **Tests:** ID persistence; stale detection; defaults-as-suggestions; time/XP independence preserved.
  **DoD:** no path persists a nonexistent role name; both sections selector-driven.

### PR7 — Channel/category move & reorder manager  ·  Risk: Medium-High
- **Objective / Scope:** Add the move/reorder panel button: multi-select channels/categories →
  destination + before/after/top/bottom/preserve-order strategy → preview ordering + permission/
  category-sync effects → explicit confirm → audited apply → partial-failure + "Revert Safe Changes".
  First-class category inventory. **Needs:** PR2 selectors + PR3 contracts + PR4 service.
  **Files:** `views/channels/main_panel.py` (+ new move/reorder subview), `channel_lifecycle_service`,
  tests. **UI:** new panel button + flow. **Tests:** deterministic batch order; preview purity;
  partial-failure; unsynced-permission warnings; snapshot/compensation. **Risk:** ordering races;
  never claim atomic reorder. **DoD:** move/reorder via service with preview/audit/repair.

### PR8 — Cleanup policy schema + versioning  ·  Risk: Medium
- **Objective / Scope:** Expressive *versioned* cleanup policy preserving current behavior; map the
  4 atomic levels (Off/Light/Standard/Strict) to equivalent versioned policies; **preserve RC-5**
  (threads inherit parent; thread scope rejected pre-DB). Writes stay in `GovernanceMutationPipeline`.
  **Out of scope:** the builder UI (PR9). **Files:** `governance/cleanup.py`, `governance/writes.py`,
  `services/cleanup_levels.py`/`cleanup_profiles.py`, new migration (policy version + JSONB
  dimensions on `cleanup_policies`), `tests/unit/governance/test_cleanup_scope.py` (keep green).
  **Migration:** additive, behavior-preserving level→policy mapping; no thread rows.
  **Tests:** old levels resolve identically; inheritance chain incl. thread→parent; version migration.
  **DoD:** versioned policy lands with zero behavior change at rollout.

### PR9 — Cleanup builder + dry-run + diagnostics  ·  Risk: Medium
- Presets, scoped bulk assignment (PR2 scope selectors), dry-run "why deleted/why retained" with
  inherited-source explanation, audit. **Out of scope:** schema changes (PR8). **UI:** builder panel
  + setup section hook. **Tests:** dry-run determinism; preset bundles; exemptions; inherited-scope
  explanation. **DoD:** expressive builder + dry-run without deleting.

### PR10 — Moderation first-class configuration  ·  Risk: Medium
- Schema/policy-backed config: moderator/trusted roles+capabilities, mod-log + optional public-log
  destinations, required/optional reasons, default/max durations, user-DM toggle+templates,
  escalation rules, ban delete-message behavior, post-action cleanup hook, hierarchy diagnostics.
  Routes through `SettingsMutationPipeline`/`BindingMutationPipeline`/governance. **Needs PR1.**
  **Out of scope:** numbered cases/evidence/appeals (future case system). **Files:**
  `cogs/moderation/schemas.py`, `services/moderation_service.py`, settings specs, tests.
  **Migration:** settings/bindings (not new mod-log columns). **DoD:** config-backed moderation;
  forward-compatible metadata reserved for cases without migrating a case system.

### PR11 — Setup role/moderation/governance sections  ·  Risk: Medium
- New `SetupSection`s composing PR2 selectors, PR5 role lifecycle, PR8/9 cleanup, PR10 mod config,
  staged as `SetupOperation`s through `apply_operations`. **Invariant:** setup views never import
  pipelines (`test_setup_operations_invariants.py`). **Files:** `views/setup/sections/{roles,
  moderation,governance}.py`, `services/setup_sections.py`, tests. **DoD:** sections register,
  recommend, preview, apply, preserve custom choices.

### PR12 — Setup diagnostics & repair  ·  Risk: Medium
- Stage safe repairs (stale bindings, missing resources, invalid roles, permission blockers) via
  PR2 findings + lifecycle services; improve readiness. **DoD:** repairs staged+reviewed like other
  setup ops; partial-apply safe.

### PR13 — Deterministic + AI role templates  ·  Risk: Medium (AI: High-sensitivity)
- Template schema + validation + review/edit/reorder UI; built-in deterministic templates first;
  then AI generation through the **existing AI gateway** producing strict structured suggestions →
  validation/safety filter → preview → accept/reject/edit → bind-existing-or-create → staged role
  lifecycle ops → explicit apply. **AI never** calls Discord/writes config/grants perms. Audit
  request+model+validation+edits+apply; deterministic fallback. **Needs PR5 + PR3.** **DoD:** AI is
  optional, reviewable, routes through ordinary staged mutations; safety tests pass.

### PR14 — Server Management Hub  ·  Risk: Medium
- One shared hub builder; persistent `!servermanagement` (+aliases) and ephemeral
  `/server-management`; health badges from resource_health/readiness/feasibility; navigation to
  specialized managers; **every callback rechecks capability+target-guild** (ADR-005). **LAST** —
  depends on all managers. **DoD:** both surfaces share one builder/services; no domain logic in hub;
  restoration via persistent-view contracts.

---

## Recommended First PR

**PR1 — Moderation Service Convergence.** *(Confirmed by maintainer.)*

**Why, on the evidence:**
- **The service already exists and is proven.** `services/moderation_service.py` implements
  `warn/timeout/kick/ban/unban/clear_warnings/auto_delete` with the right shape (write → log →
  `bus.emit(EVT_MOD_ACTION)`), and the **auto_delete path is already converged** across counting,
  chain, cleanup, and `message_pipeline` — so the pattern is repo-validated, not theoretical.
- **It is genuinely self-contained.** It depends on neither selectors (PR2) nor the mutation
  primitive (PR3). It can land first with no upstream work.
- **It closes a real P0 today.** All seven modals (`views/moderation/modals.py`) and the typed
  commands (`cogs/moderation_cog.py`) bypass the service, so manual moderation never emits the
  audit-routing companion (`emit_audit_action` → `audit.action_recorded`) and runs on two mutation
  paths instead of one (`mod_logs` still records today, but only the service path emits the companion).
- **It is the cheapest, safest exemplar of the convergence + invariant pattern** that PR4/PR5
  reuse: route a surface through its service, wire `mutation_id`+audit, lock it with an AST invariant.
- **No migration, no new event, no UI change** — `mod_logs` is unchanged and `EVT_MOD_ACTION` is
  already catalogued (`core/events_catalogue.py:59`). Lowest-risk possible opener.
- **It respects `docs/helper-policy.md`** — it consumes existing helpers rather than building
  abstractions ahead of consumers (the trap PR2/PR3 must avoid).

Selectors+diagnostics (PR2) is the broadest foundation but larger and partly speculative until
consumers adopt it; the mutation primitive (PR3) is pure scaffolding better extracted with a real
consumer. Leading with moderation banks a certain win and a reusable pattern first.

---

## Detailed Phase Plans

> The prompt's thematic Phase 1–9 labels are retained below for traceability. **Execution order
> is the Proposed PR Sequence above** (moderation leads). Phase 3 (moderation) = PR1.

### Phase 1 — Shared Resource Safety Foundation  *(= PR2)*
Extend the existing `views/selectors/` package, don't rebuild it. Add `MultiRoleSelector`
(mirror `MultiChannelSelector` in `views/selectors/multi.py`). Add feasibility filtering: exclude
`@everyone`, managed/integration/system roles, roles above the bot's top role, and channels where
`bot` lacks Manage; surface structured exclusion reasons + counts. Add paging/search beyond Discord's
25-cap (the package docstring already names this the intended direction). Add stale-selection
revalidation before preview/apply. Multi-select rules: clamp `max_values` to option count (existing
pattern), keep the empty-guard sentinel. Define a shared `Finding`/`FeasibilityReport` model placed
where both services and views can import it (per helper-policy), consumed by `resource_health`,
setup readiness, and (later) hub badges. Adopt in exactly one low-risk surface first
(role exemptions already uses native multi-role — good first adopter).

### Phase 2 — Mutation Plan / Preview / Audit Primitives  *(= PR3, lands with PR4)*
Mirror `ResourceProvisioningPipeline` precisely: frozen `Request`/`Preview`/`Result`/`StepResult`
dataclasses; literal `Outcome` set pinned to any new CHECK constraint; `Reversibility` enum
(reversible/compensatable/irreversible); a `_emit_lifecycle_audit` wrapper over
`services/audit_events.emit_audit_action` (11 kwargs) plus a best-effort catalogued event via
`core/events.bus.emit`; `_now_utc()` for INV-N; function-local cross-package imports for cycle
discipline. Reuse `services/setup_change_plan.ChangePlanEntry/ChangeValue` shape for preview diffs
where it fits. Ship **with** the first consumer (channel lifecycle) to satisfy the 2-caller rule;
add the generic AST invariant `test_no_direct_lifecycle_mutations.py`.

### Phase 3 — Moderation Service Convergence  *(= PR1, FIRST — see "Recommended First PR")*
Route both manual surfaces through `moderation_service`. Keep `_can_act_on_interaction`
(hierarchy/owner) and the `resolve_value` threshold read at the view/cog layer (the service
deliberately does not re-check perms). Add `mutation_id = uuid4()` + `emit_audit_action(subsystem=
"moderation", mutation_type=action, target=f"user:{target_id}", scope="guild", …)` as a **best-effort
companion emitted after the `mod_logs` write** — a bus failure (helper returns `False`) must never
invalidate the action or its `mod_logs` row — inside one private `_emit_mod_audit` helper. **Three
signals, by design** (mirror `resource_provisioning.py:571-613`): `mod_logs` = authoritative history
(no `mutation_id` column; no migration) · `moderation.action_taken` = domain event ·
`audit.action_recorded` = generic audit-routing companion. Preserve: warn→auto-timeout escalation (sequential service
calls), Discord-`Forbidden` ephemeral surfacing (modal keeps try/except around the service call),
and timeout duration logging. New clear-warning rows log `"clear_warnings"`; historical
`"clearwarnings"` rows are left as-is and the modlogs display normalizes both to one friendly label.
Add AST invariant `test_no_direct_moderation_writes.py`.

### Phase 4 — Channel / Category Lifecycle  *(= PR4, then PR7)*
`ChannelLifecycleService` owns rename/edit/overwrite/delete/clone/move/reorder/category-sync,
dispatching Discord calls only through `core/runtime/guild_resources` helpers and composing
`ResourceProvisioningPipeline` for declared creation + `BindingMutationPipeline` for bindings. Route
`cogs/channel_cog.py` + `views/channels/**` through it (PR4). Then add the move/reorder panel + first-
class category inventory (PR7) on top, with snapshot→revalidate→preview→confirm→apply→partial-failure→
Revert-Safe-Changes.

### Phase 5 — Role Lifecycle and Automation Safety  *(= PR5, then PR6)*
`RoleLifecycleService` owns create/edit/delete/reorder/assign/remove with centralized hierarchy +
managed/default/integration exclusion (one shared contract, replacing per-surface logic). Make
`utils/db/roles.py` deletes field-specific (the current `remove_role_threshold` full-row `DELETE` is
the destructive coupling). Add nullable `role_id`/`display_name` to `role_thresholds`, dual-read
(ID-first, name fallback), modeled on the already-ID-keyed `role_automation_exemptions` (migration
052). Then PR6 swaps the free-text role-name modal for the PR2 selector and persists IDs, with stale-
role diagnostics; defaults (`Neu/Iron/Beacon`) become optional suggestions. One combined section.

### Phase 6 — Cleanup Policy Expansion  *(= PR8, then PR9)*
**Preserve current behavior and the RC-5 thread-rejection invariant.** Add a policy *version* +
JSONB dimensions to `cleanup_policies`; map the 4 atomic levels to equivalent versioned policies so
rollout changes nothing. Writes stay in `GovernanceMutationPipeline`. Keep the channel→category→
guild→default resolver (`governance/cleanup.py`); threads keep inheriting from parent (no thread
rows). Then add the builder + dry-run ("why deleted/why retained", inherited-source) + presets +
diagnostics (PR9).

### Phase 7 — Setup Wizard Convergence  *(= PR11, then PR12)*
Add `SetupSection`s for roles/moderation/governance (PR11) and diagnostics/repair (PR12), composing
PR2 selectors + lifecycle services, staging `SetupOperation`s through `apply_operations` (single-
flight lock, preflight diff). Setup never imports pipelines directly (AST invariant). Repairs are
staged+reviewed like any other op; custom operator choices are never silently overwritten.

### Phase 8 — Role Templates and AI Suggestions  *(= PR13)*
Deterministic built-in templates first (schema + validation + review/edit/reorder + bind-existing-or-
stage-create). Then AI generation through the **existing AI gateway** → strict structured suggestion
(name/purpose/color/hoist/mentionable/optional threshold; **no permissions**) → validation/safety
filter/duplicate detection/hierarchy feasibility → preview → accept/reject/edit → staged role
lifecycle + automation ops → explicit apply. AI never mutates Discord/config; deterministic fallback
when unavailable; full audit of request/model/validation/edits/apply.

### Phase 9 — Server Management Hub  *(= PR14, LAST)*
One shared hub builder behind persistent `!servermanagement` and ephemeral `/server-management`;
compact health badges from resource_health/readiness/feasibility; navigation to specialized managers;
**every callback rechecks capability + target guild** (ADR-005); restoration via persistent-view
contracts; zero domain logic in the hub.

---

## Migration Strategy

- **Role name → ID (highest care):** additive nullable `role_id`/`display_name` on `role_thresholds`;
  dual-read ID-first with normalized-name fallback; **no destructive flip** in the groundwork PR.
  Ambiguous/missing names become diagnostic findings requiring operator resolution — never a silent
  guess. Model on the shipped ID-keyed `role_automation_exemptions` (migration 052).
- **Field-specific threshold deletes:** replace the full-row `DELETE` in `remove_role_threshold` with
  column-clearing; delete the row only when no automation fields remain; keep the
  `invalidate_xp_threshold_roles` cache drop.
- **Cleanup versioning:** additive policy-version + JSONB dimensions; level→policy mapping must be
  behavior-identical at rollout; **no thread rows** (RC-5 preserved).
- **Cache invalidation:** role rename/delete, channel/category move/delete, binding/policy/setup-apply
  changes must invalidate resource/governance/selector/readiness caches (extend existing invalidators).
- **Existing guild settings compatibility:** all new config rides `SettingsMutationPipeline`/
  `BindingMutationPipeline`/governance; default-on-missing via `services.settings_resolution`.
- **Migration numbering:** next sequential file in `disbot/migrations/`; the runner rejects bad/
  duplicate version files (RC-6) — match the existing format exactly.
- **Fallback behavior:** every new resolver falls back to current behavior on missing/invalid data
  (mirror `resolve_value`'s "malformed → SettingSpec default" pattern).

## Test Strategy

- **Unit:** selector filters/paging/multi-select/exclusion-reasons/stale; reversibility classification;
  threshold field-independence; cleanup level→policy mapping.
- **Service:** moderation actions (one `mod_logs` row + one `moderation.action_taken` + one best-effort
  `audit.action_recorded`; the two events share a `mutation_id`; a simulated bus failure leaves DB
  state authoritative); lifecycle preview purity + deterministic ordering + per-step results; role
  hierarchy/exclusion.
- **View:** routed panels preserve prior output (golden-output); modal error surfacing.
- **Invariant (AST, `tests/unit/invariants/`):** no direct moderation writes in mod cog/views; no
  direct lifecycle Discord mutations in migrated channel/role cog/views; setup views don't import
  pipelines; cleanup rejects thread scope pre-DB (RC-5); no silent auto-create (existing).
- **Migration:** role-ID dual-read + ambiguity→finding; cleanup version mapping behavior-identical.
- **Integration/manual Discord:** bot role below/above target; >25 roles/channels; move with unsynced
  perms; permission removed between preview and apply; partial-batch + Revert-Safe-Changes; deleted
  binding/policy diagnostics; thread/forum inheritance explanation; persistent hub restoration;
  ephemeral parity/privacy; AI themed-template review/edit/reject/apply.
- **Partial-failure / stale-resource / permission-hierarchy / AI-template-validation:** explicit
  dedicated tests per the roadmap's verification plan.

## Observability and Audit Strategy

- Every high-impact mutation carries a `mutation_id` (uuid4) threaded through audit + event.
- Moderation (three signals): `mod_logs` row = authoritative history; `moderation.action_taken`
  (`EVT_MOD_ACTION`) = domain event; `audit.action_recorded` (via **best-effort** `emit_audit_action`)
  = generic audit-routing companion (not a second history). The two events share a `mutation_id`;
  companion/event failures never invalidate the `mod_logs` write.
- Lifecycle services: append-only `*_lifecycle_audit` row (model on migration 030) + best-effort
  catalogued event via `core/events.bus`; outcome literal sets mirror CHECK constraints.
- Partial failures expose completed/failed/unattempted steps; findings include remediation +
  `repairable` flag; metrics for blocked/failed/partial/compensated/stale-plan outcomes.
- Logging destinations + diagnostics + hub badges *consume* these events; feature surfaces never
  implement their own audit delivery (matches the provisioning pipeline's contract).
- Privacy/retention: define redaction + retention + audit-channel visibility **before** storing richer
  moderation evidence, cleanup message samples, or AI prompts.

## Risks and Mitigations

- **Discord hierarchy/permission races:** revalidate immediately before apply; report stale plans.
- **Permission change between preview and apply:** re-check in the apply step (not just preview).
- **Partial Discord failures:** record actual final state; classify; offer safe compensation/repair;
  never call recreation "rollback."
- **Stale cached resources:** stale-selection revalidation in selectors; cache invalidation on every
  mutating path.
- **Role-ID migration ambiguity:** ambiguous/missing → diagnostic finding, never silent bind.
- **Cleanup behavior change at rollout:** level→policy mapping is behavior-identical; pin with tests;
  preserve RC-5.
- **Persistent panel authorization:** recheck capability + target-guild on every callback (ADR-005),
  never trust render-time authority.
- **AI safety:** structured-output enforcement, count/name/color constraints, duplicate detection,
  permission prohibition, hierarchy feasibility, rate limits, audit metadata, deterministic fallback.
- **Privacy/retention:** policy defined before richer evidence/sample storage.
- **Speculative abstraction (PR2/PR3):** ship only what the first 1–2 consumers need; extract the
  shared primitive *with* a consumer (helper-policy 2-caller rule).
- **Behavior drift during routing (PR1/PR4/PR5):** golden-output tests on existing panels/commands.

## Open Questions

Per the roadmap, **no unresolved maintainer decision blocks the sequence.** Two minor implementation
choices are decidable by the implementer at PR time (defaults noted; not blockers):

1. **Moderation clear-warning label (PR1):** new rows log `"clear_warnings"` (the service value);
   historical `"clearwarnings"` rows are left as-is and the modlogs display normalizes both to one
   friendly label. Implementer-level; not a blocker.
2. **Lifecycle audit storage (PR3/PR4):** dedicated `*_lifecycle_audit` table vs `emit_audit_action`
   only. *Default:* start with `emit_audit_action`; add a table when partial-step/snapshot detail
   needs structured persistence.

## Final Handoff Prompt

> **Task:** Implement PR1 — Moderation Service Convergence — on branch
> `claude/busy-darwin-zyPD2` in `menno420/superbot`. Planning-only context lives in this file and
> `docs/planning/server-management-roadmap-2026-06-05.md`.
>
> **Goal:** Route every *manual* moderation action through `services/moderation_service.py` and add
> the best-effort `audit.action_recorded` companion, with **zero operator-visible behavior change** and
> `mod_logs` unchanged as the authoritative moderation history.
>
> **Do:**
> 1. In `views/moderation/modals.py` (the 7 modals) and `cogs/moderation_cog.py` (typed commands +
>    the `_log` helper at ~line 48), replace inline `member.{ban,kick,timeout}` / `guild.unban` /
>    `db.{add_warning,clear_warnings,log_mod_action}` with calls to
>    `moderation_service.{warn,timeout,kick,ban,unban,clear_warnings}`. Pass `actor_id=interaction.user.id`
>    (or `ctx.author.id`).
> 2. Keep `_can_act_on_interaction` (hierarchy/owner) and the `services.settings_resolution.resolve_value`
>    threshold read at the view/cog layer. Keep the `try/except discord.Forbidden` ephemeral surfacing
>    around the service call. Preserve the warn→auto-timeout escalation as sequential service calls
>    (`warn`, then if count ≥ threshold: `timeout` + `clear_warnings`).
> 3. Inside `moderation_service.py`, add a per-action `mutation_id = uuid4()` and call
>    `services.audit_events.emit_audit_action(subsystem="moderation", mutation_type=<action>,
>    target=f"user:{target_id}", scope="guild", guild_id=…, prev_value=…, new_value=…,
>    actor_id=…, actor_type="moderator", occurred_at=_now_utc())` — **best-effort**, after the `mod_logs` write; a companion failure (helper
>    returns `False`) must never invalidate the action or its `mod_logs` row (which has no `mutation_id`
>    column — add no migration). Three signals: `mod_logs` = authoritative history ·
>    `moderation.action_taken` = domain event · `audit.action_recorded` = generic companion.
>    Keep the existing `bus.emit(EVT_MOD_ACTION, …)`. (A private `_emit_mod_audit(...)` helper is fine.)
> 4. Action string: have *new* clear-warning rows log `"clear_warnings"` (the service value); leave
>    historical `"clearwarnings"` rows untouched; normalize the `_ModLogsModal` display so both render
>    as one friendly label (it currently shows `entry['action'].upper()`).
> 5. Add `tests/unit/invariants/test_no_direct_moderation_writes.py` (AST) asserting no direct
>    `member.ban/kick/timeout`, `guild.ban/unban`, or `db.add_warning/clear_warnings/log_mod_action`
>    write-calls remain in `cogs/moderation*` or `views/moderation*`. Extend
>    `tests/unit/services/test_moderation_service.py` to assert per action one `mod_logs` row + one
>    `EVT_MOD_ACTION` + one best-effort `audit.action_recorded` (events sharing a `mutation_id`), and
>    that a simulated bus failure neither raises nor blocks the `mod_logs` write.
>
> **Don't:** add cases/evidence/appeals/notes, change the `mod_logs` schema (no `mutation_id` column),
> add new events, add a migration, or change moderation action flows/UX — the only cosmetic tweak
> allowed is normalizing the clear-warnings label in the modlogs display. Don't touch the
> already-converged `auto_delete` callers (counting/chain/cleanup/message_pipeline) — use them as the
> reference pattern.
>
> **Reference contract:** `services/resource_provisioning.py` (`emit_audit_action` usage, `_now_utc`,
> function-local imports). `auto_delete` in `moderation_service.py` shows the exact write→log→emit shape.
>
> **Gate before push (Python 3.10):** `python3.10 scripts/check_architecture.py --mode strict` and
> `python3.10 scripts/check_quality.py --full` must both exit 0. Then commit and push to
> `claude/busy-darwin-zyPD2`. Open a PR at end of session (standing maintainer request in
> `.claude/CLAUDE.md`).

---

## Verification of this plan (how to confirm it before/after PR1)

- **Re-confirm bypass surface:** `rg "\.(ban|kick|timeout|unban)\(|db\.(add_warning|clear_warnings|log_mod_action)" disbot/cogs/moderation_cog.py disbot/views/moderation/modals.py -n` — should be empty *after* PR1 (except reads like `get_mod_logs`).
- **Confirm convergence reference:** `rg "moderation_service\." disbot -n` — auto_delete callers stay; manual callers appear in the two surfaces after PR1.
- **Run the gates:** `python3.10 scripts/check_architecture.py --mode strict`; `python3.10 scripts/check_quality.py --full` (CI mirror, Python 3.10).
- **Targeted tests:** `python3.10 -m pytest tests/unit/services/test_moderation_service.py tests/unit/invariants/test_no_direct_moderation_writes.py -q`.
- **Discord smoke check (PR1):** modal `safe_defer`/`safe_followup` timing is unchanged after routing through the service (the service call sits between defer and followup) — warn/timeout/kick/ban/unban/clearwarnings each respond once (no double-ack), and `Forbidden` still yields the same ephemeral error.
- **Architecture spot-check:** views→services import is legal; confirm no `services/`→`views/` import was introduced (zero-tolerance rule).
