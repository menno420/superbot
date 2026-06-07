# Server logging foundation

> **Status:** `binding` — shipped in Phase 2 PR-11.  Default: **OFF** per-guild.

The server-logging service (`disbot/services/server_logging.py`)
subscribes to the catalogued event `moderation.action_taken` emitted
by `services/moderation_service.py` and posts a structured embed to a
configured per-guild log channel.

This is a small, fail-safe substrate for admin-facing audit visibility.
It is **not** a full analytics or log-storage platform; the goal is to
make every moderation/cleanup action visible in a channel without
relying on Discord's built-in audit log.

## Default behavior

* `logging.enabled` — default OFF.  The service ignores every event.
* `logging.auto_create_channels` — default OFF.  Missing/invalid log
  channels do not cause spontaneous channel creation.
* `logging.mod_channel` — unset.  Mod actions are not logged unless
  set.
* `logging.cleanup_channel` — unset.  Falls back to
  `logging.mod_channel` when unset.

These four keys live in the legacy `guild_settings` table; key
constants live in `disbot/utils/settings_keys/logging.py`.

## Action routing

| Action | Channel slot |
|---|---|
| `warn` / `timeout` / `kick` / `ban` / `unban` / `clearwarnings` / `post_action_cleanup` | `logging.mod_channel` |
| `auto_delete:*` (cleanup auto-deletes) | `logging.cleanup_channel` → falls back to `logging.mod_channel` |

> `post_action_cleanup` is the **moderator-initiated** post-kick/ban message
> sweep (server-management PR10) — distinct from the system `auto_delete:*`
> tier, so it routes to the mod channel like every other manual action.

