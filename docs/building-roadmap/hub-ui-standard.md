# Hub UI Standard

> **Status:** `reference` — hub UI standard.

Runtime impact: None
Scope: Future hub/panel design — how SuperBot's mother-cog hubs and child panels are laid out

This document captures the UX standard SuperBot's hubs and panels should follow from now on. It is **a reference, not a refactor plan** — existing views are not in scope. New hubs and any future hub regrouping work should align with the principles here.

Related references:

- `command-integration-standard.md` — non-negotiable rules every command/panel must obey
- `command-expansion-backlog.md` — near-term command and panel ideas
- `interface-completion-roadmap.md` — the phased plan that produced the audit feeding this doc
- `../settings-customization-command-map.md`
- `../platform-consistency-ledger.md`

---

## Why this doc exists

After Phases 1–7 of the interface-completion roadmap landed (`SUBSYSTEMS` hub metadata, the Games hub, the Help filter, the Cleanup hub, the Access explorer, the Platform flag manager, and the Blackjack/RPS router panels), an audit found that **every cog already exposes a hub view** that the Help menu and adjacent hubs route to. The shape of those hubs is inconsistent across cogs:

- Some hubs are dense action panels with seven buttons and a select.
- Some hubs are pure routers with three buttons.
- Some panels use buttons; others use a single 25-option select.
- Some panels have built-in back-nav; others rely on the wrapping context (`help_cog` / Games hub) to attach it.

The inconsistency is not a bug — each cog evolved independently. But future hubs (community, moderation, setup wizard) need a shared shape. This doc captures that shape so the next round of hubs lands consistent by construction.

The doc is also the place to record the **Phase 8 audit finding**: Role, Economy, Proof, Inventory/Leaderboard, and Channel panels were listed as future work in the interface-completion roadmap, but the source audit during this arc showed they already exist as fully integrated hub views. **Phase 8 is therefore audit-confirmed complete with zero implementation PRs.** Future work in this area should be UX standardization (using the presets below) rather than re-creating panels that already work.

---

## Core principles

1. **Hubs feel instinctive.** A user opening a hub should see the obvious next step at a glance. If they have to scan a long list to find what they want, the hub is too dense.
2. **Hubs navigate; child panels act.** The mother-cog hub's job is to route. The actual mutation, modal, or game flow happens on the child panel. Mixing many direct-action buttons with navigation buttons on the same hub blurs that contract.
3. **Don't mix action and navigation on user-facing hubs.** Mixing is acceptable on operator/admin panels (which trade density for power) but a normal user hub should pick one role per row.
4. **Prefer visible buttons for small surfaces.** A 4-button hub reveals all options at once; a dropdown hides them behind a click. Use buttons when the option count fits the layout (see thresholds below).
5. **Regroup before falling back to dropdowns.** When option count exceeds the button-friendly threshold, the first move is to subgroup (Competitive vs Activities). Dropdowns are the second move, not the first.
6. **Dropdowns are acceptable for large or dynamic lists.** SUBSYSTEMS-driven selects (Help menu, Access explorer, Flag manager) work well when the list is long, dynamic, or governance-filtered.
7. **Every panel has back-nav.** Either built-in or attached by the wrapping context (`_attach_back_to_help_button`, `attach_back_to_games_button`, `attach_back_to_settings_button`). No dead-end views.
8. **Typed commands stay first-class.** Every hub has a typed entry point (`!games`, `!cleanup`, `!platform flag`). Panels are the discoverable app surface; typed commands are the fast path. Removing a typed shortcut to force users through a panel is forbidden.
9. **No mega-cogs.** Hub cogs own navigation and rendering. Game logic, economy hooks, persistence — those stay in the child cogs they already live in. The Games hub is the canonical example: zero game-engine imports.
10. **`SUBSYSTEMS` is the source of truth.** Hub composition, child discovery, and Help filtering all derive from registry metadata. No parallel router or help system.

---

## Hub presets

