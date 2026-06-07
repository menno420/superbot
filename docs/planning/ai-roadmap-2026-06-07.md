# SuperBot AI roadmap — grounded explanation and safe orchestration

> **Status:** `plan` — source-verified planning guide for later Claude Opus planning
> sessions. **This is not implementation approval.** Each implementation slice still
> requires current-source verification, owner decisions where identified, and the
> normal promotion/approval path.
>
> **Verified:** 2026-06-07 against worktree commit `0efd55a`, live public GitHub API,
> and the sources listed in §14. Source code and binding docs win over this roadmap.
> Opus must re-verify source and live PR state before turning any phase into an
> implementation plan. AI action/write paths remain deferred unless separately
> approved.

## 1. Executive summary

SuperBot AI should become a **grounded explanation and orchestration layer over
service-owned deterministic facts**, not a parallel memory, policy, health, update,
or action system.

The intended destination is an AI layer that can safely explain:

- what the bot can do and which capabilities are available to this user, guild, and
  channel;
- what changed recently, how to use it, and which paths remain unverified;
- why AI replied, did not reply, degraded, or could not answer;
- what bot, AI, setup, server-management, and subsystem health/readiness states mean;
- what should be tested next after an update;
- what approved docs and source-backed BTD6 information are available; and
- which proposed future tools are read-only, advisory, action-gated, deferred, or
  rejected.

The ordering is deliberate. First consolidate the existing tool loop and deterministic
metadata. Then build update/help/knowledge read models. Only after those contracts are
stable should SuperBot add bounded attachment/media readers or external connectors.
Actions require a separate proposal/confirmation architecture and explicit owner
approval per action; they do not belong in `services.ai_tools`.

## 2. Verification snapshot and stop-condition result

| Check | Verified result | Consequence |
|---|---|---|
| Live GitHub default branch | `main` via `GET /repos/menno420/superbot` | Re-verify before every Opus plan. |
| Open PRs | None returned by live public GitHub API on 2026-06-07 | No AI/docs/update/server-management in-flight collision blocked this roadmap. |
| Latest merged PR | #564, `docs: consolidate BTD6 island + archive retired burst + hard reachability gate`, merged 2026-06-07 15:09:08Z | Current worktree includes the latest merge. |
| Bot-awareness state | `docs/bot-awareness-implementation-plan.md` and source confirm PR1–PR6 shipped; typed health, `!platform health`, startup health, grouped observations, owner-only AI snapshot, and durable findings exist | Reuse these owners; do not create a second diagnostics system. |
| AI tool source | `services.ai_tools` states and implements read-only tools using `AIToolSpec`, `ToolRegistry`, and scope filtering | Planned descriptors/toolsets/budgets remain foundation work, not shipped truth. |
| Migration chain | `disbot/migrations/057_operational_health_findings.sql` owns durable health findings; latest migration is `058_cleanup_policy_version.sql` | Any update-awareness schema starts at 059 or later after re-verification. |
| Stop conditions | None triggered | A confident planning-only roadmap is appropriate. |

Important verification gap: public GitHub API showed repository/PR state, but `gh` was
not installed and no authenticated checks/status payload was inspected. Production live
behavior, provider credentials, Discord permissions, and the remaining documented live
test of the PR5 AI diagnostics path were not verified.

## 3. Current state map

“Stable” below means source-backed and test-backed in the repository, not a production
SLA. “Gated” means policy/scope/config gates exist. “Docs-only” means the named future
abstraction is not present in source.

