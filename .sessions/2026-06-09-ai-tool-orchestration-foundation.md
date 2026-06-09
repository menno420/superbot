# 2026-06-09 — AI tool orchestration: Phase 1 foundation (catalogue + selector)

## Arc

Continuation of the same session as the AI+BTD6 answerability work. After shipping round-cash
Phase 1A+1B, I recommended the orchestration foundation (the AR-10 lane) as the highest-leverage
next step; the maintainer said "continue in your recommended order." Implemented **Phase 1**
(PR slices A+B) of `docs/ai/ai-complex-request-tool-orchestration-plan.md`: the canonical tool
catalogue + a deterministic, compatibility-preserving selector. This is the foundation AR-10
wanted *before* net-new tools — and it now houses the `btd6_round_cash` tool that Phase 1B
added under a one-off AR-10 lift.

## Shipped

- **`core/runtime/ai/contracts.py`**: `AIToolMetadata` (per-tool selection metadata —
  toolsets, task_affinity, grounding_domain, cost/freshness/parallel/preflight hints) and
  `ToolExclusionReason` (stable, preview-safe reason codes).
- **`services/ai_tool_catalogue.py`** (new): named-toolset constants (§5.2), the canonical
  `CATALOGUE` (one `AIToolMetadata` per registered tool — 31 of them), `scope_allows`
  (canonical home), `grounding_tool_names()` (derives the BTD6 allowlist), and the
  deterministic `select_tools` (scope → explicit-disable → toolset precedence).
- **`services/ai_tools.py`**: `build_registry` consults `select_tools` and gained optional
  `enabled_toolsets`/`disabled_tools` params (default `None` = unchanged); `_scope_allows`
  re-exports the catalogue's `scope_allows`; `BTD6_GROUNDING_TOOL_NAMES` is now **derived**
  from the catalogue (the hand-maintained 21-name frozenset is gone).
- **`tests/unit/services/test_ai_tool_catalogue.py`** (new, 12 tests): drift guard
  (catalogue == registered tools), derived grounding set, default == compatibility, toolset
  narrowing, and the key invariant — **enabling a toolset never grants a tool above scope**.

## Key design choices

- **One source of truth, no parallel registry.** The catalogue keys on tool *name* →
  metadata; `min_scope` stays authoritative on the `AIToolSpec`. The selector can only
  remove tools, never add. This is the §16 "catalogue drift" mitigation made real.
- **Compatibility first.** `build_registry()` with no policy returns byte-identical output;
  every existing `ai_tools`/NL-stage test stayed green (8278 passed total).
- **Scoped to PR A+B.** No provider tool-choice/budget changes (Phase 2), no storage/UI
  (Phase 3), no workflow (Phase 4), no requirement modes yet. Deferred within Phase 1: the
  strict-schema validator and a runtime-availability-aware preview (the selector emits reason
  codes but doesn't re-derive `runtime_unavailable` — that joins Phase 3's dry-run).

## Verification

- `python3.10 scripts/check_quality.py --full` → lint+mypy clean, **8278 passed, 16 skipped**.
- `python3.10 scripts/check_architecture.py --mode strict` → 0 errors (new module:
  services→core import only).
- Live demo: `build_registry(scope=USER, enabled_toolsets={btd6_rounds})` →
  `{btd6_round_composition, btd6_round_cash, btd6_bloon_filter}`; enabling
  `server_context_sensitive` at USER scope → `[]` (admin tools never granted); derived
  grounding set = 21 btd6 tools.

## Context delta

- **Needed but not pointed to:** the handler shape in `build_registry` — some handlers are
  plain coroutines, some are factory results bound to runtime args (`_make_*`). That's why a
  *static* catalogue must key on name+metadata and let `build_registry` keep building the
  runtime (spec, handler) pairs; the selector then filters. A naive "fully static descriptor
  list with handler_factory" (as the plan's §5.1 sketch implies) would fight that runtime binding.
- **Pointed to but didn't need:** the plan's §6–§12 (presets, provider mapping, budgets,
  evals) — all later phases; only §4–§5 + §13–§14 + §18 drove this slice.
- **Discovered by hand:** the black↔ruff COM812 fight on wrapped calls — resolved by writing
  the magic-trailing-comma expanded form (both tools accept it) or keeping calls ≤88 chars.
  Worth knowing before chasing a lint loop.
- **Unresolved for next session:** reconcile this PR's #; orchestration Phase 2 (neutral
  tool-choice + budgets, provider adapters) is next, then the answerability Phase 2
  introspection read model can compose this catalogue.
