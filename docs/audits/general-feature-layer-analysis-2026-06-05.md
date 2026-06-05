# General Discord Feature Layer Analysis — 2026-06-05

> **Superseded (2026-06-05):** reconciled into
> [`../planning/superbot-audit-consolidation-2026-06-05.md`](../planning/superbot-audit-consolidation-2026-06-05.md)
> (verified, RC-n IDs). Read that first; this raw audit is historical context.

## Scope

This document records the Agent C audit of the general Discord feature layer.
It intentionally focuses on user-facing feature cogs, panels, command surfaces,
service boundaries, DB ownership, and interaction flows.

Excluded from deep review: AI, BTD6 internals, setup wizard internals, settings
implementation internals, full migration review, and exhaustive test execution.
Those areas may still be affected by shared platform systems such as command
access, Help routing, message pipeline ordering, and governance visibility.

## Verification baseline

- Repository: `menno420/superbot`
- Default branch: `main`
- Code audit baseline: `d583dcb082580298e063d718ab7eb534a47ad3ea` / merged PR #506
- This docs PR branch is based on newer `main` commit `eb20bac10b7b09b570c669f1c7ac150cde348a53` after docs-only PRs #507 and #508.
- No files were modified during the audit itself.
- Local `git status`, local test execution, and local full-tree grep were not available from the execution environment. Findings below are based on GitHub connector reads of the current repository files.

## Most important findings

### 🔴 1. The feature layer is usable, but many cogs are still not thin adapters

The repo has a clear target architecture: cogs should be command adapters,
services should own business rules and DB mutation, views should own interaction
UI, and runtime systems should provide governance, message pipeline, tasks,
resources, and observability.

Several features now follow this direction well. `games_cog.py` is router-only,
`logging_cog.py` delegates runtime logging behavior to `server_logging`,
`leaderboard_cog.py` uses rank providers, and XP/Cleanup/Counting/Chain are
integrated into the message pipeline.

However, many older cogs still combine multiple layers in one file:

- `role_cog.py` contains `RoleHubPanelView`, local permission checks, hidden legacy commands, direct DB threshold/reaction-role calls, and Discord role mutation.
- `admin_cog.py` contains `_AdminPanelView`, `_LogLevelModal`, cog management, restart/log-level controls, and panel navigation.
- `inventory_cog.py` contains the item catalogue, inventory query helper, category view, hub view, and command surface.
- `utility_cog.py` contains commands, panel view, modals, and in-memory reminder scheduling.
- `deathmatch_cog.py` contains duel domain state, views, active-duel tracking, and leaderboard updates.
- `chain_cog.py` contains command group logic, message-stage logic, DB writes, modals, and panel view.
- `cleanup_cog.py` contains message-stage logic, prohibited-word commands, inline modals/views, and history cleanup commands.
- `mining_cog.py` claims to be Discord plumbing only, but hidden commands still implement chop/build/explore/use/admin inventory flows.
- `rps_tournament_cog.py` has helper modules and recovery, but the main tournament state machine still lives in the cog.
- `blackjack_cog.py` has recovery helpers and views, but active game/tournament orchestration remains cog-owned.

This is the biggest architectural issue because it slows every future change:
fixing a user-visible bug often requires touching command code, UI code, state
logic, DB calls, and Discord mutation in the same file.

### 🔴 2. Direct DB access is still broad and should be turned into an exception ledger

Direct `utils.db` usage remains common across general features. Some calls are
acceptable short-term read helpers, but others are real business mutations that
should belong to services/workflows.

Highest-priority direct DB areas:

- Economy: `daily`, `work`, and job listing still perform reward/cooldown/query orchestration in the cog.
- Role: threshold/reaction-role CRUD and hidden compatibility commands still use direct DB helpers.
- Moderation: warnings/logs are written directly from manual moderation commands instead of a full moderation service workflow.
- Cleanup: prohibited-word CRUD is direct from commands and modals.
- Mining: inventory/crafting/admin resource updates are direct from cog commands.
- Counting: state persistence is direct and `_save_guild` suppresses exceptions.
- Chain: command group, modals, and hot-path checks all access chain DB helpers directly.
- Inventory: combined economy/mining inventory reads live in the cog file.

