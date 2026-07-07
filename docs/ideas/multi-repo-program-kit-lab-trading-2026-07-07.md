# The multi-repo program: superbot-next · the substrate-kit self-improvement lab · the trading research repo

> **Status:** `ideas` — owner-dropped live 2026-07-07 (the consolidation conversation, after
> PRs #1791–#1793), captured same day with the strengthening the owner asked for ("use your
> advanced reasoning to strengthen my ideas"). This is a **program-level** capture: it frames
> three repos and answers the repo-start-mechanics question. Nothing here changes the canonical
> rebuild plan ([`rebuild-canonical-plan-2026-07-06.md`](../planning/rebuild-canonical-plan-2026-07-06.md))
> — part 1 *is* that plan; parts 2–3 are new program surface.
> **Subsystem:** none (agent-workflow / program architecture).

## The owner's vision, in his words (condensed)

1. **Repo-start mechanics:** "should the new session in the new repo just clone the old repo
   first and work from there, kind of like how we did it with the btd6 mod helper repo, or is
   there a better way?"
2. **Multiple repos:** one for the bot and everything that belongs with it; **one dedicated to
   the memory-system kit, with the only goal of self-improvement and nothing else** — it could
   also produce ideas as its testable output; "create a system that optimises itself by
   independently working through all possible ideas they can come up with while having complete
   freedom"; Railway access; extra work surfaces where possible (a separate bot token, websites
   they can independently get online, view, and improve).
3. **A repo dedicated to stock-market research and trading** — "find, discover, create the best
   possible trading strategies and backtest them through simulations, real-time trades," possibly
   with a website to keep track of everything.
4. "How does the current substrate kit relate to these ideas?"

## Part 0 — Repo-start mechanics: fresh-from-kit, old repo attached as the ORACLE (never clone-as-base)

The canonical plan already decides this, and the reasoning survives re-examination:

- **The new repo starts empty + `dist/bootstrap.py adopt`** (plan §5 steps 6–7). It is *born*
  from the kit, not from the old code.
- **The old repo is attached to the build session read-only, alongside** — the btd6-mod-helper
  *session* pattern (both repos visible in one session) is right; the *clone-as-base* pattern is
  not. The build sessions read the old source freely (it is the oracle and the reference), but
  nothing is copied wholesale.
- **What crosses over is a pinned artifact list, not code:** the frozen specs + Gate-0 grammar
  (by reference — they live in the old repo as the what/why/how record), the **465+ parity
  goldens** (pinned outside the new repo's write reach — the behavioral contract the new bot must
  reproduce), the **compat artifacts** (`custom_id` lists, event literals, subsystem keys, audit
  payload shapes — gate 6 diffs against them), and at CUT-2 the **data** via the manifest-driven
  importer. Behavioral continuity comes from goldens, not from carried code.
- **Why not clone:** a clone imports the disease the rebuild exists to cure (the smeared files,
  ~47k dead-classified symbols, the tracked layer violations), drags the full git history into a
  repo whose whole point is clean provenance, and makes "what is new-bot truth?" ambiguous from
  day one. The rebuild's premise is *behavior continuity with zero code continuity*, enforced by
  red-until-parity.

## Part 1 — `superbot-next` (already the plan of record)

Nothing new to capture — plan §5 steps 6–17, ready to start. Listed here only so the program
frame is complete: this is repo #1 and the kit's **second consumer** (see part 2 — that matters).

## Part 2 — The substrate-kit repo: the self-improvement lab

### Why a dedicated repo is the kit's natural destiny

The kit was *designed* portable (nervous system + context-economy engine + one-step adopt;
stdlib-only; 432 tests). Today it has exactly **one consumer** (this repo), which means kit
quality and superbot idiosyncrasy are indistinguishable — nobody can tell whether a kit
convention works *in general* or merely *here*. The moment `superbot-next` adopts (plan step 7),
the kit has two consumers and the same logic as the repo's own **Q-0219 second-consumer rule**
fires at repo scale: shared machinery with ≥2 consumers earns its own home. **Extract the kit to
its own repo at that moment** — consumers adopt *versioned* kit releases via `bootstrap.py`
(the adopt/upgrade discipline already exists), so a kit change can never silently break a
consumer.

### The lab: strengthened

The owner's core idea — a repo whose autonomous loop has one goal, *make the system better*, with
complete freedom — is sound, and it already has a founding document
([`autonomous-improvement-loop-vision-2026-06-12.md`](autonomous-improvement-loop-vision-2026-06-12.md)).
The strengthening it needs is **fitness functions, not vibes**:

