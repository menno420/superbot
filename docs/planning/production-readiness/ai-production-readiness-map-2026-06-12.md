# AI / Setup Advisor production-readiness map — 2026-06-12

> **Status:** `living-ledger` — docs-only, source-verified production-readiness review.
> **Authority:** source code and merged PRs win over this map. Recheck live PRs before using it as an execution queue.
> **Scope:** AI Platform, Setup Advisor, and only the directly required settings, health/diagnostics, BTD6-grounding, and setup-behaviour seams.

## Current verified state

The subsystem is **production-capable for its currently shipped, opt-in, read-only/advisory envelope, but is not production-complete for the wider AI roadmap**.

The live path is no longer an inert scaffold: `AICog` registers the central natural-language message stage; policy resolution, permission/cooldown checks, context and instruction assembly, provider-neutral gateway execution, tool selection, audit recording, memory, BTD6 grounding, and operator diagnostics are wired. The gateway defaults off and deterministic; external provider and tool use require explicit environment/config opt-in. The Setup Advisor has deterministic and OpenAI-via-gateway implementations, validates recommendations against registered binding schemas, and remains advisory until an operator explicitly stages/applies existing setup operations.

Production confidence is bounded. The first provider-backed live-test session on 2026-06-11 exposed routing and grounding defects that were fixed in merged PRs #703, #706, #707, and #709. Those fixes materially improve the live path, but also show that unit coverage is not a substitute for recurring provider-backed and Discord-backed evaluation. The only live open PR checked on 2026-06-12 was #704, “Screenshots from live testing the bot”; it does not modify AI runtime source. The local checkout has no configured Git remote or `gh` binary, so live PR state was verified through the GitHub API for `menno420/superbot`.

No newer or more authoritative AI production-readiness tracker existed under `docs/planning/production-readiness/`; this map is therefore the canonical dated review rather than an update to another tracker.

### Status meaning

- **Done** — implemented and wired for the current declared envelope, with focused tests.
- **Partial** — implemented but deliberately limited, stale at an edge, missing live verification, or incomplete against its declared forward plan.
- **Not Done** — explicitly inert, reserved, TODO, or planned without a production implementation.

## Scope inventory table

### Cogs, runtime modules, and operator-facing read/write seams

