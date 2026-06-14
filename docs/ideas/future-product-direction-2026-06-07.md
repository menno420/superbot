# SuperBot future product direction — source-aware brainstorm

> **Status:** `ideas` — capture-only brainstorm. **Nothing in this document is
> approved for implementation, sequencing, or promotion.** Any candidate must pass
> the promotion path in [`README.md`](./README.md).
>
> **Captured:** 2026-06-07
>
> **Authority:** source code and merged PRs win, followed by binding contracts and
> decisions. `docs/current-state.md` is the global status router. The operating
> decisions and rejection ledger in
> `docs/planning/superbot-ideas-lab-2026-06-05.md` §2 and §6 remain binding.
>
> **Scope:** future-facing product discovery after the current stability,
> server-management, bot-awareness, AI-readiness, and BTD6 provenance gates mature.
> This is deliberately a backlog, not a plan or a PR sequence.

## Executive summary

SuperBot's strongest long-term direction is a **coherent, explainable Discord control
surface** rather than a collection of commands. Existing panels, Help, setup,
diagnostics, audit reads, capability/governance resolution, and subsystem folios can
converge into one product language:

- **Server owners** should feel guided from “what can SuperBot do?” through setup,
  readiness, safe configuration, and ongoing server care.
- **Moderators and staff** should get fast, policy-aware actions with clear authority,
  previews, audit history, and recovery guidance.
- **Normal users** should discover useful games, profiles, economy, inventory, and
  community features without needing to memorize commands.
- **The bot owner/operator** should be able to understand health, capability posture,
  scheduled work, failures, and source freshness without reading raw logs first.

The strongest clusters are: (1) a shared explanation/discovery language across Help,
panels, diagnostics, and setup; (2) reusable read-only readiness, audit-timeline, and
notification surfaces; (3) server-management extensions that reuse lifecycle,
provisioning, governance, and audit owners; and (4) ambitious dashboards, AI
explanations, BTD6 workspaces, and media features that remain gated and future-only.

These ideas are **not implementation approvals**. Server-management remains the
highest-value approved lane; this document must not compete with its tracker or turn
future concepts into current work.

## Repo-aligned current context

### Verified roadmap situation

- Operational stability is accepted after PR #535; known UX follow-ups are not a
  reason to start another broad stabilization programme.
- Local history includes merged PR #556, completing server-management PR10's second
  slice. The current-state router and server-management folio still identify the
  remaining PR10 items, then PR11–PR14, as the active approved lane.
- Bot-awareness PR1–PR6 is shipped. The health/diagnostics folio retains maintainer
  live verification of production AI tool calling and grouped findings as its next
  checks.
- Settings, bindings, provisioning, capability authority, lifecycle services, and
  audit seams provide useful foundations, but stale status ledgers are not automatic
  work queues.
- AI expansion remains gated by production/live verification, orchestration approval,
  provider/provenance, caching/source-health, and behavior/config correctness. No AI
  write/action tools are candidates here.
- BTD6 extraction and new mappings remain paused until ADR-006 provenance ownership,
  provider parity, cache/freshness/source health, and behavior/config gates clear.
- Games retain ADR-002: in-flight game state is intentionally not restart-safe, and
  Redis/external state is out of scope.
- Media/YouTube is shared platform infrastructure under ADR-007, not BTD6-owned, and
  any public expansion needs privacy, retention, provenance, moderation, and degraded
  provider behavior review.

### Open-PR verification

The container does not provide `gh` or a configured Git remote. A live request to the
public GitHub pull-request API for `menno420/superbot` returned **no open PRs** on
2026-06-07. This is a best-effort verification rather than a claim that the local
checkout has authenticated visibility into private PRs.

## Existing ideas and do-not-duplicate check

### Extend these existing captures; do not duplicate them

The existing Ideas Lab already captures:

- Help route labels, deprecated-command badges, channel-cap wording, game refund
  hints, and bounded game-panel gaps.
- Access explainers, cleanup dry-runs/history, counting persistence health, migration
  health, panel recovery, anchor hints, and setup resume/final-review preflight.
- Settings capability previews, “why can't I edit?” explanations, provenance cards,
  capability audit reports, and visibility pagination.
- User profile cards, coin history/explanations, inventory search, game-refund lookup,
  moderation case timelines, logging-route health, readiness deltas, and smoke status.
- BTD6 source health/answerability/freshness/provider parity and AI decision/guard/tool
  coverage explainers behind their respective gates.
