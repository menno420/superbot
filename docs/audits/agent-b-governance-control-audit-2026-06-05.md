# Agent B governance/control audit — 2026-06-05

> **Status:** `audit`

> **Superseded (2026-06-05):** reconciled into
> [`../planning/superbot-audit-consolidation-2026-06-05.md`](../planning/superbot-audit-consolidation-2026-06-05.md)
> (verified, RC-n IDs). Read that first; this raw audit is historical context.

> **Scope:** docs-only report of the Agent B audit over governance, permissions, visibility, command access, setup/onboarding, cleanup policy, interactions, sessions, panels, automation, participation, and related ownership docs.
>
> **Base inspected:** GitHub `main`, latest observed merge during PR creation: `eb20bac10b7b09b570c669f1c7ac150cde348a53`.
>
> **Execution limit:** the audit was performed through the GitHub connector. Local checkout commands and test execution were not available in the sandbox because GitHub could not be cloned from the environment. Treat all code-state findings below as source-read findings, not local test results.

---

## Most important findings

### 1. Critical: thread visibility cache identity is wrong

**Status:** confirmed source-read finding.

`GovernanceContext` and the resolver support `thread -> channel -> category -> guild` visibility resolution, but the governance cache key uses only `guild_id`, `channel_id`, tier, and optionally role fingerprint. It omits `thread_id`.

**Why this matters:** a visibility result for a thread can be cached under the parent channel key and then reused for the parent channel or another sibling thread until TTL or invalidation. This can make help visibility, command cleanup policy, and subsystem visibility wrong in thread contexts.

**Primary files:**

- `disbot/governance/models.py`
- `disbot/governance/resolver.py`
- `disbot/governance/cache.py`
- `disbot/migrations/009_thread_scope_constraint.sql`

**Recommended fix:** add `thread_id` to the cache key, or deliberately bypass cache for thread-scoped contexts. Add a regression test that resolves two contexts with the same parent channel but different `thread_id` values and proves they cannot cache-bleed.

---

### 2. Critical: persistent views fail open when no anchor is found

**Status:** confirmed source-read finding.

`PersistentView.interaction_check()` allows interaction when `message_anchor_manager.get_by_message_id()` returns `None`.

**Why this matters:** for persistent, restart-safe, owner-scoped views, a missing anchor is usually stale/orphaned state. Failing open prioritizes availability but weakens ownership and stale-panel protection.

**Primary files:**

- `disbot/core/runtime/persistent_views.py`
- `disbot/core/runtime/message_anchor_manager.py`

**Recommended fix:** decide and document the policy. Prefer fail-closed by default for owner-scoped persistent panels, with an explicit opt-in exception for public persistent panels.

---

### 3. High: settings and bindings still use placeholder authority checks

**Status:** confirmed source-read finding.

`SettingsMutationPipeline` and `BindingMutationPipeline` are good central mutation seams, but both still use visibility-tier style authority checks and explicitly document that Phase 4.5 should replace them with typed capability resolution.

**Why this matters:** expanding settings/bindings UI before this is fixed risks inconsistent permission semantics between governance capabilities, settings, bindings, setup, and command execution.

**Primary files:**

- `disbot/services/settings_mutation.py`
- `disbot/services/binding_mutation.py`
- `disbot/core/runtime/subsystem_schema.py`

**Recommended fix:** wire settings and binding writes through typed capability checks before expanding operator-facing settings surfaces.

---

### 4. High: cleanup policy write validation accepts broader scope than cleanup schema supports

**Status:** confirmed source-read finding.

`GovernanceMutationPipeline` allows `thread` in the shared scope set and uses that set for cleanup policy writes, but migration `009_thread_scope_constraint.sql` explicitly says cleanup policies intentionally keep their original non-thread constraint.

**Why this matters:** a thread cleanup write can fail at the DB layer instead of being rejected deterministically by the service layer with a clear message.

**Primary files:**

- `disbot/governance/writes.py`
- `disbot/governance/cleanup.py`
- `disbot/migrations/004_governance_tables.sql`
- `disbot/migrations/009_thread_scope_constraint.sql`

**Recommended fix:** split scope validation into visibility scopes and cleanup scopes. Visibility can allow thread; cleanup should reject thread before DB write.

---

### 5. High: tests/checks were not executable in the audit environment

**Status:** limitation, not a repo bug.

The audit could not run local `git`, `rg`, `pytest`, `scripts/check_architecture.py`, or `scripts/check_quality.py` because a local checkout was unavailable.

**Why this matters:** several architecture docs claim CI/test enforcement for invariants, but this audit could only verify source content and references, not actual pass/fail state.