Five recognised hub shapes. Picking the right preset for a new hub is the first design decision.

### 1. User Navigation Hub

For end users who want to find a feature, not configure one.

- **Primary surface:** a small set of visible buttons (≤ 8) routing to child panels.
- **Density:** low. One row of buttons, maybe two.
- **Action vs nav:** **navigation only**. The hub never starts a game, debits coins, or opens a modal.
- **Back-nav:** attached by the wrapping context.
- **Examples:** `GamesHubView` (5 children via select today, but routes only).

### 2. Feature Action Panel

For a single subsystem where the user is in the flow (playing a game, managing roles, editing settings).

- **Primary surface:** buttons that *do* things (start game, hit/stand, add word, open modal).
- **Density:** moderate — up to one full row of action buttons plus a back button.
- **Action vs nav:** **action-first**. Back-to-parent is the only nav.
- **Examples:** `BlackjackView` (the in-game view, not the panel), `_WordMenuView`, `MiningHubView`.

### 3. Operator Hub

For admins / moderators who need many tools at hand.

- **Primary surface:** category-grouped buttons or a small set of selects, each routing into a denser child page.
- **Density:** medium-high. Two to four rows of components. Acceptable to push Discord's 25-component cap when grouping is clear.
- **Action vs nav:** mixed is acceptable here. Reload-all, ServerStats, etc. can sit next to navigation.
- **Examples:** `_AdminPanelView`, `_DiagnosticsHubView`.

### 4. Platform Manager Panel

For platform-level state mutation (feature flags, future rollout, future migrations).

- **Primary surface:** a select for picking the target + a small button bank for the mutation verbs (Enable / Disable / Refresh / Back).
- **Density:** medium. Reset / advanced verbs are only present when the canonical pipeline exposes them — omit otherwise (see Phase 6.5a).
- **Action vs nav:** action-first, but every action routes through a canonical mutation pipeline. No direct DB writes from the panel. Audit-emitting only.
- **Examples:** `FlagManagerView`.

### 5. Setup Wizard Page

For the future setup wizard (Phase 11) — a single step in a guided flow.

- **Primary surface:** one or two action buttons (Apply / Skip), a back button, and (optionally) a select to pick a preset.
- **Density:** low. A wizard page that requires the user to think about more than one decision is a wizard page that should split.
- **Action vs nav:** action-first, but every action routes through the same mutation pipelines as the standalone Settings Manager. The wizard is a presentation surface over the existing write paths.

---

## Component thresholds

These thresholds map "how many children to surface" to "what component type to use". They are the answer to the question *should this hub use buttons or a dropdown?*

| Children | Recommended layout |
|---|---|
| 0–8 | Buttons preferred. All children visible at a glance. |
| 9–12 | Grouped buttons if there is a clear subgrouping (e.g. Competitive / Activities, Read / Write). Otherwise dropdown. |
| 13–25 | Dropdown preferred. Mixed buttons-and-dropdown is fine when the buttons are nav (Back / Overview) and the dropdown is the children. |
| 25+ | Subgroup pages or pagination. A flat 25-option dropdown is the ceiling Discord enforces; beyond that, group or paginate. |

Operator/Platform panels may run denser than these thresholds suggest **if** the grouping is clear and every group has a recognisable heading. Density is a power-user trade; it is never the right call for normal user hubs.

---

## Future visibility metadata (not implemented)

The `SUBSYSTEMS` schema added optional `parent_hub` and `hub_group` fields in Phase 1 (schema v2). A future schema bump may add **visibility metadata** to control where a subsystem surfaces — at the top of the Help menu, only inside its hub, in both places, or hidden entirely.

Proposed field name: `top_level_visibility` (or `surface`, name TBD).

Proposed values:

