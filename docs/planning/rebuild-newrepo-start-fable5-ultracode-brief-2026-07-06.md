# Rebuild — Fable 5 Ultracode brief: finalize the new-repo-start method + consolidate the foundational plan (2026-07-06)

> **✅ EXECUTED (2026-07-06, PR #1770):** the session ran; its output is
> [`rebuild-canonical-plan-2026-07-06.md`](rebuild-canonical-plan-2026-07-06.md) + companions
> ([test-guild](rebuild-test-guild-design-2026-07-06.md) ·
> [Phase-2.5](rebuild-phase-2.5-procedure-2026-07-06.md)). One framing correction found in
> execution (canonical D-14): the §3 line "the ONE open kit item … is the Phase-2.5 A/B"
> undercounts Q-0223 — there is also one open *code* item, kit tail ① (re-entrant transaction /
> atomic `apply_review_verdict`), still unshipped. Do not re-run this brief.

> **Status:** `historical` — a **paste-ready launch brief** for one Fable 5 Ultracode session that (a)
> **finalizes the *method* of starting the new repo** and (b) **consolidates the scattered rebuild plan
> into one comprehensive, correctly-layered, internally-consistent plan** — verifying that every
> *foundational* capability (AI integration, automation, the live verification/command-probing tooling)
> has a correct home in the layer model. It does **not** start the repo. Mirrors the launch-pad style of
> [`rebuild-ultracode-handoff-2026-07-02.md`](rebuild-ultracode-handoff-2026-07-02.md) §5, tuned for how
> Fable 5 actually behaves. Source + merged PRs win over this doc; the prompt re-verifies against live
> source (Q-0120). **Decision model: the session DECIDES its own calls and flags the high-stakes ones —
> it does not route decisions to the owner** (owner directive **Q-0240**;
> [`../owner/agent-decision-authority.md`](../owner/agent-decision-authority.md)).

## 0. How to launch

Open a **fresh Claude session on `claude-fable-5`**, set **`/effort xhigh`** (or `max` for the hardest
synthesis), and paste §3 verbatim. It's self-contained: goal, grounding anchors, constraints, output.
Ultracode = the native multi-agent Workflow (one coordinator + up to ~16 sub-agents); the prompt tells
the session to *use* that fan-out for the independent review lanes and keep the synthesis for itself.

## 1. Why this session, and why now

Gate V just closed (`../analysis/rebuild-discovery/gate-v/GATE-V-SYNTHESIS.md`): the plan is
source-accurate, **Sequence C** (capability-class, games-as-late-consumers) is adopted, and the fleet
handed Phase B a punch-list. Two things now stand between the project and **starting the new repo**
(Phase 3): the start *method* isn't consolidated into one executable plan, and the rebuild plan is
**scattered across a dozen docs** whose *foundational-layer definitions may be incomplete or
mis-placed* — e.g. AI integration is filed as an L4 "domain" though its invocation/provider seam is
cross-cutting infrastructure; automation/scheduling isn't clearly a foundational layer; the live
verification/command-probing tooling isn't defined as a foundation at all. This session closes both: a
**ratifiable start method** *and* **one comprehensive, correctly-layered plan** that is the single source
of truth.

**The decision model changed (Q-0240).** The session does **not** hand its calls to the owner. Nearly
every decision here is reversible until the owner's Phase-3 go/no-go, so the session **decides each call
itself, records the rationale, and flags the high-stakes ones** for the owner's *one-pass veto at the
gate*. The maintainer usually takes the recommendation and would rather review the set once than answer a
hundred questions. The only stop-and-wait is *executing* something irreversible (creating the repo, prod
writes, moving user data) — which this session never does.

## 2. Fable-5 operating notes (the prompt embeds these — they materially change output quality)

Fable 5 **degrades when over-prescribed** — scripts written for weaker models reduce its output. So this
brief gives it the **goal, the constraints, and the grounding**, and lets it choose its path. Baked-in
Fable tuning: act when it has enough (don't re-litigate settled decisions or narrate options it won't
pursue); **decide its own calls and flag them** rather than parking them (Q-0240); don't tidy/refactor
beyond scope; ground every progress claim on a tool result; respect explicit boundaries; **delegate
independent lanes to asynchronous sub-agents** (Fable sustains long-running sub-agent collaboration
well); keep a memory surface; expect **minutes-long turns**. Run at `xhigh`.

---

## 3. THE PROMPT (paste this)

```
You are a Claude Fable 5 session running in Anthropic Ultracode on menno420/superbot. Effort: xhigh.

GOAL
Two things, one deliverable:
(1) Finalize the METHOD for starting the fresh-rebuild repo, so the maintainer can green-light Phase 3 in
    a single sitting.
(2) Consolidate the scattered rebuild plan into ONE comprehensive, correctly-layered, internally-
    consistent plan — the single source of truth — and in doing so RECONSIDER whether the plan properly
    defines ALL foundational layers. In particular check that these genuinely-foundational capabilities
    have a correct, explicit home in the layer model, not a scattered or mis-placed one: AI integration
    (its invocation/NL-routing/provider/tool-calling seam is cross-cutting infrastructure, distinct from
    the knowledge DOMAINS btd6/project_moon — does the foundational half belong lower/earlier?);
    automation/scheduling (the AutomationScheduler + templated multi-step actions — is it a foundational
    layer near K5 managed-tasks / K7 workflow-engine, or under-defined?); and the live
    verification/command-probing tooling (parity + the Arm D live-test + the test-guild command-driver +
    the wire-level live-bot loop — should be a DEFINED verification foundation, not an afterthought).
You are NOT starting the repo and NOT writing new-repo (`sb/`) code.

DECISION MODEL (important — this is how the maintainer wants you to work; ref docs/owner/agent-decision-
authority.md, Q-0240)
DECIDE your own calls; do not route them to the owner. Nearly every decision here is reversible until the
maintainer's Phase-3 go/no-go, so make each call yourself with a recommendation + a one-line rationale,
record it in a DECISIONS LOG, and keep moving. This includes "too-technical" / architectural design calls
(manifest format, layer placement, F-3 posture, rollback window, test-guild colocation, …) — he usually
takes the recommendation and reviews the set once, at the gate. Do NOT produce an "owner-decision packet"
of open questions. Instead produce a short FLAG-FOR-GATE list: the handful of calls that are irreversible-
once-executed or were formally reserved by a prior gate — DECIDE those too (recommend the ruling), but
flag them prominently as one-line veto items for the go/no-go. Two named flag-for-gate items: the
backward-compat DATA contract (irreversible; touches user balances/inventory/xp/settings) and the Gate-0
rows (12 owner-only default values + L-21, formally reserved — pre-fill your recommended ruling per row so
the owner's sitting is a fast bless-or-override). Route to the maintainer-question-router ONLY genuine
product/vision ambiguity you cannot resolve from source + a defensible default — not technical calls.

WHY THIS MATTERS (connect the work to intent, don't infer it)
Gate V closed; Sequence C is adopted. The maintainer designs and visualizes and relies on you to make the
foundation correct/complete and the start method low-risk so he can commit with confidence. He has
explicitly asked you to make your own decisions — trust that. The current repo becomes the "artifact"
(the why); the new repo becomes the clean source of truth. Do this well and the next action is a
go/no-go, not more planning.

HOW TO WORK (Fable-tuned — follow this, it changes output quality)
- When you have enough to act, act. Don't re-derive facts already in the docs or narrate options you
  won't pursue (thinking is exempt). Where you weigh a call, decide it with a recommendation, not a survey.
- Use Ultracode's parallel sub-agents for the review lanes below, async, while you synthesize; keep the
  reconciliation, the layer taxonomy, and the decisions log for yourself. Give each sub-agent goal +
  anchors + "verify against live source, cite path:line," not a script.
- Ground every claim on a tool result. If unverified, say so; never report a checker/test as passing
  unless it ran. Source + merged PRs win over any planning doc (Q-0120) — code wins, record the drift.
- Keep a working memory file (scratch notes / decisions / open threads); consult it before each lane so
  long sub-agent runs don't lose context.
- Don't tidy/refactor or expand scope beyond (1)+(2). Repo caveats: CI is Python 3.10 — run any checker
  via python3.10 (python3.10 scripts/check_quality.py --check-only, python3.10 -m pytest …); bare tools
  give false results. CodeGraph dead-unresolved/zero-caller is ~100% false-positive here and EventBus/
  registry edges are invisible to graph tools — never assert dead/no-wiring from a graph tool; grep the
  wiring and read the source.

ORIENT FIRST (read in this order, then stop reading and start deciding)
.claude/CLAUDE.md → docs/collaboration-model.md → docs/owner/agent-decision-authority.md (how you decide)
→ docs/current-state.md + docs/current-state/S3-ai-memory.md → docs/AGENT_ORIENTATION.md. Then the two
that define the endpoint: docs/analysis/rebuild-discovery/gate-v/GATE-V-SYNTHESIS.md (the Gate V verdict
+ Phase-B punch-list) and docs/planning/next-session-priority-2026-07-05.md (owner's "what's left").

THE REVIEW LANES (spawn a sub-agent per cluster; anchors given)
1. MEMORY SUBSTRATE-KIT — substrate-kit/README.md + substrate-kit/src/engine/ + substrate-kit/dist/
   bootstrap.py (whole install = `python3 bootstrap.py adopt`) + tests/unit/substrate_kit/ (~422 tests) +
   .sessions/2026-07-02-ultracode-memory-substrate-finalize.md. FINISHED (#1649), stdlib-only. Confirm
   against source; the ONE open kit item that blocks a new-repo bootstrap is the Phase-2.5 cold-start
   substrate-on/off A/B (fresh-rebuild-strategy §3/§5.2, NEVER run). Note the two deliberate not-wired
   seams (review-seam provisioned-not-wired; harvest-table stub); say whether either blocks bootstrap.
2. THE BOT'S CODE + THE FOUNDATIONAL-LAYER TAXONOMY — disbot/ is both the thing rebuilt AND the
   correctness oracle (the new repo replays against it). Don't re-audit it (Gate V did); carry its L0
   readiness + systemic findings (audited-write atomicity across economy/karma/xp; deathmatch _DuelView
   settle-once gap). THEN do the foundational-completeness pass: walk the current L0/kernel set (K0
   config, K1 namespace, K2 manifest compiler, K3 DB seam, K4 EventBus→outbox, K5 lifecycle+tasks, K6
   authority, K7 workflow engine, K8 interaction runtime, K9/K10) against the LIVE bot and ask "is every
   genuinely-foundational capability here, at the right layer?" Explicitly resolve: (a) AI integration —
   grep disbot/services/ai_*/ + the invocation ladder (rebuild-conventions-invocation-authority Q-0225,
   exact→fuzzy→NL-intent→NL-orchestration) — which parts are foundational invocation/provider seam
   (belong at/near K8) vs L4 knowledge domain; (b) automation — grep disbot for AutomationScheduler +
   automation templates — is scheduling/templated-action a foundational layer (near K5/K7) or scattered;
   (c) verification tooling — parity/ + Arm D + tools/livebot idea — define it as a foundational
   verification layer. Use python3.10 scripts/context_map.py <file> + grep, per the caveats.
3. THE PLANS — rebuild-planning-phase-2026-07-03.md (phase arc + MIGRATION), fresh-rebuild-strategy-2026-
   07-02.md (§3 order+gates, §3.1 model allocation, §7 open decisions), rebuild-parallel-execution-plan-
   2026-07-02.md ("two gates"), the Gate-0 packet docs/analysis/rebuild-discovery/foundations/gate-0/
   (owner-decision-packet.md = 12 rows + L-21; phase-b-l0-build-order.md = the 16-step S0–S15 L0 order),
   the frozen NEW-BOT-BUILD-PLAN.md, railway-setup-plan-2026-07-02.md (§4–6 cutover). TWO phase
   vocabularies coexist (planning-phase Capstone→A→GateV→B→C→Migration vs strategy Phase 0–5) — reconcile
   into ONE canonical arc. Flag any place the scattered docs DISAGREE on a foundational definition.
4. THE SIMULATORS — tools/sim/ (8) + tools/game_sim/ (2) + tools/grammar_spike/. DESIGN/decision tools,
   not runtime tests. One line each on what it proves; decide which to re-run or wire as living checks
   (esp. grammar_spike: ~85% of surface units declarable — the linchpin fit number).
5. HOW TO TEST THE BOT — parity/README.md + parity/COVERAGE.md (black-box golden harness: 465 cases,
   current bot = oracle, rebuild replays red-until-parity; run python3.10 -m parity.run capture|check|
   coverage against a truncatable Postgres, NEVER prod). Coverage is breadth-not-depth (prefix 96% /
   slash 88% / components 94% but events 21% / tables 25% / settings 2%). The 11,510-test suite is
   white-box, CANNOT be the oracle (<10% transferable). tests/evals/ is the one pre-existing black-box
   asset. Live fidelity today is service-layer only (Arm D, LIVE-VERIFIED-EVIDENCE-PACK.md) — the full
   command pipeline (converters/cooldowns/before_invoke) isn't exercised live, partly because Discord's
   author.bot guard blocks bot-authored message-command invocation.

THE DELIVERABLES (one consolidated plan + its supporting pieces)
A. ONE comprehensive, correctly-layered, canonical rebuild plan — the single source of truth. It states:
   the corrected/complete FOUNDATIONAL-LAYER taxonomy (with AI-invocation, automation/scheduling, and the
   verification substrate placed correctly, and any missing foundational layer named); the one canonical
   phase arc (the two vocabularies reconciled); the two hard gates blocking all new-repo code (Gate-0
   ratification; Phase-2.5 cold-start) + the design-spec approval; and the ordered start sequence — create
   repo → bootstrap the finished substrate-kit → build the two spines → run the 16-step S0–S15 L0 build
   (critical path K0→K1→K2→K3→K7→K8) under the container-first 3-phase cutover (CUT-1 container-only live
   test on the test-bot token → CUT-2 manifest-driven selective import → CUT-3 token swap + retirement) on
   a new Railway project (superbot-next), keeping the repo-as-artifact framing. Output a single ordered
   "to start the new repo, do these N steps; steps k..m are owner-gated" list an operator could execute.
   Where the old scattered docs are now superseded by this one, say so (link, don't delete).
B. The FOUNDATIONAL-COMPLETENESS findings that feed A — your explicit rulings on AI-integration layering,
   automation/scheduling layering, and the verification-substrate layer, each as a decided call with
   rationale (per the DECISION MODEL — decide, don't ask). Include any foundational layer you found
   MISSING or mis-placed and where you put it.
C. The TEST-GUILD design — a concrete Discord test-guild layout with a proper channel per function so
   every subsystem has a home to be exercised and observed. Seed to refine against disbot/cogs/ (~55
   cogs): #operator-core (settings/diagnostic/help/admin/server-management/setup) · #moderation-safety
   (moderation/automod/security/cleanup/image-moderation/logging) · #server-structure (channel/role/
   ticket/counters/proof-channel) · #presentation (welcome/ux-lab/card-engine) · #economy-progression
   (economy/karma/xp/community/leaderboard/profile) · #games (blackjack/rps/deathmatch/fishing/farm/
   creature/casino/counting/chain/four-twenty/mining/giveaways/starboard/explore) · #knowledge-ai (ai/
   btd6/project-moon) · #utility-misc (utility/general) · #control-plane (dashboard/boards/migration/
   health). Per zone: which subsystems get their own channel vs share, and how the layout maps onto CUT-1.
   Then solve the fidelity gap: how the guild drives the FULL command pipeline (not just the service
   layer) given the author.bot guard — a low-privilege human/second-account driver, or an in-process
   wire-level walker (docs/ideas/wire-level-live-bot-loop-2026-07-02.md). Tie back to parity/ + the
   verified_live sign-off. Output a channel manifest + a per-zone "what you'd exercise / what proves it".
D. Make Phase-2.5 concretely runnable — the one open, OFFLINE, non-owner-gated step that closes a gate
   (substrate-on-vs-off cold-start A/B). Turn "specced but never run" into a runnable procedure: what
   environment, what to measure (boot viability, orientation budget, first-session behavior kit ON vs
   OFF), the pass bar, and the artifact it produces. Highest-leverage single thing to unblock Phase 3.
E. The DECISIONS LOG + FLAG-FOR-GATE list — every method call you made (decision · options weighed ·
   rationale), plus the short flag-for-gate list (the backward-compat data contract + the Gate-0 rows
   with your pre-filled recommended rulings) for the owner's one-pass veto at the go/no-go.

CONSTRAINTS
- Planning/consolidation only, but you DECIDE (per the DECISION MODEL) — you do not park decisions. You
  MUST NOT: create the new repo or any `sb/` code; touch production (Railway, the live token, the prod
  DB); run parity against a non-throwaway Postgres; execute the test-guild build (spec it, don't stand it
  up). The safety brake is EXECUTING something irreversible — deciding it on paper is expected.
- Match CI: python3.10 for any checker/test. Don't claim something ran unless it ran.
- Stop-and-ask only for genuine product/vision ambiguity you can't resolve from source + a defensible
  default, or a source/plan conflict that changes the foundation and has no safe call. Everything else:
  decide and flag.

OUTPUT
Write the consolidated plan as a new canonical doc under docs/planning/ (the single source of truth),
with the foundational-completeness findings, test-guild manifest, Phase-2.5 procedure, and decisions-log
+ flag-for-gate list either in it or as linked companions, homed in docs/planning/README.md. Mark the
docs it supersedes. Open a PR ready. Done when the maintainer can read the plan + skim the flag-for-gate
list and green-light Phase 3 without re-deriving any of it.
```

---

## 4. Provenance

Built 2026-07-06 after Gate V closed; **revised the same day** to (1) adopt the decide-and-flag decision
model (owner directive **Q-0240** → `../owner/agent-decision-authority.md`) so the session makes its own
calls instead of routing them, and (2) add the **foundational-completeness + consolidation** scope the
maintainer asked for — verify every foundational capability (AI integration, automation, the live
verification/command-probing tooling) is correctly layered, and fold the scattered plan into one
canonical source of truth. Grounded by a 3-lane research fan-out (substrate-kit + Phase-2.5;
new-repo-start/migration method + Gate-0; test infra + simulators + test-guild), each verified against
live source. Fable-5 tuning (anti-overplanning, decide-and-flag, no-tidying, ground-claims, boundaries,
async sub-agents, memory surface, xhigh, minutes-long turns) from Anthropic's Fable 5 guidance.