**Recommended follow-up:** run the full requested Agent B test/check list in a real checkout before treating this as final verification.

---

## Current state summary

The governance/control layer is significantly more centralized than earlier stale summaries suggested. Command admission is especially strong: `BootstrapAccessCog` installs both the prefix global check and the slash `tree.interaction_check`, and `config.INITIAL_EXTENSIONS` loads it first.

The main remaining problems are not random scattered command guards. They are deeper platform seams:

- cache identity does not fully match resolver identity;
- persistent panels do not fail safely when anchor state is missing;
- settings/bindings mutation authority is not yet capability-native;
- cleanup policy and cleanup feature ownership are still easy to confuse;
- setup/onboarding is mostly durable-anchor based, but some legacy and recovery paths still drift.

This means Analysis C/D can continue, but they should treat command/help visibility, feature views, cleanup, setup sections, AI/internal execution bypasses, and BTD6/AI setup surfaces as caveated until cross-audit consolidation.

---

## Confirmed problems by area

### Governance visibility and execution

#### GOV-1 — Thread visibility cache mismatch

**Severity:** critical.

Confirmed above as the most important finding. The schema and resolver gained thread support, but cache key identity did not.

**Likely symptom:** visibility decisions in one thread can affect the parent channel or another thread until the 60-second TTL expires or cache is invalidated.

**Root cause:** the cache key is based on the parent channel context, while resolver inputs include a more specific thread scope.

---

#### GOV-2 — Visibility, execution, and exposure remain partially conflated

**Severity:** medium.

`governance/models.py` documents visibility, execution, and exposure as distinct concepts, but the current implementation intentionally keeps them unified for simplicity.

**Why this matters:** hidden-from-help, cannot-execute, and should-not-be-discoverable are not always the same policy for AI, scheduled jobs, diagnostics, setup, and owner-only flows.

**Recommendation:** do not add more feature-specific exceptions. Keep current model until A/C/D consolidation identifies where a real split is needed.

---

#### GOV-3 — Internal execution bypass has audit coverage, but should stay tightly scoped

**Severity:** medium.

`resolve_execution(check_visibility=False)` skips visibility and writes a best-effort audit row through `_audit_internal_bypass()`.

**Positive:** the bypass is explicit and auditable.

**Risk:** if normal feature code starts using `check_visibility=False`, visibility/execution guarantees collapse.

**Recommendation:** D should verify AI/BTD6 internal flows are the only intended users and that public command/view code never uses the bypass.

---

### Command access and command routing

#### CMD-1 — Prefix and slash command admission are centralized

**Severity:** positive finding.

`BootstrapAccessCog` owns both command entry gates:

- prefix: `bot.add_check(self._channel_guard)`;
- slash/app commands: `bot.tree.interaction_check = self._slash_access_check`.

Both delegate to `core.runtime.command_access.resolve_command_access`.

**Impact:** older concerns that every cog had to implement its own channel admission are now mostly obsolete.

---

#### CMD-2 — Command access and subsystem governance are separate systems

**Severity:** medium.

Command access decides where commands may be invoked. Governance visibility decides which subsystems/capabilities are visible/executable in that context.

**Risk:** help/settings UX can drift if one layer is shown but not the other.

**Recommendation:** Analysis C should verify help output and command-denial feedback make both layers understandable to server operators.

---

### Settings, bindings, and configuration

#### SET-1 — Settings mutation service is structurally good but permission-incomplete

**Severity:** high.

`SettingsMutationPipeline` centralizes validation, DB write, audit, cache invalidation, and event emission. Its own docs still state the authority check is a placeholder.

**Recommendation:** complete typed capability enforcement before broadening settings manager surfaces.

---

#### SET-2 — Binding mutation service cache invalidation is currently a documented no-op

**Severity:** medium.

`BindingMutationPipeline._invalidate_cache()` currently logs a no-op until a later phase.

**Risk:** safe only if all current binding readers bypass cached config or re-read authoritative DB state.

**Recommendation:** Analysis A/B should verify every current binding reader. If any cached binding read exists, wire invalidation now.

---

#### SET-3 — AI setting projection is embedded in generic settings mutation

**Severity:** medium.

`SettingsMutationPipeline.set_value()` includes special projection from legacy AI settings into the typed AI guild policy table.

**Risk:** this is probably a compatibility bridge, but it is domain-specific logic inside a generic writer.

**Recommendation:** Analysis D should verify this projection is intentional, tested, and consistent with AI ownership docs.

---

### Setup wizard and onboarding

#### SETUP-1 — Main setup flow is mostly durable-anchor based now

**Severity:** positive finding with caveat.

