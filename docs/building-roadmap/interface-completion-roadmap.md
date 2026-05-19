# SuperBot Interface Completion Roadmap

Status: Open roadmap — Phases 1, 3, 4, 5, 6, 6.5a, 7 (Option A) landed; Phase 8 audit-complete
Runtime impact: None for this doc

This document captures the next major arc of SuperBot work: pulling the existing scattered cog surface into a coherent, discoverable, Discord-native application. The platform foundation (settings/customization map, registry, pipelines, `!platform` hub, Settings Manager shell, Logging subsystem) was complete before this roadmap started; the interface skeleton is now also landed (see status snapshot below).

Each phase is sized to one PR. Phases must be reviewed and smoke-tested before later phases are committed to — do not lock in downstream work before the upstream phase has merged.

Related reference:

- `command-integration-standard.md` — non-negotiable rules every phase must obey
- `command-expansion-backlog.md` — near-term command and panel ideas
- `hub-ui-standard.md` — UX standard (hub presets, component thresholds, candidate future mother hubs) — the standard new hubs must align with
- `../settings-customization-command-map.md`
- `../platform-consistency-ledger.md`

---

## Status snapshot

This is the current actual state of the roadmap, reconciled against `main`. Per-phase technical detail remains below for historical reference and for future amendments.

### Landed

| Phase | PR | What landed |
|---|---|---|
| 1 — `parent_hub` / `hub_group` schema | #118 | Two optional fields on `SUBSYSTEMS`, validator rules, `REGISTRY_SCHEMA_VERSION` 1 → 2. |
| 3 — Games hub | #119 | `games` subsystem, `!games`, `GamesHubView` (router-only), `parent_hub` set on Blackjack/RPS/Deathmatch/Mining/Counting/Chain. |
| 4 — Help filter | #120 | `parent_hub` children hidden from the top-level Help menu while staying typed-accessible and reachable via their hub. |
| 5 — Cleanup panel | #121 | `!cleanup` hub with `_WordMenuView` / `LoggingPanelView` / `SubsystemSettingsView` routing. |
| 6 — Access policy explorer | #122 | `!settings access` read-only diagnostic via `governance.resolve_subsystem_state`; airtight tier filtering. |
| 6.5a — Platform flag manager | #123 | `!platform flag` per-guild flag enable/disable through `RolloutMutationPipeline.set_flag_state` (audit + cache invalidation + event emission). |
| 7 — Game panels *(Option A)* | #124 | `BlackjackPanelView` + `RPSPanelView` router-only. No engine touches. |
| Hub UI standard | #125 | `docs/building-roadmap/hub-ui-standard.md` — five hub presets, component thresholds, future visibility metadata sketch, audit table. |
| 9a — Logging schema + resolver | #128 | Five new severity/audit channel bindings + RECOMMENDED resource requirements. `LOGGING_CONFIG_SCHEMA.version` 1 → 2. Table-driven 7-route `resolve_log_channel` with mod fallback. |
| 9b — Logging Routes UI | #129 | `LoggingRoutesView` subpage + 🗺️ Routes button on `LoggingPanelView` + `!logging routes` subcommand + parameterised `LogChannelSelectView` / `LogChannelProvisionView` for all 7 kinds. |
| 3.5 *(partial)* — Shared nav helper | *(this refresh)* | `disbot/views/navigation.py` — `attach_back_button` + `transition_to`. Migrated help-cog back-button injection and `LoggingRoutesView.btn_back`. Admin / settings / games inline factories remain as-is and migrate on demand. |

### Audit-complete (no implementation needed)

| Phase | Audit finding |
|---|---|
| 8 — Role, Economy, Proof, Inventory/Leaderboard, Channel panels | Every cog already exposes a fully integrated hub view via `build_help_menu_view`: `RoleHubPanelView`, `EconomyPanelView`, `_PrizeManagerView`, `UnifiedInventoryView` + `LeaderboardView`, `_ChannelManagerView`. No implementation PRs. Future Phase-8-adjacent work is **UX standardization and hub regrouping per `hub-ui-standard.md`**, not panel re-creation. |

### Deferred / partial

