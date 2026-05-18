# Server logging foundation

**Status:** shipped in Phase 2 PR-11.  Default: **OFF** per-guild.

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
| `warn` / `timeout` / `kick` / `ban` / `unban` / `clear_warnings` | `logging.mod_channel` |
| `auto_delete:*` (cleanup auto-deletes) | `logging.cleanup_channel` → falls back to `logging.mod_channel` |

## Embed style

| Action | Color | Icon |
|---|---|---|
| `warn` | gold | ⚠️ |
| `timeout` | orange | ⏳ |
| `kick` | dark_orange | 👢 |
| `ban` | red | 🔨 |
| `unban` | green | 🕊️ |
| `clear_warnings` | blurple | 🧹 |
| `auto_delete:*` | dark_grey | 🗑️ |
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
