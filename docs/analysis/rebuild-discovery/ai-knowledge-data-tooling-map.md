# AI, knowledge-data, eval, docs-agent, CI/tooling, and operations rebuild discovery map

> **Status:** `historical` — rebuild-discovery mapping report.
>
> Scope: Part 4 of 4 rebuild-discovery mapping for a possible future clean SuperBot repo. This report is a source-grounded design inventory, not approval to rebuild or implement. Source code and merged repo state are treated as higher authority than planning/current-state docs.

## 1. Executive summary

### Strongest ideas to preserve

1. **AI gateway as a reusable safety boundary.** `disbot/core/runtime/ai/gateway.py` centralizes provider selection, fallback, request/payload redaction, tool-result redaction, diagnostics, and degraded replies. Preserve the idea as an `AIProviderGateway` primitive, but redesign the layer boundary so core runtime does not import services.
2. **Typed AI contracts and task profiles.** `disbot/core/runtime/ai/contracts.py` defines `AITask`, `AIRequestContext`, `AIRequest`, tool specs, tool budgets, answer evidence, and diagnostics. `routing.py` maps tasks to provider/model targets with env overrides. This is exactly the kind of API a fresh repo should keep.
3. **Natural-language stage with deterministic domain gates.** `disbot/core/runtime/ai/natural_language_stage.py` is large, but the important idea is strong: passive AI is one message-pipeline stage; BTD6/Project Moon/YouTube detection and refusals happen before model calls where deterministic data is insufficient.
4. **Answer review and preset feedback loop.** `migrations/100_ai_review_log.sql`, `migrations/102_ai_answer_presets.sql`, `utils/db/ai_review_log.py`, `utils/db/ai_presets.py`, `services/ai_review_log_service.py`, `services/ai_preset_service.py`, and `cogs/ai_review_cog.py` confirm a durable loop for redacted answer capture, correction triage, and reusable preset answers.
5. **Knowledge-domain provenance contracts.** BTD6 is the mature exemplar: source registry, source snapshots, facts, committed data blobs, AI context summaries, view-model services, source health, probes, evals, and admin refresh surfaces all exist. The rebuild should generalize this into `KnowledgeDomainSpec`, `SourceProvenanceSpec`, `IngestionPipeline`, and `ViewModelContextHandle`.
6. **Repo-native agent tooling.** `scripts/context_map.py`, `scripts/wiring_map.py`, architecture/doc checks, generated agent context packs, workflow routines, and deterministic merge-state helpers make repo navigation executable. Preserve the principle, simplify the implementation.
7. **GitHub workflow safety patterns.** Code Quality, tool-pin checks, PR conflict/behind checks, CI rerun watchdog, manual BTD6 refresh PRs, dashboard data refresh, DB backups, AI evals, and subproject CI are valuable. A fresh repo should replace PAT-heavy or bespoke automation with GitHub-native features where possible.

### Biggest hallucination/data/provenance risks

- **Provider behavior can be hidden behind env.** `AI_DEFAULT_PROVIDER`, task-specific routing env vars, `AI_FALLBACK_PROVIDER`, and provider-specific API keys mean the same code can behave very differently in production, CI, and local runs.
- **BTD6 data has multiple provenance tiers.** Official Ninja Kiwi endpoints, committed CSV/JSON, parsed game dumps, wiki-derived formulas, DB facts, and manual strategy rows coexist. The rebuild must require source labels on every answer block and prohibit unlabelled cross-source merges.
- **Natural-language routing is complex and centralized in one large stage.** This reduces duplicate passive responders but creates a high-risk file where domain routing, model calls, deterministic refusals, conversation memory, and rendering meet.
- **Generated docs/context packs can drift.** They are useful orientation, but not source of truth. Fresh tooling should make freshness obvious and CI-enforced.
- **Command-only diagnostics are insufficient.** BTD6 and AI have diagnostics commands/services, but a rebuild should include panels/help routes so operators can see readiness, source health, stale data, and review backlog without memorizing commands.

### Best repo operations ideas

- Deterministic merge/conflict/behind checks using a single helper (`scripts/git_merge_state.py`) shared by workflows.
- One Code Quality workflow that runs docs, stale-claims, session-card gates, consistency, unit tests, architecture, wiring, and tool-pin style checks.
- Manual external-data refresh workflows that open reviewable PRs instead of pushing to main.
- Scheduled/dispatch routines recorded in versioned docs, with explicit token/PAT hazards.
- SHA-pinned actions plus `scripts/check_tool_pins.py` to keep workflow pins aligned with dev tooling.
- Generated agent context packs (`docs/agent/generated/*.context.md`) built from a curated manifest.

### What a future repo should simplify or centralize