| Phase | Status |
|---|---|
| 2 / 3.5 — Shared navigation helpers | Partial: ``views/navigation.py`` lands as a thin two-function module (`attach_back_button` + `transition_to`). Phase 3.5 migrated the two safest call sites (help cog's back-button injection and `LoggingRoutesView.btn_back`); admin / settings / games inline factories remain as-is and migrate one PR at a time on demand. |
| 7b — Practice / Replay | Deferred. Requires a product + game-engine decision (bet=0 vs separate no-economy path, Practice's effect on stats/leaderboards/tournaments, `BlackjackView`'s post-game callback shape, double-charge prevention on Replay). Phase 7 Option A intentionally shipped without these. |
| 9c — Logging publishers + subscribers | Deferred. Schema + UI landed via 9a/9b; publisher callsites for `audit.action_recorded`, `runtime.error_raised`, `runtime.warning_emitted` need a strategy decision (see Phase 9 section for proposed approach). |
| Cleanup Settings Foundation | Deferred until cleanup has real scalar settings the runtime consumes (channel-specific cleanup policy storage, etc.). Today's audit found zero DB-persisted cleanup scalars, so an empty `SubsystemSchema` would be noise. |
| Platform Management Actions *(broader)* | Partially started by Phase 6.5a (`!platform flag` enables/disables flags). Binding edits, provisioning edits, cache-invalidation controls, migration-retry controls remain future work — each one needs its own canonical pipeline to route through. |

### Still ahead (in priority order)

| Phase | Notes |
|---|---|
| 9c — Logging publishers + subscribers | Next major implementation candidate. Adds publish callsites + bus subscribers + per-route counter buckets. Needs the publisher-strategy decision documented in the Phase 9 section. |
| 10 — Slash front doors | Thin `/help`, `/games`, `/cleanup`, `/platform`, `/settings` hybrid-command wrappers. Small but lower-impact than Phase 9c. |
| 11 — Setup wizard | Deferred until the prerequisites (cleanup panel ✅, access explorer ✅, `SetupPackCatalogue` prototype ⏳) stabilize. |

---

## Hard architectural boundaries (re-stated for every phase)

| Concern | Single owner | Rule |
|---|---|---|
| Scalar setting writes | `SettingsMutationPipeline` | No direct DB writes |
| Channel/role/resource pointers | `BindingMutationPipeline` | No channel IDs as scalar settings |
| Discord resource creation | `ResourceProvisioningPipeline` | Preview → confirm; never silent |
| Access/visibility policy | `services/governance_service.py` | No second allowlist |
| Cleanup policies / lists | cleanup service + cleanup storage | Not scalar settings |
| Help / menu / router | one auto-iteration over `SUBSYSTEMS` | No parallel router |
| Interactive views | every view exposes back-nav | No dead-end views |

Any PR that appears to bypass one of these owners should be rejected, regardless of how convenient the shortcut looks.

---

## Ground-truth notes

These are the load-bearing facts the roadmap is built on. They are stated up front so that each phase below can be short.

1. **Logging is fully landed.** `LoggingCog`, `LoggingPanelView`, `LogChannelSelectView`, `LogChannelProvisionView`, the binding-first `resolve_log_channel`, and Admin/Help wiring are all in place. Advanced severity/source routing is deferred to Phase 9 — not first.
2. **All seven game-relevant cogs already expose `build_help_menu_view`.** Blackjack, RPS (+ Tournament), Deathmatch, Mining, Counting, Chain. The Games hub reuses them — **no cog rewrites**.
3. **Help menu auto-iterates `SUBSYSTEMS`** via `all_subsystems_sorted()`. Hiding game cogs from the top-level menu after the hub ships is a one-line filter — own PR (Phase 4), not bundled.
4. **`@panel_command` decorator exists** but has zero production callers. New panels register via `KNOWN_PANEL_COMMANDS` for now; decorator migration is a separate future PR.
5. **Three near-identical back-button factories** exist (Help, Admin, Settings). The Games hub will need a fourth. Whether to extract a shared helper before or after the Games hub depends on whether the extraction is import-safe (Phase 2 gate).
6. **Mining is `category="economy"`**, Counting and Chain are `category="games"` but message-pipeline activities. The hub treats all six as members via `parent_hub`, with `hub_group` for visual subgrouping (Competitive vs Activities). Category and routing intentionally disagree for Mining; this is a feature.
7. **No `CleanupPolicy` storage today.** Cleanup configuration today is scalar (prohibited words list, warning behavior). Channel-specific cleanup policy is a future storage change — Phase 5 stays read-mostly until that storage exists.
8. **No central panel registry yet.** `CustomizationCatalogue` infers panels from four sources. We don't add a new primitive here; we use the existing curated list.

---

## Phase 1 — `parent_hub` and `hub_group` metadata in `SUBSYSTEMS` *(✅ landed via #118)*

**Goal.** Add two optional fields to the SUBSYSTEMS schema and validate them. No Help filtering. No Games hub. No new cogs. No behavior change.

### Approach

Extend `disbot/utils/subsystem_registry.py`:

- Add optional fields `parent_hub: str | None = None` and `hub_group: str | None = None` to every entry's default shape.
- Extend `validate_registry()`:
  - `parent_hub` (if set) must reference an existing subsystem key.
  - `parent_hub` (if set) must not itself have `parent_hub` set (no two-hop hubs).
  - The referenced subsystem must have `entry_points` (routable).
  - `hub_group` (if set) must be a non-empty string ≤ 32 chars (free-form for now).
- Bump `REGISTRY_SCHEMA_VERSION` 1 → 2.
- **No existing entries change.** No subsystem yet has `parent_hub` set; this phase only adds the *capability*.

### Risk: low
Pure schema addition. Backwards-compatible. Validation runs at startup and is deterministic.

### Tests
- Valid: subsystem with `parent_hub="games"` referencing a registered hub passes.
- Invalid: `parent_hub` pointing to non-existent subsystem fails at startup.
- Invalid: two-hop `parent_hub` chain fails.
- `REGISTRY_SCHEMA_VERSION` bump asserted.
- Deep-freeze still applies to the new fields.

### Rollback
Revert the field-default additions, validator rules, and schema version bump together unless a later merged PR already depends on version 2.

### Non-goals
- No Games hub (Phase 3).
- No Help filter (Phase 4).
- No `parent_hub` assignment on existing entries (Phase 3).
- No decorator migration.

---

## Phase 2 — Shared navigation helpers *(deferred to 3.5; not yet landed)*

**Goal.** Extract the three (about-to-be-four) `attach_back_to_*` factories into one helper module, **only if** it can be done as a small import-safe PR. Deferred during the interface arc — Phase 3 landed first so the fourth call site exists, but the extraction itself was not opened. Pick this up when convenient; it is genuinely small.

### Decision gate (run before opening the PR)

1. Can `disbot/views/navigation_helpers.py` be created with **only** stdlib + `discord` imports at module load time?
2. Can view reconstruction be passed in as a callable parameter, so the helper never imports the cog?
3. Does the helper avoid pulling in `core.runtime.*` at import time?

If **yes** to all three: ship Phase 2 now. If **no** to any: defer to **Phase 3.5** (after the hub lands and the helper has a real fourth call site).

### Approach (if shipping)

New module `disbot/views/navigation_helpers.py`:

```python
def attach_back_button(
    view: discord.ui.View,
    *,
    parent: Literal["help", "admin", "settings"],
    view_factory: Callable[[], discord.ui.View],
    label: str | None = None,
    emoji: str | None = None,
) -> bool:
    """Add a Back button. Returns False (no-op) at the 25-child limit."""

def build_no_panel_embed(cog: commands.Cog) -> discord.Embed:
    """Fallback embed listing typed commands for a cog without build_help_menu_view."""
```

Each existing factory becomes a one-line shim into the helper. Shims stay for one PR cycle; a follow-up PR removes them.

### Risk: low (if decision gate passes; abort and defer otherwise)

### Non-goals
- Adding the Games button to the helper (happens in Phase 3 once `GamesHubView` exists).
- Inheritance-based panel base class. Helpers, not inheritance.

---

## Phase 3 — `games` Subsystem + `!games` Command + `GamesHubView` *(✅ landed via #119)*

**Goal.** Add the Games hub as a router/hub only. The hub presents Blackjack, RPS (+ Tournament), Deathmatch, Mining, Counting, Chain as members, visually subgrouped Competitive vs Activities. **Game logic stays exactly where it is today.** Individual game cogs remain typed-accessible and Help-discoverable — Phase 4 handles Help filtering.

### Approach

#### 3a — Add `games` entry to SUBSYSTEMS

```python
"games": {
    "display_name": "Games",
    "description": "Competitive games and channel activities",
    "emoji": "🎮",
    "color": GAME_COLOR.value,
    "visibility_tier": "user",
    "visibility_mode": "normal",
    "category": "games",
    "tags": ["games", "hub", "activities"],
    "entry_points": ["games"],
    "default_channels": ["games", "bot-commands"],
    "related_subsystems": ["blackjack", "rps_tournament", "deathmatch", "mining", "counting", "chain"],
    "dependencies": [],
    "soft_dependencies": [],
    "supports_dm": False,
    "has_cleanup_rules": False,
    "ui_priority": 25,
    "capabilities": ["games.hub.view"],
}
```

Then set `parent_hub` / `hub_group` on existing entries:

- `blackjack`, `rps_tournament`, `deathmatch`: `parent_hub="games"`, `hub_group="competitive"`
- `mining`, `counting`, `chain`: `parent_hub="games"`, `hub_group="activities"` (Mining keeps `category="economy"`)

These edits are metadata-only; they have no behavioral effect until the hub view ships (this phase) and Phase 4 hides the children from Help.

#### 3b — New `GamesHubCog`

`disbot/cogs/games_cog.py` — thin cog exposing:

- `!games` command → opens `GamesHubView`.
- `build_help_menu_view(interaction)` → returns the same embed/view.

**Strict non-goal:** this cog contains no game logic. It is a router.

#### 3c — `GamesHubView`

`disbot/views/games/hub.py`:

- One embed with two field sections labeled **Competitive** and **Activities**.
- Discovers children dynamically: iterates `SUBSYSTEMS` for entries with `parent_hub == "games"`, groups by `hub_group`.
- One `discord.ui.Select` (or two if approaching the 25-option limit).
- On select: looks up the child cog via the existing `_cog_for_subsystem()` helper and invokes `cog.build_help_menu_view(interaction)`.
- Fallback: if the child cog lacks `build_help_menu_view`, render a typed-command embed listing `entry_points`.
- "Back to Help" via the Phase 2 helper if available; otherwise an inline factory (migrated in 3.5).

#### 3d — Register the panel command

Add to `KNOWN_PANEL_COMMANDS`:

```python
("games", "games"),
```

Do not use `@panel_command` for this PR — the decorator has zero production usage.

#### 3e — Load the cog

Add `"cogs.games_cog"` to `INITIAL_EXTENSIONS` in `disbot/config.py`.

### Risk: medium
- Child ordering must be deterministic (sort by `ui_priority` then key).
- Fallback rendering must be safe (no crash, embed within Discord field limits).
- Phase 4 hides the children from Help; this phase intentionally does not.

### Tests
- Hub lists exactly the six expected children in expected groups.
- Children sort deterministically.
- Selecting any child invokes its `build_help_menu_view`.
- Fallback path renders cleanly.
- `!platform identity` passes.
- `!platform customization` reports the new `("games", "games")` panel.

### Manual Discord smoke
- `!games` opens the hub.
- Competitive: Blackjack, RPS, Deathmatch. Activities: Mining, Counting, Chain.
- Selecting any child opens its existing help view.
- Back to Help returns home.
- `!blackjack`, `!mine`, `!countingmenu`, `!chainmenu`, `!dm`, `!rps` still work.
- `!help` still shows the children individually (Phase 4 hides them; not yet).

### Rollback
Remove the new cog and view module, the SUBSYSTEMS `games` entry, the six `parent_hub` field assignments, and the `KNOWN_PANEL_COMMANDS` line. Phase 1 schema fields stay — they just go back to being unused.

### Non-goals
- No game logic in `games_cog.py`. Not one line.
- No Help filter.
- No new game modes (Phase 7).
- No active-games / tournament listings inside the hub.
- No splitting RPS and RPS Tournament — one cog, one entry.
- No `@panel_command` decoration.

---

## Phase 3.5 — Deferred navigation helper extraction *(if Phase 2 was deferred)*

Only if Phase 2's decision gate aborted. Same approach as Phase 2, now with four call sites (Help, Admin, Settings, Games), so the extraction is verifiably non-cyclical because the Games hub already imports cleanly.

---

## Phase 4 — Help menu filter for `parent_hub` children *(✅ landed via #120)*

**Goal.** Hide subsystems with a `parent_hub` set from the top-level `!help` menu. They remain typed-accessible and reachable through their hub.

### Approach

Modify `disbot/cogs/help_cog.py`:

- `build_overview_embed`: add `if meta.get("parent_hub"): continue` inside the iteration over `subsystems_by_name`.
- `HelpPanelView`'s select builder: same filter.
- `HelpPanelView._on_select`: when a hub is selected (e.g. `games`), route to its `build_help_menu_view` exactly as for any other subsystem.

### Risk: low-medium
- Easy to over-filter (hides non-game subsystems) or under-filter (children still shown). Review-light, smoke-test-heavy.

### Tests
- Overview embed excludes Blackjack/RPS/Deathmatch/Mining/Counting/Chain.
- Overview embed includes Games.
- Select options exclude `parent_hub` children, include `games`.
- Selecting Games routes to `GamesHubView`.

### Manual smoke
- `!help` shows Games but not the individual game cogs.
- `!help` → Games opens the hub.
- Typed shortcuts still work.

### Non-goals
- No removal of typed command access. `!blackjack` etc. still work.
- No governance changes.
- No changes to `!platform customization` reporting.

---

## Phase 5 — Cleanup panel shell with `wordmenu` as subpage *(✅ landed via #121)*

**Goal.** Replace the standalone `!wordmenu` UX with a full `!cleanup` panel whose first iteration is mostly read-only and routes existing functionality. No channel-specific cleanup policy writes — that requires storage that does not yet exist.

**Cleanup Settings Foundation deferral:** The schema audit (Step 5c) found zero DB-persisted cleanup scalars today. No empty `SubsystemSchema` was registered to avoid noise. When channel-specific cleanup policy storage lands (the open question below), that PR can declare the schema and lift the existing knobs in the same change.

### Approach

#### 5a — Read-only panel shell

`CleanupPanelView`:

- **Overview** field: enabled/disabled, prohibited word count, warning behavior, exempted channels (read-only summary).
- **Prohibited Words** → opens existing `wordmenu` as an in-place subpage.
- **Logging Status** → opens `LoggingPanelView` (do not duplicate).
- **Settings** → opens `SubsystemSettingsView("cleanup")`.
- **Back to Settings / Back to Help** via the navigation helper.

#### 5b — `wordmenu` becomes a subpage

`!wordmenu` remains a typed entrypoint and a `KNOWN_PANEL_COMMANDS` entry. Opened from the Cleanup panel, it renders inside the same message.

#### 5c — Schema audit

Add `SubsystemSchema` to `disbot/cogs/cleanup/` declaring whichever scalar settings already exist (warning threshold, enabled, etc.). **No new settings.** Just lift existing knobs into the schema so the Settings page renders them.

### Risk: medium
- The cleanup service touches moderation flow; the panel must stay read-only/routing-only until channel-policy storage exists.
- `!wordmenu` users have memorized the command — preserve the typed command.

### Non-goals
- No channel-specific cleanup policy writes.
- No test-rule-against-message feature.
- No exemption editor — read-only display only.

---

## Phase 6 — Access policy read-only explorer *(✅ landed via #122)*

**Goal.** Surface effective governance/access policy as a read-only explorer through `!settings access`. The write surface is a future PR.

**Implementation note:** the audit-time "explain_access" helper from the roadmap was found to already exist as `governance.resolve_subsystem_state(ctx, name)`, which returns a `SubsystemEffectiveState` with the full `ResolutionTrace`. No new helper was added; the explorer is a UI on top of the existing resolver. The `commands.group` conversion of `!settings` (required to add `!settings access`) was the only collateral change.

### Approach

#### 6a — Explorer view

`AccessExplorerView`:

- Select subsystem (from `SUBSYSTEMS`, governance-filtered).
- Select scope: guild / category / channel.
- Embed: effective tier requirement, visibility mode, `parent_hub` if any, guild overrides.
- **Explain Why Blocked** → invokes `governance_service.explain_access(member, subsystem, channel)` and shows the decision chain.

#### 6b — Audit governance read API

If `explain_access` (or equivalent) doesn't exist, add it as a pure read function returning a structured `AccessDecision`. No mutation; no caching beyond what governance already does.

### Risk: medium-high
Governance is security-sensitive. Misreporting policy is worse than no UI. Tier filtering must be airtight.

### Tests
- Explorer reports the policy a member would actually experience.
- "Explain Why Blocked" produces a deterministic chain.
- Tier filtering blocks members from viewing higher-tier policies.

### Non-goals
- Writes.
- A new allowlist parallel to governance.
- Cross-guild policy templates.

---

## Phase 6.5a — Platform flag manager *(✅ landed via #123)*

**Goal.** Make `!platform flags` editable by adding `!platform flag` (singular) — an admin-only per-guild feature-flag editor that mutates state through the existing `services.rollout_mutation.RolloutMutationPipeline.set_flag_state`. The plural read-only command is unchanged.

### Why this is a Phase 6.5 not a Phase 6

The roadmap originally moved straight from the read-only access explorer (Phase 6) to per-game panels (Phase 7). Phase 6.5a was inserted mid-arc once `RolloutMutationPipeline` was identified as a canonical write path with no UI counterpart — the Discord-side flag editor had been deferred at pipeline-creation time. Adding the UI now (a) closes that loop, (b) gives operators a way to flip flags without env vars or DB writes, and (c) proves the "Platform Manager Panel" preset from `hub-ui-standard.md`.

### Implementation

- `disbot/views/diagnostic/flag_manager.py` — `FlagManagerView` (flag select + Enable/Disable/Refresh/Back buttons + detail embed showing default/effective/source/owner/guild-override marker).
- `disbot/cogs/diagnostic_cog.py` — `!platform flag` subcommand added alongside the existing `!platform flags`.

### Hard contracts (pinned by tests)

- The view module imports nothing from `utils.db` at module load.
- The view never calls `upsert_global_with_audit`, `upsert_guild_with_audit`, `delete_guild_override`, or `delete_global_override` — every mutation routes through `RolloutMutationPipeline`.
- No Reset button: `RolloutMutationPipeline` does not expose a guild-override delete path, and the panel must not invent a direct DB delete. A future "Reset to default" button waits for the pipeline to grow that capability with audit + cache invalidation built in.

### Non-goals (kept for later)

- Global-scope mutation.
- Rollout-percent slider.
- Environment-tier editing.
- Slash command.

These belong to a future **Phase 6.5b** if and when broader Platform Management Actions are scheduled — see *Platform Management Actions (broader)* in the Status snapshot above for the full not-yet list (binding edits, provisioning edits, cache-invalidation buttons, migration retries).

---

## Phase 7 — Blackjack and RPS mode/replay panels *(Option A ✅ landed via #124; Option B / 7b deferred)*

**Goal.** Per-game mode/replay panels for the two highest-priority Competitive games, layered on the now-existing Games hub.

### What landed (Option A, router-only)

`BlackjackPanelView` and `RPSPanelView` ship as router-only views:

- Blackjack panel: Classic / Rules / Overview buttons. Each swaps the embed in place to surface the typed command for that mode.
- RPS panel: Single Round / Tournament / Rules / Overview buttons. Same pattern.

Both panels carry **no built-in back-nav** — the wrapping context (Games hub's `attach_back_to_games_button` or `help_cog`'s `_attach_back_to_help_button`) adds it, matching the convention used by Counting/Mining/Games hubs.

Cog changes are minimal: `BlackjackCog.build_help_menu_view` and `RPSTournamentCog.build_help_menu_view` now return the panel instead of `(embed, empty View)`. Dead `stats_block` / `GAME_COLOR` imports removed.

### Phase 7b deferred — Practice / Replay / Best-of

Practice mode and Replay introduce **new game-engine behaviors** that require product + engine decisions. They are explicitly *not* in Phase 7 Option A and will land as Phase 7b when the design is settled.

Open questions for Phase 7b:

- **Practice mode semantics.** `bet=0` reusing the existing path, or a separate no-economy code path? Does Practice affect stats / leaderboards / tournament eligibility?
- **Replay implementation.** Does `BlackjackView` need a post-game callback hook? How is double-charging prevented if the user clicks Replay while a charge is in flight?
- **Best-of variants in RPS.** Best-of-3 already exists for tournaments; does single-round mode want a Best-of-3 toggle? If yes, where does the state live?

Until those answers exist, the panels stay router-only. Tests pin the absence of Practice / Replay / Best-of / Change-Mode buttons so a future re-introduction is a deliberate code change, not a drift.

### Original full-spec (kept for reference; relevant to Phase 7b)

### Blackjack panel

`BlackjackPanelView`:

- **Classic** → existing `!bj`.
- **Practice** → vs bot, no economy effect.
- **Rules** → embed.
- **Replay** → post-game, re-opens the panel for explicit re-confirmation (never silent re-charge).
- **Change Mode** → re-open panel.
- **Back to Games / Back to Help**.

`!blackjack` stays as the shortcut. `!bjmenu` (or `!blackjack menu`) opens the panel. The panel is also reachable via the Games hub.

### RPS panel

`RPSPanelView`:

- **Single Round** → existing `!rps`.
- **Best of 3** → preset mode.
- **Rules** → embed.
- **Tournament** → routes to existing `!rpsregister` (does not duplicate tournament state).
- **Replay** → post-match, re-opens panel.

Tournament logic stays in `rps_tournament_cog.py`. The panel is a router.

### Risk: medium
Practice mode must not credit/debit economy. Replay must not double-charge bets.

### Non-goals
- High-stakes / economy-gated modes.
- Best of 5 / challenge-user in RPS.
- New game variants (split / insurance for Blackjack).

---

## Phase 8 — Role, Economy, Proof, Inventory/Leaderboard, Channel panels *(✅ audit-complete; no implementation PRs)*

The roadmap originally listed five sub-phases for cog-by-cog panel implementation. A source-level audit during the interface arc found that **every one of these panels already exists**:

| Sub-phase | Existing implementation | Closest hub preset |
|---|---|---|
| 8a — Role | `RoleHubPanelView` in `disbot/cogs/role_cog.py` (Create / Manage / Time Roles / XP Roles / Reaction Roles / Diagnostics) | Operator Hub |
| 8b — Economy | `EconomyPanelView` returned from `economy_cog.build_help_menu_view` | Operator Hub |
| 8c — Proof | `_PrizeManagerView` in `proof_channel_cog.py` | Operator Hub |
| 8d — Inventory + Leaderboard | `UnifiedInventoryView` + `LeaderboardView` | Feature Action Panel / User Navigation Hub |
| 8e — Channel management | `_ChannelManagerView` in `channel_cog.py` | Operator Hub |

Every one of these cogs integrates with the Help menu via `build_help_menu_view`. No implementation PRs were opened for Phase 8.

The roadmap's original button lists for each sub-phase (Self Roles, Default Role, Skip Roles, etc.) were illustrative — they did not match existing commands. Renaming buttons to those labels without backing functionality would be a low-value churn PR. The roadmap itself says *"route existing commands rather than redesign features"*; the existing panels do exactly that.

### Future Phase-8-adjacent work

If a phase-8-area panel needs attention in the future, the work is **UX standardization and hub regrouping** per `hub-ui-standard.md` — not panel re-creation. Possible follow-ups, none of which are scheduled today:

- Density audit: which Operator Hub panels exceed the component thresholds and would benefit from regrouping into a `parent_hub` cluster (the Games hub pattern)?
- Preset alignment: does each panel fit one of the five hub presets cleanly, or does it straddle two roles and need splitting?
- Helper extraction: the three (now four) `attach_back_to_*` factories across Help/Admin/Settings/Games are a candidate for Phase 3.5's shared helper. That extraction is **not** a Phase 8 task — it's the deferred Phase 2.

Panel re-creation PRs that only shuffle existing working UI should be rejected — they add noise and merge-conflict surface without UX gain.

---

## Phase 9 — Logging advanced route table

**Status:** 9a (#128) and 9b (#129) ✅ landed. 9c remains.

**Goal.** Extend `server_logging` from two channel slots (`mod_channel`, `cleanup_channel`) to a severity-and-source–aware route table, surfaced through the existing `LoggingPanelView`.

### Phase 9a — schema + resolver *(✅ landed via #128)*

Added five new optional `BindingKind.CHANNEL` slots (`debug_channel` / `info_channel` / `warning_channel` / `error_channel` / `audit_channel`) plus matching RECOMMENDED `ResourceRequirement` entries. Bumped `LOGGING_CONFIG_SCHEMA.version` 1 → 2. Refactored `resolve_log_channel` to a table-driven 7-route resolver with mod fallback for non-mod routes.

### Phase 9b — Routes UI *(✅ landed via #129)*

Added `LoggingRoutesView` (route select + Set/Create/Refresh/Back), a 🗺️ Routes button on `LoggingPanelView`, and `!logging routes` subcommand. Parameterised `LogChannelSelectView` / `LogChannelProvisionView` lookup tables to accept all seven kinds. Added a three-way table-consistency test so a future edit can't quietly let the lookup tables drift apart.

### Phase 9c — publisher strategy + subscribers *(⏳ not started)*

The remaining work is to actually deliver severity / audit events to the new channels. Phase 9c needs a publisher-strategy decision before implementation; the audit during 9a confirmed none of the target topics emit anywhere today.

#### Open question: where do the publishers land?

Three event topics need callsites:

* **`audit.action_recorded`** — emit from the canonical audit writer (the shared mutation-pipeline audit layer). Every mutation pipeline (`SettingsMutationPipeline`, `BindingMutationPipeline`, `ResourceProvisioningPipeline`, `RolloutMutationPipeline`, `GovernanceMutationPipeline`) already writes an audit row; the publish callsite goes alongside the DB insert, in one place per pipeline. Payload includes `mutation_id`, `actor_id`, `scope`, `mutation_type`, `before/after` snapshots, and a UTC timestamp. Failure to publish must not roll back the DB write (existing handler-timeout swallowing in the bus already guarantees this).

* **`runtime.error_raised`** — emit from centralized error handlers. Discord.py exposes three of them: `Bot.on_command_error`, `Bot.on_error` (event listener errors), and view-level `View.on_error`. The publish callsite goes in `BaseView.on_error` (so every view that uses the project's base inherits emission) plus a new wrapper at the bot level. Payload includes `exception_type`, `subsystem`, `actor_id` if available, `command_name` if applicable, and the exception's `repr`. **Do not** also wrap raw `logger.error(...)` calls — those are observability, not event-bus signals.

* **`runtime.warning_emitted`** — *do not* wrap every `logger.warning(...)` call. That would flood the bus with low-signal events (e.g. cache misses, transient HTTP retries). Start with a curated set of platform warnings: governance-cache invalidations that fail, pipeline-validation rejections, identity-contract findings reaching the auto-healable tier. Each publish callsite is explicit and reviewed.

#### Implementation outline (when 9c starts)

1. Register the three topic names in `core/events_catalogue.py:KNOWN_EVENTS` (the bus rejects unknown topics).
2. Add the publish callsites per the strategy above. One PR per source (so audit, error, and warning land separately and can be reviewed in isolation).
3. Subscribe `server_logging` to the three topics; route via `resolve_log_channel(guild, severity)` and `resolve_log_channel(guild, "audit")`.
4. Add per-route counter buckets (`audit_sent`, `error_sent`, `warning_sent`, etc.) to `counters_snapshot()`. Keep the existing keys for back-compat.
5. Reuse `format_log_embed` (or extend it minimally) for severity rendering — no parallel embed builder.

#### Risk: medium-high

Publishing platform-wide events is invasive: every place we add an emit needs to (a) not slow down the hot path, (b) not raise into the caller, (c) include enough payload context that a downstream subscriber can render the event without re-querying the source. The audit-pipeline path is the cleanest start; runtime.error_raised is the most invasive.

### Non-goals
- Per-event-topic custom routing (one channel per topic, not 30).
- `core.events` re-architecture.
- Log retention / archival.
- Subscribing every `logger.*` call — see warning-emit strategy above.

---

## Phase 10 — Slash front doors

**Goal.** Add slash commands that open the *same* panels as their prefix counterparts. Front doors only — not a full migration.

### Slash commands

- `/help` → `HelpPanelView`
- `/settings` → Settings Manager
- `/adminmenu` → Admin panel
- `/platform` → Platform hub
- `/games` → `GamesHubView`
- `/minemenu` → Mining hub
- `/logging` → `LoggingPanelView`
- `/cleanup` → `CleanupPanelView`

Each slash handler is a thin wrapper. Prefer hybrid commands where practical.

### Risk: medium
Slash command registration is per-guild or global; misconfiguration creates duplicates.

### Non-goals
- Migrating sub-actions to slash (`/logging routes`, `/settings access`, etc.).
- Localization.
- Migrating economy/games actions to slash.

---

## Phase 11 — Setup wizard planning / scaffold

**Status: not started; do not start until Phases 1–8 stabilize.**

### Prerequisites
- ✅ Logging fully landed
- ⏳ Cleanup panel landed (Phase 5)
- ⏳ Access policy explorer landed (Phase 6)
- ⏳ `SetupPackCatalogue` prototype
- ⏳ Resource provisioning UI proven (already true via `LogChannelProvisionView`)

### When ready

`SetupPackCatalogue` reads existing `SubsystemSchema` declarations: required settings, bindings, resource requirements, default access policies. The wizard consumes the catalogue and routes every operation through the existing pipelines — **never direct DB writes**.

Wizard flow per pack:

1. Show required + optional steps.
2. For each step: invoke `SettingsMutationPipeline` / `BindingMutationPipeline` / `ResourceProvisioningPipeline` with explicit confirmation gates.
3. End-of-pack summary with rollback option.

### Non-goals
- Any wizard step that writes directly to the DB.
- Cross-guild templates / import-export.

---

## Architecture invariants — checklist per PR

- [ ] Scalar setting writes go through `SettingsMutationPipeline`.
- [ ] Channel/role/resource pointers go through `BindingMutationPipeline`.
- [ ] Resource creation goes through `ResourceProvisioningPipeline` with preview→confirm.
- [ ] Access policy goes through `governance_service`.
- [ ] Cleanup policy/list state goes through cleanup storage/services.
- [ ] No duplicate help/menu/router system.
- [ ] No silent resource creation.
- [ ] No dead-end views — every interactive view has back-nav.
- [ ] No game logic in `games_cog.py` (router only).
- [ ] Every new panel command is registered (`KNOWN_PANEL_COMMANDS` until decorator migration).
- [ ] Every new subsystem has `SubsystemSchema` and validates via `validate_registry()`.
- [ ] `!platform identity` passes after changes.
- [ ] Unit + integration tests added.
- [ ] Manual Discord smoke checklist completed (or N/A with reason).

---

## Verification approach (per PR)

1. Unit tests under `tests/unit/` covering schemas, views, resolver branches.
2. `!platform identity` → no fatal findings.
3. `!platform customization` → new panels reported under correct subsystems.
4. `!platform settings-registry` → any new scalar settings listed.
5. `!platform provisioning` → any new resource requirements listed.
6. Help-menu walk-through: open `!help`, navigate every entry, confirm Back-nav returns home from each leaf.
7. Per-phase manual Discord smoke checklist.
8. Full existing test suite green; no flaky tests introduced.

---

## PR sequence

| Order | Phase | Status | Notes |
|---|---|---|---|
| PR-0 | Docs (this file) | ✅ landed (#117) | The initial roadmap. |
| 1 | Phase 1 | ✅ landed (#118) | `parent_hub`/`hub_group` schema v2 + validation. |
| 2 | Phase 2 *(conditional)* | ⏳ deferred to 3.5 | Helper extraction never opened — the four call sites now exist so the extraction has stable API surface. |
| 3 | Phase 3 | ✅ landed (#119) | Games hub + `!games` + `GamesHubView`. |
| 3.5 | Helper extraction | ⏳ open follow-up | Extract `attach_back_to_*` shared helper now that there are four call sites. |
| 4 | Phase 4 | ✅ landed (#120) | Help filter for `parent_hub` children. |
| 5 | Phase 5 | ✅ landed (#121) | Cleanup panel shell with wordmenu as subpage. |
| 6 | Phase 6 | ✅ landed (#122) | Access policy read-only explorer (`!settings access`). |
| 6.5a | Platform flag manager | ✅ landed (#123) | `!platform flag` per-guild enable/disable via `RolloutMutationPipeline.set_flag_state`. |
| 6.5b | Broader Platform Management Actions | ⏳ not scheduled | Binding edits, provisioning edits, cache-invalidation buttons, migration-retry controls — each needs its own canonical pipeline. |
| 7 (Option A) | Phase 7a | ✅ landed (#124) | Router-only Blackjack + RPS panels. |
| 7b | Practice / Replay / Best-of | ⏳ deferred | Requires product + game-engine decision; see Phase 7 open questions. |
| Hub UI standard | Docs | ✅ landed (#125) | `hub-ui-standard.md`. |
| 8 | Phase 8 (a–e) | ✅ audit-complete | Every panel already implemented; no PRs. Future Phase-8-adjacent work is UX standardization per `hub-ui-standard.md`, not panel re-creation. |
| Cleanup Settings Foundation | follow-up | ⏳ deferred | Waits for runtime to consume new cleanup scalar settings. |
| 9 | Phase 9 | ⏳ next major candidate | Logging advanced route table. **Not started by this roadmap-refresh PR.** Requires the prerequisites called out in Phase 9's open questions. |
| 10 | Phase 10 | ⏳ later | Slash front doors. Thin hybrid-command wrappers. |
| 11 | Phase 11 | ⏳ deferred | Setup wizard. Prereqs partially met. |

**Roadmap is open. Revise after each phase.**

---

## Open questions to resolve before affected phases

1. **Phase 2 / 3.5 helper extraction:** Now that the four call sites (Help / Admin / Settings / Games) exist, what is the smallest API that covers all four without crossing into cog imports? Action: pick this up as a small follow-up PR; the original Phase 2 decision-gate questions still apply.
2. **Phase 5 cleanup channel-policy storage:** When per-channel cleanup policy eventually ships, where is it stored? Resolve in its own design doc before any cleanup write surface lands. Today's `CleanupPanelView` is read-mostly and does not need this.
3. **Phase 7b Practice mode semantics:** `bet=0` reusing existing path vs separate no-economy path? Stats / leaderboards / tournament effect? Resolve before opening Phase 7b.
4. **Phase 7b Replay implementation:** Post-game callback shape on `BlackjackView`? Double-charge prevention strategy? Resolve before opening Phase 7b.
5. **Phase 9 event publishers:** Do `runtime.error_raised`, `runtime.warning_emitted`, `audit.action_recorded` already publish to the bus? If not, do the publish callsites land in Phase 9 or a follow-up? Default suggestion: follow-up.
6. **Phase 10 slash sync:** Global vs per-guild slash registration today? Affects rollout strategy.
7. **Phase 6.5b scope:** Which Platform Management Actions are worth canonical-pipeline UIs first? Binding edits and cache invalidation are the highest-frequency candidates; migration retry is the lowest. Sequence and scoping decision pending.

Resolved (kept for history):
- ~~Phase 6 `explain_access` helper~~ — already existed as `governance.resolve_subsystem_state`. Phase 6 used it directly; no new helper added.
