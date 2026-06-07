# SuperBot Canonical Mother-Hub Map

> **Status:** `reference` — mother-hub structure map.

Runtime impact: None (this document; subsequent PRs implement)  
Scope: Defines the mother-hub structure, Help category index, navigation doctrine, settings doctrine, and PR sequence (S1–S13) that bring SuperBot into the committed structure.

Related references:

- `hub-ui-standard.md` — hub presets, component thresholds, design principles
- `command-integration-standard.md` — rules every command/panel must obey
- `command-expansion-backlog.md` — near-term command/panel ideas
- `interface-completion-roadmap.md` — phased roadmap (Phases 1–9c.1 landed)
- `../loose-ends-audit-roadmap.md` — Phase 9b loose-ends audit (L1–L6 superseded by S1–S13 below)

---

## Context

SuperBot's structural loose ends are user-visible. Help still groups subsystems by visibility tier (User / Moderation / Administration), not by mother-hub category, so a user sees a flat list of cogs rather than a coherent app with named areas. Navigation helpers are still duplicated across 11+ panels even after PR #130 landed `views/navigation.py`. The candidate mother hubs in `hub-ui-standard.md` (Economy, Moderation/Safety, Community, Utility) were explicitly labeled "candidates, not commitments" — so each new hub PR risks reintroducing duplicate routers or inline back helpers.

The product goal: SuperBot feels like a coherent Discord-native app. Help becomes the category index. Mother hubs are metadata-driven routers shown as Help categories. Child cogs own their action panels. A user reaches common panels in ≤2 interactions after Help, common actions in ≤3.

This document commits the canonical structure and the PR sequence that lands it. It supersedes the candidate list in `hub-ui-standard.md:137-151` and the L1–L6 sequence in `loose-ends-audit-roadmap.md:296-401`.

---

## Canonical mother-hub map

The **Target primary children** column lists the children each hub should own when its panel exists. Today only Games has children declared via `parent_hub` metadata — the other hubs acquire their primary children when their hub PR (S7–S10) lands and adds `parent_hub` for the relevant subsystems.

| Hub | Cog owner | Preset | Target primary children | Cross-link buttons (no metadata change) | Typed entry | Future slash | Settings story |
|---|---|---|---|---|---|---|---|
| **Games** ✅ already live | `games_cog.GamesHubView` | User Navigation | blackjack, deathmatch, rps_tournament, mining, counting, chain (all have `parent_hub="games"` today) | none | `!games` | `/games` | none needed |
| **Economy** (not yet live) | `economy_cog` (existing) | User Navigation | economy, inventory, leaderboard (no `parent_hub` set today; S7 adds it) | mining (primary Games) | `!economy` | `/economy` | existing economy schema |
| **Moderation / Safety** (not yet live) | `moderation_cog` (existing) | Operator | moderation, cleanup, logging, proof_channel (no `parent_hub` set today; S8 adds it) | none | `!modmenu` (existing) | `/moderation` | moderation schema needs registration; cleanup uses governance; logging schema registered |
| **Community** (not yet live) | **new** `community_cog` (no existing domain owner) | User Navigation | xp, role (S9 adds `parent_hub`) | counting (primary Games), chain (primary Games), leaderboard (primary Economy) | `!community` (new) | `/community` | xp schema needs registration; role schema needs creation |
| **Utility** (not yet live) | `utility_cog` (existing) | User Navigation | utility, general (S10 adds `parent_hub`) | help (cross-link to Help itself); user-facing diagnostic slice | `!utility` (existing) | `/utility` | none needed |
| **Admin / Operations** ✅ already live | `admin_cog._AdminPanelView` (existing) | Operator | n/a — routes to subsystem panels (no `parent_hub` children) | logging (primary Moderation), cleanup (primary Moderation), settings, platform, role (primary Community), channel | `!adminmenu` (existing) | `/admin` | n/a |
| **Settings / Configuration** ✅ already live | `settings_cog.SettingsHubView` (existing) | Operator | n/a — enumerates SUBSYSTEMS with registered schemas | n/a | `!settings` (existing) | `/settings` | itself is the surface |
| **Platform / Diagnostics** ✅ already live | `diagnostic_cog._PlatformHubView` (existing) | Operator | n/a — routes to diagnostic categories | n/a | `!platform` (existing) | `/platform` | none |
| **Setup Wizard** (future) | new `setup_cog` (future) | Setup Wizard | wizard pages keyed by `SetupPackCatalogue` | n/a | `!setup` | `/setup` | presentation surface over existing pipelines |

