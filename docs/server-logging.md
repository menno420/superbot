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

## Optional public moderation log (server-management PR10)

A second, **operator-opt-in** subscriber on `moderation.action_taken` mirrors
selected moderation actions to a **public** channel — separate from the staff
mod-log, and with the **acting moderator redacted** (the maintainer's choice for
a public surface).

* Config is **moderation-owned** (`disbot/cogs/moderation/schemas.py`, read via
  `services.moderation_config.load_policy`), not a `logging.*` key:
  * `moderation_public_log_channel` — the public channel (a `channel` SettingSpec;
    empty = off).
  * `moderation_public_log_actions` — `none` (default) / `bans` / `removals`
    (kick + ban) / `all` (warn + timeout + kick + ban).  unban, clearwarnings, the
    post-action sweep, and system `auto_delete:*` are **never** publicised.
* Delivery lives in `server_logging` (it owns log delivery): the dedicated
  `_on_moderation_action_public` subscriber pre-filters to disciplinary actions,
  loads the moderation policy, and posts `format_public_log_embed` (member +
  reason; **no actor, no guild id**) to `public_log_channel`.
* **Independent of `logging.enabled`** — gated solely by its own config, since an
  operator who sets a public channel clearly wants it.  Fail-safe + counted via
  `mod_public_sent` / `mod_public_skipped`.

## Server event logging v1 (Q-0109)

> **Status:** `binding` — shipped as band slot 5 of the safety/community
> family plan. Default: **OFF** per-category.

The passive layer. Where the moderation/audit subscribers react to
**bus events**, this layer reacts to **Discord gateway events** —
posting an embed when something happens in the server that an operator
might want a record of. Owner scope (Q-0109): **message edits and
deletions · member joins and leaves · role grants/revocations**. Voice
activity is deliberately out of v1 scope.

### Where it lives

* **Listeners** — `cogs/logging_cog.py` (the `LoggingCog`) gains five
  `@commands.Cog.listener()` methods (`on_message_delete`,
  `on_message_edit`, `on_member_join`, `on_member_remove`,
  `on_member_update`). Each applies a cheap structural filter (skip
  bots / DMs / no-op embed-only edits / non-role member updates) so the
  hot path does no DB work, then delegates to a `server_logging.log_*`
  handler. The `on_member_join` listener coexists with the autorole
  cog's own — discord.py dispatches to every listener independently.
* **Handlers + embeds** — `services/server_logging.py`
  (`log_message_delete` / `log_message_edit` / `log_member_join` /
  `log_member_leave` / `log_role_change`, plus the matching
  `format_*_embed` builders). Each handler loads the policy, gates,
  resolves the routed channel, and posts — fully fail-safe. Each
  `format_*_embed` also puts the relevant **subject's** avatar + display
  name in the embed **author slot** (`_set_subject_author`) — a face per
  entry for at-a-glance scanning. Purely additive (the structured fields
  are unchanged) and network-free (the embed just references the avatar's
  CDN url, so there is nothing to fetch and no failure path). **Every log
  surface carries the same face:** the passive-event embeds use the object
  they already hold, and the **moderation** + **audit** embeds — which
  carry only ids — resolve one via `_resolve_subject_user` (guild member
  cache, then the bot's global user cache, so a just-banned member still
  gets a face; cache-only, never a network call). The mod-log shows the
  **target**; the audit embed shows the **actor**; the public mod-log shows
  the **target** only (never the moderator, preserving that surface's
  redaction).
* **Config read model** — `services/server_logging_config.py`
  (`EventLoggingPolicy` + `load_policy`), mirroring `automod_config`.

### Gating (off by default)

Every event requires **two** flags: the existing master
`logging.enabled` **and** the per-category flag
(`logging.messages_enabled` / `logging.members_enabled` /
`logging.roles_enabled`). All default OFF, so a fresh guild — and a
guild that already enabled `logging.enabled` only for moderation
logging — sees no new behaviour until it opts a category in. Configured
through the `!settings` widget (the four new `SettingSpec`s) or
`!logging status`.

### Routing (owner-configurable)

`logging.event_routing` selects the layout — the exact Q-0109 choice
the `mock_logging_routing` UX exhibit renders:

| Mode | Behaviour |
|---|---|
| `combined` (default) | every category → the `events` route (`events_channel`). |
| `per_category` | messages → `message_log`, members → `member_log`, roles → `role_log`; each falls back to `events_channel` when its own channel is unset. |

The event routes are added to the same route table as the
moderation/severity routes, so they configure through the existing
**Routes panel** (`!logging routes`) and the `BindingMutationPipeline`.
Critically, the event routes fall back to `events` (then nothing), never
to `mod` — passive-event noise must not land in the moderation-action
channel.

### Routes panel order + per-route binding (operator UX)

The Routes panel (`!logging routes`, or the 🗺️ **Routes** button on the logging
panel) lists every route in **roots-first** order — `mod` and `events` lead
because they are the two fallback roots: set those two and every route is
delivered *somewhere* (severity / audit / cleanup fall back to `mod`; the
per-category event routes fall back to `events`). Everything below refines one of
them. The order is derived from the live fallback DAG and pinned to
`tools/sim/settings_order_sim.py` by
`tests/unit/invariants/test_settings_order.py` — roots-first cut
scroll-to-full-coverage from 7 → 1 vs the old category-first order.

Each route binds **independently**: pick it, then **Set Channel** (bind an
existing channel, via `BindingMutationPipeline`) or **Create Channel** (provision
a new one, via `ResourceProvisioningPipeline`). Per-route Set Channel works for
**every** route, including the Q-0109 event routes — the `_KIND_TO_LABEL` gap
that crashed Set Channel for `events` / `message_log` / `member_log` / `role_log`
(a `KeyError` surfaced as *"An error occurred. Please try again."*) is fixed and
guarded by `test_logging_routes_panel.test_route_labels_cover_every_kind`.

### Privacy

Deleted-message logging surfaces content members removed. Q-0109
requires this be disclosed: the `messages_enabled` SettingSpec hint
carries a ⚠️ privacy line, and the setup wizard's logging-presets
section states it too. Actor attribution for role changes (who granted
the role) needs audit-log integration and is a phase-2 enhancement;
v1 logs role grants/revokes on non-bot members without naming the actor.

### Counters

`event_sent` (delivered), `event_skipped_disabled` (master/category
off), `event_missing_channel` (no routed channel). Delivery failures
share the existing `permission_error` / `send_error` buckets, and a
handler exception bumps `subscriber_errors`.

## What's NOT in PR-11 (the original foundation)

* No new migration; settings live in the legacy `guild_settings` table
  (still true for event logging v1).
* No SettingsRegistry / mutation pipeline integration *(superseded —
  the schema now drives the `!settings` edit flow)*.
* No setup wizard *(superseded — the logging-presets section exists)*.
* No slash commands.
* ~~No per-event subscription toggles~~ *(superseded by event logging
  v1's per-category flags above)*.
* ~~No edit/delete/member-join logging~~ *(superseded by event logging
  v1, Q-0109)*.
* No web dashboard / external log storage / Redis.
