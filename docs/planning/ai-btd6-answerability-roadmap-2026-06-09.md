# AI Cog Completion + BTD6 Answerability Roadmap

> **Status:** `plan` — implementation-ready mapping, not implementation approval.
> **Prepared:** 2026-06-09.
> **Area authorities:** [`../subsystems/ai.md`](../subsystems/ai.md),
> [`../subsystems/btd6.md`](../subsystems/btd6.md), and
> [`../subsystems/settings-bindings-provisioning.md`](../subsystems/settings-bindings-provisioning.md).
> **Active gate:** all *AI-exposure* phases remain blocked by the AI/BTD6 feature-expansion
> gate in [`../current-state.md`](../current-state.md) and, for net-new tools, the
> approved sequencing requirement to lock the orchestration foundation first.
> **Progress:** **Phase 1A + 1B shipped 2026-06-09.** 1A: `btd6_data_service.round_cash()`,
> the deterministic owner-calculated round / inclusive-range cash query. 1B: the read-only
> **`btd6_round_cash` AI tool** (registered in the existing `ai_tools.build_registry` — *not*
> a parallel registry — per this plan's fallback), added to the BTD6 grounding allowlist, with
> the instruction stack updated to defer to it. **The maintainer explicitly lifted the AR-10
> orchestration-first sequencing for this one read-only BTD6 tool** (it composes no workflow
> and adds no parallel registry). **Owner decision Q-0043 (2026-06-09): range cash is
> INCLUSIVE of both endpoints** (r50→r60 = $19,840), resolving a conflict where the prior
> instruction stack/smoke checklist used the exclusive `cumulative(B) − cumulative(A)`.
> **Phase 2 shipped 2026-06-09** (this session): the read-only `services/ai_introspection_service.py`
> composition read model (tool catalogue + BTD6 answerability + audience-filtered AI settings +
> policy/decision explanation) — no AI exposure, no UI. **Next: Phase 3** (the self-awareness
> tools that *expose* Phase 2 — gated). (PRs reconciled 2026-06-09: Phase 1A/1B = **#612**, Phase 2 = **#616**.)

## 1. Purpose and owner intent

This roadmap completes the **AI answerability and self-awareness bridge**, using BTD6
as the first deterministic proof path. The product outcome is not merely that SuperBot
*stores* a fact. The AI must reliably discover the owning service, select the right
read-only tool or context packet, apply deterministic semantics, explain the result,
and explain failures or non-replies without fabricating internal causes.

Target questions include:

- “What BTD6 data do you know?”
- “Can you answer cash from round 50 to 60?”
- “Why did you say you didn’t have verified data?”
- “What commands/settings/tools are available here?”
- “Why didn’t you reply in this channel?”
- “Which AI settings affect this channel?”

This is **not** a broad BTD6 extraction pass. Source verification confirms that standard
round cash is already deterministic repo data. The first proof slice closes or hardens
the route from that known data to a faithful chat answer.

### 1.1 Truth and planning posture

- Confirmed facts below come from source, tests, binding docs, or merged-history visible
  in the local checkout. Assumptions and decisions still needing review are labelled.
- Source and merged PRs win over docs; binding docs win over living ledgers and old plans.
- The local environment had no `gh` executable and no configured Git remote, so live open
  PR state could not be verified in this planning session. Re-check live GitHub before
  beginning any implementation slice.
- Existing owner decisions already set the safe posture: orchestration foundation before
  net-new tools, tiered read visibility, and explanation-only/read-only AI. No new owner
  question is required to write this roadmap.

## 2. Current-state map

### 2.1 Current natural-language AI path

Confirmed path:

```text
Discord message
  → core message pipeline
  → AINaturalLanguageStage.process
  → ai_natural_language_policy.resolve (reply admission + effective policy)
  → ai_task_router.classify
  → ai_context_service build/request context
  → feature facts (BTD6 → btd6_context_service.build)
  → intent-gated bot knowledge blocks (bot_knowledge_service; BTD6 knowledge blocks)
  → ai_instruction_service.assemble
  → ai_tools.build_registry (scope-filtered read-only specs/handlers, when enabled)
  → ai_gateway.execute / provider tool loop
  → BTD6 faithfulness verification against feature facts + approved tool-result ledger
  → regenerate once, deterministic BTD6 floor/refusal, or answer/send
  → ai_decision_audit_service.record
```

Important current properties:

- `natural_language_stage.py` is the single passive responder and records one audit row
  for every path.
- Reply admission and explanation scope are separate: policy resolution decides whether
  the bot replies; `_derive_scope` decides which read-only tools may be offered.
- BTD6 tool results only join the faithfulness ledger when the tool name is in
  `ai_tools.BTD6_GROUNDING_TOOL_NAMES`.
- When a BTD6 response cannot be grounded, the stage can regenerate once and then emit a
  deterministic version-stamped refusal/floor.
- The instruction stack explicitly says per-round cash exists and describes range cash
  as endpoint cumulative subtraction.

### 2.2 Current BTD6 answer path

Confirmed path:

```text
BTD6-classified natural-language question
  → btd6_context_service.build
  → btd6_resolver_service.resolve (entities and explicit round numbers)
  → btd6_data_service typed dataset + other domain-owned BTD6 services
  → bounded, sourced grounding facts
  → instruction stack / provider
  ↘ optional btd6_* tools from ai_tools.build_registry
     → deterministic BTD6 owner service
     → approved tool-result faithfulness ledger
  → btd6_grounding_service verification
  → answer, correction retry, or deterministic refusal
```

Confirmed round-cash state:

- `RoundEntry` stores `cash` and `cumulative_cash` as optional floats.
- `rounds.json` contains those values for standard rounds 1–140.
- `test_btd6_round_cash.py` recomputes every round’s cash from composition and verifies
  the cumulative running total from Medium’s starting cash.
- `btd6_context_service._render_fixture_round` surfaces rounded per-round and cumulative
  cash for resolver-matched rounds.
- The resolver recognizes explicit round numbers. A query containing both range endpoints
  can therefore ground both endpoint records.
- `ai_instruction_service` teaches the model to answer a range using cumulative(B) minus
  cumulative(A).
- `btd6_round_composition` is an existing direct AI tool for composition/RBE ranges, but
  there is **no dedicated round-cash tool or deterministic round-cash-range service API**.
- The BTD6 smoke checklist already expects a correct answer for “how much do you earn from
  r50 to r60,” but there is no targeted unit test pinning the complete NL/tool/faithfulness
  range-answer path.

Conclusion: round cash is an **answerability/reliability gap**, not a missing-data gap.
The present path asks the model to perform endpoint subtraction from context facts. That
can work, but it is less robust and less directly auditable than returning the derived
range total from the deterministic owner.

### 2.3 Current bot self-awareness path

```text
Meta-question heuristics
  → bot_knowledge_service.gather
     → always-on caller standing block
     → intent-gated command catalog from core.runtime.command_descriptions
     → intent-gated recent non-reply audit summary from ai_decision_audit_service
  → ai_instruction_service bot_* data blocks
  → model explanation
```

Adjacent read models and owners already present:

- `bot_knowledge_service` can answer bounded command/help questions and “why didn’t you
  reply?” questions. It does not currently expose the AI tool catalog or AI settings.
- `ai_config_projection_service.build_snapshot` already composes guild policy, channel
  override count, memory, provider, projected settings drift, instruction profile,
  readiness/diagnostics, and recent audit summary. It is the strongest existing base for
  settings introspection, but it is guild-level and not a complete effective-channel
  explanation model.
- `ai_natural_language_policy.resolve(..., dry_run=True)` provides a precedence trace for
  explaining effective guild/category/channel/role policy without side effects.
- `ai_decision_audit_service` owns bounded decision records and queries. Audit rows can
  explain many non-replies, but an explanation must distinguish “no visible/recent row”
  from a proved internal cause.
- `ai_tools.build_registry` is the runtime source of scope-filtered tool availability.
  The existing orchestration plan separately calls for a canonical tool catalogue; do not
  create a competing registry in this lane.
- Command metadata comes from the existing command description/surface owners; do not
  create a second command registry.

### 2.4 Current settings and UI foundation

Confirmed foundation:

- Settings have existing registry/resolution/mutation owners and shared selector helpers.
- `disbot/views/navigation.py` and `disbot/views/selectors/` provide shared navigation and
  channel/role/scope/subsystem selectors.
- AI has typed guild/category/channel/role policy tables plus projection/mutation services.
- The settings/customization docs require selectors for bounded choices and text modals
  only for genuine free text.

Readiness caveat: the current AI configuration read model spans typed AI policy, legacy
projected settings, memory settings, provider runtime state, instruction profiles, and
channel/category/role policy rows. An AI-only settings page is feasible only after its
read/write ownership and effective-channel projection are explicit; a broad Settings
Manager rewrite is neither needed nor allowed here.

## 3. Confirmed answerability gaps

### 3.1 Critical blockers

| Gap | Confirmed evidence | Why it blocks | Planned response |
|---|---|---|---|
| Runtime implementation is gated | `current-state.md`, AI folio, and roadmap require the AI/BTD6 expansion gate and orchestration foundation before net-new tools | Starting tools/UI now would silently promote gated work | Keep every runtime phase gated; a maintainer must explicitly activate an accepted slice |
| No canonical introspection read model | Tool availability, effective policy, config projection, audit, BTD6 coverage, and command knowledge live behind separate owners | Local patches would disagree about what the bot “knows” or why it acted | Add one read-only composition service after the orchestration catalogue contract is accepted |
| No deterministic range-cash result API/tool | Cash exists and named rounds ground, but range arithmetic is delegated to the model | Correct data can still yield refusal, arithmetic drift, or weak evidence | Add a BTD6-owned inclusive-range query and expose it through the accepted orchestration/tool seam |

### 3.2 Important improvements

| Gap | Confirmed evidence | Effect |
|---|---|---|
| Range context is endpoint-based rather than intent-shaped | Resolver extracts explicit numbers; context renders each matched round independently | It does not return an explicit “range total” fact or semantic warning packet |
| No targeted round-cash tool | Registry contains `btd6_round_composition`, not round cash | The model must infer that context facts—not a tool—own this answer |
| Settings introspection is not channel-effective | Projection snapshot is rich but primarily guild-level; policy dry-run has the effective precedence trace | “Which settings affect this channel?” requires composition and redaction rules |
| Tool-catalog self-awareness is absent | Runtime registry exists; bot knowledge only handles commands and audit | “What tools are available here?” cannot be answered authoritatively today |
| BTD6 answerability inventory is prose-fragmented | Data fixtures, services, tool specs, context renderers, coverage docs, and smoke checks are separate | “What BTD6 data do you know?” risks overclaiming or omitting known domains |
| Failure explanation is incomplete | Audit can explain decisions; grounding failure can trigger refusal; no joined explanation model exists | “Why did you say no verified data?” cannot reliably name whether retrieval, tool choice, grounding, provider, or coverage was the limiting step |

### 3.3 Cleanup

- Align stale folio wording that still says extraction is paused with the implemented
  ADR-006 provenance schema when those folios are next maintained; this roadmap follows
  `current-state.md` and source.
- Keep tool names, descriptions, scope, grounding allowlist membership, and dashboard
  exposure derived from one accepted catalogue rather than parallel lists.
- Add explicit reason-schema documentation for user-safe policy/grounding explanations.

### 3.4 Future opportunities

- Generated answerability dashboards for more domains and provider/live-source health.
- Admin-facing “test this channel’s AI policy” previews using policy dry-run.
- Answerability regression evals across paraphrases after deterministic unit coverage.
- User-visible answerability summaries split from admin-only diagnostics.

These opportunities do not justify broad data extraction or action-capable AI.

## 4. Proposed implementation phases and PR-sized slices

### Phase 0 — Gate confirmation and orchestration alignment (required before runtime work)

**Objective:** confirm the AI/BTD6 expansion gate is explicitly lifted for the selected
slice and align the work with the accepted canonical tool catalogue/orchestration
foundation.

**PR shape:** decision/plan activation only, or part of the already-approved orchestration
foundation PR; no isolated net-new tool PR before this completes.

**Acceptance:** the implementation prompt names the approved slice, scope, audience, and
catalogue seam. **Stop:** any gate remains unresolved or live open work conflicts.

### Phase 1 — Deterministic BTD6 round-cash answerability

Split into two small PRs if orchestration/catalogue work and BTD6 semantics cannot land
coherently in one review.

#### Phase 1A — BTD6-owned range semantics

> **✅ SHIPPED 2026-06-09 (this session).** Implemented as
> `btd6_data_service.round_cash(round_start, round_end=None)` — a pure, read-only
> sibling of `round_composition` / `cumulative_upgrade_costs` (kept in
> `btd6_data_service`; the service has no LOC ceiling and this is the deterministic
> BTD6 fact owner). It returns the structured result below and **owner-calculates the
> inclusive range total** (`range_cash`) plus the cumulative endpoints so the
> `cumulative(B) − cumulative(A−1)` identity is explicit. Every row of the semantics
> table is pinned by tests in `tests/unit/services/test_btd6_round_cash.py` (single
> round, inclusive both-endpoints, reversed→normalized, invalid→`invalid_range`,
> partial-overlap→`cash_unavailable`, cumulative identity, full-range detail cap, and
> disclosed economy assumptions). No AI tool, context, or UI change was made — that is
> Phase 1B, which stays gated. (Shipped in **#612**.)

Add a deterministic, read-only query in `btd6_data_service` (or a narrowly named
BTD6-owned sibling only if service size/ownership requires it) that returns:

- normalized inclusive `round_start` / `round_end`;
- per-round cash for a single-round request;
- inclusive range cash calculated by the owner, not the model;
- cumulative cash through an endpoint;
- roundset and economy assumptions;
- structured unsupported/invalid reason codes.

Expected semantics to pin:

| Request | Expected deterministic behavior |
|---|---|
| Single standard round | Return that round’s cash and cumulative cash |
| Inclusive range A–B | Return normalized endpoints and owner-calculated inclusive range total |
| Reversed range B–A | Normalize and explicitly report normalization |
| Invalid/out-of-range round | Return `found=false`/structured invalid-range reason; valid standard range is 1–140 |
| “Cumulative after/by round N” | Return cumulative through N, explicitly including the Medium starting-cash baseline |
| ABR/alternate round set | Return unsupported until an owned alternate-round dataset exists; never reuse standard numbers silently |
| Double Cash / Half Cash / difficulty wording | Do not extrapolate in the first slice; return an explicit unsupported-assumption note unless verified service semantics are added later |

Recommendation: make the deterministic owner return exact stored/derived floats and
separate display formatting from calculation. Do not parse JSON above the data service.

#### Phase 1B — AI exposure, grounding, and end-to-end reliability

> **✅ SHIPPED 2026-06-09 (this session), with the maintainer explicitly lifting AR-10 for
> this one read-only tool.** Delivered: the **`btd6_round_cash`** AI tool (read-only,
> `min_scope=USER`) registered in the existing `ai_tools.build_registry` (no parallel
> registry); added to `ai_tools.BTD6_GROUNDING_TOOL_NAMES` so its results join the
> faithfulness ledger (the subset drift-guard keeps allowlist↔registry in lockstep); the
> instruction stack (`ai_instruction_service`) now defers range-cash to the tool and teaches
> the **inclusive** formula `cumulative(B) − cumulative(A−1)` (owner decision **Q-0043**);
> tool-registry/handler tests added; the smoke-test checklist updated to the inclusive
> numbers. The existing faithfulness retry/floor choke point is untouched (preserved). The
> intent-shaped context packet (below) was **not** needed — the direct tool gives reliable
> selection and is the more auditable path (§5.7); single-round cash already renders in
> `_render_fixture_round`. (Shipped in **#612**.)

- Register the accepted read-only round-cash tool through the canonical orchestration
  catalogue/compatibility seam; if that foundation still uses `ai_tools.build_registry`,
  add it there without creating a parallel registry.
- Add the tool name to the BTD6 grounding allowlist by derivation or explicit invariant.
- Improve context intent handling so range/cumulative/unsupported-modifier questions emit
  an intent-shaped grounding packet or reliably select the direct tool.
- Preserve the existing faithfulness retry/floor choke point.
- Add targeted deterministic, tool-registry, context, grounding, natural-language-stage,
  and smoke/eval coverage.

Recommended name: **`btd6_round_cash`**, not `btd6_round_cash_apply`. Existing BTD6 tools
are read queries and use `btd6_*` nouns/actions without an `apply` suffix; “apply” implies
mutation and conflicts with this lane’s read-only boundary.

### Phase 2 — Central AI introspection read model

> **✅ SHIPPED 2026-06-09 (this session).** Implemented as the read-only
> `services/ai_introspection_service.py` — a side-effect-free composition over the existing
> owners, **no AI exposure and no UI** (those stay the gated Phase 3/4). It is the additive
> read-*model* layer that `current-state.md` flagged as unblocked once the canonical
> catalogue landed (#612); it mirrors the Phase 1A precedent (a deterministic owner shipped
> before its gated exposure). Four bounded, typed, audience-filtered builders:
> `build_tool_catalog(scope)` (joins `ai_tools.all_tool_specs` + `ai_tool_catalogue.CATALOGUE`;
> names higher-scope tools only as a count), `build_btd6_answerability()` (deterministic
> fixtures + calculations + the one live domain + explicit unsupported gaps, from
> `btd6_data_service`), `build_ai_settings_view(guild_id, scope)` (reuses
> `ai_config_projection_service.build_snapshot`, redacted by tier), and
> `build_policy_explanation(ctx, scope)` (composes `ai_natural_language_policy.resolve`
> dry-run trace + bounded `ai_decision_audit_service` history). **Audience filtering happens
> at construction** (roadmap §5.6 / AR-08): a USER sees only USER tools + enabled-flags + their
> own reply outcome; admin+ gains effective config, precedence traces, and cross-user audit;
> provider runtime diagnostics stay platform-owner-only. A small runtime-independent
> `ai_tools.all_tool_specs()` accessor was added (pinned == the catalogue) so the read model can
> report a tool's name/purpose/`min_scope` without standing up a live registry. 16 tests +
> a live smoke against the real catalogue/dataset/DB. **Not** built (still gated): the
> self-awareness tools that *expose* this (Phase 3) and any settings UI (Phase 4). Reconcile
> PR # next session.

Plan a read-only `ai_introspection_service` (name subject to architecture review; reuse an
existing equivalent if the orchestration foundation introduces one). It must compose,
not replace, current owners.

Bounded outputs:

1. **Tool catalog snapshot** — caller-scope-filtered descriptors from the accepted
   canonical catalogue/runtime registry; names, purpose, scope, read/write classification,
   and current availability reason.
2. **BTD6 answerability snapshot** — domain-level answerability assembled from generated
   inventory and runtime exposure owners; distinguish deterministic fixtures, live data,
   calculations, tools, context, renderers, and unsupported areas.
3. **AI settings/effective-config snapshot** — reuse `ai_config_projection_service`,
   settings resolution, and policy dry-run; identify guild/category/channel/role sources.
4. **Policy/recent-decision explanation** — user-safe reason code, precedence trace, and
   recent relevant audit record; never expose hidden channels or sensitive diagnostics.
5. **Command catalog adapter** — reuse `bot_knowledge_service`/command metadata only if the
   central model needs one common response shape; never own a new command registry.

The service should expose typed/frozen read models, explicit audience filtering, bounded
counts/text, and safe degraded states. It must not mutate settings or policy.

### Phase 3 — Self-awareness tools and intent-gated knowledge blocks

After Phase 2 and the orchestration foundation, expose scope-filtered read-only tools.
Candidate names follow the existing general-tool `get_*` convention, but final names must
come from the accepted catalogue:

- `get_ai_tool_catalog`
- `get_ai_settings_snapshot`
- `get_ai_policy_explanation`
- `get_btd6_answerability_snapshot`

Recommended audience split:

- Normal users: public/read-only command and BTD6 capability summary; public tools they
  can actually access; no hidden admin settings or channel metadata.
- Admin/server owner: effective-channel AI settings, policy trace, and bounded relevant
  audit explanation.
- Platform owner: already-authorized provider/readiness/diagnostic detail only.

Add intent-gated `bot_knowledge_service` blocks for tool/settings/policy/answerability
questions so every normal turn does not pay the prompt cost. Keep identity always-on and
preserve current command/audit blocks.

Grounding-failure explanation must be bounded and factual. It may say, for example, that
no matching deterministic fact reached the answer, a selected tool returned unsupported,
or the faithfulness verifier rejected unsupported names/numbers. It must not speculate
about deployment, sync, indexes, provider internals, or data absence without evidence.

### Phase 4 — AI settings UI vertical slice (conditional)

Do **not** start until Phase 2 supplies a stable effective-settings read model and existing
settings mutation seams can own every displayed action. This phase is one AI page, not a
Settings Manager rewrite.

Recommended components:

- String/select menus for bounded enum/list settings such as provider/mode/profile.
- Shared channel selector for channel policy.
- Modals only for genuine free-text instruction/profile content.
- Buttons for reset/inherit, deterministic preview/test, and explain.
- Read-only effective-value/source display before mutation.
- Existing permission checks, previews, confirmations, mutation services, and audit for
  every change; the AI itself remains unable to mutate settings.

Potential homes must be verified against the accepted Settings Manager route at build
time; reuse `disbot/views/navigation.py`, `disbot/views/selectors/`, AI policy mutation,
and settings resolution/registry owners. **Stop:** if an action would require a duplicate
settings registry, direct DB write, new navigation system, or broad settings rewrite.

### Phase 5 — Generated BTD6 answerability dashboard

Create a generator only after the catalogue/answerability ownership schema is accepted.
Recommended outputs:

- machine-readable JSON as the canonical generated artifact;
- `docs/btd6/generated/btd6-answerability-dashboard.md` rendered from that JSON;
- a generator such as `scripts/generate_btd6_answerability_dashboard.py`.

Recommended columns:

`domain`, `fixture_count`, `source/provenance`, `game_version/freshness`, `parser status`,
`deterministic service`, `AI tool exposure`, `context exposure`, `renderer/UI exposure`,
`apply support`, `scope`, and `known gaps`.

Confirmed local deterministic fixture domains to include now: towers, tower stats, heroes,
rounds, bloons, maps, modes/difficulties/modifiers, powers, Monkey Knowledge, Geraldo
items, bosses, CT relics, paragon abilities/descriptions. Confirmed live/service domains
should be inventoried separately (for example live events and CT team status) because a
fixture count does not describe their freshness/coverage.

Candidate/deferred domains must be displayed as unsupported or not inventoried—not
implied present: achievements, alternate round sets/ABR browser, Rogue/Frontier, and any
other domain without a verified owner/data path. The generator must inspect canonical
services/catalogues/manifests, not scrape prose as its source of truth.

## 5. Options and tradeoffs

### 5.1 Round cash: direct tool, context grounding, or both

| Option | Recommendation | Why / risk | Implementation impact |
|---|---|---|---|
| Direct tool only | Not preferred alone | Strong deterministic arithmetic, but a provider may fail to select it and pre-grounded answers lose a reliable fallback | Data service, catalogue/tool registry, grounding allowlist, tool tests |
| Context only | Not preferred alone | Existing path already works for explicit endpoints, but delegates subtraction/semantics to the model | Context/resolver/instruction tests; continued arithmetic/refusal risk |
| **Both, sharing one BTD6-owned query** | **Recommended** | Tool gives explicit derived result; intent-shaped context gives robust grounding/fallback. Risk is duplicate rendering if outputs diverge, mitigated by one owner result model | Data service + context adapter + catalogue/tool + grounding + NL tests |

### 5.2 Tool name: `btd6_round_cash` vs `btd6_round_cash_apply`

**Recommendation:** `btd6_round_cash`. It matches existing read-only BTD6 naming and does
not imply mutation. Risk is low; finalize through the canonical catalogue to avoid a later
rename. Likely files: orchestration catalogue/`ai_tools.py`, BTD6 service, tool tests/docs.

### 5.3 One introspection service vs local patches

**Recommendation:** one read-only composition service over existing owners. Local patches
would be faster for one question but create contradictory settings/tool/policy snapshots
and duplicate redaction. Risk: a “god service.” Mitigate with typed adapters, bounded
sub-builders, no persistence, and strict dependency direction. Likely files:
`services/ai_introspection_service.py` or accepted equivalent, existing owner adapters,
focused unit tests, bot knowledge/tool registration.

### 5.4 Dashboard: Markdown only vs JSON + Markdown

**Recommendation:** JSON + generated Markdown. JSON supports tests, future diagnostics,
and diffing; Markdown remains human-readable. Risk: schema/generator maintenance. Mitigate
with a small versioned schema and deterministic generation check. Likely files: generator,
generated artifacts, docs tests, BTD6 README/folio.

### 5.5 AI settings UI now vs after foundation

**Recommendation:** wait for Phase 2’s effective-settings read model and confirm the
existing settings UI route before implementation. Building now risks reproducing the
fragmentation the UI is meant to explain. Impact when ready: one AI page plus shared
selectors/navigation and existing mutation owners; no manager rewrite.

### 5.6 Answerability visibility: public, admin-only, or split

**Recommendation:** split by scope. Public users may see public capabilities and tools
available to them; admins may see effective channel policy/settings and relevant audit
reasons; platform diagnostics remain owner-scoped. Risk is accidental metadata leakage;
mitigate by filtering at read-model construction, not prompt wording alone.

### 5.7 Range semantics: model subtraction vs deterministic service result

**Recommendation:** deterministic service result. The model may explain the formula, but
must not own the arithmetic. This mirrors the shipped cumulative-cost pattern and makes
the audit/tool evidence explicit. Risk is semantic ambiguity around “from A to B”; pin
inclusive behavior and disclose it in the result.

## 6. Architecture boundaries

The implementation must preserve all of these boundaries:

- Deterministic BTD6 facts and derived round-cash semantics stay owned by
  `btd6_data_service`/the canonical BTD6 fact owner.
- AI tools remain read-only in this lane.
- AI may explain or propose settings, but it must not mutate them.
- Mutations continue through deterministic services, permission checks, previews,
  confirmations, and audit.
- No duplicate command registry; reuse command descriptions/surface owners.
- No duplicate settings registry; reuse settings registry/resolution and AI policy owners.
- No duplicate navigation/select helper system; reuse shared navigation/selectors.
- No direct JSON parsing in higher AI layers when a BTD6 service owns the data.
- No broad provider abstraction rewrite.
- No broad BTD6 extraction pass.
- No tower cutover unless separately accepted, ungated, and explicitly scoped.
- Preserve the central natural-language stage and faithfulness/grounding choke point.
- Absence or unsupported claims must be evidence-bounded; an unresolved lookup never
  proves data absence.
- Read-model audience filtering happens before data reaches the model.

## 7. Implementation-ready task breakdown

### Phase 0 task card — activate a safe lane

- **Objective:** verify gates/live work and approve the exact first slice.
- **Affected docs:** `docs/current-state.md`, AI/BTD6 folios, authoritative AI roadmap or
  accepted orchestration plan only if state/approval changes.
- **Reuse:** existing gate/decision owners.
- **Code/tests:** none.
- **Risk:** high product/sequencing risk, no runtime risk.
- **Dependencies:** live GitHub check; orchestration-foundation decision.
- **Rollback/safety:** docs-only activation can be reverted; no implicit approval.
- **Acceptance:** exact approved scope and stop conditions are recorded.
- **Stop conditions:** any gate unresolved; conflicting active PR; net-new tool catalogue
  seam not accepted.

### Phase 1 task card — round-cash answerability

- **Objective:** make standard round cash/ranges deterministic, selectable, grounded,
  explainable, and regression-pinned.
- **Likely affected source:** `disbot/services/btd6_data_service.py`,
  `disbot/services/btd6_context_service.py`, `disbot/services/ai_tools.py` or accepted
  catalogue equivalent, `disbot/services/ai_instruction_service.py` only if semantics need
  clarification, and the existing NL stage only if selection/ledger wiring requires it.
- **Owners to reuse:** `RoundEntry`/BTD6 dataset, BTD6 context/resolver, canonical tool
  catalogue, existing grounding ledger/verifier.
- **Expected changes:** typed round-cash result, direct read tool, intent-shaped context,
  allowlist/catalogue invariant, structured unsupported reasons.
- **Expected tests:** extend `test_btd6_round_cash.py`; tool registry/handler tests;
  context range/cumulative/modifier tests; grounding/NL-stage refusal and tool-ledger tests;
  smoke/eval paraphrases.
- **Docs:** BTD6 smoke checklist, generated dashboard when Phase 5 exists, folio/current
  state only when shipped.
- **Risk:** medium (faithfulness and semantic correctness); data mutation risk none.
- **Dependencies:** Phase 0 and accepted orchestration seam.
- **Rollback/safety:** additive read path; keep existing context fallback; feature/tool flag
  can suppress offering without deleting deterministic service semantics.
- **Acceptance:** all listed semantics are deterministic; range answers do not depend on
  model arithmetic; unsupported modifiers never receive fabricated numbers; grounding
  accepts the exact result and rejects unsupported names/numbers.
- **Stop:** implementing ABR/modifier math requires unverified data; change would bypass
  the grounding choke point; tool would be write-capable.

### Phase 2 task card — introspection read model

- **Objective:** one bounded, audience-filtered composition model for capabilities,
  settings, policy/audit explanations, and BTD6 answerability.
- **Likely affected source:** new accepted introspection service; adapters around
  `ai_tools`/canonical catalogue, `ai_config_projection_service.py`,
  `ai_natural_language_policy.py`, `ai_decision_audit_service.py`,
  `bot_knowledge_service.py`, command metadata, and BTD6 inventory owner.
- **Reuse:** all current source owners; no new persistence.
- **Expected changes:** typed snapshots, reason schema, redaction/scope filters, bounded
  degraded states.
- **Expected tests:** audience filtering, hidden-channel redaction, policy dry-run parity,
  projection reuse, audit absence semantics, catalogue parity, no writes.
- **Docs:** AI config ownership/integration map only if contracts change.
- **Risk:** high (cross-owner privacy/authority), runtime mutation risk none.
- **Dependencies:** Phase 0; accepted canonical catalogue; explicit audience rules.
- **Rollback/safety:** service is additive/read-only; callers can fall back to existing
  command/audit blocks.
- **Acceptance:** each field traces to one owner; public/admin/platform snapshots differ as
  intended; no query changes policy/cooldown/audit state.
- **Stop:** duplicate registry required; sensitive data cannot be filtered before prompt;
  effective-channel semantics remain ambiguous.

### Phase 3 task card — self-awareness exposure

- **Objective:** let the AI answer capability/settings/policy/failure questions from Phase
  2 without prompt bloat.
- **Likely affected source:** canonical tool catalogue/`ai_tools.py`,
  `bot_knowledge_service.py`, `ai_instruction_service.py`, NL-stage knowledge gathering,
  possibly task-router intent classification.
- **Reuse:** Phase 2 snapshots, existing scope derivation, bot knowledge blocks, tool loop.
- **Expected tests:** tool scope/parity, intent triggers and false positives, prompt bounds,
  safe failure explanations, no speculative internal claims.
- **Docs:** AI tool/guard maps and smoke checklist.
- **Risk:** medium-high (metadata leakage/prompt weight).
- **Dependencies:** Phases 0 and 2.
- **Rollback/safety:** remove tool/block exposure while retaining read model.
- **Acceptance:** target meta-questions receive scoped authoritative answers; ordinary
  turns do not receive large introspection blocks; all tools remain read-only.
- **Stop:** audience filtering depends on model compliance; prompt growth exceeds bounds;
  explanation would claim an unproved cause.

### Phase 4 task card — AI settings UI

- **Objective:** one deterministic AI settings/effective-policy page.
- **Likely affected source:** accepted settings manager route, AI-specific views, shared
  `views/navigation.py` and `views/selectors/`, AI config projection/policy mutation,
  settings resolution/registry.
- **Reuse:** shared components and mutation/audit owners.
- **Expected tests:** navigation, permission re-checks, selector/modal correctness,
  reset/inherit/preview/explain, mutation seam and audit parity.
- **Docs:** settings customization command map and live-surface docs.
- **Risk:** high (UI + settings authority).
- **Dependencies:** Phase 2; existing settings foundation confirmed ready.
- **Rollback/safety:** page can be removed without changing setting ownership; no direct
  writes.
- **Acceptance:** effective value/source is visible; all changes use owned mutation paths;
  AI itself cannot apply changes.
- **Stop:** broad manager rewrite, duplicate selector/navigation, or direct DB write needed.

### Phase 5 task card — generated answerability dashboard

- **Objective:** generate a truthful, diffable inventory of BTD6 answerability.
- **Likely affected files:** new generator, generated JSON/Markdown, BTD6 README/folio,
  docs/script tests.
- **Reuse:** fixture/data service, provenance/source registry, canonical tool catalogue,
  context/renderer registries where present.
- **Expected tests:** deterministic generation, schema validation, no stale diff, known
  domain anchors, unsupported-domain representation.
- **Docs:** generated dashboard links and regeneration instructions.
- **Risk:** medium (false confidence/staleness), runtime risk none.
- **Dependencies:** accepted inventory schema; preferably Phases 1–2/catalogue.
- **Rollback/safety:** generated artifacts are removable; never make dashboard prose the
  runtime source of truth.
- **Acceptance:** every row points to verified owners/status; regeneration is deterministic;
  unsupported domains are explicit.
- **Stop:** generator must infer state from prose or duplicate runtime registries.

## 8. Verification plan

Use the repo’s active Python environment. The documented `python3.10` commands may require
`PYENV_VERSION=3.10.20` in environments where that version is installed but not selected.

### 8.1 Every implementation PR

```bash
python3.10 scripts/check_quality.py --full
python3.10 scripts/check_architecture.py --mode strict
python3.10 scripts/check_docs.py --strict
```

### 8.2 Phase 1 targeted checks

```bash
python3.10 -m pytest tests/unit/services/test_btd6_round_cash.py
python3.10 -m pytest tests/unit/services/test_ai_tools.py
python3.10 -m pytest tests/unit/services/test_btd6_context_grounding.py
python3.10 -m pytest tests/unit/services/test_btd6_resolver_service.py
python3.10 -m pytest tests/unit/runtime/ai/test_natural_language_stage.py
DUMP=/tmp/btd6gd  # replace with the verified local BTD6 dump path
python3.10 scripts/parse_gamedata.py --dump "$DUMP" --validate-anchors
python3.10 scripts/parse_gamedata.py --dump "$DUMP" --audit
```

### 8.3 Phases 2–4 targeted checks

```bash
python3.10 -m pytest tests/unit/services/test_bot_knowledge_service.py
python3.10 -m pytest tests/unit/services/test_ai_config_projection_service.py
python3.10 -m pytest tests/unit/services/test_ai_decision_audit_service.py
python3.10 -m pytest tests/unit/services/test_ai_natural_language_policy.py tests/unit/services/test_ai_natural_language_policy_dry_run.py
python3.10 -m pytest tests/unit/runtime/ai/test_tool_calling.py tests/unit/runtime/ai/test_natural_language_stage.py
python3.10 -m pytest tests/unit/runtime/test_navigation_stack.py tests/unit/runtime/test_settings_registry.py
python3.10 -m pytest tests/unit/docs/test_settings_customization_doc.py tests/unit/docs/test_settings_manager_live_surface_doc.py
```

Add focused tests for the new introspection service, self-awareness tools, and AI settings
view rather than overloading unrelated files.

### 8.4 Phase 5 targeted checks

```bash
python3.10 scripts/generate_btd6_answerability_dashboard.py --check
python3.10 -m pytest tests/unit/scripts/test_generate_btd6_answerability_dashboard.py
python3.10 -m pytest tests/unit/scripts/test_check_docs.py tests/unit/docs/test_subsystem_folios_doc.py
```

The script/test names in Phase 5 are proposed and should be adjusted to the accepted repo
convention when implemented.

### 8.5 Live verification

Provider/tool selection cannot be fully proved in a provider-keyless sandbox. After all
deterministic and simulated-provider tests pass, run the target questions on the
maintainer bot and inspect bounded audit/tool traces. A live provider check supplements;
it never replaces deterministic tests.

## 9. Expected final user-facing behavior

The exact copy may evolve, but answers must have these shapes:

### “How much cash do I get from r50 to 60?”

- State that the range is inclusive and uses standard/Medium economy with no income
  towers.
- Return the deterministic range total and optionally the endpoint cumulative formula.
- State unsupported assumptions if the user asks for ABR, Half Cash, Double Cash, another
  difficulty, or farm income.
- Never estimate or perform ungrounded arithmetic in prose.

### “What BTD6 data can you answer?”

- Return a bounded capability summary from the answerability snapshot, grouped by verified
  deterministic, calculation, and live/freshness-sensitive domains.
- Name important limits and unsupported domains.
- Do not imply that a fixture’s existence means tool/context/UI/apply exposure exists.

### “Why didn’t you reply?”

- If a visible relevant audit row exists, give its user-safe reason and effective policy
  source.
- If no relevant row is visible, say that no visible recent decision was found; do not
  invent a denial cause.
- Redact inaccessible channels and platform-only diagnostics.

### “Which AI settings affect this channel?”

- Show the effective value plus source/precedence (guild → category → channel and relevant
  role policy) from policy dry-run/settings projection.
- Distinguish reply admission, model/provider configuration, instruction profile, memory,
  and tool scope.
- For authorized users, offer deterministic panel/preview navigation; the AI does not
  mutate the settings.

### “Why did you say you didn’t have verified data?”

- Explain the evidenced failure class: no matching fact reached context, a selected tool
  returned unsupported/not found, provider/tool path degraded, or faithfulness rejected
  unsupported names/numbers.
- If the exact cause is unavailable, say so.
- Never claim data is absent merely because resolution/tool selection failed.

## 10. Deferred and explicitly out of scope

- Full tower cutover.
- Achievements extraction/browser.
- Rogue/Frontier extraction or answer path.
- Alternate round-set/ABR browser or dataset extraction.
- AI-controlled setting mutations.
- Full setup wizard rewrite.
- Broad Settings Manager rewrite for every subsystem.
- New write-capable AI tools.
- Provider abstraction rewrite.
- Broad BTD6 data extraction.
- Unverified Double Cash/Half Cash/difficulty/ABR round-income math.
- Promoting any gated AI/BTD6 work without explicit activation.

## 11. Owner questions and decisions

### Existing decisions that govern this roadmap

- Orchestration foundation comes before net-new tools.
- Audience posture is tiered; read access does not grant action authority.
- AI remains explanation-only/read-only in the current lane.
- Unanswered questions are not approval; safe defaults apply.

### Questions to resolve when activating specific phases

These do **not** block the roadmap and therefore are not added as new maintainer-router
questions now:

1. Which exact Phase 1 PR boundary should be activated after the orchestration foundation:
   BTD6 service semantics alone, or service + tool/context exposure together?
2. Should the public BTD6 answerability snapshot list internal tool names, or only
   user-facing capabilities while admins see tool names?
3. Is the existing Settings Manager route ready for one AI page after Phase 2, or should
   Phase 4 wait for a separately accepted foundation slice?
4. Should the generated JSON artifact be committed or generated only in CI? Safe default:
   commit deterministic JSON + Markdown so drift is reviewable.

Route a focused question to `docs/owner/maintainer-question-router.md` only when one of
these becomes a genuine activation blocker. Do not ask them as a batch before that point.

## 12. Recommended implementation sequence and handoff

1. **Opus / broad planning-execution target:** re-verify live gates and finish/accept the
   orchestration foundation, then review this roadmap’s Phase 1/2 boundaries together.
2. **Sonnet / narrow accepted target:** only after activation, implement **Phase 1A**
   (BTD6-owned deterministic round-cash result semantics and tests) without tool/UI scope.
3. Follow with Phase 1B, then Phase 2. Do not jump to self-awareness tools or UI before the
   read model/catalogue foundations exist.
4. Treat Phase 5 as a docs/tooling visibility slice after canonical exposure metadata is
   available; do not hand-maintain the dashboard.

The most important implementation principle is: **known deterministic data is not
answerable until selection, evidence, semantics, scope, explanation, and failure behavior
are all pinned.**