| Area | Current owner / evidence | What exists now | Missing / limit | State |
|---|---|---|---|---|
| AI policy and config | `services/ai_natural_language_policy.py`, `services/ai_config_projection_service.py`, `services/ai_policy_mutation.py`, `docs/ai-config-ownership.md` | Guild/category/channel/role policy resolution, config projection, dry-run trace, deterministic mutation seams | No orchestration-profile/toolset policy | Stable, gated |
| AI readiness and diagnostics | `services/ai_readiness_service.py`, `services/ai_diagnostics_service.py`, `core/runtime/ai/diagnostics.py`, `cogs/ai_cog.py` | Provider/config/policy/readiness checks and operator-facing explanations | Not a universal update/test/readiness model | Stable, gated |
| Natural-language message flow | `core/runtime/ai/natural_language_stage.py` | Central message-level policy/cooldown/task/context/tool/provider/render/audit flow; bot knowledge and BTD6 grounding integration | No resolved orchestration profile, evidence envelope, or dynamic budget contract | Stable choke point; expansion gated |
| Provider adapters | `core/runtime/ai/providers/{base,openai_provider,anthropic_provider,deterministic_provider}.py` | Provider-neutral request/response contracts and bounded tool loops for OpenAI/Anthropic plus deterministic fallback | Provider-neutral tool-choice modes and shared budget semantics are not shipped | Stable with degraded fallback |
| Tool registry | `services/ai_tools.py`, `core/runtime/ai/contracts.py` | Read-only `AIToolSpec`; per-request `ToolRegistry`; scope-filtered tools; server, audit, health, time, user-standing, and many BTD6 reads | No `AIToolDescriptor`, named toolsets, capability tags, common evidence/result contract, or per-request selector/budget | Stable current behavior; future catalogue docs-only |
| Scope enforcement | `services/ai_tools.py::build_registry`, `AIScope`, `_scope_allows`; `_derive_scope` in natural-language stage | More-privileged tools are omitted from the offered registry; bot owner maps to platform-owner scope | Must keep proving scope can only narrow; no future connector/action authority yet | Stable, gated |
| Bot self-knowledge | `services/bot_knowledge_service.py`, `core/runtime/command_descriptions.py`, `core/runtime/command_surface_ledger.py` | Deterministic command catalogue/knowledge blocks, identity/tier context, command descriptions and surface classifications | No canonical feature maturity, guide-card, update/release, or tested-since-update metadata | Stable base; incomplete product model |
| Help and discovery | `cogs/help_cog.py`, `cogs/help/route.py`, command descriptions/ledger | Typed help routes, hub discovery, visible command lists, shared hidden-from-help classification | No unified audience-aware feature index/search or update-aware help | Stable; extend, never duplicate |
| AI decision audit | `services/ai_decision_audit_service.py`, `utils/db/ai.py`, `cogs/ai_cog.py` | Exactly one structured decision row per natural-language stage invocation; why-no-response/audit reads; no raw message content | No orchestration trace, offered-tool hash, budget outcome, or connector trace | Stable, privacy-bounded |
| Typed operational health | `services/health_contracts.py`, `services/health_snapshot_service.py`, `cogs/diagnostic_cog.py`, `cogs/diagnostic/_platform_embeds.py` | Typed aggregate snapshots, deterministic `!platform health`, startup health rendering | Does not model releases or command verification | Stable, shipped bot-awareness |
| Persistent health findings | `services/health_findings_service.py`, `utils/db/health_findings.py`, migration 057 | Durable deduped operational findings with retention; grouped recent-error observations feed snapshots | Not an update ledger; no release correlation key today | Stable, shipped bot-awareness |
| AI diagnostics health tool | `services.ai_tools::_DIAGNOSTICS_HEALTH_SPEC` and handler | Owner-only bounded `diagnostics_health_snapshot` read | Production PR5 AI-path live test remains documented as outstanding | Stable source; gated; live verification gap |
| BTD6 grounding/faithfulness | `services/btd6_grounding_service.py`, `services/btd6_ai_service.py`, many BTD6 read tools, `docs/btd6/*`, ADR-006 | Approved tool results and grounded facts constrain BTD6 replies; provenance/readiness controls exist | Complex orchestration/evidence contracts incomplete; new extraction is gated | Stable guarded core; expansion gated |
| BTD6 strategy workspace | `services/btd6_strategy_service.py`, strategy mutation/review services and cogs | Existing deterministic strategy records/review seams | Broad AI strategy workspace requires provenance, orchestration, review, and product decisions | Existing seam; future lane gated |
| Command lifecycle telemetry | `bot1.py` command start/completion/error listeners and metrics/event logging | Runtime command outcome telemetry already exists | No durable, release-keyed “tested since update” truth; raw success alone is not necessarily verification | Stable telemetry; missing read model |
| Platform/diagnostics panels | `cogs/diagnostic_cog.py`, `cogs/diagnostic/_platform_embeds.py`, `views/diagnostic/*` | Existing owner/platform diagnostics commands and panel surfaces | No Recent Updates/update confidence item | Stable owner surface; extend |
| Setup advisor | `services/setup_ai_advisor.py` and server-management/setup services/docs | Existing bounded explanation seam over deterministic setup state | Must not become an AI mutation or second setup engine | Existing advisory seam; gated expansion |
| Automation/scheduler | `services/automation_registry.py`, `automation_scheduler.py`, `automation_executor.py`, `automation_mutation.py` | Deterministic automation ownership already exists | AI does not own schedules/actions; proposal/confirmation seam is not built | Stable deterministic owner; AI actions deferred |
| Evaluations/tests | `tests/unit/runtime/ai/`, `tests/unit/services/test_ai_tools.py`, BTD6/health/docs/invariant suites, `docs/ai-guard-coverage-map.md` | Guard, provider, tool, grounding, health, and document checks exist | No shared orchestration trace/budget/connector/action eval suite | Strong base; expand per phase |
| Broad future AI capabilities | `docs/ai-tool-capability-roadmap.md`, `docs/ideas/ai-extra-tool-capability-ideas.md`, future-direction brainstorm | Source-aware options and safety analysis | Not implementation approval; most capabilities do not exist | Plan/ideas only |

### Source facts that constrain every next plan

1. `services.ai_tools` is explicitly read-only and tells future writers to use
   deterministic mutation services after explicit confirmation.
2. The natural-language stage is the central message choke point. New features must not
   create a second message-level AI pipeline.
3. Current provider adapters already have bounded tool loops; SuperBot does not need a
   general autonomous-agent framework.
4. The help router, command surface ledger, diagnostics snapshots/findings, command
   telemetry, automation services, setup advisor, and BTD6 provenance owners already
   exist. Future plans must extend them instead of creating parallels.
5. `services.ai_memory_service.py` exists for bounded conversation context, but it is not
   authority for durable operational/product truth and must not become so.

## 4. Existing documentation reconciliation

| Document | Status / authority | Current usefulness | Reconciliation into this roadmap | Must not be treated as |
|---|---|---|---|---|
| `docs/subsystems/ai.md` | Reference folio; routes to binding owners/source | Best AI subsystem entry point and current owner-intent summary | Keep as folio; link this roadmap as planning context after review | Implementation approval or replacement for binding docs |
| `docs/ai-config-ownership.md` / `docs/ai-service-integration-map.md` | Binding/reference ownership guidance | Defines config/mutation boundaries and existing integration seams | Governs all phases, especially actions/connectors | Permission for AI writes |
| `docs/ai-readiness-plan.md` | Historical/plan context with shipped foundations | Explains readiness rationale | Reuse existing readiness owner; do not restart plan | Current global roadmap |
| `docs/ai-tool-capability-roadmap.md` | `plan`, source-verified capability triage | Strong safety sequencing and first-foundation recommendation | This roadmap consolidates its capability sequence; retain it as focused capability rationale | Approval for any listed tool |
| `docs/ai-complex-request-tool-orchestration-plan.md` | `plan`, research-backed design | Canonical detailed design direction for catalogue/toolsets/budgets/complex BTD6 orchestration | Phase 1 should revise/lock this document rather than invent a second orchestration plan | Shipped `AIToolDescriptor`, toolsets, policies, budgets, or workflows |
| `docs/bot-awareness-implementation-plan.md` | Living ledger; programme complete | Shipped-status authority for bot-awareness PR1–PR6 and remaining live test | Treat as completed dependency and historical delivery ledger | A request to build more health infrastructure |
| `docs/bot-awareness-diagnostics-plan.md` | Reference/source map | Useful architecture rationale | Keep as historical map; implementation authority moved to completed plan | Active execution plan |
| `docs/ai-guard-coverage-map.md` | Reference verification artifact | Confirms expansion choke-point guards | Keep as mandatory pre-expansion check; add new invariant coverage per phase | Proof that future tools/actions are automatically safe |
| `docs/ideas/future-product-direction-2026-06-07.md` | `ideas`, capture-only | Broad product direction and do-not-duplicate seams | Feed candidate lanes and questions only | Sequencing, approval, or current truth |
| `docs/ideas/ai-extra-tool-capability-ideas.md` | `ideas`, backlog | Detailed capability/security brainstorm | Capability matrix merges its non-duplicate ideas | Approval or a standalone implementation backlog |
| `docs/planning/superbot-ideas-lab-2026-06-05.md` | Mostly ideas; §2 and §6 binding for backlog handling | Gate/rejection ledger | Its rejection/gate rules constrain this roadmap | Approval for non-binding suggestion rows |
| `docs/btd6/btd6-derived-value-groundedness-finding.md` | BTD6 finding (the requested root-level path does not exist) | Correct source for derived-value grounding risk | Keep BTD6/source-heavy expansion gated | Permission to resume extraction |
| `docs/current-state.md` | Living ledger, not binding | Global status router | Mention this roadmap only if promoted into an active candidate | Authority over source or merged PRs |

