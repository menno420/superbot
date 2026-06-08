# AI subsystem — folio

> **Status:** `living-ledger` (area index). Source + `docs/current-state.md` win.
> **Last updated:** 2026-06-06.

## What & where

The AI cog + natural-language stage: setup advisor, tool/loop orchestration, and
scoped tools (including owner-gated diagnostics). Source:
`disbot/core/runtime/ai/` (`natural_language_stage.py`, the tool registry/loop),
`disbot/cogs/ai_cog.py`, `disbot/services/ai_policy_mutation.py`,
`disbot/utils/settings_keys/ai.py`.

## Rules & approved structures (binding — link, don't restate)

- **`docs/ai-config-ownership.md`** (`binding`, doc-test-pinned) — the AI cog's read
  model, projection rules, mutation seam, and UI-surface pinning. Read before any
  AI-cog change.
- **Scope model:** `_derive_scope` → `AIScope`; `config.BOT_OWNER_USER_ID` →
  `PLATFORM_OWNER` (decision D1, shipped #541) gates owner-only tools such as
  `diagnostics_health_snapshot`.
- **Faithfulness / groundedness guards are confirmed-healthy — preserve** (do not
  refactor the orchestration choke point). See `docs/ai/ai-guard-coverage-map.md` and
  `docs/btd6/btd6-derived-value-groundedness-finding.md`.

## Current state

- AI runs **degraded in the sandbox** (no provider key): deterministic paths are
  testable here, but the model actually *calling* a tool must be verified on the
  maintainer's production bot. See `docs/current-state.md` (stability baseline + gates).
- **Shipped:** owner-gated `diagnostics_health_snapshot` tool (#541). Setup-advisor
  integration shape: `docs/ai/ai-service-integration-map.md`.
- **Gate:** AI feature expansion is gated on *all* of bot-wide stability + provider/
  provenance + caching/source-health clarity + AI behavior/config correctness — see
  `docs/current-state.md` "Gates / blocked work".

## Plans / pending approval

- **`docs/planning/ai-roadmap-2026-06-07.md`** (`plan`) — the consolidated, source-verified
  AI roadmap (Phase 0–11) that sequences all AI expansion. **AI-area sequencing authority.**
  **Owner decisions (AR batch, 2026-06-07 — `docs/owner/maintainer-question-router.md` §18):**
  AR-10 → **first Opus target = lock the orchestration foundation** before any net-new tools;
  AR-08 → **tiered audience** posture (read access never grants action authority); AR-09 →
  **explanation-only** now (recurring-report draft as the eventual first action category only
  if revisited). The rest of the AR batch holds at safe defaults until each lane is active.
- `docs/ai/ai-complex-request-tool-orchestration-plan.md` (`plan`) — the orchestration
  foundation itself (toolsets, tool-choice, budgets, evidence); the roadmap's Phase 1.
  Approve this **before** net-new tools.
- `docs/ai/ai-tool-capability-roadmap.md` (`plan`, non-authoritative) — triages/sequences
  the ideas backlog onto that foundation.

## Ideas (not approved)

- `docs/ideas/ai-extra-tool-capability-ideas.md` — capability backlog (web/vision/
  file/KB/connectors/scheduler/etc.). Promotion path: `docs/ideas/README.md`.
- **Owner intent (2026-06-07, `docs/owner/maintainer-question-router.md` Q-0001 — not
  approval):** AI may *eventually* gain broader / action capabilities beyond
  explanation-only — but only behind *all* AI gates (readiness, orchestration, authority,
  confirmation, audit, rollback) **and** a dedicated decision. Today AI stays read-only /
  explanation-only; this note changes no gate.

## Next candidates (self-direct from here)

1. Maintainer live-tests the owner-gated diagnostics tool on production
   (`docs/current-state.md` "Next candidates").
2. If/when AI expansion is unblocked: **approve the orchestration foundation**
   (`ai-complex-request-tool-orchestration-plan.md`) *before* any net-new tools — the
   roadmap sequences the backlog onto it, not as isolated cog features.
3. Promote a single backlog idea through the `docs/ideas/README.md` gates as the first
   net-new tool (the roadmap's pick is bounded public-doc knowledge search).

## Related docs

`docs/ai/ai-readiness-plan.md` (`plan`), `docs/ai/ai-readiness-pr-notes.md`,
`docs/ai/ai-provider-and-grounding-fix-plan.md` (`plan`),
`disbot/core/runtime/ai/README.md` (package intent).
