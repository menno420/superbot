# Cleanup — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `cleanup` · **Type:** server-fn · **Family:** moderation
> **State:** ◐ assessed · **Assessed:** 2026-06-29 · **Certified:** —
> Source: `disbot/cogs/cleanup_cog.py` (`!cleanup`/`!wordmenu`/`!cleanuphistory` + the message-pipeline
> `CleanupStage`) · `disbot/cogs/cleanup/panel.py` (the hub) · `disbot/cogs/cleanup/schemas.py`
> (DomainPanelSpec) · `disbot/services/history_cleanup.py` · `disbot/services/cleanup_levels.py` ·
> `disbot/services/cleanup_profiles.py` · `disbot/services/cleanup_diagnostics.py` ·
> `disbot/governance/writes.py` (`set_cleanup_policy_for_scope` → `GovernanceMutationPipeline`) ·
> `disbot/views/setup/sections/cleanup.py` · folio `docs/subsystems/server-management.md`

> Assessed during the completion-first arc (Q-0209). Cleanup is the bot's **channel-hygiene + prohibited-
> word + cleanup-policy** layer: a message-pipeline stage that filters prohibited words (exact + opt-in
> anti-evasion) and enforces command-access policy, a `!cleanuphistory` bulk sweep (keyword / commands /
> prohibited / spam / **embeds / links / attachments** modes + an `older:<duration>` age gate), and a
> per-scope cleanup-level hierarchy (Off/Light/Standard/Strict + custom) resolved guild→category→channel.
> Every write routes through the audited `GovernanceMutationPipeline`
> (DB + `governance_audit_log` + `audit.action_recorded` in one transaction) and every auto-delete
> through `moderation_service.auto_delete`. The remaining honest gaps are a hardcoded spam window
> (needs a config-input widget to be a real setting) and the live walkthrough/owner ✔.

## Rubric (server function)

### A. Functional completeness
- [x] **Core promise delivered** — prohibited-word filter (exact `\bword\b` + opt-in obfuscation match
      via `utils/text_obfuscation.py`), command-access enforcement, and four history-sweep modes
      (`history_cleanup.py`); awkward cases handled (already-deleted → audit still logs; no-perms caught;
      DM context safe; stale/ineffective scope rows flagged in diagnostics).