Known stale/superseded details: `docs/architecture.md` contains a hand-maintained diagram
label showing 51 migrations, while the authoritative migration directory reaches 058.
Some older roadmap text discusses bot-awareness PRs as pending; the completed
bot-awareness ledger and source now win. These do not block this roadmap, but future doc
cleanup should avoid broad unrelated edits.

## 5. Roadmap principles

1. **Deterministic facts first; AI explanation second.** AI may summarize, compare, and
   explain service-owned facts, but does not invent durable truth.
2. **Read models belong to their deterministic owner.** AI consumes bounded projections;
   it does not query arbitrary tables/files/logs or parse Markdown as runtime truth.
3. **`services.ai_tools` remains read-only.** Future actions use a separate, explicitly
   approved proposal/confirmation path.
4. **Future action invariant:** typed proposal → deterministic validation/risk summary →
   human confirmation → click-time reauthorization → service-owned mutation → audited
   result → rollback/cancel path.
5. **Never expose arbitrary file, SQL, shell, URL/endpoint, credential, raw runtime log,
   or raw CI-log access.** Fixed allowlisted operations only.
6. **Do not duplicate owners.** No parallel health dashboard, governance simulator,
   Help router, route registry, command telemetry system, update ledger, scheduler, or
   audit write pipeline.
7. **No AI-authored durable truth without deterministic owner confirmation.** Generated
   drafts and summaries remain drafts.
8. **One fact, one home.** Folios route; binding docs govern; living ledgers track;
   plans sequence; ideas capture.
9. **Scope and policy can only narrow authority.** Provider/model output never expands
   Discord, guild, capability, connector, or action permissions.
10. **Every result is bounded and attributable.** Strict schemas, typed result contracts,
    evidence/freshness metadata, redaction, cost/time budgets, safe traces, metrics,
    deterministic fallback, and kill switches are phase-entry requirements.
11. **Discord-first, reusable read models.** A later website companion may reuse mature
    services, but must not drive premature duplicate APIs/state.
12. **Reversible slices.** Each PR must preserve current behavior by default, have a
    narrow rollback, and stop when ownership/security decisions are unresolved.

## 6. Unified phased roadmap

### Phase 0 — Reconcile and freeze current AI truth

**Goal:** remove ambiguity before planning runtime expansion.

- Re-verify live PRs, migration head, bot-awareness shipped state, scope derivation,
  provider loops, current tools, command knowledge, BTD6 grounding, and tests/evals.
- Correct only materially stale source-pinned docs; do not perform a broad doc sweep.
- Produce a current source map and unresolved-decision list.

**Output:** this roadmap is the initial source map. Before implementation, Opus should
refresh `docs/ai-complex-request-tool-orchestration-plan.md` and the relevant focused
plan. **No runtime changes.**

### Phase 1 — Canonical AI orchestration foundation

**Goal:** create/finalize one reusable, provider-neutral foundation before net-new tools.

Required design:

- compatibility-preserving descriptor/catalogue over current `AIToolSpec`;
- named built-in toolsets and deterministic policy/toolset resolver;
- provider-neutral tool-choice modes and explicit degraded behavior;
- strict schemas plus bounded typed result/evidence envelopes;
- call/result-byte/token/time/expensive-tool budgets;
- safe orchestration trace and audit fields without raw prompt/result leakage;
- metrics, invariant tests, provider parity tests, and unchanged-behavior defaults.

This foundation must serve current general/server/health tools, BTD6 complex requests,
and later docs/connectors. The BTD6 orchestration plan is the detailed design input;
Phase 1 must not produce a separate BTD6-only registry or import an autonomous-agent
framework.

**Gate:** Opus resolves descriptor compatibility, policy ownership, audit shape, and
provider behavior before implementation. No new external/action tools in this phase.

### Phase 2 — Bot self-knowledge and help/discovery upgrade

**Goal:** let deterministic metadata answer “what can the bot do here?” consistently.

Extend—not replace—`bot_knowledge_service`, `command_descriptions`, the command surface
ledger, and the Help router with:

- richer command/panel/feature metadata and stable identifiers;
- audience/scope/capability-aware summaries and denial explanations;
- maturity/availability/degraded labels owned by deterministic services;
- a reusable help/discovery index consumed by Help and AI knowledge blocks;
- hooks for guide cards and later update-aware help.

**Missing today:** feature-level metadata, maturity, release linkage, guide cards, and a
single audience-aware feature discovery projection. **Do not create a second Help
router or infer availability from docs text.**

### Phase 3 — Update Awareness / Release Confidence

**Goal:** turn update-log/test-awareness intent into a deterministic platform read model
that AI can later explain.

**Recommended architecture (candidate names, not approved):**

- owner service: `services/update_awareness_service.py`;
- DB owner: `utils/db/update_awareness.py`;
- structured manifest entities: `bot_updates`, `bot_update_features`,
  `bot_update_command_tests`, `bot_update_verification_runs`;
- relationship: update → subsystem → changed feature/command → guide card → verification
  state → command usage since release → related health findings/errors;
- deterministic surfaces: `!platform updates`, `!platform update <key>`,
  `!platform update-tests`, and a Recent Updates diagnostics/platform panel item;
- later read-only AI tool: bounded `bot_update_snapshot`.

Subfeatures:

- current update log and feature guide cards;
- “what should I test next?” queue;
- separately labelled runtime usage, owner/staff verification, CI smoke, and failures;
- post-update confidence score with transparent formula;
- bounded regression-watch window correlated to existing findings/errors;
- update-aware help over canonical command/feature identifiers.

Boundaries:

- no AI memory or Markdown/PR text as runtime truth;
- no duplicate command telemetry: reuse `bot1.py` lifecycle events/metrics and add only
  the release-aware projection/persistence justified by the chosen truth model;
