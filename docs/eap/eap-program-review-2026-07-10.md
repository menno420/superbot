# EAP program review — everything since Projects access (2026-07-07 → 2026-07-10)

> **Status:** `reference` — owner-directed deep review of the whole Projects-EAP period:
> the day-by-day story, verdicts per chapter, root-cause analysis of every recorded problem
> class, and the structural improvement agenda (centralization, documentation, ordering).
> Method: three parallel deep-read subagents (the EAP corpus in this repo; the
> fleet-manager doctrine stack; a cross-repo structural diff over all 13 local clones)
> synthesized by the coordinating session, on top of the same-day
> [`fleet-overnight-review-2026-07-10.md`](fleet-overnight-review-2026-07-10.md) (8
> subagents, one per lane). Companion chat delivery: session
> `2026-07-10-fleet-overnight-review` (PR 2).

## 1. The story in four days

- **07-07 — access + calibration + the autonomy ruling.** The invite was evaluated the day
  it landed (#1776/#1807); Q-0241 removed the rebuild's owner gates ("never-wait, silence =
  consent"), which is what made unattended fleet operation possible at all. The coordinator
  Project was stood up deliberately: thin instructions, a 13-question calibration exchange
  *before any work*, and a working-relationship inquiry whose answers became the operating
  model (kickoff doc §8). First platform findings landed the same night (coordinator has no
  shell; stale container clone; CLAUDE.md injection works).
- **07-08 — the permission map + the first email.** An 11-test isolated probe mapped the
  auto-mode boundary (#1830/#1842): constructive actions prompt-free; destructive git
  hard-walled; the Contents API bypasses the first-publish push wall (became the sanctioned
  bootstrap). A 3-simultaneous-session stress test produced 7 merged PRs, zero collisions,
  and coordinator recall graded ≈0.98 against git (#1859). The two-vantage split (operator
  sees a Deny/Allow the agent can't) was reproduced live and became the flagship finding of
  the first Anthropic email, SENT 15:06Z.
- **07-09 — one repo becomes ten Projects; gen-1 runs and winds itself down.** The rebuild
  coordinator shipped 49 merged PRs across 18 worker sessions in ~14h, zero reverts, ending
  in a bot that boots RUNNING against real Postgres (the first live boot caught a
  Postgres-only bug unit tests missed). The fleet protocol (git-as-message-bus, one writer
  per file) was designed, fleet-manager seeded, the codetool model-comparison arms +
  trading lab launched — 10 concurrent Projects by afternoon. Evening: a deliberate
  generation change — every lane answered a shared retro and shipped a succession package,
  adversarially audited (21/21 incidents verified, zero fabrication, five real inaccuracies
  found — the worst inside the manager's own report). Anthropic extended the window to
  07-14.
- **07-10 — the gen-2 launch night.** Every lane relaunched from the now-binding
  gen2-blueprint ("born right": seed checklist, tested setup scripts, walls documented with
  verbatim error text, walking-skeleton-first, self-merge + post-merge review). Result: 116
  PRs fleet-wide 00:00–06:15Z, zero stuck, two repos born and completed (pokemon-mod-lab's
  12 proof-bundled QoL patches; gba-homebrew's scope-complete original game), superbot's
  shift plan A–E2 + 41st recon, venture-lab's two sellable zips. Full audit:
  [`fleet-overnight-review-2026-07-10.md`](fleet-overnight-review-2026-07-10.md).

## 2. Verdicts per chapter (review opinion)

- **07-07 setup: excellent.** Calibrating the coordinator before trusting it, and turning
  its answers into the operating model, is why later coordination worked.
- **07-08 probing: the highest-leverage day.** Mapping walls *systematically* (instead of
  hitting them mid-mission) is what gen-1 lanes lacked and gen-2 was born with. The ~6
  sessions of email drafting were the day's least proportionate spend (see §5.3).
- **07-09 explosion: impressive but the "discovery tax" day.** The grand review's verdict
  stands: *the model-work was efficient; the orchestration layer lost the day.* Most losses
  were platform walls, not agent failures. The deliberate wind-down + audited succession is
  the best process decision of the program — gen-1's 13 failure classes became gen-2's
  boot-time knowledge instead of re-discovered pain.
- **07-10 launch night: the payoff.** Near-flawless execution at 13-repo scale — but it ran
  *self-terminal by design* (no wake triggers armed), so the fleet's flagship night
  succeeded without its own top-priority mitigation in place. It worked because sessions
  were seeded well, not because the system can sustain itself yet.

## 3. What went very well (and why it worked)

1. **Zero abandoned work at fleet scale** — every repo: no open stale PRs, empty claims,
   terminal sessions. Cause: the born-red/claim/status machinery *where it works* plus the
   completion-bias doctrine.
2. **Honesty held at 10× parallelism** — negative results as headlines (trading's negative
   program verdict; the kit's own bench FAIL in its release notes; "cannot determine"
   attributions). Cause: the integrity rules were binding, and audits proved fabrication
   would be caught (21/21 verified).
3. **The self-audit loop closed** — a checker built at 03:43 (#1923) caught real manifest
   staleness by morning; guards shipped mid-band forced the next session to dogfood them;
   corrections were re-verified before application (#1926, Q-0120).
4. **The generation mechanism** — retro → succession package → audited → blueprint →
   relaunch is a genuine invention of this program and demonstrably worked (gen-2's 116/0
   vs gen-1's wall-hitting).
5. **Verification culture** — every headline number spot-checked here reproduced exactly
   (test counts, zips, live pages, holdout seal).

## 4. What went wrong, by root cause

- **Platform walls (~70% of lost time; not agent error):** no scheduler/self-wake, no
  inter-session channel, no fleet view, classifier inconsistency per seat, two-vantage
  permission split, fatal setup scripts, GraphQL quota, first-publish push wall, 403s on
  tags/releases/branch-deletes. All documented with verbatim errors and already in the
  Anthropic feedback pipeline. Correct handling throughout: probe, document, route around.
- **Workflow gaps (fixable, several already fixed):** claims blind window (fixed #1919),
  order-number races (fixed R19/R20), kit adoption stranding half-engaged (kit fix
  in-flight), manifest staleness (checker #1923; re-stamp pending), games CI covering half
  the tests, codetool labs contradicting each other on the release wall, model-comparison
  seat contamination.
- **Agent errors (rare, all caught by the program's own reviews):** the rebuild
  warn-escalation semantic regression (open, prescription written), the help-embed silent
  shed (fixed), reviewer inaccuracies incl. the manager's false "NO ACK" row (corrected /
  correction pending), the grand review's own 8/8-vs-6/8 parity claim (corrected #1926).

## 5. Structural findings (the things nobody's single doc flags)

1. **Proposals don't get applied — the biggest process hole.** The Fable-5 fleet review's
   30 verified findings: ~5 acted on, ~22 proposal-only, 3 idea-only. The binding blueprint
   still contains sentences three HIGH findings falsified; P1–P11 amendments were handed to
   a session that had already ended; 8 of 10 instruction packages sit undeployed; D4/D5/D6
   drift fixes queued. Realized cost: venture-lab launched on the uncorrected text and hit
   the exact predicted merge wall twice. **Fix: doctrine amendments become ORDERS in the
   manager's own inbox (which is empty — the one channel it built for everyone, unused on
   itself), with the next-session pickup rule.**
2. **Post-merge review has degraded to no review.** 116 merged PRs → zero rows in any
   review queue; no appenders, no drainer, no obligation to read it. The queue was the
   safety valve that justified "no pre-merge review." **Fix: auto-append above a size/risk
   threshold + a named standing drainer.**
3. **Conventions fork because the kit plants docs once.** The kit distributes *code* with
   versioned upgrades but *conventions* as one-shot planted docs that fork on first edit —
   the root cause behind 4 claim mechanisms, 5 session-gate workflow variants, 6 setup
   scripts, 2 review-queue formats, 4 session-README generations. **Fix: lockstep
   conventions become kit-owned-and-regenerated or checker-backed — never just planted.**
4. **The registries disagree.** Kit-version truth has four homes (manifest, per-repo
   config, heartbeat `kit:` line, kit `adopters.md`) — all currently mutually inconsistent
   (spread v1.0.0→v1.7.0); the repo roster has two (manifest vs manager's Lanes list),
   already contradicting each other. **Fix: one generated roster derived from heartbeats,
   owned by fleet-manager (see §7).**
5. **The owner-as-only-clock finding was falsified mid-review by the owner himself.** The
   doctrine (fleet-manager `capabilities.md`, blueprint §2a) says Routines are walled on
   both sides — but the owner's 07-10 ~11:01Z screen recording shows two **agent-armed,
   active, firing** wake routines (trading-strategy 4-hourly; kit-lab hourly — both
   "Created by Claude", with completed runs). Self-wake works, at least from some seats
   (same per-seat inconsistency class as the merge classifier). Residual gaps: completed
   runs are not inspectable from the Routines screen (timestamp only — new eval-log entry),
   the capability doc + blueprint wake doctrine must be corrected, and lanes without
   routines still need arming (agent-side now, apparently). The liveness-*detection*
   sweep is still worth automating.
6. **The evaluation journal went silent at the peak** — no entries after 07-09 ~16:36Z;
   the biggest night of the EAP produced zero journal rows. Same class: exhorted, not
   enforced.
7. **No open/closed ledger for the ~40 recorded frictions** — reconstructing disposition
   required cross-reading six documents. The B1 "capabilities manifest" back-port is the
   closest fix and is still only a recommendation.
8. **Verification is a closed Claude loop.** Every audit layer is another Claude session;
   the external-review pack (#1903) was built to break this and shows no evidence of use.
9. **The hub never adopted its own kit.** superbot pins a fictional v1.0.0, hand-authors
   telemetry, and maintains a parallel (better) session-gate implementation — the origin
   repo is the only active repo not on the substrate it exports.
10. **Timing/ordering nits:** the wrap-up email cites the codetool comparison without the
    later-discovered seat contamination (reconcile before sending); the born-red gate
    template shipped broken and its correct fix is stranded in gba-homebrew; the manager
    holds lanes to delta-8 but has no mission/done-when of its own.

## 6. Centralization agenda (from the cross-repo diff; ranked)

1. Born-red gate fix (gba-homebrew's ADDED-advisory/MODIFIED-locked logic) → kit CI
   template, with `substrate-gate.yml` treated as kit-owned on upgrade.
2. One generated repo roster from heartbeats (manager-owned), replacing the hand-written
   manifest + Lanes double-bookkeeping.
3. Kit-upgrade currency checker (+ generated `adopters.md`) — nothing owns the version
   spread today.
4. Claims: kit-planted one-file-per-claim template + `check_claims` unified on it (today:
   four conventions + a checker checking a fifth).
5. Setup-script contract (`scripts/env-setup.sh`, exit-0, no secrets) rendered from the
   manager's archetypes — six divergent hand-rolled scripts today.
6. Telemetry aggregator in fleet-manager + move `allocation-ladder.md` (fleet policy)
   out of the kit (mechanism) repo.
7. superbot truly adopts the kit (retire the parallel gate + hand telemetry).
8. ORDER/OWNER-ACTION grammar as one kit-owned constant consumed by both writer and
   enforcer (the manager's own seeded orders currently fail the kit's 1.7.0 grammar).
9. Review-queue template + auto-append checker (see §5.2).
10. Auto-merge enabler workflow planted by the kit + repo-settings one-time checklist in
    adopt.

## 7. Ordering ruling needed (owner)

The layering *intends*: superbot = program record · fleet-manager = coordination · kit =
mechanism. Four inversions to settle: the fleet manifest lives in superbot while its
declared sole writer lives in fleet-manager (move it, or make it generated); fleet policy
(allocation ladder, telemetry schema) lives in the kit repo; kit-version truth and the
repo roster are multi-homed (pick the generated single home); the codetool labs are
readable but never integrated into any roster lifecycle. None is urgent alone; together
they are why "what is the fleet's state?" takes six documents to answer.

## 8. Consolidated next actions

**Agent-side (no owner needed):** apply P1–P11 to the blueprint via a manager inbox ORDER;
re-stamp the manifest; games CI exploration-tests line; reconcile the codetool release-wall
contradiction + annotate the wrap-up email's comparison caveat; websites token-claim
reconcile; journal disposition column for the §4 friction log; staleness-detection sweep.
**Owner clicks (already queued, deduplicated):** send the wrap-up email (window to 07-14 —
add the routine-self-arming discovery, it changes finding #1's framing); the repo-settings
sweep (required checks, Allow auto-merge, branch cleanup); wake triggers for the lanes
agents haven't self-armed yet (kit-lab + trading already self-armed per the 07-10 recording);
paste the reviewed instruction packages; concept picks (pokemon/gba); trading holdout
unlock; kit F-5 ruling; the economics question — the free window closes 07-14 with zero
cost data collected (the fleet-economics ledger idea is the time-critical unbuilt one).
