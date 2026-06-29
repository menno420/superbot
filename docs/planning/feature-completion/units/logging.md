# Logging — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `logging` · **Type:** server-fn · **Family:** platform
> **State:** ◐ assessed · **Assessed:** 2026-06-29 · **Certified:** —
> Source: `disbot/cogs/logging_cog.py` + `disbot/cogs/logging/` (panel · routes panel · select/provision
> views · schemas) · `disbot/services/server_logging.py` (EventBus consumer + send paths) ·
> `disbot/services/server_logging_config.py` (policy read model) · `disbot/utils/settings_keys/logging.py` ·
> folio `docs/subsystems/server-management.md`

> Assessed during the completion-first arc (Q-0209). Logging is the **server audit/event logging** unit:
> it subscribes (via `bus.on`) to `moderation.action_taken` + `audit.action_recorded` and to passive
> Discord events (message edit/delete, member join/leave, role change), routing each to a category
> channel (combined or per-category, with a fallback chain). Per-category toggles + 11 channel-route
> bindings via `BindingMutationPipeline`; defaults all-OFF (silent fresh guild); fully fail-safe (every
> send path counts + swallows exceptions, never crashes the bus). Admin-gated + capability-gated; a
> "Choose a log channel" Setup step exists (#1429/#1432). The honest gaps: **no ignored-channels/users
> exclusion lists** and **no channel-create/voice event categories** (both deferred scope), plus the live ✔.

## Rubric (server function)

### A. Functional completeness
- [x] **Core promise delivered** — mod actions → `mod`/`cleanup`; audit mutations → `audit`; passive
      events (edit/delete/join/leave/role) routed per category; severity routes declared (publisher
      pending).
- [ ] **Every best-in-class sub-option** — ⚠ **partial.** Per-category toggles + per-category channels +
      combined/per-category routing + fallback chain present; **missing** vs Carl-bot/Dyno: ignored
      channels/users, channel create/delete/rename events, voice events. → punch #1/#2.
- [x] **Failure modes honest** — every send path counts (`permission_error`/`send_error`/
      `auto_create_error`) + swallows; never re-raises to the bus.
- [x] **Idempotent** — `setup(bot)` guarded by a subscribe latch; routing degrade falls back deterministically.

### B. Reachability & UI
- [x] **A command panel exists** — `!logging` → `LoggingPanelView` (status/set/create/routes/test);
      `status`/`set`/`create`/`routes`/`test` subcommands.
- [x] **Reachable every natural way** — `!logging` entry + `build_help_menu_view` hook +
      Moderation-hub child; routed from the Admin Help menu.
- [x] **Integrated into Setup** — the "Choose a log channel" step (#1429) → two-channel mod+activity
      multi-select (#1432).
- [x] **Return navigation** — "↩ Overview" + "🗺️ Routes" subpage; no dead-ends.
- [x] **In-place, not spammy** — panel buttons `safe_defer`+`safe_edit`; select/provision views self-close.

### C. Convenience
- [ ] **Multi-select event toggles / presets** — ⚠ per-category flags exist; a `logging_presets.py` setup
      preset exists, but no in-panel bulk/preset toggle surface. → punch #3.
- [x] **Defaults** — master + all categories OFF, routing `combined` (`server_logging_config.py`); silent
      fresh guild.
- [x] **Clear feedback** — bind success/clear embeds; `!logging test` confirms delivery or "no embed sent".

### D. Authority & safety
- [x] **Authority re-checked at callback** — all commands `administrator`; bindings/scalars gated by
      `logging.*` capabilities.
- [x] **All writes through the audited seam** — channel bindings via `BindingMutationPipeline`
      (audit row); scalars via `SettingsMutationPipeline`; channel provisioning via
      `ResourceProvisioningPipeline`.
- [x] **Resource creation via provisioning** — auto-create routes through the provisioning pipeline
      (preview + confirm).
- [x] **Reuses governance** — capability floor; no second allowlist.

### E. Configuration
- [x] **Settings/binding pipeline** — `EventLoggingPolicy.load_policy` composes typed values w/ defaults;
      11 channel-route bindings + scalar toggles via the pipelines.
- [x] **config-input widgets** — set/create panels, the routes subpage, channel select, provision preview.
- [x] **Everything configurable that should be** — which events (master + per-category), which channels
      (11 slots), routing mode, auto-create; ignored lists are the one gap → punch #1.

### F. Wiring & discoverability
- [x] **Registry** — key `logging`, `parent_hub: moderation`, entry `logging`, capabilities
      (`logging.settings.configure`, `logging.channel.bind`, `logging.channel.create`).
- [x] **Discoverable in Help** — `build_help_menu_view` hook; schema registered at cog load; service
      subscribed at boot.

### G. Tests & evidence (required for ✔)
- [x] **Behavior tests** — `test_server_logging.py` (57), `test_server_logging_events.py` (27,
      event→embed + listener filters), `test_server_logging_audit.py` (20).
- [x] **Authority tests** — command `administrator` gates; capability gating in `test_logging_schemas.py`.
- [x] **Mutation-seam tests** — `test_logging_binding_select.py` (binding via pipeline + error handling) +
      `test_logging_panel.py` / `test_logging_provision_channel.py` / `test_logging_routes_panel.py`.
- [ ] **Live walkthrough recorded** — pending → punch #5.
- [ ] **Owner ✔** — pending → punch #6.

## Punch-list (clear these to certify)
1. **Ignored channels / users** *(offline, deepening)* — exclusion lists per category (e.g., log all
   joins except #bot-testing).
2. **Channel + voice event categories** *(owner, deepening)* — `on_guild_channel_*` + `on_voice_state_update`
   logging (note voice volume needs tuning).
3. **In-panel presets** *(offline, minor)* — surface the logging presets / a bulk event-toggle in the panel.
4. **Auto-create collision handling** *(needs-live-bot, minor)* — suffix/guard when an auto-created log
   channel name collides.
5. **Live walkthrough** *(owner / live-bot)* — `/verify-bot` boot, bind channels, trigger each event
   category + a mod action, confirm the log embeds, with screenshots.
6. **Owner sign-off** — maintainer confirms "it does its job the most convenient way."

## Evidence
- **Tests:** `tests/unit/services/test_server_logging.py` · `…/test_server_logging_events.py` ·
  `…/test_server_logging_audit.py` · `tests/unit/cogs/test_logging_schemas.py` ·
  `…/test_logging_binding_select.py` · `…/test_logging_panel.py` · `…/test_logging_routes_panel.py`
- **Walkthrough:** pending (punch #5)
- **Owner sign-off:** pending (punch #6)

## Verdict
Logging is a **structurally complete, fail-safe, fully-audited** unit — EventBus-driven mod/audit/passive
event logging to category channels (combined or per-category, with a fallback chain), config-driven and
defaults-OFF, bindings through the audited pipeline, with a Setup step and a strong test suite. It is
**not yet `✔ certified`**: the gaps are **best-in-class breadth** — ignored lists (#1) and channel/voice
events (#2) — in-panel presets (#3), and the live walkthrough/sign-off (#5/#6). No safety/audit/dead-end
issues found.
