# 2026-07-03 — The critical-review rubric (owner-directed)

> **Status:** `complete` — PR #1685. Owner-directed: extract the *classes* of gaps caught reviewing
> the rebuild plan today into a reusable review lens. Docs-only; no `disbot/` code.

## What shipped (PR #1685)

1. **[`docs/planning/rebuild-critical-review-rubric-2026-07-03.md`](../docs/planning/rebuild-critical-review-rubric-2026-07-03.md)**
   — the rubric: **ten finding-classes**, each a probing question + the day's real example + a
   mechanization tag (🧠 human-probe / ⚙️ exists / 🔧 build):
   1. dependency-order inversion (welcome ← card engine)
   2. forgotten capability (media generation)
   3. thin/underspecified step (cutover)
   4. stale un-anchored state claim (kit 45–55% vs ~90–95%)
   5. fragmentation/reinvention (presets ×7)
   6. under-generalization (card engine)
   7. missing cross-cutting standard (naming/authority)
   8. verification hole (new-feature oracle)
   9. UX/lifecycle-contract gap (Back/Home, timeouts)
   10. naming/visibility/collision (`give`, `dock`/`sail`)
   Plus the **common-thread framing** (an artifact never self-reports completeness / order /
   duplication / verifiability / consistency), how to apply it (Stage-2 per-subsystem + Phase-B
   adversarial pass — silence on a class is not a pass), and a **mechanization roadmap**.
2. **Router Q-0233** with verbatim-quote provenance.
3. **Checker backlog idea** + homing + ledger #1685.

## 💡 Session idea (Q-0089)

**[`rebuild-critical-review-checkers-2026-07-03.md`](../docs/ideas/rebuild-critical-review-checkers-2026-07-03.md)**
— mechanize the rubric: the cheap current-repo win is extending `check_plan_staleness.py` to flag
un-anchored `NN%`/"complete" claims (the exact class that misled two sessions about the kit); the
rest build against the rebuild's declared manifests. The enforce-don't-exhort arm of the rubric.

## ⟲ Previous-session review (Q-0102)

Previous card: **#1684 (hub/navigation).** Good — it captured a large decided block cleanly and
flagged the one open sub-decision (hide-vs-disable) rather than guessing it. **The improvement it
surfaced is *this whole PR*:** #1684's review-note observed I kept discovering existing code
*reactively* ("grep for it first"). This session generalized that single observation into a
ten-class rubric — the self-auditing loop working as designed (a session-review remark became the
next session's deliverable). **Forward improvement:** the rubric should itself be applied to the
*already-written* rebuild decision logs (stage-1, conventions, hub-nav) once, as a self-check — we
built the lens from them but never ran the finished lens back over them. A good first exercise for
the next session, and a test of whether the rubric catches anything we missed live.

## Docs audit (Q-0104)

- `check_docs --strict` + `check_plan_homing` + `check_session_gate` run at close (below)
- Owner decision → Q-0233; session idea indexed; ledger entry #1685 added
- Chat-only residue: none — the rubric + the common-thread framing + the mechanization roadmap are
  all in the rubric doc.

## ⚑ Self-initiated

None — Q-0233 is owner-directed ("create a rule or system that finds exactly the kind of things
we've been spotting"). The checker backlog is captured as an idea, not self-built.

## For the next session

- **Apply the rubric to the three decision logs written this session** (self-check — see the
  previous-session-review note).
- **Resolve the open items:** hide-vs-disable (Q-0232); the new-feature oracle (rubric class 8, the
  one real verification hole).
- **Stage 2 — the subsystem walk**, now powered by the rubric: run all ten probes against each of
  the 43 subsystems alongside naming / placement / triage. Agenda in stage-1 log §6 + conventions
  log.
- **Cheap current-repo win available:** the class-4 `check_plan_staleness.py` extension.