1. **A standing, measurable benchmark.** The Phase-2.5 A/B protocol
   ([companion D](../planning/rebuild-phase-2.5-procedure-2026-07-06.md)) is exactly this and
   already exists: cold-start paired sessions on throwaway repos, measured orientation footprint,
   wrong-turn count, task completion, judge-scored. The lab re-runs it per kit release. **Its
   founding challenge is already known and honest:** the 2026-07-07 re-run left the kit's
   cold-start *benefit* claim unproven (ON arms read more and shipped no better; twice failed to
   end cleanly; never wrote back to kit surfaces). A lab whose first measurable win is "make the
   A/B flip" starts with a real, falsifiable goal instead of ceremony.
2. **Ideas as *testable* output — with an acceptance metric.** "Produce ideas" is only a real
   output if it's scored: ideas that get *implemented in a consumer repo and survive* (not
   reverted, not worked around) within N sessions count; unbuilt or reverted ones don't. The
   idea-lifecycle machinery (capture → route → build → review) already exists to ride.
3. **Work surfaces = observable outputs.** The owner's instinct is exactly right: give the lab
   its own **test bot token** (the Galaxy-Bot pattern), its own **Railway project** with a spend
   cap, and **deployable websites** it can put online and iterate on end-to-end without the owner
   in the loop. Each surface makes an improvement *externally verifiable* — the difference
   between "the loop says it improved" and "you can click the thing it improved."
3b. **Model-for-task allocation as a standing lab benchmark (owner ruling Q-0248, same day —
   BOTH planes: agent sessions AND runtime/product API calls incl. image gen/review + website AIs;
   the product plane enforces through K10's task registry/profile resolver, judged by the A-17
   eval machinery + per-call cost/latency).**
   Every session logs `model · effort · task-class · outcome` (objective outcomes first: CI-green
   on first push, checker findings, rework/revert rate, tokens per merged PR); the lab runs
   paired same-task A/Bs per task class (the Phase-2.5 judge pattern) to maintain a
   cost-quality frontier; escalation/de-escalation rules are mechanical (two red CI rounds or
   frozen-grammar contact ⇒ escalate a tier; a cheaper tier matching outcomes for M consecutive
   tasks ⇒ de-escalate). The telemetry starts at the kickoff session (Q-0248) and shares the
   Q-0249 ~2-month observation window, so budget data and allocation data are one dataset.
4. **Cross-repo friction reports close the loop.** Consumer repos (superbot-next, trading) file
   kit-friction deltas (the context-delta pattern from the collaboration model); the lab consumes
   them as its inbound work queue; fixes ship as versioned kit releases; consumers upgrade and
   the A/B + friction rate say whether it worked. That triangle — lab improves, consumers adopt,
   metrics arbitrate — is the whole design.
5. **"Complete freedom" gets the Q-0241 shape, not literal absence of rails:** reversible by
   default, budget caps (tokens + Railway spend), **scoped credentials only** (the lab never
   holds another repo's prod secrets or the live bot's token), everything audited, owner reads
   outputs and vetoes reactively. One structural guard matters more than all others:
   **the lab must measure itself on cold sessions and throwaway repos** — Phase-2.5's deepest
   lesson is that a warm session cannot evaluate its own substrate; a self-improvement loop that
   grades itself on its own warm context will optimize the grade, not the system.

## Part 3 — The trading research repo

### Understood as: a strategy-research *platform*, not a stock-picking bot

Data ingestion → strategy generation → backtesting → paper trading → (eventually) capped live
execution → a tracking website. The repo's existing DNA maps onto it almost one-to-one:

| SuperBot discipline | Trading twin |
|---|---|
| Sim-decides-design (V-3, Q-0243) | **Backtest-decides-strategy** — no strategy ships on narrative |
| Golden parity / drift pins | **Pinned point-in-time data snapshots + fully reproducible backtest runs** (a backtest that can't be replayed byte-identically doesn't count) |
| Decide-and-flag + gates | **A promotion ladder with machine-checked gates**: in-sample → out-of-sample → walk-forward → paper → small-capped live; a strategy is *promoted*, never declared |
| Adversarial verify (the workflow pattern) | **Falsification-first**: a great backtest is a *candidate for refutation* (overfitting hunt), not a result |
| Q-0213 destructive brake | **The real-money brake** (below) |
| botsite / dashboard export | The tracking website — generated from the strategy registry + results store, agent-deployable |

### The rigor that must be designed in from day one (cheap now, ruinous to retrofit)

- **Point-in-time data** — survivorship-bias-free universes, no look-ahead (fundamentals as they
  were known, not as later restated). This is the #1 silent killer of retail backtests.