Recommended next action: create a `Direct DB Exception Ledger` that classifies
each remaining DB call as `temporary accepted`, `service migration required`, or
`safe read helper`, with owner and target PR.

### 🔴 3. Local permission checks duplicate governance and capability policy

The repo now has central command admission through `bootstrap_access_cog` and
`core.runtime.command_access`, but many features still perform local permission
or role-name checks.

Examples:

- `RoleHubPanelView` checks `manage_roles` / `administrator` directly inside button callbacks.
- `ChannelCog.is_admin_or_owner()` is local command-gating logic.
- Counting uses hardcoded role names `Admin` and `Moderator` for staff checks.
- Mining admin commands manually inspect `ctx.author.guild_permissions.administrator`.
- Utility invite button checks `create_instant_invite` directly.
- Moderation and cleanup command decorators are scattered by command.

Some local Discord permission checks are still useful as immediate UX guards, but
the repo needs a documented policy for which permissions are local UI guards
versus central governance/capability decisions. Without that, Help visibility,
slash visibility, command access, and panel button access can drift.

### 🔴 4. Stateful games have inconsistent restart and recovery behavior

Recovery has improved, but not consistently across game systems.

- Blackjack has solo/PvP/tournament recovery and refund handling.
- RPS has tournament entry persistence/recovery and active tournament state checks.
- Deathmatch active duels are process-local and disappear on restart.
- Utility reminders are explicitly in-memory and cancelled on reload.
- Counting persists guild/channel state, but persistence exceptions are swallowed.

This is acceptable only if the product contract says which features are
best-effort and which are durable. Otherwise, users will experience different
restart behavior across games without a clear reason.

### 🟠 5. Help is strong, but legacy help/settings paths can drift

Help is one of the strongest systems in this audit. It is governance-aware,
uses hub/category routing, opens real subsystem panels when hooks exist, and
adds Back-to-Help navigation.

Remaining drift risks:

- `rpshelp` duplicates Help/Games routing.
- `dm_help` duplicates Help/Games routing.
- `rpssettings` mutates cog-local settings rather than clearly routing through the platform settings service in the reviewed file.
- Slash Help passes `prefix="!"` while prefix Help uses `ctx.prefix`.
- Hidden compatibility commands exist across multiple features and should remain hidden only through the command surface ledger, not ad-hoc convention.

### 🟠 6. Channel visibility UI is useful but incomplete for large guilds

The channel visibility panel supports multi-select and writes through governance,
which is good. It is still limited to the first 25 text channels, and the UI
itself says category and guild-scope controls are future work.

This is a medium-priority product gap because it weakens one of the most
important governance surfaces in larger servers.

### 🟠 7. Cleanup command detection has hardcoded prefixes

`cleanup_cog.py` uses `self.command_prefixes = ["?", "!"]` and a compiled regex
for command-like messages. If the bot prefix changes or guild-specific prefixing
is introduced, cleanup behavior can drift from actual command routing.

This should be normalized through shared command-prefix extraction or the central
command-access resolver path.

## Current state summary

The general feature layer is on track, but only partially migrated. The repo has
strong platform primitives and some good examples of the target shape:

- `bootstrap_access_cog.py` centralizes prefix and slash command admission.
- `help_cog.py` is governance-aware and route-based.
- `games_cog.py` is a router-only hub.
- `logging_cog.py` delegates runtime behavior to `services.server_logging`.
- `leaderboard_cog.py` delegates category differences to `services.rank_providers`.
- `xp_cog.py` delegates XP mutation to `xp_service` and registers an XP message stage.
- Cleanup, Counting, Chain, and XP participate in the message pipeline.
- Blackjack and RPS have meaningful crash/recovery/refund work.

The main risk is not that the bot cannot work. The risk is that the general
feature layer remains uneven: some features follow the new platform model, while
others still behave like older self-contained cogs.

## Confirmed problems by subsystem

### Help

Confirmed strengths:

- Governance-aware visibility resolution.
- Tier/hub grouping.
- Direct navigation into subsystem panels via `build_help_menu_view`.
- Back-to-Help navigation attached to opened panels.
- Prefix and slash front doors exist.

