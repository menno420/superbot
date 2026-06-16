# Dashboard live editor — plan (help appearance & command panels)

> **Status:** `plan` — owner-approved direction (2026-06-16, router Q-0156–Q-0159). Design only;
> no bot-runtime code has shipped yet. Source code and merged PRs win over this document.

## ⭐ Next session — start here (handoff 2026-06-16)

**The site is the bot's main website** (`dashboard/`, live on Railway, auto-redeploys on merge to
`main`). Two binding principles (Q-0158): the **bot stays the source of truth + top priority**, and the
website **front-ends the bot's existing audited seams — never a parallel system**.

**Shipped this run (read-only, decoupled, all merged):** `/functions` · `/games` · `/commands`
(explorer) · `/aliases` (synonym suggest) · `/settings` (now with typed `SettingSpec`
type/default/hint/choices) · `/access` (tier map). Scanners: `scan_settings` · `scan_setting_specs` ·
`scan_access` · `scan_synonyms` · `scan_commands` · `scan_env_usage`. **The bot already owns every
edit capability** — front-end these seams, do not rebuild:

| Capability | Bot seam (audited) |
|---|---|
| Settings (per-guild) | `services.settings_mutation.SettingsMutationPipeline` + `SettingSpec` (`cogs/*/schemas.py`) |
| Per-user config | `services.participation_mutation` + `core/runtime/user_config.py` + `views/profile/` |
| Help appearance | `services.help_overlay_mutation` + `views/help/editor.py` |
| Cog enable/disable | `services.command_routing.set_policy` (migration 036) |
| Aliases (soft) | `utils/synonyms.py` `COMMAND_SYNONYMS` |

**Build next, in order:**

1. ✅ **`/commands` management surface — READ side — SHIPPED 2026-06-16.** A **Manage button on every
   command and cog** (`dashboard/templates/commands.html`); each opens a slide-over panel showing the
   command's current aliases (code aliases + soft synonyms) + its cog's **cog-level** routing state
   (front-ending `command_routing.set_policy`, default-on, scope-aware) + a **per-command alias box**
   (suggest→PR mode — the `/aliases` collision check + prefilled issue + snippet, scoped to one
   command). Decoupled, read-only, no bot change. **Open decision RESOLVED → Q-0160: cog-level now,
   per-command later** (per-command would be a new bot routing layer). Drive-by: acronym-aware
   `_cog_to_subsystem` so `BTD6Cog`/`AICog`/`XPCog` join the registry (`btd6`/`ai`/`xp`).
