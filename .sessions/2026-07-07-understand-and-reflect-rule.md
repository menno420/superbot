# 2026-07-07 — Understand-and-reflect workflow rule (owner-directed in-session)

> **Status:** `in-progress`
> **Model:** Sonnet 5 · **Governance:** Q-0106 owner-directed-in-session exception applies

## What is about to happen

The owner directed, live in chat, that sessions should carry a standing practice: before
substantive work, restate the understood goal back to the user — including the broader,
implicit specs the ask didn't spell out — so misunderstandings surface before work happens,
not after. He also asked whether a general "how does a session classify its task and pick the
efficient method" guide already exists.

Per `.claude/CLAUDE.md`'s own rule ("the owner *is* the live reviewer" exception), this is
applied directly rather than routed as a proposal: mint the next router Q-number recording the
directive, add the practice as a binding rule in `.claude/CLAUDE.md`, and cross-link it from
`docs/AGENT_ORIENTATION.md`'s "Read first" mandate. Research finding folded in: three partial
systems already exist (AGENT_ORIENTATION's per-task reading routes, the ai-project-workflow
5-stage pipeline, and the substrate-kit's dormant 5-stance task classifier) but none of them is
a live, adopted "classify the message → pick the method" ruleset, and nothing existing does the
restate-and-enrich checkpoint. This session closes that specific gap without over-scoping into
adopting the whole kit stance system (that's the kit-lab program's job, not a quick chat fix).

## What shipped

- **Router Q-0254** — the directive recorded with provenance (owner's live words, what was
  found, what was decided).
- **`.claude/CLAUDE.md` § Working agreement** — a new bullet, "Understand-and-reflect," placed
  right before "Unclear owner intent" (the logical predecessor: confirm-then-escalate-if-still-
  unclear). Framed explicitly as inline/non-blocking, not a reversion to stop-and-ask.
- **`docs/AGENT_ORIENTATION.md` § "Read first" mandate** — a pointer (item 7) so the rule
  surfaces in the orientation route every session already reads, not just buried in CLAUDE.md.
- **Idea filed:** `adopt-kit-stance-classifier-2026-07-07.md` — the broader mechanism the
  owner's question gestured at (a real task-classifier, not just a restate step), routed to the
  kit-lab program rather than decided here.

## Context delta (reflection interview)

- **Needed but not pointed to:** nothing unusual — this was a short, well-scoped meta task;
  AGENT_ORIENTATION.md + ai-project-workflow.md were exactly the right two docs to check.
- **Pointed to but didn't need:** none.
- **Discovered by hand:** the CLAUDE.md file's documented section-marker convention
  (`<!-- SECTION_START/END -->`) is described in prose at line 163 but the literal markers
  themselves are real (`READ_FIRST_START/END` etc.) — had to grep for the actual HTML comments
  to confirm placement was safe, since the prose description alone doesn't show the exact names.
- **Decisions made alone:** the exact bullet placement (next to "Act vs. ask" / before "Unclear
  owner intent") and the "inline, not blocking" framing — both reversible wording calls.
- **Flagged for maintainer:** none — this was a direct, unambiguous in-session directive, not a
  judgment call requiring a flag.
- **One docs change that would have helped most:** none beyond what shipped.
- **🛠 Friction → guard:** none this session — no interruption to convert.

## ⟲ Previous-session review (Q-0102)

The kit-lab founding-plan session (PR #1804, same day) did the review-fleet-death recovery
correctly: instead of treating the usage-limit crash as a dead end, it captured the failure as a
standing idea (`usage-limit-aware-routines-2026-07-07.md`) and re-ran the review after the
window reset — a clean example of "friction → guard" done right, in the moment rather than
deferred. One thing it could have done better: its own session card review (of the band-#1800
reconciliation pass) noted a homing-convention split (plan-index row vs. sector-file entry) but
didn't actually fix the ambiguity, just flagged it as a future improvement. **Concrete
improvement carried forward:** the next session that touches `docs/planning/README.md`'s homing
convention should resolve that split rather than re-flag it a third time — three consecutive
"noted but deferred" entries on the same small ambiguity is itself worth acting on.

## 💡 Session idea (Q-0089)

[`adopt-kit-stance-classifier-2026-07-07.md`](../docs/ideas/adopt-kit-stance-classifier-2026-07-07.md) —
wire the kit's dormant 5-stance task classifier into this repo's live workflow, measured via the
kit-lab program's own A/B harness rather than adopted on faith.

## 📤 Run report

- **Did:** answered the owner's task-classification question (partial systems exist, none
  unified) and implemented the understand-and-reflect rule he directed · **Outcome:** shipped
- **Shipped:** #1806 — Q-0254 + the CLAUDE.md rule + the AGENT_ORIENTATION pointer + one idea
- **Run type:** `manual` (owner live-directed, in-chat)
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** none — direct owner directive, applied per the in-session exception
- **📊 Model:** Sonnet 5 · standard · idea/planning (docs-only rule change)
- **↪ Next:** nothing blocking; the filed idea (stance-classifier adoption) is a kit-lab-program
  backlog candidate whenever that program has capacity

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged | 1 (#1806, auto-merge on card flip) |
| CI-red rounds | 0 unexpected (born-red gate holds by design) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (adopt-kit-stance-classifier) |
| Ideas groomed | 0 |
