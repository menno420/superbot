# Dashboard website ideas and dynamic data plan

> **Status:** `plan` — planning/mapping-only review, 2026-06-16. No runtime behavior is implemented here.
> Source code, generated `dashboard/data/dashboard.json`, and merged PRs win over this document.

## Executive summary

The current SuperBot dashboard is a lightweight, public, read-only FastAPI/Jinja/Tailwind site. It renders a committed generated artifact, `dashboard/data/dashboard.json`, and intentionally does **not** import the bot package. That boundary is correct and should be preserved.

The best target is not a second configuration system. The website should become a web front-end over bot-owned read models and bot-owned mutation seams:

- keep public showcase/read-only catalogue pages fast and static/hybrid;
- add Discord OAuth only for user/server/private areas;
- expose live bot truth through a private, dormant-by-default bot control API;
- route every write through existing audited seams (`SettingsMutationPipeline`, `help_overlay_mutation`, `command_routing.set_policy`, participation/user-config seams);
- treat command/button/panel metadata as unreliable until the bot exports a typed command-and-panel manifest built from runtime command trees, the command surface ledger, and an explicit panel registry.

Most live-write work is gated on owner-controlled secrets and OAuth/Railway setup. The next safe PRs should be documentation/read-only or control-API read-model expansions, not editors.

## Review constraints and PR status

- `gh` is not installed and this checkout has no `origin` remote, so live open/merged PR verification could not be performed from GitHub in this environment. Local history shows recent dashboard-related merges through #992, including dashboard JSON integrity and command-ledger reconciliation. Treat live-PR ownership as **not externally verified** before starting implementation.
- The bot-side private control API is **merged but partial/dormant**: `disbot/control_api.py` registers only `/control/ping` and `/control/authority`, and only when `CONTROL_API_TOKEN` is set. Mutation endpoints are not implemented.
- Active gates: Discord OAuth client secret, dashboard session secret, shared control token, Railway/private-network configuration, Railway API credentials for secret value management, and owner decisions for any public bug/idea storage backend.

## Current-state inventory

| Route/page | Template | Source data | Generator/scanner | Trust level | Refresh mechanism | Drift risks |
|---|---|---|---|---|---|---|
| `/healthz` | JSON | app constant | none | trustworthy liveness only | live request | does not prove data freshness or bot health |
| `/` | `index.html` | `dashboard.json` counts, catalogue, updates | `export_dashboard_data.py` | approximate showcase | regenerate + commit + redeploy | stale if source changes without export |
| `/functions` | `functions.html` | subsystem registry projection | `export_dashboard_data.py` AST of `SUBSYSTEMS` | mostly trustworthy for declared subsystem metadata | regenerate + commit | AST literals only; runtime registration/availability not proven |
| `/games` | `games.html` | catalogue category filter + settings domains | export + settings/spec scanners | mostly trustworthy for declared metadata | regenerate + commit | not live economy/game state |
| `/commands` | `commands.html` | cog/command AST scan + synonyms + catalogue | `scan_commands.py`, `scan_synonyms.py`, export | mixed: command names/types mostly useful; button-backed approximate/unverified | regenerate + commit | decorators can drift from runtime; inherited/mixin commands and dynamic app commands are hard; button/view linkage is heuristic |
| `/aliases` | `aliases.html` | command names/aliases/synonyms | `scan_commands.py`, `scan_synonyms.py` | read-only suggestion aid | regenerate + commit | no live collision check against loaded bot; suggestions are not persisted |
| `/settings` | `settings.html` | declared keys + typed specs | `scan_settings.py`, `scan_setting_specs.py` | trustworthy for declared key/spec metadata; not values | regenerate + commit | no per-guild values; scanner can miss dynamic specs |
| `/access` | `access.html` | static mirror of visibility tier ladder | `scan_access.py` | verified static mirror for visibility, not execution authority | regenerate + commit | Discord member state/guild ownership is live-only |
| `/ideas` | `ideas.html` | `docs/ideas/*.md` | export markdown parser | trustworthy docs index | regenerate + commit | not a live product board |
| `/bugs` | `bugs.html` | `docs/health/bug-book.md` | export markdown parser | trustworthy docs index | regenerate + commit | no public submission persistence yet |
| `/updates` | `updates.html` | `.sessions/*.md` | export markdown parser | approximate activity feed | regenerate + commit | only committed session notes; not GitHub/Railway live events |
| `/env` | `env.html` | env var names/usages only | `scan_env_usage.py` | trustworthy for static code references; no values | regenerate + commit | dynamic env names and external config not shown |
| `/status` | `status.html` | dashboard artifact counts/build/open bugs/access tiers | export + app aggregation | dashboard status, not bot/deploy truth | regenerate + commit | name says live status but currently lacks Railway/GitHub/bot live probes |