2. **Bot-ready foundation (runtime — do NOT rush; owner setup required, see § "Free multi-user control
   panel").** ① a private **control API** on the bot exposing the seams above; ② the **identity →
   authority bridge** (resolve `(user_id, guild_id)` → member → run `governance.capability` checks).
3. **Website auth + editors:** Discord OAuth login → per-user + per-guild editors over the control API
   (settings global+per-server per Q-0157; help; aliases live; cog routing).

**Ready read-only slices (no auth, no bot change — grow these while phase 2/3 are gated):**

- **"Your authority" preview (pre-auth).** Per subsystem, explain *which tier / capability* governs
  each control (derivable from `SettingSpec.capability_required` + the access map) — sets correct
  expectations for the future control panel ("you'll edit X in servers where you're admin; Y is
  yours personally"). Pure read-model; a gentle on-ramp to the multi-user model. *(Groomed up from
  the 2026-06-16 multi-user-design session log, Q-0015 — now a natural extension of the shipped
  `/commands` + `/access` read surfaces.)*

**Owner setup needed before phase 2/3 (nothing needed for phase 1):** a Discord OAuth app
(client id/secret + redirect), a dashboard session secret, and a shared bot↔dashboard token —
see § "Free multi-user control panel" and the chat handoff.

**Always before pushing a dashboard change:** `pip install -r dashboard/requirements.txt httpx` then
`python3.10 -m pytest tests/unit/dashboard/` — the smoke test is `importorskip`-guarded and **skips in
CI**, so a template bug (the #979 `/settings` 500) is only caught locally with deps installed.

## ⭐ What the owner asked for

> *"I'd also like to be able to edit the help message and command panels directly from the
> website, so you can move buttons to wherever you want."*

Answered in-session (AskUserQuestion, 2026-06-16):

| Question | Owner choice |
|---|---|
| Do edits change the **live bot**, or a website-only mockup? | **Change the live bot.** |
| How far in v1? (help *text* is data-driven; panel *buttons* are hardcoded) | **Help text & visibility first**; button drag-and-drop is a larger follow-on. |
| Login for the editing side? | **Discord OAuth.** |

This plan turns those choices into a buildable, modular sequence.

## The decisive finding (why this is two efforts, not one)

- **Help appearance is already data-driven and audited.** The bot has a mature per-guild **Help
  overlay** (`services/help_overlay.py` + `services/help_overlay_mutation.py`, migrations 064/067):
  each server can **hide / rename / re-describe** hubs & subsystems and customize the **Home
  message** (title/body/color). Writes go through one **audited mutation seam** that validates,
  writes, **invalidates the bot's in-process cache**, and emits an `audit.action_recorded` event.
  An in-Discord editor (`views/help/editor.py`) already drives it. **The website editor is a second
  front-end over this existing system** — high value, achievable.
- **Command-panel buttons are hardcoded.** Panels like the XP hub define buttons with fixed
  `@discord.ui.button(..., row=N)` decorators in Python (`views/xp/main_panel.py`, etc.). There is
  **no data layer** to "move a button." Doing so needs a **new DB-backed panel-layout engine the bot
  reads at render time** — greenfield, and the second half of the owner's ask. Deferred to Phase L3.

## Hard architectural rule this must honor

`.claude/CLAUDE.md`: *"A new mutation path that bypasses the audited service seam is an immediate
blocker."* So the website **must not** write `help_overlay` rows directly into the bot's Postgres —
that would skip the audit emit **and** leave the bot's per-guild overlay cache stale (help would not
change until the next bot restart). **Every live edit must flow through the bot's existing seam.**

Because the website is a **separate process** that never imports `disbot/`, the only way to reach the
in-process seam is for the **bot to expose it over the network**. That is the spine of this design.

## Architecture

```
 Browser ──Discord OAuth──▶ Dashboard service ──(Railway private net,
            (who am I +        (FastAPI)            shared-secret auth)──▶ Bot worker
             which guilds                                                  control API
             do I admin?)                                                  (aiohttp)
                                                                              │
                                                          calls the EXISTING audited seam
                                                          services.help_overlay_mutation
                                                          → validate → DB write → cache
                                                            invalidate → audit emit
```

### 1. Bot side — a private control API over the seam

- A small **aiohttp `web.Application`** started from the bot's `setup_hook` (the bot already depends
  on `aiohttp` and runs an event loop). It listens on `$CONTROL_API_PORT` and is reachable **only on
  Railway's private network** (`worker.railway.internal`) — **never a public domain**. (The bot is a
  `worker`; we are not exposing it to the internet.)
- Endpoints (all guild-scoped):
  - `GET  /control/help/overlay?guild_id=…` → the guild's current overlay (calls
    `services.help_overlay.get_guild_help_overlay`) so the website can render current state.
  - `GET  /control/help/catalogue` → hubs/subsystems + their defaults (the website's edit targets;
    from `services.help_catalogue.build_help_catalogue`).
  - `POST /control/help/overlay` `{guild_id, kind, key, display_hidden?, display_name?, description?}`
    → calls `set_overlay_fields(...)`.
  - `POST /control/help/home` `{guild_id, title?, body?, color?}` → `set_home_message(...)`.
  - `POST /control/help/reset` `{guild_id}` → `reset_guild_overlay(...)`.
