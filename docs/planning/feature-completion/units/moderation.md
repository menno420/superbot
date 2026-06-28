# Moderation — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `moderation` · **Type:** server-fn · **Family:** moderation
> **State:** ◐ assessed · **Assessed:** 2026-06-28 · **Certified:** —
> Source: `disbot/cogs/moderation_cog.py` (commands + `!modmenu`/`/moderation` + Help hook) ·
> `disbot/views/moderation/` (`main_panel.py` `ModPanelView` + `modals.py`) ·
> `disbot/services/moderation_service.py` (the single audited mutation seam) ·
> `disbot/services/moderation_helpers.py` · `disbot/services/moderation_config.py` (policy read model) ·
> `disbot/cogs/moderation/schemas.py` (13-spec settings group, v7) ·
> `disbot/utils/db/moderation.py` · `disbot/utils/settings_keys/moderation.py` ·
> setup: `disbot/views/setup/sections/moderation.py`

> Assessed during the completion-first arc (Q-0209). Moderation is one of the **strongest** server-fn
> units: every action (warn w/ escalation · timeout · kick · ban · unban · clear-warnings) routes
> through one audited service (`moderation_service`), pinned by an AST invariant; warnings + mod-logs
> persist; authority is an OR-gate (Discord permission **or** governance capability) re-checked at every
> button; it has a real bespoke panel (7 modals), a Help hook, and Setup-wizard integration. The honest
> gaps are **best-in-class breadth** (no tempban/softban, no case-ID system, no appeal flow, no
> bulk/multi-target warn, no warn decay, no role-mute) — feature scope, not defects.

## Rubric (server function)