Confirmed risks:

- Slash Help uses hardcoded `!` in route rendering.
- Help can only be as accurate as subsystem metadata and hidden-command classification.

### Admin

Confirmed strengths:

- Admin panel can route into Settings, Platform, Diagnostics, Logging, Cleanup, and Help through existing hooks.
- Restart delegates to lifecycle service instead of owning raw process control.
- Slash sync/list diagnostics exist.

Confirmed risks:

- `_AdminPanelView` and `_LogLevelModal` live inside `admin_cog.py`.
- The cog still mixes operator commands, runtime control, panel UI, and navigation.

### Economy

Confirmed strengths:

- Some mutation paths delegate to `economy_service`.
- Work/shop panels exist outside the main cog.
- Logging channel mutation uses a settings mutation pipeline.

Confirmed risks:

- `daily` still owns cooldown/streak/reward orchestration in the cog.
- `work` still performs direct DB reads and state checks from the cog.
- Job listing reads inventory and settings directly from the cog path.

### Blackjack

Confirmed strengths:

- Recovery and cleanup are significantly better than a purely in-memory game.
- Solo, PvP, and tournament recovery flows are present.
- Entry-fee refund handling exists for stranded tournaments.

Confirmed risks:

- The cog still owns active game/tournament state maps and orchestration.
- Multiple game modes and tournament flows remain coordinated from the cog instead of a workflow layer.

### RPS

Confirmed strengths:

- Tournament active-state service is used.
- Entry fee state is persisted for recovery.
- Helper modules exist for bot matches, persistence, quickplay, rules, stage handling, and channel helpers.

Confirmed risks:

- Registration, player lists, scores, matches, channels, current round, paid players, and tournament progression remain cog state.
- `rpssettings` mutates `self.settings` in the cog.
- Help/settings surfaces can drift from platform settings.

### Roles

Confirmed strengths:

- Time-role assignment delegates decision/mutation to `services.role_automation`.
- XP role stripping regression is explicitly guarded by excluding XP rows from time-role reconciliation.
- View submodules exist under `views.roles`.

Confirmed risks:

- `RoleHubPanelView` still lives in `role_cog.py`.
- Reaction role CRUD and hidden compatibility commands use direct DB/Discord mutation paths.
- Button permission checks are local.

### XP

Confirmed strengths:

- `xp_service.award` and `xp_service.reset` are used for primary XP mutations.
- XP listener is extracted and registered as a message-pipeline stage.
- Participation gate is centralized inside the XP listener.

Confirmed risks:

- XP threshold role assignment is still listener-owned instead of a reusable reward-role workflow.

### Moderation

Confirmed strengths:

- Moderation panel is in a view module.
- Slash moderation entry exists and mirrors the prefix panel permission gate.

Confirmed risks:

- Manual warn/timeout/kick/ban/unban/clearwarnings/modlogs paths still directly call DB and Discord mutation.
- Full moderation behavior should route through `moderation_service` to keep audit/event semantics consistent.

### Cleanup

Confirmed strengths:

- Cleanup participates in the message pipeline.
- Command-policy deletion routes through governance and `moderation_service.auto_delete`.
- Prohibited-word deletion routes through `moderation_service.auto_delete`.
- History cleanup has confirmation and safety limits.

Confirmed risks:

- Command prefix detection is hardcoded to `?` and `!`.
- Word management modals/views live in the cog.
- Prohibited-word CRUD is direct DB access from commands/modals.

### Channel management

Confirmed strengths:

- Channel view modules exist under `views.channels`.
- Visibility panel supports multi-select.
- Visibility writes go through governance mutation service.

Confirmed risks:

- Direct destructive channel commands remain in `channel_cog.py`.
- Visibility panel is capped to the first 25 text channels.
- Category/guild-scope controls are explicitly future work.

### Inventory

Confirmed strengths:

- Inventory provides a unified view over economy and mining inventory.
- Category drill-down UI exists.

Confirmed risks:

- Item catalogue, combined inventory query, hub view, category view, and command live in one cog file.
- This should become an inventory read service plus `views.inventory` module before expansion.