- Large future concepts: shared media/video references, operator changelog, automated
  smoke runner, AI-assisted setup actions, server insights, BTD6 strategy workspace,
  automation builder, and website dashboard.

The command-expansion backlog already carries many panel/hub and game-entry ideas.
The AI extra-tool backlog already owns web/vision/file/KB/connectors/scheduler and
notification capability proposals. The mining brainstorm already owns mining and
exploration design ideas. New entries below either add a distinct product-level
shape or explicitly identify the existing item they should extend.

### Binding rejected ideas — do not re-propose

Re-opening any item below requires changing its governing decision first:

- Resuming BTD6 extraction or adding mappings before the provenance gate.
- Adding AI write/action tools before the AI guard/audit gate.
- A second governance simulator, panel/router framework, or generic helper module.
- Blanket fail-closed behavior for every interaction.
- Redis-backed state or universal restart-safe/checkpointed game state.
- A broad all-cogs thin-cog sweep.
- One slash command per sub-action; slash commands remain front doors to panels.
- A separate “danger” dashboard; extend `ReadinessSnapshot` instead.

## New idea catalog

Each row is safe to **document** now, not approved to implement. “Reuse” names the
preferred existing seam; promotion still requires source verification.

### Immediate future polish

| Name | Description and user value | Owner area | Reuse and architecture fit | Hidden dependencies and required gates | Risk | Suggested documentation home | Timing |
|---|---|---|---|---|---|---|---|
| **Action-language style guide** | Give panels a consistent vocabulary for status, authority, preview, apply, cancel, recovery, and next action. Reduces hesitation and makes different subsystems feel like one bot. | Help / shared views | Extend existing panel renderers, back-navigation conventions, and Help labels; copy-only first, no new framework. | Inventory current labels; respect per-surface fail-open decisions and accessibility/Discord limits. Gate: current server-management panel work must settle the vocabulary it needs first. | Low | This backlog; later a reference guide only if promoted | After current roadmap |
| **“What happens next?” panel footer** | A compact footer explains whether an action previews, mutates, audits, notifies, or needs confirmation. Helps owners and staff trust consequential actions. | Shared views / owning feature | Generated from existing action metadata, capability result, provisioning preview, and audit behavior where available; never a parallel action registry. | Needs a verified source for each claim; cannot promise audit/rollback where absent. Gate: use only on source-verified surfaces after their active work lands. | Low | Extend Ideas Lab panel next-action hints | After server-management |
| **Diagnostics summary ladder** | Render health results as “healthy / degraded / blocked / next check” with one plain-language summary before details. Makes operator diagnostics useful without hiding evidence. | Health / diagnostics | Extend typed health contracts, `diagnostics_service`, findings, and `ReadinessSnapshot`; preserve provider isolation. | Needs agreed severity wording and degraded-vs-broken rules. Gate: production live checks and existing finding semantics verified. | Low | Health folio Ideas link to this backlog | After current roadmap |
| **Setup guidance cards by owner goal** | Let an owner start from goals such as “moderate safely,” “set up roles,” or “enable games,” then link to existing setup/panels and explain prerequisites. Reduces setup confusion without rewriting the wizard. | Setup / provisioning | Compose existing setup sections, provisioning previews, capability explanations, and Help routes; read/navigation-only. | Requires route inventory and accurate readiness facts. Gate: server-management setup sections and current wizard recovery behavior mature. | Medium | Server-management/settings folio Ideas link | After server-management |
| **Audience-aware Help summaries** | Help descriptions explicitly say who a feature is for, what authority it needs, and whether it opens a panel or typed flow. Improves discovery for owners, staff, and users. | Help / command access | Extend shared Help resolver and existing route-label/deprecated-badge candidates; deterministic metadata only. | Needs command-classification accuracy and capability wording. Gate: extend rather than duplicate Ideas Lab Help labels. | Low | Extend Ideas Lab Help-label cluster | After current roadmap |

### Near-term extensions

