# SuperBot — Foundational infrastructure plan

> **Status:** planning. This document proposes the next platform
> layer (post-stabilization, pre-tournament-expansion). It is **not**
> binding. Binding architecture lives in `architecture.md`,
> `runtime_contracts.md`, `ownership.md`, and the ADRs under
> `docs/decisions/`. This plan extends those — it does not replace
> them.
>
> Scope discipline: every proposal here must (a) reuse an existing
> primitive where one exists, (b) clear the §A2.1 two-consumer rule,
> and (c) preserve the freeze guarantees from PR #59 / PR #60.

---

## 0. Executive summary

After the post-stabilization audit (three forensic sweeps covering
guild-resource access, the event/message pipeline, and the
setup/UI/config surface), the bottom line is:

- The platform is **further along than the prompt assumed**.
  Governance, services, navigation_stack, persistent_views,
  message_anchor_manager, ephemeral_surface_manager, state_store,
  GovernanceMutationPipeline, and GovernanceTemplate are all in
  production and well-tested.
- Real centralization gaps cluster in **three** places, not eight:
  1. **Guild-resource resolution** (channel / role / member lookup
     is duplicated across ~30 call sites with no shared resolver).
  2. **Message pipeline orchestration** (five independent
     `on_message` handlers run concurrently with no defined order
     or shared filtering stage; auto-mod is fragmented across
     three cogs that don't emit moderation events).
  3. **Setup orchestration** (no `!setup` entry point; no
     first-time-use detection; `onboarding_profiles.py` is
     orphaned; bulk channel/role provisioning is missing).
- Most other concerns the prompt raised (per-guild config,
  permission gating, persistent UI, multi-step wizards, cog
  toggling, template application, audit logging, session
  resumption) **already have foundations** and need integration,
  not rewriting.

The recommendation in §3-§6 is therefore a **narrow, layered**
build-out: extract one resolver, orchestrate one pipeline, build
one setup framework, and stop. No speculative platform layer, no
service registry, no "intelligent admin tooling" framework — those
are deferred until two real consumers exist.

---

## 1. Current infrastructure inventory

This section names the existing infrastructure so later sections
can reference it precisely. Citations are to file:line.

### 1.1 Platform primitives (already centralized, production)

| Primitive | File | One-line purpose |
|---|---|---|
| `BaseView` / `HubView` / `PersistentView` | `disbot/views/base.py:69`, `124`; `disbot/core/runtime/persistent_views.py:45` | Canonical interactive view lifecycle (closed by PR #60). |
| `send_panel` / `safe_defer` / `safe_edit` / `safe_followup` | `disbot/views/base.py:11`; `disbot/core/runtime/interaction_helpers.py` | Canonical send-and-update path; message binding for timeout edits. |
| `message_anchor_manager` | `disbot/core/runtime/message_anchor_manager.py` | Tracks (user, channel, subsystem) → message_id for restart-safe panels. |
| `navigation_stack` | `disbot/core/runtime/navigation_stack.py` | Per-session breadcrumb stack persisted to `runtime_session_state`. Per-session asyncio.Lock. |
| `state_store` | `disbot/core/runtime/state_store.py` | Session-scoped KV (`session_id, key, value`). |
| `ephemeral_surface_manager` | `disbot/core/runtime/ephemeral_surface_manager.py` | `send_confirmation` / `send_alert` overlays that don't replace the panel. |
| `EventBus` | `disbot/core/events.py` + `events_catalogue.py` | Pub/sub with catalogue enforcement, 5s handler timeout, unknown-event metric. |
| `interaction_router` | `disbot/core/runtime/interaction_router.py` | `on_interaction` dispatch by custom_id prefix. |
| `live_update_scheduler` | (referenced in audits) | Subscribes to (subsystem, event) pairs; refreshes panels by anchor. |
| `guild_lifecycle.teardown` | `disbot/guild_lifecycle.py:21-67` | 9-step idempotent guild cleanup on `on_guild_remove`. |

### 1.2 Service layer (audited mutations + event emission)

All follow the same shape: atomic DB write → immutable audit row →
EventBus emit. Ownership boundaries are enforced by INV-F/G AST
tests. See `docs/ownership.md`.

| Service | File | Owns |
|---|---|---|
| `economy_service` | `disbot/services/economy_service.py` | Coin balance + `economy_audit_log` |
| `xp_service` | `disbot/services/xp_service.py` | XP + level transitions |
| `moderation_service` | `disbot/services/moderation_service.py` | Warn / timeout / kick / ban / unban + `mod_logs` |
| `game_state_service` | `disbot/services/game_state_service.py` | Game-state checkpoints (not restart-safe — ADR-002) |
| `governance_service` | `disbot/services/governance_service.py` | Legacy re-export shim → `governance/` package |
| `diagnostics_service` | `disbot/services/diagnostics_service.py` | Snapshot provider registry for `!platform <name>` |
| `metrics` | `disbot/services/metrics.py` | Prometheus counters/gauges/histograms |
| `webhook_reporter` | `disbot/services/webhook_reporter.py` | Async webhook logger for bot events |

### 1.3 Governance package (subsystem visibility + command policy)

Twelve modules, ~70KB. Owns subsystem-visibility resolution,
command-execution policy, cleanup policy, and policy templates.
Public façade in `disbot/governance/__init__.py:243-301`.

Key APIs already production:

- `resolve_command_policy(ctx)` → visibility + cleanup + feedback
- `resolve_execution(ctx)` → allowed? cleanup rules?
- `GovernanceMutationPipeline` → authority validation +
  transactional write + cache invalidation + event emission
- `export_template / apply_template / save_template / load_template`
  in `governance/templates.py` (governance-state only, not Discord
  resources)

5-tier hierarchy: `user / trusted / staff / moderator /
administrator / owner`. Scope hierarchy: channel → category →
guild. Audit log: `governance_audit_log` table.

### 1.4 Help-menu architecture

- `HelpPanelView` (`cogs/help_cog.py:248`) — PersistentView,
  paginated, governance-aware.
- `build_help_menu_view(interaction)` hook adopted by **20/20**
  cogs (uniform contract, per PR #59 sweep).
- `subsystem_registry.py` provides `display_name`, `emoji`,
  `description`, `visibility_tier`, `has_onboarding` per subsystem.
- `_attach_back_to_help_button` dynamically wires back navigation.
- One active help panel per (user, channel) via UNIQUE constraint
  on `message_anchor_manager`.

### 1.5 Existing centralized helpers (guild-resource adjacent)

| Helper | File | Adoption |
|---|---|---|
| `safe_channel_name` | `disbot/utils/channels.py:8` | 1 call site |
| `get_or_create_category` | `disbot/utils/channels.py:19` | 2 call sites |
| `create_private_channel` | `disbot/utils/channels.py:31` | 3 call sites (tournaments) |
| `cleanup_category` | `disbot/utils/channels.py:66` | 4 call sites (tournament cleanup) |
| `_find_role_normalized` | `disbot/views/roles/_helpers.py:45` | 1 call site |
| `_parse_member` | `disbot/utils/helpers.py:12` | 1 call site |
| `post_log_embed` | `disbot/utils/helpers.py:58` | 5 call sites (economy + xp listener) |
| `normalize_name` | `disbot/utils/helpers.py:77` | several |
| `get_xp_config` / `invalidate_xp_config` | `disbot/utils/guild_config_accessors.py:61,74` | cached, typed guild-config wrapper pattern |
| `views/channels/` | full subsystem (`main_panel`, `create_panel`, `delete_panel`, `restrict_panel`, `visibility_panel`) | Cohesive UI; cog is thin dispatcher |
| `views/selectors/role.py` | `RoleSelector` widget | Multiple panels |

### 1.6 Settings / config layer

- `utils/settings_keys.py` — 12 canonical key constants, each owned
  by one subsystem.
- `utils/db/settings.py:13-26` — untyped string KV
  (`get_setting`, `set_setting`).
- `utils/db/governance.py` — structured JSONB visibility/cleanup
  overrides + audit log.
- `utils/guild_config_accessors.py` — typed cache wrappers for
  hot-read configs (only XP today).
- No global config table; all settings are guild-scoped.

### 1.7 Background tasks

- `@tasks.loop` decorators: **1** (`role_cog.py:221`,
  `@tasks.loop(hours=24)` for time-based role assignment).
- `core.runtime.tasks.spawn(...)` pattern: used by economy on_ready,
  economy on_guild_join, chain on_ready, counting on_message (save).
- No janitor/GC loops for stale anchors, dead match channels, or
  expired panels (these are handled inline on relevant events).

---

## 2. Centralization gaps

This is where the audits found real fragmentation worth addressing.
Everything else the prompt raised was either already centralized
(§1) or a non-issue.

### 2.1 Guild-resource resolution — fragmented (HIGH priority)

| Primitive | Fragmented call sites | Pattern |
|---|---|---|
| Channel by ID | 9 | `guild.get_channel(int(id))` |
| Channel by name | 6 | `discord.utils.get(guild.text_channels, name=…)` |
| Category by name | 6 | `discord.utils.get(guild.categories, name=…)` |
| Role by ID | 5+ | `guild.get_role(int(id))` |
| Member by ID | 15+ | `guild.get_member(id)` (leaderboards: N+1) |

Missing-channel handling is inconsistent (silent `if ch:` vs.
inline `except` vs. fail-loud). Hardcoded channel name strings
scattered across cogs: `"economy-log"`, `"proof"`, `"bot_spam"`,
`"BJ Tournament"`, `"RPS Tournaments"`.

Leaderboards in particular have an **N+1 member-fetch problem**
that no helper currently addresses.

### 2.2 Message pipeline orchestration — fragmented (HIGH priority)

Five independent `on_message` handlers run concurrently per
message:

1. `CountingCog.on_message` (`cogs/counting_cog.py:588`)
2. `ChainCog.on_message` (`cogs/chain_cog.py:252`)
3. `CleanupCog.on_message` (`cogs/cleanup_cog.py:134`)
4. `XpCog.on_message` (`cogs/xp_cog.py:43`)
5. `RpsTournamentCog.on_message` (`cogs/rps_tournament_cog.py:543`)

Consequences:

- **No defined ordering.** `XpCog` may award XP for a message
  `CleanupCog` is about to delete; `ChainCog` may delete a message
  `CountingCog` is mid-validating.
- **Auto-mod is fragmented.** CleanupCog (commands + prohibited
  words), ChainCog (chain rules), CountingCog (counting rules) all
  delete messages but **don't go through `moderation_service`** —
  so their deletions are absent from `mod_logs`, don't accumulate
  warnings, and don't appear in moderation audit channels.
- **Cache fragmentation.** Each cog maintains its own per-guild
  in-memory cache (word patterns, chain config, count_data) with
  its own invalidation rules.
- **Observability gap.** Per-cog `on_message` latency is not
  metered; one slow handler can starve the others.

### 2.3 Setup orchestration — absent (MEDIUM priority)

- No `!setup` command, no `SetupCog`, no wizard entry point.
- No first-time-use detection (no `SETUP_COMPLETED` flag).
- `disbot/utils/onboarding_profiles.py` exists but is **imported
  by zero callers**. The `has_onboarding` flag in
  `subsystem_registry.py` is **never read**.
- `economy_cog.on_guild_join` auto-creates an `economy-log` channel
  — the only existing subsystem-bootstrap behavior — but it is not
  generalized.
- `channel_cog` and `role_cog` expose single-resource create/delete
  but no bulk blueprint primitive.
- `GovernanceTemplate` (`governance/templates.py`) handles
  visibility/cleanup batch config but **does not create Discord
  channels/roles** — its scope is governance-state only.

### 2.4 Smaller observations (LOW priority — record, don't fix yet)

- Settings KV is untyped (`get_setting → str`); callers cast
  manually. Typed wrappers exist only in
  `utils/guild_config_accessors.py` for XP. Pattern is correct but
  underused.
- `bot.dispatch()` for custom events is not used; everything routes
  through `EventBus`. This is fine — recording for awareness.
- `bot.get_cog(...)` has exactly one caller (`help_cog.py:432`).
  Cross-cog coupling via `get_cog` is effectively absent. Good.
- Metrics cover commands/cache/DB; **per-cog on_message latency
  histograms are missing**. Adding them is cheap.

---

## 3. Recommended foundational subsystems

Three new modules, each with a clear two-consumer-rule justification
and a tight scope. **No** new service registry, plugin system,
"intelligent admin", or generalized orchestration framework. Each
proposal here is the smallest thing that resolves a real
fragmentation gap from §2.

### 3.1 `guild_resources` — unified resource resolver

**Why:** Resolves §2.1. ≥30 fragmented call sites today.

**Where:** `disbot/core/runtime/guild_resources.py` (new). Platform
primitive, not a service (no audited mutation; pure read).

**API:**

```python
# Channel resolution
async def resolve_channel(guild, *, channel_id=None, name=None,
                          category=None, kind="text") -> discord.abc.GuildChannel | None
async def ensure_channel(guild, name, *, kind="text", category=None,
                          overwrites=None) -> discord.abc.GuildChannel
# Role resolution
async def resolve_role(guild, *, role_id=None, name=None) -> discord.Role | None
# Member resolution
async def resolve_member(guild, member_id) -> discord.Member | None
async def resolve_members(guild, member_ids: Iterable[int]) -> dict[int, discord.Member]
def member_display(guild, member_id) -> str  # uses cache; falls back to <@id>
# Settings-channel binding
async def resolve_settings_channel(guild, setting_key) -> discord.abc.GuildChannel | None
```

**Caching:** Light TTL-bounded dict for member-id → display_name
(invalidated on `on_member_update` / `on_guild_remove`). No channel/
role cache — `guild.get_channel/get_role` are already O(1) on the
discord.py-side cache.

**Migration:** Each consumer migrates one at a time. The fragmented
call sites are mechanical replacements. The leaderboard N+1 site
moves to `resolve_members(batch)`.

**Two-consumer-rule clearance:** Already 30+ consumers.

### 3.2 `message_pipeline` — `on_message` orchestrator

**Why:** Resolves §2.2. Five concurrent handlers with no ordering
or shared filtering.

**Where:** `disbot/core/runtime/message_pipeline.py` (new). One
`on_message` listener at the platform level that **calls registered
stages in defined order**.

**Stage contract:**

```python
class MessageStage(Protocol):
    name: str
    order: int  # smaller runs first

    async def process(self, ctx: MessagePipelineContext) -> StageResult:
        ...

@dataclass
class MessagePipelineContext:
    message: discord.Message
    guild_settings: GuildSettingsCache  # read-only, per-message
    # mutable scratch:
    metadata: dict[str, Any]

@dataclass
class StageResult:
    deleted: bool = False         # this stage deleted the message
    short_circuit: bool = False   # stop pipeline (e.g. message gone)
    moderation_action: ModerationActionDescriptor | None = None
```

**Stage order (initial):**

1. `pre_filter` — drop bot messages, no-guild, etc. (order=0)
2. `moderation` — CleanupCog command policy + prohibited words +
   ChainCog chain rules + CountingCog counting rules
   (order=10). Each rule is its own stage with `short_circuit=True`
   on delete. **Auto-mod stages emit `moderation.action_taken`**
   via `moderation_service` for unified audit.
3. `rewards` — XP award (order=20). Runs only if pipeline still
   alive (no upstream short-circuit).
4. `game_input` — RPS tournament move capture (order=30). Runs
   only for tournament match channels.

**Compatibility:** Each existing `on_message` handler is rewritten
as a `MessageStage` and registered via the same hook (one-line
change in each cog). The cogs keep ownership of their own logic;
the platform owns ordering, error isolation, and metrics.

**Observability:** Per-stage latency histogram (reuses `metrics`
module). Slow-stage threshold warning at 250ms (configurable).

**Two-consumer-rule clearance:** Five existing consumers.

### 3.3 `setup_platform` — guild onboarding & configuration wizard

**Why:** Resolves §2.3. Greenfield; no existing fragmentation to
absorb, so this one is built carefully against the rule that "we
build it when we need it."

**Trigger:** The `tournament` subsystem expansion will need bulk
channel/role provisioning. That's the second consumer. The first
consumer is `!setup` itself. Two-consumer-rule cleared once the
tournament refactor begins.

**Where:** `disbot/cogs/setup_cog.py` + `disbot/setup_platform/`
package. Reuses navigation_stack, state_store, message_anchor_manager,
persistent_views, ephemeral_surface_manager.

**Architecture:**

```
disbot/setup_platform/
├── __init__.py        # public façade
├── registry.py        # @register_setup_page decorator + SetupPageRegistry
├── pages.py           # SetupPage protocol; built-in pages
├── flows.py           # SetupFlow dataclass; flow definitions
├── blueprints.py      # ChannelBlueprint, RoleBlueprint, CategoryBlueprint
└── templates.py       # apply_template(template, guild) — Discord-resource side
```

**`SetupPage` contract:**

```python
class SetupPage(Protocol):
    page_id: str
    title: str
    required_tier: VisibilityTier  # min tier to access

    async def render(self, ctx: SetupContext) -> tuple[discord.Embed, discord.ui.View]:
        ...

    async def validate(self, ctx: SetupContext) -> list[ValidationError]:
        ...

    async def apply(self, ctx: SetupContext) -> ApplyResult:
        ...
```

Each cog can register its own setup pages (e.g.
`economy_cog.register_setup_page(EconomySetupPage())`), keeping
subsystem-specific config close to the subsystem. The
`subsystem_registry.has_onboarding` flag becomes the discovery hook.

**Blueprints (the missing Discord-resource side of templates):**

```python
@dataclass
class ChannelBlueprint:
    name: str
    kind: Literal["text", "voice"] = "text"
    category: str | None = None       # name of category blueprint
    overwrites: dict[Role | str, PermissionOverwrite] = ...
    setting_key: str | None = None    # if set, channel_id written to guild_settings

@dataclass
class RoleBlueprint:
    name: str
    color: discord.Color | None = None
    permissions: discord.Permissions | None = None
    hoist: bool = False

@dataclass
class ServerTemplate:
    name: str
    categories: list[CategoryBlueprint]
    channels: list[ChannelBlueprint]
    roles: list[RoleBlueprint]
    governance: GovernanceTemplate | None = None  # reuses governance/templates.py

async def apply_server_template(template: ServerTemplate, guild: discord.Guild,
                                 *, dry_run: bool = False) -> ApplyReport:
    ...
```

Applying a template:

1. Dry-run validation: required permissions, name collisions,
   missing parents.
2. Categories created first (depended on by channels).
3. Roles created next (depended on by overwrites).
4. Channels created with resolved category + role overwrites.
5. Governance template applied last (per-scope visibility/cleanup).
6. `setting_key` channels written to `guild_settings` so subsystems
   can find them.
7. Every step emits an `EventBus` event; full ApplyReport returned.

**State persistence:** A setup session is a `runtime_session` with
`subsystem="setup"`. Navigation_stack tracks pages; state_store
holds per-page form state. A user can `!setup` and resume across
restarts (the session is anchored in the DB; the panel message
re-binds via `message_anchor_manager.restore_anchors`).

**First-time detection:** Add one settings key
`SETUP_COMPLETED: bool`. `bot1.py:on_guild_join` posts an
ephemeral "want help setting up?" prompt in the guild's system
channel (or first writable channel) if the flag is unset and the
inviter has administrator. Inviter clicks → launches setup wizard.

**Two-consumer-rule clearance:** `!setup` + tournament-expansion's
need for bulk provisioning. Defer the whole subsystem if
tournament expansion is deferred — don't build it speculatively.

### 3.4 What is explicitly **NOT** in §3

Each of these was considered and rejected as speculative under
freeze discipline:

- **`guild_manager` god-service** — would absorb `guild_resources`,
  half of `governance`, and parts of the service layer. Existing
  separation of concerns is cleaner.
- **`event_router` / `guild_event_registry`** — EventBus already
  provides this; no missing capability.
- **`permission_manager`** — governance covers subsystem-level;
  discord.py decorators cover command-level; no real gap.
- **Plugin system / dynamic cog registry** — cogs already load via
  `_load_cogs`; no second consumer for a plugin layer.
- **Remote-admin / cross-guild ownership hierarchy** — see §7.6
  for risk analysis; high abuse-surface, no current driver.
- **Help-menu config UI / per-guild cog grouping** — visibility is
  already per-guild via governance overrides. Display grouping is
  driven by tier metadata. No second consumer demanding custom
  ordering.

---

## 4. Automated setup platform plan

This expands §3.3 into an actionable architecture.

### 4.1 Architecture diagram

```
              ┌─────────────────────────────────────────────┐
              │             !setup  /  on_guild_join         │
              └────────────────────┬─────────────────────────┘
                                   │
                          ┌────────▼─────────┐
                          │   SetupCog       │
                          │   (entry point)  │
                          └────────┬─────────┘
                                   │ creates
                          ┌────────▼─────────┐
                          │   SetupFlow      │  pages, current_page,
                          │   (dataclass)    │  per-page state
                          └────────┬─────────┘
                                   │ persists via
                ┌──────────────────┼──────────────────┐
                │                  │                  │
       ┌────────▼────────┐  ┌──────▼─────────┐ ┌──────▼─────────┐
       │ navigation_stack│  │ state_store    │ │ message_anchor │
       │ (breadcrumbs)   │  │ (form data)    │ │ (panel msg)    │
       └─────────────────┘  └────────────────┘ └────────────────┘

       SetupPageRegistry
       ┌──────────────────────────────────────────────────┐
       │  built-in pages:  Welcome, ChannelPicker,         │
       │                   RolePicker, SubsystemToggles,   │
       │                   Review, Apply                   │
       │                                                   │
       │  subsystem-registered pages (via @register_page): │
       │     EconomySetupPage, XpSetupPage, ...            │
       └──────────────────────────────────────────────────┘

       Apply phase calls:
       ┌──────────────────────────────────────────────────┐
       │  apply_server_template(template, guild)           │
       │   ├─ ensure_category(...)  via guild_resources    │
       │   ├─ create_role(...)                             │
       │   ├─ ensure_channel(...)  via guild_resources     │
       │   ├─ apply_governance_template(...)               │
       │   └─ write settings_keys                          │
       └──────────────────────────────────────────────────┘
```

### 4.2 Pages

Each page is a small, testable unit. Built-in pages:

| page_id | Purpose |
|---|---|
| `welcome` | Greeting; explains what setup will do; "Begin / Skip" buttons |
| `channels.pick` | RoleSelector-style multi-select over `_NAME_PRESETS` + custom-name modal |
| `roles.pick` | Multi-select over template-suggested roles; custom-name modal |
| `subsystems.toggles` | Per-subsystem on/off (writes via `GovernanceMutationPipeline`) |
| `logging.pick` | Pick or auto-create `economy-log`, `mod-log`, etc. |
| `review` | Read-only summary of pending changes |
| `apply` | Calls `apply_server_template`; streams progress; shows ApplyReport |
| `done` | Sets `SETUP_COMPLETED=true`; shows next-step pointers |

Subsystem-specific pages (registered by cogs that opt in via
`has_onboarding=True`):

| Cog | Page |
|---|---|
| economy | thresholds, daily reward tier, log channel |
| xp | min/max per message, cooldown, level-up channel |
| moderation | warn threshold, timeout duration, log channel |
| chain | enable per channel, word list source |
| counting | enable per channel, mode (standard / primes / fibonacci) |

### 4.3 Resumability

A setup session is just a `runtime_sessions` row with
`subsystem="setup"`. Navigation_stack carries `current_page` +
breadcrumb. State_store carries form values per page. The setup
panel message is anchored via `message_anchor_manager` (unique on
`(user, channel, "setup")`). If the bot restarts mid-setup, on
`restore_anchors()` the panel is re-bound to the existing
PersistentView; the user clicks "Continue" and is restored to the
correct page.

This is **the same mechanism `HelpPanelView` already uses** — no
new infrastructure.

### 4.4 First-time-use detection

Add one settings key in `utils/settings_keys.py`:

```python
SETUP_COMPLETED = "setup_completed"   # "1" / "" (untyped KV convention)
```

In `bot1.py:on_guild_join` (which already exists for governance
caching):

1. Resolve the inviter (audit log lookup) or fall back to the guild
   owner.
2. Find the first writable text channel (system channel preferred).
3. Post an ephemeral or pinned hint: "👋 Run `!setup` to configure
   me."
4. Subscribe to a one-shot signal: on the inviter's next message in
   any guild channel, if `SETUP_COMPLETED` is still unset and they
   have administrator, prompt them again.

Don't auto-launch the wizard — server admins find that pushy. The
hint + a discoverable command is the right default.

### 4.5 Permission gating

- `!setup` requires `administrator` permission (decorator) **and**
  `tier ≥ administrator` via governance check (defense in depth).
- Each `SetupPage` declares `required_tier`; pages above the
  current user's tier are hidden, not just disabled.
- Every `apply` action routes through existing services
  (`GovernanceMutationPipeline` for governance writes,
  `economy_service` for any test credits, etc.) — no bypass.
- The apply phase emits a single `setup.applied` event with full
  ApplyReport for audit-channel routing.

### 4.6 Built-in server templates

Three starter templates shipped in `setup_platform/templates/`:

1. `minimal.py` — just `#bot-commands` + `mod-log` + `economy-log`.
2. `community.py` — adds `general`, `announcements`, `events`,
   `Bot` category, `Gaming` category, basic role tier
   (`Member`, `Trusted`).
3. `gaming.py` — adds tournament-ready structure (private-channel
   category, RPS/Blackjack category, leaderboard channel).

Templates are plain Python files (no JSON/YAML config layer until a
second consumer demands one — §A11.6 clarity-over-abstraction). A
guild admin can also export their current state as a template
(`!setup export-template my-server.py`) for reuse across guilds.

---

## 5. Scalability & future-proofing review

This section anticipates problems that will appear as the platform
grows, **without** prematurely abstracting against them.

### 5.1 Cog count growth

Current: 20 cogs. The cog-size invariant (≤800 LOC) already pushes
splits before they become unwieldy. Adding 20 more cogs is fine —
the layering in `docs/architecture.md` handles the load.

Watch for: cogs adding their own `on_message` listener instead of
registering a `MessageStage` (§3.2). Add an INV-* test if needed.

### 5.2 Per-guild cache fragmentation

Currently every cog has its own per-guild cache (chain config,
counting state, prohibited-words regex, XP config). Cache
invalidation is mostly correct (governance triggers
`EVT_CACHE_INVALIDATED`) but not uniform.

**Don't** build a unified cache manager yet — the existing per-cog
caches are simple and locality-of-reasoning wins. **Do** require
new caches to subscribe to `EVT_CACHE_INVALIDATED` and to expose a
`forget_guild(guild_id)` hook called by `guild_lifecycle.teardown`.

### 5.3 DB query budget

`db_query_seconds` Prometheus histogram already exists. Add an
alert at p99 > 100ms for any single query as the platform grows.
Leaderboard N+1 is the only known offender; §3.1 fixes it.

### 5.4 Async loop budget

5 `on_message` handlers × N messages/sec is the current hot path.
The §3.2 pipeline serializes stages (so total work is the sum, not
parallel) — this is **a behavior change**. Concurrent handlers
today mean a slow XP handler doesn't block CleanupCog's deletion;
under the pipeline, it would.

Mitigation: stages can be marked `parallel=True` for non-conflicting
work (XP award and Counting validation don't conflict). Stage
dependencies declared via `requires=[...]` allow the pipeline to
parallelize where safe. **Don't ship this until measurement shows
serial latency is a problem** — it's complexity that may not pay.

### 5.5 EventBus catalogue growth

`events_catalogue.KNOWN_EVENTS` is enforced. As new services land,
events must be added there. This is intentional friction — keeps
the catalogue scannable.

### 5.6 Setup-page count growth

If a future cog adds 10 setup pages, the wizard becomes
unnavigable. Cap setup-page count per cog at 3 (validated at
registration time). Subsystems needing more configuration use a
sub-flow: one wizard page that "opens advanced settings" via a
modal chain or sub-panel.

### 5.7 Persistent-view registry growth

`@register` decorator adds to `_REGISTRY`. At ~10 PersistentViews
today, no scaling concern. At ~50, consider lazy registration. Not
a current problem.

---

## 6. Migration strategy

Five small phases. Each ends at a stable checkpoint (CI green,
tests passing, no behavior regression) and can be deferred without
blocking the next.

**Hard rule across all phases**: no broad rewrite. Each migration
moves consumers one at a time, gated by tests.

### Phase D — `guild_resources` extraction

**Goal:** §3.1.

**Steps:**

1. Land `core/runtime/guild_resources.py` with the API in §3.1.
   Pure functions; no behavior change. Tests cover resolution
   semantics, missing-channel fallbacks, batch member fetch.
2. Migrate fragmented sites one cog at a time:
   - leaderboard_cog → fixes the N+1 (single PR, biggest payoff)
   - economy_cog → uses `resolve_settings_channel`
   - blackjack_cog, rps_tournament — category resolution
   - role_cog → `resolve_role`
3. Each migration PR touches one cog; CI green; merge; next.
4. Add INV-* test: "no `guild.get_channel`/`get_role` outside
   `guild_resources`" once migration is complete.

**Risk:** Very low. Mechanical replacement. Pure read primitives.

**Estimated PRs:** 4-6.

### Phase E — `message_pipeline` orchestration

**Goal:** §3.2.

**Steps:**

1. Land `core/runtime/message_pipeline.py` with the stage protocol
   + initial `pre_filter` stage. The platform `on_message` listener
   calls registered stages in order; no cog has migrated yet.
2. Migrate cogs one at a time:
   - `CleanupCog` first (smallest, governance-routed)
   - `CountingCog` next (well-isolated)
   - `ChainCog`, `XpCog`, `RpsTournamentCog`
3. Add `moderation.action_taken` emission to auto-mod stages so
   CleanupCog/ChainCog/CountingCog deletions reach `mod_logs`.
4. Add per-stage latency histograms.
5. Add INV-* test: "no `on_message` listeners outside the pipeline".

**Risk:** Medium. Behavior changes:
- Stages run serially by default (latency change — measurable).
- Auto-mod actions now appear in `mod_logs` (intentional; may
  surface to moderation audit channel which is good).
- Error in one stage no longer crashes that handler in isolation —
  the pipeline catches and continues with metric emission.

Each cog migration ships independently so regression scope is
small.

**Estimated PRs:** 6-8.

### Phase F — `setup_platform` foundation

**Goal:** §3.3 + §4 (excluding subsystem-specific pages).

**Steps:**

1. Land `setup_platform/` package with `SetupPage` protocol,
   `SetupFlow`, registry, blueprints.
2. Land `setup_platform/templates/` with the three starter
   templates.
3. Land `SetupCog` with `!setup` command, gated by administrator.
4. Built-in pages: welcome, channels.pick, roles.pick,
   subsystems.toggles, logging.pick, review, apply, done.
5. `bot1.py:on_guild_join` posts the first-time hint.
6. `SETUP_COMPLETED` settings key added.
7. Integration test: end-to-end setup on a mock guild with the
   `minimal` template.

**Risk:** Medium-high. New cog. Touches `on_guild_join` (already
tested under governance). Apply phase calls Discord resource
creation APIs — needs careful permission handling.

**Estimated PRs:** 3-5.

### Phase G — subsystem setup pages

**Goal:** Per-cog onboarding pages registered against
`setup_platform`.

**Steps:** Each cog that wants to opt in registers its setup
page(s). Economy first (it already has on_guild_join behavior to
move into the wizard). XP second. Moderation third. Others
opportunistically.

**Risk:** Low per-cog. Each integration is local.

**Estimated PRs:** 1 per opt-in cog.

### Phase H — channel/role blueprint templates

**Goal:** Bulk template application during tournament expansion
becomes the second consumer for `setup_platform.blueprints`.

**Steps:** Define `tournament.py` template; apply on tournament
launch; reuse blueprint primitives.

**Defer until:** Tournament refactor actually begins.

### Stabilization checkpoints

After Phase D, Phase E (mid), Phase E (full), and Phase F: full CI
sweep, identity-contract STRICT, governance healthcheck. No phase
proceeds until prior checkpoint is green.

---

## 7. Risk analysis

### 7.1 Scalability risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Pipeline serial latency under load | Medium | Medium | Add `parallel=True` opt-in when measured; don't pre-optimize |
| Setup-page registry sprawl | Low | Low | Cap pages-per-cog at 3 (§5.6) |
| Per-guild cache memory bloat at 100+ guilds | Medium | Medium | Existing `guild_lifecycle.teardown` handles GC; add cache-size metric |
| Leaderboard N+1 already biting | High | Low | §3.1 directly fixes |

### 7.2 Permission risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Setup wizard run by non-admin | Low | High | Defense in depth: decorator + governance tier check (§4.5) |
| Apply-template grants role to wrong user | Low | High | Dry-run validation; require explicit confirmation page before apply |
| Bot lacks permissions mid-apply | Medium | Medium | Pre-flight `bot.permissions_for(channel)` check; partial-rollback on failure |

### 7.3 Event-loop / handler risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| One slow pipeline stage blocks others | Medium | Medium | Per-stage timeout (200ms warn / 500ms hard); slow-path metric |
| Auto-mod over-deletion under stage misorder | Low | High | Stage `order` is integer-validated; test coverage on canonical message scenarios |
| `on_message` handler outside pipeline (regression) | Medium | Medium | INV-* test forbids registration (§6 Phase E step 5) |

### 7.4 Cache consistency risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `guild_resources` member cache stale after rename | Medium | Low | TTL bound + `on_member_update` invalidator |
| Governance cache + per-cog cache divergence | Low | Medium | Already mitigated by `EVT_CACHE_INVALIDATED` |

### 7.5 Interaction-state risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Setup wizard state lost on restart | Low | Medium | Anchored via `message_anchor_manager`; same proven recovery path as `HelpPanelView` |
| User opens two `!setup` panels | Low | Low | UNIQUE constraint on `(user, channel, "setup")` anchor |
| Stage emits event for already-deleted message | Medium | Low | Pipeline marks `deleted=True`; downstream stages check `ctx.metadata["deleted"]` |

### 7.6 Remote-admin / abuse-surface risks

The original prompt suggested platform-level remote admin
(operator overrides, delegated managers, owner-of-record). **This
plan explicitly defers it.**

Why:

- No current driver — no real consumer asking for it.
- High abuse surface — a bot that lets non-guild-owners override
  guild config is a phishing risk.
- Coupling to identity contract — `IDENTITY_CONTRACT_STRICT`
  already validates the platform owner; adding a delegation tier
  invalidates that proof.
- Trust model unclear — Discord's permission model is the source of
  truth for guild administration; cross-guild operator override
  bypasses it.

If/when it becomes necessary, the design must include: per-action
audit, mandatory `unanimous-quorum` for high-blast-radius writes,
and an opt-in flag the guild owner controls (default off). Open as
an ADR before any implementation.

### 7.7 Future coupling risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `setup_platform` becomes "god module" | Medium | High | Hard cap: only blueprints + page registry + flow orchestration. Subsystem-specific config stays in the subsystem. |
| `guild_resources` accumulates business logic | Low | Medium | Pure-read invariant; mutations always go through services |
| `message_pipeline` reimplements EventBus | Low | Medium | Stages do not emit events; they return `StageResult`. Events come from services called by stages |

---

## 8. What this plan deliberately doesn't do

For symmetry with §3.4 — explicit non-goals:

- Does not propose a new service registry, plugin system, dynamic
  cog loader, or DI framework.
- Does not propose cross-guild orchestration, multi-tenant
  ownership, or remote-admin tooling.
- Does not propose generalized "platform metadata systems",
  "subsystem manifest schemas", or YAML-driven configuration.
- Does not propose unified caching, ORM-style query builders, or
  generic CRUD scaffolding.
- Does not propose new UI frameworks; reuses BaseView /
  PersistentView / navigation_stack everywhere.
- Does not propose a help-menu redesign; the existing
  `HelpPanelView` is production-grade.

If a future phase needs any of these, **open an ADR first** under
`docs/decisions/` so the trade-off is recorded.

---

## 9. Recommended next steps

In order:

1. **Land this document** as a planning reference (this PR).
2. **Phase D (guild_resources extraction)** — lowest risk, highest
   immediate payoff (leaderboard N+1 alone justifies it). Start
   once PR #60 is merged.
3. **Phase E (message_pipeline orchestration)** — moderate risk,
   high systemic value. Critical before tournament expansion adds
   a sixth `on_message` handler.
4. **Phase F (setup_platform foundation)** — moderate risk, opens
   the door to bulk provisioning for tournaments.
5. **Tournament expansion** can proceed in parallel with Phase E
   migration if the tournament cog registers a pipeline stage
   from day one (skipping the migration debt entirely).

Each phase is independently mergeable. Each can be deferred. None
require a flag day or coordinated rollout.

---

## 10. Open questions for design review

These should be answered before Phase D begins:

1. **`guild_resources` location** — `core/runtime/` or new
   `core/guild/`? Recommendation: `core/runtime/` for symmetry
   with other read primitives.
2. **`message_pipeline` registration timing** — register stages at
   `cog_load` or at `on_ready`? Discord.py ordering guarantees
   suggest `cog_load`; verify against the identity-contract test.
3. **Setup-template format** — Python files (this plan's default)
   or JSON/YAML? Python is more flexible and avoids a config
   layer; JSON makes templates user-portable. Trade-off should be
   discussed before §4.6 ships.
4. **First-time hint channel selection** — `guild.system_channel`
   or first writable channel? Discord deprecation timelines may
   affect this; check current best practice before §4.4.
5. **Auto-mod warning accumulation** — when CleanupCog/ChainCog/
   CountingCog deletions go through `moderation_service`, do they
   issue a warning automatically, or just an audit entry? Current
   plan: audit only; warning issuance requires explicit
   `moderation_service.warn(...)` call. Open for review.

---

## Appendix A — Cross-references

- `docs/architecture.md` — binding layering rules
- `docs/runtime_contracts.md` — subsystem identity contract,
  failure modes
- `docs/ownership.md` — service ownership boundaries
- `docs/decisions/001-no-redis-backed-state.md` — state lives in
  Postgres
- `docs/decisions/002-game-state-not-restart-safe.md` — game state
  is intentionally ephemeral
- PR #59 — final stabilization sweep
- PR #60 — final lifecycle residuals (this branch)

## Appendix B — Audit citations

The three forensic audits this plan synthesizes:

- **Guild resources & service inventory** — covered §2.1, §1.5,
  §1.2
- **Event pipeline & moderation** — covered §2.2, §1.7, §5.4
- **Setup / help-menu / config / UI** — covered §2.3, §1.3, §1.4,
  §1.6

Full per-area citations to file:line are inline in §1 and §2.
