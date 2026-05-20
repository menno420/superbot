# SuperBot AI Readiness Plan

Status: planning and inert scaffold only. This document does not change runtime behavior.

## Purpose

SuperBot already has a narrow AI surface in the setup wizard. The next step should be a reusable AI platform layer rather than direct provider calls inside individual cogs.

The goal is to prepare for setup guidance, diagnostics explanations, log triage, settings help, command help, and future code-context assistance while preserving the existing architecture.

## Architectural rule

AI may recommend, summarize, classify, and explain.

Deterministic SuperBot services must continue to own all state changes.

Any future AI-produced recommendation must be converted into a typed operation and validated by the existing service layer before anything is applied.

## Existing foundations to reuse

- setup advisor boundary for Smart Suggestions
- diagnostics snapshot registry
- platform diagnostics panel
- feature flag runtime
- Prometheus metrics service
- centralized message pipeline
- settings and binding mutation pipelines
- resource provisioning pipeline
- event catalogue

AI readiness should extend those surfaces instead of creating parallel systems.

## Proposed layers

### AI gateway

Future target: `disbot/services/ai_gateway.py`.

The gateway should become the only provider boundary. It should resolve provider and model, apply redaction, enforce timeouts, emit metrics, and return typed responses. It must not write database state or Discord state directly.

### AI contracts

Future target: `disbot/core/runtime/ai/`.

Contracts should describe request scopes, task names, response payloads, suggestion records, and diagnostic snapshots. They should stay provider-neutral.

### AI diagnostics

Future target: `!platform ai`.

The platform surface should show provider status, active model, feature flag status, fallback state, recent failures, latency, and whether redaction is enabled. It should never expose sensitive values.

### AI feature flags

Future flags should include:

- `ai.primary`
- `ai.setup_advisor.enabled`
- `ai.general_cog.enabled`
- `ai.log_triage.enabled`
- `ai.bot_monitor.enabled`
- `ai.code_context.enabled`
- `ai.moderation_assist.enabled`

Broad AI behavior should default off until the gateway and diagnostics are proven.

## Candidate services

### Setup advisor v2

Improves Smart Suggestions with better explanations, confidence, and operation previews.

### Bot monitor explainer

Summarizes diagnostics, consistency checks, runtime status, slow paths, and failed tasks into operator-facing guidance.

### Log triage

Groups recent warning/error events into incidents and suggests the next deterministic diagnostic command to run.

### Settings assistant

Explains configurable settings and proposes changes that are later validated through the settings mutation pipeline.

### Help assistant

Answers questions about commands, panels, and subsystem behavior using command/help metadata.

### Code context assistant

Uses a generated context pack to explain cogs, commands, schemas, settings, events, and database ownership without runtime source-code scanning.

## Rollout order

### Phase A: inert readiness scaffold

Add docs, contracts, and templates only. No runtime imports. No behavior change.

### Phase B: diagnostics visibility

Add flags, metrics declarations, diagnostics provider, and a `!platform ai` read-only panel.

### Phase C: gateway extraction

Move provider calls behind the gateway while preserving existing setup advisor behavior.

### Phase D: read-only AI monitor

Add a bot-monitor summary service using diagnostics and consistency reports.

### Phase E: log triage MVP

Add bounded log-event ingestion and admin-only triage summaries.

### Phase F: general AI hub

Add an AI cog and UI hub that delegates to services instead of calling providers directly.

## Review checklist

Future AI PRs should answer:

1. Which service owns deterministic state changes?
2. Which feature flag gates the behavior?
3. Which diagnostics surface reports status?
4. Which metrics report latency and failures?
5. Which redaction rules run before provider calls?
6. Which permission tier can invoke it?
7. What happens if the provider is unavailable?
8. Does the bot still work without external AI?
