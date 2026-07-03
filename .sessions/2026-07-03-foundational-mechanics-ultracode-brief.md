# 2026-07-03 — Prepare two parallel ultracode session prompts (foundational-mechanics brainstorm)

> **Status:** `complete` — PR #1688. Owner-directed PREPARATION (explicitly NOT launching this
> session). Docs-only; no `disbot/` code, no workflow launched.

## What shipped (PR #1688)

1. **[`docs/planning/rebuild-foundational-mechanics-ultracode-brief-2026-07-03.md`](../docs/planning/rebuild-foundational-mechanics-ultracode-brief-2026-07-03.md)**
   — the brief:
   - **Web-researched** what a dedicated ultracode/workflow session can do (official docs: up to
     1,000 subagents / 16 concurrent, background, best for audits + cross-checked research +
     multi-angle brainstorm, quality patterns, one synthesized report).
   - **Two paste-ready, parallel-safe prompts.** Session A = the engine room (runtime/logic);
     Session B = the surface + the proving (presentation/UX + verification). Each has an explicit
     scope boundary naming the other's domain, so they don't collide in parallel; each claims its
     own lane + writes its own report + runs its own born-red PR.
   - **Shared method** encoded in both: per mechanic → find-how-now (source, file:line) +
     research 2-3 alternatives (web/competitors) + pressure-test our decision → adversarial-verify
     vs source (Q-0120) → completeness-critic loop-until-dry → synthesize; every issue scored by
     the 10-class rubric into a ranked issues ledger; owner-gated items flagged, not decided.
   - **Launch instructions** for the owner.
2. **Router Q-0236** with verbatim-quote provenance; ledger #1688; planning README homing.

## 💡 Session idea (Q-0089)

No new idea minted — the session's work *is* meta-tooling (a reusable two-session audit brief), and
the session already produced five genuine ideas today. Per Q-0089's anti-filler bar, no tenth.

## ⟲ Previous-session review (Q-0102)

Previous card: **#1687 (layout-success simulator).** Good — it grepped first (found the 5 sims) and
tied the sim to the oracle+arrangement decisions cleanly. **Improvement this session applied:** the
owner asked me to *research the web before answering* — a discipline worth generalizing: for any
question about an external capability (a tool, an API, a platform feature), fetch the authoritative
docs first rather than answering from training. I did (official workflows docs), which directly
improved the prompt design (concrete caps, quality patterns). Worth making a standing reflex, same
as "grep the source first" for internal capabilities — the external mirror of Q-0120.

## Docs audit (Q-0104)

- `check_docs --strict` + `check_plan_homing` + `check_session_gate` at close (below)
- Owner decision → Q-0236; ledger #1688; planning README homing
- Chat-only residue: none — both prompts + the research summary + launch instructions are durable
  in the brief.

## ⚑ Self-initiated

None — Q-0236 is owner-directed (prepare two ultracode sessions; explicitly not launched, per the
owner's "NOT in this current session").

## Session arc (eight PRs)

#1679 Stage-1 review · #1680 conventions freeze · #1683 permissions + endorsement · #1684
hub/navigation/presets · #1685 critical-review rubric · #1686 oracle + verification strategy ·
#1687 layout-success simulator · #1688 two parallel ultracode prompts (prepared).

## For the next session (or the owner's two parallel sessions)

- **Launch** Prompt A + Prompt B in two parallel sessions (owner action).
- Read their two issues ledgers; feed survivors into the **Stage-2 subsystem walk** (rubric-driven)
  → **Gate V** (verification fleet) → **Phase B** → migration.
- Still-open: preset hide-vs-disable (Q-0232); run the rubric over today's own decision logs.