### Where `dashboard.json` can drift

`dashboard.json` is a committed generated artifact. It can drift whenever cogs, settings, schemas, synonyms, visibility rules, docs, session logs, bug book entries, env var usage, or subsystem registry entries change without running and committing `scripts/export_dashboard_data.py`. It can also be internally consistent while still wrong about runtime reality because it is AST/static-doc based: it does not inspect the loaded bot, live app command tree, guild settings values, command routing DB rows, Discord permissions, or active panel view instances.

## Data trust matrix

| Data family | Current state | Recommended source of truth | Dashboard mode |
|---|---|---|---|
| Public subsystem catalogue | static registry projection | `SUBSYSTEMS` + optional bot manifest checksum | static/hybrid |
| Prefix/slash command names | AST scan | runtime `bot.walk_commands()` + `bot.tree.walk_commands()` exported by bot manifest, reconciled with scanner | hybrid, freshness-badged |
| Aliases/synonyms | AST scan of decorators + `COMMAND_SYNONYMS` | runtime command aliases + synonym registry + owner-approved alias overlay later | hybrid |
| Button-backed flag | heuristic `panel_action` or view-open tokens | explicit command/panel manifest with action IDs and source view/panel registry | unverified until manifest exists |
| Settings keys/specs | static scans of keys and `SettingSpec`s | `SettingSpec` registry from bot, plus per-guild values through control API | static for docs, dynamic for values |
| Access/authority | static visibility map | bot `/control/authority` per user/guild/action | static education + dynamic enforcement |
| Help appearance | not in dashboard data | `help_overlay` read model via bot API | dynamic after API read endpoints |
| Cog routing | read-only default/cog metadata | `command_routing` DB via bot API | dynamic after API read endpoints |
| Env usage | static code scan | code scan for names/locations; Railway only for values | static names, owner-gated value UI |
| Health/deploy status | artifact metadata only | dashboard `/healthz`, bot `/control/ping`, Railway deploys, GitHub checks | dynamic widgets with graceful failure |

## UX/layout review

The current templates are effective for a small read-only site: simple nav, one max-width container, Tailwind CDN, no build pipeline, and client-side filtering on catalogue pages. Keep this approach until the site needs complex authenticated state or drag-and-drop editors.

Recommended improvements:

1. **Navigation split by zone**
   - Public: Home, Status, Commands, Functions, Games, Settings reference, Access, Ideas/Bugs.
   - User: My servers, My profile, My authority preview.
   - Server admin: server picker, settings, help appearance, command/cog routing, aliases.
   - Owner/admin: bot ops, env usage/value bridge, deploys, AI/control board.
   - Developer/ops: manifest freshness, scanner drift, tests, data build metadata.
2. **Mobile-first nav**
   - Replace the long wrapping top nav with grouped tabs or a collapsible menu.
   - Keep “Report bug” visible as a primary CTA.
3. **Command explorer**
   - Add per-command detail URLs (`/commands/<qualified_name>`) with signature, aliases, classification, source file/line, runtime/manifest freshness, panel/action links, permissions, and examples.
   - Add trust badges: “runtime verified”, “static scan”, “button inferred”, “stale artifact”.
4. **Settings management UX**
   - Keep `/settings` as a public reference.
   - Add authenticated server settings grouped by subsystem and capability, with default/current/effective value, validation help, audit history, and rollback preview.
5. **Health/status UX**
   - Rename current `/status` sections to “dashboard inventory” where appropriate.
   - Add cards for dashboard build, bot control ping, bot manifest timestamp, Railway deploy, GitHub checks, and scanner/runtime drift.
6. **Ideas/bugs**
   - Public bug report form should be spam-protected and create a stored dashboard row plus GitHub issue mirror.
   - Roadmap board should separate owner-approved, ready, gated, risky/deferred, and shipped.
7. **Control panels**
   - For help/settings/cog routing, use form-first editors before visual builders.
   - For panel layout drag/drop, do not fake it: show current hardcoded layout as read-only until a bot-side layout model exists.

## Target information architecture