| Name | Description and user value | Owner area | Reuse and architecture fit | Hidden dependencies and required gates | Risk | Suggested documentation home | Timing |
|---|---|---|---|---|---|---|---|
| **Server-care checklist** | A read-only owner checklist connects moderation readiness, logging routes, role feasibility, cleanup policy, setup completeness, and key diagnostics. It answers “what should I look at next?” without becoming a second hub. | Server management / diagnostics | Compose existing diagnostics snapshots and links into existing Server Management/Help surfaces; facts remain owned by subsystems. | Requires stable read models and clear omission/degraded semantics. Gate: remaining PR10 and relevant PR11–PR14 surfaces land first. | Medium | This backlog; later server-management folio Ideas | After server-management |
| **Policy consequence preview** | Before saving moderation, cleanup, command-access, or visibility policy, explain the affected audience/scope and likely operational consequence. Reduces accidental misconfiguration. | Governance / settings / server management | Reuse effective-state resolution, cleanup diagnostics, capability authority, provisioning preview, and owning mutation service. | Needs per-policy deterministic preview definitions and stale-state handling. Gate: each owning service must already expose a trustworthy read/preview seam. | Medium | Extend Ideas Lab previews/explainers | After server-management |
| **Role automation readiness card** | Show whether the bot can apply each configured automated role and why not, linking to the owning configuration surface. Prevents silent expectation gaps. | Roles / diagnostics | Reuse role feasibility, ID-first selectors, automation reads, and diagnostics providers; read-only. | Needs bounded rendering for large guilds and privacy-safe member examples. Gate: current role automation and server-management dependencies settle. | Low | Server-management folio Ideas link | After server-management |
| **Channel workflow starter templates** | Provide preview-only starting shapes for common channel/category layouts, then route accepted changes through provisioning and lifecycle services. Saves owners repetitive setup while preserving ownership. | Provisioning / channel lifecycle | Reuse catalogue → preview → confirmed apply → audit and channel lifecycle services; no direct creation path. | Needs conflict detection, stable IDs, rollback/partial-failure design, and permission review. Gate: role templates/setup/server-management sequence and lifecycle coverage mature. | High | This backlog; later dedicated concept summary | After server-management |
| **Moderation policy explainer** | A staff-facing read view explains current reason requirements, timeout ceiling, DM behavior, purge behavior, trusted roles, escalation, and logging destination. Makes configured policy usable in practice. | Moderation / Help | Reuse `moderation_config`, capability checks, feasibility, and existing panel; no mutations. | Remaining PR10 policy fields must exist and wording must distinguish configured from effective state. Gate: remaining PR10 completes. | Low | Server-management folio Ideas link | After server-management |
| **Economy and XP activity statement** | A user-readable statement combines existing coin, XP, inventory, refund, and relevant audit reads with “why did this change?” links. Builds trust and supportability. | Economy / XP / inventory | Extend existing audits/read models and Ideas Lab coin/refund/profile candidates; all writes stay with owning services. | Requires privacy rules, pagination/retention, and a common presentation shape without merging ownership. Gate: source-verify audit completeness first. | Medium | Extend Ideas Lab user-profile/coin-history cluster | After current roadmap |
| **Command-access explanation in context** | From Help or a denied action, explain whether the blocker is channel visibility, capability, role, guild setting, or unavailable/degraded feature and point to the right next action. | Help / governance / diagnostics | Extend Ideas Lab IL-1 and existing governance/effective-state reads; no second simulator. | Must avoid revealing restricted policy details and handle resolver failure per surface. Gate: extend IL-1 only after its source seam is re-verified. | Medium | Extend Ideas Lab IL-1 | After current roadmap |

### Medium-term reusable systems