- Split natural-language routing into small task-profile/domain-router modules instead of one giant stage.
- Make provider/model routing declarative (`TaskProfile`) rather than scattered between env, settings, routing, and tests.
- Centralize knowledge-domain data provenance into one schema with mandatory `source_label`, `source_url/key`, freshness, and confidence/trust tier.
- Use one ingestion runner abstraction for BTD6, Project Moon, YouTube, and future domains.
- Keep GitHub Actions minimal: Code Quality, data refresh PRs, backups, deploy, and subproject CI; avoid bespoke auto-merge/PAT machinery unless GitHub-native auto-merge cannot satisfy the workflow.

## 2. Source route and verification

### Docs read

Read or sampled the required orientation/current-state/subsystem/operations files: `.claude/CLAUDE.md`, `docs/collaboration-model.md`, `docs/current-state.md`, `docs/current-state/S2-btd6.md`, `docs/current-state/S3-ai-memory.md`, `docs/current-state/S4-docs.md`, `docs/current-state/S5-ops.md`, `docs/AGENT_ORIENTATION.md`, `docs/architecture.md`, `docs/ownership.md`, `docs/runtime_contracts.md`, `docs/repo-navigation-map.md`, `docs/repo-review-map.md`, `docs/ultracode/README.md`, `docs/subsystems/ai.md`, `docs/subsystems/btd6.md`, `docs/subsystems/media-youtube.md`, `docs/decisions/006-btd6-data-provenance-ownership.md`, `docs/decisions/007-media-youtube-ownership.md`, `docs/context-map-tooling.md`, `docs/operations/autonomous-routines.md`, `docs/operations/production-deployment.md`, `docs/agent/README.md`, and `docs/agent/index.yml`.

### Source roots inspected

- AI: `disbot/cogs/ai_cog.py`, `disbot/cogs/ai_review_cog.py`, `disbot/core/runtime/ai/`, `disbot/services/ai*`, `disbot/utils/db/ai*`, `disbot/views/ai/`, AI migrations and tests.
- BTD6: `disbot/cogs/btd6*.py`, `disbot/cogs/paragon_cog.py`, `disbot/views/btd6/`, `disbot/services/btd6*`, `disbot/utils/db/btd6*`, `data/btd6/`, BTD6 scripts, tests, and evals.
- Project Moon: `disbot/cogs/project_moon_cog.py`, `disbot/views/projmoon/`, `disbot/services/projmoon_*`, `disbot/data/projmoon/`, `disbot/utils/projmoon/`, tests.
- Media/YouTube: `disbot/cogs/media_maintenance_cog.py`, `disbot/services/youtube_*`, `disbot/utils/db/youtube_video_cache.py`, `disbot/views/youtube_*`, migration `049_youtube_video_cache.sql`, docs and tests.
- Tooling/ops: `.github/workflows/`, `.github/dependabot.yml`, `scripts/check_*`, `scripts/context_map.py`, `scripts/wiring_map.py`, `scripts/git_merge_state.py`, `scripts/run_evals.py`, `tools/agent_context/`, `docs/agent/`, `.claude/`, `.sessions/README.md`, `pyproject.toml`, `requirements*.txt`, `.pre-commit-config.yaml`, and subproject CI paths.

### Commands run and results

- `PYENV_VERSION=3.10.20 python3.10 --version` → pass, Python 3.10.20 available only after selecting pyenv version.
- `python3.10 scripts/context_map.py disbot/cogs/ai_cog.py` initially failed because `python3.10` was not selected and then because `yaml` was missing; after installing PyYAML under `PYENV_VERSION=3.10.20`, it passed and mapped AI cog imports, docs, and tests.
- `python3.10 scripts/context_map.py disbot/cogs/btd6_cog.py` passed after PyYAML install.
- `python3.10 scripts/context_map.py disbot/services/btd6_view_model_service.py` passed after PyYAML install.
- `python3.10 scripts/context_map.py disbot/cogs/project_moon_cog.py` passed after PyYAML install.
- `python3.10 scripts/context_map.py scripts/context_map.py` returned exit 2: non-`disbot/` files are intentionally not mapped.
- `python3.10 scripts/wiring_map.py --check` passed with advisory possible-dead-subscriber warnings for `ticket.opened` and governance visibility/cache/cleanup events.
- `python3.10 scripts/check_architecture.py --mode strict` initially failed on missing `yaml`; after PyYAML install, passed with 0 errors and 49 tracked warnings.
- `python3.10 scripts/check_tool_pins.py` passed.
- `gh pr view 1509 ...` could not run because `gh` is not installed in the environment.
- `python3.10 scripts/check_docs.py --strict` was run after adding this report and passed.

