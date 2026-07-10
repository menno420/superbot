# Quiet hours design

> **Status:** `plan` — design only, not implemented.

## Goal

Add a per-guild quiet-hours window during which SuperBot suppresses clearly non-essential notifications while preserving commands, moderation, audit, security, setup, and state-changing behavior.

The first implementation should stay small enough to fit under roughly 150 new runtime lines by reusing the existing settings, mutation, cache, and audit seams instead of adding a table, scheduler, or global send wrapper.

## User-facing behavior

Each guild gets two scalar settings:

| Setting | Type | Default | Meaning |
| --- | --- | --- | --- |
| `notifications.quiet_hours_enabled` | `bool` | `False` | Master switch for quiet-hours suppression. |
| `notifications.quiet_hours_window_utc` | `str` | `""` | UTC window in `HH:MM-HH:MM` format, for example `22:00-07:00`. Empty means no configured window. |

The v1 window is UTC-only. This avoids timezone storage, daylight-saving transitions, ambiguous local times, and per-guild locale UI. If a guild wants local quiet hours, the operator converts the local window to UTC when configuring the setting.

Window semantics:

- `09:00-17:00` suppresses from 09:00 inclusive through 17:00 exclusive UTC.
- `22:00-07:00` crosses midnight and suppresses from 22:00 through midnight, then midnight through 07:00 UTC.
- `00:00-00:00` should be rejected by validation because it is ambiguous between "all day" and "never".
- Malformed values should fail validation on write. Runtime parsing should still fail open and treat the setting as disabled if an unexpected bad value is encountered.

## Existing seams to reuse

### Settings declaration

Declare both fields as `SettingSpec` values. `SettingSpec` already carries the scalar type, default, canonical `settings_key`, capability gate, hint, validator, and input metadata needed by the Settings UI and mutation pipeline.

Exact seam to reuse:

- `core.runtime.subsystem_schema.SettingSpec`

Suggested declaration shape:

```python
SettingSpec(
    name="quiet_hours_enabled",
    value_type=bool,
    default=False,
    settings_key=NOTIFICATIONS_QUIET_HOURS_ENABLED,
    capability_required="notifications.settings.configure",
    hint="Suppress non-essential bot notifications during the configured window.",
)

SettingSpec(
    name="quiet_hours_window_utc",
    value_type=str,
    default="",
    settings_key=NOTIFICATIONS_QUIET_HOURS_WINDOW_UTC,
    capability_required="notifications.settings.configure",
    validator=_validate_quiet_hours_window,
    hint="UTC quiet-hours window in HH:MM-HH:MM format, e.g. 22:00-07:00.",
)
```

A tiny `notifications` subsystem schema is enough if no better existing platform subsystem owns this behavior. The schema only needs to register these settings and does not need a custom panel.

### Settings key constants

Add canonical constants under `utils.settings_keys`, rather than using raw string literals:

```python
NOTIFICATIONS_QUIET_HOURS_ENABLED = "notifications_quiet_hours_enabled"
NOTIFICATIONS_QUIET_HOURS_WINDOW_UTC = "notifications_quiet_hours_window_utc"
```

Exact seams to reuse:

- `utils.settings_keys` package for canonical setting key ownership
- `utils.settings_keys.__all__` and re-exports for public key access

### Mutation path

All writes must go through the existing settings mutation pipeline. Do not call `db.set_setting`, `settings_audit.set_value_with_audit`, or any lower-level DB helper from a quiet-hours command or UI.

Exact seam to reuse:

- `services.settings_mutation.SettingsMutationPipeline.set_value`

The existing pipeline already performs capability checks, type coercion, validator execution, audited DB write, cache invalidation, `audit.action_recorded` emission, and `settings.changed` emission.

### Read path

Runtime notification guards should resolve settings through the scalar settings resolver.

Exact seam to reuse:

- `services.settings_resolution.resolve_setting`

The helper should read:

```python
await resolve_setting(guild_id, "notifications", "quiet_hours_enabled")
await resolve_setting(guild_id, "notifications", "quiet_hours_window_utc")
```