| Name | Description and user value | Owner area | Reuse and architecture fit | Hidden dependencies and required gates | Risk | Suggested documentation home | Timing |
|---|---|---|---|---|---|---|---|
| **Unified audit/event timeline read service** | A reusable read projection presents moderation, lifecycle, governance, economy, setup, and automation events in owner-appropriate timelines while each domain retains write ownership. Improves investigation and trust. | Audit/logging platform | Project existing audit/event records; read-only adapters over domain-owned facts, not a new mutation/event pipeline. | Event taxonomy, redaction, retention, pagination, actor privacy, and missing-history semantics. Gate: audit coverage and ownership map verified across candidate domains. | High | New dedicated concept summary after review | After server-management |
| **Notification subscription profiles** | Owners/users subscribe to approved summaries such as health degradation, moderation digests, event reminders, or personal activity; delivery uses existing notification/scheduler owners. Reduces noise while making important events visible. | Notifications / scheduler / settings | Extend existing scheduler/notification paths and settings authority; no net-new delivery subsystem. | Consent, quiet hours, rate limits, privacy, channel bindings, retry/observability, and unsubscribe guarantees. Gate: existing notification ownership/source behavior verified; AI backlog duplication avoided. | High | Extend AI extra-tool backlog's scheduler/notification ownership notes or a reviewed concept summary | Long-term |
| **Automation recipe model** | Owners compose a bounded trigger → conditions → approved service action recipe from a curated catalogue. Enables the “anything bot” direction without arbitrary scripting. | Server management / governance | Reuse capability checks, service-owned mutations, audit events, scheduler/event seams, provisioning previews, and confirmations. | Trigger/event taxonomy, recursion prevention, idempotency, rate limits, rollback, dry-run, permissions, and migration design. Gate: server-management complete and dedicated architecture/decision review; no AI actions. | High | Extend Ideas Lab rule/automation-builder item | Long-term |
| **Workflow recovery/resume contract** | Define a reusable way for multi-step panel workflows to explain expiration, reopen at a safe read step, and reconstruct only durable selections. Reduces dead ends without promising restart-safe games. | Shared views / setup / provisioning | Extend persistent anchors, setup recovery, and existing durable configuration reads; never checkpoint in-flight games. | Per-workflow durability rules, stale-resource detection, authorization re-check, and no hidden writes. Gate: existing panel recovery and setup resume behavior verified. | Medium | Extend Ideas Lab panel/setup recovery cluster | After server-management |
| **Diagnostics/readiness card contract** | A common card shape for status, evidence time, degraded reason, owner, and next check lets all subsystems contribute without a second dashboard. | Health / diagnostics | Extend typed health contracts and `ReadinessSnapshot`; providers remain isolated and domain-owned. | Stable severity/evidence schema, rendering limits, freshness semantics, and provider budgets. Gate: current health semantics/live verification complete. | Medium | Health folio Ideas link / later reference if promoted | After current roadmap |
| **Guild template/provisioning model** | A reusable, versioned description of desired roles, channels, bindings, settings, and policies supports previewed setup and safe drift explanations. | Settings / bindings / provisioning | Build only on catalogue, bindings, settings resolution, lifecycle owners, preview/confirm/audit, and role/channel selectors. | Versioning, migration, partial apply, ownership conflicts, deletion policy, rollback, and secrets/external resources. Gate: server-management setup and role-template work mature first. | High | This backlog; later dedicated concept summary | Long-term |
| **Capability explanation layer** | Standardize how surfaces describe allowed/denied/degraded outcomes and where authority came from, while the canonical resolver remains the only authority. | Governance / Help / settings | Presentation adapters over capability authority, governance snapshots, and feature readiness; no second simulator. | Redaction, context-specific wording, fail-open posture, and stable reason codes. Gate: source-verify reason outputs and extend IL-1/settings explainers. | Medium | Extend Ideas Lab explainers | After server-management |
| **Help/search/discovery index** | A deterministic index connects commands, panels, audiences, capabilities, settings, diagnostics, and folio-backed feature maturity so users can search by goal. | Help / command access | Extend shared Help resolver and command metadata; links to existing surfaces rather than creating sub-action commands. | Metadata ownership, stale-route tests, localization/search ranking, and restricted-feature visibility. Gate: command classification and Help labels mature. | Medium | Extend command-expansion backlog and Ideas Lab Help cluster | After current roadmap |
| **User preference/profile read model** | Present user-facing preferences and profile facts—notification choices, game defaults, visibility-safe activity, rank, coins, inventory—from domain-owned reads. Makes SuperBot feel personal without merging write ownership. | User profile / settings / economy/games | Compose existing reads; mutations continue through each owning service. | Privacy, guild-vs-global scope, deletion/export, retention, and absence semantics. Gate: review existing schemas and Ideas Lab profile candidate first. | Medium | Extend Ideas Lab user-profile card | Long-term |

### Long-term expansions