**Help is not a category in Help.** Help is the discovery surface itself, not a hub. The `!help` command opens Help; no hub category named "Help" exists.

---

## Primary children vs cross-links

A subsystem has **exactly one primary owner** represented by `parent_hub` where possible. Cross-listed features are exposed through cross-link buttons only. **Cross-links do not change: owning cog, action panel owner, settings owner, mutation path, or `parent_hub`.**

| Subsystem | Primary | Cross-link(s) |
|---|---|---|
| mining | Games | Economy |
| counting | Games | Community |
| chain | Games | Community |
| leaderboard | Economy | Community |
| logging | Moderation / Safety | Admin, Platform |
| (cleanup, proof_channel, settings, role, etc.) | per map table above | as applicable |

---

## Hard constraints

- **No multi-`parent_hub`.** The registry validator at `disbot/utils/subsystem_registry.py:818-827` rejects two-hop hubs. Multi-parent_hub is structurally impossible without a schema v3 bump.
- **No `mother_hubs_cog.py` god-object** owning multiple hubs. Hub view lives in the existing domain cog.
- **No business logic in hub views.** Nav and render only — no game/economy/role logic, no DB writes.
- **No direct DB writes from any new view.** Use the appropriate mutation pipeline.
- **No parallel routers.** `SUBSYSTEMS` is the single source of truth.
- **No new navigation helper modules.** `disbot/views/navigation.py` is canonical.

---

## Hub ownership rule

Hub view lives in the existing domain cog:

- Economy hub → `economy_cog`
- Moderation/Safety hub → `moderation_cog`
- Utility hub → `utility_cog`

**Exception:** Community has no existing domain owner. It gets a brand-new `community_cog` whose **only** responsibility is the hub view. No business logic. No DB writes. No game/economy/role logic.

---

## Hub visibility rule

A hub appears in Help only if:

1. The hub panel exists.
2. The user has governance visibility for the hub or at least one of its visible children.
3. The hub has at least one visible child or a valid standalone purpose.

If all children are hidden, the hub is hidden from Help. Direct typed commands may still return a specific permission-denied or missing-configuration message — they don't 404.

---

## Per-hub readiness checklist

A hub does not appear in Help (and a hub PR does not land) until **all** of these are green:

1. `parent_hub` metadata exists for every primary child.
2. Hub view exists, follows preset, uses `views/navigation.py` (no local back helper).
3. Typed `!` entry point exists.
4. `build_help_menu_view` exists on the hub's host cog and returns the hub view.
5. Every child opened from the hub has Back-to-hub and Back-to-Help.
6. Hub shows as a category in Help with purpose + child names.
7. Settings path exists OR "no settings needed" is explicit.
8. Hub view contains nav/render only.
9. Permission and role test matrix (below) passes for the hub.

---

## Help-as-category-index design (S3 target)

Today `help_cog.build_overview_embed` groups by visibility tier. S3 introduces category-grouped Help while keeping the tier view as a permanent "All Commands / Advanced" fallback.

### S3 v1 — existing-hub-only rollout

S3 v1 shows **only mother hubs that already have real panels**:

- 🎮 **Games**
- ⚙️ **Admin / Operations**
- 🔧 **Settings / Configuration**
- 🩺 **Platform / Diagnostics**
- 📋 **All Commands / Advanced** (permanent fallback)

**Economy, Moderation/Safety, Community, Utility, and Setup are not shown as top-level Help categories until their real hub panels land.** Their current commands remain discoverable through All Commands / Advanced. As S7–S10 land, each hub promotes from "All Commands" to its own category in Help.