### Mining

Confirmed strengths:

- Recipes and rewards have moved to mining submodules.
- Main mining views exist under `views.mining`.

Confirmed risks:

- The cog docstring says it is Discord plumbing only, but hidden chop/build/buildlist/buildable/explore/use/admin commands still contain game/resource logic.
- Mining inventory mutation is direct DB access.

### Counting

Confirmed strengths:

- Hot-path message handling has a good Validate/Mutate/Apply split.
- Discord I/O happens outside the scope lock.
- Counting is integrated into the message pipeline before XP.

Confirmed risks:

- Command-side match creation still builds and mutates state dicts directly in the cog.
- `_save_guild` catches all exceptions and silently ignores persistence failure.

### Chain

Confirmed strengths:

- Chain enforcement is now a message-pipeline stage.
- Deletions route through `moderation_service.auto_delete`.

Confirmed risks:

- Commands, DB writes, message-stage logic, modals, and panel view live in one cog file.
- Chain configuration should move behind a service.

### Deathmatch

Confirmed strengths:

- Help/Games panel hook exists.
- Turn timeout reads from settings resolution.

Confirmed risks:

- Duel domain model, view classes, active-duel state, challenge flow, and leaderboard update all live in the cog.
- Active duels are process-local and not recoverable.

### Leaderboards

Confirmed strengths:

- Provider registry is the right abstraction.
- Aliases route into the same provider path.
- Adding a category should not require rewriting the cog.

Confirmed risks:

- The view still lives in the cog file, but this is a lower-priority cleanup because the provider abstraction is sound.

### Logging

Confirmed strengths:

- Logging command/panel surface is separated from runtime logging behavior.
- Status embeds read from `server_logging`.
- Routes/bindings are centralized.

Confirmed risks:

- No major risk found in the reviewed surface.

### Diagnostics / Platform

Confirmed strengths:

- Broad read-only operator surface exists: status, readiness, anchors, identity, runtime, caches, locks, tasks, views, slow paths, schemas, settings registry, customization, provisioning, resources, bindings, flags, migrations, consistency, and command-access diagnostics.

Confirmed risks:

- The diagnostic cog is very large. It is currently acceptable because most behavior delegates to helper embed builders, but it should remain read-only/delegating to avoid becoming another mixed admin surface.

### Utility

Confirmed strengths:

- Utility hub exists for common user operations.
- Slash entry exists.

Confirmed risks:

- Reminders are in-memory only and cancelled on reload.
- Panel view and modals live inside `utility_cog.py`.
- Reminder persistence should be a deliberate product decision, not an accidental limitation.

## Architecture drift patterns

### Pattern 1 — Partial decomposition

Several cogs have been partially decomposed, but still retain old hidden command
paths or stateful workflows. This creates two maintenance models in the same
feature: new panels/services and old direct command logic.

### Pattern 2 — View classes still inside cogs

Some features use `views/**` cleanly, while others define views and modals in cog
files. This weakens testability and makes cogs harder to reason about.

### Pattern 3 — Local permission checks beside central command access

The central command-access resolver is a good platform primitive, but feature
buttons and legacy commands still use local permission logic. This should be
classified as either intentional UI guardrails or migration debt.

### Pattern 4 — State durability differs by feature without a visible contract

Blackjack/RPS have recovery work; Deathmatch/Utility do not. Counting persists
state but hides save errors. This should be turned into a documented feature
contract: durable, recoverable, or intentionally best-effort.

## Recommended PR sequence

### PR 1 — Direct DB Exception Ledger, docs only

Create a living ledger of remaining direct DB calls by feature:

- path/function
- read vs write
- current owner
- accepted short-term or migration required
- target service/workflow owner
- test requirement

This should happen before changing code so future implementation PRs do not
remove useful compatibility behavior accidentally.

### PR 2 — Move embedded views/modals out of cogs

Move UI classes into `views/**` or feature panel modules without changing
behavior:

- `RoleHubPanelView` → `views.roles.hub_panel`
- `_AdminPanelView` / `_LogLevelModal` → `views.admin`
- inventory views → `views.inventory`
- utility panel/modals → `views.utility`
- deathmatch duel/challenge views → `views.games.deathmatch_*`
- chain modals/view → `views.chain`
- cleanup word modals/view → `views.cleanup`