| Item | Path | Type | Status | Reason | Evidence |
|---|---|---|---|---|---|
| AI command/panel cog | `disbot/cogs/ai_cog.py` | cog | Done | Registers schemas, panel router, persistent view, and the central natural-language stage; commands read through services/projections rather than raw DB scans. | `AICog.cog_load`; `tests/unit/cogs/test_ai_cog.py`; `tests/unit/cogs/test_ai_panel_router_registration.py` |
| AI subsystem schema | `disbot/cogs/ai/schemas.py` | settings/binding declaration | Done | Declares the AI settings and `audit_log_channel` binding and registers one subsystem schema. | `AI_SETTINGS`; `AI_BINDINGS`; `register_schemas` |
| AI runtime contracts | `disbot/core/runtime/ai/contracts.py` | typed contracts | Done | Typed tasks, scopes, requests/responses, tools, budgets, and evidence are used by the live runtime despite the stale “inert scaffold” module docstring. | imports throughout gateway/stage/tools; orchestration tests |
| Feature flags | `disbot/core/runtime/ai/feature_flags.py` | runtime policy | Done | Global AI, task, tools, and member-lookup gates default safe/off; setup-advisor provider compatibility is retained. | `tests/unit/runtime/ai/test_feature_flags.py`; kill-switch tests |
| Provider routing | `disbot/core/runtime/ai/routing.py` | runtime policy | Done | Resolves task routing, env overrides, provider defaults, models, fallback provider, and timeout. | routing tests; diagnostics routing surface |
| Core gateway | `disbot/core/runtime/ai/gateway.py` | provider boundary | Done | Single provider chokepoint applies gates, safety, redaction, routing, per-guild overlay, timeout/fallback, tool dispatch, and diagnostics. | `tests/unit/runtime/ai/test_gateway.py`; provider tests |
| Service gateway shim | `disbot/services/ai_gateway.py` | service seam | Done | Keeps cogs/services off the core gateway and exposes provider-neutral `execute`. | import-boundary tests; Setup Advisor gateway test |
| Providers: deterministic/OpenAI/Anthropic | `disbot/core/runtime/ai/providers/` | provider adapters | Done | All three adapters exist; network providers implement bounded tool loops and deterministic remains the safe fallback. | `tests/unit/runtime/ai/test_openai_provider.py`; gateway/provider tests |
| Natural-language message stage | `disbot/core/runtime/ai/natural_language_stage.py` | message-pipeline stage | Partial | Live and extensively wired, including grounding retry/floor and audit; recent live defects show this highest-complexity seam still needs recurring production/eval verification. | merged #703/#706/#707/#709; `tests/unit/runtime/ai/test_natural_language_stage.py` |
| Runtime diagnostics collector | `disbot/core/runtime/ai/diagnostics.py` | health/metrics | Done | Central bounded diagnostics snapshot records provider/task outcomes for operator surfaces. | diagnostics service/cog tests |
| Redaction and safety | `disbot/core/runtime/ai/redaction.py`; `safety.py` | safety policy | Done | Redacts provider payloads, bounds payload size, contains untrusted text, and supplies grounding checks. | prompt-injection/redaction/gateway tests |
| Response renderer registry | `disbot/core/runtime/ai/response_renderer_registry.py` | runtime extension seam | Done | One registry exists and is used rather than adding response rendering to the cog. | runtime tests/import use |
| Feature-facts contracts | `disbot/core/runtime/ai/feature_facts.py` | grounding contract | Done | Typed feature-fact request/result seam is used by the natural-language stage. | merged #707; stage tests |
| Suggestion templates | `disbot/core/runtime/ai/suggestion_templates.py` | planned scaffold | Not Done | Module explicitly says it is inert and is not imported by production runtime. | module docstring |
| Runtime package README | `disbot/core/runtime/ai/README.md` | documentation | Partial | Still describes the package as intentionally inert although the package is live. | README text versus `AICog.cog_load` and live imports |
| Configuration projection | `disbot/services/ai_config_projection_service.py` | operator read model | Done | Composes the canonical `AIConfigSnapshot` used by operator-facing AI surfaces. | `build_snapshot`; projection/doc-pin tests |
| AI policy mutation | `disbot/services/ai_policy_mutation.py` | audited mutation chokepoint | Done | Validates authority/values, writes typed policy, projects legacy settings, audits, and invalidates caches. No reviewed AI-cog bypass exists. | policy mutation tests; readonly invariants |
| Natural-language policy resolver | `disbot/services/ai_natural_language_policy.py` | reply policy | Done | Single most-specific-wins resolver with dry-run explanation path and global-disable precedence. | policy and dry-run tests |
| Tool-orchestration policy | `disbot/services/ai_orchestration_policy.py` | tool policy | Done | Resolves profile most-specific-wins and can only narrow scope-authorized tools. | orchestration policy/wiring tests |
| Tool-orchestration mutation | `disbot/services/ai_orchestration_mutation.py` | audited mutation chokepoint | Done | Dedicated validated/audited writer for orchestration-profile fields. | orchestration mutation/integration tests |
| Orchestration presets | `disbot/services/ai_orchestration_presets.py` | policy catalogue | Done | Compatibility default and narrower workflow/tool presets are implemented. | preset and wiring tests |
| Durable orchestration execution trace | `docs/ai/ai-complex-request-tool-orchestration-plan.md` | planned audit capability | Not Done | The plan and AI folio still identify durable orchestration audit trace as remaining work. | plan §7/remaining-work text; `docs/subsystems/ai.md` |
| Complex-request workflow families | `disbot/services/ai_round_cash_workflow.py`; orchestration plan §7 | deterministic workflow | Partial | Round-cash plan→execute→verify vertical slice is live; the other planned complex comparison/calculation families are not. | round-cash tests; merged #634/#703/#706/#709; plan §7 |

