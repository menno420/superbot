# 2026-07-02 — Prepare the repo for the new-bot capability audit (fleet substrate)

> **Status:** `complete`
> **Branch:** `claude/review-recent-session-qcyc44` · **PR:** #1660 (opening)
> **Session type:** prep/orchestration — "prepare the repo for 2 Opus + 1 Sonnet ultracode + Codex/deep-research to create the final mapping audit, then a Fable 5 final review"

## What happened

Built the full substrate for a multi-agent **new-bot capability audit** under
`docs/analysis/rebuild-discovery/new-bot-capability-audit/`. The owner's vision, assembled across the
session: the next bot is built from **one unified, dependency-ordered, best-in-class plan** (foundations
→ core management → features; each layer production-grade before the next; every function must outperform
any other bot). To earn that plan, a fleet runs every capability through **MAP → RECONSIDER → SIMULATE →
OPTIMIZE → BENCHMARK** across **three axes**: what we have (43 subsystems), what we planned
(plans/ideas), and what the ecosystem has that we don't (known Discord bots).

### The substrate (docs-only, read-only — no runtime/new-repo code)

- **`BRIEF.md`** — the binding contract: 3-axis mandate, 5 verbs, the end-goal (unified plan / build order
  / production-grade / outperform), per-capability schema, guardrails, exit bar, grammar spine.
- **`PARTITION.md`** — **7 lanes**: A–D (43 subsystems, Axis 1), E (plans/ideas, Axis 2), F (ecosystem,
  Axis 3), **G (L0 foundations — bootstrap / dynamic cog-loader / lean main.py / helper-util arch)** +
  model→lane matching.
- **`HANDOFF-PROMPTS.md`** — copy-paste startup prompts for all 7 lanes + the Fable 5 capstone + launch order.
- **`FINAL-REVIEW-HANDOFF.md`** — the capstone spec: verify-then-rule (grammar GO/GO-with-amendments/NO-GO)
  + the unified build plan (corpus + dependency-layered order + per-capability done-definition + outperform target).
- **`README.md`** + **`ground-truth/`** (271 commands + 43 subsystems dumped) + **`lanes/`** (A–D pre-filled
  with extracted surface inventories; E/G scaffolds) + **`findings/`**.

### The fleet maps to the owner's plan

2 Opus 4.8 ultracode (B, C) · 1 Sonnet 5 ultracode (A) · a few Codex/deep-research (D, E, F, G) → Fable 5
capstone. Lanes fire in parallel (A–D + G file-disjoint; E/F cross-cutting), then the capstone.

## ⚑ Self-initiated

All owner-directed (the prep + fleet design were requested across the session). Self-initiated **within**
that direction: (1) ran a **43-agent scaffold Workflow** (~2.0M subagent tokens, 0 errors) to pre-extract
every subsystem's surface-unit inventory so the fleet spends its budget on judgment, not re-deriving facts;
(2) the 7-lane structure + the Lane G foundations lane (surfaced a partition gap — the runtime skeleton
isn't a "subsystem"); (3) the "extract-mechanically-then-judge" + one-shared-schema-so-outputs-compose
shape (the composition lesson from the prior Codex-review session). Flagged for owner/Hermes review.

## 💡 Session idea

**A reusable "fleet-substrate" skill for large multi-agent audits.** This session's shape — ground-truth
dump → shared contract/schema → disjoint partition → pre-filled scaffolds → per-lane handoff prompts →
capstone synthesis — is generic: any big audit (security sweep, dependency migration, doc reconciliation
at scale) wants exactly this. Codify it as a `/fleet-audit` skill that takes a target + partition axis and
emits the substrate, so future audits start from a template instead of hand-building it. Grounded in what
I just built by hand; dedup-checked against `docs/ideas/` (nearest is the ultracode coordinator tooling,
which is execution-side, not substrate-authoring).

## ⟲ Previous-session review

The previous session (Codex-PR review + hub/S4 drift fix) correctly ran a one-fact-one-home sweep and
verified cross-agent claims before acting — good discipline. The recurring drift it fixed (hub ▶Next-action
row contradicting its sector doc) has now bitten **twice** (#1653 and the Codex-review session). **System
improvement:** a small checker that cross-validates each `current-state.md` hub ▶Next-action row against
its sector doc's stated next-action would catch this class mechanically instead of relying on an external
reviewer to spot it — the "enforce, don't exhort" (Q-0132) response to a twice-seen drift.

## 📊 Telemetry

- PR #1660 · new-bot-capability-audit substrate: 7 lanes + capstone + ground truth + handoff prompts
- 43-agent inventory Workflow: 43/43 subsystems, 0 errors, ~2.0M subagent tokens, 271 surface units mapped
- Docs-only; `check_docs --strict` green (badges + reachability); zero runtime code
- Dir named `new-bot-capability-audit/` (owner-approved rename from `grammar-completeness/`)

## Doc audit (Q-0104)

`check_docs --strict` green · new substrate reachable from its README · ledger unaffected (docs-only) ·
claim released at close.
