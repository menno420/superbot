# AI Tool Capability Roadmap

> **Status:** `plan` — roadmap proposal (2026-06-06); not implementation approval.
> **Purpose:** refine the open AI extra-tool ideas backlog into a source-verified,
> implementation-ready sequence without replacing the approved bot-awareness plan or the
> research-backed BTD6 orchestration planning document.
> **Current gate (updated 2026-06-09):** bot-awareness PR4–PR6 shipped (#541) and the
> `PLATFORM_OWNER` reachability decision (D1) is **resolved** — `_derive_scope()` now
> returns `AIScope.PLATFORM_OWNER` for the bot owner. The orchestration-foundation gate
> below is now **largely satisfied**: the `ai-complex-request-tool-orchestration-plan.md`
> foundation **Phases 1–3 shipped 2026-06-09** — the canonical tool catalogue + deterministic
> selector (#612), provider-neutral tool-choice + budgets (#618), and the typed
> orchestration-policy storage + resolver + the **Tools & Workflows** operator UI (#619).
> So the "land the foundation before net-new capability handlers" precondition (§1 item 3,
> item 5) is met for Phases 1–3; the remaining sequencing gates for any *net-new* tool are
> Phase 4 (the complex-BTD6 workflow) **and** the per-tool AI-exposure decision (each net-new
> tool still needs the expansion gate lifted, as `btd6_round_cash` and the Tools UI were). (The
> pre-#541 verification snapshot in §2.1 is historical.)
>
> **Authority:** this document governs prioritization and integration boundaries for
> net-new AI tool capability families only. It is subordinate to the binding architecture
> docs and does not authorize runtime changes, migrations, connectors, or action tools.

---

## 1. Executive recommendation

1. Bot-awareness PR4–PR6 are **complete (shipped in #541)** — D1 (platform-owner scope)
   is resolved and the retention/history decision (D8/D11) is approved (30-day TTL). A new
   tool-capability programme may now build on the delivered health stack.
2. Treat `docs/health/bot-awareness-implementation-plan.md` as the sole execution authority for
   health diagnostics. Future diagnostics AI tools must consume `HealthSnapshot` and
   `OperationalHealthFinding`; never create a second bot-awareness service.
3. Treat `docs/ai/ai-complex-request-tool-orchestration-plan.md` as the reusable design
   direction for the orchestration foundation. Source labels it a research-backed planning
   document, not approved execution authority; obtain maintainer approval before executing
   it. Its catalogue, toolsets, neutral tool choice, budgets, evidence, and safe trace work
   should land before net-new capability handlers.
4. Keep the PR #539 ideas document as a non-authoritative backlog. Do not convert every
   idea into a project and do not use it to bypass product/security decisions.
5. The first post-bot-awareness work should be the already-planned orchestration
   foundation, not web search, vision, connectors, or actions.
6. Build one canonical descriptor catalogue around the current `AIToolSpec` registry;
   do not create parallel metadata, registries, or capability-specific tool loops.
7. Preserve compatibility: policy may narrow the current scope-allowed tool set, but it
   must never widen authority or make disabled tools callable.
8. Generalize BTD6 evidence/faithfulness concepts only where a typed neutral result
   contract is useful; do not weaken or replace BTD6-specific grounding guards.
9. Make repository/public-document knowledge search the first net-new capability after
   the foundation. It is high-value, deterministic, bounded, and can ship without an
   external connector or mutation path.
10. Follow with a safe uploaded-text reader, but only for explicitly attached, size- and
    type-bounded content. No filesystem paths, arbitrary log access, or durable raw
    uploads.
11. Add external reads only through an approved connector-provider registry keyed by
    provider and operation. Web search, GitHub/CI, status probes, creator platforms, and
    Google readers must never accept arbitrary endpoints or credentials from the model.
12. Separate read-only tools, recommendation tools, and execution tools in contracts,
    toolsets, UI, audits, and rollout phases. Action tools must never be registered in
    the current read-only `services.ai_tools` path.
13. Merge scheduler and notification ideas into the existing automation ownership path;
    AI may draft or propose, but `automation_mutation`, `automation_scheduler`, and
    `automation_executor` remain the deterministic owners.
14. Merge safe Discord/server actions into existing lifecycle/mutation services. Never
    let the model directly perform role, channel, moderation, settings, or provisioning
    mutations.
15. Defer moderation recommendations until reliable service-owned evidence packets,
    fairness review, redaction, reviewer audit, and appeal/manual-review semantics exist.
16. Defer vision/OCR until attachment authorization, modality capability projection,
    byte limits, transient processing, redaction, provider retention review, and cost
    budgets are implemented.
17. Reject unrestricted URL fetch, raw SQL, arbitrary filesystem access, unbounded logs,
    shell/Python execution, direct destructive Discord actions, and uncontrolled mentions.
18. Require every kept capability to name its deterministic owner, descriptor/toolset,
    strict input and bounded output contract, evidence/provenance shape, scope, budget,
    retention class, safe failure, tests, and rollback switch before implementation.
19. Add durable per-guild/category/channel configuration only after built-in policies are
    stable. Reuse AI policy resolution/mutation ownership and additive/idempotent
    migrations; do not create connector-specific policy tables casually.
20. Hand the conditional first three PRs in section 7 to Claude only after Phase 0 gates
    are green. Stop if source has changed or if the owner-scope decision remains open.

---

## 2. Current repo state verification

### 2.1 Verification method and snapshot (historical — pre-#541)

> **Historical snapshot.** Captured before #541 merged; PR4–PR6 have since shipped and
> D1 is resolved (see §1). Kept to show the verification *method*, not current state.

Verified on **2026-06-06** against local `main` equivalent commit `60f1cd2` and the
GitHub API for `menno420/superbot`:

- Local branch `work` points at merge commit `60f1cd2`, the same SHA reported for remote
  `main` by `GET /repos/menno420/superbot/branches/main`.
- GitHub reported one open pull request: **#539**, branch
  `chatgpt/ai-extra-tool-capability-ideas`, one commit ahead of `main`, adding only
  `docs/ai-extra-tool-capability-ideas.md` (now relocated to `docs/ideas/`).
- GitHub reported no open PR corresponding to bot-awareness PR4, PR5, or PR6. Branch
  names are not proof of active work, so Phase 0 must query open PRs and compare source
  again before implementation.
- The PR #539 file was read from its exact head SHA because it is not merged into this
  worktree.

### 2.2 Shipped facts

- Bot-awareness PR1–PR3 are shipped in #537. The source contains typed
  `HealthAudience`, `OperationalHealthFinding`, `HealthSnapshot`, the two-lane health
  snapshot service, audience projection, deterministic platform embeds/panel routes,
  and startup snapshot integration.
- `HealthAudience` is deliberately independent of AI scope. Deterministic health
  surfaces resolve owner/admin audiences through `health_snapshot_service.resolve_audience()`.
- The health service owns collection and redaction. `collect_cached_snapshot()` and
  `collect_snapshot()` return audience-projected snapshots; diagnostics consumers must
  reuse them.
- The current AI tool path is read-only. `services.ai_tools.build_registry()` constructs
  one request registry of matching `AIToolSpec` plus handlers, filtered by `min_scope`.
- `AIToolSpec` is currently small: name, description, JSON Schema parameters, and
  minimum scope. `AIToolDescriptor`, `AIOrchestrationPolicy`, `AIToolBudget`,
  `AIToolChoice`, and `ToolRequirementMode` are planned names, not shipped source types.
- The natural-language stage is the only located caller of `ai_tools.build_registry()`.
  It offers all scope-allowed tools when tools are enabled; no named toolset/policy
  resolver is shipped yet.
- OpenAI and Anthropic have separate bounded tool loops, but the neutral request does
  not yet express provider-neutral tool choice or request budgets beyond output tokens
  and timeout.
- BTD6 grounding already has a dedicated allowlist/ledger seam. Only
  `BTD6_GROUNDING_TOOL_NAMES` results enter that faithfulness ledger.
- Existing AI policy already has guild/channel/category/role precedence, a mutation
  chokepoint, config projection, readiness, diagnostics, and decision auditing. New
  policy must extend that ownership rather than bypass it.
- Existing automation already owns scheduled deterministic execution through
  `automation_mutation`, `automation_scheduler`, `automation_executor`, its DB module,
  migrations, and diagnostics panel.

### 2.3 In-progress or uncertain

- Bot-awareness PR4–PR6 are **shipped (#541)** — no longer in-progress: PR4 added the
  opt-in grouped recent-error subsystem, PR5 the owner-gated `diagnostics_health_snapshot`
  tool, PR6 the persistent findings store (migration `057`, sole-writer service, 30-day
  retention).
- D1 is **resolved**: `_derive_scope()` now returns `AIScope.PLATFORM_OWNER` for the
  verified bot owner, so owner-gated diagnostics tools are reachable.
- The BTD6 orchestration document defines the desired reusable architecture, but its
  proposed descriptor/policy/budget types have not landed in source.

### 2.4 Stale, superseded, or context-only documents

| Document | Current role |
|---|---|
| `docs/architecture.md`, `docs/ownership.md`, `docs/runtime_contracts.md`, `docs/helper-policy.md` | Binding contracts. Source wins on disagreement. |
| `docs/AGENT_ORIENTATION.md` | Binding orientation/reference routing; not implementation approval. |
| `docs/health/bot-awareness-implementation-plan.md` | Approved execution authority for bot-awareness/health PR4–PR6. |
| `docs/health/bot-awareness-diagnostics-plan.md` | Repository map/context only; explicitly defers execution authority to the implementation plan. |
| `docs/ai/ai-complex-request-tool-orchestration-plan.md` | Research-backed planning/design direction for reusable orchestration and BTD6 complex requests; source does not label it approved execution authority. |
| PR #539 `docs/ideas/ai-extra-tool-capability-ideas.md` | Ideas backlog only; useful inventory, not approval or execution authority. |
| This roadmap | Prioritization/integration proposal for net-new capability families; not runtime approval. |
| `.session-journal.md` | Cross-session state and cautions; source and binding docs outrank it. |

### 2.5 Source/doc mismatches and stop conditions

1. **Platform-owner reachability — RESOLVED (#541).** `_derive_scope()` now returns
   `AIScope.PLATFORM_OWNER` for the bot owner, so owner-only AI tools are no longer
   blocked on D1. (Pre-#541 this was the blocker: `_derive_scope()` never returned it.)
2. **Planned orchestration names are not shipped abstractions.** Backlog language can
   sound present-tense, but source has only `AIToolSpec`, `ToolRegistry`, and the current
   provider loops. Implementations must first land or reconcile the BTD6 plan's types.
3. **Scheduler/notification are not net-new subsystems.** The backlog ideas must merge
   into existing automation ownership, not create AI-owned scheduling.
4. **“Public/trusted” is not a current `AIScope` vocabulary.** Scope and channel policy
   are separate concerns; roadmap/toolset language must not invent an unimplemented
   privilege tier.
5. **Generic connectors are unsafe without a deeper architecture decision.** An approved
   provider/operation registry, credential ownership, SSRF controls, schemas, redaction,
   budgets, and audits are prerequisites.

These findings trigger the requested stop rule for implementation planning: section 7
contains only conditional, independently reviewable PR recommendations. It does not
approve PR4–PR6 changes, migrations, connectors, or action tools.

---

## 3. Relationship to existing plans

### Document-control map

| Work type | Controlling document/status | How this roadmap relates |
|---|---|---|
| Health snapshots, structured observations, AI diagnostics explanation, persistent findings | `docs/health/bot-awareness-implementation-plan.md` | Waits for and consumes that work; never duplicates it. |
| Bot-awareness repository/source context | `docs/health/bot-awareness-diagnostics-plan.md` | Use as a map only; correct against source and the implementation plan. |
| Canonical tool catalogue, named toolsets, neutral tool choice, requirements, budgets, evidence, traces, BTD6 complex workflows | `docs/ai/ai-complex-request-tool-orchestration-plan.md` — research-backed planning direction pending explicit implementation approval | Reuses its names and recommends approving/executing its foundation before net-new tools. |
| Candidate capability inventory | PR #539 `docs/ideas/ai-extra-tool-capability-ideas.md` | Keep as backlog with a status/cross-link; this roadmap triages and sequences it. |
| Cross-session operational state | `.session-journal.md` | Record decisions and verified PR status; do not promote journal assumptions over source. |
| Reading order and document classes | `docs/AGENT_ORIENTATION.md` | Add this roadmap only as a non-binding planning reference after approval. |

### Integration rules

- Diagnostics belongs to the bot-awareness plan's `HealthSnapshot` pipeline and future
  `diagnostics` toolset.
- Orchestration contracts belong to the BTD6 orchestration plan even when first used by
  non-BTD6 capabilities. One foundation must serve both programmes.
- Existing BTD6 result capture remains domain-specific. A neutral evidence envelope may
  reference it, but cannot make arbitrary tool output qualify as BTD6 evidence.
- Existing server context tools remain under the current AI tools service until the
  canonical catalogue migrates them. Do not add an isolated cog registry.
- Existing automation/lifecycle/moderation/settings services remain mutation owners.
  AI can interpret, draft, or propose typed operations only.

---

## 4. Capability triage matrix

“Scope” below means the minimum likely AI/Discord authority plus an independent
per-guild/category/channel enablement policy. Exact scope is a product decision.

| Capability | Decision | Recommended toolset | Likely scope | Mode | Required foundation | Main risks | Phase | Verify before implementation |
|---|---|---|---|---|---|---|---|---|
| Health diagnostics explanation | Merge into bot-awareness PR5 | `diagnostics` | Platform owner unless D1 changes | Read-only | PR4 reconciliation, D1, orchestration catalogue if landed | Sensitive operational detail, stale facts | 0 / bot-awareness | Health implementation plan; health contracts/service; current scope source |
| Structured/persistent health findings | Merge into bot-awareness PR4/PR6 | Not a new toolset | Admin/owner projections | Deterministic read model | Approved retention, migration, sole writer | Secret leakage, unbounded history | 0 / bot-awareness | Health implementation plan and current PR state |
| Tool descriptor/catalogue | Keep; merge into BTD6 foundation | All | N/A | Foundation | Canonical descriptor and invariant tests | Metadata drift, parallel registry | 1 | BTD6 orchestration plan; all current `AIToolSpec` handlers |
| Toolsets/policy/neutral tool choice | Keep; merge into BTD6 foundation | All | Policy resolved | Foundation | Resolver, precedence, provider mapping | Authority widening, provider divergence | 1 | AI policy ownership; provider adapters; task router |
| Budgets/rate limits/cost policy | Keep; merge into BTD6 foundation | All | Policy resolved | Foundation | Typed budgets, stable failure reasons, metrics | Cost runaway, denial of service | 1 | Provider loops, metrics, feature flags |
| Evidence/result contracts | Keep; generalize carefully | All factual toolsets | Tool-specific | Read-only foundation | Typed envelope + domain-specific validation | Unsupported claims, false provenance | 1 | BTD6 ledger/faithfulness tests and plan |
| Safe audit trace/retention/redaction | Keep; merge into foundation | All sensitive toolsets | Admin/owner visibility | Foundation | Bounded trace schema, redaction, retention class | Raw prompt/result leakage | 1 | AI decision audit, redaction, diagnostics |
| SuperBot public/repo docs search | Keep; first net-new tool | `knowledge_base` | User in approved channels; internal corpus admin/owner | Read-only | Catalogue, corpus manifest, bounded search/result evidence | Stale docs, leaking internal plans | 2 | Doc classification, repo packaging/deploy access |
| Uploaded text/log/document reader | Keep, narrow | `document_reader` | Admin by default; explicitly enabled channels | Read-only | Attachment gate, type/size limits, redaction, transient processing | Secrets/PII, prompt injection, huge files | 2 | Discord attachment access, provider/file retention |
| Arbitrary/unbounded log reader | Reject | None | None | None | Never | Secrets, privacy, uncontrolled scope | Never | N/A |
| Web research/search | Keep, defer until connectors | `web_research` | Approved channels; admin default | Read-only | Approved search provider, domain policy, evidence, budgets/cache | Freshness, misinformation, cost, unsafe pages | 3 | Provider terms, allowlists, citation contract |
| Website/API status probes | Keep, merge with approved connectors/observability | `observability_extended` | Admin/owner | Read-only | Fixed target registry, timeouts, SSRF protection, health integration | SSRF, noisy polling, false outages | 3 | Existing health/diagnostics and approved targets |
| Generic approved API connector | Keep only as bounded infrastructure | `external_integrations` | Admin/owner | Read-only initially | Provider+operation registry, secret owner, schemas, egress policy | Arbitrary network access, secret leakage | 3 | Security ADR/product decision; connector ownership |
| GitHub repository/CI lookup | Keep, approved connector | `external_integrations` / `knowledge_base` | Public repo user; private repo owner/admin | Read-only | GitHub provider operations, token scopes, redaction, cache | Private code/log leakage, rate limits | 3 | Repo visibility/token policy; CI log redaction |
| YouTube/Twitch/content lookup | Defer; connector specialization | `external_integrations` | Approved channels/admin config | Read-only | Approved operations, cache, rate limits | API churn, low priority, announcement coupling | 3+ | Existing dependencies, provider terms |
| Google Docs/Sheets reader | Defer | `external_integrations` | Owner/admin with explicit binding | Read-only | OAuth/credential ownership, document allowlist, redaction | Broad account access, private docs | 3+ | OAuth and revocation design |
| Vision/screenshot analysis | Keep, defer | `media_vision` | Explicit attachment/channel policy; admin for diagnostics | Read-only | Capability projection, byte limits, redaction, retention/cost policy | PII, unsafe content, provider retention | 4 | Provider modality support/terms; Discord permissions |
| OCR | Merge with vision/document ingestion | `media_vision` / `document_reader` | Same as source attachment | Read-only | Deterministic/provider OCR adapter, confidence/evidence | Secret extraction, bad OCR treated as fact | 4 | OCR provider and confidence contract |
| Chart/report generation | Keep, from approved read models only | `observability_extended` | Admin/owner; public only for public data | Read-only output generation | Typed metric datasets, rendering limits, transient assets | Misleading charts, data leakage | 5 | Metrics ownership; Discord attachment limits |
| Scheduler/recurring reports | Merge into existing automation | `notification_actions` only after action architecture | Admin/owner | Action-gated/persistent | Confirmation, automation mutation, cancel/edit, audit, target allowlist | Spam, stale schedules, durable state | 6 | Automation registry/mutation/scheduler/executor |
| Notification delivery | Merge into existing automation/notification paths | `notification_actions` | Admin/owner | Action-gated | Template ownership, target/mention policy, confirmation, audit | Spam, mass mentions, wrong target | 6 | Existing publisher/automation paths and permissions |
| Action-confirmation flow | Keep as prerequisite, not a normal tool | Separate action proposal/execution contract | Depends on action | Action-gated | Typed draft, expiry, re-authorization, idempotency, audit, rollback/cancel | Confused deputy, replay, race | 6 | Capability authority; interaction lifecycle; mutation services |
| Safe admin maintenance actions | Defer | `admin_actions_safe` | Platform owner | Action-gated | D1, confirmation architecture, allowlist, deterministic owners | Outage, privilege escalation, no rollback | 7 | Each target service's mutation/lifecycle contract |
| Moderation recommendations | Defer; recommendation only | Separate moderation review toolset | Moderator/admin | Advisory read-only | Service-owned evidence packet, fairness/privacy review, audit | Bias, false accusation, private-data exposure | 7 | Moderation service/data quality and policy |
| Direct moderation/admin execution | Reject for roadmap horizon | None | None | Destructive action | Not proposed | Severe harm, irreversible actions | Never | N/A |
| Per-guild/category/channel capability config | Keep after built-ins stabilize | Policy layer | Admin/server owner per decision | Configuration mutation | Existing AI policy ownership, additive migration, preview/dry run | Configuration complexity, authority widening | 1 then later UX | AI config ownership and BTD6 plan D5 |

---

## 5. Proposed stable architecture

### 5.1 Request-to-result flow

```text
Discord event / explicit command
  → existing admission + AI natural-language policy
  → task routing + resolved guild/category/channel/role policy
  → AIOrchestrationPolicy resolver
  → canonical AIToolDescriptor catalogue + named toolset resolver
  → scope/provider/capability/budget filtering (authority can only narrow)
  → provider-neutral AIRequest + AIToolChoice + AIToolBudget
  → provider adapter maps neutral choice; bounded tool loop
  → service-owned read handler OR separate action proposal flow
  → strict argument validation + bounded typed result
  → evidence ledger/result contract + redaction before model context
  → typed answer contract / deterministic fallback
  → safe AIOrchestrationTrace + bounded metrics/audit summary
```

### 5.2 Canonical catalogue and descriptor

- Preserve `AIToolSpec` as the provider-facing declaration unless the BTD6 plan's
  implementation intentionally evolves it.
- Add one canonical `AIToolDescriptor` layer as specified by the BTD6 plan: spec,
  handler key/owner, toolsets, task affinity, result contract, cost class, freshness,
  parallel safety, and preflight safety.
- Derive named toolsets and grounding membership from canonical metadata where safe.
  Keep a domain-specific BTD6 evidence qualification rule; do not infer “grounding” from
  arbitrary names or toolsets.
- Add invariant tests: unique names, handler/spec parity, valid schemas, known result
  contracts, known toolsets, read-only registration, and no authority widening.

### 5.3 Toolset and policy resolution

Reuse the BTD6 plan's `AIOrchestrationPolicy`, `ToolRequirementMode`, `AIToolChoice`,
and `AIToolBudget` direction. Resolution must consider, in deterministic order:

1. global feature/capability kill switches;
2. task route and request type;
3. caller `AIScope` and Discord permission checks;
4. guild/category/channel/role AI policy;
5. selected built-in orchestration preset/toolsets;
6. connector/provider enablement and model capabilities;
7. freshness, cost, call/hop/time/result/fan-out budgets;
8. tool-specific availability and deterministic owner readiness.

The resolver returns offered tools, required groups/preflight calls where approved, and
stable exclusion/reason codes. Configuration may only narrow authority granted by code,
scope, Discord permissions, provider capability, and kill switches.

### 5.4 Provider-neutral choice and strict schemas

- Extend the provider-neutral request rather than passing provider-specific `tool_choice`
  JSON outside adapters.
- Provider adapters must implement conformance tests for automatic, none, required-group,
  and any later approved forced/preflight semantics.
- Validate tool arguments before handler invocation with strict JSON Schemas. Existing
  schemas must be inventoried and migrated compatibly; malformed arguments return a
  stable structured failure, never silently become `{}` for sensitive tools.
- Bound all result objects by item count, byte/character count, depth, and deadline.

### 5.5 Evidence and result contracts

Every factual tool result needs a typed/bounded envelope containing as applicable:

- tool and operation identity;
- deterministic owner/provider key;
- source identifiers/URLs safe to display;
- observed/fetched timestamp and freshness class;
- query/target summary without secrets;
- bounded facts or records;
- confidence/partial/degraded markers;
- redaction marker;
- stable error/reason code.

`CalculationEvidence` and the BTD6 faithfulness ledger remain authoritative for BTD6
numeric/factual claims. A neutral envelope may carry them, but generic evidence must not
weaken BTD6 exact-output and completeness checks.

### 5.6 Budgets, rate limits, and cost

`AIToolBudget` should bound at least calls, hops, wall time, result bytes/tokens, fan-out,
and cost class. Connector providers also need operation-specific and credential-specific
rate limits. Exhaustion must stop deterministically, emit a stable reason, preserve any
safe partial evidence, and produce a useful fallback without retry loops.

### 5.7 Safe trace, audit, retention, and redaction

- `AIOrchestrationTrace` records policy/preset/toolset IDs, offered/selected/excluded tool
  names, stable reason codes, timings, budget use, result contract/status, and correlation
  ID. It never stores chain-of-thought, raw messages, raw tool arguments, credentials,
  attachment bytes, or raw tool results.
- Sensitive calls additionally write an approved audit summary through one service owner.
- Redact before model context, before logs, and before durable audit. Treat external and
  user-provided content as untrusted prompt-injection-bearing data.
- Every durable data class must have an explicit retention owner and deletion path.

### 5.8 Connector provider registry

Create no generic arbitrary fetch tool. If approved, introduce a deterministic connector
registry with code-owned:

- provider keys and operation keys;
- credential source/least-privilege scope;
- fixed base hosts and egress/redirect rules;
- strict request and result schemas;
- target/resource allowlists;
- operation timeout, rate limit, cache, and cost class;
- redaction and retention class;
- readiness/health projection and stable degraded reasons.

The model may choose only an offered operation and schema-valid arguments; it may not
supply endpoints, tokens, headers, SQL, filesystem paths, or executable code.

### 5.9 Separate confirmation flow for actions

Action tools require a separate contract and registry from read-only AI tools:

```text
AI interpretation → typed action draft → deterministic validation/risk summary
→ bounded confirmation UI → re-authorize actor + target at click time
→ service-owned idempotent mutation → audit/result → rollback or cancel path
```

Drafts expire, bind actor/guild/channel/target/action/version, suppress uncontrolled
mentions, and cannot be replayed. AI never calls the mutation service directly. Existing
capability authority and mutation pipelines remain authoritative.

### 5.10 Deterministic fallback

Every tool family must define behavior for disabled policy, insufficient scope, missing
provider capability, degraded connector, invalid arguments, timeout, budget exhaustion,
partial results, redaction failure, and provider outage. The fallback must either answer
from approved deterministic evidence or state the precise limitation; it must not fill
facts from model memory where grounding is required.

---

## 6. Phased roadmap

### Phase 0 — Reconcile bot-awareness PR4–PR6 and security decisions

**Goal:** establish the actual post-Claude source state before planning new work.

- Query open/merged PRs and compare `main` source, not branch names alone.
- Reconcile PR4 structured observations, PR5 diagnostics tool, and PR6 persistent
  findings against the approved health plan.
- D1 **decided & shipped (#541)**: `_derive_scope()` resolves platform-owner scope for
  the bot owner. Before building owner-only tools, re-confirm the anti-impersonation /
  no-widening tests still hold.
- Decide PR6 retention/history, ownership, deletion, and migration boundaries.
- Re-run targeted searches for all planned orchestration types; remove roadmap work that
  Claude has already shipped.

**Exit gate:** bot-awareness plan/status docs and source agree; owner-only reachability is
resolved or owner-only AI capabilities remain explicitly out of scope; no duplicate
abstractions exist.

### Phase 1 — Tool orchestration foundation

**Direction:** after explicit maintainer approval, execute/refine the first phases of
`docs/ai/ai-complex-request-tool-orchestration-plan.md`; do not create a competing plan.

- Inventory current specs/handlers/schemas/provider loops.
- Land the canonical descriptor catalogue and named toolsets with compatibility tests.
- Land deterministic policy/toolset resolution and stable exclusion reasons.
- Add provider-neutral tool choice and typed budgets; map in provider adapters.
- Enforce strict arguments and bounded typed results.
- Add safe trace/policy preview, metrics, and provider-degraded behavior.
- Preserve BTD6 grounding and current default behavior throughout migration.

**Exit gate:** current tools pass catalogue invariants, adapters pass conformance tests,
policy only narrows authority, budgets terminate loops, and safe traces leak no content.

### Phase 2 — Knowledge-base and document-safe read tools

1. **Repository/public-document knowledge search first.** Build a code-owned corpus
   manifest with public/internal classifications, version/freshness stamps, bounded
   excerpts, and source paths. Do not expose arbitrary repository files.
2. **Uploaded text/log/document reader second.** Accept only explicit Discord attachments
   from the current request, allowlisted MIME/extensions, strict byte/page/line limits,
   transient processing, redaction, and prompt-injection labeling.
3. Keep image/OCR out of this phase unless the ingestion/security contract is already
   modality-neutral and provider retention is approved.

**Exit gate:** no filesystem path input, no raw upload persistence, secret-leak tests are
green, internal corpus requires correct scope/policy, and every answer cites evidence.

### Phase 3 — Approved external read connectors

- Approve and implement connector registry/security ADR first.
- Add one narrow provider/operation at a time, preferably GitHub public repository/CI
  metadata or fixed website status probes before a broad web-search provider.
- Add web search with source/citation/freshness contract, allow/deny policy, cache, and
  cost budget only after the registry is proven.
- Defer private GitHub, Google Docs/Sheets, creator-platform, and custom API credentials
  until binding/revocation/retention UX is approved.

**Exit gate:** arbitrary endpoints are impossible, SSRF/redirect/secret tests pass,
provider degraded states project into readiness/health, and kill switches work.

### Phase 4 — Vision, OCR, and media

- Add provider capability projection for image input/OCR.
- Process only explicitly attached, authorized, size/type-bounded media.
- Redact or reject likely secrets/PII before model context where feasible.
- Return OCR confidence and regions/source references; do not present uncertain OCR as
  deterministic fact.
- Keep bytes transient and review provider retention/training terms.

**Exit gate:** modality cost budgets, retention, unsafe-content handling, and redaction
are tested across supported providers.

### Phase 5 — Reporting and charting

- Generate reports/charts only from approved typed read models or evidence envelopes.
- Use deterministic chart specs/data validation; AI may propose narration, not invent
  metrics.
- Bound dimensions, labels, series, output bytes, and Discord attachment lifetime.
- Add accessibility text and source/freshness metadata.

**Exit gate:** chart data exactly matches source read models and cannot leak cross-guild
or owner-only data.

### Phase 6 — Notification, scheduler, and action-confirmation foundation

- Design and approve the separate action-draft/confirmation/audit contract.
- Reuse `automation_mutation`, `automation_scheduler`, `automation_executor`, and their
  diagnostics. AI can propose a rule/report; deterministic services validate/store/run.
- Require target allowlists, mention suppression, templates, expiry, re-authorization,
  idempotency, cancel/edit, retry bounds, and audit.

**Exit gate:** replay/race/permission tests pass; all schedules can be viewed, disabled,
and deleted without AI; no uncontrolled mention or target is possible.

### Phase 7 — Safe admin actions and moderation recommendations

- Start with advisory moderation evidence packets only; no punitive execution.
- Consider a very small allowlist of reversible/low-risk maintenance actions only after
  each deterministic owner provides validation, readiness, audit, and rollback behavior.
- Keep bans, kicks, timeouts, mass deletion, permissions, deployment, shell, arbitrary
  code/file/SQL, and mass messaging rejected.

**Exit gate:** explicit owner approval per action, live authorization re-check, rollback
or safe failure, fairness/privacy review for moderation, and complete audit coverage.

---

## 7. Conditional first 2–3 PR recommendation

> **Do not start these PRs yet.** First complete Phase 0. Bot-awareness PR4–PR6 have
> landed (#541) and D1 is resolved, so re-scope these PRs against the delivered health
> stack and avoid duplication; owner-only tooling is now reachable via
> `_derive_scope` → `PLATFORM_OWNER`.

### PR A — Canonical read-only tool catalogue and compatibility invariants

**Goal:** implement the BTD6 orchestration plan's catalogue foundation without changing
which tools are offered or how providers execute them.

- **Likely files:** `disbot/core/runtime/ai/contracts.py`, a canonical catalogue module
  in the existing AI service/runtime ownership boundary, `disbot/services/ai_tools.py`,
  `tests/unit/services/test_ai_tools.py`, AI boundary/invariant tests, and the BTD6
  orchestration plan/status notes.
- **Boundary:** descriptors are pure metadata; handlers remain service-owned and
  read-only; no cog/UI/provider behavior or migration.
- **Tests:** unique descriptors, spec/handler parity, valid/strict-able schemas, known
  toolsets/result contracts, BTD6 grounding membership, read-only invariant, current
  registry snapshot compatibility.
- **Docs:** mark the exact shipped catalogue subset in the BTD6 plan; do not mark policy,
  budgets, or connectors shipped.
- **Verification:** targeted AI tool/invariant tests, docs tests, strict architecture,
  then full quality because runtime code changed.
- **Rollback:** additive metadata and derived catalogue can revert without stored state.
- **Stop conditions:** descriptor ownership conflicts with current Claude work; catalogue
  cannot preserve current offered tools; strict-schema inventory reveals breaking
  incompatibilities needing a separate decision.

### PR B — Deterministic toolset/policy resolution, neutral choice, budgets, safe trace

**Goal:** make tool availability and loop limits explicit and provider-neutral while
preserving default behavior.

- **Likely files:** AI contracts, natural-language stage, task router/policy services,
  provider base/OpenAI/Anthropic adapters, AI diagnostics/projection/readiness services,
  metrics/audit service, and focused tests/evals.
- **Boundary:** policy can only narrow code/scope/provider authority; no new capability
  handlers, no action tools, no custom guild profiles or migration in the first slice.
- **Tests:** precedence/exclusion reasons, scope gating, provider parity, required/none/
  auto choice, malformed arguments, call/hop/time/result budgets, degraded providers,
  safe-trace redaction, BTD6 faithfulness regression, eval trace grading.
- **Docs:** update the BTD6 orchestration plan with shipped contracts and unresolved UX/
  persistence decisions.
- **Verification:** focused provider/policy/eval tests, strict architecture, full quality.
- **Rollback:** built-in compatibility preset and feature flag restore the old automatic
  offered-tool behavior; no durable config.
- **Stop conditions:** D1 is accidentally widened; adapters cannot map neutral semantics
  consistently; budget termination or safe traces cannot be proven; BTD6 grounding
  regresses.

### PR C — Bounded SuperBot knowledge-base search (public corpus only)

**Goal:** add the first net-new capability as a deterministic, read-only search over an
explicit public/documentation corpus.

- **Likely files:** a service-owned knowledge corpus/search module, canonical descriptor
  registration, packaged corpus manifest, tests/evals, and capability docs. Avoid a new
  cog unless a deterministic non-AI user surface is separately approved.
- **Boundary:** no arbitrary paths, no repository-wide filesystem tool, no internal plans
  by default, no external network, no persistence/migration. Search owns retrieval; AI
  only interprets bounded evidence.
- **Tests:** corpus allowlist/classification, path traversal rejection, bounds, freshness/
  source metadata, missing corpus/degraded fallback, scope/policy gating, prompt-injection
  fixtures, secret-leak tests, evidence completeness, no-AI deterministic search test.
- **Docs:** add corpus ownership/classification and tool result contract; cross-link this
  roadmap and keep the ideas backlog non-authoritative.
- **Verification:** knowledge service/tool/eval tests, docs tests, strict architecture,
  full quality.
- **Rollback:** remove descriptor/feature flag; no durable state or external credentials.
- **Stop conditions:** deployment cannot provide a trustworthy versioned corpus; public
  versus internal docs cannot be classified; search requires arbitrary filesystem access;
  evidence contract is not stable.

---

## 8. Safety, privacy, and retention model

Default rule: retain configuration/audit only when there is a named service owner and
approved deletion policy. Raw content is transient by default. Redaction happens before
model context, logs, traces, and durable storage.

| Data/capability | Default storage | Redaction/handling | Minimum access/default gate |
|---|---|---|---|
| Raw attachment bytes | Never persist; memory/temp processing only with guaranteed cleanup | Type/size validation before read; reject archives/executables initially | Explicit attachment + enabled channel; admin for logs/configs |
| Screenshots/images | Never persist by default | Strip metadata where feasible; reject/blur secrets/PII where policy requires | Explicit attachment; modality enabled; admin for diagnostics |
| Uploaded logs/text | Never persist raw; optional short-lived request cache only | Secret/Discord ID/token/credential redaction; line/byte bounds | Admin by default; no global/unbounded logs |
| Extracted text/OCR | No durable storage by default | Carry source/confidence; redact before model | Same as source attachment |
| Knowledge corpus | Packaged/versioned approved documents only | Public/internal classification; bounded excerpts | Public corpus can be user; internal corpus admin/owner |
| Web search results | Short cache of normalized URLs/snippets/freshness only | Domain policy; no cookies/credentials/raw pages in audit | Explicitly enabled channels; admin default |
| External connector results | Operation-specific short cache only | Provider schema redaction; never store tokens/headers | Approved binding and operation; admin/owner |
| GitHub/CI data | Public metadata cache; private content transient by default | Redact secrets, actor IDs where unnecessary, raw CI logs denied initially | Public repo policy or explicit private binding/owner |
| Generated charts | Short-lived generated attachment/cache | Embed source/freshness; no hidden owner-only series | Same scope as source dataset |
| Tool traces | Durable only as bounded summaries if approved | No raw prompt/args/results/reasoning/credentials/content | Admin/owner diagnostics projection |
| Scheduled report config | Durable through automation owner until deleted | Typed template/target; no raw model prompt required | Admin/owner + confirmation + target allowlist |
| Scheduled report outputs | Discord message plus bounded audit metadata | Mention suppression; no raw sensitive evidence | Same scope as report and target |
| Admin action drafts | Short-lived, expiring, actor-bound | Store typed key/params/risk summary, not prose secrets | Platform owner + re-authorization |
| Admin action results | Persistent bounded operational audit where approved | Stable status/reason, target summary, correlation ID | Platform owner |
| Moderation recommendations | Prefer transient review packet; bounded audit of review event | Separate facts/recommendation/confidence; minimize subject data | Moderator/admin; manual review only |

No provider may receive content until its capability, retention/training terms, region/
privacy posture, and configured credentials are approved. A redaction failure must fail
closed for sensitive content.

---

## 9. Observability and audit requirements

### Required for every phase

- Structured logs with bounded labels and stable reason codes for selection exclusion,
  schema rejection, timeout, provider degradation, budget exhaustion, redaction failure,
  and deterministic owner failure.
- Metrics/counters for offered, selected, executed, succeeded, partial, rejected, timed
  out, budget-exhausted, and degraded calls by bounded tool/provider/operation/result
  contract labels. Never label with guild/user/channel IDs, arguments, URLs, or content.
- Safe orchestration traces that explain policy resolution and execution without raw
  reasoning, prompts, arguments, results, uploads, or secrets.
- Correlation IDs connecting decision audit, provider call, tool execution, deterministic
  owner log, and user-safe failure where available.
- Budget utilization and exhaustion surfaced in safe diagnostics/policy preview.
- Provider/connector degraded state integrated with AI readiness/diagnostics and, where
  operationally material, health snapshot adapters after the health plan permits it.
- Tests for silent failure paths: provider unavailable, handler raises, invalid result,
  redaction fails, audit write fails, metric sink unavailable, and Discord send fails.
- Feature/connector kill switches and a deterministic no-tool/no-provider fallback.

### Phase-specific additions

| Phase | Additional observability/audit |
|---|---|
| 0 | Record verified PR/source state and unresolved decisions; no runtime metrics. |
| 1 | Policy preview, exclusion reason distribution, provider choice parity, loop/budget termination metrics, safe trace grading. |
| 2 | Corpus version/freshness, attachment reject reasons, redaction counts without content, result bound truncation. |
| 3 | Connector readiness, rate-limit/cache/timeout/redirect rejection metrics, operation-key audit, fixed-target status. |
| 4 | Modality/provider cost, bytes/pages processed, OCR confidence bands, retention/cleanup failures. |
| 5 | Report/chart render failures, data freshness, output size, source-contract validation. |
| 6 | Draft/confirm/expire/cancel/execute/retry states, re-authorization failures, target/mention policy rejection. |
| 7 | Action rollback/safe-failure status; moderation packet evidence completeness and reviewer audit. |

---

## 10. Test plan

### Unit tests

- Descriptor/catalogue uniqueness, metadata validity, handler parity, toolset derivation,
  strict schemas, result bounds, evidence envelopes, redaction, stable error reasons,
  policy precedence, budget arithmetic, connector operation allowlists, and retention
  classification.

### Integration tests

- Natural-language stage → policy resolver → registry → provider loop → handler → safe
  evidence/trace/fallback across tools enabled/disabled and provider healthy/degraded.
- Health diagnostics tools consume projected `HealthSnapshot`; automation proposals use
  existing mutation/scheduler/executor paths; lifecycle/admin actions use service owners.

### Doc-pinning tests

- Pin this roadmap's status/authority relationship if it becomes approved guidance.
- Pin backlog status as non-authoritative and cross-link it to this roadmap.
- Extend existing AI config ownership doc pins only when new durable policy fields land.
- Do not pin speculative phase completion as shipped reality.

### Architecture/invariant tests

- Cogs remain thin; provider SDK imports remain isolated; tools remain read-only in the
  read registry; action registry cannot enter normal provider loops; no direct DB writes;
  no arbitrary endpoint/path/SQL/shell inputs; one canonical catalogue; policy cannot
  widen scope; mutations use existing owners.

### Redaction/secret-leak tests

- Plant secrets, tokens, URLs with credentials, Discord IDs, private repo data, log
  fragments, image metadata/OCR text, connector errors, provider errors, and action
  params. Assert absence from model context where disallowed, logs, metrics, traces,
  audit, embeds, and persistent records.

### Scope and permission tests

- Every `AIScope`, guild owner/admin/moderator/user distinction, bot-owner decision,
  per-guild/category/channel policy, missing Discord permissions/intents, cross-guild
  target, stale interaction, and policy-only narrowing case.

### Budget/rate-limit tests

- Calls, hops, time, result bytes/tokens, fan-out, cost class, connector rate limits,
  retry bounds, cache hits, and deterministic partial/exhaustion fallback.

### Provider degraded/offline tests

- Unsupported neutral tool choice, tools unsupported, vision unsupported, malformed tool
  calls, timeout, rate limit, connector offline, readiness degradation, and deterministic
  no-provider/no-tool result.

### Discord permission and bounded UI tests

- Attachment visibility, target channel send permission, mention suppression, embed/
  message/file limits, deleted channel/member/role, ephemeral confirmation expiry, and
  re-check authorization at interaction time.

### Confirmation-flow tests for future actions

- Draft actor/target binding, explicit confirm, deny/cancel, expiry, replay, double click,
  changed permissions, changed target, idempotency, service failure, rollback, audit
  failure, and safe user response.

### Eval/trace grading tests

- Correct toolset/selection/arguments/sequence, evidence completeness, citations,
  unsupported-claim refusal, provider parity, budget adherence, prompt-injection
  resistance, safe trace completeness, and final answer faithfulness.

### Minimum verification per PR class

- Docs-only roadmap/status change: strict architecture plus `tests/unit/docs/`.
- Runtime AI/tool change: focused unit/integration/eval tests plus
  `python3.10 scripts/check_quality.py --full`.
- Migration/action change: full quality, migration/idempotency/sole-writer tests, and
  approved live/manual smoke checklist.

---

## 11. Rejection and defer ledger

| Idea | Status | Reason now | Foundation that could unblock | Risk if early |
|---|---|---|---|---|
| Arbitrary URL fetch/scraper | Reject | Cannot guarantee target, redirects, content, or cost | None; replace with approved provider/operation registry | SSRF, data exfiltration, scraping abuse |
| Raw SQL tool | Reject | Violates ownership and least privilege | None; expose typed service read models instead | Data loss/leakage, ownership bypass |
| Arbitrary filesystem/file-path tool | Reject | Model must not choose host paths | None; explicit packaged corpus or attachments only | Secret/source/env leakage |
| Unbounded/raw bot log access | Reject | Logs contain secrets/PII and are unbounded | Typed/redacted structured observations only | Secret leakage, cost/availability failure |
| Shell/Python/code execution | Reject | No safe bounded ownership/rollback | None | Remote code execution/outage |
| Direct destructive Discord actions | Reject | High-impact and often irreversible | Not proposed; service-owned manual workflows remain | Bans/deletes/permission damage |
| Mass DM/mass messaging/uncontrolled mentions | Reject | Abuse/spam risk | Fixed automation templates/targets with mention suppression | Harassment, Discord enforcement |
| Platform-owner AI tools | Unblocked (was Defer) | D1 **resolved (#541)**: owner scope reachable; still needs per-tool owner-gating + anti-impersonation tests | Owner resolution shipped | Privilege widening if scope checks regress |
| Persistent tool traces/raw results | Defer/reject raw | No retention owner; content is sensitive | Bounded summary schema + retention/deletion approval | Privacy breach and storage growth |
| Generic connector before registry ADR | Defer | Equivalent to arbitrary network access | Provider/operation registry and egress/credential policy | SSRF, token leakage, uncontrolled cost |
| Private GitHub/CI lookup | Defer | Private code/log/token scope not approved | Binding/revocation/redaction/retention design | Source/secrets leakage |
| Google Docs/Sheets | Defer | OAuth grants are broad and revocation UX absent | Least-privilege binding and document allowlist | Private workspace data exposure |
| Vision/OCR before modality policy | Defer | Provider retention, PII, bytes/cost unresolved | Attachment/modality/redaction/retention foundation | PII/secret leakage and runaway cost |
| Scheduler/notification as AI-owned subsystem | Reject/merge | Existing automation owns scheduling/execution | Use separate proposal/confirmation over automation owner | Duplicate state, spam, unsafe execution |
| Custom guild orchestration profiles in v1 | Defer | Built-in contracts and previews not stable | Proven built-ins + mutation/preview/rollback UX | Configuration complexity and authority mistakes |
| Moderation execution | Reject | AI recommendation cannot justify punishment | Keep human-reviewed advisory packets only | Bias, false positives, irreversible harm |
| Moderation recommendation now | Defer | Evidence quality/fairness/privacy not proven | Typed evidence packets + review policy/audit | False accusation and private-data exposure |
| Cog reload/deploy/cache-clear action tools | Defer | Readiness/rollback/owner action list not approved | Per-action deterministic owner + confirmation/audit | Outage and partial state |
| YouTube/Twitch/creator announcements | Defer | Lower priority and couples reads to actions | Approved read connector, then automation proposal flow | Spam, API churn, stale announcements |

---

## 12. Final recommended document changes

### Recommended patch sequence after maintainer approval

1. **Merge PR #539 as an ideas backlog only**, after adding a short cross-link/status note
   that this roadmap owns triage/sequence and that execution remains unauthorized.
2. **Keep this new `docs/ai/ai-tool-capability-roadmap.md` as the guidance document** for
   the next sessions. Do not convert it into the BTD6 or bot-awareness execution plan.
3. **Do not replace the approved health plan or the BTD6 planning document.** Update
   their status headers only when source, approval state, and merged PRs prove it.
4. **Update `docs/AGENT_ORIENTATION.md` after roadmap approval** to list this document
   under planning/reference material for net-new AI tool capabilities, explicitly not
   under binding docs.
5. **Update `.session-journal.md` each session** with verified PR/source state, decisions,
   stop conditions, and the next bounded slice. Keep durable architecture rules in the
   binding docs, not only the journal.
6. **Add a small doc-pinning test after approval** asserting:
   - the backlog says “ideas backlog — not approved” and links here;
   - this roadmap says it is subordinate to the health execution authority and BTD6 design
     direction;
   - the bot-awareness map still points to its implementation-plan authority;
   - speculative types are not described as shipped until they exist in source.
7. When Phase 1 starts, **update the BTD6 orchestration plan's status rather than create a
   second implementation plan**. A dedicated capability plan is justified only for a
   bounded family with new product/security decisions, such as connectors or actions.

### Smallest verification set for roadmap/docs changes

```bash
python3.10 scripts/check_architecture.py --mode strict
python3.10 -m pytest tests/unit/docs/ -q
```

If a later docs patch changes source-pinned claims, also run the targeted tests for those
claims. Runtime/tool/provider changes require the full CI mirror.

---

## Handoff: copy-paste prompt for Claude Opus 4.8

```text
You are Claude Opus 4.8 reviewing SuperBot's source-verified AI Tool Capability Roadmap
after the current bot-awareness PR4–PR6 work is finished.

Repository: menno420/superbot
Primary roadmap: docs/ai/ai-tool-capability-roadmap.md

Before proposing or changing anything:
1. Read .claude/CLAUDE.md, .session-journal.md, docs/AGENT_ORIENTATION.md, and all binding
   architecture/ownership/runtime/helper docs.
2. Verify current main and all open/merged PRs. Do not trust the roadmap's 2026-06-06
   snapshot. Reconcile bot-awareness PR4, PR5, and PR6 against
   docs/health/bot-awareness-implementation-plan.md and source.
3. Read docs/ai/ai-complex-request-tool-orchestration-plan.md and determine which planned
   contracts/types have actually landed. Search for AIToolSpec, AIToolDescriptor,
   AIOrchestrationPolicy, ToolRequirementMode, tool_choice, build_registry,
   btd6_grounding, and diagnostics.
4. Re-check _derive_scope and PLATFORM_OWNER. If owner reachability is unresolved, STOP:
   do not implement owner-only AI tools or silently lower their required scope.
5. Read the open/merged AI extra-tool backlog and reconcile it with the roadmap. Do not
   create arbitrary web/file/API access, action tools, migrations, or a second health
   service.

Review goals:
- Correct stale shipped/in-progress claims in the roadmap.
- Confirm document control: the health implementation plan owns diagnostics; the BTD6
  orchestration plan supplies shared-foundation design direction pending approval; the
  backlog remains non-authoritative.
- Identify duplication with Claude's completed work and remove it from the next slice.
- Confirm that the first implementation slice is still the canonical read-only catalogue
  and compatibility invariants. If already shipped, advance only to the next smallest
  independently revertible foundation slice.
- Preserve thin cogs, service ownership, strict schemas, bounded results, evidence,
  budgets, redaction, audit, deterministic fallbacks, and rollback safety.

Do not start implementation until the maintainer approves your refined 2–3 PR plan.
If approved, execute no more than the next 2–3 independently revertible PRs, run Python
3.10 CI-parity checks, update source-pinned status docs and the session journal, and stop
on any roadmap security/ownership gate.
```
