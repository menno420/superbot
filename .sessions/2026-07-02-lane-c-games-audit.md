# 2026-07-02 — Lane C new-bot capability audit (Games & Community)

> **Status:** `complete`
> **Branch:** `claude/lane-c-games-audit-q35nkr` · **PR:** #1664
> **Session type:** ultracode audit (docs-only) — new-bot-capability-audit Lane C

## What happened

Completed **Lane C** of the new-bot capability audit — the hardest grammar-fit lane (blackjack
measured 44% in the spike). Verified + tiered every surface unit of the 10 Games & Community
subsystems against the §2 manifest grammar, wrote manifest sketches, dispositioned every tier-3,
computed fit numbers, flagged structural danger zones, and added MAP→RECONSIDER→SIMULATE→OPTIMIZE
recommendations with the capstone carry-forward fields. Output is one file:
`docs/analysis/rebuild-discovery/new-bot-capability-audit/lanes/lane-C-games.md`. **Zero `disbot/`
runtime code touched.**

**Method (ultracode fan-out):** 10 parallel deep source-verification agents (one per subsystem,
every `file:line` re-verified against source per Q-0120) → a 4-lens adversarial re-check (blackjack
calibration · every proposed game-state amendment · every tier-3-that-could-be-tier-2 · every
reward/settlement path) → synthesis. I also ran my own independent source verification of the
highest-stakes calibration facts *in parallel with the fleet* (message-pipeline wiring, the
`game_wager_workflow` settlement seam, deathmatch turn loop, rps bracket) and cross-checked the
agents against it. 14 agents, 0 errors, ~1.37M tokens.

### Result: GO-with-amendments — 70% → 84% (289 units)

The hardest lane lands almost exactly where the spike's 3-subsystem sample predicted (spike
73%→85% vs Lane C 70%→84%), and **both spike anchors reproduce verbatim** (blackjack 44%→44%,
karma 80%→87%) — which validates the measurement. The §2 grammar *can* express the game/community
surface as durable generated declarations, given three new tier-2 families and keeping game
engines/rules/renderers/moves as deliberate tier-3 escape hatches. No structural rethink needed.

**New ratified amendments:** **G-7 MessagePipelineStageSpec** (counting/chain/rps + 8 more repo-wide;
distinct from G-1 — the shipped pipeline deliberately replaced 5 racing `on_message` listeners) ·
**G-8 ChannelMatchSpec** (counting+chain channel-bound persistent matches) · **G-9
TournamentLobbySpec** (blackjack+rps lobby/pot choreography — narrowed by the adversary split).
**Rejected:** RegistryHubSpec (hubs are core §2 `parent_hub`; community proves 100% tier-1).
**Provisional:** P-1 EventFeedProjectionSpec (1 instance), LeaderboardSpec enrichment (extends an
existing family).

### The adversarial pass materially changed 4 results (each flagged inline)

