# EventBus wiring inventory

> **Status:** reference snapshot. Source wins.
>
> **Last audited:** 2026-07-10.
>
> **Scope:** `disbot/` source only. This page inventories in-process EventBus
> wiring: every `bus.emit(...)` / `_event_bus.emit(...)` call and every
> `bus.on(...)` registration found by reading source directly. It does **not**
> include Discord framework listeners such as `@commands.Cog.listener()`.

## How to refresh this inventory

Use the wiring-map tool first, then grep any unresolved forwarding helpers by
hand before editing this page:

```bash
python scripts/wiring_map.py
rg -n "bus\.emit\(|_event_bus\.emit\(|bus\.on\(|register_refresh\(" disbot
```

`python scripts/wiring_map.py --check` gates on catalogue drift, not on
emitted-without-subscriber events. Many EventBus events are deliberately
advisory facts emitted for observability or future consumers.

## Reading the table

| Status | Meaning |
|---|---|
| `wired` | At least one in-repo emitter and one in-repo subscriber are statically visible or manually resolved from a forwarding helper. |
| `emitted-only` | The event is emitted in `disbot/`, but no concrete in-repo `bus.on(...)` subscriber was found. This can be intentional for advisory/observability events. |
| `subscribed-only` | A concrete subscriber exists, but no concrete in-repo emitter was found. |
| `dynamic` | The call uses a runtime event-name variable, so the concrete event cannot be proven from the call itself. |

## Inventory

| Event name | Emitter file:line | Subscriber file:line | Status |
|---|---|---|---|
| `ai.instruction.profile_changed` | `disbot/services/ai_instruction_mutation.py:123` | — | emitted-only |
| `ai.orchestration.category_changed` | `disbot/services/ai_orchestration_mutation.py:196` | — | emitted-only |
| `ai.orchestration.channel_changed` | `disbot/services/ai_orchestration_mutation.py:160` | — | emitted-only |
| `ai.orchestration.guild_changed` | `disbot/services/ai_orchestration_mutation.py:124` | — | emitted-only |
| `ai.policy.category_changed` | `disbot/services/ai_policy_mutation.py:304` | — | emitted-only |
| `ai.policy.channel_changed` | `disbot/services/ai_policy_mutation.py:247` | — | emitted-only |
| `ai.policy.guild_changed` | `disbot/services/ai_policy_mutation.py:173` | — | emitted-only |
| `ai.policy.projection_failed` | `disbot/services/ai_policy_mutation.py:557` | — | emitted-only |
| `ai.policy.role_changed` | `disbot/services/ai_policy_mutation.py:361` | — | emitted-only |
| `ai.review_logged` | `disbot/services/ai_review_log_service.py:297` | `disbot/cogs/ai_review_cog.py:109` | wired |
| `audit.action_recorded` | `disbot/services/audit_events.py:75` | `disbot/services/server_logging.py:1856` | wired |
| `automation.rule_changed` | `disbot/services/automation_mutation.py:452` | — | emitted-only |
| `automod.rule_triggered` | `disbot/cogs/automod/listener.py:114` | — | emitted-only |
| `bindings.changed` | `disbot/services/binding_mutation.py:531` | — | emitted-only |
| `btd6.version_detected` | `disbot/services/btd6_patch_service.py:150` | `disbot/services/btd6_version_announce.py:111` | wired |
| `channel.lifecycle_changed` | `disbot/services/channel_lifecycle_service.py:609` | — | emitted-only |
| `counters.updated` | `disbot/services/counter_service.py:130` | — | emitted-only |
| `economy.balance_changed` | `disbot/services/economy_service.py:81`; `disbot/services/economy_service.py:118`; `disbot/services/economy_service.py:270`; `disbot/services/economy_service.py:278`; `disbot/services/economy_service.py:319`; `disbot/services/farm_workflow.py:158`; `disbot/services/farm_workflow.py:235`; `disbot/services/farm_workflow.py:296`; `disbot/services/fishing_workflow.py:642`; `disbot/services/fishing_workflow.py:721`; `disbot/services/game_wager_workflow.py:460`; `disbot/services/mining_workflow.py:258`; `disbot/services/mining_workflow.py:533`; `disbot/services/shop_purchase_workflow.py:91`; `disbot/services/skill_service.py:151`; `disbot/services/skill_service.py:210`; `disbot/services/treasury_service.py:104`; `disbot/services/treasury_service.py:167` | — | emitted-only |
| `environment_tier.changed` | `disbot/services/rollout_mutation.py:613` | — | emitted-only |
| `feature_flags.changed` | `disbot/services/rollout_mutation.py:513` | — | emitted-only |
| `game_xp.awarded` | `disbot/services/game_xp_service.py:200` | — | emitted-only |
| `game_xp.level_up` | `disbot/services/game_xp_service.py:210` | — | emitted-only |
| `governance.cache.invalidated` | `disbot/governance/events.py:34` via `emit_event(event_name, ...)` | `disbot/core/runtime/__init__.py:182` | wired |
| `governance.cleanup.changed` | `disbot/governance/events.py:34` via `emit_event(event_name, ...)` | `disbot/core/runtime/__init__.py:183` | wired |
| `governance.execution.allowed` | `disbot/governance/events.py:34` via `emit_event(event_name, ...)` | — | emitted-only |
| `governance.execution.denied` | `disbot/governance/events.py:34` via `emit_event(event_name, ...)` | — | emitted-only |
| `governance.visibility.changed` | `disbot/governance/events.py:34` via `emit_event(event_name, ...)` | `disbot/core/runtime/__init__.py:181` | wired |
| `image_moderation.flagged` | `disbot/cogs/image_moderation/listener.py:185` | — | emitted-only |
| `karma.granted` | `disbot/services/karma_service.py:178` | — | emitted-only |
| `moderation.action_taken` | `disbot/services/moderation_service.py:227` | `disbot/services/server_logging.py:1854`; `disbot/services/server_logging.py:1855` | wired |
| `participation.changed` | `disbot/services/participation_mutation.py:236` via helper emitting at `disbot/services/participation_mutation.py:653` | — | emitted-only |
| `resource.provisioned` | `disbot/services/resource_provisioning.py:867` | — | emitted-only |
| `role.lifecycle_changed` | `disbot/services/role_lifecycle_service.py:400` | — | emitted-only |
| `rollout.advanced` | `disbot/services/rollout_mutation.py:565` | — | emitted-only |
| `security.account_flagged` | `disbot/services/security_service.py:426` via helper emitting at `disbot/services/security_service.py:316` | — | emitted-only |
| `security.raid_detected` | `disbot/services/security_service.py:382` via helper emitting at `disbot/services/security_service.py:316` | — | emitted-only |
| `settings.changed` | `disbot/services/settings_mutation.py:647` | — | emitted-only |
| `subscription.changed` | `disbot/services/participation_mutation.py:335` via helper emitting at `disbot/services/participation_mutation.py:653` | — | emitted-only |
| `ticket.closed` | `disbot/services/ticket_mutation.py:332` via helper emitting at `disbot/services/ticket_mutation.py:633` | — | emitted-only |
| `ticket.open_requested` | `disbot/services/ai_tools.py:2493` | `disbot/cogs/ticket_cog.py:58` | wired |
| `ticket.opened` | `disbot/services/ticket_mutation.py:201` via helper emitting at `disbot/services/ticket_mutation.py:633` | `disbot/cogs/ticket_cog.py:57` | wired |
| `user_preference.changed` | `disbot/services/participation_mutation.py:447` via helper emitting at `disbot/services/participation_mutation.py:653` | — | emitted-only |
| `user_visibility.changed` | `disbot/services/participation_mutation.py:542` via helper emitting at `disbot/services/participation_mutation.py:653` | — | emitted-only |
| `welcome.member_greeted` | `disbot/services/welcome_service.py:267` | — | emitted-only |
| `xp.awarded` | `disbot/services/xp_service.py:126` | — | emitted-only |
| `xp.level_up` | `disbot/services/xp_service.py:136` | `disbot/cogs/community_spotlight_cog.py:252` | wired |
| `xp.reset` | `disbot/services/xp_service.py:239` | — | emitted-only |
| `<dynamic event argument>` | — | `disbot/core/runtime/live_update_scheduler.py:96` inside `register_refresh(subsystem, event, refresh_fn)` | dynamic |

