# Two parallel ultracode sessions — foundational-mechanics brainstorm/audit (2026-07-03)

> **Status:** `plan` — **preparation only** (owner-directed, PR #1688). Two paste-ready ultracode
> session prompts the owner launches **in parallel** to discover + document any issues related to
> everything decided on 2026-07-03, brainstorming thoroughly over every foundational mechanic the
> bot **uses now** and **could use**. **Not launched from the preparing session.** Owner ruling →
> **Q-0236**.

---

## ⚡ Quick launch — the two short startup prompts (paste one per session)

Short launchers that point each session at its full prompt below. The `ultracode:` keyword makes
each write + run its own workflow; it reads this doc and executes its half verbatim.

**Session A (engine room):**
```text
ultracode: Read docs/planning/rebuild-foundational-mechanics-ultracode-brief-2026-07-03.md and run its "PROMPT A — the engine room" verbatim. This is the runtime/logic half; a parallel session runs PROMPT B (presentation/verification), so hold strictly to your scope boundary. Follow .claude/CLAUDE.md — claim your lane, born-red PR, auto-merge on green.
```

**Session B (surface + proving):**
```text
ultracode: Read docs/planning/rebuild-foundational-mechanics-ultracode-brief-2026-07-03.md and run its "PROMPT B — the surface + the proving" verbatim. This is the presentation/UX + verification half; a parallel session runs PROMPT A (runtime/logic), so hold strictly to your scope boundary. Follow .claude/CLAUDE.md — claim your lane, born-red PR, auto-merge on green.
```

*(The full prompts are in the two sections below; the launchers just save you pasting them.)*

---

## What a dedicated ultracode session can do (researched — informs the prompt design)

From the official docs ([code.claude.com/docs/en/workflows](https://code.claude.com/docs/en/workflows)):
a dynamic workflow is a JS orchestration Claude writes and runs **in the background** — **up to
1,000 subagents total, 16 concurrent** — holding the plan in code so only the final answer hits the
context window. It is built for **codebase audits, cross-checked research, and drafting a hard
question from many independent angles**, and supports **quality patterns** (fan-out → adversarial
cross-verify, judge-panel, loop-until-nothing-new). Output = **one synthesized report**. So each
prompt below describes the *task + the quality pattern* and lets the session write the orchestration.

## Why two, and how they split without colliding

Two parallel sessions cover the foundation faster and cross-check each other — but must not overlap
or they duplicate work and collide on files. The split is by **domain**, with an explicit scope
boundary in each prompt:

- **Session A — the engine room (runtime / logic):** how a user's intent becomes a correct,
  audited, persistent action.
- **Session B — the surface + the proving (presentation / UX / verification):** how the bot is
  organized, rendered, customized, and proven correct.

Each session **claims its own lane** (`docs/owner/claims/`), writes to its **own** report file, and
manages its **own** born-red PR — so they run cleanly in parallel.

## Shared method (both prompts encode this)

Per foundational mechanic in scope: **(a) find how it's done in the CURRENT bot** (read real
source, cite `file:line`), **(b) research 2–3 alternative methods** (web + how leading Discord bots
/ frameworks do it), **(c) pressure-test our decided approach** against them → then an
**adversarial-verify** pass against shipped source (kill any claim that fights the evidence, Q-0120)
→ a **completeness-critic** round ("what foundational mechanic did we forget?", loop until two
rounds add nothing) → **synthesize**. Every surfaced issue is scored by the **10-class
critical-review rubric** and lands in a ranked **issues ledger**; owner-gated calls are **flagged,
not decided**.

---

## PROMPT A — the engine room (paste as its own session)

```text
ultracode: Brainstorm + audit the RUNTIME/LOGIC foundation of the SuperBot rebuild — every foundational mechanic and method that turns a user's intent into a correct, audited, persistent action, both what we USE NOW and what we COULD use. DOCS-ONLY discovery+brainstorm: write no disbot/ and no new-repo code, and do NOT launch any bot. Follow .claude/CLAUDE.md — claim your lane in docs/owner/claims/ first, open a born-red session-card PR, let it auto-merge on green.

READ FIRST: the 2026-07-03 decision logs — docs/planning/rebuild-stage1-global-review-2026-07-03.md, rebuild-conventions-invocation-authority-2026-07-03.md, rebuild-hub-navigation-presets-2026-07-03.md, rebuild-critical-review-rubric-2026-07-03.md — plus router Q-0219…Q-0236 and the frozen reference docs/analysis/rebuild-discovery/new-bot-capability-audit/findings/NEW-BOT-BUILD-PLAN.md + FINAL-REVIEW.md. Where any doc and shipped source disagree, SOURCE WINS (Q-0120).

YOUR SCOPE (the engine room): manifest grammar + compiler + snapshot; the namespace registry (collision prevention, K1); command naming (shared-verb rule, Q-0224); the four-rung invocation ladder — exact (slash/prefix/additive custom triggers), the fuzzy typo matcher's logic, NL intent, NL orchestration (Q-0225); the command RESOLVER convergence point (C-1); authority + bot-owner override (Q-0227); the audited-mutation seam + draft/preview/confirm pipeline (C-2); compound/atomic composition (the workflow engine, the farm-collect canary); the event bus + generated catalogue; lifecycle/tasks + injected clock/RNG; persistence classes + restart-safety under merge=deploy; the cooldown/rate-limit engine (C-6); the DB seam + data model + the manifest-driven selective import (Q-0222); the settings model (SettingSpec, presets Q-0215, safe-default-ON); and the portable substrate-kit.

SCOPE BOUNDARY — do NOT cover (session B owns these): hub/navigation, panel rendering, the card + media engine, interface presets/templates, help/description projection, the response/result grammar, the "did you mean" suggestion rendering, the critical-review rubric itself, the correctness oracle, the layout-success simulator. Where a mechanic spans both (the fuzzy matcher's LOGIC is yours; its rendering is B's), cover only your side and note the handoff seam.

METHOD (make the workflow do this): fan out one agent per mechanic above to (a) find how it's done in the CURRENT bot today (grep/read real source — cite file:line), (b) research 2-3 alternative methods (web + leading bots/frameworks), (c) pressure-test our decided approach. Then an adversarial-verify pass over every finding against shipped source. Then a completeness-critic round — what foundational runtime mechanic did we forget? — looping until two rounds add nothing new. Then synthesize.

APPLY THE RUBRIC: score every issue by the 10 classes in docs/planning/rebuild-critical-review-rubric-2026-07-03.md (dep-order inversion · forgotten capability · thin step · stale claim · fragmentation/reinvention · under-generalization · missing standard · verification hole · UX-contract gap · naming/collision).

DELIVERABLE: docs/analysis/rebuild-discovery/foundations/runtime-logic-mechanics-2026-07-03.md — a mechanics inventory (each: how-now + file:line · options considered · recommendation) + a ranked ISSUES LEDGER (each: rubric-class · evidence · proposed durable fix · needs-owner-decision?). SURFACE issues + options; do NOT re-litigate frozen dispositions and do NOT make owner-gated decisions — flag them for the owner.
```

## PROMPT B — the surface + the proving (paste as its own session)

```text
ultracode: Brainstorm + audit the PRESENTATION/UX + VERIFICATION foundation of the SuperBot rebuild — every foundational mechanic that organizes, renders, customizes, and PROVES the bot, both what we USE NOW and what we COULD use. DOCS-ONLY discovery+brainstorm: write no disbot/ and no new-repo code, and do NOT launch any bot. Follow .claude/CLAUDE.md — claim your lane in docs/owner/claims/ first, open a born-red session-card PR, let it auto-merge on green.

READ FIRST: the 2026-07-03 decision logs — docs/planning/rebuild-stage1-global-review-2026-07-03.md, rebuild-conventions-invocation-authority-2026-07-03.md, rebuild-hub-navigation-presets-2026-07-03.md, rebuild-critical-review-rubric-2026-07-03.md — plus router Q-0219…Q-0236 and the frozen reference docs/analysis/rebuild-discovery/new-bot-capability-audit/findings/NEW-BOT-BUILD-PLAN.md + FINAL-REVIEW.md. Where any doc and shipped source disagree, SOURCE WINS (Q-0120).

YOUR SCOPE (the surface + the proving): hub topology + the navigation engine (Back/Home injected everywhere, semantic parent, every node directly openable — Q-0230/Q-0231); panel rendering (persistent views, versioned custom_id, generated-from-state, restart-safe under merge=deploy); the card engine (CardTemplateSpec + renderer) and media generation (prompt->image, Q-0221); interface presets + the template primitive (C-3, Q-0232); help/description projection + one-description-many-consumers (C-7); the response/result grammar (WorkflowResult, C-4); the "did you mean" suggestion surface (C-5, rendering side); the critical-review rubric itself (is it complete? Q-0233); the correctness oracle (parity goldens + competitor-benchmark + live co-test, Q-0234); and the layout-success simulator unifying the 5 UX-layout sims (Q-0235) + the simulation-driven-design standing rule.

SCOPE BOUNDARY — do NOT cover (session A owns): grammar/compiler, namespace registry, command naming, the invocation ladder's matching logic, the command resolver, authority, the audited-mutation/draft pipeline internals, composition, events, lifecycle, persistence internals, cooldowns, the DB/import seam, settings internals, the substrate-kit. Where a mechanic spans both, cover only your side and note the handoff seam.

METHOD (make the workflow do this): fan out one agent per mechanic above to (a) find how it's done in the CURRENT bot today (grep/read real source — cite file:line; note the 5 existing UX-layout sims and the help projection/overlay as prior art), (b) research 2-3 alternative methods (web + leading bots' UX), (c) pressure-test our decided approach. Then an adversarial-verify pass over every finding against shipped source. Then a completeness-critic round — what foundational presentation/verification mechanic did we forget? — looping until two rounds add nothing new. Then synthesize.

APPLY THE RUBRIC: score every issue by the 10 classes in docs/planning/rebuild-critical-review-rubric-2026-07-03.md.

DELIVERABLE: docs/analysis/rebuild-discovery/foundations/presentation-verification-mechanics-2026-07-03.md — a mechanics inventory (each: how-now + file:line · options considered · recommendation) + a ranked ISSUES LEDGER (each: rubric-class · evidence · proposed durable fix · needs-owner-decision?). SURFACE issues + options; do NOT re-litigate frozen dispositions and do NOT make owner-gated decisions — flag them for the owner.
```

---

## How to launch (owner)

1. Open **two** sessions on this repo.
2. Paste **Prompt A** into one, **Prompt B** into the other. The `ultracode:` keyword makes each
   write + run its own workflow.
3. They're parallel-safe (disjoint scope, own claim files, own report files, own PRs). Each lands a
   report under `docs/analysis/rebuild-discovery/foundations/` and auto-merges on green.
4. Read the two issues ledgers; owner-gated items are flagged for you. Feed the survivors into the
   next planning stage (Stage 2 walk / Gate V verification fleet).

## Deliverables (as the sessions land their reports)

- **Session B — the surface + the proving** (presentation/UX + verification):
  [`../analysis/rebuild-discovery/foundations/presentation-verification-mechanics-2026-07-03.md`](../analysis/rebuild-discovery/foundations/presentation-verification-mechanics-2026-07-03.md)
  — 46 mechanics · 220 verified issues · 87 owner-gated flags (ultracode, 108 subagents).
- **Session A — the engine room** (runtime/logic): `../analysis/rebuild-discovery/foundations/runtime-logic-mechanics-2026-07-03.md` *(lands when Session A's PR merges)*.

## Pointers

- Rubric (the scoring lens): [`rebuild-critical-review-rubric-2026-07-03.md`](rebuild-critical-review-rubric-2026-07-03.md)
- Today's decision logs: [stage-1](rebuild-stage1-global-review-2026-07-03.md) · [conventions](rebuild-conventions-invocation-authority-2026-07-03.md) · [hub/nav](rebuild-hub-navigation-presets-2026-07-03.md)
- Workflow docs: <https://code.claude.com/docs/en/workflows>
- Owner ruling: **Q-0236** in [`../owner/maintainer-question-router.md`](../owner/maintainer-question-router.md)
- Session log: `.sessions/2026-07-03-foundational-mechanics-ultracode-brief.md` (PR #1688)

## Delivered reports

Each session lands one report under `docs/analysis/rebuild-discovery/foundations/`:

- **Session A — engine room (runtime/logic):** [`runtime-logic-mechanics-2026-07-03.md`](../analysis/rebuild-discovery/foundations/runtime-logic-mechanics-2026-07-03.md) — 35 mechanics, 246 rubric-scored issues, 33 owner-gated calls (PR #1690).
- **Session B — surface + proving (presentation/verification):** lands its report in the same folder (parallel session).

## Final judgment (capstone)

After both reports + the owner's 5 independent Codex reviews, a **Fable 5 ultracode** capstone
review gives the final judgment over the whole day's work (verdict · reconciled master ledger ·
re-prioritization · what's still missing). Paste-ready prompt:
[`rebuild-phase-a-final-review-fable5-brief-2026-07-03.md`](rebuild-phase-a-final-review-fable5-brief-2026-07-03.md).