`!setup` and `/setup` route to a workspace flow that posts or edits one setup anchor message in `#superbot-setup`. Slash receives an ephemeral pointer, but the main wizard state is durable in the workspace.

**Impact:** this mostly matches the no-ephemeral direction for main menus/wizards.

---

#### SETUP-2 — Legacy `/setup-hub` remains ephemeral

**Severity:** medium.

`/setup-hub` still sends the legacy hub/readiness response ephemerally.

**Recommendation:** decide whether this is explicitly deprecated compatibility, or convert it to the same workspace-anchor model as `/setup`.

---

#### SETUP-3 — Launcher recovery is not fully self-healing

**Severity:** medium.

When `_resume_one_launcher()` cannot fetch the stored setup launcher message, it returns `False` but does not clearly clear stale session message IDs or repost.

**Risk:** setup session state can point at a missing launcher until an operator manually re-enters a recovery path.

**Recommendation:** add deterministic stale-marker/repost behavior.

---

#### SETUP-4 — Skip provenance gap is explicitly unfinished

**Severity:** medium.

Wizard docs state that without operation provenance, stale draft rows may remain after skipping a section.

**Recommendation:** verify all current setup sections stage operations with `section_slug` provenance and add regression tests for skip clearing.

---

### Interactions, sessions, panels, and views

#### UI-1 — BaseView is a strong shared abstraction

**Severity:** positive finding.

`BaseView` centralizes invoker restriction, public access opt-in, timeout disable behavior, message tracking, and error handling.

**Recommendation:** Analysis C/D should verify feature views use `BaseView` unless they have a documented reason not to.

---

#### UI-2 — Interaction helpers exist, but full adoption still needs verification

**Severity:** medium.

`safe_defer`, `safe_followup`, and `safe_edit` are present and well-shaped, but the helper module notes adoption across cogs lands later.

**Risk:** I/O-heavy callbacks that do not defer can still produce Discord `Interaction Failed` behavior.

**Recommendation:** run/extend the interaction invariant checks and inspect feature views for slow callbacks without `safe_defer`.

---

#### UI-3 — Panel lifecycle has two legitimate patterns that should not grow into three

**Severity:** medium.

There are two current panel paths:

- ordinary timeout panels through `views.base.send_panel()`;
- anchored persistent panels through `core.runtime.panel_manager.get_or_render_panel()` and `message_anchor_manager`.

**Recommendation:** document when to use each. New feature work should not introduce a third panel lifecycle pattern.

---

### Cleanup policy and cleanup feature behavior

#### CLEAN-1 — Cleanup policy and prohibited-word cleanup are different concerns but share confusing naming

**Severity:** medium.

Governance owns command cleanup policy resolution. `CleanupCog` still owns prohibited words, history cleanup, and related caches.

**Risk:** future agents may confuse governance cleanup policy with moderation/prohibited-word cleanup feature behavior.

**Recommendation:** clarify docs/UI naming: `command cleanup policy` vs `prohibited-word cleanup` / `moderation cleanup`.

---

#### CLEAN-2 — Env cleanup whitelist remains a fallback drift point

**Severity:** low to medium.

`CLEANUP_WHITELIST_CHANNELS` remains env-driven as a backward-compatible cleanup fallback.

**Recommendation:** migrate the fallback into DB-backed cleanup policy or explicitly document it as legacy-only.

---

### Automation, participation, and role templates

#### AUTO-1 — Automation has an owner-gated mutation pipeline

**Severity:** medium.

`AutomationMutationPipeline` centralizes automation rule writes and requires the guild owner by default.

**Risk:** this is clear locally, but it is not obviously integrated with governance capabilities.

**Recommendation:** decide whether automation remains special owner-only policy or becomes a typed governance capability.

---

#### PART-1 — Participation mutation follows the service-layer pattern

**Severity:** positive finding.

`ParticipationMutationPipeline` centralizes per-user participation writes, authority validation, audit, cache invalidation, and event emission.

**Recommendation:** Analysis C should verify feature surfaces call this service rather than DB helpers directly.

---

#### ROLE-1 — Role templates are declarations, not applied policy

**Severity:** low.

`governance/role_templates.py` only declares recommended templates/collections. Runtime matching and provisioning are deferred.

**Recommendation:** setup/role features must not treat templates as applied state.

---

## Architecture drift and inconsistencies

1. **Thread visibility support is only partially completed.** Schema and resolver were updated; cache identity was not.
2. **Cleanup scope support differs from visibility scope support.** This is intentional, but write validation does not fully reflect it.
3. **Settings/bindings mutation ownership is ahead of authority ownership.** The central service seam exists, but typed capability enforcement is still pending.
4. **Setup has both durable workspace and legacy ephemeral hub surfaces.** This can be acceptable only if the legacy surface is intentionally compatibility-only.
5. **Panel lifecycle is split between timeout views and anchored persistent views.** This is manageable, but new feature work should not add more patterns.
6. **Cleanup naming mixes governance command cleanup and moderation/prohibited-word cleanup.** The code can support this split, but docs/UI should make it explicit.

