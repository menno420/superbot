# Untested-surface testing checklist

> **Status:** `audit` — maintained live-walk checklist for every command/UI
> flow that automated tests **cannot** verify.
>
> **Companion to** [`production-eval-checklist-2026-06-10.md`](production-eval-checklist-2026-06-10.md)
> (the point-in-time eval for PRs #606–#672; this doc is the persistent successor).
>
> **Not duplicated here:** surfaces already verified in the production eval
> checklist or covered sufficiently by CI. See the
> [exclusion index](#what-is-not-here) at the bottom.
>
> **Owner:** update status badges (✅ / `[ ]`) as surfaces get walked; record
> the date and PR context beside each ✅ so drift is visible.

---

## Status legend

| Badge | Meaning |
|---|---|
| `[ ]` | Needs a live walk — never verified, or verification record lost |
| `[~]` | Partially tested (machine tests exist; UX / visual output unverified) |
| `[✅]` | Live-verified — date + evidence noted |
| `[⏳]` | Deferred / gated — reason noted |
| `[🤖]` | Machine-covered sufficiently; human walk not required |

---

## How to use this checklist

1. Pick a section.
2. Run each `[ ]` item in the real bot; tick it ✅ with a date.
3. Report findings as "**X should be Y / X is currently Z**" — each becomes a
   diagnosis target.
4. When a new feature ships, add its surface here **in the same PR** (treat it
   as part of done).

---

## § 1 — Economy & Inventory

> Machine coverage: `test_economy_log_channel_pipeline` tests the log-channel
> pipeline only; **the user-facing economy commands have no behavioral tests**.

### 1.1 Economy loop

- `[✅]` `!daily` — **Expect:** coins credited, cooldown message on repeat.
  **Report if:** no coins credited, or the cooldown doesn't reset after 24 h. `live walk 2026-06-14`
- `[✅]` `!work` — **Expect:** coins/XP from a "job" result; different jobs
  appear on repeat. **Report if:** always the same job, or zero reward. `live walk 2026-06-14`
- `[✅]` `!balance` (aliases: `!bal`, `!wallet`) — **Expect:** embed showing
  your coin count and inventory summary. Try `!balance @someone` too. `live walk 2026-06-13`
- `[✅]` `!shop` — **Expect:** the shop embed renders with prices; nothing
  changes until you actually buy. `live walk 2026-06-13`
- `[✅]` `!joblist` (alias: `!jobs`) — **Expect:** a readable list of available
  jobs with their XP/coin ranges. `live walk 2026-06-13`
- `[✅]` `!economymenu` — **Expect:** the Economy hub panel with navigation
  buttons to Daily, Work, Balance, Shop, etc. All buttons respond. `live walk 2026-06-13`

### 1.2 Inventory hub

- `[✅]` `!inventory` (alias: `!inv`) — **Expect:** a unified hub embed showing
  items grouped by type (mining ore, gear, consumables…). Navigation buttons
  for each category work. `live walk 2026-06-13`
- `[✅]` `!inventory @someone` — **Expect:** shows their inventory (read-only).
  **Report if:** errors on another user, or shows your own inventory. `live walk 2026-06-13`

---

## § 2 — General & Social

> Machine coverage: none. The general cog has had no behavioral tests written.

- `[✅]` `!fact` — **Expect:** a random interesting fact embed. Runs twice to
  confirm different facts appear. `live walk 2026-06-13`
- `[✅]` `!joke` — **Expect:** a joke (setup + punchline or one-liner). `live walk 2026-06-13`
- `[✅]` `!quote` — **Expect:** a famous quote with attribution. `live walk 2026-06-13`
- `[✅]` `!motivate` — **Expect:** a motivational message. `live walk 2026-06-13`
- `[✅]` `!greet` — **Expect:** a random greeting directed at you. `live walk 2026-06-13`
- `[✅]` `!trivia` — **Expect:** a trivia question with interactive answer 
  buttons; correct answer is revealed; score/result shown. `live walk 2026-06-13`
- `[✅]` `!eightball <question>` — **Expect:** a magic-8-ball style response.
  E.g. `!eightball will I win today?` `live walk 2026-06-13`
- `[✅]` `!generalmenu` (the hub entry point) — **Expect:** the General hub panel
  with buttons for each command above; each button opens the corresponding
  flow inline. `live walk 2026-06-13`

---

## § 3 — Utility

> Machine coverage: none for command behavior. UI panel classes are not tested.

- `[✅]` `!utilitymenu` — **Expect:** the Utility hub with buttons for Info,
  Clear, Poll, Remind, Invite. `live walk 2026-06-13`
- `[~]` `!info` (default: server) — **Expect:** server info embed (member
  count, region, channels, owner). `!info user` / `!info @someone` shows
  user profile. `2026-06-13`
- `[✅]` `!clear 5` — **Expect:** deletes the last 5 messages in the channel
  (requires Manage Messages). **Report if:** it deletes more or fewer, or
  errors without permission. `live walk 2026-06-13`
- `[✅]` `!poll "question" "A" "B" "C"` — **Expect:** a poll embed with
  reaction/button options for A, B, C. Results update on vote. `live walk 2026-06-13`
- `[✅]` `!remind 1 test message` — **Expect:** a confirmation, then a DM (or
  channel mention) after 1 minute. **Report if:** the reminder never fires. `live walk 2026-06-13`
- `[✅]` `!invite` — **Expect:** a bot-invite link embed. **Report if:** the
  URL is broken or missing. `live walk 2026-06-13`

---

## § 4 — Roles & Reaction Roles

> Machine coverage: `test_role_cog_routing.py` tests routing logic only;
> the full panel flow and role-assignment behavior are unverified.

### 4.1 Role hub

- `[✅]` `!roles` — **Expect:** the Roles hub panel with buttons: Create · Manage ·
  Time Roles · XP Roles · Reaction · Diagnostics · Exemptions. `live walk 2026-06-14`
- `[✅]` `!rolesettings` — **Expect:** the role settings panel (XP thresholds,
  auto-assign rules). `live walk 2026-06-14`
- `[✅]` `!rolemenu` — **Expect:** the full role management panel. `live walk 2026-06-14`
- `[✅]` `!rolecreator` — **Expect:** a role-creation flow (guided or modal). `live walk 2026-06-14`

### 4.2 Reaction roles

- `[✅]` `!reactroles message_id :emoji: @Role` — **Expect:** a
  reaction-role message posted in the named channel; reacting adds the role;
  removing the reaction removes it. `live walk 2026-06-14`
- `[✅]` `!listreactroles` — **Expect:** a list of all configured reaction-role
  entries for this guild. `live walk 2026-06-14`
- `[✅]` `!removereactrole <message_id> :emoji:` — **Expect:** the binding is
  removed; the role is no longer assigned by that reaction. `live walk 2026-06-14`

### 4.3 XP-gated and time-gated roles

- `[✅]` Confirm that roles auto-assign at the configured XP thresholds (check
  `!rolesettings` for the thresholds; award XP manually via `!givexp` and
  watch the member's roles). **Roles the task loop assigns may have a < 10-min
  delay** — note the lag, not a bug unless it never fires. `live walk 2026-06-14`
- `[✅]` Confirm time-gated roles assign after the configured membership duration
  (hard to verify in a short session; just confirm the task loop is registered
  and `!diagnostics` reports it running). `live walk 2026-06-14`

---

## § 5 — XP System

> Machine coverage: `test_xp_cog_admin_routes`, `test_xp_cog_caching`,
> `test_xp_listener_roles`, `test_xp_participation_gate` — internal behavior
> tested; **embed quality and rank-card image unverified**.

- `[✅]` `!rank` — **Expect:** a rank card (PIL image or embed fallback) showing
  your XP, level, and server rank. Judge the image quality — this is the most
  visible XP output. `live walk 2026-06-14`
- `[✅]` `!rank @someone` — **Expect:** their rank card. `live walk 2026-06-14`
- `[✅]` `!xpmenu` — **Expect:** the XP hub panel. `live walk 2026-06-14`
- `[✅]` `!givexp @someone 100` (admin) — **Expect:** XP credited, rank card
  reflects the change. `live walk 2026-06-14`
- `[✅]` `!resetxp @someone` (admin) — **Expect:** XP reset; confirm it zeroes
  correctly, including leaderboard position. `live walk 2026-06-14`
- `[✅]` `!xpconfig` — **Expect:** the XP configuration panel (rate, exclusions,
  etc.) renders with current values. `live walk 2026-06-14`
- `[✅]` Level-up announcement: send several messages to trigger a level-up;
  **Expect:** a level-up announcement in the configured channel (or DM). Pairs
  with Community Spotlight (already verified in production eval Tier 5). `live walk 2026-06-14`

---

## § 6 — Moderation

> Machine coverage: `test_moderation_panel_embed`, `test_moderation_role_authority`,
> `test_moderation_schemas` — embed/schema tests only; **command execution
> (warn/timeout/kick/ban) has never been live-tested**.
>
> ⚠️ Moderation commands are irreversible on real members — use a test account
> or a dedicated test server.

- `[ ]` `!modmenu` — **Expect:** the Moderation hub panel with action buttons.
  Slash `/moderation` also opens it.
- `[ ]` `!warn @testuser reason text` — **Expect:** a warning embed sent to
  the channel + logged; `!modlogs @testuser` should list it.
- `[ ]` `!modlogs @testuser` — **Expect:** a list of all mod actions against
  the user (warnings, timeouts, kicks, bans).
- `[ ]` `!clearwarnings @testuser` — **Expect:** their warning count resets;
  `!modlogs` confirms the clear.
- `[ ]` `!timeout @testuser 5` — **Expect:** member timed out for 5 minutes;
  Discord's native timeout UI confirms it. Expires after 5 min.
- `[ ]` `!kick @testuser reason` — **Expect:** member removed from server,
  audit log entry, log-channel message. **(Use a test account.)**
- `[ ]` `!ban @testuser reason` then `!unban <user_id>` — **Expect:** ban
  recorded, member cannot rejoin; unban reinstates. **(Use a test account.)**

---

## § 7 — Channel Management

> Machine coverage: `test_channel_list_paginate` — pagination only; channel
> mutations are untested.

- `[ ]` `!lock #channel-name` — **Expect:** the channel goes read-only for
  regular members; a "locked" message appears.
- `[ ]` `!unlock #channel-name` — **Expect:** permissions restored; confirm
  members can post again.
- `[ ]` Channel list commands (the channel management panel) — navigate to
  channel list; pagination works past 25 channels if the server has them.
- `[ ]` Channel-creation/deletion flows (if exposed via `!channel` subcommands)
  — create a throwaway channel, then delete it.

---

## § 8 — Word Filter (Cleanup subsystem)

> Machine coverage: `test_cleanup_history`, `test_cleanup_panel`,
> `test_cleanup_stage` — internal stage tests; **`!word` commands and the
> live filter behavior are unverified**.

- `[ ]` `!wordmenu` — **Expect:** the Word Filter hub panel.
- `[ ]` `!word add <phrase>` — **Expect:** phrase added to the filter;
  posting the phrase in the filtered channel triggers deletion + log.
- `[ ]` `!word remove <phrase>` — **Expect:** phrase removed; posting it no
  longer triggers the filter.
- `[ ]` `!word list` — **Expect:** all active filtered phrases listed.
- `[ ]` `!cleanup` — **Expect:** the cleanup-config panel renders with current
  auto-delete rules.
- `[ ]` `!cleanuphistory` — **Expect:** recent cleanup log (deletions).

---

## § 9 — Counting Game

> Machine coverage: `test_counting_handler`, `test_counting_modes`,
> `test_counting_parsing`, `test_counting_persistence`, `test_counting_stage` —
> extensive internal tests; **the live panel flow and multi-player session
> have never been walked**.

- `[ ]` `!countingmenu` (alias `!cm`) — **Expect:** the Counting hub panel.
- `[ ]` `!start_match` — **Expect:** a counting game starts in the channel;
  players can join/begin.
- `[ ]` `!count_info` — **Expect:** current game state (count, who's next,
  mode settings).
- `[ ]` `!count_rules` — **Expect:** the counting rules for this game embed.
- `[ ]` `!toggle_turns` — **Expect:** turn-based mode toggled; confirmation
  message.
- `[ ]` `!toggle_reset_on_wrong_count` — **Expect:** wrong-number reset
  behavior toggled; confirm the setting persists.
- `[ ]` `!set_skip_numbers 13 17` — **Expect:** those numbers are skipped in
  the count; the next player auto-advances past them.
- `[ ]` `!reset_count` — **Expect:** count resets to 0; current session data
  cleared.
- `[ ]` `!end_match` — **Expect:** game ended cleanly; results/stats shown.

---

## § 10 — Admin & Operator

> Machine coverage: `test_admin_cog_manager`, `test_admin_menu_integration`,
> `test_admin_restart`, `test_admin_slash_sync` — some tests exist; **most
> operator commands have never been run in a live bot session**.

- `[✅]` `!adminmenu` — **Expect:** the Admin hub panel (admin-tier only).
  Slash `/admin` also opens it. `live walk 2026-06-14`
- `[✅]` `!serverstats` — **Expect:** a server statistics embed (guild count,
  member total, uptime, etc.). `live walk 2026-06-14`
- `[✅]` `!cog list` — **Expect:** list of loaded/available cogs and their
  status. `live walk 2026-06-14`
- `[ ]` `!syncslash` (alias `!syncs`) — **Expect:** slash commands synced to
  Discord; count of synced commands printed. **Do not run frequently — Discord
  rate-limits global slash syncs.**
- `[✅]` `!slashes` — **Expect:** a list of all registered slash commands. `live walk 2026-06-14`
- `[✅]` `!restart` — **Expect:** bot sends a "restarting" message, goes 
  offline, comes back (exit-42 contract, PR #675 + the new 429-backoff, PR 
  #729). **Already in production eval Step 0 — re-verify if in doubt.** `live walk 2026-06-14`
- `[✅]` `!loglevel DEBUG` / `!loglevel INFO` — **Expect:** log level changes
  live without restart; subsequent log output reflects the new level. `live walk 2026-06-14`

---

## § 11 — Diagnostic commands

> Machine coverage: `test_diagnostic_consistency_embed`, `test_diagnostic_panels_data`,
> `test_platform_flags_embed`, `test_platform_health_embed`,
> `test_platform_setting_detail` — embed/data tests; **live command rendering
> and multi-section navigation unverified**.

- `[✅]` `!diagnostics` (or `!platform`) — **Expect:** multi-section platform
  health embed; navigation between sections works. **Already partially in
  production eval Tier 5 as `!platform consistency`.**
- `[✅]` `!diagnostic_bot_status` — **Expect:** internal runtime status
  (lifecycle phase, lock, Postgres pool stats).
- `[✅]` `!recent_errors` — **Expect:** a list of recent error events from the
  lifecycle buffer; empty is fine if no errors occurred.
- `[✅]` `!query_logs` — **Expect:** a log-query interface or recent structured
  log entries.

---

## § 12 — Logging Panel

> Machine coverage: `test_logging_binding_select`, `test_logging_panel`,
> `test_logging_provision_channel`, `test_logging_routes_panel`,
> `test_logging_schemas` — good schema/panel coverage; **end-to-end live
> write (bind a channel → receive a log event) unverified**.

- `[ ]` `!logging` — **Expect:** the Logging panel with current channel
  bindings and event-type toggles.
- `[ ]` Bind a log channel (Settings → Logging or via the panel) → perform
  a moderation action → **Expect:** the action appears in the bound log
  channel within seconds.
- `[ ]` Toggle a log event type off → perform the action → **Expect:** no log
  entry for that type.

---

## § 13 — BTD6 Reference, Strategy & Paragon

> Machine coverage: many `test_btd6_*` tests cover the core BTD6 cog;
> **`btd6ref`, `btd6strat`, and `paragon` are not directly tested**.

### 13.1 BTD6 reference (`!btd6ref`)

- `[✅]` `!btd6ref tower dart monkey` — **Expect:** tower stats embed for
  the Dart Monkey. `live walk 2026-06-14`
- `[✅]` `!btd6ref hero geraldo` — **Expect:** Geraldo hero stats/abilities. `live walk 2026-06-14`
- `[✅]` `!btd6ref round 63` — **Expect:** round 63 composition / bloon info. `live walk 2026-06-14`
- `[✅]` `!btd6ref relic <relic name>` — **Expect:** a Contested Territory
  relic description.
- `[✅]` `!btd6ref ct` — **Expect:** current CT season info or relic browser. `live walk 2026-06-14`
- `[ ]` Slash equivalents (`/btd6_tower`, `/btd6_hero`, `/btd6_round`,
  `/btd6_relic`, `/btd6_ct`) — **Expect:** same embeds via slash; ephemeral
  if applicable.

### 13.2 BTD6 strategy (`!btd6strat`)

- `[ ]` `!btd6strat browse` — **Expect:** a paginated list of community
  strategies.
- `[ ]` `!btd6strat mine` — **Expect:** your own submitted strategies.
- `[ ]` `!btd6strat submit` — **Expect:** a modal or guided flow to submit a
  new strategy.
- `[ ]` `!btd6strat strategies` — **Expect:** the strategies browser.
- `[ ]` Strategy moderation (admin): `!btd6strat pending` / `!btd6strat audit`
  — **Expect:** a list of pending strategy submissions for approval.

### 13.3 Paragon calculator

- `[ ]` `!paragon` — **Expect:** the Paragon degree calculator panel —
  interactive inputs for Pop count/Cash spent/abilities; degree updates live.
  Judge the UX: is the calculator usable and the output readable?

---

## § 14 — Deathmatch

> Machine coverage: `test_deathmatch_bot_duel`, `test_deathmatch_combat_stats`,
> `test_deathmatch_gear_wear`, `test_deathmatch_guild_scope` — internal combat
> math tested; **the interactive duel flow requires two participants**.

- `[ ]` `!dm @someone 50` — **Expect:** a duel challenge sent to the target;
  they accept via a button; combat rounds play out; winner declared; coins
  transfer.
- `[ ]` Gear wear: check 🧰 Gear before and after a duel — **Expect:**
  equipped combat items lost durability (Q-0054, PR #665).
- `[ ]` Duel with **no gear equipped** — **Expect:** still works; no crash on
  empty gear slot.
- `[ ]` Bot-duel shortcut (`!rpsbot` or `!dmbot` if it exists) — lets you
  duel the bot without a second person.

---

## § 15 — Community, Games, and 420 entry points

These are navigation hubs; their child surfaces are tested elsewhere.

- `[ ]` `!community` (or `/community`) — **Expect:** the Community hub panel
  with XP board, Spotlight, and community activity buttons. All sub-buttons
  navigate correctly.
- `[ ]` `!games` (or `/games`) — **Expect:** the Games hub panel (RPS, Blackjack,
  Counting, Deathmatch). Navigation to each works. **RPS and Blackjack already
  in production eval Tier 5.**
- `[ ]` `!420` (aliases: `!fourtwenty`, `!fourtwenty420`) — **Expect:** the
  420 panel opens with "rotating wisdom and number trivia"; panel buttons
  respond.

---

## § 16 — Server Management subpanels (beyond Tier 4 eval)

> Production eval Tier 4.3 walked the top-level hub; the sub-panels inside
> it have not been individually verified.

- `[ ]` **🛡️ Moderation** subpanel — opens, renders current warn-threshold /
  mute-role settings.
- `[ ]` **📺 Channels** subpanel — channel list, create/delete flows.
- `[ ]` **🎭 Roles** subpanel — delegates to the Roles hub (§4 above).
- `[ ]` **🧹 Cleanup** subpanel — delegates to the Cleanup panel (§8 above).
- `[ ]` **🧩 Setup** subpanel — opens the Setup wizard or its settings-entry
  view; confirm it doesn't re-run a completed wizard from scratch.

---

## § 17 — Bootstrap / Access Management

> Machine coverage: `test_bootstrap_access_cog.py`,
> `test_bootstrap_access_reload.py` — bootstrap guard tests; **the actual
> access-grant flow for a new server is never live-tested post-setup**.

- `[ ]` Confirm the bootstrap cog **does not** expose a button or command to
  regular members (it should be invisible until an owner-tier principal is
  detected at boot).
- `[ ]` After a fresh server join: the onboarding flow initiates cleanly
  (Setup wizard starts or an appropriate prompt appears).
- `[ ]` Access Map (`!servermanagement` → **🔓 Access Map**) — already in
  production eval Tier 4.3; confirm the access tier simulation still works
  as of the most recent deploy.

---

## § 18 — Durable regression sweep (run every ~4-6 weeks)

Short checks that confirm nothing regressed in always-on infrastructure.

- `[ ]` `!platform consistency` — **Expect:** CLEAN (or only known-triaged
  findings from `architecture_rules/`).
- `[ ]` `!help` as a regular member — **Expect:** governance filtering applies;
  hidden subsystems absent.
- `[ ]` `!spotlight` / `!activity` — **Expect:** Community Spotlight renders;
  member count sane.
- `[ ]` `!leaderboard xp` / `!leaderboard coins` / `!leaderboard mining` —
  **Expect:** boards render with your activity; no empty-state errors.
- `[ ]` `!btd6 status` — **Expect:** version 55.1, no ⚠️ Data drift flag.
- `[ ]` `!btd6 diagnostics` — **Expect:** sends cleanly (< message size limit).
- `[ ]` `!settings` — **Expect:** ~12 actionable groups, no empty pages.

---

## What is NOT here (excluded surfaces)

These are sufficiently covered by automated CI or the existing production eval checklist:

| Surface | Coverage |
|---|---|
| Mining commands (§2 of eval checklist) | `tests/unit/cogs/mining/` (8 files) + eval checklist §2 |
| BTD6 AI/grounding (§1, §3 of eval checklist) | `tests/unit/cogs/btd6/` + `tests/unit/runtime/ai/` + eval checklist |
| Chain commands (eval checklist §4.4) | `test_chain_cog_prefix.py`, `test_chain_stage.py` + eval checklist |
| Help render paths (eval checklist §4.5) | `test_help_render_paths.py`, `test_help_schemas.py` + eval checklist |
| Settings hub (eval checklist §4.1) | `test_settings_cog.py` + eval checklist |
| Proof channel (eval checklist §4.2) | `test_proof_channel_schema.py` + eval checklist |
| AI cog (eval checklist §1) | `tests/unit/cogs/ai/` (5 files) + eval checklist |
| RPS tournament (eval checklist Tier 5) | `test_rps_*.py` (4 files) + eval checklist |
| Blackjack (eval checklist Tier 5) | `test_blackjack_*.py` (3 files) + eval checklist |
| Server management hub entry (eval checklist §4.3) | eval checklist (top-level only) |
| `!restart` exit contract | PR #675 fix + `test_restart_exit_code.py` + eval Step 0 |
| Community Spotlight (eval checklist Tier 5) | `test_community_spotlight_cog.py` + eval checklist |

---

## Maintenance instructions

- **When a feature ships:** add its test surface to the relevant section with
  `[ ]` status in the same PR. Never let a surface ship without an entry here.
- **When a surface is walked:** update its badge to ✅ with `(date, PR #NNN or
  "live walk YYYY-MM-DD")`.
- **When a surface is removed:** delete its entry and note the removal at the
  bottom of its section.
- **When this doc drifts from source:** source wins. Verify live before trusting
  a ✅ that is more than 3 months old.
