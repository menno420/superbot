# 2026-06-09 — Lane 3: Orchestration Phase 4 MVP (round-cash vertical slice)

**PR:** #634 (draft → ready same session) · **Branch:** `claude/blissful-darwin-dzjlol`
**Parallel session:** Agent 2 of a deliberately parallelized multi-lane run — Agent 1 on
Lane 2 (adaptive P1B, landed as draft #632 mid-session), another agent on Lane 6 (#631).
Surfaces verified disjoint before editing (live `list_pull_requests` at start +
re-checked before push; zero open PRs at start, #631/#632 appeared during the session
and touch governance/access/router files only).

## Arc

Executed the multi-lane plan's Lane 3 (Q-0046): the **one vertical slice** of
orchestration Phase 4 — plan→execute→verify for the round-cash question family
("cash from A to B", "can I afford X at round R?") + **one** typed
answer-with-evidence contract. Read route: CLAUDE.md → current-state →
multi-lane plan → orchestration plan §4–§9 → Q-0043/Q-0046 → `round_cash` owner →
`_invoke_gateway` seam → contracts → Phase 1–3 tests.

## Shipped

- `services/ai_round_cash_workflow.py` — conservative deterministic planner
  (`RoundCashPlan`), execution via the existing `btd6_data_service.round_cash`
  owner (afford = compose on cumulative outputs, no-spending default stated),
  §10.2 evidence-completeness gate **including the Q-0043 identity check**
  (`range_cash == cum(B) − cum(A−1)`; corrupt data degrades to a precise
  *unsupported* answer), and the two render seams (system block + ledger entry).
- `core/runtime/ai/contracts.py` (+): `CalculationEvidence` (§7.4) +
  `AIAnswerWithEvidence` (§10.1, `calculation_explained`, explicit
  `inclusive_range` carrying Q-0043).
- `_invoke_gateway`: profile-gated activation on the resolved decision's
  `workflow == "analyze_execute_verify"`; default profile (`direct_or_tool`)
  never engages → byte-identical (pinned); workflow faults degrade to the
  unchanged request; evidence rides the system prompt + faithfulness ledger
  (deduped across the regenerate-once retry).
- 23 tests (17 workflow + 5 wiring + the existing 3 wiring stay green). Full CI
  mirror green (8422 passed), arch strict 0 errors, **live boot clean**
  (Galaxy Bot login, 0 ERROR/Traceback).

## Key findings (for the next §7 family)

- **The presets already declared the `workflow` labels** — Phase 4 needed zero
  preset/catalogue/migration changes. The activation gate is purely the resolved
  `OrchestrationDecision.workflow` consumed in `_invoke_gateway`.
- **The faithfulness verifier is a comma-normalised substring test**
  (`utils/btd6/name_guard.offending_numbers`) — a workflow ledger entry must carry
  **both** number forms (formatted `$19,840.00` and raw JSON `19840.0`) or the
  guard can refuse a correct reply restating the formatted form.
- `stack.user_message` is the right planner input (the wrapped current message —
  delimiters are digit-free, regexes work through the envelope); the payload text
  would include recent turns/facts and could match a *previous* question.
- The workflow only runs when `AI_TOOLS_ENABLED` is on (it lives inside the
  Phase 3 orchestration block) — same posture as the rest of the resolved policy.

## Flagged for maintainer

**Production model-loop check needed** (sandbox has no AI provider key): set a
channel to `btd6_grounded`/`btd6_grounded_strict` via `ai:tools`, ask "how much
cash from round 50 to 60?", confirm $19,840 inclusive + assumptions in the reply.

## Context delta

- **Needed but not pointed to:** `utils/btd6/name_guard.py` number-matching
  semantics — the Lane 3 brief routed to the gateway/owner/contracts but not to
  the faithfulness verifier internals, which turned out to be a correctness
  constraint on the evidence-ledger format (see Key findings).
- **Pointed to but didn't need:** orchestration plan §8 (provider mapping) and §9
  (storage/ownership) — fully shipped in Phases 2–3; reading the progress notes
  at the top of the plan would have sufficed for those sections.
- **Discovered by hand:** `InstructionStack.user_message` is the
  `wrap_untrusted_text`-wrapped current message (not raw text) — found only by
  tracing `assemble()`; worth knowing for anything that parses the user's turn
  server-side.