---

## Root causes vs symptoms

### Root causes

- Cache key identity did not evolve with thread-scope resolution.
- Permission authority is split between placeholder tier checks and intended capability checks.
- Persistent view ownership relies on optional anchor state but does not define a strict missing-anchor policy.
- Cleanup policy and cleanup feature responsibilities are named too similarly.
- Some setup wizard flows were migrated incrementally, leaving compatibility paths with older ephemeral behavior.

### Symptoms

- Help/visibility may be wrong in threads.
- Stale/orphaned persistent panel messages can still be interactive.
- Settings/binding writes may allow or deny based on broad tier rather than exact capability.
- Thread cleanup writes may fail late in the DB instead of early in the service layer.
- Operators may see inconsistent setup behavior between `/setup` and `/setup-hub`.

---

## Missing verification and test coverage

The following should be verified in a real checkout:

- `git status --short`
- `git branch --show-current`
- `git log --oneline -5`
- `git remote -v`
- `pytest tests/unit/governance`
- `pytest tests/unit/views/setup`
- `pytest tests/unit/views/settings`
- `pytest tests/unit/slash`
- runtime interaction/session/panel tests
- `python scripts/check_architecture.py`
- `python scripts/check_quality.py`

Recommended new or strengthened tests:

1. **Thread visibility cache isolation:** same guild/channel/tier, different thread IDs, different visibility overrides.
2. **PersistentView missing-anchor behavior:** missing anchor, stale anchor, owner mismatch, and explicit public-panel exception.
3. **Cleanup scope validation:** thread cleanup write fails in service validation before DB.
4. **Settings/bindings capability enforcement:** mutation is checked against declared capability, not only broad tier.
5. **Setup skip provenance:** skip removes all recommended rows for the section and preserves only deliberate custom rows.
6. **Interaction defer adoption:** all I/O-heavy callbacks use `safe_defer` or a documented immediate-response path.

---

## Cross-compartment handoff notes

### For Analysis A — platform/runtime/data

Verify:

- governance cache key behavior for thread/category/guild state;
- persistent-view recovery and missing-anchor fail-open behavior;
- `message_anchor_manager.restore_anchors()` timing and duplicate-view protection;
- `panel_manager` vs `send_panel` lifecycle boundaries;
- whether binding cache invalidation no-op is safe for current readers;
- migration behavior for unsupported thread cleanup writes;
- local execution of tests and architecture/quality scripts.

### For Analysis C — general cogs/features

Verify:

- feature cogs do not duplicate permission logic beyond Discord decorators and central gates;
- help output reflects command access and subsystem visibility clearly;
- cleanup UI/panel behavior, especially prohibited-word and history-cleanup paths;
- feature views consistently use `BaseView`, `safe_defer`, and shared UI abstractions;
- prefix/slash parity for settings/setup/cleanup/admin surfaces.

### For Analysis D — BTD6 and AI

Verify:

- AI use of `resolve_execution(check_visibility=False)` is restricted to trusted internal flows;
- AI settings projection in `SettingsMutationPipeline` matches AI policy ownership and tests;
- BTD6/AI setup sections stage operations with proper provenance;
- BTD6/AI command visibility/help behavior respects command access and governance;
- no BTD6/AI domain policy is embedded in generic governance/setup code beyond intentional schema references.

---

## Recommended next steps

### Fix before major new feature work

1. Fix governance cache identity for thread-scoped contexts.
2. Decide and implement persistent-view missing-anchor policy.
3. Split cleanup vs visibility valid scope sets in governance writes.
4. Wire settings/bindings authority to typed capabilities if new settings surfaces are planned.
5. Run the missing local tests/checks in a real checkout.

### Can wait until after A/C/D consolidation

1. Full visibility/execution/exposure split.
2. Cleanup prohibited-word service migration.
3. `/setup-hub` deprecation or workspace-anchor conversion.
4. Broader feature-view selector/list parity cleanup.
5. Automation owner-only vs governance-capability decision.

---

## Agent B verdict

The governance/control layer is not blocked for parallel Analysis C/D work, but it has important platform risks that should be tracked before implementation planning.

**Continue C/D with caveats.** Treat command/help parity, feature-view lifecycle, cleanup behavior, setup section behavior, AI/internal execution bypasses, and BTD6/AI setup/config surfaces as areas requiring direct verification.