- **Multiple-testing correction** — an autonomous loop that searches thousands of strategies
  *will* find spectacular backtests by chance; the promotion ladder must price that in (holdout
  embargo periods, deflated performance metrics, strict out-of-sample discipline).
- **Pessimistic cost modeling** — commissions, spread, slippage, borrow costs; a strategy that
  dies under pessimistic costs was never alive.
- **Regime honesty** — walk-forward evaluation across regimes, never one heroic full-history fit.
- **The real-money brake:** paper trading is fully autonomous (broker paper environments, e.g.
  Alpaca-class APIs); **live orders sit behind owner-set hard caps** (per-trade, per-day, total
  exposure) **+ a kill switch**, keys scoped to a small account. This is the one genuinely
  irreversible-money surface in the whole program — it keeps the ask-first tier even under
  never-wait, exactly like CUT-3's data tier kept its reversibility rider.
- **Honest goal-setting:** the measurable objective is "strategies that survive falsification and
  beat costs out-of-sample," never promised returns. The lab's value is the *platform* — the
  discipline, reproducibility, and search capacity — which is real regardless of whether any
  single strategy is an edge.

## How the substrate kit relates to all of it (the connective answer)

The kit is the **shared substrate of the whole program** — that was its founding purpose
("portable"). Concretely: every repo adopts it for orientation/journal/guards/session-workflow;
the kit repo is its home *and* its lab; `superbot-next` and the trading repo are consumers #2 and
#3. Multi-repo is not just compatible with the kit — **it is what finally makes the kit's value
measurable**, because improvements must generalize across three very different consumers (a
Discord bot port, a greenfield research platform, and the lab itself) instead of fitting one
repo's habits. The workflow layer above the kit (claims, question router, routines, CI guards)
ships as kit-planted templates that each repo instantiates.

## Recommended sequencing (decide-and-flag; ⚑ vetoable)

1. **Now:** `superbot-next` per plan §5 steps 6–8 — unchanged, ready.
2. **At step 7 (the second-consumer moment):** extract the kit to its own repo; superbot-next
   adopts *from the kit repo* rather than from the in-tree copy; this repo's `substrate-kit/`
   becomes a consumer pin too. The lab starts small: the A/B benchmark as a routine + the
   friction-report inbox — not a fleet of loops on day one.
3. **Third:** the trading repo, adopting the kit (consumer #3) — data + backtest engine + paper
   trading first; the website next; capped live execution last, behind the real-money brake.
4. **Rail before scale:** each repo's autonomy loop gets its guardrails (budgets, scoped
   credentials, benchmark) proven before the next repo launches — three unproven autonomy loops
   in one week is how a program loses observability.

## Open forks for the owner (flag, not blockers)

- ~~Kit-repo timing: extract at step 7 (recommended) vs immediately vs after the port completes.~~
  **RATIFIED (Q-0247, 2026-07-07): extract at step 7; both repos created in the kickoff session
  (brief: [`../planning/rebuild-kickoff-steps-6-8-brief-2026-07-07.md`](../planning/rebuild-kickoff-steps-6-8-brief-2026-07-07.md)).**
- ~~The lab's Railway budget cap~~ **superseded by Q-0249 (2026-07-07): no caps yet — spend
  telemetry + a ~2-month observation window first; security rails (scoped credentials, the
  trading real-money brake) stand regardless.** Still open: which extra work surfaces to
  provision first (bot token vs website vs both).
- ~~Trading: which market/asset class first (the data-vendor and broker-API choice hangs on it)~~
  **RULED (Q-0250, 2026-07-07): stocks-first — US large-cap tech (the owner's domain; crypto
  suggestion withdrawn); point-in-time universe rule (never the owner's current holdings); paper
  lane on an API broker (DEGIRO has no official API); DEGIRO integrates read-only at the tracker
  as the owner's manual benchmark lane.** Still open: the initial live-execution caps when that
  distant gate arrives.
- Whether the trading repo's autonomy runs under the same never-wait model from day one or
  starts owner-gated until the falsification ladder has proven itself on paper trades.

## Recommended routing

Program-level; touches the rebuild plan only at the step-7 extraction note. **Sequencing ratified
same day (Q-0247)** and the kickoff is packaged:
**[`../planning/rebuild-kickoff-steps-6-8-brief-2026-07-07.md`](../planning/rebuild-kickoff-steps-6-8-brief-2026-07-07.md)**
(paste-ready; creates both repos, pre-decides the extraction fork ⚑, owner-input checklist).
The trading repo gets its own founding brief when its turn comes (third, rail-before-scale) —
its rigor list above is the skeleton. Related rulings landed after capture: Q-0248
(model-for-task allocation discipline) and Q-0249 (budget observe-first window).