```text
Public showcase
  /, /status, /commands, /commands/<id>, /functions, /games, /settings, /access, /ideas, /bugs, /updates, /env

Authenticated user dashboard
  /me, /me/profile, /me/servers, /me/authority

Server admin dashboard
  /servers/<guild_id>/overview
  /servers/<guild_id>/settings
  /servers/<guild_id>/help
  /servers/<guild_id>/commands
  /servers/<guild_id>/aliases
  /servers/<guild_id>/panels (read-only first)

Owner/admin control area
  /owner/ops, /owner/env, /owner/deploys, /owner/control-board, /owner/audit

Developer/ops area
  /dev/manifest, /dev/scanner-drift, /dev/data-build, /dev/test-status
```

## Dynamic data architecture options

| Option | Pros | Cons | Use |
|---|---|---|---|
| Static committed `dashboard.json` | safe, fast, deploy-simple, no secrets | stale, not runtime truth | public docs/showcase baseline |
| CI/cron regenerated JSON | reduces manual drift | still static between runs; needs automation | good near-term improvement |
| GitHub-backed data | useful for PRs/issues/checks | rate limits/auth; not bot truth | ideas/bugs/roadmap/status widgets |
| Railway API data | deploy/env truth | owner/creds gated; secrets risk | owner ops only, masked values |
| Bot private control API | live bot truth; can call audited seams | must secure carefully; bot uptime dependency | authority, settings values, help, routing, command manifest |
| Read-only bot manifest endpoint | simple, cacheable, low-risk | requires bot endpoint/schema | best next foundation for accurate command/button data |

### Chosen recommendation

Use a **hybrid model**:

1. Public pages load committed `dashboard.json` immediately.
2. Add freshness metadata and badges everywhere generated data is shown.
3. Add a bot read-only manifest endpoint under the private control API for command/settings/help/routing health snapshots.
4. Cache dynamic API responses in the dashboard for short TTLs (30-300 seconds depending on data) and render graceful stale/fallback states.
5. Never let cached dashboard data become writable source of truth. Writes go dashboard → bot control API → audited seam → bot DB/cache/audit/event path.

### Caching, invalidation, observability

- Include `generated_at`, git SHA, scanner version, bot manifest version, bot boot time, and endpoint timestamp.
- Use per-widget states: fresh, stale, fallback-static, unavailable, unauthorized.
- Cache public manifest reads briefly; invalidate on successful mutation responses and by manifest version changes.
- Log control API calls with request ID, actor user ID, guild ID, action, result, and latency; never log secret values.
- Add drift checks comparing committed JSON to a freshly exported artifact in CI (already present locally via dashboard integrity work) plus runtime manifest reconciliation once the endpoint exists.

## Command/button/panel metadata reliability plan

### Current sources of command truth

- Decorators in cog files (`commands.command`, `commands.group`, `hybrid_command`, `app_commands.command`, subcommands).
- Decorator aliases and `extras` classifications.
- `utils/synonyms.py` soft synonyms.
- `disbot/core/runtime/command_surface_ledger.py`, built from the live bot command surface and router prefixes.
- Runtime command trees: `bot.walk_commands()` and `bot.tree.walk_commands()`.
- Panel/action classifications (`extras={"classification": "panel_action"}`).
- View classes and hardcoded `@discord.ui.button(... row=N, custom_id=...)` declarations.
- Panel manager/send-panel call sites and persistent custom IDs.
- Bot status command count, which has already been corrected to use runtime walking rather than top-level prefix count.

### Why `button_backed` is approximate now

`scan_commands.py` marks a command as button-backed when it is explicitly classified as `panel_action` or when its body text contains broad tokens such as `panel_manager`, `send_panel`, `View(`, or `view=`. That answers “does this command look related to a view/panel?” but not “is this command truly backed by a Discord button, which button, in which panel, for which guild/state, and with what authority?” It misses buttons that call services without a command wrapper, may over-count commands that merely send a view, and cannot map hardcoded button rows or custom IDs into a movable layout.

### Long-term source of truth

Add a typed **bot-owned command and panel manifest**. It should be generated by the bot from runtime state and explicit registries, not maintained by the dashboard.

Minimum schema:

```json
{
  "version": 1,
  "generated_at": "...",
  "bot_build": "...",
  "commands": [
    {
      "qualified_name": "settings set",
      "kind": "prefix|slash|hybrid",
      "cog": "SettingsCog",
      "subsystem": "settings",
      "aliases": [],
      "classification": "primary_entrypoint|panel_action|...",
      "visibility_tier": "admin|...",
      "source": {"file": "disbot/cogs/...", "line": 123},
      "runtime_verified": true,
      "panels": ["settings:main"],
      "actions": ["settings:set"]
    }
  ],
  "panels": [
    {
      "panel_id": "xp:main",
      "view_class": "XPMainPanel",
      "source": {"file": "disbot/views/xp/main_panel.py", "line": 1},
      "layout_source": "hardcoded|db_overlay",
      "buttons": [
        {"action_id": "xp:config", "custom_id": "xp:config", "label": "Config", "row": 0, "command": "xp"}
      ]
    }
  ],
  "findings": []
}
```

