# 2026-06-26 — Cross-domain AI-routing disjointness guard (S1 / Project Moon prep)

> **Status:** `complete`
> **Run type:** routine · dispatch
> **Branch:** `claude/funny-franklin-8s9r5j` · **PR:** #1470

## Goal (dispatch run, empty scheduled fire → advance the next plan slice)

Empty scheduled fire. The Project Moon knowledge-domain arc (Q-0192) is the active S1
program; Slice A (grounding path + faithfulness guard) shipped through #1469. The plan's
remaining ▶ Next items are all genuinely blocked for an unattended dispatch run:
**owner-gated** (the live Q-0086 runtime walk), **fragile-unattended** (Slice A item 1 —
the StaticData exact-number ingest, which poisons grounding if sourced wrong), or **Slice B**
(the gated BTD6-grounding seam refactor the plan §4 explicitly flags as wanting a
*runtime-verified* session). The clean, safe, offline-buildable slice both of the last two
runs' session ideas flagged is the **cross-domain over-route harness**.

It guards a **currently-unguarded invariant**: `ai_task_router.classify` routes BTD6 first,
then Limbus, on the bare comment *"BTD6 keywords never collide with the distinctive Limbus
tokens"* — asserted, never tested. The two detectors even use **different match semantics**
(`has_btd6_context` is a substring scan; `has_limbus_context` is word-boundary), so a future
keyword-set edit could silently make a Limbus question route to BTD6 (starving projmoon) or a
BTD6 phrase trip the Limbus detector.

## What shipped (PR #1470)

