# 2026-07-06 — Fable 5 Ultracode launch brief: finalize the new-repo-start method

> **Status:** `complete` — deliberate final flip (born-red gate, Q-0133). Docs-only session (no
> `disbot/` runtime code): `check_plan_homing.py --strict` / `check_docs.py --strict` /
> `check_current_state_ledger.py --strict` all green.

## What this session did

Owner asked for **the best possible Fable 5 Ultracode launch prompt** to **finalize the method of
starting the new repo soon** — reviewing the memory substrate-kit, the bot code, the plans, the
simulators, the ways to test the bot, and designing a per-function test-guild. Used my judgment on Fable
5 + Ultracode to shape it.

**Shipped (PR #TBD):** `docs/planning/rebuild-newrepo-start-fable5-ultracode-brief-2026-07-06.md` — a
paste-ready launch brief, homed in the plan index.

**Grounding:** loaded authoritative Fable 5 facts (claude-api skill) + a 3-lane research fan-out
(substrate-kit + Phase-2.5; new-repo-start/migration method + Gate-0; test infra + sims + test-guild),
each verified against live source. Key established facts folded into the prompt:
- **Substrate-kit is FINISHED** (422 tests, #1649, stdlib-only, `python3 bootstrap.py adopt`); the one
  open kit item that gates a new-repo bootstrap is the **Phase-2.5 cold-start A/B — specced but never
  run** (one of two Phase-3 gates; the other is Gate-0 owner ratification).
- **"Finalize the method = close decisions, not write code"** — the new-repo `sb/` package must not be
  created; the session produces a ratifiable start method + owner-decision packet.
- **Two phase vocabularies coexist** (planning-phase vs strategy §3) → the prompt makes reconciling them
  into one canonical arc part of the job.
- **Parity oracle is built but breadth-not-depth** (prefix 96% / events 21% / settings 2%); the 11,510
  suite can't be the oracle; live fidelity is service-layer-only today (author.bot guard blocks
  bot-authored command invocation) → the test-guild deliverable must solve full-pipeline fidelity.
- **No systematic test-guild exists** → the prompt seeds a ~9 category-zone channel layout over the ~55
  cogs for the session to refine.

**Fable-5 tuning folded in** (the reason this is a good prompt, not just a long one): goal + constraints
+ grounding instead of a step-by-step script (Fable degrades when over-prescribed); act-when-ready /
no-tidying / ground-claims-on-evidence / explicit boundaries; use async sub-agents for the review lanes;
keep a memory surface; expect minutes-long turns; run at xhigh.

## ⚑ Self-initiated

None beyond owner direction (author the prompt). Docs-only, reversible; owner-only calls are routed by
the prompt, not decided.

## 💡 Session idea (Q-0089)

**A `docs/planning/` "launch-brief" doc-type convention.** This is now the third paste-ready
Fable/Opus/Codex launch brief in the repo (ultracode-handoff §5, the Gate V launch pad, this one), each
re-deriving the same wrapper: how-to-launch + why-now + model-tuning notes + the prompt + provenance. A
one-page `launch-brief-template.md` (the wrapper + a model-tuning-notes checklist per model family:
Fable=de-prescribe/async-subagents/xhigh, Codex=explorer-fallback/source-read, Agent-Mode=clone-over-
connector) would make the next brief a fill-in rather than a re-derivation, and keep the model-specific
tuning from being forgotten. Pairs with the earlier review-fleet-template idea. (Grep-checked
`docs/ideas/` — not present.)

## ⟲ Previous-session review (Q-0102)

Previous (this branch): the Gate V synthesis (#1767). **Did well:** its §7 owner-decision routing and
the systemic-atomicity finding are exactly the inputs this brief points the Fable session at — the
synthesis handed the next step a clean, decision-shaped surface, which is the whole point of the fleet.
**Missed / system delta:** the synthesis left "two owner gates remain (Gate-0, Phase-2.5)" as prose
without making either *runnable* — this session had to discover that Phase-2.5 is "specced but never
run" via research to realize it's the highest-leverage unblock. The durable lesson: when a synthesis
names a gate as remaining, it should also state whether that gate is *runnable-now-offline* vs
*owner-only* — the actionability class matters as much as the gate's existence. Folded into this brief's
deliverable D (make Phase-2.5 concretely runnable).

## ▶ Next action

Owner runs the brief: fresh `claude-fable-5` session, `/effort xhigh`, paste §3. It produces the
canonical new-repo-start plan + owner-decision packet + test-guild manifest + runnable Phase-2.5
procedure — after which the next action is a **go/no-go on Phase 3**, not more planning. The two hard
gates (Gate-0 ratification, Phase-2.5 cold-start) plus design-spec approval remain the owner's to clear.