1. **rps 88% → 78%** — the agent lifted the *whole* bracket to tier-2; the adversary split it: the
   lobby/pot choreography recurs (G-9), but the single-elimination bracket topology exists in ONE
   subsystem → 6 bracket-orchestration handlers stay tier-3 (mirroring blackjack's lobby handlers).
2. **games 90% → 100%** — the agent tiered its registry hub tier-3-needing-a-new-amendment;
   community tiered the *identical* pattern tier-1. Community is right (core §2 `parent_hub`), so I
   re-tiered games' two hubs and rejected RegistryHubSpec.
3. **spotlight 100% → 94%** — its 100% depended on the provisional P-1; I report the ratified floor.
4. **blackjack citation fix** — `_state.py:106` (a 57-line re-export shim) → the real
   `utils/terminal_guard.py:49` / `views/blackjack/pvp_view.py:201`.

### Two live runtime bugs surfaced (documented + flagged, NOT fixed — docs-only scope)

Two adversaries *independently* found reachable anti-double-settle defects in shipped source:
**deathmatch PvP** (`_DuelView._resolve`/`on_timeout` guard only on `is_over`+`pop`, no atomic
claim → double records write + double gear-wear) and **blackjack free-tournament** (`payout_tournament`
free_reward leg not row-guarded + `_check_tourn_done` has no aggregate settle-once → double consolation
pay in a free tournament). Both close by construction under a kernel-owned `settle_once` seam — i.e.
they are the empirical case for the rebuild design. In scope I documented them (audit danger-zone
section, full repro) and flag them for the owner; fixing runtime code is out of scope for this PR.

## Context delta

- **Needed but not pointed to:** the `core/runtime/message_pipeline.py` ordered-stage contract is the
  load-bearing fact for counting/chain/rps tiering (it's why they're *not* raw `on_message` G-1
  listeners), but nothing in the orientation route or the games folio points there — I found it by
  grepping `*Stage` classes. The games folio should name the message-pipeline as the intake seam for
  the message-driven games. Also: `services/game_wager_workflow.py` is *the* settlement/escrow seam
  for all wagered games and the single best doc for the money-safety story — it deserves a pointer
  from `docs/subsystems/games.md`.
- **Pointed to but didn't need:** the bulk of `docs/current-state.md`'s dated narrative (passes 6–9,
  the mining/BTD6 arcs) — for a scoped docs-only audit, the per-sector `S1-bot.md` + the substrate
  BRIEF were enough; the long historical narrative was noise for this task.
- **Discovered by hand:** (1) the message-pipeline stage table + short-circuit ordering; (2) the
  `game_wager_workflow` idempotency contract (FOR UPDATE row-consumption = settle-once); (3) that
  blackjack's spike `wins leaderboard` + `stat_writes` are *not in current source* (a spike-vs-source
  drift); (4) `SettleOnceMixin` actually lives in `utils/terminal_guard.py`, not `_state.py`.

## Decisions made alone (for owner ratification)

- **Amendment adjudication.** Ratified G-7/G-8/G-9 on the ≥2-subsystem recurrence bar; **narrowed**
  G-9 to lobby-only (bracket topology = deliberate tier-3, 1 instance); **rejected** RegistryHubSpec
  (core §2); held P-1 EventFeedProjectionSpec + the LeaderboardSpec enrichment as provisional. These
  are audit *proposals* into the amendment corpus, not build approval — the capstone/owner ratifies.
- **Reported the ratified-amendment floor (84%)**, not the with-provisional ceiling, as the headline —
  the disciplined number.

## Flagged for maintainer (⚑)

- **Two live anti-double-settle bugs** (deathmatch PvP; blackjack free tournament) — see the audit's
  danger-zone section for repro. Worth a small fix PR (add the synchronous `claim_settlement`/aggregate
  settle-once guard). I did not fix them (docs-only audit).
- **Amendment corpus now has G-7/G-8/G-9 + P-1** proposed by Lane C — the capstone must merge these
  with the other lanes' proposals and de-collide numbers (see the friction note below).

## 🛠 Friction → guard