Implementation notes:

- Start read-only: manifest endpoint returns command ledger + runtime command trees + static panel registry.
- Add a `PanelRegistry` or declarative panel descriptors beside view classes. Without this, drag/drop cannot be reliable.
- Add reconciliation tests:
  - scanner output vs `dashboard.json`;
  - scanner output vs `CommandSurfaceLedger` classifications;
  - ledger vs `bot.walk_commands()` and `bot.tree.walk_commands()`;
  - manifest command count vs bot status command count;
  - panel registry vs view classes/custom IDs;
  - dashboard artifact vs fresh export.

## Best website functions by readiness

| Feature | Classification | Notes |
|---|---|---|
| Command explorer filters, trust badges, per-command detail pages | ready now/read-only | Use current JSON; badge approximate fields clearly |
| Public function/game/settings/access references | ready now/read-only | Keep static generated data |
| Your authority explainer preview | ready now/read-only first; dynamic later | Static education now, live `/control/authority` after auth |
| Server picker | requires auth + bot authority | Discord OAuth `identify guilds`; bot verifies membership/authority |
| Cog management | requires bot control API | Front `command_routing.set_policy`; cog-level first |
| Alias suggestions/live alias overlay | suggestion ready now; live overlay requires bot API/data model | Current synonyms are code/static; live per-guild aliases need model/seam |
| Settings editor global + per-server | requires auth + bot control API | Front `SettingsMutationPipeline` and `SettingSpec` metadata |
| Help editor | requires auth + control API mutation endpoints | Front `help_overlay_mutation`; high-value first write UI |
| Panel layout editor / drag-and-drop button rows | requires new bot data model | Needs DB-backed layout engine and registry before website editor |
| Public bug reporting | requires DB/spam protection/GitHub token | Owner/backend gated |
| Bug/idea/roadmap boards | read-only now; write requires auth/storage | Start docs/GitHub-backed; avoid unaudited writes |
| Status/health/deploy widgets | dynamic read-only; some owner/creds gated | Bot ping/control manifest, Railway/GitHub APIs |
| Env usage/value management | usage ready now; values owner/creds gated | Railway remains source of truth; mask secrets |
| AI/control-board ideas | owner/creds gated/risky | Use existing `/fire` routine APIs; do not build multi-provider dispatcher yet |
| Mobile/dashboard navigation improvements | ready now/read-only | Template-only, low risk |

## Security and authority model

1. **Discord OAuth**
   - Scopes: `identify` and `guilds` for login/server list.
   - Dashboard stores user ID and minimal guild list in a signed session.
   - The browser never decides authority.
2. **Session storage**
   - Short term: signed/encrypted cookie session with `DASHBOARD_SESSION_SECRET`, secure/same-site/http-only cookies.
   - If sessions need server revocation/audit: dashboard Postgres session table.
3. **Guild authority**
   - Dashboard can pre-filter guilds using Discord OAuth guild permission bits.
   - Bot must re-check every read/write with live guild/member/capability checks via `/control/authority` or action-specific endpoints.
4. **Writes**
   - Every write request includes actor user ID, guild ID, idempotency key, and CSRF token.
   - Bot resolves live member and calls the audited seam; dashboard must not write bot DB tables directly.
5. **Protections**
   - CSRF tokens for form posts; same-site cookies; rate limits per IP/user/guild/action.
   - Audit logs in bot-owned audit system for bot-affecting writes.
   - Public/private zone separation in routing and templates.
   - Secret masking and never rendering full env values; Railway writes owner-only.
   - Control API bearer token on Railway private network only; rotateable `CONTROL_API_TOKEN`.

## Required bot-side foundations

- Expand `disbot/control_api.py` from read-only ping/authority to read-model endpoints first:
  - command manifest;
  - settings specs + per-guild effective values;
  - help overlay/catalogue;
  - command routing policies;
  - audit/freshness metadata.
- Add mutation endpoints only after read endpoints and auth are stable:
  - settings → `SettingsMutationPipeline`;
  - help → `help_overlay_mutation`;
  - cog routing → `command_routing.set_policy`;
  - user config/participation → existing participation/user-config seams.
