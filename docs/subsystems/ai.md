# AI subsystem — folio

> **Status:** `living-ledger` (area index). Source + `docs/current-state.md` win.
> **Last updated:** 2026-06-20 (noted the self-introduction capability overview layer).

## What & where

The AI cog + natural-language stage: setup advisor, tool/loop orchestration, and
scoped tools (including owner-gated diagnostics). Source:
`disbot/core/runtime/ai/` (`natural_language_stage.py`, the tool registry/loop),
`disbot/cogs/ai_cog.py`, `disbot/services/ai_policy_mutation.py`,
`disbot/utils/settings_keys/ai.py`.

## Owner vision (Q-0062 block — seeded from the Q-0040/Q-0051 markup, 2026-06-09)

- **What this area is for:** the AI dungeon master is the owner's single
  highest-regret-if-missing feature — "the most creative, differentiating feature —
  nothing else in Discord bots does this well" (owner-vision §25).
- **What right feels like:** AI that feels genuinely *generative*, not canned — it
  writes the story AND **chooses** quests/rewards/difficulty — but always from
  pre-approved menus whose hard caps deterministic code enforces (Q-0040, chosen over
  both pure narration and free-form authority).
- **One example of wrong:** a player talks the AI into a jackpot, or a session burns
  uncapped provider spend — the cap and the budget are the product, not red tape.

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

### Adding a knowledge domain — detector curation recipe

A knowledge domain (BTD6, Project Moon/Limbus, future LoR/LobCorp) routes through a
curated `has_<domain>_context(text)` detector (`utils/<domain>/keywords.py`) that
`services.ai_task_router.classify` checks in a fixed **priority order** (BTD6 first,
then Limbus). Two disciplines keep this multi-domain router correct — both were
re-derived from source twice before being written down here:

- **Distinctive vs generic tokens.** A detector / name-index keyword list must carry
  only *distinctive* proper-noun tokens. Ordinary English words a domain happens to use
  — bloon colours (`red`/`blue`), the Limbus Sins (`pride`/`wrath`), damage types
  (`slash`), statuses (`burn`) — are **excluded** as bare single tokens; they enter the
  faithfulness name-index (`btd6_grounding_service._name_index` /
  `projmoon_grounding_service._name_index`) only as **multi-word phrases** or via the
  resolver. Routing or flooring on a generic word over-triggers on normal chat.
- **Cross-domain disjointness.** The router relies on each domain's distinctive tokens
  being **inert to every other domain's detector** — in both directions and across the
  match-semantics gap (`has_btd6_context` is a substring scan; `has_limbus_context` is a
  word-boundary regex). When two domains could both claim a phrase, the **earlier domain
  in the priority order wins** (the documented tie-break).

**Guard:** `tests/unit/runtime/ai/test_domain_routing_disjoint.py` is the registry-driven
harness that pins all three properties (routing · token disjointness · priority order).
**Adding a domain is a one-line `DOMAINS` registration there** (detector, expected task,
distinctive tokens, sample questions) — do not re-derive the discipline; register and let
the guard cover it. (Slice B of the Project Moon program folds the per-domain name-index
builders into one shared `KnowledgeDomain` helper — until then this recipe is the contract.)

## Current state

- **Production-readiness map (verified 2026-06-12):**
  `docs/planning/production-readiness/ai-production-readiness-map-2026-06-12.md` inventories
  the live AI / Setup Advisor envelope, direct seams, gaps, gates, and recommended
  verification session. Source code and merged PRs remain authoritative.
- **Provider keys live in agent sessions since 2026-06-11 (Q-0086)** — the
  full model loop (mention → router → grounding → gateway → guard → reply)
  is sandbox-testable against the test bot; the old "model loop awaits the
  maintainer's production check" constraint is lifted. Boot recipes (floor-test
  vs prod-mirror) + the guild-`default_provider`-outranks-env-routing trap:
  journal Runbook + router **Q-0095**. Model allocation canon: `btd6.answer` +
  `general.nl_answer` → Haiku 4.5; rest OpenAI. Memory default (off + last-3
  floor) is owner-confirmed canon (**Q-0094**). Live-found bug classes:
  `docs/health/bug-book.md` (BUG-0005…0010, first Q-0086 session).
