# Welcome — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `welcome` · **Type:** server-fn · **Family:** community
> **State:** ◐ assessed · **Assessed:** 2026-06-28 · **Certified:** —
> Source: `disbot/cogs/welcome_cog.py` (listeners + `!welcome` status + Help hook) ·
> `disbot/cogs/welcome/schemas.py` (8-spec settings group) · `disbot/services/welcome_service.py`
> (greeting send + entry-role grant) · `disbot/services/welcome_config.py` (policy read model) ·
> `disbot/utils/welcome_render.py` (PIL card) · `disbot/utils/settings_keys/welcome.py` ·
> setup: `disbot/views/setup/essential_setup.py` (`GreetMembersStep`)

> Assessed during the completion-first deepening run (Q-0209). Welcome greets joiners, farewells
> leavers, and optionally grants an entry role, with placeholder templates and an optional PIL card.
> It is **fail-safe and fully audited** (greeting faults swallowed; entry-role via the audited
> `role_automation.apply`; all config through `SettingsMutationPipeline`), with strong unit coverage.
> The remaining honest gap against the server-fn rubric is the **no bespoke command panel** item
> (config is the generic `!settings → Welcome` widget group + a read-only `!welcome` status embed) plus
> the owner walkthrough/sign-off. The **best-in-class welcome options are now complete** (2026-06-30:
> DM greeting · multiple/random messages · join-delay age-gating · ping-then-delete) — punch-list #2 is
> CLOSED.

## Rubric (server function)

### A. Functional completeness — "does its job, in every case"
- [x] **Core promise delivered** — join greeting + leave farewell (embed, avatar thumbnail, placeholder
      template) + optional entry-role grant (`welcome_service.py` `handle_member_join`/`handle_member_leave`/
      `_grant_entry_role`). Bots filtered at the listener (`welcome_cog.py:48`).