## Current emitted-only events

These events are emitted in `disbot/` with no concrete in-repo subscriber found
in this audit:

- `ai.instruction.profile_changed`
- `ai.orchestration.category_changed`
- `ai.orchestration.channel_changed`
- `ai.orchestration.guild_changed`
- `ai.policy.category_changed`
- `ai.policy.channel_changed`
- `ai.policy.guild_changed`
- `ai.policy.projection_failed`
- `ai.policy.role_changed`
- `automation.rule_changed`
- `automod.rule_triggered`
- `bindings.changed`
- `channel.lifecycle_changed`
- `counters.updated`
- `economy.balance_changed`
- `environment_tier.changed`
- `feature_flags.changed`
- `game_xp.awarded`
- `game_xp.level_up`
- `governance.execution.allowed`
- `governance.execution.denied`
- `image_moderation.flagged`
- `karma.granted`
- `participation.changed`
- `resource.provisioned`
- `role.lifecycle_changed`
- `rollout.advanced`
- `security.account_flagged`
- `security.raid_detected`
- `settings.changed`
- `subscription.changed`
- `ticket.closed`
- `user_preference.changed`
- `user_visibility.changed`
- `welcome.member_greeted`
- `xp.awarded`
- `xp.reset`

## Current subscribed-only events

No concrete event name is subscribed without a known in-repo emitter after
manual resolution of the forwarding helpers. The only unresolved subscription
shape is the dynamic scheduler registration at
`disbot/core/runtime/live_update_scheduler.py:96`; it depends on callers passing
an event name into `register_refresh(...)`.
