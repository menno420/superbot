# Dashboard live editor — plan (help appearance & command panels)

> **Status:** `plan` — owner-approved direction (2026-06-16, router Q-0156). Design only;
> no bot-runtime code has shipped yet. Source code and merged PRs win over this document.

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