- `python3.10 scripts/btd6_probe.py --help` passed and confirmed the offline probe interface.
- `python3.10 scripts/btd6_probe.py --route "how much cash do rounds 1-10 give in btd6"` failed before probing because `discord` is not installed in the selected Python environment.
- `python3.10 scripts/run_evals.py --help` passed and confirmed the `--smoke`, `--btd6`, and `--btd6-only` modes.
- `python3.10 scripts/run_evals.py --smoke` failed before running the smoke matrix because `discord` is not installed in the selected Python environment.

### Open PR / active gate status

- Live GitHub PR verification was blocked by missing `gh`. No source claim in this report treats PR #1509 as merged truth.
- Current-state docs identify active BTD6 live retest/menu-layout and AI substrate/consistency-linter queues, but source code remains the authority for this map.
- `docs/agent/index.yml` still lists AI expansion gates around provider/provenance checks, caching/source-health clarity, behavior/config correctness, and orchestration foundation approval.
- `docs/operations/production-deployment.md` confirms merge-to-main deploys production, so any future workflow changes must account for merge=deploy.

### Verification limits

- No live Discord, Railway, GitHub settings, secrets, production DB, paid model calls, or external BTD6 dump credentials were used.
- Several context/doc claims are treated as advisory unless source-backed below.
- The report maps code architecture; it does not prove production settings, branch protection, required checks, or secret availability.

## 3. AI platform inventory

### Provider abstraction

Confirmed source-backed components:

- `core/runtime/ai/contracts.py`: typed `AITask`, `AIScope`, `AIResponseMode`, `AIRequestContext`, `AIToolSpec`, `AIToolChoice`, `AIToolBudget`, `CalculationEvidence`, `AIAnswerWithEvidence`, `AIRequest`, `AIResponse`, and `AIDiagnosticsSnapshot`.
- `core/runtime/ai/providers/base.py`: provider protocol and tool-loop helpers.
- `providers/openai_provider.py` and `providers/anthropic_provider.py`: provider-specific execution with tool-calling support.
- `providers/openai_moderation.py`: image moderation via OpenAI key.
- `gateway.py`: registers providers, resolves provider/model routing, redacts request payload/system prompts, wraps tool dispatch, handles fallback/degraded responses, and records diagnostics.

Reusable primitive: **`AIProviderGateway`**. Copy the idea, not the exact file shape; keep provider protocol, redaction, fallback, diagnostics, and tool-dispatch wrapper, but place it in a layer that does not violate architecture boundaries.

### Routing/task profiles

- `routing.py` resolves task-to-provider/model targets, with defaults for OpenAI and Anthropic and env fallback.
- `feature_flags.py` reads `AI_ENABLED`, `AI_DEFAULT_PROVIDER`, task enablement, tool enablement, server-member lookup, and setup-advisor provider flags.
- Tests cover routing disjointness and provider behavior (`tests/unit/runtime/ai/test_domain_routing_disjoint.py`, provider tests, task-router tests for Project Moon/YouTube/strategy channel).

Reusable primitive: **`TaskProfile`** with fields for task name, provider preference, model, response mode, tool budget, deterministic grounding requirements, cache policy, and eval suite.

### Natural-language gates

- `natural_language_stage.py` explicitly says the AI cog stays unregistered so this stage is the only passive responder.
- It detects direct bot mentions, strips mentions, derives `AIScope`, records visible user turns, gathers knowledge/context blocks, builds BTD6/Project Moon constraints/refusals, invokes the gateway, renders registered responses, redacts outbound text, and splits Discord messages.
- It contains deterministic refusals for BTD6 and Project Moon when data is absent or grounding is unsafe.

Reusable primitive: **`NaturalLanguageRouter`** plus per-domain `KnowledgeRouter` modules. Do not copy the monolith as-is.

### Context gathering

- `services/ai_context_service.py` and `services/ai_instruction_service.py` build base bot/guild/user/system context.
- `_gather_bot_knowledge_blocks` in `natural_language_stage.py` integrates feature facts, BTD6, Project Moon, and YouTube-style context.
- `services/btd6_ai_context_service.py`, `services/projmoon_context_service.py`, and `services/youtube_context_service.py` are domain context providers with length/provenance constraints.

Reusable primitive: **`ContextBlock`** with `domain`, `facts`, `source_label`, `freshness`, `max_chars`, and `render()`.

### Review-log loop

- `migrations/100_ai_review_log.sql` creates `ai_review_log` with redacted question/answer/correction fields.
- `utils/db/ai_review_log.py` provides DB access.
- `services/ai_review_log_service.py` handles capture/listing/triage behavior.
- `cogs/ai_review_cog.py` and `views/ai/` provide operator surfaces.
- `docs/operations/ai-review-backlog-runbook.md` documents the operational loop.

Reusable primitive: **`AnswerReviewLog`**. Preserve redacted storage, correction capture, task/provider metadata, and staff triage states.

