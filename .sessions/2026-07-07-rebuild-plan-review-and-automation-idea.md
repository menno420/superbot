# 2026-07-07 — Rebuild plan review (owner Q&A) + user-automation idea capture

> **Status:** `complete` — deliberate final flip (born-red gate, Q-0133). Docs-only session: no
> `disbot/` runtime changes, no plan edits to frozen/canonical documents. One new idea capture doc.

## What this session did

The owner asked three things, in sequence, purely conversational:

1. **"Explain the rebuild plan in plain language — what will this bot be when it's done?"**
   Read the canonical plan (`docs/planning/rebuild-canonical-plan-2026-07-06.md`), its owner-briefing
   companion, and the design spec's plain-language summary/executive-summary sections, plus
   `docs/current-state.md` for feature texture. Answered in chat only — no doc changes (a read-only
   explanation task).
2. **"Do you think there are improvements or overlooked items?"**
   Cross-checked my own candidate gaps against the corpus's own self-review
   (`rebuild-verification-review-2026-07-03.md`, `rebuild-final-review-report-2026-07-07.md`) before
   asserting anything — most of what I would have flagged (layer-V thinness, AI-answer verification
   being a different oracle shape than golden parity, the human-lane verified_live bottleneck, cost
   posture, rollback-window length) turned out either already named as the plan's own top risk or
   already resolved; reported back which of my points were genuinely additive vs. already covered,
   rather than re-presenting the self-review as if it were my own finding.
3. **Owner floated a product idea:** a guardrailed, unlockable, user-self-service recurring
   scheduler ("cron jobs for themselves") — e.g. a daily rank ping, or a periodic game-state check —
   explicitly requested as a **foundational, cross-subsystem** primitive, not a one-off command.
   Captured as `docs/ideas/user-self-service-automation-scheduler-2026-07-07.md`: dedup-checked
   against existing prior art (`!remind`'s known restart-loss bug, the competitive-teardown #8
   scheduler-slice idea, the future-product-direction notification-profiles idea), split the ask into
   a low-risk notify-only tier and a higher-risk auto-acting tier (named the concrete fairness failure
   mode: automating an action a forgetful human would otherwise miss is a real balance break, not a
   QoL win), and tied the design to the not-yet-built K9 durability band so it can land as a kernel
   extension instead of a later per-feature bolt-on.

## Shipped (this PR)

- **New:** `docs/ideas/user-self-service-automation-scheduler-2026-07-07.md`.
- **This session log.**
- No `disbot/` changes. No edits to the canonical plan or any frozen rebuild doc — deliberately
  routed as a standalone idea doc instead of editing `rebuild-canonical-plan-2026-07-06.md` directly,
  since that document's whole value is that every line traces to a decisions-log entry from a
  reviewed pass; the idea doc names exactly where it should land (K9's Phase-B step) for whenever
  that amendment pass happens.

## 🛠 Friction → guard (Q-0194)

No new friction this session that warrants a checker/hook — the workflow (read plan → answer →
capture idea → commit/push) worked as designed, including the Stop-hook catching the untracked idea
file and prompting the commit+push that produced this PR.

## ⟲ Previous-session review (Q-0102)

Previous session (`2026-07-06-gate-v-arm-d-live-testing.md`) ran Gate V's Arm D live-testing pass
carefully, with a well-reasoned sandbox-methodology fallback it folded back into the source doc for
future sessions. One thing worth flagging forward: that session's own "💡 Session idea" proposed a
reusable in-process synthetic-gateway-with-real-HTTP harness (one fidelity tier above what it built)
— it's a small, well-scoped, ready-to-pick-up idea that hasn't been picked up in the two days since
(band #1770→#1783 shipped a lot of rebuild-consolidation work but not this). **Concrete improvement
for the system:** nothing structural to fix here — this is a plain reminder that a good idea captured
in a session log's prose (rather than as its own `docs/ideas/` file) is easy to lose track of once
several bands pass; worth grooming it into its own idea file next time someone is in that area, so it
surfaces in `docs/ideas/` greps instead of only in one old session log.

## 💡 Session idea (Q-0089)

Already delivered as this session's substantive idea capture (§ above): the user-self-service
automation scheduler. No separate filler idea added — one genuine idea, not two thin ones.

## 🧹 Grooming (Q-0015)

This session's idea capture doubles as its own grooming: it explicitly routes a raw owner drop into
a structured `docs/ideas/` entry with prior-art cross-references and a named landing spot (K9
Phase-B), rather than leaving it to be re-derived from chat history later.

## 📋 Docs audit (Q-0104)

New idea doc cross-references and is reachable from existing related ideas (fun-and-ease-brainstorm
C4, competitive-teardown #8, future-product-direction) and from the canonical plan's automation
section (B-2) by path. No new owner-facing decision needed routing to the question router — the one
open call the idea doc names (whether auto-acting automations should ever ship) is explicitly left
for whoever picks up the K9 landing, since no subsystem needs it yet and nothing is blocked.

## 📤 Run report

- **Did:** explained the rebuild plan in plain language; gave an independent critique of the plan
  cross-checked against its own self-review; captured a new owner-proposed feature idea with a
  concrete design sketch and fairness analysis. **Outcome:** shipped (docs-only).
- **Shipped:** this PR — 1 new idea doc + this session log. No runtime change.
- **Run type:** `manual` (owner-directed, live conversation).
- **⚑ Owner decisions needed:** none blocking. The idea doc names one open product call (notify-only
  vs. ever allowing auto-acting automations) but explicitly does not block anything today.
- **⚑ Owner manual steps:** none.
- **⚑ Self-initiated:** the idea capture went slightly beyond the owner's literal words — added the
  notify-vs-act risk split and the concrete fairness-failure definition, and proposed the specific
  K9 landing point, none of which the owner specified verbatim.
- **↪ Next:** no forced next step. Natural pickup point is whenever K9's Phase-B per-step plan gets
  written (canonical plan §5 step 10) — fold this idea in then, per its own "Recommended routing."
