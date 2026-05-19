# SuperBot Interface Completion Roadmap

Status: Open roadmap — revisable after every phase
Runtime impact: None (PR-0 is docs-only)

This document captures the next major arc of SuperBot work: pulling the existing scattered cog surface into a coherent, discoverable, Discord-native application. The platform foundation (settings/customization map, registry, pipelines, `!platform` hub, Settings Manager shell, Logging subsystem) is **complete**. This roadmap is what comes after.

Each phase below is sized to one PR. Phases must be reviewed and smoke-tested before later phases are committed to — do not lock in downstream work before the upstream phase has merged.

Related reference:

- `command-integration-standard.md` — non-negotiable rules every phase must obey
- `command-expansion-backlog.md` — near-term command and panel ideas
- `../settings-customization-command-map.md`
- `../platform-consistency-ledger.md`

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

## Phase 1 — `parent_hub` and `hub_group` metadata in `SUBSYSTEMS`

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

## Phase 2 — Shared navigation helpers *(conditional)*

**Goal.** Extract the three (about-to-be-four) `attach_back_to_*` factories into one helper module, **only if** it can be done as a small import-safe PR.

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

## Phase 3 — `games` Subsystem + `!games` Command + `GamesHubView`

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

## Phase 4 — Help menu filter for `parent_hub` children

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

## Phase 5 — Cleanup panel shell with `wordmenu` as subpage

**Goal.** Replace the standalone `!wordmenu` UX with a full `!cleanup` panel whose first iteration is mostly read-only and routes existing functionality. No channel-specific cleanup policy writes — that requires storage that does not yet exist.

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

## Phase 6 — Access policy read-only explorer

**Goal.** Surface effective governance/access policy as a read-only explorer through `!settings access`. The write surface is a future PR.

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

## Phase 7 — Blackjack and RPS mode/replay panels

**Goal.** Per-game mode/replay panels for the two highest-priority Competitive games, layered on the now-existing Games hub.

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

## Phase 8 — Role, Economy, Proof, Inventory/Leaderboard, Channel panels

Each sub-phase follows the same pattern: a `<cog>PanelView`, schema declaration, `build_help_menu_view` exposure, panel command, back-nav. One PR per cog, conservative scope, route existing commands rather than redesign features.

### 8a — Role Panel (`!roles`)
Self Roles, Reaction Roles, Default Role, Skip Roles, Role Menu Setup, Role Settings, Back to Help. **Non-goal:** automated role creation/assignment beyond what exists. Hierarchy and permission risk.

### 8b — Economy Panel
Balance, Daily, Work, Shop, Inventory, Transfer, Economy Settings, Economy Logs, Back to Help. Routes existing commands. **No new betting rules or shop redesign.**

### 8c — Proof Panel (`!proof`)
Submit Proof, Proof Requirements, Staff Review Queue, Approval Role, Proof Settings, Back to Help.

### 8d — Inventory / Leaderboard
Add `build_help_menu_view` to each if missing; integrate into Economy panel.

### 8e — Channel Management Panel
Consolidate `disbot/views/channels/{create,delete,restrict}_panel.py` under one entry.

**Risk per sub-phase:** low-medium. **Non-goals:** no feature redesigns; no new settings unless lifting an existing knob into schema.

---

## Phase 9 — Logging advanced route table

**Goal.** Extend `server_logging` from two channel slots (`mod_channel`, `cleanup_channel`) to a severity-and-source–aware route table, surfaced through the existing `LoggingPanelView`. Default behavior unchanged; new routes are optional and additive.

**Why this is late, not first.** Basic logging is fully landed and operationally sufficient. Centralized interface completion is higher leverage than incremental logging features.

### Approach

- Extend `disbot/cogs/logging/schemas.py` with new bindings (`debug_channel`, `info_channel`, `warning_channel`, `error_channel`, `audit_channel`), all OPTIONAL via `BindingMutationPipeline`. Resource requirements RECOMMENDED only; auto-create defaults stay OFF.
- Extend `resolve_log_channel(guild, kind)` with route lookup order:
  1. severity-specific binding (`error_channel`, etc.)
  2. source-specific fallback (`mod_channel` / `cleanup_channel` / `audit_channel`)
  3. legacy scalar fallback
- Subscribe to more event topics on `core.events`: `runtime.error_raised`, `runtime.warning_emitted`, `audit.action_recorded`. If a publisher does not yet exist, add it in a follow-up PR — keep this PR small.
- Add a "Routes" subpage to `LoggingPanelView` with `LogChannelSelectView` / `LogChannelProvisionView` per-route.
- Add `!logging routes` subcommand mirroring the panel page.

### Risk: medium
Schema extension to a frozen registry; resolver fallback order must remain deterministic; counters need new buckets without breaking `counters_snapshot()` consumers.

### Non-goals
- Per-event-topic custom routing.
- `core.events` re-architecture.
- Log retention / archival.

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

| Order | Phase | Notes |
|---|---|---|
| PR-0 | Docs | This document |
| 1 | Phase 1 | `parent_hub`/`hub_group` schema + validation only |
| 2 | Phase 2 *(conditional)* | Navigation helper extraction — only if import-safe |
| 3 | Phase 3 | Games hub + `!games` + `GamesHubView` (router only) |
| 3.5 | *(if Phase 2 skipped)* | Extract navigation helper with 4 call sites |
| 4 | Phase 4 | Help filter for `parent_hub` children |
| 5 | Phase 5 | Cleanup panel shell |
| 6 | Phase 6 | Access read-only explorer |
| 7 | Phase 7 | Blackjack + RPS mode/replay panels |
| 8 | Phase 8 (a–e) | Role, Economy, Proof, Inventory/Leaderboard, Channel — one PR each |
| 9 | Phase 9 | Logging advanced routes |
| 10 | Phase 10 | Slash front doors |
| 11 | Phase 11 | Setup wizard scaffolding |

**Roadmap is open. Revise after each phase.**

---

## Open questions to resolve before affected phases

1. **Phase 2 decision gate:** Does the helper extraction pass the import-safety check? Resolve before opening the Phase 2 PR; if any check fails, skip to Phase 3 and revisit at 3.5.
2. **Phase 5 cleanup channel-policy storage:** When per-channel cleanup policy eventually ships, where is it stored? Resolve in its own design doc before Phase 5 writes (read-only Phase 5 doesn't need it).
3. **Phase 6 `explain_access`:** Does `governance_service` already expose a read-only "why is this blocked" helper, or must we add one? Inspect before opening the PR.
4. **Phase 9 event publishers:** Do `runtime.error_raised`, `runtime.warning_emitted`, `audit.action_recorded` already publish to the bus? If not, do the publish callsites land in Phase 9 or a follow-up? Default suggestion: follow-up.
5. **Phase 10 slash sync:** Global vs per-guild slash registration today? Affects rollout strategy.

None of these block PR-0 or Phase 1.
