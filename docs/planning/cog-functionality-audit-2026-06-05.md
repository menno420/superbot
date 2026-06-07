# Cog-by-Cog Functionality Audit — 2026-06-05

> **Status:** `audit` — live working document. This is the session tracker for a structured,
> cog-by-cog walkthrough of **every** command (prefix + slash) and command panel,
> assigning each cog a current status. Built against a **live test bot**
> (`Galaxy Bot#6724`) booted in the cloud container on a **fresh local Postgres**
> (56 migrations, 68 tables). Updated as we test each surface.
>
> **How to use:** for each cog we run the chat commands and open the panels in the
> private test server, watch the live logs, cross-check the source, and set a status.
> Fill the **Status** + **Notes** as we go. Source is authoritative over this doc.

---

## Environment caveats — features that are *intentionally* degraded here

The container is **not** a full production environment. Several features are gated
behind env vars / API keys that are not set here. When one of these "doesn't work,"
that is the environment, **not a bug** — flag it `⏸️ env-gated`, don't call it broken.

| Env var (this container) | State | What is degraded |
|---|---|---|
| `AI_ENABLED` | **unset → off** | The whole AI platform runs in deterministic/disabled mode. `AICog` chat answers, AI setup-advisor suggestions, BTD6 AI strategy generation/grounding → no real LLM calls. |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | **empty** | No LLM provider available even if a task is toggled on; factory falls back to `deterministic`. |
| `SETUP_ADVISOR_PROVIDER` | `deterministic` | Setup advisor uses name-matching rules only (no AI recommendations). |
| `AUTOMATION_SCHEDULER_ENABLED` | **`false`** | The background **time/XP role auto-assignment loop is not spawned**. Manual triggers (`!assignroles`, panel "▶️ Run Now") still work. |
| `YOUTUBE_API_KEY` | **unset** | YouTube context / video-reference lookups (BTD6 strategy sourcing) degraded/off. |
| `PARAGON_API_KEY` (+ `PARAGON_API_BASE_URL`) | key empty, public URL default | Paragon calculator calls the public API **if outbound is reachable**, else falls back to a labelled local estimate. |
| `BTD6_DATA_BACKEND` | **unset → `file`** | BTD6 data served from committed files under `disbot/data/btd6/`. `postgres`/`cloud` backends inactive. |
| `DISCORD_WEBHOOK_URL` | **unset** | Webhook startup/log mirroring disabled (cosmetic; no user-facing command). |