### Preset loop

- `migrations/102_ai_answer_presets.sql` creates `ai_answer_presets` with guild/question key/answer fields and optional routed-task provenance.
- `utils/db/ai_presets.py` is explicit that redaction/normalization happens before DB calls.
- `services/ai_preset_service.py` and orchestration preset tests confirm presets are used to bypass/reuse answer behavior.

Reusable primitive: **`PresetAnswerStore`** keyed by normalized question, guild/scope, task, locale, and source/provenance metadata.

### Audits/redaction

- `redaction.py` redacts text and JSON-like payloads.
- `gateway.py` redacts the full payload/system prompt, provider input, tool results, and degraded responses.
- `services/ai_decision_audit_service.py`, `migrations/039_ai_policy.sql`, and AI policy DB tables provide decision audit history.

Reusable primitive: **`RedactionContract`** with tests proving every request field and tool result crosses the redactor.

### Settings/bindings

- `migrations/039_ai_policy.sql` creates instruction profiles and guild/channel/category/role policy tables.
- `services/ai_policy_mutation.py`, `services/ai_config_projection_service.py`, `utils/settings_keys/ai.py`, and views/cogs provide settings projection and mutation boundaries.
- `docs/ai-config-ownership.md` is a binding doc for config ownership.

Reusable primitive: **`AIConfigProjection`**: read-only projection separate from mutation service.

### Diagnostics

- `diagnostics.py` records requests/failures/successes and reports provider/redaction status.
- `services/ai_readiness_service.py`, `services/ai_introspection_service.py`, and diagnostics providers support readiness and self-knowledge.
- The rebuild should add a visible diagnostics panel, not only commands.

### Tests/evals

AI tests cover gateway, providers, redaction, prompt injection, natural-language stage, tool orchestration/calling, response rendering, memory, policy, presets, review log, readiness, settings projection, and domain routers. `.github/workflows/ai-evals.yml` manually runs `scripts/run_evals.py` with OpenAI/Anthropic keys and a BTD6 QA suite option.

### Failure modes

- Missing provider SDK/API key degrades behavior.
- Mis-set provider/model env can route to unregistered providers.
- Redaction contract expansion risk: new `AIRequest` fields must be covered.
- Monolithic natural-language stage increases regression risk.
- Domain routing ambiguity can hallucinate by sending deterministic questions to the model without facts.
- Review/preset tables rely on normalization before DB calls.

## 4. Knowledge-domain inventory

### BTD6

- **Data sources:** official Ninja Kiwi endpoints/source registry; committed `data/btd6/towers.csv` and `heroes.csv`; parsed game data; wiki-derived formulas for round XP/cash where not in game dump; DB facts/snapshots; staff strategy submissions.
- **Ingestion/extraction scripts:** `scripts/fetch_btd6_wiki_data.py`, `scripts/parse_gamedata.py`, `scripts/seed_btd6_data.py`, `scripts/upload_btd6_data.py`, `scripts/btd6_probe.py`, `scripts/btd6_patch_diff.py`, `scripts/btd6_gamedata_inventory.py`, `scripts/btd6_decode_inventory_report.py`, and related import/probe scripts.
- **Committed data:** `data/btd6/README.md`, `heroes.csv`, `towers.csv`, plus generated/parsed fixtures under the data tree where present.
- **Runtime DB tables:** `btd6_source_registry`, `btd6_source_audit`, `btd6_source_snapshots`, `btd6_facts`, `btd6_patch_notes`, `btd6_strategies`, `btd6_strategy_audit`, `btd6_ingestion_runs`, and `btd6_data_blobs`.
- **View-model services:** `services/btd6_view_model_service.py` feeds tower/hero/live-events/leaderboard browser views.
- **Context IDs/handles:** BTD6 AI context summaries carry stable IDs for towers/heroes/events/leaderboards/facts and render length-bounded source-labelled facts.
- **Answer routing:** natural-language stage and BTD6 grounding services decide deterministic refusal vs grounded AI answer vs panel/browser flow.
- **Source/provenance labels:** `btd6_ai_context_service.py`, `btd6_source_registry.py`, data migrations, parser comments, and tests assert source labels/freshness.
- **Evals/probes:** `scripts/run_evals.py`, BTD6 eval suite in `.github/workflows/ai-evals.yml`, `scripts/btd6_probe.py`, many BTD6 unit tests.
- **UI/browser panels:** `views/btd6/panel.py`, tower/hero/live-events/leaderboard browser views, admin panel, strategy review views.
- **Admin/ops refresh flows:** `cogs/btd6_ops_cog.py`, `views/btd6/admin_panel.py`, manual `btd6-data-refresh.yml`, seed/upload scripts.
- **Tests:** extensive services/utils/db/invariant/cog/script tests listed under `tests/unit/services/test_btd6_*`, `tests/unit/utils/test_btd6_*`, `tests/unit/scripts/test_btd6_*`.

