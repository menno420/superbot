# Plan: AI tool-calling (BTD6 lookup as the first tool)

> **Status:** `reference` — **IMPLEMENTED.** The BTD6 lookup tools described here now ship in
> `services/ai_tools.py` — `btd6_lookup`, `btd6_list_roster` (the complete
> heroes/towers/paragons roster, #468), `btd6_capability_lookup`,
> `btd6_superlative_lookup`, `btd6_difficulty_cost`, and the two paragon tools
> — wired into the central AI request path. `btd6_capability_lookup` covers camo
> detection plus lead/black/white/purple popping and returns a coverage note so
> the model states its data limits. This doc is retained as the design record;
> the sections below describe the architecture as built.
>
> **#468 added a faithfulness backstop:** the natural-language stage now verifies
> every BTD6 answer against the grounded payload (auto-grounding facts ∪ approved
> BTD6 tool results) and rejects → regenerates-once → version-stamped-refuses
> rather than serve an ungrounded name/number. Only the `btd6_*` tools ground an
> answer (the ledger allowlist `ai_tools.BTD6_GROUNDING_TOOL_NAMES`). See
> `btd6-gamedata-decode-status.md` → "Next steps" for the data-side roadmap that
> feeds it (e.g. wiring `textTable` descriptions into grounding).
>
> Motivation: today the AI only "knows" what we *pre-inject* into its prompt
> via trigger-gated knowledge blocks. When a trigger misses, the model answers
> from (often wrong) memory — e.g. it called the tier-5 *True Sun God* the
> "most expensive Paragon". Broad-gating (PR #377) mitigates this; **tool-calling
> is the proper fix**: give the model a function it can *call when it decides it
> needs data*, so there's no phrase-matching and no guessing.

## Current architecture (verified)

```
core/runtime/ai/natural_language_stage.py
  ├─ gathers knowledge blocks (bot_knowledge_service + btd6_ai_knowledge_block_service)
  ├─ builds the instruction stack (ai_context_service / ai_instruction_service)
  └─ AIRequest(system_prompt=..., payload={"text": ...}, mode, max_output_tokens)
        → services.ai_gateway.execute(request)            # thin shim
            → core/runtime/ai/gateway.py AIGateway.execute # THE chokepoint
                 feature-flag → routing(task→provider/model) → redaction
                 → provider.<call>()                        # single provider call
                 → parse text/JSON → AIResponse
```

Key facts that shape the design:
- **`AIRequest`** (`core/runtime/ai/contracts.py`): `context`, `system_prompt: str`,
  `payload: dict`, `mode` (TEXT/JSON), `response_schema`, `max_output_tokens`,
  `timeout_seconds`. **No `tools` field.**
- **`AIResponse`**: `text` / `data` / `suggestions` / `degraded` / `fallback_reason`.
  **No tool-call representation.**
- **Gateway** is "the single chokepoint for provider calls" — 1 execute = 1
  provider call, with redaction + degraded handling per call.
- **Providers** (`core/runtime/ai/providers/`): `base.Provider` Protocol,
  `openai_provider` (OpenAI `client.chat.completions.create`), `deterministic_provider`.
  No Anthropic provider; no tool plumbing.
- The NL stage is heavily tested (`tests/unit/runtime/ai/test_natural_language_stage.py`,
  fan-out 76) — high blast radius.

## Design

### 1. Provider-neutral tool contracts (`core/runtime/ai/contracts.py`)
- `ToolSpec`: `name: str`, `description: str`, `parameters: dict` (JSON Schema).
- `ToolCall`: `id: str`, `name: str`, `arguments: dict`.
- `ToolResult`: `id: str`, `content: str` (JSON-encoded result text).
- `AIRequest.tools: tuple[ToolSpec, ...] = ()` (additive, default empty → today's behaviour unchanged).
- Keep tool *execution* out of the contracts (pure data).

### 2. Tool loop — put it in the gateway (keeps the chokepoint invariant)
`AIGateway.execute` gains an internal loop when `request.tools` is non-empty
**and** the routed provider advertises tool support:
```
for _ in range(MAX_TOOL_ITERS):           # cap (e.g. 4) — bounds cost/latency
    resp = await provider.call(..., tools=specs, prior_messages=msgs)
    if not resp.tool_calls: break
    for call in resp.tool_calls:
        result = await registry.execute(call, ctx)   # allowlisted, read-only
        msgs.append(tool_result(call.id, result))
return final AIResponse(text=...)
```
- Redaction still runs on every provider call; tool args/results pass through
  the same redaction + are treated as **untrusted data** (never instructions).
- A `MAX_TOOL_ITERS` cap + per-call timeout prevents loops/runaway cost.
- Providers without tool support (deterministic) ignore `tools` → single-shot,
  so nothing regresses.
- *Alternative considered:* orchestrate the loop in the NL stage. Rejected —
  it spreads provider-call logic outside the chokepoint and duplicates
  redaction/degraded handling.

### 3. Tool registry + executor (new, e.g. `core/runtime/ai/tools.py`)
- A registry: `name → async handler(args: dict, ctx: AIRequestContext) -> str`.
- **Allowlisted + read-only.** Handlers may only *read* (services/fixtures);
  no mutations, no DB writes, no network. Validate args against the ToolSpec
  schema before dispatch; unknown tool / bad args → structured error result
  (fed back to the model, never raised).
- Which tools a request may use is set by the caller (NL stage), per task —
  BTD6 task gets BTD6 tools only.

### 4. Provider support (`openai_provider.py`)
- Translate `ToolSpec` → OpenAI `tools=[{type:"function", function:{...}}]`,
  pass `prior_messages`, parse `choice.message.tool_calls` → `ToolCall`s.
- Advertise capability (`provider.supports_tools = True`).
- `deterministic_provider`: `supports_tools = False`.
- (Future: an Anthropic provider would map ToolSpec → its `tools` block; the
  neutral contracts already allow it.)

### 5. BTD6 tools (the first consumers) — `services/btd6_ai_tools.py`
Thin wrappers over **existing** read-only services (no new data logic):
- `btd6_price(kind, n)` — `kind ∈ {tower, upgrade, paragon}`, highest/lowest;
  backs onto `btd6_knowledge_service.upgrades_by_price` + base costs. Returns
  the distinct tower/upgrade/Paragon facts (the thing the model keeps confusing).
- `btd6_tower_stats(tower, crosspath="000")` — `btd6_stats_service` normal/pro
  stats for a specific crosspath (fixes "give me the 4-0-0" precisely).
- `btd6_list(category=None)` — roster from `btd6_knowledge_service`.
Each returns compact JSON. Register them; expose to the BTD6 task in the NL stage.

### 6. Enablement / migration
- Feature-flag the whole loop (off → exact current behaviour).
- Additive: keep the knowledge-block grounding as the fallback while tools bake.
- Once tools prove reliable for BTD6, *loosen/retire* the now-redundant
  price/catalog trigger gating (PR #377) to cut prompt size.

## Testing
- Contracts: ToolSpec/ToolCall/ToolResult round-trip.
- Registry: allowlist, arg validation, read-only guarantee, error→result.
- Gateway loop: tool_call → execute → re-call → final; `MAX_TOOL_ITERS` cap;
  provider-without-tools path unchanged; redaction on tool args/results.
- openai_provider: ToolSpec→API and tool_calls→ToolCall (mock the client, like
  existing provider tests).
- BTD6 tools: each handler against the real fixtures (Monkey Ace Paragon
  $900k; 4-0-0 Glue Gunner = Bloon Liquefier).
- NL stage: BTD6 task offers the tools; **don't break the existing 76-fan-out tests.**
- Pin: non-tool requests are byte-for-byte unchanged (regression guard).

## Risks & mitigations
| Risk | Mitigation |
|---|---|
| Core/shared blast radius (NL stage, gateway) | Additive contracts; feature-flag; pin "no-tools = unchanged" |
| Provider-neutral tool formats diverge | Neutral ToolSpec; per-provider translation; only OpenAI first |
| Tool loop cost/latency / infinite loop | `MAX_TOOL_ITERS` cap + per-call timeout |
| Trust model (tools that act) | Allowlist; read-only handlers; args validated; outputs = untrusted data |
| Breaking heavy AI tests | Build behind flag; expand tests before flipping default |
| AI-config doc-pins (`docs/ai-config-ownership.md`) | Review/extend pins; route tools through existing config seams |

## Suggested PR sequence
1. **Contracts + gateway loop scaffold** behind a flag; deterministic provider
   no-op; full unit tests; "no-tools unchanged" pin. *(no behaviour change)*
2. **openai_provider tool support** + a trivial echo tool + round-trip tests.
3. **BTD6 tools** (`btd6_ai_tools.py`) over existing services + register +
   enable for the BTD6 task in the NL stage + integration tests.
4. **Tune**: loosen the redundant knowledge-block gating; measure prompt-size win.

## Files to touch
- `core/runtime/ai/contracts.py` — tool dataclasses + `AIRequest.tools`
- `core/runtime/ai/gateway.py` — the loop + `MAX_TOOL_ITERS`
- `core/runtime/ai/tools.py` *(new)* — registry/executor
- `core/runtime/ai/providers/{base,openai_provider,deterministic_provider}.py`
- `services/btd6_ai_tools.py` *(new)* — BTD6 read-only handlers
- `core/runtime/ai/natural_language_stage.py` — offer tools for the BTD6 task
- `docs/ai-config-ownership.md` — record the new capability + any config seam

## Why not now
Honest call: a provider-neutral tool loop in the AI chokepoint, plus a registry
and trust model, is a multi-PR change to shared code I'd want to land
incrementally behind a flag with the existing AI test-suite green at each step
— not something to start with a compaction imminent. Broad-gating (PR #377)
already fixes the user-visible bug; this is the durable upgrade.