| Name | Description and user value | Owner area | Reuse and architecture fit | Hidden dependencies and required gates | Risk | Suggested documentation home | Timing |
|---|---|---|---|---|---|---|---|
| **Owner-facing control center** | An eventual Discord-first control center joins setup progress, server-care checklist, health, audit timelines, policy explainers, and Help routes into a coherent owner journey. | Server management / Help / diagnostics | Compose existing panels and read models; it is an evolution of the approved unified hub, not a second router/dashboard. | Information architecture, permission/redaction, Discord limits, and avoiding duplicated facts. Gate: server-management hub plus shared explanation/read systems mature. | High | Extend Ideas Lab website/control-center themes after review | Long-term |
| **Website companion dashboard** | A later web companion offers dense read views and carefully approved configuration flows while Discord remains the primary interaction surface. | Platform / operator UX | Must reuse the same services, authority, audit, and read models; no web-only ownership path. | Authentication, session security, CSRF, hosting, privacy, parity, rate limiting, rollback, and operational burden. Gate: Discord panels/read models mature and dedicated security architecture is approved. | High | Extend Ideas Lab web-dashboard item | Long-term |
| **AI-assisted admin advisor — explanations only** | AI summarizes deterministic diagnostics, policy consequences, setup gaps, and audit history, then links to manual panels; it does not perform actions. Helps owners understand complex state. | AI / diagnostics / server management | Reuse approved orchestration choke point and deterministic read models; explanations are downstream of facts. | Production live verification, cost/budgets, redaction, prompt-injection defense, grounding, source freshness, and denial explanations. Gate: all AI-readiness/orchestration gates clear; no write/action tools. | High | Extend Ideas Lab AI decision/setup-advisor items and AI backlog | After AI-readiness |
| **BTD6 strategy workspace** | A future workspace combines source-grounded facts, calculators, saved comparison views, media references, and answerability/freshness cues. Gives players a trustworthy planning surface. | BTD6 / media | Reuse BTD6 provider/provenance, derived-value guards, existing browsers/calculators, and shared media subsystem. | ADR-006 implementation, provider parity, cache/source health, data licensing, freshness, save-model ownership, and groundedness. Gate: BTD6 provenance and global AI/BTD6 gates clear; no new extraction here. | High | Extend Ideas Lab BTD6 strategy-workspace item | After BTD6 provenance |
| **Media/video reference library** | Curated, provenance-aware video references support Help, games, BTD6, and community learning without pretending provider content is bot-owned truth. | Media / YouTube | Reuse ADR-007 fetch/cache/context/render seams and downstream links. | Consent, moderation, transcript safety, retention, credentials, freshness, provider failures, and copyright/policy review. Gate: media cache/privacy/source-health behavior verified. | High | Extend Ideas Lab shared-media item / media folio Ideas | Long-term |
| **Privacy-bounded server insights** | Owners see trends such as feature adoption, setup completion, moderation workload, and health history using aggregate, explainable metrics. Helps prioritize server care. | Diagnostics / analytics | Reuse audited events, task metrics, and read projections; no covert tracking or duplicate event pipeline. | Privacy policy, consent, retention, aggregation thresholds, deletion, metric definitions, and cost. Gate: event taxonomy/timeline and privacy review mature. | High | Extend Ideas Lab server-insights item | Long-term |

### Experimental / maybe-later ideas

| Name | Description and user value | Owner area | Reuse and architecture fit | Hidden dependencies and required gates | Risk | Suggested documentation home | Timing |
|---|---|---|---|---|---|---|---|
| **Feature maturity labels** | Help and owner diagnostics distinguish stable, degraded, gated, experimental, and unavailable features based on authoritative readiness facts. Sets honest expectations. | Help / diagnostics | Project current readiness/config facts; labels do not become a competing status ledger. | One-fact-one-home enforcement, stale-label tests, and clear ownership for each label. Gate: define authoritative machine-readable inputs first. | Medium | This backlog | After current roadmap |
| **Cross-server personal profile view** | With explicit consent, a user can see selected personal achievements/preferences across guilds without exposing guild-private activity. Adds continuity for normal users. | User profile / privacy | Compose domain-owned user reads and preference controls; no cross-guild admin data. | Consent, data minimization, deletion/export, guild policy, abuse, and identity scope. Gate: user preference/profile read model and privacy decision first. | High | New dedicated concept summary only after privacy review | Long-term |
| **Operator release/change digest** | A Discord panel summarizes shipped changes, affected subsystems, migrations, and operator checks from a maintained release manifest. Makes upgrades understandable. | Bot operator / diagnostics | Extend Ideas Lab operator changelog and existing docs/smoke surfaces; read-only. | Reliable release manifest ownership, version detection, migration mapping, and stale-content prevention. Gate: release metadata source approved. | Medium | Extend Ideas Lab operator-changelog item | Long-term |
| **Guided smoke-test surfaces** | Operator-facing cards show available smoke checks, prerequisites, last manual verification, and links; automation remains opt-in and bounded. Improves operational confidence. | Health / diagnostics / testing | Extend existing smoke checklist, task outcomes, and readiness cards; no second test runner by default. | Secrets/test-guild safety, destructive-action prevention, false confidence, and retention. Gate: smoke ownership and environments explicitly defined. | High | Extend Ideas Lab smoke-runner/status items | Long-term |
| **BTD6 answer cache (resolved-entity keyed)** | Cache bot answers to cut AI/API cost — but key on `(resolved_entity_id, query_type, params, data_version)`, **never** question text (text keys reintroduce keyword-fragility and risk serving stale numbers); cache **only provenance-stamped tool results**, never fallback/generated answers; **invalidate on every data-version bump** (flush on BTD6 ingest). | BTD6 / AI / cost | Reuse the entity resolver, provenance stamping, and the ingest version marker; sit behind the answerability read model. | Cache-key design (above), stale-answer prevention, never caching ungrounded answers, and ingest-triggered invalidation. Gate: BTD6 provenance + answerability complete. | Medium | This backlog (owner design constraint, Q-0132) | After BTD6 provenance |