> The clear-warnings action token is **`clearwarnings`** (one word) — the canonical
> value `moderation_service` emits (server-management PR1 / #521). The embed style
> map keys on it; `clear_warnings` is retained only as a back-compat alias.

## Embed style

| Action | Color | Icon |
|---|---|---|
| `warn` | gold | ⚠️ |
| `timeout` | orange | ⏳ |
| `kick` | dark_orange | 👢 |
| `ban` | red | 🔨 |
| `unban` | green | 🕊️ |
| `clearwarnings` | blurple | 🧹 |
| `auto_delete:*` | dark_grey | 🗑️ |
| `post_action_cleanup` | teal | 🧽 |
| anything else | dark_grey | • |

Every embed includes Target (mention + id), Actor (mention or
`"system"` for auto-delete), Guild id, Reason (truncated to 1000
chars), and any extras from the bus payload (e.g. `until` for
timeouts).

## Fail-safe guarantees

The event bus already swallows handler exceptions
(`disbot/core/events.py` — 5-second timeout, ERROR log, no re-raise),
so a logging failure cannot crash the source moderation/cleanup
action.  Inside the service, each potential failure path is caught
individually and counted:

| Counter | When it increments |
|---|---|
| `sent_total` | Embed delivered successfully. |
| `skipped_disabled` | `logging.enabled` is OFF for the guild. |
| `skipped_no_guild` | Bot not connected, or `guild_id` not in cache. |
| `missing_channel` | Configured channel unresolvable + auto-create OFF. |
| `created_channel` | `ensure_channel` created the fallback channel. |
| `permission_error` | `discord.Forbidden` on send or create. |
| `send_error` | `discord.HTTPException` (or unexpected) on send. |
| `auto_create_error` | `discord.HTTPException` (or unexpected) on create. |
| `subscriber_errors` | The bus subscriber itself raised. |

Counters are exposed via `services.diagnostics_service` under the
name `"server_logging"` and surface in `!platform consistency`
(PR-10) under the "Runtime providers" section.

## Audit logging (Phase 9c)

A second channel slot — `logging.audit_channel` — receives the
canonical `audit.action_recorded` event emitted by every production
mutation pipeline (Phase 9c.1 / 9c.2). Each accepted mutation lands a
single embed describing what was changed, by whom, with the
pre/post values where they are not PII.

> Since server-management PR1 (#521), **moderation actions also emit
> `audit.action_recorded`** — every manual action and every system
> `auto_delete` (the latter with `actor_type="system"`). So a single
> moderation action now lands **two** embeds when both slots are
> configured: the domain embed on `mod_channel` / `cleanup_channel`
> (from `moderation.action_taken`) **and** the generic audit embed on
> `audit_channel` (from `audit.action_recorded`). The two share a
> `mutation_id`. The `mod_logs` row remains the authoritative history;
> the companion is best-effort and never blocks the action.

### Subscriber

`services.server_logging._on_audit_action` is registered on
`audit.action_recorded` by `setup(bot)`. The handler reads the bus
payload, resolves the channel via
`resolve_log_channel(guild, "audit")`, and renders
`format_audit_embed(...)`.

### Routing and fallback

Channel resolution uses the Phase 9a route table:

1. If `logging.audit_channel` is set and resolves to a usable channel
   → that channel.
2. Otherwise the route table falls back to `logging.mod_channel`.
3. If both are unset and `logging.auto_create_channels` is OFF, the
   handler bumps `missing_channel` and returns.
4. If `logging.auto_create_channels` is ON, `ensure_log_channel`
   creates `bot-audit-log` (or the source-tier fallback) and binds
   it on the fly.

The subscriber itself always asks for `kind="audit"` — it never
walks the fallback chain manually. This keeps the route table the
single source of truth.

### Payload contract

`audit.action_recorded` carries 11 keyword fields, all required:

| Field | Type | Notes |
|---|---|---|
| `mutation_id` | str (UUID) | Links the bus event to the per-pipeline DB audit row. |
| `subsystem` | str | High-level area (`"logging"`, `"xp"`, `"governance"`, …). |
| `mutation_type` | str | Pipeline-specific verb token (`"set_value"`, `"upsert_binding"`, `"set_flag_state"`, …). |
| `target` | str | Human-resolvable identifier (`"setting:xp.xp_min"`, `"flag:bindings.primary"`). |
| `scope` | str | `"global"`, `"guild"`, or a scope-type token (`"channel"`, `"category"`, …). |
| `guild_id` | int \| None | Discord guild id, or `None` for global scope. |
| `prev_value` | str \| None | Pre-mutation value, string-rendered. `None` for first writes / PII-shielded preferences. |
| `new_value` | str \| None | Post-mutation value, string-rendered. `None` for clears / PII-shielded preferences. |
| `actor_id` | int \| None | Discord user id, or `None` for system / backfill. |
| `actor_type` | str | Capability-resolver actor type token. |
| `occurred_at` | str (ISO-8601) | DB commit timestamp serialised by the shared publisher. |

The shared publisher lives in
`disbot/services/audit_events.py:emit_audit_action`. Every wired
pipeline imports it directly so the payload contract stays
identical across publishers.

### Counters

The `audit_sent` counter increments per delivered audit embed.
Failure paths share the existing counters in the table above
(`skipped_disabled`, `missing_channel`, `permission_error`,
`send_error`, `subscriber_errors`). Operators monitor counts via
`!platform diagnostics server_logging`.

### Operator workflow (audit channel)

1. Set `logging.enabled` to `true`.
2. Set `logging.audit_channel` to your preferred audit destination
   (typically a staff-only channel). If unset, audit embeds fall
   back to `logging.mod_channel`.
3. Optionally set `logging.auto_create_channels` to `true` so the
   service can create `bot-audit-log` on demand.
4. Verify with `!platform diagnostics server_logging` — every
   accepted mutation should bump `audit_sent`.

## Channel provisioning

When auto-create is enabled and the configured channel id is
missing/invalid, the service calls
`core.runtime.guild_resources.ensure_channel(guild, name, kind="text")`
to create one of:

* `bot-mod-log` for the mod slot.
* `bot-cleanup-log` for the cleanup slot.

The service does NOT depend on `ChannelCog` — channel provisioning
goes through the shared `guild_resources.ensure_channel` primitive
that lives at the runtime layer, so the service and the cog both
call the same code path.  No Cog→Cog dependency.

## Operator workflow

1. Decide which channel(s) you want logs posted to.
2. Set `logging.mod_channel` (and optionally `logging.cleanup_channel`)
   via your settings tool of choice (`!set`, future settings wizard,
   or a direct `guild_settings` row insert).
3. Set `logging.enabled` to `true`.
4. Optionally set `logging.auto_create_channels` to `true` so the
   service falls back to creating `bot-mod-log` / `bot-cleanup-log`
   if your configured ids ever become invalid.
5. Verify with `!logging status`.  Run `!logging test` to fire a
   synthetic warn embed to the configured channel.

## Admin commands

| Command | Effect |
|---|---|
| `!logging status` | Shows enabled state, channel resolution, and counters. |
| `!logging test`   | Sends a synthetic warn embed to the configured log channel. |

Both require Administrator permission.

## What's NOT in PR-11

* No new migration; settings live in the legacy `guild_settings` table.
* No SettingsRegistry / mutation pipeline integration.
* No setup wizard.
* No slash commands.
* No per-event subscription toggles (`logging.enabled` is master switch).
* No edit/delete/member-join logging.
* No web dashboard / external log storage / Redis.

These belong to the broader UX phase that comes after the Command
Surface Ledger and SettingsRegistry land.