This keeps the per-guild, global-default, and declared-default behavior consistent with the rest of the settings platform.

### Cache behavior

No quiet-hours-specific cache should be added. `resolve_setting` already reads through the typed setting accessor, and the mutation pipeline already invalidates the changed key after a successful write.

Exact seams to reuse:

- `utils.guild_config_accessors.get_setting_value`
- `utils.guild_config_accessors.invalidate_setting_value`

### Audit behavior

No new audit event is needed. Quiet-hours configuration changes are normal scalar setting mutations and should audit through the existing settings pipeline.

Exact seams to reuse:

- `services.audit_events.emit_audit_action`
- existing `audit.action_recorded` event
- existing `settings.changed` event

Per-notification suppression should not emit an audit event in v1. Emitting an audit row every time an XP or economy notification is skipped would create noisy logs and partly defeat the point of quiet hours.

## Runtime helper

Add one small helper module, for example `services/quiet_hours.py`, with this public function:

```python
async def suppress_nonessential_notifications(
    guild_id: int,
    *,
    now: datetime | None = None,
) -> bool:
    """Return True when non-essential guild notifications should be skipped."""
```

Implementation outline:

1. Resolve `notifications.quiet_hours_enabled`.
2. If disabled, return `False`.
3. Resolve `notifications.quiet_hours_window_utc`.
4. If empty, return `False`.
5. Parse `HH:MM-HH:MM` into two `datetime.time` values.
6. Compare against `now` in UTC.
7. Return `True` if the current UTC time is inside the configured window.
8. On unexpected resolver or parser errors, log a warning and return `False`.

Fail-open behavior is intentional: quiet hours should not break notification-producing code paths if configuration is bad or temporarily unreadable.

## First call sites

Do not monkeypatch Discord sends and do not add a global transport wrapper. Quiet hours should be an explicit opt-in at known non-essential send sites.

Recommended first call sites:

1. `cogs.xp.listener.announce_level_up`
   - Suppress only the public level-up celebration embed.
   - Do not suppress XP award bookkeeping or XP threshold role assignment.

2. `utils.helpers.post_log_embed`
   - Suppress economy-style log embeds routed through the shared helper.
   - This gives a useful amount of noise reduction with a single guard.

Future non-essential announcement senders may opt in by calling the same helper.

## Essential messages that must not be suppressed

Quiet hours must not block:

- command responses;
- setup/configuration confirmations;
- moderation actions or moderation DMs;
- security, automod, or safety alerts;
- audit logs;
- support-ticket lifecycle messages;
- role grants, XP awards, or other state mutations;
- errors that operators need in order to repair a broken configuration.

This keeps v1 conservative: the feature suppresses noise, not functionality.

## Implementation-size budget

A plausible implementation remains under 150 new runtime lines:

| Area | Approximate lines |
| --- | ---: |
| settings key constants and exports | 8-15 |
| two `SettingSpec` declarations plus validator | 35-50 |
| `services/quiet_hours.py` parser/helper | 45-55 |
| first call-site guards | 8-15 |
| total | about 96-135 |

Tests and docs can be added separately without changing the runtime-size goal.

## What I deliberately did NOT build

1. Per-guild time zones
   - Time zones introduce additional settings, UI, validation, and daylight-saving behavior. UTC is enough for v1.

2. Deferred notification queues
   - The requirement is suppression, not delayed delivery. Queues would require persistence, scheduling, duplicate handling, and expiry rules.

3. A global `send` wrapper or monkeypatch
   - A global wrapper could accidentally suppress command replies, moderation confirmations, audit logs, or security alerts. Explicit call-site guards are safer.

4. Per-channel, per-role, or per-category quiet-hours policies
   - These are useful later, but the first version only needs one guild-wide window for clearly non-essential notifications.

5. Per-suppression audit records
   - Auditing every skipped notification would add noise and work against the quiet-hours goal. Only configuration changes need audit records in v1.

6. A custom `!quiet-hours` command
   - The settings manager and control API already have a mutation seam. A custom command would either duplicate that path or become a thin wrapper around it, which is unnecessary for v1.