This rule prevents Help from advertising hubs that don't exist — no "Coming soon" categories.

### All Commands / Advanced is permanent

The tier-grouped command view is preserved as a permanent category named "All Commands / Advanced." Reasons:

- Power users who know a command name shouldn't be forced through category navigation.
- It's the fallback for subsystems that don't fit any mother hub.
- It's where future hubs' children live before their hub lands.
- It guarantees discoverability for every visible subsystem.

### S3 v1 Help layout (what ships in S3)

```
📚 Help Menu

🎮 Games
  Game flows and tournaments.
  Includes: Blackjack, RPS, Deathmatch, Mining, Counting, Chain.
  → !games

⚙️ Admin / Operations          (hidden unless tier allows)
  Cog management, health checks, role/channel administration.
  → !adminmenu

🔧 Settings / Configuration    (hidden unless tier allows)
  Configure all subsystems via mutation pipelines.
  → !settings

🩺 Platform / Diagnostics      (hidden unless tier allows)
  Platform identity, feature flags, runtime health.
  → !platform

📋 All Commands / Advanced
  Browse every visible command directly, grouped by tier.
```

### Final-target Help layout (after S7–S10 land — not S3 v1)

The eventual shape of Help once Economy, Moderation/Safety, Community, and Utility hubs land. S3 v1 does **not** include these categories.

```
📚 Help Menu

🎮 Games
  Game flows and tournaments.
  Includes: Blackjack, RPS, Deathmatch, Mining, Counting, Chain.
  → !games

💰 Economy                     (added by S7)
  Currency, items, leaderboards, work, shop.
  Includes: Economy, Inventory, Leaderboard. Cross-link: Mining.
  → !economy

🛡️ Moderation & Safety         (added by S8)
  Moderation actions, cleanup, audit, proof channel.
  Includes: Moderation, Cleanup, Logging, Proof Channel.
  → !modmenu

🌱 Community                   (added by S9)
  Progression, roles, community games.
  Includes: XP, Roles. Cross-links: Counting, Chain, Leaderboard.
  → !community

🧰 Utility                     (added by S10)
  Info, tools, discovery.
  Includes: Utility, General. Cross-links: Help, Platform info.
  → !utility

⚙️ Admin / Operations          (hidden unless tier allows)
  Cog management, health checks, role/channel administration.
  → !adminmenu

🔧 Settings / Configuration    (hidden unless tier allows)
  Configure all subsystems via mutation pipelines.
  → !settings

🩺 Platform / Diagnostics      (hidden unless tier allows)
  Platform identity, feature flags, runtime health.
  → !platform

📋 All Commands / Advanced
  Browse every visible command directly, grouped by tier.
```

**Utility appears only when its hub panel exists.** S10 ships the Utility hub; until then Utility commands live under All Commands / Advanced.

### Selecting a category

