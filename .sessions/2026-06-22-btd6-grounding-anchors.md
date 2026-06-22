# 2026-06-22 — P1-1 BTD6 grounding-anchor eval guard (the #704 finding)

> **Status:** `in-progress`
> **Run type:** routine · dispatch

## What I'm about to do

Scheduled dispatch fire, no work order → advance the next ▶ startable plan slice.
`dispatch_menu --unattended` pick: **S2 (Next) — P1-1 BTD6 eval cases** (🟢 offline-verifiable,
self-mergeable). The lane is the [#704 live-test triage](../docs/audits/pr704-live-test-triage-2026-06-14.md)
finding, routed to P1-1: *"capability message must match refusal behaviour; asserted BTD6 numbers
must be grounded."*

This PR encodes both halves as **offline, no-DB, deterministic** guards over the eval golden set:

1. **Grounding-anchor guard** (`tests/evals/test_btd6_grounding_anchors.py`) — every BTD6 number the
   golden set asserts (Despo 0-4-1 Impoppable $12,025 / ×10 $120,250; Elite Lych HP per tier; ABR
   r25-83 $113,872.30; round-cash ranges 60-68 / 50-60 / 54-70) must be **reproducible from
   `services.btd6_data_service`** AND appear in the named eval case's rubric. Closes the data-drift
   *and* prose-drift directions: a re-seed that changes a price, or an edited rubric number, fails
   the guard instead of the eval silently grading against a stale "truth".
2. **Capability-consistency guard** — the `ai_introspection_service` BTD6 answerability snapshot must
   advertise exactly what the deterministic layer can/can't do (round_cash projection *supported* as a
   `calculation`; `modified_economy` listed as a guarded "NOT applied" domain), so the capability
   message can never drift back to the #704 over-promise.

Small enabling change: `tests/evals/graders.py` exposes `.rubric` / `.subgraders` metadata on
`llm_judge` / `all_of` / `any_of` so the guard can read rubric prose (grading behaviour unchanged).

Verified offline before writing: all anchor numbers reproduce from `btd6_data_service` (probed).
