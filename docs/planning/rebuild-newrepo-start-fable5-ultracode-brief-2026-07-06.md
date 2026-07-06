# Rebuild — Fable 5 Ultracode brief: finalize the new-repo-start method (2026-07-06)

> **Status:** `plan` — a **paste-ready launch brief** for one Fable 5 Ultracode session whose job is to
> **finalize the *method* of starting the new repo** — not to start it. Mirrors the launch-pad style of
> [`rebuild-ultracode-handoff-2026-07-02.md`](rebuild-ultracode-handoff-2026-07-02.md) §5, tuned for how
> Fable 5 actually behaves. Source + merged PRs win over this doc; the prompt tells the session to
> re-verify everything against live source (Q-0120).

## 0. How to launch

Open a **fresh Claude session on `claude-fable-5`**, set **`/effort xhigh`** (or `max` for the hardest
synthesis), and paste §3 verbatim. It's self-contained: goal, grounding anchors, constraints, output.
Ultracode = the native multi-agent Workflow (one coordinator + up to ~16 sub-agents); the prompt tells
the session to *use* that fan-out for the independent review lanes and keep the synthesis for itself.

## 1. Why this session, and why now

Gate V just closed (`../analysis/rebuild-discovery/gate-v/GATE-V-SYNTHESIS.md`): the plan is
source-accurate, **Sequence C** (capability-class, games-as-late-consumers) is adopted, and the fleet
handed Phase B a punch-list. What now stands between the project and actually **starting the new repo**
(Phase 3) is a small, *decidable* set of things — **two gates and a handful of open method decisions** —
plus the confidence that the test strategy will catch regressions during cutover. This session's job is
to **close that gap on paper** so the owner can green-light the build with one sitting, not ten.

The maintainer's framing (verified in the planning set): **"finalizing the method = closing decisions,
not writing code."** The new-repo `sb/` package must not be created here. The deliverable is a
*ratifiable* start method + the owner-decision packet for the few calls that are genuinely the owner's.

## 2. Fable-5 operating notes (the prompt embeds these — they materially change output quality)

