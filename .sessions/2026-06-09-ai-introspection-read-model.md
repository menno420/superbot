# 2026-06-09 — AI + BTD6 answerability Phase 2 (central introspection read model)

## Arc

"Continue with the work from PR 612." #612 (merged) shipped the AI tool orchestration
**Phase 1 foundation** (`ai_tool_catalogue`) + BTD6 round-cash answerability (1A/1B). Two
docs named different "next" steps: PR #612's body said orchestration Phase 2, but
`current-state.md`'s ▶ Next action (the later end-of-session reconciliation) recommended
**answerability Phase 2 first** — "the read-only AI introspection read model … now unblocked
because it can compose the new catalogue (lower-risk, additive, read-only)." Took the
documented recommendation: it's the lower-risk, additive, gate-safe continuation (the
authoritative living ledger outranks the mid-PR "Next" note, and its rationale held up).

## Shipped

- **`services/ai_introspection_service.py`** (new, ~330 LoC) — read-only composition over the
  existing AI owners; **no new registry, no AI exposure, no UI**. Four bounded, typed,
  frozen, audience-filtered builders:
  - `build_tool_catalog(scope)` — joins `ai_tools.all_tool_specs()` (authoritative
    `min_scope` + purpose) with `ai_tool_catalogue.CATALOGUE` (toolsets/grounding/cost/
    freshness); a tool is visible only when `scope_allows`; higher-scope tools are *counted*,
    never named.
  - `build_btd6_answerability()` — deterministic fixtures (with real counts) + calculations +
    the one live domain + **explicit unsupported gaps** (ABR / achievements / Rogue-Frontier /
    modified-economy), from `btd6_data_service`. Degrades to `available=False` when data is
    unavailable.
  - `build_ai_settings_view(guild_id, scope)` — reuses `ai_config_projection_service.build_snapshot`,
    redacted by tier (everyone: enabled flags; admin+: effective config; platform-owner:
    provider runtime diagnostics).
  - `build_policy_explanation(ctx, scope)` — composes `ai_natural_language_policy.resolve`
    (dry-run precedence trace) + bounded `ai_decision_audit_service` history; trace +
    cross-user history are admin+ only; audit-read failure degrades to an empty history
    without sinking the authoritative decision.
- **`services/ai_tools.py`** — added `all_tool_specs()` (+ the `_ALL_TOOL_SPECS` tuple): every
  registered tool's spec keyed by name, **with no runtime binding** (no guild/member/bot, no
  handlers) — the runtime-independent catalogue half a read model / effective-policy preview
  needs. Pinned `== CATALOGUE` by a new drift test.
- **Tests** — `tests/unit/services/test_ai_introspection_service.py` (15) + the catalogue
  drift test (1). Audience redaction, metadata join, fixture/calculation/live/unsupported
  split, degraded states, dry-run gating, audit-failure degrade.

## Key design choices

- **Audience filtering at construction (AR-08 / roadmap §5.6), never by prompt wording.**
  One scope model (`AIScope` + `scope_allows`); `min_scope` stays the tool authority.
- **Compose, never replace.** Each builder reads one existing owner; the service owns no
  data, no persistence, no mutation seam. Avoids the "god service" risk via small independent
  sub-builders + strict services→{services,core} import direction.
- **Stayed inside the additive/read-only envelope.** No AI tool registration (Phase 3) and no
  UI (Phase 4) — those are the genuinely gated steps. This mirrors Phase 1A: the deterministic
  owner ships before its gated exposure, so building the read *model* doesn't promote gated work.
- **Low-drift BTD6 inventory.** Domain counts come straight from `get_dataset()`; I did **not**
  hand-maintain a domain→tool map (the exact drift the catalogue just killed) — tool exposure
  lives in the tool-catalogue snapshot instead.

## Verification

- `python3.10 scripts/check_quality.py --full` → lint+mypy clean, **8307 passed, 3 skipped**.
- `python3.10 scripts/check_architecture.py --mode strict` → 0 errors (new module imports
  core + services only). `check_docs` clean.
- **Live smoke** (real catalogue/dataset/DB): tool catalogue tiers USER 28 / ADMIN 30 /
  PLATFORM_OWNER 31 (hidden 3/1/0); BTD6 answerability inventories the real dataset
  (rounds 140, monkey_knowledge 134, …, v1.0/game 55.0) with calc/live/unsupported split;
  settings view + policy explanation against the unconfigured DB redact correctly per tier
  (USER hides provider/trace/history; only PLATFORM_OWNER sees `degraded`).

## Context delta

- **Needed but not pointed to:** there was **no runtime-independent enumeration of the tool
  specs** — `build_registry` needs live `guild`/`member`/`bot` and conditionally includes
  tools. A read model can't stand up a live registry just to list names, so the clean fix was
  a flat `all_tool_specs()` accessor pinned to the catalogue. Worth knowing for any future
  preview/dry-run surface (orchestration Phase 3 will want the same).
- **Pointed to but didn't need:** the orchestration plan's Phase 2–5 (tool-choice, budgets,
  storage, UI) and the answerability roadmap's Phase 3–5 — all later/gated; only Phase 2's
  §4/§5.3/§5.6 drove this.
- **Discovered by hand:** `current-state.md` (the living ledger) and the merged PR #612 body
  **disagreed on next-step ordering**; the folio still said the answerability roadmap was
  "fully gated." Resolved by precedence (living ledger > mid-PR note) + scoping to the
  read-model-only layer both agree is safe, and corrected the folio line.
- **Unresolved for next session:** reconcile this PR's #; then either **orchestration Phase 2**
  (neutral tool-choice + budgets — higher-risk, edits provider adapters, needs a live provider
  to fully verify) or **answerability Phase 3** (scope-filtered self-awareness *tools* that
  expose this read model — gated; needs the AI-exposure gate explicitly lifted, like the
  one-off AR-10 lift for `btd6_round_cash`).