### AI services

| Item | Path | Type | Status | Reason | Evidence |
|---|---|---|---|---|---|
| Behavior profiles | `disbot/services/ai_behavior_profile_service.py` | behavior policy service | Done | Lists/describes/applies seeded presets through instruction and policy mutation seams. | behavior-profile tests; behavior UI tests |
| Context assembly | `disbot/services/ai_context_service.py` | request service | Done | Builds typed request context outside the stage/cog. | stage/context tests |
| Conversation memory | `disbot/services/ai_conversation_service.py` | in-process memory | Done | Bounded per-channel memory and forget/stat operations are implemented under the no-Redis decision. | memory and forget-command tests |
| Discord-aware memory gathering | `disbot/services/ai_memory_service.py` | memory orchestration | Done | Reads settings, uses the in-process floor, and optionally scans visible channel history. | memory service/stage tests |
| Decision audit | `disbot/services/ai_decision_audit_service.py` | persistent audit service | Done | One recording/query seam supports why-no-response and support reporting without storing raw message content. | audit/stage/cog tests |
| AI diagnostics service | `disbot/services/ai_diagnostics_service.py` | diagnostics read model | Done | Provides cog-safe status/provider/routing snapshots. | cog diagnostics tests |
| AI readiness service | `disbot/services/ai_readiness_service.py` | readiness scan | Done | Performs bounded chain checks over flags, provider/routing, policy, channel, and tools. | readiness service/cog tests |
| Instruction-profile mutation | `disbot/services/ai_instruction_mutation.py` | audited mutation chokepoint | Done | Owns validated/audited profile upsert/delete; behavior writes route here. | instruction mutation/behavior tests |
| Instruction stack | `disbot/services/ai_instruction_service.py` | prompt policy | Done | Assembles ordered safety/policy/profile/facts/user layers and self-awareness blocks. | instruction/grounding tests |
| AI introspection | `disbot/services/ai_introspection_service.py` | read model | Done | Provides audience-filtered tool catalogue, BTD6 answerability, settings view, and policy explanation. | introspection/self-awareness tests; merged #639 |
| Permission/cooldown service | `disbot/services/ai_permission_service.py` | reply permission policy | Done | Owns access snapshot, cooldown, fresh allowance, and reset behavior. | permission and policy integration tests |
| Task router | `disbot/services/ai_task_router.py` | natural-language routing | Partial | Live and broadly tested, but routing misses were a repeated finding in the first live provider sessions. | merged #703/#706/#707; router tests |
| Tool catalogue | `disbot/services/ai_tool_catalogue.py` | canonical tool metadata/selector | Done | Single canonical descriptor catalogue and deterministic selector; no second registry was introduced. | catalogue tests; merged #612 |
| Tool registry/handlers | `disbot/services/ai_tools.py` | live read-only tool registry | Partial | One request-scoped registry contains live handlers and scope/toolset filtering; a TODO still calls for moving the health tool into the canonical diagnostics toolset metadata. | `build_registry`; `tests/unit/services/test_ai_tools.py`; TODO(#536) |
| Setup advisor | `disbot/services/setup_ai_advisor.py` | advisory setup service | Partial | Deterministic and OpenAI-via-central-gateway paths validate against schemas; Anthropic is explicitly reserved/unimplemented and provider choice retains a separate compatibility env seam. | setup-advisor tests; gateway-boundary test |
| Setup advisor final-review wrapper | `disbot/services/setup_advisor_review.py` | read-only setup seam | Done | Optional, bounded, advisory-only, fail-safe review; cannot block apply. | setup-advisor-review and readonly invariant tests |
| BTD6 AI augmentation | `disbot/services/btd6_ai_service.py` | BTD6 answer seam | Done | Deterministic answer remains authoritative and AI augmentation fails safely without replacing it. | BTD6 AI service/grounding-pin tests |
| BTD6 context/knowledge blocks | `disbot/services/btd6_context_service.py`; `btd6_ai_context_service.py`; `btd6_ai_knowledge_block_service.py` | grounding input seams | Done | Supply bounded facts/live context to AI paths rather than allowing ungrounded provider knowledge. | BTD6 context/knowledge-block tests |
| BTD6 grounding verifier | `disbot/services/btd6_grounding_service.py` | post-generation safety | Partial | Name/number verification, retry constraint, and deterministic refusal/floor are live; continuing live fixes show vocabulary/routing coverage remains an operational risk. | grounding tests; merged #703/#707/#709 |

### Canonical live tools

All tools below are registered in the single request-scoped registry in `disbot/services/ai_tools.py`, described/selected through `disbot/services/ai_tool_catalogue.py`, scope-filtered, read-only, and covered by catalogue/tool tests. “Done” means the handler exists for its current envelope, not that every possible natural-language phrasing has live verification.

| Item | Path | Type | Status | Reason | Evidence |
|---|---|---|---|---|---|
| `get_user_standing`; `get_server_time` | `disbot/services/ai_tools.py` | user tools | Done | Live user-safe handlers. | tool registry/tests |
| `get_server_overview`; `list_server_roles`; `list_server_channels` | same | server introspection tools | Done | Live bounded guild metadata handlers. | tool registry/tests |
| `lookup_member`; `list_all_members` | same | sensitive server tools | Done | Live but additionally gated by `AI_SERVER_MEMBER_LOOKUP_ENABLED`. | feature flag and tool tests |
| `get_guild_ai_config`; `recent_audit` | same | admin AI tools | Done | Live admin-scoped config/audit handlers through service read models. | tool scope/tests |
| `diagnostics_health_snapshot` | same | platform-owner health tool | Partial | Live, audience-filtered, and owner-gated; catalogue/toolset integration TODO remains and production live-test follow-up is still called out. | TODO(#536); health tool tests; AI folio |
| `get_ai_tool_catalog`; `get_ai_policy_explanation`; `btd6_answerability` | same | self-awareness tools | Done | Live audience-tiered tools over the introspection read model; BTD6 answerability joins the grounding ledger. | merged #639; self-awareness/tool tests |
| `btd6_lookup`; `btd6_list_roster`; `btd6_capability_lookup`; `btd6_superlative_lookup` | same | BTD6 knowledge tools | Done | Live canonical lookup/capability families. | tool and BTD6 service tests |
| `btd6_difficulty_cost`; `btd6_round_composition`; `btd6_round_cash`; `btd6_cumulative_cost` | same | BTD6 calculation tools | Done | Live deterministic calculation handlers; round-cash also has the verified workflow path. | calculation/tool/workflow tests |
| `btd6_map_lookup`; `btd6_mode_lookup`; `btd6_relic_lookup`; `btd6_power_lookup`; `btd6_monkey_knowledge_lookup`; `btd6_geraldo_lookup`; `btd6_boss_lookup`; `btd6_bloon_filter`; `btd6_power_effect` | same | BTD6 domain tools | Done | Live bounded domain lookups whose outputs can enter the BTD6 grounding ledger. | tool/grounding tests |
| `btd6_paragon_calculate`; `btd6_paragon_requirements`; `btd6_paragon_stats_at_degree`; `btd6_ct_team_status` | same | BTD6 specialist tools | Done | Live deterministic specialist handlers. | tool/paragon/CT tests |

### Settings and policy keys

| Item | Path | Type | Status | Reason | Evidence |
|---|---|---|---|---|---|
| `ai_enabled` | `disbot/utils/settings_keys/ai.py` | guild setting / policy projection | Done | Declared in schema and projected into typed guild policy. | settings projection/doc-pin tests |
| `ai_natural_language_enabled` | same | guild setting / policy projection | Done | Declared and projected; resolver applies it beneath global gate. | policy/projection tests |
| `ai_default_provider`; `ai_default_model` | same | guild routing settings / policy projection | Done | Declared/projected and overlaid by the gateway with model-family protection. | gateway/projection/provider-allowlist tests |
| `ai_minimum_level_default`; `ai_cooldown_seconds`; `ai_fresh_user_mention_allowance` | same | guild reply-policy settings / policy projection | Done | Declared/projected and enforced by policy/permission services. | policy/permission/projection tests |
| `ai_guild_instruction_profile` | same | legacy/backcompat setting | Partial | Retained for backcompat reads but hidden from generic settings UI; authoritative edits use instruction-profile + policy mutation seams. | `docs/ai-config-ownership.md`; schema/projection tests |
| `ai_memory_window_minutes`; `ai_memory_channel_scan_enabled` | same | memory settings | Done | Declared and consumed by the memory service; scan is opt-in and visibility-filtered. | memory/schema tests |
| `audit_log_channel` | `disbot/cogs/ai/schemas.py` | binding | Done | Declared AI-owned binding; no direct raw-ID setting duplication. | binding/schema tests |
| Typed guild/channel/category/role policies | `disbot/utils/db/ai.py`; mutation/resolver services | persistent policy | Done | Typed policies are runtime source of truth with dedicated mutation/resolution seams. | DB/policy/invariant tests |
| Instruction profiles | `disbot/utils/db/ai.py`; `ai_instruction_mutation.py` | persistent prompt policy | Done | Typed profile storage has a dedicated audited mutation seam. | instruction/behavior tests |
| Orchestration profile fields | typed policy tables; orchestration services | persistent tool policy | Done | Written only through orchestration mutation and resolved independently of reply behavior. | orchestration DB/integration tests |
| Environment gates/routing: `AI_ENABLED`, `AI_DEFAULT_PROVIDER`, `AI_TASK_<NAME>_ENABLED`, `AI_TOOLS_ENABLED`, `AI_SERVER_MEMBER_LOOKUP_ENABLED`, `AI_ROUTING_<TASK>` | `disbot/core/runtime/ai/feature_flags.py`; `routing.py` | deployment settings | Done | Explicit boot-safe gates and routing overrides exist. | feature-flag/routing tests |
| Setup Advisor environment: `SETUP_ADVISOR_PROVIDER`, `OPENAI_API_KEY` | `disbot/services/setup_ai_advisor.py`; feature flags | deployment settings | Partial | Compatibility path works and falls back safely; Anthropic selection only logs/falls back, and setup provider selection is not fully unified with guild AI config. | setup-advisor tests/source |

### User-facing functions

| Item | Path | Type | Status | Reason | Evidence |
|---|---|---|---|---|---|
| `!ai` / `/aimenu` AI Platform panel | `disbot/cogs/ai_cog.py`; `disbot/views/ai/` | admin UI | Done | Persistent panel exposes canonical operator surfaces and stable custom IDs. | panel/router/view tests |
| AI status, diagnostics, providers, routing | `disbot/cogs/ai_cog.py` | admin commands | Done | Prefix/slash surfaces read diagnostics/projection services. | cog command tests |
| AI readiness scan | same | admin commands/panel action | Done | Prefix/slash/channel-targeted scan and status summary are wired. | readiness tests |
| AI settings | same; settings subsystem UI | admin commands/UI | Done | Reuses the central subsystem settings view rather than creating an AI-only writer. | settings projection/cog tests |
| AI policy explanation | same | admin commands | Done | Dry-run resolver plus config snapshot explains effective channel policy without mutation. | policy-command tests |
| Why-no-response / support report | same | admin commands | Done | Uses audit/config/readiness services and omits raw message content. | formatting/support-report tests |
| Forget AI memory | same | admin commands | Done | Prefix/slash command clears bounded channel memory. | forget-command tests |
| Behavior chooser / instruction profiles | `disbot/views/ai/` | admin UI | Done | Applies presets through approved mutation services. | behavior/view/service tests |
| Tools & Workflows chooser | `disbot/views/ai/` | admin UI | Done | Configures orchestration profiles through the dedicated mutation seam. | tools-view/orchestration tests |
| Natural-language replies | message pipeline + AI stage | user function | Partial | Provider-backed reply loop is live and guarded, but remains opt-in and needs continued live eval after recent routing/grounding fixes. | merged #703/#706/#707/#709; stage tests |
| Setup “Smart Suggestions” | `disbot/views/setup/launcher.py`; `sections/suggestions.py`; `views/setup/ai_review/` | admin setup UI | Done | Runs advisor, supports aggregate/per-item review, and stages only accepted recommendations through existing setup flow. | AI review panel/setup-advisor tests |
| Final Review “Ask AI to review” | `disbot/views/setup/final_review.py`; `setup_advisor_review.py` | admin setup UI | Done | Optional, advisory-only, and fail-safe; never applies changes. | readonly invariant/review tests |
| Setup wizard “AI setup” section | `disbot/views/setup/sections/ai_setup.py` | admin setup UI | Partial | Deliberately link-only: opens AI policy manager or skips; it does not configure AI in the wizard. | source docstring/view tests |
| BTD6 AI-augmented answers and central natural-language BTD6 answers | BTD6 cog/service + central stage | user function | Partial | Deterministic/grounded paths are live, but production sessions continue to uncover phrase-routing and grounding-vocabulary misses. | BTD6 AI/grounding tests; merged #703/#706/#707/#709 |

## Required before production-ready

“Production-ready” must be interpreted in two layers:

### Required for the **current shipped envelope**

1. **Run recurring provider-backed evaluation and Discord live checks after each routing, grounding, tool, or prompt-policy change.** The 2026-06-11 live session found defects not caught by unit tests.
2. **Live-verify the owner-gated `diagnostics_health_snapshot` and Setup Advisor external-provider path** with production-like credentials, permissions, redaction audience, timeout, and fallback behavior.
3. **Resolve the runtime-documentation drift** in `disbot/core/runtime/ai/README.md` and the stale “inert scaffold” wording in live contracts so operators/agents do not misclassify active code.
4. **Keep the central chokepoints intact:** provider calls via `services.ai_gateway`, AI policy writes via `ai_policy_mutation`, orchestration writes via `ai_orchestration_mutation`, instruction writes via `ai_instruction_mutation`, and operator reads via `ai_config_projection_service`/introspection/diagnostics services.
5. **Define a repeatable production smoke/eval record** that proves global/task/tool kill switches, deterministic fallback, audit visibility, grounding refusal, and Setup Advisor no-write behavior on the deployed configuration.

### Required only for the **wider roadmap envelope**

These are not blockers for the current opt-in read-only/advisory feature set, but they must ship before claiming the wider planned AI product is complete:

- durable orchestration execution/audit trace;
- remaining complex-request plan→execute→verify families beyond round cash;
- any approved settings assistant, log-triage, diagnostics explainer, or server-management generation layer;
- any external-call, write/action, or new-UI exposure only after its owner gate is lifted;
- Anthropic Setup Advisor only if it becomes an approved product requirement.

## Bugs, inconsistencies, and risks

- **Live-eval defect rate:** merged #703, #706, #707, and #709 fixed boss/shorthand routing, round projections, carryover grounding, feature-fact/tool behavior, and ABR workflow qualification after real provider-backed testing. This is the strongest current reason to retain a Partial rating on the natural-language stage/router/grounding chain.
- **Stale runtime docs:** `disbot/core/runtime/ai/README.md` and the contracts module still call active runtime pieces inert.
- **Health-tool metadata debt:** `ai_tools.py` still carries TODO(#536) to register `diagnostics_health_snapshot` in the canonical diagnostics toolset/descriptor layer. It is live, but its metadata placement is incomplete.
- **Setup-provider split:** Setup Advisor honors `SETUP_ADVISOR_PROVIDER` for compatibility and falls back to the central default, while guild routing/config uses typed policy plus AI routing. This is safe but adds operational explanation burden.
- **Setup Anthropic adapter:** selecting Anthropic for Setup Advisor only warns and falls back to deterministic.
- **Setup AI section expectation mismatch:** the wizard has an “AI setup” step, but it is intentionally a link to the separate AI manager rather than an in-wizard configurator.
- **In-process memory:** intentional and bounded, but restarts erase context; operators must not mistake it for durable memory.
- **Broad default-on task behavior beneath the global gate:** once `AI_ENABLED` is enabled, tasks default enabled unless individually killed. This is tested and intentional, but production rollout must set/verify task and tool gates explicitly.
- **No open AI source PR at review time:** open PR #704 is screenshots only, so no in-flight code changes alter this map; recheck before execution because this can change quickly.

## Gated or blocked work

- Read-only deterministic AI tools have a standing lift. Anything that writes, costs money, calls external services, or adds UI still needs a per-exposure lift; broad expansion remains gated on stability, provider/provenance, caching/source-health, and AI behavior/config correctness.
- Remaining orchestration §7 families and durable trace are planned, not approved as automatic production-readiness requirements for the current envelope.
- Settings-assistant mutation, server-management AI generation, and other action tools must not bypass existing mutation/operation pipelines and remain gated.
- Anthropic Setup Advisor is reserved but not implemented; no source establishes that it is required for current production readiness.
- No maintainer Q-block was added: current owner intent is explicit enough to classify these items as gated/optional rather than ambiguous requirements.

## Simplification opportunities

1. Update the stale runtime README/contracts wording so one live architecture is described consistently.
2. Finish TODO(#536) by representing the health tool in the existing canonical tool catalogue/toolset model—do **not** create another registry.
3. Document Setup Advisor provider precedence beside the central provider-precedence explanation to reduce the appearance of two competing provider systems while preserving compatibility.
4. Keep the setup wizard’s link-only AI section explicit, or remove the section if it creates more expectation than value; do not add a second settings/mutation UI path.
5. Treat the round-cash workflow as the template for future deterministic complex workflows rather than adding ad hoc arithmetic/prompt logic to the natural-language stage.

## Tests and live-verification gaps

### Strong automated coverage already present

- Cog commands/panel routing, config projection/doc pins, policy mutation/cache invalidation/provider allowlist, natural-language policy dry-run, readiness, diagnostics, memory, permissions, audit formatting, orchestration policy/mutation/presets/wiring, tool catalogue/handlers, Setup Advisor gateway/no-write behavior, BTD6 grounding/context/router/workflow, and readonly/import boundaries all have focused unit/invariant coverage.
- Repo invariants prohibit Setup Advisor writes, factual AI writes, and AI/BTD6 boundary violations.

### Remaining gaps

- No automated test proves the full deployed Discord event → external provider → tool call(s) → grounded reply → audit row path against real provider APIs.
- No recurring live-eval artifact is required by CI after router/grounding/tool changes.
- External-provider Setup Advisor needs production-like validation for timeout/fallback/redaction and recommendation quality.
- `diagnostics_health_snapshot` still needs an operator live-test record across audience/redaction and fresh/cached modes.
- The broader natural-language phrase space and BTD6 vocabulary cannot be exhaustively unit-tested; regression prompts from each live miss should continue to enter the eval suite.
- The Setup Advisor’s OpenAI path is tested through mocks/contracts, while Anthropic is intentionally absent.
- Docs checks can verify links/pins/structure but cannot prove live provider or Discord behavior.

## Recommended next session

Run a **production-envelope verification session**, not a feature-expansion session:

1. Build a short, versioned eval/smoke matrix covering global/task/tool gates, provider fallback, two-hop tool use, recent fixed BTD6 prompts, grounding refusal, audit/support report, readiness, and Setup Advisor advisory/no-write behavior.
2. Execute it with production-like Discord permissions and provider credentials; capture failures in the bug book and add regression tests before fixes.
3. Live-test `diagnostics_health_snapshot` for platform-owner and non-owner access, cached/fresh behavior, and redaction.
4. In a separate docs-only cleanup, correct the stale inert-scaffold runtime wording and document Setup Advisor provider precedence.
5. Only after that evidence is green, choose whether the next approved product slice is the durable orchestration trace or one additional deterministic complex-request family.
