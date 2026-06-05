# AI choke-point guard coverage map (RC-11)

> **Purpose.** RC-11 / roadmap PR 10 / Ideas Lab §6 gate AI feature expansion (and
> any new AI write/action tool) on guard tests being in place. This doc verifies
> those guards **already exist** and maps each required guarantee to the test that
> pins it, so a future AI-expansion session can treat the gate as satisfied —
> *without* re-deriving the coverage and without touching the central stage.
>
> **Date:** 2026-06-05. This is a verification artifact (wave PR6); it adds no
> tests because the guarantees are already covered — re-pinning them would be
> redundant and risks asserting non-current behavior on a confirmed-healthy
> subsystem (priority map: "do not refactor the AI central stage").

## The central choke point

`disbot/core/runtime/ai/natural_language_stage.py` is the single pipeline stage
for natural-language AI. Its documented steps (module docstring) end with
`ai_decision_audit_service.record()` on every terminal path. There are 10
`record(...)` call sites (one per outcome), and the cooldown check sits at
`:301-326` — *after* policy resolution, recorded as
`PolicyDenialReason.COOLDOWN_ACTIVE`.

## Guarantee → guard test

| RC-11 guarantee | Pinned by |
|---|---|
| **One audit row per stage invocation** (after retry/floor; exactly once, not zero/duplicate) | `tests/unit/runtime/ai/test_natural_language_stage.py::test_triggering_mention_recorded_exactly_once_after_success` and `::…_after_denied` |
| **Every terminal outcome audits** (replied / degraded / skipped / errored / send-failure) | same file: `test_replied_audit_carries_provider_and_model`, `test_degraded_response_audits_as_degraded`, `test_healthy_empty_response_audits_as_skipped`, `test_gateway_raises_audits_as_errored`, `test_send_failure_video_task_writes_video_send_failed`, `test_send_failure_non_video_task_writes_response_send_failed` |
| **Cooldown ordering** (checked after policy, before the provider call; denial recorded) | stage `:301-326`; the denied-path audit-once test exercises a denial → `record`. *(See "Optional refinement" below.)* |
| **Read-only grounding-tool whitelist** (no write/action tools offered) | `tests/unit/services/test_ai_tools.py` (whole file): `test_build_registry_returns_specs_and_matching_handlers`, the `BTD6_GROUNDING_TOOL_NAMES == registered` + `all(name.startswith("btd6_"))` assertions, `test_admin_scope_offers_all_read_only_tools`; plus `ai_tools.py`'s "every tool here is **read-only**" contract |
| **Tool ledger only captures grounding results** | `tests/unit/runtime/ai/test_natural_language_stage.py::test_ledger_captures_only_btd6_tool_results` |
| **I-2 non-mutating** (projection/readiness services never mutate/append/audit/call providers) | `tests/unit/services/test_ai_readonly_invariants.py` (AST scan) |
| **Decision-audit service correctness** | `tests/unit/services/test_ai_decision_audit_service.py` |
| **Provider neutrality / gateway seam** | `tests/unit/runtime/ai/test_gateway.py`, `test_anthropic_provider.py`, `test_openai_provider.py`, `test_tool_calling.py`, `test_safety_and_routing.py` |
| **Grounding / faithfulness guard** (BTD6 leak refused, healthy-empty refused, verifier-crash fails closed) | same stage file: `test_general_path_btd6_leak_is_refused`, `test_btd6_healthy_empty_reply_is_refused`, `test_btd6_verifier_crash_fails_closed`, `test_btd6_grounded_answer_is_served` |

## Verdict

**The RC-11 gate is satisfied by existing coverage.** The audit-row-once,
read-only-tool-whitelist, I-2 non-mutating, and grounding-guard guarantees are all
pinned. No new guard test was added in this pass (it would duplicate the above).

## Optional refinement (for the AI-expansion session, not now)

The one guarantee covered only *indirectly* is **cooldown ordering** — the
denied-path audit-once test exercises a denial, but there is no test that
specifically asserts: when `ai_permission_service.is_on_cooldown(...)` is True,
the stage records exactly one `COOLDOWN_ACTIVE` row **and never calls the
gateway**. A future session that owns the AI-stage test harness (`stub_services`)
can add that focused test cheaply. It is deliberately left to that session rather
than written here blind, per the must-not-touch-the-stage rule.

## Before adding any AI write/action tool

Ideas Lab §6 rejects new AI write/action tools until this gate is affirmatively
extended. When that work starts: add a guard to `tests/unit/services/test_ai_tools.py`
asserting the new tool's scope/permissioning, and re-affirm that
`build_registry(...)` offers only the intended set — do not weaken the read-only
contract in `ai_tools.py` without an ADR.