### Project Moon

- **Data sources:** committed structural data under `disbot/data/projmoon/`; utility parsing/keyword helpers under `disbot/utils/projmoon/`.
- **Runtime:** `cogs/project_moon_cog.py`, `services/projmoon_data_service.py`, `services/projmoon_grounding_service.py`, `services/projmoon_context_service.py`, and `views/projmoon/`.
- **Context/provenance:** `ProjmoonContext` mirrors the BTD6 context pattern and appends honest provenance (`Limbus Company structural data`) to bounded facts.
- **Routing/tests:** AI natural-language Project Moon tests and task-router tests confirm a deterministic domain route exists.
- **Rebuild note:** copy the BTD6-style context/provenance idea, but Project Moon should get the same explicit domain spec/ingestion/freshness schema as BTD6.

### Media / YouTube

- **Data sources:** YouTube metadata/transcripts fetched by `youtube_fetch_service.py` and cached in Postgres.
- **Runtime DB:** `migrations/049_youtube_video_cache.sql`; `utils/db/youtube_video_cache.py` supports get/upsert/purge/stats.
- **Runtime/services:** `youtube_context_service.py`, `youtube_fetch_service.py`, `youtube_diagnostics.py`, `media_maintenance_cog.py`, `views/youtube_embeds.py`, and `views/youtube_renderers.py`.
- **Docs/ownership:** `docs/subsystems/media-youtube.md` and decision 007 define ownership.
- **Tests:** YouTube cache, diagnostics, context, fetch service, and AI task-router tests.
- **Rebuild note:** preserve transcript/metadata caching and diagnostics, but make cache TTL, transcript source, video ID normalization, and summarization policy explicit in a domain spec.

### Other deterministic knowledge domains

Fishing, games, settings, health diagnostics, and help projections use similar patterns, but they are out of deep scope here. The key rebuild lesson is to make deterministic domains first-class specs instead of ad hoc services.

## 5. BTD6 deep mapping

### Runtime cogs

- `btd6_cog.py`: product subsystem command/panel entrypoint; context map identifies docs and tests.
- `btd6_events_cog.py`: live events surfaces.
- `btd6_ops_cog.py`: admin/operator refresh and readiness surfaces.
- `btd6_reference_cog.py`: reference/browser surfaces.
- `btd6_strategy_cog.py`: staff strategy submission/review flow.
- `paragon_cog.py`: paragon calculator and data interactions.

### Ops/admin refresh surfaces

- `views/btd6/admin_panel.py` and `btd6_ops_cog.py` provide in-bot ops surfaces.
- `.github/workflows/btd6-data-refresh.yml` is manual only, fetches a dump, runs parse/audit/inventory/decode scripts, and opens a reviewable PR rather than pushing to main.
- `scripts/seed_btd6_data.py` seeds deterministic data into `btd6_data_blobs`; `scripts/upload_btd6_data.py` uploads a manifest/tree to public object storage.

### Data pipeline scripts

- `fetch_btd6_wiki_data.py`: fetches tower/hero data from Bloons wiki API and writes CSV rows.
- `parse_gamedata.py`: parses game dumps, overlays structured data, audits anchors, builds round XP/cash formulas with source notes, and emits data files.
- `btd6_gamedata_inventory.py` and `btd6_decode_inventory_report.py`: inventory/decode coverage.
- `btd6_patch_diff.py`: patch diffing.
- `btd6_probe.py`: grounding triage for AI answerability.
- `seed_btd6_data.py` and `upload_btd6_data.py`: runtime data distribution.

### Data freshness model

- `btd6_source_registry.py` classifies source freshness buckets and exposes health/listing/usable-source checks.
- `btd6_ingestion_runs` and source audit/snapshot tables capture refresh attempts and source history.
- `btd6_data_blobs.sha256` stores source-file provenance for committed deterministic data.
- Fresh repo recommendation: define freshness policy once per source in `SourceProvenanceSpec`; avoid each service inventing freshness semantics.

### Context bridge to AI

- `btd6_ai_context_service.py` returns dataclasses like `ActiveEventSummary`, `EventDetailsSummary`, `EntitySummary`, `RestrictionSummary`, `LeaderboardSummary`, `SourceStatusSummary`, and `FactSummary`, each with `render()` and provenance-preserving length caps.
- Natural-language stage calls BTD6 grounding/refusal functions before model invocation.
- Tests pin BTD6 grounding injection, answer guidance, context tower stats, fact-store fetch, and source labels.

### Paragon calculator/data