- `"top_level"` — show at the top of Help, not inside any hub.
- `"parent_only"` — show only via its `parent_hub`, never at the top of Help. (Equivalent to today's Phase 4 filter result, but explicit.)
- `"both"` — show at the top of Help **and** inside the hub.
- `"hidden"` — never surface via Help or any hub; reachable only via typed command. Useful for compatibility aliases (`rolemenu`, `wordmenu`) or feature-flagged early entries.

**Do not implement this field yet.** Phase 4's `parent_hub` filter already handles the most important case (`parent_hub` set → hide from top of Help). Adding the metadata field becomes worthwhile when:

- A subsystem wants to appear in **both** the top-level Help and inside a hub (no current case).
- A subsystem wants to be intentionally hidden from Help without losing typed access (today's "hidden" commands rely on `@commands.command(hidden=True)`; pulling that into the schema is a clean future move).

When the field lands, it will be a schema-version bump (v3) and a single `if meta.get("top_level_visibility") not in {"top_level", "both"}: continue` filter — mirroring how `parent_hub` was rolled out.

---

## Candidate future mother hubs

> **Status update (S1):** The candidates below are now **committed structure**. See [`mother-hub-map.md`](./mother-hub-map.md) for the canonical hub map, primary-vs-cross-link policy, Help-as-category-index design, and the S1–S13 PR sequence that lands them. The candidate table is preserved as historical context — the canonical assignments (including primary owner, cross-links, and the cross-link policy that supersedes schema v3 multi-`parent_hub`) live in `mother-hub-map.md`.

The Games hub (Phase 3) proved the pattern: a `parent_hub` group + `hub_group` subdivision + a single `XHubView` that discovers children dynamically. The same pattern fits several other clusters in `SUBSYSTEMS`:

| Candidate hub | Likely children (today's subsystems) | Sub-groups |
|---|---|---|
| **Games** ✅ already done | Blackjack, RPS Tournament, Deathmatch, Mining, Counting, Chain | Competitive / Activities |
| **Economy** | Economy, Inventory, Leaderboard (read-side), Mining (cross-listed) | Wallet / Marketplace / Standings |
| **Moderation / Safety** | Moderation, Cleanup, Logging | Auto-mod / Manual mod / Audit |
| **Community** | XP, Role, Counting, Chain | Progression / Roles / Community games |
| **Utility** | Utility, General, Help, Leaderboard (top-level), Diagnostics (user-facing slice) | Info / Tools / Discovery |
| **Admin / Operations** | Admin, Diagnostic, Platform commands, Settings Manager, Cleanup admin slice | Cogs / Health / Settings |
| **Setup** *(future)* | Setup wizard pages keyed by `SetupPackCatalogue` entries | One sub-group per pack |

These were originally listed as **candidates**, not commitments. As of S1 (`mother-hub-map.md`), they are committed structure with explicit primary owners and cross-link assignments. The mapping in `mother-hub-map.md` supersedes the "Mining can appear under Games and Economy depending on `top_level_visibility`" speculation here — cross-listing is now done via UI buttons (no schema v3), and Mining's primary owner is Games.

---

## Audit references — what exists today

The following views are the working set this standard was distilled from. Use them as cross-references when designing a new hub.

| View | File | Preset (closest match) | Notes |
|---|---|---|---|
| `GamesHubView` | `disbot/views/games/hub.py` | User Navigation Hub | Single dynamic select, discovers via `parent_hub`. Routes via `_cog_for_subsystem`. |
| `BlackjackPanelView` | `disbot/views/games/blackjack_panel.py` | User Navigation Hub | Three buttons (Classic / Rules / Overview). Embed-swap-in-place. |
| `RPSPanelView` | `disbot/views/games/rps_panel.py` | User Navigation Hub | Four buttons routing to typed-command instructions. |
| `RoleHubPanelView` | `disbot/cogs/role_cog.py` | Operator Hub | Six buttons (Create / Manage / Time / XP / Reaction / Diagnostics). |
| `EconomyPanelView` | `disbot/cogs/economy_cog.py` | Operator Hub | Returned from `build_help_menu_view`. |
| `_PrizeManagerView` | `disbot/cogs/proof_channel_cog.py` | Operator Hub | Proof-channel admin actions. |
| `UnifiedInventoryView` | `disbot/cogs/inventory_cog.py` | Feature Action Panel | Per-user inventory + categories. |
| `LeaderboardView` | `disbot/cogs/leaderboard_cog.py` | User Navigation Hub | Category select + pagination. |
| `_ChannelManagerView` | `disbot/cogs/channel_cog.py` | Operator Hub | Create / Delete / Restrict child views. |
| `CleanupPanelView` | `disbot/cogs/cleanup/panel.py` | Operator Hub | Read-mostly: routes to wordmenu / logging / settings. |
| `_AdminPanelView` | `disbot/cogs/admin_cog.py` | Operator Hub | Five rows, dense, mixes action + nav (acceptable for admin). |
| `_PlatformHubView` | `disbot/views/diagnostic/platform_panel.py` | Operator Hub | Four category selects + Overview button. |
| `FlagManagerView` | `disbot/views/diagnostic/flag_manager.py` | Platform Manager Panel | Pipeline-mediated mutation only. Reset button intentionally omitted. |
| `_DiagnosticsHubView` | `disbot/views/diagnostic/...` | Operator Hub | Health/latency/system info routing. |
| `HelpPanelView` | `disbot/cogs/help_cog.py` | User Navigation Hub | Paginated select; filters `parent_hub` children (Phase 4). |
| `SettingsHubView` | `disbot/views/settings/hub.py` | Operator Hub | Subsystem dropdown + per-subsystem page. Gated by feature flag. |
| `AccessExplorerView` | `disbot/views/access/explorer.py` | Platform Manager Panel *(read-only)* | Subsystem + scope selects + Explain button. |

Where a view does not fit a preset cleanly, that's signal — either the preset list is incomplete, or the view straddles two roles and should split.

---

## Phase 8 finding (audit-confirmed complete)

The interface-completion roadmap (`interface-completion-roadmap.md`, Phase 8 sub-phases a–e) listed Role, Economy, Proof, Inventory/Leaderboard, and Channel panels as future implementation work. The source audit during this arc showed every one of those panels already exists and is fully integrated with `build_help_menu_view`. No PRs were opened for Phase 8.

The illustrative button labels in the roadmap (Self Roles, Default Role, Skip Roles, etc.) did not match existing commands. Renaming buttons just to align with that wording would have been a low-value churn PR — and the roadmap itself says *"route existing commands rather than redesign features"*. Existing panels do exactly that.

**Future Phase-8-adjacent work, if any, belongs in this standard, not in re-creation PRs:**

- If an existing hub does not fit one of the five presets above, split or regroup.
- If an existing hub's density exceeds the threshold, consider regrouping into a `parent_hub` cluster (the Games hub pattern).
- If multiple hubs share back-nav boilerplate (the case today across Help / Admin / Settings / Games), the shared helper extraction noted in `interface-completion-roadmap.md` Phase 3.5 is the right home for the consolidation. It is **not** a Phase 8 task.

---

## Decision checklist for a new hub

Before opening a new hub PR, answer these:

- [ ] Which preset does this hub match? (If "none", split or pick the closest.)
- [ ] How many children does it surface today? In a year?
- [ ] Does it need to discover children dynamically (via `parent_hub`) or is the child list static?
- [ ] What is the typed entry point? (Mandatory — never `panel-only`.)
- [ ] Is there a back-nav path back to the wrapping hub or Help? (If not via the existing helpers, why?)
- [ ] If the hub is a Platform Manager Panel, which mutation pipeline does every action route through?
- [ ] Does any new state need governance / visibility / capability declarations in `SUBSYSTEMS`? If yes, is the schema bump worth doing in this PR or a separate one?
- [ ] Does the hub belong in one of the candidate mother hubs above, or is it a new top-level subsystem?

---

**Standard is open.** Revise after each new hub lands. PRs that violate the standard should call it out explicitly so the deviation is visible to reviewers — not silent.
