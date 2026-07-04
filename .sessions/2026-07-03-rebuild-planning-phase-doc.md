# 2026-07-03 — Document the rebuild review-then-plan phase (process + next-session goal)

> **Status:** `complete`
> **Branch:** `claude/bot-capability-audit-capstone-scy0zx` · **PR:** #1677
> **Session type:** owner-directed docs — capture the next-phase process after the capstone.

## What happened

The capability-audit capstone (#1674) merged; the BUILD-PLAN is the frozen reference. The owner
directed the next phase and asked me to document it so the next session lands running:

1. **One more content review pass first** — dedicated owner-led brainstorming sessions over the
   whole plan, focused on the **commands / functions / methods** (not feasibility — the capstone
   settled that; this decides whether the surface is *right* and gives it exact names).
2. **Then per-step planning** — one **100%-complete design plan per step** before any code, every
   file designed from line one to handle its **entire eventual surface** (bounded by the corpus,
   not open-ended). The same "declare completely once" bet as the manifest grammar.

Wrote [`docs/planning/rebuild-planning-phase-2026-07-03.md`](../docs/planning/rebuild-planning-phase-2026-07-03.md):
the three-phase sequence (Content review → Per-step planning → Build), Phase A as the explicit
next-session goal with a 7-topic seed agenda, the Phase-B process design (fixed plan template,
hard completeness test = "a fresh agent could build it with zero further decisions",
adversarial-completeness gate, two-level layer/component hierarchy, dependency-order starting at
the Gate-0 grammar freeze, sequential-on-the-spine/parallel-on-the-leaves, plan-is-source-of-truth,
plans-are-the-permanent-design-record), and the **durable-fix ledger** assigning every open
uncertainty (ModerationActionSpec, compound-composition, forward-fit, G-22/R-12/P-1, Lane-D trust)
to the phase/plan that must resolve it. Cross-linked from the BUILD-PLAN top pointer and the S4
current-state ▶ Next.

The doc distilled a genuine capstone-chat discussion; the improvements over the owner's raw idea
(completeness test, corpus-boundedness, dependency-order-of-planning, two-level hierarchy,
provides/consumes, plans-as-permanent-record, the plan-is-truth feedback loop) are folded in as
the process design.

## ⚑ Self-initiated

Docs-only within the owner's explicit request; nothing beyond the documented scope. Cross-links +
the S4 pointer are the "make it discoverable" half of "document so the next session knows the
goal" — not separately directed, but the obvious completion of the instruction (a doc no session
finds is not documented). Flagged for visibility, not because it's out of scope.

## 💡 Session idea

**A `parity/`-golden *recapture* protocol for current-bot bug fixes.** The capstone routed six
live bugs (two money bugs) as immediate current-bot work, *and* the rebuild will parity-check the
new bot against the frozen old bot's captured behavior. Those collide: if a current-bot bug is
fixed **after** its golden is captured, parity later "verifies" the *fixed* behavior — fine — but
if fixed **before** capture with no re-capture step, the golden encodes the buggy behavior and the
rebuild faithfully reproduces the bug. The durable fix is a one-line protocol: *every current-bot
behavior fix must re-capture its golden (or explicitly note "pre-capture, no golden yet")*, wired
into the bug-fix session checklist. Cheap, prevents a silent bug-preservation class the merge=
deploy + parity-oracle combination otherwise invites. Dedup-checked: no existing golden-recapture
protocol in `docs/ideas/` (the doc-set reviewer proposed the *idea* in the capstone chat; this
files it durably).

## ⟲ Previous-session review

The previous session (this same branch, the capstone #1674) did the hard synthesis well and, to
its credit, **surfaced its own uncertainties honestly** rather than shipping a clean-looking
verdict — which is exactly what made *this* owner-directed follow-up productive (the owner could
act on a named uncertainty list). One thing it could have done better, which this session
corrects: it left the "what happens next" implicit in FINAL-REVIEW §7 (the Gate-0 checklist) and
BUILD-PLAN §4, scattered across two large docs — a next session would have had to reconstruct the
phase sequence. **System improvement:** a capstone/verdict artifact should always ship with a
**one-page "next phase" pointer** as a first-class sibling doc, not buried in a §7 — the reference
plan and the process-to-execute-it are different genres and want different files (which is now the
shape: BUILD-PLAN = *what*, rebuild-planning-phase = *how we proceed*). Cheap convention, prevents
the "great artifact, unclear next step" gap.

## 📊 Telemetry

- PR #1677 · 1 process doc + 2 cross-links (BUILD-PLAN pointer, S4 ▶ Next) + 1 idea file + this log
- Docs-only; `check_docs --strict` green; no runtime touched; Phase-3 owner gate unchanged
- Born-red gate held through the session as designed (the #1677 CI "failure" was `check_session_gate`
  on the in-progress card — flipped complete as the final step)

## Doc audit (Q-0104)

`check_docs --strict` green (new doc badged + linked + reachable) · new idea file indexed in
`docs/ideas/README.md` · `check_current_state_ledger --strict` benign newest-merge lag
only (this PR unmerged) · no new owner decisions taken (the doc *records* an owner directive — the
phase sequence — but mints no new binding rule) · claim released at close.