- **The bot is the authority.** Each write carries the acting **Discord user id** (from the
  dashboard's OAuth session) + `guild_id`. The handler resolves the live member
  (`guild.get_member(user_id)`) and the seam's `_check_admin` verifies `administrator` —
  **the same gate the in-Discord editor uses**. The website's claim is never trusted on its own.
- **Service↔service trust:** a shared secret (`CONTROL_API_TOKEN`) on every request (bearer/HMAC), so
  only the dashboard can call the API. Defense in depth: secret **and** per-request admin re-check.

### 2. Website side — Discord OAuth + the editor UI

- **Discord OAuth** (`identify guilds` scopes). The session stores the user id and the guild list;
  the editor only offers servers where the user is an admin (and the bot is present).
- New **private zone** (the plan's existing public/private split): `/admin/help` — pick a server →
  see its hubs/subsystems and Home message → hide / rename / re-describe / edit Home → the page calls
  the bot control API. Mirrors the in-Discord editor's flow so behavior is identical across surfaces.
- The website keeps **no overlay state of its own** — the bot's DB stays the single source of truth.

### 3. Secrets (all already managed via Railway; surfaced read-only on `/env`)

`DISCORD_OAUTH_CLIENT_ID` · `DISCORD_OAUTH_CLIENT_SECRET` · `DASHBOARD_SESSION_SECRET` ·
`CONTROL_API_TOKEN` (shared bot↔dashboard) · `CONTROL_API_PORT`. None are committed; the `/env`
usage-map page lists them by name once they exist.

## Phased build (modular PRs)

- **Phase L0 — auth foundation (website-only, low risk).** Discord OAuth login + session +
  admin-guild gating; an empty private zone. No bot changes. *Verifiable without touching runtime.*
- **Phase L1 — bot control API (read).** aiohttp app in `setup_hook`, private-network bind,
  shared-secret auth, the two `GET` endpoints. Dashboard `/admin/help` renders **current** overlay
  state read-only. Small, focused `disbot/` PR (the risky-runtime rule → its own PR).
- **Phase L2 — bot control API (write) + editor UI.** The `POST` endpoints over the seam (admin
  re-check per request) + the website's hide/rename/re-describe/Home editing. **This delivers the
  owner's "edit the help message live from the website."**
- **Phase L3 — panel layout engine (greenfield, the "move buttons" half).** A DB-backed
  `panel_layout` overlay (button order/row/visibility per panel), a render-time reader the panel
  views consult, an audited mutation seam mirroring `help_overlay_mutation`, **then** a drag-and-drop
  website editor. Largest slice; planned separately once L0–L2 land.

## Settings editor — global + per-server (owner ask, 2026-06-16)

Owner: *"edit the settings from the website — it's fine if that triggers a redeploy — and as bot owner
let me change things globally, as well as per-server if available."*

**What the bot does today** (`utils/db/settings.py`): settings are a per-guild key/value store
(`guild_settings(guild_id, key, value)`); `get_setting(guild_id, key, default)` returns the guild's
row or a **default passed by the caller** — defaults are scattered at call sites, and there is **no
global layer**. But `core/runtime/feature_flags.py` already resolves **per-guild → global → default**,
so that resolution shape is a proven in-repo pattern to mirror.

**Design (both scopes, mirrors feature_flags):**

1. **Global layer.** Add a global settings row space — `guild_settings` at `guild_id = 0` (the repo
   already uses `guild_id = 0` as the global/no-guild sentinel in several stores) *or* a sibling
   `global_settings` table. A global value = the owner's default for every server.
2. **Resolution change (one function, hot path — small but careful).** `get_setting` becomes
   **per-guild row → global row → caller default**. This is a single, well-contained change to one
   function, but it is read on every settings access, so it ships as its own focused, well-tested
   `disbot/` PR (the risky-runtime rule).
3. **Audited mutation seam** `services/settings_mutation.py` (mirrors `help_overlay_mutation`):
   `set_setting(scope, key, value, actor)` where `scope` is `global` (owner-only) or a `guild_id`
   (server admin) — value-validated per key, audited, cache-invalidated.
4. **Website (owner auth) → control API → seam.** The editor shows each setting with a **scope
   picker: "Global (all servers)" vs a specific server**; global is gated to the **bot owner**,
   per-server to that server's admin (re-checked bot-side, like the help editor).

**On "redeploy is fine":** with the global layer in the DB, **neither scope needs a redeploy** — both
apply live (better than asked). The redeploy path is only needed if we instead edit *code* defaults;
since defaults are scattered, the DB global layer is cleaner than centralising them into a committed
file just to PR-and-redeploy. (If you'd rather avoid any hot-path change for now, the fallback is a
committed `settings_defaults` file the website edits → PR → redeploy — but the DB layer is the better
long-term answer and reuses the feature-flags pattern.)

**The editor + metadata already exist (do NOT rebuild).** The bot has a typed, audited settings
system: each editable setting is a `core.runtime.subsystem_schema.SettingSpec`
(`value_type` / `default` / `hint` / `allowed_values`) declared in `cogs/<subsystem>/schemas.py`,
**`services.settings_mutation.SettingsMutationPipeline.set_value(guild, subsystem, name, value,
actor)`** is the audited write seam (coerce → validate → capability-gate → DB+audit txn → cache
invalidate → emit), and `views/settings/edit_*` is a full in-Discord typed editor. **The metadata
registry I planned to build already is `SettingSpec`** — surfaced read-only on `/settings` as of this
session (`scripts/scan_setting_specs.py`: 64 typed specs with type/default/hint/choices). So the web
settings editor is a **front-end over the existing pipeline**, exactly like help over
`help_overlay_mutation` — *not* a from-scratch build.

**What's genuinely new = the global scope.** `set_value` and `resolve_setting` are **per-guild
only** today. The owner's "change things globally" needs the global tier (steps 1–2 above:
`guild_id = 0` rows + `resolve_setting` → per-guild → global → spec default), then `set_value` gaining
a global-scope path (owner-gated). That is the one focused runtime PR; per-server editing is *just*
the existing pipeline behind the control API.

**Phase placement (revised):** ① surface `SettingSpec` on `/settings` ✅ (shipped — read-model done) →
② global-scope tier in `resolve_setting` + `SettingsMutationPipeline` (focused runtime PR) →
③ website settings editor over the control API (the **same** auth + control-API foundation L0–L2 the
help/alias editors need; per-server reuses the existing pipeline as-is).

## Strategic framing — the bot's main website (owner, 2026-06-16)

The owner set the scope: **this is the bot's main website.** A separate, broader
**project-management** site (review repo sectors — the AI memory system, etc.) comes later. Two
standing principles for everything here:

1. **The bot stays the source of truth and the top priority.** Everything must remain fully
   manageable *in the bot itself*; the website is a **faster-oversight shortcut**, never the only way
   to do something.
2. **Front-end the bot's seams — never build a parallel system.** Every write the website performs
   goes through an **existing audited bot seam** over the control API: settings →
   `SettingsMutationPipeline`, help → `help_overlay_mutation`, **cog enable/disable →
   `services.command_routing.set_policy`**, aliases → the synonym layer. The website renders current
   state and drives those seams; it never owns a second copy of the truth.

## Command management surface (`/commands` → manage, owner ask 2026-06-16)

The owner wants `/commands` to become a **management surface**: the existing search **plus a Manage
button on every command and cog**, each opening an editor.

- **Per-cog enable/disable — front-ends `command_routing` (exists).** `services/command_routing.py`
  (migration 036) already does per-guild, scope-aware (channel→category→guild) cog enable/disable with
  an audited mutation owner (`set_policy` → `RoutingMutationResult`). The website's per-cog toggle
  calls it via the control API — no new model. **Per-individual-command** disable is *finer* than the
  bot does today (it routes at cog granularity); offering it would be a new per-command routing layer,
  so start at cog level (what the bot supports) and treat command-level as a later extension.
- **Per-command alias box (owner correction).** The global `/aliases` form stays as the broad
  *search / quick-add*; additionally **each command gets its own alias box** inline in `/commands`.
  Backing: the synonym layer (suggest→PR today; live once the synonym overlay + control API land).
- **Read side — SHIPPED 2026-06-16** (`dashboard/templates/commands.html`): a Manage button on every
  command and cog opening a slide-over panel — current aliases (code + soft synonyms), cog-level
  routing state (front-ends `command_routing`), and a per-command alias suggest box (the `/aliases`
  collision check + prefilled issue + snippet, scoped to one command). The global `/aliases` page
  stays the broad search. **Write side** (live toggle, live alias) lands with the control-API + auth
  foundation (L0–L2). **Granularity owner-decided → Q-0160: cog-level now, per-command later.**

## Free multi-user control panel — identity & authority (owner, 2026-06-16)

The owner widened the scope again: the site is becoming a **free-to-use control panel** — *anyone*
signs in with Discord, not just the owner — and **everyone configures it personally how they like**,
so the site needs **per-user** config as well as per-guild. Explicit guidance: *"we should not rush
it — first the bot needs to be ready for this."*

**Good news — both config layers already exist (front-end them):**

| Layer | Bot system (audited) |
|---|---|
| **Per-guild** | `guild_settings` + `SettingsMutationPipeline` · `help_overlay` · `command_routing` |
| **Per-user** | `user_participation` (migrations 027/028) + `services.participation_mutation` + `core/runtime/user_config.py` + the in-Discord profile editor (`views/profile/`) |

So "everyone changes it personally" is **not new bot work** — it is the existing per-user
participation/preferences seam, surfaced on the web.

**What "bot ready" actually means (the real gap — *not* the config layers):**

1. **The control API** — the bot exposing these seams to the decoupled site (Q-0156).
2. **An identity → authority bridge.** Discord OAuth tells the site *who* you are and *which guilds*
   you're in; but **the bot must decide what you may edit**. Every seam already authority-checks with a
   live `discord.Member` (`governance.capability.actor_holds_capability`, the settings/participation
   pipelines' capability gate). The control API must, per request, resolve the member for `(user_id,
   guild_id)` and run that **same** check — so the site renders only the controls you're allowed, and
   every write is **bot-verified**, never trusted from the browser. Per-user edits gate on "is this
   your own profile"; per-guild edits gate on your tier in that guild.
3. **No new source of truth.** The site stores only a session (who you are); all config stays in the
   bot's per-user / per-guild stores.

**Sequencing (owner: don't rush):** bot-ready first — ① control API, ② the identity→authority bridge
(reuse the existing capability checks) — *then* the website's Discord login + editors. The per-user +
per-guild config and their audited seams are already there; the foundation is the API + the bridge.

## Alternatives considered (and why not)

- **Website writes `help_overlay` rows directly (shared Postgres).** Rejected: bypasses the audited
  seam (blocker rule) and never invalidates the bot's overlay cache → stale help until restart.
- **Public bot HTTP API.** Rejected: needlessly exposes the worker to the internet. Private-network
  only, plus shared-secret + admin re-check.
- **Control queue table the bot polls.** Workable fallback if private networking is unavailable, but
  adds a queue + polling + eventual-consistency lag. Prefer the private API; keep this in reserve.

## Open questions (decide at the phase)

- **Session store** for the website (signed cookie vs the dashboard's own Postgres) — Phase L0.
- **Multi-guild UX:** the dashboard is one personal site but the bot is multi-guild — confirm the
  server picker + whether a "global default" overlay is ever wanted (today overlays are per-guild).

## Verification (per phase)

- L0: OAuth round-trip in a local run; admin-guild gating unit-tested with a stub guild list.
- L1/L2: the bot control API unit-tested against a fake bot/guild; the seam calls assert audit emit +
  cache invalidation (reuse the `help_overlay_mutation` test patterns). `check_architecture --mode
  strict` stays green (the API lives in `cogs/`-adjacent runtime, never in `views/`/`utils/`).