### A. Functional completeness — "does its job, in every case"
- [x] **Core promise delivered** — warn (with threshold escalation to a configured action),
      timeout (clamped to the guild's max ceiling), kick (optional post-action cleanup), ban
      (configurable 0–7d message purge), unban, clear-warnings, read-only mod-logs view
      (`moderation_service.py`). Warnings persist (atomic upsert, `utils/db/moderation.py`); mod-logs
      append-only with action/moderator/reason/timestamp.
- [ ] **Every best-in-class sub-option exists** — ❌ **partial.** Has: warn/timeout/kick/ban/unban,
      escalation, DM-on-action, post-action cleanup, configurable purge window, public-log routing.
      **Missing vs Carl-bot/Dyno/MEE6:** tempban/softban · case-ID system (grouped incidents) · appeal
      flow · role-based mute (survives restart vs. native timeout) · note/history command. → punch-list #2.
- [x] **Failure modes honest / fail-safe** — `discord.Forbidden` caught at call sites; hierarchy +
      owner + role-equality guards via `_can_act_on()` before any action; `ReasonRequiredError` raised
      at the seam before mutation when reason is required; unban-already-unbanned surfaces the 404.
- [x] **Idempotent** — re-applying settings is a normal pipeline write; clear-warnings/unban are safe
      to re-issue (no-op or honest "not found").

### B. Reachability & UI — "the most convenient way"
- [x] **A command panel exists** — `ModPanelView` (`views/moderation/main_panel.py`): 7 action buttons
      (⚠️ Warn · ⏳ Timeout · 👢 Kick · 🚫 Ban · ✅ Unban · 📋 Mod Logs · ⬛ Clear Warnings), each
      dispatching a dedicated modal (`views/moderation/modals.py`); the embed shows bot-permission +
      hierarchy readiness.
- [x] **Reachable every natural way** — `!modmenu` + `/moderation` (ephemeral) + the individual
      commands (`!warn`/`!timeout`/`!kick`/`!ban`/`!unban`) + Help hook (`build_help_menu_view`);
      moderator-tier hub.
- [x] **Integrated into the Setup wizard** — Moderation section (`views/setup/sections/moderation.py`)
      stages DM-on-action / require-reason / warn-escalation / moderator-role.
- [x] **Return navigation** — modals respond ephemerally and return to the persistent panel; no
      trapped views.
- [x] **In-place, not spammy** — modal responses are ephemeral; the panel persists for re-use.

### C. Convenience
- [ ] **No needless steps / bulk actions** — ⚠️ single-target only; no `!warn @a @b @c` batch and no
      bulk action during raids. → punch-list #3.
- [x] **Sensible defaults + presets** — warn threshold 3 → timeout 10m; ban purge 0d; timeout ceiling
      28d (Discord max); DM-on-action off; public-log off — all configurable (`schemas.py`).
- [x] **Clear feedback** — warn shows count + threshold + escalation status; each action echoes
      emoji + target + reason; cleanup reports only when messages were deleted (`moderation_helpers.py`).

### D. Authority & safety
- [x] **Authority re-checked at callback** — `_require_mod()` OR-gate on prefix commands;
      `ModPanelView.interaction_check()` applies the **same** OR-gate (`moderate_members` **or**
      `moderation.*.apply` capability) to **every** button; per-action hierarchy re-check via
      `_can_act_on()` at execute time.
- [x] **All mutations through the audited seam** — every action routes through `moderation_service`,
      pinned by `tests/unit/invariants/test_no_direct_moderation_writes.py` (AST: no direct
      `db.add_warning`/`member.kick`/`.ban`/`.timeout` outside the service). `_record_action()` fans out
      the mod_logs row + the `audit.action_recorded` companion + the `EVT_MOD_ACTION` domain event with a
      shared `mutation_id`.
- [x] **Resource creation N/A** — moderation creates no channels/roles (the public-log channel is a
      binding pointer, not created here).
- [x] **Reuses governance** — the capability tier is the second OR-gate arm; no second allowlist.

### E. Configuration
- [x] **Settings route through the pipeline** — 13 typed specs in one `SubsystemSchema` (v7) via
      `SettingsMutationPipeline` (`schemas.py`); policy read model `ModerationPolicy`
      (`moderation_config.py`) loaded at the seam (uniform across surfaces).
- [x] **`settings_keys` constants** — all keys from `utils/settings_keys/moderation.py` (no raw strings).
- [x] **Typed widgets / config-input-standard** — per-setting validators (positive int / bool / enum /
      channel id / role id / csv).
- [x] **Authority floor** — every settings spec requires `moderation.settings.configure`.

### F. Wiring & discoverability
- [x] **Registry** — key `moderation`, `category: moderation`, `visibility_tier: moderator`,
      `entry_points: [modmenu, warn, timeout, kick, ban, unban]`, 7 capabilities
      (`subsystem_registry.py`).
- [x] **Discoverable in Help** — `build_help_menu_view` hook routes the panel.
- [x] **Homed in `ownership.md`** — `services/moderation_service.py` owns every moderation write
      (pinned by the invariant).

### G. Tests & evidence (required for ✔)
- [x] **Behavior tests** — `test_moderation_service.py` (escalation count/threshold/blocked edge;
      timeout/kick/ban Discord calls + audit; unban/clear/auto-delete); `test_moderation_config.py`
      (pure policy logic); `test_moderation_panel_embed.py`; `test_moderation_modals_defer.py`.
- [x] **Authority tests** — `test_moderation_role_authority.py` (ADR-008 OR-gate: permission admits,
      capability admits without permission, neither → `MissingPermissions`; panel interaction_check).
- [x] **Mutation-seam tests** — `test_no_direct_moderation_writes.py` (AST fence) +
      `test_moderation_schemas.py` (spec defaults match policy, validators).
- [ ] **Live walkthrough recorded** — pending. → punch-list #4.
- [ ] **Owner ✔** — pending. → punch-list #5.

## Punch-list (clear these to certify)

1. **Public-log delivery verification** *(offline/live)* — the `public_log_*` settings exist; confirm
   the delivery path is fully wired (likely via `services/server_logging.py`) end-to-end, or note it
   as a documented owner-config dependency.
2. **Best-in-class breadth (rubric A)** *(owner-paced, deepening)* — tempban/softban · case-ID/incident
   grouping · appeal flow · role-based mute · note/history command. Each is a discrete additive slice.
3. **Bulk / multi-target actions (rubric C)** *(deepening)* — `!warn @a @b @c` and a raid-mode bulk
   action; today every action is single-target.
4. **Live walkthrough** *(owner / live-bot)* — `/verify-bot` boot + scripted click-through (panel →
   warn → escalation → timeout/kick/ban → mod-logs → settings → setup section), with screenshots.
5. **Owner sign-off** — maintainer uses it and confirms "it does its job the most convenient way."

## Evidence
- **Tests:** `tests/unit/services/test_moderation_service.py` · `…/test_moderation_config.py` ·
  `tests/unit/cogs/test_moderation_role_authority.py` · `…/test_moderation_schemas.py` ·
  `tests/unit/invariants/test_no_direct_moderation_writes.py` · view/modal tests
- **Walkthrough:** pending (punch-list #4)
- **Owner sign-off:** pending (punch-list #5)

## Verdict
Moderation is **structurally excellent** — a single audited mutation seam (invariant-pinned), persistent
history, an OR-gate re-checked at every button, a real 7-action panel, full settings schema, and Setup
integration. It is **not yet `✔ certified`**: the honest gaps are **best-in-class breadth** (tempban,
case system, appeal, role-mute — #2), **bulk actions** (#3), public-log delivery verification (#1), and
the owner walkthrough/sign-off (#4/#5). No safety/audit/dead-end issues found.