- **Shipped:** owner-gated `diagnostics_health_snapshot` tool (#541). Setup-advisor
  integration shape: `docs/ai/ai-service-integration-map.md`.
- **Self-introduction / capability overview (2026-06-20):** the static system layer
  `ai_instruction_service._CAPABILITIES_OVERVIEW` (always assembled, alongside
  `_SYSTEM_SAFETY` / `_BOT_AI_POLICY` / `_TASK_CONTRACT`) is what teaches the model to
  introduce itself with its real feature areas — general assistant + BTD6 expertise,
  the available **games** (Blackjack / RPS / Deathmatch / Counting / Chain / Mining /
  Fishing), economy + progression, and server management. Introduction phrasings
  ("introduce yourself", "who are you", "what do you do") also trip the
  `bot_knowledge_service` command-catalog trigger so the live command list reaches the
  model. The overview keeps BTD6 mentions general (no ungrounded entity names) so a
  friendly intro is not floored by the faithfulness guard. This is the place to edit the
  bot's self-description — *not* a DB instruction profile (those are guild overrides).
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
  foundation itself (toolsets, tool-choice, budgets, evidence). **Phase 1 shipped 2026-06-09:**
  `services.ai_tool_catalogue` is now the canonical tool catalogue (`AIToolMetadata` + named
  toolsets + the deterministic `select_tools`), `build_registry` consults it, and
  `BTD6_GROUNDING_TOOL_NAMES` is derived from it. **Phase 2 shipped 2026-06-09:**
  provider-neutral `AIToolChoice`/`ToolRequirementMode` + `AIToolBudget` on `AIRequest`,
  mapped onto both the OpenAI and Anthropic adapters via a shared `ToolLoopState`
  (compatibility-preserving defaults). **Phase 3 shipped 2026-06-09:** typed orchestration-policy
  storage (migration `062`) + `services.ai_orchestration_presets` / `ai_orchestration_policy` (resolver,
  most-specific-wins) / `ai_orchestration_mutation` (audited seam) + `AIConfigSnapshot.orchestration` +
  the `_invoke_gateway` wiring (default byte-identical) + the **Tools & Workflows** panel button
  (`ai:tools` → `views.ai.tools`: per-scope profile pickers + dry-run analyzer). The operator UI was
  gate-lifted by the maintainer this session. **Phase 4 MVP built 2026-06-09 (#634, Q-0046):**
  the round-cash plan→execute→verify workflow (`services/ai_round_cash_workflow.py`) + the one
  typed answer-with-evidence contract (`AIAnswerWithEvidence`/`CalculationEvidence`, Q-0043
  inclusive semantics), profile-gated on `workflow == "analyze_execute_verify"`; default
  byte-identical; **model loop awaits the maintainer's production check** (no sandbox provider
  key). The remaining §7 families/contracts + the durable orchestration audit trace are next.
- `docs/ai/ai-tool-capability-roadmap.md` (`plan`, non-authoritative) — triages/sequences
  the ideas backlog onto that foundation.

- **`docs/planning/ai-btd6-answerability-roadmap-2026-06-09.md`** (`plan`) — source-verified answerability/self-awareness bridge with BTD6 round cash as the first proof path. **Phase 1A/1B (round cash, #612) + Phase 2 (`services/ai_introspection_service.py`, the read-only composition read model) + Phase 3 (#639, Q-0047 — the three self-awareness tools `get_ai_tool_catalog` / `get_ai_policy_explanation` / `btd6_answerability`, audience-tiered at construction over the Phase 2 read model) shipped 2026-06-09.** `btd6_answerability` deliberately carries the btd6 grounding domain (and so the `btd6_*` name) — its counts/versions must join the faithfulness ledger or the number-guard would block its own replies. The remaining exposure lanes stay gated: any settings UI is Phase 4 (per-exposure ask + settings foundation), the generated dashboard Phase 5.
- **`docs/planning/ai-panel-inplace-navigation-plan-2026-06-19.md`** (`plan`, 2–3 PRs) — migrate the
  `views/ai/` settings/panel family off per-click ephemeral messages onto the rest-of-bot in-place
  **HubView** pattern (V-02) + centralize the seven scattered subpanels. **Substantial runtime + wants a
  live guild walk;** it is the blocker for graduating the consistency linter's `edit_in_place` rule (its
  17 remaining findings are exactly this family). Idea: `ideas/ai-panel-inplace-navigation-2026-06-11.md`.

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

## Answer review loop (didn't-know + corrections → correct answers)

The bot records every question it got wrong or couldn't answer in `ai_review_log`
(migration 100, #1494): `services/ai_review_log_service.py` + `cogs/ai_review_cog.py`
(`!aireview`). The **answer loop** that turns that backlog into correct answers —
`!aireview export` → `scripts/ai_review_triage.py` → root-cause fix + regression probe
**or** a vetted preset (`services/ai_preset_service.py`, served with zero model call) →
`!aireview resolve` — is the
[AI review-log backlog runbook](../operations/ai-review-backlog-runbook.md).

## Related docs

`docs/ai/ai-readiness-plan.md` (`plan`), `docs/ai/ai-readiness-pr-notes.md`,
`docs/ai/ai-provider-and-grounding-fix-plan.md` (`plan`),
`disbot/core/runtime/ai/README.md` (package intent),
[AI review-log backlog runbook](../operations/ai-review-backlog-runbook.md).

## Product-extension routing (not approved)

The [AI product-extension routing addendum](../ai/ai-product-extension-routing-2026-06-08.md) routes dungeon-master, generated-event, wider-intent, and extra-tool ideas under the existing authoritative AI roadmap. It does not change the fully gated status or permit write/action tools.
