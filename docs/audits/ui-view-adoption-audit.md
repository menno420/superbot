# SuperBot — UI / View Adoption Audit

> **Status:** `living-ledger` — ⚠️ SUPERSEDED inventory snapshot, dated 2026-05-24, `main` at
> `948f539` (post-PR-#289). The PR 1–7 backlog in §7 / §9.3 has all
> shipped; **`docs/audits/repo-wide-audit-2026-05-29.md` reconciles this
> snapshot against current code and supersedes its open backlog.** Do
> not action items from this doc without re-verifying against the
> source — e.g. `views/economy/work_panel.py:86` is no longer "bare"
> (it now defers before I/O).
> Companion to `docs/helper-policy.md`, `docs/building-roadmap/hub-ui-standard.md`,
> `docs/help-command-surface-map.md`, and `docs/audits/helper-debt-inventory.md`.
>
> **What this is:** the second half of the doc-only audit started by
> `docs/audits/helper-debt-inventory.md`. That inventory looked at *where*
> helpers live; this one looks at *whether the canonical UI
> primitives are being used*. Output is a prioritized backlog of
> small UI PRs.
>
> **What this is not:** a code-change PR. Items are recommendations;
> each gets its own follow-up PR.

---

## 1. Audit areas — adoption summary

| Area | Canonical primitive | Adoption | Status |
|---|---|---|---|
| Panel command dispatch | `views/base.py:send_panel` | 18 cogs, ~5 ad-hoc holdouts in one-off confirmation dialogs | **healthy** |
| Hub view base | `views/base.py:HubView` (extends `BaseView`) | 51 view files inherit `BaseView` / `HubView`; ~6 game-state views extend `discord.ui.View` directly with justified custom timeout | **healthy** |
| Back-button factory | `views/navigation.py:attach_back_button` | **complete** as of PR #297 — all 6 known wrappers (`games`, `community`, `cleanup`, `help`, `admin`, `settings`) now delegate to the canonical helper. See § 4 for the correction history. | clean |
| Interaction safety wrappers | `core/runtime/interaction_helpers.py:safe_defer/safe_edit/safe_followup` | 146 call sites across 14 files; ~60% of inspected I/O callbacks adopted, ~25% partial, ~15% bare | **drift** — see § 5 |
| Help-route panel class names | `cogs/help/route.py` + `docs/help-command-surface-map.md` § 2 | Structural routing correct; 4 panel class names in the surface map drifted from code | **fixed in this PR** — see § 6 |

The rest of this doc details the two drift areas not already covered
by `docs/audits/helper-debt-inventory.md`, and lists the prioritized
backlog.

---

## 2. What `helper-debt-inventory.md` already covered

`docs/audits/helper-debt-inventory.md` § 3 (views/navigation.py) is the
canonical reference for back-button duplication. The drift list there
is the same one referenced by this audit; do not split it.

`docs/audits/helper-debt-inventory.md` § 4 (views/base.py) confirmed:

- `BaseView` / `HubView` are uniformly adopted (51 view files).
- `send_panel` is used by 18 cogs; ~5 one-off `ctx.send(embed=…, view=…)`
  call sites remain in confirmation dialogs (acceptable per
  `docs/building-roadmap/hub-ui-standard.md`).
- `handle_view_error` is used by `BaseView` and by the blackjack
  views that extend `discord.ui.View` directly with custom lifecycle.

These three are not re-classified here.

---

## 3. `safe_defer` / `safe_edit` / `safe_followup` adoption

### 3.1 Canonical helpers

| Helper | Definition | Wraps |
|---|---|---|
| `safe_defer` | `disbot/core/runtime/interaction_helpers.py:65` | `interaction.response.defer(...)` inside the 3 s window; idempotent; swallows `NotFound` / `HTTPException`; returns `bool`. |
| `safe_followup` | `disbot/core/runtime/interaction_helpers.py:101` | Sends regardless of deferred state: `followup.send` if deferred else `response.send_message`. Returns `Message \| None`. |
| `safe_edit` | `disbot/core/runtime/interaction_helpers.py:150` | Edits the original message regardless of deferred state: `followup.edit_original_response` if deferred else `response.edit_message`. |

All three log at WARNING on token expiry or HTTP error and never raise.

### 3.2 Sampled adoption (15 callbacks across subsystems)

Sample classification (where "bare" = directly calls `interaction.response.*`
without a safe-* wrapper, and "partial" = mixed):

| File:line | Callback | Class |
|---|---|---|
| `views/economy/main_panel.py:58` | `daily_btn` | adopted |
| `views/economy/work_panel.py:86` | `_JobSelect.callback` | **bare** — heavy DB I/O precedes raw `response.edit_message` |
| `views/economy/work_panel.py:173` | `back_btn` | adopted |
| `views/economy/main_panel.py:218` | lazy-imports inventory cog symbols | (cross-package leak, tracked in helper-debt-inventory § 7) |
| `views/rps/solo_play.py:97` | `rock` callback | **partial** — raw `response.edit_message` after I/O |
| `views/rps/pvp_challenge.py:49` | `accept` | **bare** — async `game_state_service.save` after raw edit |
| `views/blackjack/pvp_view.py:47` | `accept` | **bare** — `_start_pvp` async work after raw edit |
| `views/blackjack/tournament_views.py:152` | `hit` | **partial** |
| `views/channels/delete_panel.py:97` | `delete_btn` | **bare** |
| `views/channels/restrict_panel.py:157` | `lock_btn` → `_apply_restriction` | **bare** — Discord permission write before raw edit |
| `views/channels/create_panel.py:98` | `create_btn` | adopted |
| `views/roles/management_panel.py:117` | `EditRoleModal.on_submit` | **partial** — `safe_defer` called *after* `role.edit()` (ordering inverted) |
| `views/mining/main_panel.py:68` | hub select callback | adopted |
| `views/xp/modals.py:237` | `_XpRangeModal.on_submit` | adopted |
| `views/moderation/main_panel.py:59` | `warn_btn` | **bare** (modal-send only — allowed; see § 3.4) |

Headline ratio (sample only): **~60% adopted / ~25% partial / ~15% bare.**
The full call-site count is 146 across 14 files; this sample is
intentionally subsystem-diverse.

### 3.3 Top drift hotspots

| Rank | Hotspot | Why it matters | Suggested fix |
|---|---|---|---|
| 1 | `views/economy/work_panel.py:86` `_JobSelect.callback` | Performs multiple DB reads + `economy_service.credit` + `xp_service.award` + `post_log_embed` before `response.edit_message`. Most exposed to 3 s token-expiry races. | `await safe_defer(interaction); …; await safe_edit(interaction, …)`. |
| 2 | `views/rps/pvp_challenge.py:49` `accept` / `decline`, `views/blackjack/pvp_view.py:47` `accept` | Edit before dispatching async game-state writes (`game_state_service.save`) and channel sends. Token may expire mid-dispatch. | Defer immediately; route the edit and any follow-up through `safe_edit` / `safe_followup`. |
| 3 | `views/channels/{delete,restrict}_panel.py` | Discord `set_permissions` / channel-delete API calls precede a raw `response.edit_message`. Permission writes are not instant. | Defer before the API call; edit after via `safe_edit`. |

### 3.4 Patterns that are correctly bare (not flagged)

- **Modal sends without prior defer.** Button callbacks whose only
  job is `await interaction.response.send_modal(...)` are fine; the
  modal protocol expects immediate ack.
- **Lightweight back-button edits.** Back buttons that rebuild an
  in-memory embed without DB I/O can use raw `response.edit_message`
  (still inside the 3 s window).
- **Validation-error replies in modals.** `interaction.response.send_message(ephemeral=True)`
  for a "your input was invalid" path is allowed before any I/O has
  happened.

### 3.5 Out-of-scope nuances flagged

- Several views implement custom `on_error` handlers that gate on
  `interaction.response.is_done()` (`views/channels/{delete,restrict}_panel.py:48-62`).
  These predate `handle_view_error`; standardising on
  `handle_view_error` + `safe_followup` would unify the recovery
  path, but it's a separate PR.

---

## 4. Back-button factory consolidation — referenced

See `docs/audits/helper-debt-inventory.md` § 3 for the full list. Summary:

| Location | Status (post-PR-#297) |
|---|---|
| `views/games/hub.py:212-245` `attach_back_to_games_button` | already migrated |
| `cogs/admin_cog.py:367-410` `attach_back_to_admin_button` | migrated in PR #297 |
| `views/settings/subsystem_view.py:244-277` `attach_back_to_settings_button` | migrated in PR #297 |
| `views/community/hub.py:189-214` `attach_back_to_community_button` | already migrated (original audit mis-classified) |
| `cogs/cleanup/panel.py:100-130` `_attach_back_to_cleanup_button` | already migrated (original audit mis-classified) |
| `cogs/help_cog.py:190-243` `_attach_back_to_help_button` | already migrated (original audit mis-classified) |

**Correction:** the original audit assumed every `attach_back_to_*`
factory was a hand-rolled duplicate without opening each source
file. Three (community, cleanup, help) were already wrappers around
`attach_back_button` with parent-builder closures. PR #297 closed
the two real duplicates (admin, settings). Phase 3.5 is now
complete; no further migration is queued for this area.

---

## 5. `send_panel` and `HubView` — referenced

See `docs/audits/helper-debt-inventory.md` § 4. Adoption is healthy:

- 18 cogs use `send_panel` for `!<sub>menu` / `!<sub>hub` commands.
- 51 view files inherit `BaseView` / `HubView`.
- Direct `discord.ui.View` extension is limited to game-state /
  tournament views with justified custom timeout (~6 files).

No new migration PRs needed for these areas. Future game-state views
that bypass `BaseView` should justify the bypass in their class
docstring.

---

## 6. Help-route corrections applied in this PR

`docs/help-command-surface-map.md` § 2 documented four panel class
names that drifted from the code. This PR corrects the doc; **no
code change is needed**. The Help system works regardless because
`cogs/help/route.py` calls the hook by method name
(`build_help_menu_view`), not by panel class name.

| Row | Doc said (was) | Code returns (is) | Verified at |
|---|---|---|---|
| `chain` | `ChainPanelView` | `_ChainMenuView` | `disbot/cogs/chain_cog.py:249` (instantiated inside `build_help_menu_view`) |
| `channel` | `ChannelPanelView` | `_ChannelManagerView` | `disbot/cogs/channel_cog.py:150` |
| `cleanup` | `CleanupHubView` | `CleanupPanelView` | `disbot/cogs/cleanup/panel.py:133` |
| `counting` | `CountingPanelView` | `_CountingHubView` | `disbot/cogs/counting_cog.py:134` |

`logging` row (`LoggingPanelView`) was suspected of drift but checked
clean — `disbot/cogs/logging/panel.py:49` matches the doc.

`tests/unit/docs/test_help_surface_map_doc.py` pins section headings,
hub keys, and subsystem keys, but does **not** pin panel class
names. A future small PR could add such a check (parse the panel
hook column, grep for the class) — out of scope here.

---

## 7. Prioritized follow-up backlog

Each row is an independent small PR. Order is roughly by
reward / risk, smallest first.

| # | PR | Scope | Estimate |
|---|---|---|---|
| 1 | **Pin panel class names in surface-map test** | Add a fifth assertion to `tests/unit/docs/test_help_surface_map_doc.py` that extracts the panel hook from each row and greps for the class definition. Catches the drift this PR just fixed. | XS |
| 2 | **Fix `views/economy/work_panel.py:86`** | Wrap `_JobSelect.callback` with `safe_defer` → `safe_edit`. Single-file change. | S |
| 3 | **Fix RPS / blackjack PvP accept callbacks** | `views/rps/pvp_challenge.py:49` and `views/blackjack/pvp_view.py:47`. Two-file change. | S |
| 4 | **Fix `channels/{delete,restrict}_panel.py`** | Add `safe_defer` before the Discord permission API call; route the edit through `safe_edit`. Two-file change. | S |
| 5 | ~~**Phase 3.5 back-button finish — public three**~~ | **Complete** as of PR #297 (admin + settings migrated; community / cleanup / help were already migrated and only mis-classified by this audit). |
| 6 | **Standardise view `on_error` paths** | Replace the custom `is_done()` ladders in `channels/{delete,restrict}_panel.py:48-62` (and any similar) with `handle_view_error` + `safe_followup`. | M |
| 7 | ~~**Phase 3.5 back-button finish — private two**~~ | **Withdrawn** — both private factories were already migrated before this audit was written; the audit mis-classified them. |

PR 1 is recommended **first**: it's a one-line test addition that
prevents the same drift from happening again. PR 2–4 are the
highest-impact behaviour fixes (real token-expiry race exposure).

---

## 8. What this audit does *not* do

- It does **not** change `views/*` or `cogs/*` code. All
  classifications are recommendations.
- It does **not** re-litigate `helper-policy.md` § 3 or the
  back-button duplication already documented in
  `helper-debt-inventory.md` — it references those documents.
- It does **not** propose new view primitives. The canonical
  primitives are already adequate; the gap is adoption uniformity.

---

## 9. Back-button coverage per view (Smooth Interaction Pass)

> **Added:** 2026-05-24. Companion to the original audit, focused on
> *per-view* coverage rather than per-helper duplication. PR #297
> finished the back-button **helper consolidation**; this section
> finishes the back-button **adoption** sweep — every user-facing
> subpanel either routes through `views/navigation.attach_back_button`
> or is explicitly classed as not needing one.

### 9.1 Classification

Each view file in `disbot/views/` is one of:

- **root-hub** — top-of-stack panel opened by `!<sub>menu`. No back
  button required; closing the panel is exit.
- **subpanel** — opened from a hub. Back required.
- **terminal-result** — game/result view where the user expects
  replay/back controls, not a normal parent back button. Tracked
  separately (PRs 6-7 in the Smooth Interaction Pass).
- **modal-only** — a `discord.ui.Modal` subclass; back navigation
  is impossible by Discord's modal contract.
- **game-state** — custom-timeout view with its own lifecycle
  (e.g. `BlackjackView`, `_TournBlackjackView`); excluded from
  standard back-button rules.
- **persistent-root** — `PersistentView` registered for cross-restart
  use; no parent.

Back-button status:

- **canonical** — uses `views/navigation.attach_back_button`.
- **hand-rolled** — has its own `@discord.ui.button(label="↩ Back" …)`
  that calls `interaction.response.edit_message` directly. Migrate.
- **none-needed** — root-hub / persistent-root / modal-only / leaf
  game-state.
- **missing** — should have a back path but doesn't. Add one.

### 9.2 Coverage table

| File | Class | Role | Back status | Parent surface | Priority |
|---|---|---|---|---|---|
| `views/economy/main_panel.py:288` | `EconomyPanelView` | root-hub | canonical (back-to-Help via `attach_back_button`) | Help | — |
| `views/economy/shop_panel.py:142` | `_ShopSubView` | subpanel | **hand-rolled** | `EconomyPanelView` | P1 (PR 4) |
| `views/economy/work_panel.py:182` | `_WorkSubView` | subpanel | **hand-rolled** | `EconomyPanelView` | P1 (PR 4) |
| `views/economy/work_panel.py:224` | `_WorkResultView` | subpanel | **hand-rolled** | `EconomyPanelView` | P1 (PR 4) |
| `views/channels/create_panel.py:224` | `_CreateSubView` | subpanel | **hand-rolled** | `_ChannelManagerView` | P1 (PR 4) |
| `views/channels/delete_panel.py:117` | `_DeleteSubView` | subpanel | **hand-rolled** | `_ChannelManagerView` | P1 (PR 4) |
| `views/channels/restrict_panel.py:191` | `_RestrictSubView` | subpanel | **hand-rolled** | `_ChannelManagerView` | P1 (PR 4) |
| `views/channels/visibility_panel.py:93` | `_VisibilitySubView` | subpanel | **hand-rolled** | `_ChannelManagerView` | P1 (PR 4) |
| `views/roles/reaction_panel.py:50` | `ReactionRolesPanel` | subpanel | **hand-rolled** | `RoleHubView` | P1 (PR 4) |
| `views/roles/management_panel.py:81` | `ManagementPanel` | subpanel | **hand-rolled** | `RoleHubView` | P1 (PR 4) |
| `views/roles/diagnostics_panel.py:79` | `DiagnosticsPanel` | subpanel | **hand-rolled** | `RoleHubView` | P1 (PR 4) |
| `views/roles/xp_roles_panel.py:79` | `XpRolesPanel` | subpanel | **hand-rolled** | `RoleHubView` | P1 (PR 4) |
| `views/roles/time_roles_panel.py:97` | `TimeRolesPanel` | subpanel | **hand-rolled** | `RoleHubView` | P1 (PR 4) |
| `views/xp/config_panel.py:22` | `XpConfigView` | subpanel | **missing** | `_XpHubView` | **P0 (PR 5)** |
| `views/counting/hub_panel.py:21` | `_CountingHubView` | root-hub¹ | none-needed (sub-hub opened only from Help) | Help | — |
| `views/setup/section_card.py:207` | `SectionCardView` back btn | subpanel | hand-rolled but custom (multi-step wizard with own lifecycle) | `SetupHubView` | P2 (PR 5 if simple) |
| `views/setup/ai_review/per_recommendation.py:186` | `PerRecommendationView` | subpanel | hand-rolled (one-at-a-time walker — keep custom) | overview view | — |
| `views/games/hub.py:237` | `GamesHubView` | root-hub | canonical | Help | — |
| `views/games/blackjack_panel.py:414` | `BlackjackPanelView` | subpanel | canonical (`BackToPanelButton` factory) | `GamesHubView` | — |
| `views/games/rps_panel.py` | `RPSPanelView` | subpanel | canonical (`BackToPanelButton` factory) | `GamesHubView` | — |
| `views/games/deathmatch_panel.py` | `DeathmatchPanelView` | subpanel | canonical | `GamesHubView` | — |
| `views/community/hub.py:189` | `CommunityHubView` | root-hub | canonical (back-to-Help) | Help | — |
| `views/settings/subsystem_view.py:244` | `SubsystemSettingsView` | subpanel | canonical | `SettingsHubView` | — |
| `views/mining/main_panel.py` | `MiningHubView` | persistent-root | none-needed | — | — |
| `views/mining/mine_view.py:176` | `_MineResultsView` | terminal-result | hand-rolled (game-flow multi-target) | game-state | — |
| `views/moderation/main_panel.py` | `ModPanelView` | persistent-root | none-needed | — | — |
| `views/diagnostic/platform_panel.py:239` | `_PlatformHubView` | root-hub | none-needed (Overview button is in-panel reset) | Help | — |
| `views/diagnostic/flag_manager.py` | `FlagManagerView` | subpanel | (verify in audit; opened by `!platform flag` and from Platform hub mutation button after PR 1) | `_PlatformHubView` | P2 (PR 5) |
| `views/rps/solo_play.py:24` | `_RpsView` | terminal-result | none currently — gains replay+back in PR 6 | `RPSPanelView` | P0 (PR 6) |
| `views/blackjack/solo_view.py:26` | `BlackjackView` | terminal-result | none currently — gains replay+back in PR 7 | `BlackjackPanelView` | P0 (PR 7) |
| `views/rps/pvp_play.py:27` | `_RpsPvpPlayView` | game-state | none-needed (PvP terminal) | — | — |
| `views/rps/pvp_challenge.py` | `_RpsPvpChallengeView` | game-state | none-needed (accept/decline modal-ish) | — | — |
| `views/blackjack/pvp_view.py` | `_ChallengeView` | game-state | none-needed | — | — |
| `views/blackjack/tournament_views.py` | `_TournBlackjackView` | game-state | none-needed | — | — |
| `views/access/explorer.py` | `AccessExplorerView` | root-hub | none-needed (top-level) | — | — |

¹ `_CountingHubView` is opened from the Help route and acts as the
top of its own sub-tree; it has no parent above Help. If a future
binding wires it under a wider community hub, add a back button at
that time.

### 9.3 Follow-up PRs driven by this section

| PR | Scope | Targets |
|---|---|---|
| PR 4 (Smooth Interaction Pass) | Migrate 12 hand-rolled subpanel back buttons to `attach_back_button` | channels (4) + roles (5) + economy (3) |
| PR 5 (Smooth Interaction Pass) | Add `attach_back_button` to the one **missing** subpanel; consider for setup `SectionCardView` and `FlagManagerView` after verifying parent surfaces | `XpConfigView` (P0); setup/flag (P2) |
| PR 6 (Smooth Interaction Pass) | RPS solo result view → `Play again` + `↩ Back to RPS menu` | `_RpsView` |
| PR 7 (Smooth Interaction Pass) | Blackjack solo result view → `Play again` + `↩ Back to Blackjack menu` | `BlackjackView` (solo gate only) |

### 9.4 Rules locked by this section

- **No new back-button helper.** `views/navigation.attach_back_button`
  is the only sanctioned entry point. PR 4-5 migrate to it; no
  parallel "back" abstraction may be introduced.
- **Parent-builder closures must re-resolve.** The wrapper that PR 4
  generates per file should call the parent hub's existing
  build-from-state path rather than caching a stale embed.
- **Terminal game-result views are excluded.** They follow PR 6-7's
  replay/back-to-menu pattern, not the standard subpanel back rule.
- **Modal `discord.ui.Modal` subclasses are excluded.** Discord's
  modal protocol allows no return path other than dismiss.