Fable 5 is Anthropic's most capable model but **degrades when over-prescribed** — prompts written as
step-by-step scripts for weaker models reduce its output. So this brief gives it the **goal, the
constraints, and the grounding**, and lets it choose its own path. The prompt bakes in the behavioral
tuning Anthropic documents for Fable 5: act when it has enough to act (don't re-litigate settled
decisions or narrate options it won't pursue), don't tidy/refactor beyond the task, ground every
progress claim on a tool result, respect explicit boundaries, **delegate independent lanes to
asynchronous sub-agents** (Fable sustains long-running sub-agent collaboration well), keep a memory
surface, and expect **minutes-long turns**. Run it at `xhigh`.

---

## 3. THE PROMPT (paste this)

```
You are a Claude Fable 5 session running in Anthropic Ultracode on menno420/superbot. Effort: xhigh.

GOAL
Finalize the METHOD for starting the fresh-rebuild repo, so the maintainer can green-light Phase 3 (the
new-repo build) in a single sitting. You are NOT starting the repo and NOT writing new-repo (`sb/`)
code. Your deliverable is a ratifiable start-method plan + an owner-decision packet for the calls that
are genuinely the owner's + a concrete test-guild design. "Finalize the method" = close the decidable
decisions and cleanly frame the rest — not build.

WHY THIS MATTERS (so you can connect the work to intent rather than infer it)
Gate V just closed: the plan is source-accurate, Sequence C (games-as-late-consumers) is adopted. The
only things between here and the build are two gates and a few open method decisions. The maintainer
designs and visualizes; he relies on you to make the start method correct, complete, and low-risk so he
can commit with confidence. The current repo is becoming the "artifact" (the why); the new repo will be
the clean source of truth. Do this well and the next action is a go/no-go, not more planning.

HOW TO WORK (Fable-tuned — follow this, it changes output quality)
- When you have enough to act, act. Don't re-derive facts already in the docs, re-litigate decisions the
  maintainer already made, or narrate options you won't pursue in user-facing text (thinking is exempt).
  Where you're weighing a call, give a recommendation, not a survey.
- Use Ultracode's parallel sub-agents for the independent review lanes below, running asynchronously
  while you synthesize; keep the final reconciliation and the owner-decision packet for yourself. Give
  each sub-agent the goal + the anchors + "verify against live source, cite path:line," not a script.
- Ground every claim on a tool result (a file you read, a command you ran). If something isn't verified,
  say so. Never report a checker/test as passing unless it actually ran. Source + merged PRs win over
  any planning doc (Q-0120) — when a doc and the code disagree, the code wins and you record the drift.
- Keep a working memory file as you go (scratch notes / decisions / open threads); consult it before
  each lane so long sub-agent runs don't lose context.
- Don't tidy, refactor, or expand scope beyond finalizing the method. Don't decide the owner-only items
  (below) — route them to `docs/owner/maintainer-question-router.md` as a clean packet.
- Repo caveats: CI is Python 3.10 — run any checker via `python3.10` (`python3.10 scripts/check_quality.py
  --check-only`, `python3.10 -m pytest …`); bare tools give false results. CodeGraph `dead-unresolved`/
  zero-caller is ~100% false-positive here and EventBus/registry edges are invisible to graph tools —
  never assert dead/no-wiring from a graph tool; grep the wiring and read the source.

ORIENT FIRST (read in this order, then stop reading and start deciding)
.claude/CLAUDE.md → docs/collaboration-model.md → docs/current-state.md + docs/current-state/S3-ai-memory.md
→ docs/AGENT_ORIENTATION.md. Then the two that define the endpoint you're finalizing the path to:
docs/analysis/rebuild-discovery/gate-v/GATE-V-SYNTHESIS.md (the just-closed Gate V verdict + Phase-B
punch-list) and docs/planning/next-session-priority-2026-07-05.md (owner's own "what's left" read).

THE FIVE THINGS TO REVIEW (the maintainer named these — spawn a sub-agent lane per cluster; anchors given)
1. MEMORY SUBSTRATE-KIT — substrate-kit/README.md + substrate-kit/src/engine/ + substrate-kit/dist/bootstrap.py
   (the whole install is `python3 bootstrap.py adopt`) + tests/unit/substrate_kit/ (~422 tests) +
   .sessions/2026-07-02-ultracode-memory-substrate-finalize.md. It is FINISHED (#1649) and stdlib-only.
   Confirm that against source; identify the ONLY genuinely-open kit item that blocks a new-repo bootstrap:
   the Phase-2.5 cold-start substrate-on/off A/B (specced in fresh-rebuild-strategy §3/§5.2, NEVER run).
   Note the two deliberate not-fully-wired seams (review-seam provisioned-not-wired; harvest-table stub)
   and whether either blocks bootstrap. Deliverable: a one-page "kit is bootstrap-ready EXCEPT X" verdict.
2. THE BOT'S CODE — disbot/ is both the thing being rebuilt AND the correctness oracle (the new repo
   replays against it). You don't re-audit it (Gate V did); confirm the L0 readiness the synthesis
   already established and the systemic findings it must carry (audited-write atomicity across
   economy/karma/xp; deathmatch _DuelView settle-once gap). Use python3.10 scripts/context_map.py <file>
   and grep, per the caveats.
3. THE PLANS — docs/planning/rebuild-planning-phase-2026-07-03.md (phase arc + MIGRATION section),
   fresh-rebuild-strategy-2026-07-02.md (§3 order+gates, §3.1 model allocation, §7 open decisions),
   rebuild-parallel-execution-plan-2026-07-02.md (schedule + the "two gates" framing), the Gate-0 packet
   docs/analysis/rebuild-discovery/foundations/gate-0/ (owner-decision-packet.md = 12 owner-only rows +
   L-21; phase-b-l0-build-order.md = the 16-step S0–S15 L0 build order), the frozen reference
   docs/analysis/rebuild-discovery/new-bot-capability-audit/findings/NEW-BOT-BUILD-PLAN.md, and
   railway-setup-plan-2026-07-02.md (§4–6 cutover). TWO phase vocabularies coexist (planning-phase's
   Capstone→A→GateV→B→C→Migration vs strategy's Phase 0–5); reconciling them into ONE canonical arc is
   part of your job.
4. THE SIMULATORS — tools/sim/ (8), tools/game_sim/ (2), tools/grammar_spike/. These are DESIGN/decision
   tools, not runtime tests. Confirm what each proves (one line each) and, crucially, which ones the
   new-repo-start method should re-run or wire in as living checks (esp. grammar_spike: ~85% of surface
   units declarable — the linchpin fit number).
5. HOW TO TEST THE BOT — parity/README.md + parity/COVERAGE.md (the black-box golden harness: 465 cases,
   current bot = oracle, rebuild replays red-until-parity; run `python3.10 -m parity.run capture|check|
   coverage` against a truncatable Postgres, NEVER prod). Coverage is deliberately breadth-not-depth
   (prefix 96% / slash 88% / components 94% but events 21% / tables 25% / settings 2%). The 11,510-test
   suite is white-box and CANNOT be the oracle (<10% transferable). tests/evals/ is the one pre-existing
   black-box asset. Live fidelity today is service-layer only (Arm D, LIVE-VERIFIED-EVIDENCE-PACK.md) —
   the full command pipeline (converters/cooldowns/before_invoke) is not yet exercised live, partly
   because Discord's author.bot guard blocks bot-authored message-command invocation.

THE FOUR DELIVERABLES (this is the finalized method)
A. ONE canonical new-repo-start method. Reconcile the two phase vocabularies into a single arc ending at
   Phase 3. State plainly: the two hard gates that block all new-repo code — (1) Gate-0 owner
   ratification (rule/bless the 12 owner-only default values + L-21; grammar shapes are already frozen),
   (2) Phase-2.5 cold-start proof (never run) — plus the design-spec owner approval. Then the concrete
   start sequence: create repo → bootstrap the finished substrate-kit → build the two spines → run the
   16-step S0–S15 L0 build (critical path K0→K1→K2→K3→K7→K8), under the container-first 3-phase cutover
   (CUT-1 container-only live test on the test-bot token → CUT-2 manifest-driven selective import →
   CUT-3 token swap + retirement), on a new Railway project (superbot-next). Keep the repo-as-artifact
   framing. Output a single ordered "to start the new repo, do these N steps; steps k..m are owner-gated"
   list an operator could execute.
B. The owner-decision packet — the small set of calls that genuinely gate the start and are the owner's,
   framed for a one-sitting ruling (each: the decision, the options, your recommendation, the
   consequence, the owning artifact). At minimum: Gate-0's 12 rows + L-21; the backward-compat contract
   (strategy §7 calls it "the single biggest rebuild decision"); the manifest physical format (Python
   dataclasses vs YAML/JSON); F-3 intent-denial posture (degrade vs fail-closed); the rollback window;
   whether the test guild is the live "Superbot Admin" HQ guild or strictly separate. Route these to
   docs/owner/maintainer-question-router.md — do not decide them.
C. The TEST-GUILD design — a concrete Discord test-guild layout with a proper channel per function so
   every subsystem has a home to be exercised and observed. Start from this proposed category-zone
   seed (refine it against the real cog set in disbot/cogs/, ~55 cogs): #operator-core (settings/
   diagnostic/help/admin/server-management/setup) · #moderation-safety (moderation/automod/security/
   cleanup/image-moderation/logging) · #server-structure (channel/role/ticket/counters/proof-channel) ·
   #presentation (welcome/ux-lab/card-engine) · #economy-progression (economy/karma/xp/community/
   leaderboard/profile) · #games (blackjack/rps/deathmatch/fishing/farm/creature/casino/counting/chain/
   four-twenty/mining/giveaways/starboard/explore) · #knowledge-ai (ai/btd6/project-moon) ·
   #utility-misc (utility/general) · #control-plane (dashboard/boards/migration/health). For each zone,
   say which subsystems get their own channel vs share, and how the layout maps onto the CUT-1
   container-only live test. Then solve the fidelity gap: how the guild drives the FULL command pipeline
   (not just the service layer) given the author.bot guard — e.g. a low-privilege human/second-account
   driver, or an in-process wire-level walker (see docs/ideas/wire-level-live-bot-loop-2026-07-02.md).
   Tie it back to parity/ (the golden oracle) and the verified_live sign-off. Output a channel manifest
   + a per-zone "what you'd exercise here and what proves it" table.
D. Make Phase-2.5 concretely runnable. It's the one open, OFFLINE, non-owner-gated step that closes a
   gate (the substrate-on-vs-off cold-start A/B validating the portability thesis). Turn "specced but
   never run" into a runnable procedure: what environment, what to measure (boot viability, orientation
   budget, first-session behavior with the kit ON vs OFF), what the pass bar is, and what artifact it
   produces. This is the highest-leverage single thing to unblock Phase 3.

CONSTRAINTS
- Planning/finalization only. You MAY create/refine planning docs and route owner decisions. You MUST
  NOT: create the new repo or any `sb/` code; touch production (Railway, the live token, the prod DB);
  run parity against a non-throwaway Postgres; decide owner-only items. Test-guild work is DESIGN here —
  actually standing it up is operator work you spec, not do.
- Match CI: python3.10 for any checker/test. Don't claim something ran unless it ran.
- If a genuine blocker appears (a source/plan conflict that changes the method, a missing canonical
  artifact, an owner-only call with no safe default), surface it in the packet rather than guessing.

OUTPUT
Write the finalized method as a new planning doc under docs/planning/ (a single canonical
new-repo-start plan), with the owner-decision packet and the test-guild manifest either in it or as
linked companions, homed in docs/planning/README.md. Open a PR ready. The session is done when the
maintainer can read the plan and the packet and green-light Phase 3 (or answer the packet) without
re-deriving any of it.
```

---

## 4. Provenance

Built 2026-07-06 after Gate V closed. Grounded by a 3-lane research fan-out (substrate-kit + Phase-2.5;
new-repo-start/migration method + Gate-0; test infra + simulators + test-guild), each verified against
live source. Fable-5 tuning (anti-overplanning, no-tidying, ground-claims, boundaries, async sub-agents,
memory surface, xhigh effort, minutes-long turns) taken from Anthropic's Fable 5 guidance and folded in
so the prompt gives goal+constraints+grounding rather than an over-prescribed script. The four
deliverables map to the maintainer's ask: finalize the start method, review the kit/code/plans/sims/
tests, and design a per-function test guild.
