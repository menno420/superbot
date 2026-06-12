# AI Runtime (core/runtime/ai)

The **active** AI platform layer: provider-neutral contracts, the gateway,
routing, feature flags, safety, and the natural-language stage that the AI
cog and services consume. *(Header rewritten 2026-06-12, P2 doc-drift sweep —
this README previously described the package as "intentionally inert"
scaffold; that was true at the readiness-scaffold PR and stale ever since
the gateway/orchestration waves shipped. The AI readiness map flagged it.)*

## Files

- `contracts.py` — provider-neutral request/response/suggestion/scope and
  diagnostics dataclasses (the typed seam everything else speaks).
- `gateway.py` — the one place provider SDKs are invoked; env-gated
  (`AI_ENABLED`), boot-safe by default.
- `routing.py` + `feature_flags.py` — per-task provider/model routing
  (`AI_ROUTING_<TASK>`) and task enablement (`AI_TASK_<NAME>_ENABLED`).
- `natural_language_stage.py` — the NL admission/matching stage in front of
  workflows.
- `providers/` — concrete adapters behind the gateway.
- `safety.py`, `redaction.py` — payload preparation + guardrails.
- `response_renderer_registry.py`, `feature_facts.py`, `diagnostics.py`,
  `suggestion_templates.py` — rendering, capability facts, and the
  read-only diagnostics surface.

## Flow (live)

```text
Cog or view
  -> AI service / workflow
    -> natural_language_stage / routing
      -> gateway -> provider adapter
    -> typed AIResponse / answer-with-evidence contract
  -> existing deterministic pipeline for any state change
```

## Ownership boundaries

AI runtime contracts do not import cogs, views, Discord clients, or database
modules. Provider SDKs stay behind the gateway. State changes belong in the
existing deterministic services (the audited mutation seams) — the AI layer
proposes; deterministic pipelines apply.

Binding contract: `docs/ai-config-ownership.md` (read model, projection
rules, mutation seam, UI pinning). Area entry point: `docs/subsystems/ai.md`.
