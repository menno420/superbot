# AI Readiness Scaffold PR Notes

> **Status:** `plan` — AI-readiness PR notes; read for context, cross-check source.

## Intent

This PR prepares connector points for broader AI support without changing runtime behavior.

It is designed to avoid conflicts with active implementation work by adding only new files.

## What this PR adds

- AI readiness architecture plan.
- Service integration map for future AI use cases.
- Inert runtime AI package scaffold.
- Provider-neutral AI contracts.
- Deterministic redaction helper scaffold.
- Suggestion templates that map AI output to existing deterministic service owners.

## What this PR does not do

- Does not import the new package from existing runtime files.
- Does not add a new cog.
- Does not call any external AI provider.
- Does not alter setup advisor behavior.
- Does not add or change environment variables.
- Does not add feature flags yet.
- Does not mutate existing docs or source files.

## Why this helps later development

Future PRs can now reference stable task names, request/response contracts, suggestion types, redaction expectations, and service ownership rules.

This should speed up later work on:

- `!platform ai`
- AI gateway extraction
- setup advisor v2
- AI bot monitor
- AI log triage
- AI settings assistant
- AI help assistant
- generated code context pack

## Suggested review focus

- Are the task names broad enough?
- Are the ownership boundaries strict enough?
- Are the suggested connector points aligned with the current platform architecture?
- Are there any future AI services missing from the integration map?

## Suggested follow-up PRs

1. Add AI feature flags and AI metrics declarations.
2. Add read-only AI diagnostics provider and `!platform ai` surface.
3. Extract provider calls from setup advisor into a central AI gateway.
4. Add a fake-provider test harness for gateway behavior.
5. Add read-only AI bot monitor using diagnostics snapshots.
