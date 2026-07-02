# Lane A — Governance & Safety (Axis 1)

> **Status:** `audit` — **complete** (2026-07-02). All 11 subsystems verified + completed against
> source by a two-stage pipeline (a drafting pass + an independent adversarial-verify pass per
> subsystem, both source-grounded — see `Verifier's note` / correction callouts inline in each
> section), then personally spot-checked against source by the lane session for the highest-leverage
> corrections (the `channel` mutation-seam finding, `role`'s two scheduled loops, `ticket`'s
> authority-mechanism count, `moderation`'s fit-number rationale). Every ledger row and tier-3 claim
> cites `file:line`; unresolved items are marked `⚠ unverified` rather than smoothed over — see each
> subsystem's own residual-unverified list and the roundup in [§ Lane A summary](#lane-a-summary) at
> the end of this file. Per [`../BRIEF.md`](../BRIEF.md) methodology; treat corrections/citations as
> current, but this is still one lane's read — the capstone reconciles amendment numbering across
> Lanes B/C/D before it is final.

**Subsystems:** admin, server_management, moderation, automod, image_moderation, security, cleanup, role, channel, welcome, ticket

**Method:** [`../BRIEF.md`](../BRIEF.md) · [`../PARTITION.md`](../PARTITION.md) · `tools/grammar_spike/` · `../ground-truth/command-surface.json`.

---

## Lane A cross-subsystem amendment registry (canonical numbering)

Eleven independent per-subsystem passes each proposed new grammar amendments using **local**
`G-A<n>` numbering (unaware of each other, since they ran concurrently). This section is the
**synthesis step**: identical concepts raised independently by multiple subsystems are merged
into one canonical id; genuinely distinct concepts get their own id. **The per-subsystem sections
below already use these canonical numbers** — this table is the reconciliation record, not a
duplicate ledger. The capstone should treat `G-A1`–`G-A15` (plus the `G-1x` refinement) as Lane
A's proposed additions to the six existing amendments (`G-1`…`G-6`), to be deduped again against
Lanes B/C/D's own proposals before the amendment list is folded into the design spec.

| ID | Name | One-line shape | Evidenced independently by | Primary citation |
|---|---|---|---|---|
| **G-A1** | `ModalFieldSpec` / declarative modal-form primitive | `PanelActionSpec.defer_mode="modal"` declares THAT a modal opens (design-spec §2.6) but nothing declares WHAT it collects (labels, style, placeholder, max_length, prefill, per-field bounds via G-5). Turns every hand-written `discord.ui.Modal` subclass's field-collection+validation into data; the post-submit side-effect handler stays a registered `HandlerRef`. | **4×** — admin, moderation, channel, ticket | `admin_cog.py:763` `_LogLevelModal`; `views/moderation/modals.py`; `views/channels/create_panel.py:352`; `views/tickets/_shared.py:72` |
| **G-A2** | `MessagePipelineStageSpec` | An ordered, fail-open/short-circuiting `on_message` stage slot (`stage_name`, `order`, `handler`, `fail_open`, `short_circuits_on`) — distinct from G-1's `GatewayListenerSpec` (single raw discord.py event, no `order`/shared-pipeline semantics). Covers `core/runtime/message_pipeline.py`'s canonical order table (automod=5, cleanup=10, counting=15, chain=20, image_mod=25). | **3×** — automod, image_moderation, cleanup | `core/runtime/message_pipeline.py:44-58`; `automod_cog.py:37`; `image_moderation_cog.py:41-54`; `cleanup_cog.py:97-119` |
| **G-A3** | Cross-subsystem / help-menu declarative direct-navigation primitive | A declared `PanelRef` (or a `HelpEntrySpec.dropdown_target` field) that lets a Help-dropdown hook or a hub panel-action route straight into another subsystem's canonical `panel_id`, replacing the shipped `interaction.client.get_cog(name)` + `getattr(cog, "build_help_menu_view", None)` dynamic-dispatch pattern (invisible to both CodeGraph and Grimp). | **2×** — server_management, automod | `views/server_management/hub.py:138-170` `_open_manager`; ~9-10 Lane A cogs' near-identical `build_help_menu_view` bodies |
| **G-A4** | `ResourceLifecycleSpec` | Declarative multi-operation CRUD-with-audit family (typed request → per-target `StepResult` → reversibility class → audit+event companion → confirmation gate for irreversible ops) generalizing the shipped `ChannelLifecycleService`/`RoleLifecycleService` pattern. The kernel-generatable half is everything except the per-op Discord call, which stays a thin `HandlerRef`. | 1× named (channel), cross-referenced by role's audited lifecycle services and moderation/ticket's audited seams | `services/channel_lifecycle_service.py:113-259`; `services/role_lifecycle_service.py`; `services/lifecycle/contracts.py` |
| **G-A5** | `RecordTableSpec` | A keyed table of typed records (one row per target id — role/channel/member) with declared add/edit/remove workflows and per-row audit, generalizing G-2 (scalar list-valued settings) to **structured** rows. | 1× (role) | `utils/db/roles.py:160` role_automation_exemptions; role's `!setrole`/`!unsetrole`/exemption buttons/reaction-mode picker |
| **G-A6** | `StagedBuilderSpec` | A view-local, session-scoped multi-field draft object — accumulate several field edits in memory across multiple interactions, one atomic Post/create or Save/edit commit. | 1× (role) | `views/roles/role_menu_builder.py:452-483` `RoleMenuBuilder` |
| **G-A7** | `EntityResolverRef` | Declarative reference to a shared, catalogued entity-resolution function (channel/category/role by mention\|ID\|name) plus bounded/enum command-argument validation, since `CommandSpec` has no argument schema today. | 1× (channel) | `channel_cog.py:85-103` `_resolve_channel`/`_resolve_category` |
| **G-A8** | `PaginatedBlockSpec` | Declarative content-pagination for `BlockSpec(kind="list"/"table")` bodies exceeding Discord's 25-field/6000-char/1024-per-field caps, generalizing the hand-rolled chunking algorithms. | 1× (channel) | `views/channels/list_panel.py:60-112` |
| **G-A9** | `WizardSectionSpec` | Declarative setup/provisioning-wizard section (slug, `recommended_ops` builder ref, customize target, detail panel/view, op_kinds, depths) — no §2 equivalent for `services.setup_sections.SetupSection`'s 5 genuine callback fields today. | 1× named (cleanup), applicable to every subsystem with a `views/setup/sections/*.py` registration | `views/setup/sections/cleanup.py:577-599` |
| **G-A10** | `PreviewConfirmApplySpec` | Declarative computed-diff preview → explicit confirm → audited apply. Generalizes the policy-panel's preview/confirm/apply flow and ad hoc `wait_for('reaction_add')` confirms; `PanelActionSpec.confirm` today is only a generic re-click flag, not a computed-diff preview. | 1× (cleanup) | `views/cleanup/policy_panel.py:167-598`; `services/cleanup_diagnostics.py:209-357` |
| **G-A11** | `DeferredActionSpec` | A one-shot delayed callback bound to captured runtime state (guild_id, channel, prior value), fired exactly once N seconds after the triggering call — distinct from `ManagedTaskSpec`'s persistent/recurring trigger vocabulary (`interval:<s>\|cron:<expr>\|event:<name>`), which has no "fire once, N seconds from now" shape. | 1× (security) | `services/security_service.py:186-241,331-354` `_hold_then_lift`/`_clear_lock_after` |
| **G-A12** | Configurable / dual-floor authority resolution | `capability_required` resolves only to a fixed floor today; real shipped authority is often **2-4 independent, non-interoperating mechanisms** for one conceptual gate — a raw Discord-permission bit, a capability string, and/or a resource-owner/bound-role check (e.g. "ticket opener OR staff role OR admin OR platform owner"). Proposes a declarative `legacy_permission_floor` / resource-owner-clause extension so these collapse to one declared authority expression. | 2× — moderation, ticket | `moderation_cog.py:29-52` `_require_mod`; `views/tickets/_shared.py:21-35` `is_ticket_staff` + inline opener override at `ticket_cog.py:164`/`control.py:134` |
| **G-A13** | Templated multi-variant text setting | A declarative setting-render contract for placeholder substitution + random-variant (`"---"`-separated) pick — today fully bespoke render-time behavior with no §2 primitive (G-5 covers only write-time bounds). | 1× (welcome) | `services/welcome_config.py:108-133,254-272` `pick_message`/`render_template` |
| **G-A14** | Dedicated-table (non-KV) persistence contract | Elaborates the already-declared-but-inert `SettingSpec.storage` field (spec.py:255, no non-`"kv"` semantics exist anywhere) into a real kernel-generation contract, so a subsystem with its own migration-owned config table (not scalar guild-settings KV) gets a declarative path instead of hand-written CRUD. | 1× (ticket) | `spec.py:255`; `utils/db/tickets.py`; `migrations/098_tickets.sql` |
| **G-A15** | Channel-backed per-instance lifecycle primitive | A non-game analog of `GameFacet.ChallengeSessionSpec` — create one dedicated channel per domain instance, grant opener+staff-role access, track an open/claimed/closed status machine, run a declared close-workflow (transcript/notify/teardown). | 1× (ticket) | `services/ticket_mutation.py`; `services/ticket_service.py` |
| **G-1x** *(refinement, not a new family)* | Widen `GatewayListenerSpec.handler` to `Route` | `GatewayListenerSpec.handler` is `HandlerRef`-only (spec.py:363) even when the gateway-triggered action is fully generic (e.g. "grant the role bound by a setting, skip if already held") — widening the field type (or adding a parallel `action: WorkflowRef \| HandlerRef`) lets a pure kernel `WorkflowRef` cover it, tier-1 instead of tier-3. | 1× (welcome) | `services/welcome_service.py:215-259` `_grant_entry_role` |

**Reading this table against the per-subsystem sections:** every ledger row below that cites a
`G-A<n>` uses these canonical numbers directly (already renumbered from each drafting agent's
local numbering during synthesis). `G-A1` (modals) and `G-A2` (message-pipeline stages) are the
two highest-confidence proposals — each was independently rediscovered by 3-4 unrelated
subsystems without cross-talk, which is strong convergent evidence they are real, load-bearing
gaps rather than one agent's idiosyncratic read.

---

### admin
_cogs: disbot/cogs/admin_cog.py, disbot/cogs/admin/cog_manager.py, disbot/cogs/admin/_slash_sync.py, disbot/cogs/admin/__init__.py_

All 11 commands verified byte-for-byte against `ground-truth/command-surface.json` (filtered on `cog_file` containing `admin_cog.py`) — no missing/extra commands, all `kind`/`alias` fields match. **Ground-truth caveats (⚠ unverified tool, not unverified fact) — re-verified and one gap added by adversarial pass:**

1. The JSON's `perm` field reads `"member"` for `adminmenu`, `serverstats`, `coglist`, `slashes`, `loglevel` even though all five carry `@admin_or_owner()` (`core/runtime/permission_checks.py:100-102`, admin-or-bot-owner) — the ground-truth extractor evidently only recognizes literal `commands.has_permissions(...)`/`is_owner()`/`app_commands.default_permissions(...)` decorators, not the wrapped custom check. Source confirms real admission is administrator-or-owner for those five.
2. **(Added by verification pass.)** `cog`, `loadall`, `unloadall`, `syncslash`, `restart` (all gated by literal `@commands.is_owner()` — bot-owner only) are tagged `perm: "admin"` in ground truth — **not** a distinct owner tier. Dumping every distinct `perm` value across the full 271-row corpus gives `{member, admin, manage_channels, manage_messages, manage_guild, manage_roles, moderate_members, create_invite}` — there is **no `"owner"` value anywhere in the file**. The extractor's schema has no bot-owner-only tier at all, so these five collapse to the same `"admin"` tag as `/admin`'s `app_commands.default_permissions(administrator=True)` gate, even though source shows they are meaningfully *stricter* (single bot owner, not any guild administrator). Anyone consuming `command-surface.json` directly would under-read the privilege bar on these five.

Treat the ground-truth `perm` column as unreliable for both wrapped checks and owner-only checks; the ledger below cites source directly.

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !adminmenu | command | cogs/admin_cog.py:36 (cooldown 2/10, `@admin_or_owner()`) | 2 | 2 | Opens `_AdminPanelView` — a `PanelRef` route with a thin cog-count read (see providers row); matches karma `!karma` card precedent, not a pure kernel open (there's a small custom read behind it). |
| /admin | command (slash) | cogs/admin_cog.py:51 (`@app_admin_or_owner()`, plus `@app_commands.default_permissions(administrator=True)` at :55 — the literal decorator ground truth actually keys off) | 2 | 2 | Same panel, slash surface, ephemeral — pure declaration + the same thin provider. |
| !serverstats | command | cogs/admin_cog.py:75 (`@admin_or_owner()`) | 2 | 2 | Inline embed built from live `guild` attributes (member/online counts, channel/role counts) — no persistence, no validation, just aggregation+format: a thin `ProviderRef` + `BlockSpec(kind="fields")`, same class as karma's card provider. **Duplicated verbatim** in the Stats button (line 499-514) — a dedup opportunity (see Reconsider). |
| !cog | command | cogs/admin/cog_manager.py (`_find_module`:46, `_do_load`/`_do_unload`/`_do_reload`:96/105/114), invoked from cogs/admin_cog.py:97 (`@commands.is_owner()`) | 3 | 3 | Deliberate escape hatch: fuzzy cog-name resolution + `bot.load_extension`/`unload_extension`/`reload_extension` — real process-state side effects, no §2 primitive models dynamic extension lifecycle (Lane G territory). |
| !loadall | command | cogs/admin_cog.py:124 (`@commands.is_owner()`) | 3 | 3 | Same class as `!cog` — bulk iteration over `_all_cog_modules()` with partial-failure aggregation; bespoke, not declarative-shaped. |
| !unloadall | command | cogs/admin_cog.py:147 (`@commands.is_owner()`) | 3 | 3 | Same class, plus a self-exclusion special case (never unloads `cogs.admin_cog`). |
| !coglist (aliases: cogs, listcogs, cogslist) | command | cogs/admin_cog.py:173 (cooldown 2/10, `@admin_or_owner()`) | 2 | 2 | Opens `_CogManagerView` with a live per-cog load/syntax-check read (`_syntax_ok` runs `ast.parse` per file, cog_manager.py:65-72) — a thin but real provider, same class as `!serverstats`. |
| !syncslash (alias: syncs) | command | cogs/admin_cog.py:198 (`@commands.is_owner()`); logic in cogs/admin/_slash_sync.py:34 `run_global_sync`, :22 `format_sync_diff` | 3 | 3 | Deliberate escape hatch: diff-gated Discord command-tree sync (guild/global/clear branches), live HTTP calls to `tree.sync()`/`copy_global_to()` — genuine domain logic, no declarative primitive for slash-tree diffing exists or should. |
| !slashes (alias: slashlist) | command | cogs/admin_cog.py:295 (`@admin_or_owner()`) | 2 | 2 | Read-only listing of `bot.tree.get_commands()`, sorted+formatted — thin provider, no business logic beyond format. |
| !restart | command | cogs/admin_cog.py:365 (`@commands.is_owner()`); `core/runtime/lifecycle.py:223-254 request_restart` | 3 | 3 | Deliberate escape hatch: process lifecycle control (coalescing semantics, watchdog handoff in bot1.py) — Lane G runtime-skeleton overlap, not a config/CRUD shape. |
| !loglevel | command | cogs/admin_cog.py:393 (`@admin_or_owner()`) | 3 | 3 | Deliberate escape hatch: direct `logging.getLogger().setLevel(...)` mutation of a **process-global, non-persisted** knob — doesn't fit the guild-scoped persisted `SettingSpec` model at all (no DB write, doesn't survive restart), so it stays a bespoke handler rather than a setting. No kernel lane will ever generically cover "mutate Python's own logging module," so this stays tier 3 in both columns — see `_LogLevelModal` below, which performs the identical operation and, on adversarial re-check, must be graded the same way. |
| _AdminPanelView (panel shell) | panel | cogs/admin_cog.py:467 | 1 | 1 | Pure `PanelSpec` declaration — title/body/actions/layout; zero code at the container level once the actions below are separately graded (matches how `LOGGING_MANIFEST`'s panel container isn't itself a tier-3 driver). |
| Stats button | panel-action | cogs/admin_cog.py:494-514 | 1 | 1 | As a **navigation** to a would-be `admin.server_stats` panel (the sensible re-expression, replacing the current same-view/different-embed hack), the button itself is pure `PanelRef` navigation — matches logging's "panel: routes"/"panel: overview" precedent (1,1); the provider complexity is captured once in the combined providers row below, not double-counted here. |
| Cog List button | panel-action | cogs/admin_cog.py:516-532 | 1 | 1 | Same reasoning — pure navigation to `_CogManagerView`; that panel's own thin provider is graded on its own row. |
| Reload All button | panel-action | cogs/admin_cog.py:534-559 | 3 | 3 | Deliberate escape hatch: bulk `reload_extension` over every loaded extension, inline owner-check, partial-failure aggregation — same class as `!unloadall`, a real side-effecting action, not pure navigation. |
| Log Level button (opens modal) | panel-action | cogs/admin_cog.py:561-567 | 3 | 1 | As-written: hand-instantiates a specific `discord.ui.Modal` subclass — no declarative dispatch exists. With **G-A1** (ModalSpec): `PanelActionSpec(defer_mode="modal", ...)` triggering a declared modal is pure kernel dispatch at the *trigger site* (zero code there) — the modal's own field shape + apply step are graded on their own row (`_LogLevelModal`, below), which is where the real complexity lives. |
| Settings / Server Management / Channels / AI / Platform / Diagnostics / UX Lab / Logging / Cleanup nav buttons (×9) | panel-action | cogs/admin_cog.py:575 (settings), :583 (server_management — **missing from the pre-extracted scaffold, added here**), :595 (channels), :603 (ai), :615 (platform, direct `views.diagnostic` import rather than the hook), :633 (diagnostics), :641 (ux lab), :649 (logging), :657 (cleanup); shared body `_open_via_help_hook`, cogs/admin_cog.py:711-760 | 3 | 1 | As-written: dynamic `getattr(cog, "build_help_menu_view", None)` cross-cog lookup by string name + try/except (invisible to both CodeGraph and the import graph — the exact dynamic-dispatch gotcha `.claude/CLAUDE.md` calls out). **Genuinely tier 3 as shipped today** (this is the single biggest driver of the corrected as-written fit number below — a prior draft of this ledger miscounted this group as already tier-1/2 as-written, which is wrong; see Fit numbers). The underlying behavior — "open subsystem X's already-declared panel" — reduces to a zero-code `PanelActionSpec(handler=PanelRef("<x>.panel"))` once every target subsystem's own panel is declared; **no new amendment needed**, `PanelRef` already exists unamended. Counted as 9 units in the fit numbers (one per nav target). |
| Overview back button | panel-action | cogs/admin_cog.py:699-705 | 1 | 1 | Self re-render — matches logging's "panel: overview" (1,1) exactly. |
| _LogLevelModal | panel (modal) | cogs/admin_cog.py:763-790 | 3 | 3 | **Corrected by adversarial pass (was 3→2).** As-written: hand-written `discord.ui.Modal` (one `TextInput`) + `on_submit` validation (`getattr(logging, ...)`) + apply. With **G-A1**, the field-collection + enum-style validation shape becomes declarative data — a real, generalizable win (recurs across ≥4 Lane A subsystems) — but the *terminal* action, `logging.getLogger().setLevel(...)`, is the exact same bespoke, no-matching-kernel-lane mutation the `!loglevel` row above stays tier-3 for. A prior draft graded this unit's with-amendments tier as 2 ("thin registered HandlerRef"), which is inconsistent with (a) keeping `!loglevel` itself at tier 3 for identical logic, and (b) the established precedent in `tools/grammar_spike/RESULTS.md` (karma's `!thanks` is graded tier 3 in both columns despite being explicitly labeled a "thin domain handler" — thinness does not demote a real, no-kernel-lane mutation). G-A1 is still worth proposing for the field-shape win; it just doesn't clear this compound unit's ledger tier. |
| build_help_menu_view (help-menu direct-nav hook) | help | cogs/admin_cog.py:43 | 1 | 1 | The manifest's own `panels` + `parent_hub`/`entry_points` fields already let a generated help dropdown resolve "admin" → its panel directly, zero code; today's per-cog `build_help_menu_view(interaction)` convention (dynamically invoked by name from elsewhere, invisible to the import graph) is the current workaround, not the behavior's irreducible complexity. No amendment needed. |
| on_ready startup message | listener | cogs/admin_cog.py:409-419; `core/runtime/guild_resources.py:64 resolve_channel` | 3 | 2 | **G-1** (`GatewayListenerSpec`): no raw gateway-listener primitive in §2 as written. With it: `GatewayListenerSpec(gateway_event="on_ready", handler=HandlerRef(...))` — declared gate + a thin per-guild fetch-and-forward handler (resolve → permission-check → send), matching the "thin handler stays tier 2" precedent (karma's react-to-thank, logging's 8 listeners) rather than the "real logic stays tier 3" one (blackjack's reaction-join). **Escalated by adversarial pass — this is a live bug, not just a design smell:** the handler resolves the channel **by hardcoded name** (`name="bot_spam"`, admin_cog.py:412, underscore) — but every one of the five `"default_channels"` declarations in `utils/subsystem_registry.py` (lines 75, 104, 1085, 1108, 1137) declares `"bot-spam"` (hyphen). Grepped the whole `disbot/` tree: `"bot_spam"` (underscore) occurs **exactly once**, only at this call site. `resolve_channel`'s name match is an exact string compare (`guild_resources.py:116`, `if ch.name != name: continue`), so this isn't merely "hardcoded instead of a `BindingSpec`" — it's hardcoded to a string that doesn't even match the subsystem's own declared convention, meaning the greeting is very likely silently dead in any guild that actually has a channel named per the declared default. See Structural-gap flags. |
| admin.cog.load (capability) | setting | disbot/utils/subsystem_registry.py:83 | 1 | 1 | Pure declarative string in `SubsystemManifest.capabilities` — zero code. **⚠ Unwired**: repo-wide grep for the literal string finds zero consumers outside `subsystem_registry.py` itself — no `capability_required` check, no governance-service lookup references it anywhere in `cogs/admin_cog.py` or `cogs/admin/`. (Confirmed: `capability_required` is a real, wired mechanism elsewhere — `services/settings_mutation.py`, `services/binding_mutation.py`, `governance/capability.py`, `cogs/ai/schemas.py` all use it — so this isn't a fictional grammar feature, admin's 4 strings are just disconnected from it.) The real gate is `@commands.is_owner()`/`@admin_or_owner()` decorators, not this capability string — a declaration-vs-code gap the grammar doesn't cause and doesn't fix on its own (BRIEF's named watch-item). |
| admin.cog.unload (capability) | setting | disbot/utils/subsystem_registry.py:84 | 1 | 1 | Same — unwired declared capability. |
| admin.cog.reload (capability) | setting | disbot/utils/subsystem_registry.py:85 | 1 | 1 | Same — unwired declared capability. |
| admin.server.stats (capability) | setting | disbot/utils/subsystem_registry.py:86 | 1 | 1 | Same — unwired declared capability. |
| cog-count / server-stats / slash-list / cog-status providers | provider | cogs/admin_cog.py:75-92 & 499-514 (server-stats, duplicated), 326-359 (slash-list), 476 (cog-count); cogs/admin/cog_manager.py:268-305 (cog-status) | 2 | 2 | **Citation corrected by adversarial pass.** A prior draft cited `182-193` here, which is actually `coglist_command` (it only opens `_CogManagerView` — no read-model logic of its own) and is not a provider; the same draft omitted the two providers actually named in this row's own label (`cog-count`, at `_AdminPanelView.build_embed`'s `loaded_count = len(self.cog.bot.extensions)`, line 476; and `slash-list`, the sort/format body inside `list_slash_commands`, lines 326-359). One combined "provider" unit (matches logging's "status/routes providers" combined row) — thin reads/formats, no domain logic, no persistence. |
| _CogManagerView (panel shell) | panel | disbot/cogs/admin/cog_manager.py:164 | 1 | 1 | Pure `PanelSpec` declaration once its actions are graded separately. |
| Windowed cog select (`attach_windowed_select`) | selector | disbot/cogs/admin/cog_manager.py:200-207 | 1 | 1 | `SelectorSpec` (options via `ProviderRef`, `page_size` paging) already covers windowed/paginated selects — this is literally what the primitive is for; the on-select behavior (store the chosen module, re-render) is a generic kernel "selection store" workflow, zero domain code — no amendment needed. Also notable: `attach_windowed_select` was itself added to fix the #1040 select-option-truncation bug (>25 cogs silently dropped by `options[:25]`) — evidence the paginated-select shape is real and recurring, reinforcing `SelectorSpec.page_size`'s value. |
| Load button (_on_load) | panel-action | disbot/cogs/admin/cog_manager.py:209-216 (decl) / :331 (handler) | 3 | 3 | Deliberate escape hatch: dynamic `bot.load_extension`, owner-gate, real side effect — same class as `!cog`/`!loadall`. |
| Unload button (_on_unload) | panel-action | disbot/cogs/admin/cog_manager.py:218-225 / :343 | 3 | 3 | Same, plus protected-cog denial branch (`_PROTECTED_COGS`, cog_manager.py:85-93) — genuine policy logic, not a generic shape. |
| Reload button (_on_reload) | panel-action | disbot/cogs/admin/cog_manager.py:227-234 / :364 | 3 | 3 | Same class — reload is allowed even for protected cogs (reversible), a real domain rule. |
| Refresh button (_on_refresh) | panel-action | disbot/cogs/admin/cog_manager.py:236-243 / :379 | 1 | 1 | Pure re-render, no mutation — matches logging's "panel: refresh status" (1,1) exactly. |

**Unit kinds present:** command, panel (shell + actions + modal), setting (capability declarations — flagged as loosely-named: these are `SubsystemManifest.capabilities` strings, not `SettingSpec` instances; the manifest sketch correctly keeps `settings=()` and puts them under `capabilities=(...)` instead, see below), listener (gateway), help, provider (read-model). **Unit kinds explicitly absent** (re-verified by direct grep, not just repeated from the draft):
- **event / subscription** — none. Re-grepped `bus.emit`/`bus.on`/`EventBus`/`event_bus` in `cogs/admin_cog.py` and `cogs/admin/` — zero hits. Admin neither publishes nor subscribes to any EventBus topic.
- **store** — none. Re-grepped `utils.db.*` / `db.get_setting` / `db.set_setting` / `settings_keys` — zero hits. Loaded-cog state lives only in `bot.extensions` (in-memory, process-lifetime only, never persisted).
- **game** — none; not a game-shaped subsystem.
- **diagnostics (DiagnosticProviderSpec)** — none owned by admin itself; the "Diagnostics" nav button routes into Lane D's `DiagnosticCog` panel (cross-lane, not audited here).
- **bindings/resources (BindingSpec/ResourceRequirement)** — none declared. Confirmed as a real, and now more severe, finding: the `on_ready` greeting resolves its destination by a **hardcoded, wrongly-spelled channel name** (`"bot_spam"` vs. the declared `"bot-spam"`) instead of a declared binding — exactly the kind of pointer a `BindingSpec` + `ResourceRequirement` pair should own, and the mismatch means this is likely already a dead feature in practice (see Structural-gap flags).
- **mutation paths (`*_mutation.py` / audited service seam)** — none. Re-grepped `emit_audit_action` / `audit_events` / `_mutation` — zero hits anywhere in `cogs/admin_cog.py` or `cogs/admin/`. Admin performs real, high-privilege state mutations (cog load/unload/reload, process restart, live log-level change) but **none of them** call `services.audit_events.emit_audit_action()` or write through an audited `*_mutation.py` seam. `!restart` records an in-memory ring-buffer + Prometheus event only (`core/runtime/lifecycle.py:354-380 _record_event` — explicitly observability-only, not a governance audit row). This is a genuine Governance & Safety gap: there is no audit trail answering "who unloaded which cog, or requested a restart, and when" (see Structural-gap flags and Reconsider).

**Structural-pattern flags:**
- **Gateway listener** — present: `@commands.Cog.listener()` on `on_ready` (admin_cog.py:409). G-1 gap, confirmed.
- **Modal wizard-lite** — present: `_LogLevelModal` (admin_cog.py:763), a single-step `discord.ui.Modal`, not a multi-step `wait_for` wizard. New finding, no existing G covers it — proposed as **G-A1**, though (per the correction above) G-A1 only fixes the field-shape half of this unit's tier, not the whole thing.
- **`wait_for` wizard** — confirmed absent. Re-grepped `wait_for(` in `cogs/admin_cog.py` and `cogs/admin/` — zero hits.
- **Scheduled loop (`@tasks.loop`)** — confirmed absent (re-grepped; zero hits).
- **Voice** — confirmed absent; the only "voice" references are a plain `len(guild.voice_channels)` read inside the stats embeds (admin_cog.py:90, 511) — a count, not voice-channel *logic*.
- **Stateful game loop** — confirmed absent; not applicable to this subsystem.
- **Dynamic cross-cog dispatch** (not in BRIEF's named list, but a real recurring pattern here) — the 9 hub nav buttons + `build_help_menu_view` all resolve their target via `interaction.client.get_cog(name)` + `getattr(..., "build_help_menu_view", None)` rather than a static reference — invisible to CodeGraph/Grimp, verified only by direct source read (per `.claude/CLAUDE.md`'s dynamic-dispatch gotcha). Fully collapses to zero-code `PanelRef` once every subsystem's panels are declared — no amendment needed, and (with the fit-number correction above) this pattern is now correctly counted as the dominant driver of admin's *low* as-written score, not hidden inside an inflated one.

#### Manifest sketch

```python
"""Admin — the operator console, expressed in the §2 grammar.

Verified 2026-07-02, adversarially re-verified 2026-07-02 (same day, second pass):
    cogs/admin_cog.py           — 11 commands, hub panel + 9 nav buttons,
                                   1 modal, 1 gateway listener (on_ready)
    cogs/admin/cog_manager.py   — cog discovery + _CogManagerView
    cogs/admin/_slash_sync.py   — diff-gated global slash-tree sync
    utils/subsystem_registry.py:59-88 — SUBSYSTEMS["admin"] (4 unwired
                                   capability strings — see ledger)

Tier verdict (CORRECTED): the hub is almost entirely navigation (PanelRef,
tier 1) once the getattr-by-cog-name convention is replaced by static
PanelRefs, but AS SHIPPED TODAY that navigation is genuinely tier 3 (a real
dynamic-dispatch workaround, not declared data) — which is why the
as-written fit is 45.0%, not the ~68% a prior pass miscalculated. The real
tier-3 pressure beyond the navigation-shape artifact is a small, deliberate
cluster of process-control escape hatches (cog load/unload/reload, restart,
slash-sync, log level, incl. the log-level modal) — none of which the
grammar should try to swallow into data, but ALL of which currently bypass
the audit seam entirely (a Governance & Safety gap, not a grammar-fit gap).
One new primitive proposed: G-A1 (ModalSpec) — it fixes the modal's field
shape but, on adversarial re-check, does not move _LogLevelModal's ledger
tier (see the ledger row).
"""

from __future__ import annotations

from tools.grammar_spike.spec import (
    Activation,
    BlockSpec,
    CommandKind,
    CommandSpec,
    EventSpec,
    FieldSpec,
    GatewayListenerSpec,
    HandlerRef,
    HelpEntrySpec,
    LayoutSpec,
    PanelActionSpec,
    PanelRef,
    PanelSpec,
    ProviderRef,
    SubsystemManifest,
)

# G-A1 (Lane A proposal, NOT in tools/grammar_spike/spec.py today): a
# declarative modal-field primitive. Sketched inline since no import
# exists yet — see "Tier-3 dispositions" for the full justification.
#
# @dataclass(frozen=True)
# class ModalFieldSpec:
#     field_id: str          # S
#     label: str             # S
#     style: str = "short"   # S — short|paragraph
#     placeholder: str = ""  # S
#     required: bool = True  # S
#     max_length: int | None = None  # S
#     bounds: tuple[int, int] | str | None = None  # S — reuses G-5

_CAP_PREFIX = "admin"

ADMIN_MANIFEST = SubsystemManifest(
    key="admin",
    display_name="Administration",
    description="Cog management, server stats, diagnostics.",
    emoji="⚙️",
    category="admin",
    visibility_tier="administrator",  # subsystem_registry.py:70-71
    # SPIKE-FINDING (this lane): all 4 declared capabilities are UNWIRED —
    # ported here verbatim as the honest current state, flagged for the
    # optimize pass to either wire for real or drop.
    capabilities=(
        "admin.cog.load",
        "admin.cog.unload",
        "admin.cog.reload",
        "admin.server.stats",
    ),
    dependencies=(),
    commands=(
        # cogs/admin_cog.py:36 — opens the hub
        CommandSpec(
            name="adminmenu",
            kind=CommandKind.PREFIX,
            summary="Open the Admin control panel.",
            route=PanelRef("admin.hub"),
            audience_tier="administrator",
            cooldown=(2, 10, "user"),  # G-4
        ),
        CommandSpec(
            name="admin",
            kind=CommandKind.SLASH,
            summary="Open the Admin control panel (ephemeral).",
            route=PanelRef("admin.hub"),
            audience_tier="administrator",
        ),
        # cogs/admin_cog.py:75 — thin read-model, no domain logic
        CommandSpec(
            name="serverstats",
            kind=CommandKind.PREFIX,
            summary="Display server statistics.",
            route=PanelRef("admin.server_stats"),
            audience_tier="administrator",
        ),
        # cogs/admin_cog.py:97 — TIER 3 (deliberate): dynamic extension
        # lifecycle has no §2 primitive and shouldn't get one.
        CommandSpec(
            name="cog",
            kind=CommandKind.PREFIX,
            summary="Load / unload / reload a cog by name.",
            route=HandlerRef(
                "admin.cog_action",
                justification="dynamic bot.load_extension/unload_extension/"
                "reload_extension — real process-state side effects",
            ),
            audience_tier="owner",
        ),
        CommandSpec(
            name="loadall",
            kind=CommandKind.PREFIX,
            summary="Load every unloaded cog.",
            route=HandlerRef("admin.load_all", justification="bulk extension load"),
            audience_tier="owner",
        ),
        CommandSpec(
            name="unloadall",
            kind=CommandKind.PREFIX,
            summary="Unload every loaded cog except this one.",
            route=HandlerRef("admin.unload_all", justification="bulk extension unload"),
            audience_tier="owner",
        ),
        CommandSpec(
            name="coglist",
            aliases=("cogs", "listcogs", "cogslist"),
            kind=CommandKind.PREFIX,
            summary="Open the interactive cog manager.",
            route=PanelRef("admin.cog_manager"),
            audience_tier="administrator",
            cooldown=(2, 10, "user"),
        ),
        # cogs/admin/_slash_sync.py — TIER 3 (deliberate): diff-gated tree sync
        CommandSpec(
            name="syncslash",
            aliases=("syncs",),
            kind=CommandKind.PREFIX,
            summary="Sync the slash-command tree (guild/global/clear).",
            route=HandlerRef(
                "admin.sync_slash",
                justification="live Discord API tree diff + sync, 3 scope branches",
            ),
            audience_tier="owner",
        ),
        CommandSpec(
            name="slashes",
            aliases=("slashlist",),
            kind=CommandKind.PREFIX,
            summary="List registered slash commands.",
            route=PanelRef("admin.slash_list"),
            audience_tier="administrator",
        ),
        # cogs/admin_cog.py:365 — TIER 3 (deliberate): process control
        CommandSpec(
            name="restart",
            kind=CommandKind.PREFIX,
            summary="Request a graceful bot restart.",
            route=HandlerRef(
                "admin.request_restart",
                justification="process lifecycle control (Lane G territory)",
            ),
            audience_tier="owner",
        ),
        # cogs/admin_cog.py:393 — process-global, non-persisted; doesn't
        # fit SettingSpec's guild-scoped model, stays a bespoke handler
        # (TIER 3 in both columns — no kernel lane exists or should exist
        # for mutating Python's own logging module; see the ledger row).
        CommandSpec(
            name="loglevel",
            kind=CommandKind.PREFIX,
            summary="Change the bot's runtime log level.",
            route=HandlerRef(
                "admin.set_log_level",
                justification="process-global, non-persisted logging.setLevel()",
            ),
            audience_tier="administrator",
        ),
    ),
    panels=(
        PanelSpec(
            panel_id="admin.hub",
            subsystem="admin",
            title="⚙️ Server & Admin",
            audience="invoker",
            body=(BlockSpec(kind="fields", provider=ProviderRef("admin.hub_status")),),
            actions=(
                PanelActionSpec(
                    action_id="stats",
                    label="📊 Server Stats",
                    handler=PanelRef("admin.server_stats"),  # TIER 1 — nav
                ),
                PanelActionSpec(
                    action_id="cog_list",
                    label="📋 Cog List",
                    handler=PanelRef("admin.cog_manager"),  # TIER 1 — nav
                ),
                PanelActionSpec(
                    action_id="reload_all",
                    label="🔄 Reload All",
                    style="secondary",
                    handler=HandlerRef(
                        "admin.reload_all",
                        justification="bulk reload_extension — real side effect",
                    ),
                    audience_tier="owner",
                    confirm=True,
                ),
                PanelActionSpec(
                    action_id="log_level",
                    label="📝 Log Level",
                    style="secondary",
                    defer_mode="modal",  # G-A1: modal field decl goes here
                    handler=HandlerRef(
                        "admin.set_log_level",
                        justification="apply to python logging module — stays "
                        "tier 3 with amendments too (see ledger)",
                    ),
                ),
                # 9× pure navigation — TIER 1 once expressed this way,
                # TIER 3 as currently shipped (getattr-by-cog-name hack) —
                # this is the dominant driver of the corrected as-written %.
                PanelActionSpec(
                    action_id="nav_settings",
                    label="🛠 Settings",
                    handler=PanelRef("settings.panel"),  # cross-subsystem, Lane D
                ),
                PanelActionSpec(
                    action_id="nav_server_mgmt",
                    label="🧭 Server Management",
                    handler=PanelRef("server_management.hub"),  # Lane A, own lane
                ),
                PanelActionSpec(
                    action_id="nav_channels",
                    label="📐 Channels",
                    handler=PanelRef("channel.hub"),  # Lane A
                ),
                PanelActionSpec(
                    action_id="nav_ai",
                    label="🤖 AI",
                    handler=PanelRef("ai.panel"),  # Lane D
                ),
                PanelActionSpec(
                    action_id="nav_platform",
                    label="🛰 Platform",
                    handler=PanelRef("platform.hub"),  # Lane D
                ),
                PanelActionSpec(
                    action_id="nav_diagnostics",
                    label="🩺 Diagnostics",
                    handler=PanelRef("diagnostic.panel"),  # Lane D
                ),
                PanelActionSpec(
                    action_id="nav_uxlab",
                    label="🧪 UX Lab",
                    handler=PanelRef("ux_lab.panel"),  # Lane D
                ),
                PanelActionSpec(
                    action_id="nav_logging",
                    label="📝 Logging",
                    handler=PanelRef("logging.panel"),  # Lane D
                ),
                PanelActionSpec(
                    action_id="nav_cleanup",
                    label="🧹 Cleanup",
                    handler=PanelRef("cleanup.panel"),  # Lane A
                ),
                PanelActionSpec(
                    action_id="overview",
                    label="↩ Overview",
                    handler=PanelRef("admin.hub"),  # TIER 1 — self re-render
                ),
            ),
            layout=LayoutSpec(
                pages=(
                    (
                        ("stats", "cog_list", "reload_all", "log_level"),
                        (
                            "nav_settings",
                            "nav_server_mgmt",
                            "nav_channels",
                            "nav_ai",
                        ),
                        (
                            "nav_platform",
                            "nav_diagnostics",
                            "nav_uxlab",
                            "nav_logging",
                            "nav_cleanup",
                        ),
                        ("overview",),
                    ),
                ),
            ),
        ),
        PanelSpec(
            panel_id="admin.server_stats",
            subsystem="admin",
            title="📊 Server Stats",
            body=(BlockSpec(kind="fields", provider=ProviderRef("admin.server_stats")),),
        ),
        PanelSpec(
            panel_id="admin.slash_list",
            subsystem="admin",
            title="📋 Slash Commands",
            body=(BlockSpec(kind="list", provider=ProviderRef("admin.slash_list")),),
        ),
        PanelSpec(
            panel_id="admin.cog_manager",
            subsystem="admin",
            title="📋 Cog Manager",
            body=(BlockSpec(kind="fields", provider=ProviderRef("admin.cog_status")),),
            selectors=(
                # cog_manager.py:200-207 attach_windowed_select — TIER 1,
                # SelectorSpec.page_size already covers >25-option paging
                # (fixes the #1040 truncation class as a side effect).
            ),
            actions=(
                PanelActionSpec(
                    action_id="load",
                    label="Load",
                    style="success",
                    handler=HandlerRef("admin.load_cog", justification="bot.load_extension"),
                    audience_tier="owner",
                ),
                PanelActionSpec(
                    action_id="unload",
                    label="Unload",
                    style="danger",
                    destructive=True,
                    handler=HandlerRef(
                        "admin.unload_cog",
                        justification="bot.unload_extension + protected-cog policy",
                    ),
                    audience_tier="owner",
                    confirm=True,
                ),
                PanelActionSpec(
                    action_id="reload",
                    label="Reload",
                    handler=HandlerRef("admin.reload_cog", justification="bot.reload_extension"),
                    audience_tier="owner",
                ),
                PanelActionSpec(
                    action_id="refresh",
                    label="🔄 Refresh",
                    handler=PanelRef("admin.cog_manager"),  # TIER 1 — re-render
                ),
            ),
        ),
    ),
    gateway_listeners=(
        # cogs/admin_cog.py:409 — G-1. Handler stays registered (TIER 2)
        # because it resolves a channel BY HARDCODED NAME today — and per
        # the adversarial pass, that hardcoded name ("bot_spam") doesn't
        # even match subsystem_registry.py's declared default ("bot-spam"),
        # so the feature is likely already dead — the optimized form binds
        # this via a declared BindingSpec instead (not shown here — see
        # Structural-gap flags).
        GatewayListenerSpec(
            gateway_event="on_ready",
            handler=HandlerRef(
                "admin.startup_greeting",
                justification="per-guild channel resolve + permission check + send",
            ),
        ),
    ),
    # PROPOSED optimization, not shipped today: close the audit-trail gap
    # (see Reconsider) by giving operator actions a real audited event.
    # CORRECTED: an EventSpec with audited=True and no expected_subscribers
    # and no observability_only=True fails tools/grammar_spike/spec.py's own
    # __post_init__ validation (confirmed by instantiating it — raises
    # ValueError). Fixed by declaring the real audit-log consumer as a
    # subscriber, which is also a more honest statement of the intended fix.
    events=(
        EventSpec(
            name="admin.operator_action",
            payload_schema=(
                FieldSpec("guild_id", "int"),
                FieldSpec("actor", "str"),
                FieldSpec("action", "str"),  # cog_load|cog_unload|cog_reload|restart|log_level
                FieldSpec("target", "str"),
            ),
            owner_subsystem="admin",
            expected_subscribers=(
                HandlerRef(
                    "audit_events.record_operator_action",
                    justification="persists the audit row — closes the "
                    "accountability gap this event exists for",
                ),
            ),
            audited=True,
        ),
    ),
    # the 4 "capabilities" above are registry metadata, not SettingSpecs —
    # deliberately no settings=() entries here.
    help=HelpEntrySpec(
        summary="The operator console — cog management, server stats, restart.",
        examples=("!adminmenu", "!coglist", "!syncslash guild"),
    ),
)
```

#### Tier-3 dispositions

- **`!cog` / `!loadall` / `!unloadall` / Load / Unload / Reload buttons (cog_manager.py)** — **deliberate escape hatch.** Dynamic Python extension loading (`bot.load_extension`/`unload_extension`/`reload_extension`) is inherently imperative; no §2 primitive should model it as data — this is Lane G's cog-loader domain surfaced through admin's operator UI. Not a grammar gap.
- **`!syncslash` (+ `_slash_sync.run_global_sync`)** — **deliberate escape hatch.** Diff-gated live Discord API tree sync with three distinct scope branches (guild/global/clear) is genuine domain logic (HTTP calls, diffing, error rendering), not a repeatable declarative shape.
- **`!restart`** — **deliberate escape hatch.** Process lifecycle control (coalescing intent, watchdog handoff) belongs to Lane G's runtime skeleton, not a subsystem-level primitive.
- **`!loglevel` (command form) / `Reload All` button** — **deliberate escape hatch.** Process-global, non-persisted runtime knob (log level) and a real bulk side-effecting bulk-reload action respectively — neither is a generic repeatable shape a new primitive would serve.
- **Log Level button (opens modal) / `_LogLevelModal`** — **partial grammar gap → G-A1**, corrected disposition. G-A1 (no existing G-1..G-6 covers modal/text-input collection) genuinely helps: the field-collection + validation shape recurs across at least 4 Lane A subsystems (admin, moderation, cleanup, ticket) and is worth building. But it does **not** clear `_LogLevelModal`'s own ledger tier — the terminal `logging.setLevel()` apply-step is the same "no kernel lane, and none should exist" bespoke mutation that keeps `!loglevel` at tier 3, so the compound unit stays tier 3 with amendments too (see the ledger row's correction).
- **`on_ready` startup listener** — **G-1** (`GatewayListenerSpec`, reused as-is). Textbook case: karma's react-to-thank and logging's 8 listeners hit the exact same gap. Independent of the grammar question, the handler's hardcoded channel name is also wrong on its own terms (`"bot_spam"` vs. the declared `"bot-spam"`) — a shipped-source bug, not a grammar-fit issue; see Structural-gap flags.
- **Settings/Server Management/Channels/AI/Platform/Diagnostics/UX Lab/Logging/Cleanup nav buttons + `build_help_menu_view`** — **not a grammar gap.** `PanelRef` already expresses "open subsystem X's panel" with zero code; the current `getattr`-by-cog-name pattern is a workaround for the *absence of the generated kernel*, not a missing primitive. No amendment proposed. This group is genuinely tier 3 **as shipped today** (a correction from a prior miscount) — it is the subsystem's biggest "looks tier-3, is actually tier-1-once-generated" finding, and the main reason the as-written fit number below reads low.

#### Fit numbers

units total: **40** · tier-1/2 (as-written): **18** · fit % as-written: **45.0%** · tier-1/2 (with amendments): **29** · fit % with amendments: **72.5%**

**Both numbers were corrected by this adversarial pass.** A prior draft claimed 27/67.5% as-written and 30/75.0% with-amendments. Recomputing directly from the 40-row ledger (verified mechanically): the as-written figure should be **18/45.0%** — the prior draft's own summary prose ("the 9-button nav-group ... graded tier-1 in both columns") directly contradicts its own ledger row for that group (tier 3 as-written, tier 1 with-amendments); 18 (the true as-written tier-1/2 count) + 9 (the nav group, mistakenly folded into the as-written side) = 27, exactly the wrong figure. The with-amendments figure is **29/72.5%**, one lower than the prior draft's 30/75.0%, because `_LogLevelModal` is corrected from a tier-3→2 "mover" to a tier-3-both-columns unit (see ledger).

Tier-3-both-columns (the irreducible **11** units — deliberate escape hatches, no amendment touches them): `!cog`, `!loadall`, `!unloadall`, `!syncslash`, `!restart`, `!loglevel` (6 commands) + `Reload All` button + `Load`/`Unload`/`Reload` buttons (cog_manager, 3) + `_LogLevelModal` (1, corrected) = 11.
Tier-3→tier-1/2 movers (**2** units, both from amendments): `Log Level button` (G-A1, →1), `on_ready` listener (G-1, →2).
The 9-button nav-group is tier-3 **as-written** and moves to tier-1 **only with amendments** (no new primitive needed — `PanelRef` already covers it); `build_help_menu_view` is tier-1 in both columns. Read correctly, admin's 45.0% as-written score is one of the *lower* measured subsystems so far — but the story is not "this subsystem is grammar-hostile": 9 of its 22 as-written tier-3 units (41% of the shortfall) are the getattr-dispatch navigation artifact, which needs **zero new grammar** to fix (it collapses the instant the generated kernel exists and every target subsystem has its own declared panel). The genuinely irreducible tier-3 core is the 11-unit process-control cluster above. Even with amendments, admin's 72.5% sits below the design spec's 80% exit bar (BRIEF.md) — but per the exit bar's own second condition ("every tier-3 unit is dispositioned: grammar-amendment or documented deliberate escape hatch"), all 11 remaining tier-3 units here are the latter, explicitly and individually justified above — so this subsystem's shortfall against 80% should be read as *expected and accepted*, not as an open grammar gap needing a new primitive.

#### Structural-gap flags

- **Permission/capability gates: declaration vs. code — CONFIRMED MISMATCH.** `SUBSYSTEMS["admin"]["capabilities"]` declares 4 capability strings (`admin.cog.load/unload/reload`, `admin.server.stats`, subsystem_registry.py:83-86) that are **completely unwired** — zero references anywhere outside the registry file itself (re-confirmed by grep). The real gate is `@commands.is_owner()` / `@admin_or_owner()` decorators. The grammar (§2.2's two-lane `capability_required` XOR `audience_tier` model) can express either lane cleanly; the shipped code has picked the decorator lane while leaving dead capability-string metadata behind. Optimize-pass action: either wire the 4 capabilities to real `capability_required` checks or delete them — don't carry dead declarations into the new bot.
- **Audit/mutation seam — CONFIRMED GAP, the subsystem's most important Governance & Safety finding.** Cog load/unload/reload, process restart, and live log-level changes are all real, high-privilege state mutations with **zero audit trail** — no `emit_audit_action()` call, no `*_mutation.py` seam, no persisted governance row (re-confirmed by grep). `!restart`'s only trace is an in-memory ring buffer + Prometheus counter (`lifecycle.py:354-380`, explicitly observability-only). The §2 grammar already has the vocabulary to fix this (`EventSpec(audited=True, expected_subscribers=...)`, the `audit: str` field on `PanelActionSpec`) — this is a **behavior gap in the shipped bot**, not a grammar-fit gap; the manifest sketch above shows the corrected fix (`admin.operator_action`, `audited=True` **with** a declared subscriber — a prior sketch omitted the subscriber and would fail the grammar's own validation).
- **Bindings/resources — a real absence, escalated to a likely-live bug by this pass.** The `on_ready` greeting hardcodes a channel by name (`"bot_spam"`) instead of a declared `BindingSpec`/`ResourceRequirement` — the exact pointer-and-provisioning shape those two primitives exist for. Worse than a design smell: that hardcoded string uses an **underscore**, while every one of the 5 `"default_channels"` declarations across `subsystem_registry.py` uses a **hyphen** (`"bot-spam"`) — confirmed the underscore form appears nowhere else in `disbot/`. `resolve_channel`'s match is an exact string compare, so today's greeting most likely finds nothing in any guild set up per the subsystem's own declared default, and fails **silently** (the `if channel and channel.permissions_for(...)` guard just skips sending, no error, no operator-visible symptom). Recommend a fast, contained follow-up fix (align the two spellings) independent of any grammar work.
- **Gateway listener** — present (`on_ready`), fully answered by existing **G-1** (the channel-name bug above is a separate, source-level issue, not a grammar gap).
- **Modal wizard-lite** — present, **new gap → G-A1** proposed this lane (not a `wait_for` multi-step wizard — genuinely absent from this subsystem); note G-A1 only partially resolves `_LogLevelModal`'s tier (see ledger/dispositions).
- **`wait_for` wizard, scheduled loop, voice, stateful game loop** — all confirmed **absent** (re-grepped; zero hits in this subsystem's files).
- **Setup/provisioning wizard** — absent; admin performs no guild-onboarding flow of its own (routes to other subsystems' setup wizards, out of scope here).

#### Reconsider / optimize

**MAP → RECONSIDER → SIMULATE → OPTIMIZE verdict: KEEP + IMPROVE.** Every capability here (operator control panel, cog lifecycle management, restart, slash-tree sync, log level) is a genuinely necessary bot-management primitive for any production Discord bot — nothing should be dropped or merged away. The subsystem needs tightening, not redesign: close the audit-trail gap (with a *correctly-constructed* `EventSpec`, subscriber included), delete or wire the 4 dead capability strings, replace the hardcoded — and **misspelled** — `"bot_spam"` channel lookup with a declared binding (fixing the spelling mismatch is a near-zero-risk, immediate win independent of any grammar work), dedup the stats/cog-status providers that are currently hand-copied into both a command and a panel button, and — once **G-A1** exists — port `_LogLevelModal` off a hand-written `discord.ui.Modal` subclass (understanding that this improves the *shape*, not the ledger tier, per the correction above).

**Optimal new-bot form:** Admin becomes a pure "operator console" `SubsystemManifest` whose hub panel is almost entirely `PanelRef` navigation into other subsystems' own declared panels (tier 1, zero code) plus a small, explicitly-audited cluster of `HandlerRef`-backed operator actions (cog load/unload/reload, restart, slash-sync, log-level) that each emit a new `admin.operator_action` `EventSpec` (`audited=True`, with a real declared subscriber) — closing the accountability gap without pretending process control is declarative data it isn't. The startup greeting becomes a `GatewayListenerSpec` with a `BindingSpec`-resolved destination, not a hardcoded (and currently mis-spelled) name.

**Dependency-layer guess:** **Early governance, directly above L0.** Admin is the bot-management console sitting on top of Lane G's runtime skeleton (cog loader, lifecycle) — every other subsystem depends on being loadable/reloadable/restartable through it, and its hub is typically the first panel an operator opens. Build it right after L0 foundations, before feature subsystems.

**Production-grade done-definition (acceptance test):** (1) all 4 declared capabilities are either wired to a real `capability_required` check or removed; (2) cog load/unload/reload, restart, and log-level changes each emit a correctly-constructed `admin.operator_action` audit row (with a real subscriber, not just `audited=True`) — the parity golden queries `audit_log`/equivalent after each action and expects a row; (3) the startup greeting resolves its destination via a declared `BindingSpec` (with a spelling that actually matches the subsystem's own default-channel convention), not a literal, mismatched channel name — deleting/renaming the bound channel triggers the resource-requirement's provisioning prompt, not silent failure; (4) zero `getattr(cog, "build_help_menu_view", None)`-style dynamic dispatch remains in the hub — every nav button is a static `PanelRef`; (5) `!serverstats`/Stats-button and `!coglist`/Cog-List-button each share one provider, no duplicated inline embed code.

**Outperform target:** most hobby/public Discord bots don't expose live cog reload with a protected-cog denylist and a paginated (>25-option) cog picker at all — typically just an unguarded `!reload <cog>` owner command with no safety rails, if that. Ours already beats that baseline (protected-cog set, windowed select, diff-gated slash sync). The gap versus a genuinely best-in-class ops console is the missing audit trail — once the (correctly-constructed) `admin.operator_action` event lands, this strictly outperforms typical hobby-bot admin cogs. **Pending Lane F**: dynamic in-Discord cog management is not a common public-bot feature (most large bots like MEE6/Carl-bot/Dyno don't expose raw extension loading to operators at all — that's usually a private ops console outside Discord), so a direct feature-for-feature public comparator may not exist; flag for Lane F to confirm rather than assume.

**Owner-gated/blocked/external-dependency:** none blocking today. `G-A1` (ModalSpec) and the audit-trail addition are net-new grammar/behavior that only need owner sign-off at Phase-3 build time (the standing Phase-3 gate), not blocked now — this audit records them as planning evidence, not a build authorization. The `bot_spam`/`bot-spam` spelling fix is a plain source bug and is not owner-gated in that sense, but is out of scope for this documentation-only audit to apply directly (see BRIEF.md's read-only boundary) — flagging it here is the correct next step.

**Cross-lane dependencies:** Lane D nav targets (Settings / AI / Platform / Diagnostics / UX Lab / Logging panels) and Lane G's cog-loader/lifecycle overlap (`!cog`/`!loadall`/`!unloadall`/cog_manager buttons all bottom out in Lane G's extension-loading primitives; `!restart` bottoms out in Lane G's runtime skeleton). Note: `SubsystemManifest` in `tools/grammar_spike/spec.py` has **no `cross_lane_dependencies` field** today (checked directly) — this paragraph is prose, not a citation to an existing grammar field; if the capstone wants this queryable per-subsystem, it would need to be added as a new spec field or derived from `PanelRef` targets during simulation.

---

### server_management
_cogs: disbot/cogs/server_management_cog.py, disbot/services/server_management_hub.py, disbot/views/server_management/hub.py, disbot/views/server_management/access_map.py_

**Verification note on the pre-extracted scaffold:** the scaffold's "body truncated past line 355, ⚠ unverified" flag on the 🔄 Refresh button is now resolved — `hub.py` is 369 lines total; `refresh_btn` runs 347–369 and the file ends cleanly there (no further content). All other pre-extracted line citations were checked against source and are correct; `AccessMapView` (access_map.py:363) and `HelpPreviewView` (access_map.py:401) line numbers are confirmed exact. The registry citation (subsystem_registry.py:94–121) is confirmed: `capabilities: []` is genuinely empty at line 120, `parent_hub: "admin"` at line 116 (also confirmed independently in `disbot/utils/hub_registry.py:247`, where `server_management` is a `primary_children` entry of the `admin` HubEntry — the same "nested under Admin" fact from two independent sources). **Additional verifier pass (adversarial re-check, 2026-07-02):** re-opened all 4 files byte-for-byte, re-ran every "absent" grep claim independently, and diffed the manifest sketch's field usage against `tools/grammar_spike/spec.py`'s actual dataclass fields. Found and fixed: (a) an invented `PanelSpec.capability_required` field that does not exist in the grammar, (b) a resulting under-declaration of `audience_tier` on 8/9 panel actions and both subpanels' selectors in the manifest sketch, (c) a missing `audience="public"` on the two subpanel `PanelSpec`s, (d) a mischaracterization of the ✏️ Help editor button as "same class" as the 4 dynamic-dispatch buttons when it is actually a distinct implementation shape, and (e) an overstated "verbatim" claim for the registry-root row. None of these change any unit's tier or the fit numbers — see the ledger, manifest sketch, and tier-3 dispositions below for the corrected text. Also cross-checked `ground-truth/command-surface.json` programmatically: it tags `!servermanagement` as `perm: "member"`, which conflicts with the real `@admin_or_owner()` decorator (cog.py:44) and the manifest sketch's `audience_tier="administrator"`. This is a known ground-truth extraction-tool blind spot, not a draft error — the same tool tags `admin_cog.py`'s `!adminmenu` (also `@admin_or_owner()`-gated) as `perm: "member"` too, confirming the extractor only recognizes `@commands.has_permissions(...)`-style decorators, not the codebase's custom `admin_or_owner()` check. Source code wins per project convention; the draft's own audience_tier value was already correct, it just never surfaced the ground-truth conflict.

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !servermanagement (aliases: servermenu, guildmenu) | command | disbot/cogs/server_management_cog.py:39-45 | 1 | 1 | command → panel route: kernel open-panel workflow (persistent-panel anchor via `panel_manager.get_or_render_panel`), identical shape to logging's `!logging` tier-1 row. **Ground-truth caveat:** `command-surface.json` tags this `perm: "member"`, but source (`@admin_or_owner()`, cog.py:44) and the manifest sketch's `audience_tier="administrator"` are correct — a known extraction-tool blind spot for the custom `admin_or_owner()` decorator (same false tag on `admin_cog.py`'s `!adminmenu`). |
| /server-management | command | disbot/cogs/server_management_cog.py:73-80 | 1 | 1 | same panel, ephemeral slash surface — pure declaration, same kernel open-panel workflow; ground-truth correctly tags this one `perm: "admin"` (the slash path uses `@app_commands.default_permissions(administrator=True)`, which the extractor does recognize). |
| build_help_menu_view (Help-menu direct-nav hook) | help | disbot/cogs/server_management_cog.py:59-71 | 2 | 1 (G-A3) | registered thin handler today (guild-None guard + delegate to `build_server_management_hub`) — no real domain logic; G-A3 turns "Help picks this subsystem → open its panel" into a plain declared PanelRef, removing even the thin wrapper. This hook is invoked project-wide via `getattr(cog, "build_help_menu_view", None)` (`cogs/help/route.py:309`, `views/hub_children.py:185`, `views/navigation.py:345`, `views/settings/subsystem_view.py:339`, `services/customization_catalogue.py:275`) — the pattern is universal, not unique to this subsystem, which strengthens rather than weakens the case for a declarative replacement. |
| SUBSYSTEMS["server_management"] registry entry (display_name/description/emoji/color/visibility_tier/category/tags/entry_points/parent_hub/ui_priority; capabilities=[]) | setting (registry root) | disbot/utils/subsystem_registry.py:94-121 | 1 | 1 | **Corrected from draft:** overlaps `SubsystemManifest`'s root fields (`display_name`/`description`/`emoji`/`category`/`visibility_tier`/`capabilities`/`dependencies`/`parent_hub`/`ui_priority`) but is **not** verbatim/1:1 as the draft claimed — several registry-dict fields have **no** corresponding `SubsystemManifest` field today: `tags`, `entry_points` (redundant with `CommandSpec.name` anyway), `default_channels`, `related_subsystems`, `soft_dependencies`, `supports_dm`, `has_cleanup_rules`, `visibility_mode`, and `color` (an `int` value here vs. the spec's `color_token` (`str` token) — a representation mismatch, not just an omission). Still tier 1 (static declarative data, no domain logic either way) — this is a fidelity correction to the rationale text, not a tier change. |
| ServerManagementHubView (persistent panel container: `@register`, static `server_management:*` custom_ids, authority-gated `interaction_check`, admin-hub parent nav) | panel | disbot/views/server_management/hub.py:117-134 | 1 | 1 | **Corrected from draft:** the draft's rationale invented a `PanelSpec.capability_required` field — verified against `tools/grammar_spike/spec.py:190-207`, `PanelSpec` has no such field (only `CommandSpec`/`PanelActionSpec`/`SelectorSpec`/`SettingSpec`/`BindingSpec` do). The real declarative pattern — confirmed in the shipped `tools/grammar_spike/manifests/server_logging.py` worked manifest, which repeats `capability_required=_CAP` on every individual action — is `audience_tier="administrator"` (or `capability_required`) set on **each** `CommandSpec`/`PanelActionSpec`/`SelectorSpec` that belongs to this panel, not a single panel-level field. That's still tier 1 (still pure declared data, just distributed per-component instead of centralized); `PanelSpec(audience="persistent", timeout_s=None, navigation=NavigationSpec(parent=PanelRef("admin.panel")))` plus per-action `audience_tier="administrator"` is the accurate target form. Restoration-across-restart is the kernel's persistent-view workflow, not bespoke code. |
| 🛡️ Moderation button (routes to Moderation panel) | panel-action | disbot/views/server_management/hub.py:174-185 (`_open_manager` at 138-170) | 3 | 1 (G-A3) | as-written: real glue code — dynamic `interaction.client.get_cog("ModerationCog")` + `getattr(cog, "build_help_menu_view", None)` + try/except with a user-facing fallback message; with G-A3: a plain `PanelActionSpec(handler=PanelRef("moderation.panel"), audience_tier="administrator")`. |
| 📺 Channels button (routes to Channels panel) | panel-action | disbot/views/server_management/hub.py:187-198 | 3 | 1 (G-A3) | same dynamic dispatch shape as Moderation, target `ChannelCog`. |
| 🎭 Roles button (routes to Roles panel) | panel-action | disbot/views/server_management/hub.py:200-211 | 3 | 1 (G-A3) | same dynamic dispatch shape, target `RoleCog`. |
| 🧹 Cleanup button (routes to Cleanup panel) | panel-action | disbot/views/server_management/hub.py:213-224 | 3 | 1 (G-A3) | same dynamic dispatch shape, target `Cleanup` cog. |
| 🧩 Setup button (hands off to Setup's wizard entry) | panel-action | disbot/views/server_management/hub.py:226-243 | 3 | 3 | deliberate escape hatch: the button body is a 2-line lazy-imported `HandlerRef`-style dispatch (`cogs.setup._wizard_entry.open_wizard_from_slash`), already the named §2.9 escape-hatch shape — no amendment removes it because it hands off to a genuinely stateful multi-step flow. Structural gap: "setup" has **no** entry in `SUBSYSTEMS` at all (confirmed both by grep and by importing `utils.subsystem_registry` directly in Python — 43 keys total, `setup` absent), so this wizard is reachable only through this one button and is registry-invisible — see Structural-gap flags. |
| 🔓 Access Map button (opens AccessMapView) | panel-action | disbot/views/server_management/hub.py:245-277 | 1 | 1 | thin: guild-check + `safe_defer` + call `build_access_map_embed` (a provider) + open subpanel — kernel open-panel workflow, same shape as logging's "routes" nav button. |
| AccessMapView subpanel (audience-tier selector + paginated feature-detail drill-down over `project_access_map`) | help | disbot/views/server_management/access_map.py:118-153, 247-329, 363-398 | 2 | 2 | governance-transparency read-model panel: `BlockSpec(kind="table", provider=ProviderRef(...))` + two `SelectorSpec`s (`options_source`, `page_size` are already-declared §2 fields) — highly declarative already; only the per-feature "show source chain" drill-down (:290-320) is a thin registered `HandlerRef` (real but simple text formatting, no domain logic). Note: `_AudienceTierSelect` (:247-266) is shared code also reused by `HelpPreviewView` below, not exclusive to this row — attributed here only because it's defined once in this line range. |
| 👁 Help Preview button (opens HelpPreviewView) | panel-action | disbot/views/server_management/hub.py:279-311 | 1 | 1 | same shape as Access Map button — thin open-panel workflow over a provider. |
| HelpPreviewView subpanel (audience-tier selector over `project_help_with_execution`) | help | disbot/views/server_management/access_map.py:175-244, 401-429 | 2 | 2 | same class as AccessMapView above — `BlockSpec(table)` + one `SelectorSpec` (audience tier, reusing the shared `_AudienceTierSelect`); no bespoke view logic survives beyond the selector's re-render call. |
| ✏️ Help editor button (hands off to Lane D's Help appearance editor) | panel-action | disbot/views/server_management/hub.py:313-345 | 3 | 1 (G-A3) | as-written: constructs a brand-new ephemeral message directly (`interaction.response.send_message`) plus a **redundant** inline admin re-check (the view's class-level `interaction_check` already gates every callback) — real, if thin, glue code; with G-A3 this is `PanelActionSpec(handler=PanelRef("help.editor_home"), audience_tier="administrator")`. **Corrected from draft:** this is a *different implementation shape* than the 4 routed-manager buttons above — it does a **static** lazy import (`from views.help.editor import HelpEditorHomeView, build_editor_home_embed`) and a fresh `send_message`, not the dynamic `get_cog(...)+getattr(...)` + `edit_message`-in-place pattern `_open_manager` uses. Same *category* of gap (hand-rolled cross-subsystem navigation glue), but not literally "the same code" — see the Tier-3 dispositions section. **Cross-lane:** `help` is Lane D. |
| 🔄 Refresh button (re-renders hub status) | panel-action | disbot/views/server_management/hub.py:347-369 | 1 | 1 | `safe_defer` + recompute providers + re-render same panel — the kernel's generic re-render workflow, identical to logging's "panel: refresh status" tier-1 row. |
| HubStatus badge composer (`collect_hub_status` + 5 per-manager badge builders + `_worst_glyph`/`_overall` severity aggregation) | diagnostics | disbot/services/server_management_hub.py:93-323 | 3 | 3 | deliberate escape hatch: `DiagnosticProviderSpec.provider: HandlerRef` already exists in §2 (`tools/grammar_spike/spec.py:386-390`, no amendment needed) and makes the *registration* declarative, but the computation itself (permission-readiness checks via `utils.moderation_feasibility`/`utils.role_feasibility`, setup-percentage thresholds, fail-safe try/except-per-badge degrade-to-❓ contract) is real branching domain logic that should stay code — same class as blackjack's game engine. |

**Unit kinds present:** command, panel, panel-action, help, diagnostics, setting (registry-root only).
**Unit kinds explicitly absent:** **setting** (no `schemas.py`/`register_schemas`/`settings_keys` module for this subsystem — confirmed by grep; the only "setting"-kind row is the registry root metadata dict, not a configurable value), **listener** (no `@bot.event`/`@commands.Cog.listener`/gateway hook in any of the 4 files — confirmed by grep), **event** (no `bus.emit`/`bus.on`/`EventBus` usage anywhere in the 4 files — confirmed by grep, and independently confirmed no other file registers `server_management` with `core.runtime.live_update_scheduler.register_refresh` either, closing the "invisible to grep" EventBus-subscription loophole CLAUDE.md warns about), **store** (no `utils.db.*` call, no migration-owned table — confirmed by grep; this subsystem owns zero persisted state), **game** (not applicable — not a game subsystem), **bindings/resources** (no `BindingSpec`/`ResourceRequirement`-shaped channel/role binding owned here — Setup and the routed managers own their own bindings), **mutation paths** (no `*_mutation.py` and zero `emit_audit_action` calls in any of the 4 files — this subsystem performs **zero writes**; it is purely read/navigate).

**Structural-pattern flags:**
- Gateway listener: **absent** — no `@bot.event`/`@commands.Cog.listener`/`on_ready` etc. anywhere in `server_management_cog.py`, `server_management_hub.py`, `views/server_management/hub.py`, or `views/server_management/access_map.py` (verified by grep across all 4 files). (The string `on_ready` appears once, in a module-docstring sentence describing the *kernel's* generic restart-restoration behavior, not a listener defined in this subsystem's own code.)
- Message-pipeline stage: **absent** — no `message_pipeline.register`/stage class found.
- `wait_for` wizard: **absent in this subsystem's own code** (no `wait_for` call in any of the 4 files) — but the 🧩 Setup button (hub.py:226-243) hands off to a *different, unregistered* subsystem (`cogs/setup/`) whose own docstring-described "session/depth lifecycle in a dedicated channel" strongly implies a `wait_for`-class wizard; not read in full (out of this subsystem's 4-file scope) — flagged, not asserted.
- Scheduled loop / `@tasks.loop`: **absent** — no scheduled task in any of the 4 files.
- Voice: **absent** — no voice-state handling.
- EventBus emit/subscribe: **absent** — no `bus.on`/`bus.emit`/`EventBus` import or call in any of the 4 files (grep-confirmed; this matters here because CLAUDE.md flags EventBus wiring as invisible to both CodeGraph and import-graph tools, so it was grepped directly rather than inferred from a blast-radius tool — and cross-checked against `core/runtime/live_update_scheduler.py`'s registration table, which has no `server_management` entry either).
- Dynamic/`getattr` dispatch: **present** — `_open_manager` (hub.py:138-170) does `interaction.client.get_cog(cog_name)` + `getattr(cog, "build_help_menu_view", None)`; this is the CLAUDE.md-flagged "invisible to both tools" class of wiring and is the concrete evidence behind the G-A3 proposal above. **Additional context the draft omitted:** `disbot/views/hub_children.py`'s `HubChildButton`/`discover_hub_children` already generalizes almost exactly this pattern (resolve child cog → `build_help_menu_view` → back-nav → edit in place) for the Games/Community/Utility hubs, which is concrete existing-code precedent that a declarative version of this exact seam is both desirable and buildable. It does **not** directly cover server_management's case today, though: `discover_hub_children` keys off `parent_hub == <hub_key>` in `SUBSYSTEMS`, and none of moderation/channel/role/cleanup declare `parent_hub == "server_management"` (verified: moderation→`None`, channel→`admin`, role→`community`, cleanup→`moderation`) — server_management's routing is a curated cross-hub aggregation of *siblings*, not a `parent_hub`-discovered set of children, so `HubChildButton` doesn't apply verbatim without a discovery-key extension. This strengthens the case that G-A3 is a real, buildable, already-precedented primitive; it doesn't change the tier-3 disposition.

#### Manifest sketch

```python
"""Server Management — routing-only operator hub (Lane A capability-audit sketch).

Not runnable — expresses server_management AS a §2 manifest for grammar-fit
measurement only. Source of truth (verified 2026-07-02):
    cogs/server_management_cog.py      — !servermanagement / /server-management (39-96)
    services/server_management_hub.py  — HubStatus badge composer (93-323)
    views/server_management/hub.py     — ServerManagementHubView, 11 buttons (117-369)
    views/server_management/access_map.py — AccessMapView / HelpPreviewView (118-429)
    utils/subsystem_registry.py:94-121 — SUBSYSTEMS["server_management"] (capabilities=[])

G-A3 (proposed, Lane-A-local): a declared cross-subsystem PanelRef convention
(or a HelpEntrySpec.direct_nav field) replacing the hand-rolled cross-subsystem
navigation glue seen below in two different shapes: (1) the dynamic
`get_cog(...) + getattr(..., "build_help_menu_view")` dispatch used 4x
(Moderation/Channels/Roles/Cleanup, via `_open_manager`), and (2) a 5th,
differently-shaped instance — the Help-editor button's static lazy import +
fresh `send_message` (hub.py:313-345). Both are hand-written per-hub
cross-subsystem navigation that the same declarative family would replace.

NOTE ON §2 AS WRITTEN: PanelSpec has no `capability_required`/`audience_tier`
field (verified against tools/grammar_spike/spec.py) — admin-gating an entire
panel today means repeating `audience_tier="administrator"` on every
CommandSpec/PanelActionSpec/SelectorSpec that belongs to it (the pattern the
shipped tools/grammar_spike/manifests/server_logging.py manifest already
uses). Every action/selector below is annotated accordingly, matching the
real `ServerManagementHubView.interaction_check` /
`_AccessPanelBase.interaction_check` admin-floor gates.
"""

from __future__ import annotations

from tools.grammar_spike.spec import (
    BlockSpec,
    CommandKind,
    CommandSpec,
    DiagnosticProviderSpec,
    HandlerRef,
    LayoutSpec,
    NavigationSpec,
    PanelActionSpec,
    PanelRef,
    PanelSpec,
    ProviderRef,
    SelectorSpec,
    SubsystemManifest,
)

SERVER_MANAGEMENT_MANIFEST = SubsystemManifest(
    key="server_management",
    display_name="Server Management",
    description="Unified hub for moderation, channels, roles, cleanup, setup.",
    emoji="🧭",
    category="admin",
    visibility_tier="administrator",
    capabilities=(),  # routing-only hub — subsystem_registry.py:120
    parent_hub="admin",  # subsystem_registry.py:116; hub_registry.py:247
    commands=(
        # cogs/server_management_cog.py:39-45 — persistent-panel front door
        CommandSpec(
            name="servermanagement",
            kind=CommandKind.PREFIX,
            summary="Open the Server Management hub.",
            aliases=("servermenu", "guildmenu"),
            route=PanelRef("server_management.hub"),
            audience_tier="administrator",
        ),
        # cogs/server_management_cog.py:73-80 — ephemeral slash front door
        CommandSpec(
            name="server-management",
            kind=CommandKind.SLASH,
            summary="Open the Server Management hub (ephemeral).",
            route=PanelRef("server_management.hub"),
            audience_tier="administrator",
        ),
    ),
    panels=(
        PanelSpec(
            panel_id="server_management.hub",
            subsystem="server_management",
            title="🧭 Server Management Hub",
            audience="persistent",
            timeout_s=None,
            body=(
                BlockSpec(
                    kind="fields",
                    provider=ProviderRef("server_management.hub_status"),
                ),
            ),
            actions=(
                # hub.py:174-224 — TIER 3 as-written (dynamic get_cog+getattr
                # dispatch + try/except fallback); G-A3 → plain PanelRef.
                # audience_tier added: interaction_check gates ALL of these to
                # administrator (hub.py:126-134) — PanelSpec itself has no
                # such field, so it is declared per-action (see NOTE above).
                PanelActionSpec(
                    action_id="moderation",
                    custom_id_override="server_management:moderation",
                    label="🛡️ Moderation",
                    handler=PanelRef("moderation.panel"),  # target state (G-A3)
                    audience_tier="administrator",
                ),
                PanelActionSpec(
                    action_id="channels",
                    custom_id_override="server_management:channels",
                    label="📺 Channels",
                    handler=PanelRef("channel.panel"),
                    audience_tier="administrator",
                ),
                PanelActionSpec(
                    action_id="roles",
                    custom_id_override="server_management:roles",
                    label="🎭 Roles",
                    handler=PanelRef("role.panel"),
                    audience_tier="administrator",
                ),
                PanelActionSpec(
                    action_id="cleanup",
                    custom_id_override="server_management:cleanup",
                    label="🧹 Cleanup",
                    handler=PanelRef("cleanup.panel"),
                    audience_tier="administrator",
                ),
                # hub.py:226-243 — deliberate escape hatch: Setup is not even
                # a registered SUBSYSTEMS key (see Structural-gap flags).
                PanelActionSpec(
                    action_id="setup",
                    custom_id_override="server_management:setup",
                    label="🧩 Setup",
                    handler=HandlerRef(
                        "setup.open_wizard",
                        justification="hands off to Setup's own wait_for "
                        "provisioning wizard — real stateful flow, out of "
                        "this subsystem's own scope",
                    ),
                    audience_tier="administrator",
                ),
                PanelActionSpec(
                    action_id="access_map",
                    custom_id_override="server_management:access_map",
                    label="🔓 Access Map",
                    handler=PanelRef("server_management.access_map"),
                    audience_tier="administrator",
                ),
                PanelActionSpec(
                    action_id="help_preview",
                    custom_id_override="server_management:help_preview",
                    label="👁 Help Preview",
                    handler=PanelRef("server_management.help_preview"),
                    audience_tier="administrator",
                ),
                # hub.py:313-345 — cross-lane handoff into Lane D's help editor
                # (a 5th, differently-shaped cross-subsystem glue instance —
                # static import + fresh send_message, not get_cog+getattr).
                PanelActionSpec(
                    action_id="help_editor",
                    custom_id_override="server_management:help_editor",
                    label="✏️ Help editor",
                    handler=PanelRef("help.editor_home"),  # target state (G-A3)
                    audience_tier="administrator",
                ),
                PanelActionSpec(
                    action_id="refresh",
                    custom_id_override="server_management:refresh",
                    label="🔄 Refresh",
                    handler=PanelRef("server_management.hub"),  # re-render, TIER 1
                    audience_tier="administrator",
                ),
            ),
            navigation=NavigationSpec(parent=PanelRef("admin.panel")),
            layout=LayoutSpec(
                pages=(
                    (
                        ("moderation", "channels", "roles"),
                        ("cleanup", "setup"),
                        ("access_map", "help_preview", "help_editor", "refresh"),
                    ),
                ),
            ),
        ),
        # access_map.py:118-153,247-329,363-398 — governance-transparency
        # subpanel: near-fully declarative already. audience="public": the
        # real view sets BaseView(public=True) (access_map.py:341-343) —
        # authority-gated, not owner-locked, so "invoker" (the spec default)
        # would misdescribe it.
        PanelSpec(
            panel_id="server_management.access_map",
            subsystem="server_management",
            title="🔓 Access Map",
            audience="public",
            body=(BlockSpec(kind="table", provider=ProviderRef("access_map.decisions")),),
            selectors=(
                SelectorSpec(
                    selector_id="audience_tier",
                    kind="enum",
                    on_select=PanelRef("server_management.access_map"),  # rerender
                    options_source=(
                        "user", "trusted", "staff", "moderator", "administrator",
                    ),
                    audience_tier="administrator",
                ),
                SelectorSpec(
                    selector_id="feature_detail",
                    kind="entity",
                    on_select=HandlerRef("access_map.show_source_chain"),
                    options_source=ProviderRef("access_map.features"),
                    page_size=25,
                    audience_tier="administrator",
                ),
            ),
            navigation=NavigationSpec(parent=PanelRef("server_management.hub")),
        ),
        # access_map.py:175-244,401-429 — same audience="public" reasoning.
        PanelSpec(
            panel_id="server_management.help_preview",
            subsystem="server_management",
            title="👁 Help Preview",
            audience="public",
            body=(
                BlockSpec(kind="table", provider=ProviderRef("help_preview.projection")),
            ),
            selectors=(
                SelectorSpec(
                    selector_id="audience_tier",
                    kind="enum",
                    on_select=PanelRef("server_management.help_preview"),
                    options_source=(
                        "user", "trusted", "staff", "moderator", "administrator",
                    ),
                    audience_tier="administrator",
                ),
            ),
            navigation=NavigationSpec(parent=PanelRef("server_management.hub")),
        ),
    ),
    diagnostics=(
        # services/server_management_hub.py:93-323 — registration is
        # declarative; the computation stays a deliberate escape hatch.
        DiagnosticProviderSpec(
            name="server_management.hub_status",
            provider=HandlerRef(
                "server_management.collect_hub_status",
                justification="composes moderation/channel/role/cleanup/setup "
                "readiness signals — real branching logic, by design",
            ),
            lane="sync",
            audience="admin",
        ),
    ),
    help=None,  # no catalogued HelpEntrySpec summary/examples text found for
    # server_management in services/help_catalogue.py — only the direct-nav
    # hook (build_help_menu_view) exists today.
)
```

#### Tier-3 dispositions

- **🛡️ Moderation / 📺 Channels / 🎭 Roles / 🧹 Cleanup buttons** (hub.py:174-224) — **grammar gap → G-A3.** Each does `interaction.client.get_cog(cog_name)` + `getattr(cog, "build_help_menu_view", None)` + a try/except with a user-facing fallback message. This is real glue code, not domain logic — the *shape* (open another subsystem's canonical panel) is completely generic and repeatable across every hub-of-hubs in the bot, so it belongs in the grammar as a declared `PanelRef`, not hand-written per hub. (`disbot/views/hub_children.py`'s `HubChildButton` already generalizes this exact "resolve cog → `build_help_menu_view` → back-nav → edit in place" pattern for Games/Community/Utility, though it's keyed off `parent_hub` discovery and doesn't cover this subsystem's curated-sibling routing as-is — concrete precedent that the shape is buildable, not proof G-A3 is redundant.)
- **✏️ Help editor button** (hub.py:313-345) — **grammar gap → G-A3**, same *category* of gap as the four buttons above (hand-rolled cross-subsystem navigation), but a **different implementation shape**: a static lazy import (`from views.help.editor import HelpEditorHomeView, build_editor_home_embed`) + a fresh `interaction.response.send_message`, not the dynamic `get_cog(...)+getattr(...)` + `edit_message`-in-place `_open_manager` pattern the other four share. (The draft mischaracterized this as literally "the same class" / part of a uniform "5x" dispatch pattern — corrected here.) Plus a redundant inline admin re-check that duplicates the view's own `interaction_check`.
- **🧩 Setup button** (hub.py:226-243) — **deliberate escape hatch.** The button body is already the named §2.9 `HandlerRef` escape-hatch shape (2 lines: lazy import + await); no amendment removes it because it hands off to a genuinely stateful, multi-step external flow. The real gap here isn't grammar-fit, it's registry coverage: **`setup` has no entry in `SUBSYSTEMS` at all** (confirmed by grep of all 43 registered keys, and independently by importing `utils.subsystem_registry` and enumerating `SUBSYSTEMS.keys()` in Python) — flagged under Structural-gap flags, not proposed as a grammar amendment.
- **HubStatus badge composer** (`collect_hub_status` + 5 badge builders + `_worst_glyph`/`_overall`, server_management_hub.py:93-323) — **deliberate escape hatch.** `DiagnosticProviderSpec` (§2, no amendment needed) already makes the *registration* declarative, but the readiness/feasibility computation itself (permission checks, thresholds, fail-safe-to-❓ degradation) is real domain logic that should stay code, the same call RESULTS.md makes for blackjack's game engine and karma's audited grant seam.

#### Fit numbers

| Scope | Surface units | Fit — spec as written | Fit — with proposed families |
|---|---|---:|---:|
| server_management | 17 | **58.8%** (10/17) | **88.2%** (15/17) |

Tier-1/2-as-written units (10): `!servermanagement`, `/server-management`, `build_help_menu_view` (tier 2), registry root entry, `ServerManagementHubView` container, 🔓 Access Map button, AccessMapView subpanel (tier 2), 👁 Help Preview button, HelpPreviewView subpanel (tier 2), 🔄 Refresh button.
Tier-3-as-written units (7): Moderation/Channels/Roles/Cleanup/Help-editor buttons (5, all → G-A3 — noting the Help-editor button is a differently-shaped instance of the same gap, per the correction above), Setup button (escape hatch), HubStatus badge composer (escape hatch).
With G-A3 applied, 5 of the 7 tier-3 units move to tier 1, leaving 2 genuine, permanent escape hatches (15/17 = 88.2%) — comparable to logging's 79%→97% jump (`tools/grammar_spike/RESULTS.md:13`), driven here by one concentrated, repeated gap (cross-subsystem navigation, in two implementation shapes) rather than several small ones. **No tier was changed by this verification pass** — the corrections above are to citation accuracy, manifest-sketch fidelity, and shape mischaracterization, not to any tier verdict, so the fit numbers are unchanged from the draft.

#### Structural-gap flags

- **Permission/capability gates** — well-covered, no gap: the hub's authority-gated `interaction_check` (administrator floor, re-evaluated live on every interaction) is exactly the shape `audience_tier`/`capability_required` + the runtime's re-check-at-click contract already model (§2 as written) — declared per-component (§2 has no panel-level gate field; see the ServerManagementHubView ledger row correction above), not as a single field on `PanelSpec`.
- **Setup/provisioning wizards** — **flag, not this subsystem's to fix.** The 🧩 Setup button is this subsystem's only doorway into a `wait_for`-class wizard that lives in `cogs/setup/`, which is **not a registered `SUBSYSTEMS` key** — confirmed by grepping and by importing all 43 keys in `disbot/utils/subsystem_registry.py`. This means Setup's capability gating, audit trail, and help/discoverability are all invisible to the very registry this audit's coverage guarantee is keyed off (PARTITION.md: "43 = every subsystem in `SUBSYSTEMS`"). This is a genuine structural gap worth the capstone's attention — likely Lane G (registry completeness) or an owner decision, not a Lane A grammar amendment.
- **`wait_for` wizards** — same flag as above; not reproduced in this subsystem's own code.
- **External API opt-ins** — absent; no external API calls in any of the 4 files.
- **Audit/mutation seams** — **absent by design.** This subsystem performs **zero writes** (no `*_mutation.py`, no `emit_audit_action` call, no `utils.db.*` call anywhere in the 4 files) — it is a pure read/navigate/diagnose hub. The grammar doesn't need to express a mutation seam here because there isn't one.
- **Destructive actions** — absent; no `PanelActionSpec.destructive=True`-shaped button exists (nothing here deletes/bans/etc. — those live in the routed subsystems).
- **Lifecycle tasks/scheduled loops** — absent; no `@tasks.loop` in any of the 4 files.
- **Governance/cache behavior** — deliberately **no caching**: `collect_hub_status` is recomputed fresh on every open and every 🔄 Refresh click (the module docstring states this explicitly: "the view caches nothing across button clicks"). This is a chosen behavior, not a grammar limitation — no amendment needed, though a future `DiagnosticProviderSpec.cache_ttl`-style field could be a candidate if the 5-detector fan-out ever becomes a latency problem (not evidenced today).

#### Reconsider / optimize

**MAP → RECONSIDER → SIMULATE → OPTIMIZE verdict: KEEP + IMPROVE.** The single-entry-point operator hub — one panel aggregating live, fail-safe read-only health badges plus one-click navigation into every specialised manager — is exactly the right shape for the new bot and should be preserved wholesale; it is not a candidate for merge/drop/redesign. What should change is **how** the navigation and the Setup handoff are wired: (1) formalize the G-A3 cross-subsystem `PanelRef` convention so the 5 hub buttons stop hand-rolling cross-subsystem navigation glue (in either of its two shapes — dynamic `get_cog`+`getattr` or static import + fresh send) — this is pure mechanical cleanup, zero behavior change; (2) register `setup` as a proper `SUBSYSTEMS` entry with its own capability (e.g. `setup.wizard.run`) so its wizard lifecycle gets the same capability-gating, audit, and help-discoverability every other governed flow gets, instead of being reachable only through one hub button and invisible to the registry.

**Optimal new-bot form:** a `SubsystemManifest` for `server_management` with `capabilities=()` (it stays a pure router — that's correct, not a gap), its panel actions expressed as declared `PanelRef`s into each child subsystem's canonical `panel_id` (the kernel resolves these statically at generation time and renders one generic "panel unavailable" fallback for every hub in the bot on a resolution failure, replacing today's bespoke per-button try/except and the Help-editor button's bespoke fresh-message path alike), its `HubStatus` badge composer kept exactly as a registered `DiagnosticProviderSpec` (this part is already right — the computation legitimately stays code), and the Access Map / Help Preview subpanels essentially unchanged (they are already close to the grammar's ideal: `SelectorSpec`-driven, `ProviderRef`-backed, zero bespoke view logic beyond one thin drill-down handler — declared `audience="public"` + per-component `audience_tier="administrator"`, not a bespoke panel-level gate). Setup should be promoted to its own registered subsystem with a `WizardSpec`-class facet (a new primitive family, itself out of this lane's scope — likely Lane G / owner-gated design work) rather than remaining an unregistered side door reached only through this hub.

**Dependency-layer guess:** early governance — this hub sits directly on top of moderation/channel/role/cleanup (all mid-tier governed subsystems) and Setup, so it can only be "100% done" once those are; place it in the same build wave as those subsystems, right after L0 foundation and before non-governance-adjacent feature subsystems (economy/games/etc.).

**Production-grade done-definition (acceptance test / golden):** (a) every nav button resolves via the declared `PanelRef` convention with zero dynamic `get_cog`/`getattr` and zero bespoke fresh-`send_message` paths in generated code; (b) the fail-safe badge contract is golden-tested — kill one detector (e.g. force `evaluate_moderation_readiness` to raise) and assert the hub still renders the other 4 badges plus a ❓ on the killed one, never blanking the whole hub; (c) Access Map / Help Preview projections never disagree with the live Help renderer for the same simulated tier (a parity test against `services.help_projection`'s own reason codes — the docstring already names the pre-#657 regression this class of test would have caught); (d) the Setup button only renders/executes behind a real registered capability check, not a bare "administrator" assumption.

**Outperform-target status:** comparable capability = the "dashboard" aggregator most competitor bots (Dyno, MEE6, Carl-bot) push to a **web** control panel rather than rendering in-Discord. Our in-Discord hub with live, fail-safe, per-module health badges plus a governance-transparency Access Map/Help Preview (showing exactly what a simulated tier can see/do) is already ahead of anything found in-channel for comparable bots — the remaining work is purely internal (generate it from the grammar so it scales past 40+ subsystems without hand-authored routing glue), not feature-catch-up. `pending Lane F` to confirm no competitor's web dashboard has an equivalent in-Discord-native, no-second-tab health/transparency surface.

**Owner-gated/blocked/external-dependency status:** none blocking for server_management's own hub-navigation cleanup (G-A3 is a documentation-only grammar amendment proposal). Promoting `setup` to a registered subsystem and any `WizardSpec` primitive family are **owner-gated design decisions** (Phase-3 hard stop applies) and are out of this Lane A subsystem's scope to execute — flagged for the capstone / a router discussion, not actioned here.

---

### moderation
_cogs: disbot/cogs/moderation_cog.py, disbot/cogs/moderation/__init__.py, disbot/cogs/moderation/schemas.py_

**Cross-check resolved (scaffold's flagged item):** `!modlogs` gates on capability `moderation.log.view` (`_require_mod("moderation.log.view", "manage_roles")`, moderation_cog.py:291) and `!clearwarnings` gates on `moderation.warn.apply` (`_require_mod("moderation.warn.apply", "manage_roles")`, moderation_cog.py:276) — both capability strings exist verbatim in `SUBSYSTEMS["moderation"]["capabilities"]` (subsystem_registry.py:139-146: `moderation.warn.apply`, `moderation.timeout.apply`, `moderation.kick.apply`, `moderation.ban.apply`, `moderation.ban.remove`, `moderation.log.view`, `moderation.settings.configure`). All 7 registered capabilities are exercised by exactly one command each (clearwarnings deliberately reuses `warn.apply` rather than getting its own capability — there is no `moderation.warn.clear` in the registry, and none is needed). **No missing or mismatched capability** — the scaffold's "unverified" flag is resolved clean. The one real nuance found in verifying this: `_ModLogsModal`/`_ClearWarningsModal` (reached via `ModPanelView`) do **not** re-check their commands' specific capabilities — the panel's single `interaction_check` (main_panel.py:45-61) gates ALL seven buttons on `moderate_members OR moderation.warn.apply` only, so the panel path is coarser than the prefix-command path for `modlogs`/`clearwarn` specifically (see G-A12 below and the Reconsider section).

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !modmenu | command | cogs/moderation_cog.py:79 | 3 | 1 | route=PanelRef (kernel open-panel workflow, tier-1 shape like logging's `!logging`); auth is `_require_mod` dual-floor (moderate_members raw perm OR moderation.warn.apply capability, cogs/moderation_cog.py:29-52,78) — no single-field declaration exists today (G-A12); with G-A12 the whole command becomes pure declaration |
| /moderation | command | cogs/moderation_cog.py:98 | 3 | 1* | same PanelRef shape, but auth uses a **third**, capability-blind mechanism (`app_commands.default_permissions`+`app_perms_or_owner`, :96-97) that ignores a guild's configured moderator_role entirely — G-A12 fixes the field gap; *the with-amendments call assumes the rebuild deliberately unifies behavior across the three surfaces (a product decision, not just a grammar fix — see Reconsider) |
| !warn | command | cogs/moderation_cog.py:128 | 3 | 3 | HandlerRef carrying real logic: hierarchy check (`_can_act_on`), `ReasonRequiredError` typed exception, warn-count escalation ladder rendering (`render_warn_outcome_lines`) — deliberate escape hatch, same class as karma's `!thanks` |
| !timeout | command | cogs/moderation_cog.py:155 | 3 | 3 | hierarchy check + timeout-ceiling clamp (`effective_max_timeout_minutes`) + Discord Forbidden/HTTPException handling — deliberate escape hatch |
| !kick | command | cogs/moderation_cog.py:181 | 3 | 3 | hierarchy check + `ReasonRequiredError` + optional post-action cleanup sweep request (cross-subsystem orchestration into `history_cleanup`) — deliberate escape hatch |
| !ban | command | cogs/moderation_cog.py:213 | 3 | 3 | same shape as kick + `ban_delete_message_days` purge-window handling — deliberate escape hatch |
| !unban | command | cogs/moderation_cog.py:246 | 3 | 3 | `fetch_user` + typed NotFound/Forbidden/HTTPException handling — thin but real domain handler, deliberate escape hatch |
| !clearwarnings | command | cogs/moderation_cog.py:277 | 3 | 3 | thinnest of the six action commands (no hierarchy check, no typed branching) but still an audited-seam mutation (HandlerRef by definition) — deliberate escape hatch, consistent with karma's `!thanks` precedent |
| !modlogs | command | cogs/moderation_cog.py:292 | 3 | 2 | as-written: hand-rolled embed loop over `db.get_mod_logs`, no panel declared; with amendments: PanelRef + a ListBlock/ProviderRef read-model (matches logging's `!logging routes` tier-2 call) — read-only, no mutation |
| ModPanelView (container + interaction_check) | panel | views/moderation/main_panel.py:36 | 3 | 2 | as-written: bespoke `PersistentView` subclass with a hand-written OR-gate `interaction_check` (:45-61); with amendments: PanelSpec container + G-A12 makes the dual-floor capability pure data — panel body still carries a real "bot readiness" computation (`_build_mod_panel_embed`→`utils.moderation_feasibility.evaluate_moderation_readiness`, moderation_helpers.py:36-76), so it lands at tier-2 (thin ProviderRef), not tier-1 — same class as karma's card panel |
| warn_btn (mod:warn) | panel-action | views/moderation/main_panel.py:63-70 | 3 | 2 | as-written: bespoke `@discord.ui.button` opening a hand-built `discord.ui.Modal` instance, no declaration at all; with G-A1: `defer_mode="modal"` + declared `ModalFieldSpec` makes the OPEN step pure data (the real mutation logic lives in the modal's own on_submit unit, scored separately below) |
| timeout_btn (mod:timeout) | panel-action | views/moderation/main_panel.py:72-79 | 3 | 2 | same as warn_btn |
| kick_btn (mod:kick) | panel-action | views/moderation/main_panel.py:81-88 | 3 | 2 | same as warn_btn |
| ban_btn (mod:ban) | panel-action | views/moderation/main_panel.py:90-97 | 3 | 2 | same as warn_btn |
| unban_btn (mod:unban) | panel-action | views/moderation/main_panel.py:99-106 | 3 | 2 | same as warn_btn |
| modlogs_btn (mod:logs) | panel-action | views/moderation/main_panel.py:108-115 | 3 | 2 | same as warn_btn; note this button's authority is the panel-wide check, NOT `moderation.log.view` specifically (see cross-check note above) [corrected file:line — verified end of the button block is line 115 (`await interaction.response.send_modal(_ModLogsModal())`); line 116 is a blank separator before the next decorator, not part of this unit] |
| clearwarn_btn (mod:clearwarn) | panel-action | views/moderation/main_panel.py:117-128 | 3 | 2 | same as warn_btn; same panel-wide-vs-specific-capability nuance as modlogs_btn [corrected file:line — the file is 128 lines total (`wc -l`); line 128 is the last real line, so "129" doesn't exist] |
| _WarnModal | modal | views/moderation/modals.py:48 | 3 | 3 | G-A1 declares the 2 TextInput fields as data, but `on_submit` still runs `_parse_member` + `_can_act_on_interaction` + the warn/escalation seam — real logic survives as a registered HandlerRef, deliberate escape hatch |
| _TimeoutModal | modal | views/moderation/modals.py:95 | 3 | 3 | same shape (3 fields: member/duration/reason) — deliberate escape hatch |
| _KickModal | modal | views/moderation/modals.py:160 | 3 | 3 | deliberate escape hatch |
| _BanModal | modal | views/moderation/modals.py:215 | 3 | 3 | deliberate escape hatch |
| _UnbanModal | modal | views/moderation/modals.py:271 | 3 | 3 | `fetch_user` + typed error handling in `on_submit` — deliberate escape hatch |
| _ModLogsModal | modal | views/moderation/modals.py:313 | 3 | 2 | as-written: bespoke 1-field modal + hand-rolled embed loop; with G-A1 + a ListBlock/ProviderRef read-model: pure read, no mutation — matches `!modlogs`'s with-amendments call |
| _ClearWarningsModal | modal | views/moderation/modals.py:349 | 3 | 3 | mutating HandlerRef (audited seam) — deliberate escape hatch, kept consistent with `!clearwarnings` |
| warn_threshold (setting) | setting | cogs/moderation/schemas.py:193 | 2 | 1 | `_validate_positive_int` registered validator (schemas.py:68-70) is a simple lower-bound check — classic G-5 (declarative `bounds`) case |
| warn_timeout_minutes (setting) | setting | cogs/moderation/schemas.py:205 | 2 | 1 | same G-5 class |
| warn_escalation_action (setting) | setting | cogs/moderation/schemas.py:217 | **2** | **1†** | **CORRECTED** — ships `allowed_values=WARN_ESCALATION_ACTIONS` (schemas.py:225), but verified this does **not** make the registered validator redundant today: `allowed_values` is documented (`core/runtime/subsystem_schema.py:140-147`) as a **UI-widget-selection hint only** ("renders a `discord.ui.Select` widget... instead of a free-form text input") — it is never independently checked by the write or read pipelines. Confirmed by reading the actual enforcement code: `services/settings_mutation.py:315-317` and `services/settings_resolution.py:272-276` both call **only** `spec.validator`, never `spec.allowed_values`; and `control_api.py:331-364`'s `POST /control/settings` handler feeds an unchecked JSON `value` straight into that same pipeline with no widget in between. So `_validate_escalation_action` (schemas.py:108-113) is today the *only* thing rejecting an out-of-vocabulary value on that path — real, load-bearing (if thin) domain logic, not dead code. Same class as the G-5 bounds settings above: tier-2 as-written. †With amendments this can reach tier-1 only if the rebuild's kernel is made to enforce `allowed_values` at the mutation seam itself (mirroring the enforcement G-5 already promises for `bounds`) — that enforcement doesn't exist in the shipped pipeline yet, so treat "1" as conditional on closing that (currently unnamed) kernel gap, not as already-free |
| dm_on_action (setting) | setting | cogs/moderation/schemas.py:234 | 1 | 1 | `_validate_bool` is a trivial type check the kernel already performs for any bool-typed spec — no real domain logic. (Verified this is a *materially different* case from the enum settings above: `services/settings_mutation.py`'s `_coerce_for_write` for `value_type=bool` already guarantees `isinstance(value, bool)` before the validator ever runs, so `_validate_bool` genuinely checks nothing the coercion step doesn't already guarantee — unlike the enum validators, which check a domain-specific vocabulary coercion never enforces.) |
| dm_actions (setting) | setting | cogs/moderation/schemas.py:248 | 2 | 1 | `_validate_dm_actions` (schemas.py:134-151) parses a CSV subset of a fixed vocabulary — this is exactly **G-2**'s list-valued-setting shape (stored as a scalar CSV string rather than `value_type="list[str]"` with `allowed_values`); G-2 collapses it to pure declaration |
| dm_template (setting) | setting | cogs/moderation/schemas.py:263 | 2 | 1 | `_validate_dm_template` (schemas.py:99-105) is a simple `max_len` check — G-5's string-`bounds` case (design-spec.md:700 explicitly names `max_len` for string specs) |
| require_reason (setting) | setting | cogs/moderation/schemas.py:276 | 1 | 1 | `_validate_bool` — trivial (same coercion-already-guarantees-it reasoning as dm_on_action) |
| ban_delete_message_days (setting) | setting | cogs/moderation/schemas.py:289 | 2 | 1 | `_validate_ban_delete_days` (schemas.py:79-86) is a numeric range check (0-7) + `presets` — G-5 |
| max_timeout_minutes (setting) | setting | cogs/moderation/schemas.py:303 | 2 | 1 | `_validate_timeout_ceiling` (schemas.py:89-96) numeric range check + `presets` — G-5 |
| post_action_cleanup (setting) | setting | cogs/moderation/schemas.py:320 | **2** | **1†** | **CORRECTED** — ships `allowed_values=POST_ACTION_CLEANUP_ACTIONS`; same verified not-actually-redundant case as `warn_escalation_action` above (`_validate_post_action_cleanup`, schemas.py:116-121, is the only enforcement on the control-API / stale-stored-value paths). Note the consuming function `moderation_config.cleanup_applies_to` (moderation_config.py:233-247) already fails safe on an unrecognized value (treats it as "no sweep"), so a dropped validator would not misbehave, only silently under-enforce input hygiene — still real code today, tier-2 |
| public_log_actions (setting) | setting | cogs/moderation/schemas.py:352 | **2** | **1†** | **CORRECTED** — ships `allowed_values=PUBLIC_LOG_ACTIONS`; same case as the two rows above (`_validate_public_log_actions`, schemas.py:154-159); `moderation_config.public_log_includes` also fails safe on an unrecognized value, but the validator is still the only thing catching it at write/read time — tier-2, not tier-1, as-written |
| public_log_channel (setting) | setting | cogs/moderation/schemas.py:367 | 2 | 1 | `_validate_public_log_channel` (schemas.py:162-170) hand-validates "empty or numeric channel id" — a channel pointer stored as a bare string instead of a `BindingSpec(kind="channel")`; **not a new amendment** — `BindingSpec` already exists verbatim in §2.5, this is a re-modeling debt (design-spec.md's decision-3 "pointer keys become declared read-aliases behind bindings") |
| moderator_role (setting) | setting | cogs/moderation/schemas.py:390 | 2 | 1 | `_validate_role_id_or_empty` (schemas.py:173-181) — same class as public_log_channel but for a role pointer; re-model as `BindingSpec(kind="role")`, no new amendment needed. Underlying key constant is defined in `utils/settings_keys/governance.py:13` (shared governance key, not moderation-owned) |
| trusted_role (setting) | setting | cogs/moderation/schemas.py:405 | 2 | 1 | same as moderator_role; key constant at `utils/settings_keys/governance.py:7` |
| mod_log channel (ResourceRequirement) | resource | cogs/moderation/schemas.py:417-430 | 1 | 1 | pure `ResourceRequirement` declaration (§2.5 shipped verbatim), but **no `binding_name` set** — unlike `logging`'s identical `intent="mod_log"` requirement (cogs/logging/schemas.py:422, which does bind via `binding_name="mod_channel"` at :428), moderation's own copy is informational/orphaned: it never resolves to a functional channel at the moderation-subsystem level (the real destination is Lane D logging's `mod_channel` binding) |
| SUBSYSTEMS["moderation"] registry entry | setting-registry | utils/subsystem_registry.py:122-148 | 1 | 1 | pure declarative dict: display/tags/entry_points/`related_subsystems=["cleanup"]`/7 capabilities — matches the pattern used by every other subsystem's registry card |
| moderation.action_taken (EVT_MOD_ACTION) | event | services/moderation_service.py:88 (declared), :226 (emitted) | 1 | 1 | pure EventSpec declaration; emit lives inside the audited `_record_action` seam — matches karma.granted's 1/1 call |
| audit.action_recorded (emit_audit_action) | event | services/moderation_service.py:213 | 1 | 1 | the generic cross-subsystem audit companion (`services.audit_events.emit_audit_action`), identical shape for every mutation seam in the codebase — kernel-level, not moderation-specific code |
| mod_logs table | store | utils/db/migrations.py:257 (+ ALTER: migrations/006_audit_log_and_timestamps.sql:29-41); utils/db/moderation.py:44 (write), :66 (read) | 1 | 1 | StoreSpec declaration, ledger checkpoint_class — matches karma_audit_log's 1/1 |
| warnings table | store | utils/db/migrations.py:251; utils/db/moderation.py:12 (read), :20 (increment), :32 (clear) | 1 | 1 | StoreSpec declaration, aggregate checkpoint_class — matches karma table's 1/1 |
| moderation_service.warn (mutation seam) | mutation-path | services/moderation_service.py:361 | 3 | 3 | escalation-ladder evaluation, DM-on-action, typed `ReasonRequiredError` — real business logic, deliberate escape hatch; note the escalation-ladder SHAPE (counter+threshold+terminal-action lookup, moderation_config.py:212-230) recurs elsewhere (role's tenure/xp thresholds) but was judged too domain-specific in its *application* (DM copy, Discord-call side effects) to propose as a new declarative primitive here — flagged for Lane-wide reconsideration, not proposed as G-A |
| moderation_service.timeout | mutation-path | services/moderation_service.py:446 | 3 | 3 | ceiling clamp + notify — deliberate escape hatch |
| moderation_service.kick | mutation-path | services/moderation_service.py:484 | 3 | 3 | notify-before-removal ordering + cleanup-sweep request — deliberate escape hatch; also called cross-subsystem from `services/security_service.py:379` (account-age auto-kick on join) — another consumer of this seam beyond moderation's own surfaces |
| moderation_service.ban | mutation-path | services/moderation_service.py:530 | 3 | 3 | ban-purge-window + cleanup-sweep request — deliberate escape hatch |
| moderation_service.unban | mutation-path | services/moderation_service.py:587 | 3 | 3 | thin but real — deliberate escape hatch |
| moderation_service.clear_warnings | mutation-path | services/moderation_service.py:605 | 3 | 3 | thinnest seam — deliberate escape hatch |
| moderation_service.auto_delete | mutation-path | services/moderation_service.py:629 | 3 | 3 | system-initiated variant (actor_id=None, actor_type="system"), swallows Discord exceptions itself (unlike the other 6); consumed by automod, cleanup, image_moderation (same lane) **and chain, counting (Lane C — cross-lane, see bullet below)** — deliberate escape hatch, genuinely shared infrastructure |
| build_help_menu_view (help-menu direct-nav hook) | help | cogs/moderation_cog.py:85-90 | 1 | 1 | returns `(_build_mod_panel_embed(...), ModPanelView())` — the same generic direct-navigation convention used by admin/server_management/security/welcome/ticket/image_moderation/automod/cleanup; zero moderation-specific code beyond the panel builder itself |
| server_logging._on_moderation_action (bus.on EVT_MOD_ACTION) | listener | services/server_logging.py:1854 | external (Lane D) | external (Lane D) | verified `bus.on(EVT_MOD_ACTION, _on_moderation_action)` — external subscriber, owned by Lane D's `logging` subsystem; **excluded from this ledger's unit totals** (it is logging's surface, not moderation's) |
| server_logging._on_moderation_action_public (bus.on EVT_MOD_ACTION) | listener | services/server_logging.py:1855 | external (Lane D) | external (Lane D) | same as above — the public-mirror subscriber; excluded from totals |

**Unit kinds present:** command (9), panel/panel-action (8), **modal (7)**, setting (15), event (2), store (2), mutation-path (7), resource (1), setting-registry (1), help (1) = **53 moderation-owned units** (the 2 external Lane-D listener rows above are shown for the cross-check but excluded from this count and from the fit numbers below, since they are logging's surface). **[Corrected: the first-pass draft's tally omitted the "modal" kind entirely from this sentence — its own listed sub-counts summed to 46, not the stated 53, even though all 7 modal rows are present in the ledger table above and in the manifest sketch below. 9+8+7+15+2+2+7+1+1+1 = 53, confirmed.]**

**Unit kinds explicitly absent (verified by grep across `cogs/moderation_cog.py`, `cogs/moderation/*.py`, `services/moderation_*.py`, `views/moderation/*.py`):**
- **listener / gateway** — no `@commands.Cog.listener()`, no `@bot.event`, and **no `bus.on` subscription owned by moderation itself** (grep for `bus.on|@commands.Cog.listener|@bot.event` returns zero hits in moderation's own files — the only two `bus.on(EVT_MOD_ACTION, ...)` calls in the codebase live externally in `server_logging.py`, already covered above).
- **message-pipeline stage** — no `message_pipeline.register` call in `moderation_cog.py` (unlike automod/image_moderation/cleanup, which do register stages); moderation is invoked BY the pipeline indirectly only through `auto_delete` being called from those other subsystems' stages, not by registering its own.
- **diagnostics** — no `DiagnosticProviderSpec`-shaped registration found (verified: zero case-insensitive "diagnostic" hits anywhere in moderation's own files).
- **game** — not applicable; moderation is not a game subsystem.
- **`wait_for` wizard / scheduled loop (`@tasks.loop`) / voice** — zero grep hits across all moderation files; none present.
- **bindings** — zero shipped `BindingSpec` instances (the two candidate channel/role pointers — `public_log_channel`, `moderator_role`, `trusted_role` — ship as validated bare-string `SettingSpec`s instead; see the settings rows above).

**Structural-pattern flags:** modal-based single-step action forms (7 `discord.ui.Modal` classes, `views/moderation/modals.py`) — NOT a multi-step `wait_for` wizard (each is a one-shot form-submit-and-done); persistent panel view (`ModPanelView(PersistentView)`, correctly extends the required base per `docs/architecture.md`); three independent hand-written moderator-only authorization checks across the prefix/slash/panel surfaces, but **not all the same shape** — prefix (`_require_mod`) and panel (`interaction_check`) are both genuine dual-floor (raw Discord permission OR the `moderation.warn.apply` governance capability), while slash (`app_perms_or_owner`) is a *different*, single-floor, capability-blind check (raw permission OR platform owner — it never consults the governance capability at all). See G-A12 and the Structural-gap flags section below for the precise per-surface breakdown. No gateway listener, no message-pipeline stage registration, no scheduled loop, no voice, no stateful game loop owned by moderation itself.

#### Manifest sketch

```python
"""Moderation — Lane A audit manifest sketch (spike style, illustrative only).

Verified against: cogs/moderation_cog.py, cogs/moderation/schemas.py,
services/moderation_service.py, services/moderation_config.py,
services/moderation_helpers.py, views/moderation/main_panel.py,
views/moderation/modals.py, utils/db/moderation.py,
utils/settings_keys/moderation.py, utils/subsystem_registry.py.

Uses only fields that exist in tools/grammar_spike/spec.py today; where a
proposed amendment (G-A1 ModalFieldSpec, G-A12 dual-floor authority) would
add a field, that gap is called out in a comment rather than fabricated on
the frozen dataclass.
"""

from __future__ import annotations

from tools.grammar_spike.spec import (
    Activation,
    BlockSpec,
    CommandKind,
    CommandSpec,
    EventSpec,
    FieldSpec,
    HandlerRef,
    HelpEntrySpec,
    PanelActionSpec,
    PanelRef,
    PanelSpec,
    ProviderRef,
    ResourceRequirement,
    SettingSpec,
    StoreSpec,
    SubsystemManifest,
    ViewRef,
)

_CAP = "moderation.settings.configure"

# G-A12 (proposed, NOT a real field yet): every capability_required below
# also needs an OR'd raw-permission floor (manage_roles / moderate_members /
# kick_members / ban_members, varying per action) plus the slash surface's
# separate app_perms_or_owner path — today none of that is declarable, so
# every command/action below is tier-3 on auth alone until G-A12 lands.

MODERATION_MANIFEST = SubsystemManifest(
    key="moderation",
    display_name="Moderation",
    description="Warnings, timeouts, bans, mod logs",
    emoji="🔨",
    category="moderation",
    visibility_tier="moderator",
    capabilities=(
        "moderation.warn.apply",
        "moderation.timeout.apply",
        "moderation.kick.apply",
        "moderation.ban.apply",
        "moderation.ban.remove",
        "moderation.log.view",
        _CAP,
    ),
    dependencies=("cleanup",),  # post-action sweep is *requested from* cleanup;
    # NOTE: the real subsystem_registry.py entry actually ships this as
    # related_subsystems=["cleanup"] with dependencies=[] (subsystem_registry.py:
    # 133-134) — i.e. today it is explicitly a SOFT relationship (governance's
    # hard-dependency blocking, governance/dependency.py, does NOT apply here;
    # the post-action sweep call is a best-effort, exception-swallowing import,
    # not something that requires cleanup to be enabled). Modeling it as a hard
    # `dependencies` entry in this sketch is illustrative of the new grammar's
    # field, not a claim that today's registry already treats it as hard.
    parent_hub="server_management",
    commands=(
        # moderation_cog.py:79 — !modmenu opens the panel (tier-1 shape)
        CommandSpec(
            name="modmenu",
            kind=CommandKind.PREFIX,
            summary="Show the interactive moderation action panel.",
            route=PanelRef("moderation.panel"),
            capability_required="moderation.warn.apply",  # G-A12: drops the
            # `manage_roles`-or-`moderate_members` raw-permission OR-branch
            # (moderation_cog.py:42-50) — behavior-preserving only once a
            # legacy_permission_floor field exists.
        ),
        # moderation_cog.py:98 — /moderation, TODAY capability-blind (:96-97)
        CommandSpec(
            name="moderation",
            kind=CommandKind.SLASH,
            summary="Open the Moderation hub (moderator only).",
            route=PanelRef("moderation.panel"),
            capability_required="moderation.warn.apply",  # unifies with the
            # prefix surface — a deliberate behavior change vs. today's
            # capability-blind app_perms_or_owner(moderate_members=True).
        ),
        CommandSpec(
            name="warn",
            kind=CommandKind.PREFIX,
            summary="Warn a member; escalates at the configured threshold.",
            route=HandlerRef(
                "moderation.warn",
                justification="hierarchy check + ReasonRequiredError + "
                "warn-threshold escalation ladder rendering",
            ),
            capability_required="moderation.warn.apply",
        ),
        CommandSpec(
            name="timeout",
            kind=CommandKind.PREFIX,
            summary="Timeout a member for N minutes.",
            route=HandlerRef(
                "moderation.timeout",
                justification="hierarchy check + timeout-ceiling clamp",
            ),
            capability_required="moderation.timeout.apply",
        ),
        CommandSpec(
            name="kick",
            kind=CommandKind.PREFIX,
            summary="Kick a member.",
            route=HandlerRef(
                "moderation.kick",
                justification="hierarchy check + optional post-action "
                "cleanup sweep request (cross-subsystem: cleanup)",
            ),
            capability_required="moderation.kick.apply",
        ),
        CommandSpec(
            name="ban",
            kind=CommandKind.PREFIX,
            summary="Ban a member.",
            route=HandlerRef(
                "moderation.ban",
                justification="hierarchy check + ban-purge-window + "
                "post-action cleanup sweep request",
            ),
            capability_required="moderation.ban.apply",
        ),
        CommandSpec(
            name="unban",
            kind=CommandKind.PREFIX,
            summary="Unban a user by ID.",
            route=HandlerRef(
                "moderation.unban",
                justification="fetch_user + typed NotFound/Forbidden",
            ),
            capability_required="moderation.ban.remove",
        ),
        CommandSpec(
            name="clearwarnings",
            kind=CommandKind.PREFIX,
            summary="Clear all warnings for a member.",
            route=HandlerRef(
                "moderation.clear_warnings",
                justification="audited-seam mutation, no branching",
            ),
            capability_required="moderation.warn.apply",  # shares warn's cap
        ),
        CommandSpec(
            name="modlogs",
            kind=CommandKind.PREFIX,
            summary="Show moderation log history for a member.",
            route=PanelRef("moderation.logs"),  # tier-2 read-model, was
            # a hand-rolled embed loop (moderation_cog.py:292-308) as-shipped
            capability_required="moderation.log.view",
        ),
    ),
    panels=(
        PanelSpec(
            panel_id="moderation.panel",
            subsystem="moderation",
            title="🔨 Moderation Panel",
            audience="persistent",
            timeout_s=None,
            body=(
                BlockSpec(kind="fields", text="7 static action descriptions"),
                # real domain logic behind this provider — tier-2, not -1:
                BlockSpec(
                    kind="fields",
                    provider=ProviderRef("moderation.bot_readiness"),
                ),
            ),
            actions=(
                PanelActionSpec(
                    action_id="warn",
                    custom_id_override="mod:warn",
                    label="⚠️ Warn",
                    defer_mode="modal",  # G-A1: the modal's OWN field
                    # schema (member, reason) still has no primitive —
                    # see ModalFieldSpec proposal below.
                    handler=HandlerRef(
                        "moderation.warn",
                        justification="same seam as !warn",
                    ),
                    capability_required="moderation.warn.apply",
                ),
                PanelActionSpec(
                    action_id="timeout",
                    custom_id_override="mod:timeout",
                    label="⏳ Timeout",
                    defer_mode="modal",
                    handler=HandlerRef("moderation.timeout", justification="same seam as !timeout"),
                    capability_required="moderation.timeout.apply",
                ),
                PanelActionSpec(
                    action_id="kick",
                    custom_id_override="mod:kick",
                    label="👢 Kick",
                    style="danger",
                    defer_mode="modal",
                    handler=HandlerRef("moderation.kick", justification="same seam as !kick"),
                    capability_required="moderation.kick.apply",
                ),
                PanelActionSpec(
                    action_id="ban",
                    custom_id_override="mod:ban",
                    label="🚫 Ban",
                    style="danger",
                    destructive=True,
                    defer_mode="modal",
                    handler=HandlerRef("moderation.ban", justification="same seam as !ban"),
                    capability_required="moderation.ban.apply",
                ),
                PanelActionSpec(
                    action_id="unban",
                    custom_id_override="mod:unban",
                    label="✅ Unban",
                    defer_mode="modal",
                    handler=HandlerRef("moderation.unban", justification="same seam as !unban"),
                    capability_required="moderation.ban.remove",
                ),
                PanelActionSpec(
                    action_id="logs",
                    custom_id_override="mod:logs",
                    label="📋 Mod Logs",
                    defer_mode="modal",
                    handler=PanelRef("moderation.logs"),
                    # NOTE (cross-check resolved): as-shipped this button is
                    # gated by the PANEL-WIDE interaction_check only
                    # (moderate_members OR moderation.warn.apply) — NOT by
                    # moderation.log.view, unlike the standalone !modlogs
                    # command. Declaring capability_required="moderation.
                    # log.view" here (as written) is the FIX the manifest
                    # form enables that today's monolithic interaction_check
                    # cannot express per-action.
                    capability_required="moderation.log.view",
                ),
                PanelActionSpec(
                    action_id="clearwarn",
                    custom_id_override="mod:clearwarn",
                    label="⬛ Clear Warnings",
                    defer_mode="modal",
                    handler=HandlerRef(
                        "moderation.clear_warnings",
                        justification="same seam as !clearwarnings",
                    ),
                    capability_required="moderation.warn.apply",
                ),
            ),
            # Without G-A1 (modal fields) + G-A12 (dual-floor auth), this
            # panel would not validate as "generated" at all — it would
            # need: legacy_view=ViewRef("views.moderation.ModPanelView",
            # justification="7 hand-written Modal classes; hand-written
            # dual-floor interaction_check — pre-amendment escape hatch").
        ),
        PanelSpec(
            panel_id="moderation.logs",
            subsystem="moderation",
            title="📋 Mod Logs",
            body=(BlockSpec(kind="list", provider=ProviderRef("moderation.mod_logs")),),
        ),
    ),
    settings=(
        SettingSpec(
            name="warn_threshold",
            value_type="int",
            default=3,
            settings_key="warn_threshold",
            capability_required=_CAP,
            # G-5: bounds=(1, None) replaces _validate_positive_int
        ),
        SettingSpec(
            name="warn_timeout_minutes",
            value_type="int",
            default=10,
            settings_key="warn_timeout_minutes",
            capability_required=_CAP,
        ),
        SettingSpec(
            name="warn_escalation_action",
            value_type="str",
            default="timeout",
            settings_key="moderation_warn_escalation_action",
            capability_required=_CAP,
            allowed_values=("timeout", "kick", "ban", "none"),  # ALREADY
            # shipped as data (schemas.py:225) — but verified NOT yet
            # sufficient on its own: today `allowed_values` only routes the
            # S6 edit-widget choice (Select vs free-text), it is not checked
            # by the write/read pipeline or by control_api.py's settings
            # endpoint. The registered validator below is what actually
            # enforces the vocabulary today; dropping it requires the
            # kernel to enforce allowed_values directly (not yet true).
            validator=HandlerRef(
                "moderation.validate_warn_escalation_action",
                justification="enforces allowed_values membership at the "
                "mutation seam until the kernel does it generically",
            ),
        ),
        SettingSpec(
            name="dm_on_action",
            value_type="bool",
            default=False,
            settings_key="moderation_dm_on_action",
            capability_required=_CAP,
            activation=Activation.OFF_UNTIL_OPT_IN,
            external_side_effects=True,  # sends a DM to the target member
        ),
        SettingSpec(
            name="dm_actions",
            value_type="list[str]",  # G-2: was a CSV-in-a-str scalar
            default=("warn", "timeout", "kick", "ban"),
            settings_key="moderation_dm_actions",
            capability_required=_CAP,
            allowed_values=("warn", "timeout", "kick", "ban"),
        ),
        SettingSpec(
            name="dm_template",
            value_type="str",
            default="",
            settings_key="moderation_dm_template",
            capability_required=_CAP,
            # G-5: bounds=(0, 1500) replaces _validate_dm_template's max_len
        ),
        SettingSpec(
            name="require_reason",
            value_type="bool",
            default=False,
            settings_key="moderation_require_reason",
            capability_required=_CAP,
            activation=Activation.ON_BY_DEFAULT,
        ),
        SettingSpec(
            name="ban_delete_message_days",
            value_type="int",
            default=0,
            settings_key="moderation_ban_delete_message_days",
            capability_required=_CAP,
            presets=(0, 1, 7),  # G-5: bounds=(0, 7)
        ),
        SettingSpec(
            name="max_timeout_minutes",
            value_type="int",
            default=40320,
            settings_key="moderation_max_timeout_minutes",
            capability_required=_CAP,
            presets=(60, 1440, 10080, 40320),  # G-5: bounds=(1, 40320)
        ),
        SettingSpec(
            name="post_action_cleanup",
            value_type="str",
            default="none",
            settings_key="moderation_post_action_cleanup",
            capability_required=_CAP,
            allowed_values=("none", "kick", "ban", "both"),
            # same not-yet-redundant validator caveat as warn_escalation_action
            validator=HandlerRef(
                "moderation.validate_post_action_cleanup",
                justification="enforces allowed_values membership at the "
                "mutation seam until the kernel does it generically",
            ),
        ),
        SettingSpec(
            name="post_action_cleanup_limit",
            value_type="int",
            default=100,
            settings_key="moderation_post_action_cleanup_limit",
            capability_required=_CAP,
            presets=(50, 100, 200, 500),  # G-5: bounds=(1, 500)
        ),
        SettingSpec(
            name="public_log_actions",
            value_type="str",
            default="none",
            settings_key="moderation_public_log_actions",
            capability_required=_CAP,
            allowed_values=("none", "bans", "removals", "all"),
            # same not-yet-redundant validator caveat as warn_escalation_action
            validator=HandlerRef(
                "moderation.validate_public_log_actions",
                justification="enforces allowed_values membership at the "
                "mutation seam until the kernel does it generically",
            ),
        ),
        # public_log_channel / moderator_role / trusted_role: modeled as
        # BindingSpec below (decision-3 re-model), not SettingSpec, per the
        # optimize recommendation — they ship today as validated bare
        # strings (schemas.py:367,390,405).
    ),
    bindings=(
        # Re-model, not a new amendment — BindingSpec is an existing §2.5
        # shipped primitive; today these three are plain str SettingSpecs.
        # (illustrative only — BindingSpec's real field set may differ)
    ),
    resources=(
        ResourceRequirement(
            kind="channel",
            intent="mod_log",
            provisioning="recommended",
            description="Recommended channel for moderation actions — "
            "orphaned today: no binding_name, so it never resolves to an "
            "actual destination at the moderation-subsystem level (the "
            "functional binding lives in Lane D logging's mod_channel).",
        ),
    ),
    events=(
        EventSpec(
            name="moderation.action_taken",
            payload_schema=(
                FieldSpec("mutation_id", "str"),
                FieldSpec("guild_id", "int"),
                FieldSpec("target_id", "int"),
                FieldSpec("actor_id", "int"),
                FieldSpec("action", "str"),
                FieldSpec("reason", "str"),
            ),
            owner_subsystem="moderation",
            expected_subscribers=(
                HandlerRef("logging.on_moderation_action"),
                HandlerRef("logging.on_moderation_action_public"),
            ),
            audited=True,
        ),
    ),
    gateway_listeners=(),  # explicit absence — verified by grep
    stores=(
        StoreSpec(
            table="mod_logs",
            sole_writer="moderation.service",
            checkpoint_class="ledger",
            reader_domains=("moderation.modlogs_view",),
        ),
        StoreSpec(
            table="warnings",
            sole_writer="moderation.service",
            checkpoint_class="aggregate",
        ),
    ),
    game=None,
    help=HelpEntrySpec(
        summary="Warnings, timeouts, kicks, and bans — with an "
        "auto-escalation ladder and optional public log.",
        examples=("!modmenu", "!warn @user spamming", "!ban @user rule 3"),
    ),
)
```

#### Tier-3 dispositions

- **!warn / !timeout / !kick / !ban / !unban / !clearwarnings (commands) + `moderation_service.warn/timeout/kick/ban/unban/clear_warnings` (mutation seams) + their 6 matching modals** — **deliberate escape hatch.** Each is a thin-but-real audited domain mutation (hierarchy checks, typed `ReasonRequiredError`, the warn-escalation ladder, DM-on-action, post-action cleanup requests, Discord Forbidden/HTTPException handling). No amendment removes this — it is exactly the class of code `HandlerRef` exists for, consistent with karma's `!thanks` precedent.
- **`moderation_service.auto_delete`** — **deliberate escape hatch.** System-initiated variant with its own exception-swallowing contract; shared infrastructure consumed across and beyond this lane (also `moderation_service.kick`, via `security_service.py:379`).
- **!modmenu / /moderation (commands) + ModPanelView (panel container) + all 7 panel buttons + the panel's `interaction_check`** — **grammar gap → G-A12** (new, proposed). The dual-floor "capability OR a specific raw Discord permission" authorization pattern (prefix + panel), plus a *third, different* single-floor capability-blind pattern (slash), has no declarative field in the §2.2 two-lane model. Full justification in `new_amendments_proposed`.
- **All 7 `discord.ui.Modal` classes' field declarations (not their `on_submit` logic)** — **grammar gap → G-A1** (new, proposed). `PanelActionSpec.defer_mode="modal"` declares THAT a modal opens but not WHICH fields it collects; every modal's `TextInput` schema is 100% hand-written today. Full justification in `new_amendments_proposed`.
- **!modlogs / `_ModLogsModal`** — **grammar gap, already covered by existing vocabulary** (no new amendment needed): a `PanelRef` + `BlockSpec(kind="list")`/`ProviderRef` read-model, matching `logging.routes`'s tier-2 call — the gap is that today's code hand-rolls the embed loop instead of using the panel/provider pattern that already exists.
- **`warn_threshold`, `warn_timeout_minutes`, `ban_delete_message_days`, `max_timeout_minutes`, `post_action_cleanup_limit` (settings)** — **reuse G-5** (declarative validator bounds) — each validator is a simple numeric range check.
- **`dm_template` (setting)** — **reuse G-5** (`bounds`/`max_len` for string specs, design-spec.md:700 explicitly names this case).
- **`dm_actions` (setting)** — **reuse G-2** (list-valued settings + add/remove workflow) — a CSV-in-a-string subset-of-fixed-vocabulary is exactly G-2's shape.
- **`warn_escalation_action`, `post_action_cleanup`, `public_log_actions` (settings)** — **CORRECTED disposition.** The first-pass draft called these "not tier-3 at all as-written" (already pure declaration via `allowed_values`, validator "redundant"). Verified against the actual write/read pipelines (`services/settings_mutation.py:315-317`, `services/settings_resolution.py:272-276`) and `control_api.py`'s `/control/settings` endpoint (`:331-364`): `allowed_values` is a UI-widget-selection hint only (`core/runtime/subsystem_schema.py:140-147`), never independently enforced — the registered validator is the *only* enforcement on any non-Discord-widget write path (and on re-reading a stale/legacy stored value). So these are **tier-2 as-written**, same class as the G-5 bounds group, **not** already-tier-1. They reach tier-1 with amendments only if a (currently unnamed, newly-surfaced-by-this-verification) kernel change enforces `allowed_values` as a hard mutation-seam constraint the way G-5 already promises for `bounds` — that is a plausible, low-risk extension of an already-shipped field, not a new grammar family, so it is **not** proposed here as a formal `G-A<n>` (it doesn't add a field, it closes an enforcement gap in an existing one); flagging it for the capstone rather than minting a number unilaterally. This does not change the fit percentages below, since tier-2 already counts as "fit."
- **`public_log_channel`, `moderator_role`, `trusted_role` (settings)** — **not a grammar gap at all** — `BindingSpec` already exists verbatim in §2.5; these are shipped-code re-modeling debt (channel/role pointers stored as validated bare strings instead of bindings), not an amendment.

#### Fit numbers

| Scope | Surface units | Fit — spec as written | Fit — with proposed amendments |
|---|---|---:|---:|
| moderation | 53 | **41.5%** (22/53) | **64.2%** (34/53) |

Note on comparability: unlike the karma/logging spike (which folded each mutation seam into its calling command's single tier call), this ledger — per the audit brief's explicit "mutation paths" unit-kind requirement — counts `moderation_service`'s 7 seam functions as their own rows, separate from the 6 commands/6 modals that route to them. All 7 are tier-3 both ways, so they lower both percentages without changing which grammar gaps exist. Folding them back into their calling commands (karma/logging's convention) gives 46 units; since all 7 folded rows were tier-3 in both columns (contributing 0 to either numerator), the numerators are unchanged at 22 and 34, giving **47.8%** as-written / **73.9%** with amendments — still well below karma (87%) and logging (97%), because moderation's surface is disproportionately built of individually-thin-but-real audited mutations rather than config/CRUD choreography. **[Corrected: the first-pass draft stated "45.7% / 71.7%" here, which does not follow from its own 22/34-of-53 counts — 22/46 = 47.8% and 34/46 = 73.9%, not 45.7%/71.7%. The primary 53-unit Fit Numbers table above (41.5%/64.2%) was independently re-verified against the ledger and is correct; only this secondary comparability note had the arithmetic error.]** **This is a domain characteristic, not a poisoned reading of the grammar** — it matches PARTITION.md's own framing of Lane A as "capability-gated" rather than pure CRUD.

#### Structural-gap flags

- **Permission/capability gates** — **danger zone, confirmed, addressed by G-A12.** Three independent hand-written authority mechanisms gate the same conceptual "moderator-only" surface (prefix `_require_mod` dual-floor, slash `app_perms_or_owner` single-floor capability-blind, panel `interaction_check` dual-floor) — all tier-3 today, all collapse to declaration with the proposed `legacy_permission_floor` field.
- **Setup/provisioning wizards, `wait_for` wizards** — **absent, verified.** No multi-step wizard; each modal is single-shot.
- **External API opt-ins** — **absent.** No external API calls in this subsystem (Discord-native only).
- **Audit/mutation seams** — **present, well-formed, deliberate escape hatch.** Every mutation routes through the single audited `moderation_service` seam (`_record_action`: mod_logs row + `audit.action_recorded` + `EVT_MOD_ACTION`, all sharing one `mutation_id`), pinned by `tests/unit/invariants/test_no_direct_moderation_writes.py` per the module docstring. This is exactly the shape the grammar's `HandlerRef` + kernel audit-emission is built for — no gap.
- **Destructive actions** — **present, correctly modeled today.** `ban`/`kick` map cleanly to `PanelActionSpec.destructive=True ⇒ style="danger"` (already enforced by the compile rule at spec.py:141-145); the manifest sketch above declares `destructive=True` on the ban action.
- **Lifecycle tasks/scheduled loops** — **absent, verified.** No `@tasks.loop` anywhere in moderation's files.
- **Governance/cache behavior** — **present via the shared `governance` package** (`can_execute_ctx`/`can_execute` → `governance.execution.resolve_execution`, capability-override caching) — this is shared cross-subsystem infrastructure outside the 43-subsystem partition, not something moderation itself needs to express; the manifest only needs `capability_required` (+ the proposed G-A12 floor) to hook into it.
- **Modal form-field schema** — **danger zone not previously named in G-1..G-6, addressed by proposed G-A1.** 7 of moderation's units are hand-written modal field schemas; this recurs heavily across Lane A (cleanup, ticket, roles all ship several modals each), so G-A1 is a lane-wide, not moderation-only, finding.
- **Declarative-field enforcement gap (newly surfaced by this verification pass)** — 3 of moderation's `str`-typed enum settings (`warn_escalation_action`, `post_action_cleanup`, `public_log_actions`) ship `allowed_values` but are still enforced today only by a registered validator, because the shipped mutation/resolution pipeline never checks `allowed_values` itself (verified: `services/settings_mutation.py`, `services/settings_resolution.py`, `control_api.py`). This is not moderation-specific — any subsystem with an enum-shaped `str` setting (and there are many across the 43) likely has the same latent gap — so it is flagged here for the capstone as a candidate kernel-enforcement item, not resolved unilaterally in this lane section.

#### Reconsider / optimize

**MAP → RECONSIDER → SIMULATE → OPTIMIZE verdict: IMPROVE.** Moderation is core governance functionality every serious Discord bot needs (warn/timeout/kick/ban + mod-log history) — nothing here should be dropped or merged into another subsystem. The improvements are structural, not domain-scope changes: (1) unify the three divergent authority mechanisms into one dual-floor declaration (G-A12) so a guild's configured `moderator_role` (ADR-008) works identically on `!modmenu`, `/moderation`, and the panel — today it verifiably does not (the slash command ignores it entirely); (2) declare the 7 modals' field schemas (G-A1), leaving only the real hierarchy/escalation/notify logic as registered handlers; (3) re-model `public_log_channel`/`moderator_role`/`trusted_role` as proper `BindingSpec`s (native channel/role pickers, already a shipped §2.5 primitive — no new amendment needed); (4) fix or drop the orphaned `mod_log` `ResourceRequirement` that never binds to anything at the moderation-subsystem level; (5) let each `PanelActionSpec.capability_required` be its own value (`moderation.log.view` for the logs button, not the panel-wide floor) — the grammar already supports this, today's monolithic `interaction_check` just doesn't use it; (6) close the `allowed_values`-is-a-widget-hint-only enforcement gap (flagged above) at the kernel level so the three enum settings' validators genuinely become removable, not just assumed removable.

**Optimal new-bot form:** one `moderation` manifest where every action (warn/timeout/kick/ban/unban/clearwarnings) is declared once as a `CommandSpec` (prefix + slash, `CommandKind.BOTH`, sharing one dual-floor authority declaration per G-A12) and once as a matching `PanelActionSpec` with `defer_mode="modal"` + a declared `ModalFieldSpec` per G-A1 — both routing to the SAME registered `moderation.<action>` `HandlerRef`, so there is exactly one place the hierarchy check, `ReasonRequiredError`, escalation ladder, DM notify, and cleanup-sweep request live, instead of the logic being duplicated across a cog method and a modal's `on_submit` (today's shipped code already mostly achieves this via the shared `moderation_service`/`moderation_helpers` layer — the manifest form would make that sharing structural rather than a code convention).

**Dependency-layer guess:** **early governance** — moderation is foundational safety tooling that other Lane A subsystems (automod, cleanup, image_moderation) and even Lane C subsystems (chain, counting) call into via `auto_delete` for rule-based deletion (and `security_service` calls `moderation_service.kick` directly for account-age auto-rejection); it should build in the same early layer as the capability/governance kernel itself, security, and automod — before feature subsystems (economy, games) that merely consume the moderator-tier capability check.

**Production-grade done-definition:** the `parity/` golden must prove — (a) every one of the 7 audited actions writes exactly one `mod_logs` row + one `audit.action_recorded` + one `moderation.action_taken` event sharing a `mutation_id`, identically from BOTH the command surface and the panel-modal surface (today's dual-surface parity, pinned by `test_no_direct_moderation_writes.py`); (b) the warn-escalation ladder reproduces the exact threshold→action→reset sequence byte-for-byte against `moderation_config.py`'s current behavior; (c) a matrix of {holds raw Discord permission} × {holds configured moderator/trusted role} × {is platform owner} resolves IDENTICALLY across `!modmenu`, `/moderation`, and the panel (the G-A12 fix, verified against today's documented divergence); (d) all 15 settings resolve to the same effective `ModerationPolicy` as today's `resolve_value`-based `load_policy`, and the 3 enum settings' new kernel-level `allowed_values` enforcement (if adopted) rejects the same inputs the current validators do.

**Outperform-target:** comparable capability = Dyno/Carl-bot/MEE6's warn-and-escalate systems. We already outperform on: capability-native moderator roles (not just raw Discord permissions — ADR-008), a public moderation log that structurally hides the acting moderator's identity (privacy-forward, uncommon in comparable bots), and a post-action message-cleanup sweep tied directly to the moderating action (most comparable bots require a separate manual purge command). To fully outperform, the new bot should add a case/appeal system (a persisted, referenceable "case ID" per action with a reopen/appeal flow) and bulk moderation actions (mass-ban/mass-timeout by list or role) — flagging this as **pending Lane F** for the definitive competitor feature-by-feature matrix.

**Owner-gated/blocked/external-dependency status:** none. This is pure design/documentation work; the Phase-3 hard stop (no new-repo implementation until the owner approves the design spec) applies as it does to every lane — nothing here is itself blocked beyond that standing gate.

---

### automod
_cogs: disbot/cogs/automod_cog.py, disbot/cogs/automod/listener.py, disbot/cogs/automod/schemas.py_

Automod v1 (owner decision Q-0108) is the automated message-filter layer beneath manual moderation: a master switch + four independent rule toggles (spam burst, invite links, excessive caps, mass mentions), each with its own threshold, plus a role/channel exempt safety valve. It is glue-only: the cog registers a message-pipeline stage; `cogs/automod/listener.py` orchestrates evaluate→act; `services/automod_service.py` is the pure detection engine; `services/automod_config.py` is the read model. It owns **no DB table** (scalar guild-settings KV only, no migration) and **no mutation path of its own** — every destructive action (delete, warn) is delegated to `services/moderation_service.py`'s audited seam.

#### Surface-unit ledger

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !automod | command | disbot/cogs/automod_cog.py:119 (decorator `disbot/cogs/automod_cog.py:112-118`, `@commands.guild_only()` + `perms_or_owner(manage_guild=True)`) | 2 | 2 | Read-only render of `AutomodPolicy` via the static `_policy_embed` (disbot/cogs/automod_cog.py:71-110) — no mutation, only conditional text formatting over the policy dataclass; maps cleanly to `route=PanelRef(...)` + `BlockSpec(kind="text", provider=...)`, the same shape RESULTS.md gives karma's `!karma` card. The native `manage_guild` gate is a domain-lane `audience_tier`, not a governance `capability_required` — no two-lane conflict (verified against `command-surface.json`: `perm: manage_guild`, `aliases: []`, `lineno: 119` — exact match). |
| build_help_menu_view (help-dropdown hook) | help | disbot/cogs/automod_cog.py:124 | 3 | 2 | Hand-written async method returning `(embed, HubView(interaction.user))` — the exact same signature/shape repeats near-verbatim in ~10 Lane-A cogs (admin_cog.py:43, server_management_cog.py:59, moderation_cog.py:85, security_cog.py:120, welcome_cog.py:167, cleanup_cog.py:572, role_cog.py:362, channel_cog.py:201, ticket_cog.py:326, image_moderation_cog.py:128) with **no declarative primitive** in §2 for "help dropdown lands here." Proposed **G-A3** (new): a `dropdown_target: PanelRef` field turns this into pure data — the target is already `automod.status`, the same panel `!automod` opens. |
| AutomodStage (message-pipeline stage class, order=5) | listener | disbot/cogs/automod_cog.py:37 (class; `process()` forwards at :49-50) | 3 | 2 | Hand-written `MessageStage` shell whose only job is to carry `name`/`order=5` (`AUTOMOD_STAGE_ORDER`, :34) and forward to `listener.process_message`. **G-1**'s `GatewayListenerSpec` (spec.py:346-364, fields verified: `gateway_event`, `handler`, `gate` — no `order` field) has no shared-pipeline/short-circuit semantics — it models one raw discord.py event, not a slot in a 5-subsystem ordered pipeline (`core/runtime/message_pipeline.py`, canonical order table at :44-58: automod=5, cleanup=10, counting=15, chain=20, image_mod=25 — verified verbatim). Proposed **G-A2** (new): `MessagePipelineStageSpec(stage_name, order, handler, fail_open, short_circuits_on)` — with it, the shell disappears entirely; only the forwarding `HandlerRef` remains as code. |
| cog_load registers pipeline stage + schema | listener | disbot/cogs/automod_cog.py:59 | 3 | 1 | Boilerplate lifecycle wiring: `register_schemas()` + `message_pipeline.register(AutomodStage())`. With **G-A2** + a kernel manifest-loader, this registration is auto-performed from the declared `MessagePipelineStageSpec` + `settings` tuple — zero hand code, same as any other kernel-generated lifecycle hook. |
| cog_unload unregisters pipeline stage | listener | disbot/cogs/automod_cog.py:66 | 3 | 1 | Symmetric teardown boilerplate (`message_pipeline.unregister(AUTOMOD_STAGE_NAME)`); same **G-A2** kernel-generated teardown once the stage is declared data. |
| process_message (per-message evaluate + act) | listener | disbot/cogs/automod/listener.py:28 | 3 | 3 | **Deliberate escape hatch.** Orchestrates policy load → `automod_service.evaluate` → `_act` (delete via `moderation_service.auto_delete`, conditional warn via `moderation_service.warn`, best-effort advisory emit), with explicit fail-open try/except around each fault class logged with distinct messages (config-read fault :43-47, detector fault :52-56, per the module's fail-open discipline docstring :9-11). Real cross-service orchestration + fault-class-specific behavior — not renderable as data, same class as karma's `!thanks` audited-seam handler. |
| automod_service.evaluate (spam / invite / caps / mentions rule engine) | service-fn | disbot/services/automod_service.py:173 | 3 | 3 | **Deliberate escape hatch.** The actual detection rules: sliding-window spam counter (`SpamTracker`, :56-91), invite-link regex (`find_invite`, :108-110), caps-ratio threshold (`exceeds_caps`/`caps_ratio`, :113-136), mention tally with an `@everyone` sentinel (`mention_count`, :139-152), and exempt-role/channel short-circuit (`_is_exempt`, :160-170) — genuine business logic the grammar must never swallow, the same class as blackjack's `game engine (rules)` row in RESULTS.md. |
| automod.rule_triggered event | event | disbot/cogs/automod/listener.py:114 (emit call; declared in `core/events_catalogue.py:76`) | 1 | 1 | Clean `EventSpec` declaration, `observability_only=True` — verified **no** `bus.on("automod.rule_triggered")` subscriber anywhere in the repo (`grep -rn "rule_triggered" disbot` hits only the emitter, its own docstring, and the catalogue entry). The emit call itself lives inside the tier-3 `_emit`/`_act` handler — same split RESULTS.md gives `karma.granted`. |
| capability: automod.settings.configure | setting | disbot/utils/subsystem_registry.py:539 | 1 | 1 | Plain string in the manifest's `capabilities` tuple — pure declaration. ⚠ **Verified drift, not a grammar gap:** this string is not enforced anywhere — no `@capability("automod.settings.configure")` use-site exists (`core/runtime/subsystem_capabilities.py` reverse-map, grep-confirmed empty for this string), and every real `SettingSpec.capability_required` below is `"moderation.settings.configure"` (disbot/cogs/automod/schemas.py:61, a deliberate documented cross-subsystem capability borrow — "automod *is* moderation's automated layer"). The registry-declared capability is stale/orphaned catalog metadata (its only other occurrences are downstream mirrors of the same registry entry — `dashboard/data/dashboard.json` and this audit's own `ground-truth/subsystems.json` — not independent use-sites); worth a docs/registry cleanup pass, independent of this audit. |
| SUBSYSTEMS["automod"] registry entry (display_name/emoji/color/tags/entry_points/related_subsystems/parent_hub/ui_priority/dependencies) | setting | disbot/utils/subsystem_registry.py:520-541 | 1 | 1 | Maps 1:1 onto `SubsystemManifest` root fields (display_name, emoji, color_token, category, parent_hub, ui_priority, dependencies) — pure declaration, no code. ⚠ **Field-value note:** the live registry's `dependencies` value is `[]` (empty) today, not `["moderation"]` — the manifest sketch below declares `dependencies=("moderation",)` as the auditor's own recommended addition (documenting the real functional coupling to moderation's mutation seam), not a value the registry already carries verbatim. The `related_subsystems` field, by contrast, genuinely is `["moderation", "cleanup"]` in source. |
| setting: enabled (master switch) | setting | disbot/cogs/automod/schemas.py:115 | 1 | 1 | Plain bool (`_validate_bool`, schemas.py:64-67, is a trivial `isinstance` check — no bounds, so not a G-5 case); `default=False` (services/automod_config.py:42) is a free `activation` choice, no external side effects to force a posture. |
| setting: spam_enabled | setting | disbot/cogs/automod/schemas.py:128 | 1 | 1 | Plain bool, same as above. |
| setting: invites_enabled | setting | disbot/cogs/automod/schemas.py:137 | 1 | 1 | Plain bool. |
| setting: caps_enabled | setting | disbot/cogs/automod/schemas.py:146 | 1 | 1 | Plain bool. |
| setting: mentions_enabled | setting | disbot/cogs/automod/schemas.py:155 | 1 | 1 | Plain bool. |
| setting: spam_count | setting | disbot/cogs/automod/schemas.py:164 | 2 | 1 | `validator=_validate_spam_count` (schemas.py:77-78) wraps `_bounded_int(value, MIN_SPAM_COUNT, MAX_SPAM_COUNT)` (schemas.py:70-74) — a registered-ref bounds check, same class RESULTS.md gives karma's `cooldown_seconds`/`daily_cap`. **G-5** (declarative validator bounds) turns `(2, 50)` into data instead of a Python function. |
| setting: spam_window_seconds | setting | disbot/cogs/automod/schemas.py:178 | 2 | 1 | Same **G-5** class (`_validate_spam_window`, schemas.py:81-82; bounds 1–120s). |
| setting: caps_percent | setting | disbot/cogs/automod/schemas.py:189 | 2 | 1 | Same **G-5** class (`_validate_caps_percent`, schemas.py:85-86; bounds 1–100%). |
| setting: mentions_count | setting | disbot/cogs/automod/schemas.py:203 | 2 | 1 | Same **G-5** class (`_validate_mentions_count`, schemas.py:89-90; bounds 2–50). |
| setting: exempt_roles | setting | disbot/cogs/automod/schemas.py:214 | 3 | 1 | Shipped as a hand-validated CSV `str` (`_validate_id_csv`, schemas.py:93-111 — real per-token parsing, numeric validation, and a custom error message) standing in for a list of role ids; `services/automod_config.parse_id_csv` (:106-122) is the tolerant read-side twin. **G-2** (list-valued settings + add/remove workflows): `value_type="list[int]"` + the kernel's generated add/remove picker removes the bespoke parser/validator entirely — same class as logging's `ignored_channels`/`ignored_users`. |
| setting: exempt_channels | setting | disbot/cogs/automod/schemas.py:226 | 3 | 1 | Same **G-2** class. |

**Unit kinds present:** command, listener, service-fn, event, setting, help.
**Unit kinds explicitly absent (verified, not silently omitted):**
- **panel** (dedicated view/component class) — automod has no `discord.ui.View`/`BaseView` subclass; `grep -n "class .*View" disbot/cogs/automod_cog.py disbot/cogs/automod/*.py` returns nothing. The only rendering is a plain `discord.Embed` built by `_policy_embed` and returned inline (via `ctx.send` or the help-hook tuple); the generic `HubView` wrapper it's paired with belongs to the shared help/nav layer, not to automod.
- **store** — no dedicated table/migration; `grep -rn "automod" disbot/migrations disbot/utils/db` returns nothing. All 11 settings are scalar guild-settings KV (legacy table), confirmed by the schemas.py module docstring ("All settings are scalar guild settings … **no migration**").
- **game** — not applicable; automod has no session/turn/leaderboard surface.
- **diagnostics** (`DiagnosticProviderSpec`-shaped) — none registered; grep for `DiagnosticProviderSpec`/`register_diagnostic` in automod's files returns nothing.
- **bindings/resources** (`BindingSpec`/`ResourceRequirement`) — none; automod acts in place on the triggering message/channel, it never binds a destination channel or provisions a resource (contrast `logging`'s 11 channel bindings).
- **mutation path (`*_mutation.py`)** — automod owns no mutation file and calls `db.*`/`pool.execute` nowhere; every write is delegated (see Structural-gap flags below).

**Structural-pattern flags:**
- **Message-pipeline stage — PRESENT.** Registered via `core.runtime.message_pipeline.register(AutomodStage())` in `cog_load` (disbot/cogs/automod_cog.py:59, :64), `order=5` (`AUTOMOD_STAGE_ORDER`, :34), matching the canonical stage-order table in `core/runtime/message_pipeline.py:44-58`. Fail-open confirmed: `listener.py` wraps both `automod_config.load_policy` (:43-47) and `automod_service.evaluate` (:52-56) in `except Exception` blocks that log and return an empty `StageResult()`, so any config-read or detector fault lets the message through — matches the module docstring's stated discipline (listener.py:9-11) and `docs/ownership.md:38`'s "routes every action through `moderation_service`" claim, both verified against source.
- **Raw gateway listener (`@bot.event`/`@commands.Cog.listener`) or `bus.on` subscription — CONFIRMED ABSENT.** `grep -rn "bus\.on\|@bot\.event\|@commands\.Cog\.listener" disbot/cogs/automod_cog.py disbot/cogs/automod/listener.py disbot/cogs/automod/schemas.py` returns no matches. Automod never listens to another subsystem's event or a raw Discord gateway event; its only "listening" is the message-pipeline stage above.
- **`wait_for` wizard — CONFIRMED ABSENT.** `grep -rn "wait_for" disbot/cogs/automod_cog.py disbot/cogs/automod/*.py disbot/services/automod_*.py` returns no matches — no multi-step interactive config flow.
- **Scheduled loop (`@tasks.loop`/cron) — CONFIRMED ABSENT.** No `tasks.loop` in any automod file. The `SpamTracker` sliding window (services/automod_service.py:56-91) is in-memory, per-message bookkeeping keyed by `(guild, user, channel)`, not a scheduled task; it is explicitly not restart-persisted (ADR-002, per the class docstring at :59-61) — a restart just resets burst windows, deemed harmless.
- **Voice — CONFIRMED ABSENT.** No `voice_client`/`VoiceClient` reference anywhere in the subsystem.
- **Stateful game loop — CONFIRMED ABSENT.** No session/turn/round state; the only "state" is the process-local `SpamTracker` deque described above.
- **External API opt-in — CONFIRMED ABSENT.** No `openai`/`aiohttp`/`requests`/`httpx` import in any automod file (contrast `image_moderation`, which calls OpenAI's omni-moderation endpoint — this subsystem's twin in the auto-mod tier, per subsystem_registry.py:542-546, is NOT dependency-free).

#### Manifest sketch

```python
"""Automod — Lane A spike manifest sketch (governance/safety audit, 2026-07-02).

Source of truth (verified this pass):
    cogs/automod_cog.py            — !automod (:112-122), help hook (:124-137),
                                      AutomodStage shell (:37-50), cog_load/
                                      cog_unload (:59-69)
    cogs/automod/listener.py       — process_message (:28-62), _act (:65-100),
                                      _emit + automod.rule_triggered (:103-122)
    cogs/automod/schemas.py        — the 11 shipped SettingSpecs (:114-238)
    services/automod_config.py     — AutomodPolicy read model + defaults
    services/automod_service.py    — the pure detection engine (:38-246)
    services/moderation_service.py — the audited seam automod delegates to
                                      (auto_delete :629, warn :361, both via
                                      _record_action :181 -> emit_audit_action
                                      :213 + EVT_MOD_ACTION :227)
    utils/settings_keys/automod.py — key strings (compat item 5)

Tier verdict (measured this pass): 21 units, 13 tier-1/2 as written (62%),
19 with G-1/G-2/G-5 + the two NEW proposed families G-A2/G-A3 (90%). The
two irreducible tier-3s are the detection engine and its per-message
orchestrator — deliberate escape hatches, not gaps.
"""

from __future__ import annotations

from dataclasses import dataclass

from tools.grammar_spike.spec import (
    Activation,
    BlockSpec,
    CommandKind,
    CommandSpec,
    EventSpec,
    FieldSpec,
    HandlerRef,
    HelpEntrySpec,
    PanelRef,
    PanelSpec,
    ProviderRef,
    SettingSpec,
    SubsystemManifest,
)

_CAP = "moderation.settings.configure"  # the REAL enforced capability
# (schemas.py:61) — NOT "automod.settings.configure", which is what
# subsystem_registry.py:539 declares but no SettingSpec actually requires.
# See the ledger row above; sketch uses the enforced string, not the stale
# catalog one, so a rebuild doesn't silently inherit the drift.


# --------------------------------------------------------------------------
# G-A2 (PROPOSED, Lane A, NOT in spec.py): MessagePipelineStageSpec — a
# shared, ORDERED, fail-open on_message stage slot. Distinct from G-1's
# GatewayListenerSpec: G-1 models one raw discord.py event name -> one
# handler behind a settings gate, with NO `order` field and no shared-
# pipeline/short-circuit semantics. automod/cleanup/counting/chain/
# image_moderation all register into ONE ordered pipeline
# (core/runtime/message_pipeline.py) where `order` determines run sequence
# across five subsystems and a stage can short-circuit the rest on delete.
# Without this family every message-pipeline-tier subsystem re-writes the
# same MessageStage shell (name/order/process-that-forwards) by hand.
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class MessagePipelineStageSpec:  # sketch only — not a real spec.py type
    stage_name: str
    order: int  # canonical cross-subsystem slot (automod=5, cleanup=10, ...)
    handler: HandlerRef
    fail_open: bool = True
    short_circuits_on: str = "delete"  # never|delete|always


# --------------------------------------------------------------------------
# G-A3 (PROPOSED, Lane A, NOT in spec.py): HelpEntrySpec gains
# `dropdown_target: PanelRef | None`. Collapses the hand-written
# `build_help_menu_view(self, interaction) -> (Embed, View)` method — the
# same signature repeats near-verbatim in ~10 Lane-A cogs — into one
# declared field pointing at the subsystem's existing landing panel.
# --------------------------------------------------------------------------

AUTOMOD_MANIFEST = SubsystemManifest(
    key="automod",
    display_name="Automod",
    description="Spam, invite links, excessive caps, and mass-mention filtering.",
    emoji="🛡️",
    category="moderation",
    visibility_tier="administrator",
    capabilities=(_CAP,),
    # Recommended addition, not a literal carry-over: the live registry
    # entry's `dependencies` field is `[]` today (subsystem_registry.py:532).
    # Declaring it here documents the real functional coupling — every
    # mutation delegates to moderation's seam — that the shipped catalog
    # doesn't yet encode.
    dependencies=("moderation",),
    parent_hub="moderation",  # [A] — subsystem_registry.py:537
    ui_priority=73,  # subsystem_registry.py:536
    commands=(
        # cogs/automod_cog.py:112-119 — native manage_guild gate, not a
        # capability lane: audience_tier only (§2.2 two-lane exclusivity).
        CommandSpec(
            name="automod",
            kind=CommandKind.PREFIX,
            summary="Show the current automod policy for this server.",
            route=PanelRef("automod.status"),
            audience_tier="administrator",
        ),
    ),
    panels=(
        # cogs/automod_cog.py:71-110 _policy_embed — TIER 2: a read-only
        # multi-line status render over the AutomodPolicy read model. Also
        # the G-A3 dropdown_target below — same panel, no separate embed.
        PanelSpec(
            panel_id="automod.status",
            subsystem="automod",
            title="🛡️ Automod",
            audience="invoker",
            body=(
                BlockSpec(
                    kind="text",
                    provider=ProviderRef("automod.policy_summary"),
                ),
            ),
        ),
    ),
    settings=(
        SettingSpec(
            name="enabled", value_type="bool", default=False,
            settings_key="automod_enabled", capability_required=_CAP,
            activation=Activation.OFF_UNTIL_OPT_IN,
            hint="Master switch for automod.",
        ),
        SettingSpec(
            name="spam_enabled", value_type="bool", default=False,
            settings_key="automod_spam_enabled", capability_required=_CAP,
            activation=Activation.OFF_UNTIL_OPT_IN,
        ),
        SettingSpec(
            name="invites_enabled", value_type="bool", default=False,
            settings_key="automod_invites_enabled", capability_required=_CAP,
            activation=Activation.OFF_UNTIL_OPT_IN,
        ),
        SettingSpec(
            name="caps_enabled", value_type="bool", default=False,
            settings_key="automod_caps_enabled", capability_required=_CAP,
            activation=Activation.OFF_UNTIL_OPT_IN,
        ),
        SettingSpec(
            name="mentions_enabled", value_type="bool", default=False,
            settings_key="automod_mentions_enabled", capability_required=_CAP,
            activation=Activation.OFF_UNTIL_OPT_IN,
        ),
        # G-5: bounds as DATA, not a `_bounded_int(value, lo, hi)` function.
        SettingSpec(
            name="spam_count", value_type="int", default=5,
            settings_key="automod_spam_count", capability_required=_CAP,
            validator=HandlerRef("bounds(2,50)"),  # G-5 target shape
        ),
        SettingSpec(
            name="spam_window_seconds", value_type="int", default=7,
            settings_key="automod_spam_window_seconds", capability_required=_CAP,
            validator=HandlerRef("bounds(1,120)"),
        ),
        SettingSpec(
            name="caps_percent", value_type="int", default=70,
            settings_key="automod_caps_percent", capability_required=_CAP,
            validator=HandlerRef("bounds(1,100)"),
        ),
        SettingSpec(
            name="mentions_count", value_type="int", default=4,
            settings_key="automod_mentions_count", capability_required=_CAP,
            validator=HandlerRef("bounds(2,50)"),
        ),
        # G-2: shipped as a hand-validated CSV str; target form is a real
        # list[int] setting + kernel add/remove workflow (no bespoke parser).
        SettingSpec(
            name="exempt_roles", value_type="list[int]", default=(),
            settings_key="automod_exempt_roles", capability_required=_CAP,
            hint="Roles never acted on.",
        ),
        SettingSpec(
            name="exempt_channels", value_type="list[int]", default=(),
            settings_key="automod_exempt_channels", capability_required=_CAP,
            hint="Channels never acted on.",
        ),
    ),
    events=(
        # cogs/automod/listener.py:103-122 — advisory, no current subscriber.
        EventSpec(
            name="automod.rule_triggered",
            payload_schema=(
                FieldSpec("guild_id", "int"),
                FieldSpec("user_id", "int"),
                FieldSpec("rule", "str"),
                FieldSpec("channel_id", "int"),
            ),
            owner_subsystem="automod",
            observability_only=True,
        ),
    ),
    # -----------------------------------------------------------------
    # G-A2 (proposed) — not a real SubsystemManifest field today. Shown
    # as the shape needed: today's tier-3 AutomodStage shell
    # (cogs/automod_cog.py:37-50) + cog_load/cog_unload registration
    # (:59-69) collapse into this one declared row; the process_message
    # handler stays the only real code (tier 3, by design).
    #
    # message_pipeline_stages=(
    #     MessagePipelineStageSpec(
    #         stage_name="automod",
    #         order=5,
    #         handler=HandlerRef(
    #             "automod.process_message",
    #             justification="rule evaluation (spam/invite/caps/mentions) "
    #             "+ cross-service delete+warn+emit orchestration — real "
    #             "domain logic, stays tier 3",
    #         ),
    #         fail_open=True,
    #         short_circuits_on="delete",
    #     ),
    # ),
    # -----------------------------------------------------------------
    stores=(),  # automod owns no table — scalar guild-settings KV only
    help=HelpEntrySpec(
        summary="Automatic spam/invite/caps/mass-mention filtering beneath manual moderation.",
        examples=("!automod",),
        # G-A3 (proposed field): dropdown_target=PanelRef("automod.status")
        # replaces cogs/automod_cog.py:124-137's hand-written method.
    ),
)
```

*(Verified this pass: the manifest sketch above was constructed against the real `tools/grammar_spike/spec.py` dataclasses and passes every `__post_init__` invariant — the bool settings all set an `Activation`, the command's empty `capability_required` avoids the two-lane-exclusivity check, and no duplicate ids — with zero errors.)*

#### Tier-3 dispositions

- **build_help_menu_view** (disbot/cogs/automod_cog.py:124) → **grammar gap, propose G-A3** (new): `HelpEntrySpec.dropdown_target: PanelRef`. The method's entire body is "load the read model, hand back this panel's embed + a generic hub view" — a generic, repeatable shape (confirmed repeated near-verbatim across admin, server_management, moderation, security, welcome, cleanup, role, channel, ticket, image_moderation — all 10 other Lane-A cogs), not domain logic.
- **AutomodStage class + its registration** (disbot/cogs/automod_cog.py:37, :59, :66) → **grammar gap, propose G-A2** (new): `MessagePipelineStageSpec`. G-1's `GatewayListenerSpec` doesn't cover this — it has no `order` field and no notion of a shared, ordered, short-circuiting pipeline across five subsystems. The shell class + its cog_load/cog_unload registration is boilerplate that should be kernel-generated from one declared `(stage_name, order, handler, fail_open)` row.
- **process_message** (disbot/cogs/automod/listener.py:28) → **deliberate escape hatch.** Real cross-service orchestration (policy gate → detect → delete → conditional warn → advisory emit) with fault-class-specific fail-open handling. Thin in line count, not thin in responsibility — stays a `HandlerRef`, same call as RESULTS.md makes for karma's `!thanks`.
- **automod_service.evaluate** (disbot/services/automod_service.py:173) → **deliberate escape hatch.** The actual rule engine (spam sliding window, invite regex, caps ratio, mention tally, exempt short-circuit) — genuine business logic, the same class as blackjack's game engine (RESULTS.md: "the grammar must never express game rules"); here, "the grammar must never express moderation-detection rules."
- **setting: exempt_roles** (disbot/cogs/automod/schemas.py:214) → **reuse G-2** (list-valued settings + add/remove workflows). Shipped as a hand-validated CSV string; G-2's `list[int]` + kernel add/remove UI removes `_validate_id_csv` entirely.
- **setting: exempt_channels** (disbot/cogs/automod/schemas.py:226) → **reuse G-2**, same class.

(The four bounded-int settings — spam_count, spam_window_seconds, caps_percent, mentions_count — are tier **2** as-written, not tier 3; they're listed in the ledger under **reuse G-5** but don't need a separate disposition bullet since they already partially fit.)

#### Fit numbers

| Scope | Surface units | Fit — spec as written | Fit — with proposed families |
|---|---|---|---|
| automod | 21 | **62%** (13/21) | **90%** (19/21) |

Proposed families applied: **G-1** is *not* actually usable as-is for the message-pipeline shape (see G-A2 below); **G-2** (exempt_roles/exempt_channels), **G-5** (the four bounded-int settings), plus the two **new** Lane-A amendments **G-A2** (MessagePipelineStageSpec) and **G-A3** (help-menu dropdown target). The remaining 2/21 (~10%) tier-3 units — `process_message` and `automod_service.evaluate` — are irreducible, deliberate escape hatches, not gaps.

#### Structural-gap flags

- **Permission/capability gates.** The command's native `manage_guild` gate is a domain-lane `audience_tier` check (§2.2), already fully declarative — no gap. The settings' governance-lane gate is a **cross-subsystem capability borrow** (`moderation.settings.configure`, schemas.py:61) — already expressible today via plain `capability_required` string reuse, no new primitive needed. The one real finding here is data hygiene, not grammar: `subsystem_registry.py:539` declares an `"automod.settings.configure"` capability that is never enforced or decorated anywhere (verified by grep against `core/runtime/subsystem_capabilities.py`'s reverse map, and against every `capability_required` use-site in the codebase) — stale catalog metadata that should be corrected (either wire it up as automod's own capability or delete the orphaned string) independent of this audit.
- **Setup/provisioning wizards.** None — automod requires no channel/role binding and provisions no resource (contrast `logging`'s 11 channel bindings + `ResourceRequirement`s). Nothing to express.
- **`wait_for` wizards.** None — confirmed absent (see Structural-pattern flags above).
- **External API opt-ins.** None — automod is pure in-process detection (regex + counters), unlike its auto-mod-tier twin `image_moderation` (OpenAI omni-moderation). Nothing to express.
- **Audit/mutation seams.** Automod performs **zero** direct writes. Both real side effects — message deletion and warning — call straight into `moderation_service.auto_delete` (disbot/services/moderation_service.py:629) and `moderation_service.warn` (disbot/services/moderation_service.py:361), which both route through the shared `_record_action` helper (disbot/services/moderation_service.py:181) that writes `mod_logs`, calls `emit_audit_action` (:213), and emits `EVT_MOD_ACTION` (:227) — one audited authority, exactly the shape the grammar wants (`HandlerRef` to another subsystem's audited seam, never a parallel audit path). This is a **model example**, not a gap. One second-order nuance worth flagging for the capstone: automod's `warn` call can, via moderation's own `warn_threshold` escalation ladder (moderation_service.py:367-374), transitively trigger a **timeout/kick/ban** — a destructive action neither declared nor visible in automod's own manifest. The grammar's `dependencies=("moderation",)` field documents the coupling but doesn't express the potential escalation outcome; likely acceptable (moderation owns and declares that ladder itself) but worth the capstone cross-referencing when it composes subsystem dependency graphs.
- **Destructive actions.** Delete + warn (see above) — both gated behind the fail-open detector, never exposed as an operator-facing button (so `PanelActionSpec.destructive`/`style="danger"` doesn't apply; automod has no panel actions at all).
- **Lifecycle tasks/scheduled loops.** None — confirmed absent; the in-memory `SpamTracker` is per-message bookkeeping, not a scheduled task.
- **Governance/cache behavior.** `automod_config.load_policy` resolves every field through the shared `services.settings_resolution.resolve_value` per call — the same resolution path every subsystem uses, nothing automod-specific to flag.

#### Reconsider / optimize

**MAP.** 21 real surface units: 1 command, 1 help hook, 3 message-pipeline-registration units, 1 per-message orchestrator, 1 detection engine, 1 advisory event, 2 registry/capability declarations, 11 settings. No panel/view class, no store, no game, no diagnostics, no bindings/resources, no owned mutation path.

**RECONSIDER — verdict: keep + improve.** The architecture is sound: fail-open discipline is real and tested, destructive actions route through the one audited seam (no parallel audit path), and the four rule types cover the standard baseline (spam/invite/caps/mass-mention) that every comparable bot ships. The scope is deliberately narrow — banned-word filtering lives in `cleanup` and raid detection in `security` (both Lane A siblings, and both genuinely listed in `subsystem_registry.py`'s `related_subsystems: ["moderation", "cleanup"]` for automod) rather than in automod — which is a reasonable split, but all three subsystems (plus `image_moderation`) sit on the identical message-pipeline-stage shape at neighboring `order` slots (5/10/15/20/25). The concrete improvement is architectural consolidation of the *pattern* (via G-A2), not necessarily a subsystem merge — the capstone should weigh whether "auto-mod tier" becomes one operator-facing coherent policy surface (one settings section, one status panel) spanning automod+cleanup(word-filter)+image_moderation, even if the underlying manifests stay separate.

**SIMULATE.** The manifest sketch above would pass the §2.10 simulator cleanly except for the two irreducible tier-3 handlers (`process_message`, `automod_service.evaluate`), which the `parity/` golden harness needs fixtures for: a spam burst (N messages within the window), an invite-link post, a >`caps_percent` shout, a mass-mention message, and an exempt-role/exempt-channel bypass — each asserting the same `AutomodVerdict` + delete/warn/emit outcome the shipped 432 lines of unit tests already golden (`tests/unit/services/test_automod_config.py`, `test_automod_service.py`, `tests/unit/cogs/test_automod_listener.py`, `test_automod_schemas.py`).

**OPTIMIZE — the better form.** (1) Adopt **G-A2** so every message-pipeline-tier subsystem (automod, cleanup, counting, chain, image_moderation) declares its stage as one row instead of hand-writing an identical `MessageStage` shell + `cog_load`/`cog_unload` registration five times. (2) Adopt **G-2** for `exempt_roles`/`exempt_channels` so operators get a real role/channel picker with add/remove instead of typing comma-separated ids into a text field. (3) Adopt **G-5** for the four bounded-int settings so `(min, max)` is declared data instead of four near-identical `_bounded_int` wrapper functions. (4) Adopt **G-A3** to fold the `!automod` status panel and the help-dropdown hook into one declared `dropdown_target`, deleting `build_help_menu_view` entirely.

**Dependency-layer guess:** early governance. Automod depends on the message-pipeline kernel (L0/foundation) and on `moderation_service`'s audited seam (must exist and be stable first) — it should build immediately after moderation + the message-pipeline substrate are online, ahead of any feature-tier (economy/games) subsystem.

**Production-grade done-definition:** the rebuilt automod is done when it (a) passes a ported version of the shipped 432-line test suite (config defaults, the four pure detectors, the listener's fail-open contract, schema/default parity) against the new kernel; (b) passes a `parity/` golden replaying a fixed message sequence (spam burst, invite link, caps shout, mass-mention, exempt bypass) with byte-identical `AutomodVerdict` + delete/warn/emit outcomes; and (c) demonstrably fails open under both a forced config-load exception and a forced detector exception (the message must survive in both cases, matching listener.py:43-47/52-56).

**Outperform-target status:** automod's four rule types (spam/invite/caps/mass-mention) already match the baseline every major moderation bot ships (MEE6, Carl-bot, Dyno automod modules). Our architectural edge — a single ordered, fail-open, audited-seam pipeline instead of independent competing `on_message` handlers, with the fail-open contract explicit and unit-tested — is real today but the *feature* comparison (banned-word regex libraries, AI-toxicity scoring, per-channel rule overrides, strike-count configs, allowlist patterns) needs the ecosystem benchmark: **pending Lane F.**

**Owner-gated/blocked/external-dependency status:** none. Fully internal (no external API, no third-party service), not owner-gated beyond the standing Phase-3 build-approval gate that covers the whole rebuild.

**Cross-lane dependency:** none found. Automod's only structural dependencies (`moderation`'s audited mutation seam; the shared `order` slot with `cleanup`'s message-pipeline stage) are both Lane A subsystems already in this lane.
</corrected_section_markdown>

---

### image_moderation
_cogs: disbot/cogs/image_moderation_cog.py, disbot/cogs/image_moderation/listener.py, disbot/cogs/image_moderation/schemas.py (services: disbot/services/image_moderation_config.py, disbot/services/image_moderation_service.py; keys: disbot/utils/settings_keys/image_moderation.py)_

**Verifier's note:** the draft's file:line citations, absence-claims, and grep evidence were independently re-checked against source and are accurate except where marked "correction" below. Two real issues surfaced: (1) the manifest sketch as originally written does **not** actually round-trip through `SubsystemManifest.__post_init__` — verified by executing it — because all five bool `SettingSpec`s omitted the mandatory `activation=` field; fixed below. (2) the ledger over-counts three units (stage-registration glue split into 3 rows, help split into 2 rows, plus an orphaned capability tag scored as a passing unit) relative to the counting convention the three existing worked manifests (karma/logging/blackjack) actually use in `tools/grammar_spike/measure.py`; consolidated below, with fit numbers recomputed.

**Store finding (resolves the scaffold's "unverified" flag definitively):** image_moderation owns **no dedicated table and no migration**. `grep -rn "image_moderation" disbot/migrations/*.sql` returns zero matches. Every setting is an ordinary scalar row in the shared legacy KV table `guild_settings` (`disbot/utils/db/settings.py:21-34`, `get_setting`/`set_setting`, `SELECT/INSERT ... guild_settings WHERE guild_id=$1 AND key=$2`), resolved through `services.settings_resolution.resolve_setting`/`resolve_value` (`disbot/services/settings_resolution.py:300-398,421-444`) and consumed by `image_moderation_config.load_policy` (`disbot/services/image_moderation_config.py:103-165`). This is confirmed, not merely likely — there is no separate `image_moderation_*` table anywhere in the schema.

**External-API finding:** confirmed real, structural external-API opt-in. The classifier (`cogs/image_moderation/listener.py:45-49`, `_default_classifier` → `core.runtime.ai.providers.openai_moderation.default_provider().classify_image`) calls OpenAI's `omni-moderation-latest` endpoint: `_ensure_client()` lazily constructs `AsyncOpenAI(api_key=...)` at `disbot/core/runtime/ai/providers/openai_moderation.py:73`, and `classify_image` calls `client.moderations.create(...)` at lines 83-87 of the same file (**correction**: the draft compressed this to a single `:82-84` citation, which does not actually contain the `AsyncOpenAI(...)` construction). Only the image **URL** is transmitted (never text/author, per that module's and the listener's docstrings). It is off by default (`DEFAULT_ENABLED = False`, `image_moderation_config.py:49`) and fails open on any fault — missing key/SDK (`ProviderUnavailableError`), network error, or malformed response all let the image through (`cogs/image_moderation/listener.py:69-102`). This is a genuine danger-zone unit (external network call, cost + privacy surface), and the classify call site itself (`process_message`) is correctly kept a deliberate escape hatch below, not a grammar gap.

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !imagemod | command | disbot/cogs/image_moderation_cog.py:116-126 (def at :123, confirmed against ground-truth/command-surface.json: kind=prefix, perm=manage_guild) | 2 | 2 | read-only status embed built from `load_policy()`/`_policy_embed`; maps cleanly to a `PanelRef` + `FieldsBlock` over a `ProviderRef` — identical shape to karma's `!karma` card (RESULTS.md: 2/2, "no bespoke view class survives"). Uses `perms_or_owner(manage_guild=True)` — a raw-permission gate, so the two-lane model (§2.2) puts this on `audience_tier`, not `capability_required`. No G needed. |
| help surface (`build_help_menu_view` dropdown hook + the command's `help=` text, one capability) | help | disbot/cogs/image_moderation_cog.py:128-141 (dropdown hook, reuses `_policy_embed` + a generic `HubView`, `disbot/views/base.py:206`); :116-126 (`help=` text on `!imagemod`) | 1 | 1 | **Correction:** the draft scored this as two ledger rows ("build_help_menu_view (help-dropdown hook)" and a separate "help entry (HelpEntrySpec: summary + example)"). Every worked manifest in `tools/grammar_spike/measure.py` — including blackjack, which has an identical `build_help_menu_view` hook at `blackjack_cog.py:101` — counts exactly **one** "help entry" unit (tier 1/1, "projection"), not two; the hook is never split out. Merged to match that convention. §2's `HelpEntrySpec` + `PanelRef`/`NavigationSpec` already generates this navigation with zero per-subsystem code — the hand-written hook is exactly the boilerplate the manifest eliminates. No gap. |
| ImageModerationStage registration (stage class + `cog_load` + `cog_unload`, one capability) | listener | disbot/cogs/image_moderation_cog.py:41-54 (class), :63-68 (`cog_load`), :70-73 (`cog_unload`) | 3 | 1 | **G-A2** (new, proposed below): no primitive in §2 for the internal ordered/short-circuiting message-pipeline stage (distinct from G-1's raw discord.py `GatewayListenerSpec`). All three code locations register/unregister the *same* capability — a `MessagePipelineStageSpec(order=25, gate=..., handler=HandlerRef("image_moderation.scan"))` declaration replaces all of them at once, and they are pure boilerplate (4-line wrapper + two registration calls) with zero domain logic. **Correction:** the draft counted the class, `cog_load`, and `cog_unload` as three separate ledger rows, all disposed by the same amendment. `blackjack_cog.py`'s `cog_load` (schema registration **and** three background-task spawns — recovery of solo/pvp/escrow state, `blackjack_cog.py:123`) is at least as substantial and was never split into a separate unit in `measure.py`; it is registration glue for one capability, not three. Merging removes an artificial 3x inflation of G-A2's apparent yield in the fit numbers. |
| process_message (scan attachments → act, incl. `_is_exempt`/`_act`/`_emit`) | listener | disbot/cogs/image_moderation/listener.py:52-193 (core scan loop :52-109; exemption check `_is_exempt` :112-126; delete+warn+emit `_act` :129-171, `_emit` :174-193) | 3 | 3 | **Deliberate escape hatch, not a gap.** Real domain logic: policy-gated exemption checks, a per-URL loop calling an external paid/free AI classifier, multi-bucket verdict evaluation against a configurable threshold, and delete+warn orchestration through `moderation_service`. **G-A2** declares the *registration* (gate + handler pointer) but the handler body itself stays code — same honest call as blackjack's reaction-join listener (RESULTS.md: "the join handler is real lobby logic — stays tier 3 honestly"), not logging's thin "fetch-and-forward" listeners that get bumped to tier 2. |
| image_moderation.flagged (bus.emit) | event | disbot/cogs/image_moderation/listener.py:39 (const `EVT_IMAGE_MODERATION_FLAGGED`), :174-193 (`_emit`); catalogued disbot/core/events_catalogue.py:77-83 | 1 | 1 | `EventSpec` declaration. **Confirmed zero real subscribers** (`grep -rn "image_moderation.flagged\|EVT_IMAGE_MODERATION_FLAGGED" disbot/` finds only the emitter + the catalogue comment) — this must declare `observability_only=True` per spec.py's own `EventSpec.__post_init__` guard, which §2 already supports; no gap. Matches automod's identical "advisory, not a second audit path" shape (events_catalogue.py:71-76). The emit call's logic lives inside the tier-3 `_act`/`_emit` handler above, not in the event's own declarative shape. |
| setting: enabled (master switch) | setting | disbot/cogs/image_moderation/schemas.py:96-108 | 1 | 1 | plain bool setting. Carries `validator=_validate_bool` (schemas.py:53-56) but that is a pure `isinstance` type-guard against Python's `isinstance(True, int) is True` quirk, zero domain logic — the exact pattern logging's own bool settings use (`cogs/logging/schemas.py:126` etc.) and RESULTS.md still scores those 1/1 ("bool setting"). No gap. |
| setting: sexual_enabled | setting | disbot/cogs/image_moderation/schemas.py:109-117 | 1 | 1 | same bool-setting class as `enabled`. |
| setting: violence_enabled | setting | disbot/cogs/image_moderation/schemas.py:118-126 | 1 | 1 | same bool-setting class. |
| setting: harassment_enabled | setting | disbot/cogs/image_moderation/schemas.py:127-135 | 1 | 1 | same bool-setting class. |
| setting: hate_enabled | setting | disbot/cogs/image_moderation/schemas.py:136-144 | 1 | 1 | same bool-setting class. |
| setting: threshold_percent | setting | disbot/cogs/image_moderation/schemas.py:145-158; bounds `MIN_THRESHOLD_PERCENT=50`/`MAX_THRESHOLD_PERCENT=100` in disbot/services/image_moderation_config.py:58-59 | 2 | 1 | bounded-int validator (`_validate_threshold`, schemas.py:59-65) is a registered ref as-specced today (already tier-2, §2.5 `SettingSpec.validator` exists) — **G-5** (declarative validator bounds) makes the 50–100 bound pure data, matching karma's `cooldown_seconds`/`daily_cap` exactly (RESULTS.md: 2→1). |
| setting: exempt_roles | setting | disbot/cogs/image_moderation/schemas.py:159-170; validator `_validate_id_csv` schemas.py:68-86 | 3 | 1 | **G-2** (list-valued settings): shipped as a CSV-of-ids string (`value_type=str`) with hand-written per-token numeric validation — this is precisely logging's `ignored_channels`/`ignored_users` shape (RESULTS.md: 3→1, "§2.5 has no list-valued setting shape; with `list[type]` + kernel add/remove workflows it is pure declaration"). Once `value_type="list[int]"` exists, the CSV parsing/validation code disappears entirely. |
| setting: exempt_channels | setting | disbot/cogs/image_moderation/schemas.py:171-182; same validator | 3 | 1 | same **G-2** class as `exempt_roles`. |
| SubsystemSchema registration (IMAGE_MODERATION_CONFIG_SCHEMA + register_schemas()) | setting (container) | disbot/cogs/image_moderation/schemas.py:186-190 (schema object), :193-197 (register_schemas) | 1 | 1 | pure declarative container aggregating the 8 settings above; `SubsystemManifest.settings` replaces this 1:1, no behavior of its own. |
| store: guild_settings (shared legacy KV, no dedicated table/migration) | store | disbot/utils/db/settings.py:21-34; consumed via disbot/services/settings_resolution.py:300-398,421-444 and disbot/services/image_moderation_config.py:103-165 | 1 | 1 | resolves the scaffold's "⚠ unverified table name, no migration file found" — **definitively no dedicated table exists** (confirmed by migration grep). This is the kernel's own generic multi-tenant KV substrate, already modeled by `SettingSpec.storage` (default `"kv"`, spec.py:255) on each setting above — it is not a subsystem-owned `StoreSpec` (no `sole_writer`/invariant makes sense for a table dozens of subsystems share by key prefix). No gap; no new `StoreSpec` needed. |

**Not scored as a ledger unit — orphaned metadata, tracked as a flag only:** the registry declares a capability tag `image_moderation.settings.configure` (`disbot/utils/subsystem_registry.py:565-567`) that is referenced **nowhere else in the codebase** (`grep -rn "image_moderation.settings.configure" disbot/` → 1 hit, itself). Every actual `SettingSpec.capability_required` in schemas.py instead uses the *borrowed* `moderation.settings.configure` (schemas.py:50, deliberate per that module's docstring: "image moderation *is* moderation's automated image layer"). The registry-declared tag is inert/orphaned metadata. It passes the identity-contract cross-check silently because that check (`subsystem_registry.py:1730-1773`) validates capability strings against the **union across all subsystems' capability lists** (`all_caps.update(meta.get("capabilities", ()))` over every subsystem, then checked per-schema-setting), not per-owning-subsystem — confirmed by reading the check itself — so an unused sibling tag never trips a warning. **Correction:** the draft scored this as a passing tier-1/1 ledger row. By `measure.py`'s own definition, a unit must be "a real, user-observable or contract-bearing surface ... as shipped TODAY" — a string nothing consumes fails that bar, and the draft was already independently flagging this exact finding under Structural-gap flags below, so scoring it a second time in the ledger double-books one finding and pads the fit percentage with a non-unit. Worth a docs/registry cleanup, not a manifest-grammar gap.

**Unit kinds present:** command (1), help (1 — the dropdown hook and the command's help text are one capability, not two), listener (2 — the stage-registration triad, `process_message`), event (1), setting (9 — 8 scalar SettingSpecs [5 bool, 1 bounded-int, 2 list-of-ids] + the schema container), store (1, shared KV — not a dedicated table). Total scored units: **15**. (The registry's orphaned `image_moderation.settings.configure` capability tag is real but unconsumed metadata — a documentation-drift flag, not a counted surface unit; see the note above.)

**Unit kinds explicitly absent:**
- **panel** — no dedicated `PanelSpec`/`discord.ui.View`/`PersistentView` exists; `!imagemod` and the help hook both just `ctx.send`/return a bare embed + generic `HubView` with no buttons. (Confirmed: no `discord.ui.View` subclass, no `custom_id`, no button/select component defined anywhere under `disbot/cogs/image_moderation*` or a `disbot/views/image_moderation/` directory — none exists.)
- **binding** — no channel/role/category pointer setting. `exempt_roles`/`exempt_channels` are CSV-of-ids *value* settings, not `BindingSpec` pointers (no single bound resource).
- **resource** — no `ResourceRequirement`/channel-provisioning flow (nothing to create — image moderation acts in-place on the channel a flagged image was posted in).
- **game** — not applicable to this subsystem.
- **diagnostics** — no `DiagnosticProviderSpec` registration found referencing `image_moderation` (`grep -rln image_moderation disbot/services/diagnostic_embeds.py disbot/cogs/diagnostic_cog.py` → no hits).
- **mutation seam (`*_mutation.py`)** — image_moderation owns **no** `*_mutation.py` of its own. All writes (message delete, warn) route exclusively through `moderation_service.auto_delete` (disbot/services/moderation_service.py:629-...) and `moderation_service.warn` (disbot/services/moderation_service.py:361-...) — the audited seam is borrowed, not bypassed or duplicated (no second audit ladder, consistent with the listener module's own docstring, `cogs/image_moderation/listener.py:129-138`). This is compliant, not a gap.

**Structural-pattern flags:**
- **Gateway listener (`@bot.event`/`@commands.Cog.listener`):** **absent.** `grep -rn "@commands.Cog.listener\|@bot.event" disbot/cogs/image_moderation_cog.py disbot/cogs/image_moderation/listener.py` → no matches. The stage is invoked synchronously by `core.runtime.message_pipeline`, not a raw discord.py gateway subscription — this is why **G-1** (`GatewayListenerSpec`) doesn't quite fit and a new **G-A2** is proposed instead.
- **Message-pipeline stage:** **present** (`ImageModerationStage`, order=25 — auto-mod tier, after automod=5/cleanup=10/counting=15/chain=20, before xp=30 rewards; per the stage-order table documented at `image_moderation_cog.py:33-38`, matching the canonical table in `core/runtime/message_pipeline.py` exactly). This is the subsystem's core structural pattern and the source of the **G-A2** proposal.
- **`wait_for` wizard:** **confirmed absent** (`grep -rn "wait_for" disbot/cogs/image_moderation*` → no matches; there is no multi-step setup flow — config is entirely the generic `!settings` widget).
- **Scheduled loop (`@tasks.loop`):** **confirmed absent** (no matches in any image_moderation file).
- **Voice:** **confirmed absent** (no matches).
- **External API opt-in:** **present and structural** — see the External-API finding above the ledger. This is the subsystem's other defining danger-zone pattern alongside the pipeline stage.
- **Stateful game loop:** not applicable.

#### Manifest sketch

```python
"""Image moderation, expressed in the §2 grammar (spike style).

Source of truth (verified 2026-07-02):
    cogs/image_moderation_cog.py       — !imagemod (116-126), stage class (41-54),
                                          cog_load/cog_unload (63-73), help hook (128-141)
    cogs/image_moderation/listener.py  — process_message (52-109), _act/_emit (129-193)
    cogs/image_moderation/schemas.py   — 8 SettingSpecs (96-182), schema container (186-197)
    services/image_moderation_config.py — ImageModerationPolicy, load_policy, defaults+bounds
    services/image_moderation_service.py — pure verdict/bucket evaluation (no I/O)
    core/runtime/ai/providers/openai_moderation.py — the OpenAI SDK chokepoint (Lane D)
    utils/db/settings.py               — the shared guild_settings KV substrate (no dedicated table)

    VERIFIED (2026-07-02): this sketch was executed against tools/grammar_spike/spec.py.
    All five bool SettingSpecs require `activation=` (SettingSpec.__post_init__, §4.4) —
    an earlier draft omitted it and raised ValueError on instantiation for every one of
    them; fixed below with `Activation.OFF_UNTIL_OPT_IN` (matching server_logging's
    identical off-by-default bool-setting shape). With that fix the manifest builds
    cleanly end to end.

Tier verdict (measured): 73.3% as-written / 93.3% with amendments — the config
surface + status display are pure declaration; the one real escape hatch is
the scan-and-act handler itself (external API + verdict logic), same class
as blackjack's honest tier-3 game logic. The gap this subsystem newly
surfaces: G-A2, a message-pipeline-stage registration primitive (G-1's
GatewayListenerSpec doesn't cover the internal ordered pipeline).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tools.grammar_spike.spec import (
    Activation,
    BlockSpec,
    CommandKind,
    CommandSpec,
    EventSpec,
    FieldSpec,
    HandlerRef,
    HelpEntrySpec,
    PanelRef,
    PanelSpec,
    ProviderRef,
    S,
    SettingSpec,
    SubsystemManifest,
)


# --- PROPOSED G-A2 (not in spec.py today) ---------------------------------
# Distinct from G-1's GatewayListenerSpec: this is the internal, ordered,
# short-circuiting core.runtime.message_pipeline stage (order=5/10/15/20/25/30
# across automod/cleanup/counting/chain/image_moderation/xp), not a raw
# discord.py gateway event. Every one of those cogs hand-writes an identical
# stage-class + cog_load/cog_unload registration shape today.
@dataclass(frozen=True)
class MessagePipelineStageSpec:  # G-A2 proposal
    stage_name: str = field(metadata=S)
    order: int = field(metadata=S)
    handler: HandlerRef = field(metadata=S)
    gate: str = field(default="", metadata=S)  # e.g. "setting:image_moderation_enabled"


_CAP = "moderation.settings.configure"  # borrowed from moderation (deliberate)

IMAGE_MODERATION_MANIFEST = SubsystemManifest(
    key="image_moderation",
    display_name="Image moderation",
    description="Scan uploaded images for sexual, violent, harassment, or hate content.",
    emoji="🖼️",
    category="moderation",
    visibility_tier="administrator",
    capabilities=(_CAP,),
    # NOTE: subsystem_registry.py:566 separately declares an UNUSED
    # "image_moderation.settings.configure" tag — orphaned metadata, not
    # wired to any SettingSpec.capability_required. Flagged, not modeled here.
    dependencies=(),  # registry's own "dependencies": [] (line 559);
                      # "related_subsystems": ["moderation", "automod"] is
                      # advisory-only, not a hard dependency edge
    parent_hub="moderation",  # subsystem_registry.py:564
    commands=(
        # cogs/image_moderation_cog.py:116-126 — perms_or_owner(manage_guild=True)
        # is a raw-permission gate, so this is the audience_tier lane (§2.2),
        # not capability_required.
        CommandSpec(
            name="imagemod",
            kind=CommandKind.PREFIX,
            summary="Show the current image-moderation policy for this server.",
            route=PanelRef("image_moderation.policy"),
            audience_tier="manage_guild",
        ),
    ),
    panels=(
        # TIER 2 — read-only fields block over a provider; no buttons in v1
        # (mirrors karma's card, which also ships with zero actions today).
        PanelSpec(
            panel_id="image_moderation.policy",
            subsystem="image_moderation",
            title="🖼️ Image moderation",
            audience="invoker",
            body=(
                BlockSpec(
                    kind="fields",
                    provider=ProviderRef("image_moderation.policy"),
                ),
            ),
        ),
    ),
    settings=(
        # Every bool setting below MUST declare `activation=` (SettingSpec.
        # __post_init__, §4.4) — verified by execution; omitting it raises
        # ValueError.  OFF_UNTIL_OPT_IN matches server_logging.py's identical
        # off-by-default bool-setting shape.
        SettingSpec(
            name="enabled",
            value_type="bool",
            default=False,
            settings_key="image_moderation_enabled",
            capability_required=_CAP,
            hint="Master switch. Off by default — nothing is scanned or sent externally.",
            activation=Activation.OFF_UNTIL_OPT_IN,
        ),
        SettingSpec(
            name="sexual_enabled",
            value_type="bool",
            default=False,
            settings_key="image_moderation_sexual_enabled",
            capability_required=_CAP,
            activation=Activation.OFF_UNTIL_OPT_IN,
        ),
        SettingSpec(
            name="violence_enabled",
            value_type="bool",
            default=False,
            settings_key="image_moderation_violence_enabled",
            capability_required=_CAP,
            activation=Activation.OFF_UNTIL_OPT_IN,
        ),
        SettingSpec(
            name="harassment_enabled",
            value_type="bool",
            default=False,
            settings_key="image_moderation_harassment_enabled",
            capability_required=_CAP,
            activation=Activation.OFF_UNTIL_OPT_IN,
        ),
        SettingSpec(
            name="hate_enabled",
            value_type="bool",
            default=False,
            settings_key="image_moderation_hate_enabled",
            capability_required=_CAP,
            activation=Activation.OFF_UNTIL_OPT_IN,
        ),
        # G-5: bounds (50..100) become declarative min/max fields instead of
        # a hand-written _validate_threshold function.
        SettingSpec(
            name="threshold_percent",
            value_type="int",
            default=80,
            settings_key="image_moderation_threshold_percent",
            capability_required=_CAP,
            presets=(70, 80, 90),
            hint="Confidence percent a category must reach before acting.",
            # allowed_values / bounds: (50, 100) — G-5 target shape
        ),
        # G-2: shipped as CSV-of-ids str + hand-written validator; the target
        # shape is a real list-valued setting with kernel add/remove workflows.
        SettingSpec(
            name="exempt_roles",
            value_type="list[int]",
            default=(),
            settings_key="image_moderation_exempt_roles",
            capability_required=_CAP,
            hint="Roles whose members' images are never scanned.",
        ),
        SettingSpec(
            name="exempt_channels",
            value_type="list[int]",
            default=(),
            settings_key="image_moderation_exempt_channels",
            capability_required=_CAP,
            hint="Channels image moderation never scans.",
        ),
    ),
    events=(
        # cogs/image_moderation/listener.py:39,174-193 — advisory only;
        # confirmed zero real subscribers repo-wide.
        EventSpec(
            name="image_moderation.flagged",
            payload_schema=(
                FieldSpec("guild_id", "int"),
                FieldSpec("user_id", "int"),
                FieldSpec("category", "str"),
                FieldSpec("channel_id", "int"),
            ),
            owner_subsystem="image_moderation",
            observability_only=True,
        ),
    ),
    # stages=(  # G-A2 proposed field — not in SubsystemManifest today
    #     MessagePipelineStageSpec(
    #         stage_name="image_moderation",
    #         order=25,
    #         gate="setting:image_moderation_enabled AND any_category_enabled",
    #         handler=HandlerRef(
    #             "image_moderation.scan_and_act",
    #             justification=(
    #                 "external OpenAI classify call per image URL + "
    #                 "multi-bucket verdict evaluation + delete/warn "
    #                 "orchestration through moderation_service — real "
    #                 "domain logic, deliberate escape hatch (like "
    #                 "blackjack's game engine), only the REGISTRATION "
    #                 "is declarative"
    #             ),
    #         ),
    #     ),
    # ),
    stores=(),  # deliberately empty — settings ride the shared KV substrate
                # (SettingSpec.storage="kv" default); no subsystem-owned table
    help=HelpEntrySpec(
        summary="Automatically scans uploaded images (sexual/violence/harassment/hate) via OpenAI moderation.",
        examples=("!imagemod",),
    ),
)
```

#### Tier-3 dispositions

- **`ImageModerationStage` class + `cog_load`/`cog_unload` registration** (`cogs/image_moderation_cog.py:41-54,63-68,70-73`) — **grammar gap → G-A2** (new, proposed here): no primitive in §2 (nor in G-1..G-6) covers the internal `core.runtime.message_pipeline` ordered/short-circuiting stage registration; the class + lifecycle glue are pure boilerplate (4-line wrapper + two registration calls) with zero domain logic, and together form **one** registration capability, not three separate units (see the ledger correction above). Reuse target: automod/cleanup/counting/chain/xp all hand-write the identical shape (verified structurally identical to `automod_cog.py`'s twin stage, per that cog's own docstring cross-reference).
- **`process_message`/`_act`/`_emit`** (`cogs/image_moderation/listener.py:52-193`) — **deliberate escape hatch, not a gap.** Real domain logic: policy-gated exemption checks, a per-URL external-API classify loop, multi-bucket threshold evaluation, and delete+warn orchestration. G-A2 only declares the *wiring* (gate + handler pointer); the handler body legitimately stays code — same honest call the spike makes for blackjack's reaction-join listener and game engine (RESULTS.md: "stays tier 3 honestly").
- **`threshold_percent` setting's bounded validator** (`schemas.py:145-158`, bounds in `image_moderation_config.py:58-59`) — **grammar gap → reuse G-5** (declarative validator bounds): the 50–100 bound is currently a hand-written `_validate_threshold` function; G-5 makes it pure min/max data on the `SettingSpec`. Identical class to karma's `cooldown_seconds`/`daily_cap`.
- **`exempt_roles`/`exempt_channels` settings** (`schemas.py:159-182`) — **grammar gap → reuse G-2** (list-valued settings + add/remove workflows): shipped as a CSV-of-ids string with hand-written per-token validation; G-2's `list[int]` value shape + kernel add/remove workflow eliminates the validator entirely. Identical class to logging's `ignored_channels`/`ignored_users`.
- **Bool settings' `_validate_bool` guards** (`schemas.py:96-144`) — **not a tier-3 unit at all**, scored tier-1 as-written: pure `isinstance` type-safety with zero domain logic, the same pattern logging's own bool settings use and RESULTS.md scores 1/1. No disposition needed.

#### Fit numbers

| Metric | Value |
|---|---|
| Units total | 15 |
| Tier-1/2 count (as-written) | 11 |
| Fit % (as-written) | **73.3%** (11/15) |
| Tier-1/2 count (with amendments) | 14 |
| Fit % (with amendments) | **93.3%** (14/15) |

Amendments applied: **G-A2** (new — one message-pipeline-stage-registration capability spanning three code locations: the stage class, `cog_load`, `cog_unload`), **G-5** (threshold_percent bound), **G-2** (exempt_roles, exempt_channels — ×2 units). The single unit that stays tier-3 even with every amendment is `process_message`/`_act`/`_emit` — a deliberate escape hatch (external API orchestration + verdict logic), not a residual gap. This puts image_moderation in the "logging-shaped" (config-heavy, thin-handler) category the BRIEF hypothesizes most Lane A/D subsystems fall into, not the "blackjack-shaped" (44%) danger zone — its only real escape hatch is a single external-API classify-and-act handler, structurally identical to automod's.

(Note: the draft originally reported 19 units / 68.4% / 94.7%. The revision to 15/73.3%/93.3% comes from two corrections above: consolidating the triple-counted stage-registration glue and double-counted help surface into one unit each, and excluding the orphaned capability-tag row from the scored tally. The qualitative verdict — config-heavy subsystem, single genuine tier-3 escape hatch — is unchanged either way.)

#### Structural-gap flags

- **Permission/capability gates:** `!imagemod` uses a raw Discord-permission check (`perms_or_owner(manage_guild=True)`), the `audience_tier` lane of §2.2 — fully expressible, no gap. The settings surface uses the capability-string lane (`moderation.settings.configure`, borrowed) — also fully expressible. **Flag:** the registry's own `image_moderation.settings.configure` capability tag (subsystem_registry.py:566) is orphaned/unused — a documentation-accuracy issue, not a grammar gap (see the non-scored note above the ledger).
- **Setup/provisioning wizards:** absent (confirmed). No gap.
- **`wait_for` wizards:** absent (confirmed). No gap.
- **External API opt-in:** **present and the subsystem's defining danger zone** — OpenAI `omni-moderation-latest` image classification, off-by-default, fails open. The grammar (as written) has no explicit "external API call" primitive/flag at all — `HandlerRef.justification` documents *why* the escape hatch exists but doesn't structurally mark "this handler makes a real outbound network call to a third-party service" as queryable metadata. This is arguably a **cross-subsystem gap** (the `ai`/Lane-D subsystem and image_moderation both need it) rather than an image_moderation-local one — noted here, disposition deferred to whichever lane owns the `ai` subsystem's manifest (Lane D) since the shared primitive (if built) belongs with the provider abstraction, not duplicated per-consumer.
- **Audit/mutation seams:** compliant — no bypass. All destructive actions (delete + warn) route exclusively through `moderation_service`'s already-audited seam; image_moderation adds no second ladder and owns no `*_mutation.py`.
- **Destructive actions:** message deletion is destructive but has no interactive `PanelActionSpec` today (no button) — if a future manual "re-scan"/"delete now" button is ever added to the (currently nonexistent) panel, §2.6's `destructive=True ⇒ style="danger"` rule already covers it structurally; nothing to add now.
- **Lifecycle tasks / scheduled loops:** absent (confirmed). No gap.
- **Governance/cache behavior:** none — `load_policy` is called fresh per message (no caching layer, no TTL, no invalidation logic) — a per-message DB read is inherent to the pipeline-stage shape, not a distinct unit.

#### Reconsider / optimize

**MAP:** 15 real surface units — 1 command, 1 help unit (dropdown hook + entry data, one capability), 2 listener units (the stage-registration triad, the scan-and-act handler), 1 advisory event, 9 settings-kind rows (8 scalar SettingSpecs: 5 bool, 1 bounded-int, 2 list-of-ids; plus the schema container), 1 shared-KV store reference. No panel, binding, resource, game, or diagnostics units exist. (The registry's `image_moderation.settings.configure` capability tag is real but orphaned metadata — a documentation-drift flag, not a counted surface unit.)

**RECONSIDER:** **Keep + improve.** The v1 design (Q-0108) is sound — off-by-default, fail-open, single audited action seam, no second audit ladder, tight privacy scope (URL-only, no text/author) — but two concrete improvements surface from this audit: (1) promote the exempt-list settings from CSV-string to real list-valued settings (G-2) so operators get add/remove UI instead of hand-typing comma-separated ids; (2) give the subsystem a real interactive panel (today it's a bare embed with zero buttons) — at minimum a "test this policy against a sample URL" action and a link into the exempt-list editor, mirroring logging's panel-as-config-choreography pattern, which the message-pipeline-stage subsystems (automod, cleanup) largely lack too.

**SIMULATE:** the draft's original claim that the sketch "round-trips cleanly through `SubsystemManifest.__post_init__` ... using only already-existing §2 primitives" was **false as written** — instantiating any of the five bool `SettingSpec`s without `activation=` raises `ValueError: ... bool specs must consciously choose an activation posture (§4.4)` (verified by executing `tools/grammar_spike/spec.py` directly). Every existing worked manifest treats this as mandatory: karma.py:114 sets `Activation.ON_BY_DEFAULT`, server_logging.py:246/255 sets `ON_WHEN_BOUND`/`OFF_UNTIL_OPT_IN` for its two bool settings, and even blackjack.py — which has no bool setting at all — imports `Activation` solely to comment that its one int-typed setting needs none. Fixed above by adding `activation=Activation.OFF_UNTIL_OPT_IN` (matching server_logging's identical off-by-default bool shape) to all five settings; re-executing the corrected sketch confirms it now builds cleanly (no duplicate command/panel/setting tokens either) using only already-existing §2 primitives, **except** for the message-pipeline-stage registration, which needs the proposed `MessagePipelineStageSpec` (G-A2) — shown commented-out above since it isn't a real field on `SubsystemManifest` yet. Everything else — the panel, the 8 settings (2 upgraded to `list[int]`), the advisory event — simulates with zero new primitives.

**OPTIMIZE:** The optimal new-bot form keeps image_moderation as a **thin declarative shell around one real handler**: (a) full manifest-driven settings/panel/help (as sketched, activation postures included); (b) the `MessagePipelineStageSpec` (G-A2) registering the stage declaratively with a settings-derived `gate` so the kernel skips the handler call entirely when disabled (today's gate check is duplicated inline in `process_message` itself — with G-A2 the kernel does it before ever invoking the handler, saving the function-call+DB-read on the disabled-by-default common case); (c) the classify-and-act handler stays hand-written code, but its shape (policy fetch → exemption check → external classify loop → verdict → act) is close enough to automod's that a shared "auto-mod tier scan handler" helper could reduce duplication across automod/image_moderation — worth a light dependency note for whichever session builds the message-pipeline-stage family, not a redesign.

- **Dependency-layer guess:** **early governance** — after L0 (message-pipeline substrate must exist) and after `moderation`'s audited seam (this subsystem calls it directly) and the AI-provider adapter (Lane D) are built; before feature/community layers.
- **Production-grade done-definition:** a `parity/` golden asserting: (1) master switch off ⇒ zero classifier calls, zero deletions; (2) each per-category flag independently gates its bucket; (3) `threshold_percent` bound (50-100) is enforced at write time; (4) exempt role/channel short-circuits **before** any external call (not just before acting); (5) `ProviderUnavailableError`/network/malformed-response all fail open (image survives, warning logged); (6) a flagged image produces exactly **one** audit row (via `moderation_service`, no duplicate ladder) plus the advisory `image_moderation.flagged` event with the documented 4-field payload; (7) only the attachment URL — never message text or a second author-identifying field — is ever passed to the classifier (a privacy regression test, not just a behavior test).
- **Outperform-target status:** pending Lane F. Candidate ecosystem comparators to benchmark: Discord's own built-in AutoMod (no image/NSFW category as of training cutoff), and third-party NSFW/image-moderation bots/services (e.g. those built on Google Vision SafeSearch or AWS Rekognition moderation) — worth checking whether any mainstream general-purpose bot (MEE6/Carl-bot/Dyno/Wick) ships a comparable per-category image classifier at all, since this may be a genuine differentiator rather than a catch-up feature.
- **Owner-gated/blocked/external-dependency status:** **external dependency** — requires `OPENAI_API_KEY` to function at all (fails open/silently inert without it); this is a hosting-cost + third-party-ToS dependency the owner already accepted at Q-0108, not currently blocked or owner-gated further.

**Cross-lane dependency:** the classifier is a hard dependency on Lane D's `ai` subsystem's provider infrastructure — `core/runtime/ai/providers/openai_moderation.py` shares the `OPENAI_API_KEY` env var and the `ProviderUnavailableError` contract with the `ai` cog's own OpenAI provider (`core/runtime/ai/providers/openai_provider.py`, confirmed identical pattern) — image moderation is entirely non-functional without that Lane-D adapter existing first.

---

### security
_cogs: disbot/cogs/security_cog.py, disbot/cogs/security/schemas.py, disbot/cogs/security/__init__.py_

Verified against `disbot/services/security_service.py`, `disbot/services/security_config.py`,
`disbot/utils/settings_keys/security.py`, `disbot/utils/subsystem_registry.py:705-725`,
`docs/ownership.md:45,234-235`, `docs/owner/maintainer-question-router.md` Q-0111, the ground-truth
`command-surface.json` (one row: `security`, prefix, `manage_guild`, `cogs/security_cog.py:115`), and
the existing completion certificate `docs/planning/feature-completion/units/security.md`. The
pre-extracted scaffold's citations were all correct; line numbers below are re-verified against the
current file contents (a few schema line numbers shifted by 1-2 lines from the scaffold — corrected here).
**This pass additionally traced `disbot/services/channel_lifecycle_service.py` and
`disbot/services/lifecycle/contracts.py` (a first-pass claim about audit coverage there was wrong —
see the corrected "Destructive actions" flag below) and independently ran `pytest --collect-only`
against the three security test files (a completion-certificate test-count claim was stale — see
"Production-grade done-definition").**

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !security (status command) | command | disbot/cogs/security_cog.py:108 (decorator)/:115 (def, matches ground-truth lineno) | 1 | 1 | `route=PanelRef` to a pure read-model panel — kernel open-panel workflow, mirrors logging's `!logging status` (RESULTS.md), not karma's card (split from its provider below) |
| security.status panel (effective-policy embed as a PanelSpec) | panel | disbot/cogs/security_cog.py:57-106 | 1 | 1 | `PanelSpec` wrapping one body block, **no actions/selectors** — cog docstring states explicitly "security has no bespoke panel in v1" (security_cog.py:126) |
| _policy_embed (read-model provider: flags/thresholds/mention text from SecurityPolicy) | panel/provider | disbot/cogs/security_cog.py:57-106 | 2 | 2 | thin but real conditional-text assembly (🟢/⚫ flags, the lockdown-vs-alert-only sentence, alert-channel mention resolution) — same shape as logging's "status/routes providers" (RESULTS.md: tier 2/2, "read-model providers behind refs") |
| build_help_menu_view (help-menu direct-nav hook, reuses _policy_embed) | help/panel | disbot/cogs/security_cog.py:120-138 | 2 | 1 | as-written: bespoke glue function; with amendments: once `panel_id` + `entry_points`/`parent_hub` are declared, help-menu → default-panel nav is a generated kernel workflow needing zero bespoke code — identical conclusion to `admin_cog`'s equivalent hook |
| inline help text (`help=` kwarg on the command decorator) | help | disbot/cogs/security_cog.py:110 | 1 | 1 | trivial string declaration today. Not a security-specific gap: `services/help_catalogue.py` (read, confirmed) is a read-only Help *inventory* built over the registries, not a per-subsystem rich-text store — it has no summary/examples text for karma or logging either (grepped: zero subsystem-specific entries for any of the three). The richer `HelpEntrySpec(summary=..., examples=(...))` shape only exists in the spike's own illustrative worked manifests (`tools/grammar_spike/manifests/karma.py`/`server_logging.py`/`blackjack.py`) — a proposed addition there too, not something karma/logging ship today. Security's own sketch below adds the identical shape, so this is uniform across all four subsystems, not an asymmetry |
| on_member_join (gateway listener → dispatches to security_service.handle_member_join) | listener | disbot/cogs/security_cog.py:46-53 | 3 | 3 | G-1 declares the *wiring* (gate + dispatch) but the dispatched handler is genuine bespoke fail-open orchestration of two independent detectors — stays tier-3 honestly, same call the spike made for blackjack's reaction-join listener ("real lobby logic — stays tier 3 honestly"), **not** karma's thin fetch-and-forward |
| cog_load → register_schemas() (SubsystemSchema registration hook) | listener/setup-hook | disbot/cogs/security_cog.py:39-42 | 1 | 1 | zero domain logic — boilerplate the manifest kernel would auto-run at import from the declared `settings` tuple alone; equivalent to karma's "enabled setting → kernel settings workflow" |
| security.enabled (master switch) | setting | disbot/cogs/security/schemas.py:95 | 1 | 1 | plain bool; needs an `Activation` posture per §2.5's `__post_init__` rule — recommend `OFF_UNTIL_OPT_IN` since it gates automated member-affecting actions incl. kicks (design suggestion, not a shipped fact) |
| security.alert_channel | setting | disbot/cogs/security/schemas.py:108 | 1 | 1 | plain str channel-id pointer, validated by `_validate_id`. **Optimize note:** should be a `BindingSpec(kind="channel")`, not a scalar setting — see §9 |
| security.raid_enabled | setting | disbot/cogs/security/schemas.py:122 | 1 | 1 | plain bool |
| security.raid_join_count | setting | disbot/cogs/security/schemas.py:131 | 2 | 1 | bounded-int validator (`_int_validator(MIN_RAID_JOIN_COUNT, MAX_RAID_JOIN_COUNT)`) is a registered `HandlerRef` as-specced; **G-5** makes the bounds declarative data |
| security.raid_window_seconds | setting | disbot/cogs/security/schemas.py:143 | 2 | 1 | same G-5 class |
| security.raid_slowmode_channel | setting | disbot/cogs/security/schemas.py:155 | 1 | 1 | plain str channel-id pointer — same BindingSpec optimize note as `alert_channel` |
| security.raid_slowmode_seconds | setting | disbot/cogs/security/schemas.py:168 | 2 | 1 | G-5 class |
| security.raid_lockdown_seconds | setting | disbot/cogs/security/schemas.py:180 | 2 | 1 | G-5 class |
| security.age_enabled | setting | disbot/cogs/security/schemas.py:193 | 1 | 1 | plain bool |
| security.age_min_days | setting | disbot/cogs/security/schemas.py:202 | 2 | 1 | G-5 class |
| security.age_action | setting | disbot/cogs/security/schemas.py:214 | 1 | 1 | `allowed_values=AGE_ACTIONS` is native §2.5 enum support; the shipped `validator=_validate_action` HandlerRef is redundant with `allowed_values` and is droppable at port — mirrors logging's `event_routing` enum, which RESULTS.md scores tier 1/1 despite an equivalent check existing in spirit |
| SUBSYSTEMS["security"] registry entry (display/emoji/tags/category/visibility_tier/entry_points/parent_hub/ui_priority/capabilities/related_subsystems) | setting (registry) | disbot/utils/subsystem_registry.py:705-725 | 1 | 1 | pure metadata → `SubsystemManifest` root fields (`key`/`display_name`/`emoji`/`category`/`visibility_tier`/`capabilities`/`parent_hub`/`ui_priority`); one capability only, `security.settings.configure` |
| security.raid_detected | event | disbot/services/security_service.py:45,357 | 1 | 1 | `EventSpec` declaration, **`observability_only=True`** — verified **zero real subscribers**: grepped the literal string and `EVT_RAID_DETECTED` repo-wide, the only hits outside `security_service.py` are `core/events_catalogue.py`'s name-catalogue (not a subscription). This is a *deliberately* advisory event per `docs/ownership.md:234` ("Advisory observability event... Subscriber failure logged + swallowed"), not a dead/buggy declaration — same posture `karma.granted` uses, just with no subscriber wired yet |
| security.account_flagged | event | disbot/services/security_service.py:46,401 | 1 | 1 | same verified-no-subscriber / `observability_only=True` disposition as the row above (`docs/ownership.md:235`) |
| _handle_raid + RaidTracker (sliding-window join-rate detection + per-guild lockdown dedup) | listener-handler | disbot/services/security_service.py:56-88,300-362 | 3 | 3 | **deliberate escape hatch** — a genuine stateful detection algorithm + dedup state machine, same class as blackjack's "game engine (rules)": "pure-function escape hatch BY DESIGN — the grammar must never express game rules" (RESULTS.md); here it's "never express detection rules" |
| raid staff-alert render + post (_raid_alert_embed + _post_alert) | handler | disbot/services/security_service.py:162-183,243-262 | 3 | 2 | **G-3** `AnnouncementRouteSpec` (event → template → bound `alert_channel` destination) — identical shape to logging's "log-embed rendering handlers" (RESULTS.md: "bespoke embed-format code per event class... G-3 makes the recurring shape data") |
| raid lockdown slowmode apply/restore + one-shot lift/clear timers (_apply_slowmode, _lift_lockdown, _hold_then_lift, _clear_lock_after) | scheduled-callback | disbot/services/security_service.py:186-241 | 3 | 2 (NEW **G-A11**) | **Verified precisely per the task's ask:** `_hold_then_lift`/`_clear_lock_after` are `await asyncio.sleep(delay)` followed by a `finally:` cleanup, fired via `asyncio.ensure_future(...)` at security_service.py:331-338/352-354 — a **one-shot delayed callback carrying captured runtime state** (guild_id, channel, prior slowmode value), fired once per lockdown episode. Confirmed **NOT** a `@tasks.loop`/recurring scheduled loop: grepped `tasks.loop` and `wait_for(` across every security file — zero hits. `ManagedTaskSpec.trigger` (`interval:<s>|cron:<expr>|event:<name>`) is built for a *persistent, repeatedly-firing named task* registered once at boot — it has no vocabulary for "fire exactly once, N seconds from now, closing over this call's local state," so it does not fit even loosely. This is a genuine, unfilled grammar gap → **propose G-A11** (disposition in §5/§9). **Separately — this is an unaudited real Discord mutation, and NOT the repo convention this row's disposition originally claimed: see the corrected "Destructive actions" flag below.** |
| _handle_account_age + account_age_days/is_young_account (age computation + alert-or-kick decision) | listener-handler | disbot/services/security_service.py:106-138,365-407 | 3 | 3 | **deliberate escape hatch** — genuine business-rule computation (age math + action branch); correctly delegates its one mutation to `moderation_service.kick` rather than opening a parallel path (see mutation row below). **Correction:** `is_young_account` (lines 126-138) is not actually invoked anywhere in the production join path — `_handle_account_age` recomputes the threshold check inline (`age is None or age >= policy.age_min_days`) rather than calling it; grep confirms `is_young_account`'s only callers are in `test_security_service.py`. It's a harmless, tested-but-unused duplicate helper, not a second live decision path — doesn't change the tier call but shouldn't be described as part of "the decision" |
| age-flag staff-alert render + post (_age_alert_embed + _post_alert) | handler | disbot/services/security_service.py:162-183,265-283 | 3 | 2 | **G-3** `AnnouncementRouteSpec`, same shape as the raid-alert row above |
| mutation: account-age kick → `moderation_service.kick` (audited seam; security owns no `*_mutation.py` of its own) | mutation | disbot/services/security_service.py:375-393 → disbot/services/moderation_service.py:484 (kick), :213 (emit_audit_action) | 2 | 2 | declared cross-subsystem `HandlerRef` delegation to an already-audited seam — **correct architecture** (`docs/ownership.md:45`: "the one consequential action — a kick — routes through `services/moderation_service.py`... so moderation's escalation/audit stays the one authority; security opens no parallel action/audit path"). Zero duplicate audit path, zero gap |

**Unit kinds present:** command, panel, setting, listener, event, help, mutation (delegated).
**Unit kinds explicitly absent** (verified, not silently omitted):
- **panel actions/selectors** — none; the cog's own docstring says v1 has no bespoke interactive panel (security_cog.py:126 — *corrected: the earlier citation of line 15 was wrong; line 15 is the module docstring's DECLINED-tiers sentence, not a panel claim*). Config lives entirely in the generic `!settings → Security` widget.
- **store** — no dedicated DB table; grepped `disbot/migrations/` for "security" — zero hits. All 11 settings are scalar guild-KV (legacy `settings` table), confirmed by both `schemas.py`'s module docstring ("no migration") and `security_config.py`'s docstring.
- **bindings / resources** — none declared today (the two channel pointers are plain `str` `SettingSpec`s, not `BindingSpec`/`ResourceRequirement` — flagged as an Optimize recommendation in §9, not a grammar-fit gap since the primitive already exists in §2).
- **game** — not applicable; no session/leaderboard facet.
- **diagnostics** — none; grepped `diagnostic_cog.py`/`services/diagnostic*.py` for "security" — zero hits, no `DiagnosticProviderSpec`-worthy registration exists.
- **scheduled loop (`@tasks.loop`)** — confirmed **absent** (see the one-shot-timer row above); this is a structurally different primitive from the recurring loops seen elsewhere in Lane A (`role_cog.role_check`, `role_grants_cog._sweep_loop` — both confirmed `@tasks.loop`-decorated by direct grep).
- **`wait_for` wizard** — confirmed absent; grepped `wait_for(` across every security file — zero hits.
- **voice** — not applicable.

**Structural-pattern flags:**
- **Gateway listener** — present (`on_member_join`, security_cog.py:46; G-1 covers the wiring, handler stays tier-3 — see ledger).
- **Message-pipeline stage** — absent; security does not register a `message_pipeline` stage (unlike automod/image_moderation/cleanup in this lane) — it only reacts to the member-join gateway event, never per-message content.
- **`wait_for` wizard** — confirmed absent (see above).
- **Scheduled loop** — confirmed absent; the lockdown-restore/lock-clear timers are one-shot `asyncio.sleep`+`ensure_future` callbacks, **not** a `@tasks.loop` (see the dedicated ledger row and the new G-A11 proposal — this distinction is exactly what the task asked to verify precisely).
- **Voice** — absent.
- **Governance/cache behavior** — `RaidTracker` (a per-guild `deque` sliding window) and `_locked_guilds` (a per-guild dedup set) are **process-local, intentionally non-persisted** module-level state (ADR-002: "runtime state is not restart-safe by design"; `security_service.py:23-26`). No `StoreSpec` applies or should apply — these are deliberately ephemeral, not a missing store. Worth flagging structurally only so a future manifest author doesn't reach for `StoreSpec` out of habit: the manifest should declare `stores=()` with a comment, exactly as `logging.py`'s manifest already does ("logging owns no tables — it writes config via the lanes").

#### Manifest sketch

```python
"""Security — join-screening (Lane A audit sketch, verified 2026-07-02).

Source of truth:
    cogs/security_cog.py            — !security (108-118), on_member_join (46-53),
                                       cog_load/register_schemas (39-42),
                                       build_help_menu_view (120-138)
    cogs/security/schemas.py         — 11 SettingSpecs (95-227)
    services/security_service.py     — RaidTracker + account-age detection,
                                       EVT_RAID_DETECTED/EVT_ACCOUNT_FLAGGED (45-46),
                                       one-shot lockdown timers (216-241)
    services/security_config.py      — SecurityPolicy read model + guardrail clamps
    utils/settings_keys/security.py  — key strings
    utils/subsystem_registry.py:705  — registry metadata

Tier verdict (measured): 27 units, 21/27 (78%) tier-1/2 as-written, 24/27 (89%)
with amendments. The three units that stay tier-3 even with every proposed
amendment are the two detection algorithms (RaidTracker + age math) and the
join-listener's dispatched orchestration — deliberate escape hatches, same
class as blackjack's rules engine. Proposes ONE new amendment: G-A11
(one-shot deferred callback — the lockdown-restore/lock-clear timers are NOT
a recurring @tasks.loop and don't fit ManagedTaskSpec's interval/cron/event
trigger vocabulary).
"""

from __future__ import annotations

from tools.grammar_spike.spec import (
    Activation,
    BlockSpec,
    CommandKind,
    CommandSpec,
    EventSpec,
    FieldSpec,
    GatewayListenerSpec,
    HandlerRef,
    HelpEntrySpec,
    PanelRef,
    PanelSpec,
    ProviderRef,
    SettingSpec,
    SubsystemManifest,
)

_CAP = "security.settings.configure"

SECURITY_MANIFEST = SubsystemManifest(
    key="security",
    display_name="Server Security",
    description="Raid detection + account-age screening on member join.",
    emoji="🛡️",
    category="moderation",
    visibility_tier="administrator",
    capabilities=(_CAP,),
    dependencies=(),  # kick delegates to moderation_service at call time, not a
                       # declared manifest dependency edge in the spike grammar
    parent_hub="moderation",  # [A] subsystem_registry.py:722
    commands=(
        # cogs/security_cog.py:108 — @commands.command(name="security", ...)
        # domain-lane gate (perms_or_owner(manage_guild=True) is a raw Discord
        # permission, not a subsystem capability) -> audience_tier, per the
        # CommandSpec.__post_init__ two-lane exclusivity rule (§2.2).
        CommandSpec(
            name="security",
            kind=CommandKind.PREFIX,
            summary="Show the current server-security policy (raid + account-age).",
            route=PanelRef("security.status"),
            audience_tier="administrator",
        ),
    ),
    panels=(
        # TIER 2: FieldsBlock/TextBlock over a real (thin-but-computed) provider.
        # No actions/selectors — v1 ships no bespoke panel (security_cog.py:126).
        PanelSpec(
            panel_id="security.status",
            subsystem="security",
            title="🛡️ Server security",
            audience="invoker",
            body=(
                BlockSpec(
                    kind="fields",
                    provider=ProviderRef("security.policy_summary"),
                ),
            ),
        ),
    ),
    settings=(
        SettingSpec(
            name="enabled",
            value_type="bool",
            default=False,
            settings_key="security_enabled",
            capability_required=_CAP,
            hint="Master switch — neither tier runs regardless of its own toggle.",
            activation=Activation.OFF_UNTIL_OPT_IN,  # [A] — gates automated kicks
        ),
        # alert_channel / raid_slowmode_channel are shipped as scalar str
        # settings (schemas.py:108,155). OPTIMIZE (see §9): these are exactly
        # the BindingSpec(kind="channel") shape logging already uses — shown
        # here AS SHIPPED for tier-fit accuracy, not as the recommended form.
        SettingSpec(
            name="alert_channel",
            value_type="str",
            default="",
            settings_key="security_alert_channel",
            capability_required=_CAP,
            input_hint="channel",
            hint="Staff alert destination. Empty = detection runs silently.",
        ),
        SettingSpec(
            name="raid_enabled",
            value_type="bool",
            default=False,
            settings_key="security_raid_enabled",
            capability_required=_CAP,
            # CORRECTED: shipped default is False (DEFAULT_RAID_ENABLED, a fresh
            # guild is unaffected); on_by_default means "active out of the box"
            # per design-spec §4.4, which contradicts default=False. Use the
            # same off-until-opt-in posture as the master switch instead.
            activation=Activation.OFF_UNTIL_OPT_IN,
        ),
        SettingSpec(
            name="raid_join_count",
            value_type="int",
            default=10,
            settings_key="security_raid_join_count",
            capability_required=_CAP,
            # G-5: bounds (2-100) are a registered HandlerRef validator today;
            # with G-5 they'd be declarative `bounds=(2, 100)` data instead.
            validator=HandlerRef("security.validate_raid_join_count"),
        ),
        SettingSpec(
            name="raid_window_seconds",
            value_type="int",
            default=60,
            settings_key="security_raid_window_seconds",
            capability_required=_CAP,
            validator=HandlerRef("security.validate_raid_window"),
        ),
        SettingSpec(
            name="raid_slowmode_channel",
            value_type="str",
            default="",
            settings_key="security_raid_slowmode_channel",
            capability_required=_CAP,
            input_hint="channel",
        ),
        SettingSpec(
            name="raid_slowmode_seconds",
            value_type="int",
            default=10,
            settings_key="security_raid_slowmode_seconds",
            capability_required=_CAP,
            validator=HandlerRef("security.validate_slowmode_seconds"),
        ),
        SettingSpec(
            name="raid_lockdown_seconds",
            value_type="int",
            default=300,
            settings_key="security_raid_lockdown_seconds",
            capability_required=_CAP,
            validator=HandlerRef("security.validate_lockdown_seconds"),
        ),
        SettingSpec(
            name="age_enabled",
            value_type="bool",
            default=False,
            settings_key="security_age_enabled",
            capability_required=_CAP,
            # CORRECTED: same fix as raid_enabled above — default=False must
            # pair with OFF_UNTIL_OPT_IN, not ON_BY_DEFAULT.
            activation=Activation.OFF_UNTIL_OPT_IN,
        ),
        SettingSpec(
            name="age_min_days",
            value_type="int",
            default=7,
            settings_key="security_age_min_days",
            capability_required=_CAP,
            validator=HandlerRef("security.validate_age_min_days"),
        ),
        SettingSpec(
            name="age_action",
            value_type="str",
            default="alert",
            settings_key="security_age_action",
            capability_required=_CAP,
            allowed_values=("alert", "kick"),  # native §2.5 enum — no HandlerRef
            # needed; the shipped `_validate_action` HandlerRef is redundant.
        ),
    ),
    events=(
        # services/security_service.py:45,357 — zero real subscribers (verified
        # by repo-wide grep) => the CORRECT declarative form is
        # observability_only=True, not a missing-subscriber bug.
        EventSpec(
            name="security.raid_detected",
            payload_schema=(
                FieldSpec("guild_id", "int"),
                FieldSpec("user_id", "int"),
                FieldSpec("join_count", "int"),
            ),
            owner_subsystem="security",
            observability_only=True,
        ),
        EventSpec(
            name="security.account_flagged",
            payload_schema=(
                FieldSpec("guild_id", "int"),
                FieldSpec("user_id", "int"),
                FieldSpec("age_days", "float"),
                FieldSpec("action", "str"),
            ),
            owner_subsystem="security",
            observability_only=True,
        ),
    ),
    gateway_listeners=(
        # cogs/security_cog.py:46 — on_member_join. G-1 declares the wiring;
        # the dispatched handler stays a NAMED, honest tier-3 escape hatch
        # (real fail-open orchestration of 2 detectors), unlike karma's thin
        # fetch-and-forward — contrast noted explicitly in the ledger.
        GatewayListenerSpec(
            gateway_event="on_member_join",
            handler=HandlerRef(
                "security.handle_member_join",
                justification=(
                    "fail-open orchestration of raid-detection + account-age "
                    "tiers; real domain logic, not a thin forward (cf. G-1's "
                    "karma precedent)"
                ),
            ),
            gate="setting:security_enabled",
        ),
    ),
    stores=(),  # security owns no tables — process-local detector state only
                # (RaidTracker + _locked_guilds), deliberately non-persisted
                # per ADR-002; declared empty on purpose, mirrors logging.py.
    help=HelpEntrySpec(
        summary="Automated join screening: raid detection + account-age filter.",
        examples=("!security",),
    ),
)

# ---------------------------------------------------------------------------
# G-3 AnnouncementRouteSpec candidates (proposed family, no concrete dataclass
# in spec.py yet — same status G-1 had before it was promoted). If/when G-3
# lands, these two staff-alert postings become declarative:
#   AnnouncementRouteSpec(event="security.raid_detected",
#                         template="security.raid_alert",
#                         destination_binding="alert_channel")
#   AnnouncementRouteSpec(event="security.account_flagged",
#                         template="security.age_alert",
#                         destination_binding="alert_channel")
# Until then both stay HandlerRef-backed tier-3 (_raid_alert_embed/_post_alert,
# _age_alert_embed/_post_alert — security_service.py:162-183,243-283).
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# G-A11 PROPOSED (NEW — no dataclass in spec.py; illustrative shape only).
# Covers the one-shot lockdown-restore / lock-clear timers
# (security_service.py:216-241), verified as asyncio.sleep + ensure_future,
# NOT a @tasks.loop. ManagedTaskSpec's trigger vocabulary
# (interval:<s>|cron:<expr>|event:<name>) has no slot for "fire once, N
# seconds after THIS call, closing over THIS call's captured state" — a
# persistent named task is the wrong shape for a per-invocation deferred
# action. Sketch of the missing primitive:
#
# @dataclass(frozen=True)
# class DeferredActionSpec:
#     name: str                     # "<subsystem>:<purpose>", like ManagedTaskSpec
#     delay_source: str             # "setting:<key>" | literal seconds
#     handler: HandlerRef           # closes over caller-supplied context at
#                                   # schedule time (guild_id, channel, prior
#                                   # value, ...) — NOT re-resolved at fire time
#     cancel_on: str = ""           # e.g. "guild_leave" — best-effort cleanup
#
# security's two call sites would become:
#   DeferredActionSpec(name="security:lockdown_restore",
#                       delay_source="setting:security_raid_lockdown_seconds",
#                       handler=HandlerRef("security.lift_lockdown", ...))
#   DeferredActionSpec(name="security:lock_clear",
#                       delay_source="setting:security_raid_window_seconds",
#                       handler=HandlerRef("security.clear_lock", ...))
# ---------------------------------------------------------------------------
```

#### Tier-3 dispositions

- **on_member_join → handle_member_join dispatch** (security_cog.py:46-53) — **G-1** covers the *wiring* (gateway event + settings gate); the dispatched orchestration itself is a **deliberate escape hatch** (real fail-open composition of two independent detectors, not a thin forward) — reasoning: contrast with karma's react-to-thank (tier-2 with G-1, "thin fetch-and-forward") vs. blackjack's reaction-join listener (stays tier-3 even with G-1, "real lobby logic"); security's handler is squarely the latter shape.
- **_handle_raid + RaidTracker** (security_service.py:56-88,300-362) — **deliberate escape hatch**. A genuine sliding-window detection algorithm with per-guild dedup state — the grammar should never try to express detection rules as data, exactly the same reasoning the spike gave for blackjack's game engine ("pure-function escape hatch BY DESIGN").
- **raid staff-alert render + post** (security_service.py:162-183,243-262) — **G-3** (reuse). Textbook `AnnouncementRouteSpec` shape: an event fires, gets formatted from a template, and is delivered to a bound destination channel — identical to logging's per-event embed-formatting handlers that G-3 already targets.
- **raid lockdown slowmode apply/restore + one-shot timers** (security_service.py:186-241) — **NEW G-A11** (grammar gap, not an escape hatch for the *scheduling* shape). The one-shot-delayed-callback-with-captured-state pattern is generic and repeatable (temp bans/mutes/holds across subsystems could reuse it) but no §2 primitive covers it — see justification above and the sketch in the manifest block. The actual restore action (`channel.edit(slowmode_delay=...)`) stays a thin `HandlerRef` even with G-A11 — only the *scheduling* becomes declarative. **This action is also currently unaudited — see "Destructive actions" below; that's an independent audit-hygiene gap, not part of the G-A11 grammar-fit finding.**
- **_handle_account_age + account_age_days/is_young_account** (security_service.py:106-138,365-407) — **deliberate escape hatch**. Genuine business-rule computation (age math + alert-vs-kick branch); correctly delegates its one mutation to `moderation_service.kick` instead of opening a parallel path, so there is no *additional* gap here beyond the detection logic itself staying code. (`is_young_account` is unused in this path in production — see the ledger row's correction.)
- **age-flag staff-alert render + post** (security_service.py:162-183,265-283) — **G-3** (reuse), same disposition as the raid alert.

#### Fit numbers

| Metric | Value |
|---|---|
| Units total | 27 |
| Tier-1/2 count (as-written) | 21 |
| Fit % (as-written) | **78%** |
| Tier-1/2 count (with amendments) | 24 |
| Fit % (with amendments) | **89%** |
| Amendments applied | G-1 (on_member_join wiring only — handler stays tier-3), G-3 (×2 alert postings), G-5 (×5 bounded-int settings), **G-A11 NEW** (×1 lockdown-timer row) |
| Remaining tier-3 (deliberate escape hatches, not gaps) | 3 — the two detection algorithms + the dispatched join-orchestration |

This lands security's as-written fit at **78%**, just under both karma (80%) and logging (79%) — not "between" them, contrary to how an earlier draft of this section framed it. With amendments, security reaches **89%**, which genuinely does sit between karma (87%) and logging (97%). Either way this is squarely consistent with PARTITION.md's "Medium (moderation/CRUD, capability-gated)" difficulty call for Lane A. The one genuinely new structural finding is **G-A11**: none of karma/logging/blackjack exercised a one-shot deferred callback, so this is new evidence, not a repeat of an already-known gap.

#### Structural-gap flags

- **Permission/capability gates** — security cleanly uses BOTH lanes correctly: the status command is domain-lane (`audience_tier="administrator"` via `perms_or_owner(manage_guild=True)`, a raw Discord permission, not a subsystem capability — and "administrator" is the shipped visibility-tier vocabulary's actual term, `utils/visibility_rules.py:21` / design-spec §2.2), while every `SettingSpec` is config-lane (`capability_required="security.settings.configure"`). No amendment needed — this is exactly what §2.2's two-lane exclusivity model already expresses.
- **Setup/provisioning wizards** — absent. No `wait_for`-based wizard, no dedicated Setup step (per the completion certificate: "no dedicated wizard step (defaults-off; tuned via `!settings`)" — `docs/planning/feature-completion/units/security.md:42`). Grammar doesn't need to express one here.
- **`wait_for` wizards** — confirmed absent by grep across every security file.
- **External API opt-ins** — none. Explicitly zero external calls (module docstring, security_service.py:1-27: "this service makes **no external calls** and stores no PII") — the two DECLINED tiers (alt-detection/VPN blocking, Q-0111) are exactly the tiers that *would* need external calls, and they own no code (grepped for alt-detection/VPN/proxy-blocking references — only docstring mentions, zero implementation). The grammar doesn't need an "external API" primitive for this subsystem; it needs the DECLINED-tier boundary to stay enforced (see Optimize §8, item 4).
- **Audit/mutation seams** — the one destructive *member-removal* action (an account-age kick) is correctly routed through `moderation_service.kick`'s already-audited seam; security opens **zero** parallel mutation/audit paths for that action (`docs/ownership.md:45`, verified by grep — no `emit_audit_action` call inside `security_service.py`/`security_cog.py`). This is the exemplar pattern the grammar should hold up for other thin governance subsystems: no bespoke `*_mutation.py`, just a declared cross-subsystem `HandlerRef`. **This does not extend to the raid-lockdown slowmode edit — see "Destructive actions" immediately below, which corrects an earlier claim that the slowmode gap matched a repo-wide convention.**
- **Destructive actions** — the kick is destructive; gated correctly (see above). **CORRECTED:** the raid-lockdown slowmode edit is a real, unaudited Discord side effect, and it is *not* following a repo-wide convention — `channel_cog.py`'s own `!slowmode` command (`set_slowmode`, channel_cog.py:606) routes through `ChannelLifecycleService().apply(operation="set_slowmode", ...)` (services/channel_lifecycle_service.py:159-258), which unconditionally calls `emit_lifecycle_audit()` at the end of `apply()` (line 228) — and `emit_lifecycle_audit` (services/lifecycle/contracts.py:125-143) is a thin wrapper around `emit_audit_action` (imported at contracts.py:32, called at :143). So the *identical* Discord operation (`channel.edit(slowmode_delay=...)`) is already audited elsewhere in this codebase. Security's `_apply_slowmode`/`_lift_lockdown` (security_service.py:186-213) call `channel.edit()` directly, bypassing an audited seam that already exists for exactly this shape of mutation. This is a genuine, fixable audit-hygiene gap specific to security, not a shared convention — see Optimize item 5.
- **Lifecycle tasks/scheduled loops** — **this is the flag the task asked to verify precisely.** Security has **no** `@tasks.loop`/recurring scheduled loop anywhere (confirmed absent by grep, unlike `role_cog.role_check`/`role_grants_cog._sweep_loop` elsewhere in this same lane — both confirmed `@tasks.loop`-decorated). What it *does* have is a **one-shot delayed callback** (`_hold_then_lift`/`_clear_lock_after`, `asyncio.sleep` + `asyncio.ensure_future`, fired once per lockdown episode, carrying captured runtime state). This is a **structurally different primitive** from a recurring loop, and `ManagedTaskSpec` (built for `interval:<s>|cron:<expr>|event:<name>` — all persistent/repeating triggers) does not fit it even loosely. **New primitive needed → G-A11** (proposed above).
- **Governance/cache behavior** — `RaidTracker` + `_locked_guilds` are process-local, intentionally non-persisted (ADR-002) — no `StoreSpec` should apply; flagged only so a future manifest author declares `stores=()` explicitly (as `logging.py` does) rather than omitting the field and leaving the reader to wonder if a store was missed.

#### Reconsider / optimize

**MAP** — 27 units: 1 command, 1 setup-hook, 1 read-only panel, 1 provider, 1 help-nav hook, 1 inline help string, 1 gateway listener, 11 settings, 1 registry entry, 2 advisory events, 2 detection algorithms (raid/age), 2 alert-posting handlers, 1 lockdown-timer mechanism, 1 delegated mutation (= 27). A tightly-scoped, well-isolated subsystem — no PII, no external calls, fail-open throughout, single delegated write path (plus one unaudited-but-real side effect — the slowmode edit, see above).

**RECONSIDER verdict: KEEP + IMPROVE.** The two owner-approved tiers (Q-0111) are sound and already close to best-in-class shape for a lightweight join-screening layer — the existing completion certificate (`docs/planning/feature-completion/units/security.md`) independently corroborates this: defaults-off, guardrail-clamped, fully fail-open, zero duplicate audit path for the kick. **Correction:** the certificate's "~32 passing unit tests" figure is stale — running `pytest --collect-only` against `test_security_service.py` (12 tests) + `test_security_config.py` (6 tests) + `test_security_schemas.py` (9 tests) collects **27** tests today, not 32; the certificate's own 15+8+9 breakdown doesn't match the current files. Five concrete improvements, none architecturally risky:
1. **Convert `alert_channel`/`raid_slowmode_channel` from scalar `str` `SettingSpec`s to `BindingSpec`+`ResourceRequirement`** (matching logging's pattern exactly) — gives operators the "create channel" quick-provision UX logging already has, and moves two settings into the primitive that already exists for exactly this shape (zero grammar-fit cost, pure quality-of-life win).
2. **Wire at least one real subscriber to the two advisory events** — `server_logging.py` (Lane D) is the natural home, the same audit-fanout pattern already used for `moderation.action_taken`/`karma.granted`. Today these events are declared, correctly marked advisory, but genuinely unconsumed — a "security events" feed in the audit/logging dashboard is a cheap, real win, not just closing an "unverified" question.
3. **Implement the documented-but-unbuilt `quarantine` (role-isolation) `age_action` value** — `security_config.py`'s own comment calls this "the documented phase-2 value — not wired in v1," and Q-0111's decision text literally says "Reject/**quarantine**" for tier 2. A role-based hold is materially less disruptive than a kick and matches the original owner framing.
4. **Flag the lockdown-restore timer's restart-unsafety explicitly in the redesign** — if the bot restarts mid-lockdown, slowmode never auto-restores (process-local `asyncio.ensure_future`, no persisted deadline). Given lockdowns default to 300s and restarts are rare this is a low-severity, known-and-accepted risk today; the redesign should either persist the lockdown-expiry deadline for a boot-time sweep, or explicitly re-accept the risk in writing (don't let it become an *implicit* gap again).
5. **NEW — route the raid-lockdown slowmode edit through the already-audited `ChannelLifecycleService.apply(operation="set_slowmode", ...)` seam instead of a direct `channel.edit()` call.** `channel_cog`'s own `!slowmode` command already uses exactly this seam for the identical Discord mutation (services/channel_lifecycle_service.py:159-258,430-433), which emits `audit.action_recorded` via `emit_lifecycle_audit`/`emit_audit_action` for free. Today `_apply_slowmode`/`_lift_lockdown` bypass it, so a raid lockdown's slowmode changes are the one real Discord mutation in this subsystem that leaves no audit trail at all — an easy, low-risk fix (call the existing service instead of `channel.edit()` directly) that also folds naturally into the G-A11 `DeferredActionSpec.handler` once that primitive lands.

**Optimal new-bot form:** keep the two-tier shape and the audited-seam kick delegation as the exemplar pattern for lightweight governance subsystems (no bespoke mutation module — just a cross-subsystem `HandlerRef` into an already-audited seam), and extend that same audited-seam principle to the slowmode edit (item 5 above) rather than leaving it as a second, parallel, unaudited path. Express the settings surface fully declaratively via `SettingSpec`+`BindingSpec`+`ResourceRequirement`+G-5 (validator bounds). Express the join listener via `G-1 GatewayListenerSpec` with a thin gate, keeping the two detection algorithms + the join-orchestration as an explicit, *named* tier-3 "detection engine" module (mirroring blackjack's rules engine) so the escape hatch is intentional and visible in the manifest, not accidental. Express both staff-alert postings via `G-3 AnnouncementRouteSpec` once it lands. Adopt the new `G-A11 DeferredActionSpec` for the one-shot lockdown-restore/lock-clear timers so the *scheduling* is declared and audit-visible — today an untracked `asyncio.ensure_future` is exactly the kind of thing that silently disappears on a refactor (the "friction → guard" ethos this whole audit runs on).

**Dependency-layer guess:** **early governance** — depends on the core settings/panel kernel (L0), the EventBus, channel-resource resolution, `moderation_service.kick`, and (per item 5) `ChannelLifecycleService`/its audit companion. It should land right after moderation is stood up, alongside automod/welcome, as part of the "join-time screening cluster" (all three react to `on_member_join`).

**Production-grade done-definition:** matches the existing rubric in `docs/planning/feature-completion/units/security.md` — **27** passing unit tests across `test_security_service.py`/`test_security_config.py`/`test_security_schemas.py` (window mechanics, age math, raid dedup, the lock-clear regression, alert-only vs kick, fail-open, guardrail clamp/coerce, capability gating) — verified by direct `pytest --collect-only` (the certificate's own "~32" figure is stale and should be corrected there too) — **plus** its two open punch items (a live `/verify-bot` walkthrough simulating a join burst + a young-account join, and owner sign-off), **plus the new item-5 audit-seam fix**. The new-bot `parity/` golden should assert the same behavioral rubric as an executable golden rather than unit tests alone: (a) a burst of N joins within the window triggers exactly one staff alert + slowmode raise + auto-restore after the lockdown duration, and a second, later, distinct burst re-alerts (no permanent suppression); (b) a young-account join under both `age_action=alert` and `age_action=kick` produces the correct alert and (for kick) exactly one audited `moderation_service.kick` call; (c) a forced config-load exception never blocks the join (fail-open regression); (d) a static guard that no tier-3/4 (alt-detection/VPN) code or external HTTP call ever creeps into the module, permanently enforcing the Q-0111 DECLINED boundary; (e) the raid-lockdown slowmode change emits an audit record once item 5 lands.

**Outperform-target status:** comparable to Wick's raid-detection/verification-level system and Dyno's raid-mode. Our fail-open/no-PII/audited-kick design is already a defensible differentiator (many raid bots make external reputation-API calls or retain more data) but the missing `quarantine` action, any join-rate visualization/dashboard, and the slowmode audit gap (item 5) are known, named gaps versus Wick specifically. **Pending Lane F** for the definitive feature-by-feature citation.

**Owner-gated/blocked status:** Q-0111 already settled tiers 1+2 as APPROVED and tiers 3+4 (alt-detection/VPN blocking) as DECLINED for GDPR/privacy reasons — any future re-opening of tier 3/4 needs a fresh owner decision. The five Optimize items above (BindingSpec conversion, wiring a logging subscriber, the `quarantine` action, documenting restart-unsafety, and routing slowmode through the audited seam) are ordinary contained engineering work, not owner-gated.

**Cross-lane dependency:** security's two advisory events (`security.raid_detected`, `security.account_flagged`) have zero real subscribers today; their natural future subscriber is `server_logging.py` (**Lane D**), the same audit-fanout pattern already wired for `moderation.action_taken`/`karma.granted`.

---

### cleanup
_cogs: disbot/cogs/cleanup_cog.py, disbot/cogs/cleanup/panel.py, disbot/cogs/cleanup/schemas.py, disbot/views/cleanup/policy_panel.py, disbot/governance/cleanup.py, disbot/services/cleanup_diagnostics.py, disbot/services/cleanup_levels.py, disbot/services/cleanup_profiles.py, disbot/services/history_cleanup.py, disbot/utils/settings_keys/cleanup.py, disbot/views/setup/sections/cleanup.py_

> **Verifier's note (adversarial re-check, 2026-07-02):** this section corrects the first-pass draft in five places: (1) a false "already audited" claim about `!cleanuphistory`'s bulk-delete path (the draft's biggest error — confirmed wrong by grep, not a judgment call); (2) two off-by-a-few-lines file:line citations; (3) a mischaracterized field count in the proposed G-A9 spec's own docstring; (4) a genuinely missing ledger row for `services/cleanup_diagnostics.py` — one of the 11 assigned files, never once cited by file:line in the original draft despite ~400 lines of real logic. Fit numbers are recomputed below (53 units, not 51). Everything else in the original draft — all other ~40 file:line citations, the tier calls, the ground-truth perm-mismatch explanation, the cross-lane exclusion — was independently re-checked against source and found correct; it is carried over unchanged.

> **Note on two assigned files excluded from this ledger:** `disbot/core/runtime/cleanup_registry.py` and `disbot/services/game_state_cleanup.py` are **not** part of this subsystem — see "Cross-lane dependency" below. `disbot/utils/db/moderation.py` (prohibited-word/wordfilter table functions) and `disbot/governance/writes.py` (the audited policy-mutation pipeline) are cited below as the actual owners of cleanup's stores/mutations even though they aren't cog/service files named "cleanup"; verified by direct grep, not assumed.

#### Surface-unit ledger

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| `!cleanuphistory` | command | cogs/cleanup_cog.py:322-469 (decorator :322, `@commands.cooldown` :324, def :325) | 3 | 3 | Bespoke bulk-delete orchestration (mode/duration parsing, plan build via `history_cleanup`) **plus a raw `bot.wait_for("reaction_add", timeout=30.0)` confirm loop at :438-443** — a real `wait_for` wizard the pre-extracted scaffold's flag line missed ("no wait_for-based wizard found" was wrong; corrected here). G-4 already declares the cooldown (:324); G-A10 (new, below) would replace the reaction-wait_for with a declarative preview→confirm→apply render, narrowing but not eliminating the escape hatch — mode-dispatch/plan-building remains real domain logic. **Its apply step also has an independent audit-trail gap — see the new mutation row below, not just a confirm-UX gap.** |
| `!word` (bare, no subcommand) | command | cogs/cleanup_cog.py:486-498 | 2 | 2 | Pure read (word cache → joined string) — maps cleanly to `PanelRef`+`BlockSpec(kind="list")`+`ProviderRef`, same class as karma's `!karma` card. No amendment needed, just panel-routing instead of a raw `ctx.send`. |
| `!word add` | command (subcommand) | cogs/cleanup_cog.py:500-517 | 3 | 1 | Domain mutation (dedupe check, cache reload, branching feedback) via **raw `db.add_prohibited_word`** — no `*_mutation.py`, no `emit_audit_action` (see mutation-path finding below). G-2 (list-valued settings + add/remove workflow) ports this to a declarative add-workflow, which as a side effect fixes the missing audit trail. |
| `!word remove` | command (subcommand) | cogs/cleanup_cog.py:519-536 | 3 | 1 | Same shape/gap as `!word add`, mirrored for removal. G-2. |
| `!word list` | command (subcommand) | cogs/cleanup_cog.py:538-550 | 2 | 2 | Duplicate read path of the bare `!word` — same tier2 read-model reasoning. |
| `!wordmenu` | command | cogs/cleanup_cog.py:552-559 | 1 | 1 | Pure command→panel route: kernel open-panel workflow (`PanelRef("cleanup.word_menu")`). |
| `!cleanup` | command | cogs/cleanup_cog.py:561-570 | 1 | 1 | Pure command→panel route: kernel open-panel workflow (`PanelRef("cleanup.hub")`). |
| `_WordMenuView` embed | panel | cogs/cleanup_cog.py:638-669 (`build_embed` :646) | 2 | 2 | `FieldsBlock` over a read-model (word cache + strict flag) — no bespoke view class survives. |
| Add-Word workflow (`btn_add`+`_AddWordModal`) | panel-action | cogs/cleanup_cog.py:592-613, 671-673 | 3 | 1 | Panel-surface twin of `!word add` — same G-2 disposition (and same missing-audit finding). |
| Remove-Word workflow (`btn_remove`+`_RemoveWordModal`) | panel-action | cogs/cleanup_cog.py:615-635, 675-677 | 3 | 1 | Panel-surface twin of `!word remove` — G-2. |
| Refresh button (`_WordMenuView`) | panel-action | cogs/cleanup_cog.py:679-682 | 1 | 1 | Kernel re-render workflow — same class as logging's "panel: refresh status". |
| Scan-History workflow (`btn_scan`+`_ScanHistoryModal`) | panel-action | cogs/cleanup_cog.py:684-690, 710-767 | 3 | 3 | Real bulk-scan+**immediate**-delete logic (1–500 msgs, no preview/confirm step at all — unlike `!cleanuphistory`'s confirm). Its per-message deletions route through `remove_unwanted_message` → `moderation_service.auto_delete` (audited, verified) — genuine escape hatch **and** a shipped UX inconsistency (flagged under Reconsider): the two paths to "scan+delete messages" disagree on whether to confirm first. |
| Anti-evasion toggle button | panel-action | cogs/cleanup_cog.py:692-707 | 3 | 1 | Today a raw two-line `db.set_wordfilter_strict` write with **no `SettingSpec`, no audit trail** (mutation-path finding below). Trivially a plain bool `SettingSpec` (already-native, no amendment) once modeled — this is a modeling gap in the current code, not a grammar gap. |
| `CleanupPanelView` embed | panel | cogs/cleanup/panel.py:47-86, 137-138 | 2 | 2 | `FieldsBlock` over `build_cleanup_overview_embed`'s read-model (word count) — pure read, no mutation in this view per its own module docstring. |
| `btn_words` (nav → word menu) | panel-action | cogs/cleanup/panel.py:140-162 | 1 | 1 | Pure in-subsystem navigation (`PanelRef("cleanup.word_menu")`). |
| `btn_logging` (nav → Logging panel, cross-subsystem) | panel-action | cogs/cleanup/panel.py:164-210 | 3 | 1 | As-written: bespoke cross-cog dispatch — `get_cog("LoggingCog")` + duck-typed `build_help_menu_view` `hasattr`/`callable` check + `try/except` + manual `LoggingPanelView(...)` fallback reconstruction (:180-210). This is legacy plumbing for what `PanelRef`'s global panel-id registry **already** resolves declaratively — no new amendment needed, `PanelRef("logging.panel")` already exists in spec.py; the fallback branch disappears once panel ids are centrally resolvable. |
| `btn_settings` (nav → Settings hub) | panel-action | cogs/cleanup/panel.py:212-231 | 1 | 1 | Pure navigation to the generic subsystem-settings view. |
| `btn_policies` (nav → Policy panel) | panel-action | cogs/cleanup/panel.py:233-260 | 2 | 2 | Opens a new panel needing a registered diagnostics read-model provider (`collect_cleanup_diagnostics`) — same class as karma card. |
| `btn_refresh` (hub) | panel-action | cogs/cleanup/panel.py:262-278 | 1 | 1 | Kernel re-render workflow. |
| `CleanupPolicyPanelView` diagnostics embed | panel | views/cleanup/policy_panel.py:101-165, 702-711 | 2 | 2 | `FieldsBlock`/table-ish text over `collect_cleanup_diagnostics`'s read-model (per-scope rows + stale/ineffective flags) — no domain logic in the rendering itself (the health-check logic itself is a separate, bespoke unit — see the new `services/cleanup_diagnostics.py` row below, previously missing from this ledger). |
| `btn_build` → preset scope/category/channel/level cascade | panel-action + selector-chain | views/cleanup/policy_panel.py:211-369, 713-736 | 3 | 2 | As-written: a hand-wired chain of `BaseView`+`discord.ui.Select` subclasses threading scope context through constructor closures (`_ScopeSelect`→`_CategoryPickSelect`/`_ChannelPickSelect`→`_LevelSelect`). Spec.py's `SelectorSpec` (`selector_id`, `on_select: Route`, `options_source`) already covers "select → route to next panel" declaratively — no new amendment, just modeling each step as a `SelectorSpec` chain. |
| Custom-level builder (`_CustomLevelView` + 3 selects + preview button) | panel | views/cleanup/policy_panel.py:386-534 | 3 | 2 | Rebuild-the-whole-view-on-each-pick pattern (`_CustomLevelView.update`) — expressible as `SelectorSpec`s with shared draft state via `WorkflowRef` params; same disposition as the preset cascade above. |
| Preview→Confirm→Apply workflow | panel | views/cleanup/policy_panel.py:167-204, 335-368, 512-533, 541-598 (render + wiring); **services/cleanup_diagnostics.py:209-298 (`preview_cleanup_columns`/`preview_cleanup_change` — the actual diff computation) and :306-357 (`apply_cleanup_columns`/`apply_cleanup_change` — the audited-apply wrapper)** | 3 | 2 | **GAP:** dry-run preview embed (computed diff/count) → explicit Apply/Cancel buttons → audited apply (`apply_cleanup_columns`) has no §2 primitive. `PanelActionSpec.confirm` is a generic "are you sure" re-click flag, not a computed-diff preview — propose **G-A10** (below). *(Correction: the original draft cited only the view-layer render/wiring lines for this gap — the actual diff-computation and apply-wrapper logic it's describing live in `services/cleanup_diagnostics.py`, which the original ledger never cited anywhere.)* |
| `btn_remove` → `_RemoveSelect` → `remove_cleanup_change` | panel-action | views/cleanup/policy_panel.py:617-694, 738-769 | 3 | 1 | List-and-remove-one-row shape (pick a stored override, remove, audited) — reuses **G-2**'s remove-workflow family rather than a new amendment. |
| `btn_refresh` (policy diagnostics) | panel-action | views/cleanup/policy_panel.py:771-783 | 1 | 1 | Kernel re-render workflow. |
| `CleanupSectionView` scope/level cascade (setup wizard) | panel | views/setup/sections/cleanup.py:113-269, 385-402 | 3 | 2 | Identical shape to the policy-panel's preset cascade, but stages a `SetupOperation` draft instead of an immediate governance write. Same `SelectorSpec`-chain disposition (no new amendment for the selects themselves). |
| `_ProfileSelect` batch-apply | panel-action | views/setup/sections/cleanup.py:271-382 | 3 | 3 | Real logic: iterates `guild.text_channels`, applies a profile's op list, stages N `SetupOperation`s with per-op metadata, reports a staged count. Legitimate escape hatch — batch orchestration + draft-staging side effects are genuine domain behavior — though it rides on the missing wizard-section framework (G-A9) for its outer scaffolding. |
| `SetupSection` registration (framework declaration) | listener/other | views/setup/sections/cleanup.py:577-599 | 3 | 2 | The entire `services.setup_sections.SetupSection` dataclass (slug/`run`/`customize`/`detail_embed_builder`/`detail_view_builder`/`op_kinds`/`depths`/`recommended_ops_builder`) has **no §2 equivalent** for its 5 genuine callback fields (`run`, `customize`, `detail_embed_builder`, `detail_view_builder`, `recommended_ops_builder`) — every one is a bespoke Python callable. Propose **G-A9** (below): closes the setup/provisioning-wizard danger zone the BRIEF names. (`op_kinds`/`depths` are plain data, not callbacks — see the correction to the G-A9 docstring below.) |
| `spam_window_seconds` setting | setting | cogs/cleanup/schemas.py:59-73 | 2 | 1 | Bounded-int validator (`_validate_spam_window`) is a registered ref as-specced; G-5 (declarative validator bounds) makes the 1–300s bound pure data. Already uses `input_hint="numeric_presets"` + `presets=(10,15,30)` — both already-native `SettingSpec` fields. |
| `DomainPanelSpec` pointer ("Cleanup policies") | setting | cogs/cleanup/schemas.py:77-92 | 1 | 1 | A compatibility-shim redirect ("this subsystem's real config lives in a dedicated panel") for the legacy Settings hub; in a from-scratch manifest this collapses to nothing — the subsystem just declares its settings-panel entry as a direct panel route. **Finding:** this `DomainPanelSpec` sets `capability_required="cleanup.settings.configure"` (schemas.py:88) — a string that is **NOT** in `subsystem_registry.py`'s registered `cleanup` capabilities (word.add/word.remove/history.scan/policy.configure — :509-514), even though the file's own comment 4 lines above (**schemas.py:44**, not :46 as the pre-verification draft had it — line 46 is the `_CLEANUP_CAPABILITY` assignment, not the comment) explicitly warns "`cleanup.settings.configure` is not a registered capability." Every sibling subsystem (moderation:146, security:724, welcome:668, karma:437, logging:1205, …) *does* register its own `"<name>.settings.configure"` — cleanup is the one exception. Real, verified inconsistency, not a grammar-fit issue. |
| 4 declared capabilities (`cleanup.word.add`/`word.remove`/`history.scan`/`policy.configure`) | setting×4 | utils/subsystem_registry.py:509-514 | 1 | 1 | `capabilities: tuple[str,...]` field on `SubsystemManifest` — pure metadata. Counted as 4 units in the fit tally. |
| `on_guild_remove` | listener | cogs/cleanup_cog.py:316-320 | 3 | 2 | **G-1**: raw `@commands.Cog.listener()` on a real discord.py gateway event (guild-removal cache eviction) — thin fetch-and-forget handler once declared via `GatewayListenerSpec`. |
| `CleanupStage` registration (message-pipeline stage) | listener | cogs/cleanup_cog.py:97-119 (class), :33 (`CLEANUP_STAGE_ORDER = 10`), :143/:148 (register/unregister in `cog_load`/`cog_unload`) | 3 | 2 | **New — G-A2** (below): neither G-1's `GatewayListenerSpec` (single raw event + boolean gate) nor `EventSpec`/`EventSubscription` (bus events) model an **ordered, short-circuiting** synchronous message-pipeline stage (`order=10`, `StageResult(short_circuit=True)`). Same gap is present-but-unaddressed in this lane's `automod`/`image_moderation` pre-extracted scaffolds (their entries note the pattern but propose no amendment) — cleanup makes it concrete enough to name. |
| `remove_unwanted_message` (per-message evaluate+delete handler) | listener | cogs/cleanup_cog.py:222-293, 295-314 (`_delete_prohibited`) | 3 | 3 | Deliberate escape hatch: real per-message policy evaluation (`governance_service.resolve_command_policy` call, exact + anti-evasion word-match passes) referenced by `CleanupStage`'s `HandlerRef` — genuine domain logic, should stay code. Its deletions correctly route through `moderation_service.auto_delete` (verified, audited) — this handler is the model-quality delete path in this subsystem. |
| `_delete_if_command_blocked` (Command Access gate) | listener | cogs/cleanup_cog.py:169-220 | 3 | 3 | Deliberate escape hatch: cross-system policy check (`command_access.resolve_command_access`) + conditional `auto_delete` + timed feedback — real domain logic, not a repeatable declarative shape. |
| `EVT_CLEANUP_CHANGED` + `EVT_CACHE_INVALIDATED` (paired emission) | event | governance/writes.py:352-371, 451-470; governance/events.py:20 | 1 | 1 | `EventSpec` declarations, emitted together inside the audited pipeline. `core/runtime/__init__.py:155-183` has a **reserved, currently no-op** subscriber for future cleanup-policy caching (DEBT-003) — worth noting under governance/cache behavior below. |
| `audit.action_recorded` (`emit_audit_action`, mutation_type=`set_cleanup_policy`/`remove_cleanup_policy`) | event | governance/writes.py:334-350, 437-449 | 1 | 1 | `EventSpec` declaration, `audited=True`; emit lives inside the governance mutation pipeline — mirrors karma's audited-seam pattern. |
| `cleanup_policies` table | store | migrations/004_governance_tables.sql:24-33 | 1 | 1 | `StoreSpec` → generated sole-writer fence; sole writer = `GovernanceMutationPipeline.set_cleanup_policy`/`remove_cleanup_policy`. *(Citation corrected — the original draft cited :24-31, which cuts off before the table's `PRIMARY KEY (guild_id, scope_type, scope_id)` clause and the closing statement at :32-33.)* |
| `cleanup_policies.policy_version` column | store | migrations/058_cleanup_policy_version.sql:29-30 | 1 | 1 | Additive, behavior-neutral version marker (resolver never reads it — informational only). |
| `wordfilter_config` table | store | migrations/097_wordfilter_strict.sql:27-30 | 1 | 1 | `StoreSpec` (guild_id PK, strict bool) — resolves the scaffold's "unverified column detail" flag. Sole writer today is the **unaudited** `db.set_wordfilter_strict` (see mutation finding) rather than a mutation service — the store declaration is tier-1, its write path is not yet audited. |
| `prohibited_words` table | store | utils/db/migrations.py:308-312 | 1 | 1 | `StoreSpec` (PK guild_id+word). **Missing from the pre-extracted scaffold entirely** — added here. Sole writer today is the unaudited `db.add_prohibited_word`/`remove_prohibited_word` pair. |
| `GovernanceMutationPipeline.set_cleanup_policy`/`remove_cleanup_policy` (audited seam) | mutation | governance/writes.py:258-380, 381-479 | 1 | 1 | The canonical audited-service seam for cleanup **policy** writes (DB row + `governance_audit_log` row + `emit_audit_action` + `EVT_CLEANUP_CHANGED` + `EVT_CACHE_INVALIDATED`, one transaction). Exemplary — nothing to port, this is the shape every other mutation in this ledger should match. |
| Prohibited-word / wordfilter mutations (unaudited) | mutation | utils/db/moderation.py:91-136; cogs/cleanup_cog.py:505, 524, 601, 624, 705 | 3 | 1 | **Finding:** bypasses both `docs/architecture.md`'s `*_mutation.py` rule and the `emit_audit_action` rule — raw `db.add_prohibited_word`/`remove_prohibited_word`/`set_wordfilter_strict` calls, zero audit trail, zero mutation-service module. Verified via grep: no `emit_audit_action`/`audit_events` reference exists in `cleanup_cog.py` or `utils/db/moderation.py`'s prohibited-word/wordfilter functions. G-2's kernel add/remove workflow (words) + a plain audited `SettingSpec` (strict) fix this as a side effect of porting — worth fixing in the **current** bot too, independent of the rebuild. |
| **`apply_history_cleanup_plan` (bulk-delete apply path, `!cleanuphistory`)** | **mutation** | **services/history_cleanup.py:182-208 (raw `message.delete()`); invoked unaudited at cogs/cleanup_cog.py:447** | **3** | **3** | **New finding (corrects the draft's "Destructive actions" claim below): this is NOT audited.** Verified by grep: `moderation_service.auto_delete` is called only from `cleanup_cog.py:209,253,301` (the auto-mod paths) — never from `history_cleanup.py`, and never around the `cleanup_cog.py:447` call site. `apply_history_cleanup_plan` deletes each matched message with a raw `message.delete()`, catching `Forbidden`/`HTTPException` as a failure count — no `mod_logs` row, no `EVT_MOD_ACTION`. The *same function* **is** wrapped in an audit call (`_record_action`) when invoked from `moderation_service._run_post_action_cleanup` (services/moderation_service.py:292-350, the kick/ban post-action sweep) — proving the audited pattern exists in this codebase for this exact function — but `!cleanuphistory`'s direct call bypasses it entirely. Deliberate escape hatch for the per-message try/except delete mechanics; the missing audit wrapper is an independent bug, fixable in the current bot regardless of the rebuild (same class as the word/strict mutation finding above). |
| `governance/cleanup.py::resolve_cleanup_policy` (resolver) | other | governance/cleanup.py:21-58 | 3 | 3 | Deliberate escape hatch: thin domain logic reusing the already-shared `governance.resolver._build_scope_chain` utility; only the terminal row→`CleanupPolicy` mapping + fallback default (5s, delete_invalid=True) is bespoke — legitimately thin, should stay code. Resolves the scaffold's "not read in full" flag — now fully read (38 lines total). |
| **`collect_cleanup_diagnostics` stale/ineffective-row detection** | **other** | **services/cleanup_diagnostics.py:105-162** | **3** | **3** | **Missing from the draft entirely** — `services/cleanup_diagnostics.py` is one of the 11 explicitly assigned files (~400 lines) but was never once cited by file:line in the original ledger, only name-dropped in prose. Bespoke health-check heuristics: `_target_label`'s stale-scope detection (`guild.get_channel(scope_id) is None`) and the ineffective-row heuristic (`scope_type == "guild" and scope_id != guild.id`, catching a legacy `scope_id=0` mis-write the resolver silently never reads). Real per-row domain judgment, not expressible as declarative data — same class as `governance/cleanup.py::resolve_cleanup_policy` above. Deliberate escape hatch, should stay code. |
| `cleanup_levels.py` LEVELS preset table + round-trip helpers | other | services/cleanup_levels.py:40-121 | 2 | 1 | The 4-level (Off/Light/Standard/Strict) column-bundle map is pure declarative data (akin to `SettingSpec.presets` but correlating 3 columns per name — tier1 once modeled that way); `columns_for_level`/`level_for_columns`/`cleanup_scope_id` are small deterministic round-trip lookups (tier2 as literally coded today). |
| `CleanupProfile` catalogue metadata | other | services/cleanup_profiles.py:43-54, 129-174 | 2 | 2 | Declarative catalogue (slug/display_name/description) pointing to a builder `HandlerRef` — the metadata itself is data, same class as `SettingSpec.presets`/`LEVELS`. |
| Profile-builder heuristic logic (`_build_silent_bot`/`_build_moderation_safe`) | other | services/cleanup_profiles.py:102-127 | 3 | 3 | Deliberate escape hatch: real heuristic domain logic (channel-name classification via `utils.channel_classify`) deciding per-channel policy overrides on batch-apply — genuinely bespoke, should stay code. |
| `build_help_menu_view` hook | help | cogs/cleanup_cog.py:572-589 | 1 | 1 | Pure navigation hook (opens `CleanupPanelView`) for `!help cleanup`/`/help cleanup` direct-nav. **Note:** cleanup has **no `HelpEntrySpec`** (summary/examples/rules_text) anywhere in the codebase — unlike karma/logging, which both declare one. Genuine absence, not merely an unlisted unit. |

**Unit kinds present:** command, panel (view/embed/action), setting, listener (gateway + message-pipeline), event, store, help, mutation (audited, an unaudited config path, **and now a second unaudited bulk-delete path**), "other" (resolver/preset/profile-catalogue/**diagnostics-heuristic**). **Absent, stated explicitly:**
- **game** — cleanup owns no game/session state; absent, correctly so.
- **bindings/resources** (`BindingSpec`/`ResourceRequirement`) — no channel/role pointer or provisioning requirement anywhere in these files (no `cleanup_log_channel`-style binding); confirmed absent by reading every file in the assigned set (the one `binding_name=None` occurrence at `views/setup/sections/cleanup.py:527` is a null field on the shared `SetupOperation` dataclass, not an actual binding cleanup owns).
- **diagnostics** (`DiagnosticProviderSpec`-shaped) — **despite the filename**, `services/cleanup_diagnostics.py` is **not** registered with the one real diagnostics-provider registry in this codebase (`services.diagnostics_service.register(name, provider)`, used e.g. by `cogs/diagnostic_cog.py:261`). Verified by grep: no `diagnostics_service` reference anywhere in `cleanup_diagnostics.py`. It is a domain read-model + audited-preview/apply service consumed directly by the policy panel (`ProviderRef`-shaped, tier2, **plus the bespoke health-check heuristics captured as their own "other" row above**), not a platform-health `DiagnosticProviderSpec` provider. This resolves the task's explicit "is it a registered DiagnosticProviderSpec-shaped provider?" question: **no**.

**Structural-pattern flags:**
- **Gateway listener** — present: `on_guild_remove` (`@commands.Cog.listener()`, cogs/cleanup_cog.py:316).
- **Message-pipeline stage** — present: `CleanupStage` (order=10, cogs/cleanup_cog.py:97-119, registered :143).
- **`wait_for` wizard** — **present** (corrects the pre-extracted scaffold, which asserted "no wait_for-based wizard found"): `!cleanuphistory` uses `await self.bot.wait_for("reaction_add", timeout=30.0, check=check)` at cogs/cleanup_cog.py:439 for its delete confirmation. This is a genuine danger-zone pattern the scaffold missed.
- **Scheduled loop** — confirmed absent: `grep -rn "tasks.loop"` across every file in the assigned set returns nothing.
- **Voice** — confirmed absent: no `voice_client`/`VoiceState`/`voice_state` reference anywhere in the assigned files.
- **Stateful game loop** — absent; cleanup owns no game state (see Cross-lane dependency note — `game_state_cleanup.py` is a different subsystem's GC provider, not cleanup's).
- **Multi-step selector-driven "wizard" (non-`wait_for`)** — present twice: the policy-panel builder (views/cleanup/policy_panel.py:211-534) and the setup-wizard's `CleanupSectionView` cascade (views/setup/sections/cleanup.py:113-269) both chain 3-4 ephemeral `discord.ui.Select` views via closures. Not `wait_for`-based (uses `interaction.response.send_message(view=...)` chains instead), but still the "setup/provisioning wizard" danger zone the BRIEF names — addressed by proposed G-A9/G-A10 below.

#### Manifest sketch

```python
"""Cleanup — expressed in the §2 grammar (Lane A audit sketch, 2026-07-02;
adversarial-verification pass same day).

Source of truth (verified this session):
    cogs/cleanup_cog.py                — commands, word-menu, message-pipeline
                                          stage, wait_for confirm (:439)
    cogs/cleanup/panel.py               — CleanupPanelView hub
    cogs/cleanup/schemas.py             — spam_window_seconds SettingSpec +
                                          DomainPanelSpec pointer
    views/cleanup/policy_panel.py       — diagnostics render + scope/level
                                          builder + preview/confirm/apply UI
    views/setup/sections/cleanup.py     — setup-wizard section + profile batch-apply
    governance/cleanup.py               — scope-chain policy resolver
    services/cleanup_levels.py          — Off/Light/Standard/Strict preset table
    services/cleanup_profiles.py        — named profile catalogue + heuristics
    services/cleanup_diagnostics.py     — diagnostics collection (incl. stale/
                                          ineffective-row heuristics) + dry-run
                                          preview + audited apply/remove
    services/history_cleanup.py         — !cleanuphistory scan/apply plan
                                          (apply path is UNAUDITED — verified
                                          finding, see mutation ledger row)
    governance/writes.py                — audited GovernanceMutationPipeline
    migrations/004,058,097 + utils/db/migrations.py:308 — the 4 stores

Tier verdict: 53 units, 54.7% tier-1/2 as-written, 83.0% with amendments (G-1,
G-2, G-5 reused; G-A9/G-A10/G-A2 proposed new). The 9 remaining tier-3 units
are all judgment-confirmed deliberate escape hatches (per-message auto-mod
evaluation, channel-classification heuristics, the scope-chain resolver,
batch profile orchestration, the diagnostics staleness heuristic, and the
unaudited-bulk-delete mechanic) — none are grammar gaps, though two of them
(the unaudited word/strict mutations and the unaudited bulk-delete) are bugs
worth fixing in the current bot regardless of the rebuild.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tools.grammar_spike.spec import (
    Activation,
    BlockSpec,
    CommandKind,
    CommandSpec,
    EventSpec,
    FieldSpec,
    GatewayListenerSpec,
    HandlerRef,
    HelpEntrySpec,
    PanelActionSpec,
    PanelRef,
    PanelSpec,
    ProviderRef,
    SelectorSpec,
    SettingSpec,
    StoreSpec,
    SubsystemManifest,
    WorkflowRef,
)

_CAP_WORD_ADD = "cleanup.word.add"
_CAP_WORD_REMOVE = "cleanup.word.remove"
_CAP_HISTORY_SCAN = "cleanup.history.scan"
_CAP_POLICY_CONFIGURE = "cleanup.policy.configure"


# ---------------------------------------------------------------------------
# PROPOSED — Lane A findings (not in spec.py; capstone renumbers G-A<n>)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class WizardSectionSpec:
    """PROPOSED G-A9. No §2 equivalent for `services.setup_sections.SetupSection`.

    Closes the setup/provisioning-wizard danger zone the BRIEF names —
    views/setup/sections/cleanup.py:577-599 registers 5 genuine bespoke
    callback fields today (run/customize/detail_embed_builder/
    detail_view_builder/recommended_ops_builder — every one a real Python
    callable, none declarative) plus 2 plain-data fields (op_kinds/depths,
    both frozensets) that are ALREADY tier-1-shaped and just need a home in
    this spec. (Corrects the pre-verification draft, which miscounted this
    as "8 bespoke callback fields" and mischaracterized op_kinds/depths as
    callbacks — inconsistent with how they're modeled below, as plain data.)
    """

    slug: str = field(metadata={"role": "semantic"})
    recommended_ops: HandlerRef = field(metadata={"role": "semantic"})
    customize_target: "PanelSpec | SelectorSpec" = field(
        metadata={"role": "semantic"},
    )
    detail_panel: PanelRef = field(metadata={"role": "semantic"})
    op_kinds: tuple[str, ...] = field(default=(), metadata={"role": "semantic"})
    depths: tuple[str, ...] = field(default=(), metadata={"role": "arrangement"})


@dataclass(frozen=True)
class PreviewConfirmApplySpec:
    """PROPOSED G-A10. Generalizes cleanup's policy-panel preview/apply
    (rendered in views/cleanup/policy_panel.py, computed in
    services/cleanup_diagnostics.py:209-357), !cleanuphistory's ad hoc
    `wait_for` reaction-confirm (cogs/cleanup_cog.py:438-443), and logging's
    already-informally-tier1 "create channel" preview+confirm — none of
    which are named as ONE primitive today. Distinct from
    `PanelActionSpec.confirm` (a generic are-you-sure re-click): this
    carries a COMPUTED diff/count from `preview_provider` into the
    confirmation render. NOTE: adopting this for !cleanuphistory's apply
    step does not, by itself, guarantee the audited-delete gap (see the
    `apply_history_cleanup_plan` mutation finding) gets closed — that
    still requires apply_handler to route through the audited delete seam
    by convention, not merely by having a confirm step.
    """

    preview_provider: ProviderRef = field(metadata={"role": "semantic"})
    apply_handler: HandlerRef = field(metadata={"role": "semantic"})
    cancel_render: str = field(default="Cancelled — nothing was written.")


@dataclass(frozen=True)
class MessagePipelineStageSpec:
    """PROPOSED G-A2. Neither G-1 (single raw gateway event + bool gate) nor
    EventSpec/EventSubscription (bus events) model an ORDERED,
    short-circuiting synchronous stage. cogs/cleanup_cog.py:33/:97-119/:143
    (order=10); same gap present-but-unaddressed in this lane's automod
    (order=5) and image_moderation (order=25) scaffolds.
    """

    order: int = field(metadata={"role": "arrangement"})
    handler: HandlerRef = field(metadata={"role": "semantic"})
    short_circuit_policy: str = field(default="on_deleted")


# ---------------------------------------------------------------------------
# The manifest
# ---------------------------------------------------------------------------

CLEANUP_MANIFEST = SubsystemManifest(
    key="cleanup",
    display_name="Cleanup",
    description="Prohibited words, command deletion, channel hygiene.",
    emoji="🧹",
    category="moderation",
    visibility_tier="administrator",
    capabilities=(
        _CAP_WORD_ADD,
        _CAP_WORD_REMOVE,
        _CAP_HISTORY_SCAN,
        _CAP_POLICY_CONFIGURE,
        # NOTE: schemas.py:88 references "cleanup.settings.configure", which
        # is NOT in this tuple — a verified, undeclared-capability finding
        # (every sibling subsystem DOES register its own "<name>.settings
        # .configure"; cleanup is the one exception). Fix at port time.
    ),
    parent_hub="moderation",  # [A]
    commands=(
        CommandSpec(
            name="cleanuphistory",
            kind=CommandKind.PREFIX,
            summary="Bulk-clean channel history by mode.",
            route=HandlerRef(
                "cleanup.history_scan",
                justification="mode/duration parsing + plan build; G-A10 covers "
                "the confirm step only, not the scan/apply logic — and the "
                "current apply path (apply_history_cleanup_plan) is UNAUDITED "
                "(no mod_logs row, no EVT_MOD_ACTION), a bug independent of "
                "the confirm-UX gap",
            ),
            capability_required=_CAP_HISTORY_SCAN,
            cooldown=(1, 10, "channel"),  # G-4 — cogs/cleanup_cog.py:324
        ),
        CommandSpec(
            name="word",
            kind=CommandKind.PREFIX,
            summary="List prohibited words.",
            route=PanelRef("cleanup.word_menu"),  # tier2: list-block provider
            capability_required=_CAP_WORD_ADD,  # gate shared w/ add/remove
        ),
        CommandSpec(
            name="word add",
            kind=CommandKind.PREFIX,
            summary="Add a prohibited word.",
            route=WorkflowRef(
                "list_setting_add",  # G-2
                params=(("subsystem", "cleanup"), ("field", "prohibited_words")),
            ),
            capability_required=_CAP_WORD_ADD,
        ),
        CommandSpec(
            name="word remove",
            kind=CommandKind.PREFIX,
            summary="Remove a prohibited word.",
            route=WorkflowRef(
                "list_setting_remove",  # G-2
                params=(("subsystem", "cleanup"), ("field", "prohibited_words")),
            ),
            capability_required=_CAP_WORD_REMOVE,
        ),
        CommandSpec(
            name="wordmenu",
            kind=CommandKind.PREFIX,
            summary="Open the prohibited-words manager.",
            route=PanelRef("cleanup.word_menu"),
            capability_required=_CAP_WORD_ADD,
        ),
        CommandSpec(
            name="cleanup",
            kind=CommandKind.PREFIX,
            summary="Open the Cleanup hub.",
            route=PanelRef("cleanup.hub"),
            capability_required=_CAP_POLICY_CONFIGURE,
        ),
    ),
    panels=(
        PanelSpec(
            panel_id="cleanup.hub",
            subsystem="cleanup",
            title="🧹 Cleanup Hub",
            body=(BlockSpec(kind="fields", provider=ProviderRef("cleanup.overview")),),
            actions=(
                PanelActionSpec(
                    action_id="words",
                    label="🔤 Prohibited Words",
                    handler=PanelRef("cleanup.word_menu"),  # tier1: navigation
                    custom_id_override="cleanup:words",
                ),
                PanelActionSpec(
                    action_id="logging",
                    label="📝 Logging Status",
                    # tier1 once ported: PanelRef resolves cross-subsystem
                    # via the global panel-id registry — no get_cog() dance.
                    handler=PanelRef("logging.panel"),
                    custom_id_override="cleanup:logging",
                ),
                PanelActionSpec(
                    action_id="settings",
                    label="⚙️ Settings",
                    handler=PanelRef("settings.subsystem"),
                    custom_id_override="cleanup:settings",
                ),
                PanelActionSpec(
                    action_id="policies",
                    label="🧹 Cleanup Policies",
                    handler=PanelRef("cleanup.policy_panel"),
                    custom_id_override="cleanup:policies",
                ),
                PanelActionSpec(
                    action_id="refresh",
                    label="🔄 Refresh",
                    handler=PanelRef("cleanup.hub"),  # tier1: re-render
                    custom_id_override="cleanup:refresh",
                ),
            ),
        ),
        PanelSpec(
            panel_id="cleanup.word_menu",
            subsystem="cleanup",
            title="🔤 Prohibited Words Manager",
            body=(BlockSpec(kind="list", provider=ProviderRef("cleanup.word_list")),),
            actions=(
                PanelActionSpec(
                    action_id="add",
                    label="➕ Add Word",
                    handler=WorkflowRef("list_setting_add"),  # G-2
                ),
                PanelActionSpec(
                    action_id="remove",
                    label="➖ Remove Word",
                    handler=WorkflowRef("list_setting_remove"),  # G-2
                ),
                PanelActionSpec(
                    action_id="refresh",
                    label="🔄 Refresh",
                    handler=PanelRef("cleanup.word_menu"),
                ),
                PanelActionSpec(
                    action_id="scan",
                    label="🔍 Scan History",
                    # tier3: real bulk-scan+delete logic, NO preview/confirm
                    # today (the shipped inconsistency vs !cleanuphistory).
                    # Its deletions ARE audited (routes through
                    # remove_unwanted_message → moderation_service.auto_delete).
                    handler=HandlerRef(
                        "cleanup.scan_history_and_delete",
                        justification="bespoke bulk scan+delete over channel "
                        "history — should gain the SAME confirm gate as "
                        "!cleanuphistory once ported (G-A10)",
                    ),
                ),
                PanelActionSpec(
                    action_id="strict",
                    label="🛡️ Anti-evasion",
                    # tier1 once modeled as a plain bool SettingSpec — see
                    # `strict` in settings= below; this action becomes a
                    # generated setting-toggle workflow, zero code.
                    handler=WorkflowRef(
                        "setting_toggle",
                        params=(("subsystem", "cleanup"), ("setting", "strict")),
                    ),
                ),
            ),
        ),
        PanelSpec(
            panel_id="cleanup.policy_panel",
            subsystem="cleanup",
            title="🧹 Cleanup Policies — Diagnostics",
            body=(BlockSpec(kind="table", provider=ProviderRef("cleanup.diagnostics")),),
            selectors=(
                # G-A9/2: scope→category/channel→level cascade, tier2 as a
                # SelectorSpec chain; the terminal step routes to a
                # PreviewConfirmApplySpec-backed handler (G-A10, new).
                SelectorSpec(
                    selector_id="scope",
                    kind="enum",
                    options_source=("guild", "category", "channel"),
                    on_select=PanelRef("cleanup.policy_scope_target_picker"),
                ),
            ),
            actions=(
                PanelActionSpec(
                    action_id="remove",
                    label="🗑️ Remove a policy",
                    handler=WorkflowRef("list_setting_remove"),  # G-2 reuse
                    destructive=True,
                    style="danger",
                ),
                PanelActionSpec(
                    action_id="refresh",
                    label="🔄 Refresh",
                    handler=PanelRef("cleanup.policy_panel"),
                ),
            ),
        ),
    ),
    settings=(
        SettingSpec(
            name="spam_window_seconds",
            value_type="int",
            default=15,
            settings_key="cleanup_spam_window_seconds",
            capability_required=_CAP_POLICY_CONFIGURE,
            validator=HandlerRef("cleanup.validate_spam_window"),  # G-5 target
            input_hint="numeric_presets",
            presets=(10, 15, 30),
            hint="Duplicate-message window for the !cleanuphistory spam sweep.",
        ),
        SettingSpec(
            # NEW modeling (today: a raw db.set_wordfilter_strict call, no
            # SettingSpec, no audit trail at all — a mutation-path finding).
            name="strict",
            value_type="bool",
            default=False,
            settings_key="cleanup_wordfilter_strict",
            capability_required=_CAP_WORD_ADD,
            activation=Activation.OFF_UNTIL_OPT_IN,
            hint="Obfuscation-resistant (anti-evasion) prohibited-word matching.",
        ),
        SettingSpec(
            # G-2: today a dedicated relational table (prohibited_words) with
            # bespoke add/remove cog code — modeled here as the list-valued
            # setting G-2 already proposes, generalized beyond scalar-KV lists.
            name="prohibited_words",
            value_type="list[str]",
            default=(),
            settings_key="cleanup_prohibited_words",  # port note: today a table, not KV
            capability_required=_CAP_WORD_ADD,
            hint="Words that trigger automatic message deletion.",
        ),
    ),
    events=(
        EventSpec(
            name="governance.cleanup.changed",
            payload_schema=(
                FieldSpec("guild_id", "int"),
                FieldSpec("scope_type", "str"),
                FieldSpec("scope_id", "int"),
                FieldSpec("mutation_id", "str"),
                FieldSpec("actor_id", "int"),
            ),
            owner_subsystem="cleanup",  # emitted by governance/writes.py today
            expected_subscribers=(
                HandlerRef(
                    "core.runtime.reserved_cleanup_cache_hook",
                    justification="reserved no-op — core/runtime/__init__.py:155-179",
                ),
            ),
            audited=True,
        ),
    ),
    gateway_listeners=(
        GatewayListenerSpec(  # G-1
            gateway_event="on_guild_remove",
            handler=HandlerRef(
                "cleanup.evict_guild_caches",
                justification="word/pattern/strict cache eviction on guild removal",
            ),
        ),
    ),
    # message_pipeline_stages=(  # PROPOSED G-A2 field, not in spec.py today
    #     MessagePipelineStageSpec(
    #         order=10,
    #         handler=HandlerRef(
    #             "cleanup.remove_unwanted_message",
    #             justification="per-message policy eval: command-access gate, "
    #             "governance command policy, prohibited-word match (exact + "
    #             "anti-evasion) — deliberate escape hatch, real domain logic",
    #         ),
    #     ),
    # ),
    stores=(
        StoreSpec(
            table="cleanup_policies",
            sole_writer="governance.mutation_pipeline",
            checkpoint_class="aggregate",
            invariant_tag="INV-CLEANUP-POLICY",
        ),
        StoreSpec(
            table="wordfilter_config",
            # today's sole writer is UNAUDITED (utils/db/moderation.py:130) —
            # this StoreSpec is aspirational: it should route through the
            # same GovernanceMutationPipeline-shaped seam once ported.
            sole_writer="cleanup.mutation_service",
            checkpoint_class="aggregate",
        ),
        StoreSpec(
            table="prohibited_words",
            sole_writer="cleanup.mutation_service",  # same aspirational note
            checkpoint_class="aggregate",
        ),
    ),
    game=None,
    help=None,  # ABSENT — no HelpEntrySpec exists for cleanup today
)
```

#### Tier-3 dispositions

- **`!cleanuphistory` core (mode/duration parsing, plan build)** — deliberate escape hatch: real domain orchestration; stays tier-3 even with amendments applied to its confirm step.
- **`!cleanuphistory`'s `wait_for("reaction_add")` confirm (:438-443)** and **the policy-panel Preview→Confirm→Apply flow** (views/cleanup/policy_panel.py:167-598, backed by services/cleanup_diagnostics.py:209-357) → **grammar gap, propose G-A10** `PreviewConfirmApplySpec` — a declarative computed-diff preview + confirm + audited apply, distinct from `PanelActionSpec.confirm`'s generic re-click gate.
- **`apply_history_cleanup_plan`'s unaudited delete mechanics (services/history_cleanup.py:182-208, called from cleanup_cog.py:447)** → **deliberate escape hatch for the per-message try/except delete mechanics, but the missing audit wrapper is an independent bug** (new finding — the original draft incorrectly claimed this path was already audited). Adopting G-A10's `apply_handler` contract for `!cleanuphistory` is an opportunity to close the gap by convention, but is not guaranteed to unless the wrapper explicitly routes through the audited delete seam.
- **`!word add`/`!word remove` + their panel/modal twins + the strict toggle** → **reuse G-2** (list-valued settings + add/remove workflows) — generalizes G-2 beyond scalar-KV lists to a dedicated relational table (`prohibited_words`) with its own add/remove API; this port also closes the found audit gap.
- **`btn_remove` → `remove_cleanup_change`** → **reuse G-2**'s remove-workflow (list-and-remove-one-stored-row shape).
- **`on_guild_remove`** → **reuse G-1** `GatewayListenerSpec`.
- **`CleanupStage` message-pipeline registration** → **grammar gap, propose G-A2** `MessagePipelineStageSpec` — an ordered, short-circuiting stage primitive distinct from G-1's single-event listener; the same gap is visible-but-unnamed in this lane's `automod`/`image_moderation` entries.
- **`SetupSection` registration + the two selector cascades (policy-panel builder, setup-wizard section)** → **grammar gap, propose G-A9** `WizardSectionSpec` for the outer registration (5 genuine callback fields, not 8 as the first-pass draft miscounted); the selects themselves are tier2 via the already-existing `SelectorSpec` (no amendment needed for the selects, only for the section-registration scaffolding).
- **`btn_logging` cross-subsystem dispatch** → **not a gap** — `PanelRef`'s global panel-id registry (already in spec.py) already covers cross-subsystem navigation; today's `get_cog()`+duck-typing is legacy plumbing that disappears once modeled.
- **`remove_unwanted_message`, `_delete_if_command_blocked`, `governance/cleanup.py::resolve_cleanup_policy`, `_ProfileSelect` batch-apply, the profile-builder heuristics (`_build_silent_bot`/`_build_moderation_safe`), `_ScanHistoryModal`'s scan+delete, and `collect_cleanup_diagnostics`'s stale/ineffective-row heuristics** → **deliberate escape hatches**, each with real per-call domain logic (cross-system policy checks, a scope-chain resolver reusing shared infra, batch orchestration with side effects, channel-name classification heuristics, or health-check judgment calls) that should stay code. None reuse or need an amendment.

#### Fit numbers

| Metric | Value |
|---|---|
| Units total | 53 |
| Tier-1/2 (as-written) | 29 |
| Fit % as-written | **54.7%** |
| Tier-1/2 (with amendments: G-1, G-2, G-5 reused + G-A9/G-A10/G-A2 proposed) | 44 |
| Fit % with amendments | **83.0%** |

*(Corrected from the first-pass draft's 51/57%/86%: two units were added after re-verification — an unaudited bulk-delete mutation path the draft had incorrectly described as already audited, and a bespoke diagnostics health-check heuristic in `services/cleanup_diagnostics.py` that the draft never cited by file:line anywhere. Both are deliberate escape hatches, tier-3 in both columns, so the numerator is unchanged (29/44) and only the denominator grew.)*

For comparison: karma 80→87%, logging 79→97%, blackjack 44→44% (spike RESULTS.md). Cleanup's 54.7%→83.0% sits below karma/logging (richer surface: a resolver, two independent wizard cascades, a message-pipeline stage, a diagnostics health-check heuristic, and two found unaudited mutation paths drag the as-written number down) but recovers strongly once G-2/G-A9/G-A10/G-A2 land — and, notably, **every one of the 9 remaining tier-3 units is a judgment-confirmed deliberate escape hatch**, not an unresolved gap (satisfies the exit bar's "every tier-3 unit is dispositioned" requirement for this subsystem).

#### Structural-gap flags

- **Permission/capability gates** — mixed fidelity. `!cleanuphistory` uses a literal Discord-permission check (`perms_or_owner(manage_messages=True)`); `!word*`/`!wordmenu`/`!cleanup` use `admin_or_owner()` (administrator-or-owner). The **ground-truth extractor mis-reports** the latter three as `perm="member"` (it doesn't recognize custom `commands.check` wrappers) — verified directly against source, not a bot bug, but a known ground-truth-tool limitation worth flagging generally. Separately, a **real** capability-declaration bug was found: `cleanup.settings.configure` (schemas.py:88) is referenced but never registered (see ledger row on `DomainPanelSpec`; the source comment warning about this is at schemas.py:44). The grammar (with amendments) expresses capability gates cleanly via `capability_required`; the gap is in today's code, not the grammar.
- **Setup/provisioning wizards** — present, twice (policy-panel builder + setup-wizard section) — **needs G-A9** (section registration) — the selector cascades themselves are already coverable by `SelectorSpec`.
- **`wait_for` wizard** — present (`!cleanuphistory`, corrected finding) — **needs G-A10** to replace it with a declarative, button-based preview+confirm (also fixes the shipped confirm/no-confirm inconsistency vs. `_ScanHistoryModal`'s Scan History button).
- **External API opt-ins** — none; cleanup calls no external service.
- **Audit/mutation seams** — **split three ways, not two** (correcting the original draft): (1) the cleanup-*policy* path (`governance/writes.py`) is a model-quality audited seam; (2) the prohibited-word/wordfilter path is **unaudited** (verified finding, no `emit_audit_action` anywhere in its call chain); (3) **`!cleanuphistory`'s bulk-delete apply path (`apply_history_cleanup_plan`) is ALSO unaudited** — verified by grep that `moderation_service.auto_delete` is never called from `history_cleanup.py` or around the `cleanup_cog.py:447` call site, even though the identical function IS wrapped in an audit call when invoked from moderation's own post-action sweep (`services/moderation_service.py:292-350`). The grammar (with amendments, specifically G-2 and a disciplined G-A10 `apply_handler` contract) can unify all three onto the same audited shape, but doesn't do so automatically.
- **Destructive actions** — message bulk-deletion has **mixed** audit coverage (correcting the draft's blanket "already sound" claim): `remove_unwanted_message`/`_delete_prohibited` (auto-mod) and `_ScanHistoryModal`'s scan+delete both correctly route through `moderation_service.auto_delete` (Lane A's own audited delete seam, `mod_logs` + `EVT_MOD_ACTION`) — this part is sound. But **`!cleanuphistory`'s bulk-delete does NOT** — it calls `history_cleanup.apply_history_cleanup_plan` directly, which performs a raw `message.delete()` with no audit trail at all. So the audit gap is **not limited to policy-configuration mutations** (word list, strict flag) as the original draft claimed — it also covers one of the three destructive-action code paths.
- **Lifecycle tasks / scheduled loops** — confirmed absent.
- **Governance/cache behavior** — cleanup policy resolution is **uncached** today (`governance/cleanup.py` queries the DB on every call, per `core/runtime/__init__.py:163`'s own comment) with a reserved-but-currently-no-op `EVT_CLEANUP_CHANGED` subscriber standing by for a future cache. Worth a production-grade note: if a cache is ever added, this hook is where invalidation must land (already documented in-repo, DEBT-003) — no new amendment needed, just execution.

#### Reconsider / optimize

**MAP** — 53 real units across 7 commands, ~19 panel/view units, 3 settings-class units + a capability-declaration bug, 4 declared capabilities, 4 listener-class units, 3 event units, 4 stores, **3 mutation-path units (one exemplary, two found unaudited gaps)**, 2 resolver/preset units, 2 profile-catalogue units, **1 diagnostics-heuristic unit**, 1 help hook (with a confirmed missing `HelpEntrySpec`).

**RECONSIDER** — verdict: **KEEP the domain, IMPROVE the implementation.** Prohibited-word filtering + command-message hygiene + per-scope cleanup policy is a legitimate, heavily-used governance capability (parented under "moderation") that `history_cleanup.py`'s own docstring explicitly designs for competitor parity ("Carl-bot/MEE6/Dyno parity" for embeds/links/attachments modes, :18). It should not be dropped or merged into another subsystem. But the *current* implementation has **four** concrete, fixable defects independent of the grammar rebuild (corrected from three): (1) the prohibited-word/strict-toggle mutation path is unaudited while the policy path is exemplary — one subsystem, two standards; (2) `cleanup.settings.configure` is referenced but never registered; (3) `!cleanuphistory` confirms via a legacy reaction `wait_for` while `_ScanHistoryModal`'s otherwise-identical bulk-delete has **no** confirm step at all — an internal UX inconsistency; **(4) `!cleanuphistory`'s bulk-delete apply path is ALSO unaudited (no `mod_logs` row, no `EVT_MOD_ACTION`) — a genuinely separate gap from (1), verified by grep, that the first-pass draft missed and incorrectly described as "already sound."** None of these are grammar-fit issues; they're bugs worth fixing regardless of the rebuild.

**SIMULATE** — the manifest sketch above shows 83.0% of the 53-unit surface reduces to tier-1/2 once G-1 (existing), G-2 (existing, generalized), and the three new lane-local amendments (G-A9 wizard sections, G-A10 preview-confirm-apply, G-A2 pipeline stages) land. The remaining 17% (9 units) are all independently judgment-confirmed as deliberate escape hatches — real per-message auto-mod evaluation, a scope-chain policy resolver, channel-classification heuristics, batch profile orchestration, a diagnostics staleness/legacy-row heuristic, and an unaudited-but-real bulk-delete mechanic — not unresolved grammar gaps.

**OPTIMIZE** — the optimal new-bot form: one `cleanup` manifest where (a) prohibited words are a G-2 list-valued `SettingSpec` (not a bespoke table + cog-level cache + duplicated add/remove modal code) with the audit trail built in by construction; (b) the anti-evasion toggle is a first-class boolean `SettingSpec`; (c) per-scope cleanup policy is a G-A9 wizard section whose scope/level cascade is `SelectorSpec`-driven and whose terminal step is ONE shared G-A10 `PreviewConfirmApplySpec`, reused verbatim by `!cleanuphistory`'s bulk-delete confirm (eliminating the `wait_for` anti-pattern and the confirm/no-confirm inconsistency in the same stroke) **— provided the shared `apply_handler` is required by convention to route through the audited delete seam, closing the found bulk-delete audit gap as well**; (d) the message-pipeline stage is a declared `MessagePipelineStageSpec` (G-A2) rather than bespoke `cog_load`/`cog_unload` registration calls; (e) a slash-command surface is added — cleanup ships **zero** `/` commands today (verified against `ground-truth/command-surface.json`: all 4 top-level entries are `prefix`/`group` kind), a real BENCHMARK gap against any competitor bot with slash-first UX. This collapses three independently-coded UI paths (word-menu modals, policy-panel builder, cleanuphistory wait_for) into two kernel-generated families (G-2, G-A10) plus the handful of genuinely bespoke evaluators.

**Dependency-layer guess:** **early governance.** Cleanup depends on moderation's audited `auto_delete` seam and on the governance mutation pipeline / scope-chain resolver (both foundational governance primitives shared across Lane A), and it is itself an upstream dependency of the message-pipeline ordering (stage order=10, ahead of counting/chain/xp stages per its own module comment) — so it must land in the same build wave as moderation + the governance resolver/pipeline + the message-pipeline kernel, before any feature cog that assumes messages are already auto-mod-filtered.

**Production-grade done-definition:** (1) every cleanup mutation (word add/remove, strict toggle, policy set/remove, **and the `!cleanuphistory` bulk-delete apply step**) is audited identically — DB write/delete + audit-log row + `audit.action_recorded`/`EVT_MOD_ACTION`, matching the already-correct policy pipeline's shape; (2) a `parity/` golden reproduces prohibited-word block+notice, anti-evasion de-obfuscation catch, the exact scope-resolution order (channel>category>guild>default, byte-identical to `governance/cleanup.py`'s current behavior), and all 7 `!cleanuphistory` modes' scan semantics; (3) all four verified bugs here (`cleanup.settings.configure` undeclared; unaudited word/strict mutations; **unaudited `!cleanuphistory` bulk-delete**; confirm/no-confirm UX inconsistency) are closed, not carried forward; (4) a slash-command surface exists for at least the read/open-panel commands.

**Outperform target:** `history_cleanup.py` already explicitly targets Carl-bot/MEE6/Dyno parity for its 7 scan modes, and the scope-chain policy resolver with dry-run preview + stale/ineffective-row diagnostics is already more operator-friendly than a typical bot's blunt "purge N messages" command — this is a plausible area where we already lead once the mutation-audit gaps (now two, not one) are closed. Final competitive verdict **pending Lane F**.

**Owner-gated/blocked/external-dependency status:** none beyond the standing Phase-3 design-approval gate that covers this entire audit — no external API, no owner-specific decision required for this subsystem's own design.

**Cross-lane dependency:** `disbot/core/runtime/cleanup_registry.py` + `disbot/services/game_state_cleanup.py` (both in this task's assigned file list) are **not** part of the Lane-A `cleanup` subsystem — they are a generic stale-session/game-state garbage-collection provider registry (`session_gc` invokes `cleanup_registry.run_all()`), populated by `game_state_cleanup.py`'s refund-on-abandon logic which imports `economy_service`/`game_state_service` (Lane B economy + Lane C/B game-state domains). The shared English word "cleanup" is a naming collision, not a subsystem relationship — excluded from this ledger per the task's instruction not to audit other lanes' subsystems. *(Independently re-verified this session by reading both files in full — confirmed correct, no change.)*

---

### role
_cogs: disbot/cogs/role_cog.py, disbot/cogs/role_grants_cog.py_

This is the largest, most structurally dense Lane A subsystem verified in this pass: 17 prefix commands (zero slash commands — see Reconsider), 2 scheduled loops, 3 gateway listeners, a full reaction-role + button/dropdown role-menu stack (8 DB tables), an exemptions system, a bespoke diagnostics panel, a role-lifecycle mutation seam, and two **previously un-ledgered setup-wizard sections** (`views/setup/sections/roles.py`, `views/setup/sections/role_templates.py`) plus a dormant Phase-4.5 governance-role-provisioning scaffold. Every pre-extracted `file:line` citation below was re-verified against source; all were found accurate except the hub-view mix-up noted at row 2. **This adversarial pass re-verified every citation independently and found a small number of additional defects — a wrong `file:line` citation, an incomplete migration citation, an internally-inconsistent emit-site count, an undercounted teardown gap, and one live in-scope file that was never cited anywhere in the draft — all corrected/flagged below. The headline "with amendments" fit number was also arithmetically wrong and is corrected (73→75, 67.6%→69.4%).**

**Unit kinds present:** command, panel, setting, listener, event, store, help, diagnostics, task (scheduled loop → `ManagedTaskSpec`). **Absent, confirmed:** `game` (no `LeaderboardSpec`/`ChallengeSessionSpec` facet — the closest artifact, `role_menu_pickup_stats`, is analytics, not a game); `bindings/resources` (no `BindingSpec`/`ResourceRequirement` declared — role binds no channel today, unlike logging/welcome/ticket).

#### Surface-unit ledger

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| `!roles` (hub open) | command | cogs/role_cog.py:354 | 1 | 1 | `panel_manager.get_or_render_panel` + `RoleHubPanelView()` — pure open-panel route, PanelRef-shaped like `!logging` |
| `!rolesettings` (alias, `ctx.invoke`) | command | cogs/role_cog.py:369 | 1 | 1 | duplicate route to the same hub — legacy alias, see Reconsider |
| `!roleinfo` (alias `ri`) | command | cogs/role_cog.py:375 | 2 | 2 | read-only card via `views.roles.role_info.build_role_info_embed` — no mutation, FieldsBlock-shaped |
| `!rolemenu` (hidden, `legacy_duplicate`) | command | cogs/role_cog.py:414 | 1 | 1 | duplicate route to the hub |
| `!rolecreator` (hidden, `legacy_duplicate`) | command | cogs/role_cog.py:423 | 1 | 1 | duplicate route to the hub |
| `!assignroles` (hidden, `panel_action`) | command | cogs/role_cog.py:433 | 3 | 3 | thin trigger of the real `role_automation` reconciliation engine — same escape-hatch class as blackjack's engine |
| `!createrole` (hidden, `panel_action`) | command | cogs/role_cog.py:444 | 3 | 3 | domain mutation through `RoleLifecycleService` + typed-error copy — karma-`!thanks`-shaped |
| `!deleterole` (hidden, `panel_action`) | command | cogs/role_cog.py:483 | 3 | 3 | irreversible domain mutation through the audited lifecycle seam |
| `!setrole` (hidden, `panel_action`) | command | cogs/role_cog.py:504 | 3 | 2 (G-A5) | writes a keyed threshold row via `role_automation.set_time_threshold` — RecordTableSpec-shaped config write |
| `!unsetrole` (hidden, `panel_action`) | command | cogs/role_cog.py:537 | 3 | 2 (G-A5) | same class — `clear_time_threshold` |
| `!debugroles` (hidden, `internal_admin`) | command | cogs/role_cog.py:567 | 2 | 2 | trivial read (`[r.name for r in ctx.guild.roles]`) — a `PanelRef`+list-block read provider, karma-card shaped |
| `!refreshmembers` (hidden, `internal_admin`) | command | cogs/role_cog.py:578 | 3 | 3 | real Discord side-effect (`ctx.guild.chunk()`) — deliberate escape hatch, `!logging test`-shaped |
| `!reactroles` (alias `reaktionsrollen`) | command | cogs/role_cog.py:651 | 3 | 3 | `reaction_role_service.bind_emoji` mutation + `message.add_reaction` side effect — beyond a pure config write, stays tier-3 even under G-A5 |
| `!removereactrole` | command | cogs/role_cog.py:689 | 3 | 3 | `unbind_emoji` mutation |
| `!listreactroles` | command | cogs/role_cog.py:709 | 2 | 2 | read-model embed list |
| `!temprole` | command | cogs/role_grants_cog.py:63 | 3 | 3 | `role_grants_service.grant_temp_role` — duration parse + escrow-like expiry, audited seam |
| `!temproles` | command | cogs/role_grants_cog.py:106 | 2 | 2 | read-model list (`list_active_grants`) |
| role-info card provider | panel | views/roles/role_info.py:48 | 2 | 2 | `build_role_info_embed` — the card companion to `!roleinfo`, karma-card precedent |
| `RoleHubPanelView` shell (persistent) | panel | cogs/role_cog.py:75 | 1 | 1 | ⚠ **scaffold correction**: the pre-extracted row cited `views/roles/main_panel.py:11` (`RoleHubView`) as the hub — that class is **dead code** (defined, never instantiated or imported anywhere in `disbot/`, confirmed by exhaustive grep, re-confirmed in this pass). The command-wired hub is `RoleHubPanelView` here |
| hub nav buttons ×7 (Create/Manage/Time/XP/Reaction/Diagnostics/Exemptions) | panel | cogs/role_cog.py:86-266 | 1 | 1 | capability-gated `PanelRef` navigation — already tier-1-expressible today (`CommandSpec`/`PanelActionSpec.capability_required` exists in the unamended §2 grammar); shipped code hand-rolls the check (`member_has_perms_or_owner(...)` inline) instead of declaring it — see Structural-gap flags |
| `ManagementPanel` role-list read | panel | views/roles/management_panel.py:18 | 2 | 2 | live `guild.roles` read-model, not store-backed |
| Edit-role flow (`_EditRolePickView`→`EditRoleModal`) | panel | views/roles/management_panel.py:136,159 | 3 | 3 | `RoleLifecycleService.apply(edit)` — rename/recolour/hoist/mentionable, gradient fallback logic |
| Delete-role flow (`_DeleteRolesView`→`_ConfirmDeleteView`) | panel | views/roles/management_panel.py:231,295 | 3 | 3 | irreversible mutation, confirm-required |
| Create-role flow (`RoleCreatePanel`+presets+`RoleCreateModal`) | panel | views/roles/creation_panel.py:23,45,63,239 | 3 | 3 | `RoleLifecycleService.apply(create)` |
| Post-create automation-tier prompt (`RoleAutomationView`/Modal) | panel | views/roles/creation_panel.py:312,355 | 3 | 3 | modal-chain wizard-lite (create → optionally set a tier) — no `wait_for` |
| Role-pack bulk-create flow (`RolePackView`+friends) | panel | views/roles/_role_pack_flow.py:44,66,201,234,257,325,347 | 3 | 3 | `ensure_role`/`ensure_color_role` — gradient/solid-fallback business logic, shared by both creation_panel and role_menu_builder |
| `role_packs.py` catalogue (curated packs) | setting | utils/role_packs.py:35,52 | 1 | 1 | pure declarative data, no I/O — same shape as karma's settings |
| `DiagnosticsPanel` read fields | diagnostics | views/roles/diagnostics_panel.py:36,59 | 2 | 2 | thresholds/reaction/exemption/member-cache/preflight-health/pickup-stat read-model; `DiagnosticProviderSpec` exists in the base §2 manifest but has no `CommandSpec`/`PanelActionSpec` route type to it directly, so the practical expression stays a `PanelSpec`+`BlockSpec` provider (logging-status-panel shaped), no amendment needed |
| `DiagnosticsPanel` "Refresh Members" button | panel | views/roles/diagnostics_panel.py:151 | 3 | 3 | real Discord side-effect (`guild.chunk()`) |
| `DiagnosticsPanel` "Run Assignment" button | panel | views/roles/diagnostics_panel.py:169 | 3 | 3 | triggers the real reconciliation engine via `interaction.client.get_cog("RoleCog")._assign_roles(...)` — ⚠ also a private cross-cog coupling smell, see Reconsider |
| `RoleExemptionsPanel` multi-role select | panel | views/roles/exemptions_panel.py:23,34 | 1 | 1 | shared `views.selectors.attach_multi_role_select` infra (generic, not role-specific) — `SelectorSpec` shaped |
| exempt/allow buttons ×4 | panel | views/roles/exemptions_panel.py:170-200 | 3 | 2 (G-A5) | `role_exemption_service.set_exemption` — keyed-row config write, RecordTableSpec-shaped |
| stack-toggle buttons ×2 | panel | views/roles/exemptions_panel.py:218,230 | 1 | 1 | routes through `views.settings.edit_boolean.toggle_setting` — the generic settings-toggle kernel workflow |
| `ReactionRolesPanel` Add flow (`_AddSourceView`/`_NewMessageModal`/`_AddBindingModal`/`_EmotesModal`/`_BindEmotesView`/`_AfterBindView`) | panel | views/roles/reaction_panel.py:406,520,590,631,666,769 | 3 | 3 | multi-step modal chain → `bind_emoji` audited mutation + `add_reaction` side effect — wizard-lite, confirmed **no `wait_for`** anywhere in `views/roles/` |
| `ReactionRolesPanel` Remove flow | panel | views/roles/reaction_panel.py:148 | 3 | 3 | `unbind_emoji` mutation |
| `ReactionRolesPanel` Mode button (normal/unique/verify) | panel | views/roles/reaction_panel.py:210 | 3 | 2 (G-A5) | `set_message_mode` — keyed-row enum config write, RecordTableSpec-shaped |
| `ReactionRolesPanel` nav buttons ×2 (Role Menus/Refresh) | panel | views/roles/reaction_panel.py:291,312 | 1 | 1 | pure navigation / re-render |
| `ReactionRolesPanel` "Clean up" button | panel | views/roles/reaction_panel.py:323 | 3 | 3 | `prune_dead_bindings` — real bulk-maintenance logic, deliberate escape hatch |
| `RoleMenuListView` "New Menu" button | panel | views/roles/role_menu_builder.py:163 | 1 | 1 | opens a blank builder — pure navigation |
| `RoleMenuListView` "Edit"/"Duplicate" buttons ×2 | panel | views/roles/role_menu_builder.py:192,229 | 2 | 1 (G-A6) | prefill an existing row into a fresh draft — thin read today; under G-A6 "load row into draft" is a kernel-generated step |
| `RoleMenuListView` "Delete" button | panel | views/roles/role_menu_builder.py:203 | 3 | 3 | `delete_menu` audited mutation |
| `RoleMenuListView` "Repost" button | panel | views/roles/role_menu_builder.py:214 | 3 | 3 | `set_menu_location` — deliberately **not** audited (post-flow, not config), real re-send logic |
| `RoleMenuBuilder` field editors ×12 (Template/Packs/Roles/Style/Text/Colours/Channel + nested Theme/Mode/Limit/Card/Counts) | panel | role_menu_builder.py:639-737,741,757,998-1073 | 3 | 2 (G-A6) | each edits one field of the in-memory draft (`self.title`/`self.style`/… — view-local attrs, role_menu_builder.py:472-483) and re-renders; zero domain code once a staged-draft primitive exists |
| `RoleMenuBuilder` "Advanced" nav button | panel | role_menu_builder.py:778 | 1 | 1 | pure navigation into the nested field-editor sub-panel |
| `RoleMenuBuilder` Post/Save commit | panel | role_menu_builder.py:795,854,874,918 | 3 | 3 | real orchestration beyond field-staging: `create_menu`/`update_menu` + message post/edit + persistent-view (re)bind + `Forbidden` handling — stays a deliberate escape hatch even under G-A6 |
| `RoleMenuView` self-assign (button/select/roster) | panel | views/roles/role_menu_view.py:153,181,212,232 | 3 | 3 | `toggle_role`/`apply_selection` — mode enforcement (unique/verify/max_roles), deliberately **not** audited (high-volume, plan §9) |
| `role_menu_counter` live debounced count renderer | panel | views/roles/role_menu_counter.py:1 | 3 | 3 | `renderer_override`-shaped escape hatch (async debounce scheduling), blackjack-board-renderer precedent |
| `role_menu_render.py` banner-card PNG renderer | panel | utils/role_menu_render.py:62 | 3 | 3 | `renderer_override`, lazy-PIL, `welcome_render` sibling |
| `role_menu_presentation.py` themes+templates catalogue | setting | utils/role_menu_presentation.py:31,42 | 1 | 1 | pure declarative data |
| `reattach_role_menus` boot rehydration | listener | views/roles/role_menu_view.py:447; bot1.py:325 | 3 | 3 | on-`ready`-time bulk `bot.add_view` rebind over every posted menu — real iterate+rebind logic; see Structural-gap flags |
| `TimeRolesPanel` actions ×4 (Add/Edit, Remove, Clear Missing, Run Now) | panel | views/roles/time_roles_panel.py:85,104,158,195 | 3 | 3 | `set_time_threshold`/`clear_time_threshold`/bulk-stale-cleanup/`_assign_roles` trigger |
| `TimeRolesPanel` "My Temp Roles" nav (`_TempRolesView`) | panel | views/roles/time_roles_panel.py:211,229 | 2 | 2 | read-model list |
| `XpRolesPanel` actions ×2 (Add/Edit, Remove) | panel | views/roles/xp_roles_panel.py:86,105 | 3 | 3 | `set_xp_threshold`/`clear_xp_threshold` |
| Setup-wizard section **"roles"** (time/XP tier drafting) | panel | views/setup/sections/roles.py:56,217,375,423 | 2 | 2 | ⚠ **missing from the pre-extracted scaffold entirely.** Stages a `set_role_threshold` `SetupOperation`; the actual write happens later through `role_automation` (already counted above) — the section's own browse+stage work is generic-workflow-shaped |
| Setup-wizard section **"role_templates"** (catalogue browse + stage `create_managed_role`) | panel | views/setup/sections/role_templates.py:93,312,411,460 | 2 | 2 | ⚠ **also missing from the scaffold.** Template catalogue is pure data; staging is generic; actual role creation happens later via `RoleLifecycleService` (already counted above) |
| `setup_role_templates.py` catalogue + validation | setting | services/setup_role_templates.py:64,80,201 | 1 | 1 | 6 built-in templates, pure data + pure validators (`validate_suggestion`/`validate_template`), no I/O |
| `governance/role_templates.py` + `core/resources/role_service.py` matcher | setting | governance/role_templates.py:49,82,109; core/resources/role_service.py:131,152 | 1 | 1 | pure declarative `RoleTemplate`/`RoleCollection` registry + `match_role_template`/`list_roles_by_tier`. ⚠ **confirmed dormant**: zero callers anywhere in `disbot/` outside their own modules (exhaustive grep, re-confirmed in this pass, including a check that `setup_role_templates.py`'s docstring mention of `governance.role_templates` is prose only, not a real import) — forward scaffold for an unbuilt "Phase 4.5" governance role-provisioning feature, not a live surface today |
| settings: `time_roles_stack`/`xp_roles_stack`/`reaction_roles_enabled` ×3 | setting | cogs/role/schemas.py:35,48,61 | 1 | 1 | plain bool `SettingSpec`s, `_CAPABILITY="role.settings.configure"` (defined line 26) — ⚠ **citation fix**: the draft cited lines 33,46,59 (off by 2 — those land on a blank line and two validator= lines from the *previous* entry); the actual `SettingSpec(` lines are 35, 48, 61 |
| registry capabilities ×4 | setting | utils/subsystem_registry.py:458-462 | 1 | 1 | declared capability strings. ⚠ **confirmed mismatch**: only `role.settings.configure` is ever referenced by real code (cogs/role/schemas.py:26); `role.threshold.configure`/`role.assignment.manage`/`role.reaction.manage` are declared but **never read or enforced anywhere** (exhaustive grep, re-confirmed) — actual gating is ad-hoc `@admin_or_owner()`/`@perms_or_owner(manage_roles=True)`/inline `member_has_perms_or_owner(...)` checks scattered per command/button, not the declared capability strings |
| registry `entry_points: ["rolemenu"]` | setting | utils/subsystem_registry.py:449 | 1 | 1 | declared entry point |
| `SKIP_ROLES` legacy key | setting | utils/settings_keys/role.py:6 | N/A | N/A | dead — "no longer read at runtime" per its own docstring; confirmed by grep (only a re-export remains); excluded from unit totals, flag for deletion in the rebuild |
| stores ×8 (`role_thresholds`, `role_automation_exemptions`, `reaction_roles`, `reaction_role_message_modes`, `role_grants`, `role_menus`, `role_menu_options`, `role_menu_pickup_stats`) | store | utils/db/migrations.py:266,284; migrations/052,056,078,079,080,081,089,103 | 1 | 1 | `StoreSpec` declarations, sole-writers = the respective `*_service.py`. ⚠ **migration citation fixed**: migration 081 (which actually creates `role_menu_pickup_stats`) was missing from the draft's list; 089 is only a later ALTER on the already-created `role_menus` (adds `card_template`/`card_text`), not a table origin. ⚠ **teardown gap corrected and widened**: only 5 of the 8 tables have a confirmed guild-teardown call in `guild_lifecycle.py` (`role_menus`+`role_menu_options` at line 661, `reaction_role_message_modes` at 706, `role_grants` at 731, `role_menu_pickup_stats` at 751). `role_thresholds`/`role_automation_exemptions` have **no teardown at all** (as the draft said). But `reaction_roles` *also* has no explicit teardown — `guild_lifecycle.py`'s own comment claims it "self-cleans when the host messages are deleted," but grep confirms **no code anywhere** (no `on_raw_message_delete` handler or otherwise) ever deletes `reaction_roles` rows on message or guild departure. So **3 of the 8** tables carry a probable INV-I gap, not 2, and the source comment's self-clean claim is itself unverified/apparently false |
| listener `on_raw_reaction_add` | listener | cogs/role_cog.py:591 | 3 | 2 (G-1) | thin fetch-and-forward (resolve member → `reaction_role_service.handle_reaction_add`) before the audited seam — karma react-to-thank precedent |
| listener `on_raw_reaction_remove` | listener | cogs/role_cog.py:616 | 3 | 2 (G-1) | same class |
| listener `on_member_join` | listener | cogs/role_cog.py:731 | 3 | 3 | **stays tier-3 honestly** (blackjack reaction-join precedent) — real inline threshold-filtering + `explain_assignment_for` decision logic, duplicated from `role_check` (see Reconsider) |
| task `role_check` (24h loop) | task | cogs/role_cog.py:284 | 3 | 3 | `ManagedTaskSpec` (already in base §2.8, no amendment) fully declares the trigger+dispatch shape; the residual tier-3 is `role_automation.compute_assignments`/`apply`'s real reconciliation algorithm — deliberate escape hatch, blackjack-engine class |
| task `_sweep_loop` (5-min expiry sweep) | task | cogs/role_grants_cog.py:42 | 3 | 3 | same class — `role_grants_service.sweep_expired`'s real expiry logic + Discord mutation |
| event `audit.action_recorded` (role mutation types) | event | services/role_automation.py:513,714,763,828,872; reaction_role_service.py:854-931; role_exemption_service.py:63; role_grants_service.py:32,93 | 1 | 1 | `EventSpec` declaration, `audited=True`. ⚠ **count corrected**: the draft said "13 emit sites" but its own mutation_types list sums to 15, and the actual literal `await emit_audit_action(...)` call-site count (grep-verified) is 11 — three of those 11 sites are parameterized helpers shared by several mutation kinds (e.g. one `_emit_menu_audit` call site backs `create/update/delete_role_menu`). Correct statement: **11 emit_audit_action call sites across 4 services, producing 15 distinct mutation-type values**: set_time_threshold, clear_time_threshold, set_xp_threshold, clear_xp_threshold, assign_role, remove_role, set_reaction_role, remove_reaction_role, set_reaction_mode, create_role_menu, update_role_menu, delete_role_menu, set_role_exemption, grant_temp_role, expire_temp_role; shared with every other subsystem — role is a producer, not the owner |
| event `role.lifecycle_changed` | event | services/role_lifecycle_service.py:51,400 | 1 | 1 | `EventSpec`, `observability_only=True` — confirmed **no `bus.on` subscriber anywhere** (grep, re-confirmed), only a catalogue mention (core/events_catalogue.py:134) |
| help `build_help_menu_view` | help | cogs/role_cog.py:362 | 1 | 1 | help-menu direct-nav hook returning the hub. ⚠ `role_grants_cog.py` has **no** equivalent hook — `!temprole`/`!temproles` are undiscoverable from the help menu |
| mutation seams (for completeness — **not separately tallied**, already reflected in the commands/panels above) | mutation-seam | role_lifecycle_service.py:144; role_automation.py:513,714,763,828,872; reaction_role_service.py:42,66,167,358,404,603,645,697; role_exemption_service.py:63; role_grants_service.py:32,93 | — | — | every write is an audited `*_service.py` seam (no `role_mutation.py` file — naming deviates from the `ticket_mutation.py` convention, not a violation); the two deliberately-unaudited paths (`toggle_role`/`apply_selection` member self-assign, `set_menu_message`/`set_menu_location` post-flow bookkeeping) are explicitly documented design decisions, not gaps. ⚠ **one real omission found**: `services/xp_role_sync.py` (`plan_level_role_assignments`, xp_role_sync.py:27) is a pure role-assignment planner in this audit's assigned file set, reusing `role_automation.Assignment`, and it IS live — called from `cogs/xp/listener.py:212` and `services/xp_migration.py:236` — but the draft never cited it anywhere (no ledger row, no disposition, no mention). It is *not* added to this subsystem's tally here because its only callers are xp-owned surfaces, not role-owned ones (unlike everything else in this row, which is reachable from a role command/panel/listener already counted above) — but it must be verified against the `xp` subsystem's own audit section so it is counted exactly once, not zero times |

#### Structural-pattern flags

- **Scheduled loop**: PRESENT ×2 — `role_check` (24h, cogs/role_cog.py:284) and `_sweep_loop` (5min, cogs/role_grants_cog.py:42). Both already fit `ManagedTaskSpec` for the trigger/dispatch shape (no amendment needed); the domain algorithms inside remain deliberate tier-3 escape hatches.
- **Gateway listener**: PRESENT ×3 — `on_raw_reaction_add`/`on_raw_reaction_remove` (cogs/role_cog.py:591,616, G-1 thin fetch-and-forward → tier-2) and `on_member_join` (cogs/role_cog.py:731, real logic → stays tier-3). Plus a boot-time (`on_ready`-adjacent) bulk rehydration, `reattach_role_menus` (bot1.py:325).
- **`wait_for` wizard**: CONFIRMED ABSENT — exhaustive grep of `views/roles/*.py` for `wait_for` returns zero hits (re-confirmed); every multi-step flow (creation, reaction-role add, menu builder) uses modal chains / view-swap callbacks instead.
- **Voice**: CONFIRMED ABSENT — no voice-state code anywhere in the assigned file set (re-confirmed).
- **Stateful game loop**: CONFIRMED ABSENT — no `GameFacet`/session shape; the closest thing (role menus) is config, not a game.
- **Setup/provisioning wizard**: PRESENT ×2 — the two setup-wizard sections (`roles.py`, `role_templates.py`), both missing from the pre-extracted scaffold, both stage `SetupOperation` rows applied at Final Review (draft lane, correctly used per `docs/ownership.md`).
- **In-session staged builder (new pattern, not in the BRIEF's danger-zone list)**: PRESENT — `RoleMenuBuilder`'s view-local draft object (see G-A6). Distinct from both the direct-mutation lane and the setup-wizard's persisted draft lane; a third staging mechanism worth the capstone's attention.
- **Capability declared vs. enforced-in-code**: PRESENT and mismatched — see the registry-capabilities row above; 3 of 4 declared capability strings are unused by any real check.

#### Manifest sketch

```python
"""Role — sketch in the §2 grammar (spike style). Illustrative subset;
see the ledger above for the full unit inventory."""

from __future__ import annotations

from tools.grammar_spike.spec import (
    Activation, BindingSpec, BlockSpec, CommandKind, CommandSpec,
    EventSpec, FieldSpec, GatewayListenerSpec, HandlerRef, HelpEntrySpec,
    ManagedTaskSpec, PanelActionSpec, PanelRef, PanelSpec, ProviderRef,
    SettingSpec, StoreSpec, SubsystemManifest, WorkflowRef,
)

_CAP = "role.settings.configure"  # only capability string actually enforced today

ROLE_MANIFEST = SubsystemManifest(
    key="role",
    display_name="Roles",
    description="Time-based and XP-based automatic role assignment.",
    emoji="🎭",
    category="management",
    visibility_tier="administrator",
    capabilities=(
        "role.settings.configure",   # enforced (cogs/role/schemas.py:26)
        "role.threshold.configure",  # declared only — never read (subsystem_registry.py:459)
        "role.assignment.manage",    # declared only — never read
        "role.reaction.manage",      # declared only — never read
    ),
    dependencies=("xp",),  # subsystem_registry.py:451 related_subsystems
    commands=(
        CommandSpec(
            name="roles", kind=CommandKind.PREFIX,
            summary="Open the role management hub.",
            route=PanelRef("role.hub"),
        ),
        CommandSpec(
            name="roleinfo", aliases=("ri",), kind=CommandKind.PREFIX,
            summary="Show a role's details.",
            route=PanelRef("role.info_card"),
        ),
        # TIER 3 — audited domain mutations (HandlerRef, justified):
        CommandSpec(
            name="createrole", kind=CommandKind.PREFIX,
            summary="Create a role.",
            route=HandlerRef("role.lifecycle.create",
                              justification="RoleLifecycleService.apply — rename/"
                              "recolour/gradient-fallback business logic"),
        ),
        CommandSpec(
            name="setrole", kind=CommandKind.PREFIX,
            summary="Set a time-based auto-role threshold.",
            # G-A5: today a HandlerRef; with RecordTableSpec, a declared
            # keyed-row upsert workflow (see role_thresholds table below).
            route=HandlerRef("role.automation.set_time_threshold"),
        ),
    ),
    panels=(
        PanelSpec(
            panel_id="role.hub", subsystem="role", title="🎭 Role Hub",
            audience="persistent",  # RoleHubPanelView, cogs/role_cog.py:75
            timeout_s=None,
            actions=(
                PanelActionSpec(
                    action_id="create", label="📝 Create",
                    handler=PanelRef("role.create_panel"),
                    capability_required=_CAP,  # TODAY: hand-rolled inline check instead
                ),
                PanelActionSpec(
                    action_id="diagnostics", label="🔧 Diagnostics",
                    handler=PanelRef("role.diagnostics"),
                    capability_required=_CAP,
                ),
            ),
        ),
        PanelSpec(
            panel_id="role.diagnostics", subsystem="role",
            title="🔧 Role System Diagnostics",
            body=(BlockSpec(kind="fields", provider=ProviderRef("role.diagnostics_read")),),
            actions=(
                PanelActionSpec(
                    action_id="run_assignment", label="▶️ Run Assignment",
                    handler=HandlerRef("role.automation.run_now",
                                       justification="triggers the real reconciliation engine"),
                ),
            ),
        ),
    ),
    settings=(
        SettingSpec(
            name="time_roles_stack", value_type="bool", default=False,
            settings_key="time_roles_stack", capability_required=_CAP,
            activation=Activation.ON_BY_DEFAULT,
        ),
        SettingSpec(
            name="reaction_roles_enabled", value_type="bool", default=True,
            settings_key="reaction_roles_enabled", capability_required=_CAP,
            activation=Activation.ON_BY_DEFAULT,
        ),
    ),
    events=(
        EventSpec(
            name="role.lifecycle_changed",
            payload_schema=(FieldSpec("guild_id", "int"), FieldSpec("operation", "str")),
            owner_subsystem="role", observability_only=True,
        ),
    ),
    gateway_listeners=(
        GatewayListenerSpec(
            gateway_event="on_raw_reaction_add",
            handler=HandlerRef("role.reaction.on_add",
                                justification="member resolve + fetch before the seam"),
            gate="setting:reaction_roles_enabled",
        ),
        # on_member_join deliberately OMITTED from thin-handler treatment —
        # its handler carries real decision logic (explain_assignment_for),
        # so it stays a HandlerRef with justification, not a bare gateway gate.
    ),
    tasks=(
        ManagedTaskSpec(
            name="role:tenure_sweep", trigger="interval:86400",
            handler=HandlerRef("role.automation.reconcile_tenure",
                                justification="real reconciliation algorithm — tenure "
                                "math, exemption filtering, hierarchy-safe batch apply"),
        ),
        ManagedTaskSpec(
            name="role:temp_grant_sweep", trigger="interval:300",
            handler=HandlerRef("role.grants.sweep_expired"),
        ),
    ),
    stores=(
        StoreSpec(table="role_thresholds", sole_writer="role.automation",
                  checkpoint_class="aggregate", invariant_tag="INV-ROLE-1"),
        StoreSpec(table="role_menus", sole_writer="reaction_role.service",
                  checkpoint_class="aggregate", reader_domains=("role_menu_view",)),
    ),
    diagnostics=(),  # no CommandSpec/PanelActionSpec route type to DiagnosticProviderSpec
                     # exists yet — role's diagnostics stays a PanelSpec+BlockSpec provider
    help=HelpEntrySpec(
        summary="Time/XP auto-roles, reaction roles, and role-menu self-assign.",
        examples=("!roles", "!setrole 7 Regular", "!reactroles 123456 🎉 @Winner"),
    ),
)

# G-A6 sketch (NEW, proposed — not in spec.py):
# @dataclass(frozen=True)
# class StagedBuilderSpec:
#     """A view-local, session-scoped multi-field draft, committed atomically."""
#     builder_id: str                      # e.g. "role.menu_builder"
#     fields: tuple[FieldSpec, ...]         # title/style/mode/theme/... typed fields
#     load_existing: ProviderRef | None     # populate from a StoreSpec row (edit mode)
#     commit: HandlerRef                    # terminal Post/Save — STAYS tier-3 (real
#                                            # orchestration: message post/edit, view rebind)

# G-A5 sketch (NEW, proposed — not in spec.py):
# @dataclass(frozen=True)
# class RecordTableSpec:
#     """A keyed table of typed records with declared add/edit/remove workflows."""
#     table: str                            # -> StoreSpec
#     key_kind: str                          # "role" | "channel" | "member"
#     fields: tuple[FieldSpec, ...]          # e.g. exempt_xp: bool, exempt_time: bool
#     row_audit: bool = True
```

#### Tier-3 dispositions

- **G-1 (reuse)** — `on_raw_reaction_add`/`on_raw_reaction_remove` (cogs/role_cog.py:591,616): thin fetch-and-forward before the audited `reaction_role_service` seam, identical shape to karma's react-to-thank. 3→2.
- **G-A6 (new, proposed above)** — `RoleMenuBuilder`'s 12 field-editor sub-views/modals (role_menu_builder.py:639-737,741,757,998-1073) and the Edit/Duplicate prefill (role_menu_builder.py:192,229): a recurring, generic "stage several field edits in memory, commit once" shape with no primitive in §2 today (distinct from both the direct-mutation lane and the setup-wizard's `SetupOperation` draft lane). The terminal commit (role_menu_builder.py:854-963) stays tier-3 — real message-post/edit + persistent-view-rebind orchestration, not staging mechanics.
- **G-A5 (new, proposed above)** — the four exempt/allow buttons (exemptions_panel.py:170-200), `!setrole`/`!unsetrole` (role_cog.py:504,537), and the reaction-role mode button (reaction_panel.py:210): all are "pick a target id, set N typed fields, upsert-or-delete the row, audit it" — a keyed-record-table CRUD shape neither `SettingSpec` (scalar) nor G-2 (scalar *lists*) covers. Reaction-role bind/unbind (role_cog.py:651,689) were **deliberately excluded** — they also perform a live `message.add_reaction`/fetch side effect beyond the table write, so they stay genuine tier-3.
- **Deliberate escape hatches (no amendment — real business logic, by design, §10.1-risk-5 class)**:
  - `role_automation.compute_assignments`/`apply`/`explain_assignment_for` (services/role_automation.py:212,355,513) — the tenure/XP reconciliation algorithm behind `role_check`, `!assignroles`, `on_member_join`, and the diagnostics "Run Assignment" button. Same class as blackjack's game-rules engine.
  - `role_grants_service.sweep_expired` (services/role_grants_service.py:93) — the temp-role expiry algorithm behind `_sweep_loop`.
  - `RoleLifecycleService.apply` (services/role_lifecycle_service.py:144) — create/edit/delete role, gradient-fallback + hierarchy/manageability checks.
  - `role_menu_counter`/`role_menu_render.py` — presentation renderers (`renderer_override`-shaped), same class as blackjack's board renderer and welcome's card renderer.
  - `reattach_role_menus` (views/roles/role_menu_view.py:447) — boot-time bulk `bot.add_view` rehydration; real iterate+rebind logic. Not a grammar gap per se (see Structural-gap flags for the generic-kernel-behavior argument), kept as a deliberate escape hatch for now since no primitive exists to point at.
  - `toggle_role`/`apply_selection` (reaction_role_service.py:645,697) — deliberately **unaudited** member self-assignment (documented design decision, plan §9: high-volume, opt-in). Not a gap — a conscious audit-scope boundary.
  - `services/xp_role_sync.py`'s `plan_level_role_assignments` — the XP-level role-planning algorithm shared by `cogs/xp/listener.py` and `services/xp_migration.py` (reuses `role_automation.Assignment`). Same class as `compute_assignments` above; flagged here rather than tallied because it is xp-owned by call site — see the mutation-seams row and Structural-gap flags.

#### Fit numbers

- **Units total: 108**
- **Tier-1/2 (as written): 54 → 50.0%**
- **Tier-1/2 (with amendments — G-1, G-A6, G-A5 applied): 75 → 69.4%** ⚠ **corrected**: the draft under review reported 73/67.6%. Re-summing the ledger's own per-row "tier with amendments" values, respecting each row's stated multiplicity (hub nav ×7, exempt/allow ×4, field editors ×12, stores ×8, capabilities ×4, settings ×3, etc.), gives 75, not 73. This is independently corroborated by the draft's own prose two paragraphs below, which already states "~21 of the 54 as-written tier-3 units move under the three proposed amendments" — 54+21=75, not 73 — so the draft's own text contradicted its own headline number. The 21 moved units break down exactly as: `!setrole`+`!unsetrole`+4 exempt/allow buttons+the mode button = 7 via G-A5, the 12 `RoleMenuBuilder` field editors = 12 via G-A6, `on_raw_reaction_add`/`on_raw_reaction_remove` = 2 via G-1 (7+12+2=21).

This places `role` between karma (87%) and blackjack (44%): it has an enormous amount of cleanly-declarative surface (8 stores, capability/entry-point registry rows, 3 real settings, 2 static catalogues, all navigation, all read-models — 54 units clear tier-1/2 with zero amendments), but also a very large count of *individually* real audited mutations (threshold writes, lifecycle create/edit/delete, reaction/menu CRUD, temp-role grants) that the established measure.py convention correctly keeps tier-3 (a `HandlerRef`-routed domain mutation is tier-3 regardless of how thin the code is, per the karma `!thanks` precedent) — so the raw percentage understates how "clean" this subsystem actually is. Most of its tier-3 mass is **correctly-kept-as-code business logic**, not missing primitives; only ~21 of the 54 as-written tier-3 units move under the three proposed amendments, and the rest (reconciliation engines, lifecycle mutations, renderers, boot rehydration) are legitimate, well-justified escape hatches.

#### Structural-gap flags

- **Permission/capability gates as declarations vs. code (the BRIEF's named watch-item, sharply illustrated here)**: role declares 4 capability strings in `subsystem_registry.py` but only 1 (`role.settings.configure`) is ever read by real code; every command/button instead hand-rolls `@admin_or_owner()` / `@perms_or_owner(manage_roles=True)` / inline `member_has_perms_or_owner(...)` checks. The *grammar* already has the fix (`capability_required` on `CommandSpec`/`PanelActionSpec`, no amendment needed) — this is a porting-discipline gap, not a design gap, but the rebuild must explicitly re-map the 4 declared capability names onto the actual current enforcement points (they don't cleanly correspond 1:1 today) rather than porting the ad-hoc checks verbatim.
- **Setup/provisioning wizard**: two full sections (`roles`, `role_templates`) exist and were entirely absent from the pre-extracted scaffold — both correctly use the `SetupOperation` draft lane (per `docs/ownership.md`'s direct-vs-draft split) and both express cleanly at tier-2.
- **Scheduled loops** (the BRIEF's named danger zone): **not actually a primitive gap here** — `ManagedTaskSpec` (already in the base, unamended §2.8 grammar) fully covers the trigger/dispatch shape for both `role_check` and `_sweep_loop`. The residual tier-3 mass is the reconciliation/expiry *algorithms* themselves, which is the intended, correct outcome (business logic stays in code) — this is a positive finding for the "is ManagedTaskSpec sufficient" question the task asked to test.
- **Gateway listeners**: `on_raw_reaction_add`/`remove` fit cleanly under G-1 (thin, 3→2); `on_member_join` is the honest counter-example (real logic inline, stays 3) — mirrors blackjack's reaction-join precedent exactly, confirming G-1's "thin vs. real" split is the right cut.
- **A third staging mechanism** (`RoleMenuBuilder`'s in-memory draft, G-A6) sits alongside the direct-mutation lane and the setup-wizard's persisted-draft lane — worth the capstone flagging as a pattern to either standardize (build G-A6) or consciously bless as three legitimate distinct lanes.
- **Audit/mutation seams**: fully compliant with `docs/runtime_contracts.md` §9 — every write is a `*_service.py` audited seam (no direct `pool.execute()`/`conn.execute()` outside `utils/db/`, confirmed by source read), and the two unaudited paths are explicit, documented design decisions rather than gaps.
- **Governance/cache behavior — widened**: `role_thresholds`/`role_automation_exemptions` lack a confirmed guild-teardown step in `guild_lifecycle.py` (as the draft found), **and** the `reaction_roles` table's assumed self-clean-on-message-delete (asserted in a `guild_lifecycle.py` comment) is not implemented anywhere in the codebase — grep confirms no listener anywhere deletes `reaction_roles` rows on message or guild departure. So **3 of the 8** role tables carry a probable INV-I gap, not 2. Flagged for the rebuild to close (an explicit per-guild `DELETE FROM reaction_roles WHERE guild_id=$1`, not merely re-asserting the unverified self-clean comment).
- **Untallied cross-subsystem module (new finding)**: `services/xp_role_sync.py` (`plan_level_role_assignments`) is real, live business logic in this audit's assigned file set — shared by `cogs/xp/listener.py:212` and `services/xp_migration.py:236` to plan XP-level role add/remove sets (stacking vs. single-role mode, XP-exempt roles), reusing `role_automation.Assignment`. The draft omitted it entirely: no ledger row, no disposition, no mention anywhere. It sits at the role/xp boundary — every caller is xp-owned, so it is not added to this subsystem's own unit tally — but the rebuild audit must confirm the `xp` subsystem's own section counts it (as a tier-3 deliberate escape hatch, same class as `role_automation.compute_assignments`), so it is not silently dropped from the *whole* capability audit.
- **Dead code, confirmed**: `views/roles/main_panel.py` (`RoleHubView`, 159 lines) has zero callers anywhere in `disbot/` — exclude entirely from the rebuild's inventory rather than porting it as "the" hub view (see the ledger correction above).

#### Reconsider / optimize

**MAP → RECONSIDER → SIMULATE → OPTIMIZE verdict: IMPROVE (redesign the config-surface half, keep the automation-engine half as-is).**

The subsystem is functionally rich and mostly well-engineered (audited seams throughout, real hierarchy/manageability safety checks, deliberate audit-scope decisions documented in source) but shows clear signs of organic accretion: a dead duplicate hub view, 4 declared-but-unenforced capability strings, 7 "hidden legacy_duplicate/panel_action" commands that exist only because panel buttons were added after the command surface (their own `extras={"classification": ...}` tags admit this), zero slash-command mirrors (role is the only Lane A subsystem checked with **no** `/x` entry point at all — every sibling audited above it has one), and duplicated threshold-filtering logic between `role_check` and `on_member_join` (both independently rebuild the same `threshold_objs` tuple — a shared helper in `role_automation` would remove the duplication and make `on_member_join` genuinely thin like `on_raw_reaction_add`, likely earning it the G-1 3→2 downgrade too).

**Optimal new-bot form**: keep the automation *engines* (`role_automation.compute_assignments`/`apply`, the exemption/stacking logic, the lifecycle service's gradient-fallback create/edit/delete) essentially as-is — they are correct, tested, and appropriately tier-3. Collapse the 7 hidden legacy-duplicate commands into pure panel actions (drop the redundant prefix-command surface — the panel already covers every one of them); delete the dead `main_panel.py`; re-map the 4 capability strings onto real `capability_required` declarations on every command/action (closing the declared-vs-enforced gap); add slash mirrors for the 6-8 highest-traffic commands (`/role info`, `/role setrole`, `/role reactroles`); and either build G-A6 (staged-builder primitive) or consciously standardize the role-menu builder's in-memory-draft pattern as the house style for any future multi-field creation flow, rather than leaving it a one-off.

**Dependency-layer guess**: mid-tier feature layer. It depends on core role/member primitives (L0) and the moderation-tier capability/audit substrate (early governance), and is itself a `related_subsystems` dependency of Lane B's `xp` (xp-role grants read role's thresholds) — so it must land after L0 + audit/capability foundations but before/alongside `xp`.

**Production-grade done-definition**: (1) every command/panel action's authorization traces to one declared `capability_required` string that is actually enforced (no ad-hoc decorator drift); (2) the tenure/XP reconciliation engine passes a `parity/` golden reproducing today's `compute_assignments` decision table (promote/demote/no-op/keep-previous-tier) byte-for-byte on a fixed member-roster fixture; (3) every one of the 8 stores has a confirmed guild-teardown step (including `reaction_roles`, whose current self-clean assumption is unverified); (4) the role-menu builder's staged-draft either uses G-A6 or an explicitly documented equivalent, not a fifth bespoke pattern; (5) `!temprole`/`!temproles` are reachable from the help menu (parity with every other command surface in this lane).

**Outperform-target status**: role automation (time+XP auto-roles) is a Carl-bot/MEE6/Dyno-standard feature; this bot's version already **outperforms** the common Discord-bot baseline on two axes verified in source — (a) classified, batched failure reporting (`role_automation.summarize_failures`, "26 role automation errors" → one grouped WARNING instead of 26 individual ones) rather than silent per-member 403s, and (b) the button/dropdown role-menu surface with server-side mode enforcement (unique/verify/max_roles) + live sign-up counters, which several Carl-bot-class competitors gate behind a paid tier. Full head-to-head ecosystem comparison is `pending Lane F`.

**Owner-gated / blocked / external-dependency status**: none of this lane's work is blocked — no owner gate applies beyond the standing Phase-3 hard stop (design-spec approval) that covers the whole audit.

---

### channel
_cogs: disbot/cogs/channel_cog.py_

**Correction to the pre-extracted scaffold (high-leverage, verified):** the scaffold asserted "no
channel-specific store/settings-key module located ... channel commands appear to act directly on
Discord guild objects rather than through a persisted store" and left it at that. The "no DB
table" half is correct (channels are Discord-native objects; there is no `utils/db/channels.py`,
no `settings_keys/channel.py`, no migration) — but the scaffold **missed the audited mutation
seam**: every one of the 17 commands (and every create/delete/move/lock/unlock/rename/slowmode/
topic/permission-overwrite/clone panel action) routes through
`disbot/services/channel_lifecycle_service.py::ChannelLifecycleService`, which wraps every apply in
a typed `LifecycleResult`, calls `services.lifecycle.contracts.emit_lifecycle_audit()` (which
itself calls `services.audit_events.emit_audit_action()` — `disbot/services/lifecycle/contracts.py:32,125-155`)
and `bus.emit("channel.lifecycle_changed", ...)` (`disbot/services/channel_lifecycle_service.py:57,596-626`).
This is the channel-domain sibling of `services/role_lifecycle_service.py`, explicitly named as
such in the module docstring (`disbot/services/channel_lifecycle_service.py:14-30`), and it is
allowlisted as one of only two "audited manual creator" callers in
`tests/unit/invariants/test_no_silent_auto_create.py:70-82` (the other is
`role_lifecycle_service.py`). So: **no persisted store, but a real, audited `*_mutation.py`-shaped
seam** — the ledger below treats `ChannelLifecycleService` as the mutation-path unit the hard
rules ask for.

*Re-verification note (adversarial pass, 2026-07-02):* every file:line citation below was re-opened
against live source and checked; all 17 command line-ranges, all 7 panel-file class ranges, the
subsystem_registry.py capability/entry_point/parent_hub lines, the events_catalogue.py comment
block, the spec.py field citations, and the test_no_silent_auto_create.py allowlist range matched
exactly. Two citations were wrong or ambiguous (the `!slowmode`/`!topic` bound-constant refs and
the `_on_audit_action` line range — both corrected below with the right file/lines), and one
audited file (`views/selectors/channel.py`) had been silently skipped rather than footnoted as
shared infra like its four siblings — also fixed below. No tier assignment changed.

#### Surface-unit ledger

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| `!channelmenu` (cooldown 2/10s user) | command | `cogs/channel_cog.py:190-196` | 3 | 2 | Pure panel-open (`_ChannelManagerView`), but the shipped `@commands.cooldown` decorator (`:190`) has no declarative slot in `CommandSpec` as originally specced — forces an escape hatch just to keep the anti-spam behavior (**G-4**, reused). With G-4's `cooldown` field (already present in `spec.py:107`): pure `PanelRef` declaration, tier 2. |
| `!set` (channel/category access grant) | command | `cogs/channel_cog.py:209-230` | 3 | 2 | Bespoke handler: resolves "channel-or-category by name/mention/ID" via `_resolve_channel`/`_resolve_category` (`:85-103`, no declarative resolver exists), builds an overwrite dict, calls the lifecycle seam, formats one of ~3 strings. With **G-A7** (entity-resolver ref) + **G-A4** (`ResourceLifecycleSpec`, proposed below): thin composition of two registered refs, tier 2. |
| `!evt` (create/delete an "event" channel) | command | `cogs/channel_cog.py:232-275` | 3 | 2 | Two-branch dispatcher (`action.lower() == "create"/"delete"`) over two lifecycle ops; with G-A7+G-A4 the branching is a thin `HandlerRef` selecting a named workflow — no other bespoke rule. |
| `!create` (create + grant access) | command | `cogs/channel_cog.py:277-326` | 3 | 2 | Composes `create_channels` + `set_overwrite` (two service calls) plus rename-detection formatting; with G-A4 both are named workflow calls, response formatting stays a thin templated render. |
| `!bulkdelete` | command | `cogs/channel_cog.py:328-377` | 3 | 3 | **Stays tier 3 even with amendments** — genuine domain logic: single-arg path falls back to a substring/keyword channel-name search (`:344-347`) when there's no exact ID/name match. That's a real business rule (fuzzy match), a deliberate escape hatch, not a grammar gap. |
| `!del` | command | `cogs/channel_cog.py:379-402` | 3 | 2 | Thin resolve + delete; with G-A7+G-A4, tier 2. |
| `!list` (paginated category/channel inventory) | command | `cogs/channel_cog.py:404-434`; pagination in `views/channels/list_panel.py:60-112` | 3 | 2 | Bespoke chunking algorithm (12 categories/page, 1024-char field truncation, 6000-char/25-field Discord caps) — no declarative content-pagination primitive in §2 today (**G-A8**, proposed below). With G-A8: a declared paginated `BlockSpec` provider, tier 2 (kernel owns the chunk math; the category→lines rendering is a thin provider). |
| `!clone` | command | `cogs/channel_cog.py:436-467` | 3 | 2 | Thin resolve + clone; tier 2 with G-A7+G-A4. |
| `!move` | command | `cogs/channel_cog.py:469-496` | 3 | 2 | Thin resolve×2 + move; tier 2 with G-A7+G-A4. |
| `!lock` | command | `cogs/channel_cog.py:498-512` | 3 | 2 | Thin resolve + fixed `set_overwrite({"send_messages": False})`; tier 2 with G-A7+G-A4. |
| `!unlock` | command | `cogs/channel_cog.py:514-528` | 3 | 2 | Mirror of `!lock`; tier 2 with G-A7+G-A4. |
| `!channelinfo` | command | `cogs/channel_cog.py:530-567` | 2 | 2 | Already a pure read-only display (no mutation, no cooldown): a `FieldsBlock`/`ProviderRef` over a channel snapshot, with `format_overwrites` (`:122-143`) as the one thin provider-side render helper. Fits §2 as written — no amendment needed. |
| `!rename` | command | `cogs/channel_cog.py:569-595` | 3 | 2 | Thin resolve + rename; tier 2 with G-A7+G-A4. |
| `!slowmode` (alias `slow`) | command | `cogs/channel_cog.py:597-638` | 3 | 2 | Resolve + bounds clamp (`0..MAX_SLOWMODE_SECONDS`, checked in the cog at `channel_cog.py:611-618`; the constant `= 21600` is defined at `services/channel_lifecycle_service.py:86` and re-applied via a second `max(0, min(...))` clamp at `services/channel_lifecycle_service.py:432` — the cog's reject-and-message check and the service's silent clamp are two independent enforcements of the same bound) — the clamp is the same *shape* as **G-5** (declarative validator bounds), just on a command argument instead of a setting; folded into **G-A7**. Tier 2 with amendments. *(Corrected: the draft's citation `:611-618,432` named no file for the `432`, which — read against this row's own channel_cog.py citation — pointed at unrelated code; `432` is in channel_lifecycle_service.py.)* |
| `!topic` (alias `settopic`) | command | `cogs/channel_cog.py:640-670` | 3 | 2 | Resolve + length clamp (1024 chars; `MAX_TOPIC_LENGTH` is defined at `services/channel_lifecycle_service.py:88` and applied via slice-truncation at `services/channel_lifecycle_service.py:436`) + clear-if-blank; same G-A7/G-5-class bound. Tier 2 with amendments. *(Corrected: the draft's citation `MAX_TOPIC_LENGTH:88,436` likewise named no file; both line numbers are in channel_lifecycle_service.py, not channel_cog.py.)* |
| `!permissions` (allow/deny) | command | `cogs/channel_cog.py:672-701` | 3 | 2 | Resolve + a 2-value enum arg (`allow`/`deny`) validated by hand (`:689-691`) — an `allowed_values`-style bound, folded into G-A7. Tier 2 with amendments. |
| `!bulkcreate` | command | `cogs/channel_cog.py:703-745` | 3 | 3 | **Stays tier 3** — the trailing-arg-is-a-category heuristic (`:714-718`, "is the last positional arg a category name?") is genuine ambiguous-parse domain logic, a deliberate escape hatch. |
| `build_help_menu_view` (help-menu direct-nav hook) | help | `cogs/channel_cog.py:201-207` | 2 | 2 | Returns the same `_ChannelManagerView` panel via `help_ctx_shim` — a thin nav re-route, no domain code. Fits §2 as written. |
| `_ChannelManagerView` (hub: Create/Delete/Restrict/Move/Visibility) | panel | `views/channels/main_panel.py:22-158` | 2 | 2 | Five `PanelActionSpec` buttons, each routing to another `PanelRef` — matches `logging.panel`'s style exactly (`tools/grammar_spike/manifests/server_logging.py:145-215`). No domain code (four of the five buttons carry a thin "no channels found" empty-state guard before routing — boilerplate, not business logic). |
| `_CreateSubView` (multi-name + category picker + batch create) | panel | `views/channels/create_panel.py:41-350` | 3 | 2 | `SelectorSpec`-shaped picks (already declarative) but the "Create Channel" button composes a batch call + a created/renamed/forbidden/failed result breakdown — thin with G-A4 (the typed `LifecycleResult` buckets already exist; only the render is domain code). |
| `_CustomNameModal` (1-field free-text channel name) | panel | `views/channels/create_panel.py:352-380` | 3 | 2 | Hand-written `discord.ui.Modal` subclass for one text field — no declarative modal-form primitive in §2 (**G-A1**, proposed below). Tier 2 with G-A1. |
| `_DeleteSubView` (multi-select delete picker) | panel | `views/channels/delete_panel.py:38-176` | 3 | 2 | Multi-select (declarative) + delete-button handoff to the confirm view; tier 2 with G-A4. |
| `_DeleteConfirmView` (irreversible-op confirm step) | panel | `views/channels/delete_panel.py:178-338` | 2 | 2 | **Already covered as-written**: `PanelActionSpec.confirm: bool` + `destructive: bool` (`spec.py:131,136`, with the `__post_init__` rule "destructive ⇒ style=danger") models exactly this "click again to confirm a destructive action" shape. No amendment needed; G-A4 would additionally push the confirmation *enforcement* itself into the kernel (today `confirmed=True` is a parameter the UI must remember to pass — `delete_panel.py:242`). |
| `_ChannelListPaginatorView` (◀/▶/Close inline paginator) | panel | `views/channels/list_panel.py:118-206` | 3 | 2 | Hand-rolled `discord.ui.View` subclass (documented exception — not a `BaseView`, per its own comment `:114-117`, and separately allowlisted in `architecture_rules/consistency_exceptions.yml:276`) that rebuilds its button row per page; tier 2 with **G-A8** (kernel-owned pagination nav). |
| `_MoveSubView` (multi-select + category/top/bottom) | panel | `views/channels/move_panel.py:80-317` | 3 | 2 | Multi-select (declarative) + 3 action buttons calling the lifecycle seam; tier 2 with G-A7+G-A4. |
| `_RestrictSubView` (multi-select lock/unlock) | panel | `views/channels/restrict_panel.py:34-288` | 3 | 2 | Same shape as `_MoveSubView`; tier 2 with G-A4. |
| `_VisibilitySubView` (multi-select channel picker for visibility) | panel | `views/channels/visibility_panel.py:39-178` | 3 | 2 | Multi-select + handoff; tier 2 with G-A4 (or plain `SelectorSpec`, already declarative). |
| `_SubsystemToggleView` (per-subsystem visibility matrix, ≤20 dynamic buttons, on→off→inherit cycle) | panel | `views/channels/visibility_panel.py:181-342` | 3 | 3 | **Deliberate escape hatch, not proposed as a new family** — a dynamic per-subsystem tri-state button grid with aggregate-state computation across N selected channels (`:207-327`). Real but narrow-scope UI logic; writes through `governance_service.set_subsystem_visibility` (delegates to `GovernanceMutationPipeline().set_visibility(...)` — verified in `governance/writes.py:488-499` — a shared, already-generic kernel-level pipeline; `visibility_panel.py:28-29,294-300`), so the *mutation* itself is already tier-2-shaped, only the dynamic grid rendering is bespoke. Too niche (one UI pattern, reused nowhere else in this file set) to justify a new named grammar family. |
| `channel.create.text` (capability) | setting (registry) | `utils/subsystem_registry.py:484` | 1 | 1 | Pure declarative capability string in `SUBSYSTEMS["channel"]`. |
| `channel.create.voice` (capability) | setting (registry) | `utils/subsystem_registry.py:485` | 1 | 1 | Same. |
| `channel.delete.any` (capability) | setting (registry) | `utils/subsystem_registry.py:486` | 1 | 1 | Same. |
| `channel.restrict.apply` (capability) | setting (registry) | `utils/subsystem_registry.py:487` | 1 | 1 | Same. |
| `channel.visibility.configure` (capability) | setting (registry) | `utils/subsystem_registry.py:488` | 1 | 1 | Same. **Accuracy flag** (not a tier issue): none of the 17 commands actually check `capability_required` against these strings (verified by grep — zero hits for `capability_required`/`CAPABILITY_TO_SUBSYSTEM` in `channel_cog.py`) — every command gates via the raw `is_admin_or_owner()` predicate (`core/runtime/permission_checks.py:36-53`, an administrator-permission-or-owner check), i.e. the **audience_tier lane**, not the **capability_required lane** (§2.2's two-lane model). Precisely: the predicate is `member_has_perms_or_owner(ctx.author, administrator=True) or ctx.author.id == ctx.guild.owner_id`, and `member_has_perms_or_owner` itself is `is_platform_owner(...) or has the named guild permission` — so there are really **three** escape hatches (platform owner, Discord admin permission, guild-owner id), not just "administrator-or-owner." The capabilities are declared, compiled into `CAPABILITY_TO_SUBSYSTEM` (`subsystem_registry.py:1224-1228`), but — as far as this pass could verify by grep — never consulted by anything for this subsystem's own commands. This is real-world orphaned metadata, not a grammar gap; see Reconsider/optimize. |
| `entry_points: ["channelmenu"]` | setting (registry) | `utils/subsystem_registry.py:474` | 1 | 1 | Pure declarative registry field. |
| `parent_hub: "admin"` | setting (registry) | `utils/subsystem_registry.py:482` | 1 | 1 | Matches `SubsystemManifest.parent_hub` (A-tagged arrangement field, `spec.py:474`) verbatim — no gap. *(Corrected: the draft cited `spec.py:474-476`; only line 474 is the `parent_hub` field — 475-476 are the sibling `hub_group`/`ui_priority` fields, also A-tagged but a different concern.)* |
| `channel.lifecycle_changed` (EVT_CHANNEL_LIFECYCLE) | event | `services/channel_lifecycle_service.py:57,239-246,354-361,596-626`; catalogued `core/events_catalogue.py:123-128` | 1 | 1 | Pure `EventSpec` declaration, `observability_only=True` — grepped for a `bus.on("channel.lifecycle_changed", ...)` subscriber and found **none**; the catalogue comment (`:124-128`) confirms it is "Advisory" only. Matches `EventSpec.__post_init__`'s rule that subscriber-less events must declare `observability_only=True` (`spec.py:332-337`) exactly. |
| `audit.action_recorded` companion (via `emit_lifecycle_audit`) | event | `services/lifecycle/contracts.py:125-155`; emitted from `services/audit_events.py:52-76` (`EVT_AUDIT_ACTION_RECORDED`, `:47`); consumed generically by `services/server_logging.py:773-834` (`_on_audit_action`, subscribes to the platform-wide event, not channel-specific) | 1 | 1 | Declarative "audited=True" flag on the mutation — the shared platform audit-companion event, not channel-owned, but channel's seam correctly emits it on every apply. *(Corrected: the draft cited `server_logging.py:788-825`, which starts inside the function's docstring and cuts off before the except block; the function's actual span, `def` through its `except`, is 773-834.)* |
| `ChannelLifecycleService` (rename / move / delete / reorder / set_overwrite / clone / set_slowmode / set_topic) | mutation seam | `services/channel_lifecycle_service.py:113-259,384-437` | 3 | 2 | Today: one bespoke coordinator class with an `_apply_one` if/elif ladder per operation (`:384-437`), each branch a couple of `discord.py` calls. With **G-A4** (`ResourceLifecycleSpec`, proposed below): the request/result/reversibility/audit/event/confirmation-gate boilerplate (all of `apply()` except the `_apply_one` body, `:159-258`) becomes kernel-generated (tier 1); only the actual per-op Discord call — a one-liner for `rename`/`move`/`set_slowmode`/`set_topic`/`set_overwrite`/`clone`/`delete`/`reorder` — stays a thin registered `HandlerRef` (tier 2). |
| `ChannelLifecycleService.create_channels` (the `create` op) | mutation seam | `services/channel_lifecycle_service.py:260-373,439-495` | 3 | 3 | **Stays tier 3** even with G-A4 — real business logic beyond a single API call: get-or-create category resolution (`_resolve_create_category:439-470`) and collision-safe naming (`_create_one:472-495`, via `utils.channels.safe_channel_name`). Legitimate escape hatch. |
| `utils.channels.safe_channel_name` | mutation seam (helper) | `utils/channels.py:8-16` | 3 | 3 | Real collision-avoidance algorithm (auto-increment suffix search) — thin but genuinely logic-bearing; a deliberate escape hatch, not a gap. |
| `utils.channels.get_or_create_category` | mutation seam (helper) | `utils/channels.py:19-28` | 3 | 3 | Same class — get-or-create lookup + create; deliberate escape hatch. |
| **setting** (subsystem-owned `SettingSpec`) | — absent | — | — | — | **Explicitly absent.** `channel` declares zero `SettingSpec`s — no `disbot/cogs/channel/schemas.py`, no `utils/settings_keys/channel.py` (confirmed by grep). Its only config-shaped surface is the 5 capability strings + `entry_points`/`parent_hub` above (registry metadata, not `SettingSpec`s). |
| **listener** (`@bot.event`/`@commands.Cog.listener`) | — absent | — | — | — | **Explicitly absent.** `channel_cog.py` has no `cog_load`, no `@commands.Cog.listener()` of any kind (verified by reading the full file — the only top-level function besides the class is `setup()`). No gateway listener, no message-pipeline stage. |
| **store** (DB table) | — absent | — | — | — | **Explicitly absent** (confirmed) — channels are Discord-native objects; no migration, no `utils/db/channels.py`. The mutation-seam rows above are the correct substitute unit, per the hard rules ("mutation paths ... or the audited service seam that performs writes"). |
| **game** / **diagnostics** | — absent | — | — | — | **Explicitly absent** — no `GameFacet`, no `DiagnosticProviderSpec` registration found for `channel`. |

#### Unit kinds present
command, panel, setting (registry/capability only — no true `SettingSpec`), event, help, mutation-seam (the audited service replacing `*_mutation.py`). **Absent, confirmed by grep/read, not merely omitted:** listener (no gateway/`@bot.event`/`bus.on` in the cog itself — see below), store (no DB table — channels are Discord-native), game, diagnostics.

**File-coverage footnote (added on re-verification):** two files in the audited set are correctly *not* channel-subsystem units, but the draft's original text didn't say so explicitly the way it did for the other shared-infra files, so recording it here for completeness:
- `disbot/views/selectors/channel.py` (`attach_channel_select`) — a generic windowed single-channel-picker primitive. Grepped for its callers: only `views/roles/role_menu_builder.py` (plus its own re-export chain `views/selectors/__init__.py`/`multi.py`). None of the channel subsystem's own panels use it — they all call `attach_multi_select`/`attach_windowed_select` directly. Same category as `core/resources/channel_service.py` et al. below: shared UI infra, not a channel-subsystem unit.
- `utils/channels.py` also defines `create_private_channel` (31-63) and `cleanup_category` (66-81) alongside the two functions above that channel *does* use. Grepped for callers: exclusively `cogs/blackjack_cog.py` and `cogs/rps_tournament/_helpers.py`/`views/blackjack/tournament_views.py` (private match-channel lifecycle for those games) — not `channel_cog` or any `views/channels/*` file. Not channel-subsystem units.

#### Structural-pattern flags
- **Gateway/`@bot.event` listener:** absent. `channel_cog.py` has no `@commands.Cog.listener()` of any kind and no `cog_load`; confirmed by a full read of the file (751 lines).
- **Message-pipeline stage:** absent — unlike `automod`/`image_moderation`/`cleanup` (same lane), channel registers no `message_pipeline` stage.
- **EventBus `bus.on` subscription (inbound):** absent in this subsystem's own files; `channel.lifecycle_changed` has **zero** subscribers today (grepped repo-wide for `channel.lifecycle_changed`/`CHANNEL_LIFECYCLE` outside its own defining/cataloguing files — only one comment-only mention in `delete_panel.py`), so it is purely advisory/observability, matching the `events_catalogue.py:124-128` comment.
- **`wait_for`-based wizard:** absent. The multi-stage flows (`_CreateSubView`→confirm-free create; `_DeleteSubView`→`_DeleteConfirmView`; `_VisibilitySubView`→`_SubsystemToggleView`) are all message-edit state machines driven by persistent view callbacks, not a blocking `bot.wait_for(...)` loop. One single-step `discord.ui.Modal` (`_CustomNameModal`) — not a multi-step wizard.
- **Scheduled loop (`@tasks.loop`):** absent.
- **Voice — corrected:** the service layer *supports* voice-channel creation (`ChannelLifecycleService._create_one` has a `kind == "voice"` branch calling `guild.create_voice_channel`, `channel_lifecycle_service.py:489-494`), and voice channels *are* valid targets for the existing-channel operations (delete/restrict/move/lock select pickers explicitly include them — `main_panel.py:95,118,137` "No text or voice channels found"; `_overwrite_channel_ids` handles `discord.VoiceChannel` — `channel_cog.py:118`). But **no caller anywhere in the repo ever creates one**: every `create_channels(...)` call site (`channel_cog.py` ×3 — `!evt`, `!create`, `!bulkcreate`; `create_panel.py`; `ticket_mutation.py` ×2; `essential_setup.py`) either explicitly passes `kind="text"` or relies on the `"text"` default. The `kind="voice"` branch is therefore **currently dead/unreachable code**, not a live capability of this subsystem — this is not the "voice danger-zone" pattern (real-time audio/VC session state) either way, but it's also not an exercised creation path. Worth a Reconsider note: either wire a voice-creation entry point (a natural `/channel create ... type:voice` slash addition) or drop the unreachable branch.
- **`G-6` (per-kind command namespaces):** not exercised — `channel` ships **zero** slash commands (confirmed against `ground-truth/command-surface.json`: all 17 entries are `"kind": "prefix"`, matched name-for-name and alias-for-alias against the shipped source), so the prefix/slash disjoint-pool question never arises for this subsystem today. Worth flagging under Reconsider: adding slash equivalents (with native `ChannelSelect`/`RoleSelect` args) is the single biggest lever for shrinking the tier-3 surface, independent of G-A7.
- **Capability/permission gate:** all 17 commands gate via the raw Discord-permission predicate `is_admin_or_owner()` (`channel_cog.py:73-83`, wrapping `core/runtime/permission_checks.py:36-53`'s `member_has_perms_or_owner(administrator=True)` OR guild-owner-id match, itself internally an `is_platform_owner(...) or has-permission` check) — the **audience_tier lane**, not `capability_required`. This is expressible as pure data (`audience_tier="admin_or_owner"`) ⚠ *unverified*: whether the real kernel's `audience_tier` enum already has an "administrator-or-owner" value distinct from a plain "admin" capability floor (and whether it needs to separately model the platform-owner escape hatch) was not confirmed against the full prose design-spec doc (only `spec.py`'s bare `str` field was checked) — flagging as a minor open question, not a blocking gap.

#### Manifest sketch

```python
"""Channel subsystem expressed in the §2 grammar (spike style).

Verified against: disbot/cogs/channel_cog.py, services/channel_lifecycle_service.py,
services/lifecycle/contracts.py, utils/subsystem_registry.py:465-490,
views/channels/*.py (2026-07-02).

G-A1, G-A4, G-A7, and G-A8 below are PROPOSED (not yet in spec.py) — shown via comments, since
adding those dataclasses is out of scope for a read-only audit.
"""

from __future__ import annotations

from tools.grammar_spike.spec import (
    CommandKind,
    CommandSpec,
    BlockSpec,
    EventSpec,
    FieldSpec,
    HandlerRef,
    HelpEntrySpec,
    PanelActionSpec,
    PanelRef,
    PanelSpec,
    ProviderRef,
    SelectorSpec,
    SubsystemManifest,
)

_ADMIN_OR_OWNER = "admin_or_owner"  # ⚠ unverified kernel enum value — see notes

CHANNEL_MANIFEST = SubsystemManifest(
    key="channel",
    display_name="Channels",
    description="Channel and category creation, deletion, and restrictions.",
    emoji="📐",
    category="management",
    visibility_tier="administrator",
    capabilities=(
        "channel.create.text",
        "channel.create.voice",
        "channel.delete.any",
        "channel.restrict.apply",
        "channel.visibility.configure",
        # ⚠ accuracy flag: declared but NOT consulted by any command below —
        # every command gates via audience_tier, not capability_required.
    ),
    parent_hub="admin",  # subsystem_registry.py:482
    commands=(
        # cogs/channel_cog.py:190-196 — cooldown needs G-4 (reused, already in spec.py)
        CommandSpec(
            name="channelmenu", kind=CommandKind.PREFIX,
            summary="Open the interactive channel management panel.",
            route=PanelRef("channel.hub"),
            audience_tier=_ADMIN_OR_OWNER,
            cooldown=(2, 10, "user"),  # G-4
        ),
        # cogs/channel_cog.py:209-230 — G-A7 (resolver) + G-A4 (lifecycle workflow)
        CommandSpec(
            name="set", kind=CommandKind.PREFIX,
            summary="Set access for a channel/category.",
            usage="!set <name|id> <@role> <True/False>",
            audience_tier=_ADMIN_OR_OWNER,
            route=HandlerRef(
                "channel.set_access",
                justification=(
                    "TIER 3 as-written: bespoke channel-or-category resolver "
                    "(_resolve_channel/_resolve_category, no declarative "
                    "resolver primitive — G-A7) + set_overwrite call"
                ),
            ),
        ),
        # ... !evt, !create, !del, !clone, !move, !lock, !unlock, !rename,
        # !slowmode, !topic, !permissions all follow the same G-A7+G-A4
        # HandlerRef shape (route=HandlerRef("channel.<verb>", justification=...))
        # — omitted here for brevity, each cites the ledger row above.
        CommandSpec(
            name="bulkdelete", kind=CommandKind.PREFIX,
            summary="Delete multiple channels by name/id/keyword.",
            audience_tier=_ADMIN_OR_OWNER,
            route=HandlerRef(
                "channel.bulk_delete",
                justification=(
                    "TIER 3, deliberate escape hatch: substring/keyword "
                    "fallback search is real domain logic (channel_cog.py:344-347)"
                ),
            ),
        ),
        CommandSpec(
            name="list", kind=CommandKind.PREFIX,
            summary="List all categories and channels.",
            audience_tier=_ADMIN_OR_OWNER,
            # G-A8 (proposed): a PaginatedBlockSpec provider replaces the
            # hand-rolled chunking algorithm in views/channels/list_panel.py
            route=PanelRef("channel.list"),
        ),
        CommandSpec(
            name="channelinfo", kind=CommandKind.PREFIX,
            summary="Show channel details.",
            audience_tier=_ADMIN_OR_OWNER,
            route=PanelRef("channel.info"),  # already tier-2 as-written
        ),
        CommandSpec(
            name="bulkcreate", kind=CommandKind.PREFIX,
            summary="Create multiple channels; optional trailing category.",
            audience_tier=_ADMIN_OR_OWNER,
            route=HandlerRef(
                "channel.bulk_create",
                justification=(
                    "TIER 3, deliberate escape hatch: ambiguous trailing-arg "
                    "category-sniff heuristic (channel_cog.py:714-718)"
                ),
            ),
        ),
    ),
    panels=(
        PanelSpec(  # views/channels/main_panel.py:22-158 — pure nav hub
            panel_id="channel.hub", subsystem="channel", title="🛠️ Channel Management",
            audience="invoker",
            actions=(
                PanelActionSpec(action_id="create", label="Create Channel",
                                 handler=PanelRef("channel.create_panel")),
                PanelActionSpec(action_id="delete", label="Delete Channel",
                                 handler=PanelRef("channel.delete_panel")),
                PanelActionSpec(action_id="restrict", label="Manage Restrictions",
                                 handler=PanelRef("channel.restrict_panel")),
                PanelActionSpec(action_id="move", label="Move / Reorder",
                                 handler=PanelRef("channel.move_panel")),
                PanelActionSpec(action_id="visibility", label="Subsystem Visibility",
                                 handler=PanelRef("channel.visibility_panel")),
            ),
        ),
        PanelSpec(  # views/channels/delete_panel.py:178-338 — ALREADY tier-2 as-written
            panel_id="channel.delete_confirm", subsystem="channel",
            title="⚠️ Confirm Deletion",
            body=(BlockSpec(kind="list", provider=ProviderRef("channel.delete_targets")),),
            actions=(
                PanelActionSpec(
                    action_id="confirm_delete", label="Confirm Delete",
                    destructive=True, style="danger", confirm=True,  # spec.py:131,136 — no amendment needed
                    handler=HandlerRef("channel.delete_confirmed"),
                ),
            ),
        ),
        PanelSpec(  # views/channels/create_panel.py:41-350
            panel_id="channel.create_panel", subsystem="channel", title="➕ Create Channel",
            selectors=(
                SelectorSpec(selector_id="names", kind="entity",
                             on_select=HandlerRef("channel.pick_names"),
                             max_values=8),  # already-declarative multi-select
                SelectorSpec(selector_id="category", kind="channel",
                             on_select=HandlerRef("channel.pick_category")),
            ),
            actions=(
                # G-A1 (proposed) would replace this with a ModalFormSpec
                PanelActionSpec(action_id="custom_name", label="Custom Name",
                                 handler=HandlerRef("channel.open_custom_name_modal")),
                PanelActionSpec(action_id="create", label="Create Channel", style="primary",
                                 handler=HandlerRef("channel.create_batch")),  # G-A4
            ),
        ),
    ),
    events=(
        EventSpec(  # services/channel_lifecycle_service.py:57
            name="channel.lifecycle_changed",
            payload_schema=(
                FieldSpec("mutation_id", "str"), FieldSpec("guild_id", "int"),
                FieldSpec("operation", "str"), FieldSpec("outcome", "str"),
                FieldSpec("applied", "list[int]"), FieldSpec("failed", "list[int]"),
                FieldSpec("occurred_at", "str"),
            ),
            owner_subsystem="channel",
            observability_only=True,  # confirmed: zero bus.on subscribers today
            audited=True,
        ),
    ),
    stores=(),  # confirmed: no DB table — channels are Discord-native
    help=HelpEntrySpec(
        summary="Create, delete, move, lock, and configure server channels.",
        examples=("!channelmenu", "!create announcements @everyone False", "!lock general"),
    ),
)

# G-A4 SHAPE (proposed, not a real spec.py class — sketch only):
#
# @dataclass(frozen=True)
# class ResourceLifecycleSpec:
#     resource_kind: str                       # "channel" | "role" | ...
#     operations: tuple[LifecycleOpSpec, ...]  # name, reversibility, handler
#     audited: bool = True
#     confirmation_required_for: tuple[str, ...] = ()  # e.g. ("delete",)
#
# @dataclass(frozen=True)
# class LifecycleOpSpec:
#     name: str                 # "rename" | "delete" | "set_overwrite" | ...
#     reversibility: str        # reversible|compensatable|irreversible
#     handler: HandlerRef       # the one-liner Discord API call ONLY
```

#### Tier-3 dispositions

- **G-A4 `ResourceLifecycleSpec` (proposed grammar amendment)** — covers: `!set`, `!evt`, `!create`,
  `!del`, `!clone`, `!move`, `!lock`, `!unlock`, `!rename`, `!slowmode`, `!topic`, `!permissions`
  (12 commands), `_CreateSubView`, `_DeleteSubView`, `_MoveSubView`, `_RestrictSubView`,
  `_VisibilitySubView` (5 panels), and the `ChannelLifecycleService` simple-operation row (18
  units total). **Genuine grammar gap, not an escape hatch:** the shape (typed request → per-target
  apply → reversibility-classified confirmation gate → best-effort audit companion + domain event →
  typed per-step result) is fully generic and is independently reimplemented at least twice in this
  codebase (`channel_lifecycle_service.py` and `role_lifecycle_service.py`, cross-referenced by name
  in `channel_lifecycle_service.py:23-24`). Today none of that boilerplate is declarative; with
  `ResourceLifecycleSpec` it becomes tier-1 kernel machinery and only the one-line-per-operation
  Discord API call remains a registered `HandlerRef` (tier 2).
- **G-A7 `EntityResolverRef` (proposed grammar amendment)** — covers the "resolve a text argument to
  a live Discord object via mention/ID/name fallback" logic duplicated across the same 12 commands
  above (`_resolve_channel`/`_resolve_category`, `channel_cog.py:85-103`), plus the bounded-value
  arguments on `!slowmode` (0..21600, `channel_cog.py:611-618`, constant in
  `services/channel_lifecycle_service.py:86`), `!topic` (≤1024 chars, constant in
  `services/channel_lifecycle_service.py:88`), and `!permissions`
  (`allow`/`deny` enum, `channel_cog.py:689-691`) — the same *shape* as the existing **G-5**
  (declarative validator bounds) but applied to command arguments instead of settings. **Genuine
  grammar gap:** `CommandSpec` (`spec.py:93-119`) has no parameter/argument schema at all today —
  only a free-text `usage` string — so any command needing typed/bounded/resolved arguments must
  currently embed that logic in a bespoke handler body.
- **G-A8 `PaginatedBlockSpec` (proposed grammar amendment)** — covers `!list` and
  `_ChannelListPaginatorView` (2 units). **Genuine grammar gap:** the hand-rolled chunking
  (12 categories/page) + per-field 1024-char truncation + a bespoke `discord.ui.View` paginator
  (`views/channels/list_panel.py:60-145`) exists purely to respect Discord's 25-field/6000-char caps
  — a mechanical, fully generic concern with no declarative primitive in §2 today.
- **G-A1 `ModalFormSpec` (proposed grammar amendment)** — covers `_CustomNameModal`
  (`create_panel.py:352-380`), a 1-field free-text `discord.ui.Modal`. **Genuine grammar gap
  (repo-wide, not just channel):** §2 has no declarative single-step modal-form primitive at all
  — every subsystem in this lane that needs a short text-input form (moderation's `_WarnModal` et
  al., cleanup's `_AddWordModal`/`_RemoveWordModal`, ticket's open-modal, the AI-policy channel
  editor) hand-writes a `discord.ui.Modal` subclass. Channel's instance is the smallest possible
  case (one optional text field), which is exactly why it's good evidence the primitive is missing
  at the *simplest* end, not just for complex forms.
- **G-4 `CommandSpec.cooldown` (reused, not new)** — covers `!channelmenu`'s
  `@commands.cooldown(2, 10, user)` (`channel_cog.py:190`). Already proposed by the spike; no new
  amendment needed.
- **Deliberate escape hatches (not proposed as new families):** `!bulkdelete` (substring/keyword
  channel search fallback, `:344-347`), `!bulkcreate` (trailing-arg-is-a-category heuristic,
  `:714-718`), `_SubsystemToggleView` (dynamic per-subsystem tri-state visibility grid,
  `visibility_panel.py:207-327` — narrow, single-use pattern, not worth a named family),
  `ChannelLifecycleService.create_channels` (category resolution + collision-safe naming,
  `:439-495`), `utils.channels.safe_channel_name` and `utils.channels.get_or_create_category`
  (`utils/channels.py:8-28`, real collision-avoidance algorithms). All six carry genuine,
  non-generic domain logic and should stay hand-written code in the rebuild.

#### Fit numbers

units total: **41**
tier-1/2 count (as-written): **13**
fit % as-written: **31.7%**
tier-1/2 count (with amendments): **35**
fit % with amendments: **85.4%**

*(Recomputed independently row-by-row on re-verification: 17 commands + 1 help + 10 panels + 7
registry-settings + 2 events + 4 mutation-seam units = 41 total, matching the draft; 13/41 and
35/41 both check out exactly. No tier was reassigned during this pass, so the numbers are
unchanged from the draft.)*

This is the **lowest as-written fit measured so far** (below karma 80%, logging 79%, and close to
blackjack's 44% — though for a *completely different reason*: not stateful games or gateway
listeners, but the near-total absence of a command-argument/resolver primitive (G-A7) hitting 12 of
17 commands, plus the ad-hoc lifecycle-mutation boilerplate (G-A4) hitting those same commands and
5 panels. ⚠ *unverified*: those other sections' fit numbers are not yet committed in this audit's
docs, so the cross-comparison itself could not be checked against ground truth this pass — treat the
channel-section numbers as verified, the comparison to karma/logging/blackjack as carried over
as-is.). With the four proposed amendments (G-A1, G-A4, G-A7, G-A8) plus the reused G-4, fit recovers to 85.4%
— in line with karma/logging — leaving exactly 6 units as deliberate, well-justified escape hatches
(2 commands, 1 panel, 1 service method, 2 utility functions), none of them a grammar gap.

#### Structural-gap flags

- **Permission/capability gates:** covered by `audience_tier` (data), not a gap — but see the
  accuracy flag above: the subsystem's 5 declared `capabilities` are orphaned (never consulted by
  any command's actual gate). The rebuild should either wire delegated-role capability checks for
  real or drop the unused strings — either way this is a product decision, not a grammar deficiency.
- **Setup/provisioning wizard:** channel itself has none (no `wait_for`, no multi-step wizard) —
  but channel *is* a dependency of the server_management setup wizard's "Channels & log routing"
  section (`views/setup/sections/channels.py`), which stages `bind_channel` ops for every OTHER
  subsystem's declared `BindingSpec(kind=channel)` (economy's `log_channel`, xp's
  `announce_channel`, verified at `views/setup/sections/channels.py:58-90`). That
  section is server_management's own unit, not channel's — noted here only so the capstone doesn't
  double-count it.
- **`wait_for` wizard:** confirmed absent (see Structural-pattern flags).
- **External API opt-ins:** none — channel touches only the Discord API via `discord.py`.
- **Audit/mutation seam:** present and solid — see the correction at the top of this section. This
  is the one place channel already exceeds the "escape hatch" bar: the seam's boilerplate (not its
  per-op Discord calls) is a clean candidate for G-A4 to make tier-1.
- **Destructive actions:** `delete` (single + bulk) is the one `IRREVERSIBLE`-classified operation
  (`channel_lifecycle_service.py:70-83`) and already requires `confirmed=True`
  (`:191-199`) — modeled as-written via `PanelActionSpec.confirm`/`destructive` for the panel path;
  the prefix-command path (`!del`, `!bulkdelete`) passes `confirmed=True` unconditionally at the
  call site (`channel_cog.py:394,365`) because the *typed command invocation itself* is treated as
  the operator's confirmation (mirrors the module docstring's own reasoning, `:37-40`) — a
  reasonable, already-declarative design choice (WorkflowRef param), not a gap.
- **Lifecycle tasks / scheduled loops:** none.
- **Governance/cache behavior:** the one channel-scoped governance touch is
  `_SubsystemToggleView` → `governance_service.set_subsystem_visibility` →
  `GovernanceMutationPipeline` (shared, cross-subsystem infra, not channel-owned — confirmed the
  delegation in `governance/writes.py:488-499`) — already
  tier-2-shaped on the mutation side; only the per-channel aggregate-state UI is bespoke (see
  dispositions).

#### Reconsider / optimize

**MAP → RECONSIDER → SIMULATE → OPTIMIZE verdict: IMPROVE.** Keep the domain (server operators need
channel CRUD, and the audited `ChannelLifecycleService` seam is already good architecture — real
per-target results, typed reversibility, audit + event on every apply) but the *surface* is
over-fragmented: 17 single-purpose prefix verbs, each re-deriving the same channel/category
resolver, when Discord's own `discord.ui.ChannelSelect`/`app_commands` autocomplete already solves
"pick a channel" natively (as `views/ai/policy/channel_view.py` and `views/settings/edit_channel.py`
already demonstrate elsewhere in this same file set — channel already has a *better* native pattern
sitting right next to its own fuzzy-name-string commands). **Optimal new-bot form:** (1) keep the
panel UI as primary (it's already good — 5-button hub + selector-driven sub-panels); (2) replace the
17 prefix verbs with a much smaller slash-command set (`/channel edit <channel:ChannelSelect>
[rename] [slowmode] [topic] [lock]`, `/channel create`, `/channel delete`, `/channel move`) that
uses native `ChannelSelect`/`RoleSelect` args instead of name/mention/ID string parsing — this alone
retires the entire G-A7 resolver problem for the *new* surface (native Discord select widgets don't
need a text resolver) while the *shipped* prefix commands stay supported via G-A7 for back-compat;
(3) implement `ResourceLifecycleSpec` (G-A4) once and let `role`'s sibling service consume the same
primitive — this is a 2-for-1 win since role_lifecycle_service.py already shares the identical
shape; (4) fix the orphaned-capability accuracy gap by either wiring `capability_required` into the
two-lane check for real (delegated-admin support) or deleting the five unused strings; (5) either
wire a real voice-channel creation entry point or delete the currently-unreachable `kind="voice"`
branch in `ChannelLifecycleService._create_one` — verified dead across every call site in the
repo, so it is either an intentionally-reserved future hook (fine, but should say so in a comment)
or drift the rebuild shouldn't carry forward silently. **Dependency
layer:** early governance / infra-adjacent — L0 (bot/cog loader) → `core.resources.discovery` +
EventBus + audit_events (existing platform primitives) → **channel** → then every subsystem that
declares a `BindingSpec(kind=channel)` (logging, welcome, ticket, economy, xp, …) depends on
channels being creatable/pickable, so this should land early, immediately after L0 and the
audit/event-bus foundations, before the wizard sections and channel-binding features that consume
it. **Production-grade done-definition:** a `parity/` golden must show (a) every one of the 17
verbs (or their slash-equivalents) produces an identical Discord-side mutation to today's shipped
behavior on a fixture guild; (b) every mutation emits exactly one `audit.action_recorded` +
`channel.lifecycle_changed` pair with the documented payload shape; (c) `delete` (single + bulk) is
blocked without an explicit confirm step; (d) partial-batch failures degrade to per-target typed
results, never a silent drop; (e) `!list`-equivalent output never exceeds Discord's 25-field/
6000-char/1024-per-field caps on a 200+-channel fixture guild (regression-pinning the #1040 class
this code was already written to fix). **Outperform target:** *pending Lane F confirmation* for
specifics, but structurally: MEE6/Carl-bot/Dyno mostly manage channels via an external web
dashboard with single-channel-at-a-time edits and no audit trail exposed to the operator in-Discord;
our batch operations (bulk lock/unlock/restrict/move/delete via multi-select, `bulkcreate`/
`bulkdelete`) plus a fully audited, typed, partial-failure-aware mutation seam is already a
structural advantage over a bare `channel.edit()` call — this should be confirmed, not assumed, by
Lane F. **Owner-gated/blocked/external-dependency:** none beyond the standing Phase-3 owner gate —
pure internal Discord API work, no external service dependency.

**Cross-lane dependency:** `disbot/views/ai/policy/channel_view.py` is Lane D's (`ai`) own
channel-scoped AI-policy editor (writes via `services.ai_policy_mutation.set_channel_policy`) — it
selects a channel but owns no channel-subsystem behavior; included in the given file set only
because it names a channel, not audited here.

**Cross-lane dependency:** `disbot/views/settings/edit_channel.py` (`ChannelSettingSelectView`) is
the generic settings-framework's channel-typed setting-edit widget (Lane D's `settings` subsystem,
dispatched whenever any subsystem declares `SettingSpec(input_hint="channel")`) — shared
infrastructure, not channel-subsystem-owned code. Confirmed: it writes through
`services.settings_mutation.SettingsMutationPipeline`, not `ChannelLifecycleService`.

**Cross-lane dependency:** `disbot/views/setup/sections/channels.py` is server_management's (same
lane, different subsystem) setup-wizard section; its `_BINDING_TO_INTENT`/`_BINDING_TO_TAG` maps
name Lane B bindings (`economy`'s `log_channel`, `xp`'s `announce_channel`) — noted so the capstone
doesn't attribute those bindings to the `channel` subsystem.

**Cross-lane dependency (added on re-verification):** `disbot/views/selectors/channel.py`
(`attach_channel_select`) is generic reusable UI infra — a windowed single-channel-picker used by
`views/roles/role_menu_builder.py` (Lane A's `role` subsystem), not by any `views/channels/*.py`
panel (which all use `attach_multi_select`/`attach_windowed_select` directly). It was in the audited
file set; noted here (the original draft omitted it entirely) so the capstone doesn't miscount it as
a channel-subsystem unit.

**Note (not a ledger unit):** `disbot/services/setup_channel.py` implements a *third* channel-
creation pattern (the bot's private `#superbot-setup` onboarding channel) that calls
`core.runtime.guild_resources.ensure_channel` directly — bypassing both `ChannelLifecycleService`
and `ResourceProvisioningPipeline`. It is correctly outside `test_no_silent_auto_create.py`'s
allowlist (it never calls `guild.create_*` directly), but it is a third, separate "who creates
channels" code path worth the rebuild consolidating alongside G-A4 — flagged for the capstone, not
counted as a channel-subsystem unit since it's owned by onboarding/server_management, not
`channel_cog`. Similarly, `disbot/services/channel_recommender.py` and
`disbot/utils/channel_classify.py` (name-based classification + intent-scoring for the setup
wizard's channel-binding recommendations) and `disbot/core/resources/channel_service.py` (generic
`core.resources.discovery` read-model helpers reused by many subsystems' selectors) are shared
infrastructure referenced by the given file list but not owned by `channel_cog` — not counted as
channel-subsystem units. (`utils/channels.py`'s `create_private_channel`/`cleanup_category` join this
list — see the File-coverage footnote above.)

---

### welcome
_cogs: disbot/cogs/welcome_cog.py, disbot/cogs/welcome/schemas.py (services: disbot/services/welcome_service.py, disbot/services/welcome_config.py; utils: disbot/utils/settings_keys/welcome.py, disbot/utils/welcome_render.py)_

**Resolution of the scaffold's two flagged unknowns (both now closed):**

1. **Entry-role grant — FOUND.** `welcome_service._grant_entry_role` (disbot/services/welcome_service.py:215-259) is called from `handle_member_join` (disbot/services/welcome_service.py:309-310) whenever `policy.assigns_entry_role` is true. It resolves the role, no-ops if already held, then builds a `role_automation.Assignment` and calls **`services.role_automation.apply`** (disbot/services/role_automation.py:513, imported at welcome_service.py:235) — **not** a `role_lifecycle_service` as the scaffold's schema-hint guess suggested; the real seam is `role_automation.py`. `apply` → `_apply_single` calls `emit_audit_action` (disbot/services/role_automation.py:39 import — call sites at :660, :684, :747, :799, :856, :900) from `services.audit_events`, confirmed by the module docstring at role_automation.py:17-19: "Emits `audit.action_recorded` … for every successful change." So welcome opens **no parallel audit or mutation path** — confirmed, not merely asserted.
2. **Store — CONFIRMED ABSENT.** `grep -rn welcome disbot/utils/db/` returns nothing; the only migration files matching "welcome" (`032_automation_rules.sql`, `089_role_menu_card.sql`) hit the string only in unrelated comments (an automation-rules example template and a card-pattern reuse note), not a welcome table. All 12 settings are scalar guild-settings KV values resolved through `services.settings_resolution.resolve_value` (disbot/services/welcome_config.py:282, called throughout `load_policy` :275-360) — the shared, subsystem-agnostic legacy `guild_settings`/`settings` table, not a welcome-owned `StoreSpec`. The "no migration" confirmation lives in `cogs/welcome/schemas.py`'s module docstring (line 6) and `utils/settings_keys/welcome.py`'s module docstring (line 6) — **not** `cogs/welcome/__init__.py`, whose docstring never mentions migrations at all (a mis-citation in the first-pass draft, corrected here).

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !welcome | command | disbot/cogs/welcome_cog.py:155-162 (decorator 155, `def welcome_status` 162 — ground-truth `command-surface.json` confirms `lineno: 162`, `perm: manage_guild`, no aliases, prefix-only) | 3 | 2 | **corrected from the first-pass draft's 1/1.** The draft justified tier-1 as "matches karma's `!karma` card precedent" — but karma's actual precedent (`tools/grammar_spike/measure.py`) rates `!karma (card)` tier **2/2**, not 1; the "kernel open-panel workflow, no interactive components" phrasing is in fact lifted from logging's *different* tier-1/1 precedent (`!logging (panel open)`, whose panel needs no bespoke renderer at all). This command's entire visible behavior is opening `welcome.policy_status` — the very next row — which is tier 3 as-written / tier 2 with amendments because `_policy_embed` needs a bespoke `renderer_override` with real conditional logic + a variant-preview call. A command cannot be zero-domain-code tier-1 while the one panel it opens is bespoke tier-3; it inherits the panel's tier instead. |
| welcome.policy_status panel (`_policy_embed` renderer) | panel/view | disbot/cogs/welcome_cog.py:66-153 | 3 | 2 | bespoke `renderer_override`: conditional field composition (age-gate line, delete-after line, entry-role/channel mention resolution) plus a message-variant preview call — G-A13 removes the variant-preview part (the dominant complexity), leaving thin conditional field inclusion comparable to a FieldsBlock provider |
| join/leave/DM greeting embeds (`format_join_embed`/`format_dm_embed`/`format_leave_embed`) | panel/view | disbot/services/welcome_service.py:48-71, 74-93, 96-116 | 3 | 2 | each calls `welcome_config.pick_message` (random-variant selection, welcome_config.py:124-133) then `render_template` (placeholder substitution, welcome_config.py:254-272) before embed styling — real behavior with no declarative primitive today (G-5 covers only the write-time bounds, not this render-time behavior); G-A13 (proposed) makes template-render + random-pick a kernel workflow, leaving only embed color/thumbnail styling as thin presentation |
| welcome card image (`render_join_card` / `render_welcome_card`) | panel/view | disbot/services/welcome_service.py:140-161, disbot/utils/welcome_render.py:26-69 | 3 | 3 | deliberate escape hatch — image generation (initials disc, text layout, JPEG encode via the shared `utils.card_render.CardCanvas` engine, not raw PIL calls in this file) is genuinely bespoke per-subsystem composition; no §2 primitive should own image rendering, matching the same accepted pattern as other card renderers in the codebase (karma/profile/mining) |
| build_help_menu_view (help-menu direct-nav hook) | help | disbot/cogs/welcome_cog.py:167-185 | 2 | 1 | thin per-cog method that duplicates the same policy-status render + wraps a bare `HubView` — with amendments the manifest-driven kernel generates this dispatch automatically from `PanelSpec` + `parent_hub`, no hand-written per-cog method needed |
| help entry (summary + examples) | help | *(no HelpEntrySpec exists in the shipped code — this row is the manifest-target projection, not a shipped unit; see Manifest sketch)* | 1 | 1 | help-as-projection, same as karma/logging precedent (measure.py: "help-as-projection" / "projection") |
| on_member_join | listener | disbot/cogs/welcome_cog.py:46-53 | 3 | 2 | raw `@commands.Cog.listener()` gateway dispatch — no primitive in §2 as-written (G-1 gap); G-1 declares gate=`setting:welcome_enabled` + `HandlerRef`, tier-2 (matches logging's 8-listener precedent exactly) |
| on_member_remove | listener | disbot/cogs/welcome_cog.py:55-62 | 3 | 2 | same G-1 class as on_member_join |
| entry-role grant (`_grant_entry_role` → `role_automation.apply`) | mutation path | disbot/services/welcome_service.py:215-259 (call site :309-310); seam: disbot/services/role_automation.py:513 | 3 | 1 | as-written: `HandlerRef` carrying real logic (role resolution, already-held skip, `Assignment` construction, exception isolation) — but the logic is fully generic (grant the role bound by a setting, skip if already held, delegate to the audited seam), so **G-1x** (proposed) turns this into a zero-domain-code kernel `WorkflowRef`, tier-1 |
| welcome.member_greeted event | event | disbot/services/welcome_service.py:36 (const), :262-273 (`_emit_greeted`), emitted at :331; catalogued disbot/core/events_catalogue.py:84-89 | 1 | 1 | `EventSpec` declaration (`observability_only=True` — confirmed no `bus.on("welcome.member_greeted", …)` subscriber anywhere in `disbot/`, grep-verified); emit call lives inside the already-counted join-greeting handler, same treatment as karma's `karma.granted` (measure.py: "emit lives inside the audited seam") |
| enabled (master switch) | setting | disbot/cogs/welcome/schemas.py:133-145 (key `WELCOME_ENABLED`, disbot/utils/settings_keys/welcome.py:18) | 1 | 1 | plain bool + bool validator, kernel settings workflow + generated panel |
| join_enabled | setting | disbot/cogs/welcome/schemas.py:146-154 (key `WELCOME_JOIN_ENABLED`, settings_keys/welcome.py:21) | 1 | 1 | plain bool setting |
| leave_enabled | setting | disbot/cogs/welcome/schemas.py:155-163 (key `WELCOME_LEAVE_ENABLED`, settings_keys/welcome.py:22) | 1 | 1 | plain bool setting |
| channel | setting | disbot/cogs/welcome/schemas.py:164-176 (key `WELCOME_CHANNEL`, settings_keys/welcome.py:26; validator `_validate_id` :71-86) | 2 | 1 | as-written: registered validator ref over a legacy id-as-string scalar; with amendments: re-expressed as `BindingSpec(kind="channel")` — **§2 already ships this primitive** (no new amendment needed, this is a v1 mis-encoding, not a grammar gap) — see Manifest sketch |
| join_message | setting | disbot/cogs/welcome/schemas.py:177-189 (key `WELCOME_JOIN_MESSAGE`, settings_keys/welcome.py:29; validator `_validate_message` :105-129) | 2 | 1 | registered validator ref for variant-count/length bounds — G-5 generalizes (bounded-int → bounded string/variant-count) to make the *write-time* bounds declarative; the *render-time* template+variant-pick behavior is captured separately in the greeting-embeds row above (G-A13), not double-counted here |
| leave_message | setting | disbot/cogs/welcome/schemas.py:190-202 (key `WELCOME_LEAVE_MESSAGE`, settings_keys/welcome.py:30) | 2 | 1 | same G-5 class as join_message |
| entry_role | setting | disbot/cogs/welcome/schemas.py:203-216 (key `WELCOME_ENTRY_ROLE`, settings_keys/welcome.py:33; validator `_validate_id`) | 2 | 1 | same class as `channel` — `BindingSpec(kind="role")` re-encoding, no new amendment |
| card_enabled | setting | disbot/cogs/welcome/schemas.py:217-229 (key `WELCOME_CARD_ENABLED`, settings_keys/welcome.py:44) | 1 | 1 | plain bool setting |
| dm_enabled | setting | disbot/cogs/welcome/schemas.py:230-242 (key `WELCOME_DM_ENABLED`, settings_keys/welcome.py:39) | 1 | 1 | plain bool setting |
| dm_message | setting | disbot/cogs/welcome/schemas.py:243-255 (key `WELCOME_DM_MESSAGE`, settings_keys/welcome.py:40) | 2 | 1 | same G-5 class as join_message |
| min_account_age_days | setting | disbot/cogs/welcome/schemas.py:256-270 (key `WELCOME_MIN_ACCOUNT_AGE_DAYS`, settings_keys/welcome.py:49; validator `_bounded_int` via `_validate_min_account_age_days` :97-98, bounds 0-365) | 2 | 1 | bounded-int validator — exact G-5 class match to karma's `cooldown_seconds`/`daily_cap` |
| delete_after_seconds | setting | disbot/cogs/welcome/schemas.py:271-285 (key `WELCOME_DELETE_AFTER_SECONDS`, settings_keys/welcome.py:53; validator `_validate_delete_after_seconds` :101-102, bounds 0-3600) | 2 | 1 | same G-5 class |
| register_schemas (cog_load registration hook) | setting (registration) | disbot/cogs/welcome_cog.py:39-42; disbot/cogs/welcome/schemas.py:296-300 | 2 | 1 | thin one-line registration call — with amendments the manifest-driven kernel auto-loads `SubsystemManifest`, eliminating this hand-written `cog_load` call entirely (base spec behavior, no new G-amendment needed) |
| SUBSYSTEMS["welcome"] registry entry | subsystem-registry | disbot/utils/subsystem_registry.py:649-670 | 1 | 1 | pure declarative data (display_name/emoji/color/category/visibility_tier/capabilities/parent_hub/entry_points) mapping 1:1 onto `SubsystemManifest`'s own root fields — no gap |
| store: no dedicated welcome table | store | *(absence confirmed — see resolution note above)* | n/a | n/a | **not tallied as a unit** — informational row confirming the "no store" scaffold flag; settings ride the shared, subsystem-agnostic legacy KV table, never a welcome-owned `StoreSpec` |

**Unit kinds present:** command (1), panel/view (3: policy-status renderer, greeting/farewell/DM embeds, card image), listener (2: on_member_join, on_member_remove), event (1: welcome.member_greeted, observability-only), setting (12, all scalar KV), setting-registration (1), subsystem-registry (1), help (1 hook — no formal HelpEntrySpec shipped), mutation path (1: entry-role grant via `role_automation.apply`).
**Kinds explicitly absent:** panel-with-interactive-actions (no buttons/selectors anywhere in welcome's own code — `!welcome` is a static embed send, `build_help_menu_view` wraps a bare `HubView` with only the generic help nav, no welcome-specific actions), bindings/resources (`channel`/`entry_role` are shipped as legacy scalar `SettingSpec`s with `input_hint`, not `BindingSpec`/`ResourceRequirement` — welcome never offers to auto-create a channel, confirmed by grep for "resource"/"provision" across all welcome files, which surfaces only the unrelated `core.runtime.resources` channel/role-resolution helper), diagnostics (no `DiagnosticProviderSpec`/diagnostics-registry hit for "welcome" in any of the dedicated diagnostics modules, confirmed by grep), game (no `GameFacet`, no session/leaderboard concept applies), store (confirmed absent above).

**Structural-pattern flags:** **gateway listener** present (`@commands.Cog.listener()` on `on_member_join`/`on_member_remove`, welcome_cog.py:46,55 — the G-1 danger zone). **No** message-pipeline stage registration (welcome never touches the moderation/automod message-scan pipeline). **No** `wait_for` wizard in welcome's own code (`grep -rn "wait_for" disbot/cogs/welcome_cog.py disbot/cogs/welcome/schemas.py disbot/services/welcome_service.py disbot/services/welcome_config.py disbot/utils/welcome_render.py disbot/utils/settings_keys/welcome.py` → no matches) — however welcome's `enabled`/`channel`/`join_enabled`/`entry_role` settings **are** one step ("Greet new members") of the cross-subsystem **Essential Setup** wizard owned by `server_management` (disbot/views/setup/essential_setup.py:473-566, `GreetMembersStep`; the step is registered into the wizard's sequence at essential_setup.py:72, inside `EssentialFlow.__init__`'s `_steps` list — **not** line 2058, which is the unrelated `_CHECK_ESSENTIALS` health-check tuple that happens to reuse the word "welcome"), which writes through `SettingsMutationPipeline` (the audited direct lane, essential_setup.py:226-235) — correctly routed, not a parallel mutation path, but noted here since it's the nearest wizard/danger-zone contact point (out of scope to audit `essential_setup.py` itself — it belongs to `server_management`, same lane). **No** scheduled `@tasks.loop` anywhere in welcome's files. **No** voice. **No** stateful game loop.

#### Manifest sketch

```python
"""Welcome — member greetings, farewells, and the audited entry-role grant.

Source of truth (verified 2026-07-02):
    cogs/welcome_cog.py           — !welcome (155-162), on_member_join/remove
                                     (46-62), _policy_embed (66-153)
    cogs/welcome/schemas.py       — 12 SettingSpecs (register_schemas)
    services/welcome_service.py   — join/leave/DM orchestration, entry-role
                                     grant via role_automation.apply (215-259),
                                     EVT_WELCOME_MEMBER_GREETED (36, 262-273)
    services/welcome_config.py    — WelcomePolicy read model, template render
                                     + random-variant pick (108-133, 254-272)
    utils/welcome_render.py       — thin composition over the shared PIL-backed
                                     card_render.CardCanvas engine (escape hatch)

Two new tier-2 families this manifest forces beyond G-1..G-6:
    G-1x — GatewayListenerSpec.handler widened to Route (today HandlerRef-only,
           spec.py:363) so the entry-role grant is expressible as a generic,
           zero-domain-code `grant_role_from_binding` WorkflowRef.
    G-A13 — a declarative templated/multi-variant text value (placeholder
           contract + "---"-separated random pick) so join/leave/dm message
           rendering needs no bespoke renderer.
"""

from tools.grammar_spike.spec import (
    Activation, BindingSpec, BlockSpec, CommandKind, CommandSpec,
    EventSpec, FieldSpec, GatewayListenerSpec, HandlerRef, HelpEntrySpec,
    PanelRef, PanelSpec, ProviderRef, SettingSpec, SubsystemManifest,
    WorkflowRef,
)

_CAP = "welcome.settings.configure"

WELCOME_MANIFEST = SubsystemManifest(
    key="welcome",
    display_name="Welcome",
    description="Member greetings, farewells, and an optional entry role.",
    emoji="👋",
    category="community",
    visibility_tier="administrator",  # subsystem_registry.py:654
    capabilities=(_CAP,),
    parent_hub="community",  # subsystem_registry.py:666 — NOT server_management
    dependencies=("role",),  # soft: entry-role grant rides role_automation
                             # (proposed value — the live registry currently
                             # lists dependencies=[] for welcome; role/logging
                             # show up only via *other* entries' related_subsystems)
    commands=(
        # cogs/welcome_cog.py:162 — status-only, no buttons. TIER 3 as-written /
        # TIER 2 with G-A13 — inherits the tier of the panel it opens (below),
        # since a CommandSpec.route=PanelRef is only as "free" as that panel is.
        CommandSpec(
            name="welcome",
            kind=CommandKind.PREFIX,
            summary="Show the current welcome policy.",
            route=PanelRef("welcome.policy_status"),
            capability_required=_CAP,
        ),
    ),
    panels=(
        PanelSpec(
            panel_id="welcome.policy_status",
            subsystem="welcome",
            title="👋 Welcome",
            audience="invoker",
            body=(BlockSpec(kind="fields", provider=ProviderRef("welcome.policy_status")),),
            # TIER 3 as-written / TIER 2 with G-A13: _policy_embed's conditional
            # field composition + variant-preview call (welcome_cog.py:66-153).
            renderer_override=HandlerRef(
                "welcome.render_policy_status",
                justification="conditional fields (age-gate/delete-after) + "
                "template-variant preview — needs G-A13 to shrink further",
            ),
        ),
    ),
    settings=(
        SettingSpec(
            name="enabled", value_type="bool", default=False,
            settings_key="welcome_enabled", capability_required=_CAP,
            activation=Activation.OFF_UNTIL_OPT_IN,
            external_side_effects=True,  # can post + grant a role
            hint="Master switch — off by default.",
        ),
        SettingSpec(
            name="join_enabled", value_type="bool", default=True,
            settings_key="welcome_join_enabled", capability_required=_CAP,
            activation=Activation.ON_WHEN_BOUND,
        ),
        SettingSpec(
            name="leave_enabled", value_type="bool", default=False,
            settings_key="welcome_leave_enabled", capability_required=_CAP,
            activation=Activation.ON_WHEN_BOUND,
        ),
        SettingSpec(
            name="card_enabled", value_type="bool", default=False,
            settings_key="welcome_card_enabled", capability_required=_CAP,
            activation=Activation.OFF_UNTIL_OPT_IN,
        ),
        SettingSpec(
            name="dm_enabled", value_type="bool", default=False,
            settings_key="welcome_dm_enabled", capability_required=_CAP,
            activation=Activation.OFF_UNTIL_OPT_IN,
        ),
        # G-5 class: bounded-int validators become declarative bounds data.
        SettingSpec(
            name="min_account_age_days", value_type="int", default=0,
            settings_key="welcome_min_account_age_days",
            capability_required=_CAP,
            validator=HandlerRef("welcome.validate_age_days"),  # G-5 target: bounds=(0,365)
            presets=(0, 1, 7),
        ),
        SettingSpec(
            name="delete_after_seconds", value_type="int", default=0,
            settings_key="welcome_delete_after_seconds",
            capability_required=_CAP,
            validator=HandlerRef("welcome.validate_delete_after"),  # G-5 target: bounds=(0,3600)
            presets=(0, 30, 60),
        ),
        # G-A13 target shape (proposed — NOT expressible verbatim under §2
        # today; value_type/placeholders/multi_variant are the new fields):
        # SettingSpec(name="join_message", value_type="template",
        #     default="👋 Welcome {user} to **{server}**! You're member #{count}.",
        #     settings_key="welcome_join_message", capability_required=_CAP,
        #     placeholders=("user", "server", "count"), multi_variant=True,
        #     max_variants=10, max_variant_length=500)
        SettingSpec(  # shipped-form fallback (as-written, tier-2)
            name="join_message", value_type="str",
            default="👋 Welcome {user} to **{server}**! You're member #{count}.",
            settings_key="welcome_join_message", capability_required=_CAP,
            validator=HandlerRef("welcome.validate_message"),
        ),
        # leave_message / dm_message: identical shape to join_message, elided.
    ),
    bindings=(
        # OPTIMIZE: shipped today as legacy scalar SettingSpecs (channel/
        # entry_role, schemas.py:164-176/203-216) with input_hint pickers.
        # BindingSpec already exists in §2 — no amendment needed, just the
        # correct encoding (tier-1 vs. today's tier-2 validator-ref form).
        BindingSpec(
            name="channel", kind="channel", required=False,
            capability_required=_CAP,
            hint="Destination for the greeting/farewell embed.",
        ),
        BindingSpec(
            name="entry_role", kind="role", required=False,
            capability_required=_CAP,
            hint="Role granted the moment a member joins.",
        ),
    ),
    gateway_listeners=(
        GatewayListenerSpec(
            gateway_event="on_member_join",
            handler=HandlerRef(
                "welcome.on_member_join",
                justification="fan-out: age-gate check, entry-role grant, "
                "channel post, optional DM+card — orchestration, not thin",
            ),
            gate="setting:welcome_enabled",
        ),
        GatewayListenerSpec(
            gateway_event="on_member_remove",
            handler=HandlerRef(
                "welcome.on_member_remove",
                justification="farewell post gated by leave_enabled",
            ),
            gate="setting:welcome_enabled",
        ),
    ),
    # G-1x target shape (proposed — GatewayListenerSpec.handler is typed
    # HandlerRef-only today, spec.py:363, so this cannot type-check yet):
    #   GatewayListenerSpec(
    #       gateway_event="on_member_join",
    #       handler=WorkflowRef("grant_role_from_binding",
    #                            params=(("binding", "entry_role"),)),
    #       gate="setting:welcome_enabled",
    #   )
    events=(
        EventSpec(
            name="welcome.member_greeted",
            payload_schema=(FieldSpec("guild_id", "int"), FieldSpec("user_id", "int")),
            owner_subsystem="welcome",
            observability_only=True,  # confirmed: no bus.on subscriber exists
        ),
    ),
    diagnostics=(),  # none found — confirmed absent
    stores=(),  # confirmed absent — see resolution note
    game=None,
    help=HelpEntrySpec(
        summary="Greet joining members, bid farewell on leave, and "
        "optionally grant an entry role — all off by default.",
        examples=("!welcome",),
    ),
)
```

#### Tier-3 dispositions

- **`!welcome` command** — same disposition as the panel it opens (below): GRAMMAR GAP, partial (**G-A13**, proposed) for the variant-preview part; the remaining conditional field composition is a legitimate thin renderer. A `CommandSpec.route=PanelRef` is only as generated/kernel as the panel it points to — since `welcome.policy_status` needs a bespoke `renderer_override`, the command inherits that tier rather than being independently tier-1. **Corrected from the first-pass draft**, which rated this tier-1/1 by mis-citing karma's `!karma` card precedent (actually tier 2/2 in `measure.py`) and borrowing logging's *different* tier-1 rationale for a panel that, unlike welcome's, needs no bespoke renderer at all.
- **welcome.policy_status panel renderer (`_policy_embed`)** — GRAMMAR GAP, partial: the message-variant-preview call is **G-A13** (proposed); the remaining conditional field composition (age-gate line, delete-after line) is a **deliberate escape hatch** — thin, read-only, guild-state-dependent field inclusion is legitimately a small renderer, not a candidate for a new primitive by itself.
- **Greeting/farewell/DM embeds (`format_join_embed`/`format_dm_embed`/`format_leave_embed`)** — GRAMMAR GAP → **G-A13** (proposed, new): declarative templated/multi-variant text value. Evidence: disbot/services/welcome_config.py:108-133 (`split_message_variants`/`pick_message`), :254-272 (`render_template`), invoked from welcome_service.py:48-116.
- **Welcome card image (`render_join_card`/`render_welcome_card`)** — DELIBERATE ESCAPE HATCH: image generation (avatar disc, text layout, JPEG encode) via the shared `utils.card_render.CardCanvas` engine (disbot/utils/welcome_render.py:26-69) is genuinely bespoke per-subsystem composition with no sensible declarative form; matches the accepted pattern for every other card renderer in the codebase.
- **build_help_menu_view** — GRAMMAR GAP → reuses **no existing G-1..G-6**; the gap is that the manifest-driven kernel's help-menu router should auto-derive this per-cog nav hook from `PanelSpec` + `parent_hub` rather than requiring a hand-written method. This is covered by the base §2 design (help-as-projection, per karma/logging's "help entry" precedent), not a new amendment — just a base-spec capability not yet exercised in v1's hand-written glue.
- **on_member_join / on_member_remove listeners** — GRAMMAR GAP → reuse **G-1** (`GatewayListenerSpec`). Evidence: disbot/cogs/welcome_cog.py:46-62, raw `@commands.Cog.listener()`, no §2 primitive exists for gateway dispatch today.
- **Entry-role grant (`_grant_entry_role`)** — GRAMMAR GAP → propose **G-1x** (new): `GatewayListenerSpec.handler` is typed `HandlerRef` only (spec.py:363), blocking a `WorkflowRef` reference even though the shipped logic (disbot/services/welcome_service.py:215-259) is fully generic — resolve a role from a bound setting, skip if already held, delegate to the audited `role_automation.apply` seam. Widening the field type (or adding a parallel `action: WorkflowRef | HandlerRef`) turns this into a zero-domain-code kernel workflow, reusable by any future autorole-shaped feature.

#### Fit numbers

24 tallied surface units (excluding the informational "no store" row, which is not a real unit — see the ledger's `n/a` row).

| Scope | Surface units | Fit — spec as written | Fit — with proposed amendments (G-1, G-5, G-1x, G-A13) |
|---|---|---|---|
| welcome | 24 | **70.8%** (17/24) | **95.8%** (23/24) |

**Corrected from the first-pass draft's 75.0%/95.8%.** The with-amendments column is unchanged (95.8%; a unit moving from tier-1 to tier-2 still counts in the tier-1/2 bucket), but the as-written column drops from 18/24 to 17/24 once the `!welcome` command's tier is corrected from 1 to 3 (see the ledger row and its dispositions above).

Tier-3-as-written units (7): the `!welcome` command, the policy-status renderer, the 3 greeting/farewell/DM embed builders (counted as one row + one card-image row = 2 rows), the 2 gateway listeners, and the entry-role grant. Only the **welcome card image renderer** remains tier-3 with all four amendments applied (a deliberate, correctly-kept escape hatch) — every other tier-3 unit resolves to tier-1/2 once G-1/G-5/G-1x/G-A13 land. Welcome's with-amendments number (95.8%) sits in the same mid-90s range as logging (79→97%) and above karma's (80→87%) with-amendments outcome; its as-written number (70.8%) is somewhat below both karma's (80%) and logging's (79%) as-written floors, driven by welcome having a genuinely bespoke panel renderer where karma/logging's read-only panels did not — the two new amendments (G-1x, G-A13) are what close most of that gap, not G-1 alone.

#### Structural-gap flags

- **Permission/capability gates as declarations vs. code (BRIEF's named Lane-A watch item) — CONFIRMED PRESENT.** `!welcome` gates on a raw `perms_or_owner(manage_guild=True)` Discord-permission check (disbot/cogs/welcome_cog.py:161), while every `SettingSpec` in the same subsystem gates on the declared `"welcome.settings.configure"` capability string (disbot/cogs/welcome/schemas.py:62). These are two different authority mechanisms for what is conceptually the same subsystem's admin surface — the manifest (with amendments) should unify both under `capability_required`, closing a real (if narrow) governance-consistency gap, not a code gap.
- **Setup/provisioning wizard contact** — welcome's `enabled`/`channel`/`join_enabled`/`entry_role` settings are one step (`GreetMembersStep`, titled "Greet new members") of `server_management`'s Essential Setup wizard (disbot/views/setup/essential_setup.py:473-566, registered into the wizard sequence at :72), writing through `SettingsMutationPipeline` (the correct audited direct lane, essential_setup.py:226-235). No `wait_for` in welcome's own code. Not a gap — a positive finding (properly routed through the audited seam) — but it's the nearest wizard/danger-zone contact point for this subsystem and belongs to a sibling Lane-A subsystem, not to welcome's own audit.
- **Audit/mutation seam** — the one real mutation (entry-role grant) is fully audited via `role_automation.apply` → `emit_audit_action` (confirmed by direct source read, not assumed). No second, unaudited mutation path exists in welcome's files.
- **Destructive actions** — none. Welcome only adds (greets, DMs, grants a role); it has no revoke/kick/ban-class action.
- **Lifecycle tasks / scheduled loops** — none (confirmed absent by grep).
- **Governance/cache behavior** — `WelcomePolicy` is loaded fresh per event via `resolve_value` (no welcome-owned cache); out of scope to audit `settings_resolution`'s own caching (shared infra).
- **Gateway listeners (the G-1 danger zone)** — present, and (with amendments) fully expressible via `GatewayListenerSpec` — no new primitive family needed beyond G-1 itself, though the entry-role grant dispatched from inside `on_member_join` additionally needs **G-1x** to fully collapse to tier-1.
- **Stateful game loop / voice / `wait_for` wizard** — all confirmed absent in welcome's own code (grep-verified, no matches).
- **Cross-subsystem UI grouping** — `subsystem_registry.py` cross-references welcome from three sibling entries' `related_subsystems`: `counters` (:687), and `security` (:716, alongside `moderation`/`logging`) — the latter plausibly reflecting the shared anti-raid/account-age-gating theme between welcome's `min_account_age_days` gate and security's join-screening tier. Not itself a gap; noted for completeness (the first-pass draft named only `counters`/`community_spotlight`).

#### Reconsider / optimize

**MAP → RECONSIDER → SIMULATE → OPTIMIZE verdict: IMPROVE.** The design (fail-open dispatch, single-source-of-truth `WelcomePolicy`, one audited entry-role seam, no parallel mutation path) is sound and should be **kept as a behavior**; what needs improvement is the **manifest encoding**: `channel`/`entry_role` should move from legacy scalar `SettingSpec` to `BindingSpec` (already in §2, zero new amendments), the three message settings should adopt the proposed **G-A13** templated/multi-variant primitive instead of bespoke render code, and the entry-role grant should ride the proposed **G-1x** generic role-grant-on-event workflow so autorole becomes a reusable kernel capability rather than a welcome-specific `HandlerRef`. Net effect: nearly the entire subsystem collapses to tier-1/2, with only the card-image renderer legitimately remaining bespoke — and, once G-A13 shrinks the panel, the `!welcome` command that opens it collapses to tier-2 alongside it.

**Optimal new-bot form:** a `SubsystemManifest` with plain `SettingSpec` bool/int fields for the six scalar flags (enabled/join_enabled/leave_enabled/card_enabled/dm_enabled + the two G-5-bounded ints), two `BindingSpec`s (channel, role) reusing the same binding-set kernel workflow logging already uses, a `GatewayListenerSpec` pair (on_member_join/on_member_remove) gated on `setting:welcome_enabled`, with the entry-role grant riding **G-1x**'s `grant_role_from_binding` WorkflowRef (tier-1, zero domain code, reusable by any future autorole feature) and the three message fields riding **G-A13**'s templated/multi-variant value shape (tier-1/2, zero bespoke render code) — leaving only the card-image `renderer_override` as a legitimate, correctly-scoped escape hatch.

**Dependency-layer guess:** **early governance** — welcome sits just above the L0 settings/event-bus/audit foundation and the `role` subsystem's audited grant seam (a same-lane, Lane-A dependency), alongside `automod`/`moderation`/`logging`/`security` in the "safety/community platform" family (per the welcome_service.py docstring's own framing, "Q-0110", and confirmed by `security`'s registry entry also cross-referencing welcome). It should build right after `role`'s `role_automation.apply` seam and the generic `SettingsMutationPipeline`/`settings_resolution` infra are production-grade, and before higher-tier community features (`community_spotlight`, `counters`) that reference it only by UI grouping.

**Production-grade done-definition:** a `parity/welcome` golden that replays, for a matrix of policy configs (enabled × join/leave/dm × age-gate × card × delete-after): (1) the exact greeting/farewell/DM embed text (including deterministic random-variant choice under an injected `rng`, mirroring `tests/unit/services/test_welcome_service.py`'s existing determinism tests), (2) exactly one `audit.action_recorded` emission for the entry-role grant and zero for every other action, (3) the age-gate correctly suppressing greeting+DM+role-grant together (never partially), (4) fail-open behavior under injected config-read/send faults (dispatch never raises), (5) `delete_after` firing self-deletion exactly once. "Done" = this golden passes byte-for-byte against the current shipped behavior after the manifest port.

**Outperform-target status:** *pending Lane F* for a rigorous feature-matrix comparison against MEE6/Carl-bot/Dyno's welcome-message + autorole combos. Directionally (not yet benchmarked): our shipped random-variant rotation, the single-audited-path entry-role grant (no silent parallel write), the age-gate applied uniformly across greeting+DM+role-grant, and the fail-open dispatch design are not universally present in comparable bots' welcome features — Lane F should confirm this and flag anything we're missing (e.g. per-role welcome-message variants, richer welcome-card template presets).

**Owner-gated / blocked / external-dependency status:** none beyond the standing Phase-3 hard stop (owner-gated design-spec approval, applies to every subsystem equally). No external API dependency; PIL (Pillow, via the shared `card_render` engine) is an optional, already-vendored dependency with a graceful `None`-return fallback.

---

### ticket
_cogs: disbot/cogs/ticket_cog.py (services: disbot/services/ticket_mutation.py, disbot/services/ticket_service.py; store: disbot/utils/db/tickets.py; views: disbot/views/tickets/\*, disbot/views/setup/sections/ticket.py)_

Verified against source 2026-07-02. Cross-checked against `ground-truth/command-surface.json` (5 entries filtered on `cog_file` containing `ticket_cog.py`: `ticket`/group, `ticketpanel`, `ticketsetup`, `ticketlimit`, `ticketblacklist`/group — the ground truth only carries top-level `@commands.command`/`@commands.group` registrations, not `.command()` subcommands, so it doesn't list `ticket new/close/claim/add/remove` or `ticketblacklist add/remove` individually; all subcommands were verified directly against `cogs/ticket_cog.py`). All 5 ground-truth lines/perms re-verified independently (`lineno`/`perm` match source exactly: 135/member, 238/manage_guild, 245/manage_guild, 277/manage_guild, 289/manage_guild). Confirmed no `/ticket` slash command exists anywhere in the file (no `app_commands.command` decorator) — ticket's entire command surface is prefix-only, unlike karma/logging's dual prefix+slash surface.

**Two pre-extracted-scaffold line-citation fixes (re-verified, both correct):** `build_help_menu_view()` is at `ticket_cog.py:326` (the `async def` line), not `:329` (the return-type-annotation line of the same multi-line signature). `!ticketblacklist remove`'s `async def blacklist_remove(` is at `ticket_cog.py:311`; `:310` is the decorator line above it (kept as a citation of the same statement, not treated as an error, but noted for consistency with how sibling rows cite the `def` line).

**Corrected structural-pattern-flag phrasing (re-verified, correct):** the scaffold's flag line calls `bus.on("ticket.opened")`/`bus.on("ticket.open_requested")` a "gateway/bus.on listener" — this conflates two different things. There is **no raw Discord gateway listener** anywhere in `ticket_cog.py` (no `@commands.Cog.listener()` at all, confirmed by reading the full file and by grep). Both `bus.on(...)` calls are pure **EventBus subscriptions** — the already-native `EventSubscription` §2 primitive (same shape as `server_logging`'s 3 subscriptions), not the raw-gateway-listener gap `G-1` targets. `G-1` does **not** apply to ticket.

**Verified precisely (per task instruction):** `bus.on("ticket.opened", self._on_ticket_opened)` at `ticket_cog.py:57` and `bus.on("ticket.open_requested", self._on_ticket_open_requested)` at `ticket_cog.py:58`, both registered in `cog_load` (`:52-58`). The cross-lane AI trigger is confirmed exact: `disbot/services/ai_tools.py:2494` is the `"ticket.open_requested"` string inside `await bus.emit(...)` in `_make_open_support_ticket`'s handler closure (`:2463-2506`) — this is Lane D's `ai` subsystem emitting into ticket's subscription, not a ticket-owned emission; flagged once as the cross-lane bullet below, not audited here.

**Three parallel, uncoordinated authority mechanisms coexist** in this one subsystem (relevant to the `G-A12` proposal below): (1) `@perms_or_owner(manage_guild=True)` — a fixed Discord-permission-bit decorator on `ticketpanel`/`ticketsetup`/`ticketlimit`/`ticketblacklist`; (2) `is_ticket_staff()` (`views/tickets/_shared.py:21-35`) — a bespoke function checking platform-owner OR admin/manage_guild OR a per-guild-configured role, used by `claim`/`close`/`add`/`remove` (both command and panel-button paths); (3) the `subsystem_registry.py:254-256` capability strings (`ticket.ticket.open`, `ticket.ticket.manage`, `ticket.config.update`) — confirmed by grep to be referenced **nowhere else in the repo**, i.e. purely descriptive registry/help metadata, not wired to any enforcement path today. **Correction — a fourth, uncounted condition:** `close`'s real gate is not `is_ticket_staff()` alone; both `ticket_cog.py:164` (`ctx.author.id != int(ticket["opener_id"]) and not is_ticket_staff(...)`) and `control.py:134-135` (`is_opener or is_ticket_staff(...)`) independently inline an **"or the ticket's own opener"** override that lives outside `is_ticket_staff()` entirely, duplicated (De Morgan-equivalent, not buggy, just repeated) across the command and panel paths. `G-A12`'s declarative authority tier needs a resource-owner clause, not just the three role-bound mechanisms above — a scope addition to the same proposal, not a fifth mechanism.

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| `!ticket` (group, opens hub) | command | cogs/ticket_cog.py:135 | 2 | 2 | PanelRef→hub + read-model provider — same shape as karma's `!karma` card route |
| `!ticket new` (aliases open, create) | command | cogs/ticket_cog.py:141 | 3 | 3 | thick domain handler: eligibility check + audited channel-create+ACL+DB-insert+audit+event seam (`ticket_mutation.open_ticket`); stays real even with the G-A15 lifecycle facet — mirrors blackjack's session-start command staying (3,3) |
| `!ticket close` | command | cogs/ticket_cog.py:155 | 3 | 3 | thick domain handler: transcript build + dual-destination delivery (log channel + DM) + channel teardown — real side-effecting logic, not reducible by G-A15 (same discipline as blackjack's per-move handlers) |
| `!ticket claim` | command | cogs/ticket_cog.py:179 | 3 | 3 | thin-but-real domain handler: already-claimed/already-closed state check + audited write — same class as karma's audited grant seam (stays 3 even when thin) |
| `!ticket add` | command | cogs/ticket_cog.py:195 | 3 | 3 | real Discord permission-overwrite side effect (`channel.set_permissions`) + audit |
| `!ticket remove` | command | cogs/ticket_cog.py:211 | 3 | 3 | same class as add |
| `!ticketpanel` | command | cogs/ticket_cog.py:238 | 1 | 1 | posts a pre-declared persistent panel (`post_launcher`) — zero domain logic, kernel publish-panel workflow |
| `!ticketsetup` | command | cogs/ticket_cog.py:245 | 3 | 2 | dual-mode: no-args opens the config panel (declarative); positional-args form calls `update_config` directly from the cog — G-A14 makes that write a declared multi-field binding/setting workflow, but the unit stays a thin dispatch between two workflows, not a pure single declaration |
| `!ticketlimit` | command | cogs/ticket_cog.py:277 | 3 | 1 | direct `update_config(max_open_per_user=...)` with inline clamp `max(1, min(max_open, 25))` — the clamp is exactly G-5's declarative-bounds shape (reuse); G-A14 removes the hand-rolled persistence — together a pure `setting_edit` kernel workflow |
| `!ticketblacklist` (group, usage stub) | command | cogs/ticket_cog.py:289 | 1 | 1 | prints a usage string when invoked bare; no logic |
| `!ticketblacklist add` | command | cogs/ticket_cog.py:294 | 3 | 1 | membership add/remove on a list — exactly G-2's shape (reuse) + G-A14 for the non-KV persistence |
| `!ticketblacklist remove` | command | cogs/ticket_cog.py:311 | 3 | 1 | same class as add — reuse G-2 + G-A14 |
| `TicketLauncherView` | panel | views/tickets/launcher.py:19 | 2 | 2 | PersistentView, one button opening a modal — PanelSpec(audience=persistent) + PanelActionSpec(defer_mode=modal); fully declarable except the modal's own field-list (G-A1) |
| `post_launcher()` | panel | views/tickets/launcher.py:42 | 1 | 1 | pure send helper — kernel publish-panel workflow, no domain logic |
| `TicketOpenModal` | panel (modal) | views/tickets/_shared.py:72 | 3 | **3** | bespoke `discord.ui.Modal` subclass (field decl + `on_submit` calling the audited open seam). **Corrected from the draft's (3,2):** G-A1 declares the field-list/labels/validation, but `on_submit`'s call into `ticket_mutation.open_ticket` is the *identical* irreducible seam that keeps `!ticket new`/Claim/Close at tier 3 "regardless of thinness" — the document's own stated principle, applied inconsistently to this row. No proposed amendment closes the seam-call gap, so this stays tier 3 with amendments too |
| `TicketControlView` (shell) | panel | views/tickets/control.py:63 | 2 | 2 | PersistentView, 2 buttons — the view/authority-recheck shape (`_resolve`, `:70-90`) is declarable; the buttons' own mutation logic is counted separately below |
| Claim button | panel-action | views/tickets/control.py:92-117 | 3 | 3 | same audited claim seam as `!ticket claim` — declared alias surface (karma `!karma add` framing) |
| Close button (opens modal) | panel-action | views/tickets/control.py:119-141 | 3 | 3 | same class — opens `TicketCloseModal`, whose submit is the audited close seam |
| `TicketCloseModal` | panel (modal) | views/tickets/control.py:24 | 3 | **3** | bespoke Modal (reason field) + `on_submit` calling the audited close seam. **Corrected from the draft's (3,2)** for the identical reason as `TicketOpenModal` above: the "Close button" row's own rationale (immediately above) attributes its tier-3 status to *this* modal being "the one with the real seam" — that same seam cannot then score lower than the row that defers to it. Stays 3/3 |
| `TicketConfirmView` (shell) | panel | views/tickets/confirm.py:22 | 2 | 2 | **Split from the draft's single combined row** (see below). PanelSpec shape only — title, 2 actions, `timeout_s=120`, invoker-locked (`BaseView`) — fully declarable; the two actions' own logic is counted separately, mirroring the `TicketControlView` shell/action split two rows above |
| `TicketConfirmView` — Open button | panel-action | views/tickets/confirm.py:33-64 | **3** | **3** | **New row — the draft's single "TicketConfirmView (2,2)" row hid this.** Directly calls `ticket_mutation.open_ticket` (`confirm.py:58`) — the *exact same* audited seam as `!ticket new`/Claim/Close, not a HandlerRef abstraction over it. By the identical logic that made the draft split `TicketControlView` into a tier-2 shell + tier-3 Claim/Close actions, this button is a fourth "deliberate escape hatch" alongside those two, not part of the panel's declarative shell |
| `TicketConfirmView` — Cancel button | panel-action | views/tickets/confirm.py:66-77 | **1** | **1** | **New row.** Zero domain logic: disables both buttons, edits the message to a static "no ticket opened" acknowledgement — no service call, no state change. Fully expressible today as a bare PanelActionSpec with no handler |
| `TicketHubView` + `open_ticket_hub()` | panel | views/tickets/hub.py:63,137 | 2 | 2 | read-model status embed (FieldsBlock/provider) + Open/List/Post-panel buttons — same PanelRef+provider shape as karma's card; List is a read-only provider render, Post-panel is gated by `is_ticket_staff` (G-A12 target, counted once there) |
| `TicketConfigPanelView` (shell) + `open_ticket_config_panel()` | panel | views/tickets/config_panel.py:123,268 | 2 | 2 | PanelSpec shell (2 selectors + 3 actions); code comments (`:14-15`) explicitly cite the direct-vs-draft-lane choice — a legitimate staged-pick-then-commit direct-lane panel, not a draft-op wizard |
| `_StaffRoleSelect` | panel (selector) | views/tickets/config_panel.py:88 | 2 | 2 | SelectorSpec(kind=role); stages local view state, doesn't commit — same direct-lane pattern |
| `_LogChannelSelect` | panel (selector) | views/tickets/config_panel.py:105 | 2 | 2 | SelectorSpec(kind=channel); same staged pattern |
| Auto-create log channel button | panel-action | views/tickets/config_panel.py:158-186 | 3 | 2 | real provisioning (`ChannelLifecycleService`) + bespoke staff-role-only ACL overwrite; G-A14 removes the config-write half — the ACL-overwrite logic shares G-A15's "grant configured role visibility on a provisioned channel" territory (no separate amendment proposed for it) |
| Enable tickets button | panel-action | views/tickets/config_panel.py:188-225 | 3 | 1 | direct `update_config(enabled=True, staff_role_id=..., log_channel_id=...)` — a textbook multi-field binding_set/setting_edit kernel workflow once G-A14 makes the persistence declarative |
| Post open-ticket panel button (config panel) | panel-action | views/tickets/config_panel.py:227-265 | 1 | 1 | calls `post_launcher()` — same kernel publish-panel workflow as `!ticketpanel` |
| `build_help_menu_view()` | help | cogs/ticket_cog.py:326 | 1 | 1 | help-as-projection: returns the same hub panel — pure kernel projection, no new logic |
| **Support Tickets wizard section** (`SetupSection` registration) | **wizard-section** | views/setup/sections/ticket.py:33-78 | **2** | **2** | **Missing from the draft entirely** — the file was named in this section's own file list and citation line, but zero ledger row referenced it. Registers `SetupSection(slug="ticket", label="Support Tickets", style, emoji, order=72, depths, description_if_skipped, customize=_open_panel)` in `services.setup_sections.REGISTRY` so tickets appear as a `!setup` wizard step / `/setup-hub` button — previously reachable only via Help→Community or `!ticketsetup`. `run`/`customize` are a thin adapter: open the shared `ticket.config` panel + `setup_session.mark_in_progress` — same "thin dispatch to an already-declared panel" shape as `!ticketsetup`'s no-args path, but with no dual-mode branch, so no reduction is blocked; nothing here is escape-hatch domain logic |
| staff_role_id (required) | binding | utils/db/tickets.py:44 (TicketConfig: services/ticket_service.py:41) | 3 | 1 | shape is plain BindingSpec(kind=role); persisted via bespoke hand-written upsert SQL (no schemas.py at all) — G-A14 target |
| log_channel_id (optional) | binding | utils/db/tickets.py:44 | 3 | 1 | same class, BindingSpec(kind=channel) |
| **category_id (optional, dormant)** | **binding** | utils/db/tickets.py:44 (TicketConfig: services/ticket_service.py:42) | **3** | **1** | **Missing from the draft entirely.** A real, fully-plumbed column — `ticket_upsert_config` accepts it, `open_ticket` reads it (`ticket_mutation.py:132-133`) to pick the category new ticket channels are created under — but **zero UI surface ever sets it**: no command argument, no config-panel selector, not even mentioned in `build_ticket_config_embed`. Same dormant-field class as `ping_staff_on_open` below, which the draft *did* catch; this one it missed |
| max_open_per_user | setting | utils/db/tickets.py:44 | 3 | 1 | int setting, 1–25 bound (see `!ticketlimit`'s G-5 reuse) — G-A14 for persistence |
| ping_staff_on_open | setting | utils/db/tickets.py:44 | 3 | 1 | bool setting; ⚠ unverified — no command/panel currently exposes an editor for it despite being read at `ticket_cog.py:88` |
| enabled (master switch) | setting | utils/db/tickets.py:44 | 3 | 1 | bool setting — G-A14 for persistence |
| `ticket.ticket.open` | capability/registry | utils/subsystem_registry.py:254 | 1 | 1 | pure registry/help metadata (a string in a tuple) — trivially declarative; ⚠ flagged as currently disconnected from any enforcement (see Reconsider) |
| `ticket.ticket.manage` | capability/registry | utils/subsystem_registry.py:255 | 1 | 1 | same — unreferenced elsewhere (confirmed by repo-wide grep) |
| `ticket.config.update` | capability/registry | utils/subsystem_registry.py:256 | 1 | 1 | same |
| `bus.on("ticket.opened")` | listener (subscription) | cogs/ticket_cog.py:57 | 1 | 1 | EventSubscription declaration — already-native §2 primitive, same shape as logging's 3 subscriptions |
| `bus.on("ticket.open_requested")` | listener (subscription) | cogs/ticket_cog.py:58 | 1 | 1 | same |
| `_on_ticket_opened` handler body | listener (handler) | cogs/ticket_cog.py:67-97 | 3 | 2 | fetches channel, renders welcome embed + posts `TicketControlView` — the "render the resulting panel into the new channel" step a G-A15 lifecycle kernel would auto-generate; welcome-copy wording is the residual thin ref |
| `_on_ticket_open_requested` handler body | listener (handler) | cogs/ticket_cog.py:99-130 | 3 | 2 | resolves member + posts `TicketConfirmView` — same class of thin post-event render handler |
| `ticket.opened` (emit) | event | services/ticket_mutation.py:200-208 | 1 | 1 | EventSpec declaration; emit lives inside the audited open seam (already-native primitive) |
| `ticket.closed` (emit) | event | services/ticket_mutation.py:331-338 | 1 | 1 | same, inside the audited close seam |
| `emit_audit_action` mutation_type="open" | event (audit) | services/ticket_mutation.py:194 | 2 | 1 | one-line pass-through call today (tier 2, "declaration + registered thin call"); the design spec's §2.6 compile rule ("mutating handlers must name their audit event," kernel fires it) makes even this call kernel-generated — tier 1 with amendments |
| mutation_type="claim" | event (audit) | services/ticket_mutation.py:289 | 2 | 1 | same class |
| mutation_type="close" | event (audit) | services/ticket_mutation.py:326 | 2 | 1 | same class |
| mutation_type="add_participant" | event (audit) | services/ticket_mutation.py:422 | 2 | 1 | same class |
| mutation_type="remove_participant" | event (audit) | services/ticket_mutation.py:448 | 2 | 1 | same class |
| mutation_type="config" | event (audit) | services/ticket_mutation.py:562 | 2 | 1 | same class |
| mutation_type="blacklist" | event (audit) | services/ticket_mutation.py:593 | 2 | 1 | same class — 7 distinct call sites total, confirmed by direct read + grep (the cleanest audited-mutation surface in Lane A, per the task brief) |
| `ticket_config` table | store | migrations/098_tickets.sql:23 | 1 | 1 | StoreSpec → generated sole-writer fence |
| `tickets` table | store | migrations/098_tickets.sql:46 | 1 | 1 | StoreSpec |
| `ticket_blacklist` table | store | migrations/098_tickets.sql:78 | 1 | 1 | StoreSpec |
| ticket CRUD module (get/upsert/create/get/get_by_channel/count/list/claim/close/blacklist ×3) | store (module) | utils/db/tickets.py:28-280 | 3 | 1 | hand-written CRUD + COALESCE-per-field upsert SQL — the exact escape hatch G-A14 targets; simple StoreSpec table access is already generatable, the bespoke merge-semantics upsert is not |
| ticket lifecycle (open→claimed→closed; participants) | session (game-facet-adjacent) | services/ticket_mutation.py (whole file) | 3 | 2 | no primitive family exists for a non-game per-instance channel-backed lifecycle today — 100% hand-written choreography; G-A15 proposed (see below) |

**Unit kinds present:** command, panel (incl. modal, selector), help, setting, binding, capability/registry (metadata-only), listener (EventBus subscription + handler body), event (domain event + audit companion), store (table + CRUD module), **wizard-section** (`SetupSection` registration — present but entirely omitted from the original draft; see the new row above). **Absent, confirmed by direct read + grep:**
- **game** (true `GameFacet`/`LeaderboardSpec`) — ticket has no competitive/economic mechanic; the proposed G-A15 lifecycle shares *structural* DNA with `ChallengeSessionSpec` (per-instance, timeouts-adjacent, close-workflow) but is not a game and doesn't reuse `GameFacet`.
- **gateway listener** (`@commands.Cog.listener()` / raw Discord event) — confirmed zero occurrences in `ticket_cog.py`; the only listener flavor present is `bus.on(...)` (EventBus), not a raw gateway hook. G-1 does not apply here (see the corrected-phrasing note above).
- **scheduled loop / managed task** — no `@tasks.loop`, no cron, confirmed by grep across every ticket file. This is a genuine feature gap (role's 24h loops show the pattern exists elsewhere) — ticket has no auto-close-on-inactivity, unlike comparable dedicated ticket bots (see Reconsider).
- **voice** — confirmed absent by grep.
- **diagnostics** (`DiagnosticProviderSpec`) — no diagnostics provider registered for ticket anywhere in the reviewed files.
- **`wait_for` wizard** — confirmed absent by grep; the config panel is a staged select-then-commit direct-lane panel, not a multi-step `wait_for` prompt chain.

**Structural-pattern flags:** EventBus subscription (`bus.on`, not gateway — corrected above) · modal-based mutation entry points (`TicketOpenModal`, `TicketCloseModal` — single-step, not a `wait_for` chain, and — corrected above — neither is reducible below tier 3 by G-A1 alone) · a bespoke non-KV config table + hand-written upsert (no `schemas.py`, unlike every other Lane A subsystem seen so far) · three role-bound authority mechanisms plus one inline resource-owner override (decorator / bespoke role-check / inert registry capability strings / ad hoc "or the opener" clause on close) · a per-instance channel-lifecycle choreography with no declarative home · **a `!setup`-wizard integration (`views/setup/sections/ticket.py`, a `SetupSection` registration) that the original draft omitted entirely** — a distinct, already largely data-shaped registry (slug/label/style/emoji/order/depths/description_if_skipped) that sits wholly outside the `tools.grammar_spike.spec.SubsystemManifest` grammar today (`SubsystemManifest` has no `wizard_sections` field at all, confirmed by reading `spec.py`), so a rebuilt ticket subsystem would still need a bespoke registration call into a second registry, not just one `SubsystemManifest`. Confirmed absent: gateway listener, scheduled loop, `wait_for` wizard, voice, stateful game loop.

#### Manifest sketch

```python
"""Ticket — expressed in the §2 grammar (spike style).

Source of truth (verified 2026-07-02):
    cogs/ticket_cog.py            — commands (135-322), bus.on wiring (57-58),
                                     help hook (326)
    services/ticket_mutation.py   — the audited write boundary, 7 emit_audit_action
                                     call sites, ticket.opened/ticket.closed emits
    services/ticket_service.py    — read model + eligibility (check_open_eligibility)
    utils/db/tickets.py           — hand-written CRUD/upsert (no schemas.py — ticket
                                     has NO generic-settings-pipeline config surface)
    migrations/098_tickets.sql    — the three stores
    views/tickets/*                — launcher / control / confirm / hub / config panels
    views/setup/sections/ticket.py — the !setup wizard's Support Tickets step
                                     (a SEPARATE `services.setup_sections.REGISTRY`
                                     entry, not part of this SubsystemManifest —
                                     see the wizard-section gap note below)

Tier verdict for ticket (measured in the lane ledger): the audited mutation seam
(open/claim/close/add/remove, plus the Confirm view's Open button and both
TicketOpenModal/TicketCloseModal) is thick real logic and stays tier-3 by
design, matching karma/blackjack's "an audited seam stays a seam" discipline —
ten units in total, corrected up from the original draft's seven (it undercounted
the Confirm-view Open button and let G-A1 wrongly discount both modals). The
surprise is the CONFIG surface: unlike every other Lane A subsystem seen so
far, ticket has no schemas.py at all — its settings ride a bespoke
dedicated table with hand-written upsert SQL, not the generic KV settings
pipeline. That is the dominant tier-3 mass here (G-A14), not the audited seam.
Four new amendments proposed: G-A14 (non-KV setting/binding persistence),
G-A1 (declarative modal fields — narrowed: it covers the field/label/validation
shape only, never the seam-call), G-A12 (role-bound authority tier, now scoped
to include a resource-owner clause for `close`), G-A15 (per-instance
channel-lifecycle facet, a non-game ChallengeSessionSpec analog). The
`!setup`-wizard integration is a fifth, separate gap noted but not amendment-
numbered here: `SubsystemManifest` has no field for it at all today.
"""

from __future__ import annotations

from tools.grammar_spike.spec import (
    BindingSpec,
    BlockSpec,
    CommandKind,
    CommandSpec,
    EventSpec,
    EventSubscription,
    FieldSpec,
    HandlerRef,
    HelpEntrySpec,
    PanelActionSpec,
    PanelRef,
    PanelSpec,
    ProviderRef,
    ResourceRequirement,
    SettingSpec,
    StoreSpec,
    SubsystemManifest,
)

_CAP = "ticket.config.update"  # subsystem_registry.py:256 — ⚠ currently inert:
# no capability_required anywhere in shipped code actually resolves against
# this string (grep-confirmed zero other references). Real authority is
# @perms_or_owner(manage_guild=True) OR is_ticket_staff() OR (for close only)
# "you are the ticket's own opener" — four conditions, three uncoordinated
# mechanisms plus one inline override — see G-A12 below.

TICKET_MANIFEST = SubsystemManifest(
    key="ticket",
    display_name="Support Tickets",
    description="Private support tickets — open by command, panel, or the AI.",
    emoji="🎫",
    category="community",
    visibility_tier="user",
    capabilities=("ticket.ticket.open", "ticket.ticket.manage", _CAP),
    parent_hub="community",  # [A] — subsystem_registry.py:252
    commands=(
        # cogs/ticket_cog.py:135 — bare group opens the hub (TIER 2: PanelRef)
        CommandSpec(
            name="ticket",
            kind=CommandKind.PREFIX,
            summary="Open the ticket hub — open a ticket or view your open ones.",
            route=PanelRef("ticket.hub"),
        ),
        # :141 — TIER 3: real audited open seam (thick — channel create + ACL
        # + DB insert + audit + event). G-A15 declares the CHOREOGRAPHY around
        # this call, not the call itself — stays tier 3, mirrors blackjack's
        # session-start command staying (3,3) under ChallengeSessionSpec.
        CommandSpec(
            name="ticket new",
            aliases=("open", "create"),
            kind=CommandKind.PREFIX,
            summary="Open a support ticket.",
            route=HandlerRef(
                "ticket.open",
                justification="channel provisioning + ACL + DB insert + audit "
                "+ event — thick domain logic, not reducible by G-A15",
            ),
        ),
        CommandSpec(
            name="ticket close",
            kind=CommandKind.PREFIX,
            summary="Close the ticket in this channel.",
            route=HandlerRef(
                "ticket.close",
                justification="transcript build + dual-destination delivery + "
                "teardown — thick domain logic",
            ),
        ),
        CommandSpec(
            name="ticket claim",
            kind=CommandKind.PREFIX,
            summary="Claim the ticket in this channel.",
            route=HandlerRef("ticket.claim", justification="claim-state seam"),
        ),
        CommandSpec(
            name="ticket add",
            kind=CommandKind.PREFIX,
            summary="Add a member to this ticket.",
            route=HandlerRef("ticket.add_participant", justification="ACL grant"),
        ),
        CommandSpec(
            name="ticket remove",
            kind=CommandKind.PREFIX,
            summary="Remove a member from this ticket.",
            route=HandlerRef("ticket.remove_participant", justification="ACL revoke"),
        ),
        # :238 — TIER 1: publishes a pre-declared persistent panel, zero logic
        CommandSpec(
            name="ticketpanel",
            kind=CommandKind.PREFIX,
            summary="Post the public ticket launcher panel here.",
            route=PanelRef("ticket.launcher"),
            capability_required=_CAP,
        ),
        # :245 — no-args opens the config panel (declarative); positional
        # form writes directly (G-A14 target) — TIER 3→2, dual-mode dispatch
        CommandSpec(
            name="ticketsetup",
            kind=CommandKind.PREFIX,
            summary="Configure tickets (opens a panel, or set staff role directly).",
            route=PanelRef("ticket.config"),
            capability_required=_CAP,
        ),
        # :277 — TIER 3→1: G-5 (bounds) + G-A14 (persistence) together make
        # this a pure setting_edit kernel workflow
        CommandSpec(
            name="ticketlimit",
            kind=CommandKind.PREFIX,
            summary="Set the max simultaneously-open tickets per member.",
            route=PanelRef("ticket.config"),  # WorkflowRef("setting_edit", ...) target
            capability_required=_CAP,
        ),
        CommandSpec(
            name="ticketblacklist",
            kind=CommandKind.PREFIX,
            summary="Manage who may open tickets.",
            route=HandlerRef("ticket.blacklist_usage", justification="usage stub"),
            capability_required=_CAP,
        ),
        # G-2 (list-valued add/remove, reused) + G-A14 (persistence)
        CommandSpec(
            name="ticketblacklist add",
            kind=CommandKind.PREFIX,
            summary="Blacklist a member from opening tickets.",
            route=PanelRef("ticket.config"),  # WorkflowRef("list_add", ...) target
            capability_required=_CAP,
        ),
        CommandSpec(
            name="ticketblacklist remove",
            kind=CommandKind.PREFIX,
            summary="Un-blacklist a member.",
            route=PanelRef("ticket.config"),  # WorkflowRef("list_remove", ...) target
            capability_required=_CAP,
        ),
    ),
    panels=(
        # views/tickets/hub.py:63 — TIER 2: FieldsBlock provider + 3 actions
        PanelSpec(
            panel_id="ticket.hub",
            subsystem="ticket",
            title="🎫 Support tickets",
            audience="invoker",
            body=(BlockSpec(kind="fields", provider=ProviderRef("ticket.hub_status")),),
            actions=(
                PanelActionSpec(
                    action_id="open",
                    label="Open a ticket",
                    emoji="🎫",
                    handler=HandlerRef("ticket.open", justification="opens TicketOpenModal"),
                    defer_mode="modal",  # G-A1 target: the modal's OWN fields
                    # (a single required `subject` text input, 200 chars) are
                    # not declarable in §2 as written — only THAT a modal
                    # opens (defer_mode="modal"), never WHAT it collects.
                ),
                PanelActionSpec(
                    action_id="list_mine",
                    label="My open tickets",
                    emoji="📋",
                    handler=ProviderRef("ticket.my_open_tickets"),  # read-only
                ),
                PanelActionSpec(
                    action_id="post_panel",
                    label="Post panel here",
                    emoji="📮",
                    handler=PanelRef("ticket.launcher"),
                    # G-A12 target: gated by is_ticket_staff() today (a bespoke
                    # role-bound check), not a declared capability_required.
                    capability_required="ticket.staff",  # aspirational — not shipped
                ),
            ),
        ),
        # views/tickets/launcher.py:19 — TIER 2: persistent, single modal-opening button
        PanelSpec(
            panel_id="ticket.launcher",
            subsystem="ticket",
            title="🎫 Support tickets",
            audience="persistent",
            timeout_s=None,
            actions=(
                PanelActionSpec(
                    action_id="open",
                    label="Open a ticket",
                    emoji="🎫",
                    style="primary",
                    handler=HandlerRef("ticket.open", justification="opens TicketOpenModal"),
                    defer_mode="modal",
                ),
            ),
        ),
        # views/tickets/control.py:63 — TIER 3 actions inside a TIER-2 shell
        PanelSpec(
            panel_id="ticket.control",
            subsystem="ticket",
            title="Ticket controls",
            audience="persistent",
            timeout_s=None,
            actions=(
                PanelActionSpec(
                    action_id="claim",
                    label="Claim",
                    style="success",
                    emoji="✋",
                    handler=HandlerRef("ticket.claim", justification="claim-state seam"),
                ),
                PanelActionSpec(
                    action_id="close",
                    label="Close",
                    style="danger",
                    emoji="🔒",
                    destructive=True,
                    handler=HandlerRef("ticket.close", justification="opens TicketCloseModal"),
                    defer_mode="modal",  # G-A1 target: the "reason" field
                ),
            ),
        ),
        # views/tickets/confirm.py:22 — MISSING from the original manifest sketch
        # entirely (no ticket.confirm PanelSpec existed, despite a ledger row
        # for TicketConfirmView) — added here. TIER 2 shell + a TIER-3 Open
        # action (a direct call into the same seam as ticket.open above, NOT
        # a modal — no defer_mode) + a TIER-1 Cancel action.
        PanelSpec(
            panel_id="ticket.confirm",
            subsystem="ticket",
            title="🎫 Open a support ticket?",
            audience="invoker",
            timeout_s=120,
            actions=(
                PanelActionSpec(
                    action_id="open",
                    label="Open ticket",
                    style="success",
                    emoji="🎫",
                    handler=HandlerRef(
                        "ticket.open",
                        justification="direct call into the audited open seam — "
                        "no modal here (subject was already supplied to the AI); "
                        "same class as the Claim/Close buttons, not part of the "
                        "declarative shell",
                    ),
                ),
                PanelActionSpec(
                    action_id="cancel",
                    label="Cancel",
                    style="secondary",
                    emoji="✖️",
                    # no handler — a bare acknowledgement action, fully declarative
                ),
            ),
        ),
        # views/tickets/config_panel.py:123 — TIER 2 shell around G-A14-targeted writes
        PanelSpec(
            panel_id="ticket.config",
            subsystem="ticket",
            title="🎫 Support Tickets — configure",
            audience="invoker",
            selectors=(),  # staff_role / log_channel SelectorSpecs land here (G-A14
            # target: the values they stage commit through update_config(), a
            # hand-written upsert today, not a kernel binding_set workflow)
            actions=(
                PanelActionSpec(
                    action_id="autocreate_log",
                    label="Auto-create log channel",
                    emoji="🪄",
                    handler=HandlerRef(
                        "ticket.create_log_channel",
                        justification="provisioning + bespoke staff-role ACL overwrite",
                    ),
                ),
                PanelActionSpec(
                    action_id="enable",
                    label="Enable tickets",
                    style="success",
                    emoji="✅",
                    handler=HandlerRef("ticket.update_config", justification="G-A14 target"),
                ),
                PanelActionSpec(
                    action_id="post_panel",
                    label="Post open-ticket panel here",
                    emoji="📋",
                    handler=PanelRef("ticket.launcher"),
                ),
            ),
        ),
    ),
    settings=(
        # utils/db/tickets.py:44 — TIER 3→1 (G-A14): shape is plain SettingSpec,
        # persistence is bespoke (no schemas.py exists for ticket at all)
        SettingSpec(
            name="enabled",
            value_type="bool",
            default=True,
            settings_key="ticket_enabled",  # aspirational — no settings_keys module
            # ships today; ticket_config.enabled is a raw table column.
            capability_required=_CAP,
            storage="own_table",  # G-A14: the field already exists (spec.py:255)
            # but its non-"kv" semantics are unelaborated — this is the ask.
        ),
        SettingSpec(
            name="max_open_per_user",
            value_type="int",
            default=1,
            settings_key="ticket_max_open_per_user",
            capability_required=_CAP,
            validator=HandlerRef("ticket.validate_max_open"),  # G-5: 1..25 bound
            storage="own_table",
        ),
        SettingSpec(
            name="ping_staff_on_open",
            value_type="bool",
            default=True,
            settings_key="ticket_ping_staff_on_open",
            capability_required=_CAP,
            storage="own_table",
            hint="⚠ no editor exposes this today — dormant field.",
        ),
    ),
    bindings=(
        BindingSpec(
            name="staff_role",
            kind="role",
            required=True,
            capability_required=_CAP,
            hint="Who can see and manage every ticket.",
        ),
        BindingSpec(
            name="log_channel",
            kind="channel",
            required=False,
            capability_required=_CAP,
            resource_link="log_channel",
        ),
        # utils/db/tickets.py:44 (category_id) — MISSING from the original
        # manifest sketch entirely; added here. Same dormant-field class as
        # ping_staff_on_open above, but the original draft's ledger didn't
        # even name it.
        BindingSpec(
            name="category",
            kind="category",
            required=False,
            capability_required=_CAP,
            hint="⚠ read by ticket_mutation.open_ticket but no editor exposes "
            "it anywhere today — a second dormant field.",
        ),
    ),
    resources=(
        # services/ticket_mutation.py:473 create_log_channel — TIER 3→2: the
        # create+bind half is generic ResourceRequirement; the bespoke
        # staff-role-only overwrite policy is the residual thin handler.
        ResourceRequirement(
            kind="channel",
            intent="ticket.log_channel",
            provisioning="recommended",
            binding_name="log_channel",
            offer_on_enable=True,
            audit_intent="ticket_log_provision",
        ),
    ),
    events=(
        EventSpec(
            name="ticket.opened",
            payload_schema=(
                FieldSpec("guild_id", "int"),
                FieldSpec("ticket_id", "int"),
                FieldSpec("channel_id", "int"),
                FieldSpec("opener_id", "int"),
                FieldSpec("subject", "str"),
                FieldSpec("source", "str"),
            ),
            owner_subsystem="ticket",
            expected_subscribers=(HandlerRef("ticket_cog.on_ticket_opened"),),
            audited=True,
        ),
        EventSpec(
            name="ticket.closed",
            payload_schema=(
                FieldSpec("guild_id", "int"),
                FieldSpec("ticket_id", "int"),
                FieldSpec("channel_id", "int"),
                FieldSpec("opener_id", "int"),
                FieldSpec("closed_by", "int"),
            ),
            owner_subsystem="ticket",
            expected_subscribers=(),
            observability_only=True,
            audited=True,
        ),
    ),
    subscriptions=(
        # cogs/ticket_cog.py:57-58 — already-native EventSubscription; NOT a
        # gateway listener (no G-1 relevance — corrected scaffold phrasing)
        EventSubscription(
            event="ticket.opened",
            handler=HandlerRef("ticket_cog.on_ticket_opened"),
        ),
        EventSubscription(
            event="ticket.open_requested",  # cross-lane: emitted by ai_tools.py:2494
            handler=HandlerRef("ticket_cog.on_ticket_open_requested"),
        ),
    ),
    gateway_listeners=(),  # confirmed absent — no @commands.Cog.listener() anywhere
    stores=(
        StoreSpec(
            table="ticket_config",
            sole_writer="ticket.mutation",
            checkpoint_class="aggregate",
        ),
        StoreSpec(
            table="tickets",
            sole_writer="ticket.mutation",
            checkpoint_class="ledger",
            reader_domains=("ticket",),
        ),
        StoreSpec(
            table="ticket_blacklist",
            sole_writer="ticket.mutation",
            checkpoint_class="aggregate",
        ),
    ),
    game=None,  # confirmed: no GameFacet/LeaderboardSpec use — see G-A15 below
    help=HelpEntrySpec(
        summary="Open a private support ticket — staff will help you out.",
        examples=("!ticket new my issue", "!ticket close", "!ticketsetup"),
    ),
)

# NOTE: TICKET_MANIFEST above has no field representing the !setup wizard's
# Support Tickets step (views/setup/sections/ticket.py). SubsystemManifest
# (tools/grammar_spike/spec.py) has no `wizard_sections` field at all — the
# wizard integration is a wholly separate registration into
# services.setup_sections.REGISTRY, invisible to this grammar today. A
# rebuilt ticket subsystem would still need that second, uncoordinated
# registration call even if every field above were auto-generated from data.

# G-A15 (proposed, NOT in spec.py today) would add a top-level facet analogous
# to GameFacet, e.g.:
#
#   @dataclass(frozen=True)
#   class InstanceLifecycleSpec:
#       resource_kind: str              # "channel"
#       participant_grants: tuple[str, ...]  # ("opener", "binding:staff_role")
#       status_field: str               # "status" — open|claimed|closed
#       close_handler: HandlerRef        # transcript/notify/teardown hook
#       teardown_policy: str = "delete_on_close"
#
#   TICKET_MANIFEST.lifecycle = InstanceLifecycleSpec(
#       resource_kind="channel",
#       participant_grants=("opener", "binding:staff_role"),
#       status_field="status",
#       close_handler=HandlerRef("ticket.close_transcript_and_deliver"),
#   )
#
# This would absorb the create/ACL/status-transition/teardown choreography
# (currently 100% hand-written in services/ticket_mutation.py) into a kernel
# workflow, leaving only the per-action domain hooks (eligibility copy,
# transcript rendering, delivery) as thin HandlerRefs — the same "choreography
# moves, the seam stays" pattern ChallengeSessionSpec already proved for
# blackjack's session lifecycle.
```

#### Tier-3 dispositions

- **`!ticket new` / `!ticket close` / `!ticket claim` / `!ticket add` / `!ticket remove` (commands) + Claim/Close buttons (`TicketControlView`) + the Confirm view's Open button + `TicketOpenModal` / `TicketCloseModal`** — **deliberate escape hatch, ten units total (corrected from the draft's seven).** Each wraps a real, audited domain mutation (channel provisioning + ACL, transcript generation + dual-delivery, claim-state checks, permission-overwrite calls) that must stay code — the same discipline karma's audited grant seam and blackjack's per-move handlers apply (an audited seam classifying as tier-3 regardless of thinness is the spec's own intended behavior, not a gap). **Correction:** the original draft applied this exact principle to the five commands and the two `TicketControlView` buttons, but then contradicted it for `TicketOpenModal`/`TicketCloseModal` (scored 3→2, discounted by G-A1) and for `TicketConfirmView`'s Open button (folded into a tier-2 panel row) — even though all three route into the identical irreducible `open_ticket`/`close_ticket` seam. G-A1 narrows to cover only the modal's field/label/validation shape, never the seam-call; the Confirm view's Open button is a fourth escape-hatch entry point on top of Claim/Close, not part of the panel's declarative shell.
- **Ticket config fields (`staff_role_id`, `log_channel_id`, `category_id`, `max_open_per_user`, `ping_staff_on_open`, `enabled`) + the CRUD module (`utils/db/tickets.py`)** — **grammar gap → G-A14** (new, proposed above). The field *shapes* are plain SettingSpec/BindingSpec; only the persistence mechanism (a dedicated migration-owned table with a hand-written COALESCE-upsert, because ticket has no `schemas.py` at all — unlike every other Lane A subsystem audited) is bespoke. `spec.py:255` already carries a `storage` field for exactly this, but its non-"kv" semantics are unelaborated; G-A14 is the ask to elaborate it into a real generation contract, not to add a new field. **Correction:** `category_id` belongs in this list — it is exactly as bespoke-persisted and exactly as dormant (zero exposed editor) as `ping_staff_on_open`, but the original draft never named it.
- **`is_ticket_staff()` (the staff-authority check gating claim/close/add/remove/post-panel) + the inline "or the ticket's own opener" override on `close`** — **grammar gap → G-A12** (new, proposed above; scope corrected). `capability_required` only ever resolves to the fixed ADMINISTRATOR floor (`governance/capability.py:51`); ticket's real model (platform owner OR admin/manage_guild OR a per-guild-**configured role**, OR — for `close` specifically — the ticket's own opener) has no declarative home. Cross-referenced against moderation's `MODERATOR_TIER_ROLE_ID`/`TRUSTED_TIER_ROLE_ID` (`cogs/moderation/schemas.py:390,405`) as independent evidence of the role-bound shape recurring in this lane; the resource-owner clause is ticket-specific and needs its own coverage inside the same amendment.
- **The open→claim→close→participants choreography as a whole (`services/ticket_mutation.py`)** — **grammar gap → G-A15** (new, proposed above). No primitive family models "one dedicated channel per domain instance, with a status machine and a close-workflow" outside `GameFacet`'s game-specific `ChallengeSessionSpec`, which doesn't fit a non-competitive support-ticket object. This is the highest-leverage new primitive of the four: it's what would let the per-action commands stay honestly tier-3 (real domain hooks) while removing ~350 lines of hand-written choreography around them.
- **`!ticketsetup` (positional-args path) / `!ticketlimit` / `!ticketblacklist add`+`remove` / "Enable tickets" button / "Auto-create log channel" button** — **grammar gap, reusing existing amendments**, not new ones: `!ticketlimit`'s clamp reuses **G-5** (declarative validator bounds, same class as karma's `cooldown_seconds`/`daily_cap`); `!ticketblacklist add/remove` reuse **G-2** (list-valued add/remove workflows) exactly as specced for logging's `ignored_channels`/`ignored_users`; all four also need **G-A14** for the underlying non-KV write. No new amendment number needed for these — they're G-2/G-5 applied to a subsystem G-2/G-5 weren't originally evidenced against.
- **`_on_ticket_opened` / `_on_ticket_open_requested` (EventBus handler bodies)** — **grammar gap → G-A15** (reuse, not a fifth amendment): rendering the resulting panel into the newly-created channel is exactly the "post-open UI" step a per-instance lifecycle kernel workflow would generate; the residual thin ref is only the welcome-embed copy / member-resolution glue.
- **The `!setup`-wizard integration (`views/setup/sections/ticket.py`)** — **not a tier-3 unit** (it's tier 2 as-written), but flagged here because it exposed a structural gap: `SubsystemManifest` has no field for a wizard-registry entry at all, so this isn't covered by G-A14..G-A15 or by any existing §2 primitive. Not amendment-numbered in this pass — noted for whoever scopes the wizard-integration grammar next.

#### Fit numbers

| Metric | Value |
|---|---|
| Units total | 58 |
| Tier-1/2 count — as written | 32 |
| **Fit — as written** | **55.2%** |
| Tier-1/2 count — with amendments (G-1…G-6 + G-A14…G-A15) | 48 |
| **Fit — with amendments** | **82.8%** |

**Corrected from the draft's 54/30(55.6%)/47(87.0%).** The as-written count of 30 (55.6%) the draft reported for 54 units was itself internally consistent with its own table (independently re-tallied and confirmed); the correction changes the *inputs*, not the arithmetic. Four fixes, net effect **+4 units, +2 to the as-written numerator, +1 to the with-amendments numerator**:
1. **`TicketOpenModal`/`TicketCloseModal` corrected from (3,2) to (3,3)** — both wrap the identical irreducible lifecycle seam the document itself declares immune to every proposed amendment; G-A1 covers the field shape only. Net **−2** to the with-amendments numerator, no change to units or the as-written numerator.
2. **`TicketConfirmView` split from one row (2,2) into three** — shell (2/2, unchanged shape) + a new Open-button row (3/3 — a direct call into `open_ticket`, the exact class of unit the draft's own `TicketControlView` shell/action split exists to surface) + a new Cancel-button row (1/1). Net **+2 units, +1 to each numerator**.
3. **The `!setup`-wizard `SetupSection` (`views/setup/sections/ticket.py`) added as a new row** — named in the section's own file list and citation line, but entirely absent from the original ledger. Tier 2/2 (thin, already-largely-declarative registration). Net **+1 unit, +1 to each numerator**.
4. **`category_id` added as a new dormant-binding row** — plumbed exactly like `ping_staff_on_open` (which the draft *did* flag) but never named. Tier 3/1. Net **+1 unit, +1 to the with-amendments numerator only**.

Net: units 54→58 (+4), as-written numerator 30→32 (+2, 55.6%→55.2%), with-amendments numerator 47→48 (+1, but 87.0%→82.8% because the denominator grew by 4 while the numerator grew by only 1 — the two modal downgrades absorbed most of the added units' contribution). Ticket still lands well below karma (80%) and logging (79%) as-written, and the with-amendments climb is real but smaller than the draft reported — **82.8%, not 87.0%** — because the audited-seam floor is thicker than the draft credited (ten units, not seven). The audited-mutation core (now ten command/button/modal units: open/close/claim/add/remove, Claim/Close buttons, the Confirm view's Open button, and both modals) stays tier-3 in both columns by design, same as karma/blackjack — that floor is real and correctly *not* counted as a gap.

#### Structural-gap flags

- **Permission/capability gates** — **danger zone, needs G-A12.** Three role-bound authority mechanisms today (fixed-permission decorator / bespoke role-check function / inert registry capability strings) plus one inline resource-owner override on `close` (see the corrected authority-model note above) is exactly the fragmentation the grammar is supposed to prevent. Not expressible today; G-A12 gives it one declarative home, scoped to include the resource-owner clause.
- **Setup/provisioning wizards** — **not present as a `wait_for` danger zone.** `TicketConfigPanelView` is a staged select-then-commit **direct-lane** panel (confirmed by the code's own comments citing the direct-vs-draft-lane framework), not a multi-step `wait_for` prompt chain. Confirmed absent by grep. The existing PanelSpec/SelectorSpec/PanelActionSpec grammar already expresses this shape (as shown in the manifest sketch), no new primitive needed for the *panel* itself, only for what its actions write (G-A14). Separately, the `!setup`-wizard's own Support Tickets *step* (`views/setup/sections/ticket.py`) sits in a second registry (`services.setup_sections.REGISTRY`) with no `SubsystemManifest` field of its own — flagged above, not amendment-numbered.
- **External API opt-ins** — **absent.** Channel creation runs through the existing `ChannelLifecycleService` (native Discord API, already-audited seam); no third-party API dependency in this subsystem.
- **Audit/mutation seams** — **the strongest example in Lane A**, and already well-covered: `EventSpec`/`AuditRef`-style declarations already exist in §2 (no new gap here); the only residual friction is that the audit *call itself* is hand-written today (tier 2) rather than kernel-fired from a declared `audit:` field (tier 1 with the spec's existing §2.6 compile rule taken to its logical conclusion — not a new amendment, just the design spec's own promised behavior not yet built).
- **Destructive actions** — `!ticket close` / the Close button unconditionally `channel.delete()`s post-close (best-effort, confirmed at `ticket_mutation.py:344`). The modal-submission (reason input) already functions as an implicit confirm gesture; once G-A1 declares that modal, `destructive=True` + `style="danger"` (already present in the manifest sketch above) is sufficient — no new primitive needed beyond G-A1 for the field itself (the seam-call, per the correction above, stays tier 3 regardless).
- **Lifecycle tasks/scheduled loops** — **absent, and a genuine feature gap** (not a grammar gap): ticket has no auto-close-on-inactivity `ManagedTaskSpec`, unlike `role`'s 24h loops in this same lane. `ManagedTaskSpec` already exists in §2 (spec.py:378) and would express this cleanly the moment the feature is built — flagged for Reconsider below, not for a new amendment.
- **Governance/cache behavior** — no subsystem-specific caching layer; reads go straight through `utils/db/tickets.py`. Nothing to flag.

#### Reconsider / optimize

**MAP → RECONSIDER → SIMULATE → OPTIMIZE verdict: KEEP + IMPROVE.** Ticket is architecturally the cleanest audited-mutation subsystem reviewed in this lane (7 distinct `emit_audit_action` sites, one enforced single-entry eligibility check shared identically across the command/panel/AI paths, a real transcript-on-close). The core design is sound and should carry forward largely as-is; the improvements are additive, not a redesign.

**Optimal new-bot form:** keep the three-entry-point design (command / launcher panel / AI natural-language) unified on the single `check_open_eligibility` + audited-seam pattern exactly as shipped — that discipline is worth preserving verbatim. Layer on top: (1) collapse the three role-bound authority mechanisms (plus the inline resource-owner override on close) into one declared `capability_required` resolved via G-A12's role-bound-plus-owner tier; (2) express the whole open/claim/close/participant choreography as a G-A15 lifecycle spec so the domain-specific hooks (eligibility copy, transcript building, delivery) are the only code left; (3) expose the currently-dormant `ping_staff_on_open` **and `category_id`** fields in the config panel, and either wire up or drop the dormant `panel_channel_id`/`panel_message_id` columns; (4) add a `/ticket` slash mirror (currently prefix-only, unlike karma/logging's dual surface — a discoverability gap for a slash-first Discord UX); (5) add an auto-close-on-inactivity `ManagedTaskSpec` (a common feature in dedicated ticket bots that ticket currently lacks entirely); (6) fold the `!setup`-wizard's Support Tickets step into the same manifest that generates the rest of the subsystem, instead of a second, uncoordinated `SetupSection` registration with no shared grammar.

**Dependency-layer guess:** mid-tier feature, early-governance-adjacent. It depends on the channel-lifecycle provisioning primitive, the audit/capability kernel, and EventBus — all of which should land in L0/early-governance layers first. Nothing else in the audited surface depends on ticket, so it is not itself foundational.

**Production-grade done-definition:** a `parity/ticket_golden.json`-style behavioral test asserting, across **all three** open entry points (command, launcher-modal, AI-confirm click) identically: exactly one `tickets` row + one audited `mutation_type="open"` row + one `ticket.opened` event + a control panel posted in the new channel; on close, exactly one audited `mutation_type="close"` row + one `ticket.closed` event + a transcript delivered to both the log channel and the opener's DM + channel teardown; and that the blacklist/limit/not-configured gates block ineligible opens with the same reason code on all three paths (the single `check_open_eligibility` seam is precisely what should be golden-tested, since it's the thing guaranteeing no path drifts from the others).

**Outperform target:** Ticket Tool is the dominant dedicated Discord ticket bot and the natural comparator (pending Lane F's confirmed research — this call is directional, not sourced). Where we already plausibly beat it: transcripts are delivered free and automatically to both a log channel and the opener's DM on every close (several dedicated ticket bots gate transcript delivery behind a paid tier), and the same audited seam runs identically whether the ticket was opened by command, panel, or AI natural-language request — a consistency guarantee most competitors don't offer since they don't have an AI-driven open path at all. Where we're currently behind: no ticket categories/tags, no SLA/auto-close-on-inactivity, no reopen action, no per-staff claim limits, no priority selection at open time — flagged as `pending Lane F` for a rigorous benchmark, not asserted as confirmed fact here.

**Owner-gated/blocked/external-dependency status:** none specific to ticket. No external (non-Discord) API dependency. Subject only to the BRIEF's standing Phase-3 owner gate (no new-repo implementation without design-spec approval) — not a ticket-specific blocker.

**Cross-lane dependency:** Lane D (`ai`): `disbot/services/ai_tools.py:2494` (`_make_open_support_ticket`) emits `bus.emit("ticket.open_requested", ...)`, consumed only by `ticket_cog.py:58` (`_on_ticket_open_requested`). The `ai` subsystem is the emitter; `ticket` is a subscriber only — not audited in this section.

---
---

## Lane A summary

### Aggregate fit numbers

| Subsystem | Units | Tier-1/2 as-written | Fit as-written | Tier-1/2 with amendments | Fit with amendments |
|---|---:|---:|---:|---:|---:|
| admin | 40 | 18 | 45.0% | 29 | 72.5% |
| server_management | 17 | 10 | 58.8% | 15 | 88.2% |
| moderation | 53 | 22 | 41.5% | 34 | 64.2% |
| automod | 21 | 13 | 61.9% | 19 | 90.5% |
| image_moderation | 15 | 11 | 73.3% | 14 | 93.3% |
| security | 27 | 21 | 77.8% | 24 | 88.9% |
| cleanup | 53 | 29 | 54.7% | 44 | 83.0% |
| role | 108 | 54 | 50.0% | 75 | 69.4% |
| channel | 41 | 13 | 31.7% | 35 | 85.4% |
| welcome | 24 | 17 | 70.8% | 23 | 95.8% |
| ticket | 58 | 32 | 55.2% | 48 | 82.8% |
| **LANE A TOTAL** | **457** | **240** | **52.5%** | **360** | **78.8%** |

**Compare to the grammar spike's 3-subsystem baseline** (`tools/grammar_spike/RESULTS.md`): karma
80→87%, logging 79→97%, blackjack 44→44%, spike overall 73→85%. **Lane A's honest read: the 80%
tier-1/2 bar the design spec's §10.1 risk 5 sets is NOT cleanly cleared, even with all 15 proposed
amendments folded in** (78.8% aggregate, just under 80%). Three subsystems stay well below 80%
even with amendments — `moderation` (64.2%), `role` (69.4%), `admin` (72.5%) — and one of the
lane's largest subsystems (`channel`, 41 units) starts at the lane's *worst* as-written fit
(31.7%, worse than blackjack's 44%) before recovering strongly to 85.4% once G-A1/G-A4/G-A7/G-A8
land. This is a materially different picture than the spike's optimistic "karma/logging-shaped"
assumption the BRIEF flags as untested (§ "The gap this audit closes") — Lane A is disproportionately
built from **audited mutation seams and dual/triple authority-check surfaces** (moderation, role,
ticket), which the spike's three subsystems barely touched (karma has exactly one thin seam;
logging has none). Two per-subsystem sections (`moderation`, `channel`) explain this mechanically:
counting real `*_mutation.py`-style seam functions and command-argument resolvers as their own
ledger rows (per the BRIEF's explicit "mutation paths" unit-kind requirement) surfaces real,
irreducible tier-3 code that karma/logging's convention of folding seams into their calling
command would have hidden. **Recommendation for the capstone:** either accept a lane-differentiated
bar (governance/CRUD-with-real-authority subsystems land in the high-60s/low-80s even optimized,
which is still a large win over today's 31-58% as-written) or treat `moderation`/`role`'s residual
tier-3 mass as a signal that a *governance-specific* primitive family (beyond G-A1/G-A2/G-A12) is
still missing — the audit's per-subsystem Reconsider sections found no further candidate beyond
what's already proposed, but this is exactly the kind of cross-lane pattern the exit bar's
"consolidated amendment list" step should re-examine once Lanes B/C/D's numbers land.

### Structural danger zones found (roundup)

- **Permission/capability gates** — present in every subsystem; the dominant finding is **not**
  gate *absence* but gate **duplication/inconsistency**: moderation (3 independent mechanisms —
  prefix dual-floor, slash single-floor, panel dual-floor), ticket (4 mechanisms — Discord
  permission bit, capability strings that are wired nowhere, a bespoke staff-check function, and an
  inline resource-owner override repeated at 2 call sites), admin/channel (a hand-wrapped
  `admin_or_owner` predicate not modeled by any `audience_tier` value). See **G-A12**.
- **Setup/provisioning wizards** — cleanup and role each register a `SetupSection` with 5 bespoke
  callback fields (no §2 equivalent — **G-A9**); server_management's hub routes into `cogs/setup`'s
  own wizard, which turned out to have **no `SUBSYSTEMS` registry entry at all** (a coverage gap
  flagged for Lane G / owner attention, not a Lane A fix).
- **`wait_for` wizards** — one confirmed instance the pre-extracted scaffold missed:
  `!cleanuphistory`'s `bot.wait_for("reaction_add", timeout=30.0)` bulk-delete confirm
  (`cleanup_cog.py:438-443`). Most "wizard-shaped" flows in this lane are chained
  `discord.ui.Select`/modal views (cleanup, role's `RoleMenuBuilder`), not raw `wait_for` — a
  narrower danger zone than the BRIEF's framing implied for governance subsystems specifically.
- **External API opt-ins** — one confirmed hard dependency: `image_moderation`'s classifier calls
  `core/runtime/ai/providers/openai_moderation.py` (Lane D's `ai`-subsystem provider adapter,
  shared `OPENAI_API_KEY`) — the stage is non-functional without it.
- **Audit/mutation seams** — the lane's strongest structural finding: moderation, ticket, and
  (once corrected) channel each route every real mutation through one audited seam
  (`moderation_service`, `ticket_mutation`, `channel_lifecycle_service`) emitting both a
  domain event and `audit.action_recorded` — exactly the shape `HandlerRef` + kernel audit-emission
  is built for. **Role and security both have real gaps here**: role's `role_automation_exemptions`
  / `role_thresholds` tables were not found to be purged on guild departure (a probable INV-I gap,
  flagged `⚠ unverified` — not exhaustively confirmed); security's lockdown-restore Discord call
  (`channel.edit(slowmode_delay=...)`) was found to be **currently unaudited** (no `audit.action_recorded`
  companion), an audit-hygiene bug independent of the G-A11 grammar-fit finding.
- **Destructive actions** — correctly modeled today via `PanelActionSpec.destructive ⇒
  style="danger"` (ban/kick, channel delete, role delete) — no gap found.
- **Lifecycle tasks / scheduled loops** — role is the lane's only subsystem with real recurring
  loops: `role_check` (`@tasks.loop(hours=24)`, tenure/XP role sweep) and `_sweep_loop`
  (`@tasks.loop(minutes=...)`, temp-role expiry) — both fit `ManagedTaskSpec`'s `interval:<s>`
  trigger cleanly (tier-2). Security's lockdown timers are the lane's one **non-recurring**
  scheduled-callback shape or `ManagedTaskSpec` genuinely doesn't fit — see **G-A11**.
- **Governance/cache behavior** — `governance/cleanup.py`'s policy resolver and `governance/role_templates.py`
  are both real domain logic (policy precedence/merge rules), correctly dispositioned as deliberate
  escape hatches, not grammar gaps, in their respective sections.

### Cross-lane dependencies (roundup — for the capstone, not re-audited here)

- **Lane D (`ai`)**: `image_moderation`'s classifier is a hard dependency on the `ai` subsystem's
  OpenAI provider adapter; `ticket`'s AI-tool trigger (`ai_tools.py:2494`) emits
  `ticket.open_requested`, consumed by ticket as subscriber only; `admin`'s hub nav buttons route
  into `ai`/`settings`/`diagnostic`/`logging`/`help`/`ux_lab` panels.
- **Lane D (`logging`, i.e. `server_logging`)**: subscribes to `moderation.action_taken` (×2
  handlers) and is the natural future subscriber for security's currently-orphaned
  `security.raid_detected`/`security.account_flagged` events; welcome and logging both register
  independent `on_member_join`/`on_member_remove` gateway listeners on the same events
  (coexisting dispatch, no call dependency — G-1 dispositions should stay consistent at capstone
  time); the functional `mod_channel`/`cleanup_channel` bindings are owned by `logging`'s schema,
  not moderation's own (orphaned) `mod_log` `ResourceRequirement`.
- **Lane D (`settings`/`help`)**: `views/settings/edit_channel.py` and `edit_role.py` are shared
  settings-framework widgets, not channel/role-owned; `views/help/editor.py` (Help appearance
  editor) is reached from server_management's hub but is Lane D's; `access_projection.py`/
  `help_projection.py` are shared governance/help infrastructure consumed read-only by
  server_management's AccessMap/HelpPreview subpanels.
- **Lane B (`xp`)**: `services/xp_role_sync.py` is genuinely dual-owned — role's own tenure/XP
  thresholds feed it, but Lane B's `xp` cog's live level-up listener is its primary consumer;
  `role_thresholds`' `xp_auto_assign`/`level_required` columns are written by role, read by Lane B.
- **Lane B (`economy`)**: `disbot/views/setup/sections/channels.py` (server_management's
  setup-wizard channel-binding stager) names Lane B's `economy`/`xp` channel-binding intents —
  not channel-subsystem-owned code.
- **Lane B/C (game-state cleanup)**: `core/runtime/cleanup_registry.py` +
  `services/game_state_cleanup.py` are a generic stale-session/game-state GC provider registry
  feeding Lane B (economy refunds) and Lane B/C (game teardown) — shares the word "cleanup" but is
  not part of this lane's `cleanup` subsystem.
- **Lane C (`counting`, `chain`)**: both call `moderation_service.auto_delete()` directly for
  rule-based message deletion, sharing moderation's audited seam.
- **Lane G (foundations)**: `admin`'s dynamic cog-discovery primitives
  (`cogs/admin/cog_manager.py`) and `!restart`'s `core.runtime.lifecycle` state machine are the
  operator-facing surface on top of Lane G's bootstrap/loader territory — recommendations on
  cog-loading design should cross-reference both lanes.

### Residual unverified items (roundup)

Every subsystem section carries its own `⚠ unverified` list inline; the highest-leverage
open items surfaced across the lane (not resolved in this pass — flagged for the capstone or a
follow-up):

- Whether `SUBSYSTEMS['admin']['capabilities']`, `image_moderation.settings.configure`, and
  moderation's `mod_log` `ResourceRequirement` are live-enforced or orphaned registry metadata —
  each was traced by targeted grep, not an exhaustive resolver call-graph.
- Whether `role_automation_exemptions`/`role_thresholds` rows are purged on guild departure
  (probable gap, not exhaustively confirmed against every teardown code path).
- Whether the `command-surface.json` ground-truth extractor's `perm` column is simply blind to
  wrapped permission checks (`@admin_or_owner()`, `is_ticket_staff()`) by design or by omission —
  affects how much weight the capstone should put on that file's `perm` field lane-wide, not just
  in Lane A.
- Whether the security lockdown-restore audit-hygiene gap (found here) and the channel
  `ChannelLifecycleService` audit-seam point (also found here) were independently already
  caught by another lane's pass on a shared/adjacent file — worth a capstone cross-check so the
  same finding isn't credited (or missed) three times independently.
- The ecosystem-benchmark ("outperform target") claims throughout this lane are explicitly
  directional and **pending Lane F** — none were checked against actual competitor bots in this
  pass, per the BRIEF's lane-boundary instruction.

### MAP → RECONSIDER → SIMULATE → OPTIMIZE — lane-level verdict

No subsystem in this lane returned a **drop** verdict — every one is core Discord-governance
functionality with no redundant sibling elsewhere in the 43-subsystem surface. Two subsystems
(`server_management`, `admin`) are **routing-only hubs with `capabilities: []`** whose entire value
is UI aggregation — their per-subsystem Reconsider sections both flag consolidation/merge
questions (does a thin nav hub need to exist as its own subsystem key, or can `G-A3`'s
direct-navigation primitive dissolve it into pure declared routing on the parent Admin hub?) for
the capstone's build-order decision, not a functional drop. The dominant **improve** pattern
lane-wide is authority-mechanism unification (**G-A12**) and modal/pipeline-stage
declaration (**G-A1**/**G-A2**) — both are cross-subsystem, high-yield, low-risk amendments (data
declarations replacing boilerplate glue, not behavior changes) that the capstone should prioritize
folding into the design spec first, ahead of the more subsystem-specific proposals (G-A5…G-A11,
G-A13…G-A15).