- `paragon_cog.py`, `services/btd6_paragon_*`, paragon tests, and calculator commands handle paragon names, costs, income/effects, ability rosters, elite replies, and stats.
- Best rebuild idea: calculators should emit `CalculationEvidence` objects usable by both embeds and AI answers.

### Live events/heroes/towers/leaderboards

- View-model service is imported by tower browser, hero browser, live-events, leaderboard browser, and panel views.
- AI context service exposes current events, event details, tower summary, hero summary, restrictions, leaderboard summary, and source status.

### Known gates / owner-live retest items

- Current-state docs mention BTD6 live retest, menu layout, curated counter lists, decode items, and owner-live verification. These are not treated as merged requirements unless source-backed.
- Architecture strict check still warns on `views/btd6/admin_panel.py` and `views/btd6/strategy_review.py` direct `discord.ui.View` inheritance; acceptable tracked debt, but fresh repo should start on a base-view primitive.

### Best functions and anti-patterns

- Preserve: source registry freshness, AI context dataclasses with provenance-preserving render, BTD6 probe/evals, manual refresh PR workflow, seed/upload manifest tooling, view-model service for UI browsers.
- Redesign: monolithic natural-language BTD6 branches; duplicated source labels across scripts/services; split DB/file/cloud data providers behind one data-provider interface.
- Discard/avoid: hidden “AI knows game facts” paths; unlabelled wiki/game-dump merges; live API requirements in unit/eval paths; command-only diagnostics.

## 6. Repo tooling and operations inventory

| Area | Current files/workflows | Fresh-repo recommendation |
|---|---|---|
| CI quality workflow | `.github/workflows/code-quality.yml`, `scripts/check_quality.py`, docs/stale/session/consistency/test/architecture checks | **Copy idea, redesign smaller.** Keep one required quality workflow with named gates and fast/slow split. |
| Architecture/doc checks | `scripts/check_architecture.py`, `scripts/check_docs.py`, `scripts/check_stale_claims.py`, `scripts/check_consistency.py` | **Copy nearly as-is concept.** Start strict early to avoid migration debt. |
| Context map/packs | `scripts/context_map.py`, `docs/context-map-tooling.md`, `tools/agent_context/`, `docs/agent/index.yml`, generated packs | **Copy idea.** Make maps work for all repo roots, not just `disbot/`. |
| Wiring map/event observability | `scripts/wiring_map.py`, EventBus catalogue, tests | **Copy nearly as-is.** Keep dead subscribers advisory and uncatalogued events gated. |
| Tool pin checks | `scripts/check_tool_pins.py`, `.github/workflows/tool-pins.yml`, SHA-pinned actions | **Copy.** Valuable low-cost supply-chain guard. |
| Dependabot | `.github/dependabot.yml` | **Copy/simple.** Keep update cadence modest and grouped. |
| Auto-merge/enabler | `.github/workflows/auto-merge-enabler.yml` | **Replace with GitHub-native auto-merge where possible.** Keep docs of autonomy model. |
| PR conflict/behind checks | `pr-conflict-guard.yml`, `pr-auto-update.yml`, `scripts/git_merge_state.py`, `scripts/check_pr_mergeable.py` | **Copy helper, simplify workflows.** Prefer branch protection + native auto-update if available. |
| CI rerun watchdog | `ci-rerun-watchdog.yml`, `scripts/check_ci_coverage.py` | **Keep if flaky/missed CI is real.** Otherwise discard initially. |
| Dashboard/data refresh | `dashboard-data-refresh.yml`, `scripts/export_dashboard_data.py` | **Copy idea.** Automated generated-data PRs are good; keep narrow. |
| Backups | `backup-db.yml` | **Copy/redesign for target infra.** Preserve integrity check before artifact upload. |
| AI eval workflow | `ai-evals.yml`, `scripts/run_evals.py` | **Copy idea.** Separate free/offline deterministic evals from paid provider evals. |
| BTD6 data refresh | `btd6-data-refresh.yml` | **Copy pattern.** External data refresh must open PR, never push to main. |
| Botsite/dashboard/design-system CI | `botsite-ci.yml`, `dashboard-ci.yml`, `design-system-ci.yml` | **Keep if subprojects remain.** Otherwise replace with one matrix workflow. |
| Codex final review | `codex-final-review.yml` | **Discard initially.** Reintroduce only if the same born-red review gap recurs. |
| Routines | `docs/operations/autonomous-routines.md`, reconciliation trigger | **Preserve as docs-first workflow specs.** Reduce PAT reliance. |

## 7. Best ideas/functions to preserve