- no raw message content;
- do not call any successful command “verified” until the maintainer defines that term;
- AI integration waits until deterministic surfaces and audience rules exist.

**Classification:** ready for an Opus planning session. A deterministic PR1 is a likely
safe candidate after decisions and migration-head verification. AI tool integration is
deferred.

### Phase 4 — Approved-docs knowledge-base search

**Goal:** provide source-grounded access to an explicitly approved corpus without an
arbitrary filesystem reader.

Required contract:

- manifest-owned corpus with public/internal classification, stable source ID/path,
  version/freshness, audience, and removal/rebuild behavior;
- bounded excerpts/results with citations and deterministic “not found/stale” fallback;
- secret-leak, audience-isolation, stale-index, and prompt-injection tests;
- no globbing, path supplied by the model, repo-wide reader, or automatic promotion of
  planning/ideas docs into user truth.

**Sequence:** it can be designed in parallel with Phase 3 after Phase 1, but Update
Awareness should remain the earlier product implementation candidate because it creates
new deterministic truth the AI needs. Knowledge search is not a substitute for update
truth.

### Phase 5 — Uploaded text/log/document reader

**Goal:** read only files explicitly attached for the current request.

- allowlisted MIME/extensions; bounded bytes/pages/lines/chars and parser time;
- transient processing and explicit deletion/retention behavior; no durable raw content;
- secret/PII detection and redaction before model context;
- admin/owner default for logs/config-like content;
- source/page/line references and parse-confidence warnings;
- no arbitrary filesystem, process logs, historical attachments, or runtime log access.

### Phase 6 — External read connectors

**Goal:** add approved, fixed-operation, read-only external access.

First create a connector/provider registry with provider key + operation key, fixed
host/target policy, credential owner, strict schemas, SSRF controls, budgets/cache,
redaction/retention, health/readiness projection, audit, and kill switch.

Recommended order:

1. fixed public status probes;
2. public GitHub repository/PR/CI metadata (not raw logs);
3. web search/research with citation and freshness contracts;
4. private GitHub only after token scope/redaction/retention decisions;
5. Google Docs/Sheets only after OAuth, allowlist, revocation, and audience decisions;
6. creator platforms later, reusing media/automation ownership.

No generic URL fetch or broad “approved API” escape hatch without an operation registry.

### Phase 7 — Vision, OCR, and media analysis

**Goal:** safely interpret explicitly attached screenshots/images/media.

- modality capability/readiness projection and provider retention review;
- allowlisted types plus byte/dimension/page/time/cost limits;
- transient bytes, secret/PII handling, and audience controls;
- OCR confidence and region/source references;
- deterministic OCR may precede AI interpretation;
- low-confidence OCR is never deterministic fact.

### Phase 8 — Reports, charts, dashboards, and owner control center

**Goal:** generate accessible reports/charts only from approved typed read models.

- no invented metrics; include source, formula, audience, and freshness metadata;
- redact/aggregate to prevent owner-only or cross-guild leakage;
- provide text alternatives and deterministic tabular fallback;
- extend Discord-native diagnostics/platform surfaces first;
- defer a web/API companion until Discord read models, authority, and audit are mature.

### Phase 9 — Notifications, recurring reports, and scheduler integration

**Goal:** allow AI to draft/explain recurring reports while deterministic automation
owns persistence and execution.

Reuse automation registry/scheduler/executor/mutation services. Require confirmation,
target allowlists, mention suppression, quiet hours, rate limits, unsubscribe/delete,
audit, retry bounds, and a kill switch. Do not create an AI scheduler or let a generated
message silently become an active recurring job.

### Phase 10 — Future action-proposal architecture

**Goal:** prepare for eventual actions only after a dedicated owner/architecture decision.

Required invariant:

`typed draft → deterministic validation and risk summary → confirmation UI bound to
actor/guild/channel/target/action/version → click-time reauthorization → service-owned
idempotent mutation → audited result → rollback/cancel`

- no direct moderation/admin execution;
- no writes through read-only AI tools;
- each low-risk maintenance action requires explicit approval and a deterministic owner;
- moderation recommendations remain advisory, reviewed, evidence-bounded, and
  privacy/fairness-gated;
- an autonomous admin agent remains rejected.

### Phase 11 — Domain-specific expansion lanes

These lanes begin only after their required foundations; they are not a serial mandate.

| Lane | Existing owner/seam to reuse | AI role | Blockers/gates | Why later |
|---|---|---|---|---|
| BTD6 strategy workspace | BTD6 strategy, grounding, source registry, capability/readiness services; ADR-006 | Grounded compare/explain/draft strategy suggestions | Provenance, provider parity, orchestration/evidence, review UX | Source-heavy claims need stronger orchestration and review |
| Setup advisor | `setup_ai_advisor` plus setup/server-management owners | Explain setup state, gaps, and next steps | Server-management readiness, audience/capability projection | Advice quality depends on deterministic setup truth |
| Server-care checklist | Server-management, readiness, health, automation reads | Explain prioritized maintenance checklist | Stable read models and owner visibility | Must not become a parallel control center/action agent |
| Moderation policy explainer | Moderation config/services and capability authority | Explain policy and advisory review packets | Privacy/fairness/evidence decisions; no punishment | High harm from false/bias-prone claims |
| Audit/event timeline reader | Existing domain audit/event owners | Bounded read/summarize/correlate | Unified read projection, retention/audience policy | Never duplicate audit writes or expose raw logs |
| Capability explanation | Capability/governance resolvers and command metadata | Explain allow/deny and available paths | Phase 2 metadata/index | Must project canonical authority, not simulate it |
| Media/video reference library | Media/YouTube owner, ADR-007 | Search/explain approved references | Approved corpus/connector/media policies | Prevent duplicate media ownership and stale claims |
| User profile/preference read model | Existing domain-owned user/config reads | Personalize explanations | Consent, retention, deletion/export, cross-domain ownership | Privacy-sensitive; no AI-owned profile truth |
| Privacy-bounded server insights | Typed guild read models | Explain trends/health without raw content | Aggregation, consent, retention, audience decisions | Cross-user/server inference risk |

## 7. Capability matrix

The matrix deliberately merges duplicate ideas. “Minimum scope” is a planning default,
not approval.

