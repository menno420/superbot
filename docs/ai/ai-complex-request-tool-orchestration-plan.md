# Configurable AI Tool Orchestration for Complex BTD6 Requests

> **Status:** `plan` — research-backed planning document; assumes the bot-awareness and

health-diagnostics roadmap is already delivered  
**Verified against:** current repository worktree on 2026-06-06  
**Primary focus:** complex BTD6 lookups and calculations  
**Secondary goal:** reusable configuration/orchestration for future read-only tools

> **Progress (2026-06-09):** **Phase 1 foundation shipped** (PR slices A+B) — the canonical
> tool catalogue (`services.ai_tool_catalogue`: `AIToolMetadata` + named toolsets + one
> `CATALOGUE` entry per registered tool) and a deterministic, compatibility-preserving
> selector (`select_tools`, with `ToolExclusionReason` codes) that `build_registry` now uses.
> `BTD6_GROUNDING_TOOL_NAMES` is **derived** from the catalogue (no more hand-maintained
> drift). Default behaviour is unchanged; an optional `enabled_toolsets`/`disabled_tools`
> policy can only **narrow** the offered set, never grant above `AIScope` (proven by test).
> **Phase 2 shipped 2026-06-09** (PR slice C) — provider-neutral tool-choice + budgets:
> `AIToolChoice`/`ToolRequirementMode` (NONE/AUTO/REQUIRED_ANY/REQUIRED_GROUP/REQUIRED_TOOL)
> and `AIToolBudget` (hop/call/wall/result caps) on `AIRequest`, mapped onto BOTH the OpenAI
> and Anthropic adapters, enforced by a shared `ToolLoopState`. Defaults are
> **compatibility-preserving** (AUTO + hop-bounded, no other caps = today's behaviour). The
> gateway's redaction seam now uses `dataclasses.replace`, so a new request field can never be
> dropped there again.
> **Phase 3 shipped 2026-06-09** (PR slices D+E) — typed orchestration-policy storage + resolver +
> mutation + projection + the operator UI. Migration `062` adds a nullable `orchestration_profile`
> column to `ai_guild_policy` / `ai_channel_policy` / `ai_category_policy`; `services.ai_orchestration_presets`
> holds the built-in presets (the default reproduces today's behaviour byte-for-byte); `services.ai_orchestration_policy.resolve`
> picks most-specific-wins (channel → category → guild → default); `services.ai_orchestration_mutation` is the
> audited write seam (built-in keys only); the resolved policy is wired into `natural_language_stage._invoke_gateway`
> (toolset narrowing + tool_choice/tool_budget, default = byte-identical); the **Tools & Workflows** AI-panel
> button (`ai:tools`) opens the chooser (per-scope profile picker + dry-run analyzer with reason codes). The
> maintainer lifted the AI-exposure gate for this operator UI this session. **Not yet:** the complex-BTD6
> workflow (Phase 4) and the durable orchestration *audit trace* (plan §12.1 — the dry-run preview already
> gives operators inspectability; the per-decision audit column is deferred to keep the hot audit path
> untouched). PRs reconciled 2026-06-09: Phase 1 = **#612**, Phase 2 = **#618**, Phase 3 = **#619** (+ **#620** real-Postgres hardening for the 062 storage).
> **Phase 4 MVP DECIDED (Q-0046, 2026-06-09): one vertical slice** — the plan→execute→verify
> workflow for the round-cash question family ("cash from A to B / can I afford X?") with
> **one** typed answer-with-evidence contract. Prove the pattern end-to-end; remaining §7
> contracts + the §12.1 durable audit trace follow the proven template, not this slice.
> **Phase 4 MVP BUILT 2026-06-09 (PR #634, execution-plan Lane 3):** new
> `services/ai_round_cash_workflow.py` — deterministic plan (conservative question
> recogniser) → execute (the existing `btd6_data_service.round_cash` owner; afford-check
> composes on its cumulative outputs) → verify (§10.2 completeness gate incl. the Q-0043
> identity `range_cash == cum(B) − cum(A−1)`; failures degrade to precise *unsupported*
> refusals) → synthesize (evidence block onto the system prompt + the faithfulness ledger;
> the model explains, never recomputes). The one typed contract: `AIAnswerWithEvidence` +
> `CalculationEvidence` (`core/runtime/ai/contracts.py`, contract `calculation_explained`,
> **explicitly carrying Q-0043 inclusive-range semantics**). Activation is profile-gated on
> the resolved `workflow == "analyze_execute_verify"` label (`btd6_grounded` /
> `btd6_grounded_strict`); the compatible default never reaches it — **default byte-identical,
> pinned by wiring tests**. Model-loop behaviour needs the maintainer's **production check**
> (no provider key in the sandbox). Remaining §7 scope + §12.1 stay deferred.
> **Next §7 family SELECTED (consolidated-plan Batch 10 / DT10, 2026-06-10): §7.5
> multi-entity comparison** — the deterministic resolve-candidates → shared-assumption
> validation → bounded fan-out → normalize → deterministic rank/diff helper, with a typed
> comparison-evidence contract on the #634 template (the model explains a deterministic
> ranking, never compares prose). Selected because it covers the highest-frequency
> *unserved* live question shape ("X or Y — which is better/cheaper?") and every leg is
> deterministic/read-only (Q-0048 tool posture), while activation stays profile-gated +
> default-byte-identical exactly like #634. **Sequencing:** implement after the
> maintainer's production check of the #634/#639 model loops (announced as the next
> dedicated eval session) — the verify/synthesize template should be confirmed live before
> a second family stacks on it. Acceptance bar for the slice: deterministic tests for the
> rank/diff helper; a comparison-evidence contract test; wiring tests pinning the
> compatible default byte-identical; refusal paths for unresolvable candidates /
> mismatched assumptions.

## 1. Executive recommendation

SuperBot already has the difficult foundations: provider-neutral tool contracts,
bounded multi-hop tool loops, OpenAI and Anthropic adapters, a central scope-gated
read-only tool registry, BTD6 grounding/faithfulness checks, task routing, behavior
presets, channel/category AI policy, and an eval harness.

The next improvement should **not** be more prompt text or more tools offered to
every request. It should be a configurable **tool orchestration policy layer** that
answers four questions before each model call:

1. Which tool families are allowed in this scope?
2. Which tools, if any, must run before the model answers?
3. How much tool/cost/latency budget may this request consume?
4. Which deterministic workflow should handle this request class?

The target architecture is:

```text
message + resolved AI policy + routed task + request complexity
                              |
                              v
                 AI orchestration policy resolver
        (behavior preset + toolset + requirement + budget + workflow)
                              |
             +----------------+----------------+
             |                                 |
             v                                 v
 deterministic preflight tools        model-visible allowed tools
             |                                 |
             +----------------+----------------+
                              v
               bounded plan / execute / verify / answer
                              |
                              v
             BTD6 evidence ledger + response contract + eval trace
```

The strongest immediate product feature is a channel/category configuration such
as:

```text
Behavior: BTD6 Analyst
Allowed toolsets: btd6_reference, btd6_calculators
Required preflight: btd6_request_analysis
Model tool requirement: at_least_one_grounding_tool for factual BTD6 questions
Tool budget: 4 calls / 2 hops / 8 seconds
Answer format: calculation_explained
```

This is materially different from the existing behavior presets. Existing presets
control reply mode and instruction text; the proposed orchestration profile controls
what the runtime actually offers, requires, executes, budgets, and verifies.

## 2. Research findings and their implications

This plan uses primary-source provider documentation and published research. The
recommendations are translated into provider-neutral repository contracts rather
than binding behavior to one vendor.

### 2.1 Explicit tool choice is stronger than prompt-only nudges

OpenAI supports automatic tool choice, requiring one or more tools, forcing one
specific function, disabling tools, and restricting calls to an allowed subset.
It also recommends strict function schemas. Anthropic similarly documents that
prompt instructions can increase tool use, but a hard guarantee requires
`tool_choice`.

Sources:

- [OpenAI function calling: tool choice, allowed tools, parallel calls, and strict mode](https://developers.openai.com/api/docs/guides/function-calling#tool-choice)
- [Anthropic tool use: automatic triggering versus hard tool-choice guarantees](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview#when-claude-uses-tools)

**Implication for SuperBot:** “always use BTD6 tools in this channel” must be a
runtime policy represented in provider-neutral request data, not only a behavior
preset sentence. Prompt text can remain a soft hint, but required behavior needs a
hard orchestration contract.

### 2.2 Narrow allowed toolsets reduce ambiguity, cost, and context noise

Tool definitions consume prompt tokens. Provider documentation supports restricting
the currently callable subset. OpenAI's evaluation guidance also notes that as a
single agent accumulates tools/tasks, correct instruction following and tool
selection become harder.

Sources:

- [OpenAI function calling: allowed tool subsets](https://developers.openai.com/api/docs/guides/function-calling#tool-choice)
- [OpenAI evaluation best practices: tool-selection nondeterminism and architecture complexity](https://developers.openai.com/api/docs/guides/evaluation-best-practices#single-agent-architectures)
- [Anthropic tool-use pricing/context overhead](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview#pricing)

**Implication for SuperBot:** replace “every scope-allowed tool is offered on every
request” with an explicit toolset resolver. A BTD6 cost question should see a small
cost/calculation set, not server-member, audit, map, relic, CT, and unrelated tools.
Do not jump to multi-agent architecture until evals prove the single orchestrator
cannot select reliably.

### 2.3 Strict schemas and structured intermediate outputs improve reliability

OpenAI recommends strict tool schemas and Structured Outputs when schema adherence
matters. Anthropic also supports strict tool use. Structured outputs are useful for
an intermediate request analysis or calculation plan; function calling remains the
right mechanism for invoking repository tools.

Sources:

- [OpenAI function calling: strict mode](https://developers.openai.com/api/docs/guides/function-calling#strict-mode)
- [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- [Anthropic strict tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview#guarantee-schema-conformance-with-strict-tool-use)

**Implication for SuperBot:** every tool schema should become strict-compatible,
and complex requests should use typed intermediate contracts such as
`BTD6RequestAnalysis` and `CalculationEvidence`, rather than asking the model to
informally decide everything inside prose.

### 2.4 Interleaving reasoning and tools helps multi-step factual tasks

The ReAct paper found benefits from interleaving reasoning and external actions,
including reduced hallucination/error propagation in question answering. SuperBot
already has a bounded tool loop, so it does not need a new agent framework to gain
this benefit.

Source:

- [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)

**Implication for SuperBot:** retain bounded multi-hop tool use, but make the
workflow deliberate: analyze the request, call deterministic tools, inspect missing
evidence, then synthesize. Do not expose private chain-of-thought; record only safe
workflow decisions and tool traces.

### 2.5 Complex workflows need trace-level and step-level evals

OpenAI recommends evaluating tool selection and argument precision, and describes
trace grading as a way to identify workflow-level errors. It recommends using evals
to decide whether architecture complexity such as multiple agents is justified.

Sources:

- [OpenAI evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices)
- [OpenAI trace grading](https://developers.openai.com/api/docs/guides/trace-grading)

**Implication for SuperBot:** improve the existing eval harness to grade route,
resolved toolset, requirement satisfaction, arguments, call order, evidence use,
calculation correctness, restraint, latency budget, and final answer—not only whether
a tool was called.

### 2.6 Prompt structure and examples still matter, but are not enforcement

OpenAI recommends clear instruction hierarchy, logical sections, relevant context,
diverse few-shot examples, pinned model snapshots, and evals for prompt/model
changes. Reasoning models generally need goals and constraints rather than demands
to reveal step-by-step reasoning.

Sources:

- [OpenAI prompt engineering](https://developers.openai.com/api/docs/guides/prompt-engineering)
- [OpenAI reasoning best practices](https://developers.openai.com/api/docs/guides/reasoning-best-practices)

**Implication for SuperBot:** behavior presets should become structured, versioned
orchestration presets with concise task-specific examples. They should not request
visible chain-of-thought or be relied upon to enforce tool use.

## 3. Current repository state and verified gaps

### 3.1 What already exists

| Existing capability | Current repository behavior | Reuse decision |
|---|---|---|
| Provider-neutral tools | `AIToolSpec` plus request `tools` and separate live handlers | Extend, do not replace |
| Provider tool loops | OpenAI and Anthropic adapters run bounded tool loops | Extend with neutral choice/budget policy |
| Tool choice | Both providers currently hard-code automatic choice when tools are offered | Replace hard-coded `auto` with resolved policy |
| Tool registry | `services.ai_tools.build_registry()` filters by `AIScope` and runtime availability | Split catalogue metadata from per-request selection |
| BTD6 tools | Large set of lookup, roster, capability, cost, round, map, mode, relic, bloon, paragon, and CT tools | Group into declared toolsets and workflow capabilities |
| Grounding allowlist | `BTD6_GROUNDING_TOOL_NAMES` identifies results allowed to ground replies | Preserve and enrich with typed evidence metadata |
| Faithfulness guard | BTD6 replies are checked against auto-grounding facts and approved tool results | Keep as final backstop; add earlier evidence completeness checks |
| Task router | Routes BTD6/general/video request classes | Add complexity/intent analysis without replacing deterministic routing |
| Behavior presets | Seeded instruction profiles with recommended reply modes | Add separate orchestration presets; do not overload instruction text |
| Channel/category policy | Resolves reply mode, levels, cooldown, and instruction profile | Extend projection with orchestration profile/tool-policy reference |
| Eval harness | Covers tool use/restraint, structure, safety, grounding, knowledge, and format | Add orchestration and calculation trace grading |

### 3.2 Gaps that directly cause weaker complex responses

1. **All available tools are broadly offered.** `build_registry()` currently builds
   one large catalogue and filters primarily by `AIScope` and member-lookup feature
   availability. It does not narrow by routed task, request intent, behavior preset,
   channel/category tool policy, or cost budget.
2. **Provider adapters hard-code `auto`.** A scope cannot require at least one tool,
   force one specific tool, or disable model-visible tools while still using a
   deterministic preflight.
3. **Behavior presets are prompt/mode presets only.** `btd6_focused` asks the model
   to prioritize grounding but cannot guarantee a grounding tool call or disable
   unrelated tools.
4. **No reusable toolset catalogue exists.** Individual tools have names and minimum
   scopes but no family, capability tags, cost class, factual authority, parallel
   safety, freshness, or task affinity metadata.
5. **No per-request tool budget exists beyond provider hop limits.** There is no
   configured maximum call count, result-byte/token budget, wall-clock budget, or
   expensive-tool allowance by channel/profile.
6. **No deterministic complex-request analysis contract exists.** Routing identifies
   broad tasks, but not whether a BTD6 request is a lookup, comparison, calculation,
   optimization, multi-entity synthesis, ambiguous request, or unsupported question.
7. **No workflow distinction exists between deterministic preflight and model-chosen
   tools.** “Always run this tool” is unsafe/impossible when a tool requires arguments
   that only the model can infer, while some no-argument/context tools are ideal
   deterministic preflights.
8. **Tool result evidence is mostly untyped JSON/string context.** The final guard
   checks grounding, but there is no shared provenance/evidence contract that states
   which claim or calculation each result supports.
9. **Calculations are tools, but there is no calculation-plan contract.** Complex
   comparisons can require several deterministic calculations and conversions; the
   model currently decides these ad hoc.
10. **Audit/evals cannot fully explain bad orchestration.** The current audit can
    identify task/provider/model/policy, and evals can detect tool calls, but there is
    no resolved orchestration profile, offered-tool list hash, required-tool outcome,
    budget-exhaustion reason, or safe tool trace summary.

## 4. Core design: separate behavior from orchestration

A behavioral instruction profile answers:

- Should the bot reply here?
- What tone, detail level, and domain emphasis should it use?

An orchestration profile answers:

- Which toolsets are available?
- Which tools are required or pre-run?
- Which workflow handles complex requests?
- What budgets and answer/evidence rules apply?

Do not combine these into one free-text profile. Operators should be able to choose
“concise” behavior with “BTD6 calculator” orchestration, or “teaching” behavior with
“BTD6 analyst” orchestration.

### 4.1 Proposed resolved contract

```python
@dataclass(frozen=True)
class AIOrchestrationPolicy:
    profile_key: str
    enabled_toolsets: tuple[str, ...]
    disabled_tools: tuple[str, ...]
    preflight_tools: tuple[str, ...]
    tool_requirement: ToolRequirement
    workflow: str
    answer_contract: str
    budget: AIToolBudget
    parallel_policy: str
    source_trace: tuple[str, ...]
```

This is a read model assembled from built-in defaults plus guild/category/channel
configuration. It must be included in the AI configuration projection and policy
decision hash so operators can understand the effective behavior.

### 4.2 Requirement modes

```python
class ToolRequirementMode(str, Enum):
    NONE = "none"                  # no model-visible tools
    AUTO = "auto"                  # model may call zero or more
    REQUIRED_ANY = "required_any"  # at least one allowed tool
    REQUIRED_GROUP = "required_group"  # at least one tool from a named group
    REQUIRED_TOOL = "required_tool"    # force one named tool
```

`REQUIRED_GROUP` is a SuperBot orchestration rule, not necessarily a native provider
feature. The resolver narrows the offered tools to the group and uses provider
“required/any” semantics, then verifies the resulting call belongs to that group.

### 4.3 Preflight versus forced model calls

These must be distinct:

- **Preflight tool:** application calls a known safe tool before the model request.
  Use when arguments are deterministic from request context or the tool accepts no
  arguments. Example: a BTD6 data-version/capability summary.
- **Required model tool:** model must produce arguments for one of the offered tools.
  Use when the request contains entities/ranges/options that need extraction.
- **Required group:** model must choose at least one tool from a narrow family. Use
  for factual BTD6 channels where the exact lookup/calculator depends on the question.

Never configure a specific required tool “for every message in a channel” unless it
is valid for every message and has deterministic/safe arguments. For most BTD6
channels, require the `btd6_grounding` group rather than forcing `btd6_lookup`.

## 5. Tool catalogue and toolsets

### 5.1 Enrich tool metadata

Move from a flat list assembled inside `build_registry()` to declared catalogue
entries. Keep handlers private/read-only, but add metadata used by selection and UI.

```python
@dataclass(frozen=True)
class AIToolDescriptor:
    spec: AIToolSpec
    handler_factory: ToolHandlerFactory
    toolsets: frozenset[str]
    task_affinity: frozenset[AITask]
    capability_tags: frozenset[str]
    grounding_domain: str | None
    cost_class: Literal["cheap", "normal", "expensive"]
    freshness: Literal["static", "cached", "live"]
    parallel_safe: bool
    preflight_safe: bool
    result_contract: str
```

The existing `min_scope` remains authoritative. A toolset policy can only remove
scope-allowed tools; it can never grant a tool above the caller's scope.

### 5.2 Initial built-in toolsets

| Toolset | Purpose | Candidate members |
|---|---|---|
| `btd6_reference` | Entity and rule lookup | lookup, roster, capability, maps, modes, relics, bloons |
| `btd6_rounds` | Round questions and range aggregation | round composition, bloon filter where relevant |
| `btd6_costs` | Difficulty conversion and cumulative costs | difficulty cost, cumulative cost, lookup |
| `btd6_paragon` | Paragon requirements/calculation/stat projections | paragon calculate, requirements, stats-at-degree |
| `btd6_live` | Fresh server/Ninja Kiwi-related state | CT team and future live API tools |
| `btd6_grounding` | Union of safe BTD6 factual tools | derived from grounding-domain metadata, replacing manual drift-prone grouping where possible |
| `server_context_basic` | Low-risk server context | overview/time/user standing as policy permits |
| `server_context_sensitive` | Member/config/audit context | admin/scope-gated tools only |
| `diagnostics` | Future health snapshot tools | remains independent from BTD6 presets |

### 5.3 Selection precedence

Recommended effective selection:

```text
base catalogue
∩ caller AIScope
∩ runtime/feature availability
∩ routed-task affinity
∩ enabled orchestration-profile toolsets
∩ channel/category allow policy
− explicit disabled tools
− tools exceeding budget/freshness rules
= offered tools
```

Every exclusion should have a stable reason code for preview/audit:

```text
scope_denied
runtime_unavailable
task_mismatch
toolset_disabled
explicitly_disabled
budget_disallowed
freshness_disallowed
```

### 5.4 Keep selection deterministic

Do not ask an LLM to choose which tools the LLM is allowed to see. Initial selection
must be deterministic and inspectable. A later tool-retrieval index may help when the
catalogue becomes very large, but it must remain constrained by policy and evaluated
against a deterministic candidate set.

## 6. Orchestration presets

### 6.1 Preset examples

#### `balanced_helper`

- behavior profile: existing helpful/concise option;
- toolsets: task-affinity defaults;
- requirement: `AUTO`;
- workflow: `direct_or_tool`;
- budget: 2 calls, 2 hops, low result budget;
- answer contract: concise factual response.

#### `btd6_grounded_helper`

- toolsets: `btd6_reference`, `btd6_costs`, `btd6_rounds`, `btd6_paragon`;
- requirement: `REQUIRED_GROUP(btd6_grounding)` for factual BTD6 routes;
- workflow: `analyze_execute_verify`;
- budget: 4 calls, 3 hops;
- answer contract: answer plus short evidence/version note;
- non-BTD6 requests: normal auto-tool behavior or graceful redirect.

#### `btd6_calculator`

- toolsets: `btd6_costs`, `btd6_paragon`, relevant reference lookup;
- requirement: required calculator group for calculation/comparison requests;
- workflow: `calculation_plan_execute_verify`;
- budget: 6 calls, 3 hops, parallel allowed only for independent calculations;
- answer contract: inputs, assumptions, result, and deterministic calculation trace
  summary;
- forbid unsupported arithmetic from model memory when a deterministic tool exists.

#### `btd6_research_desk`

- toolsets: all BTD6 factual sets including live/cached sources;
- requirement: required grounding group;
- workflow: `decompose_gather_synthesize`;
- budget: higher but bounded;
- answer contract: comparison table, evidence coverage, ambiguities, and data version;
- recommended for dedicated expert channels, not general chat.

#### `no_tools_conversational`

- toolsets: none;
- requirement: `NONE`;
- workflow: direct answer;
- answer contract: no claim of live/current/private facts;
- useful for social channels or cost control.

#### `forced_context_channel`

- deterministic preflight: safe channel-specific context tool(s);
- model-visible requirement: `AUTO` or required group depending on task;
- intended for future support/diagnostics channels where a no-argument context snapshot
  should accompany every request.

### 6.2 Preset composition

A preset should reference separately versioned components:

```text
behavior profile + toolset policy + requirement policy + workflow + budget + answer contract
```

This avoids duplicating near-identical presets merely to change tone or budget. The
UI may expose friendly bundled presets while advanced operators edit components.

### 6.3 Safe defaults

- Existing channels inherit `balanced_helper` behavior equivalent to today.
- No migration should suddenly force tools or increase provider spend.
- A preset cannot enable a tool above caller scope or a disabled feature flag.
- Built-in presets are immutable through normal guild mutation paths.
- Custom guild presets may only reference catalogue-approved toolsets/tools/workflows.

## 7. Complex BTD6 request workflow

### 7.1 Request analysis

Add a typed, bounded `BTD6RequestAnalysis` produced deterministically where possible
and by a small structured model call only when needed.

```python
@dataclass(frozen=True)
class BTD6RequestAnalysis:
    intent: Literal[
        "lookup", "calculation", "comparison", "optimization",
        "round_analysis", "strategy", "live_state", "ambiguous", "unsupported"
    ]
    entities: tuple[EntityRef, ...]
    requested_outputs: tuple[str, ...]
    assumptions_needed: tuple[str, ...]
    required_capabilities: tuple[str, ...]
    can_parallelize: bool
    confidence: Literal["high", "medium", "low"]
```

Prefer deterministic entity extraction/catalogue resolution first. Use structured
model analysis only for genuinely complex natural language. Analysis output is not a
fact source and does not ground the answer.

### 7.2 Plan, execute, verify, synthesize

For complex requests:

1. **Analyze:** resolve entities, intent, outputs, assumptions, and required
   capabilities.
2. **Clarify or default:** ask one focused question when an omitted assumption would
   materially change the answer; otherwise use a documented default and state it.
3. **Plan:** map required capabilities to deterministic tools. This mapping should be
   mostly application-owned, not free-form model choice.
4. **Execute:** call independent read-only tools in parallel only when descriptors say
   they are parallel-safe and results do not depend on each other.
5. **Verify:** ensure required evidence/calculation outputs exist, are fresh enough,
   and agree on version/difficulty/entity identity.
6. **Synthesize:** ask the model to explain already-computed results under a typed
   answer contract.
7. **Faithfulness check:** retain the existing BTD6 guard as the final backstop.
8. **Refuse precisely:** if evidence is insufficient, state exactly which capability
   or data is missing rather than improvising.

### 7.3 Deterministic calculations first

For BTD6 calculations:

- the model extracts/clarifies inputs and explains results;
- repository calculator services perform arithmetic;
- result objects include normalized inputs, assumptions, formula/version identifier,
  output, warnings, and source version;
- comparisons call calculators for each candidate, then a deterministic comparison
  helper ranks results;
- the model must not recompute or alter returned numeric outputs;
- if a requested calculation has no deterministic implementation, label it
  unsupported or estimate-only according to explicit policy.

### 7.4 Calculation evidence contract

```python
@dataclass(frozen=True)
class CalculationEvidence:
    evidence_id: str
    calculator: str
    calculator_version: str
    normalized_inputs: Mapping[str, JsonValue]
    assumptions: tuple[str, ...]
    outputs: Mapping[str, JsonValue]
    warnings: tuple[str, ...]
    data_version: str | None
```

The final answer renderer should refer to evidence IDs internally and expose a short
human-readable calculation summary, not raw internal traces.

### 7.5 Multi-entity comparison helper

Add a reusable deterministic orchestration helper instead of expecting the model to
manually call the same tool repeatedly and compare prose:

```text
resolve candidates -> validate shared assumptions -> fan out bounded calculations
-> normalize outputs -> deterministic rank/diff -> model explains result
```

This pattern is valuable for:

- tower/upgrade cost comparisons — **SHIPPED #946** (`compare_crosspath_costs` +
  `deterministic_cost_comparison_reply`: ranks two-or-more `(tower, crosspath)` at one
  difficulty);
- difficulty cost comparisons — **SHIPPED #950** (`compare_difficulty_costs` +
  `deterministic_difficulty_cost_comparison_reply`: ranks one `(tower, crosspath)` across
  two-or-more difficulties — the sibling of the above; the two are mutually exclusive on
  candidate count, so both ride the `deterministic_btd6_list_reply` floor seam);
- paragon degree/resource scenarios — **SHIPPED** (`compare_paragon_costs` +
  `deterministic_paragon_cost_comparison_reply`: ranks the **base build price** of two-or-more
  paragons, difficulty-aware, grounded in `utils/btd6/paragon_math`'s committed `BASE_PRICES_MEDIUM`;
  fires only on an explicit `paragon` token, which also makes it mutually exclusive with the tower
  cost builders — they defer the moment "paragon" is present so a "dart/ninja paragon" question is
  never priced as the base tower);
- round-range comparisons — **SHIPPED #955** (`compare_round_ranges` +
  `deterministic_round_range_comparison_reply`: ranks the total cash of two-or-more inclusive
  round ranges via the existing `round_cash` primitive, ABR-aware; distinct from the single-range
  projection the round-cash workflow owns — they stay non-overlapping on **range count** (this
  floor requires ≥2 ranges) and the floor short-circuits before the workflow ever runs);
- future game/stat/economy functions.

### 7.6 Property/capability roster floors (new family beyond §7.5)

The §7.5 *comparison* family (above) is COMPLETE. The next deterministic-floor
family is the **property/capability roster** — the same BUG-0009 wrong-assembly
class, but a *list-by-property* rather than a *rank/diff*: "which towers can pop
lead / detect camo?", "what are all the MOAB-class bloons / which bloons are
immune to sharp?". Every entity name is grounded, so the model can silently
mis-*roster* (include/exclude the wrong entity, miscount a tier) and the
value-only faithfulness guard never catches it. The authoritative answer is
already derived deterministically from the committed stats/data, so the floor
OWNS the labelled list and rides the same `_BTD6_LIST_BUILDERS` seam:

- tower capability roster — **SHIPPED #975** (`deterministic_capability_roster_reply`
  fronts `services.btd6_capability_service.towers_with_capability` /
  `paragons_with_capability`: camo detection + lead/black/white/purple popping;
  base 0-0-0 scope by default, an explicit "with upgrades" signal flips to the
  earliest-upgrade roster, a `paragon` cue answers the per-paragon camo roster);
- bloon roster — **SHIPPED #975** (`deterministic_bloon_roster_reply` fronts the
  committed `bloons.json` fields: MOAB-class enumeration via `category` + immunity
  roster via `immune_to`, modifier pseudo-bloons excluded; the sibling
  `deterministic_roster_reply` covers heroes/towers/paragons/maps but not bloons);
- future property rosters (e.g. hero/relic property lists) extend the same seam.

All members are read-only deterministic (Q-0048), pinned by the
`test_btd6_floor_builder_exclusivity.py` one-fires invariant.

## 8. Provider-neutral request changes

### 8.1 Extend `AIRequest`

Suggested additive fields:

```python
@dataclass(frozen=True)
class AIToolChoice:
    mode: ToolRequirementMode = ToolRequirementMode.AUTO
    tool_name: str | None = None
    group_name: str | None = None

@dataclass(frozen=True)
class AIToolBudget:
    max_calls: int = 4
    max_hops: int = 4
    max_wall_seconds: float = 12.0
    max_result_chars: int = 24_000
    allow_expensive: bool = False

@dataclass(frozen=True)
class AIRequest:
    ...
    tools: tuple[AIToolSpec, ...] = ()
    tool_choice: AIToolChoice = AIToolChoice()
    tool_budget: AIToolBudget = AIToolBudget()
    parallel_tool_calls: bool = True
```

Do not expose provider-specific dictionaries outside provider adapters.

### 8.2 Provider mapping

| Neutral mode | OpenAI mapping | Anthropic mapping | SuperBot verification |
|---|---|---|---|
| `NONE` | `tool_choice="none"` or omit tools | omit tools / none | no dispatch occurs |
| `AUTO` | `auto` | `auto` | zero or more allowed calls |
| `REQUIRED_ANY` | `required` | `any` | at least one allowed call |
| `REQUIRED_TOOL` | forced function | forced tool | exact named call occurs |
| `REQUIRED_GROUP` | offer only group + `required` | offer only group + `any` | at least one call from group |

Provider adapters must enforce the resolved maximum calls/hops/wall time/result size,
not only their current constant hop limit.

### 8.3 Strict schema migration

Audit every `AIToolSpec.parameters` schema for strict compatibility:

- object schemas set `additionalProperties: false`;
- required fields are explicit;
- optional fields use a provider-neutral nullable representation compatible with
  adapters;
- enums and ranges are narrow;
- descriptions explain when **not** to use the tool;
- tools use stable canonical entity identifiers where possible;
- handler validation remains authoritative even when provider strict mode is active.

Add a startup/test validator that rejects invalid tool descriptors before they reach
a provider.

## 9. Configuration and ownership model

### 9.1 Storage direction

Do not store enabled tools as arbitrary free-text instruction profile content. Use
typed policy state. A reasonable additive design is:

- `ai_orchestration_profile`: named built-in or guild-owned orchestration components;
- `ai_tool_policy_guild`, `ai_tool_policy_category`, `ai_tool_policy_channel`, or a
  single typed scope table if repository conventions support it;
- channel/category policy references an orchestration profile or typed override;
- optional explicit deny list stored as validated tool keys/toolset keys;
- every mutation through a dedicated `ai_orchestration_mutation` service;
- every read through `ai_orchestration_policy.resolve(...)` and the canonical AI
  config projection.

Before choosing tables, compare extending existing typed policy rows versus a
separate scope-policy table. Avoid adding many nullable columns to instruction
profiles because orchestration is not instruction text.

### 9.2 Resolution precedence

Recommended precedence mirrors current policy concepts:

```text
system safe default
< guild orchestration profile
< category orchestration override
< channel orchestration override
< task-specific safe constraints
< caller scope/runtime feature constraints
```

Lower layers may narrow or tune; they may never bypass scope, runtime kill switches,
read-only constraints, grounding rules, or hard global budgets.

### 9.3 Channel “always force tools” behavior

Support operator intents with safe typed options:

- `No tools`;
- `Automatic tools from selected toolsets`;
- `Require one grounding tool for factual BTD6 requests`;
- `Require one calculator tool for BTD6 calculation requests`;
- `Run selected safe preflight context on every allowed request`;
- `Force one specific tool` only when descriptor metadata marks it safe and valid for
  the chosen trigger/task.

The configuration UI should reject invalid combinations such as forcing a Paragon
calculator for general conversation or configuring a preflight tool that requires
model-derived arguments.

### 9.4 UI additions

Extend the existing AI panel/Behavior workflow rather than creating a new unrelated
admin island:

- **Behavior** remains tone/reply-mode/instruction configuration;
- add **Tools & workflows** for orchestration profile selection;
- show effective toolsets, disabled tools, requirement mode, workflow, and budget;
- preview the resolved policy for a sample channel/user/task;
- include “Why is this tool unavailable?” reason codes;
- add a dry-run request analyzer that shows route, complexity, selected toolsets,
  requirement, and planned deterministic workflow without calling a provider;
- make dangerous/cost-increasing changes explicit in confirmation copy.

## 10. Answer contracts and response quality

Behavior presets should select a typed answer contract rather than relying only on
free-text style instructions.

### 10.1 Initial answer contracts

| Contract | Required visible elements |
|---|---|
| `concise_fact` | direct answer, short source/version note when relevant |
| `calculation_explained` | normalized inputs, assumptions, result, short explanation, warnings |
| `comparison` | compared entities, shared assumptions, compact table/ranking, key difference |
| `research_summary` | answer, evidence coverage, uncertainty/missing data, data version |
| `clarification` | one focused question and why it changes the result |
| `unsupported` | exact unsupported capability/data and nearest available command/tool |

The model may render prose, but a pre-render structured response object should be
validated before Discord output. This makes complex responses testable and reusable
for future functions/panels.

### 10.2 Evidence completeness gate

Before synthesis, verify:

- every requested output has supporting evidence;
- every compared entity resolved canonically;
- all calculations share compatible difficulty/version assumptions;
- required tool/group use was satisfied;
- no result was truncated in a way that invalidates conclusions;
- live/cached results meet freshness policy;
- warnings and unsupported portions are propagated.

If completeness fails, clarify, perform another allowed bounded step, or return a
precise partial answer. Do not let the model conceal missing evidence.

## 11. Budgeting, parallelism, and failure behavior

### 11.1 Budget dimensions

Each orchestration profile should bound:

- model/tool hops;
- total tool calls;
- per-tool and total wall-clock time;
- tool result characters/tokens;
- expensive/live tool calls;
- parallel fan-out width;
- clarification/retry count;
- final output size.

### 11.2 Parallelism policy

- parallelize only independent, descriptor-marked `parallel_safe` reads;
- do not parallelize when a later call needs a prior canonical ID/result;
- preserve deterministic output ordering after parallel calls;
- enforce fan-out limits for multi-entity questions;
- record partial failures per call and allow useful partial answers where policy
  permits.

### 11.3 Stable failure reasons

Add safe orchestration reason codes:

```text
tool_required_but_unavailable
tool_requirement_unsatisfied
tool_budget_exhausted
tool_result_too_large
tool_timeout
request_ambiguous
calculation_unsupported
evidence_incomplete
version_mismatch
freshness_requirement_failed
```

Each should map to deterministic user-facing fallback text and audit/metric labels.

## 12. Audit, metrics, and evals

### 12.1 Safe orchestration trace

Record a bounded trace summary, not private reasoning or raw results:

```python
@dataclass(frozen=True)
class AIOrchestrationTrace:
    profile_key: str
    workflow: str
    routed_task: str
    request_intent: str | None
    offered_tool_names: tuple[str, ...]
    requirement: str
    calls: tuple[SafeToolCallSummary, ...]
    requirement_satisfied: bool
    budget_outcome: str
    evidence_ids: tuple[str, ...]
    final_status: str
```

Hash or cap offered-tool lists in durable audit rows if necessary; keep full safe
traces process-local or in a dedicated bounded observability store according to the
executed diagnostics plan.

### 12.2 Metrics

Candidate metrics:

- request count by orchestration profile/workflow/intent;
- offered-tool count histogram;
- tool calls/results/errors/latency by tool;
- required-tool satisfaction and fallback reason;
- budget exhaustion count;
- evidence completeness failures;
- BTD6 faithfulness retry/refusal by orchestration profile;
- clarification rate;
- deterministic-calculator versus unsupported-calculation rate;
- answer-contract validation failures.

Avoid labels containing guild/channel/user IDs or arbitrary tool arguments.

### 12.3 Eval expansion

Expand the existing eval harness with categories:

- `toolset_selection`: only relevant tools are offered;
- `tool_requirement`: required group/tool is actually used;
- `tool_disable`: disabled tools are never offered/called;
- `tool_arguments`: canonical entity/path/difficulty/range extraction;
- `workflow_trace`: expected call sequence/parallel grouping;
- `calculation_correctness`: exact deterministic output use;
- `comparison_completeness`: every candidate evaluated under shared assumptions;
- `clarification`: asks when missing assumptions materially affect result;
- `budget`: stops/falls back safely at limits;
- `evidence_completeness`: does not answer beyond results;
- `answer_contract`: expected visible sections/fields;
- `preset_resolution`: guild/category/channel precedence and source trace;
- `provider_parity`: neutral choice modes behave equivalently on OpenAI/Anthropic.

For each complex case, grade separately:

1. route/intent;
2. resolved toolset;
3. requirement mode;
4. tool choice and arguments;
5. deterministic result/evidence use;
6. final factual/numeric correctness;
7. restraint and safety;
8. latency/call budget.

Use production failures to grow the golden set. Do not judge orchestration quality
only from final prose; a plausible answer may hide an incorrect or missing tool path.

## 13. Phased implementation plan

### Phase 0 — Contracts and policy decisions

Decide:

- built-in toolsets and descriptor metadata;
- requirement modes and provider-neutral semantics;
- which tools are preflight-safe, parallel-safe, expensive, live, or grounding;
- initial orchestration presets and safe defaults;
- scope/precedence model and custom-preset permissions;
- answer contracts and deterministic calculation evidence contract;
- budgets and failure reason codes.

**Exit criterion:** examples for general lookup, BTD6 lookup, BTD6 calculation,
comparison, ambiguous request, disabled toolset, and required-tool channel all have
an unambiguous resolved policy and expected trace.

### Phase 1 — Tool catalogue and per-request selection

> **✅ SHIPPED 2026-06-09.** `services.ai_tool_catalogue` holds `AIToolMetadata`
> (`core.runtime.ai.contracts`), the named-toolset constants, and a `CATALOGUE` entry per
> registered tool; `select_tools` is the deterministic selector with `ToolExclusionReason`
> codes; `build_registry` consults it and gained optional `enabled_toolsets`/`disabled_tools`
> params (default `None` = unchanged behaviour). `BTD6_GROUNDING_TOOL_NAMES` is derived from
> the catalogue. The **exit criterion is met and tested** (`test_ai_tool_catalogue.py`):
> default behaviour is byte-identical, a profile can narrow/disable toolsets, and an enabled
> toolset can never grant a tool above the caller's `AIScope`. **Deferred from this slice:**
> the strict-schema validator and a full runtime-availability-aware preview API (the selector
> emits reason codes today, but does not re-derive `runtime_unavailable` — that joins the
> Phase 3 dry-run/projection work).

Implement:

- enriched `AIToolDescriptor` catalogue;
- named toolsets;
- deterministic selector by scope/runtime/task/profile;
- exclusion reason codes and preview API;
- strict-schema validator;
- compatibility adapter so current behavior remains unchanged by default.

**Exit criterion:** existing requests still work, while tests prove a selected
profile can narrow/disable toolsets without granting additional authority.

### Phase 2 — Neutral tool choice and budgets

> **✅ SHIPPED 2026-06-09 (#618).** `core/runtime/ai/contracts.py` gained
> `ToolRequirementMode`, `AIToolChoice`, and `AIToolBudget`, plus `tool_choice`/`tool_budget`
> fields on `AIRequest` (defaults reproduce today's behaviour byte-for-byte). A shared
> `ToolLoopState` + `cap_tool_result` in `providers/base.py` bound the loop by hop / call /
> wall-time / result-size; the OpenAI and Anthropic adapters map the five modes onto their
> native `tool_choice` (`_openai_tool_choice` / `_anthropic_tool_choice`) — REQUIRED_* forces a
> tool on the first hop then relaxes to auto, REQUIRED_GROUP rides the resolver-narrowed set,
> NONE offers no tools. The gateway redaction now uses `dataclasses.replace` so the new fields
> survive. **Exit criterion met + tested** (`tests/unit/runtime/ai/test_tool_orchestration.py`,
> 18 tests): all five modes across both adapters + budget exhaustion + redaction preservation.
> **Deferred to later phases:** safe trace summaries / metrics and adapter-level required-group
> *verification* (the resolver pre-narrows, so the adapter mapping is correct today) ride with
> Phase 3's policy/projection work, where the orchestration trace lands.

Implement:

- neutral tool-choice and budget request contracts;
- OpenAI/Anthropic mappings;
- dynamic hop/call/wall/result budgets;
- required-group verification;
- safe trace summaries and metrics.

**Exit criterion:** tests prove `NONE`, `AUTO`, `REQUIRED_ANY`, `REQUIRED_GROUP`, and
`REQUIRED_TOOL` behavior across both provider adapters, including failures and
budget exhaustion.

### Phase 3 — Typed orchestration policy and admin UX

> **✅ SHIPPED 2026-06-09 (PR slices D+E).** Migration `062` adds the nullable
> `orchestration_profile` column to the three policy tables. `services.ai_orchestration_presets`
> (built-in presets: `compatible_default` = today's behaviour, `balanced_helper`, `btd6_grounded`,
> `btd6_grounded_strict`, `no_tools`), `services.ai_orchestration_policy.resolve` (most-specific-wins +
> dry-run trace, DB-fault-tolerant), and `services.ai_orchestration_mutation` (audited write seam,
> built-in keys only, emits `ai.orchestration.*_changed`) land the storage/read/mutation ownership.
> `AIConfigSnapshot.orchestration` carries the guild-default + override counts (read-only, I-2 preserved).
> The resolved policy is wired into `natural_language_stage._invoke_gateway` (toolset narrowing +
> `tool_choice`/`tool_budget`; default = byte-identical). The **Tools & Workflows** panel button
> (`ai:tools` → `views.ai.tools`) gives per-scope profile pickers + a dry-run analyzer that shows the
> resolved profile, offered/withheld tools with reason codes, and the budget. **Deferred:** the durable
> per-decision orchestration *audit trace* (§12.1) — the dry-run preview covers operator inspectability,
> and deferring it keeps the hot `ai_decision_audit` write path + its doc-pin untouched.

Implement:

- orchestration policy storage/read/mutation ownership;
- guild/category/channel resolution and config projection;
- seeded built-in orchestration presets;
- AI panel “Tools & workflows” UI, preview, and dry-run analyzer;
- audit rows/source trace additions.

**Exit criterion:** an operator can safely enable/disable toolsets or require BTD6
grounding/calculator groups for a channel without editing instruction text.

### Phase 4 — Complex BTD6 workflow

> **🟡 MVP SLICE BUILT 2026-06-09 (PR #634, Q-0046).** The round-cash family
> (`services/ai_round_cash_workflow.py`): typed plan (`RoundCashPlan`), deterministic
> capability-to-tool execution (the `round_cash` owner), the evidence-completeness gate,
> and the one typed answer contract (`AIAnswerWithEvidence`/`CalculationEvidence`,
> `calculation_explained`). Faithfulness verification retained as the final backstop —
> the workflow's evidence feeds the same ledger. **Still deferred from this phase:**
> general `BTD6RequestAnalysis` (other intents), clarification rules, the multi-entity
> comparison helper (§7.5), the remaining answer contracts (§10.1), and any structured
> model-call analysis. The exit criterion below is met for the round-cash family only;
> the remaining families follow this proven template.

Implement:

- typed BTD6 request analysis;
- deterministic capability-to-tool planning;
- clarification/default rules;
- calculation evidence and multi-entity comparison helper;
- evidence completeness gate;
- typed answer contracts;
- retain existing faithfulness verification as final backstop.

**Exit criterion:** representative multi-step lookup/calculation/comparison requests
produce correct, grounded, assumption-aware answers under bounded calls.

### Phase 5 — Eval-driven refinement and future-function adoption

Implement:

- orchestration trace graders and expanded golden cases;
- provider/model/preset comparisons;
- tune tool descriptions/examples and task affinity from failures;
- selectively adopt orchestration profiles for future domains;
- consider retrieval-based tool selection or specialized agents only if evals show
  the deterministic selector plus single orchestrator no longer scales.

## 14. Suggested PR slices

1. **PR A — Tool catalogue metadata and strict-schema audit.** ✅ *catalogue metadata
   shipped 2026-06-09 (`ai_tool_catalogue`); the strict-schema audit/validator is still TODO.*
2. **PR B — Named toolsets and deterministic per-request selector.** ✅ *shipped 2026-06-09
   (`select_tools` + `build_registry` toolset policy; compatibility-preserving).*
3. **PR C — Provider-neutral tool choice and dynamic budgets.** ✅ *shipped 2026-06-09
   (neutral `AIToolChoice`/`AIToolBudget` + OpenAI/Anthropic mappings + shared budget loop;
   compatibility-preserving). Safe trace summaries/metrics deferred to PR D/E.*
4. **PR D — Orchestration policy resolver, projection, and mutation ownership.** ✅ *shipped
   2026-06-09 (migration 062 + `ai_orchestration_presets` / `ai_orchestration_policy` /
   `ai_orchestration_mutation` + `AIConfigSnapshot.orchestration` + the `_invoke_gateway` wiring).*
5. **PR E — Tools & workflows admin UI, preview, and dry run.** ✅ *shipped 2026-06-09
   (`ai:tools` panel button → `views.ai.tools`: per-scope profile pickers + dry-run analyzer).*
6. **PR F — BTD6 request analysis and evidence/calculation contracts.** 🟡 *round-cash
   slice shipped 2026-06-09 (#634): `RoundCashPlan` + `CalculationEvidence` +
   `AIAnswerWithEvidence`; the general `BTD6RequestAnalysis` remains.*
7. **PR G — Complex BTD6 plan/execute/verify workflow and answer contracts.** 🟡 *round-cash
   vertical slice shipped 2026-06-09 (#634, Q-0046); remaining families/contracts follow
   the template.*
8. **PR H — Trace/eval expansion and provider/preset tuning.**

Do not combine storage, provider protocol changes, complex BTD6 workflows, and UI
into one PR.

## 15. Tests required before rollout

### Policy and selection

- toolset policies can remove but never grant tools above `AIScope`;
- task affinity and runtime feature constraints cannot be bypassed by presets;
- category/channel precedence and inheritance are deterministic;
- explicit tool disable wins over enabled toolsets;
- built-in presets are immutable through normal guild paths;
- preview/dry-run output exactly matches runtime selection;
- config projection includes effective orchestration source trace.

### Provider/tool execution

- all tool schemas satisfy strict validator rules;
- `NONE`, `AUTO`, required-any/group/tool map correctly for OpenAI and Anthropic;
- required-group cannot call outside its narrowed set;
- max calls/hops/wall/result/fan-out budgets are enforced;
- preflight tools never require model-derived arguments;
- only parallel-safe independent calls run concurrently;
- dispatch/handler validation remains authoritative;
- tool failures are structured and do not crash the whole pipeline.

### BTD6 quality

- complex entity extraction resolves aliases/canonical names correctly;
- ambiguous difficulty/path/degree assumptions trigger clarification when material;
- calculations use deterministic service outputs exactly;
- comparisons evaluate every candidate under identical assumptions;
- data-version/freshness mismatch is visible;
- evidence completeness blocks unsupported claims;
- existing BTD6 faithfulness tests remain green;
- disabled BTD6 tools cause precise refusal/fallback rather than model-memory guesses;
- answer contracts render within Discord limits.

### Eval and observability

- safe traces contain no private reasoning, raw messages, or raw tool results;
- audit/metrics labels are bounded and contain no IDs/arguments;
- evals grade selection, arguments, sequence, evidence, final answer, and budget;
- provider/preset changes cannot ship without running the relevant golden subset.

## 16. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Operators force an irrelevant tool for every channel message. | Descriptor `preflight_safe`/task constraints, UI validation, and prefer required groups over specific tools. |
| More configuration becomes impossible to understand. | Friendly bundled presets, canonical projection, effective-policy preview, source trace, and safe defaults. |
| Narrow selection hides a needed tool. | Deterministic reason codes, dry run, eval cases, and precise “tool unavailable” fallback. |
| Required tools increase latency/cost for trivial questions. | Route/intent-conditional requirements, per-profile budgets, and do not force grounding for conversational/non-factual turns. |
| Model picks a plausible but wrong calculator. | Capability-to-tool mapping, strict schemas, required groups, argument validation, and trace evals. |
| Model changes deterministic numeric results in prose. | Calculation evidence contract, typed answer object, exact-output checks, and final faithfulness guard. |
| Parallel fan-out overloads services. | Descriptor safety metadata, fan-out cap, timeouts, and cost class policy. |
| Tool catalogue metadata drifts from handlers/grounding allowlist. | One canonical descriptor catalogue plus invariant tests deriving toolsets/grounding sets. |
| Provider semantics differ. | Neutral contract, adapter conformance tests, and provider-parity evals. |
| Multi-agent architecture is introduced too early. | Keep one bounded orchestrator; only split when trace evals prove a specific selection/instruction failure. |
| Prompt presets are mistaken for enforcement. | Keep runtime orchestration policy separate and make hard guarantees in request/provider contracts. |

## 17. Product decisions required

1. Should new channels default to all current scope-allowed tools or task-affinity
   toolsets? Recommended: task-affinity toolsets after compatibility rollout.
2. Should factual BTD6 channels require one grounding tool for every factual BTD6
   request? Recommended: yes, but not for social/conversational BTD6 turns.
3. Which BTD6 calculations are allowed to return estimates, and how must estimates
   be labeled?
4. Which omissions require clarification versus a stated default—for example
   difficulty, Monkey Knowledge, hero level, degree, crosspath, or game version?
5. Who may configure toolsets and required tools: administrators, server owner, or
   platform owner only? Recommended: admins may choose safe built-in presets;
   server/platform owners may create advanced overrides.
6. Should custom orchestration profiles be guild-owned, or should v1 allow only
   built-in presets? Recommended: built-in presets first.
7. What are the default call/hop/time/result/fan-out budgets for general, grounded
   BTD6, calculator, and research profiles?
8. Should live/external BTD6 tools require explicit opt-in separately from static
   reference/calculator tools? Recommended: yes.
9. Should an operator be allowed to force a specific tool, or only pre-approved
   preflight tools/required groups in v1? Recommended: required groups and approved
   preflights first; specific-tool forcing later.

## 18. Immediate next-agent brief

Start with the tool catalogue and neutral orchestration contracts. Do not start with
new prompts or UI.

Required first implementation task:

1. inventory every current `AIToolSpec` and handler;
2. propose `AIToolDescriptor` metadata, named toolsets, and one canonical catalogue;
3. define strict-schema validation and identify incompatible existing schemas;
4. define provider-neutral tool choice and budget contracts;
5. define deterministic selection precedence and exclusion reasons;
6. add tests proving current default behavior remains compatible and policies can
   only narrow authority;
7. add orchestration selection/trace cases to the eval harness design.

Do **not** in the first PR:

- add a multi-agent framework;
- allow write-capable tools;
- let operators enter arbitrary tool names or provider-specific `tool_choice` JSON;
- remove the existing BTD6 faithfulness guard;
- use prompt instructions as the only enforcement for required tools;
- force a specific argument-requiring tool on every channel request;
- expose model chain-of-thought in traces or Discord;
- add custom guild orchestration profiles before built-in contracts are stable.

## 19. Definition of success

The initiative succeeds when a server operator can choose a clear Tools & Workflows
preset for a channel; SuperBot deterministically offers only the relevant authorized
tools; factual or calculation-heavy BTD6 requests reliably call the required lookup
or calculator family; complex comparisons use consistent assumptions and deterministic
math; every answer is supported by bounded evidence; disabled tools stay disabled;
and failures produce precise, inspectable fallbacks instead of plausible guesses.