| File/function/class/workflow | Problem solved | Value | Disposition | Hidden dependencies |
|---|---|---|---|---|
| `core/runtime/ai/gateway.py::AIGateway` | Safe provider execution/fallback/redaction/tool dispatch | One choke point for model IO | Redesign around idea | Provider SDKs, env vars, diagnostics, services imports |
| `core/runtime/ai/contracts.py` dataclasses/enums | Typed AI boundary | Makes evals/tests/provider code stable | Copy nearly as-is | Task taxonomy must match product domains |
| `core/runtime/ai/redaction.py` | Scrubs payload/text/tool results | Privacy and review-log safety | Copy with stronger tests | Pattern coverage can be incomplete |
| `core/runtime/ai/routing.py` | Task-to-provider/model routing | Enables task-specific model policy | Redesign as declarative `TaskProfile` | Env drift, model availability |
| `services/ai_review_log_service.py` + `utils/db/ai_review_log.py` | Captures answer/correction triage | Self-improving answer loop | Copy idea | Migration 100, redaction before storage |
| `services/ai_preset_service.py` + `utils/db/ai_presets.py` | Reusable reviewed answers | Reduces repeated hallucinations/cost | Copy idea | Normalized question keys, guild scope |
| `btd6_ai_context_service.py` render dataclasses | Grounded, bounded source-labelled facts | Domain-safe AI context | Copy pattern | BTD6 DB/provider availability |
| `btd6_view_model_service.py` | UI browser read model | Separates UI from data plumbing | Copy pattern | Resolver/body coercion/db provider |
| `btd6_source_registry.py` | Freshness/trust/source health | Provenance and ops visibility | Copy as `SourceProvenanceSpec` | Registered sources and audit tables |
| `scripts/parse_gamedata.py` | Game dump extraction/audit | Repeatable deterministic data pipeline | Redesign around ingestion framework | Dump availability/licensing |
| `scripts/btd6_probe.py` | AI grounding triage | Fast answerability debugging | Copy pattern | Corpus expectations and local data |
| `projmoon_context_service.py::ProjmoonContext` | Small domain context bridge | Proves pattern generalizes | Copy idea | Committed structural data completeness |
| `youtube_context_service.py` + cache DB | Metadata/transcript cache context | Avoids repeated fetch/model work | Copy idea | YouTube API/transcript limits/TTL |
| `scripts/context_map.py` | Agent orientation per file | Reduces codebase discovery cost | Copy and generalize | PyYAML, manifest coverage, disbot-only limitation |
| `scripts/wiring_map.py` | EventBus observability | Finds uncatalogued events | Copy | AST limitations/false positives |
| `scripts/git_merge_state.py` | Deterministic merge state | Shared workflow truth | Copy | Git availability/fetch depth |
| `.github/workflows/btd6-data-refresh.yml` | Reviewable external-data refresh | Prevents silent data mutation | Copy pattern | External dump URL, create-PR action |
| `.github/workflows/backup-db.yml` | Scheduled DB backup with integrity check | Operational safety | Redesign for target infra | DB URL secret, artifact retention |
| `tools/agent_context/` | Generated context packs | Better agent handoff | Copy | Pack freshness CI |

## 8. Hidden dependencies and rebuild hazards

