# 2026-07-02 — Lane F ecosystem benchmark (verify + incorporate owner-provided deep-research)

> **Status:** `complete`
> **Branch:** `claude/review-recent-session-qcyc44` · **PR:** #1672
> **Session type:** owner-directed — owner pasted the Lane F deep-research (ecosystem benchmark vs known
> Discord bots) and said "this is lane F." Task: verify it against source (Q-0120) and land it as the
> fleet's 7th lane so the Fable 5 capstone is unblocked.

## What I'm about to do (born-red placeholder)

Incorporate the owner-provided Lane F ecosystem benchmark into `findings/ecosystem-benchmark.md` — but
**corrected against shipped source**, because the raw research misread SuperBot's own surface badly (flagged
already-shipped subsystems as missing "gaps"). Preserve the genuine competitor catalog + best-in-class
targets; fix the SuperBot side; produce the per-domain outperform targets all six merged lanes deferred as
`pending Lane F`. Docs-only.

## What shipped

- `findings/ecosystem-benchmark.md` — the corrected Lane F: competitor catalog + verified SuperBot-status
  column + per-domain outperform targets (resolves the six merged lanes' `pending Lane F`) + genuine gaps vs
  deliberate omissions vs deferred options.
- `findings/README.md` — real markdown link to the new doc (reachability).
- **This completes the 7-lane fleet** (A, B, C, D, E, G merged + F now) → the Fable 5 capstone is unblocked.

**The verification mattered.** The raw owner-provided Lane F flagged **ticketing** and **advanced reaction
roles** as the top missing "strong-fit additions" — both already ship (`ticket` subsystem; `role` menu
builder + reaction panel + role packs). It also wrongly claimed no gambling (`casino`/poker ship), text-only
welcome (`welcome_card` renders images), and no web config (`dashboard/` Flask app). Landing it verbatim would
have made the capstone recommend building things that exist. Corrected column cites source throughout (Q-0120).

## ⚑ Self-initiated

None beyond the owner's direct request ("this is lane F"). The *correction* of the raw research against source
is the Q-0120 obligation, not scope creep — the owner relies on cross-agent output being verified before it
feeds the build plan.

## 💡 Session idea

**A `known-vs-shipped` guard for benchmark lanes.** Lane F's failure mode — an external agent asserting
SuperBot lacks X when X ships — is mechanically detectable: any ecosystem/benchmark doc that says "SuperBot has
no <word>" can be cross-checked against `ground-truth/subsystems.json` + a `def <word>` / cog grep, and flagged
when the word IS a shipped subsystem. A tiny checker (`scripts/check_benchmark_claims.py`) run over
`findings/*.md` would catch "we don't have tickets" when `ticket` is subsystem #33, turning the Q-0120 manual
verify into an automated tripwire for this doc class. Dedup: no existing checker reads the benchmark findings
against the subsystem ground truth.

## ⟲ Previous-session review

Previous session (the two Codex lanes D/E I verified + merged) did well: D's citations were 5/5 accurate and E
correctly deferred to Axis-1. **What the fleet as a whole could have done better** — and Lane F is the proof —
is give every lane the **subsystem ground-truth list up front** as a "you already have these, don't call them
gaps" guard. Lane F (an *external* deep-research agent) never saw `subsystems.json`, so it re-derived
SuperBot's surface from guesswork and got it wrong. **System improvement:** the `HANDOFF-PROMPTS.md` for any
Axis-3/benchmark lane should hard-require reading `ground-truth/subsystems.json` first and phrase every "gap"
as "verified absent from the 43 subsystems," not "seems missing." (Captured as the session idea above, in
enforceable form.)

## 📊 Telemetry

- PR #1672 · docs-only · `findings/ecosystem-benchmark.md` (new) + `findings/README.md` link + this log.
- 7 SuperBot-side claims in the raw research corrected against source; 5 were flat contradictions.
- Fleet complete: 7/7 lanes merged/landing (A,B,C,D,E,G merged; F this PR) → capstone unblocked.

## Doc audit (Q-0104)

`check_docs --strict` green (new doc linked from findings/README → reachable) · Lane F provenance + corrections
documented in-doc and here · ledger unaffected (docs-only) · no claim file opened (PR is the in-flight signal).