- **`tests/unit/runtime/ai/test_domain_routing_disjoint.py`** — a registry-driven harness.
  A `DomainRoute` registry (`DOMAINS`) declares each domain's detector, expected `AITask`,
  distinctive tokens, and clean sample questions; **adding a domain is one registration**.
  It pins three properties:
  1. **Routing** — each domain's clean samples route to its task.
  2. **Detector disjointness (root guard)** — no domain's distinctive tokens trip any *other*
     domain's detector, across **every ordered pair** and both match semantics. This is the
     structural form of the router's comment — a future collision fails CI.
  3. **Priority is a total order** — when two domains could claim a phrase, the earlier
     (BTD6) wins; pinned with a phrase both detectors genuinely fire on.
  Plus a "claimed only by its own detector" check (the literal "at most one domain claims
  each phrase") and a neutral-chatter → general corpus. 12 tests.
- **Detector-curation recipe** in [`docs/subsystems/ai.md`](../docs/subsystems/ai.md)
  § "Adding a knowledge domain" — the durable home for the "distinctive vs generic token"
  + cross-domain disjointness discipline that was re-derived from BTD6 source twice (the
  prev-review's flagged system improvement). Points the next domain author at the guard.

**Offline, no runtime behaviour change** — only a test + docs + the plan/S1 progress trail.
De-risks Slice B's seam extraction without touching the gated BTD6 hot path.

## Verification

- `python3.10 -m pytest tests/unit/runtime/ai/test_domain_routing_disjoint.py` → **12 passed**.
- `python3.10 scripts/check_quality.py --full` → **All checks passed** (12621 passed, 48
  skipped, 2 xfailed).
- `check_architecture.py --mode strict` → **0 errors** (49 pre-existing warnings, none new).
- `check_docs.py --strict` → green; `check_current_state_ledger.py` → benign newest-merge lag
  only (the recon pass records it).

## Status checklist
- [x] Registry-driven disjointness harness (12 tests, all 3 properties)
- [x] Detector-curation recipe in the ai folio
- [x] De-stale the project-moon plan + S1 sector doc (progress trail)
- [x] CI mirror green + arch strict 0 errors
- [x] Session enders (idea / prev-review / doc audit / run-report footer)

## Decisions made alone

- **Shipped one coherent PR, not a forced second slice.** The routine biases toward 2–3
  slices, but the remaining Project Moon ▶ items are owner-gated / fragile-data / gated-runtime
  (above), and the obvious adjacent refactor (`build_domain_name_index` folding the two
  `_name_index` builders) belongs to Slice B per the plan §3/§5 — doing it now would touch
  groundedness-critical gated code against the plan's stated "runtime-verified session"
  sequencing, purely to hit a slice count. That's the wrong trade; this is an honest natural
  boundary, not a lazy single-PR stop. Flagged here for ratification.

## 💡 Session idea (Q-0089)

**Promote the `DomainRoute` registry from the test into a runtime source of truth.** Today the
router hand-codes the domain check order (BTD6 → Limbus → video) and each domain's detector wiring
inline in `classify`, while the test's `DOMAINS` registry independently lists the same domains +
priority. When Slice B extracts the `KnowledgeDomain` seam, the router's domain dispatch could be
**driven by an ordered registry of `KnowledgeDomain` instances** (each carrying its detector +
task + priority), and this test's registry would then *assert against the real one* rather than
duplicate it — so the priority order and detector set have exactly one home, and registering LoR
is a single `KnowledgeDomain(...)` that the router, the grounding guard, and this harness all read.
(Genuinely believe in it — it's the natural endpoint of the over-route guard once the seam exists,
and it closes the last "two lists of domains" drift gap.)

## ⟲ Previous-session review (Q-0102)

The previous run (PR #1469, the projmoon faithfulness guard) did the right thing twice: it
**reused** `utils.btd6.name_guard` + `GroundingResult` instead of copying, and it deliberately
kept the guard **names-only / common-category-skipping** rather than over-indexing for coverage
(a guard that floored "deals slash damage" on *slash* would be worse than none). Its own session
idea + prev-review both flagged that the "distinctive vs generic token" discipline was being
**re-derived from BTD6 source each time** and wanted a documented recipe — this run acted on
exactly that (the ai-folio recipe) and added the missing *cross-domain* half (the disjointness
guard the faithfulness work assumed but never tested). **System improvement it surfaces (acted
on):** the recipe + registry harness together turn "read BTD6 source and re-derive the rules"
into "register a domain and let the guard cover it." One thing still open for the next run: the
two `_name_index` builders remain literal duplicates — the right fix is the `build_domain_name_index`
helper, but it correctly belongs to Slice B's seam extraction, not a premature standalone refactor.

## Context delta
- **Needed but not pointed to:** that `ai_task_router.classify` encodes the domain priority order
  *and* the disjointness assumption only as an inline comment — found by reading the router, not
  routed to by any folio. Now documented in the ai folio § "Adding a knowledge domain".
- **Pointed to but didn't need:** the bug-book full read (`bug-book.md` is 950 lines) — the
  rootfix-backlog checker (`check_bug_book_rootfix_backlog.py`) answered "what's actionable?" in
  one line; the two open entries (BUG-0009 data-gated, BUG-0019 owner-decision) were both blocked,
  so the deep read wasn't load-bearing this run.
- **Discovered by hand:** the "distinctive vs generic token" curation discipline lived only in
  `btd6_grounding_service._name_index` / `projmoon_grounding_service._name_index` comments +
  `utils/*/keywords.py` docstrings — now has a durable home in the ai folio.

## 📤 Run report

- **Did:** built the cross-domain AI-routing disjointness guard — a registry-driven harness pinning
  the previously-untested router invariant that BTD6 and Limbus detectors never collide · **Outcome:** shipped
- **Shipped:** #1470 — `tests/unit/runtime/ai/test_domain_routing_disjoint.py` (12 tests: routing ·
  token disjointness across every domain pair · priority total-order) + an ai-folio detector-curation
  recipe; de-risks Slice B without touching the gated BTD6 hot path
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none (offline test + docs; a merge auto-deploys, though nothing runtime
  changed). The live Q-0086 Limbus runtime walk remains an owner step carried from PR #1467 — not new here.
- **⚑ Self-initiated:** the over-route guard — chosen on an *empty* dispatch fire. Executes an
  already-owner-approved program (Q-0192) + a session-idea flagged by the last two runs, not a fresh
  idea→plan promotion; flagged here since no work order named it.
- **↪ Next:** S1 Project Moon — the live **Q-0086 runtime walk** (owner) + Slice A item 1 (the
  StaticData exact-number ingest, the deferred fragile lane) → then **Slice B** = extract the shared
  `KnowledgeDomain` seam from BTD6 + Limbus (fold the two `_name_index` builders into one
  `build_domain_name_index`; consider driving the router's domain dispatch off a runtime registry the
  new harness asserts against — see this run's session idea).