- **AI provider/env/secrets:** `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `AI_ENABLED`, `AI_DEFAULT_PROVIDER`, `AI_FALLBACK_PROVIDER`, task routing env vars, provider SDK packages, and optional moderation provider.
- **Review log/preset schemas:** migrations 100 and 102; normalized question keys; guild-scoped rows; redacted question/answer/correction text.
- **Redaction contracts:** every model input, output, tool argument/result, review row, and preset mutation must pass a single redactor.
- **Model routing assumptions:** task names in `AITask` must line up with provider/model defaults, settings, evals, and natural-language routers.
- **Knowledge-domain context IDs:** BTD6 tower/hero/event/leaderboard/fact IDs and Project Moon entry IDs must stay stable across UI, AI, eval fixtures, and DB rows.
- **Licensing/provenance:** BTD6 game dumps, Ninja Kiwi endpoints, Bloons wiki data, Project Moon structural data, and YouTube transcripts have different provenance and licensing expectations.
- **Seed/refresh ordering:** source registry before facts; deterministic blobs before postgres/cloud backend; ingestion run/audit before source health; AI evals after data refresh.
- **Eval fixture assumptions:** BTD6 QA corpus assumes specific data version/source labels and may fail if data updates without golden refresh.
- **GitHub Actions tokens/PAT:** routines/reconciliation and some PR/status workflows document `ROUTINE_PAT` or status permissions; default `GITHUB_TOKEN` may not trigger external routines.
- **Generated docs/context freshness:** generated context packs and current-state docs can lag source.
- **CI required-check assumptions:** auto-merge/enabler workflows assume specific check names and branch protection shape not visible locally.
- **Dashboard/botsite data pipelines:** generated JSON and subproject CI can drift from bot source if export scripts are not required checks.

## 9. Fragmentation and duplication inventory

### Critical rebuild lesson

- **AI natural-language stage monolith:** domain routing, context gathering, refusals, memory, gateway calls, render dispatch, and review logging should be split into composable routers/task profiles.
- **BTD6 data providers:** file, Postgres, cloud, parsed dump, wiki, and live endpoint concepts must share one provenance schema.
- **Workflow PAT complexity:** routine triggers, auto-merge, conflict statuses, and reconciliation can become fragile if dependent on expiring PATs.

### Important improvement

- **Diagnostics split across commands/services/views:** give AI/BTD6/media a common diagnostics panel plus command route.
- **Context maps limited to `disbot/`:** generalize to scripts, workflows, and subprojects.
- **Provider routing via env:** expose a clear runtime settings projection with safe defaults and diagnostics.

### Cleanup

- Direct `discord.ui.View` inheritance warnings in BTD6 admin/strategy views and unrelated views should be eliminated in a fresh repo by starting with one base-view library.
- Generated current-state and planning docs should have automatic stale markers.

### Acceptable specialization

- BTD6-specific parsers/calculators are acceptable because the domain is complex.
- YouTube cache/diagnostics can remain separate because API/cache behavior differs from static game data.
- Project Moon keyword/grounding utilities can remain domain-specific if they implement the shared knowledge-domain interfaces.

## 10. Future new-repo recommendations

1. **`AIProviderGateway`** — source evidence: `gateway.py`, provider modules, redaction tests. Centralize provider calls, fallback, diagnostics, and tool result redaction.
2. **`TaskProfile`** — source evidence: `AITask`, `routing.py`, `feature_flags.py`, AI eval workflow. Declaratively define provider/model/tools/grounding/eval expectations.
3. **`ContextBlock`** — source evidence: BTD6/Project Moon/YouTube context services. Make domain facts typed, bounded, source-labelled, and freshness-aware.
4. **`AnswerReviewLog`** — source evidence: migration 100, review log service/cog/tests/runbook. Store redacted answer events and corrections.
5. **`PresetAnswerStore`** — source evidence: migration 102, preset DB/service/tests. Store reviewed answers keyed by normalized task/question/scope.
6. **`KnowledgeDomainSpec`** — source evidence: BTD6 subsystem, Project Moon services, media docs. Define commands, panels, data sources, context builder, eval suite, and diagnostics.
7. **`SourceProvenanceSpec`** — source evidence: BTD6 source registry/freshness/data blobs/source labels. Require source key, trust tier, freshness, license note, and answer label.
8. **`IngestionPipeline`** — source evidence: BTD6 parse/fetch/seed/upload/refresh workflow and YouTube fetch/cache. Standardize fetch, parse, validate, audit, diff, PR, seed.
9. **`ViewModelContextHandle`** — source evidence: `btd6_view_model_service.py` and browser views. Use stable handles across UI panels, AI context, and eval fixtures.
10. **`EvalHarness`** — source evidence: `scripts/run_evals.py`, `.github/workflows/ai-evals.yml`, BTD6 probe/tests. Separate deterministic offline evals from paid provider evals.
11. **`AgentContextPack`** — source evidence: `docs/agent/index.yml`, `tools/agent_context/`, generated packs, context-map tooling. Generate task-specific orientation from source manifests.
12. **`RepoQualityGate`** — source evidence: code-quality workflow, architecture/docs/wiring/tool-pin checks. Define required checks as code.
13. **`WorkflowRoutineSpec`** — source evidence: `docs/operations/autonomous-routines.md`, reconciliation trigger, production deployment docs. Version autonomous routine prompts and their token/permission assumptions.

## 11. Handoff to other mapping sessions

### Needed from Part 1 platform primitives

- Base Discord view/navigation lifecycle (`BaseView`, hub/panel conventions, interaction ack/defer helper).
- EventBus/catalogue contract and message pipeline stage interface.
- Settings/bindings/resource requirement schema.
- Diagnostics provider registry and health snapshot model.
- Database migration and repository conventions.

### Needed from Part 2 admin/safety dependencies

- Permission tiers and owner/staff gates for AI review, BTD6 ops, media maintenance, and data refresh commands.
- Audit log mutation contract for AI policy changes, review actions, strategy approval, and source refreshes.
- Redaction/privacy policy for stored prompts, YouTube transcript snippets, Discord message context, and review corrections.
- Safety rules for autonomous routines, merge=deploy, rollback, and production verification.

### Needed from Part 3 product/game/community dependencies

- Product-level command/menu taxonomy for where BTD6, Project Moon, media, and AI panels live.
- Game/community context facts that AI may reference safely.
- User-facing help copy conventions and browser panel UX patterns.
- Live verification scripts/checklists for owner-walked BTD6/media/AI answers.
