# 2026-06-09 — AI tool orchestration Phase 2 (provider-neutral tool-choice + budgets)

## Arc

After shipping answerability Phase 2 (#616, merged) I offered the maintainer the fork
between the two logical next steps; they chose **orchestration Phase 2 first**. Implemented
PR slice C of `docs/ai/ai-complex-request-tool-orchestration-plan.md`: provider-neutral
tool-choice + budgets, mapped onto both provider adapters — the live tool-loop (the
"confirmed-healthy, preserve" choke point), so the whole job was *additive, defaults
byte-identical*.

## Shipped

- **`core/runtime/ai/contracts.py`**: `ToolRequirementMode` (NONE / AUTO / REQUIRED_ANY /
  REQUIRED_GROUP / REQUIRED_TOOL), `AIToolChoice`, `AIToolBudget`, and `tool_choice`/
  `tool_budget` fields on `AIRequest`. **Defaults reproduce today's behaviour** (AUTO choice;
  `max_hops=4`; `max_calls`/`max_wall_seconds`/`max_result_chars` = `None` = no cap).
- **`core/runtime/ai/providers/base.py`**: shared `ToolLoopState` (hop / call / wall-time
  caps via `may_offer_tools` + `record_call`) and `cap_tool_result` — so both adapters enforce
  the budget identically and the rule is tested once.
- **`openai_provider.py` / `anthropic_provider.py`**: each `execute` loop now ranges over
  `budget.max_hops`, gates each hop through `ToolLoopState`, caps each tool result, and maps
  the policy onto the native `tool_choice` via `_openai_tool_choice` / `_anthropic_tool_choice`
  — REQUIRED_* forces on the **first** hop then relaxes to auto (so a later hop can answer);
  REQUIRED_GROUP rides the resolver-narrowed set; NONE offers no tools (single-shot).
- **`gateway.py`**: the redaction reconstruction is now `dataclasses.replace(request, …)`
  instead of a field-by-field `AIRequest(...)` — it had silently dropped `tools`-adjacent new
  fields. Root-cause fix: any future `AIRequest` field now survives redaction automatically.
- **Tests** — `tests/unit/runtime/ai/test_tool_orchestration.py` (18): contract defaults,
  `ToolLoopState`/`cap_tool_result`, all five modes × both adapters (mapping + end-to-end
  loop), call/result budget exhaustion, and the gateway redaction-preservation regression.

## Key design choices

- **Compatibility is the headline.** The default budget enforces only the historical hop
  limit; every existing provider/gateway test stayed green untouched. Tighter caps are opt-in
  and adapter-enforced (plan §11).
- **REQUIRED_* forces once, then relaxes.** Forcing a tool on *every* hop would burn the
  budget and never let the model synthesise an answer; forcing only hop 0 guarantees "at least
  one" while keeping the loop terminating.
- **REQUIRED_GROUP stays a resolver concern.** The adapter (core layer) has no catalogue
  knowledge, so group *narrowing* is the resolver's job (Phase 3); the adapter just maps
  REQUIRED_GROUP → provider "require any" over the already-narrowed set. Documented in the
  mapping helpers.
- **Fixed the redaction drop-bug at the seam, not per-field.** `replace()` is the one-source
  fix (CLAUDE.md root-cause preference) and closes the class for all future fields.

## Verification

- `python3.10 scripts/check_quality.py --full` → **8327 passed, 3 skipped**; black/isort/ruff/
  mypy clean (isort/black initially flagged the new test file — `check_quality` lints `tests/`
  even though the GH workflow excludes it; fixed with `python3.10 -m isort/black`).
- `python3.10 scripts/check_architecture.py --mode strict` → 0 errors. `check_docs` clean.
- Import + contract smoke: providers load; default `AIRequest` = AUTO/hop-4/no-caps;
  `dataclasses.replace` preserves the new fields. Clean bot boot (AI degraded in sandbox — no
  provider key — so live tool-choice must be verified on the maintainer's prod bot).

## Context delta

- **Needed but not pointed to:** the gateway redaction at `gateway.py:254` **reconstructs**
  `AIRequest` field-by-field rather than `replace()`-ing it — a silent drop point for any new
  request field. Easy to miss; the new redaction-preservation test guards it. Worth checking
  the same pattern isn't repeated at other "rebuild a frozen contract" seams.
- **Pointed to but didn't need:** the plan's §12 (metrics/eval) and §9 (storage/UX) — Phase 3+;
  only §4–§5, §8, §11, §13–§14 drove this slice. Safe trace summaries (plan §12.1) deferred
  with Phase 3, where the orchestration trace + projection land.
- **Discovered by hand:** `check_quality.py` lints `tests/` for black/isort even though
  CLAUDE.md says CI excludes `tests/` — a new test file with non-trivial imports (aliased
  re-imports) can redden the local mirror while CI would pass. Run the formatters on new test
  files too.
- **Cross-agent collision (resolved):** the boot-check spotlight fix I committed turned out to
  duplicate **#617** (`fix/spotlight-logger-import`), which merged to `main` first — so the PR
  went `mergeable_state: dirty`. Resolved by **dropping my redundant commit** (reset to the new
  `main`, cherry-pick only the orchestration commit, force-push) and deferring to #617's version.
  Lesson: when a fix is "pre-existing + unrelated," expect another agent may be fixing it too;
  keeping it a **separate commit** made the drop a one-liner. Check open PRs for the same file
  before committing an adjacent fix.
- **Unresolved for next session:** reconcile this PR's #. Next is **orchestration Phase 3**
  (typed policy storage + projection + the Tools & Workflows admin UX) or **answerability
  Phase 3** (the scope-filtered self-awareness tools — net-new AI exposure, needs the gate
  lifted). Live tool-choice/budget behaviour wants a provider-keyed (prod) check.