| Capability | User value | Current state / existing source | Owner | Foundation | Class / minimum scope | Main risk / cost | State/cache | Audit/tests/kill switch | Phase | Decision before implementation |
|---|---|---|---|---|---|---|---|---|---|---|
| Tool descriptor/catalogue | Consistent safe tool metadata | `AIToolSpec` + `ToolRegistry`; planned descriptor absent | AI runtime/services | Compatibility contract | Read-only / system | Behavior drift/provider mismatch | None initially | Catalogue invariants, parity, registry fallback | 1 | Descriptor boundary and compatibility shape |
| Named toolsets/resolver | Offer only relevant tools | No reusable toolsets | AI orchestration owner TBD | Catalogue | Read-only / system | Wrong omission/authority broadening | Config later | Resolver trace, scope-narrowing tests, disable switch | 1 | Policy owner and precedence |
| Budgets/evidence envelopes | Lower cost, better grounded answers | Hop limits/BTD6 guard exist; shared contract absent | AI runtime + fact owners | Catalogue/toolsets | Read-only / system | Cost, truncation, false confidence | Metrics only | Budget/evidence evals, deterministic fallback | 1 | Budget defaults and audit retention |
| Bot capability/help discovery | Explain commands available here | Knowledge blocks, command descriptions/ledger, Help route exist | Command/help/runtime owners | Metadata index | Read-only / user | Leaking hidden/admin commands | Cache optional | Audience/capability tests; fall back to Help | 2 | Audience and maturity vocabulary |
| Capability/denial explanation | Explain why command/AI is unavailable | Policy/readiness/capability resolvers exist | Existing resolver owners | Phase 2 index | Read-only / affected user; admin detail gated | Authority confusion | None | Resolver-consistency tests; suppress detail | 2 | Detail visible per audience |
| Update log + guide cards | Understand recent changes | No canonical update model | New platform update-awareness owner | Stable IDs/owner decisions | Read-only / public-safe subset; owner detail | Stale/manual data | Migration likely | CRUD/read-model tests; hide/disable surfaces | 3 | Ingestion model, audience, required guides |
| Tested-since-update coverage | Know what remains unverified | Command telemetry exists; release-keyed truth absent | Update awareness reusing `bot1.py` events | Update manifest | Read-only / owner initially | Mislabeling usage as test; privacy | Migration likely | Correlation/formula tests; disable scoring | 3 | Meaning of tested, global vs guild |
| Regression watch/confidence | Focus post-release checks | Health findings exist; no release correlation | Update awareness + health owners | Update model | Advisory / owner | Invented score/false reassurance | Query/cache likely | Transparent formula, window tests, no-score fallback | 3 | Formula/window and visibility |
| AI update explanation | Ask what changed/test next | Does not exist | AI read tool over update service | Deterministic Phase 3 surfaces + Phase 1 | Read-only / audience-filtered | Leakage/stale truth | None beyond update model | Tool/evidence/audience evals; remove tool | After 3 | Snapshot contract and audiences |
| Approved-docs search | Ground answers in approved docs | Ideas/plan only | Corpus/search owner TBD | Phase 1 + manifest | Read-only / corpus audience | Secrets, prompt injection, stale docs | Index/cache likely | Leak/injection/freshness tests; disable corpus/tool | 4 | Public/internal corpus policy |
| Uploaded text/log reader | Summarize supplied files | Ideas only | Attachment-processing owner TBD | Phase 1 + content policy | Read-only / text user; logs admin | Secrets/PII/provider cost | Transient only | Parser/redaction/size tests; feature flag | 5 | Allowed types, retention, secret behavior |
| Fixed status probes | Explain service availability | Existing internal readiness; external connector absent | Connector registry + diagnostics projection | Connector foundation | Read-only / admin/owner | SSRF/staleness/outage | Bounded cache | Host/schema/degraded tests; connector kill switch | 6 | Approved targets and credential owner |
| Public GitHub/CI metadata | Explain PR/check status | Manual GitHub use only; no runtime connector | Connector owner | Registry | Read-only / owner/admin | Rate/cost, misleading checks | Cache | API fixtures/redaction/degraded tests; revoke op | 6 | Public-only scope and visible fields |
| Private GitHub metadata | Internal repo awareness | Absent | Connector owner | Registry + secret policy | Read-only / owner | Token/secrets/private code | Cache + credential ref | Scope/redaction/revocation tests | Later 6 | Token scope, retention, allowed repos |
| Raw CI log reader | Debug failures | Absent | — | — | Rejected now | Secret/raw-log exposure | — | — | Deferred | Dedicated sanitized-log contract decision |
| Web research/search | Fresh cited answers | Absent | Connector/search owner | Registry + citation contract | Read-only / policy-gated | Injection, SSRF, cost, misinformation | Cache | Citation/freshness/domain tests; kill switch | 6 | Providers/domains/audiences/budgets |
| Google Docs/Sheets read | Approved workspace knowledge | Absent | Connector owner | OAuth/allowlist/revocation | Read-only / owner/admin | Broad OAuth/private data | Cache/index maybe | Allowlist/revocation/redaction tests | Later 6 | OAuth owner and document allowlist |
| Generic URL/API fetch | Flexibility | Absent | — | Fixed-operation registry | Rejected as generic | SSRF/credential/data exfiltration | — | — | Deferred | Only revisit as allowlisted operation catalogue |
| Vision/OCR | Explain attached screenshots | Absent | Attachment/modality owner | Phase 1 + provider policy | Read-only / uploader; admin for sensitive | PII/secrets/cost/low confidence | Transient | Type/size/confidence/redaction evals; flag | 7 | Providers, retention, confidence UX |
| Charts/reports | Understand typed data | Deterministic embeds exist; AI charting absent | Read-model owners + renderer | Mature typed reads | Read-only/advisory / audience-filtered | Invented metrics/leakage | Render cache optional | Formula/a11y/audience tests; text fallback | 8 | Approved datasets and chart types |
| Website/API companion | Owner access beyond Discord | Idea only; Discord-first answered | Existing service owners + future API owner | Mature Discord reads/authority/audit | Read-only first / owner | Duplicate state/auth attack surface | API cache/session TBD | Auth/tenant/audit tests; disable companion | Later 8 | Dedicated architecture/security decision |
| Draft recurring report | Save operator time | Automation owner exists; AI draft absent | Automation services | Reports + proposal flow | Advisory/action-gated / admin | Spam/wrong target | Existing automation state | Preview/target/rate/audit tests; cancel | 9 | Allowed templates/targets |
| Notification delivery proposal | Send approved summary | Existing deterministic automation/delivery seams | Automation owner | Confirmation architecture | Action-gated / admin | Spam/mentions/privacy | Existing state | Reauth/idempotency/retry tests; revoke job | 9/10 | First approved delivery category |
| Safe maintenance action proposal | Guided low-risk operations | Absent; eventual actions allowed in owner intent | Per-action deterministic service owner | Phase 10 architecture | Action-gated / owner | Outage/partial state | Per action | Risk/reauth/rollback/audit tests; per-action kill | 10 | Explicit action allowlist and rollback |
| Moderation recommendation | Help human review | Policy/config sources exist; AI recommendation absent | Moderation owner | Evidence/advisory contracts | Advisory / authorized moderators | Bias/privacy/false accusation | Minimal/no raw durable content | Fairness/evidence/reviewer/audit tests; disable | Later 10/11 | Privacy/fairness/review policy |
| Direct moderation/admin action | Automation | Absent | — | — | Rejected | Irreversible harm/authority error | — | — | Rejected | Dedicated future decision cannot bypass review |
| BTD6 complex orchestration | Better multi-step source-backed answers | Many tools/grounding exist; workflow contracts planned | BTD6 + shared orchestration | Phase 1, provenance/readiness | Read-only/advisory / user | Unsupported claims/cost | Existing fact/cache owners | Trace/grounding/provider/eval suite; fallback | 11 | Provenance gates and workflow scope |
| BTD6 strategy workspace | Plan/review strategies | Strategy service/review seams exist | BTD6 strategy owner | Phase 1 + BTD6 gates | Advisory / user or guild policy | Bad strategy/source drift | Existing strategy records | Grounding/review/version tests; disable AI lane | 11 | AI draft/review/product scope |
| Setup/server-care advisor | Explain configuration/next steps | Setup advisor + readiness/health exist | Setup/server-management owners | Phase 2 + stable readiness | Advisory / admin | Wrong authority/action implication | Existing reads | Consistency/audience tests; deterministic fallback | 11 | Advice audience/detail |
| Audit/event timeline reader | Explain incidents/changes | Multiple domain audits/events exist | Domain owners + read projection | Typed bounded timeline | Read-only / owner/admin | Leakage/retention/correlation errors | Query/cache maybe | Audience/retention/evidence tests; disable projection | 11 | Included event families/retention |
| User preference read model | More relevant explanations | Domain-specific state exists; no unified profile | Domain owners + privacy projection | Consent/privacy decisions | Read-only / self | Profiling/cross-domain leakage | Projection/cache maybe | Consent/delete/export/isolation tests | 11 | Allowed fields and retention |
| Server insights | Explain trends | Idea only | Domain read owners | Privacy-bounded aggregation | Advisory / admin | Surveillance/cross-guild inference | Aggregates | Privacy thresholds/audience tests; disable | 11 | Consent/aggregation/retention |