- [x] **Every best-in-class sub-option exists** — ✅ **closed 2026-06-30.** Has: channel greeting,
      farewell, autorole, custom template (3 placeholders `{user}/{server}/{count}`), embed, image card
      (phase 2), **multiple/random welcome+farewell+DM messages** (`---`-separated variants, one picked
      at random per greeting — `welcome_config.split_message_variants`/`pick_message`, 2026-06-30), an
      **opt-in DM greeting** (`dm_enabled`/`dm_message`, fail-safe on closed DMs — 2026-06-30), a
      **join-delay age gate** (`min_account_age_days` — anti-raid: skip greeting/DM/entry-role for
      accounts younger than N days, default 0 = off; `welcome_config.account_is_too_young`), and
      **ping-then-delete** (`delete_after_seconds` — auto-delete the channel greeting/farewell after N
      seconds via discord.py's native `delete_after`, default 0 = keep). The two 2026-06-30 additions
      close the last named gaps vs Carl-bot/MEE6/Dyno; both default-off and byte-identical for existing
      configs.
- [x] **Failure modes honest / fail-safe** — no channel → suppress greeting (entry-role still
      proceeds); send `Forbidden`/`HTTPException` classified + logged, never raised; policy-load fault
      caught + swallowed; unknown placeholders render literally (injection-safe `str.replace`,
      `welcome_config.py` `render_template`).
- [x] **Idempotent** — re-applying settings is a normal pipeline write; entry-role skipped if already
      held (`welcome_service.py`); fresh-guild master defaults OFF.

### B. Reachability & UI — "the most convenient way"
- [ ] **A command panel exists** — ❌ **partial / design gap.** Welcome has **no bespoke action
      panel**: `!welcome` (manage_guild) renders a **read-only** policy summary embed, and
      configuration is the generic `!settings → Welcome` widget group (the cog states "welcome has no
      bespoke panel in v1", `welcome_cog.py:146`). The server-fn rubric wants a panel summarizing the
      function with its actions + a settings link; whether the settings-group path clears that bar is
      an owner call. → punch-list #1.
- [x] **Reachable every natural way** — `!welcome` command + Help hook (`build_help_menu_view` returns
      the policy summary + a back-nav `HubView`) + Community hub child (`parent_hub: community`).
- [x] **Integrated into the Setup wizard** — ✅ Essential Setup **step 1 "Greet new members"**
      (`GreetMembersStep`, `essential_setup.py:522`): native channel + optional-role selects, applies
      via `SettingsMutationPipeline`, in-place edits, confirmation summary.
- [x] **Return navigation** — Help hook returns a `HubView` (back-nav); the `!welcome` embed is
      read-only (no trapped interactive view).
- [x] **In-place, not spammy** — the setup step edits its embed in place; greetings are single posts.

### C. Convenience
- [x] **No needless steps** — setup step: channel mandatory, role optional, one Save; settings are
      single-click scalar widgets.
- [x] **Sensible defaults + presets** — master OFF by default; when enabled, join ON / leave OFF
      (sensible), default personalized templates, card OFF (`welcome_config.py:45`); defaults are a
      pinned single source of truth (`test_welcome_schemas.py`).
- [x] **Clear feedback** — setup applies with a summary line; `!welcome` previews the live policy with
      on/off + rendered template.

### D. Authority & safety
- [x] **Authority re-checked** — `!welcome` gated `@commands.has_permissions(manage_guild=True)`; every
      settings spec requires `capability_required="welcome.settings.configure"`; setup step inherits the
      wizard's authority floor.
- [x] **Audited mutation seam** — all config writes route through `SettingsMutationPipeline.set_value`
      (which emits `audit.action_recorded`); **no direct DB writes** in the cog/service.
- [x] **Entry-role uses the safe seam** — grants via `services.role_automation.apply`
      (`actor_type="system"`, perm/hierarchy preflight, audited); welcome opens **no parallel
      role-mutation or audit path** (`welcome_service.py:14`).
- [x] **Reuses governance** — admin-tier visibility + the capability floor; no second allowlist.

### E. Configuration
- [x] **Settings route through the pipeline** — 8 typed specs via `SubsystemSchema` /
      `SettingsMutationPipeline`; reads via the resolution pipeline with coercion + fallback
      (`welcome_config.py` `load_policy`).
- [x] **`settings_keys` constants** — all keys from `utils/settings_keys/welcome.py` (no raw strings).
- [x] **Typed widgets / config-input-standard** — bool/id/message validators (`schemas.py`); channel +
      role specs carry picker `input_hint`s; message length-capped; invalid ids rejected at write time.
- [ ] **Channel/role as binding pointers** — ⚠️ note: the channel + role are stored as **id-bearing
      settings specs** (validated, picker-hinted), not through the `BindingMutationPipeline`
      resource-pointer lane. Functional + validated, but not the canonical binding seam the rubric
      prefers for resource pointers. → punch-list #3 (minor / consistency).

### F. Wiring & discoverability
- [x] **Registry** — key `welcome`, `entry_points: [welcome]`, `category: community`,
      `visibility_tier: administrator`, cap `welcome.settings.configure`, `parent_hub: community`
      (`subsystem_registry.py:640`).
- [x] **Discoverable in Help** — Community-hub child with a clear description; Help hook present.
- [x] **Homed in `ownership.md`** — `services/welcome_service.py` row documents the audit/role seam.

### G. Tests & evidence (required for ✔)
- [x] **Behavior tests** — join/leave enable+noop, missing-channel suppress, policy-fault fail-open,
      send-forbidden swallow, card enable/disable/Pillow-absent fallback, template substitution +
      injection safety, predicate logic (`test_welcome_service.py`, `test_welcome_config.py`,
      `test_welcome_render.py`).
- [x] **Authority/schema tests** — every spec requires the capability; id/message/bool validators;
      defaults match config (single source of truth) (`test_welcome_schemas.py`).
- [x] **Mutation-seam tests** — entry-role grant asserted to go through `role_automation.apply`
      (`actor_type="system"`); config via the audited pipeline.
- [ ] **Cog-integration gaps** — no test for the `!welcome` command permission path or
      `build_help_menu_view` shape; no end-to-end setup-step→pipeline→audit test (pipeline tested
      generically). → punch-list #4 (minor).
- [ ] **Live walkthrough recorded** — pending. → punch-list #5.
- [ ] **Owner ✔** — pending. → punch-list #6.

## Punch-list (clear these to certify)

1. **Bespoke command panel (rubric B).** `!welcome` is a read-only status embed; build an actionable
   Welcome panel (toggle greet/farewell · pick channel/role · edit message · preview · link to
   `!settings` · back to Community/Help), so Welcome matches the server-fn panel bar instead of
   relying on the generic settings group. *(Or the owner waives this — the settings group + setup step
   may be deemed sufficient for an admin-tier config function.)*
2. **Best-in-class options (rubric A)** *(owner-paced, deepening)* — ~~multiple / random welcome
   messages~~ ✅ **shipped 2026-06-30** (PR #1579 — `---`-separated variants on the join, leave **and**
   DM message, one chosen at random per greeting; migration-free, single-message configs
   byte-identical) · ~~DM greeting~~ ✅ **shipped 2026-06-30** (PR #1579 — opt-in `dm_enabled` +
   dedicated `dm_message`; DMs the joiner the greeting, fail-safe on closed DMs, independent of the
   channel greeting) · ~~join-delay age-gating~~ ✅ **shipped 2026-06-30** (`min_account_age_days` — skip
   greeting/DM/entry-role for accounts younger than N days, default 0 = off; anti-raid) · ~~ping-then-delete~~
   ✅ **shipped 2026-06-30** (`delete_after_seconds` — auto-delete the channel greeting/farewell after N
   seconds, default 0 = keep). **Punch-list #2 CLOSED** — every named best-in-class option now exists.
3. **Channel/role via the binding pipeline** *(offline, consistency)* — consider routing the channel +
   entry-role pointers through `BindingMutationPipeline` (the canonical resource-pointer seam) rather
   than id-bearing settings specs.
4. **Cog-integration tests** *(offline)* — `!welcome` permission gate, `build_help_menu_view` shape,
   and a setup-step→`SettingsMutationPipeline`→audit assertion.
5. **Live walkthrough** *(owner / live-bot)* — `/verify-bot` boot + scripted click-through (setup greet
   step → join a test member → see greeting + entry role → leave → farewell → `!welcome` status), with
   screenshots.
6. **Owner sign-off** — maintainer uses it and confirms "it does its job the most convenient way;
   nothing left to add or move."

## Evidence
- **Tests:** `tests/unit/services/test_welcome_service.py` · `…/test_welcome_config.py` ·
  `tests/unit/cogs/test_welcome_schemas.py` · `tests/unit/utils/test_welcome_render.py`
- **Walkthrough:** pending (punch-list #5)
- **Owner sign-off:** pending (punch-list #6)

## Verdict
Welcome is **functionally solid, fail-safe, and fully audited** — greeting/farewell/entry-role with a
phase-2 card, all config through the audited settings pipeline, the entry-role through the audited role
seam, integrated into the Essential Setup greet step, and well unit-tested. It is **not yet
`✔ certified`**: the honest rubric gaps are a missing **bespoke command panel** (#1, or an owner
waiver) and a few **best-in-class options** (#2, owner-paced), plus the minor binding-seam (#3) and
cog-integration-test (#4) items and the owner walkthrough/sign-off (#5/#6). No safety/audit/dead-end
issues found.