## Cross-cutting abstractions worth preserving

These are **preservation targets**, not automatic new systems:

1. **Existing panel/action metadata and route registry** — enrich canonical Help/panel
   metadata before inventing a registry. It can support action-language, route labels,
   next-action hints, and discovery.
2. **Workflow recovery/resume pattern** — reuse anchors and durable configuration
   reads; never reinterpret it as game checkpointing.
3. **Audit/event timeline read projection** — unify presentation over existing
   domain-owned events without replacing write/audit owners.
4. **Existing notification/scheduler ownership** — subscriptions and digests must
   extend these seams rather than create a second delivery subsystem.
5. **Server automation recipe model** — if ever approved, it must be a bounded
   catalogue over service-owned actions, capability checks, previews, audit, and
   observability; never arbitrary scripting or AI actions.
6. **Diagnostics/readiness cards** — extend typed health contracts and
   `ReadinessSnapshot`, including evidence time, degraded reason, and next check.
7. **Capability explanation layer** — presentation over the canonical authority and
   governance resolvers, never another simulator.
8. **Guild template/provisioning model** — preserve catalogue → preview → confirmed
   apply → audit and lifecycle ownership.
9. **User profile/preference read model** — compose reads while each domain retains
   mutation ownership and privacy rules remain explicit.
10. **Help/search/discovery index** — build from canonical command/panel metadata and
    capability/readiness facts, not a parallel route tree.
11. **AI explanation and policy-read model** — deterministic facts first, grounded AI
    explanation second, and no action path.

## Ideas to avoid for now

- Do not implement any item in this document directly; none passed the ideas-to-plan
  promotion path.
- Do not create a second server-management hub, Help router, panel framework,
  governance simulator, readiness dashboard, audit write pipeline, notification
  subsystem, or generic helper collection.
- Do not let the owner-facing control-center concept distract from the approved
  server-management tracker or broaden current setup/hub work.
- Do not pursue AI actions, AI-authored policy writes, or an autonomous admin agent.
  The explanation-only advisor remains gated too.
- Do not resume BTD6 extraction/mapping or treat the strategy workspace as a reason to
  bypass provenance, provider parity, source health, or groundedness gates.
- Do not pursue Redis, cross-process state, restart-safe game sessions, or workflow
  recovery designs that silently become game checkpointing.
- Do not build arbitrary automation scripts. A future recipe model would require a
  curated action catalogue, deterministic authority, audit, observability, rollback,
  and a dedicated architecture decision.
- Do not start the website dashboard before Discord-native panels, read models,
  authority, and audits are coherent enough to reuse.
- Do not create cross-server profiles or analytics before explicit privacy,
  consent, retention, deletion/export, and aggregation decisions.
- Do not treat stale UI/helper/status inventories as current backlogs or use them to
  justify broad sweeps.

## Recommended documentation approach

Preserve this report as the broad capture document
`docs/ideas/future-product-direction-2026-06-07.md`. Keep it linked from
`docs/ideas/README.md`; do not append its full catalog to the Ideas Lab because that
would blur the Ideas Lab's binding decisions with a newer broad backlog.