## 8. Dependency graph and sequencing rationale

```text
Phase 0 verified truth
  └─> Phase 1 shared orchestration contracts
       ├─> Phase 2 command/help metadata ─> Phase 3 update awareness ─> AI update tool
       ├─> Phase 4 approved corpus search ─> Phase 5 attachment reader
       ├─> Phase 6 connector registry ─> GitHub/web/private connectors
       └─> Phase 7 modalities

Typed deterministic read models from phases 2–7
  └─> Phase 8 reports/control-center reuse
       └─> Phase 9 drafted recurring reports
            └─> Phase 10 separately approved proposal/confirmation actions

Phase 1 + provenance/readiness + domain decisions ─> Phase 11 domain lanes
```

- **Orchestration before tools:** without a catalogue, toolsets, budgets, evidence, and
  safe trace, each new tool would create its own policy/cost/audit behavior.
- **Deterministic update awareness before AI explanation:** AI cannot reliably explain
  releases or testing from conversation memory, Markdown, or raw command logs.
- **Corpus manifest instead of filesystem access:** explicit classification/freshness is
  the only way to bound secrets, audience, prompt injection, and stale planning text.
- **Connector registry before GitHub/web/Google:** fixed operations and credential/host
  policy prevent a generic fetcher from becoming SSRF/data-exfiltration authority.
- **Separate actions architecture:** model tool calls are not human confirmation and
  cannot safely own reauthorization, idempotency, rollback, or service mutations.
- **BTD6 remains gated:** source-heavy and derived claims need provenance, provider
  parity, grounding, and evidence completeness before broader workflows.
- **Website waits:** Discord-native reads and authority must mature before exposing a
  second authentication/control surface.
- **Server-management readiness matters:** an owner advisor is only as trustworthy as
  setup/config/capability/readiness projections; advice cannot compensate for missing
  deterministic truth.

## 9. Recommended next Claude Opus sessions

### Session 1 — Revise and lock the orchestration foundation

- **Goal:** reconcile the detailed BTD6 orchestration plan with current source and lock
  the smallest compatibility-first PR sequence.
- **Must read:** AI folio, AI ownership/integration docs, orchestration plan,
  `services.ai_tools`, contracts, natural-language stage, all provider adapters, guard
  map, relevant tests.
- **Expected output:** approved-or-questioned descriptor/toolset/budget/evidence design
  and 2–3 independently revertible PR specs.
- **Resolve first:** catalogue ownership, policy precedence, trace/audit retention,
  provider-neutral tool choice.
- **Stop if:** current source changed, scope can broaden, provider parity cannot be
  preserved, or behavior-neutral compatibility cannot be demonstrated.
- **Do not implement yet:** external tools, actions, admin UX, or broad BTD6 workflow.

### Session 2 — Plan deterministic Update Awareness PR1

- **Goal:** define canonical manifest/read model, stable identifiers, audience, and first
  deterministic platform surface.
- **Must read:** this roadmap, question batch, command lifecycle hooks, command metadata,
  health contracts/findings, diagnostics/platform UI, migrations, ownership/runtime docs.
- **Expected output:** schema/service/surface contract and migration/rollback/test plan.
- **Resolve first:** ingestion model, “tested” categories, global/guild dimensions,
  audiences, guide-card requirement.
- **Stop if:** it duplicates telemetry/health, depends on Markdown runtime parsing, or
  migration head/owner is unclear.
