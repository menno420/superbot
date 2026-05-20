# AI Service Integration Map

Status: planning artifact. No runtime behavior is changed by this file.

## Purpose

This map shows where future AI-assisted behavior should connect to existing SuperBot services. It is meant to reduce future implementation time and prevent duplicate architecture.

## Connector rules

1. Cogs own Discord commands and UI entry points.
2. Services own orchestration and deterministic state changes.
3. Runtime modules own registries, feature flags, event flow, and typed platform utilities.
4. AI provider calls must go through one gateway.
5. AI output must be advisory unless converted into validated operations.

## Recommended connector points

### Setup wizard

Existing surfaces:

- `services.setup_ai_advisor`
- `services.guild_snapshot`
- `services.setup_plan`
- `services.setup_operations`
- `views.setup.ai_review`
- `views.setup.hub`

AI opportunity:

- richer setup suggestions
- operation previews
- explanation of why each binding or setting is recommended
- setup readiness summary

Safe path:

`Setup UI -> SetupAdvisor -> AIGateway -> typed SetupPlanDraft -> SetupOperation preview -> existing apply dispatcher`

### Diagnostics and platform hub

Existing surfaces:

- `services.diagnostics_service`
- `services.platform_consistency`
- `cogs.diagnostic._platform_embeds`
- `views.diagnostic.platform_panel`

AI opportunity:

- explain platform consistency output
- summarize runtime health
- identify likely next diagnostic command
- translate technical findings into operator actions

Safe path:

`Platform panel -> AI monitor service -> diagnostics snapshots -> AIGateway -> read-only summary embed`

### Metrics and health

Existing surfaces:

- `services.metrics`
- `healthserver.py`

AI opportunity:

- summarize slow commands
- identify unusual latency or fallback patterns
- produce deployment health summaries

Safe path:

`metrics snapshot/derived summary -> AI monitor service -> read-only output`

### Settings manager

Existing surfaces:

- `services.settings_mutation`
- `services.settings_resolution`
- `core.runtime.subsystem_schema`
- settings UI views

AI opportunity:

- explain settings
- propose configuration changes
- generate safe operation previews

Safe path:

`AI settings assistant -> proposed SettingChange -> SettingsMutationPipeline after explicit user confirmation`

### Binding and resource provisioning

Existing surfaces:

- `services.binding_mutation`
- `services.resource_provisioning`
- subsystem schemas
- resource requirements

AI opportunity:

- recommend channel and role bindings
- explain missing resources
- propose setup packs for server types

Safe path:

`AI recommendation -> schema validation -> resource/binding preview -> existing provisioning/binding pipeline`

### Message pipeline

Existing surfaces:

- `core.runtime.message_pipeline`
- moderation services
- cleanup/counting/chain stages

AI opportunity:

- optional classification or moderation assistance
- summarize repeated message-stage failures
- identify noisy stages

Safe path:

AI stages should be disabled by default, rate-limited, and advisory in early versions. Deterministic moderation rules remain authoritative.

### Help and command navigation

Existing surfaces:

- help cog
- command registry
- command panels
- subsystem registry

AI opportunity:

- answer how-to questions
- recommend the correct command panel
- explain admin commands based on permissions

Safe path:

`Help question -> command/help metadata -> AIGateway -> response filtered by caller permission`

### Event catalogue and audit

Existing surfaces:

- `core.events_catalogue`
- audit events
- domain-specific events

AI opportunity:

- explain recent platform events
- summarize mutation history
- identify related actions across services

Safe path:

`bounded event summary -> AI explainer -> read-only output`

## Suggested AI task identifiers

Use stable task names for metrics and policy:

- `setup.suggest`
- `setup.explain`
- `platform.explain_status`
- `platform.explain_consistency`
- `logs.triage`
- `settings.explain`
- `settings.propose`
- `help.answer`
- `code_context.explain`
- `moderation.assist`

## Suggested permission tiers

- Normal users: help assistant only.
- Moderators: moderation explanations and basic server help.
- Admins: settings, setup, diagnostics summaries.
- Server owner: setup apply previews and deployment-sensitive diagnostics.
- Platform owner: code context, provider status, rollout diagnostics.

## Suggested failure behavior

When AI is unavailable:

- setup falls back to deterministic suggestions
- diagnostics still show raw platform embeds
- log triage returns a deterministic recent-error list
- help assistant falls back to command metadata
- settings assistant returns the relevant settings panel

The bot should never require AI to remain operational.
