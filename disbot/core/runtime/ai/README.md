# AI Runtime Scaffold

This package is intentionally inert in the AI readiness scaffold PR.

Nothing in production runtime imports this package yet.  The files here define future connector points so later PRs can wire AI support without inventing duplicate abstractions.

## Files

- `contracts.py` defines provider-neutral request, response, suggestion, scope, and diagnostics dataclasses.
- `redaction.py` defines deterministic redaction helpers for future provider payload preparation.
- `suggestion_templates.py` maps AI tasks to advisory suggestion categories and deterministic operation owners.

## Intended future flow

```text
Cog or view
  -> AI service
    -> AI gateway
      -> provider adapter
    -> typed AIResponse / AISuggestion
  -> existing deterministic pipeline after explicit confirmation
```

## Ownership boundaries

AI runtime contracts should not import cogs, views, Discord clients, database modules, or provider SDKs.

Provider SDKs belong behind the future AI gateway.

State changes belong in existing deterministic services.

## Safe next PRs

1. Add AI feature flags and metrics declarations.
2. Add a read-only `!platform ai` diagnostics surface.
3. Extract setup advisor provider calls behind an AI gateway.
4. Add a read-only bot-monitor explainer.
5. Add a log-triage service after a bounded log-event source exists.