- **Do not implement yet:** AI update tool, confidence score without formula, PR import.

### Session 3 — Plan command/help/discovery metadata upgrade

- **Goal:** define the minimum shared feature index that improves Help and bot knowledge.
- **Must read:** Help cog/route, bot knowledge, command descriptions, surface ledger,
  capability/governance docs and tests.
- **Expected output:** metadata vocabulary, stable IDs, audience projection, compatibility
  and adoption plan.
- **Resolve first:** maturity vocabulary, panel/feature representation, detail audiences.
- **Stop if:** it creates a second Help router/route tree or encodes authority separately.
- **Do not implement yet:** update linkage beyond agreed extension hooks.

### Session 4 — Plan approved-docs knowledge search

- **Goal:** define corpus manifest, classification, indexing/search, citation, and safety.
- **Must read:** AI orchestration/ownership docs, ideas backlog sections, docs authority
  model, secret/redaction/prompt-injection tests.
- **Expected output:** bounded read-only plan with corpus and threat model.
- **Resolve first:** public/internal corpus, planning-doc exclusion, freshness/rebuild.
- **Stop if:** model-selected paths, arbitrary file access, or audience isolation is
  required but unresolved.
- **Do not implement yet:** attachments, web search, private connectors.

### Session 5 — Plan read-only AI update snapshot (only after Phase 3 surfaces ship)

- **Goal:** expose one audience-filtered, bounded update snapshot through Phase 1.
- **Must read:** shipped update service/surfaces/tests, AI tool registry/orchestration,
  audit/redaction/evidence contracts.
- **Expected output:** tool/result/eval plan and deterministic fallback.
- **Stop if:** deterministic update truth is incomplete or audience rules are unresolved.
- **Do not implement yet:** AI-authored manifests, action suggestions, automatic imports.

## 10. Safest first implementation candidates (not approved here)

### Candidate A — AI tool descriptor/catalogue compatibility PR

- **Scope:** add pure catalogue metadata/adapter over current `AIToolSpec`; preserve
  registry output and provider behavior exactly.
- **Likely files:** `core/runtime/ai/contracts.py`, `services/ai_tools.py`, focused AI
  tests, orchestration/status docs.
- **Tests:** catalogue completeness/uniqueness, schema validity, exact current registry
  compatibility, scope filtering, provider request parity.
- **Migration:** none. **Rollback:** remove compatibility layer.
- **Why safe:** read-only and behavior-neutral foundation.
- **Stop:** any tool becomes newly reachable, schemas change silently, or provider output
  differs without an approved design.

### Candidate B — Command/help/discovery metadata compatibility upgrade

- **Scope:** add stable feature/command metadata and one shared projection consumed first
  by existing Help/bot knowledge, without route or authority changes.
- **Likely files:** `command_descriptions.py`, `command_surface_ledger.py`,
  `bot_knowledge_service.py`, Help tests/docs.
- **Tests:** catalogue completeness, hidden/help behavior, audience projection,
  per-command failure isolation, current output compatibility.
- **Migration:** none. **Rollback:** retain old metadata path/fallback.
- **Why safe:** extends deterministic existing owners and unlocks later update linking.
- **Stop:** requires duplicate route tree or unresolved maturity/audience policy.

### Candidate C — Deterministic Update Awareness manifest + owner-only platform read surface

- **Scope:** after Session 2 decisions, create manual structured update registration and
  bounded owner read surface; keep AI and automatic PR import out.
- **Likely files:** new service/DB owner, migration 059-or-later, diagnostic/platform cog
  and view/embed extension, focused tests/docs.
- **Tests:** migration structure/integration, CRUD/read projection, audience, stable IDs,
  retention/rollback, platform embed; no raw content.
- **Migration:** likely additive. **Rollback:** hide surface/revert consumer; additive
  tables can remain or be dropped only by explicit rollback plan.
- **Why safe:** deterministic, owner-first, and directly serves maintainer intent.
- **Stop:** owner questions remain unanswered, schema duplicates telemetry/health, or
  migration head changes.

Knowledge-base search is valuable but is not among the first three until the Phase 1
foundation and corpus audience decision are resolved.

## 11. Rejected and deferred ideas

| Idea | Status / reason | Safe alternative | Needed to revisit |
|---|---|---|---|
| AI memory as durable truth | Rejected; conversation context is not authoritative/auditable product state | Service-owned typed read models | New binding decision, ownership/retention/correction design |
| AI writes/actions through `services.ai_tools` | Rejected; violates explicit read-only contract | Separate Phase 10 proposal/confirmation path | Dedicated architecture decision + per-action approval |
| Arbitrary filesystem/log/SQL/shell access | Rejected; secrets, exfiltration, destructive authority | Approved corpus, explicit attachments, typed service reads | No generic revisit; only bounded named operations |
| Unrestricted URL/API fetch | Rejected; SSRF/data exfiltration | Fixed connector operation registry | Connector security decision and allowlisted operation |
| Broad connector without registry | Deferred/rejected as architecture | Phase 6 registry first | Registry, credential, host, audit, kill-switch contracts |
| Raw CI log reader | Deferred; logs commonly contain secrets/unbounded content | Public CI metadata; later sanitized bounded artifact | Sanitization/retention/audience decision |
| Direct destructive moderation/admin actions | Rejected | Advisory packets and later per-action confirmed proposal | Dedicated action/fairness/privacy decision |
| Autonomous admin agent | Rejected | Deterministic owner surfaces + human-confirmed actions | Fundamental owner/architecture decision |
| Duplicate health dashboard | Rejected; shipped health owners exist | Extend health snapshots/findings/platform views | Only if existing owner is formally replaced |
| Duplicate command telemetry system | Rejected | Reuse lifecycle hooks; add release-aware projection | Update-awareness truth-model decision |
| Duplicate governance/capability simulator | Rejected | Explain canonical resolvers | Extend resolver-owned projection only |
| Website-first control surface | Deferred; Discord-first owner intent is routed | Mature Discord read models, then companion | Dedicated API/auth/security decision |
| Resume BTD6 extraction before provenance gates | Rejected by current gates/ADR direction | Existing approved sources/grounding/readiness | Satisfy provenance/provider/source-health gates |
| Redis/external state store | Rejected by ADR-001 for current platform direction | PostgreSQL/process-local owners as documented | New ADR proving concrete need and lifecycle design |
| AI-owned scheduler/notification subsystem | Rejected duplicate/unsafe owner | Existing automation services + proposals | Phase 9/10 decisions |
| Markdown/PR metadata as automatic runtime truth | Rejected | Manual/validated structured update manifest; optional later import review | Import validation/ownership decision |