- [x] **Best-in-class sub-options** — ✅ levels + custom tuning + 6 setup profiles + **7 history
      modes** (keyword/commands/prohibited/spam + embeds/links/attachments, ✅ #2 this run) + an
      `older:<duration>` age gate composable with any mode (✅ #3 this run); Carl-bot/MEE6/Dyno parity
      on history filters reached.
- [x] **Failure modes honest** — auto-delete catches NotFound/Forbidden/HTTPException (logs the rule even
      on NotFound for audit completeness); history sweep reports scanned/matched/deleted/failed counts.
- [x] **Idempotent** — plan build is side-effect-free; apply is idempotent (already-deleted = success).

### B. Reachability & UI
- [x] **Command panel** — `!cleanup` → `CleanupPanelView` (overview embed + 5 buttons: Prohibited Words /
      Logging Status / Settings / Cleanup Policies / Refresh).
- [x] **Reachable every natural way** — `!cleanup`/`!wordmenu`/`!cleanuphistory` entry points + Help hook
      (`build_help_menu_view`) + Moderation-hub child (`parent_hub: moderation`).
- [x] **Integrated into Setup** — `views/setup/sections/cleanup.py` (Cleanup Profiles → `SetupOperation`
      drafts → Final Review → `governance.writes.set_cleanup_policy_for_scope`).
- [x] **Return navigation** — every child panel attaches a back-to-cleanup button; no dead-ends.
- [x] **In-place, not spammy** — overview edits in place; helper/blocked notices auto-delete after a delay.

### C. Convenience
- [x] **Bulk + low-step** — `!cleanuphistory` sweeps up to 1000 messages in one confirmed (✅/❌) action,
      one audit entry per sweep.
- [x] **Defaults + presets** — fallback default Standard (5s); 6 setup profiles (Off/Light/Standard/
      Strict/Silent Bot/Moderation Safe), deterministic builders.
- [x] **Clear feedback** — sweep counts; policy dry-run preview (current→new + source + warnings);
      diagnostics panel shows inherited-from source + stale/ineffective flags.

### D. Authority & safety
- [x] **Authority re-checked at callback** — policy apply calls `interaction_is_admin()` before the write;
      history command `@has_permissions(manage_messages=True)`; word add/remove `administrator`; backstop
      `GovernanceMutationPipeline._validate_authority`.
- [x] **All writes through the audited seam** — policy writes via `governance.writes` →
      `GovernanceMutationPipeline.set_cleanup_policy` (DB + `governance_audit_log` + `emit_audit_action`
      + `EVT_CLEANUP_CHANGED`/`EVT_CACHE_INVALIDATED` in one txn); auto-deletes via
      `moderation_service.auto_delete` (`auto_delete:{rule}` audit row).
- [N/A] **Provisioning pipeline** — cleanup creates no resources; it operates on existing channels +
      its own governance tables.
- [x] **Reuses governance** — cleanup levels share the governance resolver + cache-invalidation + audit
      lane; no second allowlist.

### E. Configuration
- [x] **Pipeline contract** — no scalar settings; configuration is **domain config** (the
      `cleanup_policies` governance table) written only through the audited pipeline; no raw DB writes.
- [x] **config-input widgets** — scope + level + custom-tuning selects (delete-after 0–300s, bool flags);
      no free-text that could break parsing.
- [x] **Everything configurable that should be** — words add/remove/list, anti-evasion toggle, per-scope
      levels + custom, history filters (content-type + age); intentionally fixed: pipeline order; the
      spam window stays a constant pending a config-input widget (→ punch #4).

### F. Wiring & discoverability
- [x] **Registry** — key `cleanup`, `category: moderation`, `visibility_tier: administrator`,
      `parent_hub: moderation`, entry points + 4 capabilities (`cleanup.word.add/remove`,
      `cleanup.history.scan`, `cleanup.policy.configure`).
- [x] **Discoverable in Help** — `build_help_menu_view` hook → the cleanup hub; DomainPanelSpec schema.

### G. Tests & evidence (required for ✔)
- [x] **Behavior tests** — `test_cleanup_stage.py`, `test_cleanup_panel.py`, `test_cleanup_history.py`,
      `test_history_cleanup.py`, `test_cleanup_levels.py`, `test_cleanup_profiles.py`,
      `test_cleanup_diagnostics.py`, `test_successful_command_cleanup.py` (~2,085 lines total).
- [x] **Authority tests** — pipeline `_validate_authority` + governance resolution behavior tests,
      **plus** the panel-level `interaction_is_admin` re-check on the policy-apply callback
      (`test_policy_panel.py::test_apply_button_requires_admin`, already present — punch #1 was a stale
      "covered only indirectly" note, corrected this run).
- [x] **Mutation-seam tests** — governance write/remove tests (DB+audit txn, events);
      `test_setup_operations_cleanup_and_routing.py`.
- [ ] **Live walkthrough recorded** — pending → punch #5.
- [ ] **Owner ✔** — pending → punch #6.

## Punch-list (clear these to certify)
1. ✅ **DONE — panel authority-recheck test already present.** `interaction_is_admin()` gating the
   policy-apply callback is pinned by `test_policy_panel.py::test_apply_button_requires_admin`; the
   original "covered only via the pipeline backstop" note was stale (corrected this run).
2. ✅ **DONE this run — history embed/link/attachment filters.** `embeds`/`links`/`attachments` sweep
   modes added to `build_history_cleanup_plan` + `!cleanuphistory` (Carl-bot/MEE6/Dyno parity).
3. ✅ **DONE this run — history age filter.** An `older:<duration>` token (e.g. `older:7d`) sets an
   `older_than` cutoff composable with every mode (bounded by Discord's newest-first pagination).
4. **Configurable spam window** *(offline, minor — deferred)* — surfacing
   `SPAM_DUPLICATE_WINDOW_SECONDS` as a *real* per-guild setting needs a config-input widget (a
   constant rename alone is not "configurable" in the rubric sense), so it is left for a follow-up
   rather than half-shipped.
5. **Live walkthrough** *(owner / live-bot)* — `/verify-bot` boot + scripted click-through (panel → word
   add/remove → a per-scope level set → `!cleanuphistory` confirm), with screenshots.
6. **Owner sign-off** — maintainer confirms "it does its job the most convenient way."

## Evidence
- **Tests:** `tests/unit/cogs/test_cleanup_stage.py` · `…/test_cleanup_panel.py` · `…/test_cleanup_history.py`
  (+ embeds-mode routing, `older:` parsing/strip, invalid-duration guard) ·
  `tests/unit/services/test_history_cleanup.py` (+ embeds/links/attachments modes, bot-skip, unsupported-mode
  raise, age gate incl. spam-mode composition) · `…/test_cleanup_levels.py` · `…/test_cleanup_profiles.py` ·
  `…/test_cleanup_diagnostics.py` · `tests/unit/runtime/test_successful_command_cleanup.py` ·
  `tests/unit/governance/test_cleanup_resolution_behavior.py` ·
  `tests/unit/views/cleanup/test_policy_panel.py::test_apply_button_requires_admin` (panel authority, #1)
- **Walkthrough:** pending (punch #5)
- **Owner sign-off:** pending (punch #6)

## Verdict
Cleanup is a **structurally strong, fully-audited** moderation unit — prohibited-word + command-access
filtering, a **seven-mode** bulk history sweep with an age gate, and a per-scope cleanup-level hierarchy,
all written through the audited governance pipeline and discoverable via command/hub/Help/Setup. The
best-in-class history-filter gaps (#2/#3) were **closed this run** (embeds/links/attachments modes +
`older:<duration>`), the panel-authority test (#1) was found **already present** (stale note corrected),
so the remaining gaps are the **configurable spam window** (#4 — needs a config-input widget, deferred)
and the owner walkthrough/sign-off (#5/#6). No safety/audit/dead-end issues found.