- Add explicit panel metadata/registry before any panel layout editor.
- Keep `dashboard/` decoupled from bot imports; all live bot data crosses HTTP/control API or generated JSON.

## Risks/blockers/gates

- **Open PR unknown:** external PR list was not available here; check GitHub before implementation and stop if a live PR owns this scope.
- **Owner/creds gated:** Discord OAuth secret, session secret, control token, Railway API token, GitHub issue token/app, DB choice.
- **Security risk:** any direct dashboard write to bot DB bypasses audit/cache/event seams and is blocked.
- **Correctness risk:** command/button metadata remains approximate until a bot manifest and panel registry exist.
- **UX risk:** calling `/status` “live” over-promises until bot/Railway/GitHub probes exist.
- **Architecture risk:** importing `disbot/` from `dashboard/` would couple deploy dependencies and violate the current boundary.

## Tests/verification plan

Current read-only checks:

```bash
python3.10 scripts/export_dashboard_data.py
python3.10 scripts/scan_commands.py --summary
python3.10 -m pytest tests/unit/scripts/test_export_dashboard_data.py tests/unit/scripts/test_scan_commands.py
python3.10 -m pytest tests/unit/dashboard/
```

Add next:

- CI guard that `dashboard/data/dashboard.json` equals a fresh export.
- Unit tests for every control API read endpoint, including dormant/no-token behavior.
- Contract tests for manifest schema stability.
- Reconciliation tests: scanner ↔ manifest ↔ ledger ↔ `bot.walk_commands()` ↔ `bot.tree.walk_commands()` ↔ status count.
- Template smoke tests for every route with representative fresh/stale/unavailable data.
- Security tests: auth required, CSRF required, bot-side authority re-check rejects forged guild/user claims, rate-limit behavior, secret masking.

## Suggested first implementation PRs

1. **PR A — dashboard trust/freshness badges**
   - Add generated-at/build/stale badges and “static scan vs runtime verified” labels, especially on `/commands` and `/status`.
2. **PR B — per-command detail pages (read-only)**
   - Use existing JSON only; include source file, aliases, classification, warning for approximate button-backed metadata.
3. **PR C — bot command manifest read endpoint**
   - Dormant behind `CONTROL_API_TOKEN`; no mutations; tests only.
4. **PR D — dashboard dynamic manifest consumer**
   - Optional fetch with cache/fallback to committed JSON; visible freshness state.
5. **PR E — Discord OAuth/session foundation**
   - Login/logout/server picker shell; no bot writes.
6. **PR F — help/settings/cog-routing read models**
   - Authenticated read-only server admin pages over the bot API.
7. **PR G — first live write: help overlay only**
   - Smallest useful editor; uses `help_overlay_mutation`; full audit and authority tests.
8. **PR H — settings editor**
   - Fronts `SettingsMutationPipeline` with `SettingSpec` validation.
9. **PR I — panel registry/layout design**
   - Plan and implement bot data model before any drag/drop UI.

## Open owner questions

1. Confirm no active open PR already owns dashboard auth/control API/editor scope.
2. Confirm the production OAuth app credentials and session/control secrets are ready to set in Railway.
3. Choose the dashboard mutable-state store for bugs/ideas/checklists: dashboard Postgres vs GitHub-first vs hybrid.
4. Decide whether owner-only env value management should ship before or after server-admin bot controls.
5. Approve the panel-layout model scope before any drag/drop UI is built.

## Context delta

### needed-not-pointed

- `disbot/control_api.py` to verify the private API is partial/dormant, not merely planned.
- `scripts/check_dashboard_data.py` and recent tests to understand dashboard JSON integrity direction.
- Panel/view files under `disbot/views/**` and button-heavy legacy cogs to confirm hardcoded rows/custom IDs.
- `tests/unit/runtime/test_control_api.py` and command-ledger tests to understand existing guarantees.

### pointed-not-needed

- Full contents of every `cogs/*/schemas.py` were not needed for this planning pass because `scan_setting_specs.py` already maps the intended metadata extraction path.
- Full template internals beyond route/layout/navigation patterns were not needed; route/template inventory plus app data flow was enough.

### discovered-by-hand

- `dashboard/README.md` route list omits the newer `/status` page even though `dashboard/app.py` implements it.
- `docs/planning/dashboard-live-editor-plan.md` is newer than parts of `docs/current-state.md` regarding the bot control API: the API foundation is merged but mutation endpoints remain absent.
- The local environment lacks `gh` and a git remote, blocking direct open-PR verification.
