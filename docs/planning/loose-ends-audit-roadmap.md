# SuperBot Loose Ends Audit Roadmap

> **Status:** `plan` — doc-only planning PR

Runtime impact: none  
Baseline inspected: `main` at Phase 9b merge (`baacf461`)  
Purpose: define the safest completion pass before feature expansion, with a button-first command surface, complete Help discovery, consistent panel navigation, and a clear slash-front-door strategy.

> **Status note (S1):** The PR sequence L1–L6 below is **superseded** by [`building-roadmap/mother-hub-map.md`](../building-roadmap/mother-hub-map.md) S1–S13. PR L1 (shared navigation helper) partially landed via PR #130 — S2 in the new sequence completes the migration. The findings, navigation duplication evidence, placeholder inventory, and panel/subsystem inventory in this document remain valid as the source audit; only the PR sequence is replaced.
>
> **Stabilization plan update (PRs #143-#151, 2026-05):** A nine-PR
> stabilization sequence landed on top of the post-PR-#142 baseline:
>
> - **Navigation duplication.** Five sibling Back-to-X helpers now
>   exist (Help / Admin / Settings / Games / Economy) — PR #143 added
>   `attach_back_to_economy_button` to round out the family for the
>   live mother hubs. The duplication finding in Finding 1 below is
>   still accurate as audit context, but the migration is now
>   feature-complete for the affected surface.
> - **Phase 4 parent_hub filter.** PR #145 declared `parent_hub`
>   metadata on the eight S7-S10 children (`inventory`, `leaderboard`,
>   `xp`, `role`, `cleanup`, `logging`, `proof_channel`, `general`),
>   so the filter consistently hides them from the top-level Help
>   overview.
> - **Community hub.** PR #146 migrated `CommunityHubView` to
>   metadata-driven discovery (primary children from `SUBSYSTEMS`,
>   cross-links from `hub_registry`), mirroring the Games hub
>   pattern.
> - **Direct-write remediation.** PR #147 and PR #148 routed the
>   last XP and Economy direct-write sites through
>   `SettingsMutationPipeline` (closing the audit gap that Finding 5
>   flagged).
> - **Settings input modes.** PR #149 added the `channel_select`,
>   `role_select`, and `numeric_presets` widgets and wired the
>   dispatcher via the new `SettingSpec.input_hint` field.
> - **Settings default-on.** PR #150 flipped
>   `settings.manager_cog.enabled` to default ON with the
>   `SUPERBOT_FF_SETTINGS__MANAGER_COG__ENABLED=off` env-var kill-switch
>   retained.
> - **Slash front door.** PR #151 added `/help` reusing `HelpRoute` —
>   the first slash command in the bot. The remaining slash front
>   doors (`/games`, `/economy`, `/community`, `/utility`,
>   `/moderation`, `/admin`, `/platform`, `/settings`) are
>   straightforward follow-ups using the same recipe.
>
> The placeholder inventory below remains the canonical audit; the
> Mining root "↩ Overview" no-op button was removed in PR #143 and
> the Games-fallback finding still applies.

---

## Executive summary

SuperBot is now beyond the point where the main problem is missing backend infrastructure. The current loose ends are mostly **interface completion, route consistency, and discoverability**:

1. The bot already has strong foundations: `BaseView`, `HubView`, `send_panel`, governance-aware Help routing, Games hub routing, Settings/Platform/Logging/Cleanup panels, binding/provisioning/settings mutation pipelines, and Phase 9a/9b logging route UI.
2. Navigation is still duplicated. Help, Games, Settings/Admin-style panels, Logging Routes, and channel subpanels each implement local `Back`, `Back to Help`, `Back to Games`, `Back to Logging`, `Overview`, or `Refresh` behavior.
3. Several panels are discoverable and wired, but the user experience is not yet uniformly button-first. Some commands still exist mainly as typed subcommands, while some buttons are router-only or fallback to command-list embeds.
4. Placeholder-style UX remains in at least the channel visibility flow: category and guild-scope controls are described as “coming soon” while only per-channel controls exist today.
5. Slash commands should wait until panel routing is stable. `/help`, `/games`, `/cleanup`, `/platform`, `/settings`, `/logging`, `/admin`, and `/setup` should be thin front doors, not a parallel command system.
6. Phase 9c should not start until the navigation and panel-completion pass is stable. When started, publishers should be added only at canonical event ownership points, not by wrapping every warning log.

The recommended next implementation PR is **Phase L1: Shared Navigation Helper**, followed by **Phase L2: Help Discovery Completion** and **Phase L3: Placeholder/Button Execution Completion**.

---

## Current architecture facts used by this audit

### Existing stable primitives

| Primitive | Current role | Completion implication |
|---|---|---|
| `views.base.BaseView` | Invoker restriction, timeout disabling, error handling | Keep using it for general interactive panels. |
| `views.base.HubView` | Standard hub timeout and private panel behavior | All hub panels should inherit or clearly justify divergence. |
| `views.base.send_panel` | Sends embed/view and binds `view.message` | Direct `ctx.send(embed=..., view=...)` should be audited and replaced where timeout editing matters. |
| `HelpPanelView` | Governance-aware paginated help menu | Should become the canonical discovery graph for subsystem panels. |
| `build_help_menu_view` hooks | Let Help open real subsystem panels | This contract should be formalized and expanded with optional navigation state. |
| `SUBSYSTEMS.parent_hub` | Hides child subsystems behind hubs | Keep using it for Games and future mother hubs. |
| Mutation pipelines | Canonical write boundaries | Button actions must route through these, not direct DB writes. |

### Already landed interface phases

The current interface roadmap reports that these are landed:

- Games hub and `parent_hub` filtering.
- Cleanup panel shell.
- Access policy explorer.
- Platform flag manager.
- Game panels for Blackjack/RPS as router-only surfaces.
- Hub UI standard documentation.
- Phase 8 audit finding that Role, Economy, Proof, Inventory/Leaderboard, and Channel panels already expose integrated hub views through `build_help_menu_view`.
- Phase 9a/9b logging schema, route resolver, and routes UI.

### Deferred items that remain important

| Deferred item | Why it matters now |
|---|---|
| Shared navigation helpers | Back-button duplication is now the largest UX consistency risk. |
| Cleanup settings foundation | Should wait until runtime consumes real scalar cleanup settings. |
| Broader platform management actions | Need canonical pipelines before UI buttons are added. |
| Slash front doors | Should come after panels are stable. |
| Setup wizard | Should come after command/panel discovery and core hubs are consistent. |
| Phase 9c logging publishers | Needs architecture decision on publisher ownership. |

---

## Audit findings

## Finding 1 — Navigation helpers are still duplicated

### Evidence

- `HelpPanelView` has `_attach_back_to_help_button`, which dynamically appends `↩ Back to Help` to subsystem views opened from Help.
- `GamesHubView` has `attach_back_to_games_button`, explicitly documented as an inline factory waiting for the deferred shared helper phase.
- `LoggingRoutesView` has its own `↩ Back to Logging` callback.
- Platform hub and Logging panel each have local `↩ Overview` / `Refresh` behavior.
- Channel visibility subpanels implement local `↩ Back` behavior.

### Risk

Medium. The bot works, but every new panel or subpage risks creating another slightly different return path. This becomes worse once slash front doors and setup wizard routes exist.

### Recommended fix

Add a small shared module, not a new framework:

```text
disbot/views/navigation.py
```

Initial public surface:

```python
@dataclass(frozen=True)
class PanelRoute:
    name: str
    label: str
    subsystem: str | None = None

@dataclass(frozen=True)
class PanelNavigationState:
    source: Literal["help", "command", "slash", "parent_panel", "setup"]
    help_page: int | None = None
    parent: PanelRoute | None = None

async def transition_panel(interaction, *, embed, view) -> None: ...

def attach_back_button(view, *, label, custom_id, callback, row=4) -> bool: ...

def attach_back_to_help(view, *, page: int) -> bool: ...

def attach_back_to_parent(view, *, parent_label, parent_factory) -> bool: ...
```

Rules:

- The helper must be import-light: stdlib + `discord` + local safe interaction helpers only.
- View reconstruction should be passed as callables to avoid cog import cycles.
- The helper should log component-limit skips and transition failures with view class, subsystem, guild, channel, message, and user ids.

---

## Finding 2 — Help is close to being the discovery graph, but the panel contract is not formal yet

### Evidence

- Help already opens real panels through `build_help_menu_view(interaction)` when present.
- Help falls back to command-list embeds if a cog lacks that hook or if the hook fails.
- The Games hub uses the same child-cog hook pattern.
- Many major cogs already have hooks, including games, cleanup, logging, settings, platform diagnostics, channels, role, economy, inventory/leaderboard, proof, mining, and general surfaces.

### Risk

Medium-low. The direction is correct, but there is no typed/shared contract for navigation context. Help-opened panels and command-opened panels can behave differently.

### Recommended fix

Formalize the hook as:

```python
async def build_help_menu_view(
    self,
    interaction: discord.Interaction,
    nav_state: PanelNavigationState | None = None,
) -> tuple[discord.Embed, discord.ui.View]:
    ...
```

Migration plan:

1. Keep compatibility with the old one-argument hook.
2. Update Help and Games hub to pass `nav_state` when supported.
3. Update high-value panels first: Logging, Cleanup, Games, Settings, Platform, Admin, Channels.
4. Add tests that every top-level visible subsystem either has a hook or has an explicit fallback reason.

---

## Finding 3 — Button execution parity is incomplete

### Target state

Every important command should fall into exactly one category:

| Category | Meaning |
|---|---|
| Button-executable | Common action directly runs from a button/select/modal. |
| Subpanel-executable | Button opens a subpanel where the action runs. |
| Text-only diagnostic | Advanced or filtered diagnostic remains typed, but is discoverable. |
| Deprecated/hidden | Duplicate typed command is replaced by a panel path. |

### Current state pattern

The repo is moving toward button-first operation, but not all typed subcommands should become top-level buttons. Platform is a good example: the panel exposes grouped read-only surfaces, while text commands keep advanced filters and limits. That pattern should be applied deliberately everywhere.

### Recommended fix

Create a command-to-panel inventory in the next audit implementation PR by introspecting loaded cogs and scanning `commands.command`, `commands.group`, and `build_help_menu_view` usage. The final inventory should classify every command:

- user-facing main command
- panel front door
- subcommand represented by a button
- admin/config mutation
- diagnostic/power-user text command
- candidate for deprecation or hidden status

---

## Finding 4 — Placeholder/future-state UX should be eliminated or tracked

### Evidence

The channel visibility panel currently says category and guild-scope controls are “coming soon” while the implemented flow configures up to 25 text channels only. That is useful context for operators but should be tracked as a roadmap item or replaced with a real scope selector.

### Risk

Low-medium. Placeholder language makes the bot feel unfinished and can confuse testers. The backend may already be close because visibility states support scope concepts; the UI only exposes channel scope.

### Recommended fix

For every placeholder/future-state item, choose one of three actions:

1. **Implement now** if a service/pipeline already exists.
2. **Route to an existing panel** if the functionality exists elsewhere.
3. **Remove/disable and document** if the backend does not exist yet.

For channel visibility specifically:

- Short-term: rewrite the copy to say “This panel currently configures channel scope.”
- Next implementation: add a scope selector for guild/category/channel only if `governance_service` and DB storage already support those scopes safely.

---

## Finding 5 — Slash commands should be front doors only

### Evidence

Search did not show an existing app-command/slash layer in the inspected areas. The current roadmap already defers Phase 10 slash front doors.

### Recommended slash model

Do not create slash commands for every action. Use slash commands as stable front doors:

| Slash command | Opens |
|---|---|
| `/help` | Help panel |
| `/admin` | Admin hub |
| `/games` | Games hub |
| `/mining` | Mining hub |
| `/cleanup` | Cleanup panel |
| `/logging` | Logging panel |
| `/platform` | Platform diagnostics hub |
| `/settings` | Settings hub |
| `/setup` | Setup wizard |

Each slash wrapper should call the same panel builder used by `!` commands and Help. No duplicate UI logic.

---

## Finding 6 — Phase 9c should wait until publisher ownership is decided

### Current Phase 9 state

| Sub-phase | State | Scope |
|---|---|---|
| 9a | Merged | Logging schema/resolver foundation. |
| 9b | Merged | Logging Routes UI, seven route Set/Create flows. |
| 9c | Not started | Publisher callsites, bus subscribers, per-route counters. |

### Recommended publisher strategy

| Event | Publisher ownership |
|---|---|
| `audit.action_recorded` | Emit from the canonical audit writer or shared mutation audit layer. Do not emit manually from every cog/button. |
| `runtime.error_raised` | Emit from centralized command, view, event bus, lifecycle/startup error handlers. |
| `runtime.warning_emitted` | Start with curated platform warnings only. Do not wrap every `logger.warning(...)`. |

Phase 9c implementation should start with audit events, then runtime errors, then curated warnings.

---

## Panel and subsystem completion inventory

This inventory is intentionally planning-level. A follow-up implementation PR should generate or verify it source-line-by-source with tests.

| Subsystem / surface | Current state | Loose end | Priority |
|---|---|---|---|
| Help | Governance-aware paginated panel; opens subsystem panels through hooks. | Move `Back to Help` into shared navigation helper; pass optional nav state. | P0 |
| Games | Router-only hub discovers `parent_hub == games`; attaches local Back to Games. | Migrate local back helper; ensure all child result panels return cleanly to Games. | P0 |
| Logging | Phase 9b Routes subpage exists; Set/Create routes use existing pipelines. | Migrate Back to Logging/Overview/Refresh to shared helper; defer Phase 9c. | P0 |
| Cleanup | Cleanup hub and prohibited-words/admin flows exist. | Verify scan history and word-management buttons are fully real; add consistent parent/help back paths. | P0 |
| Channel manager | Has create/delete/restrict/visibility panels and local subpanel navigation. | Replace placeholder copy or implement category/guild visibility scope; migrate Back. | P1 |
| Platform | Read-only hub groups existing `!platform` subcommands into selects. | Add slash front door later; keep advanced filters text-only. | P1 |
| Settings | Settings hub and subsystem views exist. | Migrate back helpers; ensure all setting edits route through mutation pipeline. | P1 |
| Role | Phase 8 says hub view exists. | Confirm help/direct/slash discovery; ensure role mutation buttons use canonical role/binding services. | P1 |
| Economy / Work / Shop | Hub/panels exist; screenshots show action results can dead-end with disabled dropdowns. | Ensure cooldown/result panels always have Back/Refresh path to economy hub. | P1 |
| Mining | Mining hub is button-first and visible in screenshots. | Ensure all result panels preserve Back to Mining/Games/Help depending on entry path. | P1 |
| XP | Rank and modal views exist. | Confirm whether user-facing XP commands need a hub or only command-list fallback. | P2 |
| Inventory / Leaderboard | Phase 8 says integrated views exist. | Ensure both are discoverable from Help and relevant hubs; consider parent hub grouping. | P2 |
| Proof / Prize | Phase 8 says integrated manager view exists. | Confirm button execution and help discovery; keep admin-only visibility correct. | P2 |
| General / Utility | Mixed simple commands. | Decide which remain text-only and which should become panel actions. | P2 |
| Counting / Chain | Games hub children. | Confirm direct command path and Games hub return path; avoid message-pipeline conflicts. | P2 |
| Admin menu | Existing admin panel integrations. | Make it route to subsystem-owned panels, not duplicate logic. | P1 |
| Setup wizard | Future major hub. | Wait until P0/P1 loose ends are stable. | Later |

---

## Placeholder and future-state inventory

| Location | Current issue | Recommended action |
|---|---|---|
| Channel visibility panel | Copy says category and guild-scope controls are coming soon. | Either implement scope selector if backend supports it, or replace with precise current-scope wording and track scope expansion. |
| Games fallback embeds | Fallback footer says panel view not implemented yet when a child lacks a hook. | Keep fallback, but add invariant tests so top-level important subsystems do not silently remain fallback-only. |
| Phase 9c route counters | Would be zero until publishers/subscribers exist. | Do not add counters until publisher paths are implemented. |
| Setup wizard | Planned but not ready. | Do not expose fake setup actions; wait for panel-discovery and navigation consistency. |

---

## Recommended PR sequence

## PR L1 — Shared navigation helper

Runtime impact: low  
Risk: low-medium  
Goal: remove duplicated back-button logic without changing product behavior.

Scope:

- Add `disbot/views/navigation.py`.
- Move Help back-button behavior into shared helper while preserving UX.
- Move Games back-button behavior into shared helper.
- Move Logging Routes back-to-Logging behavior into shared helper or a shared parent-panel pattern.
- Keep shims for one PR if needed to reduce churn.

Tests:

- Helper adds a button under the 25-component limit.
- Helper refuses and logs at 25 components.
- Back to Help rebuilds governance-aware Help state.
- Back to Games rebuilds `GamesHubView`.
- Back to Logging rebuilds `LoggingPanelView`.

Manual smoke:

- `!help` → Games → child → Back to Games.
- `!help` → Logging → Back to Help.
- `!logging routes` → Back to Logging.

## PR L2 — Help discovery contract

Runtime impact: low-medium  
Risk: medium  
Goal: make Help the canonical discovery graph.

Scope:

- Add optional `PanelNavigationState` support.
- Update Help and Games hub to pass nav state when supported.
- Add invariant tests: every visible top-level subsystem must have either a panel hook or an explicit fallback classification.
- Update docs so new cogs know how to expose panels.

## PR L3 — Placeholder/button execution pass

Runtime impact: medium  
Risk: medium  
Goal: remove unfinished user-facing buttons/messages.

Scope:

- Replace channel visibility “coming soon” copy or implement scope selector.
- Verify cleanup prohibited-word and scan-history actions are real and not dead-end panels.
- Verify economy/work cooldown result panels provide a live return path.
- Verify mining/game result panels preserve navigation.

## PR L4 — Main hub alignment

Runtime impact: medium  
Risk: medium  
Goal: make Admin/Settings/Platform/Help route to subsystem-owned panels instead of duplicating logic.

Scope:

- Admin menu routes to Logging/Cleanup/Settings/Platform/Role/Channel panels.
- Settings and Platform stay owner-specific; Admin does not duplicate their implementation.
- Confirm all dangerous mutations still require confirmation.

## PR L5 — Slash front doors

Runtime impact: low-medium  
Risk: medium due to Discord sync behavior  
Goal: add slash wrappers only after panels are stable.

Scope:

- `/help`
- `/admin`
- `/games`
- `/mining`
- `/cleanup`
- `/logging`
- `/platform`
- `/settings`
- `/setup` only if setup wizard exists; otherwise omit.

Rules:

- Slash commands call the same panel builders as `!` commands.
- No duplicate slash-only UI.
- No one slash command per sub-action.

## PR L6 — Phase 9c scope doc and implementation

Runtime impact: medium-high  
Risk: medium-high due to event volume  
Goal: wire real publishers/subscribers for advanced logging routes.

Order:

1. `audit.action_recorded` from canonical audit writer.
2. `runtime.error_raised` from central error handlers.
3. `runtime.warning_emitted` from curated platform warnings.
4. Server logging subscribers.
5. Per-route counters.

---

## Definition of done for the loose-ends phase

The bot is ready for major expansion when:

- Every top-level subsystem is reachable from Help.
- Every important panel is reachable from a `!` command.
- Slash front doors exist for the main hubs or are intentionally deferred.
- No visible button only sends a placeholder message unless explicitly tracked.
- Every subpanel has a consistent Back/Overview/Refresh path.
- Direct command entry and Help entry use the same panel-building logic.
- Admin/Setup/Help panels route to subsystem-owned panels instead of duplicating logic.
- Dangerous mutations use confirmation views and canonical pipelines.
- `!platform identity` and customization/discoverability invariants pass.
- Manual Discord smoke confirms Help → panel → child → back flows for Help, Games, Logging, Cleanup, Settings, Platform, Channels, and Admin.

---

## Manual smoke checklist for the next implementation PRs

- `!help` opens fresh Help panel.
- Help page navigation works across all pages.
- Each Help category opens a real panel or a clear command-list fallback.
- Back to Help works after opening a panel from Help.
- `!games` opens Games hub.
- Games child panels open and return to Games.
- `!logging` opens Logging panel.
- `!logging routes` opens Routes subpage.
- Routes Set/Create flows work for all seven route kinds.
- Back to Logging works from Routes.
- Cleanup prohibited-word management works.
- Cleanup scan history opens real data or a clearly tracked no-data state.
- Channel manager visibility panel does not advertise unavailable scope controls without tracking them.
- Platform hub selects render all grouped diagnostics.
- Settings hub edits go through mutation pipelines.
- Economy/work/mining result panels have return paths after cooldown/action results.
- Unauthorized users cannot operate private panels.
- Timed-out panels disable buttons consistently.

---

## Notes for future agents

This document is intentionally doc-only. Do not treat it as proof that every listed panel was manually smoke-tested. It is a source-guided roadmap based on the current architecture and the prior interface-completion roadmap.

When implementing, prefer small PRs with focused tests. Do not bundle navigation helper extraction, slash commands, placeholder replacement, and Phase 9c into one change.