## 12. Maintainer decisions required

A full question batch is added to `docs/owner/maintainer-question-router.md` as
**AI roadmap batch AR-2026-06-07**. The highest-impact decisions are:

1. first post-orchestration planning target: Update Awareness or command/help metadata;
2. update registration/import model;
3. separate meanings of runtime-used, manually verified, CI-smoked, and failed;
4. global/guild dimensions and audiences for update/test status;
5. guide-card requirement;
6. approved-docs corpus audience;
7. capability availability by user/admin/platform-owner;
8. whether/which first low-risk action draft is ever considered;
9. preferred first Opus target.

Safe defaults do not authorize implementation. Until answered: keep update state
manual, owner-only, deterministic, and separate verification categories; keep the docs
corpus user-safe only; keep AI read-only/advisory.

## 13. Documentation routing plan

- Keep `docs/subsystems/ai.md` as the AI folio and add a link to this roadmap only when
  a follow-up doc-routing session confirms it belongs there.
- Keep the detailed orchestration plan as the design authority for Phase 1; revise its
  status/source claims rather than duplicating its contracts here.
- Keep bot-awareness plans as completed delivery/reference history; do not reopen them.
- Keep AI extra-tool and future-product-direction docs as ideas. This roadmap may cite
  them without promoting every idea.
- Keep the AI tool capability roadmap as focused capability triage/rationale. If later
  superseded, mark and link rather than copy/delete its safety analysis.
- Do not add this roadmap to `docs/current-state.md` unless the maintainer/Opus promotes
  a specific phase into an active candidate.
- Route answered owner questions to the one appropriate folio/plan/decision; preserve
  original answers in the question router.
- Avoid copying source inventories into multiple docs; use links/symbol names and update
  only the owning status document after implementation.

## 14. Verification record

### Live GitHub verified

- Public API repository state: default `main`.
- Public API open PR list: empty on 2026-06-07.
- Recent merged PRs reviewed through #564; relevant merges include #563/#562/#561/#560,
  server-management #555/#556/#558, health findings #548, and bot-awareness completion
  #542.

### Required docs read/reconciled

- Working/status: `.claude/CLAUDE.md`, `docs/collaboration-model.md`,
  `docs/current-state.md`, `.session-journal.md`, `docs/AGENT_ORIENTATION.md`,
  `docs/owner/ai-project-workflow.md`, and the maintainer question router.
- Binding/routing: architecture, ownership, runtime contracts, helper policy,
  repo-navigation map, decisions index, ADR-001, ADR-006, ADR-007, capability authority.
- AI/diagnostics: AI folio, health folio, AI ownership/integration/readiness/tool roadmap,
  orchestration plan, bot-awareness plans, guard map, and BTD6 groundedness finding at
  its actual `docs/btd6/` path.
- Ideas/planning: ideas README, future product direction, AI extra-tool backlog, Ideas
  Lab, server-management planning/status, BTD6 and media/provenance docs as relevant.

### Source verified

- AI contracts, natural-language stage, providers, tools/registry, policy/config,
  readiness/diagnostics/audit, bot knowledge, command descriptions/ledger, Help route,
  AI cog, diagnostics cog/embeds/views, health contracts/snapshot/findings/DB,
  `bot1.py` lifecycle hooks, BTD6 grounding/source/strategy/readiness seams,
  setup advisor, automation services, migrations, and matching tests.

### Stale/superseded findings

- Requested `docs/btd6-derived-value-groundedness-finding.md` does not exist; actual file
  is `docs/btd6/btd6-derived-value-groundedness-finding.md`.
- Migration 057 is the shipped operational-health-findings migration, but latest is 058.
- Older pending bot-awareness statements are superseded by the completed implementation
  ledger and source.
- `docs/architecture.md` diagram migration count is hand-maintained/stale; migration files
  are authoritative.

### Left unverified / checks not performed

- Production live behavior, credentials, provider account features/costs/retention,
  Discord permissions/intents, and live AI diagnostics tool exercise.
- Authenticated GitHub checks/private metadata because `gh` is unavailable and only the
  public API was used.
- No runtime test suite was needed during source mapping; docs checks are recorded in the
  PR/final handoff after document edits.

## 15. Stop conditions for every follow-up session

Stop and report rather than plan confidently when:

- an open PR touches the target AI/diagnostics/docs/update/server-management owner;
- source contradicts the roadmap or completed bot-awareness ledger;
- migration head/ownership is unclear;
- current docs are too stale to identify the authoritative owner;
- orchestration source has substantially changed;
- scope/policy may broaden authority;
- an owner/security/privacy question blocks an honest sequence;
- a proposal duplicates health, Help, governance, telemetry, update, automation, or audit
  ownership; or
- deterministic fallback, audit, redaction, budget, test, and rollback designs are absent.

## Handoff

- **From → To:** Codex mapping/planning → Claude Opus planning
- **Roadmap doc:** `docs/planning/ai-roadmap-2026-06-07.md`
- **Question batch:** `docs/owner/maintainer-question-router.md` — AR-2026-06-07
- **Decided:** grounded explanation/read orchestration first; deterministic owners;
  read-only AI tools; Discord-first; no duplicate systems; actions require a separate
  proposal/confirmation architecture.
- **Open:** first post-orchestration target, update truth/test semantics/audiences,
  guide-card policy, docs corpus, role capability matrix, and eventual first action draft.
- **Recommended first Opus session:** revise and lock the shared AI orchestration
  foundation and its first 2–3 compatibility-first PRs.
- **Must-read source files:** `services/ai_tools.py`, natural-language stage/contracts,
  provider adapters, bot knowledge/command descriptions/ledger, Help route, health
  snapshot/findings, `bot1.py`, BTD6 grounding/source/readiness, automation services.
- **Must-not-do boundaries:** no runtime implementation from this roadmap; no AI writes,
  arbitrary access, duplicate owners, Markdown truth, ungated BTD6 extraction, or
  website-first/action-agent work.
- **Verification gaps:** production/live-provider behavior, authenticated GitHub/private
  state, remaining PR5 AI-path live test, and owner answers in the new batch.