**Server logging** is not env-gated but ships **OFF per guild by default** (audit/mod
log embeds won't post to a channel until enabled via `!settings` / `!logging`).

### Command access — fail-open on this fresh DB ✅
`resolve_command_access` returns **`ALL_CHANNELS` / `DEFAULT_UNCONFIGURED`** when a
guild has no policy row (`command_access.py:367`). The fresh local DB has no policy
for the test guild, so **every command is allowed in every channel** — nothing is
silently blocked by the access gate. Owner-gating uses `bot.is_owner` (the Discord
application owner = you), so owner-only commands work. Only AI's owner-personalization
keys off the hardcoded `config.BOT_OWNER_USER_ID` (and AI is off anyway).

---

## Status legend

| Symbol | Meaning |
|---|---|
| ✅ | **finished** — works as intended, complete |
| 🟡 | **unfinished / wart** — works but has UX gaps, stubs, or partial coverage |
| 🔴 | **broken** — errors, no-ops, or wrong behavior |
| ⏸️ | **env-gated** — cannot be fully verified in this container (needs a key/flag) |
| ❓ | **untested** — not yet walked through |

---

## Master progress table

> 34 cogs loaded at boot. `BootstrapAccessCog` is infrastructure (the command-access
> guard) and has no user commands. Counts are prefix / slash from the live registry.
>
> **Reconciliation (2026-06-05, post-#528):** statuses for cogs whose hard failures
> already shipped fixes are corrected from source — **DiagnosticCog** `🔴`→`🟡` (its
> Recent-Errors, schema-check, and oversized-embed failures were fixed in #528 `702cf48`,
> test-pinned; dense `platform_*` subviews remain a pagination follow-up) and **RoleCog**
> `🔴→✅`→`🟡` (the two discord.py-2.7 crashes were fixed in #528; the two UX warts remain).
> Live re-confirmation of these + the remaining `❓` cogs is the ongoing PR B walk.
>
> **Cross-cutting findings (live walk, this session) — UX track, beyond PR B's hard-failure remit:**
> 1. **Hub "↩ Back to Help" missing on direct invoke.** Subsystem hubs opened via their
>    own command (`!modmenu`, `!economymenu`, `!rolemenu`, `!minemenu`, the Blackjack menu, …)
>    render the bare view through `panel_manager.get_or_render_panel` and never attach the
>    `cogs/help_cog.py:_attach_back_to_help_button` that the `!help` route already adds — so a
>    directly-invoked hub has no way back. **Systemic; candidate for one central fix** in the
>    direct-invoke render path rather than ~20 per-cog edits.
> 2. **Moderation member entry is free-text, not a picker** (see ModerationCog) — wants a
>    `discord.ui.UserSelect` quicksearch across all actions; needs a flow restructure
>    (modals can't hold a Select). `unban` stays ID-based.
> 3. **Back nav also breaks *within* hubs.** Economy loses its back/help button as you
>    descend its sub-panels (a sub-view doesn't re-propagate the `BackTarget`), and the
>    Wallet sub-view's "Back to Economy" button is **disabled** (concrete bug). Same class
>    as #1 — back-nav attachment/propagation is inconsistent across the view tree.
>
> ⇒ Findings #1 and #3 are one **back-navigation consistency** class — **FIXED this
> session** (live-confirmed) by a holistic, layer-clean change at the shared seam:
> `get_or_render_panel` now calls a registered back-to-help hook (wired from `bot1`'s
> composition root), so every directly-invoked hub gets "↩ Back to Help" + a seeded
> `_back_target`; the Economy Work sub-views now `chain_back` the grandparent so the chain
> survives `Economy → Work → Back`. Verified on `!modmenu`, `!economymenu`, and the Work
> path. The Wallet "disabled back" (part of #3) was **not reproducible** and is dropped.
> **Item #2 (moderation member-selector / `UserSelect` quicksearch) remains open** — a
> feature for the moderation-UX track, needs a modal→view flow restructure.

### Core · Admin · Config
| Cog | Panel / hub | prefix | slash | Env-gate | Status |
|---|---|---:|---:|---|:--:|
| BootstrapAccessCog | — (infra guard) | 0 | 0 | — | ✅ infra |
| AdminCog | `!adminmenu` | 9 | 1 | — | ❓ |
| DiagnosticCog | `!platform` | 43 | 1 | — | 🟡 |
| SettingsCog | `!settings` | 2 | 1 | — | ❓ |
| SetupCog | `!setup` / `setup-hub` | 1 | 9 | advisor=deterministic | ❓ |
| LoggingCog | `!logging` | 6 | 0 | webhook off; logging OFF by default | ❓ |
| HelpCog | `!help` | 1 | 0 | — | ❓ |

### Server management
| Cog | Panel / hub | prefix | slash | Env-gate | Status |
|---|---|---:|---:|---|:--:|
| RoleCog | `!rolemenu` / `!roles` | 14 | 0 | automation scheduler off | 🟡 |
| ChannelCog | `!channelmenu` | 15 | 0 | — | ❓ |
| ModerationCog | `!modmenu` | 8 | 1 | logging dest off by default | 🟡 |
| Cleanup | `!wordmenu` | 7 | 0 | — | ❓ |
| CommunityCog | `!community` | 1 | 1 | — | ❓ |

### Economy · Progression
| Cog | Panel / hub | prefix | slash | Env-gate | Status |
|---|---|---:|---:|---|:--:|
| EconomyCog | `!economymenu` | 7 | 1 | — | ❓ |
| XpCog | `!xpmenu` | 5 | 0 | automation scheduler off | ❓ |
| InventoryCog | `!inventory` | 1 | 0 | — | ❓ |
| MiningCog | `!minemenu` | 12 | 0 | — | ❓ |
| Leaderboard | `!leaderboard` | 1 | 0 | — | ❓ |

### Games · Social
| Cog | Panel / hub | prefix | slash | Env-gate | Status |
|---|---|---:|---:|---|:--:|
| BlackjackCog | `!blackjack` / `!bjstart` | 4 | 0 | — | ❓ |
| Rock Paper Scissors | `!rps` / `!rpsstart` | 7 | 0 | — | ❓ |
| Deathmatch | `!dm_challenge` | 2 | 0 | — | ❓ |
| GamesCog | `!games` | 1 | 1 | — | ❓ |
| CountingCog | `!countingmenu` | 9 | 0 | — | ❓ |
| ChainCog | `!chainmenu` | 7 | 0 | — | ❓ |
| FourTwentyCog | `!420` | 1 | 0 | — | ❓ |
| ProofChannelCog | `!prizemenu` | 5 | 0 | — | ❓ |

### BTD6 suite
| Cog | Panel / hub | prefix | slash | Env-gate | Status |
|---|---|---:|---:|---|:--:|
| BTD6Cog | `!btd6menu` | 7 | 1 | data=file; AI off | ❓ |
| BTD6ReferenceCog | `!btd6ref …` | 6 | 0 | data=file | ❓ |
| BTD6EventsCog | `!btd6events …` | 9 | 0 | live sources need outbound | ❓ |
| BTD6StrategyCog | `!btd6strat …` | 9 | 0 | AI off; YouTube off | ❓ |
| BTD6OpsCog | `!btd6ops …` | 7 | 0 | data backends/ingestion | ❓ |
| ParagonCog | `!paragon` | 1 | 0 | Paragon API (outbound) | ❓ |

### AI · General · Utility
| Cog | Panel / hub | prefix | slash | Env-gate | Status |
|---|---|---:|---:|---|:--:|
| AICog | `!aimenu` | 12 | 1 | **AI_ENABLED off** | ⏸️ |
| General | `!generalmenu` | 8 | 0 | — | ❓ |
| UtilityCog | `!utilitymenu` | 9 | 1 | — | ❓ |

---

## Per-cog detail (seeded inventory — fill Status/Notes as we test)

### RoleCog — 🟡 unfinished (two known warts)
- **Panels:** `!rolemenu` (hub) · `!roles` · `!rolecreator` · `!rolesettings`
- **Prefix (14):** assignroles, createrole, debugroles, deleterole, listreactroles,
  reactroles, refreshmembers, removereactrole, rolecreator, rolemenu, roles,
  rolesettings, setrole, unsetrole
- **Env:** `AUTOMATION_SCHEDULER_ENABLED=false` → time/XP auto-assign loop inactive
  here; `!assignroles` / panel "▶️ Run Now" trigger it manually.
- **Known findings (prev session, verified in source):**
  1. Time/XP role panels list **phantom stale rows** (`Neu/Iron/Beacon…` whose role
     no longer resolves). They're flagged `⚠️ role missing` but can only be removed
     one-at-a-time — **no bulk "Clear missing"** (`time_roles_panel.py` /
     `xp_roles_panel.py`).
  2. **Edit Role** uses a **free-text role-name** TextInput + `_find_role_normalized`
     instead of a selector — inconsistent with Delete (which is selector-driven) and
     with PR6's pick-then-modal pattern (`management_panel.py:EditRoleModal`).
  - The "panel can no longer be verified" message is **by design** (fail-closed on a
    stale post-redeploy anchor; ADR-004/RC-3) — re-run `!roles`. Not a bug.
- **Status:** 🟡 — core works; the two warts above are the candidate fix.
- **Notes:** _…_

### ChannelCog — ❓
- **Panel:** `!channelmenu` (hub → list / create / move-reorder / etc.)
- **Prefix (15):** bulkcreate, bulkdelete, channelinfo, channelmenu, clone, create,
  del, evt, list, lock, move, permissions, rename, set, unlock
- **Notes:** rename/move/delete/reorder route through `ChannelLifecycleService`
  (PR3/4/7). create/clone/lock/permissions still on cog paths.
- **Status:** ❓ · **Notes:** _…_

### ModerationCog — ❓
- **Panel:** `!modmenu`
- **Prefix (8):** ban, clearwarnings, kick, modlogs, modmenu, timeout, unban, warn · **slash:** moderation
- **Notes:** all manual actions route through `moderation_service` (PR1). Audit/mod
  log embeds need a logging destination configured to appear in a channel.
- **Finding (live, this session):** every action modal takes the target via a free-text
  `TextInput` ("User (mention, ID, or name)") + `_parse_member` — the outdated method.
  Maintainer wants a **selectable member list with quicksearch** (`discord.ui.UserSelect`)
  across all actions. NB: a Discord **modal cannot contain a Select**, so this is a flow
  restructure (pick member in a view → reason/duration follow-up), not a component swap;
  `unban` stays ID-based (banned users aren't guild members). Scope = moderation-UX track.
- **Status:** 🟡 — actions work + route through `moderation_service`; member entry is the
  UX gap above.

### Cleanup — ❓
- **Panel:** `!wordmenu` · **Prefix (7):** cleanup, cleanuphistory, word, word add,
  word list, word remove, wordmenu
- **Status:** ❓ · **Notes:** _…_

### CommunityCog — ❓
- **Entry:** `!community` (prefix + slash)
- **Status:** ❓ · **Notes:** _…_

### AdminCog — ❓
- **Panel:** `!adminmenu` · **Prefix (9):** adminmenu, cog, loadall, loglevel,
  restart, serverstats, slashes, syncslash, unloadall · **slash:** admin
- **Notes:** `restart`/`loadall`/`unloadall`/`cog` are owner-gated (`bot.is_owner`).
  `restart` here will kill the container process — test last / with care.
- **Status:** ❓ · **Notes:** _…_

### DiagnosticCog — 🟡 (hard failures fixed in #528; live re-confirm pending)
- **Hub:** `!platform` (33 subcommands) · **Prefix (43):** check_database,
  diagnostics, find_command, latency, lifecycle, list_commands_detailed, platform (+
  access, anchors, automation, bindings, caches, cleanup-preview, command-access,
  consistency, counting-health, customization, flag, flags, identity, lifecycle,
  locks, migrations, participation-schemas, provisioning, resource-requirements,
  resources, runtime, schemas, sessions, setting, settings-registry, setup-readiness,
  slow, status, tasks, views), query_logs, recent_errors, system_info,
  test_notification, validate_json_files · **slash:** platform
- **Notes:** read-only diagnostics — great for cross-checking other cogs' state.
- **Status:** ❓ · **Notes:** _…_

### SettingsCog — ❓
- **Panel:** `!settings` (+ `!settings access`) · **slash:** settings
- **Notes:** settings registry = 24 entries across 9 subsystems (from boot).
- **Status:** ❓ · **Notes:** _…_

### SetupCog — ❓
- **Hub:** `!setup` / `setup-hub` · **slash (9):** setup, setup-delegate, setup-depth,
  setup-hub, setup-reset, setup-skip, setup-status, setup-undelegate, setup-unskip
- **Env:** advisor deterministic (no AI suggestions).
- **Status:** ❓ · **Notes:** _…_

### LoggingCog — ❓
- **Hub:** `!logging` · **Prefix (6):** logging, logging create, logging routes,
  logging set, logging status, logging test
- **Env:** webhook mirror off; server-logging policy OFF by default (enable to see
  embeds post to a channel).
- **Status:** ❓ · **Notes:** _…_

### HelpCog — ❓
- **Entry:** `!help` (dynamic help surface; 298 command descriptions at boot)
- **Status:** ❓ · **Notes:** _…_

### EconomyCog — ❓
- **Panel:** `!economymenu` · **Prefix (7):** balance, daily, economymenu, joblist,
  setlogchannel, shop, work · **slash:** economy
- **Status:** ❓ · **Notes:** _…_

### XpCog — ❓
- **Panel:** `!xpmenu` · **Prefix (5):** givexp, rank, resetxp, xpconfig, xpmenu
- **Env:** XP→role auto-assign tied to the (disabled) automation scheduler; XP gain on
  messages still works.
- **Status:** ❓ · **Notes:** _…_

### InventoryCog — ❓
- **Entry:** `!inventory`
- **Status:** ❓ · **Notes:** _…_

### MiningCog — ❓
- **Panel:** `!minemenu` · **Prefix (12):** build, buildable, buildlist, chop,
  explore, give, mine, mineinv, minemenu, minestats, reset_inventory, use
- **Status:** ❓ · **Notes:** _…_

### Leaderboard — ❓
- **Entry:** `!leaderboard`
- **Status:** ❓ · **Notes:** _…_

### BlackjackCog — ❓
- **Entry:** `!blackjack` / `!bjstart` · **Prefix (4):** bjstart, bjstatus,
  bjtournament, blackjack
- **Status:** ❓ · **Notes:** _…_

### Rock Paper Scissors — ❓
- **Entry:** `!rps` / `!rpsstart` · **Prefix (7):** rps, rpsbot, rpshelp, rpsmatchup,
  rpsregister, rpssettings, rpsstart
- **Status:** ❓ · **Notes:** _…_

### Deathmatch — ❓
- **Entry:** `!dm_challenge` · **Prefix (2):** dm_challenge, dm_help
- **Status:** ❓ · **Notes:** _…_

### GamesCog — ❓
- **Hub:** `!games` (prefix + slash) — game launcher hub
- **Status:** ❓ · **Notes:** _…_

### CountingCog — ❓
- **Panel:** `!countingmenu` · **Prefix (9):** count_info, count_rules, countingmenu,
  end_match, reset_count, set_skip_numbers, start_match,
  toggle_reset_on_wrong_count, toggle_turns
- **Status:** ❓ · **Notes:** _…_

### ChainCog — ❓
- **Panel:** `!chainmenu` · **Prefix (7):** chain, chain create, chain delete,
  chain list, chain removelimit, chain setlimit, chainmenu
- **Status:** ❓ · **Notes:** _…_

### FourTwentyCog — ❓
- **Entry:** `!420`
- **Status:** ❓ · **Notes:** _…_

### ProofChannelCog — ❓
- **Panel:** `!prizemenu` · **Prefix (5):** +prize, -prize, prizemenu, prizestatus,
  timedprize
- **Status:** ❓ · **Notes:** _…_

### BTD6Cog — ❓
- **Panel:** `!btd6menu` · **Prefix (7):** btd6, btd6 ask, btd6 ctteam,
  btd6 diagnostics, btd6 status, btd6 test-intent, btd6menu · **slash:** btd6menu
- **Env:** data=file; `btd6 ask` AI grounding off (AI disabled).
- **Status:** ❓ · **Notes:** _…_

### BTD6ReferenceCog — ❓
- **Group:** `!btd6ref` · **Prefix (6):** btd6ref ct, btd6ref hero, btd6ref relic,
  btd6ref round, btd6ref tower
- **Status:** ❓ · **Notes:** _…_

### BTD6EventsCog — ❓
- **Group:** `!btd6events` (9): event, grounding, latest-data, leaderboard, live,
  refresh-source, source-health, sources
- **Env:** live/refresh need outbound to sources.
- **Status:** ❓ · **Notes:** _…_

### BTD6StrategyCog — ❓
- **Group:** `!btd6strat` (9): browse, mine, pending, strategies, strategy,
  strategy-audit, submit, why-no-response
- **Env:** AI off; YouTube off → mining/generation degraded.
- **Status:** ❓ · **Notes:** _…_

### BTD6OpsCog — ❓
- **Group:** `!btd6ops` (7): announcechannel, readiness, runs, seed-data,
  source_disable, source_enable
- **Status:** ❓ · **Notes:** _…_

### ParagonCog — ❓
- **Entry:** `!paragon`
- **Env:** Paragon calc API (outbound); local estimate fallback.
- **Status:** ❓ · **Notes:** _…_

### AICog — ⏸️ env-gated
- **Panel:** `!aimenu` · **Prefix (12):** ai, ai diagnostics, ai forget, ai policy,
  ai providers, ai readiness, ai routing, ai settings, ai status, ai support-report,
  ai why-no-response, aimenu · **slash:** aimenu
- **Env:** `AI_ENABLED` off → chat answers won't call an LLM. The **config/diagnostic**
  subcommands (status, readiness, providers, policy, routing, settings) should still
  render — they describe the (disabled) platform. Distinguish "answer path off" from
  "panel broken."
- **Status:** ⏸️ — verify the config/diagnostic surface; answer path is expected off.

### General — ❓
- **Panel:** `!generalmenu` · **Prefix (8):** eightball, fact, generalmenu, greet,
  joke, motivate, quote, trivia
- **Status:** ❓ · **Notes:** _…_

### UtilityCog — ❓
- **Panel:** `!utilitymenu` · **Prefix (9):** avatar, clear, info, invite, poll,
  remind, serverinfo, userinfo, utilitymenu · **slash:** utility
- **Status:** ❓ · **Notes:** _…_

---

## Cross-cutting findings (env / infra, not per-cog bugs)

- `AUTOMATION_SCHEDULER_ENABLED=false` — confirmed in boot log: *"automation_scheduler:
  spawn skipped."* Affects Role + XP auto-assignment loops.
- Boot-time self-catalogue findings worth reviewing: `customization_catalogue` reported
  **52 findings** across 27 subsystems / 40 panels, `command_surface_ledger` **9
  findings**, `resource_provisioning_catalogue` **1 finding**. These are the bot's own
  gap detectors — pull them via `!platform customization` / `!platform consistency`
  while auditing.

## Session findings — live testing 2026-06-05 (supersedes ❓ where noted)

### 🔴→✅ RoleCog: two discord.py 2.7.1 crashes — FOUND & FIXED this session
The "two warts" from last session were not the real problem. Live testing crashed the
bot and broke role management because the panels collide with **discord.py 2.7.1**
internals (`requirements.txt` pins `discord.py>=2.3.0` **unpinned** → resolves to 2.7.x):

1. **Whole-bot crash.** `TimeRolesPanel` / `XpRolesPanel` defined `async def _refresh(self)`,
   shadowing discord.py's `View._refresh(components)` (called on every MESSAGE_UPDATE).
   The 1-arg override raised `TypeError` **inside the gateway poll loop** → process exit.
   **Fix:** renamed the panel re-render helper to `_rerender`. (Same latent collision —
   2-arg async, warn-only not crash — in `views/xp/config_panel.py` and
   `views/setup/ai_review/main_panel.py`; also renamed.)
2. **Delete Role + both Remove dropdowns broken.** `_DeleteRoleSelect` /
   `_TimeRemoveSelect` / `_XpRemoveSelect` did `self.parent = parent`, colliding with
   discord.py 2.7.1's **read-only `Item.parent`** property → `AttributeError` on click.
   **Fix:** store the panel as `self._panel`. (Scan confirmed these 3 selects were the
   only `self.parent`-on-an-Item assignments in the whole codebase.)

Regression-pinned by `tests/unit/views/test_role_panels_discordpy_compat.py`.
**Recommendation:** pin `discord.py>=2.7,<2.8` (CLAUDE.md "pin where the API churned")
and sweep other `discord.ui` overrides for 2.7 collisions. The 2 prior UX warts
(bulk "Clear missing", selector-ize Edit Role) remain open but are lower priority.

### 🔴 DiagnosticCog: `!platform` Runtime sub-view = your "no back button"
`!platform` → **Runtime** tab (`platform_hub.runtime`) builds an embed **> Discord's
6000-char limit** → `safe_edit` returns 400 (50035 "Embed size exceeds maximum size of
6000") → the message edit (new embed **and** its Back/Help button) never applies, so the
panel looks frozen and loses its back button. Confirmed in `bot.log` (×2). Likely affects
other dense `platform_*` sub-views. **Fix:** truncate/paginate (cap the description; push
detail into fields/pages). No `attach_back_button` 25-cap warnings were logged, so the
navigation helper itself is fine — this is purely the oversized embed.

### 🔴 DiagnosticCog: "Recent Errors / Recent Logs" panel is permanently empty
`build_query_logs_embed` (`cogs/diagnostic/_helpers.py:341`) reads
`SELECT … FROM logs`, but **nothing ever writes to the `logs` table** — the bot logs to
`bot.log` (file) + stdout via Python handlers (bot1.py); there's no DB log handler and
no `INSERT INTO logs` anywhere. So "Recent Errors" always shows "No logs found," even
right after a crash. `logs` is one of the 16 base tables, but its writer was never built
— a long-standing dead feature. **Fix options:** (a) repoint the panel to tail/parse
`bot.log` (simple, no new writes); or (b) add an async-safe DB log handler that persists
ERROR/WARNING records to `logs` (survives restarts, but needs queue/loop plumbing since
logging handlers are sync and the pool is async).

### 🟡 DiagnosticCog: "Database Schema Check" expected-tables list is 52 stale
`build_check_database_embed` (`_helpers.py:200`) hardcodes **16 expected tables** — the
pre-migration `create_tables()` base set — so every migration-added table shows as
"Unexpected (52)". The DB actually has 68 tables and `Missing: None` (the schema is
fine); the "Unexpected" list is just a stale comparison. **Fix is non-trivial:**
hand-adding 52 names re-rots on the next migration, and deriving from `migrations/*.sql`
is incomplete — validated that ~11 tables (`bot_runtime_lock`, `setup_session`,
`guild_command_access_*`, `automation_*`, …) are created by **runtime Python code**, not
a `.sql` file, so no regex over migrations is complete. Cleanest: reframe to "migrations
applied N/N" (compare `schema_migrations` to the migration files) and drop the brittle
"Unexpected" field — or maintain a complete list guarded by a fresh-DB-bootstrap CI test.

### interaction_router warnings = benign noise (with a latent gap)
Only **`ai`** registers a router prefix (`ai_cog.py:322`). Every other panel handles its
components **in-memory** via the View, but discord.py fires the global `on_interaction`
for each click too, so the router logs "Unhandled interaction prefix" once per unseen
prefix (`role`, `xp`, `help`, `community`, `settings_hub.*`, `platform_hub.*`, plus a new
hex id per component). **Buttons still work.** Latent gap: after a view times out / on
restart those clicks fall through to a router that can't answer them. Mirroring the AI
cog's safety-net registration would silence the spam and let expired panels reply
gracefully. (`role` is even in the router's `_FAIL_CLOSED_PREFIXES` with no handler, so
that posture is currently inert.)

### Bot self-audit dump (62 findings) — wiring gaps, not command breakage
The three startup catalogues introspect the loaded cogs and flag integration gaps:

- **`command_surface_ledger` — 9** · `orphan_cog_subsystems`: BTD6EventsCog, BTD6OpsCog,
  BTD6ReferenceCog, BTD6StrategyCog, FourTwentyCog, ParagonCog, ProofChannelCog,
  RockPaperScissorsCog, SetupCog. → work, but not first-class "subsystems" in the
  settings/governance model.
- **`customization_catalogue` — 52**:
  - `subsystems_missing_panel` (4): four_twenty, help, proof_channel, rps_tournament
  - `subsystems_missing_help_hook` (4): same 4 (not in the Help-menu hook system)
  - `subsystems_missing_schema` (17): admin, chain, channel, cleanup, community, counting,
    diagnostic, four_twenty, games, general, help, inventory, leaderboard, mining,
    proof_channel, settings, utility (no `!settings` schema — some legitimately none;
    channel/cleanup/counting arguably should have one)
  - `panels_without_settings` (24): panels with no settings behind them (adminmenu,
    chainmenu, wordmenu …; `<build_help_menu_view>` = auto help sub-panels)
  - `settings_without_panel` (1): rps_tournament.default_entry_fee
  - `regex_inferred_panels` (2): ai.aimenu, btd6.btd6menu (only detected via a fragile
    regex fallback, not explicitly declared)
- **`resource_provisioning_catalogue` — 1** · `orphan_requirements`: moderation/mod_log
  (declares a mod-log channel need with no binding spec to provision/resolve it; ties to
  logging being OFF by default).

→ Net: the 62 are **integration/wiring gaps** (cogs not fully registered into the
settings/help/governance framework), not broken commands. Good per-cog "is this fully
wired in?" checklist; biggest clusters are the 9 orphan subsystems + 17 missing-schema
cogs.

_(running log of issues found during the walkthrough — append below)_