**Friction:** the 10 fan-out agents worked in isolation with only a shared primer, so three of them
independently minted **"G-7"** for three *different* new primitives (MessagePipelineStageSpec,
TournamentBracketSpec, RegistryHubSpec) and two minted "G-8" for two things — I had to reconcile the
numbering by hand during synthesis. Same class of collision the repo already solved for the question
router (append-only, next free number) and claims (one-file-per-claim). **Guard (proposed, not yet
built — belongs to the audit substrate, not runtime):** a shared `amendments.md` registry in the
audit dir where each lane appends its proposed `G-<n>` against the next free number *before* writing
its lane file — the fan-out analog of the append-only router. Captured as this session's Q-0089 idea
(below) so the capstone/next audit session builds it. (Docs-substrate guard = free to ship, but it's
cross-lane so I'm routing it as an idea for the capstone rather than unilaterally creating a file the
other in-flight lanes don't know about.)

## 📤 Run report

- **Did:** Completed Lane C (Games & Community) of the new-bot capability audit — 289 units tiered,
  70%→84% grammar fit, 3 new amendments proposed, 2 live bugs surfaced · **Outcome:** shipped
- **Shipped:** #1664 — Lane C audit doc (`lanes/lane-C-games.md`), docs-only
- **Run type:** `manual` (dispatched lane assignment; not a routine)
- **⚑ Owner decisions needed:** ratify/adjust the 3 new amendments (G-7 MessagePipelineStageSpec ·
  G-8 ChannelMatchSpec · G-9 TournamentLobbySpec) + the 2 provisional (P-1 EventFeedProjectionSpec,
  LeaderboardSpec enrichment) when the capstone assembles the cross-lane amendment list. This is
  planning evidence, not build approval (Phase-3 owner gate holds).
- **⚑ Owner manual steps:** consider a small fix PR for the two live anti-double-settle bugs
  (deathmatch PvP double-records/gear-wear; blackjack free-tournament double-pay) — repro in the audit
  doc. Not fixed here (docs-only audit).
- **⚑ Self-initiated:** none — Lane C was the dispatched task; the amendment adjudications are the
  audit's assigned output, not unprompted feature work.
- **↪ Next:** other lanes (A/B/D) + the capstone merge the amendment corpus; Lane F benchmarks the
  outperform targets left `pending Lane F`.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 0 at write time (auto-merges on green) |
| CI-red rounds | 0 (docs-only; born-red card flips green as the final step) |
| Repo-rule trips | 0 (no arch/quality violations; docs-only) |
| New ideas contributed | 1 (Q-0089 — audit-fleet amendment registry) |
| Ideas groomed | 0 (see grooming note) |
| Fan-out agents | 14 (10 verify + 4 adversary), 0 errors, ~1.37M subagent tokens |
| Units audited | 289 across 10 subsystems |
| Adversary-driven corrections | 4 (rps 88→78, games 90→100, spotlight 100→94, blackjack citation) |

## 💡 Session idea (Q-0089)

**A shared amendment registry for the capability-audit fleet** — `docs/analysis/rebuild-discovery/
new-bot-capability-audit/amendments.md`, append-only, next-free-`G-<n>` (the exact convention the
question router and one-file-per-claim already use). This session hit the collision it prevents: three
isolated fan-out agents each minted "G-7" for a different primitive, forcing a hand reconciliation. As
the fleet (Lanes A–G) all propose amendments into one corpus the capstone must merge, a shared,
claim-as-you-go registry makes the numbering conflict-free and gives the capstone a single
pre-deduplicated list instead of N colliding local numberings. Dedup-checked `docs/ideas/` +
`rebuild-discovery/` — novel. Worth building as part of the capstone's assembly step or the next audit
session.

## ⟲ Previous-session review (Q-0102)

Reviewing **#1653** (`2026-07-02-review-recent-session.md` — the independent review of the #1649
substrate-kit finalize). It was strong: it verified #1649's headline claims against source, ran a
4-reviewer adversarial pass, and fixed 10 confirmed defects at root with regression tests. Its own
closing insight was sharp — *"happy-path fixtures masked several defects; an adversarial round should
include a fixture-adversary pass that checks each guard's test actually exercises the hard case."*

**What generalizes to this session:** my adversarial pass caught the rps 88% inflation and the
amendment-number collisions **only because the verifiers re-read source rather than trusting the
Phase-1 rows** — the audit analog of "don't trust the happy-path fixture." But #1653's lesson points
at a deeper gap this session lived: **a fan-out fleet needs a shared-state seam for anything the lanes
must agree on.** My 10 agents couldn't see each other's amendment numbers (→ the G-7 collision) or
each other's tiering of shared patterns (→ games-vs-community hub inconsistency). **System
improvement:** the fixture-adversary discipline for a *fleet* is (a) a shared registry for
cross-lane-agreed artifacts (my Q-0089 idea), and (b) a standing synthesis rule that any pattern
appearing in ≥2 lanes/sections must be tiered *identically* — an explicit consistency check, not left
to the synthesizer to notice. I applied (b) by hand this session (the hub adjudication); codifying it
would make the next fan-out audit self-consistent by construction.

## Doc audit (Q-0104)

`check_docs.py --strict` green · `check_current_state_ledger.py --strict` EXIT 0 (only benign
newest-merge lag, recorded by the next reconciliation pass — my docs-only PR touches no ledger) · the
audit doc is reachable from the substrate's `lanes/` index · no new binding rules or owner decisions to
route (an audit, not a rule change; the amendment proposals live in the audit doc for the capstone, and
the two bugs are flagged in the run report for a fix PR, not the router). Grooming (Q-0015): this was a
heavy single-deliverable session; I contributed the Q-0089 idea rather than moving an existing one —
noted honestly rather than forcing a low-value backlog move.