- Category dropdown selection opens the hub's `build_help_menu_view`.
- "All Commands / Advanced" opens a paginated tier-grouped view (today's behavior).
- Governance still filters within categories — a user who can't see Moderation just doesn't see that category.

### Promotion path

When a new hub lands in S7–S10:

1. Add the hub's panel and `build_help_menu_view` (per the per-hub readiness checklist).
2. Add the hub to the central hub presentation registry (below).
3. Help automatically shows the new category — no `help_cog` code change required if registry-driven rendering is in place.
4. The hub's child subsystems disappear from "All Commands" (because they now have a hub primary owner), or stay if they're cross-link-only.

---

## Central hub presentation registry

Hub display metadata must **not** be scattered inside `help_cog.py`. Use a central hub-presentation registry near `SUBSYSTEMS` or in an adjacent module (`disbot/utils/hub_registry.py` proposed).

### Fields per hub entry

- `key` — internal id (e.g., `"games"`).
- `display_name` — user-facing name (e.g., `"Games"`).
- `emoji` — single emoji.
- `purpose` — 1-line description.
- `entry_command` — e.g., `"!games"`.
- `slash_command` — e.g., `"/games"` or `None` until S11.
- `primary_children` — list of subsystem keys (auto-derivable from `SUBSYSTEMS` where `parent_hub == key`).
- `cross_links` — list of `(subsystem_key, label)` tuples for cross-link buttons.
- `minimum_tier` — visibility tier required to see the hub.
- `settings_path` — settings hub subsystem key or `None`.
- `panel_available` — bool. Drives the visibility rule: hubs with `panel_available=False` don't appear as Help categories.

### Rules

- **Presentation only.** The registry describes Help/category display. It is **not** a second router and must not own business logic.
- **No DB writes, no governance resolution, no command dispatch.**
- Help, hub views, and slash registration all read from the same registry.
- Schema v3 (`top_level_visibility`, `mother_hubs`, `primary_hub`, `hub_groups`) is **not** pursued — the registry covers presentation needs without a metadata schema bump.

### S3 builds the registry

The S3 PR introduces this registry with the v1 entries (Games, Admin, Settings, Platform, All Commands). Subsequent S7–S10 PRs each add one entry.

---

## Navigation state contract (deferred)

A typed navigation-state contract would let Back return the user to the route they came from, with examples like:

- `!help` → Games → Mining → **Back** to Games.
- `!help` → Economy → Mining → **Back** to Economy (not Games).
- `!mining` direct → Back semantics differ from Help-launched.

**Status: deferred.** Until a real use case forces it, parent-builder closures in `views/navigation.py` already capture where-to-go-back via the closure's captured variables. Each call site provides its own builder; that's sufficient for everything shipping in S2–S6.

### When to revisit

- When **cross-link back-navigation** in a real hub PR exposes a case where the same panel can be opened from two different hubs and the closure approach becomes unwieldy (likely S7 Economy with its mining cross-link).
- When **slash routing** (S11) needs to propagate "I came from slash" so Back doesn't try to return to a stale text-command message.

If either condition triggers, add a small PR that introduces `NavigationState` with `source` / `parent_hub` / `help_page` / `breadcrumb` fields and an optional second parameter on `build_help_menu_view`. Until then, do not pre-build the contract.

### Tests that must accompany whichever PR finally introduces it

- Help → Games → Mining → Back → Games hub (not Help).
- Help → Economy → Mining → Back → Economy hub (not Games).
- `!mining` direct → no breadcrumb prefix.
- Slash `/mining` → no breadcrumb prefix.
- Back-to-Help always returns to Help regardless of source.

---

## User-centered UX requirements

These apply to every panel and hub. Each subsequent PR references this section.

### 1. Orientation
- Every hub embed states: what the hub is for, which child cogs it contains, primary entry command.
- Embeds include a breadcrumb such as `Help / Moderation / Cleanup` in the footer where practical.

### 2. Speed
- Common panels reachable in ≤2 interactions after Help.
- Common actions reachable in ≤3 interactions after Help.
- Action subpanels (the 4th layer) are reserved for confirmation views and modal-equivalent flows.

### 3. Escape routes
- Every panel has Back-one-layer and direct return to Help.
- Back uses `views/navigation.py:attach_back_button` with a `parent_builder` closure.
- Back-to-Help is attached by the surface that opened the panel.

### 4. Feedback
- Every button action produces exactly one of: ✅ success, ✏️ needs input, ⏳ cooldown, 🔒 permission denied, ⚙️ missing configuration, 💤 no-op / already set, ⚠️ safe failure.

### 5. Empty states
- An empty panel must explain what the feature does and what the next step is. Example: an empty leaderboard says "Earn XP to appear here. Use `!rank` to check your progress."
- No silent empty embeds.

### 6. Safety
- Dangerous changes use preview + confirm.
- Confirmation embeds include: old value, new value, scope, actor, and a one-line audit reason input where applicable.
- Pipelines handle audit emission; the view never writes the audit log itself.

### 7. Mobile usability
- ≤5 embed fields per panel where possible.
- Critical controls never hidden behind dropdowns when ≤8 visible buttons would be clearer.
- Disabled buttons labeled clearly ("Cooling down" not greyed).
- Long descriptions truncate with a "see `!command help`" hint.

### 8. Settings discoverability
- Every mother hub and major child cog has a settings path or declares "no settings needed".
- Settings paths reachable from Help → Settings → subsystem dropdown.
- Every settings change routes through the appropriate pipeline.

### 9. Breadcrumbs
- Hub-level embeds: `Help / <Hub>`.
- Child panels: `Help / <Hub> / <Child>`.
- Action subpanels: `Help / <Hub> / <Child> / <Action>`.

### 10. No duplication
- A subsystem may appear under multiple mother hubs via cross-link buttons, but it has **one** owning cog and **one** action panel.
- Hubs route; child cogs act.

---

## Permission and role testing matrix

Help and hub behavior must be tested for all of these contexts. S3 and every hub PR (S7–S10) must include tests covering this matrix for the affected surface.

| Context | Expected behavior |
|---|---|
| Normal user (`user` tier) | Sees only user-tier categories; cannot open Admin/Settings/Platform |
| Moderator (`moderator` tier) | Sees user + moderation categories; cannot open Admin |
| Administrator (`administrator` tier) | Sees all categories |
| Bot owner / operator (`owner` tier) | Sees all categories + restricted operator surfaces |
| Wrong user clicks another user's panel | Ephemeral "this isn't your panel" — view not mutated |
| DM context | Help opens with a "no guild context" message; guild-scoped hubs disabled |
| Disabled subsystem (governance) | Hub hides the category if all children disabled |
| Disabled channel visibility | Subsystem visible from typed command if the channel allows; hidden from category list otherwise |
| Incomplete guild configuration | Hub category appears but selecting it shows ⚙️ "missing configuration" with a link to the settings path |

---

## New cog checklist

Every future cog must declare/implement, before merging:

1. `SUBSYSTEMS` metadata entry (key, display_name, emoji, description, entry_points, visibility_tier).
2. Primary mother hub (`parent_hub` if a child; otherwise primary ownership entry in `hub_registry`).
3. Optional cross-links (entries in `hub_registry.cross_links`).
4. Typed entry command (`!<name>` and aliases).
5. `build_help_menu_view(interaction, nav_state=None)` hook (the optional second parameter is reserved for the deferred navigation state contract; today's hook signature remains single-argument until S7/S11 promotes the contract).
6. Settings classification: scalar / bindings / provisioning / governance / "no settings needed" — and the corresponding schema or service.
7. Back-navigation via `views/navigation.py:attach_back_button` only — no local helpers.
8. Empty-state behavior — explains feature + next step.
9. Permission-denied behavior — clear ephemeral with what permission is missing.
10. Help/discoverability tests — appears in Help under correct category for each tier in the matrix above.

---

## Navigation gap list (informs S2)

| Panel | File | Migration target |
|---|---|---|
| Games hub back | `disbot/views/games/hub.py:114-150` | `attach_back_button(parent_builder=games_hub_builder)` |
| Settings subsystem back | `disbot/views/settings/subsystem_view.py:240-273` | `attach_back_button(parent_builder=settings_hub_builder)` |
| Logging panel overview | `disbot/cogs/logging/panel.py:188-202` | `transition_to(builder=logging_overview_builder)` |
| Cleanup back-to-help | `disbot/cogs/cleanup/panel.py` | use `attach_back_button` where back-to-help is attached |
| Channels visibility back | `disbot/views/channels/visibility_panel.py:93` | `attach_back_button(parent_builder=channel_manager_builder)` |
| Economy main/shop/work back | `disbot/views/economy/*.py:265/142/162` | `attach_back_button(parent_builder=economy_hub_builder)` |
| Mining main/mine back | `disbot/views/mining/*.py:206/197` | `attach_back_button(parent_builder=mining_hub_builder)` |
| Roles diagnostics/management/reaction/time/xp | `disbot/views/roles/*.py` | `attach_back_button(parent_builder=role_hub_builder)` |
| Diagnostic platform | `disbot/views/diagnostic/platform_panel.py` | add `attach_back_button(parent_builder=admin_hub_builder)` |

**Refresh stays local** — it re-reads state without navigating; not a back/transition.

**Migration order in S2:**

1. Games hub (highest leverage — canonical pattern for S7+).
2. Settings subsystem (second pattern; cleans the only other inline factory module).
3. Channels visibility (leaf; preps S4 placeholder cleanup).
4. The rest, grouped by cog family (economy / mining / roles), one PR per family if scope grows too large.

---

## Help discovery gap list (informs S3)

- Discovery is near-complete (21/22 cogs have `build_help_menu_view`).
- Help today groups by **tier**. S3 changes to category grouping with tier filtering retained.
- Invariant test (small, additive): every visible top-level subsystem either has a `build_help_menu_view` hook OR is in a whitelisted "static-fallback-acceptable" set. Fail CI if a new cog is added without one or the other.
- Central hub presentation registry (`hub_registry.py`) introduced in S3.

---

## Settings / config gap list (informs S5)

### Classification

| Subsystem | Settings story | Status |
|---|---|---|
| economy | bindings (log channel) | ✅ registered |
| logging | scalars + 7 bindings + resources | ✅ registered |
| moderation | scalars (WARN_THRESHOLD, WARN_TIMEOUT_MINS) | ⚠️ declared, not registered |
| xp | scalars (XP_MIN/MAX/COOLDOWN/CHANNEL) | ⚠️ declared, not registered |
| cleanup | governance policies (cleanup service) | ✅ routes correctly |
| role | role-XP/time thresholds | ❌ no schema; direct DB writes |
| channel | channel binding policies | ❌ no schema |
| proof_channel | resource (proof channel binding) | ❌ no schema |
| blackjack | tournament settings | ❌ orphaned; direct DB write |
| mining | game state | none scalar; direct DB writes (S6) |
| counting, chain, deathmatch, rps_tournament | game state | none needed |
| inventory, leaderboard | n/a | none needed |
| general, utility, help, admin, diagnostic, settings, games | n/a | none needed |

### Doctrine

- Scalar settings → `SettingsMutationPipeline`.
- Channel/role/resource bindings → `BindingMutationPipeline`.
- Resource creation → `ResourceProvisioningPipeline` (preview + confirm).
- Access/visibility → `governance_service`.
- Cleanup policies → cleanup service/storage.
- No direct DB writes from views.

---

## Placeholder / dead-end doctrine (informs S4)

Three actions per placeholder:

1. **Implement now** if backend already supports it.
2. **Route to an existing panel** if functionality exists elsewhere.
3. **Remove/disable and document** in `command-expansion-backlog.md` if backend doesn't exist yet.

### Current placeholder inventory

| Location | Issue | Action |
|---|---|---|
| `disbot/views/channels/visibility_panel.py` | "category and guild-scope coming soon" | Inspect `governance_service` capability. Implement if supported; else rewrite copy to "configures channel-scope visibility" and add a backlog entry. **Specific exception: this placeholder depends on settings ownership (Settings hub vs Channels hub) — so this one waits for S5.** |
| `disbot/views/games/hub.py:173` | "Panel view not implemented yet" | Unreachable today. Keep as safety net. Add invariant test in S3. |
| Phase 9c.2 route counters | Would show 0 until publishers wired | Deferred. Do not surface counters until publishers exist. |

### S4 sequencing

S4 generally precedes S5 (don't let settings completeness block visible UX fixes). The channel visibility scope is the one exception — that specific item waits for S5.

---

## Final prioritized PR sequence

| PR | Goal | Gate | Risk |
|---|---|---|---|
| **S1** | docs-only canonical mother-hub map (this document) | none | trivial |
| **S2** | migrate remaining local back helpers to `views/navigation.py` | S1 merged | low |
| **S3** | Help category index v1 (existing hubs only: Games + Admin + Settings + Platform + All Commands); introduces `hub_registry` | S2 merged for the Games hub | medium |
| **S4** | visible placeholder/dead-end cleanup (except channel visibility scope) | S2 merged | low-medium |
| **S5** | settings/config completion: register dormant schemas (moderation, xp); declare missing schemas (role, channel, proof_channel, blackjack); resolve channel visibility scope | S4 merged for everything except channel visibility | medium |
| **S6** | direct-DB-writes-from-views remediation; scoped, incremental, one cog per PR | S5 merged | medium-high |
| **S7** | Economy hub — uses existing `economy_cog`; cross-link to mining; promotes to Help category. **If cross-link back-nav forces it, this PR adds the deferred `NavigationState` contract; otherwise stays closure-only.** | S2 + S3 merged | medium |
| **S8** | Moderation/Safety hub — uses existing `moderation_cog`; promotes to Help category | S7 merged | medium |
| **S9** | Community hub — new `community_cog` (nav-only); XP + Role primary, cross-links | S8 merged | medium |
| **S10** | Utility hub — uses existing `utility_cog`; lightweight | S9 merged | low |
| **S11** | slash front doors for stabilized hubs. **If slash routing forces it and `NavigationState` is not yet in, this PR adds it.** | S10 merged | medium (Discord sync) |
| **S12** | Setup wizard scaffolding | S11 merged | medium |
| **S13** | resume Phase 9c.2 (publishers) | S12 merged or explicitly skipped | medium-high |

### Hard gates

- No new mother hub PR (S7+) until S2 migrates the Games hub (canonical template).
- No new mother hub PR (S7+) until S3 introduces `hub_registry` (presentation layer).
- No slash PR (S11) until all hubs being slash-fronted are stable.
- No Phase 9c.2 (S13) before S4 placeholder cleanup is complete.
- No new cog before its hub metadata is committed to this document.
- `NavigationState` contract is **not pre-built**. It lands inside the first PR (S7 or S11) where closure-only back-nav demonstrably falls short.

---

## Acceptance criteria per PR

### S1 — this PR
- Only `.md` files changed.
- This document exists in `docs/building-roadmap/mother-hub-map.md`.
- `hub-ui-standard.md` has a header pointing here; the candidates section is labeled as committed; the original candidate table is preserved as historical context.
- `loose-ends-audit-roadmap.md` has a top note stating L1–L6 is superseded by S1–S13; findings remain valid as the source audit.
- `docs/building-roadmap/README.md` indexes this document.

### S2 — navigation migration (first code PR)
- Uses existing `views/navigation.py`.
- Removes Games hub's `attach_back_to_games_button`.
- Preserves custom IDs (`games:back` stays `games:back`).
- Tests: back click rebuilds `GamesHubView`; 25-component cap preserved; failure path logs + ephemeral fallback.
- Manual smoke: `!help` → Games → child → Back to Games → Back to Help still works.

### S3 — Help category index v1
- Help top-level shows Games + Admin + Settings + Platform + All Commands as categories.
- Each category lists purpose and included child names.
- Governance filters categories per the visibility rule.
- "All Commands / Advanced" is permanent and reproduces today's tier-grouped behavior.
- `hub_registry` introduced and used by Help.
- Permission and role testing matrix passes.

### S4 — placeholder cleanup
- No visible "coming soon" copy unless tracked in `command-expansion-backlog.md`.
- No reachable "panel not implemented yet" for important panels.
- Empty states explain the feature and next step.
- No backend behavior invented.

### S7–S10 — new hub PRs
- Hub passes the per-hub readiness checklist (9 items).
- Hub promotes to Help category via `hub_registry`.
- Cross-link buttons work, with Back returning correctly.
- Permission and role testing matrix passes.

---

## Out-of-scope for S1

- All code changes.
- Schema v3 (`top_level_visibility`, `mother_hubs`, `primary_hub`, `hub_groups`) — documented as a future option only; not pursued speculatively. The `hub_registry` covers presentation needs without a schema bump.
- Direct-DB-write remediation — PR S6.
- Phase 9c.2 — PR S13.
