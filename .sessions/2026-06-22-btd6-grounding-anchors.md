# 2026-06-22 — P1-1 BTD6 grounding-anchor eval guard (the #704 finding)

> **Status:** `complete`
> **Run type:** routine · dispatch

## What this run did

Scheduled dispatch fire, no work order → advanced the next ▶ startable plan slice.
`dispatch_menu --unattended` pick: **S2 (Next) — P1-1 BTD6 eval cases** (🟢 offline-verifiable,
self-mergeable). The lane is the [#704 live-test triage](../docs/audits/pr704-live-test-triage-2026-06-14.md)
finding, routed to P1-1: *"capability message must match refusal behaviour; asserted BTD6 numbers
must be grounded."* **PR #1295.**

Shipped both halves of the finding as **offline, no-DB, deterministic** guards over the eval golden
set:

1. **Grounding-anchor guard** (`tests/evals/test_btd6_grounding_anchors.py`, new) — an explicit
   **anchor table** pairs each BTD6 *knowledge* case id with a deterministic re-derivation from
   `services.btd6_data_service`, and checks **both directions**:
   - the derived value must equal the truth the golden set asserts (data drift → fail), and
   - that truth must appear, comma/decimal-insensitive, in the named case's rubric (prose drift → fail).
   Anchors: Desperado 0-4-1 Impoppable **$12,025** unit / **$120,250** ×10; Elite Lych HP **30k /
   180k / 1.1M / 4.8M / 24M**; ABR r25-83 **$113,872.30**; standard round-cash ranges **60-68 =
   13,093.90 · 50-60 = 19,840 · 54-70 = 29,386.70**.
2. **Capability-consistency guard** (same file) — the `ai_introspection_service` BTD6 answerability
   snapshot must advertise `round_cash` as a `calculation` whose note covers **projection** (matching
   the shipped #634 workflow), and list `modified_economy` as a guarded **"NOT applied"** domain — so
   the capability message can never drift back to the #704 over-promise.

Enabling change: `tests/evals/graders.py` now exposes `.rubric` on `llm_judge` and `.subgraders` on
`all_of`/`any_of` (read-only introspection metadata; grading behaviour unchanged) so the guard can
read rubric prose recursively.

**Verification:** every anchor number was probed against `btd6_data_service` before writing — all
reproduce exactly. `check_quality.py --full` GREEN (11,565 passed, 47 skipped); `check_architecture
--mode strict` 0 errors (only pre-existing baseview/edit-in-place warnings, none in touched files);
new file: 35 targeted tests pass.

## Files

- `tests/evals/test_btd6_grounding_anchors.py` (new — the guard, 24 anchor checks + table/meta/capability)
- `tests/evals/graders.py` (expose `.rubric` / `.subgraders` metadata)
- `docs/roadmap.md` § S2 Next + `docs/current-state/S2-btd6.md` (de-staled: offline half shipped)

## Handoff — next dispatch

The #704 P1-1 BTD6 lane's **offline half is closed**. Remaining BTD6/P1-1 work (all gated on prod
creds, not buildable unattended): the **live `llm_judge` battery** (model actually using the grounded
facts) + **absence-guard Layer B** (negative-existential gate, design-for-review). Other ▶ startable
green lanes for the next empty fire (`dispatch_menu --unattended`): S1 **Project Moon runtime PR 1**
(`KnowledgeDomain` seam + first ingest — substantial → `needs-hermes-review`) · S1 **botsite React-SPA
migration**. The pattern in this PR (deterministic re-derivation ↔ asserted truth ↔ rubric) generalizes
to any future numeric eval anchor — append to `ANCHORS`.

## Session enders

**💡 Session idea (Q-0089):** *Generalize the grounding-anchor guard into a tiny reusable
`tests/evals/grounding_anchor.py` helper* (the `Anchor` dataclass + the two parametrized direction
checks + `_rubric_numbers`), so any LLM-judged eval that bakes a *deterministically-derivable* number
into its rubric (mining costs, XP curves, creature combat constants — the creature sim↔engine parity
guard #1229 is the same shape in a different home) can drop in an anchor instead of trusting prose.
Genuinely believe in it: the value-vs-claim gap (BUG-0009's whole class) is that grounded *values*
drift from *asserted* truth; a one-line anchor closes it for any numeric fact, repo-wide. Worth an
idea file if a second domain wants it.

**⟲ Previous-session review (Q-0102):** the prior run (#1291, BUG-0024 — hermetic dashboard
determinism test) did the right thing well: it root-caused a `-n auto` flake to a real
`_git_meta` timeout→wall-clock fallback and made the *test* hermetic without touching correct
production logic, and added a companion test for the intentional fallback branch — textbook
"fix the test, not the code, and cover both branches." What it (reasonably) left: it's the
*second* real-clock `-n auto` flake in two days (BUG-0021 was the first), both from un-mocked
time in tests. **System improvement surfaced:** these are a *class*, not one-offs — a lightweight
lint/convention ("eval/CI-timing tests must inject the clock, never read real `time.monotonic`/
`datetime.now`") would catch the next one at write time instead of as a flaky-CI surprise. Captured
here as a candidate; not promoted unilaterally (it's a new guard touching test conventions).

**Doc audit (Q-0104):** `check_current_state_ledger.py --strict` + `check_docs --strict` run below
(see commit). No new owner decisions this run (no router entry needed). New test file is reachable
from `tests/evals/`; no new top-level doc. De-staled S2 roadmap + sector state in the same PR.

## 📤 Run report

- **Run type:** routine · dispatch
- **PR:** #1295 (self-merge on green — offline-verifiable, contained; not substantial → no
  `needs-hermes-review`)
- **⚑ Self-initiated:** none (advanced the existing S2 ▶ P1-1 plan slice — not an invented feature)
- **⚑ Owner-decisions:** none
- **⚑ Owner-manual-steps:** none
- **Remarks:** CodeGraph available (built clean at session start). Grimp not needed. Arch warnings
  unchanged (pre-existing baseview/edit-in-place, none in touched files).