If a cluster is reviewed later, create a short concept summary that links back here
and records ownership, reuse verification, privacy/security/cost/moderation review,
migration/cache/test/rollback mechanics, and the exact cleared gate. Do not update an
active tracker or `docs/current-state.md` until a candidate is actually promoted.
Subsystem folios may link to reviewed cluster summaries, but should not copy catalog
rows or current-state facts.

Suggested future concept-summary header and outline:

```markdown
# <Concept> — reviewed concept summary

> **Status:** reviewed concept; not an approved implementation plan
> **Source idea:** docs/ideas/future-product-direction-2026-06-07.md
> **Owner:** <canonical owner area>
> **Gate:** <specific prerequisite and evidence>

## User problem and non-goals
## Existing seams to reuse
## Ownership and authority
## Privacy, security, cost, and moderation review
## Migration, cache, test, observability, and rollback mechanics
## Promotion decision
```

## Top 10 preserved ideas

Ranked for long-term value, architectural fit, user value, readiness after current
roadmaps, and low risk of creating parallel systems:

1. **Capability explanation layer** — turns existing authority into understandable,
   reusable answers without becoming another simulator.
2. **Diagnostics/readiness card contract** — gives every subsystem a coherent,
   evidence-based operator language while preserving `ReadinessSnapshot`.
3. **Server-care checklist** — connects shipped and active server-management reads
   into a clear owner journey after that roadmap matures.
4. **Moderation policy explainer** — a low-risk, high-value read surface over the
   configuration already converging in PR10.
5. **Help/search/discovery index** — advances the “anything bot” direction while
   preserving slash-as-front-door and existing panels.
6. **Policy consequence preview** — prevents configuration mistakes by extending
   established read/preview seams.
7. **Unified audit/event timeline read service** — high long-term value across
   moderation, lifecycle, setup, economy, and automation if privacy/retention are
   solved.
8. **Workflow recovery/resume contract** — improves setup and panel reliability
   without violating ADR-002 or adding external state.
9. **Guild template/provisioning model** — powerful reusable setup direction once
   server-management and lifecycle foundations mature.
10. **AI-assisted admin advisor — explanations only** — a compelling eventual use of
    deterministic diagnostics and policy reads, kept safely behind AI-readiness.

## Follow-up handoff prompt

```text
You are working in the SuperBot Decisions project. Review
`docs/ideas/future-product-direction-2026-06-07.md` as a capture-only backlog and
decide whether any ideas should become reviewed roadmap candidates.

First verify source, merged PRs, live open PRs, `docs/current-state.md`, the relevant
subsystem folios, `docs/ideas/README.md`, and the binding Ideas Lab §2 and §6. Do not
treat rankings or timing labels as approval. Keep server-management as the active
approved lane unless current repo state proves otherwise; keep AI and BTD6 expansion
gated unless their documented gates have verifiably cleared.

For at most three candidates, produce a decision record that states: user problem,
canonical owner, existing seams reused, duplicate-system check, privacy/security/
cost/moderation risks, migration/cache/test/observability/rollback mechanics,
prerequisites with evidence, non-goals, and promote/defer/reject verdict. Rejected or
deferred candidates must remain ideas; promoted candidates may move only to a
reviewed concept summary, not directly to implementation or an active tracker.
```

## Verification checklist

- [x] No Ideas Lab rejection-ledger item is reintroduced as a normal candidate.
- [x] No idea is framed as approved implementation or as a PR sequence.
- [x] Every catalog entry names an owner area.
- [x] Every catalog entry names hidden dependencies and a required gate.
- [x] Every catalog entry identifies existing architecture to reuse.
- [x] Existing Ideas Lab, command, AI, and mining backlog concepts are extended rather
  than silently duplicated.
- [x] Placement follows `docs/ideas/README.md`: broad capture in `docs/ideas/`, with no
  active planning tracker or current-state rewrite.
- [x] Current roadmap work is not displaced; server-management remains the active
  approved lane.
- [x] AI and BTD6 expansion remain explicitly gated.
- [x] Architecture boundaries remain explicit: thin cogs, service-owned mutations,
  centralized helpers, deterministic flows, correct authority seams, auditability,
  observability, testability, and rollback safety.


## Routing update — 2026-06-08

Its catalog is consolidated by cluster in [`../planning/idea-roadmap-inventory-2026-06-08.md`](../planning/idea-roadmap-inventory-2026-06-08.md). Existing-plan, blocked, rejected, and new-roadmap outcomes are explicit there; this source-aware capture remains canonical historical input, not an implementation queue.