Keep this PR mostly mechanical and covered by import/backward-compat tests.

### PR 3 — Service ownership pass for DB/business mutations

Move business and DB mutations behind services/workflows:

- economy daily/work/job listing
- mining inventory/crafting/use/explore/admin resource mutation
- chain config CRUD
- cleanup prohibited-word CRUD
- moderation warn/timeout/kick/ban/unban/log actions
- role reaction-role CRUD
- inventory read aggregation

### PR 4 — Game/session durability contract

Define and implement durability rules for:

- Blackjack
- RPS
- Deathmatch
- Utility reminders
- Counting

Each should be classified as durable, recoverable, or best-effort. Tests and user
messages should match that classification.

### PR 5 — Governance and permission parity pass

Centralize or document remaining local permission checks. Ensure Help visibility,
command access, slash default permissions, prefix decorators, and panel button
checks do not contradict each other.

### PR 6 — Help/settings parity cleanup

Review legacy local help/settings commands and either:

- keep them as compatibility aliases with clear hidden/help classification, or
- route them to the platform Help/Settings panels.

Targets include RPS, Deathmatch, Chain, Utility, Inventory, Mining hidden commands,
and any old settings surfaces.

## Missing verification / tests to add

High-priority tests:

- command-access and local permission parity tests
- direct DB ledger enforcement test or lint helper
- Help route actionability for every visible subsystem
- slash/prefix parity for top-level hubs
- message-pipeline ordering test for cleanup/counting/chain/xp/rps
- Counting persistence failure visibility test
- Channel visibility large-guild pagination test
- Deathmatch restart behavior test or explicit best-effort contract test
- Utility reminder reload behavior test or persistence migration test
- RPS settings persistence/Help parity test

Medium-priority tests:

- hidden compatibility command classification
- view import/backward-compat tests after moving embedded view classes
- role reaction-role service tests
- cleanup prohibited-word service tests
- inventory aggregation service tests

## Recommended next destination

Recommended destination: **Revision**, then **Decisions**.

The repo is not blocked, but it should not jump straight into another broad
implementation pass. The next useful step is to consolidate this with the other
audit agents, decide which architecture drift is accepted temporarily, and then
plan the cleanup PR sequence.

## Copy-paste collaboration summary

```text
Agent C reviewed the general Discord feature layer for menno420/superbot. The audit
was code-read through GitHub connector against code baseline d583dcb / PR #506;
this docs PR is based on newer main eb20bac after docs-only PRs #507 and #508.
No code was changed and local tests could not be run.

Core finding: the feature layer is usable but architecturally uneven. Strong
platform patterns exist: central command access, governance-aware Help routing,
Games hub router-only design, Logging service ownership, Leaderboard providers,
message-pipeline stages for Cleanup/Counting/Chain/XP/RPS, and partial recovery
for Blackjack/RPS.

Most important problems:
1. Many cogs are still not thin adapters. Role/Admin/Inventory/Utility/Deathmatch/
   Chain/Cleanup/Channel/Mining/Economy/Blackjack/RPS still mix views, modals,
   direct DB access, business logic, state machines, Discord mutation, or local
   permission checks.
2. Direct DB access remains broad and needs a Direct DB Exception Ledger before
   more feature work.
3. Local permission checks duplicate governance/capability policy and can drift
   from Help visibility and command access.
4. Stateful games have inconsistent restart/recovery behavior: Blackjack/RPS have
   partial recovery, Deathmatch and Utility are process-local, Counting persists
   but suppresses save failures.
5. Help is strong, but legacy help/settings routes like rpshelp, dm_help, and
   rpssettings can drift.
6. Channel visibility is governance-backed but limited to first 25 text channels;
   category/guild scope is still future work.
7. Cleanup hardcodes ?/! command prefixes separately from real command routing.

Recommended PR sequence: Direct DB Exception Ledger; move embedded views/modals
out of cogs; migrate business/DB mutations into services; define game/session
durability contract; governance/permission parity pass; Help/settings parity
cleanup.
```
