# Channels — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `channel` · **Type:** server-fn · **Family:** management
> **State:** ◐ assessed · **Assessed:** 2026-06-29 · **Certified:** —
> Source: `disbot/cogs/channel_cog.py` (14 commands + `!channelmenu`) · `disbot/views/channels/`
> (create/delete/restrict/move panels + main hub + list pagination) ·
> `disbot/services/channel_lifecycle_service.py` (the Q-0100 audited create/mutate seam) · folio
> `docs/subsystems/server-management.md`

> Assessed during the completion-first arc (Q-0209). Channels is the **operator channel/category
> management** unit: create (single/bulk/voice), clone, delete (single/bulk/keyword), rename, move,
> reorder, lock/unlock, per-role restrict/permissions, list (paginated), info — all routed through the
> audited `ChannelLifecycleService` (Q-0100), which is the **only** allowed creator of ad-hoc operator
> channels (pinned by `test_no_direct_channel_mutations` + `test_no_silent_auto_create`), emits
> `channel.lifecycle_changed` + an audit row per op, and handles partial-batch failure honestly with
> collision-safe naming. Admin-gated at the cog and `manage_channels`-checked at the service. The gaps
> are best-in-class extras (slowmode / topic / NSFW toggles) and per-command authority tests.

## Rubric (server function)

### A. Functional completeness
- [x] **Core promise delivered** — full channel/category CRUD (`channel_cog.py` 14 commands +
      `channel_lifecycle_service.py`); per-step partial-failure handling; collision-safe `safe_channel_name`.
- [ ] **Every best-in-class sub-option** — ⚠ **partial.** Create/bulk/voice/clone/delete/move/reorder/
      lock/restrict/permissions/list/info all present; **missing** vs Carl-bot/Dyno: slowmode, topic/
      description set, NSFW toggle. → punch #1–#3.
- [x] **Failure modes honest** — Forbidden/missing-channel/missing-category reported per step; create
      blocked if the bot lacks `manage_channels`.
- [x] **Idempotent** — batch ops are per-channel atomic (no rollback of prior successes by design);
      re-create yields an auto-incremented safe name (documented, not silent).

### B. Reachability & UI
- [x] **A command panel exists** — `!channelmenu` → `_ChannelManagerView` (Create/Delete/Restrict/Move).
- [x] **Reachable every natural way** — 14 commands + `!channelmenu` + `build_help_menu_view` hook +
      Admin-hub child (`parent_hub: admin`).
- [N/A] **Integrated into Setup** — channel management is action-oriented; Setup binds channel *pointers*
      to subsystems (a separate concern), not this unit's config.
- [x] **Return navigation** — every sub-panel has a back-to-manager button (`restore_parent_or_send_fresh`).
- [x] **In-place, not spammy** — panels `response.edit_message`; per-step success/failure summaries.

### C. Convenience
- [x] **Bulk + presets** — bulk create/delete/lock/move; 8 name presets + 5 category presets + free-form
      modal; get-or-create category by name.
- [x] **Defaults** — channels created with default Discord perms; sensible.
- [x] **Clear feedback** — per-channel ✅/❌ summaries + outcome embeds + first-error extraction.

### D. Authority & safety
- [x] **Authority re-checked at callback** — every command `@is_admin_or_owner()`; the service re-checks
      bot `manage_channels` before each op; panels invoker-locked.
- [x] **All mutations through the audited seam** — `ChannelLifecycleService` is the sole mutator (pinned
      by `test_no_direct_channel_mutations`); irreversible ops require `confirmed=True`.
- [x] **Resource creation via the provisioning seam** — the service is the **only** allowed
      `guild.create_*_channel` caller (`test_no_silent_auto_create` allowlist); emits
      `channel.lifecycle_changed` + audit.
- [x] **Reuses governance** — admin floor; no second allowlist.

### E. Configuration
- [N/A] **Settings pipeline** — channel management is action-oriented, not config-oriented (no scalars).
- [N/A] **config-input widgets** — n/a.
- [N/A] **Everything configurable that should be** — n/a.

### F. Wiring & discoverability
- [x] **Registry** — key `channel`, `category`/family management, `parent_hub: admin`, entry
      `channelmenu`, capabilities (`channel.create.text/voice`, `delete.any`, `restrict.apply`,
      `visibility.configure`).
- [x] **Discoverable in Help** — `build_help_menu_view` hook; all 14 commands carry docstrings.

### G. Tests & evidence (required for ✔)
- [x] **Behavior tests** — `test_channel_lifecycle_service.py` (23: rename/move/reorder/delete/
      set_overwrite/clone/create incl. voice + by-name/by-id category + partial-Forbidden) +
      `test_channel_list_paginate.py` (22: chunking, multi-page nav, truncation).
- [x] **Authority/seam tests** — `test_no_direct_channel_mutations.py` (3) +
      `test_no_silent_auto_create.py` (4); per-command admin-gate is decorator-level (not unit-tested →
      punch #4).
- [x] **Mutation-seam tests** — event + audit emission asserted in the lifecycle tests.
- [ ] **Live walkthrough recorded** — pending → punch #5.
- [ ] **Owner ✔** — pending → punch #6.

## Punch-list (clear these to certify)
1. **Slowmode** *(offline, deepening)* — `!slowmode <channel> <seconds>` (Carl-bot/Dyno parity).
2. **Topic/description set** *(offline, deepening)* — settable (visible in `!channelinfo`, not editable).
3. **NSFW toggle** *(offline, deepening)* — `!nsfw <channel> <on|off>`.
4. **Per-command authority tests** *(offline, minor)* — unit tests that a non-admin is rejected on each
   command (today decorator-gated, integration-covered only).
5. **Live walkthrough** *(owner / live-bot)* — `/verify-bot` boot + create/bulk/move/delete/restrict,
   confirm audit rows + the lifecycle event, with screenshots.
6. **Owner sign-off** — maintainer confirms "it does its job the most convenient way."

## Evidence
- **Tests:** `tests/unit/services/test_channel_lifecycle_service.py` ·
  `tests/unit/invariants/test_no_direct_channel_mutations.py` · `…/test_no_silent_auto_create.py` ·
  `tests/unit/cogs/test_channel_list_paginate.py` (~52 cases total)
- **Walkthrough:** pending (punch #5)
- **Owner sign-off:** pending (punch #6)

## Verdict
Channels is a **structurally complete, fully-audited** management unit — full channel/category CRUD
through the single Q-0100 `ChannelLifecycleService` seam (no direct mutations / no silent auto-create,
both CI-pinned), with `channel.lifecycle_changed` + audit per op, honest partial-batch handling, and
~52 tests. It is **not yet `✔ certified`**: the gaps are best-in-class extras (slowmode/topic/NSFW —
#1/#2/#3), per-command authority tests (#4), and the owner walkthrough/sign-off (#5/#6). No safety/audit/
dead-end issues found.
